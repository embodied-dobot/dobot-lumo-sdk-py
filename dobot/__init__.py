"""Dobot 机器人 Python SDK。"""

# 增加函数是次版本；修改已有函数的参数或返回值是主版本。
# 只有 Python 接口变了才改这里。C++ SDK 的版本看 cpp_sdk_version。
__version__ = "0.1.0"

from ._load import native as _native

_module = _native()
cpp_sdk_version = _module.cpp_sdk_version


def __getattr__(name):
    return getattr(_module, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_module)))
