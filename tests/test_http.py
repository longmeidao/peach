import unittest

import httpx

from peach.http import CurlCffiTransport, HttpRequest, HttpxTransport


class _CurlResponse:
    status_code = 206
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    @staticmethod
    def iter_content():
        yield b"abc"
        yield b"def"


class _CurlSession:
    def __init__(self):
        self.calls = []
        self.closed = False

    def stream(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return _CurlResponse()

    def close(self):
        self.closed = True


class HttpTransportTests(unittest.TestCase):
    def test_shared_transport_bounds_response_without_hiding_status(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["X-Test"], "yes")
            return httpx.Response(304, headers={"ETag": '"v1"'}, content=b"abcdef")

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            response = HttpxTransport(client)(
                HttpRequest("GET", "https://example.test/feed", {"X-Test": "yes"}),
                timeout=2,
                max_bytes=4,
            )
        self.assertEqual(response.status, 304)
        self.assertEqual(response.body, b"abcde")
        self.assertEqual(response.headers["etag"], '"v1"')

    def test_the_final_url_after_a_redirect_is_reported_not_the_requested_one(self):
        """两个 transport 都开着 follow_redirects，请求地址因此不等于实际取到的页面。

        真实用例：minnano-av 的女优检索唯一命中时会跳到 `actressNNN.html`，多命中则
        停在检索页。两种情况的请求地址一模一样，只有最终地址能区分——而检索页正文里
        同样有一堆 `actressNNN.html`（那是「相关女优」）。丢掉最终地址，判断「这一页
        属于谁」就只能去解析正文，那会把别人的资料安到这个人头上。
        """
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/search":
                return httpx.Response(302, headers={"Location": "/actress494354.html"})
            return httpx.Response(200, content=b"ok")

        with httpx.Client(transport=httpx.MockTransport(handler),
                          follow_redirects=True) as client:
            response = HttpxTransport(client)(
                HttpRequest("GET", "https://example.test/search", {}), timeout=2,
                max_bytes=64)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.url, "https://example.test/actress494354.html")

    def test_a_transport_that_cannot_report_a_final_url_falls_back_to_the_request(self):
        """替身不带 url 时退回请求地址，语义仍成立，不必逼替身长出不关心的属性。"""
        session = _CurlSession()
        response = CurlCffiTransport(impersonate="firefox147", session=session)(
            HttpRequest("GET", "https://example.test/x", {}), timeout=2, max_bytes=64)
        self.assertEqual(response.url, "https://example.test/x")

    def test_browser_transport_keeps_the_same_bounded_contract(self):
        session = _CurlSession()
        transport = CurlCffiTransport(impersonate="firefox147", session=session)
        response = transport(
            HttpRequest("GET", "https://example.test/detail", {"X-Test": "yes"}),
            timeout=3,
            max_bytes=4,
        )
        self.assertEqual(response.status, 206)
        self.assertEqual(response.body, b"abcde")
        method, url, kwargs = session.calls[0]
        self.assertEqual((method, url), ("GET", "https://example.test/detail"))
        self.assertEqual(kwargs["headers"]["X-Test"], "yes")
        self.assertEqual(kwargs["timeout"], 3)
        self.assertTrue(kwargs["allow_redirects"])

    def test_injected_browser_session_is_not_closed_by_the_transport(self):
        session = _CurlSession()
        transport = CurlCffiTransport(impersonate="firefox147", session=session)
        transport.close()
        self.assertFalse(session.closed)


if __name__ == "__main__":
    unittest.main()
