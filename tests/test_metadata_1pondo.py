"""一本道官网作品 JSON 的解析。"""
import json
import unittest

from peach.metadata_1pondo import (PAGE_URL, SOURCE, STUDIO, detail_url, movie_id,
                                   names_this_studio, parse_details)

COVER = "https://www.1pondo.tv/moviepages/112312_478/images/str.jpg"


def details(movie="112312_478", title="裸演奏 〜第5回演奏会・ホルン〜", release="2012-11-23",
            duration=3874, series="裸演奏", actresses=("飯岡かなこ",), english=("Kanako Iioka",),
            tags=("AV女優", "スレンダー", "中出し", "720p"), thumbs=True):
    raw = {"MovieID": movie, "Title": title, "Release": release, "Duration": duration,
           "Desc": "楽器とエロスのハーモニー。", "DescEn": None,
           "Series": series, "SeriesEn": "Hadaka Enso",
           "Actor": actresses[0] if actresses else "",
           "ActressesJa": list(actresses), "ActressesEn": list(english),
           "UCNAME": list(tags), "SiteID": 2470, "Status": True,
           "MovieThumb": f"https://www.1pondo.tv/moviepages/{movie}/images/thum_b.jpg"}
    if thumbs:
        for field in ("ThumbLow", "ThumbMed", "ThumbHigh", "ThumbUltra"):
            raw[field] = f"https://www.1pondo.tv/moviepages/{movie}/images/str.jpg"
    return json.dumps(raw, ensure_ascii=False)


class OnePondoCodeTests(unittest.TestCase):
    def test_the_shop_writes_the_code_with_an_underscore(self):
        # 分隔符是片商标识，账本两种写法都有：文件名带进来的那个可能是连字号。
        self.assertEqual(movie_id("112312_478"), "112312_478")
        self.assertEqual(movie_id("092415-001"), "092415_001")
        self.assertEqual(detail_url("092415-001"),
                         "https://www.1pondo.tv/dyn/phpauto/movie_details/movie_id/092415_001.json")

    def test_codes_that_are_not_dated_ask_nowhere(self):
        # `125735_816` 是手机录像 `VID_20220818_125735_816.mp4` 剪出来的，12 月 57 日不存在。
        for code in ("ABW-358", "FC2-PPV-4364209", "n1234", "125735-816", "", None):
            self.assertEqual(movie_id(code), "", repr(code))
            self.assertEqual(detail_url(code), "", repr(code))

    def test_only_local_evidence_names_this_studio(self):
        # 一本道与カリビアンコム 的番号同形，拿另一家的番号去问，答回来的是同一天发行的
        # 另一部片。所以问不问它看本机手上的路径、文件名与账本厂牌。
        self.assertTrue(names_this_studio("B:/云下载/[JAV] [Uncensored] 1pon 112312_478/x.mp4", "", ""))
        self.assertTrue(names_this_studio("B:/MVP/1pondo-092415_159-001-FHD/x.mp4", "x.mp4", None))
        self.assertTrue(names_this_studio("", "", "一本道"))
        self.assertFalse(names_this_studio("B:/云下载/Carib-040221-001-FHD/x.mp4", "x.mp4", "カリビアンコム"))
        self.assertFalse(names_this_studio())


class OnePondoDetailTests(unittest.TestCase):
    def test_the_work_json_gives_every_field_the_review_card_shows(self):
        found = parse_details(details(), "112312_478")
        self.assertEqual(found["id"], "112312_478")
        self.assertEqual(found["content_id"], "112312_478")
        self.assertEqual(found["source_url"], PAGE_URL.format(movie_id="112312_478"))
        self.assertEqual(found["title"], "裸演奏 〜第5回演奏会・ホルン〜")
        self.assertEqual(found["release_date"], "2012-11-23")
        self.assertEqual(found["maker"], STUDIO)
        self.assertEqual(found["series"], "裸演奏")
        self.assertEqual(found["genres"], ["AV女優", "スレンダー", "中出し", "720p"])
        self.assertEqual(found["cover_url"], COVER)
        self.assertEqual(found["cover_urls"], [COVER])

    def test_the_runtime_arrives_in_seconds_and_lands_in_minutes(self):
        self.assertEqual(parse_details(details(), "112312_478")["runtime"], 64.57)
        self.assertIsNone(parse_details(details(duration=0), "112312_478")["runtime"])
        self.assertIsNone(parse_details(details(duration=None), "112312_478")["runtime"])

    def test_the_japanese_name_is_the_identity_and_the_romaji_follows_as_an_alias(self):
        found = parse_details(details(actresses=("白咲碧", "陽菜"), english=("Aoi Shirosaki", "Hina")),
                              "112312_478")
        self.assertEqual(found["actresses"],
                         [{"japanese_name": "白咲碧", "name_romaji": "Aoi Shirosaki"},
                          {"japanese_name": "陽菜", "name_romaji": "Hina"}])

    def test_a_work_with_only_the_single_actor_field_still_names_her(self):
        found = parse_details(details(actresses=("飯岡かなこ",), english=()), "112312_478")
        self.assertEqual(found["actresses"], [{"japanese_name": "飯岡かなこ", "name_romaji": ""}])

    def test_another_works_json_is_not_this_ones_data(self):
        # 番号同形的另一家片子问到这里时，官网回的作品号对不上，那份资料一个字都不能用。
        self.assertIsNone(parse_details(details(movie="092415_001"), "112312_478"))
        self.assertIsNone(parse_details("null", "112312_478"))
        self.assertIsNone(parse_details(details(), "ABW-358"))

    def test_the_cover_falls_back_to_the_list_thumb_when_the_still_is_missing(self):
        found = parse_details(details(thumbs=False), "112312_478")
        self.assertEqual(found["cover_url"],
                         "https://www.1pondo.tv/moviepages/112312_478/images/thum_b.jpg")
        self.assertEqual(SOURCE, "1pondo")


if __name__ == "__main__":
    unittest.main()
