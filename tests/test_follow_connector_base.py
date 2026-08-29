"""连接器基类共享骨架的隔离测试。

八个连接器的 fetch 开头原本各写一份「条件请求 → 304 短路 → 状态检查」。抽成
`_BaseConnector._request()` 之后，这些规则只有一处实现，所以也只需要在这里守住；
各站的解析差异仍由 `test_follow_sources.py` 覆盖。测试不联网，transport 全部注入。
"""
import unittest

from peach.follow import FollowSourceError
from peach.follow_sources import CONNECTORS, KemonoConnector, _BaseConnector
from peach.http import HttpResponse


def _transport(status=200, headers=None, body=b"", record=None):
    def call(request, timeout, max_bytes):
        if record is not None:
            record.append(request)
        return HttpResponse(status, headers or {}, body)
    return call


class _Probe(_BaseConnector):
    provider = "probe"


class SharedRequestSkeletonTests(unittest.TestCase):
    def test_first_page_sends_conditional_headers(self):
        seen = []
        connector = _Probe(transport=_transport(body=b"{}", record=seen))
        common, response = connector._request(
            "https://example.test/a", ref="r", etag='"v0"',
            last_modified="Wed, 13 Aug 2026 08:00:00 GMT")
        self.assertIsNotNone(response)
        self.assertEqual(seen[0].headers.get("If-None-Match"), '"v0"')
        self.assertEqual(seen[0].headers.get("If-Modified-Since"),
                         "Wed, 13 Aug 2026 08:00:00 GMT")
        self.assertEqual(common["ref"], "r")
        self.assertEqual(common["request_url"], "https://example.test/a")

    def test_paging_back_drops_conditional_headers(self):
        """往回翻页不能带条件请求头。

        `If-None-Match` 存的是第一页的 etag，拿它去问第二页，站点很可能回 304，
        表现就是「点了没反应」。这条规则过去在每个连接器里各写一遍，现在只有一处。"""
        seen = []
        connector = _Probe(transport=_transport(body=b"{}", record=seen))
        connector._request("https://example.test/a?o=50", ref="r", etag='"v0"',
                           last_modified="Wed, 13 Aug 2026 08:00:00 GMT", page=1)
        self.assertNotIn("If-None-Match", seen[0].headers)
        self.assertNotIn("If-Modified-Since", seen[0].headers)

    def test_not_modified_short_circuits_with_usable_common(self):
        connector = _Probe(transport=_transport(status=304, headers={"ETag": '"v1"'}))
        common, response = connector._request("https://example.test/a", ref="r")
        self.assertIsNone(response, "304 必须短路，调用方据此直接返回 not_modified")
        self.assertEqual(common["etag"], '"v1"')
        self.assertEqual(common["provider"], "probe")

    def test_request_url_can_be_masked_so_credentials_never_reach_evidence(self):
        """带凭据的真实 URL 绝不能落进证据档案。

        rule34xxx 的 `api_key` 在查询串里，必须传脱敏版本；`_request` 请求用真实 URL，
        `common` 里放脱敏 URL。"""
        seen = []
        connector = _Probe(transport=_transport(body=b"{}", record=seen))
        common, _ = connector._request(
            "https://example.test/a?api_key=secret", ref="r",
            request_url="https://example.test/a")
        self.assertIn("api_key=secret", seen[0].url, "请求本身仍要带真实凭据")
        self.assertNotIn("secret", str(common["request_url"]))

    def test_non_200_raises_before_the_caller_parses_anything(self):
        connector = _Probe(transport=_transport(status=500))
        with self.assertRaises(FollowSourceError):
            connector._request("https://example.test/a", ref="r")


class PublicProbeApiTests(unittest.TestCase):
    """`follow_discovery` 与 `web_follow` 要的是探测能力，不该去摸私有方法。"""

    def test_probe_returns_the_response_without_checking_status(self):
        """发现流程按状态码判断「作者页在不在」，404 是答案不是故障。"""
        connector = _Probe(transport=_transport(status=404))
        self.assertEqual(connector.probe("https://example.test/a").status, 404)

    def test_fetch_json_parses_and_rejects_non_200(self):
        connector = _Probe(transport=_transport(body=b'{"name": "x"}'))
        self.assertEqual(connector.fetch_json("https://example.test/a"), {"name": "x"})
        failing = _Probe(transport=_transport(status=503, body=b"{}"))
        with self.assertRaises(FollowSourceError):
            failing.fetch_json("https://example.test/a")

    def test_parse_json_rejects_a_non_json_body(self):
        connector = _Probe(transport=_transport(body=b"<html/>"))
        with self.assertRaises(FollowSourceError):
            connector.parse_json(connector.probe("https://example.test/a"))

    def test_every_connector_inherits_the_public_probe_api(self):
        for provider, factory in CONNECTORS.items():
            for name in ("probe", "fetch_json", "parse_json"):
                self.assertTrue(
                    hasattr(factory, name) or hasattr(KemonoConnector, name),
                    f"{provider} 缺少公开的 {name}",
                )


class NoPrivateReachIntoConnectorsTests(unittest.TestCase):
    def test_other_modules_never_call_connector_private_methods(self):
        """连接器之外的模块只能用公开 API。

        缺少「探测」这类公开入口时，调用方会直接摸 `_get`/`_check_status`/`_json`，
        于是基类的任何改动都可能悄悄弄坏发现流程。这条门槛把它挡在源码层面。"""
        import pathlib

        import peach

        root = pathlib.Path(peach.__file__).parent
        offenders = []
        for path in sorted(root.glob("*.py")):
            if path.name == "follow_sources.py":
                continue  # 基类自己的实现文件
            text = path.read_text(encoding="utf-8")
            for private in ("connector._get(", "connector._check_status(",
                            "connector._json(", "connector._post("):
                if private in text:
                    offenders.append(f"{path.name}: {private}")
        self.assertEqual(
            offenders, [],
            "改用 probe()／fetch_json()／parse_json()；缺能力就在基类补公开方法",
        )


if __name__ == "__main__":
    unittest.main()
