"""amane 桥的 Peach 一侧：起子进程、翻 payload、失败分档、冷却动作，以及采集链上那一档。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from peach import metadata_amane
from peach.jav_cover_fetch import NotFound, Unavailable
from peach.library_processing import LibraryMetadataProvider, PROVIDER_NAMES, SOURCE_LABELS
from peach.metadata import MetadataProviderError, extract_peach_fields
from peach.metadata_policy import SOURCE_SPECS
from peach.metadata_routes import AMANE_STAGE
from peach.scraping_access import SourcePaused, cooldown_state, paused_until, pause_source

ROOT = Path(__file__).resolve().parents[1]


def completed(stdout, returncode=0, stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def report(**sites):
    return json.dumps({"number": "FC2-PPV-1234567", "language": "jp", "sites": sites,
                       "amane": {"version": "0.16.1"}}, ensure_ascii=False)


FOUND = {"status": "found", "metadata": {
    "number": "FC2-PPV-1234567", "title": "標題", "studio": "卖家", "publisher": "レーベル",
    "release": "2024-01-02", "runtime": 61, "tags": ["a", "b"], "series": "",
    "actors": [{"name": "女優", "gender": "female"}, {"name": "男", "gender": "male"}],
    "poster_urls": ["https://x/p.jpg"], "thumb_urls": ["https://x/t.jpg"],
    "trailer_urls": [], "extrafanart": ["https://x/1.jpg"], "directors": ["監督"],
    "source_url": "https://fc2ppvdb.com/articles/1234567", "external_id": "https://fc2ppvdb.com/articles/1234567",
}, "elapsed_s": 0.3}


class ManifestTests(unittest.TestCase):
    def test_the_manifest_pins_a_full_sha_and_the_lock_names_that_version(self):
        revision = metadata_amane.pinned_revision()
        self.assertRegex(revision, r"^[0-9a-f]{40}$")
        self.assertTrue(metadata_amane.locked_version())
        lock = (metadata_amane.BRIDGE_ROOT / "uv.lock").read_text(encoding="utf-8")
        self.assertIn(revision, lock)

    def test_every_opened_site_is_a_registered_community_source_and_a_bridge_site(self):
        bridge_sites = set(__import__("re").findall(r'^\s+"([a-z0-9]+)": \("', (
            metadata_amane.BRIDGE_SCRIPT).read_text(encoding="utf-8"), flags=__import__("re").M))
        for site in metadata_amane.SITES:
            with self.subTest(site=site):
                self.assertEqual(SOURCE_SPECS[site].kind, "community")
                self.assertIn(site, bridge_sites)
                self.assertIn(site, SOURCE_LABELS)
                self.assertIn(site, PROVIDER_NAMES)
        self.assertEqual(set(AMANE_STAGE), set(metadata_amane.SITES))
        for own in ("javdb", "javbus", "dmm"):
            self.assertNotIn(own, metadata_amane.SITES)

    def test_every_upstream_failure_reason_has_a_kind(self):
        reasons = set(__import__("re").findall(r'"([a-z_]+)",?\s', (
            metadata_amane.BRIDGE_SCRIPT).read_text(encoding="utf-8").split("FAILURE_REASONS = (", 1)[1]
            .split(")", 1)[0]))
        self.assertEqual(len(reasons), 16)
        self.assertEqual(reasons - set(metadata_amane.REASON_KINDS), set())
        self.assertEqual(set(metadata_amane.REASON_KINDS.values()), {"auth", "unavailable", "not_found"})


class RebuildTests(unittest.TestCase):
    def test_the_rebuild_command_syncs_the_lock_into_the_tools_root(self):
        command, env = metadata_amane.rebuild_command(Path("T:/tools"), uv=Path("uv.exe"))
        self.assertEqual(command[:4], ["uv.exe", "sync", "--locked", "--no-dev"])
        self.assertIn("--python", command)
        self.assertEqual(command[command.index("--project") + 1], str(metadata_amane.BRIDGE_ROOT))
        self.assertEqual(Path(env["UV_PROJECT_ENVIRONMENT"]), Path("T:/tools") / "amane-bridge" / ".venv")

    def test_rebuild_reports_uv_failures_and_success_with_the_pinned_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = Path(tmp)
            with patch.object(metadata_amane, "find_uv", return_value=Path("uv.exe")):
                failed = metadata_amane.rebuild(tools, runner=lambda *a, **k: completed("", 2, "boom"))
                self.assertFalse(failed["ok"])
                self.assertIn("boom", failed["error"])
                python = metadata_amane.bridge_python(tools)

                def build(*args, **kwargs):
                    python.parent.mkdir(parents=True, exist_ok=True)
                    python.write_text("", encoding="utf-8")
                    return completed("")

                done = metadata_amane.rebuild(tools, runner=build)
            self.assertTrue(done["ok"])
            self.assertTrue(done["installed"])
            self.assertIn(metadata_amane.pinned_revision()[:12], done["result"])
            with patch.object(metadata_amane, "find_uv", return_value=None):
                self.assertIn("uv", metadata_amane.rebuild(tools, runner=lambda *a, **k: completed(""))["error"])

    def test_describe_lists_the_facts_the_settings_card_shows(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = metadata_amane.describe(Path(tmp))
        self.assertEqual(set(facts), {"repository", "license", "revision", "version", "installed", "python", "sites"})
        self.assertFalse(facts["installed"])
        self.assertEqual([site["source"] for site in facts["sites"]], list(metadata_amane.SITES))

    def test_the_upstream_tag_is_never_guessed(self):
        class Client:
            def __init__(self, status, body):
                self.status, self.body = status, body

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get(self, url):
                import httpx
                return httpx.Response(self.status, json=self.body, request=httpx.Request("GET", url))

        with patch("httpx.Client", lambda **kw: Client(200, {"tag_name": "v0.17.0"})):
            self.assertEqual(metadata_amane.latest_upstream_tag({"trust_env": False}), "v0.17.0")
        with patch("httpx.Client", lambda **kw: Client(403, {"message": "rate limited"})):
            self.assertEqual(metadata_amane.latest_upstream_tag({"trust_env": False}), "未取得")

        def explode(**kw):
            raise OSError("no network")

        with patch("httpx.Client", explode):
            self.assertEqual(metadata_amane.latest_upstream_tag({"trust_env": False}), "未取得")


class ProxyArgumentTests(unittest.TestCase):
    def test_the_three_proxy_modes_map_onto_the_bridge_flag(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "http://env:1", "NO_PROXY": "x"}, clear=False):
            args, env = metadata_amane.proxy_argument({"trust_env": False, "proxy": "http://peach:2"})
            self.assertEqual(args, ["--proxy", "http://peach:2"])
            args, env = metadata_amane.proxy_argument({"trust_env": False})
            self.assertEqual(args, [])
            self.assertNotIn("HTTPS_PROXY", env)
            self.assertNotIn("NO_PROXY", env)
            args, env = metadata_amane.proxy_argument({"trust_env": True})
            self.assertEqual(args, ["--proxy", "http://env:1"])


class BridgeQueryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.tools = Path(self.temporary.name)
        self.python = metadata_amane.bridge_python(self.tools)
        self.python.parent.mkdir(parents=True)
        self.python.write_text("", encoding="utf-8")

    def test_create_refuses_when_the_venv_is_missing(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(MetadataProviderError) as caught:
                metadata_amane.AmaneBridge.create(Path(empty))
        self.assertIn("amane 桥未安装", str(caught.exception))

    def test_query_runs_the_pinned_interpreter_and_reads_the_last_json_line(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return completed("noise from a stray print\n" + report(fc2ppvdb=FOUND) + "\n")

        bridge = metadata_amane.AmaneBridge.create(self.tools, runner=runner)
        result = bridge.query("fc2-ppv-1234567", ["fc2ppvdb"], proxy_options={"trust_env": False, "proxy": "http://p:1"},
                              timeout=42)
        self.assertEqual(result["sites"]["fc2ppvdb"]["status"], "found")
        command, kwargs = calls[0]
        self.assertEqual(command[0], str(self.python))
        self.assertEqual(command[command.index("--number") + 1], "FC2-PPV-1234567")
        self.assertEqual(command[command.index("--sites") + 1], "fc2ppvdb")
        self.assertEqual(command[command.index("--proxy") + 1], "http://p:1")
        self.assertEqual(kwargs["timeout"], 42)
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["env"]["PYTHONIOENCODING"], "utf-8")

    def test_query_rejects_sites_peach_did_not_open(self):
        bridge = metadata_amane.AmaneBridge.create(self.tools, runner=lambda *a, **k: completed(""))
        with self.assertRaises(ValueError):
            bridge.query("ABW-220", ["javdb"])

    def test_timeouts_and_garbage_output_become_provider_errors(self):
        def slow(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        bridge = metadata_amane.AmaneBridge.create(self.tools, runner=slow)
        with self.assertRaises(MetadataProviderError) as caught:
            bridge.query("ABW-220", ["avsox"])
        self.assertEqual(caught.exception.kind, "unavailable")
        bridge = metadata_amane.AmaneBridge.create(self.tools, runner=lambda *a, **k: completed("Traceback…", 1))
        with self.assertRaises(MetadataProviderError) as caught:
            bridge.query("ABW-220", ["avsox"])
        self.assertIn("非 JSON", str(caught.exception))
        bridge = metadata_amane.AmaneBridge.create(
            self.tools, runner=lambda *a, **k: completed(json.dumps({"error": "amane 加载失败：X"}), 3))
        with self.assertRaises(MetadataProviderError) as caught:
            bridge.query("ABW-220", ["avsox"])
        self.assertIn("amane 加载失败", str(caught.exception))


class PayloadTests(unittest.TestCase):
    def test_amane_metadata_lands_in_the_javinizer_shaped_payload(self):
        payload = metadata_amane.to_payload("fc2ppvdb", "FC2-PPV-1234567", FOUND["metadata"])
        self.assertEqual(payload["source"], "fc2ppvdb")
        self.assertEqual(payload["content_id"], "FC2-PPV-1234567")
        self.assertEqual(payload["id"], "FC2-PPV-1234567")
        self.assertEqual(payload["maker"], "卖家")
        self.assertEqual(payload["label"], "レーベル")
        self.assertEqual(payload["actresses"], [{"japanese_name": "女優"}])
        self.assertEqual(payload["cover_url"], "https://x/t.jpg")
        self.assertEqual(payload["poster_url"], "https://x/p.jpg")
        self.assertEqual(payload["director"], "監督")
        self.assertEqual(payload["genres"], ["a", "b"])
        fields = extract_peach_fields(payload)
        self.assertEqual(fields["title"]["value"], "標題")
        self.assertEqual([row["name"] for row in fields["performers"]["value"]], ["女優"])
        self.assertEqual(fields["studio"]["value"], "卖家")
        self.assertEqual(fields["release_date"]["value"], "2024-01-02")

    def test_split_report_keeps_hits_that_identify_the_code_and_files_the_rest(self):
        wrong = {"status": "found", "metadata": {**FOUND["metadata"], "number": "FC2-PPV-7654321", "source_url": "https://fc2club.top/html/FC2-PPV-7654321.html"}}
        found, failures = metadata_amane.split_report("FC2-PPV-1234567", json.loads(report(
            fc2ppvdb=FOUND, fc2club=wrong,
            avsox={"status": "failed", "reason": "rate_limited", "http_status": 429},
            airav={"status": "not_found", "reason": "not_found"})))
        self.assertEqual([site for site, _ in found], ["fc2ppvdb"])
        self.assertEqual(set(failures), {"fc2club", "avsox", "airav"})
        self.assertEqual(failures["fc2club"].kind, "not_found")
        self.assertEqual(failures["avsox"].kind, "unavailable")
        self.assertEqual(failures["avsox"].detail, "rate_limited")
        self.assertEqual(failures["avsox"].status_code, 429)
        self.assertEqual(failures["airav"].kind, "not_found")


class FailureMappingTests(unittest.TestCase):
    def test_reasons_map_onto_the_three_existing_kinds_and_keep_the_detail(self):
        for reason, kind in metadata_amane.REASON_KINDS.items():
            with self.subTest(reason=reason):
                error = metadata_amane.failure_error("avsox", {"reason": reason, "http_status": 0})
                self.assertEqual(error.kind, kind)
                self.assertEqual(error.detail, reason)
                self.assertIn("AVSOX", str(error))
        auth = metadata_amane.failure_error("airav", {"reason": "cloudflare_blocked", "http_status": 403})
        self.assertFalse(auth.retryable)
        self.assertTrue(auth.temporary)
        parse = metadata_amane.failure_error("airav", {"reason": "parse_error", "detail": "selector missing"})
        self.assertFalse(parse.retryable)
        self.assertIn("selector missing", str(parse))
        timeout = metadata_amane.failure_error("airav", {"reason": "timeout", "detail": "curl 28"})
        self.assertTrue(timeout.retryable)
        self.assertNotIn("curl 28", str(timeout))

    def test_only_blocks_and_rate_limits_pause_the_whole_site(self):
        self.assertEqual(metadata_amane.cooldown_action(
            metadata_amane.failure_error("avsox", {"reason": "ip_banned"})), "blocked")
        self.assertEqual(metadata_amane.cooldown_action(
            metadata_amane.failure_error("avsox", {"reason": "rate_limited"})), "rate_limited")
        for reason in ("not_found", "timeout", "server_error", "parse_error", "age_verification"):
            self.assertEqual(metadata_amane.cooldown_action(
                metadata_amane.failure_error("avsox", {"reason": reason})), "")
        self.assertEqual(metadata_amane.cooldown_action(MetadataProviderError("plain")), "")


class CooldownHelperTests(unittest.TestCase):
    def test_pause_source_uses_the_existing_two_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(paused_until(root, "avsox"), 0.0)
            first = pause_source(root, "avsox", refused=True)
            self.assertAlmostEqual(first - time.time(), 900, delta=5)
            second = pause_source(root, "avsox", refused=True)
            self.assertAlmostEqual(second - time.time(), 1800, delta=5)
            self.assertEqual(cooldown_state(root, "avsox")[1], 2)
            self.assertGreater(paused_until(root, "avsox"), time.time())
            limited = pause_source(root, "airav", retry_after=30)
            self.assertAlmostEqual(limited - time.time(), 30, delta=5)
            self.assertEqual(cooldown_state(root, "airav")[1], 0)


class ProviderStageTests(unittest.TestCase):
    """`LibraryMetadataProvider.amane()`：跳过冷却中的站、按桥的报告分三种结局、把封禁写回冷却。"""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.secrets, self.tools = root / "secrets", root / "tools"
        self.secrets.mkdir()
        python = metadata_amane.bridge_python(self.tools)
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")
        self.calls = []

    def provider(self, stdout, returncode=0):
        def runner(command, **kwargs):
            self.calls.append(command)
            return completed(stdout, returncode)

        provider = LibraryMetadataProvider(self.secrets, tools_root=self.tools)
        self.addCleanup(provider.transport.close)
        patcher = patch.object(metadata_amane.AmaneBridge, "create",
                               classmethod(lambda cls, tools_root, **kw: metadata_amane.AmaneBridge(
                                   metadata_amane.bridge_python(tools_root), runner=runner)))
        patcher.start()
        self.addCleanup(patcher.stop)
        return provider

    def test_a_hit_comes_back_as_source_payload_pairs_and_is_cached(self):
        provider = self.provider(report(fc2ppvdb=FOUND, fc2club={"status": "not_found", "reason": "not_found"}))
        found = provider.amane("FC2-PPV-1234567", route=("fc2ppvdb", "fc2club"))
        self.assertEqual([site for site, _ in found], ["fc2ppvdb"])
        self.assertEqual(found[0][1]["title"], "標題")
        provider.amane("FC2-PPV-1234567", route=("fc2ppvdb", "fc2club"))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][self.calls[0].index("--sites") + 1], "fc2ppvdb,fc2club")

    def test_all_misses_are_not_found_and_errors_are_unavailable_with_the_reason(self):
        provider = self.provider(report(fc2ppvdb={"status": "not_found", "reason": "not_found"},
                                        fc2club={"status": "not_found", "reason": "not_found"}))
        with self.assertRaises(NotFound):
            provider.amane("FC2-PPV-1234567", route=("fc2ppvdb", "fc2club"))
        provider = self.provider(report(fc2ppvdb={"status": "failed", "reason": "server_error", "http_status": 526},
                                        fc2club={"status": "not_found", "reason": "not_found"}))
        with self.assertRaises(Unavailable) as caught:
            provider.amane("FC2-PPV-7654321", route=("fc2ppvdb", "fc2club"))
        self.assertIn("FC2PPVDB", str(caught.exception))
        self.assertIn("526", str(caught.exception))

    def test_a_block_pauses_that_site_and_a_fully_paused_stage_is_reported_as_paused(self):
        provider = self.provider(report(avsox={"status": "failed", "reason": "cloudflare_blocked", "http_status": 403}))
        with self.assertRaises(SourcePaused):
            provider.amane("HEYZO-1380", route=("avsox",))
        self.assertGreater(paused_until(self.secrets, "avsox"), time.time())
        # 站已在冷却：下一部片连子进程都不起。
        self.calls.clear()
        provider = self.provider(report(avsox=FOUND))
        with self.assertRaises(SourcePaused):
            provider.amane("HEYZO-1381", route=("avsox",))
        self.assertEqual(self.calls, [])

    def test_a_missing_venv_is_an_unavailable_stage_not_a_crash(self):
        with tempfile.TemporaryDirectory() as empty:
            provider = LibraryMetadataProvider(self.secrets, tools_root=Path(empty))
            self.addCleanup(provider.transport.close)
            with self.assertRaises(Unavailable) as caught:
                provider.amane("HEYZO-1380", route=("avsox",))
        self.assertIn("amane 桥未安装", str(caught.exception))

    def test_a_route_without_bridge_sites_is_not_found_without_a_subprocess(self):
        provider = self.provider(report())
        with self.assertRaises(NotFound):
            provider.amane("ABW-220", route=("javdb",))
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
