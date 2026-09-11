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

from peach.windows_restart import (
    find_tray_windows, restart_source_tray, restart_tray,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="静默无窗口地重启 Windows Peach 托盘及子服务")
    parser.add_argument("--target", type=Path,
                        default=PROJECT_ROOT / "dist" / "Peach" / "Peach.exe")
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--source", action="store_true",
                        help="重启源码部署的托盘（pythonw -m peach.tray），不做换包")
    parser.add_argument("--swap-from", type=Path, default=None,
                        help="旧托盘退出后把这个暂存包换上生产入口，失败自动回退")
    args = parser.parse_args(argv)
    # 源码托盘没有生产入口可换，`--swap-from` 在这条路上无处可去。默默忽略它的话，
    # 命令照样退出 0、照样打印 ok，而那个包根本没换上——换包失败最不能是静默的。
    if args.source and args.swap_from:
        parser.error("--source 不能与 --swap-from 同用：源码托盘没有可换的生产入口")

    if not args.source and find_tray_windows(args.target):
        result = restart_tray(args.target, timeout=max(1.0, args.timeout),
                              swap_from=args.swap_from)
    else:
        result = restart_source_tray(timeout=max(1.0, args.timeout))
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
