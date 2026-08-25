"""广告复核队列的判据回归。

样本全部来自 2026-08-15 的真实误判与用户手工标记的真广告：命中推广词本身
不是证据，要看剥掉推广词后还剩不剩内容。
"""
import unittest

from peach.web_contract import (
    PART_MARK,
    PROMO_DOMAIN,
    PROMO_PHRASE,
    REAL_CODE,
    promo_residue,
)


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


if __name__ == "__main__":
    unittest.main()
