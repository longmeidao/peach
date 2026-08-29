"""追更的共享错误类型与工具。

这个模块原本是 ADR-0007 的 RSS/Atom 适配层。ADR-0019 之后那条路线不再成立——
七个实际来源实测无一提供 feed，站点连接器（`follow_sources.py`）取而代之。
2026-08-29 删掉 `FeedAdapter`、`FeedSnapshotStore` 及其专属 DTO，只留连接器和
存储层真正在用的四样东西：错误类型、正文净化、稳定 id、只写一次的证据落盘。

适配器只负责发现候选，不写 ledger 真相；调用方必须落盘原始证据，并让归一化后的
条目走复核边界。
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup


DEFAULT_MAX_BYTES = 5 * 1024 * 1024


class FollowSourceError(RuntimeError):
    pass


def plain_text(value: str | None) -> str | None:
    """把站点返回的 HTML 片段压成一行纯文本。"""
    if not value:
        return None
    cleaned = BeautifulSoup(value, "html.parser").get_text(" ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def stable_id(*parts: str | None) -> str:
    """来源没给 id 时，用内容本身算一个稳定的替代 id。"""
    material = "\n".join(part or "" for part in parts).encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def write_immutable(path: Path, payload: bytes) -> None:
    """原始证据只写一次。同名不同内容说明取证边界被破坏，直接报错。"""
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise FollowSourceError("immutable follow snapshot collision")
