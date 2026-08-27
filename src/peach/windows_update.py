from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


WINDOWS_TRAY_INPUTS = (
    "src/peach/",
    "scripts/build_app_entry.py",
    "scripts/build_windows.ps1",
    "scripts/replace_windows_tray.py",
    "web/",
    "migrations/",
    "resources/",
    "pyproject.toml",
)


def windows_tray_rebuild_required(changed_paths: tuple[str, ...]) -> bool:
    """The frozen Windows entry must carry every packaged runtime input."""
    return any(
        path == prefix or path.startswith(prefix)
        for path in changed_paths
        for prefix in WINDOWS_TRAY_INPUTS
    )


@dataclass(frozen=True)
class PendingWindowsUpdate:
    commit: str
    changed_paths: tuple[str, ...]


@dataclass(frozen=True)
class WindowsUpdatePreparation:
    state: str
    message: str


class WindowsUpdateInstaller:
    """Test an updated checkout and stage a recoverable Windows tray replacement."""

    def __init__(
        self,
        root: Path,
        *,
        state_dir: Path,
        log_dir: Path,
        current_executable: Path | None = None,
        run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        powershell: str | None = None,
        frozen: bool | None = None,
        process_id: int | None = None,
    ) -> None:
        self.root = root.resolve()
        self.state_dir = state_dir.resolve()
        self.log_dir = log_dir.resolve()
        self.current_executable = Path(current_executable or sys.executable).resolve()
        self._run = run
        self._popen = popen
        self._powershell = powershell
        self._frozen = (
            bool(getattr(sys, "frozen", False)) and os.name == "nt"
            if frozen is None else frozen
        )
        self._process_id = os.getpid() if process_id is None else process_id
        self.pending_path = self.state_dir / "windows-source-sync.json"
        self.log_path = self.log_dir / "windows-source-sync.log"

    def mark_pending(self, commit: str, changed_paths: tuple[str, ...]) -> None:
        self.pending_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.pending_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"commit": commit, "changed_paths": list(changed_paths)},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temporary, self.pending_path)

    def pending(self) -> PendingWindowsUpdate | None:
        try:
            payload = json.loads(self.pending_path.read_text(encoding="utf-8"))
            commit = str(payload["commit"])
            changed = tuple(str(path) for path in payload["changed_paths"])
        except (OSError, ValueError, KeyError, TypeError):
            return None
        return PendingWindowsUpdate(commit, changed)

    def clear_pending(self) -> None:
        self.pending_path.unlink(missing_ok=True)

    def _powershell_executable(self) -> str | None:
        if self._powershell:
            return self._powershell
        for name in ("pwsh.exe", "pwsh", "powershell.exe", "powershell"):
            found = shutil.which(name)
            if found:
                return found
        known = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")
        return str(known) if known.is_file() else None

    def _run_logged(self, command: list[str], *, append: bool = True) -> int:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with self.log_path.open(mode, encoding="utf-8", errors="replace") as log:
            log.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {' '.join(command)}\n")
            log.flush()
            result = self._run(
                command,
                cwd=str(self.root),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        return result.returncode

    def prepare(
        self, commit: str, changed_paths: tuple[str, ...],
    ) -> WindowsUpdatePreparation:
        shell = self._powershell_executable()
        if shell is None:
            return WindowsUpdatePreparation(
                "failed", "代码已快进，但找不到 PowerShell，未运行测试或重启服务。",
            )

        test_script = self.root / "scripts" / "test.ps1"
        test_exit = self._run_logged(
            [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(test_script)],
            append=False,
        )
        if test_exit != 0:
            return WindowsUpdatePreparation(
                "failed", "代码已快进，但完整测试失败；服务与托盘均未重启，请查看日志。",
            )

        if not windows_tray_rebuild_required(changed_paths):
            return WindowsUpdatePreparation("services", "代码与完整测试已通过。")

        if not self._frozen:
            return WindowsUpdatePreparation(
                "services-manual-tray",
                "代码与完整测试已通过；当前不是打包托盘，托盘进程需手动重开。",
            )

        if not self.current_executable.is_file():
            return WindowsUpdatePreparation(
                "failed", "代码与测试已通过，但找不到当前托盘 EXE，未执行替换。",
            )

        staging_dir = self.state_dir / "source-sync-build" / commit
        staging_dir.mkdir(parents=True, exist_ok=True)
        staged = staging_dir / "Peach.exe"
        staged.unlink(missing_ok=True)
        build_script = self.root / "scripts" / "build_windows.ps1"
        build_exit = self._run_logged([
            shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(build_script),
            "-OutputDirectory", str(staging_dir),
        ])
        if build_exit != 0 or not staged.is_file():
            return WindowsUpdatePreparation(
                "failed", "代码与测试已通过，但新托盘构建失败；旧托盘和服务保持运行。",
            )

        reset_environment = os.environ.copy()
        reset_environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        with self.log_path.open("a", encoding="utf-8", errors="replace") as log:
            validation = self._run(
                [str(staged), "migrate", "status"],
                cwd=str(self.root), stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, check=False, env=reset_environment,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        if validation.returncode != 0:
            return WindowsUpdatePreparation(
                "failed", "新托盘未通过打包迁移资源检查；旧托盘和服务保持运行。",
            )

        backup = self.current_executable.with_name(
            f"Peach.pre-source-sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}.exe"
        )
        shutil.copy2(self.current_executable, backup)
        helper_python = self.root / ".venv" / "Scripts" / "pythonw.exe"
        helper_script = self.root / "scripts" / "replace_windows_tray.py"
        if not helper_python.is_file() or not helper_script.is_file():
            return WindowsUpdatePreparation(
                "failed", "新托盘已构建，但替换助手不完整；旧托盘和服务保持运行。",
            )

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        try:
            self._popen(
                [
                    str(helper_python), str(helper_script),
                    "--wait-pid", str(self._process_id),
                    "--staged", str(staged),
                    "--target", str(self.current_executable),
                    "--backup", str(backup),
                    "--pending", str(self.pending_path),
                    "--log", str(self.log_path),
                ],
                cwd=str(self.root), stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                shell=False, creationflags=creationflags,
            )
        except OSError:
            return WindowsUpdatePreparation(
                "failed", "新托盘已构建，但替换助手启动失败；旧托盘和服务保持运行。",
            )
        return WindowsUpdatePreparation(
            "replace", "代码、完整测试和新托盘检查均已通过；正在安全替换并重启。",
        )
