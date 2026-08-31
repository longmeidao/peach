"""逐项审计旧 ``asset.creator`` 到规范创作者关系的投影。

当前扫描器不再从目录推断创作者；本脚本只读地列出历史
``source='legacy:asset'`` 关系。目录命中只是一条证据，不等于身份真相。
"""
from __future__ import annotations

import argparse
import sqlite3
from collections import Counter
from pathlib import Path

from peach.review_csv import write_rows
from peach.config import DATABASE_PATH


ITEM_FIELDS = (
    "asset_id", "medium", "location", "path", "current_creator", "relation_source",
    "confidence", "path_contains_creator", "parent_component", "child_component",
    "verdict", "proposed_creator", "reason",
)
SUMMARY_FIELDS = ("verdict", "current_creator", "assets", "reason")
STRUCTURAL = {"门槛", "视频", "宣傳文件", "宣传文件", "asce"}


def _parts(path: str) -> list[str]:
    return [part for part in path.replace("/", "\\").split("\\") if part]


def classify(path: str, creator: str) -> tuple[str, str, str, str, str, str]:
    parts = _parts(path)
    folded = creator.casefold().strip()
    matches = [index for index, part in enumerate(parts) if part.casefold().strip() == folded]
    parent = parts[matches[0] - 1] if matches and matches[0] else ""
    child = parts[matches[0] + 1] if matches and matches[0] + 1 < len(parts) else ""
    normalized = "\\".join(parts).casefold()

    if folded == "足交仙人".casefold() and matches:
        return "yes", parent, child, "replace", "suzuq", "用户确认水印为 suzuq；Suzyq 文件名交叉佐证"
    if folded == "捅主任".casefold() and normalized.startswith(
        "b:\\mvp\\捅主任\\tokyodolls\\".casefold()
    ):
        return "yes", parent, child, "remove", "", "TokyoDolls 子树与捅主任身份冲突；仅移除错误创作者关系"
    if creator in STRUCTURAL:
        return "yes" if matches else "no", parent, child, "review_structural", "", "结构或集合目录名，不应直接作为创作者"
    if matches:
        return "yes", parent, child, "review_folder_projection", "", "创作者名只由路径组件交叉命中，仍需水印、番号或发行元数据"
    return "no", "", "", "review_legacy_projection", "", "旧扁平字段没有路径组件交叉佐证"


def rows(database: Path) -> list[dict[str, object]]:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    result: list[dict[str, object]] = []
    query = """
      SELECT a.id AS asset_id,a.medium,a.location,a.path,e.canonical_name AS creator,
             ae.source,ae.confidence
      FROM asset_entity ae
      JOIN entity e ON e.id=ae.entity_id AND e.kind='creator'
      JOIN asset a ON a.id=ae.asset_id
      WHERE ae.role='creator' AND ae.source='legacy:asset'
      ORDER BY a.id,e.canonical_name
    """
    for row in connection.execute(query):
        contains, parent, child, verdict, proposed, reason = classify(row["path"], row["creator"])
        result.append({
            "asset_id": row["asset_id"], "medium": row["medium"],
            "location": row["location"], "path": row["path"],
            "current_creator": row["creator"], "relation_source": row["source"],
            "confidence": row["confidence"], "path_contains_creator": contains,
            "parent_component": parent, "child_component": child,
            "verdict": verdict, "proposed_creator": proposed, "reason": reason,
        })
    connection.close()
    return result


def summaries(items: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter((str(row["verdict"]), str(row["current_creator"]), str(row["reason"])) for row in items)
    return [
        {"verdict": verdict, "current_creator": creator, "assets": count, "reason": reason}
        for (verdict, creator, reason), count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _write(path: Path, fields: tuple[str, ...], data: list[dict[str, object]]) -> None:
    write_rows(path, fields, data)


def main() -> int:
    parser = argparse.ArgumentParser(description="逐项审计历史创作者投影，不写数据库")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--output", type=Path, required=True, help="逐项 CSV 输出路径")
    parser.add_argument("--summary", type=Path, help="按创作者和 verdict 汇总 CSV")
    args = parser.parse_args()
    items = rows(args.db)
    _write(args.output, ITEM_FIELDS, items)
    if args.summary:
        _write(args.summary, SUMMARY_FIELDS, summaries(items))
    print(f"逐项 {len(items)} 条；汇总 {len(summaries(items))} 组；数据库未修改")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
