#!/usr/bin/env python3
import argparse

from common import add_connection_args, open_session

import dobot


def main():
    parser = argparse.ArgumentParser(description="向 rt/lower/cmd 发一帧全 0 的下肢命令。必须加 --send。")
    add_connection_args(parser)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    if not args.send:
        raise SystemExit("这是关节命令。确认要做通信测试时再加 --send。")
    session, robot = open_session(args)
    try:
        publisher = session.Publish(robot.kTopicLowerCmd)
        if not publisher.valid():
            raise SystemExit("创建发布失败")
        command = dobot.LowerCmd_()
        sent = publisher.Write(command)
        print(f"write={sent} matched={publisher.Matched()}")
        return 0 if sent else 1
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
