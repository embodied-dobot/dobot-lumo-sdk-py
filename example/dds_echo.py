#!/usr/bin/env python3
import argparse

from common import add_connection_args, open_session


def main():
    parser = argparse.ArgumentParser(description="订阅下肢和上肢状态，打印前几个关节。")
    add_connection_args(parser)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    session, robot = open_session(args)
    try:
        lower = session.Subscribe(robot.kTopicLowerState)
        upper = session.Subscribe(robot.kTopicUpperState)
        if not lower.valid() or not upper.valid():
            raise SystemExit("创建订阅失败")
        timeout_ms = int(args.seconds * 1000)
        got_lower = lower.WaitForData(timeout_ms)
        got_upper = upper.WaitForData(timeout_ms)
        print(f"matched lower={lower.Matched()} upper={upper.Matched()}")
        if not got_lower and not got_upper:
            raise SystemExit("没有收到状态。核对 domain，多网卡时核对 --nic。")
        sample = lower.Latest()
        if sample is not None:
            motors = sample.motor_state
            print(f"lower joints={len(motors)}")
            for index, motor in enumerate(motors[:4]):
                print(f"  [{index}] q={motor.q} dq={motor.dq} tau_est={motor.tau_est}")
        sample = upper.Latest()
        if sample is not None:
            print(f"upper robot_type={sample.robot_type!r} is_upper_control={sample.is_upper_control}")
        return 0
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
