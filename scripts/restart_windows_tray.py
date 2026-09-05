"""重启 Windows 托盘的命令行入口，实现在 `peach.windows_restart`。

    .venv\\Scripts\\python.exe scripts\\restart_windows_tray.py

换生产二进制走 `scripts/deploy_windows_tray.py`，不要单独用这里的 `--swap-from`。
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.windows_restart import restart_tray


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="静默、正常地重启 Windows Peach 托盘及其子服务")
    parser.add_argument("--target", type=Path,
                        default=PROJECT_ROOT / "dist" / "Peach" / "Peach.exe")
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--swap-from", type=Path, default=None,
                        help="旧托盘退出后把这个暂存包换上生产入口，失败自动回滚")
    args = parser.parse_args(argv)
    result = restart_tray(args.target, timeout=max(1.0, args.timeout),
                          swap_from=args.swap_from)
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
