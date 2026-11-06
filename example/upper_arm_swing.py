#!/usr/bin/env python3
# SR_3588 的上肢摆臂示例。持续写 rt/upper/cmd，直到 Ctrl+C。
# 先读当前上肢角度。双臂第二个关节先向外让出 10°，再以这个角度为内侧起点来回摆。
# Ctrl+C 后回到启动时的贴身角度。
import argparse
import math
import os
import signal
import sys
import threading
import time

from common import add_connection_args, open_session

import dobot


UPPER_JOINTS = 18
LEFT_ARM_JOINT = 4  # 左臂第 1 关节，向外为正。上肢顺序：0–2 腰，3–9 左臂，10–16 右臂，17 头
RIGHT_ARM_JOINT = 11  # 右臂第 1 关节，向外为负
LEFT_LATERAL_MIN = -0.43
LEFT_LATERAL_MAX = 3.14
RIGHT_LATERAL_MIN = -3.14
RIGHT_LATERAL_MAX = 0.43
MIT_MODE = 11
DEFAULT_KP = 10.0
DEFAULT_KD = 1.0
PI = math.pi
DEFAULT_AMPLITUDE = PI / 2.0
DEFAULT_PERIOD = 2.0
DEFAULT_HZ = 1000.0
MAX_HZ = 1000.0
MAX_AMPLITUDE = PI / 2.0
MAX_KP = 40.0
MAX_KD = 5.0
CLEARANCE_RAD = 10.0 * PI / 180.0
APPROACH_SEC = 1.0
RETURN_SEC = 1.0


def install_stop():
    stop = threading.Event()

    def on_signal(_signum, _frame):
        if stop.is_set():
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGINT)
            return
        stop.set()

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    return stop


def limit_joint(q, delta, dq, q_min, q_max):
    out_q = q + delta
    out_dq = dq
    if out_q > q_max:
        out_q = q_max
        if out_dq > 0.0:
            out_dq = 0.0
    elif out_q < q_min:
        out_q = q_min
        if out_dq < 0.0:
            out_dq = 0.0
    return out_q, out_dq


def make_cmd(q0, left, right, kp, kd):
    motors = []
    for index, position in enumerate(q0):
        motor = dobot.MotorCmd_()
        motor.mode = MIT_MODE
        motor.q = position
        motor.dq = 0.0
        motor.tau = 0.0
        motor.kp = kp
        motor.kd = kd
        if index == LEFT_ARM_JOINT:
            motor.q, motor.dq = left
        elif index == RIGHT_ARM_JOINT:
            motor.q, motor.dq = right
        motors.append(motor)
    command = dobot.UpperCmd_()
    command.motor_cmd = motors
    return command


def read_pose(upper):
    sample = upper.Latest()
    if sample is None or len(sample.motor_state) < UPPER_JOINTS:
        return None
    return [sample.motor_state[index].q for index in range(UPPER_JOINTS)]


def sleep_until(deadline):
    delay = deadline - time.monotonic()
    if delay > 0:
        time.sleep(delay)


def catch_up(next_tick, dt):
    next_tick += dt
    now = time.monotonic()
    if now > next_tick:
        return now
    return next_tick


def main():
    parser = argparse.ArgumentParser(
        description=(
            "向 rt/upper/cmd 持续发送 SR_3588 上肢命令。"
            "双臂第二个关节先向外让出 10°，再以这个角度为内侧起点向外抬起。"
            "往复只回到这 10°。腰、头和其余关节保持启动时读到的角度。"
            "必须加 --move。一直运行，Ctrl+C 后先回到贴身角度再退出。再按一次 Ctrl+C 会立刻结束。"
            "这是真实关节命令。机器人需要已经处于会执行 rt/upper/cmd 的使能状态。"
        )
    )
    add_connection_args(parser)
    parser.add_argument("--move", action="store_true", help="确认发送真实关节命令。")
    parser.add_argument("--amplitude", type=float, default=DEFAULT_AMPLITUDE, help=f"10° 之外再向外的幅度，rad，最大 {MAX_AMPLITUDE}")
    parser.add_argument("--period", type=float, default=DEFAULT_PERIOD, help="向外再回到这 10° 的秒数，范围 2 到 30")
    parser.add_argument("--hz", type=float, default=DEFAULT_HZ, help=f"发送频率，范围 20 到 {MAX_HZ:g}")
    parser.add_argument("--kp", type=float, default=DEFAULT_KP, help=f"最大 {MAX_KP:g}")
    parser.add_argument("--kd", type=float, default=DEFAULT_KD, help=f"最大 {MAX_KD:g}")
    args = parser.parse_args()
    if args.model != "sr_3588":
        print("这个示例是 SR_3588 的上肢摆臂，关节序号和限位不能用在其他型号上。", file=sys.stderr)
        return 2
    if not args.move:
        print("必须加 --move 才会发送上肢命令。", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 2
    if not (args.amplitude > 0.0 and args.amplitude <= MAX_AMPLITUDE + 1.0e-4):
        print(f"amplitude 要在 (0, {MAX_AMPLITUDE}] rad", file=sys.stderr)
        return 2
    if not (2.0 <= args.period <= 30.0):
        print("period 要在 [2, 30] 秒", file=sys.stderr)
        return 2
    if not (20.0 <= args.hz <= MAX_HZ):
        print(f"hz 要在 [20, {MAX_HZ:g}]", file=sys.stderr)
        return 2
    if not (0.0 < args.kp <= MAX_KP) or not (0.0 <= args.kd <= MAX_KD):
        print(f"kp 要在 (0, {MAX_KP:g}]，kd 要在 [0, {MAX_KD:g}]", file=sys.stderr)
        return 2

    stop = install_stop()
    session, robot = open_session(args)
    try:
        upper = session.Subscribe(robot.kTopicUpperState)
        writer = session.Publish(robot.kTopicUpperCmd)
        if not upper.valid() or not writer.valid():
            print("创建订阅或发布失败", file=sys.stderr)
            return 1
        if not upper.WaitForData(5000):
            print("5 秒内没有收到 rt/upper/state，不发送命令", file=sys.stderr)
            return 1

        print("等待 rt/upper/cmd 匹配。Ctrl+C 结束。", flush=True)
        while not stop.is_set() and writer.Matched() == 0:
            time.sleep(0.05)
        if stop.is_set():
            print("匹配前已停止")
            return 0

        q0 = read_pose(upper)
        if q0 is None:
            print(f"上肢状态关节数不足 {UPPER_JOINTS}，不发送命令", file=sys.stderr)
            return 1

        print(
            f"开始摆臂。左臂下标 {LEFT_ARM_JOINT} 与右臂下标 {RIGHT_ARM_JOINT} 先向外让出 {CLEARANCE_RAD}"
            f" rad，再向外抬起 {args.amplitude} rad，往复回到这 10°，来回 {args.period} s，{args.hz}"
            f" Hz，kp={args.kp} kd={args.kd}。",
            flush=True,
        )
        print("其余上肢关节保持当前角度。Ctrl+C 后回到贴身角度。", flush=True)

        dt = 1.0 / args.hz
        next_tick = time.monotonic()
        report_at = next_tick + 1.0
        write_ok = 0
        write_fail = 0
        window_ok = 0
        window_fail = 0
        left_delta = 0.0
        right_delta = 0.0
        left = (q0[LEFT_ARM_JOINT], 0.0)
        right = (q0[RIGHT_ARM_JOINT], 0.0)

        approach_steps = max(1, int(args.hz * APPROACH_SEC))
        for step in range(1, approach_steps + 1):
            if stop.is_set():
                break
            tau = step / approach_steps
            outward = CLEARANCE_RAD * 0.5 * (1.0 - math.cos(PI * tau))
            outward_vel = CLEARANCE_RAD * 0.5 * math.sin(PI * tau) * (PI / APPROACH_SEC)
            left_delta = outward
            right_delta = -left_delta
            left = limit_joint(q0[LEFT_ARM_JOINT], left_delta, outward_vel, LEFT_LATERAL_MIN, LEFT_LATERAL_MAX)
            right = limit_joint(q0[RIGHT_ARM_JOINT], right_delta, -outward_vel, RIGHT_LATERAL_MIN, RIGHT_LATERAL_MAX)
            if writer.Write(make_cmd(q0, left, right, args.kp, args.kd)):
                write_ok += 1
            else:
                write_fail += 1
            next_tick = catch_up(next_tick, dt)
            sleep_until(next_tick)

        swing_start = time.monotonic()
        while not stop.is_set():
            elapsed = time.monotonic() - swing_start
            angle = 2.0 * PI * elapsed / args.period
            swing = args.amplitude * 0.5 * (1.0 - math.cos(angle))
            outward = CLEARANCE_RAD + swing
            outward_vel = args.amplitude * (PI / args.period) * math.sin(angle)
            left_delta = outward
            right_delta = -left_delta
            left = limit_joint(q0[LEFT_ARM_JOINT], left_delta, outward_vel, LEFT_LATERAL_MIN, LEFT_LATERAL_MAX)
            right = limit_joint(q0[RIGHT_ARM_JOINT], right_delta, -outward_vel, RIGHT_LATERAL_MIN, RIGHT_LATERAL_MAX)
            if writer.Write(make_cmd(q0, left, right, args.kp, args.kd)):
                write_ok += 1
                window_ok += 1
            else:
                write_fail += 1
                window_fail += 1

            now = time.monotonic()
            if now >= report_at:
                print(
                    f"t={elapsed}s left={left[0]} right={right[0]} matched={writer.Matched()}"
                    f" write_ok={window_ok} write_fail={window_fail}",
                    flush=True,
                )
                window_ok = 0
                window_fail = 0
                report_at = now + 1.0

            next_tick = catch_up(next_tick, dt)
            sleep_until(next_tick)

        print("正在回到贴身角度", flush=True)
        next_tick = time.monotonic()
        return_steps = max(1, int(args.hz * RETURN_SEC))
        left_from = left_delta
        right_from = right_delta
        for step in range(1, return_steps + 1):
            scale = 1.0 - step / return_steps
            vel = 0.0 if step == return_steps else -1.0 / RETURN_SEC
            left = limit_joint(q0[LEFT_ARM_JOINT], left_from * scale, left_from * vel, LEFT_LATERAL_MIN, LEFT_LATERAL_MAX)
            right = limit_joint(q0[RIGHT_ARM_JOINT], right_from * scale, right_from * vel, RIGHT_LATERAL_MIN, RIGHT_LATERAL_MAX)
            writer.Write(make_cmd(q0, left, right, args.kp, args.kd))
            next_tick += dt
            sleep_until(next_tick)

        print(f"已停止 write_ok={write_ok} write_fail={write_fail}")
        return 0
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
