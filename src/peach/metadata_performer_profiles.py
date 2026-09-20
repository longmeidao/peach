"""新导入人物的别名与官方头像补全。

演员真值仍由元数据自动落库规则决定；本模块只消费同一个来源人物对象里与身份绑定的
附加证据。别名必须与已经连到这条资产的实体对得上，头像只允许 r18/DMM 固定目录，
候选 CSV 即使被改写也不能让 Peach 请求任意地址。
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from . import avatar_picker
from .entities import canonicalize_entity_name, normalize_entity_name, resolve_entity
from .http import HttpxTransport
from .previews import entity_image_key
from .repository import LedgerDatabase


PROFILE_ALIAS_SOURCE = "r18dev:performer-profile"
OFFICIAL_AVATAR_HOST = "pics.dmm.co.jp"
OFFICIAL_AVATAR_PREFIX = "/mono/actjpgs/"


def _approved_key(connection, group: dict) -> str:
    row = connection.execute(
        "SELECT note FROM review_decision WHERE category='metadata_fields' "
        "AND item_key=? AND status='approved'", (str(group.get("item_key") or ""),),
    ).fetchone()
    if row is None:
        return ""
    try:
        return str(json.loads(row[0]).get("candidate_key") or "")
    except (AttributeError, TypeError, ValueError):
        return ""


def _profiles(connection, groups) -> list[dict]:
    found: dict[tuple[int, str, str], dict] = {}
    for group in groups:
        if str(group.get("field") or "") != "performers":
            continue
        try:
            asset_id = int(group.get("asset_id") or 0)
        except (TypeError, ValueError):
            continue
        if asset_id <= 0:
            continue
        approved_key = _approved_key(connection, group)
        if not approved_key:
            continue
        try:
            candidates = json.loads(str(group.get("candidates_json") or "[]"))
        except (TypeError, ValueError):
            continue
        for candidate in candidates:
            if (not isinstance(candidate, dict)
                    or str(candidate.get("candidate_key") or "") != approved_key):
                continue
            for person in candidate.get("value") or []:
                if not isinstance(person, dict):
                    continue
                source = str(person.get("profile_source") or "").strip()
                external_id = str(person.get("external_id") or "").strip()
                name = canonicalize_entity_name("performer", person.get("name"))
                if not source or not name:
                    continue
                key = (asset_id, source, external_id or name)
                found[key] = {
                    "asset_id": key[0], "source": source, "external_id": external_id,
                    "name": name, "aliases": person.get("aliases") or [],
                    "avatar_url": str(person.get("thumb_url") or "").strip(),
                }
    return list(found.values())


def _entity_id(connection, profile: dict) -> tuple[int | None, bool]:
    entity = resolve_entity(connection, "performer", profile["name"])
    entity_id = int(entity["id"]) if entity is not None else None
    referenced_id = None
    if profile["external_id"]:
        row = connection.execute(
            "SELECT entity_id FROM entity_external_ref WHERE provider=? "
            "AND external_kind='performer' AND external_id=?",
            (profile["source"], profile["external_id"]),
        ).fetchone()
        referenced_id = int(row[0]) if row else None
    if entity_id is not None and referenced_id not in (None, entity_id):
        return None, True
    entity_id = entity_id or referenced_id
    if entity_id is None:
        return None, False
    linked = connection.execute(
        "SELECT 1 FROM asset_entity WHERE asset_id=? AND entity_id=? "
        "AND role='performer' LIMIT 1", (profile["asset_id"], entity_id),
    ).fetchone()
    if not linked:
        return None, False
    if profile["external_id"] and referenced_id is None:
        connection.execute(
            "INSERT OR IGNORE INTO entity_external_ref"
            "(entity_id,provider,external_kind,external_id) VALUES(?,?,?,?)",
            (entity_id, profile["source"], "performer", profile["external_id"]),
        )
    return entity_id, False


def _official_avatar(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return (parsed.scheme == "https" and parsed.hostname == OFFICIAL_AVATAR_HOST
            and parsed.username is None and parsed.password is None
            and parsed.path.startswith(OFFICIAL_AVATAR_PREFIX)
            and parsed.path != OFFICIAL_AVATAR_PREFIX)


def enrich_performer_profiles(db_path: Path, groups, avatar_root: Path,
                               providers_root: Path, *, transport_factory=None) -> dict:
    """把已落库且仍连着这条资产的人物资料补齐；单项失败不打断整批导入。"""
    result = {"aliases": 0, "avatars": 0, "conflicts": 0, "failed": 0}
    tasks: dict[int, dict] = {}
    database = LedgerDatabase(Path(db_path))
    with database.write_transaction() as connection:
        profiles = _profiles(connection, groups)
        for profile in profiles:
            entity_id, conflict = _entity_id(connection, profile)
            result["conflicts"] += int(conflict)
            if entity_id is None:
                continue
            canonical = connection.execute(
                "SELECT canonical_name FROM entity WHERE id=?", (entity_id,)).fetchone()[0]
            canonical_key = normalize_entity_name(canonical)
            for raw_alias in profile["aliases"] if isinstance(profile["aliases"], list) else []:
                alias = canonicalize_entity_name("performer", raw_alias)
                alias_key = normalize_entity_name(alias)
                if not alias or alias_key == canonical_key:
                    continue
                if connection.execute(
                        "SELECT 1 FROM entity_alias WHERE entity_id=? AND normalized_alias=?",
                        (entity_id, alias_key)).fetchone():
                    continue
                collision = connection.execute(
                    "SELECT id FROM entity WHERE kind='performer' AND normalized_name=? AND id<>? "
                    "UNION SELECT entity_id FROM entity_alias WHERE normalized_alias=? "
                    "AND entity_id<>? LIMIT 1",
                    (alias_key, entity_id, alias_key, entity_id),
                ).fetchone()
                if collision:
                    result["conflicts"] += 1
                    continue
                connection.execute(
                    "INSERT OR IGNORE INTO entity_alias"
                    "(entity_id,alias,normalized_alias,source,confidence) VALUES(?,?,?,?,?)",
                    (entity_id, alias, alias_key, PROFILE_ALIAS_SOURCE, 0.95),
                )
                result["aliases"] += int(connection.execute(
                    "SELECT changes()").fetchone()[0])
            avatar = avatar_root / f"{entity_image_key('performer', entity_id)}.img"
            if (not avatar.is_file() and _official_avatar(profile["avatar_url"])
                    and entity_id not in tasks):
                tasks[entity_id] = profile

    if not tasks:
        return result
    transport = transport_factory() if transport_factory else None
    owns_transport = not callable(transport)
    if owns_transport:
        transport = HttpxTransport()
    try:
        for entity_id, profile in tasks.items():
            try:
                body = avatar_picker.fetch_image(transport, profile["avatar_url"])
                avatar_picker.accept_image(body)
                avatar_picker.install(
                    providers_root, avatar_root, "performer", entity_id, body,
                    {"source": "r18.dev performer profile", "provider": "r18dev",
                     "source_kind": "official_profile", "matched_name": profile["name"],
                     "name_source": "r18dev", "external_id": profile["external_id"],
                     "upstream_url": profile["avatar_url"]},
                )
                result["avatars"] += 1
            except Exception:  # 网络、解码或可选人脸模型失败都只影响这一张头像。
                result["failed"] += 1
    finally:
        if owns_transport:
            transport.close()
    return result
