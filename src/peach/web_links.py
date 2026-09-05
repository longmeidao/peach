"""实体链接管理：库里有哪些外链，以及它们现在还打不打得开。

从 `web_contract` 拆出，理由和资源对账一样：这一域自己持有检查线程的状态和网络往返，
和浏览、复核没有共享逻辑。

为什么资料页需要这么一块管理面：链接是**别人服务器上的东西**，会在我们不知情的时候烂掉。
2026-09-01 实测 719 条里 152 条打不开，其中 84 条 official 是 404——而它们在资料页上
和好链接长得一模一样，只有点下去才知道。检查这件事必须能随时重跑，不能是一次性脚本。

`gone` 与 `unclear` 必须分开，这是这块面板最重要的一条：`linktr.ee` 回 403 是挡爬虫、
`x.com` 回 500 是临时错误，链接本身好好的。按「非 200 就删」会连它们一起删掉。
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from .jobs import BackgroundJob

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
#: 「这个页面没了」——只有上游明确这么说，才够格作为删除依据。
GONE_STATUSES = frozenset({404, 410})
CHECK_TIMEOUT = 12.0
CHECK_INTERVAL = 0.25


class LinkContract(Protocol):
    """链接管理需要契约提供的能力；比整个 WebContract 小得多。"""

    db_path: Path
    link_check: BackgroundJob
    link_prune_job: BackgroundJob

    def read_connection(self): ...

    def write_transaction(self): ...


def _probe(url: str, timeout: float = CHECK_TIMEOUT) -> tuple[int, str]:
    """(status, 说明)。status 为 0 表示连都没连上。

    每个请求新建 client 并立刻关掉：这批地址分布在上百个互不相同的主机上，其中不少
    连不上，而失败的连接会在共享池里漏掉槽位，几十个请求之后一切都变成 PoolTimeout。
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout,
                          limits=httpx.Limits(max_connections=4,
                                              max_keepalive_connections=0)) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
    except Exception as error:
        return 0, type(error).__name__
    return response.status_code, ""


def link_verdict(status: int, note: str) -> str:
    """ok / gone / unclear。

    取不到不等于没了。实测反例：`linktr.ee` 403（Linktree 挡爬虫，浏览器里能开）、
    `facebook.com` 400、`x.com` 500（临时错误，账号还在）、连接失败与超时。
    把它们并进 gone，删除时就会连好链接一起删。
    """
    if status == 200:
        return "ok"
    if status in GONE_STATUSES:
        return "gone"
    return "unclear"


def w_links(contract: LinkContract, args=None):
    """库里链接的现状。纯读库，随页面一起加载，不联网。"""
    with contract.read_connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT l.id, l.link_kind, l.label, l.url, l.hostname, e.kind AS entity_kind, "
            "e.canonical_name AS entity, e.id AS entity_id "
            "FROM entity_link l JOIN entity e ON e.id=l.entity_id "
            "ORDER BY e.kind, e.canonical_name, l.link_kind")]
    by_kind: dict[str, int] = {}
    by_entity_kind: dict[str, int] = {}
    hosts: dict[str, int] = {}
    for row in rows:
        by_kind[row["link_kind"]] = by_kind.get(row["link_kind"], 0) + 1
        by_entity_kind[row["entity_kind"]] = by_entity_kind.get(row["entity_kind"], 0) + 1
        host = row["hostname"] or urlsplit(row["url"]).hostname or ""
        if host:
            hosts[host] = hosts.get(host, 0) + 1
    return {
        "ok": True,
        "total": len(rows),
        "entities": len({row["entity_id"] for row in rows}),
        "by_kind": by_kind,
        "by_entity_kind": by_entity_kind,
        "top_hosts": sorted(hosts.items(), key=lambda item: (-item[1], item[0]))[:12],
    }


def _check_public(state: dict) -> dict:
    return {
        "ok": state["status"] != "failed",
        "status": state["status"],
        "check_id": state["check_id"],
        "checked": state["checked"],
        "total": state["total"],
        "gone": [dict(item) for item in state["gone"]],
        "unclear": [dict(item) for item in state["unclear"]],
        **({"error": state["error"]} if state["status"] == "failed" else {}),
    }


def _run_link_check(contract: LinkContract, check_id: str) -> None:
    """逐条联网重验。异常由 `BackgroundJob` 翻成 `failed` 状态，这里不再自己接。"""
    job = contract.link_check
    with contract.read_connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT l.id, l.link_kind, l.label, l.url, e.canonical_name AS entity "
            "FROM entity_link l JOIN entity e ON e.id=l.entity_id ORDER BY l.id")]
    with job.editing(check_id) as state:
        if state is None:
            return
        state["total"] = len(rows)
    for row in rows:
        status, note = _probe(row["url"])
        verdict = link_verdict(status, note)
        with job.editing(check_id) as state:
            if state is None:
                return   # 被新的检查顶掉了，安静收工
            state["checked"] += 1
            if verdict != "ok":
                state["gone" if verdict == "gone" else "unclear"].append({
                    "id": row["id"], "entity": row["entity"],
                    "link_kind": row["link_kind"], "label": row["label"],
                    "url": row["url"],
                    "note": f"HTTP {status}" if status else f"取不到：{note}",
                })
        time.sleep(CHECK_INTERVAL)
    job.update(check_id, status="complete", completed_at=time.time())


def w_links_check(contract: LinkContract, body=None):
    """开始（或查询）一次死链检查。

    七百多条链接逐条联网要好几分钟，同步请求必然超时，所以和资源对账走同一套：
    `BackgroundJob` 的后台线程 + 可轮询状态。
    """
    body = body or {}
    if body.get("status_only") is True:
        state = contract.link_check.snapshot()
        if state is None:
            return {"ok": True, "status": "idle", "check_id": "", "checked": 0,
                    "total": 0, "gone": [], "unclear": []}
        return _check_public(state)
    return _check_public(contract.link_check.start(
        lambda check_id: _run_link_check(contract, check_id),
        initial={"checked": 0, "total": 0, "gone": [], "unclear": []},
        restart=body.get("restart") is True,
    ))


def w_links_prune(contract: LinkContract, body):
    """删掉上一次检查判定为 gone 的链接。

    只接受**刚跑完的那一次**检查的 `check_id`：拿一份放了半天的清单去删，删的可能是
    早已改好的链接。删除前逐条重验一次，这几秒钟换的是「不会因为一次网络抖动删掉好链接」。
    """
    body = body or {}
    if body.get("confirm") is not True:
        return {"ok": False, "error": "需要 confirm"}
    if body.get("background"):
        return contract.link_prune_job.start_result(
            lambda: w_links_prune(contract, {**body, "background": False}))
    state = contract.link_check.snapshot()
    if state is None or state["status"] != "complete":
        return {"ok": False, "error": "没有已完成的检查结果"}
    if body.get("check_id") != state["check_id"]:
        return {"ok": False, "error": "检查结果已过期，请重新检查"}
    planned = [dict(item) for item in state["gone"]]

    confirmed, recovered = [], []
    for item in planned:
        status, note = _probe(item["url"])
        (confirmed if link_verdict(status, note) == "gone" else recovered).append(item)

    removed = 0
    if confirmed:
        # 整批删除走同一个写事务：要么这一次判定的 gone 全部落库，要么一条都不落。
        with contract.write_transaction() as connection:
            for item in confirmed:
                removed += connection.execute(
                    "DELETE FROM entity_link WHERE id=?", (item["id"],)).rowcount
    with contract.link_check.editing(body.get("check_id")) as state:
        if state is not None:
            state["gone"] = []
    return {"ok": True, "removed": removed, "recovered": len(recovered),
            "entities": len({item["entity"] for item in confirmed})}
