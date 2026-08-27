from __future__ import annotations

import ctypes
import logging
import os
import re
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

from .certs import ensure_certificate
from .config import (
    DATABASE_PATH, LOG_DIR, MDNS_HOSTNAME, PROJECT_ROOT, SECRETS_DIR,
    SHARED_DATABASE_PATH, SHARED_SMB_HOST, SHARED_SMB_SHARE, SHARED_SMB_USER,
    STATE_DIR,
)
from .mdns import lan_ipv4
from .netwatch import NetworkChangeWatcher
from .platform import mount_share as mount_smb_share
from .sync import COPY_ACTIONS, SyncPlan, device_id, resolve
from .versioning import VersionManager, VersionSnapshot


LOGGER = logging.getLogger(__name__)


#: macOS 菜单栏项拉起的端口。80/443 在 macOS 上要 root，开发机不该为一个菜单栏图标
#: 去要管理员权限；本机 CA 的那套 TLS 材料也是给 Windows 生产实例签的。
MACOS_PORT = 8900
#: HTTPS 同理，443 也要 root，所以走 8443。
MACOS_TLS_PORT = 8443
#: 单击菜单栏/托盘图标打开本机的固定地址：macOS 是 `peach.local`，Windows 是
#: `peach-win.local`。macOS 上 80/443 由 pf 转到高位端口
#:（scripts/setup_macos_port80.sh）。
OPEN_URL = f"https://{MDNS_HOSTNAME}/"

#: LaunchAgent 的标签，和 `scripts/install_macos_agent.py` 里那个必须一致。
LAUNCH_AGENT_LABEL = "gg.lmd.peach.tray"

#: 改到这些路径就得重启托盘进程本身。托盘启动那一刻就把它们装进了内存，重启子服务
#: 追不上——「同步开发进度」之后菜单还是旧的，正是这个原因。
TRAY_SOURCES = (
    "src/peach/tray.py",
    "src/peach/menubar.py",
    "src/peach/versioning.py",
    "src/peach/sync.py",
    "src/peach/certs.py",
    "src/peach/netwatch.py",
    "src/peach/config.py",
    "pyproject.toml",
)


def tray_restart_required(changed_paths: tuple[str, ...]) -> bool:
    """这次更新动没动托盘自己的代码。"""
    return any(path in TRAY_SOURCES for path in changed_paths)


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
        run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        ledger_plan: Callable[[], SyncPlan] | None = None,
        mount_share: Callable[[], bool] | None = None,
    ) -> None:
        self.specs = specs
        self._popen = popen
        self._health_get = health_get
        self._run = run
        self._ledger_plan = ledger_plan or self._current_ledger_plan
        self._mount_share = mount_share or self._mount_shared_root
        self._owned: dict[str, subprocess.Popen] = {}
        self._logs: list[object] = []
        self._last_health: dict[str, tuple[bool, str]] = {
            spec.name: (False, "未检测") for spec in specs
        }
        self._lock = threading.RLock()

    def healthy(self, spec: ServiceSpec) -> bool:
        # trust_env=False：健康检查永远直连回环。代理客户端（Stash 等）会设置系统级
        # HTTP 代理，httpx 默认读它（urllib.getproxies 在 macOS 走系统配置），于是
        # 探测 http://127.0.0.1 的请求被送进代理、由代理回 503——服务明明活着，
        # 状态却显示「未运行」。实测 Stash 开着时就是这样，HTTPS 探测不受影响。
        try:
            response = self._health_get(
                spec.health_url, timeout=0.5, verify=spec.verify, trust_env=False,
            )
            ok = response.status_code == 200 and response.json().get("ok") is True
            detail = "" if ok else f"状态码 {response.status_code}"
        except (httpx.HTTPError, OSError, ValueError):
            ok, detail = False, "无响应"
        with self._lock:
            self._last_health[spec.name] = (ok, detail)
        return ok

    def status(self) -> str:
        """菜单里那一行状态：每个服务逐个点名，正常的和异常的都写出来。

        只说「未运行」或「部分运行」没法行动——HTTP 和 HTTPS 各自会因为端口占用、
        证书过期、pf 转发写错等完全不同的原因挂掉。异常的附带最近一次探测的失败原因。
        """
        with self._lock:
            parts = []
            for spec in self.specs:
                ok, detail = self._last_health[spec.name]
                state = "正常" if ok else f"异常（{detail}）" if detail else "异常"
                parts.append(f"{spec.name.upper()} {state}")
        return " · ".join(parts)

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

    def stop_owned(self, name: str | None = None) -> None:
        """停掉自己拉起来的服务。给 `name` 就只停那一个（证书重签后只需重启 HTTPS）。"""
        with self._lock:
            if name is None:
                processes = list(self._owned.values())
                self._owned.clear()
                stopped = [spec.name for spec in self.specs]
            else:
                process = self._owned.pop(name, None)
                processes = [process] if process is not None else []
                stopped = [name]
            for key in stopped:
                if key in self._last_health:
                    self._last_health[key] = (False, "已停止")
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
        if name is None:
            for handle in self._logs:
                handle.close()
            self._logs.clear()

    def restart(self) -> bool:
        self.stop_owned()
        self.start_missing()
        return self.wait_until_ready()

    @staticmethod
    def _current_ledger_plan() -> SyncPlan:
        return resolve(DATABASE_PATH, SHARED_DATABASE_PATH, device_id(STATE_DIR))

    @staticmethod
    def _mount_shared_root() -> bool:
        """把共享副本所在的盘挂回来；不是 macOS 或挂不上都返回 False。"""
        return mount_smb_share(SHARED_SMB_HOST, SHARED_SMB_SHARE, SHARED_SMB_USER)

    def _ledger_plan_after_mount(self) -> SyncPlan:
        """判定一次；共享盘没挂就补挂一次再判。

        macOS 重启后 SMB 共享不会自己回来，`offline` 因此是本机的日常状态而不是结论：
        在此之前菜单栏只能回一句「盘不可达」，而手动挂一下同一条同步链路立刻就通。
        挂不上时原样返回那个 offline 判定，调用方照旧降级到那条消息。
        只有 `offline` 才试挂载——判定已经通了还去碰挂载，是一次白跑的网络往返。
        """
        decision = self._ledger_plan()
        if decision.action != "offline" or not self._mount_share():
            return decision
        return self._ledger_plan()

    def _ledger_shortcut(self, *, take_ownership: bool) -> tuple[bool, str] | None:
        """这次同步会不会真的复制？不会就别停服务。

        原来的做法是无条件停服务、跑一遍 CLI、再启回来。共享盘没挂（`offline`）或者
        本机压根不是写入端（`conflict`）时，那一停一启换来的只有一次白白的停机和一条
        「同步失败」通知——实测就是本机的日常状态：`/Volumes/peach-sync` 没挂时，
        点一次「同步 Ledger」网页就断十几秒，然后告诉你盘不可达。

        「接管 Ledger 写入」只在共享盘不可达时短路：它要求两侧 `in-sync`，而 `in-sync`
        对同步是无事可做、对接管却正是要做的那一次。

        判定走 `_ledger_plan_after_mount`：`offline` 先当成「盘掉了」补挂一次再重判，
        真挂不上才落到下面这条降级消息。
        """
        try:
            decision = self._ledger_plan_after_mount()
        except OSError as exc:                     # 判定本身失败也不该拖着服务停机
            return False, f"未同步：无法判定账本状态（{exc}）"
        if take_ownership:
            if decision.action == "offline":
                return False, f"未接管：{decision.reason}；先挂上共享副本所在的盘。"
            return None
        if decision.action in COPY_ACTIONS:
            return None
        if decision.action in ("offline", "conflict", "missing"):
            return False, f"未同步：{decision.reason}"
        return True, f"账本同步：{decision.action} · {decision.reason}"

    def sync_ledger(
        self, executable: Path | None = None, *, take_ownership: bool = False,
    ) -> tuple[bool, str]:
        """停掉本托盘拥有的服务，单次同步后恢复；不碰别的进程拥有的服务。"""
        shortcut = self._ledger_shortcut(take_ownership=take_ownership)
        if shortcut is not None:
            return shortcut
        with self._lock:
            external = []
            for spec in self.specs:
                owned = self._owned.get(spec.name)
                if self.healthy(spec) and (owned is None or owned.poll() is not None):
                    external.append(spec.name.upper())
        if external:
            return False, f"未同步：{'/'.join(external)} 服务不归本托盘管理"

        peach = executable or _peach_executable()
        self.stop_owned()
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            command = [
                str(peach), "ledger-sync", "--db", str(DATABASE_PATH),
                "--shared-db", str(SHARED_DATABASE_PATH),
            ]
            if take_ownership:
                command.append("--take-ownership")
            sync_environment = os.environ.copy()
            # Windows 上 Python 的 stdout 被管道捕获时默认使用 ANSI code page
            #（简中系统是 GBK），而父进程按 UTF-8 解码。明确约定子进程输出 UTF-8，
            # 不能只锁定父进程的 decoding，否则中文通知会全部变成替换字符。
            sync_environment["PYTHONIOENCODING"] = "utf-8"
            result = self._run(
                command,
                cwd=str(PROJECT_ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", shell=False,
                env=sync_environment,
                creationflags=creationflags,
            )
            output = (result.stdout or result.stderr or "账本同步没有输出").strip()
            ok = result.returncode == 0
        except (OSError, subprocess.SubprocessError) as exc:
            ok, output = False, f"账本同步启动失败：{exc}"
        finally:
            self.start_missing()
            ready = self.wait_until_ready()
        if not ready:
            return False, f"{output}；服务未能在 20 秒内恢复"
        return ok, output


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
            (
                peach, "serve", "--host", "0.0.0.0", "--port", str(MACOS_PORT),
                "--no-ledger-sync",
            ),
            True,
        ),
    ]
    cert_dir = SECRETS_DIR / "tls"
    ca, cert, key = (cert_dir / n for n in
                     ("peach-local-ca.crt", "peach.crt", "peach.key"))
    if all(path.is_file() for path in (ca, cert, key)):
        specs.append(ServiceSpec(
            "https",
            # 健康检查走回环，不走局域网地址。走 `peach.local` 会先解析到本机的
            # 局域网 IP，那条路径要穿过 pf 的转发规则，连接慢到几秒、还会超时，
            # 于是服务在跑却被判成「未运行」。证书的 SAN 已经包含 127.0.0.1
            # （见 scripts/setup_local_tls.sh），主机名校验照样成立。
            f"https://127.0.0.1:{MACOS_TLS_PORT}/healthz",
            (
                peach, "serve", "--host", "0.0.0.0", "--port", str(MACOS_TLS_PORT),
                "--no-mdns", "--no-ledger-sync",
                "--ssl-certfile", str(cert), "--ssl-keyfile", str(key),
            ),
            str(ca),
        ))
    return tuple(specs)


def build_service_specs(
    lan_address: str | None = None,
    *,
    tls_dir: Path | None = None,
) -> tuple[ServiceSpec, ...]:
    if sys.platform == "darwin":
        return build_macos_service_specs()
    address = lan_address or os.environ.get("PEACH_LAN_ADDRESS") or lan_ipv4()
    peach = str(_peach_executable())
    cert_dir = Path(tls_dir) if tls_dir is not None else SECRETS_DIR / "tls"
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
            (
                peach, "serve", "--host", "0.0.0.0", "--port", "80",
                "--mdns-address", address, "--no-ledger-sync",
            ),
            True,
        ),
        ServiceSpec(
            "https",
            f"https://{address}/healthz",
            (
                peach, "serve", "--host", address, "--port", "443", "--no-mdns",
                "--no-ledger-sync",
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
        self._sync_lock = threading.Lock()
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
                pystray.MenuItem("同步 Ledger", self.sync_ledger),
                pystray.MenuItem("接管 Ledger 写入", self.take_ownership),
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

    def sync_ledger(self, icon=None, _item=None) -> None:
        self._run_ledger_action(icon, take_ownership=False)

    def take_ownership(self, icon=None, _item=None) -> None:
        self._run_ledger_action(icon, take_ownership=True)

    def _run_ledger_action(self, icon=None, *, take_ownership: bool) -> None:
        if not self._sync_lock.acquire(blocking=False):
            return
        tray_icon = icon or self.icon
        action = "接管写入" if take_ownership else "同步"
        tray_icon.notify(f"正在安全停止服务并{action}…", "Peach Ledger")

        def work() -> None:
            try:
                ok, message = self.manager.sync_ledger(take_ownership=take_ownership)
                tray_icon.update_menu()
                tray_icon.notify(message, "Peach Ledger" if ok else "Peach Ledger 同步失败")
            finally:
                self._sync_lock.release()

        threading.Thread(target=work, name="PeachLedgerAction", daemon=True).start()

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


def launchd_owns_this_process(
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    *, uid: int | None = None,
) -> bool:
    """本进程是不是 LaunchAgent 拉起的那一个。

    判据是 launchd 报的 pid 等于自己的 pid，不是「plist 存在」。`kickstart -k` 只重启
    launchd 名下那一份；托盘要是从终端跑起来的，kickstart 会在旁边**再**起一个，
    菜单栏上就出现两个桃子，而旧的那个还占着单实例锁。
    """
    if uid is None:
        getuid = getattr(os, "getuid", None)
        if getuid is None:
            return False
        uid = getuid()
    result = run(
        ["launchctl", "print", f"gui/{uid}/{LAUNCH_AGENT_LABEL}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        return False
    match = re.search(r"^\s*pid\s*=\s*(\d+)", result.stdout or "", re.MULTILINE)
    return match is not None and int(match.group(1)) == os.getpid()


def restart_tray_process(
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    *, uid: int | None = None,
) -> subprocess.CompletedProcess:
    """让 launchd 杀掉并重新拉起托盘。调用方必须先停掉自己拥有的服务。

    顺序不能反：先重启服务再 kickstart，新托盘会看到一组健康但不属于自己的服务，
    `_owned` 是空的，之后每次「同步 Ledger」都被自己的归属检查挡成
    「服务不归本托盘管理」。
    """
    if uid is None:
        getuid = getattr(os, "getuid", None)
        if getuid is None:
            raise OSError("launchd is unavailable on this platform")
        uid = getuid()
    return run(
        ["launchctl", "kickstart", "-k", f"gui/{uid}/{LAUNCH_AGENT_LABEL}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )


def run_macos_menu_bar(manager: "ServiceManager") -> None:
    """macOS 走原生菜单栏项。

    pystray 的 darwin 后端漏了 activation policy 和图标尺寸两件必需的事，补齐等于
    重写它那层封装，所以这里直接用 AppKit（见 `peach.menubar`）。Windows 继续走 pystray。
    """
    from .menubar import MenuBarApp

    versions = VersionManager()
    # 「同步开发进度」会把版本行写旧，所以标题读这个可变快照而不是闭包里那一份。
    # 不在标题里直接调 `inspect()`：它要开四次 git，而标题每 5 秒刷新一次。
    state: dict[str, VersionSnapshot] = {"snapshot": versions.inspect()}
    app: dict[str, object] = {}
    # 开发进度和账本共用一把锁：两者都会停服务，同时跑等于让两条路径抢同一组进程。
    action_lock = threading.Lock()

    def restart() -> None:
        manager.stop_owned()
        manager.start_missing()

    def quit_now() -> None:
        manager.stop_owned()
        holder = app.get("app")
        if holder is not None:
            holder.stop()

    def notify(message: str, title: str) -> None:
        holder = app.get("app")
        if holder is not None:
            holder.notify(message, title)

    def sync_source() -> None:
        """把本地检出快进到更新通道，再让新代码真的跑起来。

        和「同步 Ledger」分成两个按钮，因为它们除了名字里都有「同步」之外没有共同点：
        走的是 GitHub 而不是 SMB 共享，任一方不可达都不该拖住另一方（本机常态就是
        共享盘没挂而 GitHub 正常）；快进失败什么都没变，账本同步失败却牵涉唯一写入端
        和可能的数据取舍。合成一个按钮只会让「失败了」这句话失去意义。
        """
        if not action_lock.acquire(blocking=False):
            return

        def work() -> None:
            try:
                notify("正在检查更新通道…", "Peach 开发进度")
                result = versions.update()
                state["snapshot"] = result.snapshot
                if result.state != "updated":
                    notify(result.message, "Peach 开发进度")
                    return
                if tray_restart_required(result.changed_paths):
                    if launchd_owns_this_process():
                        notify(f"{result.message}正在重启菜单栏项…", "Peach 开发进度")
                        manager.stop_owned()
                        restarted = restart_tray_process()
                        if restarted.returncode != 0:
                            # kickstart 失败时旧进程仍在；把刚停掉的服务恢复，不能留下
                            # 一个有菜单图标却没有 HTTP/HTTPS 的半死状态。
                            manager.start_missing()
                            notify("代码已同步，但菜单栏项重启失败；服务已恢复。",
                                   "Peach 开发进度")
                        return
                    notify(
                        f"{result.message}服务已重启；菜单栏项本身要手动退出重开才会生效。",
                        "Peach 开发进度",
                    )
                    manager.restart()
                    return
                manager.restart()
                notify(f"{result.message}服务已重启。", "Peach 开发进度")
            finally:
                action_lock.release()

        threading.Thread(target=work, name="PeachSourceSync", daemon=True).start()

    def run_ledger_action(*, take_ownership: bool) -> None:
        if not action_lock.acquire(blocking=False):
            return

        def work() -> None:
            try:
                action = "接管写入" if take_ownership else "同步"
                notify(f"正在判定账本状态并{action}…", "Peach Ledger")
                ok, message = manager.sync_ledger(take_ownership=take_ownership)
                notify(message, "Peach Ledger" if ok else "Peach Ledger 同步失败")
            finally:
                action_lock.release()

        threading.Thread(target=work, name="PeachLedgerSync", daemon=True).start()

    def sync_ledger() -> None:
        run_ledger_action(take_ownership=False)

    def take_ownership() -> None:
        run_ledger_action(take_ownership=True)

    menu = MenuBarApp(
        create_icon(template=True),
        "Peach · 蜜桃",
        [
            ("打开 Peach", lambda: webbrowser.open(OPEN_URL)),
            (lambda: f"状态：{manager.status()}", None),
            (f"地址：{OPEN_URL}", None),
            (None, None),
            ("同步开发进度", sync_source),
            ("同步 Ledger", sync_ledger),
            ("接管 Ledger 写入", take_ownership),
            ("重启服务", restart),
            ("查看日志", lambda: subprocess.run(["open", str(LOG_DIR)], check=False)),
            (lambda: f"版本 {state['snapshot'].package_version}"
                     f" · {state['snapshot'].build_label}", None),
            (None, None),
            ("退出 Peach", quit_now),
        ],
    )
    app["app"] = menu

    # `manager.status()` 读的是 `healthy()` 写下的缓存。pystray 那条路径有 `_monitor`
    # 线程定时重采样，这条路径漏了，于是缓存永远停在启动那一刻——服务还没起来时测的
    # 那一次 False，菜单里就一直显示「未运行」。
    def poll_health() -> None:
        while not stopped.wait(5.0):
            for spec in manager.specs:
                manager.healthy(spec)

    def refresh_certificate() -> bool:
        """本机地址变了就补签证书并重启 HTTPS。成功返回 True。

        证书的 SAN 是签死的，而局域网地址随 DHCP 和换网络变化；地址一变，用 IP 访问就
        报证书无效。由系统的网络变化事件驱动，不轮询——换 Wi-Fi 的那一刻就跑。
        """
        try:
            reason = ensure_certificate(SECRETS_DIR / "tls", MDNS_HOSTNAME, {lan_ipv4()})
        except Exception:
            LOGGER.exception("证书自检失败")
            return False
        if reason is None:
            return True
        LOGGER.info("证书已重签（%s），重启 HTTPS 服务", reason)
        manager.stop_owned("https")
        manager.start_missing()
        return True

    #: 事件到达时网络往往还没就绪，必须配重试；纯事件驱动会在这里断掉。
    CERT_RETRY_DELAYS = (0.0, 5.0, 15.0, 45.0, 120.0)
    cert_lock = threading.Lock()

    def refresh_certificate_with_retry() -> None:
        """换网瞬间地址还没拿到，事件那一刻必然失败——之后没人再管就一直是旧证书。

        实测：一次换网连发 7 个事件，全部落在 `lan_ipv4()` 抛
        `no publishable LAN IPv4 address` 的窗口里，网络稳定后证书仍停在上一个网段。
        所以失败要按退避重试，而不是把间隔轮询加回来。
        """
        if not cert_lock.acquire(blocking=False):
            return                      # 已经有一轮在重试，事件重复到达不用叠加
        try:
            for delay in CERT_RETRY_DELAYS:
                if delay and stopped.wait(delay):
                    return
                if refresh_certificate():
                    return
            LOGGER.error("证书自检重试仍失败，等下一次网络变化再试")
        finally:
            cert_lock.release()

    def on_network_change() -> None:
        threading.Thread(
            target=refresh_certificate_with_retry, name="PeachCertRetry", daemon=True).start()

    stopped = threading.Event()
    threading.Thread(target=poll_health, name="PeachMenuHealth", daemon=True).start()
    # 启动时先对一次账，之后由网络变化事件驱动（失败按退避重试）。
    refresh_certificate_with_retry()
    watcher = NetworkChangeWatcher(on_network_change)
    watcher.start()
    try:
        menu.run()
    finally:
        stopped.set()
        watcher.stop()


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
