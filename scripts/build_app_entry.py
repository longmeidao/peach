import ctypes
import os
import sys

from peach.cli import main as cli_main
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


if len(sys.argv) > 1 and sys.argv[1] in {"serve", "migrate"}:
    _prepare_console()
    raise SystemExit(cli_main())
raise SystemExit(tray_main())
