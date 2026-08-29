from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlite3 import Connection


def normalize_entity_name(name: str) -> str:
    return str(name).strip().casefold()


PERSON_ENTITY_KINDS = frozenset({"creator", "performer"})
INVALID_PERSON_ENTITY_NAMES = frozenset({"画像を拡大する"})


def collapse_repeated_entity_name(name: str) -> str:
    """把 ``姓名 姓名`` 这类完整重复串收敛为一次。

    这里只处理以空白分隔、前后两半完全相同的高置信错误；不会碰
    ``M M Produce``、无空白的叠字或带分隔符的内容标签。
    """
    original = str(name or "").strip()
    canonical = " ".join(original.split())
    parts = canonical.split(" ") if canonical else []
    half = len(parts) // 2
    if (len(parts) >= 2 and len(parts) % 2 == 0
            and [part.casefold() for part in parts[:half]]
            == [part.casefold() for part in parts[half:]]):
        return " ".join(parts[:half])
    return original


def canonicalize_entity_name(kind: str, name: str | None) -> str:
    canonical = str(name or "").strip()
    if kind in PERSON_ENTITY_KINDS:
        canonical = collapse_repeated_entity_name(canonical)
        if canonical in INVALID_PERSON_ENTITY_NAMES:
            return ""
    return canonical


def merge_entity(
    connection: Connection, *, target_id: int, source_id: int,
    source_name: str, alias_source: str, now: str | None = None,
) -> dict:
    """把 source 实体并入 target，然后删除 source。调用方负责事务与备份。

    合并是不可逆的，只应在人工确认两个实体确为同一身份后调用——典型场景是
    同一位女优的旧艺名与现用艺名各自成了一个实体。

    `entity_external_ref` 有 `UNIQUE(entity_id, provider, external_kind)`，
    同一 provider 下只能留一条，所以 source 侧同类引用会被丢弃而不是覆盖；
    丢弃数量在返回值里报告，便于人工回看。
    """
    stamp = now or datetime.now(timezone.utc).isoformat()
    moved = {"assets": 0, "aliases": 0, "refs": 0, "links": 0, "terms": 0,
             "dropped_refs": 0}

    # 被并入的名字本身留作别名，否则按旧名搜索会落空。
    connection.execute(
        "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
        " VALUES(?,?,?,?,1.0)",
        (target_id, source_name, normalize_entity_name(source_name), alias_source),
    )
    connection.execute(
        "INSERT OR IGNORE INTO entity_alias"
        " SELECT ?,alias,normalized_alias,source,confidence FROM entity_alias WHERE entity_id=?",
        (target_id, source_id),
    )
    moved["aliases"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM entity_alias WHERE entity_id=?", (source_id,))

    connection.execute(
        "INSERT OR IGNORE INTO asset_entity"
        " SELECT asset_id,?,role,source,confidence,metadata_json,first_seen_at,last_seen_at"
        " FROM asset_entity WHERE entity_id=?", (target_id, source_id))
    moved["assets"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM asset_entity WHERE entity_id=?", (source_id,))

    before = connection.execute(
        "SELECT count(*) FROM entity_external_ref WHERE entity_id=?", (source_id,)).fetchone()[0]
    connection.execute(
        "UPDATE OR IGNORE entity_external_ref SET entity_id=? WHERE entity_id=?",
        (target_id, source_id))
    left = connection.execute(
        "SELECT count(*) FROM entity_external_ref WHERE entity_id=?", (source_id,)).fetchone()[0]
    moved["refs"] = before - left
    moved["dropped_refs"] = left
    connection.execute("DELETE FROM entity_external_ref WHERE entity_id=?", (source_id,))

    connection.execute(
        "INSERT OR IGNORE INTO entity_link(entity_id,link_kind,label,url,hostname,"
        "is_sensitive,metadata_json,created_at,updated_at)"
        " SELECT ?,link_kind,label,url,hostname,is_sensitive,metadata_json,created_at,updated_at"
        " FROM entity_link WHERE entity_id=?", (target_id, source_id))
    moved["links"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM entity_link WHERE entity_id=?", (source_id,))

    connection.execute(
        "INSERT OR IGNORE INTO entity_search_term(entity_id,term,purpose,source,created_at)"
        " SELECT ?,term,purpose,source,created_at FROM entity_search_term WHERE entity_id=?",
        (target_id, source_id))
    moved["terms"] = connection.execute("SELECT changes()").fetchone()[0]
    connection.execute("DELETE FROM entity_search_term WHERE entity_id=?", (source_id,))

    connection.execute("UPDATE entity SET updated_at=? WHERE id=?", (stamp, target_id))
    connection.execute("DELETE FROM entity WHERE id=?", (source_id,))
    return moved


def upsert_asset_entity(
    connection: Connection, *, kind: str, name: str | None, asset_id: int,
    role: str, source: str, confidence: float = 1.0,
    external_provider: str | None = None, external_id: str | int | None = None,
    metadata: dict | None = None, now: str | None = None,
) -> int | None:
    """写入规范实体关系；调用方负责事务和兼容投影。"""
    canonical = canonicalize_entity_name(kind, name)
    if not canonical:
        return None
    stamp = now or datetime.now(timezone.utc).isoformat()
    normalized = normalize_entity_name(canonical)
    payload = json.dumps(metadata or {}, ensure_ascii=False)
    entity_id = None
    if external_provider and external_id is not None:
        matched = connection.execute(
            "SELECT e.id FROM entity_external_ref x JOIN entity e ON e.id=x.entity_id "
            "WHERE x.provider=? AND x.external_kind=? AND x.external_id=? AND e.kind=?",
            (external_provider, kind, str(external_id), kind),
        ).fetchone()
        entity_id = int(matched[0]) if matched else None
    if entity_id is None:
        matched = connection.execute(
            "SELECT id FROM entity WHERE kind=? AND normalized_name=?",
            (kind, normalized),
        ).fetchone()
        entity_id = int(matched[0]) if matched else None
    if entity_id is None and kind in PERSON_ENTITY_KINDS:
        alias_matches = connection.execute(
            "SELECT DISTINCT e.id FROM entity e JOIN entity_alias a ON a.entity_id=e.id "
            "WHERE e.kind=? AND a.normalized_alias=? ORDER BY e.id LIMIT 2",
            (kind, normalized),
        ).fetchall()
        if len(alias_matches) == 1:
            entity_id = int(alias_matches[0][0])
    if entity_id is None:
        connection.execute(
            "INSERT INTO entity(kind,canonical_name,normalized_name,metadata_json,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?)",
            (kind, canonical, normalized, payload, stamp, stamp),
        )
        entity_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
    else:
        connection.execute(
            "UPDATE entity SET metadata_json=?,updated_at=? WHERE id=?",
            (payload, stamp, entity_id),
        )
    connection.execute(
        """INSERT INTO asset_entity(asset_id,entity_id,role,source,confidence,
                                     metadata_json,first_seen_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?)
           ON CONFLICT(asset_id,entity_id,role,source) DO UPDATE SET
             confidence=excluded.confidence,
             metadata_json=excluded.metadata_json,
             last_seen_at=excluded.last_seen_at""",
        (asset_id, entity_id, role, source, confidence, payload, stamp, stamp),
    )
    if external_provider and external_id is not None:
        connection.execute(
            """INSERT INTO entity_external_ref(
                 entity_id,provider,external_kind,external_id,metadata_json,last_synced_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(provider,external_kind,external_id) DO UPDATE SET
                 entity_id=excluded.entity_id,
                 metadata_json=excluded.metadata_json,
                 last_synced_at=excluded.last_synced_at""",
            (entity_id, external_provider, kind, str(external_id), payload, stamp),
        )
    return int(entity_id)


def resolve_entity(connection: Connection, kind: str, name: str):
    """先取精确规范名，再取唯一别名；撞名时不任意指向另一位。

    别名撞名返回 None 而不是随便挑一个：指错实体会把作品挂到另一个人名下，
    那是要人工复核才能发现的错误。
    """
    canonical = connection.execute(
        "SELECT e.* FROM entity e WHERE e.kind=? AND e.canonical_name=? LIMIT 1",
        (kind, name),
    ).fetchone()
    if canonical:
        return canonical
    aliases = connection.execute(
        "SELECT DISTINCT e.* FROM entity e JOIN entity_alias a ON a.entity_id=e.id "
        "WHERE e.kind=? AND a.alias=? ORDER BY e.id LIMIT 2",
        (kind, name),
    ).fetchall()
    return aliases[0] if len(aliases) == 1 else None
