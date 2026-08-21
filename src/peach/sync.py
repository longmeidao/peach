"""本地工作副本与专用共享副本之间的单写者复制。

刻意**不是**多主实时同步。SQLite 没有安全的自动三方合并：两台机器各自写过
之后，没有任何规则能把「看过 / 喜欢 / 标签」这类断言合成一份而不丢东西。
这里做的是单用户场景下能做到、且不会悄悄丢数据的那种：

- 共享副本只负责传输，两台机器各持一份本地工作副本；
- 启动时比对世代：共享副本更新就拉取，本地更新就保留，**两边都动过就拒绝自动合并**，
  进只读并报冲突，由人来选一边；
- 运行中定期回写共享副本，所以同一时刻只有一台在写；
- 同步点不可达时本地照常运行，恢复后再同步。

世代号只表示血缘先后，不表示时间：时钟在两台机器上不可靠，尤其 exFAT 只有
2 秒精度的本地时间戳。

复制一律走 SQLite 的 backup API，不复制文件：账本是 WAL 模式，直接拷 `.db`
会漏掉 `-wal` 里已提交但未 checkpoint 的事务，拷完还可能和目标残留的 `-wal`
拼成一个已经损坏的库。
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import tempfile
import threading
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from .platform import root_online


LOGGER = logging.getLogger(__name__)

#: 回写间隔。够短，崩溃时丢的是几十秒的浏览行为；够长，不会一直碾 USB 盘。
PUSH_INTERVAL_SECONDS = 60


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Marker:
    """一份副本的血缘与指纹。

    `generation`/`device` 是血缘，两份副本同源时相等；`size`/`mtime_ns` 是**相邻那个
    库文件**在写下标记那一刻的指纹，用来判断这份副本之后有没有被本机写过。
    """

    generation: int
    device: str
    written_at: str
    size: int
    mtime_ns: int

    def as_json(self) -> str:
        return json.dumps(
            {
                "generation": self.generation,
                "device": self.device,
                "written_at": self.written_at,
                "size": self.size,
                "mtime_ns": self.mtime_ns,
            },
            ensure_ascii=False,
            indent=2,
        )


@dataclass(frozen=True)
class SyncPlan:
    """启动时的判定结果。`action` 决定接下来做什么，`reason` 是给人看的。"""

    action: str          # disabled / offline / missing / pull / push / local-ahead / in-sync / conflict
    reason: str
    local_generation: int = 0
    shared_generation: int = 0

    @property
    def conflict(self) -> bool:
        return self.action == "conflict"


def marker_path(db_path: Path) -> Path:
    return db_path.with_name(db_path.name + ".sync.json")


def fingerprint(db_path: Path) -> tuple[int, int] | None:
    try:
        stat = db_path.stat()
    except OSError:
        return None
    return stat.st_size, stat.st_mtime_ns


def read_marker(db_path: Path) -> Marker | None:
    try:
        raw = json.loads(marker_path(db_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        return Marker(
            generation=int(raw["generation"]),
            device=str(raw["device"]),
            written_at=str(raw.get("written_at", "")),
            size=int(raw.get("size", -1)),
            mtime_ns=int(raw.get("mtime_ns", -1)),
        )
    except (KeyError, TypeError, ValueError):
        return None


def write_marker(db_path: Path, marker: Marker) -> Marker:
    """把标记写到库文件旁边，指纹按落盘后的实际状态重算。"""
    current = fingerprint(db_path)
    if current is not None:
        marker = replace(marker, size=current[0], mtime_ns=current[1])
    target = marker_path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(marker.as_json(), encoding="utf-8")
    os.replace(temporary, target)
    return marker


def device_id(state_dir: Path) -> str:
    """本机标识。只用来说明「这一代是谁写的」，不参与任何权限判断。"""
    path = state_dir / "device-id"
    try:
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except OSError:
        pass
    generated = f"{os.uname().nodename if hasattr(os, 'uname') else 'host'}-{uuid.uuid4().hex[:8]}"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generated, encoding="utf-8")
    except OSError:
        LOGGER.warning("无法保存 device-id，本次运行使用临时标识")
    return generated


def local_dirty(db_path: Path, marker: Marker | None) -> bool:
    """这份副本在上次标记之后有没有被写过。"""
    current = fingerprint(db_path)
    if current is None:
        return False
    if marker is None:
        return True
    return current != (marker.size, marker.mtime_ns)


def copy_database(source: Path, target: Path) -> None:
    """用 backup API 生成一致快照，再原子替换目标。

    不能让 SQLite 直接把目标连接开在 SMB 上：macOS 的 smbfs 目录可普通写入，SQLite
    却可能因锁或事务侧文件失败而报 ``unable to open database file``。先在本机临时目录
    生成已关闭的独立快照，再传到目标旁边原子替换；复制的不是活跃数据库文件，所以不会
    漏掉源库 WAL 中已提交的事务。
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, snapshot_name = tempfile.mkstemp(prefix="peach-ledger-", suffix=".db")
    os.close(descriptor)
    snapshot = Path(snapshot_name)
    transfer = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        origin = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        try:
            destination = sqlite3.connect(snapshot)
            try:
                origin.backup(destination)
            finally:
                destination.close()
        finally:
            origin.close()
        shutil.copyfile(snapshot, transfer)
        # Windows 的 FlushFileBuffers 需要可写句柄；只读句柄上调用 fsync 会返回
        # ``OSError: [Errno 9] Bad file descriptor``。这里同步的是刚写完、尚未发布
        # 的临时快照，使用读写句柄不会改变内容。
        with transfer.open("r+b") as handle:
            os.fsync(handle.fileno())
        # 旧副本的 sidecar 不能和新快照拼在一起。同步调用方保证目标没有服务在写。
        for suffix in ("-wal", "-shm", "-journal"):
            Path(f"{target}{suffix}").unlink(missing_ok=True)
        os.replace(transfer, target)
    finally:
        snapshot.unlink(missing_ok=True)
        transfer.unlink(missing_ok=True)


def plan(local: Path, shared: Path) -> SyncPlan:
    """只读判定，不碰任何文件。"""
    if local == shared or local.resolve() == shared.resolve():
        return SyncPlan("disabled", "本机直接使用共享副本，不需要复制")
    if not root_online(shared.parent):
        return SyncPlan("offline", "共享副本所在的盘不可达，本地照常读写")

    local_exists, shared_exists = local.is_file(), shared.is_file()
    if not shared_exists and not local_exists:
        return SyncPlan("missing", "两侧都没有账本")
    if not shared_exists:
        return SyncPlan("push", "共享副本不存在，用本地副本播种")
    if not local_exists:
        return SyncPlan("pull", "本地副本不存在，从共享副本拉取")

    local_marker, shared_marker = read_marker(local), read_marker(shared)
    dirty = local_dirty(local, local_marker)
    local_generation = local_marker.generation if local_marker else 0
    shared_generation = shared_marker.generation if shared_marker else 0

    if local_marker is None or shared_marker is None:
        # 没有血缘可比，两份都有数据。这种情况只能人来选，自动挑一边就是丢数据。
        return SyncPlan(
            "conflict", "缺少同步标记，无法判断两份账本的先后",
            local_generation, shared_generation,
        )
    if shared_generation > local_generation:
        if dirty:
            return SyncPlan(
                "conflict",
                f"共享副本已到第 {shared_generation} 代，本地仍是第 {local_generation} 代"
                f"且有未回写的改动",
                local_generation, shared_generation,
            )
        return SyncPlan("pull", "共享副本更新", local_generation, shared_generation)
    if shared_generation < local_generation:
        return SyncPlan("push", "本地副本更新", local_generation, shared_generation)
    if dirty:
        return SyncPlan("local-ahead", "本地有待回写的改动", local_generation, shared_generation)
    return SyncPlan("in-sync", "两侧一致", local_generation, shared_generation)


class LedgerSync:
    """启动判定、周期回写和只读闸门。"""

    def __init__(
        self,
        local: Path,
        shared: Path,
        device: str,
        interval: float = PUSH_INTERVAL_SECONDS,
    ):
        self.local = local
        self.shared = shared
        self.device = device
        self.interval = interval
        self.status = "unstarted"
        self.detail = ""
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def read_only(self) -> bool:
        """冲突未解决时禁止写入。宁可拒绝，也不能在两份分叉的账本上继续加断言。"""
        return self.status == "conflict"

    # ── 单次动作 ────────────────────────────────────────────────────────────
    def pull(self) -> None:
        shared_marker = read_marker(self.shared)
        copy_database(self.shared, self.local)
        generation = shared_marker.generation if shared_marker else 1
        origin = shared_marker.device if shared_marker else self.device
        write_marker(self.local, Marker(generation, origin, _now(), 0, 0))

    def push(self) -> None:
        shared_marker = read_marker(self.shared)
        local_marker = read_marker(self.local)
        base = max(
            shared_marker.generation if shared_marker else 0,
            local_marker.generation if local_marker else 0,
        )
        generation = base + 1
        copy_database(self.local, self.shared)
        stamp = _now()
        write_marker(self.shared, Marker(generation, self.device, stamp, 0, 0))
        write_marker(self.local, Marker(generation, self.device, stamp, 0, 0))

    # ── 生命周期 ────────────────────────────────────────────────────────────
    def startup(self) -> SyncPlan:
        decision = plan(self.local, self.shared)
        self.status, self.detail = decision.action, decision.reason
        if decision.action == "pull":
            self.pull()
            self.status = "in-sync"
        elif decision.action == "push":
            self.push()
            self.status = "in-sync"
        return decision

    def synchronize_now(self) -> SyncPlan:
        """重新判定并完成一次安全同步，供服务停机后的手动同步使用。"""
        decision = plan(self.local, self.shared)
        self.status, self.detail = decision.action, decision.reason
        if decision.action == "pull":
            self.pull()
            self.status = "in-sync"
        elif decision.action in ("push", "local-ahead"):
            self.push()
            self.status = "in-sync"
        return decision

    def push_if_needed(self) -> str:
        """周期回写。别人抢先推过就转冲突，绝不覆盖。"""
        if self.read_only:
            return "conflict"
        decision = plan(self.local, self.shared)
        if decision.action in ("local-ahead", "push"):
            self.push()
            self.status = "in-sync"
            return "pushed"
        if decision.action == "conflict":
            self.status, self.detail = "conflict", decision.reason
            LOGGER.error("账本同步冲突：%s", decision.reason)
            return "conflict"
        self.status = decision.action
        return decision.action

    def start(self) -> None:
        if self.interval <= 0 or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="peach-ledger-sync", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=self.interval + 5)
        # 退出前再回写一次，否则最后一段浏览行为只留在本地副本里。
        try:
            self.push_if_needed()
        except (OSError, sqlite3.Error):
            LOGGER.exception("退出前回写账本失败")

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                self.push_if_needed()
            except (OSError, sqlite3.Error):
                LOGGER.exception("周期回写账本失败")
