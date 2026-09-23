"""站点解析器：契约在 `base`，一个站一个模块。已套契约的站登记在 `SITE_SOURCES`，迁移状态见 `docs/SOURCING.md`。"""
from __future__ import annotations

from .base import (COOLDOWN_ACTIONS, PERMANENT_REASONS, REASON_KINDS, FailureReason, Page, Session,
                   SiteConfig, SiteRecord, SiteSource, SourceFailure, http_failure)
from .javbus import JAVBUS, JavBusSource
from .javdb import JAVDB, JavDBSource

#: 来源名 → 站的类。`community_catalog` 按它取站，测试按它核配置与 `SOURCE_SPECS` 等表的一致。
SITE_SOURCES: dict[str, type[SiteSource]] = {
    JAVBUS.name: JavBusSource,
    JAVDB.name: JavDBSource,
}

__all__ = ["COOLDOWN_ACTIONS", "PERMANENT_REASONS", "REASON_KINDS", "SITE_SOURCES", "FailureReason", "Page",
           "Session", "SiteConfig", "SiteRecord", "SiteSource", "SourceFailure", "http_failure",
           "JAVBUS", "JAVDB", "JavBusSource", "JavDBSource"]
