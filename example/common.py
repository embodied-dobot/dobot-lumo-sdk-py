import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "dobot").is_dir():
    sys.path.insert(0, str(ROOT))

import dobot
from dobot import sr_3588, sr_thor


def model_module(name):
    if name == "sr_3588":
        return sr_3588
    if name == "sr_thor":
        return sr_thor
    raise SystemExit(f"未知型号: {name}")


def add_connection_args(parser, default_model="sr_3588"):
    parser.add_argument("--model", choices=("sr_3588", "sr_thor"), default=default_model)
    parser.add_argument("--ip", default="")
    parser.add_argument("--on-robot", action="store_true")
    parser.add_argument("--domain", type=int, default=0)
    parser.add_argument("--nic", default="")
    parser.add_argument("--timeout-ms", type=int, default=3000)


def open_session(args, async_subscribe=None):
    robot = model_module(args.model)
    config = dobot.SessionConfig()
    config.where = dobot.RunWhere.kRobot if args.on_robot else dobot.RunWhere.kComputer
    config.robot_ip = args.ip
    config.domain_id = args.domain
    config.network_interface = args.nic
    if async_subscribe is not None:
        config.async_subscribe = async_subscribe
    session = dobot.Session()
    ok, error = session.Init(robot.Profile(), config)
    if not ok:
        raise SystemExit(error)
    return session, robot
