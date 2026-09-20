import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CloudflaredPackagingTests(unittest.TestCase):
    def test_the_pinned_windows_asset_has_a_sha256_and_official_source(self):
        manifest = json.loads((ROOT / "scripts" / "cloudflared-windows.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["asset"], "cloudflared-windows-amd64.exe")
        self.assertRegex(manifest["sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(manifest["url"].startswith("https://github.com/cloudflare/cloudflared/"))
        self.assertEqual(manifest["license"], "Apache-2.0")

    def test_fetch_and_build_verify_the_pinned_hash_and_only_standalone_carries_the_sidecar(self):
        fetch = (ROOT / "scripts" / "fetch_cloudflared.ps1").read_text(encoding="utf-8-sig")
        build = (ROOT / "scripts" / "build_windows.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("Get-FileHash", fetch)
        self.assertIn("Get-FileHash", build)
        self.assertIn("Copy-Item -LiteralPath $CloudflaredSource", build)
        self.assertIn("if ($Standalone)", build)
        self.assertLess(build.index("if ($Standalone) {\n    $BuildMode"), build.index("Copy-Item -LiteralPath $CloudflaredSource"))


if __name__ == "__main__":
    unittest.main()
