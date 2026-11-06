#!/usr/bin/env python3
import argparse

from common import add_connection_args, open_session

import dobot


MODES = {
    "zero": dobot.RobotMode.kZeroTorque,
    "damp": dobot.RobotMode.kDamping,
    "debug": dobot.RobotMode.kCustomDebug,
    "ready": dobot.RobotMode.kReady,
    "stand": dobot.RobotMode.kStanding,
    "walk": dobot.RobotMode.kWalking,
}

ACTIONS = {
    "enter-box": "AutoEnterBox",
    "lie": "LieDown",
    "prone": "GoProne",
    "exit-box": "AutoExitBox",
    "stand-supine": "StandUpFromSupine",
    "stand-prone": "StandUpFromProne",
}


def print_fsm(motion):
    code, fsm_id = motion.GetFsmId()
    if code != 0:
        print(f"GetFsmId 失败 {dobot.RpcErrorName(dobot.RpcError(code))}")
        return code
    print(f"fsm_id={fsm_id} {dobot.Motion.FsmIdToString(fsm_id)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="查询状态机、切换模式、预设动作、舞蹈。")
    add_connection_args(parser)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--mode", choices=tuple(MODES))
    parser.add_argument("--action", choices=tuple(ACTIONS))
    parser.add_argument("--dance", type=int)
    parser.add_argument("--fsm-id", type=int)
    args = parser.parse_args()
    chosen = sum(item is not None and item is not False for item in (args.mode, args.action, args.dance, args.fsm_id))
    if chosen > 1:
        raise SystemExit("--mode、--action、--dance、--fsm-id 只能指定一个")

    session, _robot = open_session(args)
    try:
        motion = session.motion()
        if args.list:
            code, fsm_list = motion.GetFsmList(args.timeout_ms)
            if code != 0:
                print(f"GetFsmList 失败 {dobot.RpcErrorName(dobot.RpcError(code))}")
                return 1
            for info in fsm_list:
                print(f"{info.fsm_id} {info.name}")
            return 0
        code = 0
        if args.mode:
            code = motion.SetRobotMode(MODES[args.mode], args.timeout_ms)
            print(f"SetRobotMode {args.mode} -> {code}")
        elif args.action:
            code = getattr(motion, ACTIONS[args.action])(args.timeout_ms)
            print(f"{ACTIONS[args.action]} -> {code}")
        elif args.dance is not None:
            code = motion.PlayDance(args.dance, args.timeout_ms)
            print(f"PlayDance {args.dance} -> {code}")
        elif args.fsm_id is not None:
            code = session.rpc().SetFsmId(args.fsm_id, args.timeout_ms).error
            code = int(code)
            print(f"SetFsmId {args.fsm_id} -> {code}")
        if code != 0:
            return 1
        return print_fsm(motion)
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
