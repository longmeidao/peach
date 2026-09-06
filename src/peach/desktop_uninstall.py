"""独立 Windows 安装的卸载计划与托盘退出后的系统清理助手。"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from filelock import FileLock

from . import desktop_startup, distribution, settings_file, standalone_update
from .fsutil import atomic_write_text


def plan(config, *, delete_data: bool, program: Path | None = None) -> dict:
    if type(delete_data) is not bool:
        raise ValueError("请选择是否删除 Peach 数据")
    target = (program or Path(sys.executable).parent).resolve()
    root = config.data_root.resolve()
    if not (target / "_internal/standalone.txt").is_file() or not (target / "Peach.exe").is_file():
        raise ValueError("源码安装请先退出托盘，再手动移除项目；数据目录见下方")
    if len(target.parts) < 3 or target == Path.home().resolve() or (target / ".git").exists():
        raise ValueError("程序目录不适合自动卸载")
    if root.is_relative_to(target) or target.is_relative_to(root):
        raise ValueError("程序与数据目录重叠，请手动卸载")
    directories = [config.directory(key).resolve() for key in settings_file.DIRECTORY_KEYS] if delete_data else []
    if any(path.parent != root or path.is_symlink() or path.is_junction() for path in directories):
        raise ValueError("数据使用了外部或嵌套目录，请保留数据卸载后按目录清单手动清理")
    media = [Path(value).resolve() for group in (config.locations, config.mounts) for rows in group.values() for value in rows]
    for path in [target, *directories]:
        if any(item.is_relative_to(path) or path.is_relative_to(item) for item in media):
            raise ValueError("卸载目录与媒体目录重叠，请手动检查")
    files = [config.path.resolve(), root / "config.previous.toml", root / "config.pending.toml"] if delete_data else []
    return {"program": str(target), "data_root": str(root), "directories": [str(p) for p in directories],
            "files": [str(p) for p in files], "delete_data": delete_data}


def snapshot(config) -> dict:
    result = {"available": False, "message": "此系统请退出 Peach 后手动移除程序与数据目录", "data_root": str(config.data_root),
              "directories": [str(config.directory(key)) for key in settings_file.DIRECTORY_KEYS], "full_available": False}
    if sys.platform != "win32":
        return result
    try:
        if not distribution.standalone():
            raise ValueError("源码安装请先关闭开机自启并退出托盘，再手动移除项目与数据目录")
        plan(config, delete_data=False)
        result.update(available=True, message="")
        try:
            plan(config, delete_data=True)
            result["full_available"] = True
        except ValueError as exc:
            result["message"] = str(exc)
    except ValueError as exc:
        result["message"] = str(exc)
    return result


def request(config, delete_data: bool) -> dict:
    if not distribution.standalone() or sys.platform != "win32":
        raise ValueError(snapshot(config)["message"])
    if standalone_update.public().get("state") in standalone_update.ACTIVE | {"ready"}:
        raise ValueError("更新任务尚未结束，请完成后卸载")
    data = plan(config, delete_data=delete_data)
    path = config.directory("state") / "uninstall-request.json"
    with FileLock(str(path) + ".lock", timeout=0):
        atomic_write_text(path, json.dumps(dict(data, requested_at=time.time())), mode=0o600)
    return {"accepted": True, "message": "正在卸载，Peach 将退出。完成后可关闭此页。"}


# 系统助手从 stdin 接受数据，路径不拼进脚本文本；只清理计划中的目录。
_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$peachJob = [Console]::In.ReadToEnd() | ConvertFrom-Json
$peachProgram = [IO.Path]::GetFullPath($peachJob.program)
$peachData = [IO.Path]::GetFullPath($peachJob.data_root)
if (-not (Test-Path -LiteralPath (Join-Path $peachProgram '_internal/standalone.txt'))) { exit 2 }
if ($peachProgram.Length -lt 4 -or $peachProgram -eq $env:USERPROFILE) { exit 2 }
$peachProcess = Get-Process -Id $peachJob.pid -ErrorAction SilentlyContinue
if ($peachProcess -and -not $peachProcess.WaitForExit(90000)) { exit 3 }
foreach ($peachPath in @($peachJob.directories) + @($peachJob.files)) {
  if ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($peachPath)) -ne $peachData) { exit 2 }
}
try {
  function Test-PeachTree($peachNode) {
    $peachItem = Get-Item -LiteralPath $peachNode -Force
    if ($peachItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Directory contains a link; manual cleanup required' }
    if ($peachItem.PSIsContainer) {
      foreach ($peachChild in Get-ChildItem -LiteralPath $peachNode -Force) { Test-PeachTree $peachChild.FullName }
    }
  }
  foreach ($peachPath in @($peachJob.directories) + @($peachJob.files) + @($peachProgram)) {
    if (Test-Path -LiteralPath $peachPath) { Test-PeachTree $peachPath }
  }
  foreach ($peachPath in @($peachJob.directories) + @($peachJob.files) + @($peachProgram)) {
    if (Test-Path -LiteralPath $peachPath) {
      $peachItem = Get-Item -LiteralPath $peachPath -Force
      if ($peachItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Directory is a link' }
      Remove-Item -LiteralPath $peachPath -Recurse -Force
    }
  }
  if ($peachJob.delete_data -and (Test-Path -LiteralPath $peachData) -and -not (Get-ChildItem -LiteralPath $peachData -Force | Select-Object -First 1)) {
    Remove-Item -LiteralPath $peachData
  }
} catch {
  [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null
  [System.Windows.Forms.MessageBox]::Show('卸载未完成，请手动检查：' + $peachProgram + [Environment]::NewLine + $peachData, 'Peach') | Out-Null
  exit 1
}
"""


def poll(tray) -> None:
    if not distribution.standalone() or sys.platform != "win32":
        return
    config = settings_file.load_config()
    path = config.directory("state") / "uninstall-request.json"
    if not path.is_file() or not tray._action_lock.acquire(blocking=False):
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data["requested_at"] > 120:
            path.unlink()
            return
        checked = plan(config, delete_data=data["delete_data"])
        if any(data.get(key) != value for key, value in checked.items()):
            raise ValueError("配置已变更，请重新确认卸载")
        shell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        desktop_startup.save(config, enabled=False, silent=True)
        process = subprocess.Popen([str(shell), "-NoProfile", "-NonInteractive", "-EncodedCommand",
                                    base64.b64encode(_SCRIPT.encode("utf-16-le")).decode("ascii")],
                                   stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        process.stdin.write(json.dumps(dict(checked, pid=os.getpid())).encode("utf-8"))
        process.stdin.close()
        path.unlink()
        tray.exit()
    except Exception as exc:
        path.unlink(missing_ok=True)
        tray.icon.notify(f"卸载未能启动：{exc}", "Peach")
    finally:
        tray._action_lock.release()
