"""把自动落库写下的一批实体结果整批撤回（ADR-0052）。

自动落库的每条写入都带归属串和批次号：官网链接记在 `entity_link.metadata_json` 的
`source` 与 `batch`，标识文件记在边车 `.provenance.json` 的同名两项，别名的
`entity_alias.source` 直接就是批次号 `<source>@<任务行 id>`（ADR-0055）。女优资料行的
`performer_profile.source` 同样是批次号，后继登记的站上编号在 `entity_external_ref.metadata_json`
里记 `source` 与 `batch`（ADR-0067），番号样张的 `code_sample_image.source` 也是批次号（ADR-0068），
种子包补的所属事务所 `entity_membership.source` 与 label 的片商 `label_maker.source` 同样（ADR-0073、ADR-0075）。
判据错了一批，就按它们认出来一起撤掉，不必一条条找。

撤回是删除，不是恢复旧值：补厂牌后继只在盘上一张图都没有、账本里一条官网都没有时才写，
补别名后继只写账本里还没有的写法，补女优资料后继只写自动来源的那一行，补样张后继只给还没有
样张的番号写，写下的就是那一格的全部，删掉就回到它写之前的样子。

    revert_auto_landing.py --source auto:performer-alias
    revert_auto_landing.py --source auto:performer-alias --batch auto:performer-alias@812
    revert_auto_landing.py --source auto:performer-profile
    revert_auto_landing.py --source auto:sample-images
    revert_auto_landing.py --source auto:seed --batch auto:seed@2026-09-25

默认只列计划；`--apply` 必须同时给 `--backup`，删文件在账本行之后、同一次运行里完成。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import sample_images  # noqa: E402
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


def planned_aliases(connection, source: str, batch: str) -> list[dict]:
    """这个来源写下的别名。`source` 列存的是批次号，所以不给批次时按「来源@」前缀认。"""
    clause, values = _batch_clause("a.source", source, batch)
    return [{"entity_id": row["entity_id"], "entity": row["canonical_name"], "alias": row["alias"],
             "normalized": row["normalized_alias"], "source": row["source"]}
            for row in connection.execute(
                "SELECT a.entity_id,e.canonical_name,a.alias,a.normalized_alias,a.source"
                " FROM entity_alias a JOIN entity e ON e.id=a.entity_id WHERE " + clause
                + " ORDER BY a.entity_id,a.alias", values)]


def _batch_clause(column: str, source: str, batch: str) -> tuple[str, tuple]:
    """`column` 存的是批次号：给了批次就逐字比，不给就按「来源@」前缀认。"""
    if batch:
        return f"{column}=?", (batch,)
    return f"({column}=? OR substr({column},1,?)=?)", (source, len(source) + 1, source + "@")


def planned_profiles(connection, source: str, batch: str) -> list[dict]:
    """这个来源写下的女优资料行。"""
    clause, values = _batch_clause("p.source", source, batch)
    return [{"entity_id": row["entity_id"], "entity": row["canonical_name"], "source": row["source"]}
            for row in connection.execute(
                "SELECT p.entity_id,e.canonical_name,p.source FROM performer_profile p"
                " JOIN entity e ON e.id=p.entity_id WHERE " + clause + " ORDER BY p.entity_id",
                values)]


def planned_memberships(connection, source: str, batch: str) -> list[dict]:
    """这个来源写下的所属事务所（`source` 列存批次号）。"""
    clause, values = _batch_clause("m.source", source, batch)
    return [{"member_id": row["member_id"], "entity": row["canonical_name"], "agency": row["agency"],
             "source": row["source"]}
            for row in connection.execute(
                "SELECT m.member_id,e.canonical_name,a.canonical_name AS agency,m.source"
                " FROM entity_membership m JOIN entity e ON e.id=m.member_id"
                " JOIN entity a ON a.id=m.agency_id WHERE " + clause + " ORDER BY m.member_id", values)]


def planned_makers(connection, source: str, batch: str) -> list[dict]:
    """这个来源写下的 label 归属片商（`source` 列存批次号）。"""
    clause, values = _batch_clause("l.source", source, batch)
    return [{"label_id": row["label_id"], "entity": row["canonical_name"], "maker": row["maker"],
             "source": row["source"]}
            for row in connection.execute(
                "SELECT l.label_id,e.canonical_name,m.canonical_name AS maker,l.source"
                " FROM label_maker l JOIN entity e ON e.id=l.label_id"
                " JOIN entity m ON m.id=l.maker_id WHERE " + clause + " ORDER BY l.label_id", values)]


def planned_refs(connection, source: str, batch: str) -> list[dict]:
    """这个来源登记的站上编号（`metadata_json` 里记着 `source` 与 `batch`）。"""
    found = []
    for row in connection.execute(
            "SELECT r.entity_id,e.canonical_name,r.provider,r.external_kind,r.external_id,"
            "r.metadata_json FROM entity_external_ref r JOIN entity e ON e.id=r.entity_id"
            " WHERE r.metadata_json LIKE ?", (f"%{source}%",)):
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except ValueError:
            continue
        if isinstance(metadata, dict) and matches(metadata, source, batch):
            found.append({"entity": row["canonical_name"], "provider": row["provider"],
                          "kind": row["external_kind"], "id": row["external_id"],
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
        aliases = planned_aliases(connection, args.source, args.batch)
        profiles = planned_profiles(connection, args.source, args.batch)
        refs = planned_refs(connection, args.source, args.batch)
        memberships = planned_memberships(connection, args.source, args.batch)
        makers = planned_makers(connection, args.source, args.batch)
        files = planned_files(args.logo_root, args.source, args.batch)
        samples = sample_images.planned_revert(connection, args.source, args.batch)
        for link in links:
            print(f" - 链接 {link['entity'][:20]:<20} {link['url'][:56]} {link['batch']}")
        for alias in aliases:
            print(f" - 别名 {alias['entity'][:20]:<20} {alias['alias'][:40]} {alias['source']}")
        for profile in profiles:
            print(f" - 资料 {profile['entity'][:20]:<20} {profile['source']}")
        for ref in refs:
            print(f" - 编号 {ref['entity'][:20]:<20} {ref['provider']} {ref['id']} {ref['batch']}")
        for membership in memberships:
            print(f" - 归属 {membership['entity'][:20]:<20} {membership['agency'][:30]} {membership['source']}")
        for maker in makers:
            print(f" - 片商 {maker['entity'][:20]:<20} {maker['maker'][:30]} {maker['source']}")
        for path in files:
            print(f" - 标识 {path.name}")
        for sample in samples:
            print(f" - 样张 {sample['code']:<20} {sample['count']} 张 {sample['source']}")
        print({"链接": len(links), "别名": len(aliases), "资料": len(profiles), "编号": len(refs),
               "归属": len(memberships), "片商": len(makers), "标识文件": len(files),
               "样张": sum(sample["count"] for sample in samples)})
        if not args.apply:
            print("dry-run；确认无误后加 --apply --backup <路径>")
            return 0
        with connection:
            connection.executemany("DELETE FROM entity_link WHERE id=?",
                                   [(link["id"],) for link in links])
            connection.executemany(
                "DELETE FROM entity_alias WHERE entity_id=? AND normalized_alias=? AND source=?",
                [(alias["entity_id"], alias["normalized"], alias["source"]) for alias in aliases])
            connection.executemany(
                "DELETE FROM performer_profile WHERE entity_id=? AND source=?",
                [(profile["entity_id"], profile["source"]) for profile in profiles])
            connection.executemany(
                "DELETE FROM entity_external_ref WHERE provider=? AND external_kind=?"
                " AND external_id=?", [(ref["provider"], ref["kind"], ref["id"]) for ref in refs])
            connection.executemany(
                "DELETE FROM entity_membership WHERE member_id=? AND source=?",
                [(membership["member_id"], membership["source"]) for membership in memberships])
            connection.executemany(
                "DELETE FROM label_maker WHERE label_id=? AND source=?",
                [(maker["label_id"], maker["source"]) for maker in makers])
            removed_samples = sample_images.revert(connection, args.source, args.batch)
        integrity, orphans = verify_after_write(connection)
    finally:
        connection.close()
    removed = 0
    for path in files:
        for target in (path, *(path.with_name(path.name + suffix) for suffix in SIDECARS)):
            if target.exists():
                target.unlink()
                removed += 1
    print({"删除链接": len(links), "删除别名": len(aliases), "删除资料": len(profiles),
           "删除编号": len(refs), "删除归属": len(memberships), "删除片商": len(makers),
           "删除样张": removed_samples,
           "删除文件": removed,
           "integrity_check": integrity, "foreign_key_check": orphans})
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
