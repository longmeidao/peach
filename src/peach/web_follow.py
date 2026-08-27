"""追更的 Web 契约层。

读接口无副作用；`/api/follow/check` 是唯一会联网的端点，且只在用户显式点击时触发。
`/api/follow/save` 写真相，走和 CLI 同一个 `save_asset(confirm=True)` 边界。
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

from .follow import FollowSourceError
from .follow_discovery import discover
from .follow_secrets import CredentialError, CredentialStore
from .follow_sources import (
    CONNECTORS, KemonoConnector, build_connector, canonical_source_ref,
    parse_source_url,
)
from .follow_store import FollowStore, ReleaseGroup
from .taste_history import read_creator_candidates


#: 界面上给每个来源的中文短名。没登记的 provider 直接显示原名。
PROVIDER_LABELS = {
    "fanbox": "FANBOX",
    "patreon": "Patreon",
    "subscribestar": "SubscribeStar",
    "kemono": "Kemono",
    "coomer": "Coomer",
    "pawchive": "Pawchive",
    "rule34video": "Rule34Video",
    "rule34xxx": "Rule34.xxx",
    "f95zone": "F95zone",
    "simpcity": "SimpCity",
}

_STATUSES = ("new", "seen", "saved", "ignored")
_BACKFILL_PROVIDERS = frozenset(
    {"kemono", "coomer", "pawchive", "rule34video", "rule34xxx"}
)


def _store(contract, connection) -> FollowStore:
    return FollowStore(lambda: connection, sources_root=contract.follow_sources_root)


#: 一条目最多给前端多少个 tag。筛选条是给人扫一眼用的，不是导出全部——
#: rule34.xxx 的热门帖能带上百个标签，整串发下去只会把筛选条撑爆。
MAX_ITEM_TAGS = 24

# 用户明确点名的既有超大合集。连接器现在会按详情页署名作者数拦截同类条目；这条
# 只让已经存在的旧候选立即从浏览面隐藏，不删除 ledger 行。
RULE34VIDEO_EXCLUDED_IDS = frozenset({"4533145"})

# 内容筛选不让载体/渲染方式挤掉动作、角色与作品标签。原始 metadata 仍完整保留。
LOW_VALUE_FOLLOW_TAGS = frozenset({
    "2d", "3d", "animated", "animation", "video", "tagme", "sound",
    "no sound", "audio", "loop", "webm", "mp4",
})

_IMAGE_MEDIA_RE = re.compile(r"\.(?:avif|gif|jpe?g|png|webp)(?:$|[?#])", re.I)
_VIDEO_MEDIA_RE = re.compile(r"\.(?:m4v|mov|mp4|og[gv]|webm)(?:/)?(?:$|[?#])", re.I)


def _item_tags(item) -> list[str]:
    """条目的真实标签。

    rule34.xxx 存空格分隔标签；Rule34Video 详情页存保留空格的标签列表和分类列表。
    kemono 系与 f95zone 的列表接口不给标签，所以它们是空列表。

    去掉作者手柄本身：按作者筛已经有专门的筛选条，标签里再出现一次没有信息量。
    """
    raw = item.metadata.get("tags")
    if isinstance(raw, str):
        values = raw.split()
    elif isinstance(raw, list):
        values = [str(value).strip() for value in raw if str(value).strip()]
    else:
        values = []
    categories = item.metadata.get("categories")
    if isinstance(categories, list):
        values.extend(str(value).strip() for value in categories if str(value).strip())
    subject = str(item.metadata.get("tag") or "").casefold()
    seen, tags = set(), []
    for tag in values:
        key = tag.casefold()
        if key == subject or key in seen or key in LOW_VALUE_FOLLOW_TAGS:
            continue
        seen.add(key)
        tags.append(tag)
        if len(tags) >= MAX_ITEM_TAGS:
            break
    return tags


def _item_tag_types(item, tags: list[str]) -> dict[str, str]:
    raw = item.metadata.get("tag_types")
    recorded = raw if isinstance(raw, dict) else {}
    allowed = {"artist", "character", "copyright", "metadata", "general"}
    return {
        tag: (str(recorded.get(tag)) if str(recorded.get(tag)) in allowed else "general")
        for tag in tags
    }


def _media_kind(item) -> str:
    recorded = str(item.metadata.get("media_kind") or "")
    if recorded == "video" or item.provider == "rule34video":
        return "video"
    media = str(item.media_url or "")
    if _IMAGE_MEDIA_RE.search(media):
        return "image"
    if _VIDEO_MEDIA_RE.search(media):
        return "video"
    return "external"


def _thumb_url(item) -> str | None:
    if item.thumb_url:
        return item.thumb_url
    # 旧的 Kemono/Pawchive 行在封面修复前已入库：media_url 是图片，但 thumb_url
    # 为空。按连接器同一条已验证规则即时推导缩略图，不改 ledger 就能补齐旧卡片。
    if item.provider in KemonoConnector.HOSTS and _IMAGE_MEDIA_RE.search(
            str(item.media_url or "")):
        parsed = urllib.parse.urlsplit(str(item.media_url))
        return f"https://{KemonoConnector.HOSTS[item.provider]}/thumbnail/data{parsed.path}"
    return None


def _excluded_item(item) -> bool:
    return (item.provider == "rule34video"
            and item.external_id in RULE34VIDEO_EXCLUDED_IDS)


def _item_payload(item) -> dict:
    tags = _item_tags(item)
    media_kind = _media_kind(item)
    return {
        "id": item.id,
        "provider": item.provider,
        "provider_label": PROVIDER_LABELS.get(item.provider, item.provider),
        "source_id": item.source_id,
        "source_label": item.source_label,
        "external_id": item.external_id,
        "title": item.title,
        "author": item.metadata.get("author") or None,
        "summary": item.metadata.get("summary") or None,
        "url": item.url,
        "thumb_url": _thumb_url(item),
        "published_at": item.published_at,
        # 界面必须照实显示精度：rule34video 只给「1 周前」，换算值不是发布时间。
        "published_precision": item.published_precision,
        "version": item.version,
        "duration": item.duration,
        "variant_kind": item.variant_kind,
        "variant_label": item.variant_label,
        "status": item.status,
        "asset_id": item.asset_id,
        "media_needs_credential": bool(item.metadata.get("media_needs_credential")),
        "has_media": bool(item.media_url),
        "media_kind": media_kind,
        "playable": bool(item.media_url) and media_kind in {"video", "image"}
                    and not bool(item.metadata.get("media_needs_credential")),
        "tags": tags,
        "tag_types": _item_tag_types(item, tags),
    }


def _group_payload(group: ReleaseGroup) -> dict:
    return {
        "release_key": group.release_key,
        "primary": _item_payload(group.primary),
        "variants": [_item_payload(item) for item in group.variants],
        "duplicates": [_item_payload(item) for item in group.duplicates],
        "providers": list(group.providers),
        "has_wip": group.has_wip,
        "is_release": group.is_release,
        "newest_at": group.newest_at,
    }


#: 标签里跟在中点后面的服务名。`LazyProcrastinator · fanbox` 和 rule34video 上的
#: `lazyprocrastinator` 是同一个人，中点后面那截只说明他在哪个平台连载。
_LABEL_SERVICE_RE = re.compile(r"\s*[·|]\s*[A-Za-z0-9_\-]+\s*$")
_AUTHOR_NOISE_RE = re.compile(r"[^0-9a-z一-鿿]+")
_F95_TITLE_SUFFIX_RE = re.compile(r"\s+collections?\s*$", re.IGNORECASE)


def _normalized_author_name(value: str, *, provider: str = "") -> str:
    stripped = _LABEL_SERVICE_RE.sub("", str(value or "").strip())
    if provider == "f95zone":
        # F95 thread titles describe a container, not a different author.  The real
        # data is ``Lazy Procrastinator Collection`` while every author source is
        # ``LazyProcrastinator``; retaining the generic suffix creates a false group.
        stripped = _F95_TITLE_SUFFIX_RE.sub("", stripped)
    return _AUTHOR_NOISE_RE.sub("", stripped.casefold())


def _author_display_name(row) -> str:
    """Return the readable author spelling carried by one follow source."""
    if row["entity_id"] and row["entity_name"]:
        return str(row["entity_name"])
    label = _LABEL_SERVICE_RE.sub("", str(row["label"] or row["ref"] or "").strip())
    if str(row["provider"] or "") == "f95zone":
        label = _F95_TITLE_SUFFIX_RE.sub("", label)
    return label.strip()


def _source_metadata(row) -> dict:
    try:
        payload = json.loads(row["metadata_json"] or "{}")
    except (KeyError, TypeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def author_key(row, aliases: dict[str, str] | None = None) -> str:
    """把一条来源归到「哪个作者」。

    这跟 ADR-0019 的变体分组**不是同一个轴**：那个是同一条发布的多个变体，
    这个是同一个作者在不同站点上的多条来源。用户在 Kemono 和 Pawchive 上关注的
    `LazyProcrastinator · fanbox`、在 Rule34Video 和 Rule34.xxx 上关注的
    `lazyprocrastinator`，是四条来源、一个人。

    实体已经绑上就用实体 id——那是规范身份，比名字可靠。没绑才退回名字归一化：
    去掉「· 服务名」后缀，再去掉大小写、空格、连字符这些不影响身份的噪声。
    归一化只做到这一步，不做模糊匹配：把两个碰巧相似的名字并成一个人，
    比让用户自己看到两行严重得多。
    """
    entity = row["entity_id"]
    if entity:
        return f"entity:{entity}"
    recorded = str(_source_metadata(row).get("author_key") or "").strip()
    if recorded:
        normalized = recorded
    else:
        label = str(row["label"] or row["ref"] or "")
        normalized = _normalized_author_name(label, provider=str(row["provider"] or ""))
    if normalized:
        normalized = (aliases or {}).get(normalized, normalized)
        return f"name:{normalized}"
    return f"source:{row['id']}"


def _follow_alias_state(connection) -> tuple[dict[str, str], list[dict]]:
    rows = connection.execute(
        "SELECT alias_key,alias_name,canonical_key,canonical_name,source "
        "FROM follow_author_alias ORDER BY canonical_name,alias_name"
    ).fetchall()
    mapping = {str(row["alias_key"]): str(row["canonical_key"]) for row in rows}
    groups: dict[str, dict] = {}
    for row in rows:
        canonical_key = str(row["canonical_key"])
        group = groups.setdefault(canonical_key, {
            "canonical_key": canonical_key,
            "canonical_name": str(row["canonical_name"]),
            "aliases": [],
        })
        if str(row["alias_key"]) != canonical_key:
            group["aliases"].append({
                "key": str(row["alias_key"]),
                "name": str(row["alias_name"]),
                "source": str(row["source"]),
            })
    return mapping, [group for group in groups.values() if group["aliases"]]


def _follow_alias_suggestions(rows, aliases: dict[str, str]) -> list[dict]:
    """Suggest conservative cross-platform aliases; never merge automatically."""
    identities: dict[str, dict] = {}
    for row in rows:
        if row["entity_id"]:
            continue
        raw_key = author_key(row).removeprefix("name:")
        if not raw_key or raw_key.startswith("source:"):
            continue
        identity = identities.setdefault(raw_key, {
            "key": raw_key, "name": _author_display_name(row), "providers": set(),
        })
        identity["providers"].add(str(row["provider"]))
        candidate_name = _author_display_name(row)
        if candidate_name and len(candidate_name) < len(identity["name"]):
            identity["name"] = candidate_name

    suggestions = []
    values = sorted(identities.values(), key=lambda item: item["key"])
    for index, left in enumerate(values):
        for right in values[index + 1:]:
            if aliases.get(left["key"], left["key"]) == aliases.get(
                    right["key"], right["key"]):
                continue
            shorter, longer = sorted((left, right), key=lambda item: len(item["key"]))
            if len(shorter["key"]) < 5 or shorter["key"] not in longer["key"]:
                continue
            suggestions.append({
                "canonical": shorter["name"],
                "alias": longer["name"],
                "evidence": "规范化名称存在包含关系，仅供人工确认",
            })
            if len(suggestions) >= 12:
                return suggestions
    return suggestions


def _avatar_url(provider: str, ref: str) -> str | None:
    """作者头像。**只有实测拿得到的来源才给，取不到就是 `None`。**

    2026-08-27 实测（`curl`，不带凭据）：
    `https://kemono.cr/icons/fanbox/30917150` → 302 → `img.kemono.cr`，
    200 `image/webp` 160×160；`pawchive.pw` 同路径 200、14,534 字节。
    coomer.st 对这个创作者回 404，但那只说明他不在 coomer 上，
    不能据此断定 coomer 没有这个端点——所以 coomer 照样按同一规则给 URL，
    取不到时由 `<img onerror>` 收场。

    rule34video / rule34.xxx **未取得**：没有可用的作者页样本可测，不猜一个路径。
    取不到头像时界面显示站点缩写，不用首字母假装成头像。
    """
    if provider not in KemonoConnector.HOSTS:
        return None
    service, _, user = str(ref or "").partition("/")
    if not service or not user:
        return None
    return f"https://{KemonoConnector.HOSTS[provider]}/icons/{service}/{user}"


def _official_avatar_url(provider: str, ref: str) -> str | None:
    """Local resolver for an avatar from the creator's official profile.

    FANBOX archive refs carry the Pixiv user id, which is enough for Peach's fixed-host
    resolver to locate the public FANBOX profile and its official ``user.iconUrl``.
    Other services have no verified resolver yet, so they keep the archive fallback.
    """
    if provider not in KemonoConnector.HOSTS:
        return None
    service, _, user = str(ref or "").partition("/")
    if service != "fanbox" or not user.isdigit():
        return None
    return "/follow-avatar?" + urllib.parse.urlencode({"service": service, "id": user})


def _source_payload(row, aliases: dict[str, str] | None = None) -> dict:
    return {
        "id": row["id"],
        "provider": row["provider"],
        "provider_label": PROVIDER_LABELS.get(row["provider"], row["provider"]),
        "ref": row["ref"],
        "label": row["label"],
        "author_key": author_key(row, aliases),
        "official_avatar_url": _official_avatar_url(row["provider"], row["ref"]),
        "avatar_url": _avatar_url(row["provider"], row["ref"]),
        "url": row["url"],
        "semantics": row["semantics"],
        "enabled": bool(row["enabled"]),
        "entity_id": row["entity_id"],
        "entity_name": row["entity_name"],
        "can_backfill": row["provider"] in _BACKFILL_PROVIDERS,
        # 往回抓到哪一页了（0 起，0 = 只抓过第一页）。界面据此说清进度，
        # 否则用户点一次只看到列表变长一点，不知道自己走到第几页。
        "backfill_page": row["backfill_page"],
        "last_checked_at": row["last_checked_at"],
        "last_status": row["last_status"],
        "last_error": row["last_error"],
    }


def q_follow(contract, args) -> dict:
    statuses = tuple(
        value for value in str(args.get("status") or "").split(",") if value in _STATUSES
    )
    try:
        limit = max(1, min(int(args.get("limit") or 200), 1000))
    except (TypeError, ValueError):
        limit = 200
    source = args.get("source")
    source_id = int(source) if str(source or "").isdigit() else None
    with contract.database.read_connection() as connection:
        store = _store(contract, connection)
        source_rows = store.sources()
        alias_map, author_aliases = _follow_alias_state(connection)
        sources = [_source_payload(row, alias_map) for row in source_rows]
        alias_suggestions = _follow_alias_suggestions(source_rows, alias_map)
        items = tuple(item for item in store.items(
            statuses=statuses, source_id=source_id, limit=limit)
            if not _excluded_item(item))
        groups = [_group_payload(group) for group in store.group(items)]
        counts = dict(connection.execute(
            "SELECT status, count(*) FROM follow_item GROUP BY status").fetchall())
        excluded_marks = ",".join("?" for _ in RULE34VIDEO_EXCLUDED_IDS)
        excluded_counts = connection.execute(
            "SELECT i.status, count(*) FROM follow_item i"
            " JOIN follow_source s ON s.id=i.source_id"
            f" WHERE s.provider='rule34video' AND i.external_id IN ({excluded_marks})"
            " GROUP BY i.status",
            tuple(RULE34VIDEO_EXCLUDED_IDS),
        ).fetchall()
        for status, count in excluded_counts:
            counts[status] = max(0, int(counts.get(status, 0)) - int(count))
    suggestions = _suggestions(contract, sources)
    return {
        "ok": True,
        "sources": sources,
        "author_aliases": author_aliases,
        "alias_suggestions": alias_suggestions,
        "suggestions": suggestions,
        "groups": groups,
        "counts": {status: int(counts.get(status, 0)) for status in _STATUSES},
        "providers": sorted(CONNECTORS),
    }


#: 「猜你喜欢」一次给多少个。这是给人挑的，不是导出全部。
MAX_SUGGESTIONS = 12


def _suggestions(contract, sources) -> list[dict]:
    """「猜你喜欢」取**浏览历史品味分析**产出的创作者候选，按访问次数排序。

    之前两次都取错了源，记下来免得再犯：`facets.creators` 是「他有谁的文件」，
    `location='online'` 的资产是「他关注过谁」，两者都不是「他常搜谁」。真正的信号是
    `scripts/taste_history.py` 从 Chrome/Safari/Zen/Google Takeout 的历史里分析出来的
    `taste-creator-candidates-*.csv`——用户举的两个名字在那里分别排第 1 和第 3
    （`lazyprocrastinator` 28 次、`ffxivinitiala` 13 次）。

    分析没跑过就没有建议，不拿别的数据顶替。
    """
    followed = {str(row["label"]).casefold() for row in sources}
    picked = []
    for row in read_creator_candidates(contract.taste_history_root,
                                       limit=MAX_SUGGESTIONS * 4):
        name = row["name"]
        if name.casefold() in followed:
            continue
        picked.append({"name": name, "visits": row["visits"],
                       "origin": row["sources"]})
        if len(picked) >= MAX_SUGGESTIONS:
            break
    return picked


def _write_item_ids(body) -> list[int]:
    item_id = body.get("item")
    item_ids = body.get("items")
    if isinstance(item_id, int):
        return [item_id]
    if isinstance(item_ids, list) and 0 < len(item_ids) <= 1000:
        if not all(isinstance(value, int) for value in item_ids):
            raise ValueError("items must contain only integer follow item ids")
        return list(dict.fromkeys(item_ids))
    raise ValueError("item must be an integer follow item id or items a non-empty list")


def w_follow_status(contract, body) -> dict:
    item_ids = _write_item_ids(body)
    status = str(body.get("to") or "")
    with contract.database.write_transaction() as connection:
        store = _store(contract, connection)
        for item_id in item_ids:
            store.set_status(item_id, status)
    result = {"ok": True, "items": item_ids, "status": status}
    if len(item_ids) == 1:
        result["item"] = item_ids[0]
    return result


def w_follow_save(contract, body) -> dict:
    item_ids = _write_item_ids(body)
    with contract.database.write_transaction() as connection:
        store = _store(contract, connection)
        asset_ids = [store.save_asset(item_id, confirm=True) for item_id in item_ids]
    result = {"ok": True, "items": item_ids, "asset_ids": asset_ids}
    if len(item_ids) == 1:
        result.update({"item": item_ids[0], "asset_id": asset_ids[0]})
    return result


def w_follow_check(contract, body) -> dict:
    """显式检查更新。这是唯一会向站点发请求的端点。

    没有 `source` 就检查全部已启用来源。逐个来源独立成败：一个来源缺凭据或被
    机器人验证挡住，不该让其余来源的更新一起消失。
    """
    requested = body.get("source")
    source_id = requested if isinstance(requested, int) else None
    # 往回抓一页。这是**显式的、一次一页**的动作：常规检查永远只看第一页，
    # 因为追更关心的是增量；但那也意味着每个来源只有第一页那点内容
    # （rule34video 的作者页一页 24 条，实际 61 页）。用户点一次，往前挪一页。
    older = bool(body.get("older"))
    credentials = _credential_store(contract)
    results: list[dict] = []
    with contract.database.read_connection() as connection:
        rows = [dict(row) for row in _store(contract, connection).sources(enabled_only=True)
                if (source_id is None or row["id"] == source_id)
                and (not older or row["provider"] in _BACKFILL_PROVIDERS)]
    for row in rows:
        moment = datetime.now(timezone.utc)
        provider, ref = row["provider"], row["ref"]
        page = (row["backfill_page"] + 1) if older else 0
        try:
            connector = build_connector(provider, credential=credentials.load(provider))
            fetch = connector.fetch(ref, etag=row["etag"],
                                    last_modified=row["last_modified"], page=page)
        except CredentialError as error:
            results.append(_failure(contract, row, error, moment, "unauthorized"))
            continue
        except FollowSourceError as error:
            results.append(_failure(contract, row, error, moment, "error"))
            continue
        with contract.database.write_transaction() as connection:
            store = _store(contract, connection)
            outcome = store.record(
                row["id"], fetch,
                creator_aliases=store.creator_aliases(row["entity_id"]), moment=moment,
                page=page)
        results.append({
            "source": row["id"], "provider": provider,
            "provider_label": PROVIDER_LABELS.get(provider, provider),
            "ref": ref, "label": row["label"], "ok": True,
            # 这次读的是第几页，以及往回还剩没剩。界面据此说「已经抓到第 N 页」，
            # 而不是让用户点了一次不知道自己走到哪儿了。
            "page": page, "older": older,
            "not_modified": outcome.not_modified, "discovered": outcome.discovered,
            "added": outcome.added, "updated": outcome.updated,
            # 抓到了但判为「不是 release」而丢掉的条数。丢了多少必须说出来，
            # 否则用户分不清少的是被过滤掉的还是根本没抓到——这次问「为什么这么少」
            # 就是因为界面从来没说过这类数字。
            "skipped": fetch.skipped,
            "skipped_compilations": fetch.skipped_compilations,
            # 列表判不出来、额外抓了详情页的条数。这是唯一会放大请求数的路径。
            "probed": fetch.probed,
            # 证据没存下来不算检查失败，但界面必须说出来，不能悄悄少一份原始响应。
            "evidence_error": outcome.evidence_error,
        })
    return {"ok": True, "checked": len(results), "results": results}


def _failure(contract, row, error, moment, status) -> dict:
    with contract.database.write_transaction() as connection:
        _store(contract, connection).record_error(
            row["id"], str(error), moment, status=status)
    # 界面按人看得懂的站名和来源标签报失败，不让用户去猜 `rule34xxx` 是哪个站。
    return {"source": row["id"], "provider": row["provider"],
            "provider_label": PROVIDER_LABELS.get(row["provider"], row["provider"]),
            "ref": row["ref"], "label": row["label"],
            "ok": False, "status": status, "error": str(error)}


def _resolve_label(contract, parsed, credential) -> str:
    """尽量把标签换成人看得懂的名字。

    kemono 系有 profile 端点，一次请求就能把 `30917150 · fanbox` 换成创作者名；
    取不到就保留从链接推出来的标签，不猜。
    """
    if parsed.provider not in KemonoConnector.HOSTS:
        return parsed.label
    connector = KemonoConnector(provider=parsed.provider, credential=credential)
    service, _, user = parsed.ref.partition("/")
    try:
        response = connector._get(
            f"https://{connector.host}/api/v1/{service}/user/{user}/profile")
        if response.status != 200:
            return parsed.label
        name = (connector._json(response) or {}).get("name")
    except (FollowSourceError, CredentialError):
        return parsed.label
    return f"{name} · {service}" if name else parsed.label


def w_follow_source(contract, body) -> dict:
    """粘一条来源链接就登记，并立刻检查一次。

    登记成功但首次检查失败不算失败：来源已经在列表里，错误显示在它那一行上——
    rule34.xxx 缺 key 就是这种情况，把它整个回滚掉反而让人不知道发生了什么。
    """
    action = str(body.get("action") or "add")
    if action == "remove":
        source_id = body.get("id")
        if not isinstance(source_id, int):
            raise ValueError("id must be an integer follow source id")
        with contract.database.write_transaction() as connection:
            connection.execute("DELETE FROM follow_source WHERE id=?", (source_id,))
        return {"ok": True, "removed": source_id}
    if action == "enabled":
        source_id = body.get("id")
        enabled = body.get("enabled")
        if not isinstance(source_id, int) or not isinstance(enabled, bool):
            raise ValueError("id must be an integer and enabled must be a boolean")
        with contract.database.write_transaction() as connection:
            store = _store(contract, connection)
            exists = any(row["id"] == source_id for row in store.sources())
            if not exists:
                raise ValueError("这个关注来源不存在")
            store.set_enabled(source_id, enabled)
        return {"ok": True, "source": source_id, "enabled": enabled}
    if action != "add":
        raise ValueError(f"unknown follow source action: {action}")

    parsed = parse_source_url(str(body.get("url") or ""))
    credentials = _credential_store(contract)
    credential = credentials.load(parsed.provider)
    label = str(body.get("label") or "").strip() or _resolve_label(
        contract, parsed, credential)
    author_hint = str(body.get("author") or "").strip()
    author_hint = _normalized_author_name(author_hint) if author_hint else ""
    metadata = {"author_key": author_hint} if author_hint else None
    with contract.database.write_transaction() as connection:
        source_id = _store(contract, connection).register(
            provider=parsed.provider, ref=parsed.ref, label=label, url=parsed.url,
            semantics=parsed.semantics, metadata=metadata)
    checked = w_follow_check(contract, {"source": source_id})
    outcome = next((row for row in checked["results"]
                    if row["source"] == source_id), None)
    return {"ok": True, "source": source_id, "provider": parsed.provider,
            "ref": parsed.ref, "label": label, "checked": outcome}


def w_follow_author_alias(contract, body) -> dict:
    """Add or remove a user-confirmed cross-platform follow-author alias."""
    action = str(body.get("action") or "add")
    if action == "remove":
        alias_name = str(body.get("alias") or "").strip()
        alias_key = _normalized_author_name(alias_name)
        if not alias_key:
            raise ValueError("别名不能为空")
        with contract.database.write_transaction() as connection:
            row = connection.execute(
                "SELECT canonical_key FROM follow_author_alias WHERE alias_key=?",
                (alias_key,),
            ).fetchone()
            if row is None:
                raise ValueError("这个作者别名不存在")
            if str(row["canonical_key"]) == alias_key:
                raise ValueError("规范名不能作为别名移除")
            connection.execute(
                "DELETE FROM follow_author_alias WHERE alias_key=?", (alias_key,))
            _, groups = _follow_alias_state(connection)
        return {"ok": True, "removed": alias_name, "author_aliases": groups}
    if action != "add":
        raise ValueError(f"unknown follow author alias action: {action}")

    canonical_name = str(body.get("canonical") or "").strip()
    alias_name = str(body.get("alias") or "").strip()
    canonical_key = _normalized_author_name(canonical_name)
    alias_key = _normalized_author_name(alias_name)
    if not canonical_key or not alias_key:
        raise ValueError("规范作者名和平台别名都不能为空")
    if canonical_key == alias_key:
        raise ValueError("这两个名字归一化后相同，不需要维护别名")

    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with contract.database.write_transaction() as connection:
        mapping, _ = _follow_alias_state(connection)
        canonical_root = mapping.get(canonical_key, canonical_key)
        alias_root = mapping.get(alias_key, alias_key)
        if canonical_root != alias_root:
            connection.execute(
                "UPDATE follow_author_alias SET canonical_key=?,canonical_name=?,updated_at=? "
                "WHERE canonical_key=?",
                (canonical_root, canonical_name, stamp, alias_root),
            )
        connection.execute(
            "INSERT INTO follow_author_alias(alias_key,alias_name,canonical_key,"
            "canonical_name,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(alias_key) DO UPDATE SET canonical_key=excluded.canonical_key,"
            "canonical_name=excluded.canonical_name,alias_name=excluded.alias_name,"
            "source=excluded.source,updated_at=excluded.updated_at",
            (canonical_root, canonical_name, canonical_root, canonical_name,
             "manual", stamp, stamp),
        )
        connection.execute(
            "INSERT INTO follow_author_alias(alias_key,alias_name,canonical_key,"
            "canonical_name,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(alias_key) DO UPDATE SET canonical_key=excluded.canonical_key,"
            "canonical_name=excluded.canonical_name,alias_name=excluded.alias_name,"
            "source=excluded.source,updated_at=excluded.updated_at",
            (alias_key, alias_name, canonical_root, canonical_name,
             "manual", stamp, stamp),
        )
        _, groups = _follow_alias_state(connection)
    return {"ok": True, "canonical": canonical_name, "alias": alias_name,
            "author_aliases": groups}


#: 一次最多解析多少行。粘一屏链接是正常的，粘一整个书签导出不是。
MAX_RESOLVE_LINES = 40


def _candidate_payload(candidate, *, author: str = "") -> dict:
    return {"provider": candidate.provider,
            "provider_label": PROVIDER_LABELS.get(candidate.provider, candidate.provider),
            "ref": canonical_source_ref(candidate.provider, candidate.ref),
            "url": candidate.url, "label": candidate.label, "author": author,
            "semantics": candidate.semantics, "evidence": candidate.evidence}


def _external_search_payload(search) -> dict:
    return {"provider": search.provider,
            "provider_label": PROVIDER_LABELS.get(search.provider, search.provider),
            "label": search.label, "query": search.query,
            "url": search.url, "evidence": search.evidence}


def w_follow_resolve(contract, body) -> dict:
    """把粘进来的每一行解析成「可以添加什么」，但**不添加**。

    一行是链接就直接认；不是链接就当成名字或 id 拿去各来源查一遍。两种都只返回结果，
    由人勾选之后再调 `/api/follow/source` 落地——发现要联网，结果也可能不止一个，
    自动登记等于替用户做决定。
    """
    raw = body.get("lines")
    if isinstance(raw, str):
        raw = raw.splitlines()
    if not isinstance(raw, list):
        raise ValueError("lines must be a list of strings")
    lines = [str(line).strip() for line in raw if str(line).strip()]
    if not lines:
        raise ValueError("没有可解析的内容")
    if len(lines) > MAX_RESOLVE_LINES:
        raise ValueError(f"一次最多解析 {MAX_RESOLVE_LINES} 行，收到 {len(lines)} 行")

    known = {(row["provider"], canonical_source_ref(row["provider"], row["ref"])) for row in
             (_source_payload(r) for r in _existing_sources(contract))}
    results = []
    for line in lines:
        try:
            parsed = parse_source_url(line)
        except FollowSourceError as url_error:
            if "://" in line or "/" in line:
                # 看着就是链接，那就照链接的错误报，不要再拿去当名字查一遍。
                results.append({"line": line, "kind": "error", "error": str(url_error)})
                continue
            try:
                found = discover(line, secrets_root=contract.follow_secrets_root,
                                 state_root=contract.follow_state_root)
            except (FollowSourceError, CredentialError) as term_error:
                results.append({"line": line, "kind": "error", "error": str(term_error)})
                continue
            results.append({
                "line": line, "kind": "term",
                "candidates": [{**_candidate_payload(c, author=line),
                                "known": (c.provider, canonical_source_ref(
                                    c.provider, c.ref)) in known}
                               for c in found.candidates],
                "failures": found.failures,
                "external_searches": [_external_search_payload(search)
                                      for search in found.external_searches],
            })
            continue
        results.append({"line": line, "kind": "url",
                        "candidates": [{**_candidate_payload(parsed),
                                        "known": (parsed.provider, canonical_source_ref(
                                            parsed.provider, parsed.ref)) in known}]})
    return {"ok": True, "results": results}


def _existing_sources(contract):
    with contract.database.read_connection() as connection:
        return _store(contract, connection).sources()


#: 每个来源要不要凭据、要哪些字段、去哪里拿。写在这里而不是模板里，因为知道
#: 「rule34.xxx 缺 key 就抓不到」的是连接器边界，不是界面。
CREDENTIAL_GUIDE: dict[str, dict] = {
    "kemono": {"requirement": "none"},
    "coomer": {"requirement": "none"},
    "pawchive": {"requirement": "none"},
    "rule34video": {"requirement": "none"},
    "rule34xxx": {
        "requirement": "required",
        "fields": ["user_id", "api_key"],
        # 账号级、与机器无关，用户明确要求跨机同步。
        "syncable": ["user_id", "api_key"],
        "why": "网页版挂了 Cloudflare 验证码，Peach 不绕验证码，只能走官方 API。",
        "where": "https://rule34.xxx/index.php?page=account&s=options",
        "howto": "登录后在账号设置页生成 API key，把 user_id 和 api_key 写进凭据文件。",
    },
    "f95zone": {
        "requirement": "optional",
        "fields": ["cookie"],
        # cookie 绑会话与客户端 IP，同步到另一台大概率直接失效——不同步。
        "syncable": [],
        "why": "发现更新不需要登录；只有取附件和 masked 下载链接才需要会话。",
        "where": "https://f95zone.to/",
        "howto": "登录后从浏览器复制整条 Cookie 请求头，写进凭据文件的 cookie 字段。",
    },
    "simpcity": {
        "requirement": "blocked",
        "why": "站点由 DDoS-Guard 的浏览器质询保护，放行绑客户端 IP 且最短 20 分钟过期，"
               "撑不起定时追更。Peach 不绕机器人验证。",
    },
}


def w_follow_credential(contract, body) -> dict:
    """保存一个来源的凭据，写到**运行 Peach 的那台机器**的 secrets 目录。

    值只从请求体流向磁盘，**不回显、不记日志、不进任何返回体**。只接受
    `CREDENTIAL_GUIDE` 里声明过的 provider 和字段名——多余的字段一律拒绝，
    免得把任意内容写进 secrets 目录。

    **权限收紧只在 POSIX 上真的发生。** Windows 的 `os.chmod` 只能拨动只读位，
    NTFS 的权限走 ACL，落盘就是继承来的 0o666——所以那里不假装收紧过，
    `describe()` 的 `world_readable` 也照实报 `None`。要在 Windows 上真正收紧
    得走 ACL（icacls/pywin32 断继承），那需要在那台机器上实测验证才能落地，
    当前**未取得**，不写没验过的安全代码。
    """
    provider = str(body.get("provider") or "")
    guide = CREDENTIAL_GUIDE.get(provider)
    if guide is None or not guide.get("fields"):
        raise ValueError(f"{provider or '(空)'} 不接受凭据")
    values = body.get("values")
    if not isinstance(values, dict):
        raise ValueError("values must be an object")
    allowed = set(guide["fields"])
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValueError(f"{provider} 不认识这些字段：{', '.join(unknown)}")
    cleaned = {name: str(values[name]).strip() for name in guide["fields"]
               if str(values.get(name) or "").strip()}
    store = _credential_store(contract)
    path = store.path_for(provider)
    if not cleaned:
        # 全部留空 = 撤掉这份凭据。**本机和共享副本一起撤**：只删本机的话，
        # `load()` 会从共享副本把 key 重新拼回来，而共享副本还会跟着 peach-sync
        # 传到另一台，变成哪台都撤不掉。共享盘不在就如实说，不静默跳过。
        outcome = store.clear(provider)
        return {"ok": True, "provider": provider, "cleared": True,
                "shared_cleared": outcome["shared"],
                "note": CLEAR_NOTES.get(str(outcome["shared"]), ""),
                "saved": store.describe(provider)}
    _write_secret(path, cleaned)
    shared_written = _write_shared(store, provider, cleaned)
    # 返回的是 describe()，只有字段名，没有值。
    return {"ok": True, "provider": provider, "cleared": False,
            # 界面据此说明「这台机器上没有收紧文件权限」，而不是默认收紧过。
            "permissions_tightened": os.name != "nt",
            "synced": shared_written,
            "saved": store.describe(provider)}


#: 撤销后要不要多说一句。共享副本删掉了或压根没有都不必打扰用户；
#: 只有「盘不在、这次只撤掉了本机」必须说出来，否则用户以为撤干净了。
CLEAR_NOTES = {
    "offline": "共享盘不在，只撤掉了本机这份。等盘回来要再撤一次，否则会被同步回来。",
}


def _write_secret(path, values: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    if os.name != "nt":
        os.chmod(temporary, 0o600)
    temporary.replace(path)


def _write_shared(store, provider: str, values: dict) -> bool:
    """把**声明为可同步的**字段写一份到共享副本。

    只写声明过的字段：共享副本会跟着 `peach-sync` 走 SMB 并进备份，把不该出去的
    东西写进去就再也收不回来。共享盘不可达时静默跳过——凭据在本机已经存好了，
    同步失败不该让保存失败。
    """
    shared = store.shared_path_for(provider)
    syncable = set(store.syncable(provider))
    if shared is None or not syncable:
        return False
    payload = {name: value for name, value in values.items() if name in syncable}
    if not payload:
        return False
    try:
        if not store.shared_online():
            return False
        _write_secret(shared, payload)
    except OSError:
        return False
    return True


#: 哪些字段可以跨机同步，逐 provider 逐字段声明。绝不按字段名猜——今天 `api_key`
#: 能同步、`cookie` 不能，明天新增一个 `session_token` 就会落到错误的一侧。
SYNCABLE_FIELDS: dict[str, tuple[str, ...]] = {
    provider: tuple(guide.get("syncable", ()))
    for provider, guide in CREDENTIAL_GUIDE.items()
}


def _credential_store(contract) -> CredentialStore:
    return CredentialStore(contract.follow_secrets_root,
                           shared_root=contract.follow_shared_root,
                           syncable_fields=SYNCABLE_FIELDS)


def q_follow_credentials(contract, _args) -> dict:
    """报告凭据状态和怎么配。只给字段名与文件路径，绝不返回凭据值。"""
    store = _credential_store(contract)
    providers = []
    for provider in sorted(CONNECTORS):
        described = store.describe(provider)
        guide = CREDENTIAL_GUIDE.get(provider, {"requirement": "none"})
        fields = guide.get("fields", [])
        providers.append({
            **described,
            "provider_label": PROVIDER_LABELS.get(provider, provider),
            "requirement": guide["requirement"],
            "needs": fields,
            "missing": [name for name in fields if name not in described["fields"]],
            "why": guide.get("why", ""),
            "where": guide.get("where", ""),
            "howto": guide.get("howto", ""),
            "path": str(store.path_for(provider)),
            "example": (json.dumps({name: "…" for name in fields}, ensure_ascii=False)
                        if fields else ""),
        })
    return {"ok": True, "root": str(store.root), "providers": providers}
