import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from peach.metadata import (
    identifies_code,
    CATALOG_EVIDENCE_FIELDS,
    JavinizerGoProvider,
    MetadataProviderError,
    collapse_repeated_phrase,
    extract_catalog_evidence,
    extract_peach_fields,
    validate_provider_code,
)


class MetadataProviderTests(unittest.TestCase):
    def test_create_requires_the_pinned_binary_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "javinizer"
            binary.touch()
            def runner(command, **kwargs):
                return subprocess.CompletedProcess(command, 0, "v9.9.9\n", "")
            with self.assertRaises(MetadataProviderError) as caught:
                JavinizerGoProvider.create(binary, Path(tmp) / "config.yaml", runner=runner)
        self.assertIn("版本不匹配", str(caught.exception))

    def test_provider_sends_only_normalized_code_and_one_source(self):
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, json.dumps({
                "source": "r18dev", "id": "IPX-535", "actresses": [],
            }), "diagnostic")
        with tempfile.TemporaryDirectory() as tmp:
            provider = JavinizerGoProvider(
                Path("/bin/javinizer"), Path(tmp) / "config.yaml", runner=runner,
            )
            result = provider.query("IPX-535", "r18dev")
        self.assertEqual(result["id"], "IPX-535")
        command, options = calls[0]
        self.assertEqual(command[-5:], ["IPX-535", "--output", "json", "--scrapers", "r18dev"])
        self.assertFalse(options["shell"])
        self.assertEqual(options["encoding"], "utf-8")
        self.assertEqual(options["errors"], "strict")

    def test_provider_rejects_paths_and_urls_before_subprocess(self):
        for unsafe in ("/media/IPX-535.mp4", r"R:\media\IPX-535.mp4", "https://x/IPX-535"):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                validate_provider_code(unsafe)

    def test_structured_error_is_preserved(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, json.dumps({"error": {
                "kind": "rate_limited", "message": "slow down", "status_code": 429,
                "retryable": True, "temporary": True,
            }}), "")
        with tempfile.TemporaryDirectory() as tmp:
            provider = JavinizerGoProvider(
                Path("/bin/javinizer"), Path(tmp) / "config.yaml", runner=runner,
            )
            with self.assertRaises(MetadataProviderError) as caught:
                provider.query("IPX-535", "r18dev")
        self.assertEqual(caught.exception.status_code, 429)
        self.assertTrue(caught.exception.retryable)

    def test_repeated_performer_is_collapsed_before_candidate_creation(self):
        self.assertEqual(collapse_repeated_phrase("木村さん 木村さん"), ("木村さん", True))
        fields = extract_peach_fields({
            "actresses": [
                {"dmm_id": 7, "japanese_name": "木村さん 木村さん"},
                {"dmm_id": 7, "japanese_name": "木村さん"},
                {"dmm_id": 8, "japanese_name": "画像を拡大する 画像を拡大する"},
            ],
            "maker": "Studio Studio", "series": "Series A",
            "release_date": "2020-09-13T00:00:00Z", "genres": ["Anal"],
        })
        self.assertEqual(fields["performers"]["value"], [
            {"name": "木村さん", "external_id": "7", "thumb_url": ""},
        ])
        self.assertEqual(fields["studio"]["value"], "Studio")
        self.assertEqual(fields["release_date"]["value"], "2020-09-13")
        self.assertIn("已规范化", fields["release_date"]["warnings"][0])
        self.assertEqual(fields["tags"]["value"], ["肛交"])

    def test_series_and_studio_take_the_japanese_original(self):
        payload = {
            "maker": "Prestige",
            "series": "Prestige 20th Anniversary Special Event",
            "translations": [
                {"language": "en", "maker": "Prestige", "series": "Prestige 20th Anniversary Special Event"},
                {"language": "ja", "maker": "プレステージ", "series": "【プレステージ20周年特別企画】"},
            ],
        }
        fields = extract_peach_fields(payload)
        self.assertEqual(fields["series"]["value"], "【プレステージ20周年特別企画】")
        self.assertEqual(fields["studio"]["value"], "プレステージ")

    def test_catalog_titles_become_reviewable_truth_candidates(self):
        fields = extract_peach_fields({
            "title": "日本語タイトル", "original_title": "Original Title",
        })
        self.assertEqual(fields["title"]["value"], "日本語タイトル")
        self.assertEqual(fields["original_title"]["value"], "Original Title")

    def test_empty_japanese_names_fall_back_to_the_default_view(self):
        fields = extract_peach_fields({
            "maker": "FALENO",
            "series": "FALENO Compilation",
            "translations": [{"language": "ja", "maker": "", "series": ""}],
        })
        self.assertEqual(fields["series"]["value"], "FALENO Compilation")
        self.assertEqual(fields["studio"]["value"], "FALENO")

    def test_rich_catalog_fields_stay_source_evidence(self):
        evidence = extract_catalog_evidence({
            "title": "English title", "original_title": "原标题", "runtime": "121",
            "director": "Director A", "label": "Label A",
            "poster_url": "https://img.example/poster.jpg",
            "cover_url": "https://img.example/cover.jpg",
            "screenshot_urls": [
                "https://img.example/1.jpg", "https://img.example/1.jpg",
                "file:///private/2.jpg", "https://img.example/2.jpg",
            ],
            "trailer_url": "https://video.example/trailer.m3u8",
            "translations": [{
                "language": "ja", "title": "日本語タイトル", "label": "日本レーベル",
            }],
        })
        self.assertEqual(set(evidence), set(CATALOG_EVIDENCE_FIELDS))
        self.assertEqual(evidence["title"]["value"], "日本語タイトル")
        self.assertEqual(evidence["original_title"]["value"], "原标题")
        self.assertEqual(evidence["runtime"]["value"], 121)
        self.assertEqual(evidence["label"]["value"], "日本レーベル")
        self.assertEqual(evidence["screenshot_urls"]["value"], [
            "https://img.example/1.jpg", "https://img.example/2.jpg",
        ])
        self.assertIn("2 张截图", evidence["screenshot_urls"]["display_value"])

    def test_catalog_evidence_rejects_credentialed_and_non_http_urls(self):
        evidence = extract_catalog_evidence({
            "title": "Same", "original_title": "Same", "runtime": 0,
            "poster_url": "https://user:secret@example.test/poster.jpg",
            "cover_url": "R:/covers/ABC-001.jpg",
            "trailer_url": "javascript:alert(1)",
        })
        self.assertEqual(evidence, {"title": {
            "value": "Same", "display_value": "Same", "warnings": [],
        }})

class SourceIdentityTests(unittest.TestCase):
    def test_real_source_id_shapes_are_accepted(self):
        # DMM 带厂牌数字前缀，r18dev 对 IQQQ-026 会补零，259 系只在 URL 里出现番号。
        self.assertTrue(identifies_code("ABW-220", {"content_id": "118abw220"}))
        self.assertTrue(identifies_code("IQQQ-026", {"content_id": "h_086iqqq00026"}))
        self.assertTrue(identifies_code("MESU-088", {"id": "MESU-88"}))
        self.assertTrue(identifies_code("259LUXU-1475", {
            "source_url": "https://www.mgstage.com/product/product_detail/259LUXU-1475/",
        }))

    def test_unrelated_product_is_rejected_as_not_found(self):
        # dl.getchu 对 ABW-220 与 259LUXU-1475 都返回同一件同人商品 item33938。
        payload = {"id": "33938", "content_id": "33938",
                   "source_url": "https://dl.getchu.com/i/item33938"}
        self.assertFalse(identifies_code("ABW-220", payload))
        self.assertFalse(identifies_code("259LUXU-1475", payload))
        self.assertFalse(identifies_code("ABW-220", {}))
        # 番号相邻不等于同一部：ABW-2200 不能拿 ABW-220 的结果顶替。
        self.assertFalse(identifies_code("ABW-2200", {"content_id": "118abw220"}))

    def test_provider_turns_a_mismatched_product_into_not_found(self):
        def runner(command, **kwargs):
            if "version" in command:
                return subprocess.CompletedProcess(command, 0, f"v{JAVINIZER_GO_VERSION}", "")
            return subprocess.CompletedProcess(command, 0, json.dumps({
                "source": "dlgetchu", "id": "33938", "content_id": "33938",
                "source_url": "https://dl.getchu.com/i/item33938",
                "genres": ["コスプレ一般"],
            }), "")
        with tempfile.TemporaryDirectory() as tmp:
            provider = JavinizerGoProvider(
                Path("/bin/javinizer"), Path(tmp) / "config.yaml", runner=runner,
            )
            with self.assertRaises(MetadataProviderError) as caught:
                provider.query("ABW-220", "dlgetchu")
        self.assertEqual(caught.exception.kind, "not_found")


if __name__ == "__main__":
    unittest.main()
