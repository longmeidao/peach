"""扫描与采集结束后，把已有封面、还没有样张的番号补上官方样张（ADR-0068）。

挂在处理链结算那一刻（ADR-0040 的后继），不插进逐行的循环：循环里「番号、字段、封面都齐了」
的行连网盘都不碰，而存量里最该补样张的正是这些行。一轮一条后继，一条最多问 `BATCH` 部。

每部先读本机来源快照，处理链问过的站已经把样张地址带回来了（DMM 的 `sample_images`、
amane 桥的 `screenshot_urls`）；快照里没有才按番号分档问一站：有码问 DMM，素人问 MGS。
写入按 ADR-0052 直接落，`source` 记 `auto:sample-images@<任务行 id>`，
`scripts/revert_auto_landing.py --source auto:sample-images` 整批撤回。

幂等（ADR-0040 第六条）：选番号时就跳过已有样张的，写入时再判一次，已有就整组跳过。
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from . import sample_images
from .followups import FollowupType, register

TASK_KEY = "code-samples"
TASK_LABEL = "补番号样张"

#: 一轮只派一条，key 固定：同一件事同时只会有一条在排队或在跑。
FOLLOWUP_KEY = f"{TASK_KEY}:stock"

#: 一条后继最多问几部。写账本的后继共用一条串行通道，一条占太久会把补头像那几类压在后面；
#: DMM 一次约 1 秒、主机间隔 2 秒，30 部约一分半。
BATCH = 30

#: 一条后继的联网预算，到点就收工，剩下的下一轮接着补。
BUDGET_SECONDS = 150.0


def plan(database, config, cover_root) -> list[dict]:
    """处理链结算时调用：还有问得着的番号就派一条，一部都没有就不派。

    这里出任何问题都只让这一轮不派，不影响处理本身的结论。
    """
    if database is None:
        return []
    covers = Path(cover_root)
    try:
        misses = sample_images.Misses(sample_images.misses_path(config.directory("generated")))
        snapshots = sample_images.snapshot_index(config.directory("sources"))
        with database.read_connection() as connection:
            found = sample_images.pending(
                connection, lambda key: (covers / f"{key}.jpg").is_file(), misses, snapshots, limit=1)
    except (OSError, sqlite3.Error):
        return []
    return [{"key": FOLLOWUP_KEY, "task_key": TASK_KEY, "label": TASK_LABEL}] if found else []


def _missing(error: Exception) -> bool:
    """这一站明确说没有：传输层 404 或契约里 `not_found` 那一档。"""
    from .jav_cover_fetch import NotFound
    from .sources import FailureReason, SourceFailure
    return isinstance(error, NotFound) or (
        isinstance(error, SourceFailure) and error.reason == FailureReason.NOT_FOUND)


def run(contract, key: str, handle, *, transport=None, clock=time.monotonic) -> dict:
    """跑一条补样张后继，返回活动页上那一行的摘要。"""
    from .jav_cover_fetch import DeadlineExceeded, HostLimitedTransport
    from .scraping_access import SourcePaused, SourceTransport

    generated = Path(contract.candidate_root)
    misses = sample_images.Misses(sample_images.misses_path(generated))
    snapshots = sample_images.snapshot_index(Path(contract.follow_sources_root))
    with contract.database.read_connection() as connection:
        codes = sample_images.pending(connection, contract.has_cover, misses, snapshots, limit=BATCH)
    if not codes:
        return {"outcome": "没有要补的番号", "codes": 0}
    batch = sample_images.batch_for(getattr(handle, "run_id", None))
    owned = transport is None
    if owned:
        transport = HostLimitedTransport(
            SourceTransport(Path(contract.follow_secrets_root), max_requests=BATCH * 3,
                            max_bytes=64 * 1024 * 1024, max_seconds=BUDGET_SECONDS), 2.0)
    deadline = clock() + BUDGET_SECONDS
    landed = images = absent = failed = 0
    paused: set[str] = set()
    try:
        for index, code in enumerate(codes):
            if handle is not None:
                handle.progress(current=index, total=len(codes), label=f"{TASK_LABEL}：{code}")
            site, urls = "", []
            snapshot = sample_images.snapshot_samples(snapshots.get(code, ()))
            if snapshot:
                site, urls = snapshot
            elif code in snapshots:
                misses.record("snapshot", code)
            if not urls:
                site = sample_images.site_for(code) or ""
                if not site or site in paused or misses.fresh(site, code):
                    continue
                if clock() >= deadline:
                    break
                try:
                    urls = sample_images.usable(
                        sample_images.FETCHERS[site](transport, code, deadline=deadline))
                except SourcePaused:
                    # 冷却或本趟预算用完：这一站后面的都不问，也不记「没有」。
                    paused.add(site)
                    continue
                except DeadlineExceeded:
                    break
                except Exception as error:  # noqa: BLE001 - 一部取不到不影响同批其余几部
                    if _missing(error):
                        misses.record(site, code)
                        absent += 1
                    else:
                        failed += 1
                    continue
                if not urls:
                    misses.record(site, code)
                    absent += 1
                    continue
            with contract.database.write_transaction() as connection:
                count = sample_images.land(connection, code, site, urls, source=batch)
            if count:
                landed += 1
                images += count
    finally:
        misses.save()
        if owned:
            transport.close()
    if landed:
        contract.cache_bust()
    if handle is not None:
        handle.progress(current=len(codes), total=len(codes), label=TASK_LABEL, throttle=0)
    outcome = f"补上 {landed} 部的样张（{images} 张）" if landed else "这一轮没有补上样张"
    summary = {"outcome": outcome, "codes": len(codes), "landed": landed, "images": images,
               "absent": absent, "failed": failed, "batch": batch}
    if paused:
        summary["paused"] = sorted(paused)
    return summary


#: 写账本：样张地址写在 `code_sample_image`。联网在事务外做，每部写一次，很短；
#: 照样走写账本那一条串行通道（ADR-0040 第二条）。
TYPE = register(FollowupType(task_key=TASK_KEY, label=TASK_LABEL, writes_ledger=True,
                             run=lambda contract, key, handle: run(contract, key, handle)))
