#!/usr/bin/env python3
import argparse
import json

from common import add_connection_args, open_session

import dobot


def main():
    parser = argparse.ArgumentParser(description="调用一条 JSON-RPC。查状态机和切模式用 motion_demo.py。")
    add_connection_args(parser)
    parser.add_argument("--method", required=True)
    parser.add_argument("--params", default="{}")
    args = parser.parse_args()
    params = json.loads(args.params)
    session, _robot = open_session(args)
    try:
        result = session.rpc().Call(args.method, params, args.timeout_ms)
        print(f"error={dobot.RpcErrorName(result.error)} message={result.message}")
        if result.ok():
            print(result.result())
        return 0 if result.ok() else 1
    finally:
        session.Shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
