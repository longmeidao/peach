"""FC2 商品页与 fc2cmadb 镜像页的解析。"""
import json
import unittest

from peach.metadata_fc2 import (ARCHIVE_SOURCE, MIRROR_COMPONENT, MIRROR_SOURCE, SOURCE, STUDIO,
                                archive_links, archive_search_url, article_url, canonical_code,
                                mirror_partial_headers, mirror_url, parse_archive, parse_article,
                                parse_mirror, parse_mirror_actresses, runtime_minutes, video_id)

#: 站上那份前端资源的指纹，2026-09-22 实测形态。
MIRROR_VERSION = "fcb3b524d4c7f8f3d2c38e437b35b7a9"

COVER = "https://storage92000.contents.fc2.com/file/261/26076760/1711813737.76.jpg"
TITLE = "みお(19)可愛い巨乳JDの初アナル貫通動画"


def shop_page(video="4364209", title=TITLE, image=COVER, slug="otonakamenz",
              seller="大人仮面Z", sold="2024/03/31", runtime="41:50",
              tags=("おっぱい", "お尻", "素人")):
    """商品页里解析用得上的那几块，标记与站上一致。"""
    product = {"@type": "Product", "@id": f"article:{video}", "sku": video, "name": title,
               "description": "本編と別アングルの2本立て。",
               "image": {"url": image, "@type": "ImageObject"},
               "brand": {"name": None, "url": f"https://adult.contents.fc2.com/users/{slug}/",
                         "@type": "Brand"}}
    links = "".join(f'<a class="tag tagTag" href="/search/?tag=x">{tag}</a>' for tag in tags)
    return (
        '<script type="application/ld+json">{"@type": "BreadcrumbList"}</script>'
        f'<script type="application/ld+json">{json.dumps(product, ensure_ascii=False)}</script>'
        f'<div class="items_article_headerInfo"><h3>{title}</h3>'
        f'<a href="https://adult.contents.fc2.com/users/{slug}/">{seller}</a></div>'
        f'<p class="items_article_info">{runtime}</p>'
        f'<div class="items_article_Releasedate"><p>販売日 : {sold}</p></div>'
        f'<section class="items_article_TagArea"><h3>商品タグ</h3>{links}</section>'
    )


def gone_page():
    """下架后站上仍回 200，只是正文里那份 Product 不见了。"""
    return ('<script type="application/ld+json">{"@type": "BreadcrumbList"}</script>'
            '<div class="items_notfound"><h3>見つかりませんでした</h3></div>')


ARCHIVE_LINK = "/926949-FC2-PPV-4137487-Gカップ・脅威-マジ凄いです！脅威のパイパーGカップグラマラス!-pn.html"
ARCHIVE_TITLE = "Gカップ・脅威 マジ凄いです！脅威のパイパーGカップグラマラス!"
ARCHIVE_PICTURES = "https://img.javstore.net/images/2023/12/26/"


def search_page(video="4137487", picture=True, reposted=False):
    """搜索结果。侧栏的本周热门与归档菜单用的是同一种地址形状，所以它们也在这一页里。

    第二条那部没有图，只有标题链接——站上实测一半的结果是这样（`1863914`、`2110084`）。
    `reposted` 是同一个商品的第二条：不同转存者各发一次，文章号、番号写法和标题都不同。
    """
    heading = f"FC2-PPV-{video} {ARCHIVE_TITLE}"
    thumb = (f'<img src="{ARCHIVE_PICTURES}{video}ps.jpg" alt="{heading}" loading="lazy">'
             if picture else "")
    repost = (f'<li><a href="/800025-fc2ppv-{video}-離婚の後遺症で性欲が止まらない変態女-pn.html" '
              f'title="FC2PPV {video} 離婚の後遺症">转存的那一条</a></li>' if reposted else "")
    return (
        '<ul><li><a href="/1000-featured-articles-cn.html">Featured</a></li>'
        '<li><a href="/4-av-censored-cn.html">AV Censored</a></li></ul>'
        '<div class="news_1n"><ul><li>'
        f'<a href="/926949-FC2-PPV-{video}-Gカップ・脅威-マジ凄いです！脅威のパイパーGカップグラマラス!-pn.html" '
        f'title="{heading}">{thumb}</a>'
        '</li><li>'
        '<a href="/735702-fc2-ppv-1863914-10代美少女、圧倒的透明感のしほちゃん。-pn.html" '
        'title="FC2 PPV 1863914 10代美少女、圧倒的透明感のしほちゃん。">另一部</a>'
        f"</li>{repost}</ul></div>"
    )


def archive_page(video="4137487", title=None, large="{root}{video}pl.jpg",
                 small="{root}{video}ps.jpg", tags="ハメ撮り｜素人｜爆乳", release="2023/11/21",
                 runtime="50:03"):
    """作品页。封面在两个图位上，标签、日期、时长在正文那块资料里，转存者可填可不填。

    `<head>` 里那条 `description` 照站上的样子写：它把同一段话截断成 `…｜S級...` 塞进
    `content`，整页搜「标签：」会先命中它。余下几段是转载来的网盘链接，一概不取。
    """
    heading = title if title is not None else f"FC2-PPV-{video} {ARCHIVE_TITLE}"
    link = ARCHIVE_LINK if video == "4137487" else f"/926949-FC2-PPV-{video}-x-pn.html"
    slots = []
    if large:
        slots.append('<div class="fisrst_sc">'
                     f'<img src="{large.format(root=ARCHIVE_PICTURES, video=video)}" '
                     f'alt="{heading}" /></div>')
    if small:
        slots.append(f'<img itemprop="image" src="{small.format(root=ARCHIVE_PICTURES, video=video)}"'
                     f' alt="{heading}">')
    rows = "".join(f"{label}：{value} <br class='a5555' />" for label, value in
                   (("标签", tags), ("日期", release), ("时长", runtime)) if value)
    return (
        '<head><meta name="description" content="商品名称：FC2-PPV-'
        f'{video} {ARCHIVE_TITLE} 标签：ハメ撮り｜素人｜S級..." /></head>'
        f'<div class="menudd"><h1><a href="{link}" title="{heading}">{heading}</a></h1></div>'
        f'<div class="news"><div class="first_des">{heading}</div>'
        + "".join(slots)
        + f"商品名称：{heading} <br class='a5555' />{rows}"
        # 多帧拼成的长条预览，正文里标着 Preview，不是封面。
        f'Original version: <a href="{ARCHIVE_PICTURES}ARCHIVE-FC2PPV-{video}_s.jpg">CLICK HERE!</a>'
        f'<img src="{ARCHIVE_PICTURES}fc2ppv-{video}_s.jpg" alt="{heading}" />'
        '<div class="downloads">https://rapidgator.net/file/deadbeef/x.mp4.html</div></div>'
    )


def mirror_page(video="3189161", title="【無】コスプレシリーズ", image=COVER,
                slug="rina_vlog", seller="梨奈の射精動画＠個人撮影",
                release="2023-02-19", duration="46:06", tags=("ハメ撮り", "フェラ"),
                component=MIRROR_COMPONENT, version=MIRROR_VERSION):
    """fc2cmadb 是 Laravel + Inertia，整棵 props 树放在一个 script 里，正文是空壳。"""
    page = {"component": component, "version": version, "url": f"/articles/{video}",
            "props": {"appName": "FC2CMADB", "auth": {"user": None},
                      "article": {"id": 364910, "video_id": int(video), "title": title,
                                  "release_date": release, "duration": duration,
                                  "image_url": image,
                                  "writer": {"id": 1818, "slug": slug, "name": seller},
                                  "tags": [{"name": tag} for tag in tags]}}}
    return (f'<script data-page="app" type="application/json">'
            f'{json.dumps(page, ensure_ascii=False)}</script><div id="app"></div>')


def mirror_actresses(*named):
    """点名 `actresses` 那一跳回来的东西：整份 Inertia 响应，props 里只剩要的那一栏。"""
    listed = [{"id": 3667 + at, "name": name, "description": None,
               "alias_name": "ののみやすず 逢坂りの きたのあや", "redirect_url": None,
               "pivot": {"article_id": 521612, "actress_id": 3667 + at}}
              for at, name in enumerate(named)]
    return json.dumps({"component": MIRROR_COMPONENT, "version": MIRROR_VERSION,
                       "url": "/articles/3189161",
                       "props": {"errors": {}, "actresses": listed}}, ensure_ascii=False)


class Fc2CodeTests(unittest.TestCase):
    def test_a_ledger_code_becomes_the_shop_number_in_every_writing_it_wears(self):
        for code in ("FC2-PPV-4364209", "FC2PPV-4364209", "fc2_ppv_4364209",
                     "FC2 PPV 4364209", "FC2-4364209"):
            self.assertEqual(video_id(code), "4364209", code)
        self.assertEqual(canonical_code("4364209"), "FC2-PPV-4364209")
        self.assertEqual(article_url("FC2PPV-4364209"),
                         "https://adult.contents.fc2.com/article/4364209/")
        self.assertEqual(mirror_url("FC2PPV-4364209"), "https://fc2cmadb.com/articles/4364209")

    def test_a_collection_part_asks_nowhere(self):
        # `FC2-PPV-3312576-1` 是 21 段合集里的一段，两个站都只有整份合集那一页。
        # 认出商品号就意味着把合集封面套给每一段，屏幕上是 21 个内容顶着同一张图。
        for code in ("FC2-PPV-3312576-1", "FC2-PPV-3312576_4", "", "ABW-358"):
            self.assertEqual(video_id(code), "", code)
            self.assertEqual(article_url(code), "", code)
            self.assertEqual(mirror_url(code), "", code)

    def test_both_runtime_writings_read_as_minutes(self):
        self.assertEqual(runtime_minutes("41:50"), 41.83)
        self.assertEqual(runtime_minutes("1:23:45"), 83.75)
        self.assertIsNone(runtime_minutes(""))
        self.assertIsNone(runtime_minutes("収録時間 41:50"))


class Fc2ShopPageTests(unittest.TestCase):
    def test_the_shop_page_gives_every_field_the_review_card_shows(self):
        found = parse_article(shop_page(), "FC2-PPV-4364209")
        self.assertEqual(found["id"], "FC2-PPV-4364209")
        self.assertEqual(found["content_id"], "4364209")
        self.assertEqual(found["source_url"], "https://adult.contents.fc2.com/article/4364209/")
        self.assertEqual(found["title"], TITLE)
        self.assertEqual(found["release_date"], "2024-03-31")
        self.assertEqual(found["runtime"], 41.83)
        self.assertEqual(found["maker"], STUDIO)
        self.assertEqual(found["label"], "大人仮面Z")
        self.assertEqual(found["seller_url"], "https://adult.contents.fc2.com/users/otonakamenz/")
        self.assertEqual(found["genres"], ["おっぱい", "お尻", "素人"])
        self.assertEqual(found["cover_url"], COVER)
        self.assertEqual(found["cover_urls"], [COVER])

    def test_the_shop_page_names_no_performers(self):
        # 标题里那个 `みお(19)` 是卖家自己写的宣传语，没有第二处可以印证；FC2 的演员
        # 线索在 fc2cmadb 的评论区，走 `scripts/fetch_fc2_metadata.py`。
        self.assertEqual(parse_article(shop_page(), "FC2-PPV-4364209")["actresses"], [])

    def test_another_products_page_is_not_this_ones_data(self):
        # 站上的商品号会被复用给别的投稿，不核 sku 就把另一部片的资料写到这个番号头上。
        self.assertIsNone(parse_article(shop_page(video="4470851"), "FC2-PPV-4364209"))

    def test_a_delisted_product_reads_as_absent_not_as_a_broken_page(self):
        self.assertIsNone(parse_article(gone_page(), "FC2-PPV-4364209"))

    def test_a_seller_without_a_name_keeps_the_page_that_identifies_it(self):
        page = shop_page(seller="").replace(
            '<a href="https://adult.contents.fc2.com/users/otonakamenz/"></a>', "")
        found = parse_article(page, "FC2-PPV-4364209")
        self.assertEqual(found["label"], "https://adult.contents.fc2.com/users/otonakamenz/")


class Fc2MirrorPageTests(unittest.TestCase):
    def test_the_mirror_carries_what_the_shop_has_dropped(self):
        found = parse_mirror(mirror_page(), "FC2-PPV-3189161")
        self.assertEqual(found["id"], "FC2-PPV-3189161")
        self.assertEqual(found["source_url"], "https://fc2cmadb.com/articles/3189161")
        self.assertEqual(found["title"], "【無】コスプレシリーズ")
        self.assertEqual(found["release_date"], "2023-02-19")
        self.assertEqual(found["runtime"], 46.1)
        self.assertEqual(found["maker"], STUDIO)
        self.assertEqual(found["label"], "梨奈の射精動画＠個人撮影")
        self.assertEqual(found["seller_url"], "https://adult.contents.fc2.com/users/rina_vlog/")
        self.assertEqual(found["genres"], ["ハメ撮り", "フェラ"])

    def test_the_named_women_come_from_the_second_ask_not_from_this_page(self):
        # 女优是这一页的延迟 prop：首屏那份 HTML 里一个人也没有，点名要过才有。
        self.assertEqual(parse_mirror(mirror_page(), "FC2-PPV-3189161")["actresses"], [])
        found = parse_mirror(mirror_page(), "FC2-PPV-3189161",
                             actresses=parse_mirror_actresses(mirror_actresses("野々宮すず")))
        self.assertEqual(found["actresses"], ["野々宮すず"])

    def test_the_second_ask_names_this_page_and_only_the_column_it_wants(self):
        headers = mirror_partial_headers(mirror_page())
        self.assertEqual(headers["X-Inertia-Version"], MIRROR_VERSION)
        self.assertEqual(headers["X-Inertia-Partial-Component"], MIRROR_COMPONENT)
        self.assertEqual(headers["X-Inertia-Partial-Data"], "actresses")

    def test_a_page_that_is_not_a_product_page_is_never_asked_a_second_time(self):
        # 站上没有的商品回的是错误页，它照样带着版本号，问下去只会白花一趟配额。
        self.assertEqual(mirror_partial_headers(mirror_page(component="Error")), {})
        self.assertEqual(mirror_partial_headers(mirror_page(version="")), {})
        self.assertEqual(mirror_partial_headers("<div id='app'></div>"), {})

    def test_the_stage_names_a_woman_has_worn_are_not_more_women(self):
        # `alias_name` 那一串是同一个人的曾用名，一位女优挂着十几个。
        self.assertEqual(parse_mirror_actresses(mirror_actresses("野々宮すず", "ゆうか")),
                         ["野々宮すず", "ゆうか"])
        self.assertEqual(parse_mirror_actresses(mirror_actresses()), [])
        self.assertEqual(parse_mirror_actresses("<html>429</html>"), [])

    def test_the_mirror_cover_points_at_the_file_itself(self):
        # 镜像有时给的是缩放服务的地址。w276 只有 276 像素宽，连封面的最低宽度都过不了，
        # 而它后半截就是原件地址（实测同一个文件 2350×2352）。
        wrapped = "https://contents-thumbnail2.fc2.com/w276/" + COVER.removeprefix("https://")
        found = parse_mirror(mirror_page(image=wrapped), "FC2-PPV-3189161")
        self.assertEqual(found["cover_url"], COVER)
        self.assertEqual(found["cover_urls"], [COVER])

    def test_the_mirrors_own_placeholder_is_not_a_cover(self):
        # 站上没有商品图的条目挂的是镜像自己那张占位件，还是个站内相对地址。当封面交
        # 下去，抓取那侧连主机都拼不出来，报回来的是一句「来源连接未取得」。
        found = parse_mirror(mirror_page(image="/storage/images/article/no-image.jpg"),
                             "FC2-PPV-3189161")
        self.assertEqual(found["cover_url"], "")
        self.assertEqual(found["cover_urls"], [])
        self.assertEqual(found["title"], "【無】コスプレシリーズ")

    def test_another_products_mirror_page_is_not_this_ones_data(self):
        self.assertIsNone(parse_mirror(mirror_page(video="4364209"), "FC2-PPV-3189161"))
        self.assertIsNone(parse_mirror("<div id='app'></div>", "FC2-PPV-3189161"))

    def test_the_two_pages_hand_back_the_same_shape(self):
        # 两处的资料落进同一条候选流水线，字段少一个就是复核卡上少一格。
        self.assertEqual(sorted(parse_article(shop_page(), "FC2-PPV-4364209")),
                         sorted(parse_mirror(mirror_page(), "FC2-PPV-3189161")))
        self.assertEqual((SOURCE, MIRROR_SOURCE), ("fc2", "fc2cmadb"))


class JavArchiveTests(unittest.TestCase):
    def test_the_search_page_gives_up_the_link_that_carries_this_shop_number(self):
        self.assertEqual(archive_links(search_page(), "FC2-PPV-4137487"), [ARCHIVE_LINK])
        self.assertEqual(archive_links(search_page().encode(), "fc2ppv4137487"), [ARCHIVE_LINK])

    def test_a_longer_number_that_merely_starts_the_same_is_not_this_one(self):
        # 站上 `4137487` 与 `41374870` 都有；按子串比会把后者的标题和封面安到前者头上。
        self.assertEqual(archive_links(search_page(video="41374870"), "FC2-PPV-4137487"), [])
        self.assertEqual(archive_links(search_page(), "FC2-PPV-9999999"), [])
        self.assertEqual(archive_links(search_page(), "ORETD-615"), [])

    def test_one_search_page_holds_several_works_and_each_code_finds_its_own(self):
        # 一页里既有别的作品，也有侧栏的热门与归档，挑的必须是这个商品号那一条。
        self.assertTrue(archive_links(search_page(), "FC2-PPV-1863914")[0].startswith("/735702-"))
        self.assertTrue(archive_links(search_page(), "FC2-PPV-4137487")[0].startswith("/926949-"))

    def test_every_repost_of_the_same_work_is_handed_over(self):
        # 不同转存者各发一次，图也各存各的：`1436028` 的 `/641159-` 那条是 404，
        # `/800025-` 那条有 1280×720。先后没有质量含义，所以两条都要。
        found = archive_links(search_page(reposted=True), "FC2-PPV-4137487")
        self.assertEqual([link.split("-")[0] for link in found], ["/926949", "/800025"])

    def test_the_archive_page_gives_the_title_without_the_code_in_front_of_it(self):
        found = parse_archive(archive_page(), "FC2-PPV-4137487")
        self.assertEqual(found["title"], "Gカップ・脅威 マジ凄いです！脅威のパイパーGカップグラマラス!")
        self.assertEqual((found["id"], found["content_id"], found["maker"]),
                         ("FC2-PPV-4137487", "4137487", STUDIO))
        self.assertEqual(found["source_url"], "https://javarchive.com" + ARCHIVE_LINK)
        self.assertEqual(parse_archive(archive_page(title="FC2PPV 4137487 素顔"), "FC2-PPV-4137487")["title"],
                         "素顔")

    def test_the_cover_is_read_from_its_slot_whatever_the_transferrer_named_the_file(self):
        """封面认位置不认文件名：站上三种命名都有，按名字认的话两种一张都取不到。"""
        found = parse_archive(archive_page(), "FC2-PPV-4137487")
        self.assertEqual(found["cover_url"], ARCHIVE_PICTURES + "4137487pl.jpg")
        self.assertEqual(found["cover_urls"], [ARCHIVE_PICTURES + "4137487pl.jpg",
                                               ARCHIVE_PICTURES + "4137487ps.jpg"])
        # 转存者自己起的名字：`FC2PPV-4030617.jpg`、`FC2PPV835964-2.jpg`，都不带 `pl`/`ps`。
        named = parse_archive(archive_page(large="{root}FC2PPV-{video}.jpg",
                                           small="{root}FC2PPV{video}-2.jpg"), "FC2-PPV-4137487")
        self.assertEqual(named["cover_urls"], [ARCHIVE_PICTURES + "FC2PPV-4137487.jpg",
                                               ARCHIVE_PICTURES + "FC2PPV4137487-2.jpg"])
        # 只有 schema.org 那个图位时它就是封面（实测 `835964` 的页面就少了前一个）。
        self.assertEqual(parse_archive(archive_page(large=""), "FC2-PPV-4137487")["cover_url"],
                         ARCHIVE_PICTURES + "4137487ps.jpg")
        self.assertEqual(parse_archive(archive_page(large="", small=""),
                                       "FC2-PPV-4137487")["cover_urls"], [])

    def test_the_stitched_preview_is_never_a_cover(self):
        # `_s.jpg` 是把多帧拼成的长条（实测 1024×2000），装上去就是一格拉长的马赛克。
        found = parse_archive(archive_page(large="", small=""), "FC2-PPV-4137487")
        self.assertEqual(found["cover_urls"], [])
        self.assertNotIn("_s.jpg", str(parse_archive(archive_page(), "FC2-PPV-4137487")["cover_urls"]))

    def test_the_body_block_gives_up_the_tags_the_date_and_the_runtime(self):
        """转存者填了就取。2026-09-22 实测 4 部里只有 `4030617` 这块是齐的。"""
        found = parse_archive(archive_page(), "FC2-PPV-4137487")
        self.assertEqual(found["genres"], ["ハメ撮り", "素人", "爆乳"])
        self.assertEqual(found["release_date"], "2023-11-21")
        self.assertEqual(found["runtime"], 50.05)

    def test_an_empty_block_stays_empty_instead_of_taking_the_truncated_meta_line(self):
        """`<head>` 那条 description 里有同一段话的截断版，取回来就是半截标签加一串属性。"""
        bare = parse_archive(archive_page(tags="", release="", runtime=""), "FC2-PPV-4137487")
        self.assertEqual((bare["genres"], bare["release_date"], bare["runtime"]), ([], "", None))
        # 站上没填标签时那一行写成 `--`，当成一个标签就入了库。
        self.assertEqual(parse_archive(archive_page(tags="--"), "FC2-PPV-4137487")["genres"], [])

    def test_another_products_archive_page_is_not_this_ones_data(self):
        self.assertIsNone(parse_archive(archive_page(video="4364209"), "FC2-PPV-4137487"))
        self.assertIsNone(parse_archive("<div class='news'></div>", "FC2-PPV-4137487"))
        self.assertIsNone(parse_archive(archive_page(), "ORETD-615"))

    def test_the_third_page_hands_back_the_same_shape_as_the_first_two(self):
        self.assertEqual(sorted(parse_archive(archive_page(), "FC2-PPV-4137487")),
                         sorted(parse_mirror(mirror_page(), "FC2-PPV-3189161")))
        self.assertEqual(ARCHIVE_SOURCE, "javarchive")
        self.assertEqual(archive_search_url("FC2-PPV-4137487"),
                         "https://javarchive.com/search?q=FC2-PPV-4137487")
        self.assertEqual(archive_search_url("ORETD-615"), "")


if __name__ == "__main__":
    unittest.main()
