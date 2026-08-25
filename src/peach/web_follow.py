"""追更的 Web 契约层。

读接口无副作用；`/api/follow/check` 是唯一会联网的端点，且只在用户显式点击时触发。
`/api/follow/save` 写真相，走和 CLI 同一个 `save_asset(confirm=True)` 边界。
"""
from __future__ import annotations

from datetime import datetime, timezone

from .follow import FollowSourceError
from .follow_secrets import CredentialError, CredentialStore
from .follow_sources import CONNECTORS, build_connector
from .follow_store import FollowStore, ReleaseGroup


#: 界面上给每个来源的中文短名。没登记的 provider 直接显示原名。
PROVIDER_LABELS = {
    "kemono": "Kemono",
    "coomer": "Coomer",
    "pawchive": "Pawchive",
    "rule34video": "Rule34Video",
    "rule34xxx": "Rule34.xxx",
    "f95zone": "F95zone",
    "simpcity": "SimpCity",
}

_STATUSES = ("new", "seen", "saved", "ignored")


def _store(contract, connection) -> FollowStore:
    return FollowStore(lambda: connection, sources_root=contract.follow_sources_root)


def _item_payload(item) -> dict:
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
        "thumb_url": item.thumb_url,
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


def _source_payload(row) -> dict:
    return {
        "id": row["id"],
        "provider": row["provider"],
        "provider_label": PROVIDER_LABELS.get(row["provider"], row["provider"]),
        "ref": row["ref"],
        "label": row["label"],
        "url": row["url"],
        "semantics": row["semantics"],
        "enabled": bool(row["enabled"]),
        "entity_id": row["entity_id"],
        "entity_name": row["entity_name"],
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
        sources = [_source_payload(row) for row in store.sources()]
        items = store.items(statuses=statuses, source_id=source_id, limit=limit)
        groups = [_group_payload(group) for group in store.group(items)]
        counts = dict(connection.execute(
            "SELECT status, count(*) FROM follow_item GROUP BY status").fetchall())
    return {
        "ok": True,
        "sources": sources,
        "groups": groups,
        "counts": {status: int(counts.get(status, 0)) for status in _STATUSES},
        "providers": sorted(CONNECTORS),
    }


def w_follow_status(contract, body) -> dict:
    item_id = body.get("item")
    status = str(body.get("to") or "")
    if not isinstance(item_id, int):
        raise ValueError("item must be an integer follow item id")
    with contract.database.write_transaction() as connection:
        _store(contract, connection).set_status(item_id, status)
    return {"ok": True, "item": item_id, "status": status}


def w_follow_save(contract, body) -> dict:
    item_id = body.get("item")
    if not isinstance(item_id, int):
        raise ValueError("item must be an integer follow item id")
    with contract.database.write_transaction() as connection:
        asset_id = _store(contract, connection).save_asset(item_id, confirm=True)
    return {"ok": True, "item": item_id, "asset_id": asset_id}


def w_follow_check(contract, body) -> dict:
    """显式检查更新。这是唯一会向站点发请求的端点。

    没有 `source` 就检查全部已启用来源。逐个来源独立成败：一个来源缺凭据或被
    机器人验证挡住，不该让其余来源的更新一起消失。
    """
    requested = body.get("source")
    source_id = requested if isinstance(requested, int) else None
    credentials = CredentialStore(contract.follow_secrets_root)
    results: list[dict] = []
    with contract.database.read_connection() as connection:
        rows = [dict(row) for row in _store(contract, connection).sources(enabled_only=True)
                if source_id is None or row["id"] == source_id]
    for row in rows:
        moment = datetime.now(timezone.utc)
        provider, ref = row["provider"], row["ref"]
        try:
            connector = build_connector(provider, credential=credentials.load(provider))
            fetch = connector.fetch(ref, etag=row["etag"],
                                    last_modified=row["last_modified"])
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
                creator_aliases=store.creator_aliases(row["entity_id"]), moment=moment)
        results.append({
            "source": row["id"], "provider": provider, "ref": ref, "ok": True,
            "not_modified": outcome.not_modified, "discovered": outcome.discovered,
            "added": outcome.added, "updated": outcome.updated,
        })
    return {"ok": True, "checked": len(results), "results": results}


def _failure(contract, row, error, moment, status) -> dict:
    with contract.database.write_transaction() as connection:
        _store(contract, connection).record_error(
            row["id"], str(error), moment, status=status)
    return {"source": row["id"], "provider": row["provider"], "ref": row["ref"],
            "ok": False, "status": status, "error": str(error)}


def q_follow_credentials(contract, _args) -> dict:
    """只报告凭据是否存在与字段名，绝不返回凭据值。"""
    store = CredentialStore(contract.follow_secrets_root)
    return {"ok": True, "root": str(store.root),
            "providers": [store.describe(provider) for provider in sorted(CONNECTORS)]}
