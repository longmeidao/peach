import argparse
import csv
import hashlib
import importlib.util
import io
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import tomllib
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
        # `scripting` 那条回归测试守住；这里只钉「用的是那一份」。断言源码里有没有
        # `reader.backup(writer)` 这串字符的话，脚本一改成调用共享实现就会红——
        # 而那次行为恰恰是变好了。
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
        self.assertIn("$env:PYTHONIOENCODING = 'utf-8'", windows)
        self.assertIn("$env:PYTHONIOENCODING = $PreviousPythonIoEncoding", windows)
        self.assertIn("$LocalPython = Join-Path $WorktreeRoot", windows)
        self.assertIn("peach.__file__", windows)
        self.assertIn("scripts\\test_runner.py --scope $Scope", windows)
        self.assertIn("ValidateSet('full', 'auto', 'follow'", windows)
        self.assertNotIn("pytest", windows.lower())
        # 两个平台各有一个入口，契约必须相同——否则「两边都要绿」只是句口号。
        posix = (ROOT / "scripts" / "test.sh").read_text(encoding="utf-8")
        self.assertIn("rev-parse --git-common-dir", posix)
        self.assertIn('export PYTHONPATH="$SOURCE_ROOT"', posix)
        self.assertIn("export PYTHONIOENCODING=utf-8", posix)
        self.assertNotIn("    SCOPE=full", posix)
        self.assertIn("peach.__file__", posix)
        self.assertIn('scripts/test_runner.py --scope "$SCOPE"', posix)
        self.assertIn('SCOPE="${1:-auto}"', posix)
        self.assertIn("full|auto|follow|catalog|media|sync|metadata|tooling|web|checks|core|packaging)", posix)
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

    def test_posix_entrypoint_passes_extra_args_through_on_bash_3_2(self):
        """不带额外参数直接跑 `./scripts/test.sh` 必须能跑起来，参数要原样透传。

        macOS 自带 bash 3.2.57，`set -u` 下空数组的 `"${EXTRA[@]}"` 被判成未绑定变量
        （bash 4.4 起才不报），入口于是在最后一行崩掉。CI 每次都附带
        `--fresh --base <sha> --shard-*`，数组从不为空，这条路径只有本机会走到——而
        AGENTS.md 规定 macOS 的唯一测试入口就是这个脚本，崩了等于没有测试门槛。

        文本判据钉住修法本身：`set -euo pipefail` 必须还在（把 `set +u` 当解法会让
        其余变量的拼写错误没人拦），展开必须是 `${EXTRA[@]+...}` 那一种。行为判据从
        真实脚本里截出参数处理那一段来跑，改回裸展开时这一段会跟着变。
        """
        source = (ROOT / "scripts" / "test.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", source)
        self.assertIn('scripts/test_runner.py --scope "$SCOPE" ${EXTRA[@]+"${EXTRA[@]}"}', source)
        self.assertNotIn('--scope "$SCOPE" "${EXTRA[@]}"', source)

        # 真实脚本后半段要定位 venv 并跑整个测试套件，直接执行会递归。只取参数处理那一段，
        # 把 exec 的目标换成一个回显 argv 的桩，其余保持逐字一致。
        marker = 'EXTRA=("${@:2}")\n'
        prologue, separator, tail = source.partition(marker)
        self.assertEqual(separator, marker)
        exec_line = next(line for line in tail.splitlines() if line.startswith("exec "))
        stub_line = exec_line.replace('"$PYTHON" scripts/test_runner.py',
                                      '"$PEACH_PY" "$PEACH_STUB"', 1)
        self.assertNotEqual(stub_line, exec_line)

        directory = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, directory, True)
        stub = directory / "argv_stub.py"
        stub.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
        entrypoint = directory / "prologue.sh"
        # 两个路径都写成正斜杠：Windows 的 `C:\Users\…` 落进 shell 脚本后反斜杠会被当成转义符
        # 吃掉，exec 拿到的是一个粘在一起的名字。解释器也显式写出来，不靠 `#!`——Git Bash
        # 不按 shebang 找 Windows 上的 Python。
        entrypoint.write_text(
            f'{prologue}{marker}'
            f'PEACH_PY={Path(sys.executable).as_posix()}\n'
            f'PEACH_STUB={stub.as_posix()}\n'
            f'{stub_line}\n', encoding="utf-8")

        # `/bin/bash` 在 macOS 上就是那个 3.2；装了新版 bash 的机器两个都跑。
        shells = [path for path in ("/bin/bash", shutil.which("bash")) if path and Path(path).exists()]
        self.assertTrue(shells)
        for shell in dict.fromkeys(shells):
            for argv, expected in (
                    ([], ["--scope", "auto"]),
                    (["auto"], ["--scope", "auto"]),
                    (["web", "--fresh", "--base", "a b"],
                     ["--scope", "web", "--fresh", "--base", "a b"]),
            ):
                with self.subTest(shell=shell, argv=argv):
                    done = subprocess.run(
                        [shell, str(entrypoint), *argv],
                        capture_output=True, text=True, encoding="utf-8", check=False)
                    self.assertEqual(done.returncode, 0, done.stderr)
                    self.assertEqual(json.loads(done.stdout), expected)

    def test_python_floor_is_declared_once_and_ci_tests_both_ends(self):
        """`requires-python` 是唯一真相；CI 矩阵与两份 README 都从它推出来。

        下限是陌生用户按 `pip install` 装的那一端，3.14 是维护者本机运行的那一端；
        两端都在矩阵里，README 的前置条件写的也是同一个下限，三处任一处单改都要红。
        """
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        floor = project["requires-python"].removeprefix(">=")
        self.assertEqual(floor, "3.12")
        for version in (floor, "3.14"):
            self.assertIn(f"Programming Language :: Python :: {version}", project["classifiers"])
        workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        self.assertIn("fromJSON(needs.plan.outputs.matrix)", workflow)
        from scripts.ci_plan import plan
        self.assertEqual({row["python"] for row in plan("workflow_dispatch", [])["matrix"]["include"]}, {floor, "3.14"})
        self.assertIn(f"Python {floor} 或更高", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(f"Python {floor} or newer", (ROOT / "README.en.md").read_text(encoding="utf-8"))

    def test_functional_test_scopes_are_explicit(self):
        runner = load_script("test_runner")
        follow = {path.name for path in runner.selected_files("follow")}
        full = {path.name for path in runner.selected_files("full")}
        self.assertIn("test_follow_web.py", follow)
        self.assertIn("test_migrations.py", follow)
        self.assertNotIn("test_media.py", follow)
        self.assertGreater(len(full), len(follow))
        with redirect_stdout(io.StringIO()) as listed:
            self.assertEqual(runner.main(["--list-scopes"]), 0)
        self.assertEqual(listed.getvalue().split(), ["full", "auto", *runner.SCOPES])

    def test_every_test_file_is_registered_in_a_scope(self):
        """新测试文件必须登记进 `scripts/test_runner.py` 的域，否则只有 `full` 才跑到它。"""
        runner = load_script("test_runner")
        patterns = (*runner.COMMON_PATTERNS,
                    *(pattern for scopes in runner.SCOPES.values() for pattern in scopes))
        orphans = sorted(
            path.name for path in (ROOT / "tests").glob("test_*.py")
            if not any(path.match(pattern) for pattern in patterns))
        self.assertEqual(
            orphans, [],
            "这些测试文件不属于任何域，把它们登记进 scripts/test_runner.py 的 SCOPES"
            "（或 COMMON_PATTERNS），否则只有 full 才跑到它们：\n  " + "\n  ".join(orphans))

    def test_auto_scope_maps_changed_files_and_falls_back_to_full(self):
        """`auto` 的选域是纯函数：喂文件清单，不碰 git。"""
        runner = load_script("test_runner")
        pick = runner.scopes_for_changes
        # 前缀表：多个文件取并集，反斜杠路径也认。
        self.assertEqual(pick(["src/peach/follow_store.py", "web/app.js"])[0], ("follow", "web"))
        self.assertEqual(pick(["src\\peach\\tray.py"])[0], ("sync",))
        self.assertEqual(pick(["scripts/probe.py", "pyproject.toml", ".github/workflows/test.yml"])[0],
                         ("full",))
        self.assertEqual(pick(["README.md", "docs/STATUS.md", ".claude/skills/x/SKILL.md"])[0],
                         ("checks",))
        self.assertEqual(pick(["src/peach/web_entity.py", "src/peach/routes_pages.py"])[0],
                         ("catalog", "tooling", "web"))
        self.assertEqual(pick(["src/peach/web_follow.py"])[0], ("follow",))
        # 模块名 ↔ 测试文件名推断，登记在几个域就跑几个域。
        self.assertEqual(pick(["src/peach/media.py"])[0], ("media",))
        self.assertEqual(pick(["src/peach/jobs.py"])[0], ("media", "tooling"))
        # `test_metadata_library.py` 也登记在 web 域（它有一段读 `web/app.js`），
        # 名字又落在 `test_metadata_` 这一族里，于是这个模块把 web 域一起带上。
        # 宽一档是安全的那一侧，web 域全是源码文本断言，代价只有几秒。
        self.assertEqual(pick(["src/peach/metadata.py"])[0], ("metadata", "web"))
        # 测试文件按自己的文件名归域；公共门槛文件归 tooling。
        self.assertEqual(pick(["tests/test_certs.py"])[0], ("sync", "tooling"))
        self.assertEqual(pick(["tests/test_context_budget.py"])[0], ("tooling",))
        scopes, why = pick(["src/peach/follow.py", "web/app.js"])
        self.assertTrue(why.startswith("Peach auto scope: follow, web <- "), why)
        self.assertIn("web: web/app.js", why)
        self.assertEqual(pick([])[0], ("checks",))
        # full 覆盖公共设施和未知影响面。
        for paths, fragment in ((["migrations/0099_next.sql"], "必须 full"),
                                (["tests/support/ledger.py"], "必须 full"),
                                (["tests/conftest.py"], "必须 full"),
                                (["package-lock.json"], "必须 full"),
                                (["frontend/package.json"], "必须 full"),
                                (["LICENSE"], "映射不到"),
                                (["src/peach/kanji.py", "web/app.js"], "映射不到")):
            scopes, why = pick(paths)
            self.assertEqual(scopes, ("full",), paths)
            self.assertTrue(why.startswith("Peach auto scope: full <- "), why)
            self.assertIn(fragment, why)

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

    def test_the_plate_colour_follows_the_marks_own_brightness(self):
        """浅色笔画配深底，自带整块底的一律白底。

        笔画直接挨着底色的标识才会被底色吞掉：白笔画配白底等于把它抹掉。自带整
        块底的标识边界是自己画的，外面那圈只是画框，配深底反而让那块底浮在黑里。
        """
        import io

        from PIL import Image

        from peach.images import bake_square

        def png(image):
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            return buffer.getvalue()

        strokes = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
        for x in list(range(20, 80)) + list(range(120, 180)):
            for y in range(10, 50):
                strokes.putpixel((x, y), (255, 255, 255, 255))
        with Image.open(io.BytesIO(bake_square(png(strokes)))) as plate:
            self.assertEqual(plate.convert("RGB").getpixel((2, 2)), (17, 17, 17),
                             "白笔画配深底才看得见")

        card = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
        for x in range(20, 180):
            for y in range(10, 50):
                card.putpixel((x, y), (255, 255, 255, 255))
        for x in range(60, 140):
            for y in range(24, 36):
                card.putpixel((x, y), (196, 20, 24, 255))
        with Image.open(io.BytesIO(bake_square(png(card)))) as plate:
            self.assertEqual(plate.convert("RGB").getpixel((2, 2)), (255, 255, 255),
                             "自带整块白底的标识，外面那圈跟着它一起白")

    def test_a_square_plate_is_refit_so_the_round_slot_shows_the_whole_mark(self):
        """不透明方图重新摆位：内容太小裁掉留白，会被圆片切掉就补到外接圆。

        小圆片（`.brandpill .mk`）是 32 px 圆、`cover` 铺满，铺满的是整张画布不是
        内容。源站 favicon 常自带大留白，铺进去内容小得认不出；顶到边的实心方标
        四角落在圆外，那部分直接看不见。像素一律不缩放。
        """
        import io
        from math import ceil, hypot

        from PIL import Image, ImageDraw

        from peach.images import PLATE_CONTENT_RATIO, refit_plate

        def png(image):
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            return buffer.getvalue()

        def side(payload):
            with Image.open(io.BytesIO(payload)) as opened:
                self.assertEqual(opened.size[0], opened.size[1])
                return opened.size[0]

        roomy = Image.new("RGB", (400, 400), (255, 255, 255))
        ImageDraw.Draw(roomy).rectangle((160, 160, 239, 239), fill=(196, 20, 24))
        cropped = refit_plate(png(roomy))
        self.assertEqual(side(cropped), round(80 / PLATE_CONTENT_RATIO),
                         "裁到内容框，四周各留约 12%")
        with Image.open(io.BytesIO(cropped)) as plate:
            self.assertEqual(plate.getpixel((plate.width // 2, plate.height // 2)),
                             (196, 20, 24), "像素不缩放，只是换了画布")
        self.assertEqual(refit_plate(cropped), cropped, "摆好的不再动")

        speckled = roomy.copy()
        for spot in ((6, 6), (392, 8), (10, 390), (388, 394)):
            speckled.putpixel(spot, (250, 250, 250))
        self.assertEqual(side(refit_plate(png(speckled))), side(cropped),
                         "有损压缩留下的零星斑点不算内容，撑不开内容框")

        packed = Image.new("RGB", (400, 400), (255, 255, 255))
        ImageDraw.Draw(packed).rectangle((20, 20, 379, 379), fill=(196, 20, 24))
        padded = refit_plate(png(packed))
        self.assertEqual(side(padded), ceil(hypot(359, 359)),
                         "补到内容的外接圆，直径就是内容框的对角线，四角不再被圆片切掉")
        with Image.open(io.BytesIO(padded)) as plate:
            self.assertEqual(plate.getpixel((2, 2)), (255, 255, 255),
                             "补出来的边取原图底色")

        circular = Image.new("RGB", (400, 400), (255, 255, 255))
        ImageDraw.Draw(circular).ellipse((0, 0, 399, 399), fill=(196, 20, 24))
        payload = png(circular)
        self.assertEqual(refit_plate(payload), payload, "本来就是圆的图标一个字节不动")

        strip = png(Image.new("RGB", (400, 100), (196, 20, 24)))
        self.assertEqual(refit_plate(strip), strip, "条状字标的摆位归 pad_to_square 管")

        transparent = png(Image.new("RGBA", (200, 200), (0, 0, 0, 0)))
        self.assertEqual(refit_plate(transparent), transparent,
                         "还没配底的图没有底色可取，补出来的边会变成黑块")
        self.assertIsNone(refit_plate(b"not an image"))

    def test_a_plate_smaller_than_the_round_slot_grows_to_it_without_rescaling(self):
        """短边不够小圆片的实像素就用自己的底色补上去，笔画一个像素都不缩放。

        小圆片是 32 CSS px、2 倍屏 64 实像素。短边不够时浏览器只能放大整张图；
        补边换来的是笔画按原样出图，代价是标识相对圆片小一档。补到内容占宽的下限
        为止——再往外撑就成了另一条规则要裁掉的大留白，两条会来回拉锯。
        """
        import io

        from PIL import Image, ImageDraw

        from peach.images import PLATE_MIN_SIDE, PLATE_MIN_SPAN, refit_plate

        def png(image):
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            return buffer.getvalue()

        def opened(payload):
            with Image.open(io.BytesIO(payload)) as image:
                return image.convert("RGB"), image.size

        small = Image.new("RGB", (48, 48), (18, 140, 220))
        ImageDraw.Draw(small).rectangle((4, 4, 43, 43), fill=(255, 255, 255))
        grown = refit_plate(png(small))
        image, size = opened(grown)
        self.assertEqual(size, (PLATE_MIN_SIDE, PLATE_MIN_SIDE), "补到圆片要的实像素")
        self.assertEqual(image.getpixel((1, 1)), (18, 140, 220), "补出来的边取原图底色")
        self.assertEqual(image.getpixel((PLATE_MIN_SIDE // 2, PLATE_MIN_SIDE // 2)),
                         (255, 255, 255), "内容原样居中，像素不缩放")
        self.assertEqual(refit_plate(grown), grown, "补好的不再动")

        sparse = Image.new("RGB", (40, 40), (18, 140, 220))
        ImageDraw.Draw(sparse).rectangle((16, 16, 27, 27), fill=(255, 255, 255))
        capped = refit_plate(png(sparse))
        _, size = opened(capped)
        self.assertEqual(size, (int(12 / PLATE_MIN_SPAN),) * 2,
                         "内容小的补到占宽下限就停，不补到 64")
        self.assertEqual(refit_plate(capped), capped, "停在下限上，两条规则不再拉锯")

        big = Image.new("RGB", (PLATE_MIN_SIDE, PLATE_MIN_SIDE), (18, 140, 220))
        ImageDraw.Draw(big).rectangle((8, 8, 55, 55), fill=(255, 255, 255))
        payload = png(big)
        self.assertEqual(refit_plate(payload), payload, "够实像素的一个字节不动")

    def test_a_vector_mark_gets_the_same_plate_without_rasterising(self):
        """矢量标识：白底和边距一样烤进文件，但是包一层外层 SVG，原文档不动。

        VirtualTaboo 装的就是一张 207×70 的透明底字标。栅格化会把「放多大都清晰」
        这个唯一优势丢掉，所以方底由外层 SVG 给，内容整个塞进嵌套 `<svg>`。
        """
        import xml.etree.ElementTree as ElementTree

        from peach.images import (PLATE_CONTENT_RATIO, SVG_NS, bake_square_vector,
                                  vector_image_size)

        def svg(body, box="0 0 207 70"):
            return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}">'
                    f'{body}</svg>').encode("utf-8")

        wordmark = ('<svg xmlns="http://www.w3.org/2000/svg" width="207" height="70" '
                    'viewBox="0 0 207 70"><path fill="#D14747" d="M105 49h9v3z"/>'
                    '</svg>').encode("utf-8")

        self.assertEqual(vector_image_size(wordmark), (207.0, 70.0))
        plated = bake_square_vector(wordmark)
        self.assertIn(b'd="M105 49h9v3z"', plated, "原文档照抄，不栅格化")

        root = ElementTree.fromstring(plated)
        side = float(root.get("width"))
        self.assertEqual(root.get("height"), root.get("width"), "包出来必须是方的")
        self.assertAlmostEqual(207 / side, PLATE_CONTENT_RATIO, places=6,
                               msg="长边占边长约 76%，四周各留约 12%")
        plate, inner = list(root)
        self.assertEqual(plate.tag, f"{{{SVG_NS}}}rect")
        self.assertEqual(plate.get("fill"), "#ffffff", "底是白的")
        self.assertEqual(plate.get("width"), root.get("width"), "白底铺满整个方框")
        self.assertEqual(inner.get("viewBox"), "0 0 207 70", "内容自己的坐标系不变")
        self.assertAlmostEqual(float(inner.get("x")), (side - 207) / 2, places=6)
        self.assertAlmostEqual(float(inner.get("y")), (side - 70) / 2, places=6)

        self.assertEqual(bake_square_vector(plated), plated,
                         "已经包过方底的原样返回，重复跑不会越套越多")

        # 白字标配白底等于把标识抹掉：DarkRoomVR 的「DARK ROOM」和
        # TeamSkeetXReislin 的「TEAM」都是白的，白底可见率 0.20 与 0.52。
        def strokes(color):
            return svg(f'<rect x="10" y="10" width="60" height="50" fill="{color}"/>'
                       f'<rect x="137" y="10" width="60" height="50" fill="{color}"/>')

        pale = bake_square_vector(strokes("#ffffff"))
        self.assertEqual(ElementTree.fromstring(pale)[0].get("fill"), "#111111",
                         "浅色内容改配深底")
        self.assertEqual(
            ElementTree.fromstring(bake_square_vector(strokes("#101820")))[0]
            .get("fill"), "#ffffff", "深色内容仍是白底，和位图的 mark 一条规则")
        self.assertEqual(
            ElementTree.fromstring(bake_square_vector(svg(
                '<rect x="10" y="10" width="187" height="50" fill="#ffffff"/>')))[0]
            .get("fill"), "#ffffff", "自带整块底的标识不判底色，外面那圈跟着它一起白")
        # 空壳没有 viewBox 也没有 width／height：比例无从算起，方框边长也就无从定。
        self.assertIsNone(vector_image_size(b'<svg xmlns="http://www.w3.org/2000/svg"/>'))
        self.assertIsNone(bake_square_vector(b'<svg xmlns="http://www.w3.org/2000/svg"/>'))
        self.assertIsNone(bake_square_vector(b"not an image"))
        self.assertIsNone(bake_square_vector(b"<html><body>404</body></html>"))

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
        烤白底，不透明的长条补方，矢量包一层白底外层 SVG，已经归一的一个字节都不动。
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
        roomy = Image.new("RGB", (200, 200), (255, 255, 255))
        for x in range(80, 120):
            for y in range(80, 120):
                roomy.putpixel((x, y), (196, 20, 24))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / "logos"
            backup = Path(tmp).resolve() / "backup"
            root.mkdir()
            originals = {
                "wide.img": png(Image.new("RGB", (400, 100), (196, 20, 24))),
                "flat.icon.img": png(Image.new("RGB", (256, 256), (12, 12, 12))),
                "spot.icon.img": png(roomy),
                "sign.logo.img": png(mark),
                "vector.img": b'<svg xmlns="http://www.w3.org/2000/svg"/>',
                "sign.icon.img": ('<svg xmlns="http://www.w3.org/2000/svg" '
                                  'viewBox="0 0 200 60"><path d="M1 1h2v2z"/>'
                                  '</svg>').encode("utf-8"),
            }
            vectors = {"vector.img", "sign.icon.img"}
            for name, payload in originals.items():
                (root / name).write_bytes(payload)
                Path(f"{root / name}.ct").write_text(
                    "image/svg+xml" if name in vectors else "image/png",
                    encoding="utf-8")

            dry = {str(row["file"]): row for row in module.normalize(root)}
            self.assertEqual(dry["wide.img"]["action"], "would-pad")
            self.assertEqual(dry["wide.img"]["kind"], "tile")
            self.assertEqual(dry["sign.logo.img"]["action"], "would-bake")
            self.assertEqual(dry["sign.logo.img"]["kind"], "mark")
            self.assertEqual(dry["spot.icon.img"]["action"], "would-refit",
                             "已经是方图、只是内容太小的记重新摆位，不冒充补方")
            self.assertEqual(dry["spot.icon.img"]["kind"], "tile")
            self.assertEqual(dry["sign.icon.img"]["action"], "would-plate")
            self.assertEqual(dry["sign.icon.img"]["kind"], "vector")
            self.assertEqual(dry["vector.img"]["action"], "vector",
                             "连内容框都没声明，方框边长无从算起，单列出来而不是记成坏文件")
            self.assertNotIn("flat.icon.img", dry, "已经是不透明方图，不进复核件")
            for name, payload in originals.items():
                self.assertEqual((root / name).read_bytes(), payload, "dry-run 不得改图")
            with self.assertRaises(ValueError):
                module.normalize(root, apply=True)

            applied = {str(row["file"]): row for row in
                       module.normalize(root, apply=True, backup_dir=backup)}
            self.assertEqual(applied["wide.img"]["action"], "padded")
            self.assertEqual(applied["sign.logo.img"]["action"], "baked")
            self.assertEqual(applied["spot.icon.img"]["action"], "refitted")
            self.assertEqual(applied["sign.icon.img"]["action"], "plated")
            self.assertEqual((backup / "sign.icon.img").read_bytes(),
                             originals["sign.icon.img"])
            self.assertIn(b'd="M1 1h2v2z"', (root / "sign.icon.img").read_bytes(),
                          "矢量原文档照抄进外层 SVG，没有被栅格化")
            self.assertEqual(Path(f'{root / "sign.icon.img"}.ct').read_text(
                encoding="utf-8"), "image/svg+xml", "包完还是 SVG，类型不能改成 png")
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
                                 ("spot.icon.img", "refit-plate"),
                                 ("sign.logo.img", "bake-white-plate"),
                                 ("sign.icon.img", "plate-vector")):
                sidecar = json.loads(
                    Path(f"{root / name}.normalization.json").read_text(encoding="utf-8"))
                self.assertEqual(sidecar["action"], action)
                self.assertEqual(sidecar["original_sha256"],
                                 hashlib.sha256(originals[name]).hexdigest())
                self.assertEqual(sidecar["normalized_sha256"],
                                 hashlib.sha256((root / name).read_bytes()).hexdigest())
                self.assertEqual(sidecar["backup"], str(backup / name))
                if name not in vectors:
                    self.assertEqual(
                        Path(f"{root / name}.ct").read_text(encoding="utf-8"), "image/png")

            # 重跑不再有动作：位图是不透明方图，矢量已经包过方底，归一是幂等的。
            # 量不出内容框的那一行照旧每次都在，它是「还没处理」的记录，不是待办完成。
            self.assertEqual([row["action"] for row in module.normalize(root)],
                             ["vector"])

    def test_normalising_again_takes_the_backup_original_as_its_input(self):
        """已归一的文件重跑时输入取边车记的备份原图。

        烤底会毁掉透明通道，配错的底色在产物上再也判不回来。从原图重来，算法的
        改进才能落到已经装好的文件上；边车继续指向原图，别把指针改指到这一轮备份
        的归一产物。备份不在本机时只能拿现装的文件当输入。
        """
        from PIL import Image

        module = load_script("normalize_studio_logos")

        def png(image):
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            return buffer.getvalue()

        strokes = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
        for x in list(range(20, 80)) + list(range(120, 180)):
            for y in range(10, 50):
                strokes.putpixel((x, y), (255, 255, 255, 255))
        original = png(strokes)
        swallowed = Image.new("RGB", (211, 211), (255, 255, 255))
        swallowed.paste(strokes.convert("RGB"), (5, 75), strokes)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / "logos"
            archive = Path(tmp).resolve() / "archive"
            backup = Path(tmp).resolve() / "backup"
            root.mkdir()
            archive.mkdir()
            (archive / "sign.img").write_bytes(original)
            installed = png(swallowed)
            (root / "sign.img").write_bytes(installed)
            Path(f'{root / "sign.img"}.ct').write_text("image/png", encoding="utf-8")
            Path(f'{root / "sign.img"}.normalization.json').write_text(json.dumps({
                "action": "bake-white-plate", "kind": "mark",
                "backup": str(archive / "sign.img"),
            }), encoding="utf-8")

            applied = {str(row["file"]): row for row in
                       module.normalize(root, apply=True, backup_dir=backup)}
            self.assertEqual(applied["sign.img"]["action"], "baked")
            self.assertEqual(applied["sign.img"]["backup"], str(archive / "sign.img"))
            self.assertEqual(applied["sign.img"]["before_sha256"],
                             hashlib.sha256(installed).hexdigest(),
                             "复核件上的 before 是被替换掉的那个文件")
            with Image.open(root / "sign.img") as plate:
                self.assertEqual(plate.convert("RGB").getpixel((2, 2)), (17, 17, 17),
                                 "从原图重来才判得出白笔画该配深底")
            sidecar = json.loads(Path(f'{root / "sign.img"}.normalization.json')
                                 .read_text(encoding="utf-8"))
            self.assertEqual(sidecar["backup"], str(archive / "sign.img"),
                             "边车继续指向原图")
            self.assertEqual(sidecar["original_sha256"],
                             hashlib.sha256(original).hexdigest())
            self.assertEqual((backup / "sign.img").read_bytes(), installed,
                             "这一轮换掉的文件也留一份")
            self.assertEqual([row["action"] for row in module.normalize(root)], [],
                             "原图再走一遍还是同一个产物，归一是幂等的")

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

    def test_scrape_falls_back_to_the_other_writing_of_the_same_code(self):
        """`LUXU-1642` 与 `259LUXU-1642` 是同一部作品，来源各只索引其中一种。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.execute(
                "INSERT INTO asset(id,location,path,name,medium,code) "
                "VALUES(1,'local','one.mp4','one.mp4','video','LUXU-1642')")
            connection.commit(); connection.close()

            self_error = self.scrape_codes.MetadataProviderError

            class PrefixOnlyProvider:
                def __init__(self): self.calls = []
                def query(self, code, source):
                    self.calls.append((code, source))
                    if code == "LUXU-1642":
                        raise self_error("status 404", kind="not_found",
                                         status_code=404, retryable=False, temporary=False)
                    return {"source": source, "id": "259LUXU-1642", "maker": "Maan Sha"}

            provider = PrefixOnlyProvider()
            raw = root / "raw"
            output = root / "candidates.csv"
            errors = root / "errors.csv"
            with redirect_stdout(io.StringIO()):
                result = self.scrape_codes.main([
                    "--db", str(db), "--out", str(output), "--errors", str(errors),
                    "--raw-dir", str(raw), "--log-dir", str(root / "logs"),
                    "--delay", "0", "--min-free", "0", "--sources", "javbus",
                ], provider=provider)
            self.assertEqual(result, 0)
            self.assertEqual(provider.calls,
                             [("LUXU-1642", "javbus"), ("259LUXU-1642", "javbus")])
            # 两种写法各自留证据，回退命中的那次不覆盖原写法的失败快照。
            self.assertTrue((raw / "LUXU-1642" / "javbus.json").is_file())
            self.assertTrue((raw / "259LUXU-1642" / "javbus.json").is_file())
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            studio = next(row for row in rows if row["field"] == "studio")
            # 评审键仍按账本的规范写法，不随回退漂移。
            self.assertEqual((studio["query"], studio["item_key"]),
                             ("LUXU-1642", "LUXU-1642:studio"))
            with errors.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.DictReader(handle)), [], "回退命中不算失败")

    def test_scrape_rejects_a_source_result_for_a_different_release(self):
        """javbus 搜不到就返回首个近似命中：`CHU-101` 会取回 `CHUC-101`。

        韩国 MIB 那批番号由 `allows_code` 拦在刮削入口，走不到这里；这道守卫管的是
        剩下那些形状相近的误配，它们没有前缀表可依，只能靠比对来源自报的番号认出来。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ledger.db"
            sqlite3.connect(db).close(); upgrade(db, MIGRATIONS)
            connection = sqlite3.connect(db)
            connection.executemany(
                "INSERT INTO asset(id,location,path,name,medium,code) "
                "VALUES(?,'local',?,?,'video',?)",
                [(1, "1.mp4", "1.mp4", "CHU-101"), (2, "2.mp4", "2.mp4", "IQQQ-026"),
                 (3, "3.mp4", "3.mp4", "390JAC-040")])
            connection.commit(); connection.close()

            class LooseSearchProvider:
                def query(self, code, source):
                    if code == "CHU-101":
                        return {"source": source, "id": "CHUC-101", "maker": "别人的厂牌"}
                    if code in {"390JAC-040", "JAC-040"}:
                        return {"source": source, "id": "JAC-040", "content_id": "118jac040",
                                "source_url": "https://r18.dev/videos/vod/movies/detail/-/combined=118jac040/json",
                                "maker": "Prestige"}
                    return {"source": source, "id": "IQQQ-26", "maker": "Attackers"}

            raw = root / "raw"
            output = root / "candidates.csv"
            errors = root / "errors.csv"
            with redirect_stdout(io.StringIO()):
                result = self.scrape_codes.main([
                    "--db", str(db), "--out", str(output), "--errors", str(errors),
                    "--raw-dir", str(raw), "--log-dir", str(root / "logs"),
                    "--delay", "0", "--min-free", "0", "--sources", "javbus",
                ], provider=LooseSearchProvider())
            self.assertEqual(result, 0)
            with errors.open(encoding="utf-8-sig", newline="") as handle:
                error_rows = list(csv.DictReader(handle))
            self.assertCountEqual([(row["code"], row["kind"]) for row in error_rows],
                             [("390JAC-040", "identity_mismatch"), ("CHU-101", "identity_mismatch")])
            self.assertTrue(any("CHUC-101" in row["message"] for row in error_rows))
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            # 补零差异是良性的，`IQQQ-26` 必须照常收下。
            self.assertEqual({row["code"] for row in rows}, {"IQQQ-026"})
            # 原始响应仍然落盘：拒收的是候选，不是证据。
            self.assertTrue((raw / "CHU-101" / "javbus.json").is_file())

    def test_scrape_uses_official_product_identity_for_display_alias(self):
        check = self.scrape_codes._identity_mismatch
        mgs = "https://www.mgstage.com/product/product_detail/390JAC-040/"
        self.assertIsNone(check("390JAC-040", {"id": "JAC-040", "source_url": mgs}))
        dvd = {"content_id": "118jac040",
               "source_url": "https://www.dmm.co.jp/mono/dvd/-/detail/=/cid=118jac040/"}
        self.assertIsNone(check("JAC-040", dvd))
        self.assertEqual(check("390JAC-040", dvd).kind, "identity_mismatch")
        for payload in (
            {"id": "JAC-040", "source_url": "https://www.dmm.co.jp/mono/dvd/-/detail/=/cid=118jac040/"},
            {"id": "390JAC-040", "source_url": mgs.replace("040", "041")},
            {"id": "JAC-040", "source_url": mgs.replace("www.mgstage.com", "mgstage.com.example.org")},
        ):
            self.assertEqual(check("390JAC-040", payload).kind, "identity_mismatch")

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

        不收 `--database`（必填）、`--backup-dir`（目录）这类同义写法：名字不同的同义
        参数会让「上次那条命令」在另一个脚本上直接报错，而报错只说缺参数——不说该写什么。
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


class ReleaseTagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = load_script("release_tag")

    def test_latest_matching_master_run_must_finish_successfully(self):
        success = dict(id=1, head_sha="abc", head_branch="master", event="push",
                       status="completed", conclusion="success", html_url="test-url")
        self.assertEqual(self.release.require_success([success], "abc"), success)
        for changes in ({"head_sha": "other"}, {"head_branch": "feature"},
                        {"event": "pull_request"}, {"status": "in_progress"},
                        {"conclusion": "failure"}, {"conclusion": "cancelled"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.release.require_success([{**success, **changes}], "abc")
        with self.assertRaises(ValueError):
            self.release.require_success([success, {**success, "id": 2, "conclusion": "failure"}], "abc")

    def test_default_is_read_only_and_apply_stops_if_master_moves(self):
        planned = dict(sha="abc", tag="v1.2.3", repo="owner/repo")
        with mock.patch.object(self.release, "plan", return_value=planned), \
                mock.patch.object(self.release, "command") as command, redirect_stdout(io.StringIO()):
            self.assertEqual(self.release.main([]), 0)
            command.assert_not_called()
            with mock.patch.object(self.release, "api", return_value={"object": {"sha": "other"}}):
                self.assertEqual(self.release.main(["--apply"]), 1)
            command.assert_not_called()

    def test_apply_pushes_only_the_validated_tag(self):
        planned = dict(sha="abc", tag="v1.2.3", repo="owner/repo")
        with mock.patch.object(self.release, "plan", return_value=planned), \
                mock.patch.object(self.release, "api", return_value={"object": {"sha": "abc"}}), \
                mock.patch.object(self.release, "command") as command, redirect_stdout(io.StringIO()):
            self.assertEqual(self.release.main(["--repo", "owner/repo", "--apply"]), 0)
            self.assertEqual(command.call_args_list[-1], mock.call(
                "git", "push", "https://github.com/owner/repo.git", "refs/tags/v1.2.3"))
            self.assertNotIn("--force", str(command.call_args_list))

    def test_unmerged_commit_cannot_pass_release_verification(self):
        with mock.patch.object(self.release, "api", return_value={"status": "ahead"}), \
                self.assertRaises(ValueError):
            self.release.verify("owner/repo", "abc")

    #: 干净的 master 检出，HEAD 与远端一致。
    CLEAN = {("git", "status", "--porcelain"): "",
             ("git", "branch", "--show-current"): "master",
             ("git", "rev-parse", "HEAD"): "abc"}

    def _shell(self, changes=None):
        answers = {**self.CLEAN, **(changes or {})}
        return mock.patch.object(self.release, "command",
                                 side_effect=lambda *args, **_: answers.get(args, ""))

    def test_plan_refuses_dirty_checkout_wrong_branch_and_existing_tags(self):
        for changes, refs in (({("git", "status", "--porcelain"): " M file"}, []),
                              ({("git", "branch", "--show-current"): "feature"}, []),
                              ({}, [{"ref": "refs/tags/v0.7.14"}])):
            with self.subTest(changes=changes, refs=refs), self._shell(changes), \
                    mock.patch.object(self.release, "api", side_effect=lambda repo, path: {"object": {"sha": "abc"}} if path == "git/ref/heads/master" else refs), \
                    mock.patch.object(self.release.version_bump, "read_version", return_value="0.7.14"), \
                    mock.patch.object(Path, "read_text", return_value="## [0.7.14] - 2026-09-07\n"), \
                    self.assertRaises(ValueError):
                self.release.plan("owner/repo")

    def test_a_version_without_its_changelog_section_cannot_be_tagged(self):
        """使用者读到的说明只有变更日志那一节；缺了就等于发一个没有说明的版本。"""
        with self._shell(), \
                mock.patch.object(self.release, "api", return_value={"object": {"sha": "abc"}}), \
                mock.patch.object(self.release.version_bump, "read_version", return_value="0.7.14"), \
                mock.patch.object(Path, "read_text", return_value="# 变更日志\n\n## [未发布]\n"), \
                self.assertRaisesRegex(ValueError, "CHANGELOG.md 缺少 0.7.14"):
            self.release.plan("owner/repo")

    def _planned_bump(self):
        return {"range": "v0.7.14..HEAD", "bump": "minor", "current": "0.7.14",
                "version": "0.8.0", "commits": 3}

    def test_a_bump_plan_writes_nothing_until_apply(self):
        with self._shell(), mock.patch.object(self.release, "api", return_value=[]), \
                mock.patch.object(self.release.version_bump, "plan_bump",
                                  return_value=self._planned_bump()), \
                mock.patch.object(self.release.version_bump, "write_version") as write, \
                mock.patch.object(self.release.changelog, "release") as promote:
            result = self.release.prepare("owner/repo", "auto", apply=False)
        self.assertEqual((result["tag"], result["version"], result["bump"]),
                         ("v0.8.0", "0.8.0", "minor"))
        write.assert_not_called()
        promote.assert_not_called()

    def test_applying_a_bump_writes_the_version_and_the_changelog_but_commits_nothing(self):
        """措辞要人过一遍，所以脚本只落盘；提交与标签是后面两步。"""
        with self._shell() as command, mock.patch.object(self.release, "api", return_value=[]), \
                mock.patch.object(self.release.version_bump, "plan_bump",
                                  return_value=self._planned_bump()), \
                mock.patch.object(self.release.version_bump, "write_version") as write, \
                mock.patch.object(self.release.changelog, "release") as promote:
            result = self.release.prepare("owner/repo", "auto", apply=True)
        write.assert_called_once_with(self.release.ROOT, "minor")
        self.assertEqual(promote.call_args.args, (self.release.ROOT, "0.8.0"))
        self.assertEqual(promote.call_args.kwargs["spec"], "v0.7.14..HEAD")
        self.assertTrue(result["next"], "落盘之后必须告诉人下一步做什么")
        issued = [args for args, _ in command.call_args_list]
        self.assertFalse([args for args in issued
                          if {"commit", "tag", "push"} & set(args)], issued)

    def test_a_bump_stops_when_the_target_tag_already_exists(self):
        with self._shell(), \
                mock.patch.object(self.release, "api", return_value=[{"ref": "refs/tags/v0.8.0"}]), \
                mock.patch.object(self.release.version_bump, "plan_bump",
                                  return_value=self._planned_bump()), \
                mock.patch.object(self.release.version_bump, "write_version") as write, \
                self.assertRaisesRegex(ValueError, "v0.8.0 已存在"):
            self.release.prepare("owner/repo", "auto", apply=True)
        write.assert_not_called()


class ShipTests(unittest.TestCase):
    """`--ship`：定好版之后一路到标签，中途停下再跑一次要接着走。"""

    @classmethod
    def setUpClass(cls):
        cls.release = load_script("release_tag")

    #: 一次干净的起点：在 master 上，工作区正好是那两份定版文件，本地没有这个标签。
    SHELL = {("git", "branch", "--show-current"): "master",
             ("git", "status", "--porcelain"): " M CHANGELOG.md\n M src/peach/__init__.py",
             ("git", "rev-parse", "HEAD"): "abc",
             ("git", "tag", "--list", "v0.8.0"): ""}

    SUCCESS = dict(id=1, head_sha="abc", head_branch="master", event="push",
                   status="completed", conclusion="success", html_url="test-url")

    def _shell(self, changes=None):
        answers = {**self.SHELL, **(changes or {})}
        return mock.patch.object(self.release, "command",
                                 side_effect=lambda *args, **_: answers.get(args, ""))

    def _api(self, *, tags=(), remote="old", runs=(SUCCESS,)):
        def answer(_repo, endpoint):
            if endpoint.startswith("git/matching-refs/tags/"):
                return list(tags)
            if endpoint == "git/ref/heads/master":
                return {"object": {"sha": remote}}
            if endpoint.startswith("actions/workflows/test.yml/runs"):
                return {"workflow_runs": list(runs)}
            raise AssertionError(f"没预料到的调用：{endpoint}")
        return mock.patch.object(self.release, "api", side_effect=answer)

    def _version(self):
        return mock.patch.object(self.release.version_bump, "read_version", return_value="0.8.0")

    def _document(self, text="## [0.8.0] - 2026-09-07\n\n### 新增\n\n- 那件事\n"):
        return mock.patch.object(Path, "read_text", return_value=text)

    @staticmethod
    def _writes(command):
        """真正动了仓库的那些调用；`git tag --list` 这种查询不算。"""
        return [args for args, _ in command.call_args_list
                if args[:2] in {("git", "add"), ("git", "commit"), ("git", "push")}
                or args[:3] == ("git", "tag", "-a")]

    def test_a_plan_without_apply_writes_nothing(self):
        with self._shell() as command, self._api(), self._version(), self._document():
            result = self.release.ship("owner/repo", apply=False)
        self.assertEqual((result["tag"], result["commit"], result["push"]),
                         ("v0.8.0", True, True))
        self.assertEqual(self._writes(command), [])

    def test_pending_files_keep_the_status_column_of_the_first_line(self):
        """`git status --porcelain` 首行以空格开头；按列取路径前不能对整段输出 strip。

        2026-09-08 定版时两份文件都在，发布却被拒：第一行被读成 `HANGELOG.md`。"""
        porcelain = " M CHANGELOG.md\n M src/peach/__init__.py\n"
        with mock.patch.object(self.release.subprocess, "run",
                               return_value=mock.Mock(stdout=porcelain)):
            self.assertEqual(self.release._pending_files(),
                             ["CHANGELOG.md", "src/peach/__init__.py"])

    def test_unrelated_changes_are_never_carried_into_the_release_commit(self):
        """标签指向发布提交，夹带什么就等于发出去什么。"""
        dirty = {("git", "status", "--porcelain"):
                 " M CHANGELOG.md\n M src/peach/api.py\n M src/peach/__init__.py"}
        with self._shell(dirty) as command, self._api(), self._version(), self._document(), \
                self.assertRaisesRegex(ValueError, "src/peach/api.py"):
            self.release.ship("owner/repo", apply=True)
        self.assertEqual(self._writes(command), [])

    def test_a_version_without_its_changelog_section_cannot_ship(self):
        with self._shell(), self._api(), self._version(), \
                self._document("# 变更日志\n\n## [未发布]\n"), \
                self.assertRaisesRegex(ValueError, "缺少 0.8.0"):
            self.release.ship("owner/repo", apply=True)

    def test_an_occupied_tag_stops_the_whole_thing(self):
        for tags, local, message in (([{"ref": "refs/tags/v0.8.0"}], "", "已存在"),
                                     ([], "v0.8.0", "本地 v0.8.0 已存在")):
            with self.subTest(message=message), \
                    self._shell({("git", "tag", "--list", "v0.8.0"): local}), \
                    self._api(tags=tags), self._version(), self._document(), \
                    self.assertRaisesRegex(ValueError, message):
                self.release.ship("owner/repo", apply=True)

    def test_apply_commits_pushes_waits_then_tags_in_that_order(self):
        with self._shell() as command, self._api(), self._version(), self._document():
            result = self.release.ship("owner/repo", apply=True)
        self.assertEqual(self._writes(command), [
            ("git", "add", "src/peach/__init__.py", "CHANGELOG.md"),
            ("git", "commit", "-m", "chore(release): 版本 0.8.0"),
            ("git", "push", "https://github.com/owner/repo.git", "refs/heads/master"),
            ("git", "tag", "-a", "v0.8.0", "abc", "-m", "Peach v0.8.0 Windows 测试版"),
            ("git", "push", "https://github.com/owner/repo.git", "refs/tags/v0.8.0"),
        ])
        self.assertEqual(result["test"], "test-url")

    def test_a_red_test_run_never_becomes_a_tag(self):
        red = {**self.SUCCESS, "conclusion": "failure"}
        with self._shell() as command, self._api(runs=(red,)), self._version(), \
                self._document(), self.assertRaisesRegex(ValueError, "尚未通过"):
            self.release.ship("owner/repo", apply=True)
        issued = self._writes(command)
        self.assertIn(("git", "commit", "-m", "chore(release): 版本 0.8.0"), issued)
        self.assertFalse([args for args in issued if "refs/tags/v0.8.0" in args], issued)

    def test_running_it_again_skips_what_is_already_done(self):
        """网络断在半路就再跑一次：已提交的不重提，已推送的不重推。"""
        with self._shell({("git", "status", "--porcelain"): ""}) as command, \
                self._api(remote="abc"), self._version(), self._document():
            result = self.release.ship("owner/repo", apply=True)
        self.assertEqual((result["commit"], result["push"]), (False, False))
        self.assertEqual(self._writes(command), [
            ("git", "tag", "-a", "v0.8.0", "abc", "-m", "Peach v0.8.0 Windows 测试版"),
            ("git", "push", "https://github.com/owner/repo.git", "refs/tags/v0.8.0"),
        ])


class AwaitTestTests(unittest.TestCase):
    """等 Test 出结果：绿了才回来，红了不等，超时说清楚接下来怎么办。"""

    @classmethod
    def setUpClass(cls):
        cls.release = load_script("release_tag")

    RUNNING = dict(id=1, head_sha="abc", head_branch="master", event="push",
                   status="in_progress", conclusion=None, html_url="test-url")

    def _runs(self, *rounds):
        answers = iter(rounds)
        return mock.patch.object(self.release, "test_runs",
                                 side_effect=lambda *_: list(next(answers)))

    def test_polling_continues_until_the_run_completes(self):
        done = {**self.RUNNING, "status": "completed", "conclusion": "success"}
        naps = []
        with self._runs((), (self.RUNNING,), (done,)):
            checked = self.release.await_test(
                "owner/repo", "abc", timeout=90, poll=30,
                sleep=naps.append, clock=lambda: len(naps) * 30)
        self.assertEqual(checked["html_url"], "test-url")
        self.assertEqual(naps, [30, 30])

    def test_a_finished_red_run_is_not_worth_waiting_out(self):
        red = {**self.RUNNING, "status": "completed", "conclusion": "failure"}
        naps = []
        with self._runs((red,)), self.assertRaisesRegex(ValueError, "尚未通过"):
            self.release.await_test("owner/repo", "abc", timeout=3600, poll=30,
                                    sleep=naps.append, clock=lambda: 0)
        self.assertEqual(naps, [], "红的等多久都不会变绿")

    def test_giving_up_says_the_commit_is_already_pushed(self):
        with self._runs((self.RUNNING,), (self.RUNNING,)), \
                self.assertRaisesRegex(ValueError, "--ship --apply"):
            self.release.await_test("owner/repo", "abc", timeout=30, poll=30,
                                    sleep=lambda _: None, clock=iter([0, 30, 60]).__next__)


if __name__ == "__main__":
    unittest.main()
