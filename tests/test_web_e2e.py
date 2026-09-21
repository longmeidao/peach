# -*- coding: utf-8 -*-
"""真浏览器冒烟：临时数据根上的合成演示库，交给 `frontend/e2e` 的 playwright-core 用例。

页面源断言守不住布局之后才成立的事实（横向溢出、等待态卡住、控制台报错、失败请求），
靠手动开浏览器逐轮重测的话，既费时又不稳定。这里把它们固定成确定性的用例：Python 这一侧准备
数据与服务，Node 那一侧只认 `PEACH_E2E_ORIGIN`。

数据全在临时目录：`scripts/demo_dataset.py` 生成 SFW 合成库，账本来自迁移模板，
设置文件把 `local` 的声明根直接写成演示库目录。Windows 上 `[media.mounts]` 不参与
路径翻译，声明根若沿用内建默认，process 读到的就是这台机器的真实媒体目录。

短片由 ffmpeg 编码成真能解码的 2 秒片段：详情页的播放器会预加载源，占位字节只会让
`/stream` 返回 503。缺 Node、`playwright-core`、ffmpeg 或本机 Chrome 时，本机显式跳过，
CI（`GITHUB_ACTIONS=true`）判失败，与 vitest 同一口径；浏览器不另外下载，
`PEACH_E2E_CHROME` 可以指定可执行文件。CI 的 `web-e2e` job 负责装齐这四样。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from pathlib import Path
from unittest import mock

from peach import link_marks, scraping_access, settings_file
from peach.config import FFMPEG_DIR
from peach.ffmpeg import FFmpegResolver
from peach.library_processing import process_library
from support.conditions import missing_prerequisite, windows_ledger_roots
from support.ledger import fresh_ledger

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SERVER_START_SECONDS = 60
E2E_SECONDS = 600


def chrome_executable() -> str | None:
    """本机 Chrome 的可执行文件；找不到返回 None。"""
    explicit = os.environ.get("PEACH_E2E_CHROME", "").strip()
    if explicit:
        return explicit if Path(explicit).is_file() else None
    candidates: list[Path] = []
    if os.name == "nt":
        for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(variable)
            if base:
                candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    elif sys.platform == "darwin":
        candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    else:
        for name in ("google-chrome", "google-chrome-stable"):
            found = shutil.which(name)
            if found:
                candidates.append(Path(found))
    return next((str(path) for path in candidates if path.is_file()), None)


def load_demo_script():
    path = ROOT / "scripts" / "demo_dataset.py"
    spec = importlib.util.spec_from_file_location("peach_script_demo_dataset_e2e", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def refuse_network(*args, **kwargs):
    raise AssertionError("演示库的 process 不应向任何外部来源发请求")


def e2e_command(node: str, concurrency: str = "") -> list[str]:
    """串行跑是浏览器进程预算：每条用例的 Chrome 只给两个渲染进程（`e2e/harness.ts`）。

    直接启动 Node 也省掉资源守卫内的一层 npm 进程。
    """
    selected = concurrency or "1"
    if not selected.isdecimal() or int(selected) < 1:
        raise AssertionError("PEACH_E2E_CONCURRENCY 必须是正整数")
    return [node, "--test", f"--test-concurrency={int(selected)}",
            "--test-reporter=tap", "e2e/**/*.test.ts"]


@windows_ledger_roots
class WebE2ESmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = shutil.which("node")
        if node is None:
            missing_prerequisite("跳过 e2e：本机没有 Node。装 Node 24+ 后 `-Scope web` 会带上它")
        if not (FRONTEND / "node_modules" / "playwright-core").is_dir():
            missing_prerequisite("跳过 e2e：frontend/node_modules 还没装，先 `npm --prefix frontend ci`")
        ffmpeg = FFmpegResolver(FFMPEG_DIR).ffmpeg()
        if ffmpeg is None:
            missing_prerequisite("跳过 e2e：没找到 ffmpeg，演示库的短片编码不出来")
        chrome = chrome_executable()
        if chrome is None:
            missing_prerequisite("跳过 e2e：没找到 Chrome；装 Google Chrome 或用 PEACH_E2E_CHROME 指定")
        cls.node, cls.ffmpeg, cls.chrome = node, str(ffmpeg.path), chrome
        cls.root = Path(tempfile.mkdtemp(prefix="peach-e2e-")).resolve()
        cls.server = None
        try:
            cls._build_library()
            cls._start_server()
            cls._warm_stream()
        except BaseException:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        server = getattr(cls, "server", None)
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
        if getattr(cls, "log", None) is not None:
            cls.log.close()
        shutil.rmtree(cls.root, ignore_errors=True)

    @classmethod
    def _build_library(cls):
        media = cls.root / "media"
        load_demo_script().generate(media, count=12, seed=7, video="ffmpeg", duration=2,
                                    ffmpeg=cls.ffmpeg)
        data = cls.root / "peach-data"
        (data / "database").mkdir(parents=True)
        cls.db = fresh_ledger(data / "database")
        cls.port = free_port()
        config = settings_file.PeachConfig(
            data, data / settings_file.SETTINGS_FILENAME, present=True, data_root_found=True,
            locations={"local": (str(media),)},
            server=settings_file.ServerSettings(port=cls.port),
        )
        settings_file.write(config)
        generated = config.directory("generated")
        # 路由冒烟只验页面与站标端点的衔接；取图算法另有 mock 契约，不让这轮布局测试依赖外网。
        mark_root = generated / "site-marks"
        mark_root.mkdir(parents=True)
        mark = (ROOT / "resources" / "peach-logo.png").read_bytes()
        for spec in scraping_access.SOURCES.values():
            cached = link_marks.cached_path(mark_root, spec["login"])
            if cached is None:
                raise AssertionError(f"采集来源没有可缓存的主机：{spec['login']}")
            cached.write_bytes(mark)
        result = process_library(config, cls.db, generated, generated / "covers",
                                 provider_factory=refuse_network)
        if result["status"] != "complete":
            raise AssertionError(f"演示库 process 没有完成：{result}")
        with closing(sqlite3.connect(cls.db)) as connection:
            row = connection.execute(
                "SELECT id FROM asset WHERE medium='video' ORDER BY id LIMIT 1").fetchone()
        if row is None:
            raise AssertionError("演示库 process 之后账本里没有视频")
        cls.data, cls.item = data, row[0]

    @classmethod
    def _start_server(cls):
        env = dict(os.environ, PEACH_DATA_ROOT=str(cls.data), PYTHONIOENCODING="utf-8")
        cls.log = (cls.root / "serve.log").open("w", encoding="utf-8")
        cls.server = subprocess.Popen(
            [sys.executable, "-X", "utf8", "-m", "peach", "serve", "--host", "127.0.0.1",
             "--port", str(cls.port), "--db", str(cls.db),
             "--no-auth", "--no-mdns", "--no-ledger-sync"],
            cwd=str(ROOT), env=env, stdout=cls.log, stderr=subprocess.STDOUT)
        cls.origin = f"http://127.0.0.1:{cls.port}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        deadline = time.monotonic() + SERVER_START_SECONDS
        while time.monotonic() < deadline:
            if cls.server.poll() is not None:
                raise AssertionError(f"服务提前退出：{cls._server_log()}")
            try:
                with opener.open(f"{cls.origin}/healthz", timeout=2) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        raise AssertionError(f"{SERVER_START_SECONDS} 秒内 /healthz 没有就绪：{cls._server_log()}")

    @classmethod
    def _server_log(cls) -> str:
        cls.log.flush()
        return (cls.root / "serve.log").read_text(encoding="utf-8", errors="replace")[-4000:]

    @classmethod
    def _warm_stream(cls):
        """在 Chrome 启动多进程前用真实端点完成短片的兼容转码。"""
        session = f"e2e-prewarm-{os.getpid()}"
        query = urllib.parse.urlencode({"id": cls.item, "session": session})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(f"{cls.origin}/stream?{query}", timeout=60) as response:
                if response.status != 200:
                    raise AssertionError(f"演示短片预热失败：HTTP {response.status}")
                response.read()
        except (urllib.error.URLError, OSError) as error:
            raise AssertionError(f"演示短片预热失败：{error}\n{cls._server_log()}") from error
        finally:
            cancel = urllib.request.Request(
                f"{cls.origin}/api/stream-cancel?{urllib.parse.urlencode({'session': session})}",
                method="POST", headers={"Origin": cls.origin})
            try:
                with opener.open(cancel, timeout=5) as response:
                    if response.status != 200:
                        raise AssertionError(f"演示短片取消失败：HTTP {response.status}")
            except (urllib.error.URLError, OSError) as error:
                raise AssertionError(f"演示短片取消失败：{error}") from error

    def test_every_route_holds_the_layout_and_runtime_invariants(self):
        env = dict(os.environ, PEACH_E2E_ORIGIN=self.origin, PEACH_E2E_ITEM=str(self.item),
                   PEACH_E2E_CHROME=self.chrome)
        try:
            completed = subprocess.run(
                e2e_command(self.node, os.environ.get("PEACH_E2E_CONCURRENCY", "").strip()),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(FRONTEND), env=env, timeout=E2E_SECONDS, check=False)
        except subprocess.TimeoutExpired as expired:
            # 已经跑完的那几条 TAP 行指出卡在哪一条之后；只报超时等于什么都没说。
            partial = expired.stdout or ""
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            self.fail(f"{E2E_SECONDS} 秒内没跑完，已输出：\n{partial[-4000:]}")
        output = f"{completed.stdout}\n{completed.stderr}"
        self.assertEqual(completed.returncode, 0, f"{output}\n--- serve.log ---\n{self._server_log()}")
        self.assertRegex(output, r"# pass [1-9]\d*", output)
        self.assertRegex(output, r"# fail 0\b", output)


class MissingPrerequisiteTests(unittest.TestCase):
    """CI 里浏览器用例只能执行或失败，不能静默跳过；工作流那一半由 `test_frontend_build.py` 守。"""

    def test_headless_browser_stays_within_the_resource_guard_process_budget(self):
        harness = (FRONTEND / "e2e" / "harness.ts").read_text(encoding="utf-8")
        self.assertIn("args: ['--renderer-process-limit=2']", harness)
        self.assertIn("timeout: 30_000", harness)

    def test_missing_prerequisites_skip_locally_and_fail_on_ci(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with self.assertRaisesRegex(AssertionError, "没有 npm"):
                missing_prerequisite("没有 npm")
        local = {key: value for key, value in os.environ.items() if key != "GITHUB_ACTIONS"}
        with mock.patch.dict(os.environ, local, clear=True):
            with self.assertRaises(unittest.SkipTest):
                missing_prerequisite("没有 npm")

    def test_the_npm_script_runs_within_the_same_browser_process_budget(self):
        manifest = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["scripts"]["e2e"],
            'node --test --test-concurrency=1 --test-reporter=tap "e2e/**/*.test.ts"',
        )

    def test_e2e_command_serializes_by_default_and_places_the_override_before_the_glob(self):
        self.assertEqual(e2e_command("node", "1"), [
            "node", "--test", "--test-concurrency=1", "--test-reporter=tap",
            "e2e/**/*.test.ts",
        ])
        self.assertEqual(e2e_command("node"), [
            "node", "--test", "--test-concurrency=1", "--test-reporter=tap",
            "e2e/**/*.test.ts",
        ])
        with self.assertRaisesRegex(AssertionError, "必须是正整数"):
            e2e_command("node", "0")


if __name__ == "__main__":
    unittest.main()
