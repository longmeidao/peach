"""站点解析器契约：取页与解析分开、配置注入、`query` 的异常翻译、失败原因表，以及配置与各张表的一致。"""
import unittest
from unittest.mock import patch

import httpx

from peach import scraping_access
from peach.http import HttpResponse
from peach.jav_cover_fetch import DeadlineExceeded, NotFound, Unavailable
from peach.library_processing import PROVIDER_NAMES, SOURCE_INTERVALS, SOURCE_LABELS
from peach.metadata import MetadataProviderError
from peach.metadata_policy import SOURCE_SPECS
from peach.scraping_access import SourcePaused
from peach.sources import (COOLDOWN_ACTIONS, PERMANENT_REASONS, REASON_KINDS, SITE_SOURCES, FailureReason, Page,
                           Session, SiteConfig, SiteRecord, SiteSource, SourceFailure, http_failure)

DEMO = SiteConfig(name="demo", label="Demo", provider="demo-page", base_url="https://demo.test",
                  domains=("demo.test",), stage="community")


class DemoSource(SiteSource):
    """最小的一站：作品页是 `/<番号>`，页面正文就是标题。"""

    DEFAULT = DEMO

    def fetch(self, code, *, session):
        return session.get(f"{self.config.base_url}/{code}", config=self.config)

    def parse(self, page, code):
        if page.text == "gate":
            raise SourceFailure(FailureReason.AUTH_REQUIRED, "Demo 要求登录")
        return SiteRecord(source=self.config.name, provenance=self.config.provider, code=code,
                          source_url=page.url, title=page.text)


def serve(pages):
    calls = []

    def call(request, timeout, limit):
        calls.append((request.url, request.headers.get("Referer"), limit))
        body = pages.get(request.url)
        if isinstance(body, Exception):
            raise body
        return HttpResponse(200 if body is not None else 404, {}, body or b"", request.url)

    call.calls = calls
    return call


class ContractTests(unittest.TestCase):
    def test_parse_reads_a_page_without_any_transport(self):
        record = DemoSource().parse(Page("https://demo.test/ABC-001", "標題".encode()), "ABC-001")
        self.assertEqual((record.source, record.provenance, record.title, record.source_url),
                         ("demo", "demo-page", "標題", "https://demo.test/ABC-001"))

    def test_fetch_uses_the_config_for_referer_and_page_limit_and_query_chains_both_steps(self):
        transport = serve({"https://demo.test/ABC-001": "標題".encode()})
        record = DemoSource().query("ABC-001", session=Session(transport))
        self.assertEqual(record.title, "標題")
        self.assertEqual(transport.calls, [("https://demo.test/ABC-001", "https://demo.test/", DEMO.page_limit)])

    def test_an_injected_config_replaces_the_default_one(self):
        mirror = SiteConfig(name="demo", label="Demo", provider="demo-page", base_url="https://mirror.test",
                            domains=("mirror.test",), stage="community", page_limit=1024)
        transport = serve({"https://mirror.test/ABC-001": b"x"})
        DemoSource(mirror).query("ABC-001", session=Session(transport))
        self.assertEqual(transport.calls, [("https://mirror.test/ABC-001", "https://mirror.test/", 1024)])
        self.assertIs(DemoSource().config, DEMO)

    def test_query_translates_http_tiers_into_reasons_and_keeps_the_wording(self):
        with self.assertRaises(SourceFailure) as caught:
            DemoSource().query("ABC-001", session=Session(serve({})))
        self.assertEqual((caught.exception.reason, caught.exception.status_code, str(caught.exception)),
                         (FailureReason.NOT_FOUND, 404, "HTTP 404"))
        for status, reason in ((401, FailureReason.AUTH_REQUIRED), (403, FailureReason.AUTH_REQUIRED),
                               (410, FailureReason.GONE), (429, FailureReason.RATE_LIMITED),
                               (500, FailureReason.SERVER_ERROR), (503, FailureReason.SERVER_ERROR),
                               (418, FailureReason.NETWORK)):
            with self.subTest(status=status):
                failure = http_failure(Unavailable(f"HTTP {status}"))
                self.assertEqual((failure.reason, failure.status_code, failure.message), (reason, status, f"HTTP {status}"))
        self.assertEqual(http_failure(NotFound("来源给的是占位图")).reason, FailureReason.NOT_FOUND)

    def test_query_passes_parse_failures_through_and_leaves_transport_signals_alone(self):
        """冷却、预算与连接失败由传输层抛、由调用方按原语义处理，契约不改写它们。"""
        with self.assertRaises(SourceFailure) as caught:
            DemoSource().query("ABC-001", session=Session(serve({"https://demo.test/ABC-001": b"gate"})))
        self.assertEqual(caught.exception.reason, FailureReason.AUTH_REQUIRED)
        for signal in (SourcePaused("来源正在冷却"), DeadlineExceeded("动作预算已用尽"),
                       httpx.TransportError("来源连接未取得")):
            with self.subTest(signal=type(signal).__name__), \
                    patch("peach.jav_cover_fetch.NETWORK_RETRY_DELAYS", ()), \
                    self.assertRaises(type(signal)):
                DemoSource().query("ABC-001", session=Session(serve({"https://demo.test/ABC-001": signal})))

    def test_the_record_projects_into_the_snapshot_shaped_payload(self):
        record = SiteRecord(source="demo", provenance="demo-page", code="ABC-001", source_url="https://demo.test/ABC-001",
                            title="標題", performers=({"japanese_name": "女優"},), studio="片商", runtime=90,
                            cover_urls=("https://demo.test/a.jpg", "https://demo.test/b.jpg"))
        self.assertEqual(record.cover_url, "https://demo.test/a.jpg")
        self.assertEqual(record.payload(), {
            "id": "ABC-001", "source_url": "https://demo.test/ABC-001", "title": "標題",
            "actresses": [{"japanese_name": "女優"}], "maker": "片商", "label": "", "series": "", "director": "",
            "release_date": "", "runtime": 90, "cover_urls": ["https://demo.test/a.jpg", "https://demo.test/b.jpg"],
            "cover_url": "https://demo.test/a.jpg"})
        tagged = SiteRecord(source="demo", provenance="demo-page", code="ABC-001", source_url="", tags=(),
                            extra={"plot": "剧情"})
        payload = tagged.payload()
        self.assertEqual((payload["genres"], payload["plot"], payload["cover_urls"], payload["cover_url"]),
                         ([], "剧情", [], ""))
        self.assertNotIn("genres", record.payload(), "不给标签的站不带 genres 键")


class FailureReasonTests(unittest.TestCase):
    def test_the_table_has_twelve_reasons_each_with_a_kind(self):
        self.assertEqual({reason.value for reason in FailureReason}, {
            "cloudflare_challenge", "ip_banned", "geo_restricted", "auth_required", "not_found", "gone",
            "parse_error", "no_usable_metadata", "rate_limited", "timeout", "server_error", "network"})
        self.assertEqual(set(REASON_KINDS), set(FailureReason))
        self.assertEqual(set(REASON_KINDS.values()), {"auth", "unavailable", "not_found"})
        self.assertEqual({reason for reason, kind in REASON_KINDS.items() if kind == "auth"},
                         {FailureReason.CLOUDFLARE_CHALLENGE, FailureReason.IP_BANNED,
                          FailureReason.GEO_RESTRICTED, FailureReason.AUTH_REQUIRED})
        self.assertEqual({reason for reason, kind in REASON_KINDS.items() if kind == "not_found"},
                         {FailureReason.NOT_FOUND, FailureReason.GONE, FailureReason.NO_USABLE_METADATA})

    def test_provider_errors_keep_the_three_tier_semantics(self):
        auth = SourceFailure(FailureReason.CLOUDFLARE_CHALLENGE, "撞上 Cloudflare 挑战页", status_code=403)
        error = auth.provider_error("AVSOX")
        self.assertIsInstance(error, MetadataProviderError)
        self.assertEqual((error.kind, error.status_code, error.retryable, error.temporary, error.detail),
                         ("auth", 403, False, True, "cloudflare_challenge"))
        self.assertEqual(str(error), "AVSOX 需要登录或已被拒绝：撞上 Cloudflare 挑战页")
        missing = SourceFailure(FailureReason.NOT_FOUND, "javdb 没有这个番号").provider_error("javdb")
        self.assertEqual((missing.kind, str(missing)), ("not_found", "javdb 没有这个番号"))
        parse = SourceFailure(FailureReason.PARSE_ERROR, "结构对不上").provider_error("javdb")
        self.assertEqual((parse.kind, parse.retryable, parse.temporary), ("unavailable", False, False))
        timeout = SourceFailure(FailureReason.TIMEOUT, "超时", detail="curl 28").provider_error("javdb")
        self.assertEqual((timeout.kind, timeout.retryable, timeout.temporary, timeout.detail),
                         ("unavailable", True, True, "curl 28"))
        self.assertEqual(PERMANENT_REASONS, {FailureReason.PARSE_ERROR})

    def test_only_bans_and_rate_limits_pause_a_whole_site(self):
        self.assertEqual(COOLDOWN_ACTIONS, {FailureReason.CLOUDFLARE_CHALLENGE: "blocked",
                                            FailureReason.IP_BANNED: "blocked",
                                            FailureReason.RATE_LIMITED: "rate_limited"})
        for reason in FailureReason:
            with self.subTest(reason=reason):
                self.assertEqual(SourceFailure(reason, "").cooldown_action, COOLDOWN_ACTIONS.get(reason, ""))
        self.assertEqual(set(COOLDOWN_ACTIONS.values()), {"blocked", "rate_limited"},
                         "两档就是 scraping_access.pause_source 的 refused=True / retry_after 两档")


class ConfigConsistencyTests(unittest.TestCase):
    """配置是数据：`SOURCE_SPECS`、`SOURCE_LABELS`、`PROVIDER_NAMES`、`scraping_access.SOURCES` 与
    `SOURCE_INTERVALS` 里这几站的那几行，与站的配置逐项一致。"""

    def test_every_registered_site_agrees_with_the_existing_tables(self):
        for name, site in SITE_SOURCES.items():
            config = site.DEFAULT
            with self.subTest(site=name):
                self.assertIs(site().config, config)
                self.assertEqual(config.name, name)
                self.assertEqual(config.stage, SOURCE_SPECS[name].kind)
                self.assertEqual(config.label, SOURCE_LABELS[name])
                self.assertEqual(config.provider, PROVIDER_NAMES[name])
                access = scraping_access.SOURCES[name]
                self.assertEqual(set(config.domains), set(access["domains"]))
                self.assertEqual(config.cookie, bool(access.get("cookie")))
                self.assertTrue(config.base_url.startswith("https://"))
                self.assertEqual(scraping_access.source_for(config.base_url), name)
                for host, interval in SOURCE_INTERVALS.items():
                    if scraping_access.source_for("https://" + host + "/") == name:
                        self.assertEqual(interval, config.interval, f"{host} 的主机间隔与配置不一致")

    def test_javdb_keeps_the_user_set_interval_and_the_other_sites_the_default(self):
        self.assertEqual(SITE_SOURCES["javdb"].DEFAULT.interval, 3.0)
        for name in ("javbus", "avbase", "r18dev"):
            self.assertEqual(SITE_SOURCES[name].DEFAULT.interval, 2.0, name)
        self.assertEqual({host for host in SOURCE_INTERVALS if scraping_access.source_for("https://" + host + "/") == "javdb"},
                         set(SOURCE_INTERVALS), "SOURCE_INTERVALS 里只有 javdb 的主机单独设间隔")

    def test_the_four_sites_are_registered_with_their_stage_cookie_and_page_limit(self):
        self.assertEqual(set(SITE_SOURCES), {"r18dev", "avbase", "javbus", "javdb"})
        shape = {name: (site.DEFAULT.stage, site.DEFAULT.cookie, site.DEFAULT.page_limit)
                 for name, site in SITE_SOURCES.items()}
        self.assertEqual(shape, {"r18dev": ("official_mirror", False, 2 * 1024 * 1024),
                                 "avbase": ("community", False, 4 * 1024 * 1024),
                                 "javbus": ("community", True, 4 * 1024 * 1024),
                                 "javdb": ("community", True, 4 * 1024 * 1024)})
        self.assertTrue(all(SOURCE_SPECS[name].official is (name == "r18dev") for name in SITE_SOURCES))


if __name__ == "__main__":
    unittest.main()
