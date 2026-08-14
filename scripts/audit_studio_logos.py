"""Export the canonical studio-logo completion queue without network writes."""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path

from peach.config import DATABASE_PATH, GENERATED_DIR


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)[:60]


def rows(database: Path, logo_root: Path) -> list[dict[str, object]]:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    result: list[dict[str, object]] = []
    for row in connection.execute(
        """
        SELECT e.canonical_name AS studio,COUNT(DISTINCT ae.asset_id) AS assets
        FROM entity e LEFT JOIN asset_entity ae ON ae.entity_id=e.id
        WHERE e.kind='studio'
        GROUP BY e.id,e.canonical_name
        ORDER BY assets DESC,e.canonical_name
        """
    ):
        cached = logo_root / f"{safe_name(row['studio'])}.img"
        has_logo = cached.is_file()
        sidecar = Path(str(cached) + ".provenance.json")
        result.append({
            "status": "cached" if has_logo else "missing",
            "studio": row["studio"],
            "assets": row["assets"],
            "cache_path": str(cached),
            "has_provenance": sidecar.is_file(),
            "suggested_query": f"{row['studio']} official logo",
            "source_url": "",
            "review": "" if has_logo else "pending",
            "notes": "",
        })
    connection.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--logo-root", type=Path, default=GENERATED_DIR / "logos")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    findings = rows(args.db, args.logo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ("status", "studio", "assets", "cache_path", "has_provenance",
              "suggested_query", "source_url", "review", "notes")
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(findings)
    cached = sum(row["status"] == "cached" for row in findings)
    print(f"studios={len(findings)} cached={cached} missing={len(findings)-cached} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
