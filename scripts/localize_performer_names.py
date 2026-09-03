#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""用经维护的中日姓名映射本地化番号体系女优名称，并把残留的日本字形归一为简体。

译名只处理带 `r18:performer` / `javbus:performer` 发行来源的实体；账号型 performer 不翻译。
匹配按精确证据分层：既有人工复核日文名、当前日文名、既有别名，再到复核表里的旧名。
一条名字命中多个映射时不猜。多个 ledger 实体落到同一映射条目时，按同一人的旧名合并。

字形归一是独立的最后一道，不看发行来源也不需要映射：`涼` 和 `凉` 是同一个字，
把 `高山涼音` 写成 `高山凉音` 不涉及任何译名判断。映射只覆盖已收录的艺人，剩下的名字
就一直卡在日本字形上，看着像中文名又不是中文名——这一道专治那个。

映射 XML 是外部复核来源，不随 Peach 分发，可以不给：不给就只跑字形归一。默认只产出
全库 CSV；`--apply` 写真实 ledger 时必须同时提供 `--backup`。旧规范名、日文名、假名与
繁体名都保留为别名。
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import DATA_ROOT, GENERATED_DIR
from peach.entities import merge_entity, normalize_entity_name
from peach.review_csv import read_rows, write_rows
from peach.scripting import add_ledger_write_args, counts_of, open_for_write, verify_after_write


RELEASE_SOURCES = frozenset({"r18:performer", "javbus:performer"})
ALIAS_SOURCE_PREFIX = "avdb-actor-mapping"
MERGE_ALIAS_SOURCE = "merge:performer-localization"
KANJI_ALIAS_SOURCE = "kanji-simplification"
KANJI_ONLY_REVISION = "kanji-only"

# 日本汉字（新字体与旧字体）在简体中文里有确定对应字形的，逐字换。这里换的是字形不是名字，
# 所以不需要外部证据：中文资料页写「凉森玲梦」和写「涼森玲夢」指的是同一个人。
# 收录范围是本库出现过的字形，加上人名里常见、对应关系同样没有歧义的那批。
JP_KANJI_TO_SIMPLIFIED = {
    "並": "并", "亜": "亚", "亞": "亚", "倉": "仓", "児": "儿", "凜": "凛",
    "実": "实", "實": "实", "宮": "宫", "島": "岛", "嶋": "岛", "嵐": "岚",
    "塩": "盐", "姫": "姬", "尋": "寻", "恵": "惠", "愛": "爱", "斎": "齐",
    "齋": "齐", "桜": "樱", "櫻": "樱", "橋": "桥", "歩": "步", "満": "满",
    "沢": "泽", "澤": "泽", "沖": "冲", "浜": "滨", "濱": "滨", "渋": "涩",
    "涼": "凉", "湊": "凑", "瀬": "濑", "瀨": "濑", "瀧": "泷", "稲": "稻",
    "穂": "穗", "紀": "纪", "紗": "纱", "結": "结", "絵": "绘", "絢": "绚",
    "綾": "绫", "緒": "绪", "織": "织", "聖": "圣", "華": "华", "葉": "叶",
    "蔵": "藏", "藍": "蓝", "蘭": "兰", "見": "见", "遠": "远", "鈴": "铃",
    "鳥": "鸟", "鳩": "鸠", "須": "须", "優": "优", "飯": "饭", "岡": "冈",
    "時": "时", "場": "场", "圓": "圆", "廣": "广", "國": "国", "學": "学",
    "風": "风", "樂": "乐", "楽": "乐", "榮": "荣", "豐": "丰", "龍": "龙",
    "鶴": "鹤", "蓮": "莲", "東": "东", "納": "纳", "樹": "树", "麗": "丽",
    "靜": "静", "貴": "贵", "藝": "艺", "歐": "欧", "慶": "庆",
}

# 上游译名偶尔夹带零宽字符（`\u200c斋藤亚美里`）。页面上和普通名字看不出差别，
# 搜索、去重和名字唯一约束却全按另一个字符串算，等于库里多出一个查不到的人。
_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u2060\ufeff]")

# `斎`／`齋` 的简体字形是 `齐`。`斋` 在中文里是另一个字（斋戒、书斋），上游把
# `安齋らら` 写成 `安斋拉拉` 是照抄字形没换。只在日文一侧确实是 `斎`／`齋` 时才改，
# 本来就写 `斋` 的名字不动——两个字不能混为一谈。
_SAI_KANJI = ("斎", "齋")


def strip_zero_width(name: str) -> str:
    return _ZERO_WIDTH.sub("", name or "")


def resolve_sai(name: str, japanese: Iterable[str]) -> str:
    if "斋" not in name:
        return name
    if any(char in str(value or "") for value in japanese for char in _SAI_KANJI):
        return name.replace("斋", "齐")
    return name


# 简体中文没有对应字形的日本汉字：咲 凪 雫 辻 笹 榊 槙 䌷。中文资料页一律照抄，
# 表里不收，逐字换的时候原样留下——`桜咲姫莉` 该变成 `樱咲姬莉`，不是变成半个空格。
_KANA = re.compile(r"[぀-ヿ]")

# 该映射条目的 zh_cn 仍误填日文，但 keyword 同时给出简/繁中文；中文资料页也交叉确认。
# 只在外部条目确实携带这个候选时启用，避免脱离来源硬编码一个无法追溯的译名。
REVIEWED_CN_OVERRIDES = {"釈アリス": "释爱丽丝"}


@dataclass(frozen=True)
class ActorMapping:
    index: int
    jp: str
    zh_cn: str
    zh_tw: str
    keywords: tuple[str, ...]
    tmdb_id: str
    verified: str

    @property
    def key(self) -> str:
        return f"tmdb:{self.tmdb_id}" if self.tmdb_id else f"xml:{self.index}:{self.jp}"


def read_mapping(path: Path) -> list[ActorMapping]:
    root = ET.parse(path).getroot()
    rows = []
    for index, node in enumerate(root.iter("a")):
        keywords = tuple(
            dict.fromkeys(part.strip() for part in node.attrib.get("keyword", "").split(",")
                          if part.strip())
        )
        rows.append(ActorMapping(
            index=index,
            jp=node.attrib.get("jp", "").strip(),
            zh_cn=node.attrib.get("zh_cn", "").strip(),
            zh_tw=node.attrib.get("zh_tw", "").strip(),
            keywords=keywords,
            tmdb_id=node.attrib.get("tmdb_id", "").strip(),
            verified=node.attrib.get("verified", "").strip(),
        ))
    return rows


def read_identity_review(path: Path | None) -> dict[int, dict[str, str]]:
    if path is None or not path.is_file():
        return {}
    return {int(row["entity_id"]): row for row in read_rows(path)}


def _unique(values: list[int]) -> int | None:
    found = set(values)
    return next(iter(found)) if len(found) == 1 else None


def _contains_latin(value: str) -> bool:
    return bool(re.search(r"[A-Za-z]", value or ""))


def _is_non_latin_east_asian(value: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", value or "")) \
        and not _contains_latin(value)


def simplify_kanji(name: str) -> str:
    """把纯汉字姓名里的日本字形换成简体字形；含假名或拉丁字母的名字原样返回。

    假名和罗马字要的是译名，不是字形：`飯岡かなこ` 逐字换只得到 `饭冈かなこ`，
    一个半中半日的名字，比原样留着更糟。那种名字只能等映射 XML 收录。
    """
    if not name or _KANA.search(name) or _contains_latin(name):
        return name
    out: list[str] = []
    for char in name:
        # 「々」是日语的叠字符号，中文没有这个写法，照抄下来 `野々宮蘭` 就还是半个日文名。
        # 它的意思是「重复上一个字」，展开成 `野野宫兰` 没有任何判断空间。
        if char == "々" and out:
            out.append(out[-1])
            continue
        out.append(JP_KANJI_TO_SIMPLIFIED.get(char, char))
    return "".join(out)


def _target_name(mapping: ActorMapping) -> tuple[str, str]:
    override = REVIEWED_CN_OVERRIDES.get(mapping.jp)
    if override and override in mapping.keywords:
        return override, "reviewed-keyword-cn"
    return mapping.zh_cn or mapping.jp, "zh_cn" if mapping.zh_cn else "jp-fallback"


def collect(
    connection: sqlite3.Connection,
    mappings: list[ActorMapping],
    identity_review: dict[int, dict[str, str]],
    revision: str,
) -> list[dict[str, object]]:
    """审计全部 performer，返回可重放计划；未命中与非发行来源也进入 CSV。"""
    connection.row_factory = sqlite3.Row
    by_jp: dict[str, list[int]] = defaultdict(list)
    by_keyword: dict[str, list[int]] = defaultdict(list)
    by_cn: dict[str, list[int]] = defaultdict(list)
    for mapping in mappings:
        if mapping.jp:
            by_jp[normalize_entity_name(mapping.jp)].append(mapping.index)
        for keyword in mapping.keywords:
            by_keyword[normalize_entity_name(keyword)].append(mapping.index)
        for value in (mapping.zh_cn, mapping.zh_tw):
            if value:
                by_cn[normalize_entity_name(value)].append(mapping.index)

    aliases: dict[int, list[str]] = defaultdict(list)
    for entity_id, alias in connection.execute(
        "SELECT entity_id,alias FROM entity_alias ORDER BY entity_id,alias"
    ):
        aliases[int(entity_id)].append(str(alias))

    entities = connection.execute(
        """
        SELECT e.id,e.canonical_name,e.normalized_name,
               (SELECT count(DISTINCT ae.asset_id) FROM asset_entity ae
                 WHERE ae.entity_id=e.id) assets,
               (SELECT group_concat(DISTINCT ae.source) FROM asset_entity ae
                 WHERE ae.entity_id=e.id) sources,
               (SELECT x.external_id FROM entity_external_ref x
                 WHERE x.entity_id=e.id AND x.provider='r18'
                   AND x.external_kind IN ('performer','performer_name')
                 ORDER BY CASE x.external_kind WHEN 'performer_name' THEN 0 ELSE 1 END
                 LIMIT 1) release_name
        FROM entity e WHERE e.kind='performer' ORDER BY e.id
        """
    ).fetchall()
    by_id = {int(entity["id"]): entity for entity in entities}

    rows: list[dict[str, object]] = []
    resolved_groups: dict[int, list[dict[str, object]]] = defaultdict(list)
    for entity in entities:
        entity_id = int(entity["id"])
        sources = str(entity["sources"] or "")
        source_set = set(filter(None, sources.split(",")))
        base: dict[str, object] = {
            "entity_id": entity_id,
            "current_name": str(entity["canonical_name"]),
            "target_name": str(entity["canonical_name"]),
            "assets": int(entity["assets"]),
            "sources": sources,
            "mapping_key": "",
            "mapping_jp": "",
            "mapping_zh_cn": "",
            "resolution": "",
            "action": "",
            "merge_target_id": "",
            "revision": revision,
            "_aliases": set(aliases.get(entity_id, [])),
            "_mapping_index": None,
        }
        if not RELEASE_SOURCES.intersection(source_set):
            base.update(resolution="non-release performer", action="keep-non-release")
            rows.append(base)
            continue

        review = identity_review.get(entity_id, {})
        ordered: list[tuple[str, str]] = []
        if review.get("japanese_name"):
            ordered.append(("review-jp", review["japanese_name"]))
        ordered.append(("canonical-jp", str(entity["canonical_name"])))
        ordered.extend(("alias-jp", alias) for alias in aliases.get(entity_id, []))

        mapping_index = None
        resolution = ""
        for label, name in ordered:
            candidate = _unique(by_jp.get(normalize_entity_name(name), []))
            if candidate is not None:
                mapping_index, resolution = candidate, label
                break
        if mapping_index is None and review.get("japanese_name"):
            candidate = _unique(by_keyword.get(
                normalize_entity_name(review["japanese_name"]), []))
            if candidate is not None:
                mapping_index, resolution = candidate, "review-jp-keyword"
        if mapping_index is None and review.get("current_name"):
            candidate = _unique(by_keyword.get(
                normalize_entity_name(review["current_name"]), []))
            if candidate is not None:
                mapping_index, resolution = candidate, "review-romaji-keyword"
        if mapping_index is None:
            candidate = _unique(by_cn.get(
                normalize_entity_name(str(entity["canonical_name"])), []))
            if candidate is not None:
                mapping_index, resolution = candidate, "canonical-cn"

        review_aliases = {
            value.strip()
            for value in (
                review.get("current_name", ""), review.get("japanese_name", ""),
                review.get("kana", ""), *(review.get("former_names", "").split("|")),
            ) if value.strip()
        }
        base["_aliases"].update(review_aliases)
        if mapping_index is None:
            fallback = review.get("japanese_name", "").strip()
            if (fallback and _contains_latin(str(entity["canonical_name"]))
                    and normalize_entity_name(fallback) != entity["normalized_name"]):
                base.update(
                    target_name=fallback,
                    resolution="reviewed Japanese fallback",
                    action="localize-jp-fallback",
                )
            else:
                base.update(resolution="no unique mapping", action="keep-unresolved")
            rows.append(base)
            continue

        mapping = mappings[mapping_index]
        target, target_source = _target_name(mapping)
        # 外部映射偶有把 `zh_cn` 填成罗马字。不能因此把已有的日文/中文规范名
        # 倒退成英文；已发生倒退时，仅用同时出现在该映射条目中的 r18 发行名恢复。
        if _contains_latin(target):
            release_name = str(entity["release_name"] or "").strip()
            mapping_names = {
                normalize_entity_name(value)
                for value in (mapping.jp, *mapping.keywords) if value
            }
            if (_is_non_latin_east_asian(release_name)
                    and normalize_entity_name(release_name) in mapping_names):
                target, target_source = release_name, "r18-nonlatin-release-name"
            elif _is_non_latin_east_asian(str(entity["canonical_name"])):
                target, target_source = str(entity["canonical_name"]), "preserve-nonlatin"
        base.update(
            target_name=target,
            mapping_key=mapping.key,
            mapping_jp=mapping.jp,
            mapping_zh_cn=mapping.zh_cn,
            resolution=f"{resolution}/{target_source}",
            action="localize" if target != entity["canonical_name"] else "keep-localized",
            _mapping_index=mapping_index,
        )
        base["_aliases"].update(
            value for value in (mapping.jp, mapping.zh_tw, str(entity["canonical_name"]))
            if value
        )
        rows.append(base)
        resolved_groups[mapping_index].append(base)

    # 同一映射条目命中多个实体，就是同一人的旧名分裂。保留作品多的一侧。
    for group in resolved_groups.values():
        if len(group) < 2:
            continue
        keeper = max(group, key=lambda row: (int(row["assets"]), -int(row["entity_id"])))
        keeper["action"] = "merge-and-localize"
        all_aliases = set().union(*(row["_aliases"] for row in group))
        all_aliases.update(str(row["current_name"]) for row in group)
        keeper["_aliases"] = all_aliases
        for row in group:
            if row is keeper:
                continue
            row["action"] = "merge-drop"
            row["merge_target_id"] = keeper["entity_id"]

    # 字形归一走在重名门槛之前：换完字形才知道会不会撞上库里已有的同名实体。
    # 映射命中与否都过一遍——「映射没收录这个人」和「映射自己的 zh_cn 还留着日本字形」
    # 是同一个症状。只有已经判成 merge-drop 的那一侧不动，它整条要并进别人。
    for row in rows:
        if row["action"] in {"merge-drop", "conflict"}:
            continue
        current = str(row["target_name"])
        japanese = [row["mapping_jp"], *row["_aliases"]]
        simplified = simplify_kanji(resolve_sai(strip_zero_width(current), japanese))
        if simplified == current:
            continue
        row["_aliases"].add(current)
        row["target_name"] = simplified
        row["resolution"] = f"{row['resolution']}/kanji-simplification"
        if str(row["action"]).startswith("keep"):
            row["action"] = "localize-kanji"

    # 名字唯一约束最后守门。只有同一 mapping group 的 merge-drop 可以与目标重名。
    active_targets: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["action"] not in {"merge-drop", "keep-non-release", "keep-unresolved"}:
            active_targets[normalize_entity_name(str(row["target_name"]))].append(row)
    existing = {
        str(entity["normalized_name"]): int(entity["id"])
        for entity in entities
    }
    dropping_into = {
        int(row["entity_id"]): int(row["merge_target_id"])
        for row in rows if row["action"] == "merge-drop"
    }
    for normalized, target_rows in active_targets.items():
        target_ids = {int(row["entity_id"]) for row in target_rows}
        owner = existing.get(normalized)
        owner_merges_here = (
            owner is not None and len(target_ids) == 1
            and dropping_into.get(owner) == next(iter(target_ids))
        )
        conflict = len(target_rows) > 1 or (
            owner is not None and owner not in target_ids and not owner_merges_here)
        if conflict:
            for row in target_rows:
                row["action"] = "conflict"
                row["resolution"] = str(row["resolution"]) + "/target-name-conflict"
    return rows


def _insert_aliases(
    connection: sqlite3.Connection, entity_id: int, names: set[str], source: str,
) -> int:
    written = 0
    canonical = connection.execute(
        "SELECT normalized_name FROM entity WHERE id=?", (entity_id,)
    ).fetchone()[0]
    for name in sorted(names, key=str.casefold):
        normalized = normalize_entity_name(name)
        if not normalized or normalized == canonical:
            continue
        if connection.execute(
            "SELECT 1 FROM entity_alias WHERE entity_id=? AND normalized_alias=? LIMIT 1",
            (entity_id, normalized),
        ).fetchone():
            continue
        connection.execute(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
            "VALUES(?,?,?,?,1.0)", (entity_id, name, normalized, source))
        written += connection.execute("SELECT changes()").fetchone()[0]
    return written


def _rewrite_actor_tags(
    connection: sqlite3.Connection, entity_id: int, old_names: set[str], target: str,
) -> int:
    rewritten = 0
    asset_ids = [int(row[0]) for row in connection.execute(
        "SELECT DISTINCT asset_id FROM asset_entity WHERE entity_id=?", (entity_id,))]
    target_tag = f"演员:{target}"
    for asset_id in asset_ids:
        for old_name in old_names:
            old_tag = f"演员:{old_name}"
            if old_tag == target_tag:
                continue
            connection.execute(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "SELECT asset_id,?,confidence,source FROM asset_tag "
                "WHERE asset_id=? AND tag=?", (target_tag, asset_id, old_tag))
            connection.execute(
                "DELETE FROM asset_tag WHERE asset_id=? AND tag=?", (asset_id, old_tag))
            if connection.execute("SELECT changes()").fetchone()[0]:
                rewritten += 1
    return rewritten


def report_conflicts(rows: list[dict[str, object]]) -> int:
    """逐条打出重名冲突：它们靠被人看见来解决，不靠把整批改名扣在门外。"""
    stuck = [row for row in rows if row["action"] == "conflict"]
    for row in stuck:
        print(f"  重名待裁决：{row['entity_id']} {row['current_name']} -> "
              f"{row['target_name']}（{row['resolution']}）")
    return len(stuck)


def apply_rows(
    connection: sqlite3.Connection, rows: list[dict[str, object]], revision: str,
) -> dict[str, int]:
    counts = Counter()
    # 重名冲突只挡住它自己那一行：下面的写入循环本来就跳过 conflict，整批拒绝扣住的
    # 是另外九十条毫无关系的改名——一个等人授权的同人合并不该冻住整轮本地化。跳过的
    # 行照样计数、照样让退出码非零，不会悄悄消失。
    counts["conflicts_skipped"] = sum(1 for row in rows if row["action"] == "conflict")
    source = f"{ALIAS_SOURCE_PREFIX}@{revision[:12]}"
    by_id = {int(row["entity_id"]): row for row in rows}

    for row in rows:
        if row["action"] != "merge-drop":
            continue
        source_id = int(row["entity_id"])
        target_id = int(row["merge_target_id"])
        moved = merge_entity(
            connection, target_id=target_id, source_id=source_id,
            source_name=str(row["current_name"]), alias_source=MERGE_ALIAS_SOURCE,
        )
        counts["merged"] += 1
        counts["relations_moved"] += moved["assets"]
        counts["dropped_refs"] += moved["dropped_refs"]
        by_id[target_id]["_aliases"].update(row["_aliases"])
        by_id[target_id]["_aliases"].add(str(row["current_name"]))

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for row in rows:
        if row["action"] not in {
            "localize", "merge-and-localize", "localize-jp-fallback", "keep-localized",
            "localize-kanji",
        }:
            continue
        entity_id = int(row["entity_id"])
        target = str(row["target_name"])
        old_names = set(row["_aliases"])
        old_names.add(str(row["current_name"]))
        # 字形归一不来自那份映射，别名来源不能冒充它的修订号。
        alias_source = (
            KANJI_ALIAS_SOURCE if row["action"] == "localize-kanji" else source)
        connection.execute(
            "UPDATE entity SET canonical_name=?,normalized_name=?,updated_at=? WHERE id=?",
            (target, normalize_entity_name(target), stamp, entity_id),
        )
        if target != row["current_name"]:
            counts["renamed"] += connection.execute("SELECT changes()").fetchone()[0]
        counts["aliases"] += _insert_aliases(connection, entity_id, old_names, alias_source)
        counts["actor_tags_rewritten"] += _rewrite_actor_tags(
            connection, entity_id, old_names, target)

        if row["mapping_key"]:
            raw = connection.execute(
                "SELECT metadata_json FROM entity WHERE id=?", (entity_id,)
            ).fetchone()[0]
            try:
                metadata = json.loads(raw or "{}")
            except (TypeError, ValueError):
                metadata = {}
            metadata["name_localization"] = {
                "source": ALIAS_SOURCE_PREFIX,
                "revision": revision,
                "mapping_key": row["mapping_key"],
                "jp": row["mapping_jp"],
                "zh_cn": target,
            }
            connection.execute(
                "UPDATE entity SET metadata_json=? WHERE id=?",
                (json.dumps(metadata, ensure_ascii=False, separators=(",", ":")), entity_id),
            )
            counts["provenance"] += 1
    return dict(counts)


FIELDS = (
    "entity_id", "current_name", "target_name", "assets", "sources", "mapping_key",
    "mapping_jp", "mapping_zh_cn", "resolution", "action", "merge_target_id", "revision",
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    write_rows(path, FIELDS, rows, fill_missing=True)


#: 本脚本自己关心的口径；基础计数由 `scripting.counts_of` 给。
EXTRA_COUNTS = {
    "performer": "SELECT count(*) FROM entity WHERE kind='performer'",
    "asset_tag": "SELECT count(*) FROM asset_tag",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="用中日映射本地化番号体系女优姓名")
    add_ledger_write_args(parser)
    # 映射 XML 不在仓库里，也可能已经不在这台机器上。不给就只跑字形归一，
    # 那一道不需要外部来源，缺了 XML 也不该把整个脚本变成跑不起来。
    parser.add_argument("--mapping-xml", type=Path)
    parser.add_argument("--mapping-revision", default="")
    parser.add_argument(
        "--identity-review", type=Path,
        default=DATA_ROOT / "review" / "performer-identity-20260815.csv")
    parser.add_argument(
        "--review-csv", type=Path,
        default=GENERATED_DIR / "performer-name-localization.csv")
    return parser


def run(args: argparse.Namespace) -> int:
    mappings = read_mapping(args.mapping_xml) if args.mapping_xml else []
    identity_review = read_identity_review(args.identity_review)
    connection = open_for_write(args)
    try:
        rows = collect(connection, mappings, identity_review, args.mapping_revision)
        write_csv(args.review_csv, rows)
        print(f"已审计 performer {len(rows)} 位；复核 CSV：{args.review_csv}")
        print("  动作分布：", dict(Counter(str(row["action"]) for row in rows)))
        if not args.apply:
            print("  未写 ledger（加 --apply --backup 才写）")
            return 1 if report_conflicts(rows) else 0

        print(f"  已备份到 {args.backup}")
        before = counts_of(connection, EXTRA_COUNTS)
        with connection:
            changed = apply_rows(connection, rows, args.mapping_revision)
        after = counts_of(connection, EXTRA_COUNTS)
        integrity, foreign_keys = verify_after_write(connection)
        print("  写入结果：", changed)
        for key in before:
            print(f"    {key}: {before[key]} -> {after[key]}")
        print(f"  integrity_check={integrity}；foreign_key_check={foreign_keys}")
        stuck = report_conflicts(rows)
        return 1 if integrity != "ok" or foreign_keys or stuck else 0
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.mapping_xml and not args.mapping_revision:
        parser.error("给了 --mapping-xml 就必须给 --mapping-revision，别名要记得住来源")
    args.mapping_revision = args.mapping_revision or KANJI_ONLY_REVISION
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
