"""过渡加载器。

FastAPI 第一阶段复用已经验证的 q_*/w_* 数据函数；业务函数完成抽包后删除本模块。
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def load_legacy(path: Path, db_path: Path, token: str = "") -> ModuleType:
    spec = spec_from_file_location("peach_legacy_web", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载旧 Web 模块：{path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DB = str(db_path)
    module.TOKEN = token
    return module
