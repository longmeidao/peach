from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import httpx
import pystray
from PIL import Image, ImageDraw

from .config import LOG_DIR, PROJECT_ROOT, SECRETS_DIR, STATE_DIR
from .versioning import VersionManager


DEFAULT_LAN_ADDRESS = "192.168.50.162"
OPEN_URL = "https://peach.local/"


def enable_hidpi() -> str:
    """Enable native sharp Win32 menus before pystray creates any windows."""
    if os.name != "nt":
        return "not-windows"
    try:
        setter = ctypes.windll.user32.SetProcessDpiAwarenessContext
        setter.argtypes = [ctypes.c_void_p]
        setter.restype = ctypes.c_bool
        if setter(ctypes.c_void_p(-4)):  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            return "per-monitor-v2"
    except (AttributeError, OSError):
        pass
    try:
        result = ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        if result in (0, -2147024891):  # S_OK or E_ACCESSDENIED (already set)
            return "per-monitor"
    except (AttributeError, OSError):
        pass
    try:
        if ctypes.windll.user32.SetProcessDPIAware():
            return "system"
    except (AttributeError, OSError):
        pass
    return "unavailable"


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    health_url: str
    command: tuple[str, ...]
    verify: bool | str


class AlreadyRunning(RuntimeError):
    pass


class SingleInstance:
    """A process-lifetime Windows file lock for the interactive tray."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def acquire(self) -> None:
        if os.name != "nt":
            return
        import msvcrt

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("r+b") if self.path.exists() else self.path.open("w+b")
        if self.path.stat().st_size == 0:
            self._handle.write(b"0")
            self._handle.flush()
        self._handle.seek(0)
        try:
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            self._handle.close()
            self._handle = None
            raise AlreadyRunning("Peach tray is already running") from exc

    def close(self) -> None:
        if self._handle is None:
            return
        if os.name == "nt":
            import msvcrt

            self._handle.seek(0)
            try:
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        self._handle.close()
        self._handle = None


class ServiceManager:
    def __init__(
        self,
        specs: tuple[ServiceSpec, ...],
        *,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        health_get: Callable[..., httpx.Response] = httpx.get,
    ) -> None:
        self.specs = specs
        self._popen = popen
        self._health_get = health_get
        self._owned: dict[str, subprocess.Popen] = {}
        self._logs: list[object] = []
        self._last_health = {spec.name: False for spec in specs}
        self._lock = threading.RLock()

    def healthy(self, spec: ServiceSpec) -> bool:
        try:
            response = self._health_get(spec.health_url, timeout=0.5, verify=spec.verify)
            result = response.status_code == 200 and response.json().get("ok") is True
        except (httpx.HTTPError, OSError, ValueError):
            result = False
        with self._lock:
            self._last_health[spec.name] = result
        return result

    def status(self) -> str:
        with self._lock:
            results = [self._last_health[spec.name] for spec in self.specs]
        if all(results):
            return "运行中"
        if any(results):
            return "部分运行"
        return "未运行"

    def start_missing(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            for spec in self.specs:
                owned = self._owned.get(spec.name)
                if owned is not None and owned.poll() is None:
                    continue
                if self.healthy(spec):
                    continue
                stdout = (LOG_DIR / f"tray-{spec.name}.out.log").open("ab")
                stderr = (LOG_DIR / f"tray-{spec.name}.err.log").open("ab")
                self._logs.extend((stdout, stderr))
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                self._owned[spec.name] = self._popen(
                    list(spec.command),
                    cwd=str(PROJECT_ROOT),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    shell=False,
                    creationflags=creationflags,
                )

    def wait_until_ready(self, timeout: float = 20.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if all(self.healthy(spec) for spec in self.specs):
                return True
            time.sleep(0.25)
        return False

    def stop_owned(self) -> None:
        with self._lock:
            processes = list(self._owned.values())
            self._owned.clear()
            for spec in self.specs:
                self._last_health[spec.name] = False
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            if process.poll() is not None:
                continue
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        for handle in self._logs:
            handle.close()
        self._logs.clear()

    def restart(self) -> bool:
        self.stop_owned()
        self.start_missing()
        return self.wait_until_ready()


def _peach_executable() -> Path:
    sibling = Path(sys.executable).with_name("peach.exe")
    if sibling.is_file():
        return sibling
    candidate = PROJECT_ROOT / ".venv" / "Scripts" / "peach.exe"
    if candidate.is_file():
        return candidate
    raise FileNotFoundError("peach.exe is missing; reinstall the editable project")


def build_service_specs(lan_address: str | None = None) -> tuple[ServiceSpec, ...]:
    address = lan_address or os.environ.get("PEACH_LAN_ADDRESS", DEFAULT_LAN_ADDRESS)
    peach = str(_peach_executable())
    cert_dir = SECRETS_DIR / "tls"
    ca = cert_dir / "peach-local-ca.crt"
    cert = cert_dir / "peach.crt"
    key = cert_dir / "peach.key"
    missing = [path for path in (ca, cert, key) if not path.is_file()]
    if missing:
        raise FileNotFoundError("TLS material is missing: " + ", ".join(map(str, missing)))
    return (
        ServiceSpec(
            "http",
            "http://127.0.0.1/healthz",
            (peach, "serve", "--host", "0.0.0.0", "--port", "80", "--mdns-address", address),
            True,
        ),
        ServiceSpec(
            "https",
            f"https://{address}/healthz",
            (
                peach, "serve", "--host", address, "--port", "443", "--no-mdns",
                "--ssl-certfile", str(cert), "--ssl-keyfile", str(key),
            ),
            str(ca),
        ),
    )


def create_icon(size: int = 64) -> Image.Image:
    """Render a tray-sized counterpart of the web favicon with antialiasing."""
    canvas = size * 4
    scale = canvas / 64
    image = Image.new("RGBA", (canvas, canvas), (11, 11, 13, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, canvas - 1, canvas - 1), radius=14 * scale, fill=(11, 11, 13, 255))
    draw.ellipse((12 * scale, 23 * scale, 52 * scale, 57 * scale), fill=(246, 104, 118, 255))
    draw.ellipse((18 * scale, 18 * scale, 34 * scale, 52 * scale), fill=(255, 154, 118, 255))
    draw.ellipse((33 * scale, 12 * scale, 52 * scale, 25 * scale), fill=(95, 185, 95, 255))
    draw.line((32 * scale, 15 * scale, 29 * scale, 27 * scale), fill=(138, 90, 59, 255), width=max(1, round(2 * scale)))
    return image.resize((size, size), Image.Resampling.LANCZOS)


def show_message(title: str, message: str, *, error: bool = False) -> None:
    if os.name == "nt":
        flags = 0x10 if error else 0x40
        ctypes.windll.user32.MessageBoxW(None, message, title, flags)
    else:
        print(f"{title}: {message}")


class PeachTray:
    def __init__(self, manager: ServiceManager, versions: VersionManager | None = None) -> None:
        self.manager = manager
        self.versions = versions or VersionManager()
        self.version = self.versions.inspect()
        self._stop_event = threading.Event()
        self._restart_lock = threading.Lock()
        self._update_lock = threading.Lock()
        version_menu = pystray.Menu(
            pystray.MenuItem(lambda _item: f"Peach {self.version.package_version}", None, enabled=False),
            pystray.MenuItem(lambda _item: self.version.build_label, None, enabled=False),
            pystray.MenuItem(lambda _item: self.version.channel_label, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("检查更新", self.check_updates),
        )
        self.icon = pystray.Icon(
            "Peach",
            create_icon(),
            "Peach · 蜜桃",
            pystray.Menu(
                pystray.MenuItem("打开 Peach", self.open, default=True),
                pystray.MenuItem(lambda _item: f"状态：{self.manager.status()}", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("重启服务", self.restart),
                pystray.MenuItem("查看日志", self.open_logs),
                pystray.MenuItem("版本与更新", version_menu),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出 Peach", self.exit),
            ),
        )

    def open(self, _icon=None, _item=None) -> None:
        webbrowser.open(OPEN_URL)

    def restart(self, icon=None, _item=None) -> None:
        if not self._restart_lock.acquire(blocking=False):
            return

        def work() -> None:
            try:
                ready = self.manager.restart()
                if self._stop_event.is_set():
                    self.manager.stop_owned()
                    return
                (icon or self.icon).update_menu()
                if not ready:
                    (icon or self.icon).notify("服务未能在 20 秒内恢复，请查看日志。", "Peach")
            finally:
                self._restart_lock.release()

        threading.Thread(target=work, name="PeachRestart", daemon=True).start()

    def open_logs(self, _icon=None, _item=None) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(LOG_DIR)

    def check_updates(self, icon=None, _item=None) -> None:
        if not self._update_lock.acquire(blocking=False):
            return
        tray_icon = icon or self.icon
        tray_icon.notify("正在检查更新…", "Peach")

        def work() -> None:
            try:
                result = self.versions.check()
                self.version = result.snapshot
                tray_icon.update_menu()
                tray_icon.notify(result.message, "Peach 版本与更新")
            finally:
                self._update_lock.release()

        threading.Thread(target=work, name="PeachUpdate", daemon=True).start()

    def exit(self, icon=None, _item=None) -> None:
        self._stop_event.set()
        self.manager.stop_owned()
        (icon or self.icon).stop()

    def _monitor(self) -> None:
        while not self._stop_event.wait(10):
            for spec in self.manager.specs:
                self.manager.healthy(spec)
            self.icon.update_menu()

    def _setup(self, icon) -> None:
        icon.visible = True
        if self._startup_warning:
            icon.notify(self._startup_warning, "Peach")

    def run(self) -> None:
        self.manager.start_missing()
        self._startup_warning = None
        if not self.manager.wait_until_ready():
            self._startup_warning = "Peach 只启动了部分服务，请查看托盘状态和日志。"
        threading.Thread(target=self._monitor, name="PeachHealth", daemon=True).start()
        try:
            self.icon.run(setup=self._setup)
        finally:
            self._stop_event.set()


def main() -> int:
    enable_hidpi()
    instance = SingleInstance(STATE_DIR / "peach-tray.lock")
    manager = None
    try:
        instance.acquire()
    except AlreadyRunning:
        webbrowser.open(OPEN_URL)
        return 0
    try:
        manager = ServiceManager(build_service_specs())
        PeachTray(manager).run()
    except Exception as exc:
        show_message("Peach 启动失败", str(exc), error=True)
        return 1
    finally:
        if manager is not None:
            manager.stop_owned()
        instance.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
