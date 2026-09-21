"""FC2 商品页与 fc2cmadb 镜像页的解析。"""
import json
import unittest

from peach.metadata_fc2 import (MIRROR_SOURCE, SOURCE, STUDIO, article_url, canonical_code,
                                mirror_url, parse_article, parse_mirror, runtime_minutes,
                                video_id)

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


def mirror_page(video="3189161", title="【無】コスプレシリーズ", image=COVER,
                slug="rina_vlog", seller="梨奈の射精動画＠個人撮影",
                release="2023-02-19", duration="46:06", tags=("ハメ撮り", "フェラ")):
    """fc2cmadb 是 Laravel + Inertia，整棵 props 树放在一个 script 里，正文是空壳。"""
    props = {"props": {"appName": "FC2CMADB", "auth": {"user": None},
                       "article": {"id": 364910, "video_id": int(video), "title": title,
                                   "release_date": release, "duration": duration,
                                   "image_url": image,
                                   "writer": {"id": 1818, "slug": slug, "name": seller},
                                   "tags": [{"name": tag} for tag in tags]}}}
    return (f'<script type="application/json">{json.dumps(props, ensure_ascii=False)}</script>'
            '<div id="app"></div>')


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
        self.assertEqual(found["actresses"], [])

    def test_the_mirror_cover_points_at_the_file_itself(self):
        # 镜像有时给的是缩放服务的地址。w276 只有 276 像素宽，连封面的最低宽度都过不了，
        # 而它后半截就是原件地址（实测同一个文件 2350×2352）。
        wrapped = "https://contents-thumbnail2.fc2.com/w276/" + COVER.removeprefix("https://")
        found = parse_mirror(mirror_page(image=wrapped), "FC2-PPV-3189161")
        self.assertEqual(found["cover_url"], COVER)
        self.assertEqual(found["cover_urls"], [COVER])

    def test_another_products_mirror_page_is_not_this_ones_data(self):
        self.assertIsNone(parse_mirror(mirror_page(video="4364209"), "FC2-PPV-3189161"))
        self.assertIsNone(parse_mirror("<div id='app'></div>", "FC2-PPV-3189161"))

    def test_the_two_pages_hand_back_the_same_shape(self):
        # 两处的资料落进同一条候选流水线，字段少一个就是复核卡上少一格。
        self.assertEqual(sorted(parse_article(shop_page(), "FC2-PPV-4364209")),
                         sorted(parse_mirror(mirror_page(), "FC2-PPV-3189161")))
        self.assertEqual((SOURCE, MIRROR_SOURCE), ("fc2", "fc2cmadb"))


if __name__ == "__main__":
    unittest.main()
