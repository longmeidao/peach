"""稳定 JSON 契约的路由表：路径 → 处理器，以及只读端的放行清单。

前端只认这三张表。它们单独成一个模块，是为了让「加一个端点」变成一处改动：
处理器写在自己的域模块里，在这里登记一行。反过来说，这个文件是唯一需要 import
全部域模块的地方，所以域模块之间不必互相认识。

`READ_ONLY_POST_ROUTES` 是这里最容易出事的一张表：写入端闸门管的是账本分叉，
而有些 POST 只是因为要带请求体才用 POST，根本不碰账本。漏登记的表现是用户在
只读端点某个按钮直接吃 409。
"""
from __future__ import annotations

from .web_activity import (
    w_activity,
    w_feedback,
    w_play,
    w_preference,
    w_quality_goal,
    w_watch_later,
)
from .web_batch import q_ads, q_duplicates, w_batch, w_cleanup_empty_directories, w_empty_trash
from .web_catalog import (
    q_editions,
    q_facets,
    q_item,
    q_items,
    q_parts,
    q_related,
    q_tops,
    w_item_tag,
)
from .web_entity import q_entity, q_entity_photos, q_index, q_photo_set, w_entity_name
from .web_follow import (
    q_follow,
    q_follow_credentials,
    q_follow_schedule,
    q_follow_tags,
    w_follow_activity,
    w_follow_author_alias,
    w_follow_check,
    w_follow_credential,
    w_follow_play,
    w_follow_resolve,
    w_follow_save,
    w_follow_schedule,
    w_follow_source,
    w_follow_status,
)
from .web_links import w_links, w_links_check, w_links_prune
from .web_playlists import q_playlist, q_playlists, w_playlist
from .web_resource_sync import w_purge_missing, w_resource_sync_apply, w_resource_sync_scan
from .web_review import q_review, w_review_auto_apply, w_review_decision
from .web_settings import q_settings, w_settings
from .web_state import WebContract
from .web_stats import (
    q_quality_goals,
    q_search_history,
    q_stats,
    q_taste,
    w_search_history,
    w_taste_refresh,
    w_taste_source,
)


class ContractRouteNotFound(KeyError):
    """The stable JSON contract has no handler for this path."""


def _get_item(contract, args):
    return q_item(contract, int(args["id"]))


def _get_index(contract, args):
    return q_index(
        contract,
        args.get("kind", "tags"),
        args.get("q", ""),
        min(max(int(args.get("limit", "180")), 1), 600),
        max(int(args.get("offset", "0")), 0),
        args.get("category", ""),
    )


def _get_stats(contract, _args):
    return contract.cached("stats", lambda: q_stats(contract))


def _get_tops(contract, args):
    n = min(int(args.get("n", "28")), 60)
    jav = args.get("jav") == "1"
    seed = str(args.get("seed", ""))[:32]
    state = str(args.get("state", ""))
    return contract.cached(
        f"tops{n}{'-jav' if jav else ''}:{seed}:{state}",
        lambda: q_tops(contract, n, jav=jav, seed=seed, state=state),
    )


def _get_ads(contract, args):
    return q_ads(
        contract,
        min(int(args.get("limit", "60")), 200),
        max(int(args.get("offset", "0")), 0),
        args.get("kind", ""),
        args.get("status", "pending"),
    )


def _get_related(contract, args):
    """相关推荐走 LRU 缓存：打分是纯 Python 对几千个候选做 MMR，一次几百毫秒。

    每打开一次资料页都现算太贵，而结果只读不写；写路径（标签、反馈、播放、复核）
    本来就调 `cache_bust()`，缓存跟着一起作废。上面几个聚合用的是 `cached()`，
    这里必须用 `cached_lru()`：键跟着浏览过的资产走，键空间不封闭。
    键里带上 limit——同一个资产要不同条数就是不同结果。
    """
    asset_id = int(args["id"])
    limit = min(int(args.get("limit", "24")), 60)
    return contract.cached_lru(
        f"related:{asset_id}:{limit}", lambda: q_related(contract, asset_id, limit))


def _get_facets(contract, args):
    jav = args.get("jav") == "1"
    scope_kind = str(args.get("scope_kind", ""))
    scope_name = str(args.get("scope_name", ""))
    asset_id = int(args["id"]) if args.get("id") else None
    state = str(args.get("state", ""))
    scope_key = f"{scope_kind}:{scope_name}:{asset_id or ''}:{state}"
    return contract.cached(
        f"facets{'-jav' if jav else ''}:{scope_key}",
        lambda: q_facets(
            contract,
            jav=jav, scope_kind=scope_kind, scope_name=scope_name, asset_id=asset_id,
            state=state,
        ),
    )


def _get_search_history(contract, args):
    return q_search_history(contract, int(args.get("limit", "10")))


def _get_taste(contract, args):
    window = str(args.get("window") or "all")
    return contract.cached(
        f"taste:{window}",
        lambda: q_taste(contract, {"window": window}),
    )


def _get_review(contract, args):
    payload = contract.cached("review", lambda: q_review(contract))
    # 数据管理页只要一个待复核条数。完整 payload 带着每条候选的全文，实测是
    # 兆级；卡片上的一个数字不值这趟传输，但计数本身仍来自同一份缓存快照，
    # 不另立一套口径。
    if str(args.get("counts") or "") in {"1", "true"}:
        return {key: payload[key] for key in ("counts", "sources", "skipped_rows")
                if key in payload}
    return payload


def _post_empty_trash(contract, _body):
    return w_empty_trash(contract)


GET_HANDLERS = {
    "/api/settings": q_settings,
    "/api/follow": q_follow,
    "/api/follow/credentials": q_follow_credentials,
    "/api/follow/tags": q_follow_tags,
    "/api/follow/schedule": q_follow_schedule,
    "/api/items": q_items,
    "/api/item": _get_item,
    "/api/parts": q_parts,
    "/api/editions": q_editions,
    "/api/entity": q_entity,
    "/api/links": w_links,
    "/api/photos": q_entity_photos,
    "/api/photo-set": q_photo_set,
    "/api/index": _get_index,
    "/api/duplicates": q_duplicates,
    "/api/quality-goals": q_quality_goals,
    "/api/stats": _get_stats,
    "/api/tops": _get_tops,
    "/api/ads": _get_ads,
    "/api/related": _get_related,
    "/api/playlists": q_playlists,
    "/api/playlist": q_playlist,
    "/api/facets": _get_facets,
    "/api/search-history": _get_search_history,
    "/api/taste": _get_taste,
    "/api/review": _get_review,
}

POST_HANDLERS = {
    "/api/follow/check": w_follow_check,
    "/api/follow/schedule": w_follow_schedule,
    "/api/follow/source": w_follow_source,
    "/api/follow/author-alias": w_follow_author_alias,
    "/api/follow/resolve": w_follow_resolve,
    "/api/follow/credential": w_follow_credential,
    "/api/follow/status": w_follow_status,
    "/api/follow/save": w_follow_save,
    "/api/follow/play": w_follow_play,
    "/api/follow/activity": w_follow_activity,
    "/api/activity": w_activity,
    "/api/play": w_play,
    "/api/feedback": w_feedback,
    "/api/watch-later": w_watch_later,
    "/api/playlist": w_playlist,
    "/api/preference": w_preference,
    "/api/quality-goal": w_quality_goal,
    "/api/item-tag": w_item_tag,
    "/api/batch": w_batch,
    "/api/search-history": w_search_history,
    "/api/taste/refresh": w_taste_refresh,
    "/api/taste/source": w_taste_source,
    "/api/trash/empty": _post_empty_trash,
    "/api/data-cleanup/empty-folders": w_cleanup_empty_directories,
    "/api/purge-missing": w_purge_missing,
    "/api/links/check": w_links_check,
    "/api/links/prune": w_links_prune,
    "/api/resource-sync/scan": w_resource_sync_scan,
    "/api/resource-sync/apply": w_resource_sync_apply,
    "/api/review/auto-apply": w_review_auto_apply,
    "/api/review/decision": w_review_decision,
    "/api/settings": w_settings,
    "/api/entity-name": w_entity_name,
}


#: 这些 POST 不写 ledger，只是因为要带请求体才用 POST。写入端闸门管的是账本分叉，
#: 不该拦它们——「查找」只联网、「存凭据」只写本机 secrets 文件，都不碰账本。
#: 追更的「查找」在只读端被拦成 409 是实测踩到的。
READ_ONLY_POST_ROUTES = frozenset({
    "/api/follow/resolve", "/api/follow/credential",
    "/api/taste/refresh", "/api/taste/source", "/api/resource-sync/scan",
    "/api/links/check", "/api/data-cleanup/empty-folders",
})


def dispatch_api_get(contract: WebContract, path, args):
    """Dispatch the stable JSON read contract used by the current web client."""
    try:
        handler = GET_HANDLERS[path]
    except KeyError as exc:
        raise ContractRouteNotFound(path) from exc
    return handler(contract, args)


def dispatch_api_post(contract: WebContract, path, body):
    try:
        handler = POST_HANDLERS[path]
    except KeyError as exc:
        raise ContractRouteNotFound(path) from exc
    return handler(contract, body)
