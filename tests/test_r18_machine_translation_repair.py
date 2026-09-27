"""早期 r18.dev 英文机翻修复只改同源、未被用户接管的字段。"""
import argparse
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.migrations import upgrade
from scripts.repair_r18_machine_translations import apply_rows, collect, run


ROOT = Path(__file__).resolve().parents[1]


class R18MachineTranslationRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.db = root / "ledger.db"
        self.snapshots = root / "snapshots"
        self.snapshots.mkdir()
        upgrade(self.db, ROOT / "migrations")
        self.con = sqlite3.connect(self.db)
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def add_asset(self, asset_id: int, code: str, title: str, series: str, owners: dict[str, str]):
        self.con.execute(
            "INSERT INTO asset(id,location,path,name,medium,code,catalog_title,series,field_owners) "
            "VALUES(?,'local',?,?,'video',?,?,?,?)",
            (asset_id, f"{asset_id}.mp4", f"{asset_id}.mp4", code, title, series,
             json.dumps(owners)),
        )
        self.con.commit()

    def snapshot(self, code: str, *, title_machine=True, series_machine=True):
        path = self.snapshots / f"{code}-r18dev.json"
        path.write_text(json.dumps({
            "id": code,
            "combined": {
                "dvd_id": code,
                "title_en": "Machine title", "title_en_is_machine_translation": title_machine,
                "title_ja": "日本語タイトル",
                "series_name_en": "Machine series",
                "series_name_en_is_machine_translation": series_machine,
                "series_name_ja": "日本語シリーズ",
            },
            "translations": [{"language": "ja", "title": "日本語タイトル", "series": "日本語シリーズ"}],
        }, ensure_ascii=False), encoding="utf-8")

    def test_collect_and_apply_replaces_both_verified_fields(self):
        self.add_asset(1, "ABC-001", "Machine title", "Machine series", {
            "catalog_title": "auto:r18dev", "series": "auto:r18dev",
        })
        self.snapshot("ABC-001")
        rows = collect(self.con, self.snapshots)
        self.assertEqual([row["action"] for row in rows], ["replace", "replace"])
        self.assertEqual(apply_rows(self.con, rows), {"assets": 1, "fields": 2})
        self.con.commit()
        asset = self.con.execute(
            "SELECT catalog_title,series,field_owners,mutation_revision FROM asset WHERE id=1").fetchone()
        self.assertEqual((asset["catalog_title"], asset["series"]),
                         ("日本語タイトル", "日本語シリーズ"))
        self.assertEqual(json.loads(asset["field_owners"]), {
            "catalog_title": "auto:r18dev", "series": "auto:r18dev",
        })
        self.assertEqual(asset["mutation_revision"], 1)

    def test_changed_or_protected_values_are_not_candidates(self):
        self.add_asset(2, "ABC-002", "User title", "Changed series", {
            "catalog_title": "user:manual", "series": "auto:r18dev",
        })
        self.snapshot("ABC-002")
        rows = collect(self.con, self.snapshots)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["field"], "series")
        self.assertEqual(rows[0]["action"], "skip")
        self.assertEqual(rows[0]["reason"], "current-no-longer-matches-snapshot-english")

    def test_bilingual_snapshot_is_enough_when_r18_did_not_mark_the_english_as_machine_translation(self):
        self.add_asset(3, "ABC-003", "Machine title", "Machine series", {
            "catalog_title": "auto:r18dev", "series": "auto:r18dev",
        })
        self.snapshot("ABC-003", title_machine=False, series_machine=False)
        rows = collect(self.con, self.snapshots)
        self.assertEqual({row["action"] for row in rows}, {"replace"})
        self.assertEqual({row["machine_translation"] for row in rows}, {"no"})

    def test_a_latin_only_spacing_variant_is_not_mistaken_for_japanese(self):
        self.add_asset(5, "ABC-005", "Machine title", "1 VS 1", {
            "catalog_title": "auto:r18dev", "series": "auto:r18dev",
        })
        self.snapshot("ABC-005")
        payload = json.loads((self.snapshots / "ABC-005-r18dev.json").read_text(encoding="utf-8"))
        payload["combined"]["series_name_en"] = "1 VS 1"
        payload["combined"]["series_name_ja"] = "1VS1"
        (self.snapshots / "ABC-005-r18dev.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        rows = collect(self.con, self.snapshots)
        series = next(row for row in rows if row["field"] == "series")
        self.assertEqual(series["action"], "skip")
        self.assertEqual(series["reason"], "target-has-no-japanese-script")

    def test_dry_run_writes_audit_but_not_ledger_and_apply_requires_backup(self):
        self.add_asset(4, "ABC-004", "Machine title", "Machine series", {
            "catalog_title": "auto:r18dev", "series": "auto:r18dev",
        })
        self.snapshot("ABC-004")
        audit = Path(self.tmp.name) / "audit.csv"
        args = argparse.Namespace(
            db=self.db, apply=False, backup=None, snapshots=self.snapshots, audit_csv=audit,
        )
        self.assertEqual(run(args), 0)
        self.assertTrue(audit.is_file())
        self.assertEqual(self.con.execute(
            "SELECT catalog_title FROM asset WHERE id=4").fetchone()[0], "Machine title")
        args.apply = True
        with self.assertRaisesRegex(SystemExit, "--backup"):
            run(args)


if __name__ == "__main__":
    unittest.main()
