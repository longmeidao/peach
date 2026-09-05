"""资源对账：把账本里的记录和磁盘上真实存在的文件对齐。

从 `web_contract` 拆出。这一域自己持有扫描线程状态、目录遍历和孤儿缓存清理，
和浏览、复核没有共享逻辑，留在契约巨石里只是让那个文件更难读。

`source_is_online` 也在这里：判断某个来源的根挂载没挂载，只有对账要问这件事。
`w_purge_missing` 同理——按目录清缺失文件和整库扫描是同一件事的两种入口。
"""
from __future__ import annotations

import os
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Protocol, Sequence

from .catalog_rules import dir_expr, normalise_code_key, photo_set_title
from .config import LOCATION_ROOT_DECLARATIONS
from .jobs import BackgroundJob
from .media import remap_managed_path
from .platform import is_unmapped, root_online, translate_ledger_path


class ResourceSyncContract(Protocol):
    """对账需要契约提供的能力；比整个 WebContract 小得多。"""

    db_path: Path
    snapshot_root: Path | None
    legacy_snapshot_roots: tuple[Path, ...]
    cover_root: Path
    poster_root: Path
    avatar_root: Path
    photo_root: Path
    stream_root: Path
    transcode_root: Path
    resource_cleanup_enabled: bool
    resource_scan: BackgroundJob
    resource_apply_job: BackgroundJob

    def cache_bust(self) -> None: ...
    def read_connection(self): ...
    def write_transaction(self): ...


def source_is_online(location: str) -> bool:
    """这个来源整体在不在线。对账前的唯一闸门。"""
    declared = LOCATION_ROOT_DECLARATIONS.get(location)
    if not declared:
        return False
    # 几个根都在才算在线：少一块盘就对账，那块盘上的文件会被整批判成丢失。
    for root in declared:
        resolved = translate_ledger_path(root)
        if is_unmapped(resolved) or not root_online(resolved):
            return False
    return True


RESOURCE_SCAN_WORKERS = 8


def _scan_resource_directory(
    item: tuple[Path, dict[str, list[int]]],
) -> tuple[list[int], int]:
    parent, expected = item
    present: set[str] = set()
    unreadable = 0
    try:
        with os.scandir(parent) as entries:
            for entry in entries:
                key = entry.name.casefold()
                if key not in expected:
                    continue
                try:
                    if entry.is_file():
                        present.add(key)
                except OSError:
                    # The name was returned but its type could not be read.  Preserve the
                    # ledger row and report it as unreadable instead of declaring deletion.
                    present.add(key)
                    unreadable += len(expected[key])
    except FileNotFoundError:
        return [asset_id for ids in expected.values() for asset_id in ids], 0
    except OSError:
        return [], sum(len(ids) for ids in expected.values())
    return (
        [asset_id for key, ids in expected.items() if key not in present for asset_id in ids],
        unreadable,
    )


def _missing_resource_ids(rows: Sequence) -> tuple[list[int], int]:
    """Compare ledger paths one directory listing at a time.

    Cloud mounts make one ``stat`` request per path painfully slow.  ``scandir`` reuses the
    directory enumeration that the filesystem already returns, while retaining the same
    case-insensitive Windows path semantics.  An unreadable directory is skipped rather than
    being mistaken for a directory that the user deleted.
    """
    directories: dict[Path, dict[str, list[int]]] = {}
    for row in rows:
        path = translate_ledger_path(row["path"])
        expected = directories.setdefault(path.parent, {})
        expected.setdefault(path.name.casefold(), []).append(int(row["id"]))

    directory_items = list(directories.items())
    if len(directory_items) <= 1:
        results = [_scan_resource_directory(item) for item in directory_items]
    else:
        # CloudDrive directory reads are latency-bound metadata requests.  Keep concurrency
        # deliberately small: enough to hide round trips without turning a scan into a media
        # download or overwhelming either mounted provider.
        with ThreadPoolExecutor(
            max_workers=min(RESOURCE_SCAN_WORKERS, len(directory_items)),
            thread_name_prefix="PeachResourceScan",
        ) as executor:
            results = list(executor.map(_scan_resource_directory, directory_items))
    missing = [asset_id for ids, _unreadable in results for asset_id in ids]
    unreadable = sum(count for _ids, count in results)
    return missing, unreadable


def _scan_missing_resources(
    contract: ResourceSyncContract,
    progress: Callable[[dict], None] | None = None,
) -> dict:
    """Read-only reconciliation against every mounted filesystem source."""
    with contract.read_connection() as connection:
        rows = connection.execute(
            "SELECT id,location,path FROM asset "
            "WHERE path IS NOT NULL AND COALESCE(disposal,'')!='trash' "
            "AND location IN ('local','115','pikpak') ORDER BY location,id",
        ).fetchall()
    grouped: dict[str, list] = {}
    for row in rows:
        grouped.setdefault(row["location"], []).append(row)
    missing_ids: list[int] = []
    sources = []
    for location in LOCATION_ROOT_DECLARATIONS:
        items = grouped.get(location, [])
        online = source_is_online(location)
        missing = []
        unreadable = 0
        if online:
            missing, unreadable = _missing_resource_ids(items)
            missing_ids.extend(missing)
        source = {
            "location": location, "online": online,
            "checked": max(0, len(items) - unreadable) if online else 0,
            "total": len(items), "missing": len(missing), "unreadable": unreadable,
        }
        sources.append(source)
        if progress is not None:
            progress(source)
    return {"sources": sources, "missing_ids": missing_ids}


def _cache_file(path: Path, kind: str, output: list[tuple[str, Path, int]]) -> None:
    try:
        size = path.stat().st_size
    except OSError:
        return
    output.append((kind, path, size))


def _managed_cache_root(contract: ResourceSyncContract, root: Path | None) -> bool:
    """Only let a ledger clean caches inside its own runtime data directory.

    Production stores ``ledger.db`` under ``peach-data/database`` and generated files under
    the sibling ``peach-data/generated`` directory. Isolated tests commonly put the database
    directly in a temporary root. In both shapes the database identifies the only directory
    tree cleanup may enter. This prevents a temporary database paired with a forgotten default
    cache root from treating the real generated files as orphans.
    """
    if root is None:
        return False
    database_parent = Path(contract.db_path).resolve().parent
    data_root = (database_parent.parent if database_parent.name.casefold() == "database"
                 else database_parent)
    resolved = Path(root).resolve()
    return resolved != data_root and resolved.is_relative_to(data_root)


def _resource_orphan_plan(contract: ResourceSyncContract, excluded_ids: Sequence[int] = ()) -> dict:
    """Find only reproducible generated files that no active asset still owns.

    Review CSVs, provider evidence, logos and entity portraits are deliberately outside this
    boundary: they are provenance or shared identity assets, not disposable per-asset caches.
    """
    if not contract.resource_cleanup_enabled:
        return {"files": [], "dirs": set(), "summary": {},
                "total_files": 0, "total_bytes": 0}
    with contract.read_connection() as connection:
        rows = connection.execute(
            "SELECT id,code,snapshot_path FROM asset WHERE COALESCE(disposal,'')!='trash'",
        ).fetchall()
    excluded = {int(item) for item in excluded_ids}
    rows = [row for row in rows if int(row["id"]) not in excluded]
    active_ids = {int(row["id"]) for row in rows}
    active_codes = {normalise_code_key(row["code"]) for row in rows if row["code"]}
    active_codes.discard("")
    active_snapshots = set()
    for row in rows:
        raw = row["snapshot_path"]
        if raw:
            active_snapshots.add(remap_managed_path(
                raw, contract.snapshot_root, contract.legacy_snapshot_roots,
            ) if contract.snapshot_root is not None else Path(raw))

    files: list[tuple[str, Path, int]] = []
    cleanup_dirs: set[Path] = set()
    if (_managed_cache_root(contract, contract.snapshot_root)
            and contract.snapshot_root.is_dir()):
        for path in contract.snapshot_root.rglob("*"):
            if path.is_file() and path not in active_snapshots:
                _cache_file(path, "snapshots", files)

    patterns = (
        (contract.poster_root, "posters", re.compile(r"^(\d+)_\d+\.jpg$")),
        (contract.photo_root, "photo-thumbs", re.compile(r"^(\d+)\.jpg$")),
        (contract.transcode_root, "transcodes", re.compile(r"^(\d+)-.+\.mp4$")),
    )
    for root, kind, pattern in patterns:
        if not _managed_cache_root(contract, root) or not root.is_dir():
            continue
        for path in root.iterdir():
            match = pattern.match(path.name)
            if match and int(match.group(1)) not in active_ids and path.is_file():
                _cache_file(path, kind, files)

    if (_managed_cache_root(contract, contract.stream_root)
            and contract.stream_root.is_dir()):
        for directory in contract.stream_root.iterdir():
            if not directory.is_dir() or not directory.name.isdigit():
                continue
            if int(directory.name) in active_ids:
                continue
            cleanup_dirs.add(directory)
            for path in directory.rglob("*"):
                if path.is_file():
                    _cache_file(path, "stream-segments", files)

    if (_managed_cache_root(contract, contract.avatar_root)
            and contract.avatar_root.is_dir()):
        for path in contract.avatar_root.iterdir():
            match = re.match(r"^(\d+)\.jpg$", path.name)
            if match and int(match.group(1)) not in active_ids and path.is_file():
                _cache_file(path, "asset-avatars", files)

    if (_managed_cache_root(contract, contract.cover_root)
            and contract.cover_root.is_dir()):
        for path in contract.cover_root.iterdir():
            key = ""
            if path.name.endswith(".face.json"):
                key = path.name[:-10]
            elif path.suffix.lower() == ".jpg":
                key = path.stem
            if key and normalise_code_key(key) not in active_codes and path.is_file():
                _cache_file(path, "covers", files)

    summary: dict[str, dict[str, int]] = {}
    for kind, _path, size in files:
        bucket = summary.setdefault(kind, {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += size
    return {
        "files": files, "dirs": cleanup_dirs, "summary": summary,
        "total_files": len(files), "total_bytes": sum(item[2] for item in files),
    }


def clean_resource_orphans(contract: ResourceSyncContract) -> dict:
    plan = _resource_orphan_plan(contract)
    removed = 0
    reclaimed = 0
    blocked = []
    for kind, path, size in plan["files"]:
        try:
            path.unlink(missing_ok=True)
            removed += 1
            reclaimed += size
        except OSError as error:
            blocked.append({"kind": kind, "name": path.name,
                            "reason": error.strerror or str(error)})
    for directory in sorted(plan["dirs"], key=lambda item: len(item.parts), reverse=True):
        try:
            shutil.rmtree(directory)
        except FileNotFoundError:
            pass
        except OSError:
            # Individual file failures above already carry useful detail; a non-empty cache
            # directory is harmless and will be reconsidered on the next scan.
            pass
    return {"cache_removed": removed, "bytes_reclaimed": reclaimed,
            "cache_blocked": blocked}


def _resource_scan_public(state: dict) -> dict:
    if state["status"] == "complete":
        return {**state["result"], "status": "complete", "scan_id": state["scan_id"]}
    return {
        "ok": state["status"] != "failed",
        "status": state["status"],
        "scan_id": state["scan_id"],
        "sources": [dict(source) for source in state["sources"]],
        "completed_sources": len(state["sources"]),
        "total_sources": len(LOCATION_ROOT_DECLARATIONS),
        **({"error": state["error"]} if state["status"] == "failed" else {}),
    }


def _run_resource_scan(contract: ResourceSyncContract, scan_id: str) -> None:
    """Scan every mounted source.  ``BackgroundJob`` turns a failure into a pollable state."""
    job = contract.resource_scan

    def progress(source: dict) -> None:
        with job.editing(scan_id) as state:
            if state is not None:
                state["sources"].append(dict(source))

    scan = _scan_missing_resources(contract, progress)
    caches = _resource_orphan_plan(contract, scan["missing_ids"])
    result = {
        "ok": True, "sources": scan["sources"],
        "missing": len(scan["missing_ids"]),
        "cache": {"files": caches["total_files"], "bytes": caches["total_bytes"],
                  "by_kind": caches["summary"]},
    }
    job.update(scan_id, status="complete", result=result,
               missing_ids=list(scan["missing_ids"]), completed_at=time.time())


def _background_resource_scan(contract: ResourceSyncContract, restart: bool = False) -> dict:
    return _resource_scan_public(contract.resource_scan.start(
        lambda scan_id: _run_resource_scan(contract, scan_id),
        initial={"sources": [], "result": None, "missing_ids": []},
        restart=restart,
    ))


def w_resource_sync_scan(contract: ResourceSyncContract, body=None):
    body = body or {}
    if body.get("background") is True:
        if body.get("status_only") is True:
            state = contract.resource_scan.snapshot()
            if state is None:
                return {
                    "ok": True, "status": "idle", "scan_id": "", "sources": [],
                    "completed_sources": 0,
                    "total_sources": len(LOCATION_ROOT_DECLARATIONS),
                }
            return _resource_scan_public(state)
        return _background_resource_scan(contract, restart=body.get("restart") is True)
    scan = _scan_missing_resources(contract)
    caches = _resource_orphan_plan(contract, scan["missing_ids"])
    return {
        "ok": True, "sources": scan["sources"],
        "missing": len(scan["missing_ids"]),
        "cache": {"files": caches["total_files"], "bytes": caches["total_bytes"],
                  "by_kind": caches["summary"]},
    }


def _recheck_resource_scan_ids(contract: ResourceSyncContract, asset_ids: Sequence[int]) -> list[int]:
    if not asset_ids:
        return []
    rows = []
    with contract.read_connection() as connection:
        for offset in range(0, len(asset_ids), 400):
            batch = list(asset_ids[offset:offset + 400])
            marks = ",".join("?" for _item in batch)
            rows.extend(connection.execute(
                "SELECT id,location,path FROM asset "
                f"WHERE id IN ({marks}) AND path IS NOT NULL "
                "AND COALESCE(disposal,'')!='trash'",
                batch,
            ).fetchall())
    grouped: dict[str, list] = {}
    for row in rows:
        grouped.setdefault(row["location"], []).append(row)
    missing = []
    for location, items in grouped.items():
        if not source_is_online(location):
            continue
        source_missing, _unreadable = _missing_resource_ids(items)
        missing.extend(source_missing)
    return missing


def w_resource_sync_apply(contract: ResourceSyncContract, body):
    if body.get("confirm") is not True:
        raise ValueError("resource sync requires confirmation")
    if body.get("background"):
        return contract.resource_apply_job.start_result(
            lambda: w_resource_sync_apply(contract, {**body, "background": False}))
    scan_id = str(body.get("scan_id") or "")
    if scan_id:
        state = contract.resource_scan.snapshot()
        if (state is None or state["scan_id"] != scan_id
                or state["status"] != "complete"):
            raise ValueError("resource scan expired; scan again")
        candidates = list(state["missing_ids"])
        sources = [dict(source) for source in state["result"]["sources"]]
        # Do not trust the background result at write time.  Recheck only its bounded
        # candidate set; online sources and unreadable directories retain the safe skip.
        missing_ids = _recheck_resource_scan_ids(contract, candidates)
        scan = {"sources": sources, "missing_ids": missing_ids}
    else:
        # Compatibility path for non-browser callers: still perform a fresh full scan.
        scan = _scan_missing_resources(contract)
        missing_ids = scan["missing_ids"]
    if missing_ids:
        with contract.write_transaction() as connection:
            stamp = time.time()
            connection.executemany(
                "UPDATE asset SET disposal='trash',feedback_at=? WHERE id=?",
                [(stamp, asset_id) for asset_id in missing_ids],
            )
    contract.cache_bust()
    cleanup = clean_resource_orphans(contract) if body.get("clean_cache", True) else {
        "cache_removed": 0, "bytes_reclaimed": 0, "cache_blocked": [],
    }
    return {"ok": True, "moved_to_trash": len(missing_ids),
            "sources": scan["sources"], **cleanup}


def w_purge_missing(contract: ResourceSyncContract, body):
    """按目录对账：文件已经在磁盘上删掉的，账本行移入回收站。

    这条路径服务的是「我在资源管理器里整理网盘目录」——删掉的就是不要的，所以
    不进复核；账本记录仍先进入回收站，源文件恢复后还能还原。

    真正危险的不是删得太干净，而是把「盘没挂上」误判成「文件没了」：R: 掉线时
    整条来源 2,552 行都会看起来像被删。所以先做来源级在线判定，整源不在线就
    一行都不碰。CloudDrive 掉线后挂载点目录仍然存在，`root_online` 因此判的是
    「能否列出一个条目」而不是「目录在不在」。

    判缺失和全量扫描共用 `_missing_resource_ids`：整个目录一次列举出结果。逐条
    `is_file()` 在云挂载上每条都是一次元数据往返——已删除的路径尤其贵，CloudDrive
    对「不存在」没有负缓存；目录暂时读不了时保留账本行，不当成已删。
    """
    asset_id = int(body["id"])
    with contract.read_connection() as connection:
        anchor = connection.execute(
            "SELECT id,location,path,name FROM asset WHERE id=?", (asset_id,),
        ).fetchone()
        if not anchor:
            return {"error": "not found"}
        location, path, name = anchor["location"], anchor["path"], anchor["name"]
        if not path or not name:
            return {"error": "asset has no path"}
        if not source_is_online(location):
            # 不是失败，是拒绝：盘不在时无法区分「文件删了」和「盘没挂上」。
            return {"ok": False, "error": "source offline", "location": location}
        directory = path[: len(path) - len(name) - 1]
        rows = connection.execute(
            f"SELECT id,path,name FROM asset WHERE location=? "
            f"AND {dir_expr('')}=?",
            (location, directory),
        ).fetchall()

    missing_ids, unreadable = _missing_resource_ids(rows)
    gone = set(missing_ids)
    missing = [
        {"id": row["id"], "name": row["name"]}
        for row in rows
        if int(row["id"]) in gone
    ]
    if not missing:
        return {"ok": True, "directory": photo_set_title(directory),
                "checked": len(rows), "removed": 0, "unreadable": unreadable,
                "items": []}

    contract.cache_bust()
    ids = [item["id"] for item in missing]
    with contract.write_transaction() as connection:
        stamp = time.time()
        connection.executemany(
            "UPDATE asset SET disposal='trash',feedback_at=? WHERE id=?",
            [(stamp, asset_id) for asset_id in ids],
        )
    contract.cache_bust()
    return {
        "ok": True, "directory": photo_set_title(directory),
        "checked": len(rows), "removed": len(missing), "unreadable": unreadable,
        "items": missing,
    }
