"""站点图标发现：把候选找齐，再按「合适」而不是只按「大」来排。

这些用例的形态全部来自 2026-09-02 对真实站点的实测，注释里写的是哪一个站逼出了这一条。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import site_icons   # noqa: E402


def urls(candidates):
    return [c.url for c in candidates]


class LinkParsingTests(unittest.TestCase):
    def test_sizes_and_relative_hrefs_are_resolved(self):
        html = ('<link rel="apple-touch-icon" sizes="180x180" href="/a/touch.png">'
                '<link rel="shortcut icon" href="favicon.ico">')
        found = site_icons.link_candidates(html, "https://example.com/")
        self.assertEqual(urls(found), ["https://example.com/a/touch.png",
                                       "https://example.com/favicon.ico"])
        self.assertEqual([c.size for c in found], [180, site_icons.DEFAULT_SIZE])

    def test_a_multi_valued_sizes_attribute_takes_the_largest(self):
        """`sizes="180x180 152x152 120x120"` 是一个文件里装多份，取最大的那份记分。"""
        html = '<link rel="apple-touch-icon" sizes="120x120 180x180" href="/t.png">'
        self.assertEqual(site_icons.link_candidates(html, "https://e.com/")[0].size, 180)

    def test_an_svg_outranks_every_bitmap_regardless_of_rel(self):
        """threads.com 的实测形态，也是这次改动的起点。

        它把 512 viewBox 的成品 SVG 声明成 `rel="icon"`，同时根目录还躺着一个
        180×180 的 `apple-touch-icon.png`。按 `rel` 分层会让位图赢，那就又回到了
        「抓到一个就不找别的了」。
        """
        html = ('<link rel="apple-touch-icon" sizes="180x180" href="/touch.png">'
                '<link rel="icon" type="image/svg+xml" href="/mark.svg">')
        ranked = site_icons.rank(site_icons.link_candidates(html, "https://t.com/"))
        self.assertEqual(ranked[0].url, "https://t.com/mark.svg")
        self.assertTrue(ranked[0].vector)

    def test_a_mask_icon_is_kept_but_ranked_last(self):
        """`rel="mask-icon"` 按规范是纯黑剪影。

        当成品图标用会得到一枚全黑方块，所以不能排前面；但它矢量、无背景、边缘干净，
        是做「品牌色圆底 + 白色字形」最好的输入，所以也不能丢。
        """
        html = ('<link rel="mask-icon" href="/pinned.svg" color="#0a0">'
                '<link rel="icon" sizes="32x32" href="/small.png">')
        ranked = site_icons.rank(site_icons.link_candidates(html, "https://e.com/"))
        self.assertEqual(urls(ranked), ["https://e.com/small.png", "https://e.com/pinned.svg"])

    def test_a_windows_tile_image_counts_as_a_designed_icon(self):
        html = '<meta name="msapplication-TileImage" content="/tile.png">'
        found = site_icons.link_candidates(html, "https://e.com/")
        self.assertEqual(urls(found), ["https://e.com/tile.png"])
        self.assertGreater(found[0].size, site_icons.MIN_DESIGNED_SIZE)

    def test_tags_without_a_recognised_rel_or_href_are_ignored(self):
        html = ('<link rel="stylesheet" href="/app.css">'
                '<link rel="icon">'
                '<link rel="preconnect" href="https://cdn.example.com">')
        self.assertEqual(site_icons.link_candidates(html, "https://e.com/"), [])


class ManifestTests(unittest.TestCase):
    def test_the_manifest_link_is_resolved(self):
        html = '<link rel="manifest" href="/site.webmanifest">'
        self.assertEqual(site_icons.manifest_url(html, "https://e.com/"),
                         "https://e.com/site.webmanifest")
        self.assertEqual(site_icons.manifest_url("<html></html>", "https://e.com/"), "")

    def test_manifest_icons_bring_in_sizes_the_html_never_declared(self):
        """PWA 站常把最大的一份只写进 manifest，HTML 里只留 apple-touch-icon。

        不读 manifest 就会白白少掉最清晰的那一枚。
        """
        payload = ('{"icons":[{"src":"/i/192.png","sizes":"192x192"},'
                   '{"src":"/i/512.png","sizes":"512x512"}]}')
        ranked = site_icons.rank(
            site_icons.manifest_candidates(payload, "https://e.com/site.webmanifest"))
        self.assertEqual(urls(ranked), ["https://e.com/i/512.png", "https://e.com/i/192.png"])

    def test_a_broken_manifest_yields_nothing_instead_of_raising(self):
        self.assertEqual(site_icons.manifest_candidates(b"<html>404</html>", "https://e.com/m"), [])
        self.assertEqual(site_icons.manifest_candidates('{"icons":"nope"}', "https://e.com/m"), [])


class RankingTests(unittest.TestCase):
    def test_a_declared_icon_beats_the_root_path_guess_at_the_same_size(self):
        """T-POWERS 是这条的证据，也是这次唯一一处回归。

        它根目录的 `/apple-touch-icon.png` 是一条带「T-POWERS」文字的横向锁定图，
        而 `<link>` 里声明的 `/assets/images/common/apple-touch-icon.png` 是紧凑标识。
        两个都是 180；按大小并列时，路径更短的字标会排到前面去。站点自己指了哪一个就听
        哪一个，根路径只是我们的猜测。
        """
        declared = site_icons.link_candidates(
            '<link rel="apple-touch-icon" sizes="180x180" '
            'href="/assets/images/common/apple-touch-icon.png">', "https://t.co/")
        ranked = site_icons.rank(declared + site_icons.conventional_candidates("https://t.co/"))
        self.assertEqual(ranked[0].url, "https://t.co/assets/images/common/apple-touch-icon.png")

    def test_the_same_url_declared_twice_keeps_the_larger_score(self):
        same = "https://e.com/icon.png"
        ranked = site_icons.rank([site_icons.Candidate(same, 16, "icon"),
                                  site_icons.Candidate(same, 180, "apple-touch")])
        self.assertEqual([(c.url, c.size) for c in ranked], [(same, 180)])

    def test_an_override_outranks_everything_the_site_declares(self):
        """FANZA：资产托在 p-smith.com，video.dmm.co.jp 自己的 `<link>` 指不到那里。"""
        ranked = site_icons.rank(
            site_icons.overrides_for("https://video.dmm.co.jp/av/content/?id=x")
            + site_icons.link_candidates(
                '<link rel="icon" type="image/svg+xml" href="/dmm.svg">', "https://video.dmm.co.jp/"))
        self.assertEqual(ranked[0].url, "https://p-smith.com/pinned/favicon_r18.ico")

    def test_fc2_takes_the_confirmed_off_site_icon_on_every_subdomain(self):
        """FC2 站上只有 16×16 的 favicon，够大的那份是横向字标——不是没找对，是没有。

        用户 2026-09-03 授权用非官网来源补 `icon` 位；这一枚仍是 FC2, Inc. 自己发布的
        App Store 图标（512×512、只有独角兽标识）。作品链接落在
        `adult.contents.fc2.com`，覆盖必须跟着子域走，否则等于没配。
        """
        for url in ["https://fc2.com/", "https://adult.contents.fc2.com/article/1/",
                    "https://video.fc2.com/"]:
            got = site_icons.overrides_for(url)
            self.assertTrue(got, url)
            self.assertIn("mzstatic.com", got[0].url)
            self.assertTrue(got[0].url.endswith("512x512bb.png"), got[0].url)
        ranked = site_icons.rank(
            site_icons.overrides_for("https://adult.contents.fc2.com/")
            + site_icons.link_candidates(
                '<link rel="shortcut icon" href="//static.fc2.com/share/image/favicon.ico">',
                "https://adult.contents.fc2.com/"))
        self.assertIn("mzstatic.com", ranked[0].url)

    def test_overrides_match_subdomains_of_the_listed_host(self):
        self.assertTrue(site_icons.overrides_for("https://www.av-event.jp/actress/1"))
        self.assertEqual(site_icons.overrides_for("https://example.com/"), [])

    def test_the_host_key_ignores_www_and_case(self):
        self.assertEqual(site_icons.host_key("https://WWW.X.com/a"), "x.com")
        self.assertEqual(site_icons.host_key("not a url"), "")


class DiscoverTests(unittest.TestCase):
    def setUp(self):
        self.asked: list[str] = []

    def fetcher(self, pages):
        def fetch(url):
            self.asked.append(url)
            got = pages.get(url)
            return None if got is None else (got, "")
        return fetch

    def test_discovery_walks_homepage_then_manifest_then_conventional(self):
        fetch = self.fetcher({
            "https://e.com": b'<link rel="manifest" href="/m.json">',
            "https://e.com/m.json": b'{"icons":[{"src":"/big.png","sizes":"512x512"}]}',
        })
        found = site_icons.discover("https://e.com/talent/a", fetch)
        self.assertEqual(urls(found), ["https://e.com/big.png",
                                       "https://e.com/apple-touch-icon.png",
                                       "https://e.com/favicon.ico"])

    def test_a_homepage_that_cannot_be_fetched_still_leaves_the_old_conventions(self):
        """首页取不到不算失败：老规矩位置照样值得一试。"""
        found = site_icons.discover("https://e.com/a", self.fetcher({}))
        self.assertEqual(urls(found), ["https://e.com/apple-touch-icon.png",
                                       "https://e.com/favicon.ico"])

    def test_a_url_without_an_origin_asks_nothing(self):
        self.assertEqual(site_icons.discover("not a url", self.fetcher({})), [])
        self.assertEqual(self.asked, [])


class BestMarkTests(unittest.TestCase):
    def test_the_first_candidate_that_renders_wins(self):
        pages = {"https://e.com": b'<link rel="icon" sizes="256x256" href="/a.png">',
                 "https://e.com/a.png": b"A",
                 "https://e.com/apple-touch-icon.png": b"B"}
        rendered = []

        def render(data, content_type=""):
            rendered.append(data)
            return None if data == b"A" else b"MARK"

        made = site_icons.best_mark("https://e.com/x", lambda u: (pages[u], "") if u in pages else None, render)
        self.assertEqual(made, b"MARK")
        self.assertEqual(rendered, [b"A", b"B"])

    def test_the_fallback_reuses_bytes_already_fetched(self):
        """一个都没做成时才回落，且用循环里存下的第一份，不重新发现一遍。

        重新发现要把首页和 manifest 再取一次；为一张回落图打两轮请求不值得。
        """
        pages = {"https://e.com": b'<link rel="icon" sizes="256x256" href="/a.png">',
                 "https://e.com/a.png": b"A"}
        asked = []

        def fetch(url):
            asked.append(url)
            return (pages[url], "") if url in pages else None

        made = site_icons.best_mark("https://e.com/x", fetch,
                                    lambda *a, **k: None,
                                    fallback=lambda data, content_type="": b"PLAIN:" + data)
        self.assertEqual(made, b"PLAIN:A")
        self.assertEqual(asked.count("https://e.com"), 1, "首页只该取一次")

    def test_a_candidate_that_cannot_be_fetched_does_not_burn_an_attempt(self):
        """404 不算「试过一个站点资产」；预算是留给真的取回来了却不合格的那些。"""
        asked = []

        def fetch(url):
            asked.append(url)
            return (b"", "") if url == "https://e.com" else None

        self.assertIsNone(site_icons.best_mark("https://e.com/x", fetch, lambda *a, **k: b"M"))
        self.assertEqual(asked, ["https://e.com", "https://e.com/apple-touch-icon.png",
                                 "https://e.com/favicon.ico"])

    def test_the_fetch_budget_stops_a_site_with_dozens_of_declared_icons(self):
        """mgstage 声明了五个 apple-touch-icon。排序已经把最可能的放前面了，
        试到第五个还不成多半是这个站没有能用的图标，继续只是白打人家的服务器。
        """
        declared = "".join(f'<link rel="icon" sizes="{n}x{n}" href="/i{n}.png">'
                           for n in (512, 256, 192, 180, 152, 144, 128))
        tried = []

        def fetch(url):
            tried.append(url)
            return (declared.encode(), "") if url == "https://e.com" else (b"x", "")

        self.assertIsNone(site_icons.best_mark("https://e.com/a", fetch, lambda *a, **k: None))
        self.assertEqual(len(tried) - 1, site_icons.MAX_FETCH)


if __name__ == "__main__":
    unittest.main()
