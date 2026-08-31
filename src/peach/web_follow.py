"""追更的 Web 契约层。

读接口无副作用；`/api/follow/check` 是唯一会联网的端点，可由用户点击或已启用的
APScheduler 任务触发。
`/api/follow/save` 写真相，走和 CLI 同一个 `save_asset(confirm=True)` 边界。
"""
from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

from . import follow_providers
from .follow import FollowHistoryEnd, FollowSourceError
from .follow_discovery import discover
from .follow_secrets import CredentialError, CredentialStore
from .follow_sources import (
    CONNECTORS, KemonoConnector, build_connector, canonical_source_ref,
    f95_attachment_media_items, parse_source_url, resource_links,
)
from .follow_store import FollowStore, ReleaseGroup
from .taste_history import read_creator_candidates


#: 界面上给每个来源的中文短名。没登记的 provider 直接显示原名。
PROVIDER_LABELS = follow_providers.labels()

_STATUSES = ("new", "seen", "saved", "ignored")

#: 关注库整库取回的上限。筛选要在 Python 里做（见 follow 载荷的注释），
#: 所以这里不是分页，只是别让一个失控的库把内存吃干的护栏。
_ALL_ITEMS = 100_000
_BACKFILL_PROVIDERS = follow_providers.backfill_providers()
_OFFICIAL_IDENTITY_PROVIDERS = follow_providers.official_identity_providers()


def _store(contract, connection) -> FollowStore:
    return FollowStore(lambda: connection, sources_root=contract.follow_sources_root)


#: 一条目最多给前端多少个 tag。筛选条是给人扫一眼用的，不是导出全部——
#: rule34.xxx 的热门帖能带上百个标签，整串发下去只会把筛选条撑爆。
MAX_ITEM_TAGS = 24

# 用户明确点名的既有超大合集。连接器现在会按详情页署名作者数拦截同类条目；这条
# 只让已经存在的旧候选立即从浏览面隐藏，不删除 ledger 行。
RULE34VIDEO_EXCLUDED_IDS = frozenset({"4533145"})

# 内容筛选不让载体/渲染方式挤掉动作、角色与作品标签。原始 metadata 仍完整保留。
LOW_VALUE_GENERAL_TAGS = frozenset({
    "video", "tagme", "sound",
    "no sound", "audio", "loop", "webm", "mp4",
})

# 关注页的标签是「里面发生了什么」，不是人物计数、身体部位、画幅、年份或场景。
# 来源类型是第一道门槛：只有来源明确标成 general 的标签才会走到这里；形态判据
# 只负责 general 内部的通用词清理，绝不能拿它猜 artist/metadata 等来源类型。
_NON_CONTENT_FOLLOW_TAG_RE = re.compile(
    r"^(?:"
    r"(?:19|20)\d{2}|\d{1,2}:\d{1,2}|"
    r"\d+[_\s-]*(?:boy|girl|futa)s?|female|male|male/female|female_only|"
    r"(?:light[-_\s]?skinned[_\s-]?)?(?:female|male)|human|"
    r"(?:nude|naked)(?:[_\s-](?:female|male))?|"
    r"(?:(?:large|big|medium|small|bouncing)[_\s-])?"
    r"(?:breasts?|ass|pussy|penis|vagina|nipples?|areolae)|"
    r"(?:blonde|black|white|long|short)[_\s-](?:hair|female)|"
    r"(?:blue|green|brown)[_\s-]eyes|light[_\s-]skin|"
    r"(?:shorter|longer)[_\s-]than[_\s-]\d+[_\s-]seconds|short[_\s-]video|"
    r"beach"
    r")$", re.I,
)

_IMAGE_MEDIA_RE = re.compile(r"\.(?:avif|gif|jpe?g|png|webp)(?:$|[?#])", re.I)
_VIDEO_MEDIA_RE = re.compile(r"\.(?:m4v|mov|mp4|og[gv]|webm)(?:/)?(?:$|[?#])", re.I)
_RULE34XXX_PREVIEW_RE = re.compile(
    r"^https://api-cdn\.rule34\.xxx/thumbnails/(\d+)/thumbnail_"
    r"([0-9a-f]{32})\.jpg(?:[?#].*)?$", re.I)


def _item_all_tags(item) -> list[str]:
    """Return every recorded source tag once, preserving source spelling."""
    raw = item.metadata.get("tags")
    if isinstance(raw, str):
        values = raw.split()
    elif isinstance(raw, list):
        values = [str(value).strip() for value in raw if str(value).strip()]
    else:
        values = []
    for field in ("categories", "models"):
        recorded = item.metadata.get(field)
        if isinstance(recorded, list):
            values.extend(str(value).strip() for value in recorded if str(value).strip())
    seen, result = set(), []
    for value in values:
        tag = html.unescape(value)
        key = tag.casefold()
        if not tag or key in seen:
            continue
        seen.add(key)
        result.append(tag)
    return result


def _recorded_tag_type(item, tag: str) -> str:
    raw = item.metadata.get("tag_types")
    if not isinstance(raw, dict):
        return ""
    value = raw.get(tag)
    if value is None:
        key = tag.casefold()
        value = next((candidate for name, candidate in raw.items()
                      if html.unescape(str(name)).casefold() == key), None)
    tag_type = str(value or "").casefold()
    return tag_type if tag_type in {
        "artist", "character", "copyright", "metadata", "general"
    } else ""


def _item_tags(item) -> list[str]:
    """条目的内容标签。

    rule34.xxx 存空格分隔标签；Rule34Video 详情页存保留空格的标签列表和分类列表。
    kemono 系与 f95zone 的列表接口不给标签，所以它们是空列表。

    实体在这里统一反转义：rule34.xxx 的 dapi 曾把 `miqo&#039;te` 这类转义形态
    直接写进 metadata，归一后旧行照常显示与筛选，也和反转义后的新写法并成
    同一个身份。unescape 是幂等的，对已干净的标签不起作用。

    去掉作者手柄本身：按作者筛已经有专门的筛选条，标签里再出现一次没有信息量。
    """
    values = _item_all_tags(item)
    subject = html.unescape(str(item.metadata.get("tag") or "")).casefold()
    seen, tags = set(), []
    for tag in values:
        key = tag.casefold()
        # 来源没给类型时宁可暂不放进卡片，也不把 unknown 猜成 general。
        if (_recorded_tag_type(item, tag) != "general"
                or key == subject or key in seen or key in LOW_VALUE_GENERAL_TAGS
                or _NON_CONTENT_FOLLOW_TAG_RE.fullmatch(tag.strip())):
            continue
        seen.add(key)
        tags.append(tag)
        if len(tags) >= MAX_ITEM_TAGS:
            break
    return tags


def _item_tag_types(item, tags: list[str]) -> dict[str, str]:
    return {tag: tag_type for tag in tags
            if (tag_type := _recorded_tag_type(item, tag))}


def _media_kind(item) -> str:
    recorded = str(item.metadata.get("media_kind") or "")
    if recorded in {"video", "image"}:
        return recorded
    if item.provider == "rule34video":
        return "video"
    media = str(item.media_url or "")
    if _IMAGE_MEDIA_RE.search(media):
        return "image"
    if _VIDEO_MEDIA_RE.search(media):
        return "video"
    return "external"


def _video_media_type(value: object) -> str:
    path = urllib.parse.urlsplit(str(value or "")).path.casefold()
    if path.endswith(".webm"):
        return "video/webm"
    if path.endswith(".mov"):
        return "video/quicktime"
    return "video/mp4"


def _media_items(item) -> list[dict]:
    """给浏览器媒体序号和展示字段；真实上游 URL 仍只留在服务端 metadata。"""
    raw = item.metadata.get("media_items")
    if not isinstance(raw, list) or not raw:
        raw = f95_attachment_media_items(item.metadata) if item.provider == "f95zone" else []
    result = []
    for index, media in enumerate(raw):
        if not isinstance(media, dict):
            continue
        kind = str(media.get("media_kind") or "")
        if kind not in {"video", "image"}:
            continue
        thumb = str(media.get("thumb_url") or "")
        result.append({
            "index": index,
            "name": str(media.get("name") or f"{kind} {index + 1}"),
            "media_kind": kind,
            "media_type": _video_media_type(media.get("name") or media.get("url"))
                          if kind == "video" else None,
            "thumb_url": thumb if thumb.startswith("https://") else None,
            "size": media.get("size"),
            "resource_provider": str(media.get("resource_provider") or ""),
            "resource_group": str(media.get("resource_group") or "") or None,
            "resource_group_label": str(media.get("resource_group_label") or "") or None,
        })
    return result


def _archive_media_host(provider: str, url: str) -> str:
    """把归档站的静态资源指到 `img.` 子域。

    2026-08-30 实测（见 docs/reference-snapshots/kemono-archive-media-host.md）：

        kemono.cr/thumbnail/data/<path>        302
        img.kemono.cr/thumbnail/data/<path>    200 image/jpeg 24,050 B
        pawchive.pw/thumbnail/data/<path>      404
        img.pawchive.pw/thumbnail/data/<path>  200 image/gif   12,796 B

    kemono 主域只是重定向，浏览器跟随后仍能显示，所以一直没人发现；pawchive 主域
    直接 404，卡片因此永远是空的（`onerror` 把 img 摘掉，看起来像"没有预览图"）。
    连接器里那条注释记的是 2026-08-27 主域回 200——站点行为后来变了。

    在读取时改写而不是改 ledger：坏 URL 已经写进两千多行，而这是可推导的投影，
    不是真相字段。站点再变时也只需要改这一处。
    """
    host = KemonoConnector.HOSTS.get(provider)
    if not host or not url.startswith(f"https://{host}/"):
        return url
    return url.replace(f"https://{host}/", f"https://img.{host}/", 1)




def _thumb_url(item) -> str | None:
    # rule34.xxx 的历史行存的是 250px preview。官方 dapi 的 sample_url 与它使用
    # 同一 bucket/hash；2026-08-28 对生产历史行实测推导后为 1920x1080。
    if item.provider == "rule34xxx" and item.thumb_url:
        matched = _RULE34XXX_PREVIEW_RE.match(str(item.thumb_url))
        if matched:
            return ("https://api-cdn.rule34.xxx/images/"
                    f"{matched.group(1)}/{matched.group(2)}.jpg")
    # Paheal 图片直接经现有同源代理读原图；视频站点没有高清 poster，改由
    # /follow-cover 抽首帧并缓存。两条路径都不把原始媒体 URL放进公共 JSON。
    if item.provider == "rule34paheal" and item.media_url:
        kind = _media_kind(item)
        if kind == "image":
            return f"/follow-stream?id={item.id}"
        if kind == "video":
            return f"/follow-cover?id={item.id}"
    if item.thumb_url:
        return _archive_media_host(item.provider, str(item.thumb_url))
    # 旧的 Kemono/Pawchive 行在封面修复前已入库：media_url 是图片，但 thumb_url
    # 为空。按连接器同一条已验证规则即时推导缩略图，不改 ledger 就能补齐旧卡片。
    if item.provider in KemonoConnector.HOSTS and _IMAGE_MEDIA_RE.search(
            str(item.media_url or "")):
        parsed = urllib.parse.urlsplit(str(item.media_url))
        return _archive_media_host(
            item.provider,
            f"https://{KemonoConnector.HOSTS[item.provider]}/thumbnail/data{parsed.path}")
    return None


def _f95_has_resource(media_url: str | None, metadata: dict) -> bool:
    if media_url:
        return True
    links = metadata.get("links")
    if isinstance(links, list) and resource_links(
            "\n".join(str(value) for value in links)):
        return True
    attachments = metadata.get("attachments")
    if isinstance(attachments, list):
        return any(
            str(value).startswith("https://")
            and not _IMAGE_MEDIA_RE.search(str(value))
            for value in attachments
        )
    return False


def _excluded_item(item) -> bool:
    if (item.provider == "rule34video"
            and item.external_id in RULE34VIDEO_EXCLUDED_IDS):
        return True
    # 旧版曾把纯讨论和图片表情包写进候选。读取时隐藏，不改 ledger；真正的
    # 文件附件与文件站链接仍保留，下一次检查会按当前证据重新归类。
    return (item.provider == "f95zone"
            and not _f95_has_resource(item.media_url, item.metadata))


def _item_payload(item, credential_providers: frozenset[str] = frozenset()) -> dict:
    tags = _item_tags(item)
    detail_tags = _item_all_tags(item)
    media_kind = _media_kind(item)
    media_items = _media_items(item)
    if media_items:
        media_kind = media_items[0]["media_kind"]
    recorded_links = item.metadata.get("links")
    safe_resource_urls = resource_links(
        "\n".join(str(value) for value in recorded_links)
        if isinstance(recorded_links, list) else ""
    )
    needs_credential = bool(item.metadata.get("media_needs_credential"))
    credential_ready = not needs_credential or item.provider in credential_providers
    playable = (media_kind in {"video", "image"}
                and ((bool(media_items) and credential_ready)
                     or (bool(item.media_url) and not needs_credential)))
    return {
        "id": item.id,
        "provider": item.provider,
        "provider_label": PROVIDER_LABELS.get(item.provider, item.provider),
        "source_id": item.source_id,
        "source_label": item.source_label,
        "external_id": item.external_id,
        # 旧 rule34xxx 行的标题由带实体的标签拼成（`barnabas&#039; mother`）；
        # 出口统一反转义，与 _item_tags 同一处理，unescape 幂等。
        "title": html.unescape(item.title) if item.title else item.title,
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
        "media_needs_credential": needs_credential,
        "media_error": str(item.metadata.get("media_error") or "") or None,
        "has_media": bool(item.media_url) or bool(media_items),
        "media_kind": media_kind,
        "media_type": _video_media_type(item.media_url)
                      if media_kind == "video" else None,
        # 可直接读取的附件与仍需会话解析的外链可以同时存在。后者不能把
        # 前者整体锁死；详情继续复用同一条 /follow-stream 媒体代理路径。
        "playable": playable,
        "media_items": media_items,
        # 只投影连接器已验证过的文件页域名；原始媒体 URL 仍不进入 feed。
        "resource_urls": safe_resource_urls,
        "tags": tags,
        "detail_tags": detail_tags,
        "tag_types": _item_tag_types(item, detail_tags),
    }


def _group_payload(group: ReleaseGroup,
                   credential_providers: frozenset[str] = frozenset()) -> dict:
    return {
        "release_key": group.release_key,
        "primary": _item_payload(group.primary, credential_providers),
        "variants": [_item_payload(item, credential_providers)
                     for item in group.variants],
        "duplicates": [_item_payload(item, credential_providers)
                       for item in group.duplicates],
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


def _author_display_text(value: str) -> str:
    """Remove container/service wording that is not part of an author name."""
    stripped = _LABEL_SERVICE_RE.sub("", str(value or "").strip())
    return _F95_TITLE_SUFFIX_RE.sub("", stripped).strip()


def _author_display_name(row) -> str:
    """Return the readable author spelling carried by one follow source."""
    if row["entity_id"] and row["entity_name"]:
        return str(row["entity_name"])
    return _author_display_text(row["label"] or row["ref"] or "")


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
            # 旧别名记录可能把 F95 的容器标题保存成规范显示名；只修正读投影，
            # 不在这个只读接口里偷偷改真实表。
            "canonical_name": _author_display_text(row["canonical_name"]),
            "aliases": [],
        })
        if str(row["alias_key"]) != canonical_key:
            group["aliases"].append({
                "key": str(row["alias_key"]),
                "name": str(row["alias_name"]),
                "source": str(row["source"]),
            })
    return mapping, [group for group in groups.values() if group["aliases"]]


def _upsert_follow_author_alias(connection, canonical_name: str, alias_name: str,
                                *, source: str) -> dict | None:
    """Persist one alias without letting automatic evidence overwrite a decision.

    Manual confirmation may deliberately regroup an existing alias. Automatic learning is
    narrower: it only fills a previously unknown platform handle and leaves every existing
    mapping, especially a manual one, untouched.
    """
    canonical_key = _normalized_author_name(canonical_name)
    alias_key = _normalized_author_name(alias_name)
    if not canonical_key or not alias_key:
        raise ValueError("规范作者名和平台别名都不能为空")
    if canonical_key == alias_key:
        raise ValueError("这两个名字归一化后相同，不需要维护别名")

    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    mapping, _ = _follow_alias_state(connection)
    canonical_root = mapping.get(canonical_key, canonical_key)
    alias_root = mapping.get(alias_key, alias_key)
    if source != "manual":
        existing = connection.execute(
            "SELECT 1 FROM follow_author_alias WHERE alias_key=?", (alias_key,)
        ).fetchone()
        if existing is not None or alias_root != alias_key:
            return None
        canonical_row = connection.execute(
            "SELECT canonical_name FROM follow_author_alias WHERE canonical_key=? "
            "ORDER BY CASE WHEN alias_key=canonical_key THEN 0 ELSE 1 END LIMIT 1",
            (canonical_root,),
        ).fetchone()
        if canonical_row is not None:
            canonical_name = str(canonical_row["canonical_name"])
    elif canonical_root != alias_root:
        connection.execute(
            "UPDATE follow_author_alias SET canonical_key=?,canonical_name=?,updated_at=? "
            "WHERE canonical_key=?",
            (canonical_root, canonical_name, stamp, alias_root),
        )

    conflict = (
        "DO UPDATE SET canonical_key=excluded.canonical_key,"
        "canonical_name=excluded.canonical_name,alias_name=excluded.alias_name,"
        "source=excluded.source,updated_at=excluded.updated_at"
        if source == "manual" else "DO NOTHING"
    )
    sql = (
        "INSERT INTO follow_author_alias(alias_key,alias_name,canonical_key,"
        "canonical_name,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?) "
        f"ON CONFLICT(alias_key) {conflict}"
    )
    connection.execute(
        sql, (canonical_root, canonical_name, canonical_root, canonical_name,
              source, stamp, stamp),
    )
    inserted = connection.execute(
        sql, (alias_key, alias_name, canonical_root, canonical_name,
              source, stamp, stamp),
    ).rowcount
    if source != "manual" and not inserted:
        return None
    return {"canonical": canonical_name, "alias": alias_name, "source": source}


def _official_profile_handle(provider: str, ref: str) -> str:
    if provider == "fanbox":
        return str(ref or "").strip()
    if provider == "subscribestar":
        return str(ref or "").strip().rsplit("/", 1)[-1]
    if provider == "patreon":
        value = str(ref or "").strip().strip("/")
        if value.startswith("user/") or value.isdigit():
            return ""
        return value.rsplit("/", 1)[-1]
    return ""


def _learn_official_author_alias(connection, provider: str, ref: str,
                                  candidates) -> dict | None:
    """Learn a platform handle only from one unambiguous official profile name."""
    if provider not in _OFFICIAL_IDENTITY_PROVIDERS:
        return None
    authors: dict[str, str] = {}
    for candidate in candidates:
        name = str(candidate.author or "").strip()
        key = _normalized_author_name(name)
        if key:
            authors.setdefault(key, name)
    if len(authors) != 1:
        return None
    canonical_key, canonical_name = next(iter(authors.items()))
    handle = _official_profile_handle(provider, ref)
    if not handle or _normalized_author_name(handle) == canonical_key:
        return None
    return _upsert_follow_author_alias(
        connection, canonical_name, handle, source=f"official:{provider}")


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
    history_exhausted = _legacy_history_end(row)
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
        "created_at": row["created_at"],
        "last_checked_at": row["last_checked_at"],
        "last_status": "not_modified" if history_exhausted else row["last_status"],
        "last_error": None if history_exhausted else row["last_error"],
        "history_exhausted": history_exhausted,
    }


def _legacy_history_end(row) -> bool:
    """Normalize terminal backfill responses recorded as errors by older builds."""
    if int(row["backfill_page"] or 0) <= 0 or row["last_status"] != "error":
        return False
    provider = str(row["provider"] or "")
    message = str(row["last_error"] or "").casefold()
    if provider in {"kemono", "coomer", "pawchive"}:
        return message in {f"{provider} 返回 http 400", f"{provider} 返回 http 404"}
    if provider == "rule34paheal":
        return message == "rule34paheal 返回 http 404"
    return False


def _follow_facets(store, items, by_source, alias_map) -> dict:
    """筛选条上能选什么。

    必须按全库算而不是按筛后结果——否则选中一个作者之后，作者栏里就只剩他自己，
    再也切不回去。标签同理，按分组而不是按条目计数：一条发布的多个变体是同一件
    作品，标签不该被数三遍。
    """
    authors: set[str] = set()
    providers: set[str] = set()
    tags: dict[str, int] = {}
    for group in store.group(items):
        row = by_source.get(group.primary.source_id)
        if row is not None:
            key = author_key(row, alias_map)
            if key:
                authors.add(key)
            providers.add(str(row["provider"] or ""))
        for tag in _item_tags(group.primary):
            tags[tag] = tags.get(tag, 0) + 1
    return {
        "authors": sorted(authors),
        "providers": sorted(providers),
        "tags": sorted(tags.items(), key=lambda pair: (-pair[1], pair[0])),
    }


def q_follow_tags(contract, args) -> dict:
    """在线标签词表，供标签页和左侧抽屉列出关注页那一套标签。

    单独一个端点而不是从 `/api/follow` 里捞：那个载荷还带着来源、别名建议和一整页
    条目，抽屉每次重建都拉一遍不合算。计数与关注页筛选条完全同源——共用
    `_follow_facets`，不是另写一份统计，否则两处迟早对不上。

    返回形状刻意与 `/api/index` 一致（`items` 加 `has_more`）：标签页的分页、搜索
    和「载入更多」都是现成的，换个地址就能用，不必为在线标签再写一套。
    """
    query = str(args.get("q") or "").strip().casefold()
    try:
        limit = max(1, min(int(args.get("limit") or 180), 2000))
    except (TypeError, ValueError):
        limit = 180
    try:
        offset = max(0, int(args.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    with contract.database.read_connection() as connection:
        store = _store(contract, connection)
        source_rows = store.sources()
        alias_map, _aliases = _follow_alias_state(connection)
        enabled = {int(row["id"]) for row in source_rows if row["enabled"]}
        by_source = {int(row["id"]): row for row in source_rows}
        items = tuple(item for item in store.items(limit=_ALL_ITEMS)
                      if item.source_id in enabled and not _excluded_item(item))
        facets = _follow_facets(store, items, by_source, alias_map)
    rows = [{"k": tag, "n": count} for tag, count in facets["tags"]
            if not query or query in tag.casefold()]
    return {"kind": "tags", "scope": "online",
            "items": rows[offset:offset + limit],
            "has_more": offset + limit < len(rows)}


def q_follow(contract, args) -> dict:
    statuses = tuple(
        value for value in str(args.get("status") or "").split(",") if value in _STATUSES
    )
    try:
        limit = max(1, min(int(args.get("limit") or 200), 1000))
    except (TypeError, ValueError):
        limit = 200
    try:
        offset = max(0, int(args.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    source = args.get("source")
    source_id = int(source) if str(source or "").isdigit() else None
    requested_item = args.get("item")
    item_id = int(requested_item) if str(requested_item or "").isdigit() else None
    author = str(args.get("author") or "").strip()
    provider = str(args.get("provider") or "").strip()
    wanted_tags = tuple(value for value in
                        (part.strip() for part in str(args.get("tag") or "").split(","))
                        if value)
    credential_store = _credential_store(contract)
    credential_providers = frozenset(
        provider for provider in CREDENTIAL_GUIDE
        if credential_store.load(provider) is not None
    )
    with contract.database.read_connection() as connection:
        store = _store(contract, connection)
        source_rows = store.sources()
        alias_map, author_aliases = _follow_alias_state(connection)
        sources = [_source_payload(row, alias_map) for row in source_rows]
        alias_suggestions = _follow_alias_suggestions(source_rows, alias_map)
        enabled_source_ids = {int(row["id"]) for row in source_rows if row["enabled"]}
        # 作者、来源和标签都不是库里的列：author_key 要经实体绑定、来源 metadata 和
        # 别名映射推导，tags 要从条目 metadata JSON 解析再去噪。在 SQL 里重写这两套
        # 推导等于把同一个语义实现两遍，迟早漂移。所以整库取回来在 Python 里筛——
        # 实测 3054 条连 metadata 解析一起 15ms，不值得为它另设一套索引。
        by_source = {int(row["id"]): row for row in source_rows}

        def _matches(item) -> bool:
            row = by_source.get(item.source_id)
            if author and (row is None or author_key(row, alias_map) != author):
                return False
            if provider and (row is None or str(row["provider"] or "") != provider):
                return False
            if wanted_tags:
                tags = set(_item_tags(item))
                if not all(tag in tags for tag in wanted_tags):
                    return False
            return True

        everything = tuple(item for item in store.items(source_id=source_id, limit=_ALL_ITEMS)
                           if item.source_id in enabled_source_ids and not _excluded_item(item))
        counted = tuple(item for item in everything if _matches(item))
        if item_id is not None:
            items = tuple(item for item in store.items_for_item(item_id)
                          if item.source_id in enabled_source_ids and not _excluded_item(item))
            has_more = False   # 直达详情只取这一组，没有下一页
        else:
            # 分页在筛选之后：早先是 SQL 先分页、前端再筛，选个冷门作者会看到一页里
            # 只剩两三条，得反复点「加载更多」才凑出一屏。
            page = [item for item in counted if not statuses or item.status in statuses]
            has_more = len(page) > offset + limit
            items = tuple(page[offset:offset + limit])
        groups = [_group_payload(group, credential_providers)
                  for group in store.group(items)]
        facets = _follow_facets(store, everything, by_source, alias_map)
        # counts 与列表同源。以前它是一句全库 SQL，再逐条减掉被隐藏的 rule34video
        # 和无资源的 f95zone——同一套排除规则维护了两份，而且它完全不看作者、来源和
        # 标签筛选，于是筛选一换，列表变了、药丸上的数字纹丝不动。现在两边都从
        # `counted` 出发：筛选怎么变，数字就怎么变，扣减逻辑也不必再写第二遍。
        counts: dict[str, int] = {}
        for item in counted:
            status = str(item.status)
            counts[status] = counts.get(status, 0) + 1
    suggestions = _suggestions(contract, sources)
    return {
        "ok": True,
        "sources": sources,
        "author_aliases": author_aliases,
        "alias_suggestions": alias_suggestions,
        "suggestions": suggestions,
        "groups": groups,
        "counts": {status: int(counts.get(status, 0)) for status in _STATUSES},
        "facets": facets,
        # counts 是全库口径，groups 只是这一页——两个数并排显示过，看起来像自相矛盾。
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "providers": sorted(CONNECTORS),
    }


#: 「猜你喜欢」一次给多少个。这是给人挑的，不是导出全部。
MAX_SUGGESTIONS = 12


def _suggestions(contract, sources) -> list[dict]:
    """「猜你喜欢」取**浏览历史口味分析**产出的创作者候选，按访问次数排序。

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


def _follow_playback_row(connection, item_id: int):
    row = connection.execute(
        "SELECT id,status FROM follow_item WHERE id=?", (item_id,),
    ).fetchone()
    if row is None:
        raise ValueError("follow item not found")
    return row


def w_follow_play(contract, body) -> dict:
    """记录一次关注页直接播放；候选无需先保存成 asset。"""
    item_id = int(body["item"])
    contract.cache_bust()
    with contract.database.write_transaction() as connection:
        row = _follow_playback_row(connection, item_id)
        stamp = datetime.now(timezone.utc).timestamp()
        connection.execute(
            "INSERT INTO follow_playback(follow_item_id,profile_id,play_count,last_played) "
            "VALUES(?,'local-default',1,?) ON CONFLICT(follow_item_id,profile_id) "
            "DO UPDATE SET play_count=follow_playback.play_count+1,last_played=excluded.last_played",
            (item_id, stamp),
        )
        if row["status"] == "new":
            connection.execute(
                "UPDATE follow_item SET status='seen' WHERE id=?", (item_id,),
            )
    return {"ok": True, "item": item_id, "status": "seen" if row["status"] == "new" else row["status"]}


def w_follow_activity(contract, body) -> dict:
    """累计关注页在线播放的真实时长与最远到达位置。"""
    item_id = int(body["item"])
    position = max(float(body.get("position", 0)), 0)
    duration = max(float(body.get("duration", 0)), 0)
    delta = max(float(body.get("delta", 0)), 0)
    ended = bool(body.get("ended"))
    ratio = 1.0 if ended else (min(position / duration, 1.0) if duration > 0 else 0.0)
    contract.cache_bust()
    with contract.database.write_transaction() as connection:
        _follow_playback_row(connection, item_id)
        stamp = datetime.now(timezone.utc).timestamp()
        connection.execute(
            "INSERT INTO follow_playback(follow_item_id,profile_id,play_count,play_seconds,max_reached,last_played) "
            "VALUES(?,'local-default',1,?,?,?) ON CONFLICT(follow_item_id,profile_id) DO UPDATE SET "
            "play_seconds=follow_playback.play_seconds+excluded.play_seconds,"
            "max_reached=max(follow_playback.max_reached,excluded.max_reached),"
            "last_played=excluded.last_played",
            (item_id, delta, ratio, stamp),
        )
        result = connection.execute(
            "SELECT play_seconds,max_reached FROM follow_playback "
            "WHERE follow_item_id=? AND profile_id='local-default'", (item_id,),
        ).fetchone()
    return {"ok": True, "item": item_id, **dict(result)}


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
    if not contract.follow_check_lock.acquire(blocking=False):
        return {"ok": False, "busy": True, "checked": 0, "results": []}
    try:
        return _run_follow_check(contract, body)
    finally:
        contract.follow_check_lock.release()


def _run_follow_check(contract, body) -> dict:
    requested = body.get("source")
    source_id = requested if isinstance(requested, int) else None
    # 往回抓一页。这是**显式的、一次一页**的动作：常规检查永远只看第一页，
    # 因为追更关心的是增量；但那也意味着每个来源只有第一页那点内容
    # （rule34video 的作者页一页 24 条，实际 61 页）。用户点一次，往前挪一页。
    older = bool(body.get("older"))
    credentials = _credential_store(contract)
    results: list[dict] = []
    with contract.database.read_connection() as connection:
        store = _store(contract, connection)
        rows = [dict(row) for row in store.sources(enabled_only=True)
                if (source_id is None or row["id"] == source_id)
                and (not older or row["provider"] in _BACKFILL_PROVIDERS)]
        for row in rows:
            row["force_media_reparse"] = (
                not older and credentials.load(row["provider"]) is not None
                and store.source_needs_media_reparse(row["id"])
            )
    for row in rows:
        moment = datetime.now(timezone.utc)
        provider, ref = row["provider"], row["ref"]
        page = (row["backfill_page"] + 1) if older else 0
        try:
            connector_kwargs = {"credential": credentials.load(provider)}
            gofile_credential = credentials.load("gofile")
            if gofile_credential is not None:
                connector_kwargs["gofile_credential"] = gofile_credential
            connector = build_connector(provider, **connector_kwargs)
            # 凭据已经存在但旧候选仍标着 needs_credential 时，条件请求的 304
            # 会让旧解析结果永久不变。显式检查应无条件重取一次，让凭据真正生效。
            fetch = connector.fetch(
                ref,
                etag=None if row["force_media_reparse"] else row["etag"],
                last_modified=(None if row["force_media_reparse"]
                               else row["last_modified"]),
                page=page,
            )
        except FollowHistoryEnd:
            with contract.database.write_transaction() as connection:
                _store(contract, connection).record_history_end(row["id"], moment)
            results.append({
                "source": row["id"], "provider": provider,
                "provider_label": PROVIDER_LABELS.get(provider, provider),
                "ref": ref, "label": row["label"], "ok": True,
                "page": page, "older": older, "exhausted": True,
                "message": "没有更多历史内容",
            })
            continue
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
            learned_alias = _learn_official_author_alias(
                connection, provider, ref, fetch.candidates)
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
            "author_alias_learned": learned_alias,
        })
    return {"ok": True, "checked": len(results), "results": results}


def q_follow_schedule(contract, _args) -> dict:
    scheduler = contract.follow_scheduler
    if scheduler is None:
        return {"ok": True, "available": False, "enabled": False,
                "interval_minutes": 60, "running": False, "next_run_at": None}
    return scheduler.status()


def w_follow_schedule(contract, body) -> dict:
    scheduler = contract.follow_scheduler
    if scheduler is None:
        raise ValueError("automatic follow updates are unavailable")
    return scheduler.update(
        enabled=body.get("enabled", True),
        interval_minutes=body.get("interval_minutes", 60),
    )


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
        response = connector.probe(
            f"https://{connector.host}/api/v1/{service}/user/{user}/profile")
        if response.status != 200:
            return parsed.label
        name = (connector.parse_json(response) or {}).get("name")
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
    with contract.database.write_transaction() as connection:
        _upsert_follow_author_alias(
            connection, canonical_name, alias_name, source="manual")
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
    "fanbox": {
        "requirement": "optional",
        "fields": ["cookie"],
        # FANBOX Cookie 绑定浏览器会话与风控环境，不跨机同步。
        "syncable": [],
        "why": "公开列表不需要登录；帖子详情被 FANBOX 验证页拦住时，可用浏览器会话取得正文、多图和外部资源链接。",
        "where": "https://www.fanbox.cc/",
        "howto": "登录 FANBOX 后，从一次成功的 api.fanbox.cc/post.info 请求复制整条 Cookie 请求头。",
    },
    "gofile": {
        "requirement": "optional",
        "fields": ["api_token"],
        "syncable": [],
        "why": "用于展开 Gofile 文件页，取得其中的图片和视频列表；Gofile 当前要求 Premium 才能读取 contents API，不配置仍会保留文件页链接。",
        "where": "https://gofile.io/myprofile",
        "howto": "登录 Premium Gofile 账户后，在个人资料页复制 API token。",
    },
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
    for provider in sorted(set(CONNECTORS) | set(CREDENTIAL_GUIDE)):
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
