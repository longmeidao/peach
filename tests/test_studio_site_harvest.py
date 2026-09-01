"""厂牌官网采集：候选是假设，判定才是证据。"""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load_module():
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(
        "harvest_studio_sites", REPO / "scripts" / "harvest_studio_sites.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def page(title: str, filler: str = "本編は18歳以上の方のみご覧いただけます。") -> bytes:
    """够长、含标题的正常页面；长度必须越过空壳下限，否则测的就不是标题判定。"""
    body = f"<html><head><title>{title}</title></head><body>{filler * 400}</body></html>"
    return body.encode("utf-8")


class SlugTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_a_multiword_name_yields_both_joined_and_hyphenated_hosts(self):
        """`Wanz Factory` 的真实域名是 wanz-factory.com，而 `Idea Pocket` 是 ideapocket.com。

        两种写法都常见，只推一种就会漏掉一半；连写在前是因为它更常见。
        """
        self.assertEqual(self.module.slugs("Wanz Factory"), ["wanzfactory", "wanz-factory"])
        self.assertEqual(self.module.slugs("MOODYZ"), ["moodyz"])

    def test_a_name_without_latin_letters_yields_no_candidates(self):
        """`无码厂标` 这类名字推不出域名。

        推不出来要老实返回空，让它落到「没有可推导的候选域名」，
        而不是拼出一个必然打不开的地址再去请求一遍。
        """
        self.assertEqual(self.module.slugs("无码厂标"), [])
        self.assertEqual(self.module.candidate_urls("无码厂标"), [])

    def test_candidate_urls_are_unique_and_prefer_dot_com(self):
        urls = self.module.candidate_urls("MOODYZ")
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(urls[0], "https://moodyz.com/")
        self.assertTrue(any(u.endswith("moodyz.jp/") for u in urls))

    def test_the_www_variant_is_not_a_separate_candidate(self):
        """多出来的那一半候选几乎只在失败路径上产生开销。

        transport 开着 follow_redirects，只用 `www.` 的站会从裸域跳过来；而裸域连不上时
        `www.` 基本也连不上。首轮 57 个厂牌 × 8 个候选跑了三个多小时还没完——httpx 把
        单个标量同时当作 connect 和 read 超时，死域名每个吃掉两份。这条测试守的是那次代价。
        """
        urls = self.module.candidate_urls("Wanz Factory")
        self.assertFalse([url for url in urls if url.startswith("https://www.")])
        self.assertEqual(len(urls), 8)   # 2 个 slug 写法 × 4 种域名形态


class VerdictTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_a_title_that_names_the_studio_is_accepted(self):
        """实测标题：分隔符、全角括号和日文注音都对不齐，剥到字母数字才可比。"""
        title = "年齢チェック | 人気知名度NO.1！アダルトビデオ最強のAVメーカー【MOODYZ(ムーディーズ)】公式サイト"
        verdict, _ = self.module.site_verdict("MOODYZ", 200, page(title), title)
        self.assertEqual(verdict, "ok")

        title = "年齢チェック | ハイクオリティのAVメーカー【IDEAPOCKET (アイデアポケット）】公式サイト"
        verdict, _ = self.module.site_verdict("Idea Pocket", 200, page(title), title)
        self.assertEqual(verdict, "ok")

    def test_an_unrelated_company_with_the_same_name_is_not_confirmed(self):
        """「标题里有厂牌名」证明不了这是**这个**厂牌的站。

        实测四例全都 200、都不是停放页、标题里都有厂牌名：`madonna.com` 是歌手麦当娜
        （真站 madonna-av.com）、`hunter.com` 是 Hunter Engineering、`bazooka.com`
        是车载音响。缺的那一半是「这一页是不是 AV 厂牌站」——我们要找的就是 AV 官网，
        成人语境本来就是判据的一部分，不是补丁。这类只能判 weak 交给人看，不能算已确认：
        一条错的官网会被下游当成社媒 handle 的来源。
        """
        for studio, title in [("MADONNA", "Madonna – Icon Community"),
                              ("Hunter", "Home | Hunter Engineering Company®"),
                              ("BAZOOKA", "Bazooka Bass Tubes")]:
            verdict, note = self.module.site_verdict(
                studio, 200, page(title, "公司简介与产品目录。"), title,
                f"https://{studio.lower()}.com/")
            self.assertEqual(verdict, "weak", studio)
            self.assertIn("成人站", note)

    def test_a_derived_domain_on_an_adult_site_counts_even_when_the_title_uses_kana(self):
        """日站普遍把品牌名写成假名，拿拉丁名比标题对整整一类真站都会失败。

        实测：`honnaka.jp` 的标题是「年齢チェック | 全作品、本物中出しのAVメーカー
        【本中】公式サイト」，`muku.tv` 是「【無垢】」，`tameikegoro.jp` 是「【TAMEIKE】」。
        这是系统性漏判，不是个别情况。此时两个独立信号同样成立：域名由厂牌名按固定规则
        推出（不是人喂的），且这一页确实是成人站。
        """
        title = "年齢チェック | 全作品、本物中出しのAVメーカー【本中】公式サイト"
        verdict, note = self.module.site_verdict(
            "Hon Naka", 200, page(title), title, "https://honnaka.jp/",
            derived_hosts=frozenset({"honnaka.jp"}))
        self.assertEqual(verdict, "ok")
        self.assertIn("假名", note)

    def test_a_derived_domain_that_is_not_an_adult_site_is_still_refused(self):
        """`bazooka.com`、`madonna.com` 的域名同样推得出来。

        把它们和上面那条区分开的正是成人语境这一条；少了它，这条新规则会把每个
        「同名公司」都当成官网确认掉——比原来更糟。
        """
        title = "Bazooka Bass Tubes"
        verdict, _ = self.module.site_verdict(
            "BAZOOKA", 200, page(title, "car audio subwoofers. "), title,
            "https://bazooka.com/", derived_hosts=frozenset({"bazooka.com"}))
        self.assertEqual(verdict, "weak")

    def test_a_seeded_url_does_not_get_the_derived_domain_signal(self):
        """人喂进来的地址不能借「域名由厂牌名推出」这条的力。

        那条信号的价值在于域名是独立推出来的；种子是人给的，混在一起就等于自证。
        """
        title = "年齢チェック | マニアック フェチのAVメーカー【ダスッ！】公式サイト"
        seeded, _ = self.module.site_verdict(
            "Das", 200, page(title), title, "https://dasdas.jp/")
        found, _ = self.module.site_verdict(
            "Das", 200, page(title), title, "https://dasdas.jp/",
            derived_hosts=frozenset({"dasdas.jp"}))
        self.assertNotEqual(seeded, "ok", "种子不该借域名推导这条信号确认")
        self.assertEqual(found, "ok", "同一页面若域名是推出来的才算两个独立信号")

    def test_a_derived_domain_that_redirects_elsewhere_loses_the_signal(self):
        """跳走之后，「域名由厂牌名推出」这条证据就不再对我们落到的那一页成立。

        实测：`Natural High` 的一个推导域名重定向到了 `linkedin.com/in/fareedkhan`。
        按请求地址判 derived 的话，一个 LinkedIn 个人主页会被确认成厂牌官网。
        判据必须落在最终主机上。
        """
        title = "Fareed Khan - Ericsson | LinkedIn"
        verdict, _ = self.module.site_verdict(
            "Natural High", 200, page(title, "adult contacts and 18+ groups. "), title,
            "https://www.linkedin.com/in/fareedkhan",
            derived_hosts=frozenset({"naturalhigh.com", "naturalhigh.jp"}))
        self.assertNotEqual(verdict, "ok")

    def test_a_western_studio_page_still_counts_as_adult(self):
        """判据不能只认日文，否则西方厂牌会被一律打成待复核。"""
        title = "BLACKED - The Best Adult Video Site"
        verdict, _ = self.module.site_verdict(
            "Blacked", 200, page(title, "adult video content, 18+ only. "), title,
            "https://blacked.com/")
        self.assertEqual(verdict, "ok")

    def test_a_parked_page_is_rejected_even_though_its_title_echoes_the_name(self):
        """这是猜域名最危险的失败模式。

        抢注页同样回 200，标题里同样有厂牌名（因为那就是域名本身）。只看标题的话
        `moodyz.com` 的停放页会被当成官网采信，再被下游当成社媒 handle 的来源，
        最后把抢注者的账号安到厂牌头上。
        """
        title = "moodyz.com - This domain is for sale"
        verdict, note = self.module.site_verdict("MOODYZ", 200, page(title), title)
        self.assertEqual(verdict, "未取得")
        # 拦在标题还是正文都算数，守的是「被拒绝且理由指向域名出售」。
        self.assertRegex(note, "出售|停放")

    def test_a_generic_domain_whose_title_is_just_its_address_is_rejected(self):
        """停放页规则拦不住这一类：它是个正常的站，只是不属于这个厂牌。

        实测 `https://www.prestige.com/` 返回 200、不是停放页、标题正好是
        `prestige.com`，因此通过了「标题含厂牌名」被判成 Prestige 官网——而真站是
        `prestige-av.com`，`prestige.com` 是另一家公司。判据是：标题若不比域名多说
        任何东西，就等于没有自述身份。
        """
        verdict, note = self.module.site_verdict(
            "Prestige", 200, page("prestige.com"), "prestige.com",
            "https://www.prestige.com/")
        self.assertEqual(verdict, "未取得")
        self.assertIn("域名回显", note)

    def test_a_real_site_is_not_rejected_by_the_domain_echo_rule(self):
        """真站的标题远不止域名，这条规则不能误伤它们。"""
        title = "年齢チェック | 人気知名度NO.1！アダルトビデオ最強のAVメーカー【MOODYZ(ムーディーズ)】公式サイト"
        verdict, _ = self.module.site_verdict(
            "MOODYZ", 200, page(title), title, "https://moodyz.com/")
        self.assertEqual(verdict, "ok")

    def test_a_parked_title_is_caught_even_when_the_body_keyword_is_far_down(self):
        """实测漏判：`kawaii.com - domain for sale`。

        关键词确实在正文里，但在第 81683 字节——任何固定的正文扫描窗口都会漏掉它。
        而它就写在标题里，我此前从来没搜过标题。真站的标题不会说自己在出售，
        所以标题可以用最宽的判据。
        """
        title = "kawaii.com - domain for sale"
        body = page("无关内容") + b"x" * 90000 + "domain for sale".encode()
        verdict, note = self.module.site_verdict("kawaii", 200, body, title,
                                                 "https://www.kawaii.com/")
        self.assertEqual(verdict, "未取得")
        self.assertIn("出售", note)

    def test_a_parked_title_with_words_between_is_still_caught(self):
        """实测漏判：`Attackers - The Domain Name Attackers.com is Now For Sale.`

        逐字匹配「domain for sale」对不上——中间插了域名和 is Now。这正是为什么
        标题要单独用更松的判据，而不是把正文那套原样套过来。
        """
        title = "Attackers - The Domain Name Attackers.com is Now For Sale."
        verdict, note = self.module.site_verdict("Attackers", 200, page(title), title,
                                                 "https://attackers.com/")
        self.assertEqual(verdict, "未取得")
        self.assertIn("出售", note)

    def test_a_short_page_is_rejected(self):
        """空壳页也是 200。真站首页实测都在 10 KB 以上。"""
        verdict, note = self.module.site_verdict("MOODYZ", 200, b"<title>MOODYZ</title>", "MOODYZ")
        self.assertEqual(verdict, "未取得")
        self.assertIn("字节", note)

    def test_a_page_that_never_names_the_studio_is_not_guessed_into_ok(self):
        title = "無料動画まとめサイト"
        verdict, _ = self.module.site_verdict("MOODYZ", 200, page(title), title)
        self.assertEqual(verdict, "未取得")

    def test_a_body_only_mention_is_weak_not_ok(self):
        """正文提到不等于这是官网——转载站也会提到厂牌名。

        它值得人看一眼，所以照样出行，但判定必须和标题自述区分开，
        不能混进 ok 里被当成已确认。
        """
        body = page("よくある動画サイト", "MOODYZ の作品を紹介します。")
        verdict, note = self.module.site_verdict("MOODYZ", 200, body, "よくある動画サイト")
        self.assertEqual(verdict, "weak")
        self.assertIn("人工", note)

    def test_a_non_200_is_rejected_before_reading_the_body(self):
        verdict, note = self.module.site_verdict("MOODYZ", 404, page("MOODYZ"), "MOODYZ")
        self.assertEqual(verdict, "未取得")
        self.assertIn("404", note)

    def test_page_title_survives_nested_tags_and_whitespace(self):
        body = b"<html><head><title>\n  <span>MOODYZ</span>  \xe5\x85\xac\xe5\xbc\x8f\n</title></head>"
        self.assertEqual(self.module.page_title(body), "MOODYZ 公式")


    def test_a_shift_jis_page_is_decoded_instead_of_mangled(self):
        """老厂牌站仍有不少是 Shift_JIS。

        硬按 UTF-8 解不会报错，只会把标题变成一串 U+FFFD，然后「标题里没有厂牌名」
        这条判定会把真官网误杀掉——失败是静默的，这正是它值得一个测试的原因。
        """
        title = "MOODYZ 公式サイト"
        body = f"<html><head><title>{title}</title></head></html>".encode("cp932")
        self.assertEqual(self.module.page_title(body), title)


class LoadStudioTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = Path(tempfile.mkdtemp())

    def test_studios_are_ordered_by_asset_count_and_filtered_by_minimum(self):
        db = self.tmp / "ledger.db"
        c = sqlite3.connect(db)
        c.execute("CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT, canonical_name TEXT)")
        c.execute("CREATE TABLE asset(id INTEGER PRIMARY KEY, medium TEXT)")
        c.execute("CREATE TABLE asset_entity(asset_id INTEGER, entity_id INTEGER)")
        c.executemany("INSERT INTO entity VALUES(?,?,?)",
                      [(1, "studio", "Big"), (2, "studio", "Small"), (3, "performer", "人")])
        for asset_id, entity_id in [(10, 1), (11, 1), (12, 1), (13, 2), (14, 3)]:
            c.execute("INSERT OR IGNORE INTO asset VALUES(?,?)", (asset_id, "video"))
            c.execute("INSERT INTO asset_entity VALUES(?,?)", (asset_id, entity_id))
        c.commit()

        connection = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            self.assertEqual([r["studio"] for r in self.module.load_studios(connection, 1)],
                             ["Big", "Small"])
            self.assertEqual([r["studio"] for r in self.module.load_studios(connection, 3)],
                             ["Big"])
        finally:
            connection.close()
            c.close()


if __name__ == "__main__":
    unittest.main()
