"""数据清理：广告残留判定、批量操作、物理清除与回收站。

放在同一个模块是因为它们是同一条链上的四段：`q_ads` 判定哪些文件是广告残留，
`w_batch` 把用户的批量决定落库，`purge_assets` 真正动磁盘，`w_empty_trash` 收尾。
判定与执行分家的话，「命中推广词」和「可以删」之间那道界线就没人守了——
剥掉推广词后还剩内容的文件不是广告，这条只有把判据和删除放在一起看才成立。

物理删除的边界只写在 `ASSET_REFERENCE_TABLES` 一处；同目录隔离加数据库失败回滚
（`_restore_staged_media`）是这个模块最不能出错的部分：删错的文件找不回来。
"""
from __future__ import annotations

import errno
import os
import re
import time
import uuid

from pathlib import Path, PureWindowsPath
from typing import Sequence

from .catalog_rules import duration_clusters, is_jav_code, normalise_code_key
from .config import LOCATION_ROOT_DECLARATIONS
from .platform import is_unmapped, root_online, translate_ledger_path, within_root
from .web_activity import DEFAULT_PROFILE_ID
from .web_catalog import COST, attach_card_performers
from .web_resource_sync import clean_resource_orphans
from .web_state import WebContract


# 清空回收站时要一并清掉的资产引用表，物理删除的边界只写在这一处。
# `asset_search` 不在其中：0004 的 `asset_search_asset_delete` 触发器已经负责 FTS 行，
# 这里再删一遍只会重复，还会诱使测试库伪造一张同名普通表，把 has_fts() 骗成 True。
ASSET_REFERENCE_TABLES = (
    "asset_tag", "media_binding", "activity_event", "asset_entity",
    "watch_queue", "asset_preference", "asset_tag_preference", "asset_quality_goal",
    "playlist_item",
)

# 只认联系方式与站点形态的推广套话。「微信」「成人游戏」这类词单独出现不算：
# 实测正片标题里就有（「还要微信跟老公汇报战果」是剧情，不是联系方式）。
PROMO_PHRASE = re.compile(
    r"(扫码|二维码|加微信|加微|威信\d|微信号|微信\s*[:：]|免费看|免费玩|福利群|最新地址|"
    r"永久(?:域名|地址|发布)|点击(?:观看|下载|进入)|下载APP|下载|签到|代币|领取|"
    r"强力推荐|国产大片|在线视频|大饱眼福|房间火爆|澳门|赌场|博彩|棋牌|加我|包养|约炮|"
    r"GAMES?\d*|APP)", re.I)
# 结尾不能用 \b：`uuc82.com_2` 里 `m` 和 `_` 都是词字符，构不成边界，域名会漏掉。
PROMO_DOMAIN = re.compile(
    r"(?:https?://)?(?:www\.)?[\w-]{2,}\.(?:com|net|me|la|xyz|cc|tv|top|vip|club|"
    r"info|org|pw|cn|app|site|online|shop)(?![a-z0-9])", re.I)
# 真番号带厂牌前缀和连字号（ABW-153、259LUXU-1141）。RAIKUN325 这类没有连字号的
# 是被误填进 code 的创作者账号名，不能拿来做「同番号有完整版」的比较，
# 判据与 `is_jav_code` 同源：分隔符正是番号与账号名的唯一线索。
REAL_CODE = re.compile(r"^(?:\d{2,3})?[A-Za-z]{2,8}-\d{2,5}$|^FC2", re.I)
PART_MARK = re.compile(r"(CD\d|part\d|分卷|-\d{1,2}$|\(\d+\)$)", re.I)
# 推广站目录的两种形态，与 `scripts/find_ads.py` 的判据 D/E 同源：
# 创作者位是旧导入器的目录名投影，`bbsxv.xyz-DOCP-324` 这类广告包会直接落在那里；
# 裸域名目录（98T.la@账号、huachishe.com@系列）是转载水印，不是广告，不能进判据。
AD_DOMAIN = re.compile(
    r"\b[0-9a-z][-0-9a-z]{1,20}\.(?:cc|xyz|com|net|la|me|top|vip|club|app|cn|pw|tv|gg)\b", re.I)
AD_DIRPACK = re.compile(
    r"[0-9a-z][-0-9a-z]{1,20}\.[a-z]{2,10}[ \-_]+\[?[A-Za-z]{2,6}-?\d{2,5}", re.I)
INTERNET_SHORTCUT_SUFFIXES = frozenset({".url"})
JUNK_KINDS = frozenset({"video", "image", "audio", "archive", "url", "other"})


def promo_residue(name: str) -> int:
    """剥掉域名和推广套话后，还剩多少实质描述字符。

    这是区分「广告」与「正片被打了站点水印」的关键：
    `点击观看 房间火爆` 剥完什么都不剩；
    `236953.xyz 推特新晋4年绿帽美腿淫妻网黄「一个ren」…` 剥完仍有大段内容描述。
    """
    text = PROMO_DOMAIN.sub(" ", name or "")
    text = PROMO_PHRASE.sub(" ", text)
    # 只数中日韩文字与字母，忽略编号、扩展名和标点。
    return len(re.findall(r"[一-鿿぀-ヿ가-힯 A-Za-z]", text))


def q_ads(contract: WebContract, limit=200, offset=0, kind="", status="pending"):
    """疑似垃圾复核队列 —— **不自动删**，只排队让人看证据确认。

    没有可靠的单一判据（试过「同番号短版」会误伤 CD2/part1 分卷，
    试过「同名扩散」会误伤 001.mp4 这类通用名的真文件）。
    所以给的是**嫌疑分**，按分排序，人工看图定夺，确认的走既定 CSV 删除流程。

    2026-08-15 按用户标记的 21 条真广告重新标定：命中推广词本身不算证据，
    要看**剥掉推广词后还剩不剩内容**。三类实测误判据此排除：剧情里的「微信」、
    开头是盗版站域名但正文是真实描述、以及把创作者账号当成番号去比时长。

    物理资源的类型不能成为免检条件。视频保留时长、体积和同番号长版证据；图片、
    音频、压缩包和其它文件走共用的推广名／推广目录证据；Windows ``.url`` 是网址
    快捷方式，在媒体目录中直接进入人工复核。在线资产不是待清理的物理文件，排除。"""
    kind = str(kind or "").strip().casefold()
    status = str(status or "pending").strip().casefold()
    if kind and kind not in JUNK_KINDS:
        raise ValueError("invalid junk kind")
    if status not in {"pending", "dismissed"}:
        raise ValueError("invalid junk status")
    with contract.read_connection() as c:
        rows = c.execute(
            "SELECT id,location,name,medium,creator,code,size,duration,width,height,snapshot_path,"
            "feedback,disposal,play_count,leave_ratio,o_count,studio,ctx_orient,path "
            "FROM asset WHERE location IN ('local','115','pikpak') AND disposal IS NULL "
            "AND (COALESCE(medium,'other')<>'video' OR (size < 500*1024*1024 "
            "AND duration IS NOT NULL AND duration BETWEEN 15 AND 1200))").fetchall()
        # 同番号是否存在明显更长的版本；只在 code 是真番号时才有意义。
        longer = {r[0]: r[1] for r in c.execute(
            "SELECT code, max(duration) FROM asset WHERE medium='video' AND code IS NOT NULL "
            "AND code<>'' AND duration IS NOT NULL GROUP BY code")}
        dismissed_keys = [str(row[0]) for row in c.execute(
            "SELECT item_key FROM review_decision "
            "WHERE category='junk_file' AND status='rejected'"
        )]
        dismissed_ids = {int(key) for key in dismissed_keys if key.isdigit()}
    out = []
    for r in rows:
        d = dict(r)
        s, why = 0, []
        name = d.get("name") or PureWindowsPath(d.get("path") or "").name
        resource_path = PureWindowsPath(d.get("path") or name)
        name_path = PureWindowsPath(name)
        nm = name_path.stem
        suffix = name_path.suffix.casefold()
        d["junk_kind"] = (
            "url" if suffix in INTERNET_SHORTCUT_SUFFIXES
            else (d.get("medium") if d.get("medium") in JUNK_KINDS else "other")
        )
        residue = promo_residue(nm)
        promo = bool(PROMO_PHRASE.search(nm) or PROMO_DOMAIN.search(nm))
        if suffix in INTERNET_SHORTCUT_SUFFIXES:
            s += 60; why.append("网址快捷方式")
        # 目录维度的证据：广告包的文件名往往干净（`极道世界.mp4`），唯一线索在旧导入器
        # 从目录名投影出来的创作者位或路径里。creator 位本身是推广站域名时，它就不再是
        # 「有归属所以是正片」的证据，下面两处对 creator 的信任都必须先排除这种情况。
        owner = d.get("creator") or ""
        owner_is_promo = bool(AD_DOMAIN.search(owner))
        real_owner = bool(owner) and not owner_is_promo
        # ledger 路径在两个平台都是 Windows 形态；PureWindowsPath 才能让 macOS reader
        # 也识别反斜杠目录，os.path.dirname 在 macOS 会把整条路径当成文件名。
        folder = str(resource_path.parent)
        if promo and residue < 6:
            # 名字剥完只剩广告本身，这是最硬的信号。
            s += 60; why.append("整个名字都是推广语")
        elif promo and residue < 14 and not real_owner:
            s += 30; why.append("推广语占了名字主体")
        if owner_is_promo:
            s += 50; why.append("创作者位是推广站域名")
        elif AD_DIRPACK.search(folder):
            s += 45; why.append("目录是「域名+番号」的推广打包")
        if d.get("medium") == "video":
            code = (d["code"] or "").strip()
            mx = longer.get(code)
            if mx and REAL_CODE.match(code) and d["duration"] < mx * 0.2 \
                    and not PART_MARK.search(nm):
                # 分卷已排除，真番号下不到两成时长基本就是片段/预告，单独即可入队复核。
                # 用户标记的 `反抗不如享受.mp4`（ABW-220，244 秒）正好卡在旧的 35 分门外。
                s += 40; why.append(f"同番号有 {mx/60:.0f} 分完整版")
            if d["duration"] < 240:
                s += 15; why.append("不足 4 分钟")
            if (d["size"] or 0) < 120 * 1024**2:
                s += 10; why.append("小于 120 MB")
        # 有真实创作者归属、且名字剥完仍有实质描述的，是被打了水印的正片，不是广告。
        if real_owner and residue >= 14:
            s -= 45
        if s >= 40:
            d["score"] = s; d["why"] = " · ".join(why)
            d["cost"] = COST.get(d["location"], "metered")
            d["has_thumb"] = contract.has_snapshot(d["snapshot_path"])
            d.pop("snapshot_path", None)
            d.pop("path", None)
            out.append(d)
    out.sort(key=lambda x: (-x["score"], -(x["size"] or 0)))
    pending = [item for item in out if item["id"] not in dismissed_ids]
    dismissed = [item for item in out if item["id"] in dismissed_ids]
    pool = dismissed if status == "dismissed" else pending
    counts = {junk_kind: 0 for junk_kind in JUNK_KINDS}
    for item in pool:
        counts[item["junk_kind"]] += 1
    filtered = [item for item in pool if not kind or item["junk_kind"] == kind]
    items = filtered[offset:offset + limit]
    attach_card_performers(
        contract, [item for item in items if item.get("medium") == "video"])
    return {
        "total": len(filtered),
        "all_total": len(pool),
        "pending_total": len(pending),
        "dismissed_total": len(dismissed),
        "counts": counts,
        "kind": kind,
        "status": status,
        "items": items,
    }


def _restore_staged_media(staged):
    """Undo same-directory quarantine moves after a database failure."""
    for original, quarantine in reversed(staged):
        if quarantine.exists() and not original.exists():
            os.replace(quarantine, original)


def _online_source_roots() -> dict[str, Path]:
    """Return only declared physical roots that can be enumerated now."""
    roots: dict[str, Path] = {}
    for location, declaration in LOCATION_ROOT_DECLARATIONS.items():
        root = translate_ledger_path(declaration)
        if is_unmapped(root) or not root.is_dir() or not root_online(root):
            continue
        roots[location] = root
    return roots


def _remove_empty_ancestors(parent: Path, source_roots: Sequence[Path]) -> list[Path]:
    """Remove empty parents up to, but never including, a declared source root."""
    source_root = next(
        (root for root in sorted(source_roots, key=lambda item: len(item.parts), reverse=True)
         if within_root(parent, root)),
        None,
    )
    if source_root is None:
        return []
    removed: list[Path] = []
    current = parent
    while current != source_root and within_root(current, source_root):
        if current.is_symlink():
            break
        next_parent = current.parent
        try:
            current.rmdir()
        except FileNotFoundError:
            # CloudDrive may collapse an empty layer as soon as its last file vanishes.
            current = next_parent
            continue
        except OSError:
            # Non-empty, offline, or protected directories are a normal stop boundary.
            break
        removed.append(current)
        current = next_parent
    return removed


def cleanup_empty_source_directories() -> dict[str, object]:
    """Delete empty directories below each online physical source.

    The declared source roots themselves are permanent boundaries and are never removed.
    ``os.walk(..., topdown=False)`` ensures children are considered before their parents;
    directory links are not followed or removed.
    """
    results: list[dict[str, object]] = []
    total_scanned = total_removed = total_errors = 0
    for location, declaration in LOCATION_ROOT_DECLARATIONS.items():
        root = translate_ledger_path(declaration)
        mapped = not is_unmapped(root)
        online = bool(mapped and root.is_dir() and root_online(root))
        row: dict[str, object] = {
            "location": location,
            "mapped": mapped,
            "online": online,
            "scanned": 0,
            "removed": 0,
            "errors": 0,
        }
        if not online:
            results.append(row)
            continue

        walk_errors: list[OSError] = []
        for directory, _subdirectories, _files in os.walk(
                root, topdown=False, onerror=walk_errors.append, followlinks=False):
            candidate = Path(directory)
            if candidate == root or candidate.is_symlink():
                continue
            row["scanned"] = int(row["scanned"]) + 1
            try:
                candidate.rmdir()
            except FileNotFoundError:
                # CloudDrive can remove the same empty directory concurrently.
                continue
            except OSError as error:
                if error.errno not in {errno.ENOTEMPTY, errno.EEXIST}:
                    row["errors"] = int(row["errors"]) + 1
            else:
                row["removed"] = int(row["removed"]) + 1
        row["errors"] = int(row["errors"]) + len(walk_errors)
        total_scanned += int(row["scanned"])
        total_removed += int(row["removed"])
        total_errors += int(row["errors"])
        results.append(row)
    return {
        "ok": total_errors == 0,
        "scanned": total_scanned,
        "removed": total_removed,
        "errors": total_errors,
        "sources": results,
    }


def _finish_purge(outcome):
    """Delete committed quarantine files; report any residue for explicit cleanup."""
    cleanup_pending = []
    for _original, quarantine in outcome.pop("_staged"):
        try:
            quarantine.unlink(missing_ok=True)
        except OSError as error:
            cleanup_pending.append({
                "path": str(quarantine), "reason": error.strerror or str(error),
            })
    for snapshot in outcome.pop("_snapshots"):
        try:
            snapshot.unlink(missing_ok=True)
        except OSError:
            pass
    source_roots = tuple(_online_source_roots().values())
    removed_directories: set[Path] = set()
    for parent in outcome.pop("_parents"):
        removed_directories.update(_remove_empty_ancestors(parent, source_roots))
    outcome["cleanup_pending"] = cleanup_pending
    outcome["empty_dirs_removed"] = len(removed_directories)
    return outcome


def purge_assets(connection, rows):
    """Quarantine media, delete ledger rows, and leave final removal to the caller.

    Renaming beside the source is reversible and stays on the same filesystem. The
    caller restores the quarantined names if commit fails, then permanently removes
    them only after the SQLite transaction has committed.
    """
    purged, blocked, staged, snapshots, parents = [], [], [], [], []
    for row in rows:
        media = row["path"]
        if media:
            original = Path(media)
            try:
                if original.exists() and not original.is_file():
                    raise OSError("not a regular file")
                if original.is_file():
                    quarantine = original.with_name(
                        f".{original.name}.peach-purge-{uuid.uuid4().hex}.tmp"
                    )
                    os.replace(original, quarantine)
                    staged.append((original, quarantine))
            except OSError as error:
                blocked.append({"id": row["id"], "path": media,
                                "reason": error.strerror or str(error)})
                continue
        snapshot = row["snapshot_path"]
        if snapshot:
            snapshots.append(Path(snapshot))
        if media:
            parents.append(Path(media).parent)
        purged.append(row["id"])
    try:
        if purged:
            marks = ",".join("?" * len(purged))
            connection.execute(
                f"UPDATE playlist SET current_asset_id=NULL WHERE current_asset_id IN ({marks})",
                purged,
            )
            connection.execute(
                f"UPDATE playlist SET source_seed_asset_id=NULL WHERE source_seed_asset_id IN ({marks})",
                purged,
            )
            for table in ASSET_REFERENCE_TABLES:
                connection.execute(f"DELETE FROM {table} WHERE asset_id IN ({marks})", purged)
            connection.execute(f"DELETE FROM asset WHERE id IN ({marks})", purged)
    except BaseException:
        _restore_staged_media(staged)
        raise
    return {
        "purged": len(purged), "blocked": blocked,
        "_staged": staged, "_snapshots": snapshots, "_parents": parents,
    }


def w_empty_trash(contract: WebContract):
    """永久清空回收站：只处理 disposal='trash' 的资产，其余一律不碰。"""
    contract.cache_bust()
    outcome = None
    try:
        with contract.write_transaction() as connection:
            rows = connection.execute(
                "SELECT id,path,snapshot_path FROM asset WHERE disposal='trash'",
            ).fetchall()
            outcome = purge_assets(connection, rows)
    except BaseException:
        if outcome is not None:
            _restore_staged_media(outcome["_staged"])
        raise
    result = {"ok": True, "operation": "empty-trash", **_finish_purge(outcome)}
    result.update(clean_resource_orphans(contract))
    return result


def w_cleanup_empty_directories(_contract: WebContract, _body):
    """Remove empty folders from online physical sources without touching the ledger."""
    return cleanup_empty_source_directories()




def w_batch(contract: WebContract, body):
    """Apply one explicit, reversible marker to a bounded selected set."""
    raw_ids = body.get("ids")
    if not isinstance(raw_ids, list):
        raise TypeError("ids must be a list")
    ids = list(dict.fromkeys(int(item) for item in raw_ids))
    if not ids or len(ids) > 200:
        raise ValueError("batch requires 1 to 200 assets")
    operation = body.get("operation")
    if operation not in {
        "like", "seen", "later", "dispose", "restore", "delete",
        "dismiss-junk", "reconsider-junk",
    }:
        raise ValueError("unsupported batch operation")
    marks = ",".join("?" * len(ids))
    contract.cache_bust()
    purge_outcome = None
    try:
        with contract.write_transaction() as connection:
            found = connection.execute(
                f"SELECT id,path,snapshot_path,disposal,location FROM asset WHERE id IN ({marks})", ids,
            ).fetchall()
            valid_ids = [row["id"] for row in found]
            if not valid_ids:
                raise ValueError("assets not found")
            if operation in {"restore", "delete"} and any(row["disposal"] != "trash" for row in found):
                raise ValueError("restore/delete is only allowed for recycle-bin assets")
            if operation in {"dismiss-junk", "reconsider-junk"} and any(
                    row["location"] not in {"local", "115", "pikpak"}
                    or row["disposal"] is not None for row in found):
                raise ValueError("junk decisions are only allowed for active physical assets")
            now = time.time()
            if operation == "restore":
                placeholders = ",".join("?" * len(valid_ids))
                connection.execute(
                    f"UPDATE asset SET disposal=NULL,feedback_at=? WHERE id IN ({placeholders})",
                    [now, *valid_ids],
                )
            elif operation == "delete":
                purge_outcome = purge_assets(connection, found)
            elif operation == "dismiss-junk":
                connection.executemany(
                    "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                    "VALUES('junk_file',?,'rejected','用户确认不是垃圾',?) "
                    "ON CONFLICT(category,item_key) DO UPDATE SET "
                    "status='rejected',note=excluded.note,updated_at=excluded.updated_at",
                    [(str(asset_id), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
                     for asset_id in valid_ids],
                )
            elif operation == "reconsider-junk":
                connection.executemany(
                    "DELETE FROM review_decision WHERE category='junk_file' AND item_key=?",
                    [(str(asset_id),) for asset_id in valid_ids],
                )
            elif operation in {"seen", "dispose"}:
                column, value = ("feedback", "seen") if operation == "seen" else ("disposal", "trash")
                placeholders = ",".join("?" * len(valid_ids))
                connection.execute(
                    f"UPDATE asset SET {column}=?,feedback_at=? WHERE id IN ({placeholders})",
                    [value, now, *valid_ids],
                )
            elif operation == "later":
                connection.executemany(
                    "INSERT OR IGNORE INTO watch_queue(profile_id,asset_id,added_at,source) "
                    f"VALUES('{DEFAULT_PROFILE_ID}',?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),'web-batch')",
                    [(asset_id,) for asset_id in valid_ids],
                )
            else:
                connection.executemany(
                    "INSERT INTO asset_preference(profile_id,asset_id,liked,reason,source,updated_at) "
                    f"VALUES('{DEFAULT_PROFILE_ID}',?,1,'','web-batch',strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
                    "ON CONFLICT(profile_id,asset_id) DO UPDATE SET liked=1,source='web-batch',"
                    "updated_at=excluded.updated_at",
                    [(asset_id,) for asset_id in valid_ids],
                )
    except BaseException:
        if purge_outcome is not None:
            _restore_staged_media(purge_outcome["_staged"])
        raise
    if purge_outcome is not None:
        result = {"ok": True, "operation": operation, **_finish_purge(purge_outcome)}
        result.update(clean_resource_orphans(contract))
        return result
    return {"ok": True, "operation": operation, "changed": len(valid_ids)}


def q_duplicates(contract: WebContract, args):
    """按番号 + 时长找真重复；每簇标出最大与最长的那个。"""
    limit = min(max(int(args.get("limit", "60")), 1), 300)
    offset = max(int(args.get("offset", "0")), 0)
    with contract.read_connection() as connection:
        rows = connection.execute(
            "SELECT id,code,location,path,name,size,duration,hash,disposal "
            "FROM asset WHERE medium='video' AND code IS NOT NULL AND code<>'' "
            "AND (disposal IS NULL OR disposal<>'trash')"
        ).fetchall()

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if not is_jav_code(row["code"]):
            continue
        item = dict(row)
        # 盘符只用于判定跨盘；重复项页面还要显示完整路径，不能在契约层丢掉。
        item["drive"] = str(item.get("path") or "")[:2].upper()
        grouped.setdefault(normalise_code_key(row["code"]), []).append(item)

    groups = []
    for code, items in grouped.items():
        if len(items) < 2:
            continue
        for cluster in duration_clusters(items):
            if len(cluster) < 2:
                continue
            largest = max(cluster, key=lambda x: x.get("size") or 0)
            longest = max(cluster, key=lambda x: x.get("duration") or 0)
            hashes_present = [x["hash"] for x in cluster if x["hash"]]
            hashes = set(hashes_present)
            for item in cluster:
                item["is_largest"] = item["id"] == largest["id"]
                item["is_longest"] = item["id"] == longest["id"]
                item.pop("hash", None)
                item.pop("disposal", None)
            groups.append({
                "code": code,
                "files": sorted(cluster, key=lambda x: -(x.get("size") or 0)),
                "count": len(cluster),
                # 必须每个文件都有 sha1 且完全相同才算确证字节一致。缺一个哈希
                # 就只是「时长相近」的推断，不能对外宣称已确证。
                "identical": len(hashes) == 1 and len(hashes_present) == len(cluster),
                "drives": sorted({x["drive"] for x in cluster}),
                "cross_drive": len({x["drive"] for x in cluster}) > 1,
                "reclaimable": sum(x.get("size") or 0 for x in cluster)
                - (largest.get("size") or 0),
            })
    groups.sort(key=lambda g: -g["reclaimable"])
    window = groups[offset:offset + limit]
    return {
        "total": len(groups),
        "files": sum(g["count"] for g in groups),
        "reclaimable": sum(g["reclaimable"] for g in groups),
        "groups": window,
        "has_more": offset + limit < len(groups),
    }
