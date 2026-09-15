"""社区来源的解析与封面比对：AVBase、JavBus、javdb 各自的页面形状，以及图源印证与只有一个图源时的退路。"""
import io
import json
import unittest

from PIL import Image

from peach.community_catalog import IMAGE_LIMIT, avbase_work, javbus_work, javdb_work, verified_cover
from peach.http import HttpResponse
from peach.jav_cover_fetch import Candidate, NotFound, Unavailable, _fetch


def gradient(width, height, rising=True):
    """横向渐变。dHash 只看相邻像素谁亮：升序与降序是两张完全不同的图。"""
    image = Image.new("L", (width, height))
    row = [int(255 * (x if rising else width - 1 - x) / (width - 1)) for x in range(width)]
    image.putdata(row * height)
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG")
    return buffer.getvalue()


def serve(pages):
    def call(request, timeout, limit):
        found = request.url in pages
        return HttpResponse(200 if found else 404, {}, pages.get(request.url, b""), request.url)
    return call


TITLE = "涼森れむ流 HOW TO SEX！！"
DMM_COVER = "https://pics.dmm.co.jp/mono/movie/adult/118abw358/118abw358pl.jpg"
MGS_COVER = "https://image.mgstage.com/images/prestige/abw/358/pb_e_abw-358.jpg"
JAVDB_COVER = "https://c0.jdbstatic.com/covers/zb/Zb7mX.jpg"
JAVBUS_COVER = "https://www.javbus.com/pics/cover/9x2a_b.jpg"
AVBASE_DATA = {"props": {"pageProps": {"works": [
    {"work_id": "ABW-3580", "title": "別の作品", "products": []},
    {"prefix": "prestige", "work_id": "ABW-358", "title": TITLE, "actors": [{"name": "涼森れむ"}], "products": [
        # 收录本作的合集：标题和番号都对不上，封面和厂牌都不该带进来。
        {"source": "duga", "title": "総集編 8時間", "product_id": "prestige-9999",
         "image_url": "https://pic.duga.jp/unsecure/prestige/9999/noauth/jacket.jpg", "maker": {"name": "別メーカー"}},
        {"source": "mgstage", "title": TITLE, "product_id": "ABW-358", "image_url": MGS_COVER,
         "maker": {"name": "プレステージ"}, "date": "Tue May 23 2023 09:00:00 GMT+0900"},
        {"source": "fanza", "title": TITLE, "product_id": "118abw358", "image_url": DMM_COVER,
         "maker": {"name": "プレステージ"}, "label": {"name": "ABSOLUTELY WONDERFUL"},
         "date": "Fri May 26 2023 09:00:00 GMT+0900", "iteminfo": {"director": "監督A"}},
    ]},
]}}}
AVBASE_SEARCH = "https://www.avbase.net/works?q=ABW-358"
#: 形状取自 259LUXU-1514 的实测页：名寄せ的作品标题是 FANZA 合集那一件的标题，
#: 单卖本作的只有 MGStage 那条。
LUXU_TITLE = "ラグジュTV 1485 綺麗で笑顔が素敵な看護師さんが「普通のセックスでは物足りない…」と刺激を求めて登場！"
LUXU_COVER = "https://image.mgstage.com/images/luxutv/sp/259luxu/1514/pake-03_sp-259luxu-1514.jpg"
LUXU_DATA = {"props": {"pageProps": {"works": [
    {"work_id": "259LUXU-1514", "title": "FIRST CLASS ファーストクラス File/006",
     "actors": [{"name": "東條なつ"}], "products": [
         {"source": "fanza", "title": "FIRST CLASS ファーストクラス File/006", "product_id": "118sng013",
          "image_url": "https://pics.dmm.co.jp/mono/movie/adult/118sng013/118sng013pl.jpg",
          "maker": {"name": "プレステージ"}, "label": {"name": "SINGLE"},
          "series": {"name": "FIRST CLASS ファーストクラス"},
          "date": "Fri Aug 16 2024 09:00:00 GMT+0900"},
         {"source": "mgstage", "title": LUXU_TITLE, "product_id": "259LUXU-1514", "image_url": LUXU_COVER,
          "maker": {"name": "ラグジュTV"}, "series": {"name": "ラグジュTV"},
          "date": "Fri Nov 19 2021 09:00:00 GMT+0900"},
     ]},
]}}}
LUXU_SEARCH = "https://www.avbase.net/works?q=259LUXU-1514"
JAVBUS_WORK = "https://www.javbus.com/ABW-358"
JAVDB_SEARCH = "https://javdb.com/search?q=ABW-358&f=all"
JAVDB_DETAIL = "https://javdb.com/v/Zb7mX?locale=zh"


def avbase_page(data):
    return ('<html><script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(data, ensure_ascii=False) + "</script></html>").encode()


#: 形状取自厂牌回查缓存的 JavBus 作品页（PRED-340）：字段行之间有换行与缩进，演员不在字段行里。
JAVBUS_PAGE = (f"<h3>ABW-358 {TITLE}</h3>\n"
               '<a class="bigImage" href="/pics/cover/9x2a_b.jpg"><img src="/pics/cover/9x2a_b.jpg"></a>\n'
               '<p><span class="header">識別碼:</span> <span style="color:#CC0000;">ABW-358</span>\n</p>\n'
               '<p><span class="header">發行日期:</span> 2023-05-26</p>\n'
               '<p><span class="header">長度:</span> 210分鐘</p>\n'
               '<p><span class="header">製作商:</span> <a href="https://www.javbus.com/studio/x">プレステージ</a>\n'
               '            </p>            <p><span class="header">發行商:</span> '
               '<a href="https://www.javbus.com/label/y">ABSOLUTELY WONDERFUL</a>\n</p>'
               '<p class="header">類別:<span id="genre-toggle"></span></p>\n'
               '<div class="star-name"><a href="https://www.javbus.com/star/z" title="涼森れむ">涼森れむ</a></div>').encode()
JAVDB_RESULTS = ('<a href="/v/Q1" class="box" title="別"><div class="video-title"><strong>ABW-3580</strong></div></a>'
                 '<a href="/v/Zb7mX" class="box" title="涼森れむ流"><div class="video-title"><strong>ABW-358</strong> '
                 + TITLE + "</div></a>").encode()
JAVDB_PAGE = (f'<strong class="current-title">{TITLE}</strong>'
              f'<img src="{JAVDB_COVER}" class="video-cover" alt="">'
              '<div class="panel-block first-block"><strong>番號:</strong>&nbsp;<span class="value">'
              '<a href="/video_codes/ABW">ABW</a>-358</span></div>'
              '<div class="panel-block"><strong>日期:</strong>&nbsp;<span class="value">2023-05-23</span></div>'
              '<div class="panel-block"><strong>時長:</strong>&nbsp;<span class="value"> 210 分鍾</span></div>'
              '<div class="panel-block"><strong>片商:</strong>&nbsp;<span class="value">'
              '<a href="/makers/x">PRESTIGE,プレステージ</a></span></div>'
              '<div class="panel-block"><strong>演員:</strong>&nbsp;<span class="value">'
              '<a href="/actors/a" class="actor-female">涼森れむ</a><a href="/actors/b">男優</a></span></div>').encode()


class CommunityCatalogTests(unittest.TestCase):
    def test_avbase_takes_the_fanza_listing_and_skips_compilations(self):
        work = avbase_work(serve({AVBASE_SEARCH: avbase_page(AVBASE_DATA)}), "ABW-358")
        self.assertEqual((work["id"], work["title"], work["maker"], work["label"], work["director"]),
                         ("ABW-358", TITLE, "プレステージ", "ABSOLUTELY WONDERFUL", "監督A"))
        self.assertEqual(work["release_date"], "2023-05-26")
        self.assertEqual(work["actresses"], [{"japanese_name": "涼森れむ"}])
        self.assertEqual(work["cover_urls"], [DMM_COVER, MGS_COVER])
        self.assertEqual(work["source_url"], "https://www.avbase.net/works/prestige:ABW-358")

    def test_avbase_keeps_the_shop_listing_whose_product_number_is_this_code(self):
        """合集顶着作品标题时也不算本作：商品号认得出番号的那条说了算。"""
        work = avbase_work(serve({LUXU_SEARCH: avbase_page(LUXU_DATA)}), "259LUXU-1514")
        self.assertEqual((work["title"], work["maker"], work["series"], work["release_date"]),
                         (LUXU_TITLE, "ラグジュTV", "ラグジュTV", "2021-11-19"))
        self.assertEqual(work["cover_urls"], [LUXU_COVER])

    def test_avbase_tells_an_unknown_code_apart_from_a_page_it_cannot_read(self):
        empty = {"props": {"pageProps": {"works": []}}}
        with self.assertRaises(NotFound):
            avbase_work(serve({AVBASE_SEARCH: avbase_page(empty)}), "ABW-358")
        with self.assertRaisesRegex(Unavailable, "AVBase 页面结构未识别"):
            avbase_work(serve({AVBASE_SEARCH: b"<html><title>Just a moment...</title></html>"}), "ABW-358")

    def test_javbus_reads_the_work_page_fields_and_the_big_cover(self):
        work = javbus_work(serve({JAVBUS_WORK: JAVBUS_PAGE}), "ABW-358")
        self.assertEqual((work["id"], work["title"], work["maker"], work["label"], work["release_date"], work["runtime"]),
                         ("ABW-358", TITLE, "プレステージ", "ABSOLUTELY WONDERFUL", "2023-05-26", 210))
        self.assertEqual(work["actresses"], [{"japanese_name": "涼森れむ"}])
        self.assertEqual((work["source_url"], work["cover_urls"]), (JAVBUS_WORK, [JAVBUS_COVER]))

    def test_javbus_tells_a_missing_code_apart_from_its_age_gate(self):
        """番号页 404 是没有；年龄门回 200 却没有「識別碼」，要让人去贴 Cookie，而不是记成没有。"""
        with self.assertRaisesRegex(NotFound, "JavBus 没有这个番号"):
            javbus_work(serve({}), "ABW-358")
        with self.assertRaisesRegex(NotFound, "JavBus 没有这个番号"):
            javbus_work(serve({JAVBUS_WORK: JAVBUS_PAGE.replace(b">ABW-358</span>", b">ABW-359</span>")}), "ABW-358")
        with self.assertRaisesRegex(Unavailable, "贴上浏览器里的 Cookie"):
            javbus_work(serve({JAVBUS_WORK: b"<html><title>Age Verification JavBus</title></html>"}), "ABW-358")

    def test_javdb_opens_the_exact_code_and_keeps_the_japanese_maker(self):
        work = javdb_work(serve({JAVDB_SEARCH: JAVDB_RESULTS, JAVDB_DETAIL: JAVDB_PAGE}), "ABW-358")
        self.assertEqual((work["id"], work["title"], work["maker"], work["release_date"], work["runtime"]),
                         ("ABW-358", TITLE, "プレステージ", "2023-05-23", 210))
        self.assertEqual(work["actresses"], [{"japanese_name": "涼森れむ"}], "男优不进演员")
        self.assertEqual((work["source_url"], work["cover_urls"]), ("https://javdb.com/v/Zb7mX", [JAVDB_COVER]))

    def test_javdb_reports_a_missing_code_and_a_login_wall_differently(self):
        with self.assertRaises(NotFound):
            javdb_work(serve({JAVDB_SEARCH: JAVDB_RESULTS.replace(b"<strong>ABW-358</strong>", b"<strong>ABW-359</strong>")}),
                       "ABW-358")
        with self.assertRaisesRegex(Unavailable, "javdb 要求登录"):
            javdb_work(serve({JAVDB_SEARCH: "<title>登入 | JavDB</title>".encode()}), "ABW-358")

    def test_a_redirect_to_the_now_printing_placeholder_is_not_a_cover(self):
        """DMM 没图时 302 到 590×800 的「准备中」，尺寸够门槛，只能按最终地址认。"""
        placeholder = HttpResponse(200, {}, gradient(590, 800),
                                   "https://pics.dmm.co.jp/mono/movie/adult/now_printing/now_printing.jpg")
        with self.assertRaises(NotFound):
            _fetch(lambda *args: placeholder, DMM_COVER, referer="https://www.dmm.co.jp/", limit=IMAGE_LIMIT)


class VerifiedCoverTests(unittest.TestCase):
    def test_a_community_cover_needs_the_same_picture_from_a_second_origin(self):
        works = [("avbase", {"cover_urls": [DMM_COVER]}), ("javdb", {"cover_urls": [JAVDB_COVER]})]
        pages = {JAVDB_COVER: gradient(800, 534), DMM_COVER: gradient(400, 267)}
        candidate, size, _data, origins = verified_cover(serve(pages), "ABW-358", works)
        self.assertEqual((candidate.url, size, origins), (JAVDB_COVER, (800, 534), ("dmm", "javdb")))
        self.assertEqual(candidate.referer, "https://javdb.com/")
        pages[DMM_COVER] = gradient(400, 267, rising=False)
        with self.assertRaisesRegex(Unavailable, "^dmm、javdb 给的封面不是同一张图"):
            verified_cover(serve(pages), "ABW-358", works)

    def test_javbus_is_an_origin_of_its_own(self):
        works = [("javbus", {"cover_urls": [JAVBUS_COVER]}), ("javdb", {"cover_urls": [JAVDB_COVER]})]
        pages = {JAVBUS_COVER: gradient(800, 538), JAVDB_COVER: gradient(800, 534)}
        candidate, _size, _data, origins = verified_cover(serve(pages), "ABW-358", works)
        self.assertEqual((candidate.url, candidate.referer, origins),
                         (JAVBUS_COVER, "https://www.javbus.com/", ("javbus", "javdb")))

    def test_a_cover_only_one_origin_has_is_used_without_verification(self):
        """没有第二个图源可比时照样用最大那张，印证图源留空（ADR-0032）：卡着没有封面更糟。"""
        works = [("avbase", {"cover_urls": []}), ("javdb", {"cover_urls": [JAVDB_COVER]})]
        candidate, size, _data, origins = verified_cover(serve({JAVDB_COVER: gradient(800, 534)}), "IPX-060", works)
        self.assertEqual((candidate.url, size, origins), (JAVDB_COVER, (800, 534), ()))

    def test_a_small_official_cover_counts_as_the_second_origin(self):
        works = [("javdb", {"cover_urls": [JAVDB_COVER]})]
        small = Candidate("image.mgstage.com", "https://image.mgstage.com/images/x/pf_o1_x.jpg")
        reference = (small, (300, 200), gradient(300, 200))
        candidate, _size, _data, origins = verified_cover(serve({JAVDB_COVER: gradient(900, 600)}), "ORETD-615",
                                                          works, reference=reference)
        self.assertEqual((candidate.url, origins), (JAVDB_COVER, ("javdb", "mgstage")))
        with self.assertRaisesRegex(Unavailable, "下载失败"):
            verified_cover(serve({}), "ORETD-615", works, reference=reference)
        with self.assertRaisesRegex(Unavailable, "^javdb、mgstage 给的封面不是同一张图"):
            verified_cover(serve({JAVDB_COVER: gradient(900, 600, rising=False)}), "ORETD-615",
                           works, reference=reference)
        with self.assertRaisesRegex(Unavailable, "下载失败"):
            verified_cover(serve({}), "ORETD-615", works)
        with self.assertRaises(NotFound):
            verified_cover(serve({}), "ORETD-615", [("javdb", {"cover_urls": []})])


if __name__ == "__main__":
    unittest.main()
