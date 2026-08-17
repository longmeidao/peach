"""Export review-only Logo and performer image queues from existing evidence."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def write_rows(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--studio-review", type=Path, required=True)
    parser.add_argument("--performer-review", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    with args.studio_review.open(encoding="utf-8-sig", newline="") as handle:
        studios = list(csv.DictReader(handle))
    logo_rows = [
        {
            "studio": row["studio"], "assets": row["assets"], "status": "candidate",
            "suggested_query": row["suggested_query"], "source_url": "",
            "evidence": "官方 Logo 待查；不使用作品截图替代",
        }
        for row in studios if row["status"] == "missing"
    ]
    write_rows(
        args.output_dir / "studio-logo-candidate-20260817.csv",
        ("studio", "assets", "status", "suggested_query", "source_url", "evidence"),
        logo_rows,
    )

    with args.performer_review.open(encoding="utf-8-sig", newline="") as handle:
        performers = list(csv.DictReader(handle))
    avatar_rows = [
        {
            "entity_id": row["entity_id"], "current_name": row["current_name"],
            "japanese_name": row["japanese_name"], "assets": row["assets"],
            "verdict": row["verdict"], "avatar_url": row["avatar_url"],
            "evidence": row["note"],
        }
        for row in performers if row["verdict"] in {"no_avatar", "avatar_rejected"}
    ]
    write_rows(
        args.output_dir / "performer-avatar-candidate-20260817.csv",
        ("entity_id", "current_name", "japanese_name", "assets", "verdict", "avatar_url", "evidence"),
        avatar_rows,
    )
    print({"missing_logos": len(logo_rows), "performer_image_gaps": len(avatar_rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
