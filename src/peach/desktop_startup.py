"""当前用户的 Peach 登录启动项：Windows 快捷方式与 macOS LaunchAgent。"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

from . import distribution, settings_file
from .appid import MACOS_LAUNCH_AGENT_LABEL
from .fsutil import atomic_write_text

_SHORTCUT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$peachInput = [Console]::In.ReadToEnd() | ConvertFrom-Json
$peachLinkPath = [IO.Path]::GetFullPath($peachInput.path)
if ([IO.Path]::GetExtension($peachLinkPath) -ne '.lnk') { throw 'Expected shortcut' }
$peachExists = Test-Path -LiteralPath $peachLinkPath -PathType Leaf
$peachShell = New-Object -ComObject WScript.Shell
if ($peachInput.action -eq 'read' -and -not $peachExists) {
  @{enabled=$false; target=''; arguments=''} | ConvertTo-Json -Compress
  exit 0
}
$peachLink = $peachShell.CreateShortcut($peachLinkPath)
if ($peachInput.action -ne 'read' -and $peachExists -and $peachLink.TargetPath -ne $peachInput.expected) {
  throw 'Startup shortcut belongs to another installation'
}
if ($peachInput.action -eq 'write') {
  $peachParent = Split-Path -Parent $peachLinkPath
  [IO.Directory]::CreateDirectory($peachParent) | Out-Null
  $peachLink.TargetPath = $peachInput.target
  $peachLink.Arguments = $peachInput.arguments
  $peachLink.WorkingDirectory = $peachInput.directory
  $peachLink.Description = 'Peach'
  $peachLink.WindowStyle = 7
  $peachLink.Save()
  $peachExists = $true
}
if ($peachInput.action -eq 'remove' -and $peachExists) {
  Remove-Item -LiteralPath $peachLinkPath
  $peachExists = $false
}
@{enabled=$peachExists; target=$peachLink.TargetPath; arguments=$peachLink.Arguments} | ConvertTo-Json -Compress
"""


def shortcut(action: str, path: Path, *, target: str = "", arguments: str = "", directory: str = "", expected: str = "") -> dict:
    encoded = base64.b64encode(_SHORTCUT_SCRIPT.encode("utf-16-le")).decode("ascii")
    # 和 folder_picker 相同：发行包使用 Windows 自带的 PowerShell，不要求用户安装 pwsh。
    shell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    result = subprocess.run([str(shell), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                            input=json.dumps(dict(action=action, path=str(path), target=target, arguments=arguments,
                                                  directory=directory, expected=expected)),
                            capture_output=True, text=True, encoding="utf-8", timeout=15,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)
    if result.returncode:
        # PowerShell 说的原因不能吞掉。只留「请检查权限」这一句时，Windows runner 上
        # 这一步失败了三次，而权限、`WScript.Shell` COM 不可用、路径没落地和扩展名
        # 校验不通过在消息里长得一模一样，谁都没法往下查。
        detail = next((line.strip() for line in
                       (result.stderr or result.stdout or "").splitlines()
                       if line.strip()), "")
        raise OSError("启动项未能保存，请检查当前用户的启动文件夹权限"
                      + (f"（PowerShell：{detail}）" if detail else ""))
    return json.loads(result.stdout.lstrip("\ufeff"))


def target(config, *, executable: Path | None = None) -> tuple[Path, list[str], Path]:
    if executable is not None or distribution.standalone():
        program = (executable or Path(sys.executable)).resolve()
        return program, ["--data-root", str(config.data_root.resolve())], program.parent
    if sys.platform == "win32":
        program = Path(sys.executable).with_name("pythonw.exe").resolve()
        bootstrap = ("import os,runpy;os.environ['PEACH_DATA_ROOT']=" + repr(str(config.data_root.resolve()))
                     + ";runpy.run_module('peach.tray',run_name='__main__')")
        return program, ["-c", bootstrap], settings_file.PROJECT_ROOT
    return settings_file.PROJECT_ROOT / ".venv/bin/peach-tray", [], settings_file.PROJECT_ROOT


def startup_directory() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup"


def windows_entry(config, program: Path) -> tuple[Path, dict]:
    directory = startup_directory()
    legacy = directory / "Peach.lnk"
    current = shortcut("read", legacy)
    if current["enabled"]:
        path = Path(current["target"]).resolve()
        owned = path == program.resolve() or (not distribution.standalone() and path.is_relative_to(settings_file.PROJECT_ROOT.resolve()))
        if owned:
            return legacy, current
    identity = hashlib.sha256(str(config.data_root.resolve()).casefold().encode()).hexdigest()[:12]
    path = directory / f"Peach-{identity}.lnk"
    current = shortcut("read", path)
    if current["enabled"] and Path(current["target"]).resolve() != program.resolve():
        raise ValueError("启动项属于另一份 Peach 安装")
    return path, current


def snapshot(config=None) -> dict:
    config = config or settings_file.load_config()
    if sys.platform not in {"win32", "darwin"}:
        return {"available": False, "enabled": False, "silent": True, "message": "此系统未提供登录自启入口"}
    try:
        preference = json.loads((config.directory("state") / "desktop-startup.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        preference = {"silent": True}
    try:
        program, _, _ = target(config)
        if sys.platform == "win32":
            _, entry = windows_entry(config, program)
            enabled = entry["enabled"]
            silent = "--show" not in entry.get("arguments", "") if enabled else bool(preference.get("silent", True))
        else:
            path = Path.home() / "Library/LaunchAgents" / f"{MACOS_LAUNCH_AGENT_LABEL}.plist"
            entry = plistlib.loads(path.read_bytes()) if path.is_file() else {}
            if entry.get("ProgramArguments") and Path(entry["ProgramArguments"][0]).resolve() != program.resolve():
                raise ValueError("启动项属于另一份 Peach 安装")
            enabled = bool(entry.get("RunAtLoad", False))
            silent = "--show" not in entry.get("ProgramArguments", []) if enabled else bool(preference.get("silent", True))
        return {"available": program.is_file(), "enabled": enabled, "silent": silent,
                "message": "" if program.is_file() else "未找到本机托盘入口"}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return {"available": False, "enabled": False, "silent": True, "message": "启动项状态未取得"}


def save(config, *, enabled: bool, silent: bool, executable: Path | None = None) -> dict:
    if type(enabled) is not bool or type(silent) is not bool:
        raise ValueError("启动选项必须为开或关")
    program, args, directory = target(config, executable=executable)
    if enabled and not program.is_file():
        raise ValueError("未找到本机托盘入口")
    args = [*args, "--silent" if silent else "--show"]
    if sys.platform == "win32":
        path, existing = windows_entry(config, program)
        shortcut("write" if enabled else "remove", path, target=str(program), arguments=subprocess.list2cmdline(args),
                 directory=str(directory), expected=existing.get("target", ""))
    elif sys.platform == "darwin":
        path = Path.home() / "Library/LaunchAgents" / f"{MACOS_LAUNCH_AGENT_LABEL}.plist"
        entry = plistlib.loads(path.read_bytes()) if path.is_file() else {}
        if entry.get("ProgramArguments") and Path(entry["ProgramArguments"][0]).resolve() != program.resolve():
            raise ValueError("启动项属于另一份 Peach 安装")
        entry.update(Label=MACOS_LAUNCH_AGENT_LABEL, ProgramArguments=[str(program), *args], RunAtLoad=enabled,
                     KeepAlive=False, ProcessType="Interactive", WorkingDirectory=str(directory))
        entry["EnvironmentVariables"] = {**entry.get("EnvironmentVariables", {}), "PEACH_DATA_ROOT": str(config.data_root),
                                         "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
        atomic_write_text(path, plistlib.dumps(entry).decode("utf-8"))
    else:
        raise ValueError("此系统未提供登录自启入口")
    atomic_write_text(config.directory("state") / "desktop-startup.json", json.dumps({"silent": silent}))
    return {"available": True, "enabled": enabled, "silent": silent, "message": ""}
