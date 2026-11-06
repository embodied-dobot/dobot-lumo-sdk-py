#!/usr/bin/env python3
# 切到拟人行走，向前走一段再向后走一段，最后停住。
# 必须加 --run 才会动。Ctrl+C 会再发一次零速度。
import argparse
import signal
import sys
import threading
import time

from common import add_connection_args, open_session

import dobot


def install_stop():
    stop = threading.Event()

    def on_signal(_signum, _frame):
        stop.set()

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    return stop


def wait_seconds(seconds, stop):
    deadline = time.monotonic() + seconds
    while not stop.is_set() and time.monotonic() < deadline:
        time.sleep(0.05)
    return not stop.is_set()


def fail(what, code):
    print(f"{what} 失败 {dobot.RpcErrorName(dobot.RpcError(code))}", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(
        description=(
            "先切到拟人行走，再按 --vx 向前走 --seconds 秒，然后以同样速度向后走，"
            "重复 --laps 次，最后停住。不加 --run 不会动。速度单位是 m/s。"
        )
    )
    add_connection_args(parser)
    parser.add_argument("--run", action="store_true", help="确认让机器人行走。")
    parser.add_argument("--vx", type=float, default=0.2, help="向前速度，m/s")
    parser.add_argument("--seconds", type=float, default=2.0, help="每一段的秒数")
    parser.add_argument("--laps", type=int, default=1, help="来回次数")
    args = parser.parse_args()
    if not args.run:
        print("未加 --run，机器人不会动。", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 2
    if args.vx <= 0.0 or args.seconds <= 0.0 or args.laps < 1:
        print("--vx 和 --seconds 要大于 0，--laps 至少为 1。", file=sys.stderr)
        return 2

    stop = install_stop()
    session, _robot = open_session(args)
    try:
        motion = session.motion()
        code = motion.SetRobotMode(dobot.RobotMode.kWalking, args.timeout_ms)
        if code != 0:
            return fail("SetRobotMode(walk)", code)
        print(f"已切换到拟人行走。向前 {args.vx} m/s，每段 {args.seconds} 秒，共 {args.laps} 个来回。")

        moving = False
        for lap in range(1, args.laps + 1):
            if stop.is_set():
                break
            print(f"第 {lap} 个来回：向前")
            code = motion.SetVelocity(args.vx, 0.0, 0.0, args.seconds, args.timeout_ms)
            if code != 0:
                return fail("SetVelocity 向前", code)
            moving = True
            if not wait_seconds(args.seconds, stop):
                break
            print(f"第 {lap} 个来回：向后")
            code = motion.SetVelocity(-args.vx, 0.0, 0.0, args.seconds, args.timeout_ms)
            if code != 0:
                motion.SetVelocity(0.0, 0.0, 0.0, 1.0, args.timeout_ms)
                return fail("SetVelocity 向后", code)
            if not wait_seconds(args.seconds, stop):
                break

        if moving or stop.is_set():
            code = motion.SetVelocity(0.0, 0.0, 0.0, 1.0, args.timeout_ms)
            if code != 0:
                return fail("SetVelocity 停止", code)
            print("已停止")
        return 0
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
