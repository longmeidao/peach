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
#:
#: 按文件名推导而不是手写清单：这里原本写死四个，而拆分出 `web_review`、
#: `web_resource_sync`、`web_settings` 之后没人回来更新，那三个模块此后一直不设防。
#: 守规则的东西自己先漂了，是这条门槛最容易出的故障。
WEB_MODULES = {path.stem for path in SOURCE_ROOT.glob("web_*.py")}

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

    def test_batch_scripts_share_one_cli_tail(self):
        """批处理脚本的 main() 收尾只许有一份。

        它此前抄了四份。共用的不只是形状，还有「pid 锁必须包住整个 run」和「策略
        异常交出自己的退出码而不是抛栈」这两条约定；散成四份，下一个脚本照抄时漏掉
        锁或吞掉退出码都不会有人发现。
        """
        offenders = [path.name for path in sorted((PROJECT_ROOT / "scripts").glob("*.py"))
                     if "with PidFileLock(args.lock):" in path.read_text(encoding="utf-8")]
        self.assertEqual(offenders, [],
                         "又有脚本自己写了 main() 收尾，请改调 peach.jobs.job_main")

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
    def test_the_web_layer_is_actually_discovered(self):
        """推导出来的 web 层不能是空的。

        改成按文件名推导之后，清单不会再漂；但万一命名约定变了，glob 会安静地返回
        空集，上面那条断言就永远成立——门槛还在，只是不再拦任何东西。
        """
        self.assertGreaterEqual(len(WEB_MODULES), 4, "没发现 web 层，门槛已空转")
        self.assertIn("web_contract", WEB_MODULES)

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
