"""一次「检查更新」的完整流程：取回 → 落库 → 顺带学一条作者别名。

Web 与命令行共用这一份。各写一遍必然分岔：其中一份漏掉往回翻页、漏掉凭据到位
之后的强制重取、不学官方渠道的作者别名，于是同一句「检查更新」在网页上做的事比
在终端里多，而没有任何地方说明这一点。

网络与落库都在这里，事务边界由调用方传进来的 `writer` 决定：Web 每条来源一个写
事务，命令行是一条连接加显式 commit。展示不在这里，`CheckResult` 交回给调用方。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from .follow import FollowHistoryEnd, FollowSourceError
from .follow_secrets import CredentialError
from .follow_sources import SourceFetch, enrichment_mark
from .follow_store import RecordOutcome


@dataclass(frozen=True)
class CheckResult:
    """一条来源检查完之后发生了什么。

    失败也是返回值而不是异常：逐条独立成败，一个来源缺凭据或被机器人验证挡住，
    不该让其余来源的更新一起消失。
    """

    source_id: int
    provider: str
    ref: str
    label: str
    page: int = 0
    older: bool = False
    ok: bool = True
    status: str = "ok"
    error: str = ""
    message: str = ""
    exhausted: bool = False
    fetch: SourceFetch | None = None
    outcome: RecordOutcome | None = None
    author_alias_learned: dict | None = None


def plan_check(store, credentials, *, source_id: int | None = None,
               older: bool = False, force: bool = False,
               backfill_providers: frozenset[str] = frozenset()) -> list[dict]:
    """要检查哪些来源，以及每条要不要绕过条件请求游标。只读，不联网。

    `force_media_reparse` 单独在这里算好：凭据已经存在、但旧候选还标着
    `media_needs_credential` 时，条件请求的 304 会让旧解析结果永久不变——显式检查
    得无条件重取一次，凭据才真正生效。往回翻页时不算这个，那一页本来就没游标。

    `force=True` 是命令行 `--force` 那种无条件重取，对每条来源都成立。
    """
    rows = [dict(row) for row in store.sources(enabled_only=True)
            if (source_id is None or row["id"] == source_id)
            and (not older or row["provider"] in backfill_providers)]
    for row in rows:
        row["force_media_reparse"] = force or (
            not older and credentials.load(row["provider"]) is not None
            and store.source_needs_media_reparse(row["id"])
        )
        # 第二阶段跳过谁：细节已经补齐的条目。强制重取时不跳过任何一条——
        # 那正是把上一轮没取到的细节补回来的时机。
        mark = enrichment_mark(row["provider"])
        row["enrich_skip"] = (
            frozenset() if row["force_media_reparse"] or not mark
            else store.enriched_external_ids(row["id"], mark))
    return rows


def build_connector_for(provider: str, credentials, connector_factory, *,
                        enrich_skip: frozenset[str] = frozenset()):
    """按凭据仓库里现有的凭据造一个连接器。

    `connector_factory` 由调用方传进来（各自模块里的 `build_connector`），不在这里
    直接引用：那样调用方替换它才有效，测试也才能只替自己那一处。
    """
    kwargs = {"credential": credentials.load(provider)}
    gofile_credential = credentials.load("gofile")
    if gofile_credential is not None:
        kwargs["gofile_credential"] = gofile_credential
    if enrich_skip:
        kwargs["enrich_skip"] = enrich_skip
    return connector_factory(provider, **kwargs)


def run_check(row: Mapping, *, credentials, writer, connector_factory,
              older: bool = False, moment: datetime | None = None,
              progress=None) -> CheckResult:
    """检查一条来源。

    `row` 是 `plan_check` 给出的那种字典。`writer` 是零参可调用对象，返回一个产出
    `FollowStore` 的上下文管理器；每次写都单独取一次，好让调用方决定提交粒度。
    """
    moment = moment or datetime.now(timezone.utc)
    source_id = int(row["id"])
    provider, ref = str(row["provider"]), str(row["ref"])
    page = (int(row["backfill_page"] or 0) + 1) if older else 0
    base = {"source_id": source_id, "provider": provider, "ref": ref,
            "label": str(row["label"] or ""), "page": page, "older": older}
    force = bool(row.get("force_media_reparse"))
    try:
        connector = build_connector_for(
            provider, credentials, connector_factory,
            enrich_skip=frozenset(row.get("enrich_skip") or ()))
        if progress is not None:
            connector.progress = progress
        fetch = connector.fetch(
            ref,
            etag=None if force else row["etag"],
            last_modified=None if force else row["last_modified"],
            page=page,
        )
    except FollowHistoryEnd:
        with writer() as store:
            store.record_history_end(source_id, moment)
        return CheckResult(**base, exhausted=True, message="没有更多历史内容")
    except CredentialError as error:
        return _record_failure(writer, base, error, moment, "unauthorized")
    except FollowSourceError as error:
        return _record_failure(writer, base, error, moment, "error")
    with writer() as store:
        outcome = store.record(
            source_id, fetch,
            creator_aliases=store.creator_aliases(row["entity_id"]),
            moment=moment, page=page)
        learned = store.learn_official_author_alias(provider, ref, fetch.candidates)
    return CheckResult(**base, fetch=fetch, outcome=outcome,
                       author_alias_learned=learned)


def _record_failure(writer, base: dict, error: Exception, moment: datetime,
                    status: str) -> CheckResult:
    with writer() as store:
        store.record_error(base["source_id"], str(error), moment, status=status)
    return CheckResult(**base, ok=False, status=status, error=str(error))
