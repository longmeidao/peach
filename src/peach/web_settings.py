"""跟人走的界面设置。

大部分界面偏好留在浏览器本地就够了——悬停延迟、每批数量、默认排序，这些更像
「这台设备上顺手」而不是「我的习惯」，换台电脑重设一次也不奇怪。

侧栏不一样。左侧导航放哪些入口、什么顺序，是长出来的使用习惯；在 Windows 上排好，
到 Mac 上又是默认顺序，那不叫两台设备，叫两个应用。所以它跟着账本走。

落点是 `profile.settings_json`——0001 建表时就留好的字段，一直是空的 `{}`。
不新建表也就不需要迁移。

写入受 ledger 只读闸门约束：reader（macOS）改不了顺序，但读到的是 writer 的那份，
这正是「同一份习惯」的意思。
"""
from __future__ import annotations

import json
import time
from typing import Protocol

DEFAULT_PROFILE_ID = "local-default"

#: 默认就在侧栏里的入口，顺序即默认顺序。
DEFAULT_SIDEBAR_ORDER = (
    "", "performers", "tags", "jav", "flagged", "playlists", "follow", "immerse", "manage",
)
#: 可以加进侧栏、但默认不在的入口。
OPTIONAL_SIDEBAR_KEYS = (
    "stats", "review", "ads", "dupes", "trash", "follow-manage", "quality",
)
ALL_SIDEBAR_KEYS = frozenset(DEFAULT_SIDEBAR_ORDER) | frozenset(OPTIONAL_SIDEBAR_KEYS)

#: 只有这些键跟着账本走。白名单而不是黑名单：将来往设置里加字段的人必须显式表态
#: 它该不该跨机同步，而不是默认就同步过去。
SYNCED_SETTING_KEYS = frozenset({"sidebarOrder"})


class SettingsContract(Protocol):
    def read_connection(self): ...
    def write_transaction(self): ...


def normalise_sidebar_order(raw) -> list[str]:
    """把任意输入收敛成一份合法的侧栏顺序。

    数组同时表达顺序和显隐：在里面就显示，不在就不显示。所以「取消显示」和
    「调整顺序」是同一个写入，不需要两个字段。

    不认识的键直接丢掉——它可能来自旧版本或者手改的载荷，留着会让前端渲染出
    一个点不开的入口。全部丢光时回落到默认顺序，空侧栏没有可用性可言。
    """
    if not isinstance(raw, list):
        return list(DEFAULT_SIDEBAR_ORDER)
    seen: list[str] = []
    for key in raw:
        if not isinstance(key, str) or key not in ALL_SIDEBAR_KEYS or key in seen:
            continue
        seen.append(key)
    return seen or list(DEFAULT_SIDEBAR_ORDER)


def _stored(contract: SettingsContract) -> dict:
    with contract.read_connection() as connection:
        row = connection.execute(
            "SELECT settings_json FROM profile WHERE id=?", (DEFAULT_PROFILE_ID,),
        ).fetchone()
    if row is None:
        return {}
    try:
        payload = json.loads(row["settings_json"] or "{}")
    except (TypeError, ValueError):
        # 载荷坏了就当没设置过：这是界面偏好，不值得让页面打不开。
        return {}
    return payload if isinstance(payload, dict) else {}


def q_settings(contract: SettingsContract, _args=None) -> dict:
    """读取跟人走的那部分设置。缺省时返回默认值，不返回空。"""
    payload = _stored(contract)
    return {"sidebarOrder": normalise_sidebar_order(payload.get("sidebarOrder"))}


def w_settings(contract: SettingsContract, body) -> dict:
    """写入跟人走的设置；只认白名单里的键。

    合并而不是整体替换：请求里没提到的键保持原样，这样将来新增同步字段时，
    旧版本前端提交的载荷不会把它抹掉。
    """
    if not isinstance(body, dict):
        raise TypeError("settings body must be an object")
    unknown = set(body) - SYNCED_SETTING_KEYS
    if unknown:
        raise ValueError(f"这些设置不跟账本同步：{sorted(unknown)}")
    if not body:
        raise ValueError("没有要写入的设置")

    merged = _stored(contract)
    if "sidebarOrder" in body:
        merged["sidebarOrder"] = normalise_sidebar_order(body["sidebarOrder"])
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with contract.write_transaction() as connection:
        updated = connection.execute(
            "UPDATE profile SET settings_json=?, updated_at=? WHERE id=?",
            (json.dumps(merged, ensure_ascii=False), stamp, DEFAULT_PROFILE_ID),
        ).rowcount
        if not updated:
            raise ValueError(f"profile {DEFAULT_PROFILE_ID} 不存在")
    return {"ok": True, **q_settings(contract)}
