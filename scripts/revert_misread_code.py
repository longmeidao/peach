r"""存量修正：撤掉一个被当成番号的目录名，以及拿它刮回来的一切。

建库前的导入把 115 盘上的目录名整批写进了 `asset.code`。论坛合集包 `WX17` 下是 18 位网红的
266 个视频，`WX17` 被规范成 `WX-017` 问了 javbus，取回的是另一部片 `WXSD-017`；09-02 那次
整批复核把它的片名和标签落到了这 266 条上。新判据已在刮削入口拦住
（`scrape_codes._is_explicit_code`），这里把已经写进账本的改回去：

- `review_item` 以 `<规范键>:` 开头的 javinizer 归属，连同同源同名的 `asset_tag` 行删掉；
- 这个键下批准过的字段候选写进过的列（`METADATA_FIELD_COLUMNS`）清空，用户手改过的不动；
- `code` 以 `user:manual` 清空，扫描器此后不会再按文件名把它写回来；
- 这个键下批准过的复核决定改成 `rejected`，原批准记录留在 note 里。

只收两种写法之外的目录名：原始写法本身就是番号形态的、或这批资产里有厂牌／发行日／出演者
证据的，一律拒绝。默认只列计划；`--apply` 必须同时给 `--backup`。

    revert_misread_code.py --code WX17
    revert_misread_code.py --code WX17 --apply --backup <备份路径>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.catalog_rules import (  # noqa: E402
    RELEASE_EVIDENCE_KINDS, is_jav_code, normalise_code_key)
from peach.field_owners import is_protected, owner_of, write_owned_fields  # noqa: E402
from peach.metadata_auto_apply import METADATA_FIELD_COLUMNS  # noqa: E402
from peach.scripting import (  # noqa: E402
    add_ledger_write_args, counts_of, open_for_write, verify_after_write)

OWNER = "user:manual"
EXTRA_COUNTS = {
    "asset_tag": "SELECT count(*) FROM asset_tag",
    "有 code": "SELECT count(*) FROM asset WHERE trim(COALESCE(code,''))<>''",
    "approved 决定": "SELECT count(*) FROM review_decision WHERE status='approved'",
}


class NotADirectoryLabel(ValueError):
    """这个 code 可能是真番号，脚本不替人判。"""


def plan(connection, code: str) -> dict:
    """要改的资产、归属行、字段与复核决定；不写库。"""
    if is_jav_code(code):
        raise NotADirectoryLabel(f"{code} 的原始写法本身就是番号形态，不按目录名处理")
    key = normalise_code_key(code)
    assets = [dict(row) for row in connection.execute(
        "SELECT id,field_owners," + ",".join(sorted(set(METADATA_FIELD_COLUMNS.values()))) +
        " FROM asset WHERE code=? ORDER BY id", (code,))]
    if not assets:
        raise NotADirectoryLabel(f"账本里没有 code={code} 的资产")
    ids = [row["id"] for row in assets]
    marks = ",".join("?" * len(ids))
    kinds = ",".join("?" * len(RELEASE_EVIDENCE_KINDS))
    evidence = connection.execute(
        f"SELECT count(*) FROM asset a WHERE a.id IN ({marks}) AND ("
        "trim(COALESCE(a.studio,''))<>'' OR trim(COALESCE(a.release_date,''))<>'' OR EXISTS("
        "SELECT 1 FROM asset_entity ae JOIN entity e ON e.id=ae.entity_id "
        f"WHERE ae.asset_id=a.id AND e.kind IN ({kinds}) AND ae.source NOT LIKE 'javinizer:%'))",
        (*ids, *sorted(RELEASE_EVIDENCE_KINDS))).fetchone()[0]
    if evidence:
        raise NotADirectoryLabel(f"{code} 下有 {evidence} 条资产带本机发行证据，不按目录名处理")
    links = [dict(row) for row in connection.execute(
        f"SELECT ae.asset_id,ae.entity_id,ae.role,ae.source,e.canonical_name FROM asset_entity ae "
        f"JOIN entity e ON e.id=ae.entity_id WHERE ae.asset_id IN ({marks}) "
        "AND ae.source LIKE 'javinizer:%' "
        "AND json_extract(ae.metadata_json,'$.review_item') LIKE ?", (*ids, f"{key}:%"))]
    decisions = [dict(row) for row in connection.execute(
        "SELECT category,item_key,status,note FROM review_decision "
        "WHERE category='metadata_fields' AND item_key LIKE ? AND status='approved'",
        (f"{key}:%",))]
    columns = sorted({METADATA_FIELD_COLUMNS[field] for row in decisions
                      if (field := row["item_key"].split(":", 1)[1]) in METADATA_FIELD_COLUMNS})
    fields = {column: [row["id"] for row in assets
                       if str(row[column] or "").strip()
                       and not is_protected(owner_of(row["field_owners"], column))]
              for column in columns}
    return {"code": code, "key": key, "assets": ids, "links": links,
            "decisions": decisions, "fields": fields}


def apply(connection, work: dict, stamp: str) -> dict[str, int]:
    done = {"归属行": 0, "标签行": 0, "清空字段": 0, "清空番号": 0, "驳回决定": 0}
    for link in work["links"]:
        connection.execute(
            "DELETE FROM asset_entity WHERE asset_id=? AND entity_id=? AND role=? AND source=?",
            (link["asset_id"], link["entity_id"], link["role"], link["source"]))
        done["归属行"] += connection.execute("SELECT changes()").fetchone()[0]
        if link["role"] == "tag":
            connection.execute("DELETE FROM asset_tag WHERE asset_id=? AND tag=? AND source=?",
                               (link["asset_id"], link["canonical_name"], link["source"]))
            done["标签行"] += connection.execute("SELECT changes()").fetchone()[0]
    for column, ids in work["fields"].items():
        if ids:
            done["清空字段"] += write_owned_fields(connection, ids, {column: None}, OWNER).assets
    done["清空番号"] = write_owned_fields(connection, work["assets"], {"code": None}, OWNER).assets
    for decision in work["decisions"]:
        note = json.dumps({"reverted_approval": decision["note"],
                           "reason": f"{work['code']} 是目录名，不是番号 {work['key']}"},
                          ensure_ascii=False)
        connection.execute(
            "UPDATE review_decision SET status='rejected',note=?,updated_at=? "
            "WHERE category=? AND item_key=? AND status='approved'",
            (note, stamp, decision["category"], decision["item_key"]))
        done["驳回决定"] += connection.execute("SELECT changes()").fetchone()[0]
    return done


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="撤掉被当成番号的目录名及其刮削结果；默认只读")
    add_ledger_write_args(parser)
    parser.add_argument("--code", required=True, help="账本里存着的原始写法，如 WX17")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    connection = open_for_write(args)
    try:
        try:
            work = plan(connection, args.code)
        except NotADirectoryLabel as error:
            print(f"拒绝：{error}", file=sys.stderr)
            return 2
        print(f"{work['code']}（被当成 {work['key']}）：资产 {len(work['assets'])} 条，"
              f"javinizer 归属 {len(work['links'])} 行，批准决定 "
              f"{[row['item_key'] for row in work['decisions']]}，"
              f"清空字段 { {column: len(ids) for column, ids in work['fields'].items()} }")
        if not args.apply:
            print("dry-run：未写 ledger；加 --apply --backup <路径> 才真的写。")
            return 0
        before = counts_of(connection, EXTRA_COUNTS)
        connection.execute("BEGIN IMMEDIATE")
        try:
            done = apply(connection, work, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        after = counts_of(connection, EXTRA_COUNTS)
        integrity, violations = verify_after_write(connection)
        print("写入：" + "，".join(f"{key} {value}" for key, value in done.items()))
        for key in before:
            print(f"  {key}: {before[key]} -> {after[key]}")
        print(f"integrity_check={integrity} foreign_key_check={violations}")
        return 0 if integrity == "ok" and violations == 0 else 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
