"""Audit legacy creator projections that look like folders/categories.

Read-only by default. The three ``remove`` verdicts were manually verified from
their paths; broader heuristics remain ``review`` and are never auto-applied.
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

from peach.config import DATABASE_PATH


REMOVE = {"门槛", "视频", "宣傳文件", "宣传文件"}
REVIEW = re.compile(
    r"(^|[ _-])(视频|文件|资源|合集|下载|会员|付费|试看|预览|宣传|宣傳|无水印|无码厂标)([ _-]|$)",
    re.IGNORECASE,
)


def rows(database: Path) -> list[dict[str, object]]:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    result = []
    for row in connection.execute(
        """
        SELECT e.canonical_name AS name,COUNT(DISTINCT ae.asset_id) AS assets,
               MIN(a.location) AS location,MIN(a.path) AS sample_path
        FROM entity e JOIN asset_entity ae ON ae.entity_id=e.id
        JOIN asset a ON a.id=ae.asset_id
        WHERE e.kind='creator'
        GROUP BY e.id,e.canonical_name
        ORDER BY assets DESC,e.canonical_name
        """
    ):
        name = row["name"]
        verdict = "remove" if name in REMOVE else ("review" if REVIEW.search(name) else "")
        if not verdict:
            continue
        result.append({
            "verdict": verdict,
            "name": name,
            "assets": row["assets"],
            "location": row["location"],
            "sample_path": row["sample_path"],
            "reason": "reviewed structural folder" if verdict == "remove" else "structural-name heuristic",
        })
    connection.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    findings = rows(args.db)
    fields = ("verdict", "name", "assets", "location", "sample_path", "reason")
    if not args.output and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    stream = args.output.open("w", encoding="utf-8-sig", newline="") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(findings)
    finally:
        if args.output:
            stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
