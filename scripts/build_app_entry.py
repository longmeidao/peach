"""打包 EXE 的入口：第一个参数是 `peach` 子命令就走 CLI，否则起托盘。

判据必须从 `peach.cli.subcommands()` 现算。这里原来硬编码 `{"serve", "migrate"}`，
于是 `follow`、`ledger-sync` 在 EXE 里完全不可达，而且不报错——参数被当成托盘参数
吞掉，用户看到的是又起了一个托盘，不是「没有这个命令」。
"""
import ctypes
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.cli import main as cli_main
from peach.cli import subcommands
from peach.tray import main as tray_main

_ATTACH_PARENT_PROCESS = -1
_STD_OUTPUT_HANDLE = -11
_STD_ERROR_HANDLE = -12


def _open_std_handle(handle_id: int):
    try:
        handle = ctypes.windll.kernel32.GetStdHandle(handle_id)
        if not handle or handle == ctypes.c_void_p(-1).value:
            return None
        import msvcrt

        fd = msvcrt.open_osfhandle(handle, os.O_WRONLY)
        return os.fdopen(fd, "w", buffering=1, encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        return None


def _prepare_console() -> None:
    if os.name != "nt":
        return
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        ctypes.windll.kernel32.AttachConsole(_ATTACH_PARENT_PROCESS)
    except (AttributeError, OSError):
        pass
    devnull = open(os.devnull, "w", encoding="utf-8")
    sys.stdout = _open_std_handle(_STD_OUTPUT_HANDLE) or devnull
    sys.stderr = _open_std_handle(_STD_ERROR_HANDLE) or devnull


def cli_commands() -> frozenset[str]:
    return subcommands()


def wants_cli(argv: list[str]) -> bool:
    return len(argv) > 1 and argv[1] in cli_commands()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if wants_cli(argv):
        _prepare_console()
        return cli_main(argv[1:])
    return tray_main()


if __name__ == "__main__":
    raise SystemExit(main())
