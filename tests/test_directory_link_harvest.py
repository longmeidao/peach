"""目录型社媒采集：整站翻一遍、按名字对回账本、X 账号验活；以及抽出来共用的社媒判据。"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from peach import social_links   # noqa: E402


def load_module():
    spec = importlib.util.spec_from_file_location(
        "harvest_directory_links", REPO / "scripts" / "harvest_directory_links.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 按 2026-09-02 实测的 laoshi.ink actor-001 复刻：标题带三种写法，ld+json 有 sameAs，
# 「基本资料」是 <span>标签</span><strong>值</strong>，别名可能是占位词「待补充」。
SITEMAP = """<?xml version="1.0"?><urlset>
<url><loc>https://laoshi.ink/actresses/actor-075.html</loc></url>
<url><loc>https://laoshi.ink/actresses/actor-001.html</loc></url>
<url><loc>https://laoshi.ink/korean/actor-003.html</loc></url>
<url><loc>https://laoshi.ink/actresses/actor-001.html</loc></url>
</urlset>"""

LAOSHI_PAGE = """<html><head>
<title>波多野结衣（波多野結衣 / Yui Hatano）｜日本女优资料与职业履历 - 老师图鉴</title>
<script type="application/ld+json">{"@context": "https://schema.org", "@graph": [{"@type": "Person",
 "name": "波多野结衣", "sameAs": ["https://x.com/hatano_yui"]}]}</script>
</head><body>
<a href="/actresses/index.html">返回</a>
<a href="https://cdn.jsdelivr.net/npm/x.js">脚本</a>
<div class="spot-fact-table">
 <div><span>中文名</span><strong>波多野结衣</strong></div>
 <div><span>日文名</span><strong>波多野結衣</strong></div>
 <div><span>罗马音</span><strong>Yui Hatano</strong></div>
 <div><span>别名</span><strong>待补充</strong></div>
 <div><span>公开主页</span><strong>X / Twitter</strong></div>
</div>
<a href="https://x.com/hatano_yui" target="_blank">X</a>
<a href="https://x.com/intent/follow?screen_name=hatano_yui">关注</a>
</body></html>"""

LAOSHI_TWO_NAMES = """<html><head><title>西田カリナ（Karina Nishida）｜资料 - 老师图鉴</title></head>
<body><div><span>别名</span><strong>西田卡莉娜、にしだカリナ</strong></div></body></html>"""

# 按 2026-09-02 实测的 bstar-pro.com 复刻：列表页要先过年龄门；页脚有写坏的相对路径。
BSTAR_GATE = '<form method="post"><input type="radio" name="age_check" value="yes"></form>'
BSTAR_LIST = """<ul>
 <li><a href="model.html?mid=355" class="model_img_hover"><img alt="瀬戸環奈">
   <span class="infoDate">瀬戸環奈</span><span>Kanna Seto</span></a></li>
 <li><a href="model.html?mid=360"><img alt="架空同名"><span>架空同名</span></a></li>
 <li><a href="model.html?mid=355">重复</a></li>
</ul>
<a href="https://x.com/bstar_pro/">X</a><a href="https://www.instagram.com/bstar_pro_">IG</a>"""
BSTAR_MODEL = """<ul class="sns_list">
 <li><a href="https://x.com/kanna_seto0510"></a></li>
 <li><a href="https://x.com/setokan_sub"></a></li>
 <li><a href="https://www.instagram.com/setokanna_/"></a></li>
 <li><a href="https://www.youtube.com/@setokan.channel"></a></li>
</ul>
<a href="https://s1s1s1.com/actress/detail/849776">S1</a>
<a href="https://x.com/bstar_pro/">事务所</a>
<a href="/https://www.instagram.com/bstar_pro_">写坏的</a>"""

X_ALIVE = """<html><head><meta content="瀬戸環奈 (@kanna_seto0510) / X" property="og:title">
<meta property="og:image" content="https://pbs.twimg.com/profile_images/1/abc_200x200.jpg"></head></html>"""
X_SUSPENDED = """<html><head><meta property="og:title" content="X"><meta property="og:image"
 content="https://abs.twimg.com/responsive-web/client-web/icon-ios.png"></head></html>"""
X_SHELL = "<html><head><title>X</title></head><body><div id='react-root'></div></body></html>"


class FakeSite:
    """按 URL 查字典的取页器；模仿年龄门：POST 过之前 bstar 页面一律给门。"""

    def __init__(self, pages, gated=False, HttpStatusError=RuntimeError):
        self.pages, self.gated, self.opened = pages, gated, False
        self.posts = []
        self.fetched = self.cached = 0
        self.error = HttpStatusError

    def get(self, url, refresh=False):
        if self.gated and "bstar-pro.com" in url and not self.opened:
            return BSTAR_GATE
        if url not in self.pages:
            raise self.error(404)
        return self.pages[url]

    def request(self, method, url, body=None, headers=None):
        self.posts.append((method, url, body))
        if body and b"age_check=yes" in body:
            self.opened = True
        return ""

    def close(self):
        pass


PERFORMERS = [
    {"entity_id": 1, "name": "波多野结衣", "chain": ["波多野結衣", "波多野结衣"]},
    {"entity_id": 2, "name": "濑户环奈", "chain": ["瀬戸環奈", "濑户环奈"]},
    {"entity_id": 3, "name": "架空同名", "chain": ["架空同名"]},
    {"entity_id": 4, "name": "另一位同名", "chain": ["架空同名", "另一位同名"]},
]


class SharedJudgementTests(unittest.TestCase):
    """`peach.social_links` 是三个采集器共用的判据，行为定在这里。"""

    def test_handle_folds_case_and_skips_platform_prefixes(self):
        """`@Yua_Mikami` 和 `@yua_mikami` 是同一个人；YouTube 的 channel/ 只是路径前缀。"""
        self.assertEqual(social_links.handle("https://x.com/Yua_Mikami"), "yua_mikami")
        self.assertEqual(social_links.handle("https://www.youtube.com/channel/UCabc"), "ucabc")
        self.assertEqual(social_links.handle("https://www.youtube.com/@setokan.channel"),
                         "setokan.channel")

    def test_platform_function_pages_are_not_accounts(self):
        """`x.com/intent/follow?…` 和 `instagram.com/p/…` 谁都能挂，不是任何人的账号。"""
        self.assertEqual(social_links.handle("https://x.com/intent/follow?screen_name=a"), "")
        self.assertEqual(social_links.handle("https://www.instagram.com/p/Cxyz/"), "")

    def test_classify_labels_youtube_by_channel_name_not_by_prefix(self):
        """`@名字` 进标签；`channel/UC…` 那串是频道 ID，写进标签只是一行乱码。"""
        self.assertEqual(social_links.classify("https://www.youtube.com/@setokan.channel"),
                         ("social", "YouTube @setokan.channel"))
        self.assertEqual(social_links.classify("https://www.youtube.com/channel/UC78MKlRFJzLXiWlXcP7o1BQ"),
                         ("social", "YouTube"))
        self.assertEqual(social_links.classify("https://twitter.com/alice_710_"),
                         ("social", "X @alice_710_"))

    def test_canonical_url_only_renames_the_same_site(self):
        """twitter.com 是 x.com 的旧名，路径原样搬；别的站原样返回。"""
        self.assertEqual(social_links.canonical_url("http://twitter.com/A_b?x=1"),
                         "https://x.com/A_b?x=1")
        self.assertEqual(social_links.canonical_url("https://www.instagram.com/a/"),
                         "https://www.instagram.com/a/")

    def test_name_key_ignores_width_spacing_and_case(self):
        self.assertEqual(social_links.name_key("Yua　Mikami"), social_links.name_key("yua mikami"))
        self.assertEqual(social_links.name_key("三上 悠亜"), social_links.name_key("三上悠亜"))

    def test_x_state_needs_a_profile_image_to_count_as_alive(self):
        """封停页也有 og 标签，只是 og:image 是 X 的图标不是 profile_images。

        什么 og 都没有的是 JS 壳或限流页，看不出死活，不能把限流当成封停。
        """
        self.assertEqual(social_links.x_profile_state(X_ALIVE),
                         ("alive", "瀬戸環奈 (@kanna_seto0510) / X"))
        self.assertEqual(social_links.x_profile_state(X_SUSPENDED)[0], "gone")
        self.assertEqual(social_links.x_profile_state(X_SHELL)[0], "unknown")
        self.assertEqual(social_links.x_profile_state("<p>Account suspended</p>")[0], "gone")


class LaoshiParseTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_listing_keeps_only_actress_pages_deduped_and_sorted(self):
        self.assertEqual(self.module.laoshi_listing(SITEMAP),
                         ["https://laoshi.ink/actresses/actor-001.html",
                          "https://laoshi.ink/actresses/actor-075.html"])

    def test_names_come_from_title_and_fact_table_without_placeholders(self):
        """「待补充」不是名字；标题括号里的日文名和罗马字都要拆出来。"""
        self.assertEqual(self.module.laoshi_names(LAOSHI_PAGE),
                         ["波多野结衣", "波多野結衣", "Yui Hatano"])
        self.assertEqual(self.module.laoshi_names(LAOSHI_TWO_NAMES),
                         ["西田カリナ", "Karina Nishida", "西田卡莉娜", "にしだカリナ"])

    def test_links_merge_same_as_with_anchors_and_drop_site_internal(self):
        """sameAs 与正文锚点指向同一账号时只留一条；站内与 CDN 链接不是这个人的。"""
        links = self.module.laoshi_links(LAOSHI_PAGE)
        self.assertIn("https://x.com/hatano_yui", links)
        self.assertEqual(links.count("https://x.com/hatano_yui"), 1)
        self.assertNotIn("/actresses/index.html", links)
        self.assertTrue(all("laoshi.ink" not in url for url in links))


class BstarCollectTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.pages = {self.module.BSTAR_MODELS: BSTAR_LIST,
                      "https://bstar-pro.com/model.html?mid=355": BSTAR_MODEL}

    def test_listing_pairs_each_model_page_with_its_names_once(self):
        self.assertEqual(self.module.bstar_listing(BSTAR_LIST)[0],
                         ("https://bstar-pro.com/model.html?mid=355", ["瀬戸環奈", "Kanna Seto"]))
        self.assertEqual(len(self.module.bstar_listing(BSTAR_LIST)), 2)

    def test_the_age_gate_is_passed_once_and_the_page_refetched(self):
        """models.html 先给年龄门；POST age_check=yes 之后同一会话才给列表。"""
        site = FakeSite(self.pages, gated=True, HttpStatusError=self.module.HttpStatusError)
        site_links, pages = self.module.collect_bstar(site)
        self.assertEqual([post[0] for post in site.posts], ["POST"])
        self.assertEqual({url for url in site_links},
                         {"https://x.com/bstar_pro/", "https://www.instagram.com/bstar_pro_"})
        self.assertEqual(pages[0]["names"], ["瀬戸環奈", "Kanna Seto"])
        self.assertEqual(pages[0]["official"], ("https://bstar-pro.com/model.html?mid=355", "Bstar"))

    def test_a_missing_model_page_becomes_未取得_not_a_crash(self):
        site = FakeSite(self.pages, HttpStatusError=self.module.HttpStatusError)
        _, pages = self.module.collect_bstar(site)
        self.assertTrue(pages[1]["note"].startswith("未取得：HttpStatusError: HTTP 404"), pages[1]["note"])
        self.assertEqual(pages[1]["links"], [])

    def test_the_broken_relative_footer_link_lands_on_the_own_host_and_is_dropped(self):
        links = self.module.external_links(BSTAR_MODEL, ("bstar-pro.com",), "https://bstar-pro.com/")
        self.assertNotIn("https://bstar-pro.com/https://www.instagram.com/bstar_pro_", links)
        self.assertIn("https://s1s1s1.com/actress/detail/849776", links)


class JudgeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def page(self, source, url, names, links, official=None, note=""):
        return self.module.page_record(source, url, names, links, official=official, note=note)

    def judge(self, pages, site_links=(), existing=None, urls=None):
        return self.module.judge(pages, list(site_links), PERFORMERS, existing or {}, urls or {})

    def test_a_unique_match_yields_ok_rows_for_every_new_account_on_the_page(self):
        """同一页两个 X 账号是主号加副号，都装；事务所自己的账号减掉；非社交外链不算。"""
        page = self.page("bstar", "https://bstar-pro.com/model.html?mid=355", ["瀬戸環奈", "Kanna Seto"],
                         ["https://x.com/kanna_seto0510", "https://x.com/setokan_sub",
                          "https://www.instagram.com/setokanna_/", "https://x.com/bstar_pro/",
                          "https://s1s1s1.com/actress/detail/849776"],
                         official=("https://bstar-pro.com/model.html?mid=355", "Bstar"))
        rows, stats = self.judge([page], site_links=["https://x.com/bstar_pro/"])
        self.assertEqual([row["verdict"] for row in rows], ["ok"] * 4)
        self.assertEqual({row["label"] for row in rows},
                         {"X @kanna_seto0510", "X @setokan_sub", "Instagram @setokanna_", "Bstar"})
        self.assertTrue(all(row["entity_id"] == 2 and row["name"] == "濑户环奈" for row in rows))
        self.assertIn("对上账本「濑户环奈」", rows[0]["evidence"])
        self.assertEqual(stats["ok"], 4)

    def test_the_same_account_in_the_old_host_shape_is_已有_not_a_duplicate(self):
        """账本存 `twitter.com/Hatano_Yui`，页面给 `x.com/hatano_yui`：同一个账号。"""
        existing = {1: {("X", "hatano_yui"): "https://twitter.com/Hatano_Yui"}}
        page = self.page("laoshi", "https://laoshi.ink/actresses/actor-001.html",
                         ["波多野结衣", "波多野結衣"], ["https://x.com/hatano_yui"])
        rows, _ = self.judge([page], existing=existing)
        self.assertEqual([row["verdict"] for row in rows], ["已有"])
        self.assertIn("twitter.com/Hatano_Yui", rows[0]["evidence"])

    def test_a_different_account_on_a_platform_the_ledger_already_has_is_a_conflict(self):
        """这是用户要的「交叉对比」：两处资料说的不是同一个账号，只报不装。"""
        existing = {1: {("X", "old_hatano"): "https://x.com/old_hatano"}}
        page = self.page("laoshi", "https://laoshi.ink/actresses/actor-001.html",
                         ["波多野結衣"], ["https://x.com/hatano_yui"])
        rows, stats = self.judge([page], existing=existing)
        self.assertEqual(rows[0]["verdict"], "conflict")
        self.assertIn("另有 https://x.com/old_hatano", rows[0]["evidence"])
        self.assertEqual(stats["conflict"], 1)

    def test_an_ok_from_one_source_makes_the_next_source_report_已有_or_conflict(self):
        """两个来源先后给同一个人：第二个来源看到第一个来源装进去的账号。"""
        existing = {}
        first = self.page("laoshi", "https://laoshi.ink/actresses/actor-001.html",
                          ["波多野結衣"], ["https://x.com/hatano_yui"])
        second = self.page("bstar", "https://bstar-pro.com/model.html?mid=1",
                           ["波多野結衣"], ["https://x.com/HATANO_YUI", "https://x.com/other"])
        rows, _ = self.judge([first, second], existing=existing)
        self.assertEqual([row["verdict"] for row in rows], ["ok", "已有", "conflict"])

    def test_a_name_matching_several_performers_is_需人工消歧_with_no_entity(self):
        page = self.page("laoshi", "https://laoshi.ink/actresses/actor-9.html",
                         ["架空同名"], ["https://x.com/someone"])
        rows, _ = self.judge([page])
        self.assertEqual(rows[0]["verdict"], "需人工消歧")
        self.assertEqual(rows[0]["entity_id"], "")
        self.assertIn("架空同名、另一位同名", rows[0]["evidence"])

    def test_pages_not_in_the_ledger_are_counted_but_not_written(self):
        page = self.page("laoshi", "https://laoshi.ink/actresses/actor-8.html",
                         ["不在库里的人"], ["https://x.com/nobody"])
        rows, stats = self.judge([page])
        self.assertEqual(rows, [])
        self.assertEqual(stats["页面不在账本"], 1)

    def test_a_matched_page_without_social_links_and_a_failed_page_both_leave_a_trace(self):
        """命中却没链接要写下来——否则看不出这个人在来源里是有页没号，还是根本没页。"""
        empty = self.page("laoshi", "https://laoshi.ink/actresses/actor-001.html", ["波多野結衣"], [])
        broken = self.page("laoshi", "https://laoshi.ink/actresses/actor-002.html", [], [],
                           note="未取得：HttpStatusError: HTTP 503")
        rows, stats = self.judge([empty, broken])
        self.assertEqual([(row["verdict"], row["entity_id"]) for row in rows],
                         [("未取得", 1), ("未取得", "")])
        self.assertEqual((stats["命中但无社媒"], stats["页面未取得"]), (1, 1))

    def test_the_official_page_is_已有_when_the_ledger_already_holds_it(self):
        url = "https://bstar-pro.com/model.html?mid=355"
        page = self.page("bstar", url, ["瀬戸環奈"], [], official=(url, "Bstar"))
        rows, _ = self.judge([page], urls={2: {url}})
        self.assertEqual([(row["link_kind"], row["verdict"]) for row in rows], [("official", "已有")])


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def rows(self):
        return [self.module.row(entity_id=2, link_kind="social", url="https://x.com/kanna_seto0510",
                                verdict="ok"),
                self.module.row(entity_id=2, link_kind="social", url="https://x.com/gone_one",
                                verdict="ok"),
                self.module.row(entity_id=2, link_kind="social", url="https://x.com/missing",
                                verdict="conflict", evidence="e"),
                self.module.row(entity_id=2, link_kind="social",
                                url="https://www.instagram.com/setokanna_/", verdict="ok"),
                self.module.row(entity_id=2, link_kind="official", url="https://bstar-pro.com/m",
                                verdict="ok"),
                self.module.row(entity_id=1, link_kind="social", url="https://x.com/x", verdict="已有")]

    def test_only_live_or_unverifiable_ok_rows_enter_the_install_queue(self):
        """来源可能是旧数据：封停的 X 账号不能装；Instagram 登出页看不出死活，标未验照装。

        实测不存在的账号登出页是 200 的 JS 壳，没有任何 og；只有对照账号同一时刻有 og，
        才能说它是真没了。
        """
        site = FakeSite({"https://x.com/kanna_seto0510": X_ALIVE, "https://x.com/gone_one": X_SHELL,
                         "https://x.com/old_hatano": X_SUSPENDED, "https://x.com/X": X_ALIVE},
                        HttpStatusError=self.module.HttpStatusError)
        rows = self.rows()
        existing = {2: {("X", "old_hatano"): "https://x.com/old_hatano"}}
        stats = self.module.probe_rows(rows, existing, site)
        self.assertEqual([row["alive"] for row in rows], ["活", "疑似失效", "疑似失效", "未验", "", ""])
        self.assertIn("X 显示名「瀬戸環奈 (@kanna_seto0510) / X」", rows[0]["evidence"])
        self.assertIn("X 验活：登出页无资料，对照账号正常", rows[1]["evidence"])
        self.assertIn("账本旧号 https://x.com/old_hatano：疑似失效", rows[2]["evidence"])
        self.assertEqual(dict(stats), {"活": 1, "疑似失效": 2})
        queue = self.module.installable(rows)
        self.assertEqual([row["url"] for row in queue],
                         ["https://x.com/kanna_seto0510", "https://www.instagram.com/setokanna_/",
                          "https://bstar-pro.com/m"])

    def test_a_shell_page_is_未取得_when_the_control_account_is_also_a_shell(self):
        """对照账号也没有 og 说明是我们被限流了，不能把限流记成账号封停。"""
        site = FakeSite({"https://x.com/gone_one": X_SHELL, "https://x.com/X": X_SHELL},
                        HttpStatusError=self.module.HttpStatusError)
        rows = [self.module.row(link_kind="social", url="https://x.com/gone_one", verdict="ok")]
        self.module.probe_rows(rows, {}, site)
        self.assertEqual(rows[0]["alive"], "未取得")
        self.assertIn("限流", rows[0]["evidence"])
        self.assertEqual(len(self.module.installable(rows)), 1)

    def test_a_404_is_gone_and_a_transport_error_is_unknown(self):
        """404 是账号不存在；连不上是我们的问题，不能记在账号头上。"""
        class Boom(FakeSite):
            def get(self, url, refresh=False):
                if "boom" in url:
                    raise OSError("reset")
                return super().get(url, refresh)
        site = Boom({}, HttpStatusError=self.module.HttpStatusError)
        rows = [self.module.row(link_kind="social", url="https://x.com/missing", verdict="ok"),
                self.module.row(link_kind="social", url="https://x.com/boom", verdict="ok")]
        self.module.probe_rows(rows, {}, site)
        self.assertEqual([row["alive"] for row in rows], ["疑似失效", "未取得"])
        self.assertEqual(len(self.module.installable(rows)), 1)

    def test_without_a_probe_site_every_social_row_is_marked_unverified(self):
        rows = self.rows()
        self.module.probe_rows(rows, {}, None)
        self.assertEqual([row["alive"] for row in rows], ["未验", "未验", "未验", "未验", "", ""])


class CacheTests(unittest.TestCase):
    def test_a_cached_page_is_served_without_touching_the_network(self):
        """规则改一行就得重比 686 页；没有缓存就是一次完整重抓。"""
        module = load_module()
        calls = []

        class Transport:
            def __call__(self, request, timeout, max_bytes):
                calls.append(request.url)
                return type("R", (), {"status": 200, "body": b"<p>hi</p>", "url": request.url})()

            def close(self):
                pass

        root = Path(tempfile.mkdtemp()).resolve()
        site = module.Site(root, 0, 5, transport=Transport())
        self.assertEqual(site.get("https://laoshi.ink/a"), "<p>hi</p>")
        self.assertEqual(site.get("https://laoshi.ink/a"), "<p>hi</p>")
        self.assertEqual((len(calls), site.fetched, site.cached), (1, 1, 1))
        site.get("https://laoshi.ink/a", refresh=True)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
