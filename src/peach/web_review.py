"""复核队列：把带出处的候选摆到人面前，等一次明确的批准或否决。

从 `web_contract` 拆出。这一域读 `peach-data/generated` 下的候选 CSV、把它们和账本
现状比对、渲染成待复核行，并在用户批准后写真相字段——ADR-0006/0018 的闸门就落在
`w_review_decision` 与 `w_review_auto_apply` 这两处。

浏览域不需要知道候选文件长什么样，复核域也不需要知道首页怎么排序；它们过去只是
恰好住在同一个文件里。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import quote

from .catalog_rules import (
    collapse_superseded_taste_tags,
    normalise_code_key,
    superseded_taste_tags,
)
from .config import GENERATED_DIR
from .entities import (
    canonicalize_entity_name,
    collapse_repeated_entity_name,
    normalize_entity_name,
    resolve_entity,
    upsert_asset_entity,
)
from .metadata_policy import SOURCE_SPECS
from .review_csv import read_rows


class ReviewContract(Protocol):
    """复核需要契约提供的能力；比整个 WebContract 小得多。"""

    candidate_root: Path
    logo_root: Path
    avatar_root: Path

    def cache_bust(self) -> None: ...
    def read_connection(self): ...
    def has_cover(self, code: str) -> bool: ...
    def write_transaction(self): ...


# 候选文件名带批次日期，代码里只认前缀并永远取目录里实际最后写完的一份；
# 文件名允许附加主机/用途，不能用字典序冒充时间顺序。2026-08-30 的
# `...japanese-official-tags-20260827...` 就曾被更旧的 `...windows-p0-proof-20260822...`
# 盖住，导致新官方标签在复核页完全不可见。
CANDIDATE_PREFIX = {
    "metadata_fields": "metadata-field-candidates-",
    "creator_tags": "creator-tags-candidate-",
    "studio_logos": "studio-logo-candidate-",
    "performer_avatars": "performer-avatar-candidate-",
    # 这三类此前只落在 CSV 里没有界面入口，复核负担等于被丢回给用户去翻文件。
    "western_identity": "babepedia-candidates",
    "code_creators": "code-creator-review",
    "cover_sources": "cover-fetch-log",
    "fc2_markings": "fc2-candidate-log",
    "fc2_similarity": "fc2-similarity-candidate-",
    "video_endcards": "video-endcard-candidate-",
}
ADDITIONAL_CANDIDATE_FILES = {
    # 分区文件先于通用批次读取；同一个 item_key 出现时，窄范围的刷新证据应覆盖
    # 通用批次里的旧候选，而不是被 seen 去重静默吞掉。
    "metadata_fields": ("japanese-title-candidates.csv", "fc2-metadata-field-candidates.csv"),
}
# 每类候选的稳定主键列。缺这一列的行直接跳过并计数，绝不退化成行号——
# 行号会在 CSV 重排后把历史决定悄悄挪到别的条目上。
CANDIDATE_KEY = {
    "metadata_fields": "item_key",
    "creator_tags": "board",
    "studio_logos": "studio",
    "performer_avatars": "entity_id",
    "western_identity": "entity_id",
    "code_creators": "entity_id",
    "cover_sources": "code",
    "fc2_markings": "code",
    "fc2_similarity": "pair_key",
    "video_endcards": "candidate_key",
}
def _needs_review(category: str, row: dict) -> bool:
    """已经有定论的行不该占复核页。

    babepedia 那批 168 条里有 143 条是「确认无档案」——站上确实没有这个人，
    没有可判断的东西，全列出来只会把真正要看的 25 条淹掉。封面同理：拿到 2184
    宽的高清图不需要人确认，未取得和仍停在 800 低清基线的才需要。
    """
    if category == "western_identity":
        return str(row.get("verdict") or "") in ("命中", "需人工确认")
    if category == "studio_logos":
        # 无 handle、无落盘图片和与现有 Logo 完全相同都没有人工可判断项。
        # 只有新的/变化的确认来源，或明确标 needs_confirmation 的图片才进队列。
        saved = bool(str(row.get("saved") or "").strip())
        state = str(row.get("content_state") or "").strip()
        accepted = str(row.get("accepted") or "").lower() in {"1", "true", "yes"}
        needs_confirmation = row.get("confirmation") == "needs_confirmation"
        return saved and state not in {"unchanged", "duplicate", "rejected"} and (
            accepted or needs_confirmation
        )
    if category == "cover_sources":
        # 封面抓取的成功、尺寸和缺失都是机械状态，不需要人工批准。旧界面把
        # 241 个未取得和 800 px 基线封面全塞进复核页，却没有可执行写入动作。
        return False
    if category == "fc2_markings":
        # FC2 大多数作品页评论区是空的，全列出来会把真正有标记的几十条淹掉。
        # 只有拿到演员名、等价关系或判成合集的才需要人看。
        return bool(row.get("performers") or row.get("equivalents")
                    or row.get("is_collection"))
    return True


REVIEW_PREVIEW_LIMIT = 60
REVIEW_APPLY_LIMIT = 500


def latest_candidate_file(category: str, root: Path | None = None) -> Path | None:
    prefix = CANDIDATE_PREFIX.get(category)
    if not prefix:
        return None
    matches = list((root or GENERATED_DIR).glob(f"{prefix}*.csv"))
    if not matches:
        return None
    return max(matches, key=lambda path: (path.stat().st_mtime_ns, path.name))


def read_candidates(category: str, root: Path | None = None) -> tuple[list[dict], str | None, int]:
    """读取最新一批候选，返回（有稳定主键的行, 文件名, 被跳过的行数）。"""
    path = latest_candidate_file(category, root)
    base = root or GENERATED_DIR
    paths = [
        base / name for name in ADDITIONAL_CANDIDATE_FILES.get(category, ())
        if (base / name).is_file() and (path is None or base / name != path)
    ] + ([path] if path is not None and path.is_file() else [])
    if not paths:
        return [], None, 0
    key_column = CANDIDATE_KEY[category]
    rows, skipped, seen = [], 0, set()
    for candidate_path in paths:
        for row in read_rows(candidate_path):
            key = str(row.get(key_column) or "").strip()
            if not key:
                skipped += 1
                continue
            if key in seen:
                continue
            seen.add(key)
            row["item_key"] = key
            rows.append(row)
    return rows, "; ".join(candidate_path.name for candidate_path in paths), skipped


def _creator_entity_ids(connection, creators: list[str]) -> dict[str, int]:
    """创作者名（含别名）-> 规范 creator 实体 id；一次查完，不按候选逐个查。"""
    wanted = [name for name in dict.fromkeys(creators) if name]
    if not wanted:
        return {}
    marks = ",".join("?" * len(wanted))
    found: dict[str, int] = {}
    for row in connection.execute(
        "SELECT e.id,e.canonical_name,alias.alias FROM entity e "
        "LEFT JOIN entity_alias alias ON alias.entity_id=e.id "
        f"WHERE e.kind='creator' AND (e.canonical_name IN ({marks}) "
        f"OR alias.alias IN ({marks}))",
        [*wanted, *wanted],
    ):
        for name in (row["canonical_name"], row["alias"]):
            if name in wanted:
                found.setdefault(name, row["id"])
    return found


def _creator_previews(connection, creators: list[str]) -> dict[str, list[dict]]:
    """一次查完所有候选创作者的预览作品；按候选逐个查是 N+1。"""
    wanted = [name for name in dict.fromkeys(creators) if name]
    if not wanted:
        return {}
    marks = ",".join("?" * len(wanted))
    rows = connection.execute(
        "SELECT a.id,a.name,a.duration,e.canonical_name,alias.alias,a.creator FROM asset a "
        "LEFT JOIN asset_entity ae ON ae.asset_id=a.id AND ae.role='creator' "
        "LEFT JOIN entity e ON e.id=ae.entity_id AND e.kind='creator' "
        "LEFT JOIN entity_alias alias ON alias.entity_id=e.id "
        "WHERE a.medium='video' AND (a.disposal IS NULL OR a.disposal<>'trash') "
        "AND a.snapshot_path IS NOT NULL "
        f"AND (e.canonical_name IN ({marks}) OR alias.alias IN ({marks}) OR a.creator IN ({marks})) "
        "ORDER BY a.id",
        [*wanted, *wanted, *wanted],
    ).fetchall()
    previews: dict[str, list[dict]] = {name: [] for name in wanted}
    seen: dict[str, set] = {name: set() for name in wanted}
    for row in rows:
        for candidate in (row["canonical_name"], row["alias"], row["creator"]):
            bucket = previews.get(candidate)
            if bucket is None or len(bucket) >= REVIEW_PREVIEW_LIMIT or row["id"] in seen[candidate]:
                continue
            seen[candidate].add(row["id"])
            bucket.append({"id": row["id"], "name": row["name"], "duration": row["duration"]})
    return previews


def _attach_review_asset_context(connection, rows: list[dict]) -> None:
    """Attach one representative original video without per-row SQL queries."""
    codes = [str(row.get("code") or row.get("query") or "").strip()
             for row in rows]
    codes = [code for code in dict.fromkeys(codes) if code]
    assets_by_code: dict[str, dict] = {}
    if codes:
        marks = ",".join("?" * len(codes))
        sql = (
            "SELECT id,name,code,snapshot_path FROM asset WHERE medium='video' "
            "AND (disposal IS NULL OR disposal<>'trash') AND (code IN (" + marks + ")"
        )
        params: list[object] = list(codes)
        if any(code.upper().startswith("FC2") for code in codes):
            sql += " OR code LIKE 'FC2%'"
        sql += ") ORDER BY (snapshot_path IS NULL),id"
        for asset in connection.execute(sql, params):
            key = normalise_code_key(asset["code"])
            assets_by_code.setdefault(key, dict(asset))

    entity_ids = [int(row["entity_id"]) for row in rows
                  if str(row.get("entity_id") or "").isdigit()]
    assets_by_entity: dict[int, dict] = {}
    if entity_ids:
        marks = ",".join("?" * len(entity_ids))
        for asset in connection.execute(
            "SELECT ae.entity_id,a.id,a.name,a.code,a.snapshot_path "
            "FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
            f"WHERE ae.entity_id IN ({marks}) AND a.medium='video' "
            "AND (a.disposal IS NULL OR a.disposal<>'trash') "
            "ORDER BY (a.snapshot_path IS NULL),a.id",
            entity_ids,
        ):
            assets_by_entity.setdefault(asset["entity_id"], dict(asset))

    explicit_ids = {
        int(row["asset_id"]) for row in rows
        if str(row.get("asset_id") or "").isdigit()
    }
    comparison_ids = {
        int(value) for row in rows
        for value in (row.get("left_asset_id"), row.get("right_asset_id"))
        if str(value or "").isdigit()
    }
    comparison_assets: dict[int, dict] = {}
    requested_ids = comparison_ids | explicit_ids
    if requested_ids:
        marks = ",".join("?" * len(requested_ids))
        for asset in connection.execute(
            f"SELECT id,name,code,snapshot_path FROM asset WHERE id IN ({marks})",
            sorted(requested_ids),
        ):
            comparison_assets[asset["id"]] = dict(asset)

    for row in rows:
        code = str(row.get("code") or row.get("query") or "").strip()
        asset = assets_by_code.get(normalise_code_key(code)) if code else None
        entity_id = str(row.get("entity_id") or "")
        if asset is None and entity_id.isdigit():
            asset = assets_by_entity.get(int(entity_id))
        explicit_id = str(row.get("asset_id") or "")
        if asset is None and explicit_id.isdigit():
            asset = comparison_assets.get(int(explicit_id))
        if asset is None and row.get("preview_assets"):
            first = row["preview_assets"][0]
            asset = {"id": first["id"], "name": first["name"], "code": code,
                     "snapshot_path": True}
        if asset is None:
            pass
        else:
            row["asset_id"] = asset["id"]
            row["asset_name"] = asset["name"]
            row["asset_code"] = asset.get("code") or code
            row["asset_has_snapshot"] = bool(asset.get("snapshot_path"))
        row["comparison_assets"] = [
            comparison_assets[int(value)]
            for value in (row.get("left_asset_id"), row.get("right_asset_id"))
            if str(value or "").isdigit() and int(value) in comparison_assets
        ]


def _metadata_decision_is_stale(decision: dict, row: dict) -> bool:
    """旧批准是否已经不指向这一组里的任何一个现存候选。

    `metadata_fields` 的 `item_key` 是 `<番号>:<字段>`，不带候选身份。于是
    2026-09-01 对 r18dev「空日文标题」的一条 approved，会把之后 javbus 抓到的
    真标题一并盖住：队列里看不见这条，页面上还是英文标题。实测 TRE-080 就是
    这样卡住的，同批还有 24 个番号。判据与 `studio_logos` 的「上游内容变了就
    清掉旧判定」是同一条线，只是这里的「变了」体现为候选身份换了一个。

    只在能读出旧批准指向哪个候选时才判过期。note 不是 JSON（早期的自由文本
    留痕）就保守放过——宁可漏一条，也不要把用户已经批过的东西重新翻出来。
    """
    try:
        note = json.loads(str(decision.get("note") or ""))
    except (TypeError, ValueError):
        return False
    if not isinstance(note, dict):
        return False
    approved_key = str(note.get("candidate_key") or "").strip()
    if not approved_key:
        return False
    keys = {str(candidate.get("candidate_key") or "").strip()
            for candidate in row.get("candidates") or []}
    return bool(keys) and approved_key not in keys


def _review_rows(contract: ReviewContract, category: str) -> tuple[list[dict], str | None, int]:
    rows, source, skipped = read_candidates(category, contract.candidate_root)
    rows = [row for row in rows if _needs_review(category, row)]
    with contract.read_connection() as connection:
        decisions = {
            row["item_key"]: dict(row) for row in connection.execute(
                "SELECT item_key,status,note,updated_at FROM review_decision WHERE category=?",
                (category,),
            )
        }
        if category == "creator_tags":
            names = [str(row.get("creator") or "").strip() for row in rows]
            previews = _creator_previews(connection, names)
            # 这批候选判的是「这位创作者的作品该打什么标签」，主体是创作者本人。
            # 页面要给出创作者入口（头像 + 作品数），所以这里得把规范实体解析出来。
            entities = _creator_entity_ids(connection, names)
            for row in rows:
                name = str(row.get("creator") or "").strip()
                row["preview_assets"] = previews.get(name, [])
                row["entity_id"] = entities.get(name, "")
        elif category == "metadata_fields":
            for row in rows:
                try:
                    candidates = json.loads(str(row.get("candidates_json") or "[]"))
                except (TypeError, ValueError):
                    candidates = []
                row["candidates"] = [candidate for candidate in candidates
                                     if isinstance(candidate, dict)
                                     and str(candidate.get("candidate_key") or "").strip()]
            # 和账本已有的值比一遍，只把真差异留在队列里。实测 43 条候选里 24 条
            # 没有任何新信息：17 条与当前值逐字相同、7 条标签只是顺序不同。
            rows = [row for row in rows if _metadata_row_adds_information(connection, row)]
        elif category == "performer_avatars":
            # 候选 CSV 里的 `current_name` 是抓取来源给的罗马音；账本早就有更好的
            # 规范名（`Alice Shaku` 的规范名是 `释爱丽丝`），罗马音本身也已经登记
            # 为别名。复核页该显示账本认的那个名字，来源写法降为副标题。
            _use_canonical_entity_names(connection, rows)
        _attach_review_asset_context(connection, rows)
    for row in rows:
        decision = decisions.get(row["item_key"], {})
        if category == "studio_logos" and row.get("content_state") == "changed":
            # 同一厂牌上游头像变化是新的事实；旧批次 approved 不得把变化静默藏掉。
            decision = {}
        if (category == "metadata_fields" and decision.get("status") == "approved"
                and _metadata_decision_is_stale(decision, row)):
            decision = {}
        row["decision"] = decision.get("status", "pending")
        row["decision_note"] = decision.get("note", "")
        row["preview_url"] = (row.get("resolved_url") or row.get("source_url")
                              or row.get("avatar_url") or row.get("portrait_url") or "")
        if category == "video_endcards":
            frame = PurePosixPath(str(row.get("frame_key") or ""))
            asset_id = str(row.get("asset_id") or "")
            if (asset_id.isdigit() and len(frame.parts) == 2
                    and frame.parts[0] == asset_id and frame.suffix.lower() == ".png"):
                row["preview_url"] = (
                    f"/endcard-frame?id={asset_id}&name={quote(frame.name)}"
                )
        if category == "cover_sources" and row.get("result") == "取得":
            # 封面已经在本机，直接看落盘的那张，不要回源站再拉一次。
            row["preview_url"] = f"/cover?code={quote(str(row.get('code') or ''))}"
        asset_code = str(row.get("asset_code") or row.get("code") or "")
        if row.get("asset_id"):
            if asset_code and contract.has_cover(asset_code):
                row["asset_preview_url"] = f"/cover?code={quote(asset_code)}"
            elif row.get("asset_has_snapshot"):
                row["asset_preview_url"] = f"/poster?id={row['asset_id']}&c=4"
            else:
                row["asset_preview_url"] = ""
        for comparison in row.get("comparison_assets") or []:
            comparison_code = str(comparison.get("code") or "")
            if comparison_code and contract.has_cover(comparison_code):
                comparison["preview_url"] = f"/cover?code={quote(comparison_code)}"
            elif comparison.get("snapshot_path"):
                comparison["preview_url"] = f"/poster?id={comparison['id']}&c=4"
            else:
                comparison["preview_url"] = ""
            comparison.pop("snapshot_path", None)
        if not row.get("reason"):
            row["reason"] = _review_evidence(category, row)
    return _pending_first(rows), source, skipped


#: 元数据里的多值字段用顿号分隔；比较时按集合而不是按字符串。
MULTI_VALUE_FIELDS = {"performers", "tags"}


def _split_multi(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[、,，/|]", value or "") if part.strip()]


def _performer_identity_keys(connection, names: list[str]) -> frozenset:
    """把演员名折成身份键：能解析到实体的用实体 id，解析不到的保留原名。

    r18dev 给的是日文名，而账本规范名多数已本地化成中文——`桃谷エリカ` 与
    `桃谷绘里香` 实测就是同一条实体（日文名早已登记为别名）。按字符串比会把
    这类候选全判成「有差异」，批准反而把规范名倒退成别名。
    """
    keys = set()
    for name in names:
        # 官方源偶尔把曾用名写成「现名（旧名）」；整串当然匹配不到实体，但括号
        # 两边各自都是已登记别名。只在所有命中都指向同一实体时折叠，避免把真正
        # 的多人或同名冲突吞掉。
        variants = [name.strip()]
        match = re.fullmatch(r"\s*([^（(]+?)\s*[（(]([^）)]+)[）)]\s*", name)
        if match:
            variants.extend(part.strip() for part in match.groups() if part.strip())
        resolved = {
            row["id"] for variant in variants
            if (row := resolve_entity(connection, "performer", variant))
        }
        if resolved:
            keys.update(resolved)
        else:
            keys.add(normalize_entity_name(name))
    return frozenset(keys)


def _metadata_row_adds_information(connection, row: dict) -> bool:
    """这一行候选相对账本现值有没有新东西；没有就不该占复核队列。

    复核的成本是人的注意力：把「和现在一模一样」的行混在里面，真正要判的那些
    就被淹掉了（`_needs_review` 已经对封面和 babepedia 做过同样的取舍）。
    """
    current = str(row.get("current_value") or "").strip()
    if not current:
        return True                      # 补空值总是有信息，例如发行日期
    field = str(row.get("field") or "").strip()
    candidates = row.get("candidates") or []
    if not candidates:
        return False
    if field in MULTI_VALUE_FIELDS:
        if field == "performers":
            current_key = _performer_identity_keys(connection, _split_multi(current))
            return any(
                _performer_identity_keys(
                    connection, _split_multi(str(c.get("display_value") or ""))
                ) != current_key
                for c in candidates
            )
        current_set = frozenset(_split_multi(current))
        return any(
            frozenset(_split_multi(str(c.get("display_value") or ""))) != current_set
            for c in candidates
        )
    return any(str(c.get("display_value") or "").strip() != current for c in candidates)


def _use_canonical_entity_names(connection, rows: list[dict]) -> None:
    """把候选行的显示名换成账本规范名，来源写法留在 `source_name`。"""
    ids = [int(row["entity_id"]) for row in rows
           if str(row.get("entity_id") or "").strip().isdigit()]
    if not ids:
        return
    marks = ",".join("?" * len(ids))
    canonical = {row["id"]: row["canonical_name"] for row in connection.execute(
        f"SELECT id,canonical_name FROM entity WHERE id IN ({marks})", ids)}
    for row in rows:
        raw = str(row.get("entity_id") or "").strip()
        name = canonical.get(int(raw)) if raw.isdigit() else None
        shown = str(row.get("current_name") or "").strip()
        if name and name != shown:
            row["source_name"] = shown
            row["current_name"] = name


#: 可以不经人判断直接落库的字段。只放「补空且来源唯一」时确实无可判断的那些。
#: 演员和标签不在其中：那两类来源与账本的分歧是真实的（见 33 条噪音的核对）。
AUTO_APPLY_FIELDS = frozenset({"release_date"})


def metadata_auto_apply_candidate(connection, row: dict) -> dict | None:
    """这一行能否不经复核直接落库；不能就返回 None。

    四项必须同时成立，缺一项就仍然走人工：

    1. 目标字段当前为空——只补空，永不覆盖既有真相字段；
    2. 只有一个候选——有第二个值就存在取舍，那正是复核要做的事；
    3. 来源在当前 policy 下是 official / official_mirror；
    4. 番号在该番号名下**每一条**资产的文件名里逐字出现。

    第 4 条是这条捷径唯一的身份保证。刮削按番号取值，番号错则值错；文件名里
    逐字出现是本机可核验的证据，而复核界面其实给不了这个保证——它只并排显示
    番号和日期，并不告诉你番号跟这个文件对不对得上。

    `official` 一律按当前 policy 解析，不读候选 CSV 里的同名字段：那是抓取当时
    的快照，实测 r18dev 在 CSV 里写着 False，而现行 policy 认它是 official_mirror。
    """
    if str(row.get("field") or "").strip() not in AUTO_APPLY_FIELDS:
        return None
    if str(row.get("current_value") or "").strip():
        return None
    candidates = row.get("candidates") or []
    if len(candidates) != 1:
        return None
    candidate = candidates[0]
    spec = SOURCE_SPECS.get(str(candidate.get("source") or "").strip())
    if spec is None or not spec.official:
        return None
    code = str(row.get("code") or "").strip()
    query = str(row.get("query") or code).strip()
    if not code:
        return None
    names = [r["name"] for r in connection.execute(
        "SELECT name FROM asset WHERE medium='video' AND (upper(trim(code))=upper(?) "
        "OR upper(trim(code))=upper(?)) AND (disposal IS NULL OR disposal<>'trash')",
        (code, query))]
    if not names:
        return None
    folded = code.casefold()
    if not all(folded in str(name or "").casefold() for name in names):
        return None
    return candidate


def _pending_first(rows: list[dict]) -> list[dict]:
    """判过的不再占复核队列。

    早先这里原样返回全部候选，只给每行挂一个 `decision`，靠前端在本地把判过的
    行 splice 掉——于是「点通过」当场消失、一刷新全回来（厂牌 logo 上最明显）。
    队列该由服务端定义，前端只负责画。

    `approved` / `rejected` 是终局，直接移出；`跳过` 按字面意思是「稍后再看」，
    留在队列里但排到最后，否则一次跳过就等于永久隐藏，而界面上没有任何入口
    能把它找回来。
    """
    return sorted(
        (row for row in rows if row.get("decision") not in ("approved", "rejected")),
        key=lambda row: row.get("decision") == "skipped",
    )


def _review_evidence(category: str, row: dict) -> str:
    """给本身没有 reason 列的候选拼一句可判断的证据，别让复核页只剩一个名字。"""
    if category == "metadata_fields":
        current = str(row.get("current_value") or "").strip() or "尚无"
        return (f"当前值：{current}；{row.get('videos') or 0} 个同番号资产；"
                f"{len(row.get('candidates') or [])} 个来源候选")
    if category == "western_identity":
        overlap = row.get("token_overlap") or "0"
        variant = row.get("matched_variant") or ""
        spelling = f"（写法 {variant}）" if variant and variant != row.get("creator") else ""
        return (f"{row.get('verdict', '')} → {row.get('babepedia_name', '')}"
                f"{spelling}；词元重合 {overlap}；{row.get('videos', '')} 部作品")
    if category == "cover_sources":
        if row.get("result") != "取得":
            return f"未取得：{row.get('note') or '所有渠道都没有候选'}"
        return (f"{row.get('source', '')} · {row.get('width', '')}×{row.get('height', '')}"
                f" · {row.get('kb', '')} KB")
    if category == "fc2_markings":
        if row.get("is_collection"):
            return (f"合集，{row.get('collection_parts', '')} 个分片各自独立；"
                    f"封面不下发，分片回落到自己的缩略图")
        bits = []
        if row.get("performer_votes"):
            # 票数就是「几条独立评论这么说」，是这批候选唯一的置信度信号。
            bits.append(f"评论标记 {row.get('performer_votes')}")
        if row.get("equivalents"):
            bits.append(f"等同于 {row.get('equivalents')}")
        if row.get("writer"):
            bits.append(f"卖家 {row.get('writer')}")
        return "；".join(bits)
    if category == "fc2_similarity":
        kinds = str(row.get("evidence_kinds") or "").replace(" ", "、")
        detail = [f"证据 {kinds}" if kinds else "候选证据不足"]
        if row.get("duration_delta_seconds") != "":
            detail.append(f"时长差 {row.get('duration_delta_seconds')} 秒")
        if row.get("size_delta_percent") != "":
            detail.append(f"体积差 {row.get('size_delta_percent')}%")
        if row.get("shared_performers"):
            detail.append(f"共同演员 {row.get('shared_performers')}")
        if row.get("warnings"):
            detail.append(str(row.get("warnings")))
        return "；".join(detail)
    return ""


def q_review(contract: ReviewContract):
    with contract.read_connection() as connection:
        failures = [dict(row) for row in connection.execute(
            "SELECT id,name,location,path,duration FROM asset "
            "WHERE location='115' AND medium='video' AND snapshot_path IS NULL AND duration>2"
        )]
        decisions = {
            row["item_key"]: dict(row) for row in connection.execute(
                "SELECT item_key,status,note,updated_at FROM review_decision WHERE category='media_failure'"
            )
        }
    for row in failures:
        decision = decisions.get(str(row["id"]), {})
        row["item_key"] = str(row["id"])
        row["decision"] = decision.get("status", "pending")
        row["decision_note"] = decision.get("note", "")
        row["asset_id"] = row["id"]
        row["asset_name"] = row["name"]
        row["asset_preview_url"] = ""
    failures = _pending_first(failures)
    sections, sources, skipped = {}, {}, {}
    for category in CANDIDATE_PREFIX:
        rows, source, dropped = _review_rows(contract, category)
        sections[category] = rows
        sources[category] = source
        skipped[category] = dropped
    sections["media_failure"] = failures
    sources["media_failure"] = "ledger"
    # 候选文件缺失和主键缺失都要说出来。静默的空列表会被读成「没有待复核项」。
    return {"sections": sections, "sources": sources, "skipped_rows": skipped,
            "counts": {key: len(value) for key, value in sections.items()}}


def _selected_metadata_candidate(contract: ReviewContract, item_key: str, candidate_key: str) -> tuple[dict, dict]:
    groups = {row["item_key"]: row
              for row in read_candidates("metadata_fields", contract.candidate_root)[0]}
    group = groups.get(item_key)
    if group is None:
        raise ValueError("字段候选不在当前批次，无法批准")
    if str(group.get("status") or "").strip() != "candidate":
        raise ValueError("只有 candidate 状态的字段候选可以批准")
    try:
        candidates = json.loads(str(group.get("candidates_json") or "[]"))
    except (TypeError, ValueError) as exc:
        raise ValueError("字段候选 JSON 无效") from exc
    selected = next((candidate for candidate in candidates
                     if isinstance(candidate, dict)
                     and str(candidate.get("candidate_key") or "") == candidate_key), None)
    if selected is None:
        raise ValueError("所选来源值不在当前字段候选中")
    return group, selected


def _approved_entity_name(value: object, kind: str) -> str:
    name = str(value or "").strip()
    cleaned = canonicalize_entity_name(kind, name)
    if kind not in {"creator", "performer"}:
        cleaned = collapse_repeated_entity_name(cleaned)
    if not name or not cleaned or cleaned != name:
        raise ValueError("候选仍含重复或未规范化的实体名，拒绝写入")
    return cleaned


def _apply_metadata_candidate(connection, group: dict, candidate: dict, now: str) -> int:
    field = str(group.get("field") or "").strip()
    if field not in {
        "title", "original_title", "performers", "studio", "series", "release_date", "tags",
    }:
        raise ValueError("该元数据字段没有 Peach 写入映射")
    code = str(group.get("code") or "").strip()
    query = str(group.get("query") or code).strip()
    assets = connection.execute(
        "SELECT id FROM asset WHERE medium='video' AND (upper(trim(code))=upper(?) "
        "OR upper(trim(code))=upper(?)) AND (disposal IS NULL OR disposal<>'trash')",
        (code, query),
    ).fetchall()
    asset_ids = sorted({int(row["id"]) for row in assets})
    if not asset_ids:
        raise ValueError("当前 ledger 已没有这个番号的可用资产")
    if len(asset_ids) > REVIEW_APPLY_LIMIT:
        raise ValueError(f"同番号资产 {len(asset_ids)} 条，超过单次批准上限 {REVIEW_APPLY_LIMIT}")
    source = str(candidate.get("source") or "").strip()
    candidate_key = str(candidate.get("candidate_key") or "").strip()
    if not re.fullmatch(r"[a-z0-9_-]+", source) or not candidate_key:
        raise ValueError("字段候选来源无效")
    try:
        confidence = float(candidate.get("confidence"))
    except (TypeError, ValueError) as exc:
        raise ValueError("字段候选置信度无效") from exc
    if not 0 <= confidence <= 1:
        raise ValueError("字段候选置信度越界")
    metadata = {
        "provider": candidate.get("provider") or "javinizer-go", "source": source,
        "source_url": candidate.get("source_url"),
        "provider_id": candidate.get("provider_id"), "content_id": candidate.get("content_id"),
        "raw_snapshot": candidate.get("raw_snapshot"), "review_item": group["item_key"],
        "candidate_key": candidate_key,
    }
    marks = ",".join("?" * len(asset_ids))

    if field in {"title", "original_title"}:
        raw_value = str(candidate.get("value") or "")
        value = " ".join(raw_value.split())
        if (not value or len(value) > 1000
                or any(ord(char) < 32 for char in raw_value)):
            raise ValueError("标题候选为空、过长或含控制字符")
        column = "catalog_title" if field == "title" else "original_title"
        connection.execute(
            f"UPDATE asset SET {column}=? WHERE id IN ({marks})", (value, *asset_ids),
        )
        return len(asset_ids)

    if field == "release_date":
        value = str(candidate.get("value") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("发行日期候选必须是 YYYY-MM-DD")
        try:
            time.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("发行日期候选无效") from exc
        connection.execute(
            f"UPDATE asset SET release_date=? WHERE id IN ({marks})", (value, *asset_ids),
        )
        return len(asset_ids)

    if field in {"studio", "series"}:
        name = _approved_entity_name(candidate.get("value"), field)
        connection.execute(
            f"UPDATE asset SET {field}=? WHERE id IN ({marks})", (name, *asset_ids),
        )
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role=? "
            "AND source LIKE 'javinizer:%'",
            (*asset_ids, field),
        )
        for asset_id in asset_ids:
            upsert_asset_entity(
                connection, kind=field, name=name, asset_id=asset_id, role=field,
                source=f"javinizer:{source}:{field}", confidence=confidence,
                metadata=metadata, now=now,
            )
        return len(asset_ids)

    if field == "performers":
        raw_performers = candidate.get("value")
        if not isinstance(raw_performers, list):
            raise ValueError("演员候选必须是数组")
        performers: list[dict] = []
        seen: set[str] = set()
        for raw in raw_performers:
            if not isinstance(raw, dict):
                raise ValueError("演员候选条目无效")
            name = _approved_entity_name(raw.get("name"), "performer")
            normalized = normalize_entity_name(name)
            if normalized in seen:
                continue
            seen.add(normalized)
            performers.append({**raw, "name": name})
        if not performers:
            raise ValueError("演员候选为空")
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='performer' "
            "AND source LIKE 'javinizer:%'", asset_ids,
        )
        connection.execute(
            f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
            "AND source LIKE 'javinizer:%:performer'", asset_ids,
        )
        for asset_id in asset_ids:
            for performer in performers:
                name = performer["name"]
                external_id = str(performer.get("external_id") or "").strip()
                connection.execute(
                    "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)",
                    (asset_id, "演员:" + name, confidence, f"javinizer:{source}:performer"),
                )
                upsert_asset_entity(
                    connection, kind="performer", name=name, asset_id=asset_id,
                    role="performer", source=f"javinizer:{source}:performer",
                    confidence=confidence, external_provider=(source if external_id else None),
                    external_id=(external_id or None), metadata=metadata, now=now,
                )
        # 演员是 performer 真相，不回写 asset.creator；两种身份混写正是重复名称事故的来源之一。
        return len(asset_ids)

    raw_tags = candidate.get("value")
    if not isinstance(raw_tags, list):
        raise ValueError("标签候选必须是数组")
    tags = collapse_superseded_taste_tags(list(dict.fromkeys(
        _approved_entity_name(tag, "tag") for tag in raw_tags
    )))
    if not tags:
        raise ValueError("标签候选为空")
    obsolete_tags = superseded_taste_tags(tags)
    if obsolete_tags:
        obsolete_marks = ",".join("?" * len(obsolete_tags))
        obsolete_values = sorted(obsolete_tags)
        connection.execute(
            f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
            f"AND tag IN ({obsolete_marks})",
            [*asset_ids, *obsolete_values],
        )
        connection.execute(
            f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='tag' "
            f"AND entity_id IN (SELECT id FROM entity WHERE kind='tag' "
            f"AND canonical_name IN ({obsolete_marks}))",
            [*asset_ids, *obsolete_values],
        )
    connection.execute(
        f"DELETE FROM asset_entity WHERE asset_id IN ({marks}) AND role='tag' "
        "AND source LIKE 'javinizer:%'", asset_ids,
    )
    connection.execute(
        f"DELETE FROM asset_tag WHERE asset_id IN ({marks}) "
        "AND source LIKE 'javinizer:%:tag'", asset_ids,
    )
    for asset_id in asset_ids:
        for tag in tags:
            connection.execute(
                "INSERT INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?) "
                "ON CONFLICT DO UPDATE SET "
                "confidence=excluded.confidence,source=excluded.source",
                (asset_id, tag, confidence, f"javinizer:{source}:tag"),
            )
            upsert_asset_entity(
                connection, kind="tag", name=tag, asset_id=asset_id, role="tag",
                source=f"javinizer:{source}:tag", confidence=confidence,
                metadata=metadata, now=now,
            )
    return len(asset_ids)


#: 候选图的扩展名 -> content type。`/logo` 靠 `.ct` 边车决定回什么头。
LOGO_CONTENT_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".ico": "image/x-icon",
}


def studio_logo_key(studio: str) -> str:
    """和 `PreviewService.logo` 完全一致的落盘名，两边必须同一套规则。"""
    return re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]


#: 只记决定、不需要落地的类别，以及为什么。写在这里而不是靠人记：
#: `w_review_decision` 的每个落地分支都是手写的，把类别加进白名单却忘了写分支，
#: 表现就是「点通过、什么也没发生」——`creator_tags` 和 `studio_logos` 各犯过一次，
#: `performer_avatars` 是第三次。`test_every_approvable_category_can_land` 守住这条。
DECISION_ONLY_CATEGORIES = {
    "western_identity": "身份判断落在 entity 上，由专门的合并流程写，不在复核这一步",
    "code_creators": "番号与创作者的绑定由 metadata_fields 那条路写",
    "cover_sources": "封面已在 /cover 缓存里，复核只是确认取得与否",
    "fc2_markings": "只标注证据状态，不改真相字段",
    "fc2_similarity": "产出的是跨号候选，合并要另行授权",
    "video_endcards": "只登记首尾帧证据，不改资产",
    "media_failure": "只记录失败原因，供下一轮取证",
}


def _install_performer_avatar(contract: ReviewContract, entity_id: str) -> int:
    """把已批准的人物头像候选装进 `/entity-image` 真正读的目录。

    和 `_install_studio_logo` 同一个毛病、同一种修法：`performer_avatars` 一直只在
    分类白名单里，没有任何写入分支。审计脚本按设计只把外部图放进内容寻址缓存
    （「外部图只进入候选专用内容寻址缓存，不写 generated/avatars」），落地要人批准；
    而批准这一步什么也没做。结果是 18 个已判 ok 的候选——图早就下载好了，最大一张
    2880×1800——从 2026-08-25 起一直躺在缓存里进不去。

    按 sha256 定位缓存对象，并在装载前重算一遍校验：候选 CSV 的 `cache_path` 只是
    哈希名，路径可能过期，而内容寻址的意义就在于不必相信路径。缓存对象在
    provider-cache/performer-avatars/<provider>/objects 下按来源分目录——社媒与
    babepedia 管线（harvest_social_avatars.py）也走同一套缓存，装载按内容找，
    不绑定任何一个来源目录。

    落盘名跟着实体走（`{kind}-{id}.img`）：`/entity-image` 按 kind 分文件，creator
    实体（西方网黄，babepedia 命中的正是这批）写成 performer-<id>.img 是永远读不到的。
    """
    rows = {row["item_key"]: row
            for row in read_candidates("performer_avatars", contract.candidate_root)[0]}
    candidate = rows.get(str(entity_id))
    if candidate is None:
        raise ValueError("候选不在当前批次，无法批准")
    if str(candidate.get("verdict") or "").strip() != "ok":
        raise ValueError("只有质量判定为 ok 的候选可以装载")
    digest = str(candidate.get("sha256") or "").strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("候选没有可用的 SHA-256")
    objects_root = contract.candidate_root / "provider-cache" / "performer-avatars"
    source = next((item for item in objects_root.glob(f"*/objects/{digest}.*")
                   if item.is_file()), None)
    if source is None:
        raise ValueError(f"候选图片不在本机缓存：{digest[:12]}")
    body = source.read_bytes()
    if hashlib.sha256(body).hexdigest() != digest:
        raise ValueError("缓存对象与候选记录的哈希不一致，拒绝装载")
    content_type = str(candidate.get("mime_type") or "").strip() or "image/jpeg"
    contract.avatar_root.mkdir(parents=True, exist_ok=True)
    with contract.read_connection() as connection:
        kind_row = connection.execute(
            "SELECT kind FROM entity WHERE id=?", (int(entity_id),)).fetchone()
    kind = (kind_row[0] if kind_row and kind_row[0] in {"performer", "creator"}
            else "performer")
    destination = contract.avatar_root / f"{kind}-{int(entity_id)}.img"
    # 先写临时文件再原子替换：中途失败不会留下半张图被 `/entity-image` 读到。
    staging = destination.with_name(f"{destination.name}.{uuid.uuid4().hex}.tmp")
    staging.write_bytes(body)
    os.replace(staging, destination)
    Path(f"{destination}.ct").write_text(content_type, encoding="utf-8")
    Path(f"{destination}.provenance.json").write_text(json.dumps({
        "source": "performer avatar review",
        "provider": candidate.get("provider") or "",
        "source_url": candidate.get("source_url") or "",
        "external_id": candidate.get("external_id") or "",
        "matched_name": candidate.get("matched_name") or "",
        "name_source": candidate.get("name_source") or "",
        "sha256": digest,
        "width": candidate.get("width") or "",
        "height": candidate.get("height") or "",
        "policy_version": candidate.get("policy_version") or "",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "local performer identity cache",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1


def _install_studio_logo(contract: ReviewContract, studio: str) -> int:
    r"""把已批准的厂牌 logo 候选装进 `/logo` 真正读的目录。

    早先 `studio_logos` 只出现在分类白名单里，没有任何写入分支：点「通过」只往
    `review_decision` 记一笔，logo 一张也没装上——配合当时「队列不过滤已判项」的
    毛病，表现就是点完通过、一刷新原样又回来。

    候选 CSV 的 `saved` 列写的是 `R:\peach-data\...`，那是旧数据根；现在数据在
    `peach-data` 下，按绝对路径找必然落空。所以只取文件名，在当前候选目录里解析。
    """
    rows = {row["item_key"]: row
            for row in read_candidates("studio_logos", contract.candidate_root)[0]}
    candidate = rows.get(studio)
    if candidate is None:
        raise ValueError("候选不在当前批次，无法批准")
    saved = str(candidate.get("saved") or "").strip()
    if not saved:
        raise ValueError("该候选没有落盘的图片，无法装载")
    source = contract.candidate_root / "studio-logos" / PurePosixPath(
        saved.replace("\\", "/")).name
    if not source.is_file():
        raise ValueError(f"候选图片不在本机：{source.name}")
    key = studio_logo_key(studio)
    if not key:
        raise ValueError("厂牌名无法生成落盘名")
    content_type = LOGO_CONTENT_TYPES.get(source.suffix.lower())
    if content_type is None:
        raise ValueError(f"不支持的图片格式：{source.suffix}")
    contract.logo_root.mkdir(parents=True, exist_ok=True)
    destination = contract.logo_root / f"{key}.img"
    # 先写临时文件再原子替换：中途失败不会留下半张图被 `/logo` 读到。
    staging = destination.with_name(f"{destination.name}.{uuid.uuid4().hex}.tmp")
    staging.write_bytes(source.read_bytes())
    os.replace(staging, destination)
    Path(f"{destination}.ct").write_text(content_type, encoding="utf-8")
    Path(f"{destination}.provenance.json").write_text(json.dumps({
        "source": "studio logo review",
        "source_file": source.name,
        "resolved_url": candidate.get("resolved_url") or "",
        "handle": candidate.get("handle") or "",
        "platform": candidate.get("platform") or "",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "local studio identity cache",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1


def w_review_auto_apply(contract: ReviewContract, _body=None):
    """把确定的那部分直接落库，不占人工队列。

    ADR-0018：这是「刮削结果只作候选、不直接改写真相字段」的一个**窄例外**，
    不是废除该规则。判据见 `metadata_auto_apply_candidate`，四项缺一即回到人工。
    每条仍写 review_decision 留痕（note 里记来源与判据），所以事后可以追问
    「这个值是谁写的、凭什么」——留痕才是那条规则真正要保住的东西。
    """
    rows, _source, _skipped = read_candidates("metadata_fields", contract.candidate_root)
    applied, skipped = [], 0
    with contract.write_transaction() as connection:
        decided = {row["item_key"] for row in connection.execute(
            "SELECT item_key FROM review_decision WHERE category='metadata_fields'")}
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for row in rows:
            item_key = str(row.get("item_key") or "").strip()
            if not item_key or item_key in decided:
                continue
            if str(row.get("status") or "").strip() != "candidate":
                continue
            try:
                parsed = json.loads(str(row.get("candidates_json") or "[]"))
            except (TypeError, ValueError):
                continue
            row = dict(row)
            row["candidates"] = [c for c in parsed if isinstance(c, dict)
                                 and str(c.get("candidate_key") or "").strip()]
            candidate = metadata_auto_apply_candidate(connection, row)
            if candidate is None:
                skipped += 1
                continue
            try:
                count = _apply_metadata_candidate(connection, row, candidate, now)
            except ValueError:
                # 落库条件在这一刻不成立（例如资产已删）：回到人工，不记决定。
                skipped += 1
                continue
            connection.execute(
                "INSERT INTO review_decision(category,item_key,status,note,updated_at) "
                "VALUES('metadata_fields',?,'approved',?,?) "
                "ON CONFLICT(category,item_key) DO UPDATE SET status=excluded.status,"
                "note=excluded.note,updated_at=excluded.updated_at",
                (item_key, json.dumps({
                    "auto_applied": True, "rule": "adr-0018-empty-field-single-official-source",
                    "candidate_key": candidate.get("candidate_key"),
                    "source": candidate.get("source"),
                    "value": candidate.get("display_value"),
                }, ensure_ascii=False, separators=(",", ":")), now),
            )
            applied.append({"item_key": item_key, "field": row.get("field"),
                            "value": candidate.get("display_value"),
                            "assets": count})
    contract.cache_bust()
    return {"ok": True, "applied": len(applied), "left_to_review": skipped,
            "items": applied}


def w_review_decision(contract: ReviewContract, body):
    category = str(body.get("category", "")).strip()
    item_key = str(body.get("item_key", "")).strip()
    status = str(body.get("status", "")).strip()
    # 复核页展示的每个 tab 都必须能记录决定；漏掉一个，那一页的通过/跳过/拒绝就全部 400，
    # 前端静默时看起来就是「点了没反应」。`cover_sources` 曾这样漏掉。
    if category not in {
        "metadata_fields", "creator_tags", "studio_logos", "performer_avatars",
        "western_identity", "code_creators", "cover_sources", "fc2_markings",
        "fc2_similarity", "video_endcards", "media_failure",
    }:
        raise ValueError("invalid review category")
    if not item_key or status not in {"approved", "rejected", "skipped"}:
        raise ValueError("invalid review decision")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    note = str(body.get("note", "")).strip()[:2000]
    with contract.write_transaction() as connection:
        connection.execute(
            "INSERT INTO review_decision(category,item_key,status,note,updated_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(category,item_key) DO UPDATE SET status=excluded.status,note=excluded.note,updated_at=excluded.updated_at",
            (category, item_key, status, note, now),
        )
        applied = 0
        if category == "metadata_fields" and status == "approved":
            candidate_key = str(body.get("candidate_key") or "").strip()
            if not candidate_key:
                raise ValueError("批准字段候选时必须选择一个来源值")
            group, candidate = _selected_metadata_candidate(contract, item_key, candidate_key)
            applied = _apply_metadata_candidate(connection, group, candidate, now)
            provenance_note = json.dumps({
                "candidate_key": candidate_key, "source": candidate.get("source"),
                "user_note": note,
            }, ensure_ascii=False, separators=(",", ":"))
            connection.execute(
                "UPDATE review_decision SET note=? WHERE category=? AND item_key=?",
                (provenance_note, category, item_key),
            )
        elif category == "creator_tags" and status == "approved":
            # 权威值只能来自候选文件本身。早先版本直接采信请求体，于是「批准候选 X」
            # 可以写入与 X 无关的创作者和标签，而 review_decision 里留痕仍写着 X 通过。
            candidates = {row["item_key"]: row
                          for row in read_candidates(category, contract.candidate_root)[0]}
            candidate = candidates.get(item_key)
            if candidate is None:
                raise ValueError("候选不在当前批次，无法批准")
            if str(candidate.get("status") or "").strip() != "candidate":
                raise ValueError("只有 candidate 状态的复核项可以批准")
            creator = str(candidate.get("creator") or "").strip()
            tags = [tag.strip() for tag in str(candidate.get("tags") or "").split("|") if tag.strip()]
            claimed_creator = str(body.get("creator", "")).strip()
            claimed_tags = [tag.strip() for tag in str(body.get("tags", "")).split("|") if tag.strip()]
            if (claimed_creator and claimed_creator != creator) or (claimed_tags and claimed_tags != tags):
                raise ValueError("提交内容与候选不一致，拒绝写入")
            if not creator or not tags:
                raise ValueError("approved creator review requires creator and tags")
            entity = resolve_entity(connection, "creator", creator)
            if not entity:
                raise ValueError("creator entity not found")
            assets = connection.execute(
                "SELECT DISTINCT ae.asset_id FROM asset_entity ae JOIN asset a ON a.id=ae.asset_id "
                "WHERE ae.entity_id=? AND ae.role='creator' AND a.medium='video' AND a.disposal IS NULL",
                (entity["id"],),
            ).fetchall()
            selected_ids = {int(value) for value in body.get("selected_ids") or []}
            available_ids = {asset["asset_id"] for asset in assets}
            if selected_ids:
                if not selected_ids <= available_ids:
                    raise ValueError("selected assets are outside the reviewed creator")
                asset_ids = sorted(selected_ids)
            else:
                # 没有勾选就是「整条候选通过」。早先版本在这里什么都不写，
                # 却照样把决定记成 approved——留痕说通过、实际没写是最糟的组合。
                asset_ids = sorted(available_ids)
                if len(asset_ids) > REVIEW_APPLY_LIMIT:
                    raise ValueError(
                        f"该创作者有 {len(asset_ids)} 条作品，超过单次批准上限 "
                        f"{REVIEW_APPLY_LIMIT}，请在页面上显式勾选后再通过"
                    )
            payload = json.dumps({"review_item": item_key}, ensure_ascii=False)
            connection.executemany(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "VALUES(?,?,0.6,'vision_creator_review')",
                [(asset_id, tag) for asset_id in asset_ids for tag in tags],
            )
            for tag in tags:
                # 标签实体只解析一次，关系走 executemany。
                # 逐条调用 upsert_asset_entity 会在持写锁期间跑上千次往返，把其它写入全挡住。
                normalized = normalize_entity_name(tag)
                connection.execute(
                    "INSERT INTO entity(kind,canonical_name,normalized_name,metadata_json,"
                    "created_at,updated_at) VALUES('tag',?,?,'{}',?,?) "
                    "ON CONFLICT(kind,normalized_name) DO UPDATE SET "
                    "canonical_name=excluded.canonical_name,updated_at=excluded.updated_at",
                    (tag, normalized, now, now),
                )
                entity_id = connection.execute(
                    "SELECT id FROM entity WHERE kind='tag' AND normalized_name=?", (normalized,),
                ).fetchone()[0]
                connection.executemany(
                    "INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence,"
                    "metadata_json,first_seen_at,last_seen_at) "
                    "VALUES(?,?,'tag','vision_creator_review',0.6,?,?,?) "
                    "ON CONFLICT(asset_id,entity_id,role,source) DO UPDATE SET "
                    "confidence=excluded.confidence,metadata_json=excluded.metadata_json,"
                    "last_seen_at=excluded.last_seen_at",
                    [(asset_id, entity_id, payload, now, now) for asset_id in asset_ids],
                )
            applied = len(asset_ids)
        elif category == "studio_logos" and status == "approved":
            applied = _install_studio_logo(contract, item_key)
        elif category == "performer_avatars" and status == "approved":
            applied = _install_performer_avatar(contract, item_key)
    contract.cache_bust()   # 标签写完，聚合缓存必须失效，否则 facets 最多 90 秒还是旧数
    return {"ok": True, "category": category, "item_key": item_key, "status": status, "applied_assets": applied}
