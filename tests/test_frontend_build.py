# -*- coding: utf-8 -*-
"""island 层（`frontend/`）的门槛：产物、清单、契约与 vitest。

ADR-0022 的取舍是「构建产物进 Git」：运行时的 Python 服务、PyInstaller 包和 macOS
上的检出都没有 Node，`web/dist/peach-ui.js` 必须是仓库里现成的文件。代价是产物会和
源码脱节，所以这里分两类断言：

- **不需要 Node 的**：产物在不在、导出对不对、引用的遗留模块路径对不对、清单是否
  精确钉版本、语义契约有没有从 `web/app.js` 搬进 island 时丢掉。这些在任何机器上都跑。
- **需要 Node 的**：tsc、lint 与 vitest。npm 或 `frontend/node_modules` 不在时本机显式
  跳过——本机可能根本没装 Node，让整个测试域红掉只会让人绕过入口，而不是去装 Node。
  CI（`GITHUB_ACTIONS=true`）里判失败：工作流负责装齐，跳过等于这几道门槛在 CI 里从不执行。

「产物是否由当前源码构建出来」这一条不在这里：不装 Node 就无法重建，无从比较。
那道门槛在 CI 的 `web-bundle` job 里，`npm run build` 之后 `git diff --exit-code web/dist`。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from support.conditions import missing_prerequisite

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
        # 遗留层只按这三个名字与 island 层打交道：挂一屏、卸一屏、核对路由表。
        for symbol in ("mountIsland", "unmountIsland", "islandNames"):
            self.assertIn(f"as {symbol}", self.bundle, f"产物没有导出 {symbol}")

    def test_bundle_keeps_the_legacy_modules_external(self):
        """遗留助手不进 bundle：打进去就有两份 `LOC`／`fmtDur`，语义契约会各走一份。"""
        self.assertIn('from "/js/core.js"', self.bundle)
        self.assertIn('from "/js/ui-components.js"', self.bundle)
        for name in ("/js/core.js", "/js/ui-components.js"):
            self.assertTrue((ROOT / "web" / name.lstrip("/")).is_file(),
                            f"产物 import 的 {name} 在仓库里不存在")

    def test_the_startup_switches_and_their_payload_are_in_the_shipped_bundle(self):
        """「开机自启」那三颗开关的标签和它们发出去的键，判据落在产物上。

        `web/dist/peach-react.js` 是提交进 Git 的产物。改了 `frontend/src` 不重建，浏览器拿到
        的仍是旧的那一份，而 tsc 和 vitest 都只看源码，谁都不会红——只有扫产物这一条会。
        """
        if not REACT_BUNDLE.is_file():
            self.skipTest(f"{REACT_BUNDLE.relative_to(ROOT)} 不在：先 `npm --prefix frontend run build`")
        react = REACT_BUNDLE.read_text(encoding="utf-8")
        for label in ("开机后启动 Peach", "静默启动", "在桌面创建快捷方式"):
            self.assertIn(label, react,
                          f"产物里没有「{label}」，先跑 npm --prefix frontend run build")
        payload = react[react.index('"/api/configuration/startup"'):][:240]
        for key in ("enabled:", "silent:", "desktop:"):
            self.assertIn(key, payload, f"保存开机自启没带上 {key}")

    def test_react_bundle_records_stable_dependency_paths(self):
        """区域注释只能从 `node_modules/` 起，不得把生成它的工作树路径写进产物。"""
        if not REACT_BUNDLE.is_file():
            self.skipTest(f"{REACT_BUNDLE.relative_to(ROOT)} 不在：先 `npm --prefix frontend run build`")
        react = REACT_BUNDLE.read_text(encoding="utf-8")
        captured = [line for line in react.splitlines()
                    if line.startswith("//#region ") and "node_modules/" in line
                    and not line.startswith("//#region node_modules/")]
        self.assertEqual(captured, [],
                         "React 产物带了工作树相对路径；在当前工作树安装依赖后重新构建")

    def test_the_route_that_serves_it_is_registered(self):
        # 扫整个包而不是 `api.py` 一个文件：这条路由现在住在 `routes_pages.py`，
        # 而它属于哪个模块是内部事，前端只关心它被注册了。
        registered = [path.name for path in sorted((ROOT / "src" / "peach").glob("*.py"))
                      if 'api_route("/dist/{name}"' in path.read_text(encoding="utf-8")]
        self.assertEqual(len(registered), 1, f"/dist 路由注册了 {registered}")
        app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("await import('/dist/peach-ui.js')", app_js)


REACT_BUNDLE = DIST / "peach-react.js"
REACT_STYLES = DIST / "peach-react.css"


class BoardTokenTests(unittest.TestCase):
    """BoardUI 的语义 token 在 `web/board.css` 里另有一份定值，两份各管一片页面。"""

    @staticmethod
    def declarations(css, selector):
        """同一选择器可能分几块写，合并后返回其中的 `--color-*` 声明。"""
        found = {}
        for block in re.finditer(rf"(?ms)^{re.escape(selector)} \{{\n(.*?)^\}}", css):
            found.update(re.findall(r"(--color-[\w-]+):\s*([^;]+);", block.group(1)))
        return found

    #: Peach 自己定值、不跟上游的 token。每一条都要在 `boardui/ORIGIN.md` 的差异表里
    #: 有一行写清原因：默认逐字照抄，例外必须是写下来的决定，不是谁顺手改的一次。
    LOCAL_TOKEN_VALUES = {
        (".dark", "--color-border-checkbox-default"): "var(--color-neutral-600)",
        (".dark", "--color-separator-border"): "var(--color-neutral-700)",
    }

    def test_the_react_subtree_redeclares_shared_tokens_with_upstream_values(self):
        """board.css 在 `:root` 上另定同名 token 且排在后面；React 容器上的值逐字等于 theme.css，
        登记在 `ORIGIN.md` 差异表里的那几条除外。"""
        legacy = "".join(path.read_text(encoding="utf-8") for path in
                         [ROOT / "web" / "board.css", *sorted((ROOT / "web" / "css").glob("*.css"))])
        shared = set(re.findall(r"(--color-[\w-]+):", legacy))
        theme = (FRONTEND / "src" / "react" / "boardui" / "styles" / "theme.css").read_text(encoding="utf-8")
        styles = (FRONTEND / "src" / "react" / "styles.css").read_text(encoding="utf-8")
        origin = (FRONTEND / "src" / "react" / "boardui" / "ORIGIN.md").read_text(encoding="utf-8")
        for upstream, local in ((":root", ".peach-react"), (".dark", ".dark .peach-react")):
            expected = {name: value for name, value in self.declarations(theme, upstream).items()
                        if name in shared}
            self.assertTrue(expected, f"theme.css 的 {upstream} 块里没找到同名 token")
            for (scope, name), value in self.LOCAL_TOKEN_VALUES.items():
                if scope == upstream and name in expected:
                    self.assertIn(name, origin, f"{name} 偏离上游，要在 ORIGIN.md 的差异表里写明原因")
                    expected[name] = value
            self.assertEqual(self.declarations(styles, local), expected,
                             f"styles.css 的 {local} 要与 theme.css 的 {upstream} 同名 token 逐条一致")

    def test_manual_and_system_dark_palettes_in_board_css_agree(self):
        """手动选深色与跟随系统深色是同一副配色，两块分开写，只改一块时文字色会差一档。"""
        board = (ROOT / "web" / "board.css").read_text(encoding="utf-8")
        manual = re.search(r':root\[data-theme="dark"\]\{(--color-text-primary:[^}]*)\}', board)
        system = re.search(r"@media\(prefers-color-scheme:dark\)\{:root:not\(\[data-theme\]\)\{"
                           r"(--color-text-primary:[^}]*)\}", board)
        self.assertIsNotNone(manual)
        self.assertIsNotNone(system)
        self.assertEqual(sorted(system.group(1).split(";")), sorted(manual.group(1).split(";")))


class ReactBundleTests(unittest.TestCase):
    """React 子树（BoardUI 源码 + Tailwind）与旧样式表同处一页的门槛。

    这几条都是「tsc 和 vitest 看不见、页面上才出事」的约束：产物引用路径、样式表顺序、
    工具类有没有被层叠层压住、Preflight 有没有漏到整页。
    """

    @classmethod
    def setUpClass(cls):
        for path in (BUNDLE, REACT_BUNDLE, REACT_STYLES):
            if not path.is_file():
                raise unittest.SkipTest(
                    f"{path.relative_to(ROOT)} 不在：先 `npm --prefix frontend run build`")
        cls.islands = BUNDLE.read_text(encoding="utf-8")
        cls.react = REACT_BUNDLE.read_text(encoding="utf-8")
        cls.css = REACT_STYLES.read_text(encoding="utf-8")

    def test_islands_load_the_react_bundle_by_its_served_path(self):
        """island 按 `@peach/react` 写，产物里必须改写成服务端真的提供的路径，且 React 不进 peach-ui.js。"""
        self.assertIn('import("/dist/peach-react.js")', self.islands)
        self.assertNotIn("react-dom", self.islands)
        # 注册表按名字取页面，名字得在产物里对得上。
        for page in ("avatar-picker", "library-processing", "quality-goals", "configuration"):
            self.assertIn(page, self.react)

    def test_the_react_bundle_keeps_the_legacy_modules_external(self):
        self.assertIn('from "/js/core.js"', self.react)
        self.assertNotIn("process.env", self.react, "库模式没替换 NODE_ENV，浏览器里没有 process")

    def test_utilities_stay_outside_cascade_layers(self):
        """旧样式表不分层。工具类放进层里，`button,input,textarea{color:inherit}` 这类标签规则就会压过它。"""
        layers = set(re.findall(r"@layer\s+([\w-]+)", self.css))
        self.assertNotIn("utilities", layers)
        self.assertNotIn("base", layers)

    def test_preflight_only_reaches_the_react_subtree(self):
        self.assertEqual(self.css.count("@scope"), 1)
        self.assertRegex(self.css, r"@scope\s*\(\.peach-react\)")
        scoped = (FRONTEND / "src" / "react" / "preflight-scoped.css").read_text(encoding="utf-8")
        upstream = FRONTEND / "node_modules" / "tailwindcss" / "preflight.css"
        if not upstream.is_file():
            self.skipTest("跳过 Preflight 原文比对：frontend/node_modules 还没装")
        opening = "@scope (.peach-react) {\n"
        self.assertIn(opening, scoped)
        self.assertTrue(scoped.endswith("}\n"))
        self.assertEqual(scoped[scoped.index(opening) + len(opening):-2],
                         upstream.read_text(encoding="utf-8"),
                         "preflight-scoped.css 与 tailwindcss 依赖里的原文不一致，按文件开头的说明重新生成")

    def test_the_legacy_focus_ring_stays_out_of_the_react_subtree(self):
        """旧样式表排在后面，全局 `:focus-visible` 与 `outline-none` 同特指度时它赢，输入框会多画一圈。"""
        base = (ROOT / "web" / "css" / "01-base.css").read_text(encoding="utf-8")
        self.assertIn(":where(:not(.peach-react *)):focus-visible{outline:2px solid var(--tungsten);", base)
        self.assertNotRegex(base, r"(?m)^:focus-visible\{")

    def test_react_styles_load_before_the_legacy_stylesheets(self):
        """同名 `--color-*` token 由后面的 board.css 定值，未迁移页面的颜色才不受影响。"""
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        order = [index.index(f'href="{href}"') for href in ("/dist/peach-react.css", "/app.css", "/board.css")]
        self.assertEqual(order, sorted(order))

    def test_the_dark_class_follows_the_theme_in_both_places(self):
        """BoardUI 的深色 token 挂在 `.dark` 上；首帧脚本和 applyTheme() 都要按实际深浅加减它。"""
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("classList.toggle('dark',", index)
        self.assertIn("root.classList.toggle('dark',dark)", app_js)


class BoardUiUpstreamTests(unittest.TestCase):
    """`frontend/src/react/boardui/` 与 `evilcharts/` 是上游注册表源码的逐字副本，只加不改
    （ADR-0031、ADR-0076）。

    每个目录的 `UPSTREAM.sha256` 记下复制时每个文件的 SHA-256。改了副本、多出没登记的文件、
    登记了却删掉，都在这里红。比的是登记的快照而不是线上注册表：上游随时会改，测试不能联网。
    升级上游时重新复制文件、重算对应行，并更新同目录 `ORIGIN.md` 的条目哈希。
    """

    VENDORED = ("boardui", "evilcharts")
    RECORDS = ("ORIGIN.md", "UPSTREAM.sha256")

    def test_the_copied_sources_match_their_recorded_upstream_hashes(self):
        for name in self.VENDORED:
            with self.subTest(name):
                self.assert_matches_upstream(FRONTEND / "src" / "react" / name, name)

    def assert_matches_upstream(self, root: Path, name: str):
        recorded = {}
        for line in (root / "UPSTREAM.sha256").read_text(encoding="utf-8").splitlines():
            digest, path = line.split("  ", 1)
            recorded[path] = digest
        present = {file.relative_to(root).as_posix(): file for file in root.rglob("*")
                   if file.is_file() and file.name not in self.RECORDS}
        self.assertEqual(sorted(present), sorted(recorded),
                         f"{name}/ 的文件要与 UPSTREAM.sha256 一一对应；Peach 自己的组合放在 {name}/ 外面")
        for path, file in present.items():
            self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), recorded[path],
                             f"{name}/{path} 与复制时的上游内容不同；外观差异在 {name}/ 外面组合")


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

    def test_the_frontend_has_no_preact_left(self):
        """前端只有 React 一档（ADR-0031）：留着 Preact 就是两套运行时各打一份进产物。"""
        manifest = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
        for section in ("dependencies", "devDependencies"):
            self.assertNotIn("preact", manifest.get(section, {}))
        config = json.loads(re.sub(r"^\s*//.*$", "", (FRONTEND / "tsconfig.json")
                                   .read_text(encoding="utf-8"), flags=re.M))
        self.assertNotIn("jsxImportSource", config["compilerOptions"])

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
                     "npm --prefix frontend run typecheck", "npm --prefix frontend run lint",
                     "npm --prefix frontend test",
                     "npm --prefix frontend run build",
                     "git add --intent-to-add -- web/dist",
                     "git diff --exit-code -- web/dist"):
            self.assertIn(step, workflow, f"CI 缺了 {step}")

    def test_the_bundle_is_committed_and_the_toolchain_is_not(self):
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "web/dist/peach-ui.js"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        self.assertEqual(tracked.returncode, 1, "web/dist 被 .gitignore 排除了，产物发不出去")
        for ignored in ("frontend/node_modules/react/package.json",):
            result = subprocess.run(["git", "-C", str(ROOT), "check-ignore", ignored],
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", check=False)
            self.assertEqual(result.returncode, 0, f"{ignored} 没有被忽略")


class IslandSourceContractTests(unittest.TestCase):
    """从 `web/app.js` 搬过来时不能把语义契约丢在原地。

    `tests/test_web_ui.py` 对页面源断言这些标记，高清版目标页搬进 `frontend/` 之后那份
    断言少了一处；缺口补在这里，而不是让它无声消失。
    """

    QUALITY_GOALS = FRONTEND / "src" / "react" / "quality-goals"

    def setUp(self):
        self.source = "\n".join(
            (self.QUALITY_GOALS / name).read_text(encoding="utf-8")
            for name in ("quality-goals.ts", "quality-goals-page.tsx"))

    def test_titles_still_use_middle_truncation(self):
        """文件名和番号的差别常在尾部，末尾省略会把要看的东西切掉。"""
        self.assertIn("data-middle-truncate", self.source)

    def test_empty_and_error_states_reuse_the_shared_components(self):
        """空态与失败态走 `src/react/components/` 的组合件，不是一行灰字。"""
        self.assertIn("<EmptyState", self.source)
        self.assertIn("<Note", self.source)
        self.assertIn("没有标记中的高清版目标", self.source)

    def test_readings_reuse_the_legacy_formatters(self):
        """时长、体积、来源名共用遗留口径，不在页面里再写一套。"""
        self.assertIn("from '@peach/legacy/core'", self.source)
        for helper in ("fmtDur(", "fmtSize(", "LOC["):
            self.assertIn(helper, self.source)

    def test_the_endpoint_is_declared_once(self):
        """端点在前端只能有一个声明处，就是这一页的数据模块。

        数据管理页那张「高清版」卡片读的是同一个真相，它随那一页迁移时接同一个
        `queryKey`。所以这里扫整棵 `frontend/src`——要拦的是「两个地方各写一遍这条 URL」。
        """
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        declared = [path for path in sources
                    if "/api/quality-goals?limit=200" in path.read_text(encoding="utf-8")]
        self.assertEqual(declared, [self.QUALITY_GOALS / "quality-goals.ts"],
                         f"端点声明在 {[path.name for path in declared]}")
        # 扫整个 web 层：路由表已经从 `web_contract.py` 搬到 `web_router.py`，
        # 前者只剩再导出。island 关心的是这条路由存在且只声明一次，不是它在哪个文件。
        routed = [path.name for path in sorted((ROOT / "src" / "peach").glob("web_*.py"))
                  if "quality-goals" in path.read_text(encoding="utf-8")]
        self.assertEqual(len(routed), 1, f"quality-goals 声明在 {routed}")


class ScrapingEndpointTests(unittest.TestCase):
    """来源和凭证页的几条端点，声明处都只有这一页的数据模块。

    这一页除了读列表还有三个写操作，散着写最容易在第二处悄悄改一条路径。基址是另外三条
    的前缀，所以按带引号的字面量数，`'/api/scraping'` 不会把 `/settings` 那条也算进来。
    """

    SCRAPING = FRONTEND / "src" / "react" / "scraping" / "scraping.ts"

    def test_the_endpoints_are_declared_once(self):
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        for endpoint in ("'/api/scraping'", "'/api/scraping/settings'",
                         "'/api/scraping/check'", "'/api/scraping/cover'",
                         "'/api/scraping/amane-bridge'", "'/api/scraping/amane-bridge/check'",
                         "'/api/scraping/amane-bridge/rebuild'"):
            with self.subTest(endpoint=endpoint):
                declared = [path for path in sources
                            if endpoint in path.read_text(encoding="utf-8")]
                self.assertEqual(declared, [self.SCRAPING],
                                 f"{endpoint} 声明在 {[path.name for path in declared]}")
        routed = [path.name for path in sorted((ROOT / "src" / "peach").glob("web_*.py"))
                  if "/api/scraping" in path.read_text(encoding="utf-8")]
        self.assertEqual(len(routed), 1, f"/api/scraping 的路由声明在 {routed}")


class LibraryProcessingEndpointTests(unittest.TestCase):
    """扫描与采集这一条端点只在数据模块里声明一次。

    它有两个读者——数据管理页那张卡片和目录页顶上那条横幅——两边读同一个 `queryKey`。
    端点在第二处再写一遍就是分头取数的第一步：各存一份快照之后，卡片说「已完成」、
    横幅还挂着进度。读同一个键这件事由 `SharedStateContractTests` 从另一头守。
    """

    LIBRARY_PROCESSING = (FRONTEND / "src" / "react" / "library-processing"
                          / "library-processing.ts")

    def test_the_endpoint_is_declared_once(self):
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        declared = [path for path in sources
                    if "'/api/library-processing'" in path.read_text(encoding="utf-8")]
        self.assertEqual(declared, [self.LIBRARY_PROCESSING],
                         f"端点声明在 {[path.name for path in declared]}")
        keyed = [path.name for path in sources
                 if "LIBRARY_PROCESSING_KEY = [" in path.read_text(encoding="utf-8")]
        self.assertEqual(keyed, ["library-processing.ts"], f"queryKey 声明在 {keyed}")
        routed = [path.name for path in sorted((ROOT / "src" / "peach").glob("web_*.py"))
                  if "/api/library-processing" in path.read_text(encoding="utf-8")]
        self.assertEqual(len(routed), 1, f"/api/library-processing 的路由声明在 {routed}")


class StatsEndpointTests(unittest.TestCase):
    """统计页从 `web/app.js` 搬过来时不能把语义契约丢在原地。

    `tests/test_web_ui.py` 曾对页面源断言这些标记：四张读数卡兼页签、三个空态、体积与
    来源名走遗留口径、观看那一行中间省略。行为由 `frontend/test/react/stats.test.tsx`
    守，这里守的是「搬家之后这些标记还在同一处」。
    """

    STATS = FRONTEND / "src" / "react" / "stats"

    def setUp(self):
        self.source = "\n".join(
            (self.STATS / name).read_text(encoding="utf-8")
            for name in ("stats.ts", "stats-page.tsx", "radial-card.tsx"))

    def test_titles_still_use_middle_truncation(self):
        """最近看过那一行是文件名，差别常在尾部，末尾省略会把要看的东西切掉。"""
        self.assertIn("data-middle-truncate", self.source)

    def test_empty_and_error_states_reuse_the_shared_components(self):
        """三个空态与失败态走 `src/react/components/` 的组合件，不是一行灰字。"""
        self.assertIn("<Note", self.source)
        for title in ("还没有视频", "还没有内容标签", "还没有观看记录",
                      "还没有标签来源", "还没有存储来源"):
            self.assertIn(title, self.source)
        self.assertEqual(self.source.count("<EmptyState"), 5)

    def test_readings_reuse_the_legacy_formatters(self):
        """体积与来源名共用遗留口径，不在页面里再写一套。"""
        self.assertIn("from '@peach/legacy/core'", self.source)
        for helper in ("fmtSize(", "LOC["):
            self.assertIn(helper, self.source)

    def test_the_four_readings_are_the_tabs(self):
        """四张读数卡本身就是页签：这一页没有别的主动作，读数就是入口。"""
        self.assertIn("react-aria-components", self.source)
        self.assertEqual(self.source.count("<MetricTab"), 4)

    def test_the_endpoint_is_declared_once(self):
        """端点在前端只能有一个声明处，就是这一页的数据模块。"""
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        declared = [path for path in sources
                    if "'/api/stats'" in path.read_text(encoding="utf-8")]
        self.assertEqual(declared, [self.STATS / "stats.ts"],
                         f"端点声明在 {[path.name for path in declared]}")
        keyed = [path.name for path in sources
                 if "STATS_KEY = [" in path.read_text(encoding="utf-8")]
        self.assertEqual(keyed, ["stats.ts"], f"queryKey 声明在 {keyed}")
        routed = [path.name for path in sorted((ROOT / "src" / "peach").glob("web_*.py"))
                  if '"/api/stats"' in path.read_text(encoding="utf-8")]
        self.assertEqual(len(routed), 1, f"/api/stats 的路由声明在 {routed}")


class TasteEndpointTests(unittest.TestCase):
    """口味页从 `web/app.js` 搬过来时不能把语义契约丢在原地。

    `tests/test_web_ui.py` 曾对页面源断言这些标记：两套证据是页签、四张读数卡、六种图、
    导入走 `X-Peach-Filename`、体积与站点圆标走遗留口径。行为由
    `frontend/test/react/taste.test.tsx` 守，这里守的是「搬家之后这些标记还在同一处」。
    """

    TASTE = FRONTEND / "src" / "react" / "taste"
    ENDPOINTS = ("/api/taste", "/api/taste/refresh", "/api/taste/import", "/api/taste/source")

    def setUp(self):
        self.source = "\n".join(
            (self.TASTE / name).read_text(encoding="utf-8")
            for name in ("taste.ts", "taste-page.tsx", "charts.tsx"))

    def test_each_endpoint_is_declared_once(self):
        """四条端点在前端各只有一个声明处，就是这一页的数据模块。

        第二处再写一遍就是分头取数的第一步：导入之后换进缓存的那一份和别处取回的那一份
        会同时挂在屏幕上，谁先回来谁说了算。
        """
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        for endpoint in self.ENDPOINTS:
            declared = [path for path in sources
                        if f"'{endpoint}'" in path.read_text(encoding="utf-8")]
            self.assertEqual(declared, [self.TASTE / "taste.ts"],
                             f"{endpoint} 声明在 {[path.name for path in declared]}")
        keyed = [path.name for path in sources
                 if "TASTE_REFRESH_KEY = [" in path.read_text(encoding="utf-8")]
        self.assertEqual(keyed, ["taste.ts"], f"queryKey 声明在 {keyed}")

    def test_the_window_rides_on_the_query_key(self):
        """七天和全部时间是两份真相：键上带范围，切换时留住上一份。"""
        self.assertIn("tasteKey = (window: string) => ['taste', window]", self.source)
        self.assertIn("placeholderData: keepPreviousData", self.source)

    def test_the_import_keeps_the_filename_header(self):
        """文件原样当请求体发，文件名走请求头，服务端不必多接一个 multipart 解析器。"""
        self.assertIn("'Content-Type': 'application/octet-stream'", self.source)
        self.assertIn("'X-Peach-Filename': encodeURIComponent(file.name)", self.source)

    def test_the_two_bodies_of_evidence_are_tabs(self):
        """浏览器记录与 Peach 内部是两份证据，并排摆会被读成互相印证。"""
        self.assertIn("react-aria-components", self.source)
        for name in ("浏览器记录", "Peach 内部"):
            self.assertIn(name, self.source)

    def test_every_chart_is_a_react_component(self):
        """六种图都在 React 里：雷达、排行条、读数卡、两张热力图、创作者流向。"""
        for component in ("TasteRadar", "RankedBars", "SummaryCard", "ActivityHeat", "CreatorSankey"):
            self.assertIn(component, self.source)
        self.assertIn("from 'd3-sankey'", self.source)

    def test_empty_and_error_states_reuse_the_shared_components(self):
        """空态与失败态走 `src/react/components/` 的组合件，不是一行灰字。"""
        self.assertIn("<Note", self.source)
        for title in ("暂无足够证据", "还没有数据源", "还没有可探索的入口"):
            self.assertIn(title, self.source)

    def test_readings_reuse_the_legacy_formatters(self):
        """体积与站点圆标共用遗留口径，不在页面里再写一套。"""
        self.assertIn("from '@peach/legacy/core'", self.source)
        for helper in ("fmtSize(", "siteMarkUrl("):
            self.assertIn(helper, self.source)


class FollowManageEndpointTests(unittest.TestCase):
    """关注管理页从 `web/app.js` 搬过来时不能把语义契约丢在原地。

    这一页同时管着三份节律不同的真相（来源清单、凭据状态、两趟后台任务），行为由
    `frontend/test/react/follow-manage.test.tsx` 与 `follow-alias.test.tsx` 守；这里守的是
    「搬家之后端点、键与身份口径还在同一处」。
    """

    PAGE = FRONTEND / "src" / "react" / "follow-manage"
    ENDPOINTS = ("/api/follow", "/api/follow/credentials", "/api/follow/check", "/api/follow/source",
                 "/api/follow/resolve", "/api/follow/suggest", "/api/follow/author-alias",
                 "/api/follow/credential", "/api/follow/status")

    def setUp(self):
        self.data = (self.PAGE / "follow-manage.ts").read_text(encoding="utf-8")
        self.source = "\n".join(
            (self.PAGE / name).read_text(encoding="utf-8")
            for name in ("follow-manage.ts", "follow-manage-page.tsx", "source-list.tsx",
                         "add-source.tsx", "alias-manager.tsx", "source-view.tsx"))

    def test_each_endpoint_is_declared_once(self):
        """九条端点在前端各只有一个声明处，就是这一页的数据模块。

        第二处再写一遍就是分头取数的第一步：写完之后换进缓存的那一份和别处取回的那一份
        会同时挂在屏幕上，谁先回来谁说了算。
        """
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        for endpoint in self.ENDPOINTS:
            declared = [path for path in sources
                        if f"'{endpoint}'" in path.read_text(encoding="utf-8")]
            self.assertEqual(declared, [self.PAGE / "follow-manage.ts"],
                             f"{endpoint} 声明在 {[path.name for path in declared]}")

    def test_three_rhythms_are_three_keys(self):
        """清单、凭据与后台任务各走各的键：合成一个键，开关一条来源就会重问一遍凭据文件。"""
        for key in ("FOLLOW_MANAGE_KEY = ['follow-manage']",
                    "FOLLOW_CREDENTIALS_KEY = ['follow-manage', 'credentials']",
                    "FOLLOW_CHECK_KEY = ['follow-manage', 'check']",
                    "FOLLOW_RESOLVE_KEY = ['follow-manage', 'resolve']"):
            self.assertIn(key, self.data)

    def test_the_first_screen_takes_only_the_first_screen(self):
        """预取只取铺满首屏要的两份，后台任务的快照等挂载之后自己去问。"""
        prefetch = self.data[self.data.index("export async function prefetchFollowManage"):]
        prefetch = prefetch[:prefetch.index("\n}")]
        self.assertIn("FOLLOW_MANAGE_KEY", prefetch)
        self.assertIn("FOLLOW_CREDENTIALS_KEY", prefetch)
        for later in ("FOLLOW_CHECK_KEY", "FOLLOW_RESOLVE_KEY"):
            self.assertNotIn(later, prefetch, f"{later} 不属于首屏")

    def test_a_single_row_write_swaps_that_row(self):
        """开关、移除一条来源都只换缓存里的那一条，不为一次点击把整页重取一遍。"""
        self.assertIn("queryClient.setQueryData<FollowData>(FOLLOW_MANAGE_KEY", self.data)
        self.assertIn("export function patchSource(", self.data)
        self.assertIn("export function dropSources(", self.data)

    def test_row_identity_is_the_source_id(self):
        """行的身份是来源 ID：换页、换排序、换视图之后勾选的还是同一批来源。"""
        self.assertIn("from '@tanstack/react-table'", self.source)
        self.assertIn("getRowId: (row) => String(row.source.id)", self.source)
        self.assertIn("manualSorting: true", self.source)

    def test_both_views_sort_the_whole_result_set(self):
        """两种视图共用一套比较器，排的是全集：只排当前页会让翻页看起来像换了一份数据。"""
        self.assertIn("export const COLUMN_SORT", self.data)
        self.assertIn("export function authorGroups(", self.data)
        self.assertIn("export function tableRows(", self.data)
        self.assertIn("getPaginationRowModel", self.source)


class ReviewEndpointTests(unittest.TestCase):
    """人工复核页从 `web/app.js` 搬过来时不能把语义契约丢在原地。

    `web/app.js` 只剩一张骨架和一次挂载，页面行为由 `frontend/test/react/review.test.tsx`
    守；这里守的是「搬家之后挂载点、端点与键还在同一处」。
    """

    PAGE = FRONTEND / "src" / "react" / "review"
    ENDPOINTS = ("/api/review", "/api/review/decision", "/api/review/genre")

    def setUp(self):
        self.data = (self.PAGE / "review.ts").read_text(encoding="utf-8")
        self.source = "\n".join(
            (self.PAGE / name).read_text(encoding="utf-8")
            for name in ("review.ts", "review-page.tsx", "review-card.tsx",
                         "review-evidence.tsx", "candidate-form.tsx", "bulk-toolbar.tsx"))

    def test_the_island_mounts_where_the_skeleton_stands(self):
        """遗留层按名字挂这一屏，名字在注册表、类型表和产物里都要对得上。

        骨架和岛落在同一个容器上，读完数据只是把占位换成内容；名字对不上的话遗留层
        照样跑完，屏幕上停在那张骨架。
        """
        islands = (FRONTEND / "src" / "islands.ts").read_text(encoding="utf-8")
        self.assertIn("review: ReactBundle.ReviewProps;", islands)
        self.assertIn("review: { react: 'review' },", islands)
        app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("'/review':()=>reviewSkeletonHtml(),", app_js)
        self.assertIn('data-skeleton="review"', app_js)
        self.assertIn("await ui.mountIsland('review',$('#stats'),{...params,", app_js)
        if not REACT_BUNDLE.is_file():
            self.skipTest(
                f"{REACT_BUNDLE.relative_to(ROOT)} 不在：先 `npm --prefix frontend run build`")
        self.assertIn("\n\treview: {", REACT_BUNDLE.read_text(encoding="utf-8"),
                      "产物里没有这一页，先跑 npm --prefix frontend run build")

    def test_each_endpoint_is_declared_once(self):
        """三条端点与那一个 `queryKey` 在前端各只有一个声明处，就是这一页的数据模块。

        这一页读一整条队列（一次几兆、上千行），判定、批量判定和收录 genre 三个写操作
        全都只改缓存里那几行。第二处再写一遍就等于给同一条队列开了第二份快照：判过的行
        在一处消失、在另一处还列着，而两处都不报错。
        """
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        for endpoint in self.ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                declared = [path for path in sources
                            if f"'{endpoint}'" in path.read_text(encoding="utf-8")]
                self.assertEqual(declared, [self.PAGE / "review.ts"],
                                 f"{endpoint} 声明在 {[path.name for path in declared]}")
        keyed = [path.name for path in sources
                 if "REVIEW_KEY = [" in path.read_text(encoding="utf-8")]
        self.assertEqual(keyed, ["review.ts"], f"queryKey 声明在 {keyed}")
        routed = [path.name for path in sorted((ROOT / "src" / "peach").glob("web_*.py"))
                  if "/api/review" in path.read_text(encoding="utf-8")]
        self.assertEqual(len(routed), 1, f"/api/review 的路由声明在 {routed}")

    def test_the_queue_has_one_query_key(self):
        self.assertIn("export const REVIEW_KEY = ['review'] as const;", self.data)
        self.assertIn("queryClient.setQueryData<ReviewData>(REVIEW_KEY", self.data)
        self.assertIn("export function dropReviewRows(", self.data)

    def test_opening_review_only_reads_the_queue(self):
        """自动落库已跟随处理任务完成，打开复核页不能再发写请求。"""
        prefetch = self.data[self.data.index("export async function prefetchReview"):]
        prefetch = prefetch[:prefetch.index("\n}")]
        self.assertIn("queryKey: REVIEW_KEY", prefetch)
        self.assertNotIn("apiSend", prefetch)

    def test_empty_and_error_states_reuse_the_shared_components(self):
        """空态与失败态走 `src/react/components/` 的组合件，不是一行灰字。"""
        self.assertIn("<Note", self.source)
        self.assertIn("<EmptyState", self.source)
        for title in ("暂无候选", "这批作品尚未抽帧"):
            self.assertIn(title, self.source)

    def test_the_categories_and_their_names_live_in_one_table(self):
        """分类名只有这一张表，遗留层那份骨架按同一批名字画占位。"""
        labels = self.data.split("export const REVIEW_LABELS = {", 1)[1].split("} as const;", 1)[0]
        pairs = re.findall(r"(\w+): '([^']+)',", labels)
        self.assertEqual(len(pairs), 10, f"分类表读出来 {len(pairs)} 条")
        app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        for category, label in pairs:
            self.assertIn(f"{category}:'{label}'", app_js,
                          f"骨架里没有 {category}，占位会比到货少一枚")


class ConfigurationEndpointTests(unittest.TestCase):
    """整页和各分区读同一条 `/api/configuration`，两份产物各打包一份这个模块。"""

    def test_the_endpoint_is_declared_once(self):
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        declared = [path.name for path in sources
                    if "'/api/configuration'" in path.read_text(encoding="utf-8")]
        self.assertEqual(declared, ["configuration-endpoints.ts"], f"端点声明在 {declared}")

    def test_the_first_screen_and_the_sections_share_one_query_key(self):
        """挂载状态那一块重取回来的是整份配置，换进整页那一个键：屏幕上只有一份真相。"""
        sources = sorted(path for path in (FRONTEND / "src" / "react").rglob("*.ts*"))
        declared = [path.name for path in sources
                    if "CONFIGURATION_KEY = [" in path.read_text(encoding="utf-8")]
        self.assertEqual(declared, ["configuration.ts"], f"queryKey 声明在 {declared}")


class SharedStateContractTests(unittest.TestCase):
    """一份数据有第二个读者时，两个读者读同一个 `queryKey`（ADR-0031）。

    共享数据的家是 `src/react/query.ts` 那一个 QueryClient。这条门槛盯的是源码布局：
    等到跑起来才发现两处各存一份，已经晚了。
    """

    def test_the_react_subtree_has_exactly_one_query_client(self):
        sources = sorted(path for path in (FRONTEND / "src").rglob("*.ts*"))
        declared = [path.name for path in sources
                    if "new QueryClient(" in path.read_text(encoding="utf-8")]
        self.assertEqual(declared, ["query.ts"], f"QueryClient 建在 {declared}")

    def test_pages_do_not_keep_a_second_copy_of_shared_data(self):
        """跨页共享的数据不另起一套订阅：`@preact/signals` 已经没有读者。"""
        outside = [path.name for path in sorted((FRONTEND / "src").rglob("*.ts*"))
                   if "@preact/signals" in path.read_text(encoding="utf-8")]
        self.assertEqual(outside, [],
                         f"{outside} 用了 signal：跨页共享请读同一个 queryKey，局部状态用 hooks")


class VitestTests(unittest.TestCase):
    """vitest、tsc 与 lint 走同一个测试入口，但缺 Node 时跳过而不是红。

    三者互不覆盖：vitest 经 Vite 转译时只剥掉类型、不做检查，类型错误照样跑绿；
    裸色值、任意值和在 BoardUI 组件上改样式，类型和行为测试都看不见。
    """

    def _npm(self, tool: str, package: str) -> str:
        npm = shutil.which("npm")
        if npm is None:
            missing_prerequisite(f"跳过 {tool}：本机没有 npm。装 Node 24+ 后 `-Scope web` 会带上它")
        if not (FRONTEND / "node_modules" / package).is_dir():
            missing_prerequisite(f"跳过 {tool}：frontend/node_modules 还没装，先 `npm --prefix frontend ci`")
        return npm

    def test_the_frontend_sources_typecheck(self):
        npm = self._npm("tsc", "typescript")
        completed = subprocess.run(
            [npm, "--prefix", str(FRONTEND), "run", "typecheck", "--silent"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(FRONTEND), check=False)
        self.assertEqual(completed.returncode, 0, f"{completed.stdout}\n{completed.stderr}")

    def test_the_island_suite_has_a_bounded_worker_pool(self):
        config = (FRONTEND / "vitest.config.ts").read_text(encoding="utf-8")
        self.assertIn("maxWorkers: 4", config)

    def test_the_react_sources_follow_the_design_system_lint(self):
        """`@shadcn/lint` 挡住裸色值、任意值、内联样式和在 BoardUI 组件上改样式（ADR-0031）。"""
        npm = self._npm("lint", "oxlint")
        completed = subprocess.run(
            [npm, "--prefix", str(FRONTEND), "run", "lint", "--silent", "--", "--format=json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(FRONTEND), check=False)
        output = f"{completed.stdout}\n{completed.stderr}"
        self.assertEqual(completed.returncode, 0, output)
        report = json.loads(completed.stdout)
        self.assertEqual(report["diagnostics"], [], output)
        # 没有问题时 Oxlint 什么都不打印，路径写错查了 0 个文件也照样退出 0。
        self.assertGreater(report["number_of_files"], 0, output)

    def test_the_island_suite_passes(self):
        npm = self._npm("vitest", "vitest")
        completed = subprocess.run(
            [npm, "--prefix", str(FRONTEND), "test", "--silent"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(FRONTEND), check=False)
        output = f"{completed.stdout}\n{completed.stderr}"
        # vitest 的着色随宿主终端能力漂移，计数断言只认去码后的纯文本；
        # 退出码与用例数两道判据不受着色影响。
        plain = re.sub(r"\x1b\[[0-9;]*m", "", output)
        self.assertEqual(completed.returncode, 0, output)
        self.assertRegex(plain, r"Tests\s+\d+ passed", output)
        self.assertNotRegex(plain, r"Tests\s+0 passed", "vitest 一个用例都没跑")
        counted = re.search(r"Tests\s+(\d+) passed", plain)
        assert counted is not None
        self.assertGreaterEqual(int(counted.group(1)), 10, output)


class BrowserSuiteWorkflowTests(unittest.TestCase):
    """CI 里的浏览器冒烟与设计决定断言只能执行或失败，不能静默跳过。

    缺前置条件在 CI 判失败（`tests/support/conditions.py`）只做了一半：工作流还得真的装齐
    Node、依赖、ffmpeg 与 Chrome，并让结果进入 `verified` 的汇总。任一处被删掉，冒烟就回到
    从未在 CI 执行的状态，或者让 `python` 矩阵的全量行判失败。
    """

    @classmethod
    def setUpClass(cls):
        cls.workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    def job(self, name: str) -> str:
        found = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  \S|\Z)", self.workflow)
        self.assertIsNotNone(found, f"CI 没有 {name} job")
        return found.group(1)

    def test_the_browser_job_installs_every_prerequisite_and_runs_the_web_scope(self):
        job = self.job("web-e2e")
        for step in ("runs-on: windows-latest", "actions/setup-node", 'node-version: "24"',
                     "npm --prefix frontend ci", "FedericoCarboni/setup-ffmpeg",
                     'ffmpeg-version: "9.0.1"',
                     "PEACH_E2E_CHROME=", "& .\\scripts\\test.ps1 -Scope web"):
            self.assertIn(step, job, f"web-e2e job 缺了 {step}")

    def test_the_summary_requires_the_browser_job(self):
        needs = re.search(r"(?ms)^  verified:\n.*?^    needs: \[([^\]]*)\]", self.workflow)
        self.assertIsNotNone(needs, "verified job 没有 needs 列表")
        self.assertIn("web-e2e", [name.strip() for name in needs.group(1).split(",")])

    def test_the_browser_job_yields_to_a_wide_matrix_that_already_runs_the_web_scope(self):
        """全量矩阵的 Windows 行本身就跑 `web` 域，`web-e2e` 再跑就是同一批用例两遍。

        它只按 `plan` 的 `wide` 让路，汇总也只在 `wide` 时接受它的 skipped；条件写错或
        `wide` 没写进 `GITHUB_OUTPUT`，PR 上它一停，汇总就红，不会变成静默不跑。
        """
        job = self.job("web-e2e")
        self.assertIn("needs: [plan]", job)
        self.assertIn("if: needs.plan.outputs.wide != 'true'", job)
        verified = self.job("verified")
        self.assertIn("WIDE: ${{ needs.plan.outputs.wide }}", verified)
        self.assertIn('name == "web-e2e" and wide and job["result"] == "skipped"', verified)
        self.assertIn('"wide"', (ROOT / "scripts" / "ci_plan.py").read_text(encoding="utf-8"),
                      "ci_plan.py 没把 wide 写进 GITHUB_OUTPUT")

    def test_matrix_rows_beyond_core_install_what_the_node_suites_need(self):
        job = self.job("python")
        for step in ("actions/setup-node", "npm --prefix frontend ci",
                     "FedericoCarboni/setup-ffmpeg", 'ffmpeg-version: "9.0.1"',
                     "PEACH_E2E_CHROME="):
            self.assertIn(step, job, f"python 矩阵缺了 {step}，全量行上的用例会判失败")


class CloudDriveGuideScopeTests(unittest.TestCase):
    """配置页那一版只讲怎么填，原理和取证在 `docs/CLOUDDRIVE.md`，两边不各写一份。

    页内讲原理有两个代价。一是长度：三处缓存的分工、Mbps 与 MB/s 的换算、起步值的
    取证摊开就是十几行，读的人为了填一个数字得先读完一篇。二是维护：这些话同时写在
    页面和运维文档里，改一次要改两处，页面那一份必然先过期。
    判据是「同一句话只在一个地方维护」——页内留填哪里、填多少、怎么确认，其余由外链
    指向仓库那一份，`docs/OPERATIONS.md` 同样只留指针。
    """

    def setUp(self):
        self.source = (FRONTEND / "src" / "react" / "settings" / "clouddrive-guide.tsx").read_text(
            encoding="utf-8")
        self.doc = (ROOT / "docs" / "CLOUDDRIVE.md").read_text(encoding="utf-8")
        self.operations = (ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")

    def test_the_page_says_where_to_fill_and_how_to_confirm(self):
        for phrase in ("缓存上限和清理方式填在", "读取长度和下载线程填在",
                       "上限不要填 0", "改一个管不住另外两个", "确认存住了"):
            self.assertIn(phrase, self.source, "配置页要能独立完成一次填写")
        for moved in ("Mbps", "MB/s", "911", "客户端标出的上限", "WebDAV"):
            self.assertNotIn(moved, self.source, f"「{moved}」这一段归 docs/CLOUDDRIVE.md")

    def test_the_page_links_to_the_document_that_holds_the_reasoning(self):
        self.assertIn('<ExternalLink href="https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md">',
                      self.source)

    def test_the_document_holds_the_steps_the_reasoning_and_the_provenance(self):
        for section in ("## 配置步骤", "## 三处缓存是三处设置", "## 缓存上限与清理",
                        "## 读取长度与线程", "## 码率与速度不是一个单位",
                        "## 起步值来自哪里"):
            self.assertIn(section, self.doc)
        self.assertIn("[CloudDrive 配置与调优](CLOUDDRIVE.md)", self.operations)
        for moved in ("911", "LRU", "42169be3", "10\u201320 GiB"):
            self.assertNotIn(moved, self.operations,
                             f"「{moved}」这一段归 docs/CLOUDDRIVE.md")


if __name__ == "__main__":
    unittest.main()
