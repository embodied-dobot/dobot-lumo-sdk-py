#!/usr/bin/env python3
# 订阅四路周期状态。
# msg：消息里 timestamp_us 的前后差。recv：On() 被调用时的本地时间前后差。
# 每秒只打印这一秒。超过 5ms 时立刻打出前后时间戳和差值。到时或 Ctrl+C 后打全程汇总。
# --duration 指定运行秒数，不写则一直运行。终端上的输出同时写入 state_gap_日期时间.log。
import argparse
import os
import signal
import sys
import threading
import time
from datetime import datetime

from common import add_connection_args, open_session


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


class Log:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self._file = open(self.path, "w", encoding="utf-8")
        self._lock = threading.Lock()

    def print(self, text=""):
        line = text + "\n"
        with self._lock:
            sys.stdout.write(line)
            sys.stdout.flush()
            self._file.write(line)
            self._file.flush()

    def close(self):
        with self._lock:
            self._file.close()


def count_gap(delta_us, gaps, gaps_5ms):
    if delta_us > 5000:
        return gaps + 1, gaps_5ms + 1
    if delta_us > 2000:
        return gaps + 1, gaps_5ms
    return gaps, gaps_5ms


class GapWatch:
    def __init__(self, topic, log):
        self.topic = topic
        self._log = log
        self._lock = threading.Lock()
        self._last_msg_us = 0
        self._has_msg = False
        self._last_recv_us = 0
        self._has_recv = False
        self.samples = 0
        self.msg_gaps = 0
        self.msg_gaps_5ms = 0
        self.recv_gaps = 0
        self.recv_gaps_5ms = 0
        self.msg_sum_us = 0
        self.msg_intervals = 0
        self.msg_max_us = 0
        self.recv_sum_us = 0
        self.recv_intervals = 0
        self.recv_max_us = 0

    def on_receive(self, msg_us):
        msg_us = int(msg_us)
        now_us = time.monotonic_ns() // 1000
        over = []
        with self._lock:
            self.samples += 1
            if self._has_msg and msg_us > self._last_msg_us:
                delta = msg_us - self._last_msg_us
                self.msg_gaps, self.msg_gaps_5ms = count_gap(delta, self.msg_gaps, self.msg_gaps_5ms)
                self.msg_sum_us += delta
                self.msg_intervals += 1
                if delta > self.msg_max_us:
                    self.msg_max_us = delta
                if delta > 5000:
                    over.append(("msg", self._last_msg_us, msg_us, delta))
            self._last_msg_us = msg_us
            self._has_msg = True

            if self._has_recv:
                delta_us = now_us - self._last_recv_us
                if delta_us >= 0:
                    self.recv_gaps, self.recv_gaps_5ms = count_gap(delta_us, self.recv_gaps, self.recv_gaps_5ms)
                    self.recv_sum_us += delta_us
                    self.recv_intervals += 1
                    if delta_us > self.recv_max_us:
                        self.recv_max_us = delta_us
                    if delta_us > 5000:
                        over.append(("recv", self._last_recv_us, now_us, delta_us))
            self._last_recv_us = now_us
            self._has_recv = True
        for kind, prev_us, curr_us, delta_us in over:
            self._log.print(
                f">5ms {kind} topic={self.topic} prev_us={prev_us} curr_us={curr_us} delta_us={delta_us}"
            )

    def snapshot(self):
        with self._lock:
            return (self.samples, self.msg_gaps, self.msg_gaps_5ms, self.recv_gaps, self.recv_gaps_5ms)


def format_second(name, now, previous, matched):
    text = (
        f"{name} matched={matched} frames={now[0] - previous[0]}"
        f" msg>2ms={now[1] - previous[1]} msg>5ms={now[2] - previous[2]}"
        f" recv>2ms={now[3] - previous[3]} recv>5ms={now[4] - previous[4]}"
    )
    previous[:] = now
    return text


def format_total(name, watch, matched):
    with watch._lock:
        msg_avg = 0 if watch.msg_intervals == 0 else watch.msg_sum_us // watch.msg_intervals
        recv_avg = 0 if watch.recv_intervals == 0 else watch.recv_sum_us // watch.recv_intervals
        return (
            f"{name} matched={matched} frames={watch.samples}"
            f" msg>2ms={watch.msg_gaps} msg>5ms={watch.msg_gaps_5ms}"
            f" msg_avg_us={msg_avg} msg_max_us={watch.msg_max_us}"
            f" recv>2ms={watch.recv_gaps} recv>5ms={watch.recv_gaps_5ms}"
            f" recv_avg_us={recv_avg} recv_max_us={watch.recv_max_us}"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "订阅 rt/lower/state、rt/upper/state、rt/main/nodes/state、rt/pelvis/imu/data。"
            "msg 是消息 timestamp_us 的前后差，recv 是 On() 的本地时间前后差。"
            "大于 2ms、大于 5ms 按每一秒单独计数。超过 5ms 时立刻打印前后时间戳和差值。"
            "到时或 Ctrl+C 后打印全程汇总。不写 --duration 则一直运行。"
        )
    )
    add_connection_args(parser)
    parser.add_argument("--duration", type=int, help="运行秒数。不写则一直运行，Ctrl+C 结束。")
    args = parser.parse_args()
    if args.duration is not None and args.duration <= 0:
        print("--duration 需要正整数秒", file=sys.stderr)
        return 2

    stop = install_stop()
    # 和 C++ 示例一样，在监听线程里记收到时间，不经过有序队列。
    session, robot = open_session(args, async_subscribe=False)
    log = None
    try:
        lower = session.Subscribe(robot.kTopicLowerState)
        upper = session.Subscribe(robot.kTopicUpperState)
        main_nodes = session.Subscribe(robot.kTopicMainNodesState)
        imu = session.Subscribe(robot.kTopicPelvisImu)
        if not lower.valid() or not upper.valid() or not main_nodes.valid() or not imu.valid():
            print("创建订阅失败", file=sys.stderr)
            return 1

        stamp = datetime.now()
        log_name = stamp.strftime("state_gap_%Y%m%d_%H%M%S_") + f"{stamp.microsecond:06d}.log"
        try:
            log = Log(log_name)
        except OSError as exc:
            print(f"打开打印日志失败: {os.path.abspath(log_name)} ({exc})", file=sys.stderr)
            return 1

        watches = {
            "lower": GapWatch(robot.kTopicLowerState.name, log),
            "upper": GapWatch(robot.kTopicUpperState.name, log),
            "main": GapWatch(robot.kTopicMainNodesState.name, log),
            "imu": GapWatch(robot.kTopicPelvisImu.name, log),
        }
        lower.On(lambda sample: watches["lower"].on_receive(sample.timestamp_us))
        upper.On(lambda sample: watches["upper"].on_receive(sample.timestamp_us))
        main_nodes.On(lambda sample: watches["main"].on_receive(sample.timestamp_us))
        imu.On(lambda sample: watches["imu"].on_receive(sample.timestamp_us))

        log.print("订阅 lower/upper/main/imu。回调在监听线程。每秒只打印这一秒。超过 5ms 会立刻打印前后时间戳。")
        log.print(f"终端输出同时写入 {log.path}")
        if args.duration:
            log.print(f"计划运行 {args.duration} s。到时或 Ctrl+C 后打印全程汇总。")
        else:
            log.print("一直运行。Ctrl+C 后打印全程汇总。")

        started = time.monotonic()
        deadline = None if not args.duration else started + args.duration
        previous = {name: [0, 0, 0, 0, 0] for name in watches}
        window_start = started
        while not stop.is_set():
            slice_s = 0.1
            if deadline is not None:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                slice_s = min(slice_s, left if left > 0 else 0.001)
            time.sleep(slice_s)
            now = time.monotonic()
            time_up = deadline is not None and now >= deadline
            if now - window_start >= 1.0:
                window_start = now
                log.print(
                    format_second("lower", watches["lower"].snapshot(), previous["lower"], lower.Matched())
                    + " | "
                    + format_second("upper", watches["upper"].snapshot(), previous["upper"], upper.Matched())
                    + "\n"
                    + format_second("main", watches["main"].snapshot(), previous["main"], main_nodes.Matched())
                    + " | "
                    + format_second("imu", watches["imu"].snapshot(), previous["imu"], imu.Matched())
                )
            if stop.is_set() or time_up:
                break

        matched = {
            "lower": lower.Matched(),
            "upper": upper.Matched(),
            "main": main_nodes.Matched(),
            "imu": imu.Matched(),
        }
        elapsed_ms = int((time.monotonic() - started) * 1000)
        session.Shutdown()
        log.print("======== 汇总 ========")
        log.print(f"运行时长 {elapsed_ms // 1000}.{elapsed_ms % 1000:03d} s")
        log.print("avg/max 是相邻帧间隔，单位微秒。>2ms 含 >5ms。")
        for name in ("lower", "upper", "main", "imu"):
            log.print(format_total(name, watches[name], matched[name]))
        log.print(f"终端输出已写入 {log.path}")
        return 0
    finally:
        session.Shutdown()
        if log is not None:
            log.close()


if __name__ == "__main__":
    raise SystemExit(main())
