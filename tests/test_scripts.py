import argparse
import csv
import hashlib
import importlib.util
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from unittest import mock

from peach import scripting
from peach.migrations import upgrade
from peach.classification import is_probable_mainstream_release, is_structural_creator


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def load_script(name: str):
    """按路径加载 `scripts/<name>.py`。

    执行前先登记进 `sys.modules`：`@dataclass` 处理注解时要按 `cls.__module__` 回查
    模块，没登记就拿到 `None`，报出来的是 `'NoneType' object has no attribute
    '__dict__'`——和脚本本身毫无关系。前缀不用 `test_`，否则加载 `agent_worktree`
    会把真正的 tests/test_agent_worktree.py 从 `sys.modules` 里顶掉。
    """
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"peach_script_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
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
        cls.rehome_unknown = load_script("rehome_unknown_jav")

    def tmp_ledger(self) -> Path:
        """一份只含 rule34xxx 追更条目的临时账本：一条已有类型、一条还没有。

        临时目录先 `.resolve()`：CI runner 的临时目录都是别名（macOS `/var` 软链到
        `/private/var`，Windows `RUNNER~1` 展开成 `runneradmin`），不 resolve 的路径
        喂给被测代码只会在 CI 上红。
        """
        root = Path(tempfile.mkdtemp()).resolve()
        database = root / "ledger.db"
        connection = sqlite3.connect(database)
        connection.executescript(
            "CREATE TABLE follow_source(id INTEGER PRIMARY KEY, provider TEXT);"
            "CREATE TABLE follow_item(id INTEGER PRIMARY KEY, source_id INTEGER,"
            " external_id TEXT, url TEXT, metadata_json TEXT);")
        connection.execute("INSERT INTO follow_source VALUES(1,'rule34xxx')")
        connection.executemany(
            "INSERT INTO follow_item VALUES(?,1,?,?,?)",
            [(1, "18622796", "https://rule34.xxx/index.php?id=18622796",
              json.dumps({"tag_types": {"nier": "copyright"}})),
             (2, "18622794", "https://rule34.xxx/index.php?id=18622794",
              json.dumps({"tag_types": {}}))])
        connection.commit()
        connection.close()
        return database

    def test_import_has_no_filesystem_or_log_side_effect(self):
        self.assertIsNone(self.clean_names._logf)
        self.assertIsNone(self.scrape_codes._logf)

    def test_cover_face_detector_only_treats_dvd_proportions_as_sleeves(self):
        source = (ROOT / "scripts" / "detect_cover_faces.py").read_text(encoding="utf-8")
        self.assertIn("SLEEVE_RATIO_MIN = 1.2", source)
        self.assertIn("SLEEVE_RATIO_MAX = 1.65", source)
        self.assertIn("SLEEVE_RATIO_MIN <= ratio < SLEEVE_RATIO_MAX", source)

    def test_english_title_batch_excludes_codes_that_already_have_japanese(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("CREATE TABLE asset(medium TEXT,code TEXT,catalog_title TEXT,original_title TEXT)")
        connection.executemany("INSERT INTO asset VALUES('video',?,?,?)", [
            ("AAA-001", "English title", None),
            ("BBB-002", "English title", "日本語タイトル"),
            ("CCC-003", None, None),
        ])
        codes = [("AAA-001", 1.0, 1), ("BBB-002", 1.0, 1), ("CCC-003", 1.0, 1)]
        self.assertEqual(self.scrape_codes._select_english_title_codes(connection, codes),
                         [("AAA-001", 1.0, 1)])
        connection.close()
        source = (ROOT / "scripts" / "scrape_codes.py").read_text(encoding="utf-8")
        self.assertIn('if args.english_title_only and field != "title":', source)

    def test_unmapped_genres_are_written_out_instead_of_dropped(self):
        source = (ROOT / "scripts" / "scrape_codes.py").read_text(encoding="utf-8")
        # 未收录 genre 必须落盘。只要这条链断了，来源给过的值就会静默消失，
        # 官方 tag 的缺口下一轮仍然查不出成因。
        self.assertIn("unmapped_genres.setdefault", source)
        self.assertIn("_write_unmapped(unmapped_path, unmapped_genres)", source)
        self.assertNotIn("CATEGORY_MAP", source,
                         "genre 映射只留 peach.genre_taxonomy 一份")

    def test_reused_snapshots_are_re_checked_against_the_queried_code(self):
        # 「复用上一轮成功记录」只看 result 在不在，就会把当初那次错配一路带下去。
        import json as _json
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dlgetchu.json"
            path.write_text(_json.dumps({"result": {
                "id": "33938", "content_id": "33938",
                "source_url": "https://dl.getchu.com/i/item33938",
                "genres": ["コスプレ一般"],
            }}), encoding="utf-8")
            self.assertIsNone(self.scrape_codes._read_snapshot(path, "ABW-220"))
            path.write_text(_json.dumps({"result": {
                "content_id": "118abw220", "genres": ["中出し"],
            }}), encoding="utf-8")
            self.assertEqual(
                self.scrape_codes._read_snapshot(path, "ABW-220")["genres"], ["中出し"])

    def test_source_cools_down_only_after_repeated_failures_and_recovers(self):
        """一次抖动不能决定后面几百个番号的命运。

        2026-09-01 官方 tag 补抓实测：mgstage 中途超时一次，旧逻辑当场把它
        「本批后续全部跳过」，剩下 122 个番号再也没被问过，dmm 丢了 150 个。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.executemany(
                "INSERT INTO asset(id,location,path,name,medium,code,size) "
                "VALUES(?,'local',?,?,'video',?,?)",
                [(i, f"{i}.mp4", f"{i}.mp4", f"AAA-{i:03d}", 1_000) for i in range(1, 7)],
            )
            connection.commit(); connection.close()

            error = self.scrape_codes.MetadataProviderError

            class Flaky:
                def __init__(self): self.calls = []
                def query(self, code, source):
                    self.calls.append(code)
                    raise error("timeout", kind="unavailable",
                                retryable=True, temporary=True)

            provider = Flaky()
            clock = [0.0]
            health = root / "health.csv"
            with mock.patch.object(self.scrape_codes.time, "monotonic",
                                   side_effect=lambda: clock[0]):
                with redirect_stdout(io.StringIO()):
                    self.scrape_codes.main([
                        "--db", str(db), "--out", str(root / "c.csv"),
                        "--health", str(health), "--raw-dir", str(root / "raw"),
                        "--log-dir", str(root / "logs"), "--delay", "0",
                        "--min-free", "0", "--sources", "javbus",
                    ], provider=provider)
            # 前三个番号照常尝试，第三次连败才进冷却；时钟不走，剩下三个被跳过。
            self.assertEqual(len(provider.calls), self.scrape_codes.COOLDOWN_AFTER_FAILURES)
            with health.open(encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["fetched"], "3")
            self.assertEqual(row["cooldown_skips"], "3")
            self.assertEqual(row["blocked"], "1")

            # 冷却会过期：时钟越过窗口后，剩下的番号重新被问。
            provider = Flaky()
            clock = [0.0]

            def advancing():
                clock[0] += self.scrape_codes.COOLDOWN_SECONDS
                return clock[0]

            with mock.patch.object(self.scrape_codes.time, "monotonic",
                                   side_effect=advancing):
                with redirect_stdout(io.StringIO()):
                    self.scrape_codes.main([
                        "--db", str(db), "--out", str(root / "c2.csv"),
                        "--health", str(root / "h2.csv"), "--raw-dir", str(root / "raw2"),
                        "--log-dir", str(root / "logs"), "--delay", "0",
                        "--min-free", "0", "--sources", "javbus",
                    ], provider=provider)
            self.assertEqual(len(provider.calls), 6, "冷却过期后必须继续问剩下的番号")

    def test_only_not_found_counts_as_a_settled_source_verdict(self):
        # 本机 javinizer 没启用某个 scraper 时返回的是 unknown 错误。把它当定论
        # 复用，会让配置问题被冻结成来源判决，续跑再也不问这个番号。
        self.assertEqual(self.scrape_codes.SETTLED_ERROR_KINDS, frozenset({"not_found"}))

    def test_rule34_tag_type_backfill_reuses_the_connector_and_is_resumable(self):
        """rule34xxx 的标签类型只在帖子页上，2152 条里当时只有 40 条带着它。

        常规检查只看第一页，补不到历史条目。抓取判据不重写，直接复用连接器的
        `_detail_tag_types`；备份先做、分批提交，中断一次不至于白跑五十分钟。
        """
        backfill = load_script("backfill_rule34_tag_types")
        # 连接与备份走共享的 `open_for_write`／`open_readonly`，WAL 正确性由
        # `scripting` 那条回归测试守住；这里只钉「用的是那一份」。以前这条断言读的是
        # 源码里有没有 `reader.backup(writer)` 这串字符，脚本改成调用共享实现就红了
        # ——而行为恰恰是变好了。
        self.assertIs(backfill.open_for_write, scripting.open_for_write)
        self.assertIs(backfill.open_readonly, scripting.open_readonly)
        self.assertEqual(backfill.BACKUP_REQUIRED, scripting.BACKUP_REQUIRED)

        # 缺 `--backup` 的 `--apply` 在读输入之前就停，返回 2 且一行都不写。
        database = self.tmp_ledger()
        args = backfill.build_parser().parse_args(
            ["--db", str(database), "--apply"])
        self.assertEqual(backfill.run(args), 2)

        # `--limit` 之外的两条判据也用真实数据钉住：已经有 tag_types 的条目不再排队，
        # 取不到的条目不写空字典冒充已补（下一轮还要再问）。
        connection = sqlite3.connect(database)
        self.addCleanup(connection.close)
        connection.row_factory = sqlite3.Row
        pending = backfill.pending_rows(connection, 0)
        self.assertEqual([row["external_id"] for row in pending], ["18622794"])
        self.assertEqual(
            json.loads(backfill.merge_tag_types({"tags": "a b"}, {"a": "artist"})),
            {"tags": "a b", "tag_types": {"a": "artist"}})

    def test_test_entrypoint_enforces_worktree_source_and_unittest(self):
        windows = (ROOT / "scripts" / "test.ps1").read_text(encoding="utf-8")
        self.assertIn("rev-parse --git-common-dir", windows)
        self.assertIn("$env:PYTHONPATH = $SourceRoot", windows)
        self.assertIn("peach.__file__", windows)
        self.assertIn("scripts\\test_runner.py --scope $Scope", windows)
        self.assertIn("ValidateSet('full', 'follow'", windows)
        self.assertNotIn("pytest", windows.lower())
        # 两个平台各有一个入口，契约必须相同——否则「两边都要绿」只是句口号。
        posix = (ROOT / "scripts" / "test.sh").read_text(encoding="utf-8")
        self.assertIn("rev-parse --git-common-dir", posix)
        self.assertIn('export PYTHONPATH="$SOURCE_ROOT"', posix)
        self.assertIn("peach.__file__", posix)
        self.assertIn('scripts/test_runner.py --scope "$SCOPE"', posix)
        self.assertIn('SCOPE="${1:-full}"', posix)
        self.assertNotIn("pytest", posix.lower())
        # 文档里可以「提到」裸命令来说明它为什么不可信，但绝不能让它单独出现成为一条可照抄的指令。
        # 判据因此不是黑名单，而是：凡出现该命令的行，必须在同一行指向某个正式入口。
        for relative in ("AGENTS.md", "README.md", "docs/HANDOFF.md"):
            instructions = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("scripts\\test.ps1", instructions)
            self.assertIn("scripts/test.sh", instructions)
            for number, line in enumerate(instructions.splitlines(), 1):
                if "unittest discover" not in line:
                    continue
                self.assertTrue(
                    "test.ps1" in line or "test.sh" in line,
                    f"{relative}:{number} 单独出现了裸命令，读者会照抄；必须同时点明正式入口",
                )

    def test_functional_test_scopes_are_explicit_and_full_remains_the_default(self):
        runner = load_script("test_runner")
        follow = {path.name for path in runner.selected_files("follow")}
        full = {path.name for path in runner.selected_files("full")}
        self.assertIn("test_follow_web.py", follow)
        self.assertIn("test_migrations.py", follow)
        self.assertNotIn("test_media.py", follow)
        self.assertGreater(len(full), len(follow))
        self.assertEqual(runner.unclassified_files(), (),
                         "每个测试文件都应属于至少一个功能域")

    def test_the_full_runner_can_import_repository_scripts(self):
        runner = load_script("test_runner")
        suite = runner.build_suite("tooling")
        self.assertGreater(suite.countTestCases(), 0)

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

    def test_ledger_paths_are_split_with_windows_semantics_on_any_host(self):
        """账本路径是 Windows 口径；用 `os.path.dirname` 在 macOS 上会得到空目录，
        判据 A/E 直接失效，判据 B 的「同目录」分组还会退化成跨整个库比对。"""
        self.assertEqual(
            self.find_ads.ledger_dir(r"B:\云下载\bbsxv.xyz-DOCP-324\极道世界.mp4"),
            r"B:\云下载\bbsxv.xyz-DOCP-324",
        )
        self.assertNotEqual(
            self.find_ads.ledger_dir(r"B:\一\a.mp4"),
            self.find_ads.ledger_dir(r"B:\二\a.mp4"),
        )

    def test_promo_dirpack_flags_clean_named_ads_and_spares_watermark_dirs(self):
        """广告包把域名藏进目录名（bbsxv.xyz-DOCP-324），文件名干净、无等长重复也不得漏；
        转载水印目录（www.98T.la@账号）是来源标注，不能因带域名就进清单。"""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER,location TEXT,path TEXT,name TEXT,"
                "size INTEGER,duration REAL,medium TEXT)"
            )
            connection.executemany(
                "INSERT INTO asset VALUES(?,?,?,?,?,?,?)",
                [
                    (1, "115", r"B:\云下载\bbsxv.xyz-DOCP-324\极道世界.mp4",
                     "极道世界.mp4", 75281679, 28.08, "video"),
                    (2, "115", r"B:\云下载\bbsxv.xyz-DOCP-324\最新情报.wmv",
                     "最新情报.wmv", 90867046, 90.92, "video"),
                    (3, "115", r"B:\创作者\luckydog22\www.98T.la@luckydog22\469.avi",
                     "469.avi", 16 * 1024**2, 92.0, "video"),
                ],
            )
            connection.commit(); connection.close()

            plan, scanned = self.find_ads.find_candidates(db, min_group=3)
            self.assertEqual(scanned, 3)
            by_id = {row["id"]: row for row in plan}
            self.assertIn("推广目录", by_id[1]["hits"])
            self.assertIn("推广目录", by_id[2]["hits"])
            self.assertEqual(by_id[1]["confidence"], "确认")
            self.assertNotIn(3, by_id)

    def test_filename_cleanup_is_conservative(self):
        propose = self.clean_names.propose
        self.assertEqual(propose("www.98T.la@sample.mp4"), "sample.mp4")
        self.assertEqual(propose("CJOD-158[fuckbe.com].mp4", "CJOD-158"),
                         "CJOD-158.mp4")
        self.assertEqual(propose("sample.mp4.mp4"), "sample.mp4")
        self.assertEqual(propose("sample.mp4.jpg"), "sample.mp4.jpg")
        self.assertEqual(propose("(3).mp4"), "(3).mp4")
        self.assertEqual(
            propose("Dakota Doll - [Beauty-Angels.com] - [2024] Scene.mp4"),
            "Dakota Doll - [2024] Scene.mp4",
        )
        self.assertEqual(
            propose("❤成人游戏-导航-【688GM.CC】.png"),
            "❤成人游戏-导航.png",
        )
        self.assertEqual(
            propose("QR CODE--扫一扫.png"),
            "QR CODE--扫一扫.png",
            "没有命中清洁规则的原始双横线不能被顺手改写",
        )

    def test_filename_cleanup_normalises_only_the_confirmed_ledger_code(self):
        propose = self.clean_names.propose
        self.assertEqual(propose("PBD00390.mp4", "PBD390", True), "PBD-390.mp4")
        self.assertEqual(propose("HD-abp-0758.mp4", "ABP-758"), "HD-ABP-758.mp4")
        self.assertEqual(
            propose("fc2 3098987 sample.mp4", "FC2PPV-3098987"),
            "FC2-PPV-3098987 sample.mp4",
        )
        self.assertEqual(
            propose("KUZU_250103-U_iris3.mp4", "KUZU-25010"),
            "KUZU_250103-U_iris3.mp4",
            "番号后紧接额外数字时不能把长编号截断改写",
        )
        self.assertEqual(
            propose("raikun325.mp4", "RAIKUN325"), "raikun325.mp4",
            "没有分隔符的账号名不能先补成番号再改文件名",
        )

    def test_filename_cleanup_keeps_collision_media_with_a_numbered_suffix(self):
        rows = [
            (1, "115", r"B:\番号\ABW-234\ABW-234.mp4", "ABW-234.mp4", "ABW-234"),
            (2, "115", r"B:\番号\ABW-234\hhd800.com@abw-0234.mp4",
             "hhd800.com@abw-0234.mp4", "ABW-234"),
            (3, "115", r"B:\番号\FC2\fc2 3098987.mp4",
             "fc2 3098987.mp4", "FC2PPV-3098987"),
        ]
        plan = self.clean_names.build_plan(rows)
        by_id = {row["id"]: row for row in plan}
        self.assertEqual(by_id[2]["new"], "ABW-234 (2).mp4")
        self.assertEqual(by_id[2]["status"], "ready-suffixed")
        self.assertEqual(by_id[3]["new"], "FC2-PPV-3098987.mp4")
        self.assertEqual(by_id[3]["new_code"], "FC2-PPV-3098987")

    def test_filename_cleanup_normalises_compact_code_only_with_release_evidence(self):
        plan = self.clean_names.build_plan([
            (1, "115", r"B:\番号\PBD390\PBD00390.mp4",
             "PBD00390.mp4", "PBD390", 1),
            (2, "115", r"B:\账号\RAIKUN325\raikun325.mp4",
             "raikun325.mp4", "RAIKUN325", 0),
        ])
        self.assertEqual([(row["id"], row["new"], row["new_code"]) for row in plan],
                         [(1, "PBD-390.mp4", "PBD-390")])

    def test_filename_cleanup_joins_paths_by_the_ledger_path_shape(self):
        self.assertEqual(
            self.clean_names._join(r"B:\番号\ABW-234", "ABW-234.mp4"),
            r"B:\番号\ABW-234\ABW-234.mp4",
        )
        self.assertEqual(
            self.clean_names._join("/tmp/peach", "ABW-234.mp4"),
            "/tmp/peach/ABW-234.mp4",
        )

    def test_filename_cleanup_apply_renames_files_updates_ledger_and_validates_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "ABW-234.mp4"
            advertised = root / "hhd800.com@abw-0234.mp4"
            lowercase = root / "mide-950-C.mp4"
            existing.write_bytes(b"first")
            advertised.write_bytes(b"second")
            lowercase.write_bytes(b"third")
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER PRIMARY KEY,location TEXT,path TEXT,"
                "name TEXT,code TEXT)"
            )
            connection.executemany(
                "INSERT INTO asset VALUES(?,?,?,?,?)",
                [
                    (1, "local", str(existing), existing.name, "ABW-234"),
                    (2, "local", str(advertised), advertised.name, "ABW-234"),
                    (3, "local", str(lowercase), lowercase.name, "MIDE-950"),
                ],
            )
            connection.commit(); connection.close()

            backup_path = root / "ledger.pre-clean-names.db"
            result = self.clean_names.main([
                "--db", str(db), "--out", str(root / "plan.csv"),
                "--log-dir", str(root / "logs"),
                "--apply", "--backup", str(backup_path),
            ])

            self.assertEqual(result, 0)
            self.assertEqual(existing.read_bytes(), b"first")
            self.assertEqual((root / "ABW-234 (2).mp4").read_bytes(), b"second")
            self.assertEqual((root / "MIDE-950-C.mp4").read_bytes(), b"third")
            connection = sqlite3.connect(db)
            rows = connection.execute(
                "SELECT id,name,code FROM asset ORDER BY id"
            ).fetchall()
            connection.close()
            self.assertEqual(rows, [
                (1, "ABW-234.mp4", "ABW-234"),
                (2, "ABW-234 (2).mp4", "ABW-234"),
                (3, "MIDE-950-C.mp4", "MIDE-950"),
            ])
            backup = sqlite3.connect(backup_path)
            self.assertEqual(backup.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(backup.execute("SELECT count(*) FROM asset").fetchone()[0], 3)
            backup.close()

    def test_rehome_unknown_jav_flattens_files_and_updates_confirmed_studio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unknown = root / "番号" / "_未知厂牌"
            nested = unknown / "259LUXU-1468" / "release title"
            nested.mkdir(parents=True)
            video = nested / "259LUXU-1468.mp4"
            video.write_bytes(b"video")
            sidecar = nested / "259LUXU-1468.jpg"
            sidecar.write_bytes(b"image")
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,code) VALUES(?,?,?,?,?,?)",
                (1, "115", r"B:\番号\_未知厂牌\259LUXU-1468\release title\259LUXU-1468.mp4",
                 video.name, "video", "259LUXU-1468"),
            )
            connection.commit(); connection.close()
            mappings = root / "mappings.csv"
            mappings.write_text(
                "code,studio,source,confidence,evidence_url,note\n"
                "259LUXU-1468,ラグジュTV,user:studio-review,1.0,https://javdb.com/v/YJ148,user confirmed\n",
                encoding="utf-8-sig",
            )
            backup = root / "ledger.pre-rehome.db"
            plan = root / "plan.csv"

            result = self.rehome_unknown.main([
                "--db", str(db), "--mappings", str(mappings),
                "--physical-unknown-root", str(unknown),
                "--plan", str(plan), "--apply", "--backup", str(backup),
            ])

            self.assertEqual(result, 0)
            target = root / "番号" / "ラグジュTV" / "259LUXU-1468"
            self.assertEqual((target / video.name).read_bytes(), b"video")
            self.assertEqual((target / sidecar.name).read_bytes(), b"image")
            self.assertFalse((unknown / "259LUXU-1468").exists())
            connection = sqlite3.connect(db)
            self.assertEqual(connection.execute(
                "SELECT path,studio FROM asset WHERE id=1"
            ).fetchone(), (r"B:\番号\ラグジュTV\259LUXU-1468\259LUXU-1468.mp4",
                           "ラグジュTV"))
            self.assertEqual(connection.execute(
                "SELECT e.canonical_name,ae.source FROM asset_entity ae "
                "JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id=1 AND ae.role='studio'"
            ).fetchone(), ("ラグジュTV", "user:studio-review"))
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            connection.close()
            self.assertTrue(backup.is_file())
            self.assertIn(",done", plan.read_text(encoding="utf-8-sig"))

    def test_rehome_unknown_jav_refuses_flattening_name_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unknown = root / "番号" / "_未知厂牌"
            for folder in ("one", "two"):
                nested = unknown / "ABP-340" / folder
                nested.mkdir(parents=True)
                (nested / "ABP-340.mp4").write_bytes(folder.encode())
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            mappings = root / "mappings.csv"
            mappings.write_text(
                "code,studio,source,confidence\n"
                "ABP-340,Prestige,user:studio-review,1.0\n",
                encoding="utf-8-sig",
            )

            result = self.rehome_unknown.main([
                "--db", str(db), "--mappings", str(mappings),
                "--physical-unknown-root", str(unknown),
                "--plan", str(root / "plan.csv"),
            ])

            self.assertEqual(result, 1)
            self.assertTrue((unknown / "ABP-340" / "one" / "ABP-340.mp4").is_file())
            self.assertFalse((root / "番号" / "Prestige" / "ABP-340").exists())

    def test_rehome_unknown_jav_accepts_cloud_drive_removing_an_empty_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "code"
            vanished = root / "release title"
            vanished.mkdir(parents=True)
            original_iterdir = Path.iterdir

            def cloud_drive_iterdir(path):
                if path == vanished and path.exists():
                    path.rmdir()
                    raise FileNotFoundError(path)
                return original_iterdir(path)

            with mock.patch.object(Path, "iterdir", cloud_drive_iterdir):
                self.rehome_unknown._remove_empty_tree(root)
            self.assertFalse(root.exists())

    def test_rehome_unknown_jav_accepts_cloud_drive_removing_an_empty_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            original_iterdir = Path.iterdir

            def cloud_drive_iterdir(path):
                if path == target and path.exists():
                    path.rmdir()
                    raise FileNotFoundError(path)
                return original_iterdir(path)

            with mock.patch.object(Path, "iterdir", cloud_drive_iterdir):
                self.assertEqual(self.rehome_unknown._direct_children(target), {})

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

    def test_every_script_importing_peach_can_run_without_pythonpath(self):
        """脚本是给人直接敲的，不该要求先设 PYTHONPATH。

        2026-09-02 交给用户的 `flatten_release_dirs.py --apply` 第一行就
        ModuleNotFoundError：`from peach.catalog_rules import ...` 在裸 python 下
        找不到 `src`。仓库里 `job_status.py` 等脚本早就带着这段引导，只是没有门槛
        逼后来的脚本跟上。判据只看「导入 peach 之前有没有把 src 挂进 sys.path」，
        不规定写法。
        """
        missing = []
        for path in sorted((ROOT / "scripts").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            lines = source.splitlines()
            peach_import = next(
                (index for index, line in enumerate(lines)
                 if line.startswith(("from peach.", "import peach"))), -1)
            if peach_import < 0:
                continue
            head = "\n".join(lines[:peach_import])
            if "sys.path.insert" not in head and "sys.path.append" not in head:
                missing.append(path.name)
        self.assertEqual(missing, [],
                         "这些脚本导入 peach 前没挂 src，裸 python 跑会 ModuleNotFoundError")

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

        # 透明 Logo 的字样可能贴到四角。角上的蓝字不是底色，补边必须继续透明；
        # 否则 PREMIUM 会整张铺蓝，白字 Logo 也会因错误白底而消失。
        transparent = Image.new("RGBA", (400, 100), (0, 0, 0, 0))
        for x in range(80):
            transparent.putpixel((x, 0), (0, 174, 239, 255))
        buffer = io.BytesIO()
        transparent.save(buffer, "PNG")
        squared = Image.open(io.BytesIO(pad_to_square(buffer.getvalue())))
        self.assertEqual(squared.getpixel((5, 5)), (0, 0, 0, 0))
        self.assertEqual(squared.getpixel((200, 200)), (0, 0, 0, 0))
        self.assertEqual(squared.getpixel((20, 150)), (0, 174, 239, 255))

    def test_a_transparent_mark_is_baked_onto_a_white_plate(self):
        """带透明像素的独立图标：裁掉透明边，居中放到白色方底上。

        三处取图位都用 `object-fit: cover` 铺满方框，透明底在深色底上会露出下面
        那一层。边距烤进文件，页面就不必各自补 inset 和 padding。
        """
        import io

        from PIL import Image

        from peach.images import MARK, PLATE_CONTENT_RATIO, bake_square, classify_plate

        source = Image.new("RGBA", (400, 100), (0, 0, 0, 0))
        for x in range(10, 310):
            for y in range(20, 60):
                source.putpixel((x, y), (0, 174, 239, 255))
        buffer = io.BytesIO()
        source.save(buffer, "PNG")
        payload = buffer.getvalue()

        self.assertEqual(classify_plate(payload), MARK)
        baked = bake_square(payload)
        with Image.open(io.BytesIO(baked)) as plate:
            self.assertEqual(plate.size[0], plate.size[1], "烤出来必须是方的")
            self.assertNotIn("A", plate.getbands(), "装进去的文件必须不透明")
            side = plate.size[0]
            self.assertAlmostEqual(300 / side, PLATE_CONTENT_RATIO, places=2,
                                   msg="内容占边长约 76%，四周各留约 12%")
            self.assertEqual(plate.getpixel((2, 2)), (255, 255, 255), "四周是白底")
            self.assertEqual(plate.getpixel((side // 2, side // 2)), (0, 174, 239),
                             "主体居中，像素不缩放")

    def test_an_opaque_plate_keeps_its_own_background(self):
        """完全不透明的图自带底色，那块底是设计的一部分：方的原样返回，长条补方。"""
        import io

        from PIL import Image

        from peach.images import TILE, bake_square, classify_plate

        def opaque(size, color):
            buffer = io.BytesIO()
            Image.new("RGB", size, color).save(buffer, "PNG")
            return buffer.getvalue()

        tile = opaque((400, 400), (12, 12, 12))
        self.assertEqual(classify_plate(tile), TILE)
        self.assertEqual(bake_square(tile), tile, "已经是不透明方图，一个字节都不动")

        strip = opaque((400, 100), (196, 20, 24))
        self.assertEqual(classify_plate(strip), TILE)
        with Image.open(io.BytesIO(bake_square(strip))) as squared:
            self.assertEqual(squared.size, (400, 400))
            self.assertEqual(squared.convert("RGB").getpixel((5, 5)), (196, 20, 24),
                             "补出来的边取原图边缘主色，不刷白")

        self.assertIsNone(classify_plate(b"not an image"))
        self.assertIsNone(bake_square(b"not an image"))

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

    def test_installed_studio_logos_are_backed_up_then_made_opaque_squares(self):
        """整个目录归一成不透明方图；测试只能写临时目录。

        `*.img` 全在范围内，`<safe>.icon.img` 与 `<safe>.logo.img` 也算。带透明的
        烤白底，不透明的长条补方，已经是不透明方图的一个字节都不动。
        """
        from PIL import Image

        module = load_script("normalize_studio_logos")

        def png(image):
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            return buffer.getvalue()

        mark = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
        for x in range(20, 180):
            for y in range(10, 50):
                mark.putpixel((x, y), (0, 174, 239, 255))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "logos"
            backup = Path(tmp) / "backup"
            root.mkdir()
            originals = {
                "wide.img": png(Image.new("RGB", (400, 100), (196, 20, 24))),
                "flat.icon.img": png(Image.new("RGB", (256, 256), (12, 12, 12))),
                "sign.logo.img": png(mark),
                "vector.img": b'<svg xmlns="http://www.w3.org/2000/svg"/>',
            }
            for name, payload in originals.items():
                (root / name).write_bytes(payload)
                Path(f"{root / name}.ct").write_text(
                    "image/svg+xml" if name == "vector.img" else "image/png",
                    encoding="utf-8")

            dry = {str(row["file"]): row for row in module.normalize(root)}
            self.assertEqual(dry["wide.img"]["action"], "would-pad")
            self.assertEqual(dry["wide.img"]["kind"], "tile")
            self.assertEqual(dry["sign.logo.img"]["action"], "would-bake")
            self.assertEqual(dry["sign.logo.img"]["kind"], "mark")
            self.assertEqual(dry["vector.img"]["action"], "vector",
                             "矢量标识本脚本不栅格化，单列出来而不是记成坏文件")
            self.assertNotIn("flat.icon.img", dry, "已经是不透明方图，不进复核件")
            for name, payload in originals.items():
                self.assertEqual((root / name).read_bytes(), payload, "dry-run 不得改图")
            with self.assertRaises(ValueError):
                module.normalize(root, apply=True)

            applied = {str(row["file"]): row for row in
                       module.normalize(root, apply=True, backup_dir=backup)}
            self.assertEqual(applied["wide.img"]["action"], "padded")
            self.assertEqual(applied["sign.logo.img"]["action"], "baked")
            self.assertEqual((backup / "wide.img").read_bytes(), originals["wide.img"])
            self.assertFalse((backup / "flat.icon.img").exists(), "没动的文件不备份")
            self.assertEqual((root / "flat.icon.img").read_bytes(),
                             originals["flat.icon.img"])
            self.assertEqual((root / "vector.img").read_bytes(), originals["vector.img"],
                             "矢量标识原样留着")
            self.assertFalse(Path(f'{root / "vector.img"}.normalization.json').exists())

            with Image.open(root / "wide.img") as squared:
                self.assertEqual(squared.size, (400, 400))
            with Image.open(root / "sign.logo.img") as plate:
                self.assertEqual(plate.size[0], plate.size[1])
                self.assertNotIn("A", plate.getbands(), "烤过的文件必须不透明")

            for name, action in (("wide.img", "pad-to-square"),
                                 ("sign.logo.img", "bake-white-plate")):
                sidecar = json.loads(
                    Path(f"{root / name}.normalization.json").read_text(encoding="utf-8"))
                self.assertEqual(sidecar["action"], action)
                self.assertEqual(sidecar["original_sha256"],
                                 hashlib.sha256(originals[name]).hexdigest())
                self.assertEqual(sidecar["normalized_sha256"],
                                 hashlib.sha256((root / name).read_bytes()).hexdigest())
                self.assertEqual(sidecar["backup"], str(backup / name))
                self.assertEqual(Path(f"{root / name}.ct").read_text(encoding="utf-8"),
                                 "image/png")

            # 重跑不再有动作：产物已经是不透明方图，归一是幂等的。矢量那一行照旧
            # 每次都在，它是「还没处理」的记录，不是待办完成。
            self.assertEqual([row["action"] for row in module.normalize(root)],
                             ["vector"])

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

    def test_sheets_can_reshoot_one_named_asset_over_a_stale_product(self):
        """点名重抽是为了盖掉上一次的错结果，撞上已存在的产物就短路等于没修。"""
        sheets = self.sheets
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER PRIMARY KEY,location TEXT,path TEXT,"
                "medium TEXT,duration REAL,size INTEGER,snapshot_path TEXT)"
            )
            # 18349 已有陈旧产物且已登记；1 是同来源的另一条待抽项，不该被顺带带走。
            connection.execute(
                "INSERT INTO asset VALUES(18349,'local',?,'video',110.87,2000,'stale.jpg')",
                (str(root / "one.mp4"),),
            )
            connection.execute(
                "INSERT INTO asset VALUES(1,'local',?,'video',600.0,1000,NULL)",
                (str(root / "two.mp4"),),
            )
            connection.commit()
            connection.close()

            output_root = root / "out"
            stale = sheets.output_path(output_root, "local", str(root / "one.mp4"))
            stale.write_bytes(b"x" * 8192)

            args = sheets.build_parser().parse_args([
                "--db", str(db), "--workers", "1", "--min-free", "0",
                "--asset", "18349",
                "--output-root", str(output_root), "--log-dir", str(root / "log"),
            ])

            shot: list[str] = []

            def fake_sheet(_ffmpeg, path, _duration, destination, _frames):
                shot.append(path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"y" * 9000)
                return True, ""

            choice = type("C", (), {"path": "ffmpeg"})
            with mock.patch.object(sheets, "make_sheet", fake_sheet),                  mock.patch.object(sheets.FFmpegResolver, "ffmpeg", lambda _self: choice),                  redirect_stdout(io.StringIO()):
                sheets.run(args)

            connection = sqlite3.connect(db)
            snapshots = dict(connection.execute("SELECT id,snapshot_path FROM asset").fetchall())
            connection.close()
            rewritten = stale.read_bytes()

        self.assertEqual(len(shot), 1, "点名只该抽这一条")
        self.assertIn("one.mp4", shot[0])
        self.assertEqual(rewritten[:1], b"y", "陈旧产物必须被真正覆盖")
        self.assertIsNone(snapshots[1], "没点名的待抽项不该被这一趟带走")

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

    def test_probe_can_target_one_asset_whose_recorded_duration_is_wrong(self):
        """asset 18349 账本记 752.24 秒、真实文件 110.87 秒，--redo 的 0/-1 判据够不着。

        点名重探时不套时长筛选，但计费来源边界必须照旧生效。
        """
        probe = self.probe
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            connection = sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE asset(id INTEGER PRIMARY KEY,location TEXT,path TEXT,"
                "medium TEXT,duration REAL,size INTEGER,width INTEGER,height INTEGER,"
                "vcodec TEXT,fps REAL,has_audio INTEGER,ctx_length TEXT,ctx_orient TEXT,"
                "ctx_quality TEXT)"
            )
            for asset_id, duration in ((18349, 752.24), (1, None)):
                connection.execute(
                    "INSERT INTO asset(id,location,path,medium,duration,size) "
                    "VALUES(?,'local',?,'video',?,1000)",
                    (asset_id, str(root / f"{asset_id}.mp4"), duration),
                )
            connection.commit()
            connection.close()

            args = probe.build_parser().parse_args([
                "--db", str(db), "--workers", "1", "--min-free", "0",
                "--asset", "18349", "--log-dir", str(root / "log"),
                "--lock", str(root / "probe.lock"),
            ])
            self.assertEqual(args.asset, [18349])

            probed: list[str] = []
            choice = type("C", (), {"path": "ffprobe"})

            def fake_probe(_ffprobe, path, _timeout):
                probed.append(path)
                return 110.866667, 1920, 1072, "h264", 30.0, None

            with mock.patch.object(probe, "probe_file", fake_probe),                  mock.patch.object(probe.FFmpegResolver, "ffprobe", lambda _self: choice),                  redirect_stdout(io.StringIO()):
                probe.run(args)

            connection = sqlite3.connect(db)
            rows = dict(connection.execute("SELECT id,duration FROM asset").fetchall())
            connection.close()

        self.assertEqual(len(probed), 1, "点名只该动这一条，不能顺带重探全库")
        self.assertAlmostEqual(rows[18349], 110.866667, places=5)
        self.assertIsNone(rows[1], "没点名的未探测条目不该被这一趟带走")

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

    def test_explicit_code_judges_the_normalised_shape(self):
        """账本里 `WX17` 这种缺分隔符的写法必须和 `--codes-file` 那侧结论一致。

        两处一个按原始写法判、一个按规范化键匹配时，同一批番号会被报成
        「番号文件含 ledger 中不存在的番号」，2026-09-02 实测漏掉 42 个。
        """
        explicit = self.scrape_codes._is_explicit_code
        for code in ("WX17", "PBD390", "ABW-123", "ipvr00296", "fc2ppv-1234567"):
            self.assertTrue(explicit(code), code)
        for code in ("", "合集", "未知厂牌", "4K", "FC2-1234"):
            self.assertFalse(explicit(code), code)

    def test_repost_site_watermarks_are_never_queued_for_a_provider(self):
        # `HHD800`、`HJD2048` 是转载站域名剥掉 TLD 后的样子，不是番号。查它们只会
        # 白跑一轮限流预算，而 provider 的空结果又会被当成「这个番号没元数据」。
        for code in ("HHD800", "hhd800.com", "HJD2048", "AAVV333", "KFA33", "BEI88"):
            self.assertFalse(self.scrape_codes._is_explicit_code(code), code)

    def test_code_normalization(self):
        # 归一化本体已收进 catalog_rules；脚本只是 import 它，这里验的是脚本用的
        # 确实是那一份，而不是自己又抄了一个同名函数。
        normalise = self.scrape_codes.normalise_code_key
        self.assertEqual(normalise("fc2ppv-1234567"), "FC2-PPV-1234567")
        self.assertEqual(normalise("abw123"), "ABW-123")
        self.assertEqual(normalise("ipvr00296"), "IPVR-296")

    def test_javinizer_scrape_writes_field_candidates_and_raw_evidence_only(self):
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

            output = root / "metadata-field-candidates-20260822.csv"
            raw = root / "sources"
            class FakeProvider:
                def __init__(self):
                    self.calls = []
                def query(self, code, source):
                    self.calls.append((code, source))
                    return {
                        "source": source, "source_url": "https://r18.dev/example",
                        "id": "ABC-001", "content_id": "abc00001",
                        "title": "Catalog title", "original_title": "原标题",
                        "runtime": 121, "director": "Director A", "label": "Label A",
                        "poster_url": "https://img.example/poster.jpg",
                        "cover_url": "https://img.example/cover.jpg",
                        "screenshot_urls": ["https://img.example/1.jpg"],
                        "trailer_url": "https://video.example/trailer.m3u8",
                        "maker": "Studio A" if source == "r18dev" else "Studio B",
                        "series": "Series A", "release_date": "2020-09-13T00:00:00Z",
                        "actresses": [{"dmm_id": 7, "japanese_name": "木村さん 木村さん"}],
                        "genres": ["Foot Fetish", "Anal", "Unknown"],
                    }
            provider = FakeProvider()
            with redirect_stdout(io.StringIO()):
                result = self.scrape_codes.main([
                    "--db", str(db), "--out", str(output), "--raw-dir", str(raw),
                    "--log-dir", str(root / "logs"), "--delay", "0",
                    "--min-free", "0",
                    "--sources", "javbus,r18dev",
                ], provider=provider)
            self.assertEqual(result, 0)
            self.assertEqual(provider.calls, [("ABC-001", "javbus"), ("ABC-001", "r18dev")])

            with output.open(encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["field"] for row in rows},
                             {"title", "original_title", "performers", "studio",
                              "series", "release_date", "tags"})
            performer = next(row for row in rows if row["field"] == "performers")
            candidates = __import__("json").loads(performer["candidates_json"])
            self.assertEqual({candidate["source"] for candidate in candidates}, {"r18dev", "javbus"})
            self.assertEqual(candidates[0]["display_value"], "木村さん")
            self.assertIn("已规范化", candidates[0]["warnings"][0])
            self.assertEqual(candidates[0]["provider_id"], "ABC-001")
            self.assertEqual(candidates[0]["content_id"], "abc00001")
            self.assertEqual(candidates[0]["catalog_evidence"]["label"]["value"], "Label A")
            self.assertEqual(
                candidates[0]["catalog_evidence"]["screenshot_urls"]["value"],
                ["https://img.example/1.jpg"],
            )
            release = next(row for row in rows if row["field"] == "release_date")
            self.assertEqual(__import__("json").loads(release["candidates_json"])[0]["value"],
                             "2020-09-13")
            tag_candidates = __import__("json").loads(
                next(row for row in rows if row["field"] == "tags")["candidates_json"])
            self.assertEqual([candidate["source"] for candidate in tag_candidates],
                             ["r18dev", "javbus"], "官方 tag 来源必须排在社区来源前")
            self.assertTrue(tag_candidates[0]["official"])
            self.assertEqual(tag_candidates[0]["profile"], "custom")
            self.assertEqual(tag_candidates[0]["policy_version"],
                             "metadata-source-policy-v4")
            self.assertEqual(tag_candidates[0]["field_rank"], 9)
            self.assertEqual(tag_candidates[0]["source_kind"], "official_mirror")
            self.assertTrue(all(row["source_profile"] == "custom" for row in rows))
            self.assertTrue((raw / "ABC-001" / "r18dev.json").is_file())
            self.assertTrue((raw / "ABC-001" / "javbus.json").is_file())

            health = output.with_name("metadata-source-health-20260822.csv")
            with health.open(encoding="utf-8-sig", newline="") as handle:
                health_rows = {row["source"]: row for row in csv.DictReader(handle)}
            self.assertEqual(set(health_rows), {"javbus", "r18dev"})
            self.assertEqual(health_rows["r18dev"]["profile"], "custom")
            self.assertEqual(health_rows["r18dev"]["attempted"], "1")
            self.assertEqual(health_rows["r18dev"]["fetched"], "1")
            self.assertEqual(health_rows["r18dev"]["succeeded"], "1")
            self.assertEqual(health_rows["r18dev"]["release_date"], "1")
            self.assertEqual(health_rows["r18dev"]["title"], "1")
            self.assertEqual(health_rows["r18dev"]["trailer_url"], "1")

            connection = sqlite3.connect(db)
            asset = connection.execute(
                "SELECT creator,studio,series FROM asset WHERE id=1"
            ).fetchone()
            relation_count = connection.execute("SELECT count(*) FROM asset_entity").fetchone()[0]
            connection.close()
            self.assertEqual(asset, (None, None, None))
            self.assertEqual(relation_count, 0)

    def test_javinizer_scrape_codes_file_limits_batch_in_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close()
            upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.executemany(
                "INSERT INTO asset(id,location,path,name,medium,code,size) "
                "VALUES(?,'local',?,?,'video',?,?)",
                [(1, "large.mp4", "large.mp4", "AAA-001", 10_000),
                 (2, "small.mp4", "small.mp4", "BBB-002", 1_000)],
            )
            connection.commit()
            connection.close()
            codes_file = root / "codes.txt"
            codes_file.write_text("# exact batch\nBBB002\n", encoding="utf-8")

            class FakeProvider:
                def __init__(self):
                    self.calls = []

                def query(self, code, source):
                    self.calls.append((code, source))
                    return {"source": source, "series": "Series B"}

            provider = FakeProvider()
            output = root / "candidates.csv"
            with redirect_stdout(io.StringIO()):
                result = self.scrape_codes.main([
                    "--db", str(db), "--out", str(output),
                    "--raw-dir", str(root / "raw"), "--log-dir", str(root / "logs"),
                    "--delay", "0", "--min-free", "0", "--sources", "r18dev",
                    "--codes-file", str(codes_file),
                ], provider=provider)
            self.assertEqual(result, 0)
            self.assertEqual(provider.calls, [("BBB-002", "r18dev")])
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["query"] for row in rows}, {"BBB-002"})

    def test_javinizer_resume_throttles_only_real_network_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.executemany(
                "INSERT INTO asset(id,location,path,name,medium,code,size) "
                "VALUES(?,'local',?,?,'video',?,?)",
                [(1, "cached.mp4", "cached.mp4", "AAA-001", 2_000),
                 (2, "missing.mp4", "missing.mp4", "BBB-002", 1_500),
                 (3, "fresh.mp4", "fresh.mp4", "CCC-003", 1_000)],
            )
            connection.commit(); connection.close()
            raw = root / "raw"
            snapshot = raw / "AAA-001" / "r18dev.json"
            snapshot.parent.mkdir(parents=True)
            # 真实快照一定带得出番号身份；不带的现在按「对不上」重新联网问。
            snapshot.write_text(__import__("json").dumps({
                "result": {"source": "r18dev", "id": "AAA-001", "maker": "Cached Studio"},
            }), encoding="utf-8")
            missing = raw / "BBB-002" / "r18dev.json"
            missing.parent.mkdir(parents=True)
            missing.write_text(__import__("json").dumps({
                "error": {"kind": "not_found", "message": "status 404",
                          "status_code": 404, "retryable": False, "temporary": False},
            }), encoding="utf-8")

            class Provider:
                def __init__(self): self.calls = []
                def query(self, code, source):
                    self.calls.append((code, source))
                    return {"source": source, "maker": "Fresh Studio"}

            provider = Provider()
            errors = root / "errors.csv"
            with mock.patch.object(self.scrape_codes.time, "sleep") as sleep:
                with redirect_stdout(io.StringIO()):
                    result = self.scrape_codes.main([
                        "--db", str(db), "--out", str(root / "candidates.csv"),
                        "--errors", str(errors),
                        "--raw-dir", str(raw), "--log-dir", str(root / "logs"),
                        "--delay", "2", "--min-free", "0", "--sources", "r18dev",
                    ], provider=provider)
            self.assertEqual(result, 0)
            self.assertEqual(provider.calls, [("CCC-003", "r18dev")])
            self.assertEqual(sleep.call_count, 1, "本地快照不能消耗来源限流等待")
            with errors.open(encoding="utf-8-sig", newline="") as handle:
                error_rows = list(csv.DictReader(handle))
            self.assertEqual([(row["code"], row["status_code"]) for row in error_rows],
                             [("BBB-002", "404")])

    def test_metadata_health_distinguishes_snapshot_empty_error_and_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.executemany(
                "INSERT INTO asset(id,location,path,name,medium,code,size) "
                "VALUES(?,'local',?,?,'video',?,?)",
                [(1, "1.mp4", "1.mp4", "ABC-001", 3_000),
                 (2, "2.mp4", "2.mp4", "DEF-002", 2_000),
                 (3, "3.mp4", "3.mp4", "GHI-003", 1_000)],
            )
            connection.commit(); connection.close()
            raw = root / "raw"
            snapshot = raw / "ABC-001" / "r18dev.json"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text(__import__("json").dumps({
                "result": {"source": "r18dev", "id": "ABC-001", "maker": "Studio A"},
            }), encoding="utf-8")

            class HealthProvider:
                def __init__(self): self.calls = []
                def query(self, code, source):
                    self.calls.append((code, source))
                    if source == "javbus" and code == "DEF-002":
                        raise self_error(
                            "rate limited", kind="rate_limited", status_code=429,
                            retryable=True, temporary=True,
                        )
                    if source == "javbus":
                        return {"source": source}
                    return {"source": source, "maker": "Studio A"}

            self_error = self.scrape_codes.MetadataProviderError
            provider = HealthProvider()
            output = root / "metadata-field-candidates-health.csv"
            health = root / "health.csv"
            with redirect_stdout(io.StringIO()):
                result = self.scrape_codes.main([
                    "--db", str(db), "--out", str(output), "--health", str(health),
                    "--raw-dir", str(raw), "--log-dir", str(root / "logs"),
                    "--delay", "0", "--min-free", "0", "--sources", "r18dev,javbus",
                ], provider=provider)
            self.assertEqual(result, 0)
            with health.open(encoding="utf-8-sig", newline="") as handle:
                rows = {row["source"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["r18dev"]["snapshot_reused"], "1")
            self.assertEqual(rows["r18dev"]["fetched"], "2")
            self.assertEqual(rows["javbus"]["attempted"], "3")
            # 限流那一条之后的番号照问，所以三条都联了网。
            self.assertEqual(rows["javbus"]["fetched"], "3")
            self.assertEqual(rows["javbus"]["succeeded"], "2")
            self.assertEqual(rows["javbus"]["empty"], "2")
            self.assertEqual(rows["javbus"]["errors"], "1")
            self.assertEqual(rows["javbus"]["retryable_errors"], "1")
            # 单次可重试失败不再让来源停摆：后面的番号照问。
            self.assertEqual(rows["javbus"]["cooldown_skips"], "0")
            self.assertEqual(rows["javbus"]["blocked"], "0")
            self.assertEqual(rows["javbus"]["last_error_status"], "429")

            connection = sqlite3.connect(db)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM asset_entity").fetchone()[0], 0)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM review_decision").fetchone()[0], 0)
            connection.close()

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


class FlattenReleaseDirTests(unittest.TestCase):
    """冗余发行物目录层与目录名广告标记。"""

    @classmethod
    def setUpClass(cls):
        cls.flatten = load_script("flatten_release_dirs")

    def _ledger(self, root: Path, paths: list[str]) -> sqlite3.Connection:
        db = root / "ledger.db"
        sqlite3.connect(db).close()
        upgrade(db, MIGRATIONS)
        connection = sqlite3.connect(db)
        for index, path in enumerate(paths, 1):
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium) VALUES(?,'115',?,?,'video')",
                (index, path, PureWindowsPath(path).name))
        connection.commit()
        return connection

    def _resolver(self, root: Path):
        return lambda ledger: root.joinpath(*PureWindowsPath(str(ledger)).parts[1:])

    def test_collapse_needs_a_redundant_name_not_just_a_lone_child(self):
        """`古川结爱合集` 底下只有一个 `FC2-PPV-…` 也是有意义的一层，不能合。

        真实数据里「父目录只有一个子目录」有 747 处，绝大多数不是冗余层；只按
        「独子」判会把合集目录整片摊平。
        """
        with tempfile.TemporaryDirectory() as tmp:
            connection = self._ledger(Path(tmp), [
                r"B:\日本\Prestige\TRE-080\[44x.me]tre-080\TRE-080.mp4",
                r"B:\日本\Prestige\TRE-080\[44x.me]tre-080\TRE-080-2.mp4",
                r"B:\合集\古川结爱合集\FC2-PPV-1234567\one.mp4",
            ])
            plan = self.flatten.plan_operations(connection)
            connection.close()
            collapses = [row["ledger_dir"] for row in plan if row["kind"] == "collapse"]
            self.assertEqual(collapses, [r"B:\日本\Prestige\TRE-080\[44x.me]tre-080"])
            renames = {row["ledger_dir"] for row in plan if row["kind"] == "rename"}
            self.assertNotIn(r"B:\日本\Prestige\TRE-080\[44x.me]tre-080", renames,
                             "已经被合掉的目录不该再排一次改名")

    def test_collapse_refuses_when_the_parent_holds_something_the_ledger_never_saw(self):
        """账本只记文件，不记字幕、封面和空目录；不核真实目录就会把它们留在原地。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inner = root / "日本" / "TRE-080" / "[44x.me]tre-080"
            inner.mkdir(parents=True)
            (inner / "TRE-080.mp4").write_text("x", encoding="utf-8")
            operation = {"kind": "collapse",
                         "ledger_dir": r"B:\日本\TRE-080\[44x.me]tre-080",
                         "target_dir": r"B:\日本\TRE-080"}
            resolve = self._resolver(root)
            self.assertEqual(self.flatten.verify(operation, resolve), "ok")
            (inner.parent / "cover.jpg").write_text("x", encoding="utf-8")
            self.assertTrue(self.flatten.verify(operation, resolve).startswith("跳过：父目录还有"))

    def test_apply_moves_files_up_then_rewrites_the_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inner = root / "日本" / "TRE-080" / "[44x.me]tre-080"
            inner.mkdir(parents=True)
            (inner / "TRE-080.mp4").write_text("x", encoding="utf-8")
            connection = self._ledger(root, [r"B:\日本\TRE-080\[44x.me]tre-080\TRE-080.mp4"])
            operation = {"kind": "collapse",
                         "ledger_dir": r"B:\日本\TRE-080\[44x.me]tre-080",
                         "target_dir": r"B:\日本\TRE-080"}
            rows = self.flatten.plan_paths(connection, [operation])
            self.assertEqual(rows, [{"id": "1",
                                     "old_path": r"B:\日本\TRE-080\[44x.me]tre-080\TRE-080.mp4",
                                     "new_path": r"B:\日本\TRE-080\TRE-080.mp4"}])
            done = self.flatten.apply_operation(operation, self._resolver(root))
            self.assertTrue((root / "日本" / "TRE-080" / "TRE-080.mp4").is_file())
            self.assertFalse(inner.exists())
            self.flatten.rollback(done)
            self.assertTrue((inner / "TRE-080.mp4").is_file())
            connection.close()

    def test_ad_stripping_only_touches_the_head_and_tail(self):
        """欧美片名里的 `[Vixen.com]` 是厂牌，不是广告；删中间那段等于丢真信息。"""
        from peach.catalog_rules import strip_promo_markers
        self.assertEqual(strip_promo_markers("[44x.me]tre-080"), "tre-080")
        self.assertEqual(strip_promo_markers("MattieDoll - pornhub.com"), "MattieDoll")
        self.assertEqual(strip_promo_markers("[98t.tv][98t.tv]ABW-251"), "ABW-251",
                         "叠了两层广告要剥到不动为止")
        for keep in (
            "Hazel Moore - [FootFetishDaily.com] - Hardcore (18.10.19) -",
            # 整串都符合「标签+.com」，按通用形态删前缀会连番号一起吃掉、只剩 mp4
            "ABP-762-fuckbe.com.mp4",
            "(12P+5V_1.28G) [12P-5V-1.28GB]",
            "@9ririsuamano",
            "TRE-080",
        ):
            self.assertEqual(strip_promo_markers(keep), keep)

    def test_rename_only_strips_the_ad_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            connection = self._ledger(Path(tmp), [
                r"B:\日本\[44x.me]桃子作品集\one.mp4",
            ])
            plan = self.flatten.plan_operations(connection)
            connection.close()
            renames = [row for row in plan if row["kind"] == "rename"]
            self.assertEqual([(row["ledger_dir"], row["target_dir"]) for row in renames],
                             [(r"B:\日本\[44x.me]桃子作品集", r"B:\日本\桃子作品集")])


class ApplyMetadataTagsTests(unittest.TestCase):
    """直接写标签这条路必须走 `/review` 批准时的同一份写入映射。"""

    @classmethod
    def setUpClass(cls):
        cls.apply_tags = load_script("apply_metadata_tags")

    def test_it_reuses_the_review_write_mapping_instead_of_its_own_sql(self):
        """自己拼 INSERT 会漏掉删旧行、规范化标签名和 asset_entity 那一半。"""
        source = (ROOT / "scripts" / "apply_metadata_tags.py").read_text(encoding="utf-8")
        self.assertIn("from peach.web_review import _apply_metadata_candidate", source)
        self.assertNotIn("INSERT INTO asset_tag", source)

    def test_only_the_requested_source_and_field_are_written(self):
        rows = [
            {"item_key": "AAA-001:tags", "field": "tags", "status": "candidate",
             "candidates_json": json.dumps([{"source": "javbus", "value": ["素人"]},
                                            {"source": "javdb", "value": ["人妻"]}])},
            {"item_key": "AAA-001:title", "field": "title", "status": "candidate",
             "candidates_json": json.dumps([{"source": "javbus", "value": "タイトル"}])},
            {"item_key": "BBB-002:tags", "field": "tags", "status": "applied",
             "candidates_json": json.dumps([{"source": "javbus", "value": ["白虎"]}])},
        ]
        selected = self.apply_tags.plan(rows, "javbus", "tags")
        self.assertEqual([(group["item_key"], candidate["value"]) for group, candidate in selected],
                         [("AAA-001:tags", ["素人"])])

    def test_skipped_codes_stay_in_the_csv_but_do_not_reach_the_ledger(self):
        """批量放行里总有几条明显不对，跳过它们，但不许从复核产物里抹掉。

        实例：javbus 在 `MY-*` 系列的标题栏放的是「演员名+序号」而不是标题。
        过滤 CSV 会让这几条从此没人看见；跳过则它们仍在 `/review` 里等人处理。
        """
        rows = [
            {"item_key": "MY-101:title", "code": "MY-101", "field": "title",
             "status": "candidate",
             "candidates_json": json.dumps([{"source": "javbus", "value": "最上彩奈1"}])},
            {"item_key": "TRE-080:title", "code": "TRE-080", "field": "title",
             "status": "candidate",
             "candidates_json": json.dumps([{"source": "javbus", "value": "なまなかだし"}])},
        ]
        selected = self.apply_tags.plan(rows, "javbus", "title", frozenset({"my-101"}))
        self.assertEqual([group["item_key"] for group, _ in selected], ["TRE-080:title"])

    def test_apply_writes_tags_and_entities_for_the_whole_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close()
            upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.executemany(
                "INSERT INTO asset(id,location,path,name,medium,code) VALUES(?,'115',?,?,'video','TRE-080')",
                [(1, r"B:\TRE-080.mp4", "TRE-080.mp4"),
                 (2, r"B:\TRE-080-2.mp4", "TRE-080-2.mp4")])
            connection.commit()
            connection.close()

            candidates = root / "metadata-field-candidates-test.csv"
            candidate = {
                "candidate_key": "TRE-080:tags:javbus:abc", "source": "javbus",
                "confidence": 0.75, "provider": "javinizer-go",
                "source_url": "https://www.javbus.com/ja/TRE-080",
                "provider_id": "TRE-080", "content_id": "TRE-080",
                "raw_snapshot": "javbus.json", "value": ["中出内射", "素人"],
            }
            with candidates.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    "item_key", "code", "query", "field", "status", "candidates_json"])
                writer.writeheader()
                writer.writerow({
                    "item_key": "TRE-080:tags", "code": "TRE-080", "query": "TRE-080",
                    "field": "tags", "status": "candidate",
                    "candidates_json": json.dumps([candidate], ensure_ascii=False)})

            args = self.apply_tags.build_parser().parse_args(
                [str(candidates), "--db", str(db), "--apply", "--backup", str(root / "backup.db")])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(self.apply_tags.run(args), 0)
            self.assertTrue((root / "backup.db").is_file())

            connection = sqlite3.connect(db)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM asset_tag WHERE source='javinizer:javbus:tag'"
            ).fetchone()[0], 4, "两条资产各写两个标签")
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM asset_entity WHERE role='tag' "
                "AND source='javinizer:javbus:tag'").fetchone()[0], 4,
                "标签实体那一半不能漏")
            row = connection.execute(
                "SELECT status,note FROM review_decision "
                "WHERE category='metadata_fields' AND item_key='TRE-080:tags'").fetchone()
            connection.close()
            self.assertIsNotNone(row, "写完不登记，这一组会永远挂在 /review 里")
            self.assertEqual(row[0], "approved")
            self.assertEqual(json.loads(row[1])["candidate_key"],
                             "TRE-080:tags:javbus:abc",
                             "留痕必须带候选身份，_metadata_decision_is_stale 靠它判过期")

    def test_dry_run_never_touches_the_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / "candidates.csv"
            with candidates.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["item_key", "field", "status",
                                                            "candidates_json"])
                writer.writeheader()
                writer.writerow({"item_key": "A:tags", "field": "tags", "status": "candidate",
                                 "candidates_json": json.dumps([{"source": "javbus",
                                                                 "value": ["素人"]}])})
            args = self.apply_tags.build_parser().parse_args(
                [str(candidates), "--db", str(root / "missing.db")])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(self.apply_tags.run(args), 0)
            self.assertFalse((root / "missing.db").exists(), "空跑不该建库")


class ScriptingConventionTests(unittest.TestCase):
    """`peach.scripting` 收口的那几条约定，按行为而不是按源码字符串验收。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.addCleanup(self.tmp.cleanup)
        self.db = self.root / "ledger.db"
        connection = sqlite3.connect(self.db)
        connection.executescript(
            "CREATE TABLE asset(id INTEGER PRIMARY KEY);"
            "CREATE TABLE entity(id INTEGER PRIMARY KEY, kind TEXT);"
            "CREATE TABLE asset_entity(asset_id INTEGER, entity_id INTEGER);"
            "CREATE TABLE entity_alias(entity_id INTEGER, alias TEXT);"
            "CREATE TABLE asset_tag(asset_id INTEGER, tag TEXT);"
        )
        connection.execute("INSERT INTO asset(id) VALUES(1)")
        connection.executemany("INSERT INTO entity(id,kind) VALUES(?,?)",
                               [(1, "creator"), (2, "performer"), (3, "performer")])
        connection.commit()
        connection.close()

    def _args(self, **overrides):
        values = {"db": self.db, "apply": False, "backup": None}
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_readonly_connection_cannot_write_the_ledger(self):
        connection = scripting.open_readonly(self.db)
        self.addCleanup(connection.close)
        with self.assertRaises(sqlite3.OperationalError):
            connection.execute("INSERT INTO asset(id) VALUES(2)")

    def test_readonly_uri_survives_a_hash_in_the_directory_name(self):
        awkward = self.root / "a#b"
        awkward.mkdir()
        target = awkward / "ledger.db"
        sqlite3.connect(target).close()
        connection = scripting.open_readonly(target)
        self.addCleanup(connection.close)
        self.assertEqual(connection.execute("SELECT 1").fetchone()[0], 1)

    def test_dry_run_gets_a_read_only_connection_and_writes_no_backup(self):
        backup = self.root / "unused.db"
        connection = scripting.open_for_write(self._args(backup=backup))
        self.addCleanup(connection.close)
        with self.assertRaises(sqlite3.OperationalError):
            connection.execute("INSERT INTO asset(id) VALUES(2)")
        self.assertFalse(backup.exists(), "dry-run 不该产生备份")

    def test_apply_without_backup_is_refused_with_the_single_house_wording(self):
        with self.assertRaises(SystemExit) as caught:
            scripting.open_for_write(self._args(apply=True))
        self.assertEqual(str(caught.exception), "--apply 必须同时给 --backup")

    def test_apply_backup_keeps_transactions_that_are_still_only_in_the_wal(self):
        """WAL 里已提交未 checkpoint 的事务必须进备份；文件复制会把它们丢掉。"""
        writer = sqlite3.connect(self.db)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO asset(id) VALUES(99)")
        writer.commit()
        self.addCleanup(writer.close)

        backup = self.root / "backup.db"
        connection = scripting.open_for_write(self._args(apply=True, backup=backup))
        self.addCleanup(connection.close)
        connection.execute("INSERT INTO asset(id) VALUES(100)")
        connection.commit()

        saved = sqlite3.connect(backup)
        self.addCleanup(saved.close)
        ids = {row[0] for row in saved.execute("SELECT id FROM asset")}
        self.assertIn(99, ids, "WAL 中的已提交事务丢了")
        self.assertNotIn(100, ids, "备份必须是写入之前的状态")

    def test_counts_of_reports_the_shared_base_plus_the_callers_own_measures(self):
        connection = scripting.open_readonly(self.db)
        self.addCleanup(connection.close)
        counts = scripting.counts_of(connection, {
            "performer": "SELECT count(*) FROM entity WHERE kind='performer'",
            "asset_tag": "SELECT count(*) FROM asset_tag",
        })
        self.assertEqual(counts, {"asset": 1, "entity": 3, "asset_entity": 0,
                                  "entity_alias": 0, "performer": 2, "asset_tag": 0})

    def test_ledger_write_args_are_exactly_db_apply_backup(self):
        parser = scripting.add_ledger_write_args(argparse.ArgumentParser())
        parsed = parser.parse_args(["--db", str(self.db), "--apply",
                                    "--backup", str(self.root / "b.db")])
        self.assertEqual((parsed.db, parsed.apply, parsed.backup),
                         (self.db, True, self.root / "b.db"))
        self.assertFalse(parser.parse_args([]).apply)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--database", str(self.db)])

    #: 会真写 ledger、已经收口到本模块的脚本。
    LEDGER_WRITERS = (
        "backfill_rule34_tag_types",
        "clean_names",
        "install_entity_links",
        "localize_performer_names",
        "localize_series_names",
        "merge_duplicate_identities",
    )

    def test_every_ledger_writer_takes_the_same_three_write_arguments(self):
        """写入脚本的参数名只有一套。

        曾经并存 `--database`（必填）和 `--backup-dir`（目录）。名字不同的同义参数会让
        「上次那条命令」在另一个脚本上直接报错，而报错只说缺参数——不说改成什么。
        """
        for name in self.LEDGER_WRITERS:
            with self.subTest(script=name):
                parser = load_script(name).build_parser()
                dests = {action.dest for action in parser._actions}
                self.assertLessEqual({"db", "apply", "backup"}, dests)
                self.assertNotIn("database", dests)
                self.assertNotIn("backup_dir", dests)

    def test_every_ledger_writer_opens_the_ledger_through_this_module(self):
        """连接、备份、拒绝三件事只有一处实现。

        判据落在「用的是不是同一个函数」上，而不是源码里出现过哪个字符串：脚本各自
        `sqlite3.connect` 时，dry-run 拿到的是可写连接，「这一趟绝不写库」只是靠读代码
        维持的约定。
        """
        for name in self.LEDGER_WRITERS:
            with self.subTest(script=name):
                module = load_script(name)
                self.assertIs(module.open_for_write, scripting.open_for_write)

    def test_rate_limiter_waits_the_remainder_rather_than_the_full_interval(self):
        now = [100.0]
        slept: list[float] = []

        def sleeper(seconds):
            slept.append(seconds)
            now[0] += seconds

        limiter = scripting.RateLimiter(2.0, clock=lambda: now[0], sleeper=sleeper)
        limiter.wait()
        self.assertEqual(slept, [], "第一次不该等")
        now[0] += 1.5                        # 本地处理已经花了 1.5 秒
        limiter.wait()
        self.assertEqual(slept, [0.5], "只该补齐差额，不是又睡满一个间隔")
        now[0] += 5.0
        limiter.wait()
        self.assertEqual(slept, [0.5], "间隔已过就不再等")

    def test_zero_interval_rate_limiter_never_sleeps(self):
        slept: list[float] = []
        limiter = scripting.RateLimiter(0, sleeper=slept.append)
        limiter.wait()
        limiter.wait()
        self.assertEqual(slept, [])

    def test_host_limiter_matches_on_dot_boundaries_not_substrings(self):
        now = [0.0]
        slept: list[float] = []

        def sleeper(seconds):
            slept.append(seconds)
            now[0] += seconds

        limiter = scripting.HostLimiter({"x.com": 2.0}, clock=lambda: now[0],
                                        sleeper=sleeper)
        limiter.wait("https://netflix.com/a")
        limiter.wait("https://netflix.com/b")
        self.assertEqual(slept, [], "netflix.com 不是 x.com 的子域，不该被限速")
        limiter.wait("https://mobile.x.com/a")
        limiter.wait("https://www.x.com/b")
        self.assertEqual(slept, [2.0], "同一主机的第二次请求必须等一个间隔")

    def test_host_under_rejects_a_domain_that_merely_ends_with_the_key(self):
        self.assertTrue(scripting.host_under("x.com", ("x.com",)))
        self.assertTrue(scripting.host_under("mobile.X.com", ("x.com",)))
        self.assertFalse(scripting.host_under("notx.com", ("x.com",)))
        self.assertFalse(scripting.host_under("", ("x.com",)))


if __name__ == "__main__":
    unittest.main()
