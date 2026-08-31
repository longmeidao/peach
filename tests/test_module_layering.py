"""模块分层门槛。

Peach 是模块化单体，分层靠约定而不是包结构，所以约定必须有人守。这里守一条：
**web 层之外的模块不许 import web 层。**

这条规则不是凭空立的。`catalog_rules.py` 原名 `web_logic.py`，而 `repository.py`
（数据层）要用它的 `is_jav_code`，`taste_history.py` 要用 `LENGTH_TAGS`——数据层
import 一个叫 web 的模块，读代码的人只会得出「分层反了」的结论。实际反的是名字，
但名字骗人和结构错了一样难查。改名之后加这条断言，让下一次真反了的时候直接报错。
"""
import ast
import pathlib
import unittest

import peach


SOURCE_ROOT = pathlib.Path(peach.__file__).parent

#: web 层自己。层内互相依赖是正常的。
WEB_MODULES = {"web_contract", "web_follow", "web_activity", "web_playlists"}

#: 应用层组装点：把 web 层挂上 FastAPI 是它的职责，方向是对的。
COMPOSITION_ROOTS = {"api"}


def _local_imports(path: pathlib.Path) -> set[str]:
    """取出一个模块 import 的本包模块名（`from .x import y` 与 `from . import x`）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            if node.module:
                names.add(node.module.split(".")[0])
            else:
                names.update(alias.name for alias in node.names)
    return names


#: 项目根：`src/peach` 的上两级。脚本和源码要一起扫。
PROJECT_ROOT = SOURCE_ROOT.parent.parent


def _python_sources() -> list[pathlib.Path]:
    return sorted(SOURCE_ROOT.glob("*.py")) + sorted((PROJECT_ROOT / "scripts").glob("*.py"))


class SharedRuleTests(unittest.TestCase):
    """领域规则只许有一份实现。

    番号归一化曾经有三份：`catalog_rules.normalise_code_key`、
    `scripts/fetch_jav_covers.normalise_code`、`scripts/scrape_codes.normalise`。
    三份逐字相同，靠一句「与 scrape_codes 同口径」的注释维持一致——注释不是门槛。

    番号既是身份判定也是封面缓存键：三份一旦漂移，同一部片会解析出两个键，
    封面缓存静默失配，而两边的数都「对」，只是口径不同。
    """

    #: 归一化实现的指纹。`FC2-PPV-` 的拼装和番号形态的正则，凑齐就是又抄了一份。
    FINGERPRINTS = ('f"FC2-PPV-', r'([A-Z]+)-?(\d+)$')

    def test_release_code_normalisation_exists_once(self):
        offenders = []
        for path in _python_sources():
            if path.name == "catalog_rules.py":
                continue
            text = path.read_text(encoding="utf-8")
            if all(mark in text for mark in self.FINGERPRINTS):
                offenders.append(path.name)
        self.assertEqual(
            offenders, [],
            "番号归一化又被抄了一份，请改 import catalog_rules.normalise_code_key",
        )

    def test_pure_rules_are_imported_from_the_policy_module_not_through_web(self):
        """纯规则要直接从 `catalog_rules` 取，不要借道 web 层的再导出。

        `web_contract` 把 `is_jav_code` 再导出了一遍，于是脚本写成
        `from peach.web_contract import is_jav_code`——为一条纯规则拉起整个 web 层，
        读代码的人还会以为这条规则属于 web。
        """
        offenders = []
        for path in sorted((PROJECT_ROOT / "scripts").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for rule in ("is_jav_code", "normalise_code_key", "LENGTH_TAGS"):
                if f"from peach.web_contract import" in text and rule in text.split(
                        "from peach.web_contract import", 1)[1].split("\n", 1)[0]:
                    offenders.append(f"{path.name} → web_contract.{rule}")
        self.assertEqual(offenders, [],
                         "纯规则请直接从 peach.catalog_rules 取")


class LayeringTests(unittest.TestCase):
    def test_only_web_modules_and_the_composition_root_import_the_web_layer(self):
        offenders = []
        for path in sorted(SOURCE_ROOT.glob("*.py")):
            module = path.stem
            if module in WEB_MODULES or module in COMPOSITION_ROOTS:
                continue
            for imported in sorted(_local_imports(path)):
                if imported in WEB_MODULES:
                    offenders.append(f"{module} → {imported}")
        self.assertEqual(
            offenders, [],
            "非 web 模块不得依赖 web 层：把共享的纯规则下沉到 catalog_rules 一类的策略模块",
        )

    def test_catalog_rules_depends_on_nothing_inside_peach(self):
        """最底下那层必须是纯的：只要它开始 import 别的 Peach 模块，就不再是策略了。"""
        self.assertEqual(
            _local_imports(SOURCE_ROOT / "catalog_rules.py"), set(),
            "catalog_rules 是最底层纯规则，不能依赖任何 Peach 模块",
        )

    def test_the_old_web_logic_name_is_gone(self):
        self.assertFalse(
            (SOURCE_ROOT / "web_logic.py").exists(),
            "web_logic.py 已改名为 catalog_rules.py；两个同时存在意味着改名没做干净",
        )
        # 只看 import，不看全文：`catalog_rules` 的 docstring 要讲清楚它改过名，
        # 那句话里出现旧名字是应该的。
        for path in sorted(SOURCE_ROOT.glob("*.py")):
            self.assertNotIn(
                "web_logic", _local_imports(path),
                f"{path.name} 仍在 import 旧模块名 web_logic",
            )


if __name__ == "__main__":
    unittest.main()
