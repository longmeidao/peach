"""把自动落库写下的一批实体结果整批撤回（ADR-0052）。

自动落库的每条写入都带归属串和批次号：官网链接记在 `entity_link.metadata_json` 的
`source` 与 `batch`，标识文件记在边车 `.provenance.json` 的同名两项。判据错了一批，就按
它们认出来一起撤掉，不必一条条找。

撤回是删除，不是恢复旧值：补厂牌后继只在盘上一张图都没有、账本里一条官网都没有时才写，
写下的就是那一格的全部，删掉就回到它写之前的样子。

默认只列计划；`--apply` 必须同时给 `--backup`，删文件在账本行之后、同一次运行里完成。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.config import GENERATED_DIR  # noqa: E402
from peach.scripting import add_ledger_write_args, open_for_write, verify_after_write  # noqa: E402

SIDECARS = (".ct", ".provenance.json")


def matches(record: dict, source: str, batch: str) -> bool:
    return record.get("source") == source and (not batch or record.get("batch") == batch)


def planned_links(connection, source: str, batch: str) -> list[dict]:
    rows = connection.execute(
        "SELECT l.id,l.entity_id,e.canonical_name,l.url,l.metadata_json FROM entity_link l"
        " JOIN entity e ON e.id=l.entity_id WHERE l.metadata_json LIKE ?",
        (f"%{source}%",)).fetchall()
    found = []
    for row in rows:
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except ValueError:
            continue
        if matches(metadata, source, batch):
            found.append({"id": row["id"], "entity": row["canonical_name"], "url": row["url"],
                          "batch": metadata.get("batch", "")})
    return found


def planned_files(logo_root: Path, source: str, batch: str) -> list[Path]:
    """边车上写着这个来源的标识文件本体。"""
    found = []
    for sidecar in sorted(logo_root.glob("*.provenance.json")):
        try:
            record = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if matches(record, source, batch):
            found.append(sidecar.with_name(sidecar.name.removesuffix(".provenance.json")))
    return found


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_ledger_write_args(parser)
    parser.add_argument("--source", default="auto:studio-mark",
                        help="要撤回的归属串，与写入时记的逐字相同")
    parser.add_argument("--batch", default="", help="只撤这一批；不给就撤这个来源的全部")
    parser.add_argument("--logo-root", type=Path, default=GENERATED_DIR / "logos")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    connection = open_for_write(args)
    try:
        links = planned_links(connection, args.source, args.batch)
        files = planned_files(args.logo_root, args.source, args.batch)
        for link in links:
            print(f" - 链接 {link['entity'][:20]:<20} {link['url'][:56]} {link['batch']}")
        for path in files:
            print(f" - 标识 {path.name}")
        print({"链接": len(links), "标识文件": len(files)})
        if not args.apply:
            print("dry-run；确认无误后加 --apply --backup <路径>")
            return 0
        with connection:
            connection.executemany("DELETE FROM entity_link WHERE id=?",
                                   [(link["id"],) for link in links])
        integrity, orphans = verify_after_write(connection)
    finally:
        connection.close()
    removed = 0
    for path in files:
        for target in (path, *(path.with_name(path.name + suffix) for suffix in SIDECARS)):
            if target.exists():
                target.unlink()
                removed += 1
    print({"删除链接": len(links), "删除文件": removed,
           "integrity_check": integrity, "foreign_key_check": orphans})
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
