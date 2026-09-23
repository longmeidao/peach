"""站点解析器：契约在 `base`，一个站一个模块。已套契约的站登记在 `SITE_SOURCES`，迁移状态见 `docs/SOURCING.md`。"""
from __future__ import annotations

from .avbase import AVBASE, AVBaseSource
from .base import (COOLDOWN_ACTIONS, PERMANENT_REASONS, REASON_KINDS, FailureReason, Page, Session,
                   SiteConfig, SiteRecord, SiteSource, SourceFailure, http_failure)
from .fc2 import FC2, Fc2Source
from .fc2cmadb import FC2CMADB, Fc2cmadbSource
from .javarchive import JAVARCHIVE, JavArchiveSource
from .javbus import JAVBUS, JavBusSource
from .javdb import JAVDB, JavDBSource
from .onepondo import ONEPONDO, OnePondoSource
from .r18dev import R18DEV, R18DevSource

#: 来源名 → 站的类。`LibraryMetadataProvider` 与 `scripts/scrape_codes.py` 按它取站，
#: 测试按它核配置与 `SOURCE_SPECS` 等表的一致。
SITE_SOURCES: dict[str, type[SiteSource]] = {
    R18DEV.name: R18DevSource,
    ONEPONDO.name: OnePondoSource,
    FC2.name: Fc2Source,
    FC2CMADB.name: Fc2cmadbSource,
    JAVARCHIVE.name: JavArchiveSource,
    AVBASE.name: AVBaseSource,
    JAVBUS.name: JavBusSource,
    JAVDB.name: JavDBSource,
}

__all__ = ["COOLDOWN_ACTIONS", "PERMANENT_REASONS", "REASON_KINDS", "SITE_SOURCES", "FailureReason", "Page",
           "Session", "SiteConfig", "SiteRecord", "SiteSource", "SourceFailure", "http_failure",
           "AVBASE", "FC2", "FC2CMADB", "JAVARCHIVE", "JAVBUS", "JAVDB", "ONEPONDO", "R18DEV",
           "AVBaseSource", "Fc2Source", "Fc2cmadbSource", "JavArchiveSource", "JavBusSource", "JavDBSource",
           "OnePondoSource", "R18DevSource"]
