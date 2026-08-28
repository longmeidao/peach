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
