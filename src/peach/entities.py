from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlite3 import Connection


def normalize_entity_name(name: str) -> str:
    return str(name).strip().casefold()


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
