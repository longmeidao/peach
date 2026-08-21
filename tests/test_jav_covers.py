import csv
import importlib.util
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_jav_covers.py"
_spec = importlib.util.spec_from_file_location("fetch_jav_covers", SCRIPT)
covers = importlib.util.module_from_spec(_spec)
sys.modules["fetch_jav_covers"] = covers
_spec.loader.exec_module(covers)


def jpeg(width, height):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (128, 90, 70)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _Response:
    def __init__(self, status, body):
        self.status = status
        self.body = body


def transport_for(pages):
    """pages: URL -> (status, bytes)。未列出的 URL 返回 404。"""
    def call(request, timeout, limit):
        status, body = pages.get(request.url, (404, b""))
        return _Response(status, body)
    return call


class CodeShapeTests(unittest.TestCase):
    def test_amateur_prefix_is_stripped_as_a_second_try(self):
        # 实测：`278GYAN-017` 查不到，去掉三位厂牌前缀后的 `GYAN-017` 能查到。
        self.assertEqual(covers.code_variants("278GYAN-017"), ["278GYAN-017", "GYAN-017"])

    def test_studio_codes_have_no_second_variant(self):
        self.assertEqual(covers.code_variants("ABW-232"), ["ABW-232"])

    def test_codes_are_normalised_to_three_digits(self):
        self.assertEqual(covers.normalise_code("abw232"), "ABW-232")
        self.assertEqual(covers.normalise_code("ABW-0232"), "ABW-232")

    def test_amateur_prefix_survives_normalisation(self):
        self.assertEqual(covers.normalise_code("278gyan17"), "278GYAN-017")


class ContentIdTests(unittest.TestCase):
    def test_digits_are_padded_to_five_places(self):
        # `waaa415` 返回 404，`waaa00415` 才拿得到 2184x1468。
        self.assertIn("waaa00415", covers.cid_variants("waaa415"))

    def test_original_form_is_tried_first(self):
        self.assertEqual(covers.cid_variants("bazx00302")[0], "bazx00302")

    def test_maker_prefixed_ids_still_yield_a_bare_form(self):
        self.assertIn("abw00232", covers.cid_variants("118abw232"))

    def test_empty_content_id_yields_nothing(self):
        self.assertEqual(covers.cid_variants(""), [])


class BestCoverTests(unittest.TestCase):
    def setUp(self):
        self.avbase = "https://www.avbase.net/works/ABW-232"

    def test_largest_candidate_wins_regardless_of_host(self):
        # ABW-232 没有数字版，duga 的 1000x674 才是最优——固定优先级链会选错。
        page = (b'<img src="https://pics.dmm.co.jp/mono/movie/adult/x/xpl.jpg">'
                b'<img src="https://pic.duga.jp/unsecure/prestige/6270/noauth/jacket.jpg">'
                b'<img src="https://image.mgstage.com/images/p/pake.jpg">')
        transport = transport_for({
            self.avbase: (200, page),
            "https://pics.dmm.co.jp/mono/movie/adult/x/xpl.jpg": (200, jpeg(800, 539)),
            "https://pic.duga.jp/unsecure/prestige/6270/noauth/jacket.jpg": (200, jpeg(1000, 674)),
            "https://image.mgstage.com/images/p/pake.jpg": (200, jpeg(840, 563)),
        })
        winner, size, _ = covers.best_cover(transport, "ABW-232", 0)
        self.assertEqual((winner.source, size), ("pic.duga.jp", (1000, 674)))

    def test_constructed_hires_url_beats_the_aggregator(self):
        transport = transport_for({
            "https://r18.dev/videos/vod/movies/detail/-/dvd_id=GYAN-017/json":
                (200, b'{"content_id":"gyan00017"}'),
            "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/gyan00017/gyan00017pl.jpg":
                (200, jpeg(2184, 1464)),
            "https://www.avbase.net/works/GYAN-017":
                (200, b'<img src="https://pic.duga.jp/a/jacket.jpg">'),
            "https://pic.duga.jp/a/jacket.jpg": (200, jpeg(1000, 674)),
        })
        winner, size, _ = covers.best_cover(transport, "GYAN-017", 0)
        self.assertEqual((winner.source, size), ("awsimgsrc.dmm.co.jp", (2184, 1464)))

    def test_thumbnails_are_never_considered(self):
        page = (b'<img src="https://pic.duga.jp/a/jacket_thumb.jpg">'
                b'<img src="https://pic.duga.jp/a/jacket.jpg">')
        transport = transport_for({
            self.avbase: (200, page),
            "https://pic.duga.jp/a/jacket.jpg": (200, jpeg(1000, 674)),
            "https://pic.duga.jp/a/jacket_thumb.jpg": (200, jpeg(3000, 2000)),
        })
        winner, size, _ = covers.best_cover(transport, "ABW-232", 0)
        self.assertEqual(size, (1000, 674), "缩略图即使更大也不能入选")

    def test_undersized_images_are_rejected(self):
        transport = transport_for({
            self.avbase: (200, b'<img src="https://pic.duga.jp/a/jacket.jpg">'),
            "https://pic.duga.jp/a/jacket.jpg": (200, jpeg(147, 200)),
        })
        with self.assertRaises(covers.Unavailable):
            covers.best_cover(transport, "ABW-232", 0)

    def test_no_candidate_anywhere_is_reported_not_guessed(self):
        with self.assertRaises(covers.Unavailable):
            covers.best_cover(transport_for({}), "NOPE-999", 0)


class SettledMissTests(unittest.TestCase):
    """续跑不该把上轮已经探完的落空再探一遍——那是最贵的一类。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "cover-fetch-log.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def _log(self, rows):
        with self.log.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=covers.FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in covers.FIELDS})

    def test_a_confirmed_absence_is_not_retried(self):
        self._log([{"code": "HEYZO-1380", "result": "未取得",
                    "note": "所有渠道都没有候选"},
                   {"code": "ABW-220", "result": "未取得",
                    "note": "候选都不是可用封套"}])
        self.assertEqual(covers.settled_misses(self.log), {"HEYZO-1380", "ABW-220"})

    def test_a_transport_failure_is_always_retried(self):
        """一次超时不等于确认没有，不能靠它把番号永久踢出队列。"""
        self._log([{"code": "SSNI-001", "result": "未取得",
                    "note": "ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING]"},
                   {"code": "SSNI-002", "result": "未取得",
                    "note": "ReadTimeout: timed out"}])
        self.assertEqual(covers.settled_misses(self.log), set())

    def test_a_successful_row_is_not_treated_as_a_miss(self):
        self._log([{"code": "GYAN-017", "result": "取得", "width": "2184"}])
        self.assertEqual(covers.settled_misses(self.log), set())

    def test_missing_log_means_nothing_is_skipped(self):
        self.assertEqual(covers.settled_misses(self.log / "nope.csv"), set())

    def test_skipped_rows_are_carried_into_the_new_log(self):
        """日志是整份重写；不带上就等于把上轮判定删掉，复核页会凭空少一批。"""
        self._log([{"code": "HEYZO-1380", "result": "未取得",
                    "note": "所有渠道都没有候选"},
                   {"code": "GYAN-017", "result": "取得", "width": "2184"}])
        carried = covers.carried_rows(self.log, {"HEYZO-1380"})
        self.assertEqual([row["code"] for row in carried], ["HEYZO-1380"])
        self.assertEqual(sorted(carried[0]), sorted(covers.FIELDS))

    def test_scoped_batch_keeps_unselected_source_rows(self):
        self._log([{"code": "HEYZO-1380", "result": "未取得"},
                   {"code": "KUZU-25010", "result": "未取得"}])
        selected = {"KUZU-25010"}
        rows = [row for row in covers.logged_rows(self.log)
                if row["code"] not in selected]
        self.assertEqual([row["code"] for row in rows], ["HEYZO-1380"])


class PendingCoverTests(unittest.TestCase):
    def test_queue_can_be_scoped_to_pikpak(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "ledger.db"
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TABLE asset(code TEXT, medium TEXT, location TEXT)"
            )
            connection.executemany(
                "INSERT INTO asset(code,medium,location) VALUES(?,?,?)",
                [
                    ("ABW-232", "video", "pikpak"),
                    ("SSNI-001", "video", "115"),
                    ("RAIKUN325", "video", "pikpak"),
                ],
            )
            connection.commit()
            connection.close()

            self.assertEqual(
                covers.pending(database, root / "covers", True, "pikpak"),
                ["ABW-232"],
            )


if __name__ == "__main__":
    unittest.main()
