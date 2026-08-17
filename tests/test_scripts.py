import csv
import importlib.util
import io
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from peach.migrations import upgrade
from peach.classification import is_probable_mainstream_release, is_structural_creator


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OperationalScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean_names = load_script("clean_names")
        cls.scrape_codes = load_script("scrape_codes")
        cls.find_ads = load_script("find_ads")
        cls.probe = load_script("probe")
        cls.sheets = load_script("sheets")
        cls.traffic_watch = load_script("traffic_watch")
        cls.creator_boards = load_script("creator_boards")
        cls.creator_tags = load_script("creator_tags")
        cls.creator_attributions = load_script("audit_creator_attributions")

    def test_import_has_no_filesystem_or_log_side_effect(self):
        self.assertIsNone(self.clean_names._logf)
        self.assertIsNone(self.scrape_codes._logf)

    def test_test_entrypoint_enforces_worktree_source_and_unittest(self):
        script = (ROOT / "scripts" / "test.ps1").read_text(encoding="utf-8")
        self.assertIn("rev-parse --git-common-dir", script)
        self.assertIn("$env:PYTHONPATH = $SourceRoot", script)
        self.assertIn("peach.__file__", script)
        self.assertIn("-m unittest discover", script)
        self.assertNotIn("pytest", script.lower())
        # 文档里可以「提到」裸命令来说明它为什么不可信，但绝不能让它单独出现成为一条可照抄的指令。
        # 判据因此不是黑名单，而是：凡出现该命令的行，必须在同一行指向 test.ps1。
        for relative in ("AGENTS.md", "README.md", "docs/HANDOFF.md"):
            instructions = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("scripts\\test.ps1", instructions)
            for number, line in enumerate(instructions.splitlines(), 1):
                if "unittest discover" not in line:
                    continue
                self.assertIn(
                    "test.ps1", line,
                    f"{relative}:{number} 单独出现了裸命令，读者会照抄；必须同时点明唯一入口",
                )

    def test_structural_creator_and_mainstream_release_guards(self):
        self.assertTrue(is_structural_creator("asce"))
        self.assertTrue(is_structural_creator("门槛"))
        self.assertFalse(is_structural_creator("Alice"))
        self.assertTrue(is_probable_mainstream_release(
            "The.Great.Escape.S04E09.1080p.WEB-DL.H264.AAC-AppleTor.mp4"
        ))
        self.assertFalse(is_probable_mainstream_release("S04E09-personal-video.mp4"))

    def test_creator_attribution_audit_distinguishes_evidence_and_folder_names(self):
        classify = self.creator_attributions.classify
        self.assertEqual(classify(
            r"B:\云下载\足交仙人\feet of Suzyq (1).mp4", "足交仙人"
        )[3:5], ("replace", "suzuq"))
        self.assertEqual(classify(
            r"B:\MVP\捅主任\TokyoDolls\32.mp4", "捅主任"
        )[3], "remove")
        self.assertEqual(classify(
            r"B:\创作者\捅主任\real.mp4", "捅主任"
        )[3], "review_folder_projection")
        self.assertEqual(classify(
            r"B:\MVP\TokyoDolls\32.mp4", "捅主任"
        )[3], "review_legacy_projection")

    def test_ad_candidate_scan_is_isolated_and_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER,location TEXT,path TEXT,name TEXT,"
                "size INTEGER,duration REAL,medium TEXT)"
            )
            for asset_id in range(1, 4):
                connection.execute(
                    "INSERT INTO asset VALUES(?,?,?,?,?,?,?)",
                    (
                        asset_id,
                        "local",
                        str(root / "pack" / f"promo-{asset_id}.mp4"),
                        f"promo-{asset_id}.mp4",
                        10 * 1024**2,
                        37.4,
                        "video",
                    ),
                )
            connection.commit()
            connection.close()

            plan, scanned = self.find_ads.find_candidates(db, min_group=3)
            self.assertEqual(scanned, 3)
            self.assertEqual(len(plan), 3)
            self.assertTrue(all("等长重复x3" in row["hits"] for row in plan))
            self.assertFalse((root / "ad-candidates.csv").exists())

    def test_filename_cleanup_is_conservative(self):
        propose = self.clean_names.propose
        self.assertEqual(propose("www.98T.la@sample.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.jpg"), "sample.mp4.jpg")
        self.assertEqual(propose("(3).mp4"), "(3).mp4")

    def test_media_batch_scripts_are_import_safe_and_keep_context_rules(self):
        self.assertEqual(self.probe.context_fields(1920, 1080, 180), ("速食", "横屏", "2K"))
        with tempfile.TemporaryDirectory() as tmp:
            output = self.sheets.output_path(Path(tmp), "local", "R:/media/one.mp4")
            self.assertFalse(output.exists())
            self.assertTrue(output.parent.is_dir())
        self.assertTrue(self.traffic_watch.is_direct({"chains": ["DIRECT"]}))
        self.assertFalse(self.traffic_watch.is_direct({"chains": ["Proxy", "Relay"]}))
        self.assertEqual(self.creator_boards.safe_name("A/B:C"), "A_B_C")

    def test_age_gate_is_crossed_by_the_affirmative_link_only(self):
        """AV 厂牌官网普遍先给年龄确认页，不穿过它只能拿到约 10 KB 的空壳。

        判据必须是锚文本：否定链接指向站外（实测 dasdas.jp / muku.tv 都指向 dmm.com），
        肯定链接指向站内，两者的 href 本身看不出区别。跟错就会离开厂牌域名，
        而离开域名抓到的社交账号就不再属于这个厂牌。
        """
        module = load_script("find_studio_socials")
        gate = (
            '<a href="https://dasdas.jp/top">はい（入室する）</a>'
            '<a href="https://www.dmm.com/">いいえ</a>'
        )
        self.assertEqual(
            module.affirmative_link(gate, "https://dasdas.jp/"), "https://dasdas.jp/top")
        # 只有否定链接时不得跟随，否则会走到站外。
        self.assertIsNone(module.affirmative_link(
            '<a href="https://www.dmm.com/">いいえ</a>', "https://dasdas.jp/"))
        # 肯定文案但跨域，同样不跟。
        self.assertIsNone(module.affirmative_link(
            '<a href="https://elsewhere.example/top">ENTER</a>', "https://dasdas.jp/"))
        self.assertIsNone(module.affirmative_link("<p>没有链接</p>", "https://dasdas.jp/"))

    def test_platform_paths_are_not_mistaken_for_accounts(self):
        module = load_script("find_studio_socials")
        html = ('<a href="https://twitter.com/intent/tweet">分享</a>'
                '<a href="https://x.com/dahliaofficial0">官方</a>'
                '<a href="https://twitter.com/share">share</a>')
        self.assertEqual(module.handles_in(html), {"dahliaofficial0"})

    def test_powershell_scripts_with_chinese_carry_a_utf8_bom(self):
        """没有 BOM 的 .ps1，Windows PowerShell 5.1 会按 ANSI（简中系统即 GBK）读。

        `scripts/test.ps1` 的中文 throw 消息因此被解成乱码，引号配对错乱，
        整个脚本在解析期就失败并闪退——报错行还会落在纯 ASCII 的语句上，极难定位。
        pwsh 7 默认按 UTF-8 读无 BOM 文件，所以这个故障只在 5.1 上出现。
        """
        for path in sorted((ROOT / "scripts").glob("*.ps1")):
            raw = path.read_bytes()
            if all(byte < 128 for byte in raw):
                continue
            self.assertTrue(
                raw.startswith(b"\xef\xbb\xbf"),
                f"{path.name} 含非 ASCII 却没有 UTF-8 BOM，PowerShell 5.1 会解析失败",
            )

    def test_logo_candidates_are_squared_by_padding_not_discarded(self):
        """界面按方框渲染。接近方的直接用，长条形补背景填方，只有太小的才丢。"""
        import io

        from PIL import Image

        from peach.images import PAD, REJECT, SQUARE, classify, pad_to_square

        self.assertEqual(classify(512, 512)[0], SQUARE)
        self.assertEqual(classify(600, 500)[0], SQUARE, "轻微非方图不必补")
        self.assertEqual(classify(1600, 900)[0], PAD, "16:9 补成方图，而不是丢掉")
        self.assertEqual(classify(64, 64)[0], REJECT, "短边过小，补白也救不回来")

        wide = Image.new("RGBA", (400, 100), (10, 20, 30, 255))
        buffer = io.BytesIO()
        wide.save(buffer, "PNG")
        squared = Image.open(io.BytesIO(pad_to_square(buffer.getvalue())))
        self.assertEqual(squared.size, (400, 400))
        # 补出来的边取原图四角底色，和 Logo 自身背景连成一片，不是凭空刷白。
        self.assertEqual(squared.getpixel((5, 5)), (10, 20, 30, 255))
        self.assertEqual(squared.getpixel((200, 200)), (10, 20, 30, 255))

    def test_studio_avatar_candidates_never_guess_a_handle_by_default(self):
        """猜错 handle 会产出一个「看起来很官方」的错误 Logo，和它要取代的搜索猜测同一种失败。"""
        module = load_script("fetch_studio_avatar_candidates")
        self.assertEqual(module.guess_handle("PREMIUM"), "PREMIUM")
        self.assertEqual(module.guess_handle("S1 NO.1 STYLE"), "S1NO1STYLE")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.csv"
            source.write_text("studio\nBAZOOKA\n", encoding="utf-8-sig")
            output = Path(tmp) / "out.csv"
            with mock.patch.object(sys, "argv", [
                "fetch_studio_avatar_candidates", "--input", str(source), "--output", str(output),
            ]):
                module.main()
            written = list(csv.DictReader(output.open(encoding="utf-8-sig", newline="")))
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0]["confirmation"], "no-handle")
        self.assertEqual(written[0]["accepted"], "False")
        self.assertIn("未取得", written[0]["reason"])

    def test_frame_retry_is_reserved_for_bad_color_metadata(self):
        """坏色彩元数据才重试。无条件重试会让网盘超时的文件每帧白跑两次 45 秒。"""
        sheets = self.sheets
        for stderr, expected in (
            ("[swscale] Unsupported color primaries: reserved", [False, True]),
            ("color_trc reserved is invalid", [False, True]),
            ("ffmpeg timeout", [False]),
            ("Error opening input: Input/output error", [False]),
        ):
            calls: list[bool] = []

            def fake_capture(_ffmpeg, _path, _timestamp, _destination, color_override,
                             _stderr=stderr, _calls=calls):
                _calls.append(color_override)
                return False, _stderr

            with tempfile.TemporaryDirectory() as tmp:
                with mock.patch.object(sheets, "_capture_frame", fake_capture):
                    sheets.make_sheet("ffmpeg", "R:/media/one.mp4", 100.0,
                                      Path(tmp) / "sheet.jpg", frames=1)
            self.assertEqual(calls, expected, stderr)

    def test_failed_sheet_says_whether_the_source_or_the_duration_is_wrong(self):
        """asset 12510 与 18349 都只报「失败」，一个是片源头坏、一个是账本时长记错。

        分不出来就没法决定该修片源还是修账本，所以原因必须能区分。
        """
        sheets = self.sheets

        def capture_none(_ffmpeg, _path, _timestamp, _destination, color_override):
            return False, "missing mandatory atoms, broken header"

        def capture_first_only(_ffmpeg, _path, timestamp, destination, color_override):
            # 账本时长比真实文件长时，只有最早的采样点还落在文件里。
            if timestamp > 100.0:
                return False, ""
            destination.write_bytes(b"x" * 2048)
            return True, ""

        for capture, expected in (
            (capture_none, "broken_source"),
            (capture_first_only, "duration_mismatch"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                with mock.patch.object(sheets, "_capture_frame", capture):
                    ok, reason = sheets.make_sheet(
                        "ffmpeg", "R:/media/one.mp4", 752.24, Path(tmp) / "sheet.jpg", frames=9,
                    )
            self.assertFalse(ok)
            self.assertEqual(reason, expected)

    def test_sheet_failure_reason_reaches_the_log(self):
        """原因只写在返回值里等于没写；批次日志和汇总都要能看到。"""
        sheets = self.sheets
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER PRIMARY KEY,location TEXT,path TEXT,"
                "medium TEXT,duration REAL,size INTEGER,snapshot_path TEXT)"
            )
            connection.execute(
                "INSERT INTO asset VALUES(18349,'local',?,'video',752.24,1000,NULL)",
                (str(root / "one.mp4"),),
            )
            connection.commit()
            connection.close()

            args = sheets.build_parser().parse_args([
                "--db", str(db), "--workers", "1", "--min-free", "0",
                "--output-root", str(root / "out"), "--log-dir", str(root / "log"),
            ])
            choice = type("C", (), {"path": "ffmpeg"})
            with mock.patch.object(
                sheets, "make_sheet",
                lambda *_args, **_kwargs: (False, "duration_mismatch"),
            ), mock.patch.object(sheets.FFmpegResolver, "ffmpeg", lambda _self: choice), \
                    redirect_stdout(io.StringIO()):
                sheets.run(args)

            written = "\n".join(p.read_text(encoding="utf-8")
                                for p in (root / "log").glob("sheets-*.log"))
        self.assertIn("18349", written)
        self.assertIn("duration_mismatch", written)
        self.assertIn("失败原因：duration_mismatch 1", written)

    def test_sheets_stops_mid_run_when_the_disk_gate_trips(self):
        """验证接线，不只是 DiskGuard 类本身：起跑通过、运行中触线要真的停并报非零码。"""
        sheets = self.sheets
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER PRIMARY KEY,location TEXT,path TEXT,"
                "medium TEXT,duration REAL,size INTEGER,snapshot_path TEXT)"
            )
            for asset_id in range(1, 61):
                connection.execute(
                    "INSERT INTO asset VALUES(?,?,?,?,?,?,NULL)",
                    (asset_id, "local", str(root / f"{asset_id}.mp4"), "video", 600.0, 1000),
                )
            connection.commit()
            connection.close()

            args = sheets.build_parser().parse_args([
                "--db", str(db), "--workers", "1", "--min-free", "40",
                "--disk-check-secs", "0",
                "--output-root", str(root / "out"), "--log-dir", str(root / "log"),
            ])

            roomy = type("U", (), {"free": 500 * 1024**3})
            starved = type("U", (), {"free": 1 * 1024**3})
            calls = {"n": 0}

            def shrinking_disk(_path):
                # 起跑线检查看到充裕空间；运行几步之后盘被外部吃光。
                calls["n"] += 1
                return roomy if calls["n"] <= 2 else starved

            written = []

            def fake_sheet(_ffmpeg, path, _duration, destination, _frames):
                written.append(path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"x" * 8192)
                return True, ""

            choice = type("C", (), {"path": "ffmpeg"})
            with mock.patch.object(sheets, "make_sheet", fake_sheet), \
                 mock.patch.object(sheets.FFmpegResolver, "ffmpeg", lambda _self: choice), \
                 mock.patch("peach.jobs.shutil.disk_usage", shrinking_disk), \
                 redirect_stdout(io.StringIO()):
                code = sheets.run(args)

            self.assertEqual(code, 3, "磁盘闸门中止必须体现在退出码上")
            self.assertLess(len(written), 60, "触线后不能把剩余任务跑完")
            # 已完成的部分必须已经入库，否则续跑会重复下载。
            connection = sqlite3.connect(db)
            registered = connection.execute(
                "SELECT count(*) FROM asset WHERE snapshot_path IS NOT NULL").fetchone()[0]
            connection.close()
            self.assertEqual(registered, len(written))

    def test_traffic_ceiling_can_cover_direct_sources(self):
        """115 实测走 DIRECT。计费来源若也直连，只算代理等于没有闸门。"""
        accumulate = self.traffic_watch.accumulate
        previous = {"a": (100, True, "cdn.example"), "b": (100, False, "proxy.example")}
        current = {"a": (700, True, "cdn.example"), "b": (400, False, "proxy.example")}

        counted, uncounted, hosts = accumulate(previous, current, False)
        self.assertEqual((counted, uncounted), (300, 600))
        self.assertEqual(hosts, {"proxy.example": 300})

        counted, uncounted, hosts = accumulate(previous, current, True)
        self.assertEqual((counted, uncounted), (900, 0))
        self.assertEqual(hosts, {"cdn.example": 600, "proxy.example": 300})

        # 连接被回收后重新编号会让计数倒退；倒退不能反向抵扣已用预算。
        self.assertEqual(accumulate({"a": (900, True, "h")}, {"a": (5, True, "h")}, True)[0], 0)
        self.assertFalse(self.traffic_watch.build_parser().parse_args([]).count_direct)

    def test_probe_never_records_an_unknown_duration_as_zero(self):
        """0 会同时躲过 probe 的 `duration IS NULL` 和抽帧的 `duration>2`，永久卡住。"""
        module = self.probe

        class _Empty:
            stdout = b'{"format":{},"streams":[{"width":0,"height":0}]}'

        original = module.subprocess.run
        module.subprocess.run = lambda *args, **kwargs: _Empty()
        try:
            duration, width, height, codec, fps, audio = module.probe_file("ffprobe", "x.mp4")
        finally:
            module.subprocess.run = original
        self.assertEqual(duration, -1.0)
        self.assertEqual((width, height, codec), (0, 0, None))
        self.assertEqual(module.context_fields(width, height, duration), (None, None, None))

    def test_probe_redo_separates_unprobed_from_failed(self):
        selection = self.probe.duration_selection
        self.assertEqual(selection("none"), "duration IS NULL")
        self.assertEqual(selection("zero"), "(duration IS NULL OR duration=0)")
        self.assertEqual(selection("failed"), "(duration IS NULL OR duration<0)")
        self.assertEqual(selection("all"), "(duration IS NULL OR duration<=0)")
        self.assertEqual(self.probe.build_parser().parse_args([]).redo, "none")
        self.assertEqual(self.probe.build_parser().parse_args(["--redo", "zero"]).redo, "zero")

    def test_sheet_retries_reserved_color_metadata_frames(self):
        """prim:reserved 会被 swscale 拒绝；首次失败后用 bt709 声明兜底重试。

        符玄12.mp4 实测：`scale=480:-1` 报 Error -129，覆盖色彩声明后正常。
        """
        sheets = self.sheets
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "sheet.jpg"
            calls = []

            def fake_run(command, **kwargs):
                calls.append(list(command))
                if "-filter_complex" in command:
                    dest.write_bytes(b"x" * 8192)
                    return type("R", (), {"returncode": 0})()
                target = Path(command[-1])
                if "bt709" in command:
                    target.write_bytes(b"y" * 2048)
                    return type("R", (), {"returncode": 0, "stderr": b""})()
                return type("R", (), {
                    "returncode": 1,
                    "stderr": b"[swscale] Unsupported color primaries: reserved",
                })()

            original = sheets.subprocess.run
            sheets.subprocess.run = fake_run
            try:
                ok, reason = sheets.make_sheet("ffmpeg", "reserved.mp4", 600.0, dest, 9)
            finally:
                sheets.subprocess.run = original
            self.assertTrue(ok, reason)
            self.assertEqual(
                sum(1 for c in calls if "bt709" in c), 9,
                "9 帧都应在首次失败后用色彩覆盖重试",
            )

    def test_code_normalization(self):
        normalise = self.scrape_codes.normalise
        self.assertEqual(normalise("fc2ppv-1234567"), "FC2-PPV-1234567")
        self.assertEqual(normalise("abw123"), "ABW-123")
        self.assertEqual(normalise("ipvr00296"), "IPVR-296")

    def test_scrape_html_adapters_use_structured_parsing(self):
        avsox_search = '<a href="/cn/movie/abc123">result</a>'
        self.assertEqual(
            self.scrape_codes.avsox_movie_url(avsox_search),
            "https://avsox.click/cn/movie/abc123",
        )
        avsox = self.scrape_codes.parse_avsox("""
          <h3>Example <b>Title</b></h3>
          <p><span>制作商:</span><a href="/studio/a">Studio A</a></p>
          <a class="avatar-box"><span>Alice</span></a>
          <a class="avatar-box"><span>Bob</span></a>
        """)
        self.assertEqual(avsox["performers"], "Alice|Bob")
        self.assertEqual(avsox["studio"], "Studio A")
        self.assertEqual(avsox["title"], "Example Title")

        javbus = self.scrape_codes.parse_javbus("""
          <h3>Bus <em>Title</em></h3>
          <p><span>製作商:</span><a href="/studio/p">Prestige</a></p>
          <p><span>發行商:</span><a href="/label/l">Label A</a></p>
          <p><span>系列:</span><a href="/series/s">Series A</a></p>
          <a href="/star/alice"><span class="star-name">Alice</span></a>
        """)
        self.assertEqual(javbus["performers"], "Alice")
        self.assertEqual(javbus["studio"], "Prestige")
        self.assertEqual(javbus["label"], "Label A")
        self.assertEqual(javbus["series"], "Series A")

    def test_scrape_writeback_dual_writes_projection_and_entities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close()
            upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,code) "
                "VALUES(1,'local','one.mp4','one.mp4','video','ABC-001')"
            )
            connection.commit()
            connection.close()

            output = root / "review.csv"
            row = {
                "code": "ABC-001", "query": "ABC-001", "performers": "Alice|Bob",
                "studio": "Studio A", "label": "", "series": "Series A", "title": "",
                "categories": "Foot Fetish|Anal", "source": "r18", "status": "ok",
                "size_gb": "1", "videos": "1",
            }
            with output.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.scrape_codes.FIELDS)
                writer.writeheader()
                writer.writerow(row)

            with redirect_stdout(io.StringIO()):
                self.scrape_codes.write_back(str(db), str(output))

            connection = sqlite3.connect(db)
            asset = connection.execute(
                "SELECT creator,studio,series FROM asset WHERE id=1"
            ).fetchone()
            tags = {row[0] for row in connection.execute(
                "SELECT tag FROM asset_tag WHERE asset_id=1"
            )}
            relations = set(connection.execute(
                "SELECT e.kind,e.canonical_name,ae.role,ae.source "
                "FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=1"
            ))
            connection.close()

            self.assertEqual(asset, ("Alice", "Studio A", "Series A"))
            self.assertEqual(tags, {"演员:Alice", "演员:Bob", "足系", "肛交"})
            self.assertTrue({
                ("studio", "Studio A", "studio", "r18:studio"),
                ("series", "Series A", "series", "r18:series"),
                ("performer", "Alice", "performer", "r18:performer"),
                ("performer", "Bob", "performer", "r18:performer"),
                ("tag", "足系", "tag", "r18"),
                ("tag", "肛交", "tag", "r18"),
            } <= relations)

    def test_creator_tag_review_queue_requires_approval_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close()
            upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,creator) "
                "VALUES(1,'local','one.mp4','one.mp4','video','Alice')"
            )
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,creator) "
                "VALUES(2,'local','vocab.mp4','vocab.mp4','video','Vocabulary')"
            )
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,creator) "
                "VALUES(3,'local','The.Show.S01E02.1080p.WEB-DL.mp4',"
                "'The.Show.S01E02.1080p.WEB-DL.mp4','video','Alice')"
            )
            connection.execute(
                "INSERT INTO asset_tag(asset_id,tag,confidence,source) "
                "VALUES(2,'素人',0.9,'vision')"
            )
            connection.commit()
            connection.close()
            boards = root / "boards"
            boards.mkdir()
            (boards / "01_Alice_1.jpg").write_bytes(b"review-only fixture")
            review = root / "review.csv"

            total, pending = self.creator_tags.export_review(db, boards, review)
            self.assertEqual((total, pending), (1, 1))
            with review.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            rows[0].update({"status": "approved", "tags": "素人", "reason": "reviewed"})
            with review.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.creator_tags.REVIEW_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

            backup = root / "backup.db"
            assets, tag_rows = self.creator_tags.apply_review(db, review, backup)
            self.assertEqual((assets, tag_rows), (1, 1))
            self.assertTrue(backup.is_file())
            connection = sqlite3.connect(db)
            self.assertEqual(connection.execute(
                "SELECT source,confidence FROM asset_tag WHERE asset_id=1 AND tag='素人'"
            ).fetchone(), ("vision_creator", 0.6))
            self.assertEqual(connection.execute(
                "SELECT ae.source FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
                "WHERE ae.asset_id=1 AND e.kind='tag' AND e.canonical_name='素人'"
            ).fetchone()[0], "vision_creator")
            connection.close()


if __name__ == "__main__":
    unittest.main()
