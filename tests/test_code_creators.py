import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_code_creators.py"
_spec = importlib.util.spec_from_file_location("audit_code_creators", SCRIPT)
audit = importlib.util.module_from_spec(_spec)
sys.modules["audit_code_creators"] = audit
_spec.loader.exec_module(audit)


SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY, location TEXT NOT NULL, path TEXT NOT NULL, name TEXT,
  medium TEXT, creator TEXT, code TEXT, UNIQUE(location,path));
CREATE TABLE entity(
  id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT, normalized_name TEXT,
  metadata_json TEXT DEFAULT '{}', created_at TEXT, updated_at TEXT,
  UNIQUE(kind,normalized_name));
CREATE TABLE asset_entity(
  asset_id INTEGER, entity_id INTEGER, role TEXT, source TEXT, confidence REAL DEFAULT 1.0,
  metadata_json TEXT DEFAULT '{}', first_seen_at TEXT, last_seen_at TEXT,
  UNIQUE(asset_id,entity_id,role,source));
"""


class CodeShapeTests(unittest.TestCase):
    def test_quality_prefix_is_not_part_of_the_code(self):
        # 这批目录名正是本次要修的：HD 是画质，不是番号的一部分。
        self.assertEqual(audit.canonical_code("HD-abp-758"), "ABP-758")
        self.assertEqual(audit.canonical_code("HD_MIZD-997"), "MIZD-997")
        self.assertEqual(audit.canonical_code("HD_hrv-041"), "HRV-041")
        self.assertEqual(audit.canonical_code("FHD-ssis-070"), "SSIS-070")

    def test_version_suffix_is_stripped(self):
        self.assertEqual(audit.canonical_code("pppd-937ch"), "PPPD-937")
        self.assertEqual(audit.canonical_code("KBI044C"), "KBI-044")
        self.assertEqual(audit.canonical_code("NHDTB500C"), "NHDTB-500")

    def test_digits_are_normalised_to_three_places(self):
        self.assertEqual(audit.canonical_code("abw104"), "ABW-104")
        self.assertEqual(audit.canonical_code("IPVR00296"), "IPVR-296")

    def test_date_code_systems(self):
        self.assertEqual(audit.canonical_code("Carib-040221-001-FHD"), "040221-001")
        self.assertEqual(audit.canonical_code("1pondo-071213_625-HD"), "071213-625")

    def test_names_that_are_not_codes(self):
        for name in ("涼森れむ", "suzuq", "Timepasserby", "MyElla"):
            self.assertIsNone(audit.canonical_code(name), name)

    def test_uuid_first_segment_is_not_a_code(self):
        self.assertIsNone(
            audit.canonical_code("DCE7230C-730E-45DA-9FDC-D167663BC84E"))

    def test_filename_noise_is_stripped_before_matching(self):
        self.assertEqual(audit.code_from_filename("HD-abp-758.mp4"), "ABP-758")
        self.assertEqual(audit.code_from_filename("HD_hrv-041-1.mp4"), "HRV-041")
        self.assertEqual(audit.code_from_filename("BNST033(2).jpg"), "BNST-033")
        self.assertEqual(audit.code_from_filename("040221-001-carib-1080p.mp4"), "040221-001")

    def test_online_identities_are_not_filesystem_paths(self):
        self.assertFalse(audit.is_filesystem_path("https://www.pixiv.net/users/93812377"))
        self.assertTrue(audit.is_filesystem_path(r"B:\云下载\HD-abp-758\HD-abp-758.mp4"))


def _row(name, path, code=None):
    return {"name": name, "path": path, "code": code}


class ClassifyTests(unittest.TestCase):
    def test_release_folder_named_after_its_own_code(self):
        verdict, identity, _ = audit.classify(
            "HD-abp-758", [_row("HD-abp-758.mp4", r"B:\云下载\HD-abp-758\HD-abp-758.mp4")])
        self.assertEqual((verdict, identity), (audit.VERDICT_CODE, "ABP-758"))

    def test_existing_code_column_counts_as_evidence(self):
        verdict, identity, _ = audit.classify(
            "pppd-937ch",
            [_row("PPPD-937CH.mp4", r"B:\云下载\pppd-937ch\PPPD-937CH.mp4", "PPPD-937")])
        self.assertEqual((verdict, identity), (audit.VERDICT_CODE, "PPPD-937"))

    def test_uploader_account_with_title_filenames_is_not_touched(self):
        # banbi_555 形状上像番号，但目录里全是作品标题，没有同番号文件。
        verdict, _, _ = audit.classify("banbi_555", [
            _row("18歳Eカップ彼氏持ち美女.mp4", r"A:\Pack From Shared\pen\banbi_555\18歳.mp4"),
            _row("2_2024_06_08_172104.mp4", r"A:\Pack From Shared\pen\banbi_555\2_2024.mp4"),
        ])
        self.assertEqual(verdict, audit.VERDICT_UNCLEAR)

    def test_pixiv_artist_is_kept_out_of_the_review_entirely(self):
        verdict, _, _ = audit.classify(
            "AH18", [_row("AH18", "https://www.pixiv.net/users/93812377")])
        self.assertEqual(verdict, audit.VERDICT_KEEP)

    def test_site_post_id_is_classified_apart_from_codes(self):
        verdict, identity, _ = audit.classify("fantia-3760310", [
            _row("avruby.png", r"B:\xxr\fantia-3760310\avruby.png"),
            _row("fantia-3760310.mp4", r"B:\xxr\fantia-3760310\fantia-3760310.mp4"),
        ])
        self.assertEqual((verdict, identity), (audit.VERDICT_SITE, "fantia-3760310"))


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "ledger.db"
        self.connection = sqlite3.connect(self.db)
        self.addCleanup(self.connection.close)
        self.connection.executescript(SCHEMA)

    def _creator(self, entity_id, name, assets):
        self.connection.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name) VALUES(?,'creator',?,?)",
            (entity_id, name, name.casefold()))
        for asset_id, asset_name, path, code in assets:
            self.connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,creator,code) "
                "VALUES(?,'local',?,?,'video',?,?)",
                (asset_id, path, asset_name, name, code))
            self.connection.execute(
                "INSERT INTO asset_entity(asset_id,entity_id,role,source) "
                "VALUES(?,?,'creator','legacy:asset')", (asset_id, entity_id))

    def test_apply_removes_the_false_creator_and_fills_the_code(self):
        self._creator(1, "HD-abp-758", [
            (10, "HD-abp-758.mp4", r"B:\云下载\HD-abp-758\HD-abp-758.mp4", None)])
        self._creator(2, "banbi_555", [
            (20, "18歳.mp4", r"A:\Pack From Shared\pen\banbi_555\18歳.mp4", None)])
        self.connection.commit()

        rows = audit.collect(self.connection)
        counts = audit.apply_rows(self.connection, rows)

        self.assertEqual(counts["links"], 1)
        self.assertEqual(counts["entities"], 1)
        self.assertEqual(counts["codes"], 1)
        self.assertEqual(
            self.connection.execute("SELECT creator,code FROM asset WHERE id=10").fetchone(),
            (None, "ABP-758"))
        self.assertIsNone(
            self.connection.execute("SELECT id FROM entity WHERE id=1").fetchone())

        # 存疑的上传者账号必须原样保留：实体、关系和扁平字段都不动。
        self.assertIsNotNone(
            self.connection.execute("SELECT id FROM entity WHERE id=2").fetchone())
        self.assertEqual(
            self.connection.execute("SELECT creator FROM asset WHERE id=20").fetchone()[0],
            "banbi_555")

    def test_existing_code_is_never_overwritten(self):
        self._creator(3, "MIDA-117ch", [
            (30, "MIDA-117CH.mp4", r"B:\云下载\MIDA-117ch\MIDA-117CH.mp4", "MIDA-117")])
        self.connection.commit()
        audit.apply_rows(self.connection, audit.collect(self.connection))
        self.assertEqual(
            self.connection.execute("SELECT code FROM asset WHERE id=30").fetchone()[0],
            "MIDA-117")

    def test_site_post_id_clears_the_creator_without_writing_a_code(self):
        self._creator(4, "fantia-3760310", [
            (40, "fantia-3760310.mp4", r"B:\xxr\fantia-3760310\fantia-3760310.mp4", None)])
        self.connection.commit()
        audit.apply_rows(self.connection, audit.collect(self.connection))
        self.assertEqual(
            self.connection.execute("SELECT creator,code FROM asset WHERE id=40").fetchone(),
            (None, None))

    def test_apply_refuses_to_run_without_a_backup(self):
        parser = audit.build_parser()
        with self.assertRaises(SystemExit):
            audit.run(parser.parse_args(["--db", str(self.db), "--apply"]))


if __name__ == "__main__":
    unittest.main()
