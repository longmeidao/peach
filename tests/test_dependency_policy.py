from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest


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
            "AppKit": "pyobjc-framework-Cocoa",
            "PIL": "pillow",
            "PyObjCTools": "pyobjc-framework-Cocoa",
            "apscheduler": "APScheduler",
            "browserexport": "browserexport",
            "bs4": "beautifulsoup4",
            "curl_cffi": "curl_cffi",
            "cv2": "opencv-python-headless",
            "fastapi": "fastapi",
            "httpx": "httpx",
            "objc": "pyobjc-framework-Cocoa",
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
                                         "lucide-static", "swiper", "video.js"})
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
        for ecosystem in ("pip", "npm", "github-actions"):
            self.assertIn(f"package-ecosystem: {ecosystem}", dependabot)
        workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(
            encoding="utf-8")
        self.assertIn("npm run check:vendor", workflow)
        self.assertIn("& .\\scripts\\test.ps1", workflow)
        self.assertIn("./scripts/test.sh", workflow)


if __name__ == "__main__":
    unittest.main()
