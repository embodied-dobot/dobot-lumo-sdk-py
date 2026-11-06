"""Dobot 机器人 Python SDK。"""

from ._load import native as _native

_module = _native()


def __getattr__(name):
    return getattr(_module, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_module)))
