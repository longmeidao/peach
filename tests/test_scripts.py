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

    def test_import_has_no_filesystem_or_log_side_effect(self):
        self.assertIsNone(self.clean_names._logf)
        self.assertIsNone(self.scrape_codes._logf)

    def test_filename_cleanup_is_conservative(self):
        propose = self.clean_names.propose
        self.assertEqual(propose("www.98T.la@sample.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.jpg"), "sample.mp4.jpg")
        self.assertEqual(propose("(3).mp4"), "(3).mp4")

    def test_code_normalization(self):
        normalise = self.scrape_codes.normalise
        self.assertEqual(normalise("fc2ppv-1234567"), "FC2-PPV-1234567")
        self.assertEqual(normalise("abw123"), "ABW-123")
        self.assertEqual(normalise("ipvr00296"), "IPVR-296")

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
