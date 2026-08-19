#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 macOS 菜单栏项的 .app 外壳。

裸控制台进程拿不稳菜单栏项：`peach-tray` 直接后台启动时会拉起服务、然后自己安静
退出——AppKit 的运行循环在没有应用上下文时立刻返回，退出码 0、没有任何输出。
实测就是这样：服务进程还在，托盘父进程没了。

macOS 的标准做法是打成 bundle 并在 `Info.plist` 里声明 `LSUIElement`：只在菜单栏
出现，不占 Dock、不进 ⌘Tab。外壳本身只有一个 plist 和一个 exec 到项目 venv 的脚本
——和 Windows 那边一样，托盘不是可移动的独立发行版，服务进程仍由 venv 承担。
"""
from __future__ import annotations

import argparse
import plistlib
import shutil
import stat
from pathlib import Path

from peach import __version__
from peach.config import LOG_DIR, PROJECT_ROOT


BUNDLE_ID = "gg.lmd.peach.tray"
# `open -a` 启动的进程没有终端，stdout/stderr 直接进虚空。菜单栏项本来就没有窗口，
# 不落盘的话它为什么没起来完全看不出来——上一版就是这样：进程活着、服务没起、零输出。
LAUNCHER = """#!/bin/sh
# 由 scripts/build_macos_app.py 生成，勿手改。
LOG="{log_dir}/macos-tray.log"
mkdir -p "{log_dir}"
exec "{tray}" "$@" >>"$LOG" 2>&1
"""


def build(destination: Path, tray: Path) -> Path:
    app = destination / "Peach.app"
    macos, resources = app / "Contents" / "MacOS", app / "Contents" / "Resources"
    if app.exists():
        shutil.rmtree(app)
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    info = {
        "CFBundleName": "Peach",
        "CFBundleDisplayName": "Peach 蜜桃",
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleVersion": __version__,
        "CFBundleShortVersionString": __version__,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "Peach",
        # 只在菜单栏出现：不占 Dock、不进 ⌘Tab。菜单栏项的标准声明。
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    }
    (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info))

    launcher = macos / "Peach"
    launcher.write_text(
        LAUNCHER.format(tray=tray, log_dir=LOG_DIR), encoding="utf-8")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    logo = PROJECT_ROOT / "resources" / "peach-logo.png"
    if logo.is_file():
        shutil.copy2(logo, resources / "peach-logo.png")
    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 macOS 菜单栏项的 .app 外壳")
    parser.add_argument("--destination", type=Path, default=PROJECT_ROOT / "dist")
    parser.add_argument("--tray", type=Path, default=PROJECT_ROOT / ".venv" / "bin" / "peach-tray")
    return parser


def run(args: argparse.Namespace) -> int:
    if not args.tray.is_file():
        raise SystemExit(f"找不到 peach-tray：{args.tray}（先 pip install -e .）")
    args.destination.mkdir(parents=True, exist_ok=True)
    app = build(args.destination, args.tray)
    print(f"已生成 {app}")
    print(f"  启动：open -a '{app}'")
    print("  开机自启：系统设置 → 通用 → 登录项 → 加入这个 .app")
    return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
