#!/usr/bin/env python3
"""Fetch per-source JAV metadata into field-level Peach review candidates.

Javinizer-Go is used only as a query adapter. Peach sends a normalized movie code,
stores every raw source response, and never invokes Javinizer's organizer or DB flow.
The generated CSV is a review queue; this command has no ledger write mode.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from peach.catalog_rules import normalise_code_key
from peach.config import DATABASE_PATH, GENERATED_DIR, LOG_DIR, SOURCES_DIR, STATE_DIR
from peach.jobs import DiskGuard, JobPolicyError
from peach.metadata import (
    CATALOG_EVIDENCE_FIELDS,
    JAVINIZER_GO_VERSION,
    JavinizerGoProvider,
    MetadataProviderError,
    extract_catalog_evidence,
    extract_peach_fields,
)
from peach.metadata_policy import (
    PEACH_FIELDS,
    MetadataPolicy,
    resolve_policy,
    sort_candidates,
)
from peach.platform import system_volume
from peach.review_csv import ENCODING, write_rows


_logf = None
FIELD_LABELS = {
    "title": "标题", "original_title": "原标题",
    "performers": "演员", "studio": "厂牌", "series": "系列",
    "release_date": "发行日期", "tags": "内容标签",
}
FIELDS = [
    "item_key", "code", "query", "field", "field_label", "current_value",
    "candidates_json", "source_count", "source_profile", "policy_version",
    "status", "size_gb", "videos", "fetched_at",
]
ERROR_FIELDS = ["code", "query", "source", "kind", "status_code", "retryable", "message"]
HEALTH_FIELDS = [
    "source", "profile", "attempted", "snapshot_reused", "fetched", "succeeded",
    "empty", "errors", "retryable_errors", "cooldown_skips", "blocked", "elapsed_ms",
    *dict.fromkeys((*PEACH_FIELDS, *CATALOG_EVIDENCE_FIELDS)),
    "last_error_kind", "last_error_status", "last_error_message",
]


# Javinizer 来源类型 -> Peach 已复核的内容分类。来源里没映射到的值留在原始快照里，
# 不会变成没人复核过的自由文本标签。
#
# r18dev 给英文，javbus/javdb 给日文，所以同一张表里两套键并存；两套键不会撞，
# 值必须落在既有的 Peach 分类词表内——标签是语义契约，不能靠抓取顺手扩词表。
#
# 刻意不收的：`独占配信`、`配信専用`、`単体作品`、`企画`、`店長推薦作品`、`超VIP`、
# `超有名S級女優`、`ベスト・総集編`、`初裏`、`AV女優` 是发行与营销分类，
# `ハイビジョン`、`フルハイビジョン(FHD)`、`1080p`、`60fps`、`4時間以上作品` 是规格，
# 都不是内容标签。这与既有的「`Featured Actress` 不入库」是同一条线。
#
# 也不收罩杯（`Dカップ`…`Jカップ`）与 `巨大乳輪`：罩杯是身体尺寸不是内容分类，
# 词表里也没有对应项。2026-09-02 全部缓存快照里罩杯只出现 5 次，其中 G/H 同时带
# `巨乳`、D/F 什么都不带——五个样本推不出映射规则，来源想说巨乳时会直接写巨乳。
#
# 映射一律取来源给出的那一级，禁止升到 `乳系`、`足系` 这类粗桶。
# `catalog_rules.TAG_SUPERSESSION` 的定义就是「有具体标签时把粗桶删掉」，
# 把 `巨乳` 映成 `乳系` 是把系统准备丢弃的那个值当成结论，方向反了。
CATEGORY_MAP = {
    "Foot Fetish": "美腿", "Legs": "美腿", "Pantyhose": "丝袜", "Stockings": "丝袜",
    "Creampie": "中出内射", "Squirting": "潮吹", "Blowjob": "口交", "Deep Throat": "深喉",
    "Facial": "颜射", "Cum Swallowing": "吞精", "Handjob": "手交",
    "Big Tits": "巨乳", "Beautiful Tits": "美乳", "Small Tits": "贫乳", "Titty Fuck": "乳交",
    "Slender": "苗条", "Chubby": "丰满", "Beautiful Girl": "高颜值",
    "Office Lady": "秘书OL", "School Girls": "学生", "Nurse": "护士",
    "Uniform": "制服", "Cosplay": "角色扮演", "Maid": "女仆", "Swimsuit": "泳装",
    "Married Woman": "人妻", "Mature Woman": "人妻", "Big Tits Lover": "巨乳",
    "Threesome / Foursome": "多人", "Orgy": "多人", "Lesbian": "百合",
    "Anal": "肛交", "Bondage": "调教", "Torture": "调教", "Training": "调教",
    "Slut": "痴女", "Nymphomaniac": "痴女", "Cuckold": "绿帽NTR", "Voyeur": "偷拍偷窥",
    "Hidden Camera": "偷拍偷窥", "Amateur": "素人", "Massage": "按摩", "Bath": "浴室",
    "Outdoor": "户外露出", "Car Sex": "车震", "Ass Lover": "美臀", "Butt": "美臀",
    "Glasses": "眼镜", "Virtual Reality": "VR", "POV": "主观视角", "Restraint": "调教",
    "Incest": "近亲", "Cheating Wife": "绿帽NTR", "4K": "4K",
    "Digital Mosaic": "有码", "Cowgirl": "骑乘", "Shaved Pussy": "白虎",
    # javbus/javdb 的日文类型词。取自 2026-09-02 那批真实快照里出现过的词表，
    # 外加几个与上面英文键完全同义、javbus 常用的标准分类。
    "素人": "素人", "中出し": "中出内射", "潮吹き": "潮吹",
    "巨乳": "巨乳", "美乳": "美乳", "爆乳": "爆乳",
    "微乳": "贫乳", "貧乳・微乳": "贫乳", "貧乳": "贫乳",
    "パイズリ": "乳交", "スレンダー": "苗条", "ぽっちゃり": "丰满",
    "美脚": "美腿", "脚フェチ": "美腿", "パンスト": "丝袜", "ニーソックス": "丝袜",
    "尻フェチ": "美臀", "美尻": "美臀", "巨尻": "美臀",
    "フェラ": "口交", "イラマチオ": "深喉", "手コキ": "手交", "顔射": "颜射",
    "パイパン": "白虎", "剃毛": "白虎", "痴女": "痴女",
    "コスプレ": "角色扮演", "制服": "制服", "学生服": "制服",
    "女子校生": "学生", "女子大生": "学生",
    "OL": "秘书OL", "キャリアウーマン": "秘书OL",
    "看護婦": "护士", "ナース": "护士", "メイド": "女仆", "水着": "泳装",
    "美少女": "高颜值", "美女": "高颜值",
    "騎乗位": "骑乘", "乱交": "多人", "3P・4P": "多人", "ハーレム": "多人",
    "レズ": "百合", "アナル": "肛交",
    "SM": "调教", "拘束": "调教", "調教": "调教",
    "人妻": "人妻", "熟女": "人妻", "熟女/人妻": "人妻",
    "寝取り・寝取られ": "绿帽NTR", "不倫": "绿帽NTR",
    "野外露出": "户外露出", "露出": "户外露出",
    "盗撮・のぞき": "偷拍偷窥", "マッサージ・リフレ": "按摩", "風呂": "浴室",
    "カーセックス": "车震", "眼鏡": "眼镜", "近親相姦": "近亲",
    "主観": "主观视角", "VR": "VR", "デジモ": "有码",
}


def configure_log(log_dir: str | Path) -> None:
    global _logf
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    _logf = (path / time.strftime("metadata-candidates-%Y%m%d-%H%M%S.log")).open(
        "w", encoding="utf-8", buffering=1,
    )


def log(message: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {message}"
    print(line, flush=True)
    if _logf is not None:
        _logf.write(line + "\n")


def close_log() -> None:
    global _logf
    if _logf is not None:
        _logf.close()
        _logf = None


def _is_explicit_code(code: str) -> bool:
    """番号是否明确到可以直接查来源；判的是**规范化之后**的形态。

    真正发给 provider 的就是 `normalise_code_key(code)`，而账本里同一个番号常以
    `HJD2048`、`WX17`、`BANBI_555` 这种缺分隔符的原始写法存着。按原始写法判会把它们
    当成不明确整条跳过，`--codes-file` 那一侧却是按规范化键匹配的，于是同一批番号在
    两处结论相反，报成「番号文件含 ledger 中不存在的番号」。2026-09-02 实测漏掉 42 个。
    `normalise_code_key` 只重排本来就是「字母+数字」形态的值，不会把杂串变成番号。
    """
    value = normalise_code_key(code).upper().strip()
    if value.startswith("FC2"):
        return bool(re.search(r"\d{5,}", value))
    return bool(
        re.fullmatch(r"[A-Z]{2,8}-\d{2,5}", value)
        or re.fullmatch(r"\d{3}[A-Z]{2,6}-\d{2,5}", value)
        or re.fullmatch(r"\d{6}-\d{2,4}", value)
    )


def _candidate_key(code: str, field: str, source: str, value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{code}\0{field}\0{source}\0{canonical}".encode()).hexdigest()[:20]
    return f"{code}:{field}:{source}:{digest}"


def _current_values(connection: sqlite3.Connection, code: str, field: str) -> list[str]:
    title_columns = {"title": "catalog_title", "original_title": "original_title"}
    column = title_columns.get(field, field)
    if field in {"title", "original_title", "studio", "series", "release_date"}:
        if column not in {
            str(row[1]) for row in connection.execute("PRAGMA table_info(asset)")
        }:
            return []
        rows = connection.execute(
            f"SELECT DISTINCT trim({column}) FROM asset WHERE medium='video' "
            f"AND upper(trim(code))=upper(?) AND {column} IS NOT NULL AND trim({column})<>''",
            (code,),
        )
    elif field == "performers":
        rows = connection.execute(
            "SELECT DISTINCT e.canonical_name FROM asset a "
            "JOIN asset_entity ae ON ae.asset_id=a.id AND ae.role='performer' "
            "JOIN entity e ON e.id=ae.entity_id AND e.kind='performer' "
            "WHERE a.medium='video' AND upper(trim(a.code))=upper(?)",
            (code,),
        )
    else:
        allowed = sorted(set(CATEGORY_MAP.values()))
        marks = ",".join("?" * len(allowed))
        rows = connection.execute(
            "SELECT DISTINCT t.tag FROM asset a JOIN asset_tag t ON t.asset_id=a.id "
            f"WHERE a.medium='video' AND upper(trim(a.code))=upper(?) AND t.tag IN ({marks})",
            (code, *allowed),
        )
    return sorted({str(row[0]).strip() for row in rows if str(row[0] or "").strip()})


def _read_snapshot(path: Path) -> dict | None:
    try:
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        result = wrapper.get("result")
        return result if isinstance(result, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _read_settled_error(path: Path) -> MetadataProviderError | None:
    """复用确定失败，只让临时/可重试错误重新联网。"""
    try:
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        error = wrapper.get("error")
        if not isinstance(error, dict):
            return None
        if bool(error.get("retryable")) or bool(error.get("temporary")):
            return None
        return MetadataProviderError(
            str(error.get("message") or "metadata source error"),
            kind=str(error.get("kind") or "unknown"),
            status_code=int(error.get("status_code") or 0),
            retryable=False,
            temporary=False,
        )
    except (OSError, ValueError, TypeError):
        return None


def _write_snapshot(path: Path, *, code: str, source: str, result: dict | None = None,
                    error: MetadataProviderError | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper: dict[str, object] = {
        "provider": "javinizer-go", "provider_version": JAVINIZER_GO_VERSION,
        "code": code, "source": source,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    if result is not None:
        wrapper["result"] = result
    if error is not None:
        wrapper["error"] = {
            "kind": error.kind, "message": str(error), "status_code": error.status_code,
            "retryable": error.retryable, "temporary": error.temporary,
        }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _default_output() -> Path:
    return GENERATED_DIR / time.strftime("metadata-field-candidates-%Y%m%d-%H%M%S.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="fetch field-level metadata review candidates")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--errors", type=Path, default=None)
    parser.add_argument("--raw-dir", type=Path, default=SOURCES_DIR / "metadata" / "javinizer-go")
    parser.add_argument("--log-dir", type=Path, default=LOG_DIR)
    parser.add_argument("--config", type=Path, default=STATE_DIR / "javinizer-provider" / "config.yaml")
    parser.add_argument("--binary", type=Path)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--profile", choices=("baseline", "censored", "uncensored", "fc2"),
                              help="explicit Peach source preset; default baseline")
    source_group.add_argument("--sources", help="compatible comma-separated Javinizer scraper names")
    parser.add_argument("--health", type=Path, default=None)
    parser.add_argument(
        "--codes-file", type=Path,
        help="只处理文件中列出的番号；每行一个，空行和 # 注释忽略",
    )
    parser.add_argument(
        "--english-title-only", action="store_true",
        help="只处理已有非空英文标题、但没有日文标题的番号",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=1.2)
    parser.add_argument("--min-free", type=float, default=40.0,
                        help="系统盘最低可用 GiB；运行中每隔一段时间复查")
    parser.add_argument("--disk-check-secs", type=float, default=20.0)
    parser.add_argument("--refresh", action="store_true", help="ignore reusable raw snapshots")
    parser.add_argument("--include-fc2", action="store_true")
    return parser


def _requested_codes(path: Path) -> list[str]:
    requested: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding=ENCODING).splitlines():
        value = raw.split("#", 1)[0].strip()
        if not value:
            continue
        query = normalise_code_key(value)
        if query not in seen:
            seen.add(query)
            requested.append(query)
    return requested


def _select_requested_codes(
    codes: list[tuple[str, float, int]], path: Path,
) -> list[tuple[str, float, int]]:
    requested = _requested_codes(path)
    available: dict[str, tuple[str, float, int]] = {}
    for code, size_gb, videos in codes:
        query = normalise_code_key(code)
        previous = available.get(query)
        if previous is None:
            available[query] = (code, size_gb, videos)
        else:
            available[query] = (
                previous[0], previous[1] + size_gb, previous[2] + videos,
            )
    missing = [query for query in requested if query not in available]
    if missing:
        preview = "、".join(missing[:10])
        suffix = f" 等 {len(missing)} 个" if len(missing) > 10 else ""
        raise ValueError(f"番号文件含 ledger 中不存在的番号：{preview}{suffix}")
    return [available[query] for query in requested]


_JAPANESE_TEXT_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
_LATIN_TEXT_RE = re.compile(r"[A-Za-z]")


def _select_english_title_codes(connection, codes: list[tuple[str, float, int]]) -> list[tuple[str, float, int]]:
    """Select codes whose recorded titles are Latin-only and have no Japanese alternative."""
    titles: dict[str, list[str]] = {}
    for code, catalog_title, original_title in connection.execute(
        "SELECT code,catalog_title,original_title FROM asset "
        "WHERE medium='video' AND code IS NOT NULL AND trim(code)<>''"
    ):
        key = normalise_code_key(str(code))
        titles.setdefault(key, []).extend(
            str(value).strip() for value in (catalog_title, original_title) if str(value or "").strip()
        )
    selected = []
    for row in codes:
        values = titles.get(normalise_code_key(row[0]), [])
        if (values and any(_LATIN_TEXT_RE.search(value) for value in values)
                and not any(_JAPANESE_TEXT_RE.search(value) for value in values)):
            selected.append(row)
    return selected


def _health_output(output: Path) -> Path:
    name = output.name.replace("metadata-field-candidates-", "metadata-source-health-", 1)
    if name == output.name:
        name = output.stem + "-health.csv"
    return output.with_name(name)


def _health_rows(policy: MetadataPolicy) -> dict[str, dict[str, object]]:
    return {source: {
        "source": source, "profile": policy.profile, "attempted": 0,
        "snapshot_reused": 0, "fetched": 0, "succeeded": 0, "empty": 0,
        "errors": 0, "retryable_errors": 0, "cooldown_skips": 0,
        "blocked": 0, "elapsed_ms": 0,
        **{field: 0 for field in (*PEACH_FIELDS, *CATALOG_EVIDENCE_FIELDS)},
        "last_error_kind": "", "last_error_status": "", "last_error_message": "",
    } for source in policy.sources}


def _write_health(path: Path, rows: dict[str, dict[str, object]]) -> None:
    write_rows(path, HEALTH_FIELDS, rows.values(), atomic=True)


def main(argv: list[str] | None = None, *, provider: JavinizerGoProvider | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        policy = resolve_policy(profile=args.profile, sources=args.sources)
    except ValueError as error:
        parser.error(str(error))
    explicit_sources = args.sources is not None
    if args.profile == "fc2" and args.include_fc2:
        parser.error("fc2 profile 已只处理 FC2，不能再加 --include-fc2")
    output = args.out or _default_output()
    error_name = output.name.replace("metadata-field-candidates-", "metadata-source-errors-", 1)
    if error_name == output.name:
        error_name = output.stem + "-errors.csv"
    errors_path = args.errors or output.with_name(error_name)
    health_path = args.health or _health_output(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    errors_path.parent.mkdir(parents=True, exist_ok=True)
    configure_log(args.log_dir)
    guard = DiskGuard(system_volume(), args.min_free, args.disk_check_secs)
    try:
        free_gb = guard.check(force=True)
    except JobPolicyError as error:
        log(f"[stop] {error}")
        close_log()
        return error.exit_code
    log(f"系统盘可用 {free_gb:.1f} GiB，运行期阈值 {args.min_free:.1f} GiB")
    sources = list(policy.sources)
    health = _health_rows(policy)
    adapter = provider or JavinizerGoProvider.create(args.binary, args.config)

    connection = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro", uri=True)
    codes = [
        (str(row[0]).strip(), float(row[1]), int(row[2]))
        for row in connection.execute(
            "SELECT code,COALESCE(sum(size),0)/1073741824.0,count(*) FROM asset "
            "WHERE medium='video' AND code IS NOT NULL AND trim(code)<>'' "
            "GROUP BY code ORDER BY 2 DESC"
        )
        if _is_explicit_code(str(row[0]))
    ]
    codes = [row for row in codes if policy.allows_code(
        row[0], include_fc2=args.include_fc2, explicit_sources=explicit_sources,
    )]
    if args.codes_file:
        try:
            codes = _select_requested_codes(codes, args.codes_file)
        except (OSError, UnicodeError, ValueError) as error:
            parser.error(str(error))
    if args.english_title_only:
        codes = _select_english_title_codes(connection, codes)
    if args.limit:
        codes = codes[:max(args.limit, 0)]
    log(f"字段候选批次：profile {policy.profile}，番号 {len(codes)}，来源 {','.join(sources)}；只读查询，不写 ledger")

    blocked_sources: set[str] = set()
    groups_written = errors_written = 0
    stopped: JobPolicyError | None = None
    # 流式写：两个文件同时开着，行在长循环里边跑边落盘，中途还有 guard.check()
    # 打断点。write_rows 收的是完整行集合，改用它等于「跑完才落盘」，被打断就全丢。
    with output.open("w", encoding=ENCODING, newline="") as candidate_handle, \
            errors_path.open("w", encoding=ENCODING, newline="") as error_handle:
        candidate_writer = csv.DictWriter(candidate_handle, fieldnames=FIELDS)
        error_writer = csv.DictWriter(error_handle, fieldnames=ERROR_FIELDS)
        candidate_writer.writeheader(); error_writer.writeheader()
        for index, (code, size_gb, videos) in enumerate(codes, 1):
            try:
                guard.check()
            except JobPolicyError as error:
                stopped = error
                log(f"[stop] {error}")
                break
            query = normalise_code_key(code)
            by_field: dict[str, list[dict]] = {}
            fetched_at = datetime.now(timezone.utc).isoformat()
            for source in sources:
                source_health = health[source]
                source_health["attempted"] += 1
                if source in blocked_sources:
                    source_health["cooldown_skips"] += 1
                    continue
                snapshot = args.raw_dir / query / f"{source}.json"
                started = time.perf_counter()
                payload = None if args.refresh else _read_snapshot(snapshot)
                settled_error = None if args.refresh else _read_settled_error(snapshot)
                reused = payload is not None or settled_error is not None
                try:
                    if reused:
                        source_health["snapshot_reused"] += 1
                        if settled_error is not None:
                            raise settled_error
                    else:
                        source_health["fetched"] += 1
                        payload = adapter.query(query, source)
                    if not snapshot.is_file() or args.refresh:
                        _write_snapshot(snapshot, code=query, source=source, result=payload)
                except MetadataProviderError as error:
                    if not reused or args.refresh:
                        _write_snapshot(snapshot, code=query, source=source, error=error)
                    error_writer.writerow({
                        "code": code, "query": query, "source": source, "kind": error.kind,
                        "status_code": error.status_code, "retryable": int(error.retryable),
                        "message": str(error),
                    })
                    error_handle.flush(); errors_written += 1
                    source_health["errors"] += 1
                    source_health["retryable_errors"] += int(error.retryable)
                    source_health["last_error_kind"] = error.kind
                    source_health["last_error_status"] = error.status_code or ""
                    source_health["last_error_message"] = str(error)[:500]
                    if error.retryable or error.status_code in {403, 429, 503}:
                        blocked_sources.add(source)
                        source_health["blocked"] = 1
                        log(f"{source} 暂时不可用，本批后续番号进入来源级冷却：{error}")
                    continue
                finally:
                    source_health["elapsed_ms"] += round((time.perf_counter() - started) * 1000)
                extracted_fields = extract_peach_fields(payload, CATEGORY_MAP)
                catalog_evidence = extract_catalog_evidence(payload)
                source_health["succeeded"] += 1
                if not extracted_fields and not catalog_evidence:
                    source_health["empty"] += 1
                for field in set(catalog_evidence) | set(extracted_fields):
                    source_health[field] += 1
                for field, extracted in extracted_fields.items():
                    source_spec = policy.source(source)
                    candidate = {
                        "candidate_key": _candidate_key(query, field, source, extracted["value"]),
                        "source": source,
                        "source_url": str(payload.get("source_url") or ""),
                        "confidence": 0.9 if source == "r18dev" else 0.75,
                        "profile": policy.profile,
                        "policy_version": policy.version,
                        "field_rank": policy.field_rank(field, source),
                        "source_kind": source_spec.kind,
                        "official": source_spec.official,
                        "provider_id": str(payload.get("id") or ""),
                        "content_id": str(payload.get("content_id") or ""),
                        "value": extracted["value"],
                        "display_value": extracted["display_value"],
                        "warnings": extracted["warnings"],
                        "catalog_evidence": catalog_evidence,
                        "raw_snapshot": str(snapshot),
                    }
                    by_field.setdefault(field, []).append(candidate)
                # 续跑重建候选时会读取数百个本地快照；它们没有网络请求，不该
                # 消耗来源限流窗口。只给本次真实 fetch 留间隔，既保持 r18dev
                # 的长跑节流，也让熔断后的恢复立即越过已完成部分。
                if args.delay > 0 and not reused:
                    time.sleep(args.delay + random.uniform(0, min(0.4, args.delay / 3)))
            for field, candidates in by_field.items():
                if args.english_title_only and field != "title":
                    continue
                candidates = sort_candidates(field, candidates, policy)
                candidate_writer.writerow({
                    "item_key": f"{query}:{field}", "code": code, "query": query,
                    "field": field, "field_label": FIELD_LABELS[field],
                    "current_value": "、".join(_current_values(connection, code, field)),
                    "candidates_json": json.dumps(candidates, ensure_ascii=False, separators=(",", ":")),
                    "source_count": len(candidates), "source_profile": policy.profile,
                    "policy_version": policy.version, "status": "candidate",
                    "size_gb": round(size_gb, 2), "videos": videos, "fetched_at": fetched_at,
                })
                groups_written += 1
            candidate_handle.flush()
            _write_health(health_path, health)
            if index % 25 == 0:
                log(f"{index}/{len(codes)}：已落 {groups_written} 个字段组，错误 {errors_written}")
    connection.close()
    _write_health(health_path, health)
    log(f"完成：{groups_written} 个字段候选组 → {output}")
    log(f"来源健康 → {health_path}")
    if errors_written:
        log(f"来源错误 {errors_written} 条 → {errors_path}")
    close_log()
    return stopped.exit_code if stopped is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
