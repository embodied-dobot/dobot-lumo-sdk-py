#!/usr/bin/env python3
import argparse
import threading

from common import add_connection_args, open_session


def main():
    parser = argparse.ArgumentParser(description="订阅急停话题，收到一帧就打印。")
    add_connection_args(parser)
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    done = threading.Event()

    def on_estop(sample):
        print(f"estop stop1={sample.stop1} stop2={sample.stop2}")
        done.set()

    session, robot = open_session(args)
    try:
        estop = session.Subscribe(robot.kTopicMcuEstop)
        if not estop.valid():
            raise SystemExit("创建订阅失败")
        estop.On(on_estop)
        if not done.wait(args.seconds):
            print(f"matched={estop.Matched()}，{args.seconds} 秒内没有收到急停")
            return 1
        return 0
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
