import csv
import importlib.util
import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from peach.migrations import upgrade


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OperationalScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean_names = load_script("clean_names")
        cls.scrape_codes = load_script("scrape_codes")
        cls.find_ads = load_script("find_ads")
        cls.probe = load_script("probe")
        cls.sheets = load_script("sheets")
        cls.traffic_watch = load_script("traffic_watch")
        cls.creator_boards = load_script("creator_boards")

    def test_import_has_no_filesystem_or_log_side_effect(self):
        self.assertIsNone(self.clean_names._logf)
        self.assertIsNone(self.scrape_codes._logf)

    def test_ad_candidate_scan_is_isolated_and_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER,location TEXT,path TEXT,name TEXT,"
                "size INTEGER,duration REAL,medium TEXT)"
            )
            for asset_id in range(1, 4):
                connection.execute(
                    "INSERT INTO asset VALUES(?,?,?,?,?,?,?)",
                    (
                        asset_id,
                        "local",
                        str(root / "pack" / f"promo-{asset_id}.mp4"),
                        f"promo-{asset_id}.mp4",
                        10 * 1024**2,
                        37.4,
                        "video",
                    ),
                )
            connection.commit()
            connection.close()

            plan, scanned = self.find_ads.find_candidates(db, min_group=3)
            self.assertEqual(scanned, 3)
            self.assertEqual(len(plan), 3)
            self.assertTrue(all("等长重复x3" in row["hits"] for row in plan))
            self.assertFalse((root / "ad-candidates.csv").exists())

    def test_filename_cleanup_is_conservative(self):
        propose = self.clean_names.propose
        self.assertEqual(propose("www.98T.la@sample.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.jpg"), "sample.mp4.jpg")
        self.assertEqual(propose("(3).mp4"), "(3).mp4")

    def test_media_batch_scripts_are_import_safe_and_keep_context_rules(self):
        self.assertEqual(self.probe.context_fields(1920, 1080, 180), ("速食", "横屏", "2K"))
        with tempfile.TemporaryDirectory() as tmp:
            output = self.sheets.output_path(Path(tmp), "local", "R:/media/one.mp4")
            self.assertFalse(output.exists())
            self.assertTrue(output.parent.is_dir())
        self.assertTrue(self.traffic_watch.is_direct({"chains": ["DIRECT"]}))
        self.assertFalse(self.traffic_watch.is_direct({"chains": ["Proxy", "Relay"]}))
        self.assertEqual(self.creator_boards.safe_name("A/B:C"), "A_B_C")

    def test_code_normalization(self):
        normalise = self.scrape_codes.normalise
        self.assertEqual(normalise("fc2ppv-1234567"), "FC2-PPV-1234567")
        self.assertEqual(normalise("abw123"), "ABW-123")
        self.assertEqual(normalise("ipvr00296"), "IPVR-296")

    def test_scrape_html_adapters_use_structured_parsing(self):
        avsox_search = '<a href="/cn/movie/abc123">result</a>'
        self.assertEqual(
            self.scrape_codes.avsox_movie_url(avsox_search),
            "https://avsox.click/cn/movie/abc123",
        )
        avsox = self.scrape_codes.parse_avsox("""
          <h3>Example <b>Title</b></h3>
          <p><span>制作商:</span><a href="/studio/a">Studio A</a></p>
          <a class="avatar-box"><span>Alice</span></a>
          <a class="avatar-box"><span>Bob</span></a>
        """)
        self.assertEqual(avsox["performers"], "Alice|Bob")
        self.assertEqual(avsox["studio"], "Studio A")
        self.assertEqual(avsox["title"], "Example Title")

        javbus = self.scrape_codes.parse_javbus("""
          <h3>Bus <em>Title</em></h3>
          <p><span>製作商:</span><a href="/studio/p">Prestige</a></p>
          <p><span>發行商:</span><a href="/label/l">Label A</a></p>
          <p><span>系列:</span><a href="/series/s">Series A</a></p>
          <a href="/star/alice"><span class="star-name">Alice</span></a>
        """)
        self.assertEqual(javbus["performers"], "Alice")
        self.assertEqual(javbus["studio"], "Prestige")
        self.assertEqual(javbus["label"], "Label A")
        self.assertEqual(javbus["series"], "Series A")

    def test_scrape_writeback_dual_writes_projection_and_entities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close()
            upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,code) "
                "VALUES(1,'local','one.mp4','one.mp4','video','ABC-001')"
            )
            connection.commit()
            connection.close()

            output = root / "review.csv"
            row = {
                "code": "ABC-001", "query": "ABC-001", "performers": "Alice|Bob",
                "studio": "Studio A", "label": "", "series": "Series A", "title": "",
                "categories": "Foot Fetish|Anal", "source": "r18", "status": "ok",
                "size_gb": "1", "videos": "1",
            }
            with output.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.scrape_codes.FIELDS)
                writer.writeheader()
                writer.writerow(row)

            with redirect_stdout(io.StringIO()):
                self.scrape_codes.write_back(str(db), str(output))

            connection = sqlite3.connect(db)
            asset = connection.execute(
                "SELECT creator,studio,series FROM asset WHERE id=1"
            ).fetchone()
            tags = {row[0] for row in connection.execute(
                "SELECT tag FROM asset_tag WHERE asset_id=1"
            )}
            relations = set(connection.execute(
                "SELECT e.kind,e.canonical_name,ae.role,ae.source "
                "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=1"
            ))
            connection.close()

            self.assertEqual(asset, ("Alice", "Studio A", "Series A"))
            self.assertEqual(tags, {"演员:Alice", "演员:Bob", "足系", "肛交"})
            self.assertTrue({
                ("studio", "Studio A", "studio", "r18:studio"),
                ("series", "Series A", "series", "r18:series"),
                ("performer", "Alice", "performer", "r18:performer"),
                ("performer", "Bob", "performer", "r18:performer"),
                ("tag", "足系", "tag", "r18"),
                ("tag", "肛交", "tag", "r18"),
            } <= relations)


if __name__ == "__main__":
    unittest.main()
