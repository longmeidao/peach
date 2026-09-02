r"""转载站水印域名不得被当成番号。

起因是一次真实误判：asset 31048 的 path 是

    B:\番号\_未知厂牌\HHD800\hhd800.com@ABW-132.mp4\ABW-132.mp4

真番号 ABW-132 就在文件名里，`code` 却是 `HHD800`——hhd800.com 是转载站域名水印。
它能过关是因为 `normalise_code_key` 的形态规则会替「字母紧贴数字」补出连字符，
`HHD800` 于是变成 `HHD-800`，一路通过 `is_jav_code`、`JAV_ASSET_PREDICATE`、作品页的
`display_code`，还会被 `clean_names` 当成重命名依据写回 ledger。

所以这里同时钉住两侧：名单命中的标识一律不是番号，而真番号里同样没有分隔符的那些
（`IPX219C`、`MEYD911`、`476MLA-179`）必须继续被认出来——形态分不开，只有名单能分。
"""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from peach.catalog_rules import (
    REPOST_SITE_LABELS,
    compact_label,
    is_jav_asset,
    is_jav_code,
    is_repost_site_label,
    normalise_code_key,
    release_code_from_filename,
    release_code_from_text,
)
from peach.migrations import upgrade
from peach.review_csv import write_rows

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_domain_codes.py"
_spec = importlib.util.spec_from_file_location("audit_domain_codes", SCRIPT)
audit = importlib.util.module_from_spec(_spec)
sys.modules["audit_domain_codes"] = audit
_spec.loader.exec_module(audit)

SCHEMA = """
CREATE TABLE asset(
  id INTEGER PRIMARY KEY, location TEXT NOT NULL, path TEXT NOT NULL, name TEXT,
  medium TEXT, code TEXT, studio TEXT, release_date TEXT, UNIQUE(location,path));
CREATE TABLE entity(
  id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT, normalized_name TEXT,
  UNIQUE(kind,normalized_name));
CREATE TABLE asset_entity(
  asset_id INTEGER, entity_id INTEGER, role TEXT, source TEXT,
  UNIQUE(asset_id,entity_id,role,source));
"""


class RepostLabelTests(unittest.TestCase):
    def test_bare_label_and_full_domain_are_both_recognised(self):
        self.assertTrue(is_repost_site_label("HHD800"))
        self.assertTrue(is_repost_site_label("hhd800.com"))
        self.assertTrue(is_repost_site_label("www.98t.la"))

    def test_zero_padded_form_is_recognised_too(self):
        # `normalise_code_key` 把 `BEI88` 写成 `BEI-088`，而界面显示、SQL 谓词和
        # 重命名脚本比的都是补过零的那一种。只拦一种写法等于没拦。
        self.assertTrue(is_repost_site_label("BEI-088"))
        self.assertEqual(compact_label("BEI-088"), compact_label("bei88"))

    def test_real_codes_of_the_same_shape_are_not_labels(self):
        for code in ("MEYD911", "IPX219C", "476MLA-179", "ABW-132", "PBD390"):
            self.assertFalse(is_repost_site_label(code), code)

    def test_every_listed_label_is_stored_in_compact_form(self):
        # 名单是按压缩形比较的。写成 `HHD-800` 或 `HHD800.com` 都永远命中不了，
        # 而加名单的人不会去读 `is_repost_site_label` 才发现这件事。
        for label in REPOST_SITE_LABELS:
            self.assertEqual(compact_label(label), label, label)


class NormalisationTests(unittest.TestCase):
    def test_watermark_no_longer_gets_a_fabricated_hyphen(self):
        self.assertEqual(normalise_code_key("HHD800"), "HHD800")
        self.assertEqual(normalise_code_key("AAVV333"), "AAVV333")
        self.assertEqual(normalise_code_key("BEI88"), "BEI88")

    def test_real_compact_codes_still_normalise(self):
        self.assertEqual(normalise_code_key("MEYD911"), "MEYD-911")
        self.assertEqual(normalise_code_key("IPVR00296"), "IPVR-296")
        self.assertEqual(normalise_code_key("476MLA179"), "476MLA-179")

    def test_watermark_is_not_a_jav_code(self):
        for code in ("HHD800", "hhd800.com", "AAVV333", "KFA33", "HJD2048", "BEI88"):
            self.assertFalse(is_jav_code(code), code)
            self.assertFalse(is_jav_code(normalise_code_key(code)), code)

    def test_watermark_is_not_a_jav_asset_even_with_release_evidence(self):
        # 搬运包里混着有片商的条目。发行证据能救 `PBD390`，不能把域名变成番号。
        self.assertFalse(is_jav_asset("HHD800", "S1 NO.1 STYLE"))
        self.assertFalse(is_jav_asset("HHD800", None, "2022-04-01"))
        self.assertFalse(is_jav_asset("HHD800", None, None, ("performer",)))
        self.assertTrue(is_jav_asset("PBD390", "MOODYZ"))


class ExtractionTests(unittest.TestCase):
    def test_watermark_chain_yields_the_real_code(self):
        self.assertEqual(release_code_from_filename("ABW-132.mp4"), "ABW-132")
        self.assertEqual(release_code_from_filename("IPX219C.mp4"), "IPX-219")
        self.assertEqual(release_code_from_filename("MEYD911.mp4"), "MEYD-911")
        self.assertEqual(release_code_from_filename("476MLA-179.mp4"), "476MLA-179")

    def test_fc2_ids_survive_the_compact_form(self):
        self.assertEqual(release_code_from_text("FC2-PPV-2909046"), "FC2-PPV-2909046")
        self.assertEqual(release_code_from_text("fc2802296"), "FC2-PPV-802296")

    def test_labels_and_domains_extract_to_nothing(self):
        for text in ("HHD800", "hhd800.com", "www.98t.la", "AAVV333", "bei88"):
            self.assertIsNone(release_code_from_text(text), text)


class AuditScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.connection = sqlite3.connect(Path(self.tmp.name).resolve() / "ledger.db")
        self.addCleanup(self.connection.close)
        self.connection.executescript(SCHEMA)

    def _asset(self, asset_id, path, code, *, studio=None, kind=None):
        self.connection.execute(
            "INSERT INTO asset(id,location,path,name,medium,code,studio) "
            "VALUES(?,'local',?,?,'video',?,?)",
            (asset_id, path, path.rsplit("\\", 1)[-1], code, studio))
        if kind:
            self.connection.execute(
                "INSERT OR IGNORE INTO entity(id,kind,canonical_name,normalized_name) "
                "VALUES(?,?,?,?)", (asset_id, kind, f"e{asset_id}", f"e{asset_id}"))
            self.connection.execute(
                "INSERT INTO asset_entity(asset_id,entity_id,role,source) "
                "VALUES(?,?,?,'test')", (asset_id, asset_id, kind))
        self.connection.commit()

    def _rows(self):
        return {int(row["asset_id"]): row for row in audit.collect(self.connection)}

    def test_the_reported_asset_gets_the_code_from_its_filename(self):
        self._asset(31048, r"B:\番号\_未知厂牌\HHD800\hhd800.com@ABW-132.mp4\ABW-132.mp4",
                    "HHD800")
        row = self._rows()[31048]
        self.assertEqual(row["verdict"], audit.VERDICT_CODED)
        self.assertEqual(row["proposed_code"], "ABW-132")
        self.assertEqual(row["tier"], "E1")
        self.assertEqual(row["evidence"], "hhd800.com")

    def test_a_watermark_without_any_code_proposes_clearing_instead(self):
        self._asset(1, r"B:\番号\_未知厂牌\BEI88\bei88@sis001@某个标题.mp4\某个标题.mp4",
                    "BEI88")
        row = self._rows()[1]
        self.assertEqual(row["verdict"], audit.VERDICT_BLANK)
        self.assertEqual(row["proposed_code"], "")

    def test_the_code_named_directory_is_not_mined_for_a_proposal(self):
        # `…\WX17\` 那层目录就是被水印顶替出来的，从它身上解析只会拿回同一个水印。
        self._asset(2, r"B:\番号\_未知厂牌\WX17\[mtfdz.club]WX17.3\别删~好回家.rar", "WX17")
        row = self._rows()[2]
        self.assertEqual(row["verdict"], audit.VERDICT_PACK)
        self.assertEqual(row["proposed_code"], "")
        self.assertEqual(row["evidence"], "mtfdz.club")

    def test_a_taste_tag_does_not_shield_a_pack_label(self):
        # WX17 的 269 条里大半挂着口味标签。按「有实体就放过」判会整包漏掉。
        self._asset(3, r"B:\番号\_未知厂牌\WX17\[mtfdz.club]WX17.3\x\a.mp4", "WX17",
                    kind="tag")
        self.assertEqual(self._rows()[3]["verdict"], audit.VERDICT_PACK)

    def test_a_real_code_from_a_repost_site_is_left_alone(self):
        # 文件来自 thzu.cc，但 `TZ-105` 自带分隔符，没人替它造过番号。
        self._asset(4, r"B:\番号\_未知厂牌\TZ-105\thzu.cc@TZ-105.mp4", "TZ-105")
        self.assertNotIn(4, self._rows())

    def test_release_evidence_keeps_a_compact_code_out_of_the_review(self):
        self._asset(5, r"B:\番号\MOODYZ\thz.la@PBD390\PBD390.mp4", "PBD390",
                    studio="MOODYZ")
        self.assertNotIn(5, self._rows())

    def test_an_ad_file_inherits_the_code_its_siblings_agree_on(self):
        # 发行目录里混着广告图和被站点改过名的分卷。逐个文件名判会把它们报成
        # 「无番号，建议清空」，而同目录的另外两条已经指明这是哪一部。
        folder = r"B:\番号\_未知厂牌\HJD2048\hjd2048.com-0112mide612-h264"
        self._asset(10, folder + r"\mide612-5.mp4", "HJD2048")
        self._asset(11, folder + r"\mide612.jpg", "HJD2048")
        self._asset(12, folder + r"\最新成人AV.gif", "HJD2048")
        rows = self._rows()
        self.assertEqual((rows[10]["proposed_code"], rows[10]["proposal_from"]),
                         ("MIDE-612", "文件名"))
        self.assertEqual((rows[12]["proposed_code"], rows[12]["proposal_from"]),
                         ("MIDE-612", "同目录兄弟"))

    def test_two_codes_in_one_directory_leave_the_rest_unproposed(self):
        # 目录里有两部片时，兄弟证据指不出这条属于哪一部，宁可报「无番号」。
        folder = r"B:\番号\_未知厂牌\HHD800\hhd800.com@合集"
        self._asset(13, folder + r"\ABW-132.mp4", "HHD800")
        self._asset(14, folder + r"\SSIS-070.mp4", "HHD800")
        self._asset(15, folder + r"\广告.gif", "HHD800")
        row = self._rows()[15]
        self.assertEqual(row["verdict"], audit.VERDICT_BLANK)
        self.assertEqual((row["proposed_code"], row["proposal_from"]), ("", ""))

    def test_an_unlisted_domain_is_caught_by_path_evidence_alone(self):
        # 名单永远滞后于新站点。路径里带 `<code>.<tld>` 的，不进名单也要报出来，
        # 否则这份排查只能确认已经知道的事。
        self._asset(6, r"B:\番号\_未知厂牌\NEWSITE77\newsite77.com@SSIS-070\SSIS-070.mp4",
                    "NEWSITE77")
        row = self._rows()[6]
        self.assertEqual((row["tier"], row["confidence"]), ("E2", "高"))
        self.assertEqual(row["proposed_code"], "SSIS-070")

    def test_a_sibling_carries_the_evidence_for_a_renamed_file(self):
        # 同一批搬运包里只有部分文件保留了水印；自己那条 path 判不出来的走 E3。
        self._asset(7, r"B:\番号\_未知厂牌\NEWSITE77\newsite77.com@SSIS-070\SSIS-070.mp4",
                    "NEWSITE77")
        self._asset(8, r"B:\番号\_未知厂牌\NEWSITE77\SSIS-071\SSIS-071.mp4", "NEWSITE77")
        row = self._rows()[8]
        self.assertEqual((row["tier"], row["confidence"]), ("E3", "中"))
        self.assertEqual(row["proposed_code"], "SSIS-071")
        self.assertEqual(row["evidence"], "newsite77.com")


class ApplyTests(unittest.TestCase):
    """写库这一侧。

    用真实迁移建库，不用精简 schema：这次改的是 `asset.code`，而 `asset_search.code`
    是靠 `0004`/`0023` 的触发器跟着走的。拿一张没有触发器的表测，等于把「搜索索引里
    还留着旧水印」这个最容易漏的表面从测试里删掉。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.db = self.root / "ledger.db"
        sqlite3.connect(self.db).close()
        upgrade(self.db, MIGRATIONS)
        self.review = self.root / "review.csv"

    def _asset(self, asset_id, path, code):
        connection = sqlite3.connect(self.db)
        connection.execute(
            "INSERT INTO asset(id,location,path,name,medium,code) "
            "VALUES(?,'local',?,?,'video',?)",
            (asset_id, path, path.rsplit("\\", 1)[-1], code))
        connection.commit()
        connection.close()

    def _plan(self, *rows):
        write_rows(self.review, (*audit.FIELDS, "applied"), rows, fill_missing=True)

    def _run(self, *extra):
        return audit.run(audit.build_parser().parse_args(
            ["--db", str(self.db), "--review-csv", str(self.review), *extra]))

    def _codes(self):
        connection = sqlite3.connect(self.db)
        try:
            return {row[0]: (row[1], row[2]) for row in connection.execute(
                "SELECT a.id,a.code,s.code FROM asset a "
                "LEFT JOIN asset_search s ON s.asset_id=a.id")}
        finally:
            connection.close()

    def test_apply_without_a_backup_refuses_to_start(self):
        # `code` 是真相字段，和迁移同级：没有备份就没有回退路径。
        self._asset(1, r"B:\x\HHD800\hhd800.com@ABW-132.mp4", "HHD800")
        self._plan({"asset_id": "1", "current_code": "HHD800",
                    "proposed_code": "ABW-132", "tier": "E1"})
        with self.assertRaises(SystemExit):
            self._run("--apply")
        self.assertEqual(self._codes()[1][0], "HHD800")

    def test_the_reviewed_rows_are_written_and_the_index_follows(self):
        self._asset(1, r"B:\x\HHD800\hhd800.com@ABW-132.mp4", "HHD800")
        self._asset(2, r"B:\x\BEI88\bei88@sis001@合集.mp4", "BEI88")
        self._plan(
            {"asset_id": "1", "current_code": "HHD800",
             "proposed_code": "ABW-132", "tier": "E1"},
            {"asset_id": "2", "current_code": "BEI88",
             "proposed_code": "", "tier": "E1"})
        self.assertEqual(self._run("--apply", "--backup", str(self.root / "b.db")), 0)
        codes = self._codes()
        self.assertEqual(codes[1], ("ABW-132", "ABW-132"))
        self.assertEqual(codes[2], (None, ""))
        self.assertTrue((self.root / "b.db").exists())

    def test_a_pack_row_is_never_written(self):
        # `存疑` 的 269 条论坛整合包要人工看过再定，不能跟着这一批一起改。
        self._asset(3, r"B:\x\WX17\[mtfdz.club]WX17.3\a.rar", "WX17")
        self._plan({"asset_id": "3", "current_code": "WX17",
                    "proposed_code": "", "tier": "存疑"})
        with self.assertRaises(SystemExit):
            self._run("--apply", "--backup", str(self.root / "b.db"))
        self.assertEqual(self._codes()[3][0], "WX17")

    def test_a_row_edited_since_the_review_is_skipped_not_overwritten(self):
        # 出表和写库之间隔着一次人工阅读，期间别的脚本可能已经改过同一行。
        self._asset(4, r"B:\x\HHD800\hhd800.com@ABW-132.mp4", "SSIS-070")
        self._plan({"asset_id": "4", "current_code": "HHD800",
                    "proposed_code": "ABW-132", "tier": "E1"})
        self._run("--apply", "--backup", str(self.root / "b.db"))
        self.assertEqual(self._codes()[4][0], "SSIS-070")

    def test_a_watermark_typed_into_the_csv_is_refused(self):
        # 表是给人改的，但手填回一个域名就绕开了这次修复的全部意义。
        self._asset(5, r"B:\x\HHD800\hhd800.com@ABW-132.mp4", "HHD800")
        self._plan({"asset_id": "5", "current_code": "HHD800",
                    "proposed_code": "hhd800.com", "tier": "E1"})
        self._run("--apply", "--backup", str(self.root / "b.db"))
        self.assertEqual(self._codes()[5][0], "HHD800")

    def test_the_default_run_leaves_the_ledger_alone(self):
        self._asset(6, r"B:\x\HHD800\hhd800.com@ABW-132.mp4", "HHD800")
        self.assertEqual(self._run(), 0)
        self.assertEqual(self._codes()[6][0], "HHD800")
        self.assertIn("mode=ro", SCRIPT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
