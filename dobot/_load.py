import importlib.util
import platform
import sys
from pathlib import Path

_module = None


def native():
    global _module
    if _module is not None:
        return _module
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            "当前扩展按 Python 3.12 编译。3.13 及以上要用 dobot-sdk-py-src 的同一份源码重新编译扩展。"
        )
    machine = platform.machine()
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "aarch64"
    else:
        raise RuntimeError(f"不支持的架构: {machine}")

    library = Path(__file__).resolve().parent / "native" / arch / "dobot_native.so"
    if not library.is_file():
        raise RuntimeError(f"缺少 {library}")
    spec = importlib.util.spec_from_file_location("dobot_native", library)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {library}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["dobot_native"] = module
    spec.loader.exec_module(module)
    _module = module
    return module
