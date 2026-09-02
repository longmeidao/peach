# -*- coding: utf-8 -*-
"""island 层（`frontend/`）的门槛：产物、清单、契约与 vitest。

ADR-0022 的取舍是「构建产物进 Git」：运行时的 Python 服务、PyInstaller 包和 macOS
上的检出都没有 Node，`web/dist/peach-ui.js` 必须是仓库里现成的文件。代价是产物会和
源码脱节，所以这里分两类断言：

- **不需要 Node 的**：产物在不在、导出对不对、引用的遗留模块路径对不对、清单是否
  精确钉版本、语义契约有没有从 `web/app.js` 搬进 island 时丢掉。这些在任何机器上都跑。
- **需要 Node 的**：vitest。npm 或 `frontend/node_modules` 不在就显式跳过——本机可能
  根本没装 Node，让整个测试域红掉只会让人绕过入口，而不是去装 Node。

「产物是否由当前源码构建出来」这一条不在这里：不装 Node 就无法重建，无从比较。
那道门槛在 CI 的 `web-bundle` job 里，`npm run build` 之后 `git diff --exit-code web/dist`。
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DIST = ROOT / "web" / "dist"
BUNDLE = DIST / "peach-ui.js"


class IslandBundleTests(unittest.TestCase):
    """提交进 Git 的产物必须是浏览器能直接 import 的那一份。"""

    @classmethod
    def setUpClass(cls):
        if not BUNDLE.is_file():
            raise unittest.SkipTest(
                f"{BUNDLE.relative_to(ROOT)} 不在：先 `npm --prefix frontend run build`")
        cls.bundle = BUNDLE.read_text(encoding="utf-8")

    def test_bundle_name_carries_no_content_hash(self):
        """引用它的 `web/app.js` 不经过构建，带哈希的名字它改不了。"""
        names = sorted(path.name for path in DIST.iterdir() if path.is_file())
        self.assertIn("peach-ui.js", names)
        for name in names:
            self.assertNotRegex(name, r"-[0-9a-zA-Z_]{8}\.(?:js|css)$",
                                f"{name} 带了内容哈希，app.js 里写死的路径会指向不存在的文件")

    def test_bundle_exports_the_mount_contract(self):
        for symbol in ("mountIsland", "unmountIsland", "islandNames"):
            self.assertIn(f"as {symbol}", self.bundle, f"产物没有导出 {symbol}")

    def test_bundle_keeps_the_legacy_modules_external(self):
        """遗留助手不进 bundle：打进去就有两份 `LOC`／`fmtDur`，语义契约会各走一份。"""
        self.assertIn('from "/js/core.js"', self.bundle)
        self.assertIn('from "/js/ui-components.js"', self.bundle)
        for name in ("/js/core.js", "/js/ui-components.js"):
            self.assertTrue((ROOT / "web" / name.lstrip("/")).is_file(),
                            f"产物 import 的 {name} 在仓库里不存在")

    def test_the_route_that_serves_it_is_registered(self):
        # 扫整个包而不是 `api.py` 一个文件：这条路由现在住在 `routes_pages.py`，
        # 而它属于哪个模块是内部事，前端只关心它被注册了。
        registered = [path.name for path in sorted((ROOT / "src" / "peach").glob("*.py"))
                      if 'api_route("/dist/{name}"' in path.read_text(encoding="utf-8")]
        self.assertEqual(len(registered), 1, f"/dist 路由注册了 {registered}")
        app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("await import('/dist/peach-ui.js')", app_js)


class FrontendManifestTests(unittest.TestCase):
    """依赖清单和根 `package.json` 是两份，各自的口径都要精确。"""

    def setUp(self):
        self.manifest = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))

    def test_versions_are_exactly_pinned_and_locked(self):
        self.assertTrue(self.manifest["private"])
        declared = {**self.manifest.get("dependencies", {}),
                    **self.manifest.get("devDependencies", {})}
        self.assertTrue(declared)
        for name, version in declared.items():
            self.assertRegex(version, r"^\d+\.\d+\.\d+$",
                             f"{name} 没有钉死版本，两台机器会装出不同的产物")
        lock = json.loads((FRONTEND / "package-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["name"], self.manifest["name"])
        for name, version in declared.items():
            entry = lock["packages"].get(f"node_modules/{name}")
            self.assertIsNotNone(entry, f"{name} 不在 lockfile 里")
            self.assertEqual(entry["version"], version, name)

    def test_the_root_manifest_stays_limited_to_the_vendored_packages(self):
        """根清单只登记手工 vendor 的那几个包，构建依赖不许混进去。"""
        root = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertNotIn("vite", root.get("devDependencies", {}))
        self.assertNotIn("preact", root.get("dependencies", {}))

    def test_dependabot_watches_the_frontend_manifest(self):
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("directory: /frontend", dependabot)

    def test_ci_owns_the_only_gate_that_can_catch_a_stale_bundle(self):
        """本机验不了「产物是否由当前源码构建」，这道门槛只在 CI。

        它一旦被删掉，源码和 `web/dist/` 就能无声地分叉，而所有本地测试照样全绿——
        那正是这条断言要拦的。`git add --intent-to-add` 不能省：光 `git diff` 只看
        已跟踪的文件，构建新出的产物是未跟踪的，会被直接放过。
        """
        workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        for step in ("actions/setup-node", "npm --prefix frontend ci",
                     "npm --prefix frontend run typecheck", "npm --prefix frontend test",
                     "npm --prefix frontend run build",
                     "git add --intent-to-add -- web/dist",
                     "git diff --exit-code -- web/dist"):
            self.assertIn(step, workflow, f"CI 缺了 {step}")

    def test_the_bundle_is_committed_and_the_toolchain_is_not(self):
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "web/dist/peach-ui.js"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        self.assertEqual(tracked.returncode, 1, "web/dist 被 .gitignore 排除了，产物发不出去")
        for ignored in ("frontend/node_modules/preact/package.json",):
            result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", ignored],
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", check=False)
            self.assertEqual(result.returncode, 0, f"{ignored} 没有被忽略")


class IslandSourceContractTests(unittest.TestCase):
    """从 `web/app.js` 搬过来时不能把语义契约丢在原地。

    `tests/test_web_ui.py` 对页面源断言这些标记，高清版目标页搬进 island 之后那份
    断言少了一处；缺口补在这里，而不是让它无声消失。
    """

    def setUp(self):
        self.source = (FRONTEND / "src" / "islands" / "quality-goals.tsx").read_text(
            encoding="utf-8")

    def test_titles_still_use_middle_truncation(self):
        """文件名和番号的差别常在尾部，末尾省略会把要看的东西切掉。"""
        self.assertIn("data-middle-truncate", self.source)

    def test_empty_and_error_states_reuse_the_shared_components(self):
        """空态与失败态走 `/js/ui-components.js`，不是一行灰字。"""
        self.assertIn("emptyStateHtml(", self.source)
        self.assertIn("noteHtml(", self.source)
        self.assertIn("没有标记中的高清版目标", self.source)

    def test_readings_reuse_the_legacy_formatters(self):
        """时长、体积、来源名共用遗留口径，不在 island 里再写一套。"""
        self.assertIn("from '@peach/legacy/core'", self.source)
        for helper in ("fmtDur(", "fmtSize(", "LOC["):
            self.assertIn(helper, self.source)

    def test_the_endpoint_is_declared_once(self):
        self.assertIn("/api/quality-goals?limit=200", self.source)
        # 扫整个 web 层：路由表已经从 `web_contract.py` 搬到 `web_router.py`，
        # 前者只剩再导出。island 关心的是这条路由存在且只声明一次，不是它在哪个文件。
        declared = [path.name for path in sorted((ROOT / "src" / "peach").glob("web_*.py"))
                    if "quality-goals" in path.read_text(encoding="utf-8")]
        self.assertEqual(len(declared), 1, f"quality-goals 声明在 {declared}")


class VitestTests(unittest.TestCase):
    """vitest 走同一个测试入口，但缺 Node 时跳过而不是红。"""

    def test_the_island_suite_passes(self):
        npm = shutil.which("npm")
        if npm is None:
            self.skipTest("跳过 vitest：本机没有 npm。装 Node 24+ 后 `-Scope web` 会带上它")
        if not (FRONTEND / "node_modules" / "vitest").is_dir():
            self.skipTest("跳过 vitest：frontend/node_modules 还没装，先 `npm --prefix frontend ci`")
        completed = subprocess.run(
            [npm, "--prefix", str(FRONTEND), "test", "--silent"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(FRONTEND), check=False)
        output = f"{completed.stdout}\n{completed.stderr}"
        self.assertEqual(completed.returncode, 0, output)
        self.assertRegex(output, r"Tests\s+\d+ passed", output)
        self.assertNotRegex(output, r"Tests\s+0 passed", "vitest 一个用例都没跑")
        counted = re.search(r"Tests\s+(\d+) passed", output)
        assert counted is not None
        self.assertGreaterEqual(int(counted.group(1)), 10, output)


if __name__ == "__main__":
    unittest.main()
