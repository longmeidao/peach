from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlite3 import Connection


def normalize_entity_name(name: str) -> str:
    return str(name).strip().casefold()


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
    canonical = str(name or "").strip()
    if not canonical:
        return None
    stamp = now or datetime.now(timezone.utc).isoformat()
    normalized = normalize_entity_name(canonical)
    payload = json.dumps(metadata or {}, ensure_ascii=False)
    connection.execute(
        """INSERT INTO entity(kind,canonical_name,normalized_name,metadata_json,created_at,updated_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(kind,normalized_name) DO UPDATE SET
             canonical_name=excluded.canonical_name,
             metadata_json=excluded.metadata_json,
             updated_at=excluded.updated_at""",
        (kind, canonical, normalized, payload, stamp, stamp),
    )
    entity_id = connection.execute(
        "SELECT id FROM entity WHERE kind=? AND normalized_name=?", (kind, normalized),
    ).fetchone()[0]
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
