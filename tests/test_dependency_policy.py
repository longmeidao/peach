from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest

from scripts import adopt_dependency_bump as adopt

ROOT = Path(__file__).resolve().parents[1]


class DependencyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.pyproject = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    def test_python_dependencies_are_exactly_pinned(self):
        declared = list(self.pyproject["project"]["dependencies"])
        for values in self.pyproject["project"]["optional-dependencies"].values():
            declared.extend(values)
        self.assertTrue(declared)
        for requirement in declared:
            package = requirement.split(";", 1)[0].strip()
            self.assertRegex(package, r"^[A-Za-z0-9_.-]+==[^=<>~!]+$", requirement)
        for requirement in self.pyproject["build-system"]["requires"]:
            self.assertRegex(requirement, r"^[A-Za-z0-9_.-]+==[^=<>~!]+$", requirement)

    def test_every_imported_external_module_has_a_declared_owner(self):
        owners = {
            "tldextract": "tldextract",
            "AppKit": "pyobjc-framework-Cocoa",
            "PIL": "pillow",
            "PyObjCTools": "pyobjc-framework-Cocoa",
            "apscheduler": "APScheduler",
            "browserexport": "browserexport",
            "bs4": "beautifulsoup4",
            "curl_cffi": "curl_cffi",
            "cv2": "opencv-python-headless",
            "fastapi": "fastapi",
            "filelock": "filelock",
            "httpx": "httpx",
            "itsdangerous": "itsdangerous",
            "numpy": "numpy",
            "objc": "pyobjc-framework-Cocoa",
            "opencc": "opencc",
            "p115client": "p115client",
            "pystray": "pystray",
            "resvg_py": "resvg-py",
            "starlette": "starlette",
            "uvicorn": "uvicorn",
            "zeroconf": "zeroconf",
        }
        imported = set()
        for folder in (ROOT / "src", ROOT / "scripts"):
            for path in folder.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.update(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        imported.add(node.module.split(".")[0])
        external = imported - sys.stdlib_module_names - {"peach"}
        self.assertEqual(external - owners.keys(), set())

        requirements = self.pyproject["project"]["dependencies"][:]
        for values in self.pyproject["project"]["optional-dependencies"].values():
            requirements.extend(values)
        names = {re.split(r"[=; ]", value, maxsplit=1)[0].casefold()
                 for value in requirements}
        self.assertEqual(
            {owner.casefold() for module, owner in owners.items() if module in external} - names,
            set(),
        )

    def test_frontend_manifest_is_exact_and_matches_vendored_paths(self):
        manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["private"])
        versions = manifest["devDependencies"]
        self.assertEqual(set(versions), {"@phosphor-icons/core", "healthicons",
                                         "lucide-static", "swiper", "video.js", "remixicon"})
        for version in versions.values():
            self.assertRegex(version, r"^\d+\.\d+\.\d+$")

        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        # 首屏只剩 video.js 的样式表，脚本按需加载、版本钉在 app.js 的加载器里，
        # 所以两侧都要核。只核 index 的话，加载器里写错版本没人会拦。
        self.assertIn(f'/vendor/videojs/{versions["video.js"]}/video-js.min.css', index)
        self.assertIn(f'/vendor/videojs/{versions["video.js"]}/video.min.js', app)
        self.assertIn(f"Lucide static {versions['lucide-static']}", index)
        self.assertIn(f"Health Icons {versions['healthicons']}", index)
        self.assertIn(f"Phosphor {versions['@phosphor-icons/core']} regular", index)
        self.assertIn(f"/vendor/swiper/{versions['swiper']}/", app)

    def test_every_sprite_symbol_has_a_declared_owner(self):
        """雪碧图里每一枚 symbol 都归某一套图标集或自绘名单。

        没有归属的那几枚只画在 index.html 里，`npm run vendor:web` 从不刷新它们，
        换上游版本时新旧画法混在同一条按钮上。归属由生成脚本自己在写文件前拦，
        这里核的是那道拦阻还在、名单也还覆盖得住实际的雪碧图。
        """
        generator = (ROOT / "scripts" / "vendor_web_dependencies.mjs").read_text(
            encoding="utf-8")
        self.assertIn("const handDrawnIcons = new Set([", generator)
        self.assertIn("if (orphans.length) {", generator)

        def body(block: str) -> str:
            return generator.split(block, 1)[1].split("]);", 1)[0]

        def map_keys(block: str) -> set[str]:
            # Map 的第二项是上游名字，只取键；否则 sort-desc 这类上游名会混进来。
            return set(re.findall(r'\["([a-z0-9-]+)"', body(block)))

        owned = (map_keys("const lucideIcons = new Map([")
                 | map_keys("const phosphorIcons = new Map([")
                 | set(re.findall(r'"([a-z0-9-]+)"',
                                  body("const handDrawnIcons = new Set([")))
                 | {"sperm"})
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        sprite = {name for name in re.findall(r'id="i-([a-z0-9-]+)"', index)
                  if not name.startswith("player-")}
        self.assertEqual(sprite - owned, set())
        # 名单里挂着雪碧图已经没有的名字，等于换版本时静默少刷一枚。
        self.assertEqual(owned - sprite - {"sperm"}, set())

    def test_automation_monitors_all_dependency_manifests(self):
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        for ecosystem in ("uv", "npm", "github-actions"):
            self.assertIn(f"package-ecosystem: {ecosystem}", dependabot)
        workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(
            encoding="utf-8")
        self.assertIn("npm run check:vendor", workflow)
        self.assertIn("& .\\scripts\\test.ps1", workflow)
        self.assertIn("./scripts/test.sh", workflow)

    def test_every_npm_manifest_under_dependabot_has_a_takeover_recipe(self):
        """带派生产物的清单，`adopt_dependency_bump.py` 必须认得。

        Dependabot 只改 manifest 与 lock，派生产物它算不出来（只读 token 推不回
        `dependabot/**`），于是 `check:vendor` 或 island 产物那一关必红。这条把「新登记了
        一份 npm 清单却没给接管方式」变成本地就红，而不是等下一个周一的 PR 上才发现。
        """
        dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
        directories = re.findall(r"package-ecosystem: npm\s+directory: (\S+)", dependabot)
        self.assertTrue(directories, "dependabot.yml 里没有 npm 登记")
        known = {name for recipe in adopt.RECIPES.values() for name in recipe["manifests"]}
        for directory in directories:
            manifest = f"{directory.strip('/')}/package.json".lstrip("/")
            self.assertIn(manifest, known, f"{manifest} 没有接管方式，见 adopt_dependency_bump.RECIPES")
            self.assertIn(manifest.replace("package.json", "package-lock.json"), known)

    def test_takeover_recognises_only_the_files_it_owns(self):
        """接管只暂存清单与它自己的派生产物；别的改动一律拦下来让人看。

        盲按前缀暂存会把无关文件带上，而 `web/index.html` 是整条路径不是目录——
        `startswith` 会把 `web/index.html.bak` 一类也算进来。
        """
        key, recipe = adopt.recipe_for(["package-lock.json"])
        self.assertEqual(key, "web")
        for path in ("package.json", "web/index.html", "web/vendor/lucide/1.40.0/ORIGIN.md"):
            self.assertTrue(adopt.owned_by(recipe, path), path)
        for path in ("web/index.html.bak", "web/dist/peach-ui.js", "src/peach/api.py"):
            self.assertFalse(adopt.owned_by(recipe, path), path)
        self.assertEqual(adopt.recipe_for(["frontend/package.json"])[0], "frontend")
        # uv 与 github-actions 的升级没有派生产物，说清楚「直接合」，不要含糊地失败。
        with self.assertRaisesRegex(RuntimeError, "直接合并"):
            adopt.recipe_for(["uv.lock", ".github/workflows/test.yml"])
        with self.assertRaisesRegex(RuntimeError, "同时改了"):
            adopt.recipe_for(["package.json", "frontend/package.json"])

    def test_the_takeover_commit_message_passes_the_readme_impact_gate(self):
        """`README-Impact` 与 `Co-Authored-By` 必须同一个 trailer 块、中间不空行。

        隔一个空行 `git interpret-trailers` 就只认后一个，`ready` 会报「交付提交须有唯一
        README-Impact」——这条我在 0.29.0 那次亲手踩过。
        """
        signature = "Claude Code (Opus 5) <noreply@anthropic.com>"
        message = adopt.commit_message("web", ["lucide-static 1.38.0 → 1.40.0"],
                                       "4", signature)
        self.assertIn("\nREADME-Impact: none; ", message)
        self.assertRegex(message, r"README-Impact: none; [^\n]+\nCo-Authored-By: ")
        self.assertIn("PR #4", message)
        self.assertIn("npm run vendor:web", message)
        self.assertIn("lucide-static 1.38.0 → 1.40.0", message)
        self.assertIn(f"Co-Authored-By: {signature}", message)
        # 署名由调用方给：跑接管的可能是任一个智能体，写死一个工具名就是记错人。
        with self.assertRaisesRegex(ValueError, "--co-author"):
            adopt.commit_message("web", [], "4", "Claude Code")

    def test_the_vendor_check_prints_how_to_fix_itself(self):
        """`check:vendor` 失败时要印出重算命令。

        只列不同步的路径时，看到这一段的人得先翻 `package.json` 才知道入口叫什么；
        Dependabot 的 PR 上尤其——那些改动不是人写的，没人知道漏了哪一步。
        """
        source = (ROOT / "scripts/vendor_web_dependencies.mjs").read_text(encoding="utf-8")
        failure = source[source.index("前端固定依赖未同步"):source.index("process.exit(1)")]
        self.assertIn("npm run vendor:web", failure)
        self.assertIn("adopt_dependency_bump.py", failure)

    def test_uv_installation_preserves_interpreter_and_wheel_contracts(self):
        self.assertRegex(self.pyproject["tool"]["uv"]["required-version"],
                         r"^==\d+\.\d+\.\d+$")
        module = self.pyproject['tool']['setuptools']['dynamic']['version']['attr'].rsplit('.', 1)[0]
        version_file = f"src/{module.replace('.', '/')}/__init__.py"
        keys = {entry.get('file') for entry in self.pyproject['tool']['uv']['cache-keys']}
        self.assertTrue({'pyproject.toml', 'setup.py', version_file} <= keys)
        workflow = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        for source in (workflow, release):
            self.assertIn("astral-sh/setup-uv@", source)
            self.assertIn("cache-dependency-glob: uv.lock", source)
            self.assertIn("uv sync --locked", source)
            self.assertIn("uv pip check --python .venv/Scripts/python.exe", source)
            self.assertIn("if ($LASTEXITCODE -ne 0)", source)
        self.assertIn("uv pip check --python .venv/bin/python", workflow)
        self.assertIn("uv build --wheel --out-dir wheelhouse", workflow)
        self.assertIn("python -m pip install --no-cache-dir wheelhouse/*.whl", workflow)


if __name__ == "__main__":
    unittest.main()
