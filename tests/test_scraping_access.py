"""独立安装的来源配置、凭据边界与实际传输行为。"""
import json
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx
from PIL import Image

from peach.http import HttpRequest, HttpResponse, HttpxTransport
from peach.scraping_access import (SourceTransport, client_for, cookie_jar, describe,
                                   save, source_for, values_for)
from peach.web_scraping import q_scraping, w_scraping_check


class ScrapingAccessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def test_independent_installations_never_share_session_or_proxy(self):
        save(self.root, "fc2cmadb", {"cookie": "session=private-cookie", "network": "proxy",
                                  "proxy": "http://user:private-proxy@127.0.0.1:7890"})
        public = q_scraping(SimpleNamespace(follow_secrets_root=self.root), {})
        self.assertEqual(next(item['label'] for item in public['sources'] if item['source'] == 'fc2cmadb'), 'FC2CMADB')
        self.assertNotIn("private-cookie", json.dumps(public))
        self.assertNotIn("private-proxy", json.dumps(public))
        self.assertFalse(describe(self.root / "other-user", "fc2cmadb")["cookie_saved"])
        save(self.root, "fc2cmadb", {"revoke": True})
        self.assertFalse(describe(self.root, "fc2cmadb")["cookie_saved"])
        self.assertEqual(values_for(self.root, "fc2cmadb")["network"], "proxy")

    def test_import_discards_expired_foreign_and_cdn_cookies(self):
        text = ("# Netscape HTTP Cookie File\n"
                ".instagram.com\tTRUE\t/\tTRUE\t4102444800\tsessionid\tvalid\n"
                ".instagram.com\tTRUE\t/\tTRUE\t1\texpired\told\n"
                ".cdninstagram.com\tTRUE\t/\tTRUE\t4102444800\tsession\tcdn\n"
                ".example.org\tTRUE\t/\tTRUE\t4102444800\tforeign\tother\n")
        jar = cookie_jar({"cookies_text": text}, "instagram")
        self.assertEqual([(c.name, c.value) for c in jar], [("sessionid", "valid")])
        with httpx.Client(cookies=jar) as client:
            self.assertIn("sessionid", client.build_request("GET", "https://www.instagram.com/").headers["cookie"])
            self.assertNotIn("cookie", client.build_request("GET", "https://scontent.cdninstagram.com/x.jpg").headers)

    def test_empty_malformed_and_cross_site_cookie_imports_are_rejected(self):
        for supplied in ({"cookie": "bad\nheader"}, {"cookies_text": "not a cookie jar"},
                         {"cookie": "a=b", "cookies_text": "anything"}):
            with self.subTest(supplied=list(supplied)), self.assertRaises(ValueError):
                save(self.root, "instagram", supplied)

    def test_network_mode_reaches_the_client_and_survives_renewal(self):
        save(self.root, "dmm", {"network": "direct"})
        with patch("peach.scraping_access.httpx.Client") as factory:
            client_for(self.root, "dmm")
            self.assertFalse(factory.call_args.kwargs["trust_env"])
        transport = SourceTransport(self.root)
        self.addCleanup(transport.close)
        with patch("peach.scraping_access.client_for") as factory:
            fake = factory.return_value
            fake.stream.return_value.__enter__.return_value.iter_bytes.return_value = [b"ok"]
            for _ in range(2):
                transport(HttpRequest("GET", "https://pics.dmm.co.jp/x", {}), 1, 10)
                transport.renew()
            self.assertEqual(factory.call_count, 2)
            self.assertEqual(fake.close.call_count, 2)

    def test_redirect_selects_destination_policy_and_strips_secrets(self):
        transport = SourceTransport(self.root)
        with patch.object(transport, "_request", side_effect=[
            HttpResponse(302, {"location": "https://pics.dmm.co.jp/x"}, b""),
            HttpResponse(200, {}, b"image"),
        ]) as request:
            result = transport(HttpRequest("GET", "https://r18.dev/x", {"Cookie": "secret", "Authorization": "secret"}), 1, 20)
        self.assertEqual(result.body, b"image")
        self.assertEqual(request.call_args_list[1].args[0].headers, {})
        self.assertEqual(source_for("https://evil-dmm.co.jp/x"), None)
        self.assertEqual(source_for("https://awsimgsrc.dmm.com/x"), "dmm")

    def test_connections_do_not_claim_session_validity_or_echo_exception_urls(self):
        contract = SimpleNamespace(follow_secrets_root=self.root)
        with patch("peach.web_scraping.SourceTransport") as factory:
            factory.return_value.side_effect = httpx.ConnectError("https://secret:password@example.org/")
            result = w_scraping_check(contract, {"source": "fc2cmadb"})
        self.assertFalse(result["session_verified"])
        self.assertNotIn("password", json.dumps(result))
        self.assertFalse(result["results"][0]["ok"])

    def test_transport_ownership_is_explicit(self):
        for owned in (True, False):
            client = httpx.Client()
            transport = HttpxTransport(client, owns_client=owned)
            transport.close()
            self.assertEqual(client.is_closed, owned)
            client.close()

    def test_rate_limit_cooldown_survives_a_new_transport(self):
        from peach.scraping_access import SourcePaused
        transport = SourceTransport(self.root)
        transport.transports["dmm"] = lambda *args: HttpResponse(429, {"retry-after": "600"}, b"")
        request = HttpRequest("GET", "https://pics.dmm.co.jp/x", {})
        with self.assertRaises(SourcePaused):
            transport(request, 1, 100)
        with patch("peach.scraping_access.client_for") as factory:
            with self.assertRaises(SourcePaused):
                SourceTransport(self.root)(request, 1, 100)
        factory.assert_not_called()

    def test_full_quality_bytes_are_installed_and_cache_avoids_download(self):
        from peach.web_scraping import _fetch_cover
        from peach.jav_cover_fetch import Candidate
        output = io.BytesIO()
        Image.new("RGB", (1600, 1000)).save(output, "JPEG")
        original = output.getvalue()
        contract = SimpleNamespace(cover_root=self.root / "covers", candidate_root=self.root,
                                   follow_secrets_root=self.root / "secrets", follow_sources_root=self.root)
        with patch("peach.jav_cover_fetch.best_cover", return_value=(
            Candidate("dmm", "https://pics.dmm.co.jp/fixture.jpg"), (1600, 1000), original,
        )) as fetch:
            result = _fetch_cover(contract, "ABW-232")
            cached = _fetch_cover(contract, "ABW-232")
        self.assertTrue(result["ok"])
        self.assertTrue(cached["ok"])
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual((contract.cover_root / "ABW-232.jpg").read_bytes(), original)

    def test_smaller_candidate_cannot_overwrite_a_full_quality_cover(self):
        from peach.web_scraping import _fetch_cover
        from peach.jav_cover_fetch import Candidate
        target = self.root / "ABW-232.jpg"
        Image.new("RGB", (2000, 1400)).save(target, "JPEG")
        original = target.read_bytes()
        contract = SimpleNamespace(cover_root=self.root, candidate_root=self.root,
                                   follow_secrets_root=self.root / "secrets", follow_sources_root=self.root)
        with patch("peach.jav_cover_fetch.best_cover", return_value=(
            Candidate("dmm", "https://pics.dmm.co.jp/fixture.jpg"), (800, 600), b"small",
        )):
            result = _fetch_cover(contract, "ABW-232")
        self.assertTrue(result["ok"])
        self.assertEqual(target.read_bytes(), original)
