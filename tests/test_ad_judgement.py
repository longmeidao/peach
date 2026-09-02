"""广告复核队列的判据回归。

样本全部来自 2026-08-15 的真实误判与用户手工标记的真广告：命中推广词本身
不是证据，要看剥掉推广词后还剩不剩内容。
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from peach.web_contract import (
    PART_MARK,
    PROMO_DOMAIN,
    PROMO_PHRASE,
    REAL_CODE,
    WebContract,
    promo_residue,
    q_ads,
    q_items,
    w_batch,
)
from support.ledger import fresh_ledger


def promo_hit(name: str) -> bool:
    return bool(PROMO_PHRASE.search(name) or PROMO_DOMAIN.search(name))


class AdJudgementTests(unittest.TestCase):
    #: 用户手工标记为待删的真广告，名字剥完应当基本不剩内容。
    REAL_ADS = (
        "点击观看 房间火爆",
        "国产大片",
        "女神在线视频www.55h.me",
        "澳门皇冠赌场~vip0955.com",
        "tuu26.com",
        "极欲鬼滅之刃366gm.com",
        "苍老师强力推荐",
        "全中文AV在线观看【9se.tv】",
        "【91狼友之家91home.cc】4",
    )

    #: 真实内容，只是被打了站点水印或剧情里出现了推广同形词。
    REAL_CONTENT = (
        "1248 - #饭饭吖 NTR剧情_给单男口交深喉，被母狗式爆操，还要微信跟老公汇报战果",
        "236953.xyz 推特新晋4年绿帽美腿淫妻网黄「一个ren」《榨精美足》"
        "谁能在这美妙的裸足压榨下保持不败",
        "No.017 - 서서 펠라_뒤치기【02분 34초】",
    )

    def test_real_ads_have_nothing_left_after_stripping_promo(self):
        for name in self.REAL_ADS:
            with self.subTest(name=name):
                self.assertTrue(promo_hit(name), "应命中推广词或域名")
                self.assertLess(promo_residue(name), 14,
                                "广告名剥完不应还剩大段实质描述")

    def test_watermarked_content_keeps_its_description(self):
        """名字里有域名/推广同形词，但正文是真实描述，必须留下足够残留。"""
        for name in self.REAL_CONTENT:
            with self.subTest(name=name):
                self.assertGreaterEqual(
                    promo_residue(name), 14,
                    "真实内容剥完仍应剩下可观描述，否则会被当成广告")

    def test_plot_word_is_not_a_contact_method(self):
        """“微信跟老公汇报战果”是剧情；“加微信”“微信号”才是联系方式。"""
        self.assertIsNone(PROMO_PHRASE.search("还要微信跟老公汇报战果"))
        self.assertIsNotNone(PROMO_PHRASE.search("加微信看完整版"))
        self.assertIsNotNone(PROMO_PHRASE.search("微信号：abc123"))

    def test_domain_is_detected_when_followed_by_a_word_character(self):
        """`uuc82.com_2` 用 \\b 收尾会漏：m 与 _ 都是词字符，构不成边界。"""
        self.assertIsNotNone(PROMO_DOMAIN.search("妹妹在精彩表演 哥哥快来大饱眼福uuc82.com_2"))
        self.assertIsNotNone(PROMO_DOMAIN.search("星空天使ccc.18my.cc"))
        self.assertIsNone(PROMO_DOMAIN.search("普通标题 没有站点"))

    def test_only_real_codes_drive_the_longer_version_rule(self):
        """RAIKUN325 是被误填进 code 的创作者账号，不能拿来比时长。"""
        self.assertIsNone(REAL_CODE.match("RAIKUN325"))
        self.assertIsNotNone(REAL_CODE.match("ABW-153"))
        self.assertIsNotNone(REAL_CODE.match("259LUXU-1141"))
        self.assertIsNotNone(REAL_CODE.match("FC2-PPV-1234567"))

    def test_disposal_marks_mix_two_different_intents(self):
        """`disposal` 同时承载“这是广告”和“这个我不喜欢”，不能当纯广告标注集。

        用户 2026-08-15 澄清：`1726897607_*` 那批 10 个时间戳命名的长录像被标删，
        是因为不喜欢该来源，与广告无关。判据不该、也不可能识别出这类。
        """
        for name in ("1726897607_1726897607_20250831-214903",
                     "1726897607_1726897607_20250823-215124"):
            with self.subTest(name=name):
                self.assertFalse(promo_hit(name), "时间戳文件名不含推广特征")

    def test_part_markers_still_protect_split_volumes(self):
        for name in ("Movie CD2", "feature part1", "作品 分卷", "title-2", "title (3)"):
            with self.subTest(name=name):
                self.assertIsNotNone(PART_MARK.search(name))


class ResourceJunkQueueTests(unittest.TestCase):
    """物理资源都要经过垃圾判断，类型不能成为免检条件。"""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db_path = fresh_ledger(self.temporary.name)
        self.contract = WebContract(self.db_path)

    def add(self, asset_id, location, path, medium, size=1000, duration=None,
            creator=None, disposal=None):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,size,duration,creator,disposal) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (asset_id, location, path, path.rsplit("\\", 1)[-1], medium,
                 size, duration, creator, disposal),
            )
            connection.commit()
        finally:
            connection.close()

    def test_video_image_audio_archive_and_url_shortcut_are_all_judged(self):
        self.add(1, "115", r"B:\广告\tuu26.com.mp4", "video",
                 10 * 1024**2, 60)
        self.add(2, "115", r"B:\番号\CAWD-241\亚博体育hayob9.com.jpg", "image", 28725)
        self.add(3, "pikpak", r"A:\资源\点击这里.url", "other", 128)
        self.add(4, "local", r"R:\media\福利群vip0955.com.zip", "archive", 2048)
        self.add(5, "local", r"R:\media\苍老师强力推荐.mp3", "audio", 4096)
        # 域名属于作品出处且仍有长内容描述，不是推广垃圾。
        self.add(
            6, "115",
            r"B:\创作者\Dakota Doll - [LegalPorno.com] - [2024] - Breakfast Sex.mp4.jpg",
            "image", 280000, creator="Dakota Doll",
        )
        # online 的 path 本来就是 URL，不是等待清理的物理快捷方式。
        self.add(7, "online", "https://example.com/post/1.url", "other", 0)

        result = q_ads(self.contract, limit=200)

        self.assertEqual(result["total"], 5)
        self.assertEqual(
            {item["medium"] for item in result["items"]},
            {"video", "image", "audio", "archive", "other"},
        )
        by_id = {item["id"]: item for item in result["items"]}
        self.assertIn("网址快捷方式", by_id[3]["why"])
        self.assertEqual(by_id[3]["junk_kind"], "url")
        self.assertIn("整个名字都是推广语", by_id[2]["why"])
        self.assertNotIn(6, by_id)
        self.assertNotIn(7, by_id)
        self.assertTrue(all("path" not in item for item in result["items"]))

    def test_non_video_trash_items_remain_visible_and_recoverable(self):
        self.add(10, "115", r"B:\番号\广告图.jpg", "image", disposal="trash")
        self.add(11, "115", r"B:\番号\备用网址.url", "other", disposal="trash")
        self.add(12, "115", r"B:\番号\正片.mp4", "video", 1024, 60)

        result = q_items(self.contract, {
            "state": "trash", "limit": "60", "thumb": "1",
            "exclude_vertical": "1", "dur_min": "3600", "jav": "1",
        })

        self.assertEqual(result["total"], 2)
        self.assertEqual(
            {(item["id"], item["medium"]) for item in result["items"]},
            {(10, "image"), (11, "other")},
        )

    def test_mib_archives_can_be_excluded_and_reconsidered_per_asset(self):
        """域名文件名可能是真资源；“不是垃圾”必须可持久排除且能撤销。"""
        self.add(20, "115", r"B:\\MIB\\Mib19.com.zip", "archive", 14 * 1024**3)
        self.add(21, "115", r"B:\\MIB\\Mib19.com(2).zip", "archive", 15 * 1024**3)
        self.add(22, "115", r"B:\\广告\\hayob9.com.jpg", "image", 28000)

        pending = q_ads(self.contract, limit=200)
        self.assertEqual(pending["counts"]["archive"], 2)
        self.assertEqual([item["id"] for item in q_ads(
            self.contract, limit=200, kind="archive")["items"]], [21, 20])

        changed = w_batch(self.contract, {"ids": [20], "operation": "dismiss-junk"})
        self.assertEqual(changed["changed"], 1)
        self.assertEqual(q_ads(self.contract, limit=200)["pending_total"], 2)
        dismissed = q_ads(self.contract, limit=200, status="dismissed")
        self.assertEqual([item["id"] for item in dismissed["items"]], [20])
        self.assertEqual(dismissed["counts"]["archive"], 1)

        w_batch(self.contract, {"ids": [20], "operation": "reconsider-junk"})
        self.assertEqual(q_ads(self.contract, limit=200)["pending_total"], 3)
        self.assertEqual(q_ads(
            self.contract, limit=200, status="dismissed")["items"], [])

    def test_invalid_junk_filters_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid junk kind"):
            q_ads(self.contract, kind="document")
        with self.assertRaisesRegex(ValueError, "invalid junk status"):
            q_ads(self.contract, status="deleted")


if __name__ == "__main__":
    unittest.main()
