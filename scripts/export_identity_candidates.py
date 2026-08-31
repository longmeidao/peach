"""Export review-only Logo and performer image queues from existing evidence."""
from __future__ import annotations

import argparse
from pathlib import Path

from peach.review_csv import read_rows, write_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--studio-review", type=Path, required=True)
    parser.add_argument("--performer-review", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    studios = read_rows(args.studio_review)
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

    performers = read_rows(args.performer_review)
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
