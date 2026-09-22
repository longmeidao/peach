"""刮削登记了新实体之后，把认得准的那张头像补上（ADR-0040 第七条）。

刮削链每跑一轮都会往账本里登记新的女优和厂牌。它们刚建出来时没有头像：人物页那张圆图
退成作品抽帧，厂牌页退成首字母。补图的能力早就有，缺的是「刮完顺手补上」这一步——
在这之前它是一条人想起来才跑的命令行。

判据一个字都没新加：

* **女优**走图库，规则与 `scripts/fill_portrait_gaps.py` 同一条——按她整条名字链在图库里
  只找出一张，且尺寸过 `acceptable_avatar` 那一档，才装。找出好几张一张都不装：`ななみ`
  这种单名在图库里命中二十几张，那是二十几个人，自动挑等于随便给她安一张别人的脸。
* **厂牌**只登记缺口，不装图。厂牌 Logo 的采集要人先给出社交 handle
  （`scripts/fetch_studio_avatar_candidates.py`），猜出来的一律标 `needs_confirmation`，
  没有可以自动落图的那一档判据。

这条后继是幂等的（ADR-0040 第六条要求）：第一件事就是看盘上有没有那张图，有就当场返回。
"""
from __future__ import annotations

import sqlite3

from . import avatar_picker
from .avatar_provider import MIN_LONG_SIDE, MIN_SHORT_SIDE, acceptable_avatar
from .followups import Followup, FollowupType, register

#: 这类后继在任务中心的身份，也是活动页上那一行的名字来源。
TASK_KEY = "entity-avatar"
TASK_LABEL = "补实体头像"

#: 会被派后继的实体种类。别的种类（系列、标签）没有头像位，派了也无事可做。
KINDS = ("performer", "studio")

#: 一次刮削最多为这么多个新实体派后继。上限本身由 `task_runs.MAX_FOLLOWUPS` 判，
#: 这里先按作品数排好序再交出去：截断真的发生时，留下的该是库里出现得最多的那些。
PLAN_ORDER = "作品多的在前"


def followup_key(kind: str, entity_id: int) -> str:
    return f"{TASK_KEY}:{kind}:{int(entity_id)}"


def parse_key(key: str) -> tuple[str, int]:
    """把后继 key 拆回实体身份。形状不对就抛——那说明排队的行不是这个版本写的。"""
    prefix, _, rest = str(key).partition(":")
    kind, _, raw = rest.partition(":")
    if prefix != TASK_KEY or kind not in KINDS or not raw.isdigit():
        raise ValueError(f"认不出这条补头像后继：{key}")
    return kind, int(raw)


def plan(connection: sqlite3.Connection, avatar_root, *,
         since_entity_id: int) -> list[Followup]:
    """这一轮新登记、又没有头像的实体，一个一条后继。

    「新登记」按实体 id 的水位判：刮削开始前记一次 `max(id)`，比它大的就是这一轮建出来
    的。这比从落库结果里往回追要稳——实体可能由字段落库、别名归并或外部编号登记中的
    任何一条路建出来，而它们最终都表现为这张表上多了一行。
    """
    rows = connection.execute(
        "SELECT e.id,e.kind,e.canonical_name,"
        " (SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae"
        "  WHERE ae.entity_id=e.id) AS assets"
        " FROM entity e WHERE e.id>? AND e.kind IN (?,?) ORDER BY e.id",
        (int(since_entity_id), *KINDS)).fetchall()
    found = []
    for row in rows:
        entity_id, kind = int(row["id"]), str(row["kind"])
        if avatar_picker.installed_digest(avatar_root, kind, entity_id):
            continue
        found.append((int(row["assets"] or 0), entity_id, kind,
                      str(row["canonical_name"] or "")))
    found.sort(key=lambda item: (-item[0], item[1]))
    return [Followup(key=followup_key(kind, entity_id), task_key=TASK_KEY,
                     label=f"{TASK_LABEL}：{name}" if name else TASK_LABEL)
            for _assets, entity_id, kind, name in found]


def run(contract, key: str, handle) -> dict:
    """跑一条补头像后继。返回的摘要就是活动页上那一行。

    实体身份不进摘要——它已经在这条后继的 key 里，写两遍只是让那一行更难读。
    """
    kind, entity_id = parse_key(key)
    avatar_root = contract.avatar_root
    providers_root = contract.candidate_root / "provider-cache" / "performer-avatars"
    if avatar_picker.installed_digest(avatar_root, kind, entity_id):
        # 重跑、或者这中间人自己换过图。两种都不该再装一次。
        return {"outcome": "已有头像"}
    with contract.database.read_connection() as connection:
        row = connection.execute(
            "SELECT canonical_name FROM entity WHERE id=? AND kind=?",
            (entity_id, kind)).fetchone()
        if row is None:
            # 实体被合并或删掉了。这不是失败：那件事已经不存在了。
            return {"outcome": "实体已不存在"}
        name = str(row[0] or "")
        if kind != "performer":
            return {"name": name, "outcome": "等人复核", "matched": 0}
        # 图库索引只读本地缓存，这一步不联网；联网只发生在真的要装那一张的时候。
        listing = avatar_picker.choices(connection, providers_root, avatar_root,
                                        kind, entity_id)
        found = [choice for choice in listing["choices"]
                 if choice["source"] == "gfriends"]
        if not found:
            return {"name": name, "outcome": "图库里没有这个名字", "matched": 0}
        if len(found) > 1:
            return {"name": name, "outcome": "认不准，等人挑",
                    "matched": len(found)}
        handle.progress(label=f"{TASK_LABEL}：{name}", throttle=0)
        return _install(contract, connection, providers_root, avatar_root,
                        kind, entity_id, name, found[0])


def _install(contract, connection, providers_root, avatar_root, kind: str,
             entity_id: int, name: str, choice: dict) -> dict:
    """图库里只找出这一张，取来量一次再装。"""
    from .http import HttpxTransport

    transport = HttpxTransport()
    try:
        body, origin = avatar_picker.resolve(choice["ref"], connection,
                                             providers_root, entity_id, transport)
        inspected = avatar_picker.accept_image(body)
    finally:
        close = getattr(transport, "close", None)
        if close:
            close()
    size = f"{inspected.width}×{inspected.height}"
    if not acceptable_avatar(inspected, MIN_LONG_SIDE, MIN_SHORT_SIDE):
        return {"name": name, "outcome": "图太小", "matched": 1, "size": size}
    avatar_picker.install(providers_root, avatar_root, kind, entity_id, body, origin)
    contract.cache_bust()
    return {"name": name, "outcome": "已装上", "matched": 1, "size": size,
            "source": choice["label"]}


#: 不写账本：这条后继只往 `avatar_root` 与候选缓存里写文件。它照样一次只跑一条——
#: 通道按 task_key 分，同一种后继本来就共用一条。
TYPE = register(FollowupType(task_key=TASK_KEY, label=TASK_LABEL,
                             writes_ledger=False, run=run))
