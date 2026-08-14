import unittest

import httpx

from peach.http import HttpRequest, HttpxTransport


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


if __name__ == "__main__":
    unittest.main()
