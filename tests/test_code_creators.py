import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_code_creators.py"
_spec = importlib.util.spec_from_file_location("audit_code_creators", SCRIPT)
_script = importlib.util.module_from_spec(_spec)
sys.modules["audit_code_creators"] = _script
_spec.loader.exec_module(_script)


class _Audit:
    """判定与清理归 `peach.code_creators`，命令行入口留在脚本里；测试两边都要够得着。"""
    from peach.catalog_rules import release_code_from_filename as code_from_filename
    from peach.catalog_rules import release_code_from_text as canonical_code
    from peach.code_creators import (  # noqa: F401  逐个点名，测试不跟着模块表面漂移
        FIELDS, VERDICT_CODE, VERDICT_KEEP, VERDICT_SITE, VERDICT_UNCLEAR,
        apply_rows, classify, collect, is_filesystem_path,
    )
    build_parser = staticmethod(_script.build_parser)
    run = staticmethod(_script.run)
    main = staticmethod(_script.main)


audit = _Audit


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
        # 分隔符是片商标识：加勒比写 `-`、一本道写 `_`，同日同序号是两部不同影片，
        # 目录名给的是哪一个就留哪一个。
        self.assertEqual(audit.canonical_code("Carib-040221-001-FHD"), "040221-001")
        self.assertEqual(audit.canonical_code("1pondo-071213_625-HD"), "071213_625")

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

    def test_a_download_site_folder_around_the_code_is_still_a_release_folder(self):
        """站名、画质和分享标记贴在番号前后，目录仍是发行目录，不是创作者。

        本机实测的写法：`Jav.li_MIAD573_HD`、`[98t.tv][98t.tv]ABW-251`、
        `nes@第一会所@ATID-479`、`kpxvs-300MIUM-698`。整名比对认不出它们，而 11 个这样的
        「创作者」名下挂着 33 条资产，在创作者索引里各占一个假身份。
        """
        for name, sample, code, identity in (
            ("Jav.li_MIAD573_HD", "MIAD573_01.wmv", "MIAD-573", "MIAD-573"),
            ("[98t.tv][98t.tv]ABW-251", "ABW-251.mp4", "", "ABW-251"),
            ("nes@第一会所@ATID-479", "ATID-479.mp4", "", "ATID-479"),
        ):
            with self.subTest(name=name):
                verdict, found, _ = audit.classify(
                    name, [_row(sample, rf"B:\云下载\{name}\{sample}", code)])
                self.assertEqual((verdict, found), (audit.VERDICT_CODE, identity))

    def test_an_uploader_account_shaped_like_a_code_is_not_matched_by_containment(self):
        """按包含关系找番号时，上传者账号是最容易被误伤的一类。

        `banbi_555` 的 code 列存的就是目录名 `BANBI_555`，紧凑形一比自然「包含」。
        发行番号这道形态门槛把它挡在外面，所以它仍然只是存疑，留给人看。
        """
        verdict, _, _ = audit.classify("banbi_555", [
            _row("18歳Eカップ彼氏持ち美女.mp4",
                 r"A:\Pack From Shared\pen\banbi_555\18歳.mp4", "BANBI_555"),
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
