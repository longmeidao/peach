import importlib.util
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "import_stash_entities", ROOT / "scripts" / "import_stash_entities.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StashEntityImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        self.connection = sqlite3.connect(self.db)
        self.connection.executescript("""
          CREATE TABLE entity(id INTEGER PRIMARY KEY,kind TEXT,canonical_name TEXT,
            metadata_json TEXT DEFAULT '{}',updated_at TEXT);
          CREATE TABLE entity_alias(entity_id INTEGER,alias TEXT,normalized_alias TEXT,
            source TEXT,confidence REAL,PRIMARY KEY(entity_id,normalized_alias,source));
          CREATE TABLE entity_external_ref(entity_id INTEGER,provider TEXT,external_kind TEXT,
            external_id TEXT,metadata_json TEXT,last_synced_at TEXT,
            PRIMARY KEY(provider,external_kind,external_id),UNIQUE(entity_id,provider,external_kind));
          CREATE TABLE entity_search_term(entity_id INTEGER,term TEXT,purpose TEXT,source TEXT,
            created_at TEXT,PRIMARY KEY(entity_id,term,purpose));
          CREATE TABLE entity_link(id INTEGER PRIMARY KEY,entity_id INTEGER,link_kind TEXT,label TEXT,
            url TEXT,hostname TEXT,is_sensitive INTEGER,metadata_json TEXT,created_at TEXT,updated_at TEXT,
            UNIQUE(entity_id,url));
          INSERT INTO entity(id,kind,canonical_name,metadata_json) VALUES(1,'performer','Alice','{}');
        """)

    def tearDown(self):
        self.connection.close()
        self.tmp.cleanup()

    def test_imports_identity_data_and_rejects_default_portrait(self):
        rows = MODULE.collect(self.connection, [{
            "id": "42", "name": "Alice", "alias_list": ["@alice", "Alice A", "X:@alice"],
            "urls": [], "details": "Performer summary",
            "birthdate": "2000-01-01", "country": "JP", "height_cm": 165,
            "measurements": "B80 W55 H82",
            "image_path": "http://127.0.0.1/performer/42/image?default=true",
        }])
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["has_real_image"])
        counts = MODULE.apply(self.connection, rows)
        self.assertEqual(counts["external_refs"], 1)
        self.assertEqual(counts["aliases"], 3)
        self.assertEqual(counts["links"], 1)
        self.assertEqual(self.connection.execute(
            "SELECT link_kind FROM entity_link"
        ).fetchone()[0], "social")
        metadata = self.connection.execute(
            "SELECT metadata_json FROM entity WHERE id=1"
        ).fetchone()[0]
        self.assertIn("Performer summary", metadata)

    def test_social_host_match_lands_on_dot_boundary(self):
        """后缀匹配必须落在点边界上。

        `"notx.com".endswith("x.com")` 为真，旧写法会把任何以平台名结尾的域名判成 social，
        写进 entity_link 后在资料页上显示成官方社交账号。
        """
        for url in ("https://x.com/alice", "https://mobile.twitter.com/alice",
                    "https://www.instagram.com/alice"):
            self.assertEqual(MODULE.link_kind(url), "social", url)
        for url in ("https://notx.com/alice", "https://faketwitter.com/alice",
                    "https://example.com/alice"):
            self.assertEqual(MODULE.link_kind(url), "catalog", url)

    def test_reads_png_and_jpeg_dimensions(self):
        png_buffer = io.BytesIO()
        jpeg_buffer = io.BytesIO()
        Image.new("RGB", (600, 800)).save(png_buffer, format="PNG")
        Image.new("RGB", (500, 700)).save(jpeg_buffer, format="JPEG")
        self.assertEqual(MODULE.image_size(png_buffer.getvalue()), (600, 800))
        self.assertEqual(MODULE.image_size(jpeg_buffer.getvalue()), (500, 700))
        self.assertIsNone(MODULE.image_size(b"\x89PNG\r\n\x1a\n" + b"broken"))


if __name__ == "__main__":
    unittest.main()
