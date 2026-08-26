"""追更的 Web 契约层。

读接口无副作用；`/api/follow/check` 是唯一会联网的端点，且只在用户显式点击时触发。
`/api/follow/save` 写真相，走和 CLI 同一个 `save_asset(confirm=True)` 边界。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from .follow import FollowSourceError
from .follow_secrets import CredentialError, CredentialStore
from .platform import root_online
from .follow_discovery import discover
from .follow_sources import (
    CONNECTORS, KemonoConnector, build_connector, parse_source_url,
)
from .follow_store import FollowStore, ReleaseGroup
from .taste_history import read_creator_candidates


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
    suggestions = _suggestions(contract, sources)
    return {
        "ok": True,
        "sources": sources,
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
    credentials = _credential_store(contract)
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
            # 证据没存下来不算检查失败，但界面必须说出来，不能悄悄少一份原始响应。
            "evidence_error": outcome.evidence_error,
        })
    return {"ok": True, "checked": len(results), "results": results}


def _failure(contract, row, error, moment, status) -> dict:
    with contract.database.write_transaction() as connection:
        _store(contract, connection).record_error(
            row["id"], str(error), moment, status=status)
    return {"source": row["id"], "provider": row["provider"], "ref": row["ref"],
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
    if action != "add":
        raise ValueError(f"unknown follow source action: {action}")

    parsed = parse_source_url(str(body.get("url") or ""))
    credentials = _credential_store(contract)
    credential = credentials.load(parsed.provider)
    label = str(body.get("label") or "").strip() or _resolve_label(
        contract, parsed, credential)
    with contract.database.write_transaction() as connection:
        source_id = _store(contract, connection).register(
            provider=parsed.provider, ref=parsed.ref, label=label, url=parsed.url,
            semantics=parsed.semantics)
    checked = w_follow_check(contract, {"source": source_id})
    outcome = next((row for row in checked["results"]
                    if row["source"] == source_id), None)
    return {"ok": True, "source": source_id, "provider": parsed.provider,
            "ref": parsed.ref, "label": label, "checked": outcome}


#: 一次最多解析多少行。粘一屏链接是正常的，粘一整个书签导出不是。
MAX_RESOLVE_LINES = 40


def _candidate_payload(candidate) -> dict:
    return {"provider": candidate.provider,
            "provider_label": PROVIDER_LABELS.get(candidate.provider, candidate.provider),
            "ref": candidate.ref, "url": candidate.url, "label": candidate.label,
            "semantics": candidate.semantics, "evidence": candidate.evidence}


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

    known = {(row["provider"], row["ref"]) for row in
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
                "candidates": [{**_candidate_payload(c),
                                "known": (c.provider, c.ref) in known}
                               for c in found.candidates],
                "failures": found.failures,
            })
            continue
        results.append({"line": line, "kind": "url",
                        "candidates": [{**_candidate_payload(parsed),
                                        "known": (parsed.provider, parsed.ref) in known}]})
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
        # 全部留空 = 删掉这份凭据。给得出「配上」就要给得出「撤掉」。
        path.unlink(missing_ok=True)
        return {"ok": True, "provider": provider, "cleared": True,
                "saved": store.describe(provider)}
    _write_secret(path, cleaned)
    shared_written = _write_shared(store, provider, cleaned)
    # 返回的是 describe()，只有字段名，没有值。
    return {"ok": True, "provider": provider, "cleared": False,
            # 界面据此说明「这台机器上没有收紧文件权限」，而不是默认收紧过。
            "permissions_tightened": os.name != "nt",
            "synced": shared_written,
            "saved": store.describe(provider)}


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
        if not root_online(shared.parent.parent.parent):
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
