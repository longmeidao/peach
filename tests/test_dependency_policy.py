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
        self.assertEqual(set(versions), {"healthicons", "lucide-static", "swiper", "video.js"})
        for version in versions.values():
            self.assertRegex(version, r"^\d+\.\d+\.\d+$")

        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn(f'/vendor/videojs/{versions["video.js"]}/', index)
        self.assertIn(f"Lucide static {versions['lucide-static']}", index)
        self.assertIn(f"Health Icons {versions['healthicons']}", index)
        self.assertIn(f"/vendor/swiper/{versions['swiper']}/", app)

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
