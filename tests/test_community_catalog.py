"""社区来源的解析与封面比对：AVBase、javdb 各自的页面形状，以及「两个图源对得上才用」。"""
import io
import json
import unittest

from PIL import Image

from peach.community_catalog import IMAGE_LIMIT, avbase_work, javdb_work, verified_cover
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
AVBASE_DATA = {"props": {"pageProps": {"works": [
    {"work_id": "ABW-3580", "title": "別の作品", "products": []},
    {"prefix": "prestige", "work_id": "ABW-358", "title": TITLE, "actors": [{"name": "涼森れむ"}], "products": [
        # 收录本作的合集：标题和番号都对不上，封面和厂牌都不该带进来。
        {"source": "duga", "title": "総集編 8時間", "product_id": "prestige-9999",
         "image_url": "https://pic.duga.jp/unsecure/prestige/9999/noauth/jacket.jpg", "maker": {"name": "別メーカー"}},
        {"source": "mgs", "title": TITLE, "product_id": "ABW-358", "image_url": MGS_COVER,
         "maker": {"name": "プレステージ"}, "date": "Tue May 23 2023 09:00:00 GMT+0900"},
        {"source": "fanza", "title": TITLE, "product_id": "118abw358", "image_url": DMM_COVER,
         "maker": {"name": "プレステージ"}, "label": {"name": "ABSOLUTELY WONDERFUL"},
         "date": "Fri May 26 2023 09:00:00 GMT+0900", "iteminfo": {"director": "監督A"}},
    ]},
]}}}
AVBASE_SEARCH = "https://www.avbase.net/works?q=ABW-358"
JAVDB_SEARCH = "https://javdb.com/search?q=ABW-358&f=all"
JAVDB_DETAIL = "https://javdb.com/v/Zb7mX?locale=zh"


def avbase_page(data):
    return ('<html><script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(data, ensure_ascii=False) + "</script></html>").encode()


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

    def test_avbase_tells_an_unknown_code_apart_from_a_page_it_cannot_read(self):
        empty = {"props": {"pageProps": {"works": []}}}
        with self.assertRaises(NotFound):
            avbase_work(serve({AVBASE_SEARCH: avbase_page(empty)}), "ABW-358")
        with self.assertRaisesRegex(Unavailable, "AVBase 页面结构未识别"):
            avbase_work(serve({AVBASE_SEARCH: b"<html><title>Just a moment...</title></html>"}), "ABW-358")

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
        with self.assertRaisesRegex(Unavailable, "没有第二个图源能对上"):
            verified_cover(serve(pages), "ABW-358", works)

    def test_a_small_official_cover_counts_as_the_second_origin(self):
        works = [("javdb", {"cover_urls": [JAVDB_COVER]})]
        small = Candidate("image.mgstage.com", "https://image.mgstage.com/images/x/pf_o1_x.jpg")
        reference = (small, (300, 200), gradient(300, 200))
        candidate, _size, _data, origins = verified_cover(serve({JAVDB_COVER: gradient(900, 600)}), "ORETD-615",
                                                          works, reference=reference)
        self.assertEqual((candidate.url, origins), (JAVDB_COVER, ("javdb", "mgstage")))
        with self.assertRaisesRegex(Unavailable, "下载失败"):
            verified_cover(serve({}), "ORETD-615", works)
        with self.assertRaises(NotFound):
            verified_cover(serve({}), "ORETD-615", [("javdb", {"cover_urls": []})])


if __name__ == "__main__":
    unittest.main()
