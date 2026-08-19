from __future__ import annotations

import ctypes
import logging
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
from PIL import Image

from .config import LOG_DIR, PROJECT_ROOT, SECRETS_DIR, STATE_DIR
from .versioning import VersionManager


LOGGER = logging.getLogger(__name__)


DEFAULT_LAN_ADDRESS = "192.168.50.162"
#: macOS 菜单栏项拉起的端口。80/443 在 macOS 上要 root，开发机不该为一个菜单栏图标
#: 去要管理员权限；本机 CA 的那套 TLS 材料也是给 Windows 生产实例签的。
MACOS_PORT = 8900
#: HTTPS 同理，443 也要 root，所以走 8443。
MACOS_TLS_PORT = 8443
#: 单击菜单栏/托盘图标打开的地址。Windows 生产实例有本机 CA 的 HTTPS 和 80/443；
#: macOS 是开发环境，走非特权端口的 HTTP。
OPEN_URL = (
    f"http://127.0.0.1:{MACOS_PORT}/" if sys.platform == "darwin" else "https://peach.local/"
)


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
    """交互式托盘/菜单栏项的进程级单实例锁。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle = None

    def acquire(self) -> None:
        """进程生命周期内的单实例锁。

        Windows 用 `msvcrt.locking`，POSIX 用 `fcntl.flock`——两者都在进程退出时由
        内核释放，所以强杀之后不会留下一把解不开的锁。没有这层保护的话，菜单栏里会
        出现两个 Peach，各自再拉起一份服务去抢同一个端口。
        """
        if os.name == "nt":
            self._acquire_windows()
        else:
            self._acquire_posix()

    def _acquire_posix(self) -> None:
        import fcntl

        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise AlreadyRunning("Peach tray is already running") from exc
        self._handle = handle

    def _acquire_windows(self) -> None:
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
        environment = os.environ.copy()
        if getattr(sys, "frozen", False):
            # A frozen tray must not pass its one-file bootloader state to Peach.exe.
            environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
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
                    env=environment,
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


#: venv 里放可执行文件的目录与后缀。Windows 是 `Scripts\\peach.exe`，POSIX 是 `bin/peach`。
_BIN_DIR = "Scripts" if os.name == "nt" else "bin"
_EXECUTABLE = "peach.exe" if os.name == "nt" else "peach"


def _peach_executable() -> Path:
    if getattr(sys, "frozen", False):
        # 打包出来的托盘不是可移动的独立发行版：它仍然把服务进程的所有权交给项目 venv，
        # 因为 one-file bootloader 在本 Python 构建上再拉起一个 one-file 进程并不安全。
        # 逐级向上找 .venv，而不是写死 parents[2]——换个输出目录就不该整套失效。
        for parent in Path(sys.executable).resolve().parents:
            managed = parent / ".venv" / _BIN_DIR / _EXECUTABLE
            if managed.is_file():
                return managed
    sibling = Path(sys.executable).with_name(_EXECUTABLE)
    if sibling.is_file():
        return sibling
    candidate = PROJECT_ROOT / ".venv" / _BIN_DIR / _EXECUTABLE
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"{_EXECUTABLE} is missing; reinstall the editable project")


def build_macos_service_specs() -> tuple[ServiceSpec, ...]:
    """macOS 用非特权端口起 HTTP，有 TLS 材料时再加一个 HTTPS。

    80/443 在 macOS 上要 root，所以服务本身跑在 8900/8443，由 pf 把 80/443 转过去
    （`scripts/setup_macos_port80.sh`）。不钉 `--mdns-address`：这台机器会换网络，
    钉死等于换个 Wi-Fi 就打不开（见 `peach.mdns` 的地址复查）。

    证书缺失时**只是不起 HTTPS**，不像 Windows 那样直接报错——macOS 这份是开发环境，
    没有本机 CA 也应该能用。
    """
    peach = str(_peach_executable())
    specs = [
        ServiceSpec(
            "http",
            f"http://127.0.0.1:{MACOS_PORT}/healthz",
            (peach, "serve", "--host", "0.0.0.0", "--port", str(MACOS_PORT)),
            True,
        ),
    ]
    cert_dir = SECRETS_DIR / "tls"
    ca, cert, key = (cert_dir / n for n in
                     ("peach-local-ca.crt", "peach.crt", "peach.key"))
    if all(path.is_file() for path in (ca, cert, key)):
        specs.append(ServiceSpec(
            "https",
            # 证书签的是 `peach.local`，SAN 里的 IP 是 Windows 那台的，所以只能按名字校验。
            f"https://peach.local:{MACOS_TLS_PORT}/healthz",
            (
                peach, "serve", "--host", "0.0.0.0", "--port", str(MACOS_TLS_PORT),
                "--no-mdns",
                "--ssl-certfile", str(cert), "--ssl-keyfile", str(key),
            ),
            str(ca),
        ))
    return tuple(specs)


def build_service_specs(lan_address: str | None = None) -> tuple[ServiceSpec, ...]:
    if sys.platform == "darwin":
        return build_macos_service_specs()
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


def create_icon(size: int = 64, *, template: bool = False) -> Image.Image:
    """Load the shared square Peach brand asset at tray resolution.

    `template=True` 返回只有形状的单色版本：macOS 菜单栏图标必须是 template image，
    由系统按浅色/深色菜单栏自己反色。彩色图标不会跟着变——浅色菜单栏下那颗桃子会
    糊成一团。形状取自原图的 alpha 通道，颜色一律置黑。
    """
    resource = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "resources" / "peach-logo.png"
    if not resource.is_file():
        resource = PROJECT_ROOT / "resources" / "peach-logo.png"
    if not resource.is_file():
        raise FileNotFoundError(f"Peach logo is missing: {resource}")
    image = Image.open(resource).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    if not template:
        return image
    black = Image.new("RGBA", image.size, (0, 0, 0, 0))
    black.putalpha(image.getchannel("A"))
    return black


def apply_macos_template(icon) -> bool:
    """把菜单栏图标标成 template image。

    pystray 的 darwin 后端只做 `setImage_`，不调 `setTemplate_`，所以默认不会跟着
    系统外观反色。这里在图标已经创建之后补上；拿不到底层 NSImage 就安静跳过——
    菜单栏项本身仍然可用，只是不会自动反色。
    """
    if sys.platform != "darwin":
        return False
    image = getattr(icon, "_icon_image", None)
    setter = getattr(image, "setTemplate_", None)
    if setter is None:
        return False
    setter(True)
    return True


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
            # macOS 菜单栏要单色 template image，Windows 托盘要彩色品牌图。
            create_icon(template=sys.platform == "darwin"),
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
            os.startfile(LOG_DIR)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(LOG_DIR)], check=False)

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
        # 必须等图标真的创建出来才拿得到底层 NSImage，所以放在 setup 里而不是构造时。
        apply_macos_template(icon)
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


def run_macos_menu_bar(manager: "ServiceManager") -> None:
    """macOS 走原生菜单栏项。

    pystray 的 darwin 后端漏了 activation policy 和图标尺寸两件必需的事，补齐等于
    重写它那层封装，所以这里直接用 AppKit（见 `peach.menubar`）。Windows 继续走 pystray。
    """
    from .menubar import MenuBarApp

    versions = VersionManager()
    snapshot = versions.inspect()
    app: dict[str, object] = {}

    def restart() -> None:
        manager.stop_owned()
        manager.start_missing()

    def quit_now() -> None:
        manager.stop_owned()
        holder = app.get("app")
        if holder is not None:
            holder.stop()

    menu = MenuBarApp(
        create_icon(template=True),
        "Peach · 蜜桃",
        [
            ("打开 Peach", lambda: webbrowser.open(OPEN_URL)),
            (lambda: f"状态：{manager.status()}", None),
            (None, None),
            ("重启服务", restart),
            ("查看日志", lambda: subprocess.run(["open", str(LOG_DIR)], check=False)),
            (lambda: f"版本 {snapshot.package_version} · {snapshot.build_label}", None),
            (None, None),
            ("退出 Peach", quit_now),
        ],
    )
    app["app"] = menu
    menu.run()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
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
        manager.start_missing()
        if sys.platform == "darwin":
            run_macos_menu_bar(manager)
        else:
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
