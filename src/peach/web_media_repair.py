"""批量把缺 `ctts` 的 MP4 头修好，让这类片子起播就走原片直发。

有 B 帧却没有 `ctts` 的片源，浏览器按容器时间戳丢帧，只能退回 HLS 实时转码。
`mp4repair` 能重建一份头存成边车，但那是起播时后台补的：一部片要等下一次打开才
享受得到。这里把同一件事做成一次可以在后台跑完的批量任务。

两段走，因为两段的瓶颈不是一回事：

1. **筛**：读每个片子的 `moov` 判断它是不是这一类。一次判定只读头，但 115 上就是
   一次网络往返，所以并发做。判完的结论按「资产 + 大小 + 改动时间」落盘，下次再点
   就不必把整个库重读一遍。
2. **修**：整片解码一遍才问得出显示顺序，CPU 和读盘都吃满，所以串行做，并且按播放
   次数排序——常看的先修好，中途停下也已经换来了体感。

计费来源默认不碰（`SourceAccessPolicy`）：PikPak 上一部片要完整拉一遍才修得了。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .jobs import SourceAccessPolicy
from .platform import translate_ledger_path

#: 判定结论的落盘位置，放在边车自己的目录里：它们同生同灭，清缓存时一起走。
SCAN_CACHE_NAME = "mp4-repair-scan.json"

#: 只有这两个结论值得记：需要修的当场就修了，修完有边车为证。
CLEAN = "clean"
UNAVAILABLE = "unavailable"

POLICY = SourceAccessPolicy()


def _cache_path(contract) -> Path:
    return Path(contract.transcode_root) / SCAN_CACHE_NAME


def _load_cache(contract) -> dict[str, str]:
    try:
        payload = json.loads(_cache_path(contract).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = payload.get("entries") if isinstance(payload, dict) else None
    return {str(key): str(value) for key, value in entries.items()} if isinstance(entries, dict) else {}


def _save_cache(contract, entries: dict[str, str]) -> None:
    path = _cache_path(contract)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps({"version": 1, "entries": entries}), encoding="utf-8")
        temporary.replace(path)
    except OSError:
        # 结论缓存丢了只是下次重扫一遍，不该让整轮任务失败。
        pass


def _key(asset_id: int, source: Path) -> str:
    """和边车同一套身份：文件换了内容，旧结论就不再作数。"""
    stat = source.stat()
    return f"{asset_id}-{stat.st_size}-{stat.st_mtime_ns}"


def _candidates(contract, allow_metered: bool) -> list[tuple[int, Path]]:
    """库里所有还在的 MP4，常看的排前面。"""
    condition, parameters = POLICY.sql_filter(None, allow_metered)
    with contract.read_connection() as connection:
        rows = connection.execute(
            "SELECT id,path FROM asset "
            "WHERE path IS NOT NULL AND COALESCE(disposal,'')!='trash' "
            "AND (lower(path) LIKE '%.mp4' OR lower(path) LIKE '%.m4v')" + condition
            + " ORDER BY play_count DESC, COALESCE(last_played,0) DESC, id",
            parameters).fetchall()
    return [(row["id"], translate_ledger_path(row["path"])) for row in rows]


def _survey(contract, job, job_id: str, rows, cache: dict[str, str]) -> list[tuple[int, Path]]:
    """筛出需要修的那些。结论边判边进缓存，中途停下也不白读。"""
    store = contract.header_repairs
    transcodes = contract.transcode_service
    found: list[tuple[int, Path]] = []
    for index, (asset_id, source) in enumerate(rows, start=1):
        if job.snapshot() is None:
            break
        try:
            key = _key(asset_id, source)
        except OSError:
            continue
        if store.lookup(asset_id, source) is not None or cache.get(key) in (CLEAN, UNAVAILABLE):
            _advance(job, job_id, index, skipped=True)
            continue
        try:
            affected = transcodes.decode_order_timestamps(source)
        except OSError:
            affected = False
        if affected:
            found.append((asset_id, source))
        else:
            cache[key] = CLEAN
        _advance(job, job_id, index, skipped=False)
    return found


def _advance(job, job_id: str, checked: int, *, skipped: bool) -> None:
    with job.editing(job_id) as state:
        if state is None:
            return
        state["checked"] = checked
        if skipped:
            state["skipped"] = state.get("skipped", 0) + 1


def _repair(contract, job, job_id: str, found, cache: dict[str, str]) -> None:
    """逐个修。一部片要整片解码一遍，所以这里刻意不并发。"""
    store = contract.header_repairs
    job.update(job_id, stage="修复", checked=0, total=len(found), repaired=0, failed=0)
    for index, (asset_id, source) in enumerate(found, start=1):
        if job.snapshot() is None:
            return
        made = store.repair_now(asset_id, source)
        if not made:
            try:
                cache[_key(asset_id, source)] = UNAVAILABLE
            except OSError:
                pass
        with job.editing(job_id) as state:
            if state is None:
                return
            state["checked"] = index
            state["repaired"] = state.get("repaired", 0) + (1 if made else 0)
            state["failed"] = state.get("failed", 0) + (0 if made else 1)
            state["message"] = source.name[:80]
        _save_cache(contract, cache)


def run_media_repair(contract, job_id: str, allow_metered: bool = False) -> None:
    """一轮完整的批量修复。异常由 `BackgroundJob` 变成可轮询的失败状态。"""
    job = contract.media_repair_job
    cache = _load_cache(contract)
    rows = _candidates(contract, allow_metered)
    job.update(job_id, stage="扫描", total=len(rows), checked=0)
    found = _survey(contract, job, job_id, rows, cache)
    _save_cache(contract, cache)
    if job.snapshot() is None:
        return
    job.update(job_id, found=len(found))
    _repair(contract, job, job_id, found, cache)
    _save_cache(contract, cache)
    job.update(job_id, stage="完成", status="complete", completed_at=time.time())


def _public(state: dict | None) -> dict:
    if state is None:
        return {"ok": True, "status": "idle", "job_id": "", "stage": "",
                "checked": 0, "total": 0, "found": 0, "repaired": 0, "failed": 0}
    return {
        "ok": state["status"] != "failed",
        "status": state["status"],
        "job_id": state["job_id"],
        "stage": state.get("stage", ""),
        "checked": int(state.get("checked", 0)),
        "total": int(state.get("total", 0)),
        "found": int(state.get("found", 0)),
        "repaired": int(state.get("repaired", 0)),
        "failed": int(state.get("failed", 0)),
        "skipped": int(state.get("skipped", 0)),
        "message": state.get("message", ""),
        **({"error": state["error"]} if state["status"] == "failed" else {}),
    }


def q_media_repair(contract, args=None):
    return _public(contract.media_repair_job.snapshot())


def w_media_repair(contract, body=None):
    """启动一轮，或按 `stop` 停下正在跑的那一轮。"""
    body = body or {}
    job = contract.media_repair_job
    if body.get("stop") is True:
        job.stop()
        return _public(None)
    if body.get("status_only") is True:
        return _public(job.snapshot())
    if contract.header_repairs is None or contract.transcode_service is None:
        raise ValueError("这个服务实例没有接上转码与修复组件")
    allow_metered = body.get("allow_metered") is True
    return _public(job.start(
        lambda job_id: run_media_repair(contract, job_id, allow_metered),
        initial={"stage": "扫描", "total": 0, "checked": 0, "found": 0,
                 "repaired": 0, "failed": 0, "skipped": 0, "message": ""},
        restart=body.get("restart") is True,
    ))
