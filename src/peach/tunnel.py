"""Cloudflare Quick Tunnel 的受控进程边界。

Peach 不实现 Cloudflare 协议，只负责三件事：为两种部署选正确的本机 origin，
把访问密码作为启动前置条件，以及在自己的服务生命周期内管理 ``cloudflared``。
Quick Tunnel 的随机地址只写进数据根的状态文件，不进入设置、账本或日志文档。
"""
from __future__ import annotations

import json
import ipaddress
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TextIO

from . import access


STATE_FILENAME = "cloudflare-tunnel.json"
LOG_FILENAME = "cloudflare-tunnel.log"
PID_FILENAME = "cloudflared.pid"
QUICK_URL_RE = re.compile(
    r"https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com(?:/[^\s]*)?",
    re.IGNORECASE,
)


class TunnelError(RuntimeError):
    """Tunnel 不能安全启动或已经异常退出。"""


@dataclass(frozen=True)
class TunnelOrigin:
    url: str
    origin_server_name: str = ""
    ca_path: Path | None = None


@dataclass(frozen=True)
class TunnelPlan:
    binary: Path
    origin: TunnelOrigin
    command: tuple[str, ...]


@dataclass(frozen=True)
class TunnelSnapshot:
    state: str = "stopped"
    url: str = ""
    error: str = ""
    pid: int | None = None
    started_at: str = ""


def state_path(state_dir: Path) -> Path:
    return Path(state_dir) / STATE_FILENAME


def log_path(log_dir: Path) -> Path:
    return Path(log_dir) / LOG_FILENAME


def extract_quick_url(line: str) -> str | None:
    """从 cloudflared 的普通/警告输出中提取随机入口。"""
    match = QUICK_URL_RE.search(line or "")
    return match.group(0).rstrip(".,);]") if match else None


def resolve_binary(
    configured: str = "",
    *,
    base_dir: Path | None = None,
    executable: Path | None = None,
    environ: dict[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> Path | None:
    """按显式配置、打包旁路、环境变量和 PATH 的顺序找 cloudflared。"""
    environ = os.environ if environ is None else environ
    candidates: list[Path] = []

    explicit = (environ.get("PEACH_CLOUDFLARED") or configured).strip()
    if explicit:
        candidates.append(Path(explicit).expanduser())

    package_dir = Path(executable).resolve().parent if executable else None
    if package_dir is None and getattr(sys, "frozen", False):
        package_dir = Path(sys.executable).resolve().parent
    if package_dir is not None:
        candidates.extend((
            package_dir / "cloudflared.exe",
            package_dir / "cloudflared",
            package_dir / "_internal" / "cloudflared.exe",
            package_dir / "_internal" / "cloudflared",
        ))
    if base_dir is not None:
        candidates.extend((Path(base_dir) / "cloudflared.exe", Path(base_dir) / "cloudflared"))

    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue

    for name in ("cloudflared.exe", "cloudflared"):
        found = which(name)
        if found:
            return Path(found).resolve()
    return None


def origin_for_config(
    config, *, standalone_mode: bool, lan_address: str | None = None,
    https_port: int | None = None,
) -> TunnelOrigin:
    """为源码托盘和独立包分别构造 origin。

    源码服务的 80 端口只是跳转口，不能拿来做 Tunnel origin；独立包则没有本机 TLS
    入口，使用回环 HTTP。Cloudflare edge 到浏览器仍然是 HTTPS。未显式传端口时，
    独立包取设置文件里的服务端口，源码取标准 HTTPS 端口。
    """
    if standalone_mode:
        port = config.server.port if https_port is None else https_port
        if type(port) is not int or not 1 <= port <= 65535:
            raise TunnelError(f"独立包 Tunnel 的 HTTP 端口无效：{port}")
        return TunnelOrigin(f"http://127.0.0.1:{port}")
    if https_port is None:
        https_port = 443
    address = (lan_address or "").strip()
    if not address:
        raise TunnelError("无法确定源码服务的局域网地址")
    try:
        parsed_address = ipaddress.ip_address(address)
    except ValueError as exc:
        raise TunnelError(f"源码 Tunnel 的局域网地址不是 IP：{address}") from exc
    hostname = config.server.mdns_name.strip().rstrip(".")
    if not hostname:
        raise TunnelError("源码服务没有配置 mDNS 名称")
    origin_name = hostname if hostname.endswith(".local") else f"{hostname}.local"
    ca = config.directory("secrets") / "tls" / "peach-local-ca.crt"
    if not ca.is_file():
        raise TunnelError(f"源码 Tunnel 需要项目 CA：{ca}")
    if type(https_port) is not int or not 1 <= https_port <= 65535:
        raise TunnelError(f"源码 Tunnel 的 HTTPS 端口无效：{https_port}")
    host = f"[{address}]" if parsed_address.version == 6 else address
    return TunnelOrigin(
        f"https://{host}:{https_port}", origin_server_name=origin_name, ca_path=ca,
    )


def _access_error(policy: dict, token: str) -> str | None:
    if policy.get("mode") == "locked":
        return "访问设置损坏，不能启动公网 Tunnel"
    if policy.get("mode") == "open":
        return "启动公网 Tunnel 前必须先设置访问密码"
    if policy.get("mode") not in {"password", "legacy"}:
        return "访问设置不是受支持的密码模式"
    if not token:
        return "缺少 Peach 内部访问令牌，不能启动公网 Tunnel"
    return None


def validate_access(access_path: Path | None, token: str) -> None:
    """公网入口只接受有第二道登录闸门的部署。"""
    policy = access.load(access_path)
    message = _access_error(policy, token)
    if message:
        raise TunnelError(message)


def build_command(binary: Path, origin: TunnelOrigin) -> tuple[str, ...]:
    """构造不带凭据的 Quick Tunnel 命令。"""
    command = [
        str(binary), "tunnel", "--url", origin.url,
        "--no-autoupdate", "--loglevel", "info", "--metrics", "127.0.0.1:0",
    ]
    if origin.origin_server_name:
        command.extend(("--origin-server-name", origin.origin_server_name))
    if origin.ca_path is not None:
        command.extend(("--origin-ca-pool", str(origin.ca_path)))
    return tuple(command)


def plan_for_config(
    config,
    *,
    access_path: Path | None,
    token: str,
    standalone_mode: bool,
    lan_address: str | None = None,
    https_port: int | None = None,
    tls_enabled: bool = True,
    executable: Path | None = None,
    environ: dict[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> TunnelPlan:
    """校验安全前置并返回可审阅的启动计划。"""
    validate_access(access_path, token)
    if not standalone_mode and not tls_enabled:
        raise TunnelError("源码 Tunnel 需要正在运行的 HTTPS 服务")
    tunnel_settings = getattr(config, "tunnel", None)
    binary = resolve_binary(
        getattr(tunnel_settings, "binary", ""),
        base_dir=Path(getattr(config, "data_root", ".")),
        executable=executable,
        environ=environ,
        which=which,
    )
    if binary is None:
        raise TunnelError(
            "找不到 cloudflared；请安装官方 cloudflared，或设置 PEACH_CLOUDFLARED"
        )
    origin = origin_for_config(
        config, standalone_mode=standalone_mode, lan_address=lan_address,
        https_port=https_port,
    )
    return TunnelPlan(binary=binary, origin=origin, command=build_command(binary, origin))


def _read_state(path: Path) -> TunnelSnapshot:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return TunnelSnapshot()
    except (OSError, ValueError, TypeError):
        return TunnelSnapshot(error="Tunnel 状态文件不可读")
    if not isinstance(data, dict):
        return TunnelSnapshot(error="Tunnel 状态文件格式错误")
    return TunnelSnapshot(
        state=str(data.get("state") or "stopped"),
        url=str(data.get("url") or ""),
        error=str(data.get("error") or ""),
        pid=int(data["pid"]) if isinstance(data.get("pid"), int) else None,
        started_at=str(data.get("started_at") or ""),
    )


def saved_snapshot(state_dir: Path) -> TunnelSnapshot:
    """读取状态文件；不把旧的 running 记录误报成当前进程仍在运行。"""
    saved = _read_state(state_path(state_dir))
    if saved.state in {"running", "starting"}:
        return TunnelSnapshot(state="stopped", error="上一次 Tunnel 已随服务停止")
    return saved


def _write_state(path: Path, snapshot: TunnelSnapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state": snapshot.state,
        "url": snapshot.url,
        "error": snapshot.error,
        "pid": snapshot.pid,
        "started_at": snapshot.started_at,
    }
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".cloudflare-tunnel-", suffix=".json",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class TunnelManager:
    """一个 Peach 服务进程拥有的一条 cloudflared 子进程。"""

    def __init__(
        self,
        state_dir: Path,
        log_dir: Path,
        *,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        wait_timeout: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.log_dir = Path(log_dir)
        self._popen = popen
        self._wait_timeout = wait_timeout
        self._clock = clock
        self._lock = threading.RLock()
        # Only one caller may perform the spawn-and-ready handshake at a time.
        # `snapshot()` and `stop()` remain available while Cloudflare is connecting.
        self._start_lock = threading.Lock()
        self._process: subprocess.Popen | None = None
        self._reader: threading.Thread | None = None
        self._url = ""
        self._error = ""
        self._started_at = ""
        self._ready = threading.Event()
        # A stopped child may still be draining its pipe while a new one starts.
        # The generation prevents that old reader from publishing a stale URL.
        self._generation = 0

    @property
    def state_file(self) -> Path:
        return state_path(self.state_dir)

    @property
    def log_file(self) -> Path:
        return log_path(self.log_dir)

    @property
    def pid_file(self) -> Path:
        return self.state_dir / PID_FILENAME

    @staticmethod
    def _process_pid(process: subprocess.Popen | None) -> int | None:
        value = getattr(process, "pid", None)
        return value if isinstance(value, int) and value > 0 else None

    @staticmethod
    def _process_alive(process: subprocess.Popen | None) -> bool:
        if process is None:
            return False
        try:
            return process.poll() is None
        except (AttributeError, OSError):
            return False

    def _pidfile_matches(self, process: subprocess.Popen | None) -> bool:
        """Accept only the pidfile written by the current cloudflared child."""
        try:
            value = self.pid_file.read_text(encoding="ascii").strip()
            pid = int(value)
        except (OSError, ValueError):
            return False
        process_pid = self._process_pid(process)
        return pid > 0 and (process_pid is None or pid == process_pid)

    @staticmethod
    def _terminate_process(process: subprocess.Popen | None) -> None:
        if process is None:
            return
        try:
            alive = process.poll() is None
        except (AttributeError, OSError):
            alive = False
        if not alive:
            return
        try:
            process.terminate()
            process.wait(timeout=8)
        except (AttributeError, OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=3)
            except (AttributeError, OSError, subprocess.TimeoutExpired):
                pass

    def _write_error(self, message: str) -> None:
        self._error = message
        try:
            _write_state(self.state_file, TunnelSnapshot(state="error", error=message))
        except OSError:
            # The process must still be stopped when the state directory is not writable.
            pass

    def snapshot(self) -> TunnelSnapshot:
        with self._lock:
            process = self._process
            if self._process_alive(process):
                return TunnelSnapshot(
                    state="running" if self._url and self._pidfile_matches(process) else "starting",
                    url=self._url, error=self._error, pid=self._process_pid(process),
                    started_at=self._started_at,
                )
            if process is not None and not self._process_alive(process):
                error = self._error or "cloudflared 已退出"
                return TunnelSnapshot(
                    state="error", url=self._url, error=error,
                    pid=self._process_pid(process), started_at=self._started_at,
                )
        # 服务重启后不复用旧进程；状态文件只用于给页面一个明确的 stopped/error 结论。
        return saved_snapshot(self.state_dir)

    def _read_output(
        self, stream: TextIO, process: subprocess.Popen, handle: TextIO, generation: int,
    ) -> None:
        try:
            for raw in iter(stream.readline, ""):
                line = str(raw).rstrip("\r\n")
                if line:
                    handle.write(line + "\n")
                    handle.flush()
                url = extract_quick_url(line)
                if url:
                    with self._lock:
                        if generation == self._generation:
                            self._url = url
                            self._ready.set()
        except (OSError, ValueError):
            pass
        finally:
            try:
                stream.close()
            except OSError:
                pass
            try:
                handle.close()
            except OSError:
                pass
            if generation == self._generation:
                self._ready.set()
                if not self._process_alive(process):
                    with self._lock:
                        if not self._url and not self._error:
                            self._error = "cloudflared 在取得入口前退出"
                        snapshot = TunnelSnapshot(
                            state="error", url=self._url, error=self._error,
                            pid=self._process_pid(process), started_at=self._started_at,
                        )
                    try:
                        _write_state(self.state_file, snapshot)
                    except OSError:
                        pass

    def start(self, plan: TunnelPlan) -> TunnelSnapshot:
        with self._start_lock:
            return self._start_impl(plan)

    def _start_impl(self, plan: TunnelPlan) -> TunnelSnapshot:
        with self._lock:
            if self._process_alive(self._process):
                return self.snapshot()
            self._generation += 1
            generation = self._generation
            self._url = ""
            self._error = ""
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._ready.clear()
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.pid_file.unlink(missing_ok=True)
            handle: TextIO | None = None
            process: subprocess.Popen | None = None
            try:
                # Open the log before spawning the child. If the data root is not
                # writable, no untracked cloudflared process may be left behind.
                handle = self.log_file.open("a", encoding="utf-8")
                process = self._popen(
                    [*plan.command, "--pidfile", str(self.pid_file)],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1,
                    shell=False,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                self._terminate_process(process)
                if handle is not None:
                    try:
                        handle.close()
                    except OSError:
                        pass
                message = f"cloudflared 启动失败：{exc}"
                self._generation += 1
                self._process = None
                self._reader = None
                self._ready.set()
                self._write_error(message)
                raise TunnelError(message) from exc
            self._process = process
            stream = process.stdout
            if stream is None:
                message = "cloudflared 没有输出通道"
                self._terminate_process(process)
                self._generation += 1
                self._process = None
                self._reader = None
                self._ready.set()
                if handle is not None:
                    try:
                        handle.close()
                    except OSError:
                        pass
                self._write_error(message)
                raise TunnelError(message)
            self._reader = threading.Thread(
                target=self._read_output, args=(stream, process, handle, generation),
                name="PeachCloudflared", daemon=True,
            )
            try:
                self._reader.start()
                _write_state(self.state_file, TunnelSnapshot(
                    state="starting", pid=self._process_pid(process),
                    started_at=self._started_at,
                ))
            except (OSError, RuntimeError) as exc:
                message = f"Tunnel 启动状态失败：{exc}"
                self._generation += 1
                self._process = None
                self._reader = None
                self._ready.set()
                self._terminate_process(process)
                if handle is not None:
                    try:
                        handle.close()
                    except OSError:
                        pass
                self._write_error(message)
                raise TunnelError(message) from exc

        deadline = self._clock() + self._wait_timeout
        while self._clock() < deadline:
            self._ready.wait(0.1)
            with self._lock:
                if not self._process_alive(self._process):
                    break
                if self._url and self._pidfile_matches(self._process):
                    break
                self._ready.clear()
        with self._lock:
            process = self._process
            url = self._url
            error = self._error
            alive = self._process_alive(process)
            connected = self._pidfile_matches(process)
        if not url or not alive or not connected:
            if alive:
                self.stop()
            message = error or (
                "cloudflared 未在限定时间内取得入口"
                if not url else "cloudflared 未在限定时间内连接到 Cloudflare 边缘"
            )
            self._write_error(message)
            raise TunnelError(message)
        snapshot = TunnelSnapshot(
            state="running", url=url, pid=self._process_pid(process),
            started_at=self._started_at,
        )
        try:
            _write_state(self.state_file, snapshot)
        except OSError as exc:
            message = f"Tunnel 状态写入失败：{exc}"
            self.stop()
            self._write_error(message)
            raise TunnelError(message) from exc
        return snapshot

    def stop(self) -> TunnelSnapshot:
        with self._lock:
            process = self._process
            reader = self._reader
            self._process = None
            self._reader = None
            self._generation += 1
            cleanup_generation = self._generation
            self._url = ""
            self._error = ""
            self._ready.set()
        self._terminate_process(process)
        if reader is not None and reader.is_alive():
            reader.join(timeout=1)
        snapshot = TunnelSnapshot(state="stopped")
        with self._lock:
            if self._generation != cleanup_generation or self._process is not None:
                return snapshot
            try:
                self.state_file.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                try:
                    _write_state(self.state_file, snapshot)
                except OSError:
                    pass
            try:
                self.pid_file.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
        return snapshot
