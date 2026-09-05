"""正常重启 Windows 托盘：发停止消息、等它自己退出、再启动并核对子服务。

绝不强杀。托盘退出时要自己关掉两个 `peach serve` 子进程，被强杀的话那两个进程会
变成没人管的孤儿，继续占着 80 和 443，下一份托盘于是永远起不来服务。
`swap_from` 让它在旧托盘退出后、新托盘启动前顺手换掉二进制，那是整条链路上唯一一个
目标文件没有进程持有的窗口。
"""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .windows_update import replace_with_retry, swap_tray_binary


WM_STOP = 0x0400 + 10  # pystray._util.win32.WM_STOP


@dataclass(frozen=True)
class TrayWindow:
    process_id: int
    handle: int


@dataclass(frozen=True)
class RestartResult:
    ok: bool
    message: str
    old_tray_pid: int | None = None
    new_tray_pid: int | None = None
    service_pids: tuple[int, ...] = ()
    swapped_from: str | None = None
    backup: str | None = None


def _normal_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def process_alive(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except OSError:
        return False
    return True


def _process_paths_and_parents() -> tuple[dict[int, str], dict[int, int]]:
    if os.name != "nt":
        raise OSError("Windows tray control is only available on Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    ]
    paths: dict[int, str] = {}
    parents: dict[int, int] = {}
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        more = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while more:
            process_id = int(entry.th32ProcessID)
            parents[process_id] = int(entry.th32ParentProcessID)
            handle = kernel32.OpenProcess(0x1000, False, process_id)
            if handle:
                try:
                    buffer = ctypes.create_unicode_buffer(32768)
                    length = wintypes.DWORD(len(buffer))
                    if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
                        paths[process_id] = buffer.value
                finally:
                    kernel32.CloseHandle(handle)
            more = bool(kernel32.Process32NextW(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    return paths, parents


def find_tray_windows(target: Path) -> tuple[TrayWindow, ...]:
    if os.name != "nt":
        return ()
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    paths, _parents = _process_paths_and_parents()
    target_key = _normal_path(target)
    found: list[TrayWindow] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]

    @callback_type
    def visit(window, _extra):
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(window, ctypes.byref(process_id))
        buffer = ctypes.create_unicode_buffer(512)
        user32.GetClassNameW(window, buffer, len(buffer))
        class_name = buffer.value
        if (class_name.startswith("Peach") and class_name.endswith("SystemTrayIcon")
                and _normal_path(paths.get(int(process_id.value), "")) == target_key):
            found.append(TrayWindow(int(process_id.value), int(window)))
        return True

    ctypes.set_last_error(0)
    if not user32.EnumWindows(visit, 0):
        error = ctypes.get_last_error()
        if error:
            raise ctypes.WinError(error)
    return tuple(found)


def post_stop(window_handle: int) -> bool:
    if os.name != "nt":
        return False
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    return bool(user32.PostMessageW(window_handle, WM_STOP, 0, 0))


def owned_service_pids(tray_process_id: int, service_executable: Path) -> tuple[int, ...]:
    paths, parents = _process_paths_and_parents()
    service_key = _normal_path(service_executable)

    def descends_from(process_id: int) -> bool:
        seen: set[int] = set()
        parent = parents.get(process_id, 0)
        while parent and parent not in seen:
            if parent == tray_process_id:
                return True
            seen.add(parent)
            parent = parents.get(parent, 0)
        return False

    return tuple(sorted(
        process_id for process_id, path in paths.items()
        if _normal_path(path) == service_key and descends_from(process_id)
    ))


def start_tray(target: Path) -> subprocess.Popen:
    environment = os.environ.copy()
    environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    return subprocess.Popen(
        [str(target)], cwd=str(target.parent), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False,
        env=environment, creationflags=creationflags,
    )


def _rolled_back(
    backup: Path,
    target: Path,
    *,
    start: Callable[[Path], subprocess.Popen],
    sleep: Callable[[float], None],
    message: str,
    old_tray_pid: int | None,
    swapped_from: str | None,
) -> RestartResult:
    """新二进制起不来就把备份换回去再开一次，别把机器留在没有托盘的状态。

    备份先复制成临时名再 `os.replace`：直接把备份本身换回去的话，回滚成功了
    `dist/Peach/` 里那份可回退的副本也没了，下一次失败就无处可退。
    """
    restore = target.with_name(".Peach.rollback.exe")
    try:
        shutil.copy2(backup, restore)
        replace_with_retry(restore, target, sleep=sleep)
    except OSError as exc:
        return RestartResult(False, f"{message}；回滚失败，生产入口停在新二进制：{exc}",
                             old_tray_pid=old_tray_pid, swapped_from=swapped_from,
                             backup=str(backup))
    started = start(target)
    if started.poll() is not None:
        return RestartResult(False, f"{message}；已回滚到备份，但旧托盘也没起来",
                             old_tray_pid=old_tray_pid, swapped_from=swapped_from,
                             backup=str(backup))
    return RestartResult(False, f"{message}；已回滚到备份并重开旧托盘",
                         old_tray_pid=old_tray_pid, swapped_from=swapped_from,
                         backup=str(backup))


def restart_tray(
    target: Path,
    *,
    timeout: float = 25.0,
    swap_from: Path | None = None,
    find_windows: Callable[[Path], tuple[TrayWindow, ...]] = find_tray_windows,
    stop_window: Callable[[int], bool] = post_stop,
    alive: Callable[[int], bool] = process_alive,
    start: Callable[[Path], subprocess.Popen] = start_tray,
    services: Callable[[int, Path], tuple[int, ...]] = owned_service_pids,
    swap: Callable[[Path, Path], Path] = swap_tray_binary,
    sleep: Callable[[float], None] = time.sleep,
) -> RestartResult:
    target = target.resolve()
    service_executable = target.parents[2] / ".venv" / "Scripts" / "peach.exe"
    if not target.is_file() or target.name.lower() != "peach.exe":
        return RestartResult(False, f"拒绝重启：入口不存在或不是 Peach.exe：{target}")
    if not service_executable.is_file():
        return RestartResult(False, f"拒绝重启：服务入口不存在：{service_executable}")

    windows = find_windows(target)
    process_ids = {window.process_id for window in windows}
    if len(process_ids) != 1 or not windows:
        return RestartResult(False, "拒绝重启：没有找到唯一且路径匹配的 Peach 托盘窗口")
    old_process_id = next(iter(process_ids))
    if not all(stop_window(window.handle) for window in windows):
        return RestartResult(False, "托盘停止消息发送失败", old_tray_pid=old_process_id)

    deadline = time.monotonic() + timeout
    while alive(old_process_id) and time.monotonic() < deadline:
        sleep(0.1)
    if alive(old_process_id):
        return RestartResult(False, "托盘未在期限内正常退出；未强杀、未另启", old_tray_pid=old_process_id)

    backup: Path | None = None
    if swap_from is not None:
        try:
            backup = swap(swap_from.resolve(), target)
        except (OSError, ValueError) as exc:
            started = start(target)
            message = f"换二进制失败，已按原样重开旧托盘：{exc}"
            if started.poll() is not None:
                message = f"换二进制失败，且旧托盘未能重开：{exc}"
            return RestartResult(False, message, old_tray_pid=old_process_id,
                                 swapped_from=str(swap_from))

    swapped_from = str(swap_from) if swap_from is not None else None
    backup_path = str(backup) if backup is not None else None
    # 停和起各拿一份完整预算：换一份 40 MB 的 EXE 要几秒，那几秒不该从新托盘的
    # 启动窗口里扣掉，否则带 --swap-from 的这条路比不带的更容易假超时。
    deadline = time.monotonic() + timeout
    launched = start(target)
    while time.monotonic() < deadline:
        if launched.poll() is not None:
            if backup is not None:
                return _rolled_back(
                    backup, target, start=start, sleep=sleep,
                    message=f"新托盘退出，代码 {launched.returncode}",
                    old_tray_pid=old_process_id, swapped_from=swapped_from)
            return RestartResult(False, f"新托盘退出，代码 {launched.returncode}", old_tray_pid=old_process_id)
        new_windows = find_windows(target)
        new_process_ids = {window.process_id for window in new_windows}
        if len(new_process_ids) == 1:
            new_process_id = next(iter(new_process_ids))
            service_pids = services(new_process_id, service_executable)
            if len(service_pids) >= 2:
                return RestartResult(
                    True, "托盘已正常重启并重新拥有 HTTP/HTTPS 子服务",
                    old_tray_pid=old_process_id, new_tray_pid=new_process_id,
                    service_pids=service_pids, swapped_from=swapped_from,
                    backup=backup_path,
                )
        sleep(0.2)
    if backup is not None:
        return _rolled_back(
            backup, target, start=start, sleep=sleep,
            message="新托盘或两个子服务未在期限内就绪",
            old_tray_pid=old_process_id, swapped_from=swapped_from)
    return RestartResult(False, "新托盘或两个子服务未在期限内就绪", old_tray_pid=old_process_id)
