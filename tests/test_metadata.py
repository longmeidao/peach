import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from peach.metadata import (
    JavinizerGoProvider,
    MetadataProviderError,
    collapse_repeated_phrase,
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
            ],
            "maker": "Studio Studio", "series": "Series A", "genres": ["Anal"],
        }, {"Anal": "肛交"})
        self.assertEqual(fields["performers"]["value"], [
            {"name": "木村さん", "external_id": "7", "thumb_url": ""},
        ])
        self.assertEqual(fields["studio"]["value"], "Studio")
        self.assertEqual(fields["tags"]["value"], ["肛交"])


if __name__ == "__main__":
    unittest.main()
