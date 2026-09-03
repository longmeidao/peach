import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    path = ROOT / "scripts" / "check_reference_updates.py"
    spec = importlib.util.spec_from_file_location("check_reference_updates", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReferenceUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_checker()

    def test_registered_snapshots_match_their_locks(self):
        registry = self.checker.load_registry(ROOT / "docs" / "reference-sources.json")
        self.assertEqual(self.checker.validate_registry(ROOT, registry), [])
        sources = {source["id"]: source for source in registry["sources"]}
        self.assertEqual(
            set(sources),
            {"vercel-report-design", "vercel-web-interface-guidelines",
             "fiu758-studio-logo-discovery", "rule34-follow-tags-and-collections",
             "f95-masked-gofile-media", "follow-fanbox-gofile-paheal",
             "fanbox-browser-transport", "beeg-profile-layout",
             "vercel-geist-table-ranking",
             "vercel-geist-fieldset-scroller-empty-state",
             "vercel-geist-command-search-loading",
             "vercel-notifications-note",
             "youtube-player-controls-user-screenshot",
             "openaver-related-ranking",
             "vercel-geist-tabs-secondary",
             "vercel-geist-switch-segmented",
             "youtube-stats-buffer-20260829"},
        )
        self.assertNotEqual(
            sources["vercel-report-design"]["url"],
            sources["vercel-web-interface-guidelines"]["url"],
        )

    def test_every_snapshot_file_is_registered_or_says_why_it_is_not(self):
        """快照目录里不许有身份不明的文件。

        登记表的契约是「快照文件 + 可重抓 URL」。React 渲染的规格页、用户截图和「哪个主机
        还能取到图」这类实测给不出可哈希的上游快照，本来就不该登记。但目录里「不该登记」和
        「忘了登记」长得一模一样，所以未登记的必须在正文里自己说明理由。
        """
        registry = self.checker.load_registry(ROOT / "docs" / "reference-sources.json")
        registered = {source["snapshot"] for source in registry["sources"]}
        undeclared = []
        for path in sorted((ROOT / "docs" / "reference-snapshots").glob("*.md")):
            rel = path.relative_to(ROOT).as_posix()
            if rel in registered:
                continue
            if "reference-sources.json" not in path.read_text(encoding="utf-8"):
                undeclared.append(rel)
        self.assertEqual(
            undeclared, [],
            "这些快照既没登记进 docs/reference-sources.json，也没写明为什么不登记",
        )

    def test_changed_markdown_is_reported_without_mutating_the_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot.md"
            snapshot.write_text("old\n", encoding="utf-8")
            source = {
                "id": "example",
                "url": "https://example.invalid/reference.md",
                "snapshot": "snapshot.md",
                "sha256": self.checker.sha256_bytes(b"old\n"),
            }
            result = self.checker.inspect_source(
                root,
                source,
                fetcher=lambda _url: b"new\n",
                revision_resolver=lambda _source: None,
            )
            self.assertTrue(result["changed"])
            self.assertIn("-old", result["diff"])
            self.assertIn("+new", result["diff"])
            self.assertEqual(snapshot.read_text(encoding="utf-8"), "old\n")

    def test_registry_rejects_a_snapshot_changed_without_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "snapshot.md").write_text("changed\n", encoding="utf-8")
            registry = {
                "sources": [
                    {
                        "id": "example",
                        "snapshot": "snapshot.md",
                        "sha256": self.checker.sha256_bytes(b"locked\n"),
                    }
                ]
            }
            problems = self.checker.validate_registry(root, registry)
            self.assertTrue(any("快照校验失败" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
