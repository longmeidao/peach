#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
批处理进度同步 —— 从账本和产物反推当前状态，写进 docs/STATUS.md 的受管区块。

为什么需要它：项目里没有任何 hook、git hook 或计划任务会更新文档，全靠接手的
人记得写。2026-08-14 已经因此出过两次事：一次视觉打标的结论只留在对话里没落库
（asset_tag 至今 source='vision' 为 0 行），一次删除清单在结论被推翻后没重新生成，
里面躺着一个 3.2 GB 的正片。

所以这里的数字一律现算，不接受任何人工传入的"我记得是多少"。

只改写 STATUS.md 中两个标记之间的内容，标记外的正文不碰 —— 那部分由协调方维护。

用法:
    python scripts/job_status.py            # 打印，不改文件
    python scripts/job_status.py --write    # 写回 docs/STATUS.md
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from peach.config import DATABASE_PATH, GENERATED_DIR

DOC = Path(__file__).resolve().parent.parent / "docs" / "STATUS.md"
STATE = Path(r"R:\peach-data\state\agent-handoff.json")
START = "<!-- job-status:start -->"
END = "<!-- job-status:end -->"

# 产物 -> 说明。清单类产物必须能一眼看出"有没有过期"，所以连带报出生成时间。
ARTIFACTS = {
    "code-scrape.csv": "番号刮削结果",
    "name-clean.csv": "文件名净化清单",
    "ad-candidates.csv": "广告候选（confidence 分级）",
    "disposal-candidates.csv": "待处置候选（含「保留」判定）",
    "creator-tags-review.csv": "创作者标签待审",
}


def _readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect("file:" + path.resolve().as_posix() + "?mode=ro", uri=True)


def collect(db_path: Path, generated: Path, state_path: Path | None = None) -> list[str]:
    conn = _readonly(db_path)
    one = lambda sql, *a: conn.execute(sql, a).fetchone()[0]

    lines: list[str] = [START, "", "<!-- 由 scripts/job_status.py 生成，勿手改；数字现算于账本与产物 -->",
                        f"<!-- generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')} -->", ""]

    if state_path and state_path.is_file():
        try:
            event = json.loads(state_path.read_text(encoding="utf-8"))
            lines.append(
                f"- 最近自动交接：`{event.get('agent', 'unknown')}` / "
                f"`{event.get('event', 'unknown')}` / `{event.get('outcome', 'unknown')}`，"
                f"{event.get('at', 'unknown')}。"
            )
        except (OSError, ValueError, TypeError):
            lines.append("- 最近自动交接：状态文件不可读；本次账本数字仍已重新计算。")

    videos = one("SELECT count(*) FROM asset WHERE medium='video'")
    lines.append(f"- 资产 {one('SELECT count(*) FROM asset')} 条，其中视频 {videos} 条。")

    # 待抽帧必须报两个数。只报一个必然引起口径之争：曾经"4740"和"10196"被当成
    # 互相矛盾的数字争过一轮，其实一个是可执行量、一个是原始量，都对。
    # 没有时长就算不出 seek 点，抽帧脚本处理不了，那些要先补 probe。
    lines.append("- 待抽帧（可抽 / 缺时长待 probe / 合计）：")
    for loc in ("local", "115", "pikpak"):
        ready = one("SELECT count(*) FROM asset WHERE medium='video' AND location=? "
                    "AND (snapshot_path IS NULL OR snapshot_path='') AND duration>0", loc)
        blocked = one("SELECT count(*) FROM asset WHERE medium='video' AND location=? "
                      "AND (snapshot_path IS NULL OR snapshot_path='') "
                      "AND (duration IS NULL OR duration<=0)", loc)
        lines.append(f"  - `{loc}`：{ready} / {blocked} / {ready + blocked}")
    # 2026-08-15 实测重新标定：瓶颈是流量不是时间，旧的"25~40 秒/帧、全量 14 天"不成立。
    lines.append("  PikPak 的策略组已可切 DIRECT：2026-08-15 实测走代理时 9 帧 163 MB / 13.7 秒，"
                 "走直连时 30.5 MB / 64.2 秒——慢约 4.7 倍但流量少约 5 倍且不占代理预算。"
                 "全量抽帧仍是 773 GB 量级（代理口径），按创作者采样 88 板直连约 2.7 GB。"
                 "115 一直走直连，同样动作约 285 MB 一张接触表。")

    untagged = one("SELECT count(*) FROM asset WHERE medium='video' "
                   "AND id NOT IN (SELECT asset_id FROM asset_tag)")
    lines.append(f"- 无内容标签视频 {untagged} 条（占视频 {untagged/max(videos,1)*100:.0f}%）。")

    sources = conn.execute(
        "SELECT source,count(*) FROM asset_tag GROUP BY source ORDER BY 2 DESC").fetchall()
    lines.append("- `asset_tag` 来源分布：" +
                 "、".join(f"`{s}` {n}" for s, n in sources) + "。")

    codes = one("SELECT count(DISTINCT code) FROM asset WHERE code>''")
    with_studio = one("SELECT count(DISTINCT code) FROM asset WHERE code>'' AND studio>''")
    lines.append(f"- 番号 {codes} 个，其中 {with_studio} 个有厂牌"
                 f"（{with_studio/max(codes,1)*100:.0f}%）。")
    conn.close()

    lines.append("")
    lines.append("| 产物 | 行数 | 生成时间 | 说明 |")
    lines.append("| --- | ---: | --- | --- |")
    for name, desc in ARTIFACTS.items():
        path = generated / name
        if not path.is_file():
            lines.append(f"| `{name}` | — | 未生成 | {desc} |")
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = sum(1 for _ in csv.DictReader(handle))
        stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
        lines.append(f"| `{name}` | {rows} | {stamp} | {desc} |")

    lines += ["", END]
    return lines


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temp, path)


def write_back(doc: Path, block: list[str]) -> str:
    text = doc.read_text(encoding="utf-8")
    body = "\n".join(block)
    if START in text and END in text:
        head, _, rest = text.partition(START)
        _, _, tail = rest.partition(END)
        _atomic_write(doc, head + body + tail)
        return "替换了已有区块"
    _atomic_write(doc, text.rstrip() + "\n\n## 批处理进度（自动生成）\n\n" + body + "\n")
    return "新建了区块"


def record_hook_event(state_path: Path, payload: dict[str, object]) -> None:
    event = str(payload.get("hook_event_name") or payload.get("event") or "unknown")
    outcome = "failed" if event == "StopFailure" else (
        str(payload.get("reason") or "ended")[:80] if event == "SessionEnd" else "completed"
    )
    safe = {
        "agent": "claude",
        "event": event[:80],
        "outcome": outcome,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _atomic_write(state_path, json.dumps(safe, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="把批处理进度同步进 STATUS.md")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--generated", type=Path, default=GENERATED_DIR)
    parser.add_argument("--doc", type=Path, default=DOC)
    parser.add_argument("--state", type=Path, default=STATE)
    parser.add_argument("--hook-event", action="store_true", help="从 stdin 接收 Claude hook JSON")
    args = parser.parse_args()

    if args.hook_event:
        try:
            payload = json.load(sys.stdin)
            if not isinstance(payload, dict):
                raise ValueError("hook payload must be an object")
            record_hook_event(args.state, payload)
        except Exception as exc:
            print(f"自动交接事件记录失败：{exc}", file=sys.stderr)

    block = collect(args.db, args.generated, args.state)
    print("\n".join(block))
    if args.write:
        print("\n" + write_back(args.doc, block) + f" → {args.doc}")
    else:
        print("\n未加 --write，只打印未改文档。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
