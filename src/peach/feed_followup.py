"""给 Feed 发现的番号取一份资料（ADR-0042 第六条）。

拉取只解出番号，壳上除了番号什么都没有——没有标题就没法在页面上认出这是哪一部。
这条后继把标题、女优、厂牌、发行日与封面地址取回来写进壳。

**不复用 `process_library`**：那条路以 `asset` 行为单位、要写候选 CSV、要按字段优先级链
结算到真相字段，而壳没有真相字段可写。壳上的每个值都只是「某个来源这么说」，用户复核
的时机是文件真的到手、建成 `asset` 之后。所以这里只借来源链本身
（`metadata_routes`）和发请求那一层（`library_processing.LibraryMetadataProvider`），
不借结算。

幂等（ADR-0040 第六条要求）：重跑一次只是把同样的值再写一遍；壳已经不在了就当场返回。
"""
from __future__ import annotations

from . import feeds, metadata_routes
from .followups import Followup, FollowupType, register
from .metadata import extract_peach_fields

TASK_KEY = "feed-scrape"
TASK_LABEL = "取新作资料"

#: 一条资料够用就停。四个标量都拿到就不再问下一家——Feed 是后台跑的，
#: 多问一家换来的是配额，而壳上的值本来就不是真相字段。
WANTED = ("title", "performers", "studio", "release_date")


def followup_key(code: str) -> str:
    return f"{TASK_KEY}:{code}"


def parse_key(key: str) -> str:
    prefix, _, code = str(key).partition(":")
    if prefix != TASK_KEY or not code:
        raise ValueError(f"认不出这条取资料后继：{key}")
    return code


def plan(codes) -> list[Followup]:
    """一批新发现的番号，一个一条后继。"""
    return [Followup(key=followup_key(code), task_key=TASK_KEY,
                     label=f"{TASK_LABEL}：{code}") for code in codes]


def _cover(payload: dict) -> str | None:
    for field in ("cover_url", "cover"):
        value = str(payload.get(field) or "").strip()
        if value:
            return value
    urls = payload.get("cover_urls")
    if isinstance(urls, list):
        for value in urls:
            text = str(value or "").strip()
            if text:
                return text
    return None


def collect(provider, code: str) -> tuple[dict, str | None]:
    """按番号问来源链，返回 (字段, 封面地址)。

    问哪几家由 `metadata_routes` 决定，与刮削链同一份判据；这里没有本机证据可给，
    所以只传番号本身。一家都没给就抛——调用方把原因写进壳的 `scrape_error`，
    页面上那一行因此能说清是「还没取」还是「取不到」。
    """
    chain = metadata_routes.route_for_code(code)
    found = provider.community(
        code, route=metadata_routes.community_route(code))
    fields: dict[str, object] = {}
    cover: str | None = None
    for _source, payload in found:
        if not isinstance(payload, dict):
            continue
        cover = cover or _cover(payload)
        for name, item in extract_peach_fields(payload).items():
            if name in WANTED and name not in fields:
                fields[name] = item.get("value")
        if all(name in fields for name in WANTED):
            break
    if not fields and cover is None:
        raise ValueError(f"来源链 {'、'.join(chain)} 上都没有这个番号的资料")
    return fields, cover


def _performer_names(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item.get("name") or "") if isinstance(item, dict) else str(item)
                for item in value]
    return []


def run(contract, key: str, handle) -> dict:
    """跑一条取资料后继。返回的摘要就是活动页上那一行。"""
    from .library_processing import LibraryMetadataProvider

    code = parse_key(key)
    with contract.database.read_connection() as connection:
        row = connection.execute(
            "SELECT id,title FROM feed_discovery WHERE code=?", (code,)).fetchone()
    if row is None:
        # 壳被删了，或者这个番号这中间已经入库。两种都不该再取一遍。
        return {"outcome": "这条新作已经不在了"}
    handle.progress(label=f"{TASK_LABEL}：{code}", throttle=0)
    provider = LibraryMetadataProvider(contract.follow_secrets_root)
    try:
        fields, cover = collect(provider, code)
    except Exception as error:  # noqa: BLE001 - 原因要写到壳上给人看
        with contract.database.write_transaction() as connection:
            connection.execute(
                "UPDATE feed_discovery SET scrape_error=?,scraped_at=? WHERE id=?",
                (str(error), feeds.stamp(), int(row["id"])))
        return {"code": code, "outcome": "资料未取得", "error": str(error)}
    names = _performer_names(fields.get("performers"))
    with contract.database.write_transaction() as connection:
        connection.execute(
            "UPDATE feed_discovery SET title=COALESCE(?,title),cover_url=COALESCE(?,cover_url),"
            "studio=COALESCE(?,studio),release_date=COALESCE(?,release_date),"
            "performers=?,scrape_error=NULL,scraped_at=? WHERE id=?",
            (fields.get("title") or None, cover, fields.get("studio") or None,
             fields.get("release_date") or None, "、".join(name for name in names if name) or None,
             feeds.stamp(), int(row["id"])))
        for entity_id in feeds.match_performers(connection, names):
            feeds.link_entity(connection, int(row["id"]), entity_id)
    contract.cache_bust()
    return {"code": code, "outcome": "已取得", "performers": len(names),
            "cover": bool(cover)}


#: 写账本：壳与实体关联都在 `ledger.db` 里，所以它走串行那条通道。
TYPE = register(FollowupType(task_key=TASK_KEY, label=TASK_LABEL,
                             writes_ledger=True, run=run))
