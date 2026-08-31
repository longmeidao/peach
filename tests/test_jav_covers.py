import csv
import importlib.util
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

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


class FetchRetryTests(unittest.TestCase):
    def test_transient_transport_errors_use_the_project_backoff_window(self):
        attempts = 0

        def transport(request, timeout, limit):
            nonlocal attempts
            attempts += 1
            if attempts < 5:
                raise covers.httpx.ConnectError("temporary TLS EOF")
            return _Response(200, b"ok")

        with patch.object(covers.time, "sleep") as sleep:
            body = covers._fetch(
                transport, "https://example.test/cover.jpg",
                referer="https://example.test/", limit=100,
            )

        self.assertEqual(body, b"ok")
        self.assertEqual(attempts, 5)
        self.assertEqual(
            sleep.call_args_list,
            [call(2), call(4), call(6), call(8)],
        )

    def test_exhausted_transport_error_discards_the_poisoned_pool(self):
        class Transport:
            closed = False

            def close(self):
                self.closed = True

        original = Transport()
        replacement = Transport()
        with patch.object(covers, "HttpxTransport", return_value=replacement):
            actual = covers._renew_transport_after_error(
                original, covers.httpx.PoolTimeout("pool exhausted"),
            )

        self.assertTrue(original.closed)
        self.assertIs(actual, replacement)

    def test_confirmed_absence_keeps_the_healthy_pool(self):
        transport = object()
        actual = covers._renew_transport_after_error(
            transport, covers.Unavailable("no candidates"),
        )
        self.assertIs(actual, transport)


class HostLimitedTransportTests(unittest.TestCase):
    def test_each_host_has_an_independent_request_clock(self):
        now = [0.0]
        waits = []
        requested = []

        def clock():
            return now[0]

        def sleep(seconds):
            waits.append(seconds)
            now[0] += seconds

        def inner(request, timeout, limit):
            requested.append(request.url)
            return _Response(200, b"ok")

        transport = covers.HostLimitedTransport(
            inner, 1.5, clock=clock, sleeper=sleep,
        )
        transport(covers.HttpRequest("GET", "https://a.example/1", {}), 30, 10)
        now[0] = 0.2
        transport(covers.HttpRequest("GET", "https://b.example/1", {}), 30, 10)
        transport(covers.HttpRequest("GET", "https://a.example/2", {}), 30, 10)

        self.assertEqual(requested, [
            "https://a.example/1", "https://b.example/1", "https://a.example/2",
        ])
        self.assertEqual(waits, [1.3])


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
        # 归一化本体收进了 catalog_rules，脚本 import 它；这里验的是脚本用的
        # 确实是那一份，而不是又抄了一个同名函数。
        self.assertEqual(covers.normalise_code_key("abw232"), "ABW-232")
        self.assertEqual(covers.normalise_code_key("ABW-0232"), "ABW-232")

    def test_amateur_prefix_survives_normalisation(self):
        self.assertEqual(covers.normalise_code_key("278gyan17"), "278GYAN-017")


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

    def test_dmm_urls_expand_to_modern_and_legacy_cdn_routes(self):
        original = "https://pics.dmm.co.jp/mono/movie/adult/118abw232/118abw232pl.jpg"
        urls = {candidate.url for candidate in covers.dmm_cdn_images(original)}
        self.assertIn(
            "https://awsimgsrc.dmm.com/dig/mono/movie/118abw232/118abw232pl.jpg",
            urls,
        )
        self.assertIn(
            "https://awsimgsrc.dmm.co.jp/pics_dig/mono/movie/118abw232/118abw232pl.jpg",
            urls,
        )


class OfficialSourceTests(unittest.TestCase):
    def test_fc2_archive_cover_is_upgraded_to_the_measured_hires_rendition(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fc2-candidate-log.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "code", "result", "is_collection", "cover_url",
                ])
                writer.writeheader()
                writer.writerow({
                    "code": "FC2 3701252", "result": "取得", "is_collection": "",
                    "cover_url": "https://contents-thumbnail2.fc2.com/w276/x/cover.jpg",
                })
            candidate = covers.fc2_cover_candidates(path)["FC2-PPV-3701252"]
        self.assertEqual(candidate.url,
                         "https://contents-thumbnail2.fc2.com/w1200/x/cover.jpg")
        self.assertEqual(candidate.referer, "https://fc2cmadb.com/")

    def test_fc2_hires_candidate_skips_unrelated_jav_discovery(self):
        url = "https://contents-thumbnail2.fc2.com/w1200/x/cover.jpg"
        candidate = covers.Candidate("contents-thumbnail2.fc2.com", url,
                                     "https://fc2cmadb.com/")
        with patch.object(covers, "r18_images") as r18:
            winner, size, _body = covers.best_cover(
                transport_for({url: (200, jpeg(1200, 1361))}), "FC2-PPV-3701252", 0,
                prior_candidates=(candidate,),
            )
        r18.assert_not_called()
        self.assertEqual(winner, candidate)
        self.assertEqual(size, (1200, 1361))

    def test_cached_javinizer_cover_and_content_id_are_reused_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "ABW-232"
            folder.mkdir()
            (folder / "r18dev.json").write_text(json.dumps({
                "source": "r18dev",
                "result": {
                    "source": "r18dev",
                    "content_id": "118abw232",
                    "maker": "Prestige",
                    "cover_url": (
                        "https://pics.dmm.co.jp/mono/movie/adult/118abw232/"
                        "118abw232pl.jpg"
                    ),
                },
            }), encoding="utf-8")

            evidence = covers.cached_metadata(root, "ABW-232")

        self.assertIn("r18dev", evidence.sources)
        self.assertTrue(covers._is_prestige(evidence))
        self.assertIn(
            "https://awsimgsrc.dmm.com/dig/mono/movie/118abw232/118abw232pl.jpg",
            {candidate.url for candidate in evidence.candidates},
        )

    def test_mgstage_uses_only_the_enlarge_image(self):
        page = (b'<img src="https://image.mgstage.com/related_thumb.jpg">'
                b'<a id="EnlargeImage" '
                b'href="https://image.mgstage.com/images/prestige/abw/232/'
                b'pb_e_abw-232.jpg">open</a>')
        detail = "https://www.mgstage.com/product/product_detail/ABW-232/"
        candidates = covers.mgstage_images(
            transport_for({detail: (200, page)}), "ABW-232",
        )
        self.assertEqual(
            [candidate.url for candidate in candidates],
            ["https://image.mgstage.com/images/prestige/abw/232/pb_e_abw-232.jpg"],
        )

    def test_prestige_api_selects_exact_code_and_package_image(self):
        query = covers.urllib.parse.urlencode({
            "isEnabledQuery": "true", "searchText": "ABW-232",
            "isEnableAggregation": "false", "release": "false",
            "reservation": "false", "soldOut": "false", "from": 0,
            "aggregationTermsSize": 0, "size": 20,
        })
        search = f"{covers.PRESTIGE_SEARCH}?{query}"
        product = covers.PRESTIGE_PRODUCT.format(uuid="exact-uuid")
        image = "https://www.prestige-av.com/api/media/a/b/package.jpg"
        candidates = covers.prestige_images(transport_for({
            search: (200, json.dumps({"hits": {"hits": [
                {"_source": {"deliveryItemId": "GOOEABW-232",
                              "productUuid": "goods-uuid"}},
                {"_source": {"deliveryItemId": "ABW-232",
                              "productUuid": "exact-uuid"}},
            ]}}).encode()),
            product: (200, b'{"packageImage":{"path":"a/b/package.jpg"}}'),
        }), "ABW-232")
        self.assertEqual([candidate.url for candidate in candidates], [image])

    def test_prestige_hit_skips_the_smaller_mgstage_fallback(self):
        official = [covers.candidate_for(
            "https://www.prestige-av.com/api/media/a/package.jpg"
        )]
        with patch.object(covers, "prestige_images", return_value=official), \
                patch.object(covers, "mgstage_images") as mgstage:
            actual = covers.prestige_group_images(object(), "ABW-232")
        self.assertEqual(actual, official)
        mgstage.assert_not_called()

    def test_prestige_miss_uses_mgstage_as_the_fallback(self):
        fallback = [covers.candidate_for(
            "https://image.mgstage.com/images/prestige/abw/232/pb_e_abw-232.jpg"
        )]
        with patch.object(covers, "prestige_images", return_value=[]), \
                patch.object(covers, "mgstage_images", return_value=fallback) as mgstage:
            actual = covers.prestige_group_images(object(), "ABW-232")
        self.assertEqual(actual, fallback)
        mgstage.assert_called_once_with(unittest.mock.ANY, "ABW-232")

    def test_standard_flow_never_requests_blocked_avbase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "DASS-468"
            folder.mkdir()
            url = "https://awsimgsrc.dmm.com/dig/digital/video/dass00468/dass00468pl.jpg"
            (folder / "r18dev.json").write_text(json.dumps({
                "source": "r18dev",
                "result": {"source": "r18dev", "cover_url": url},
            }), encoding="utf-8")

            def transport(request, timeout, limit):
                self.assertNotIn("avbase", request.url)
                return _Response(200, jpeg(2184, 1468)) if request.url == url else _Response(404, b"")

            winner, size, _ = covers.best_cover(
                transport, "DASS-468", 0, metadata_root=root,
            )

        self.assertEqual((winner.url, size), (url, (2184, 1468)))


class BestCoverTests(unittest.TestCase):
    def test_known_same_size_url_is_not_probed_during_upgrade(self):
        known = "https://pics.dmm.co.jp/mono/movie/adult/x/xpl.jpg"
        larger = "https://awsimgsrc.dmm.com/dig/mono/movie/x/xpl.jpg"

        def transport(request, timeout, limit):
            if request.url == known:
                raise AssertionError("成功日志已证明同尺寸，不应重复请求")
            if request.url == larger:
                return _Response(200, jpeg(1200, 808))
            return _Response(404, b"")

        winner, size, _ = covers.best_cover(
            transport, "ABW-232", 0,
            prior_candidates=tuple(map(covers.candidate_for, (known, larger))),
            known_sizes={known: (800, 539)},
            minimum_pixels=800 * 539,
        )

        self.assertEqual((winner.url, size), (larger, (1200, 808)))

    def test_known_larger_url_is_still_probed(self):
        known = "https://pic.duga.jp/a/jacket.jpg"
        transport = transport_for({known: (200, jpeg(1000, 674))})

        winner, size, _ = covers.best_cover(
            transport, "ABW-232", 0,
            prior_candidates=(covers.candidate_for(known),),
            known_sizes={known: (1000, 674)},
            minimum_pixels=800 * 539,
        )

        self.assertEqual((winner.url, size), (known, (1000, 674)))

    def test_largest_candidate_wins_regardless_of_host(self):
        # ABW-232 没有数字版，duga 的 1000x674 才是最优——固定优先级链会选错。
        dmm = "https://pics.dmm.co.jp/mono/movie/adult/x/xpl.jpg"
        duga = "https://pic.duga.jp/unsecure/prestige/6270/noauth/jacket.jpg"
        mgs = "https://image.mgstage.com/images/p/pake.jpg"
        transport = transport_for({
            dmm: (200, jpeg(800, 539)),
            duga: (200, jpeg(1000, 674)),
            mgs: (200, jpeg(840, 563)),
        })
        winner, size, _ = covers.best_cover(
            transport, "ABW-232", 0,
            prior_candidates=tuple(map(covers.candidate_for, (dmm, duga, mgs))),
        )
        self.assertEqual((winner.source, size), ("pic.duga.jp", (1000, 674)))

    def test_constructed_hires_url_beats_the_aggregator(self):
        transport = transport_for({
            "https://r18.dev/videos/vod/movies/detail/-/dvd_id=GYAN-017/json":
                (200, b'{"content_id":"gyan00017"}'),
            "https://awsimgsrc.dmm.com/dig/digital/video/gyan00017/gyan00017pl.jpg":
                (200, jpeg(2184, 1464)),
            "https://pic.duga.jp/a/jacket.jpg": (200, jpeg(1000, 674)),
        })
        winner, size, _ = covers.best_cover(
            transport, "GYAN-017", 0,
            prior_candidates=(covers.candidate_for("https://pic.duga.jp/a/jacket.jpg"),),
        )
        self.assertEqual((winner.source, size), ("awsimgsrc.dmm.com", (2184, 1464)))

    def test_official_jacket_url_is_used_when_content_id_is_not_a_digital_path(self):
        official = "https://pics.dmm.co.jp/mono/movie/adult/118abw232/118abw232pl.jpg"
        transport = transport_for({
            "https://r18.dev/videos/vod/movies/detail/-/dvd_id=ABW-232/json":
                (200, ('{"content_id":"118abw232","images":{"jacket_image":'
                       '{"large":" ","large2":"' + official + '"}}}').encode()),
            official: (200, jpeg(800, 539)),
        })

        winner, size, _ = covers.best_cover(transport, "ABW-232", 0)

        self.assertEqual((winner.url, size), (official, (800, 539)))

    def test_thumbnails_are_never_considered(self):
        thumb = "https://pic.duga.jp/a/jacket_thumb.jpg"
        cover = "https://pic.duga.jp/a/jacket.jpg"
        transport = transport_for({
            cover: (200, jpeg(1000, 674)),
            thumb: (200, jpeg(3000, 2000)),
        })
        winner, size, _ = covers.best_cover(
            transport, "ABW-232", 0,
            prior_candidates=tuple(map(covers.candidate_for, (thumb, cover))),
        )
        self.assertEqual(size, (1000, 674), "缩略图即使更大也不能入选")

    def test_undersized_images_are_rejected(self):
        url = "https://pic.duga.jp/a/jacket.jpg"
        transport = transport_for({
            url: (200, jpeg(147, 200)),
        })
        with self.assertRaises(covers.Unavailable):
            covers.best_cover(
                transport, "ABW-232", 0,
                prior_candidates=(covers.candidate_for(url),),
            )

    def test_full_download_failure_falls_back_to_the_next_measured_cover(self):
        high = "https://one.example/high.jpg"
        low = "https://two.example/low.jpg"

        def transport(request, timeout, limit):
            if "Range" in request.headers:
                return _Response(200, jpeg(1200, 800) if request.url == high
                                 else jpeg(1000, 674))
            if request.url == high:
                return _Response(503, b"")
            return _Response(200, jpeg(1000, 674))

        winner, size, _data = covers.best_cover(
            transport, "ABW-232", 0,
            prior_candidates=tuple(map(covers.candidate_for, (high, low))),
        )

        self.assertEqual((winner.url, size), (low, (1000, 674)))

    def test_no_candidate_anywhere_is_reported_not_guessed(self):
        with self.assertRaises(covers.Unavailable):
            covers.best_cover(transport_for({}), "NOPE-999", 0)

    def test_related_work_images_never_enter_candidates(self):
        main = "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/vrkm00711/vrkm00711pl.jpg"
        related = "https://pics.dmm.co.jp/digital/video/vrkm01340/vrkm01340jp-1.jpg"
        base_transport = transport_for({
            main: (200, jpeg(2184, 1365)),
        })
        def transport(request, timeout, limit):
            if related in request.url:
                raise AssertionError("关联作品图片不得进入量尺寸请求")
            return base_transport(request, timeout, limit)
        winner, size, _ = covers.best_cover(
            transport, "VRKM-711", 0,
            prior_candidates=(covers.candidate_for(main),),
        )
        self.assertEqual((winner.url, size), (main, (2184, 1365)))


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


class RestoreLoggedSuccessTests(unittest.TestCase):
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

    def test_missing_successes_are_restored_from_the_recorded_url(self):
        url = "https://awsimgsrc.dmm.co.jp/cover.jpg"
        data = jpeg(800, 539)
        self._log([{"code": "ABP-993", "result": "取得", "width": "800",
                    "height": "539", "url": url}])
        output = Path(self.tmp.name) / "covers"

        result = covers.restore_logged_successes(
            transport_for({url: (200, data)}), self.log, output)

        self.assertEqual(result, {"logged": 1, "restored": 1, "skipped": 0,
                                  "failed": []})
        self.assertEqual((output / "ABP-993.jpg").read_bytes(), data)
        self.assertFalse((output / "ABP-993.restore.tmp").exists())

    def test_changed_upstream_image_is_refused_without_overwriting(self):
        url = "https://awsimgsrc.dmm.co.jp/cover.jpg"
        self._log([{"code": "ABP-993", "result": "取得", "width": "800",
                    "height": "539", "url": url}])
        output = Path(self.tmp.name) / "covers"

        result = covers.restore_logged_successes(
            transport_for({url: (200, jpeg(900, 600))}), self.log, output)

        self.assertEqual(result["restored"], 0)
        self.assertEqual([item["code"] for item in result["failed"]], ["ABP-993"])
        self.assertFalse((output / "ABP-993.jpg").exists())


class PendingCoverTests(unittest.TestCase):
    def test_fc2_only_queue_excludes_every_other_code_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "ledger.db"
            connection = sqlite3.connect(database)
            connection.execute("CREATE TABLE asset(code TEXT, medium TEXT, location TEXT)")
            connection.executemany(
                "INSERT INTO asset(code,medium,location) VALUES(?, 'video', '115')",
                [("ABW-232",), ("FC2-PPV-3701252",), ("RAIKUN325",)],
            )
            connection.commit(); connection.close()
            self.assertEqual(
                covers.pending(database, root / "covers", False, fc2_only=True),
                ["FC2-PPV-3701252"],
            )

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

    def test_upgrade_queue_contains_only_existing_covers_within_width_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "ledger.db"
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TABLE asset(code TEXT, medium TEXT, location TEXT)"
            )
            connection.executemany(
                "INSERT INTO asset(code,medium,location) VALUES(?,?,?)",
                [("ABW-232", "video", "115"), ("DASS-468", "video", "115"),
                 ("PPT-018", "video", "115")],
            )
            connection.commit()
            connection.close()
            output = root / "covers"
            output.mkdir()
            (output / "ABW-232.jpg").write_bytes(jpeg(800, 539))
            (output / "DASS-468.jpg").write_bytes(jpeg(2184, 1468))

            self.assertEqual(
                covers.pending(database, output, True, existing=True, max_width=800),
                ["ABW-232"],
            )

    def test_audit_uses_the_same_jav_shape_and_size_buckets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "ledger.db"
            output = root / "covers"
            log = root / "cover-fetch-log.csv"
            output.mkdir()
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TABLE asset(code TEXT, medium TEXT, location TEXT)"
            )
            connection.executemany(
                "INSERT INTO asset(code,medium,location) VALUES(?,?,?)",
                [("ABW-232", "video", "115"), ("DASS-468", "video", "115"),
                 ("FC2-PPV-1234567", "video", "115"),
                 ("RAIKUN325", "video", "115")],
            )
            connection.commit()
            connection.close()
            (output / "ABW-232.jpg").write_bytes(jpeg(800, 539))
            with log.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=covers.FIELDS)
                writer.writeheader()
                writer.writerow({"code": "ABW-232", "result": "取得"})

            report = covers.audit_state(database, output, log)

        self.assertEqual(report["jav_codes"], 2)
        self.assertEqual(report["decoded_covers"], 1)
        self.assertEqual(report["missing"], 1)
        self.assertEqual(report["width_buckets"]["le_800"], 1)


class UpgradeExistingTests(unittest.TestCase):
    def test_only_a_larger_candidate_replaces_the_cover_and_success_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            database = root / "ledger.db"
            output = root / "covers"
            log = root / "cover-fetch-log.csv"
            output.mkdir()
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TABLE asset(code TEXT, medium TEXT, location TEXT)"
            )
            connection.executemany(
                "INSERT INTO asset(code,medium,location) VALUES(?,?,?)",
                [("AAA-001", "video", "115"), ("BBB-002", "video", "115")],
            )
            connection.commit()
            connection.close()
            (output / "AAA-001.jpg").write_bytes(jpeg(800, 539))
            (output / "BBB-002.jpg").write_bytes(jpeg(800, 539))
            with log.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=covers.FIELDS)
                writer.writeheader()
                writer.writerow({"code": "AAA-001", "result": "取得",
                                 "source": "old-a", "width": 800, "height": 539})
                writer.writerow({"code": "BBB-002", "result": "取得",
                                 "source": "old-b", "width": 800, "height": 539})

            def fetched(_transport, code, _delay, **_kwargs):
                if code == "AAA-001":
                    return (covers.Candidate("new-a", "https://new/a.jpg"),
                            (1000, 674), jpeg(1000, 674))
                return (covers.Candidate("new-b", "https://new/b.jpg"),
                        (700, 470), jpeg(700, 470))

            args = covers.build_parser().parse_args([
                "--db", str(database), "--out", str(output), "--log", str(log),
                "--upgrade-existing", "--delay", "0", "--min-free", "0",
            ])
            transport = unittest.mock.Mock()
            with patch.object(covers, "HttpxTransport", return_value=transport), \
                    patch.object(covers, "best_cover", side_effect=fetched), \
                    patch.object(covers, "system_volume", return_value=root), \
                    patch.object(covers.DiskGuard, "check", return_value=100.0):
                self.assertEqual(covers.run(args), 0)

            self.assertEqual(Image.open(output / "AAA-001.jpg").size, (1000, 674))
            self.assertEqual(Image.open(output / "BBB-002.jpg").size, (800, 539))
            rows = {row["code"]: row for row in covers.logged_rows(log)}
            self.assertEqual(rows["AAA-001"]["source"], "new-a")
            self.assertEqual(rows["BBB-002"]["source"], "old-b")


if __name__ == "__main__":
    unittest.main()
