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
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.catalog_rules import code_query_variants, is_jav_code, normalise_code_key
from peach.scripting import open_readonly
from peach.config import DATABASE_PATH, GENERATED_DIR, LOG_DIR, SOURCES_DIR, STATE_DIR
from peach.genre_taxonomy import CONTENT_GENRES, map_genres
from peach.jobs import DiskGuard, JobPolicyError
from peach.metadata import (
    CATALOG_EVIDENCE_FIELDS,
    JAVINIZER_GO_VERSION,
    JavinizerGoProvider,
    MetadataProviderError,
    extract_catalog_evidence,
    extract_peach_fields,
    identifies_code,
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
UNMAPPED_FIELDS = ["genre", "source", "occurrences", "sample_code"]
HEALTH_FIELDS = [
    "source", "profile", "attempted", "snapshot_reused", "fetched", "succeeded",
    "empty", "errors", "retryable_errors", "cooldown_skips", "blocked", "elapsed_ms",
    *dict.fromkeys((*PEACH_FIELDS, *CATALOG_EVIDENCE_FIELDS)),
    "last_error_kind", "last_error_status", "last_error_message",
]


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
    r"""番号是否明确到可以直接查来源；判的是**规范化之后**的形态。

    真正发给 provider 的就是 `normalise_code_key(code)`，而账本里同一个番号常以
    `WX17`、`BANBI_555`、`IPVR00296` 这种缺分隔符的原始写法存着。按原始写法判会把它们
    当成不明确整条跳过，`--codes-file` 那一侧却是按规范化键匹配的，于是同一批番号在
    两处结论相反，报成「番号文件含 ledger 中不存在的番号」。2026-09-02 实测漏掉 42 个。

    形态判定交给 `is_jav_code`，这里不再抄一份正则。抄出来的那份和它逐字相同，于是
    `HHD800`、`HJD2048` 这些转载站水印域名在 `catalog_rules` 侧被排除之后，这里还会
    继续把它们发给 provider 查——同一个「什么算番号」有两个答案。
    """
    return is_jav_code(normalise_code_key(code))


def _fetch_source(adapter, *, query: str, source: str, snapshot: Path,
                  refresh: bool,
                  health: dict) -> tuple[dict | None, MetadataProviderError | None, bool]:
    """取一个写法一个来源：优先复用快照，失败也落盘，返回 (payload, error, reused)。

    单独拆出来是因为一个番号要问的写法可能不止一个，而每个写法的快照、限流计数和
    错误落盘规则完全一样。身份校验不在这里：`JavinizerGoProvider.query` 已经用
    `identifies_code` 把「返回的不是这一部」判成 `not_found`，`_read_snapshot` 复用
    快照时也照同一条判据再过一遍。
    """
    payload = None if refresh else _read_snapshot(snapshot, query)
    settled = None if refresh else _read_settled_error(snapshot)
    reused = payload is not None or settled is not None
    try:
        if reused:
            health["snapshot_reused"] += 1
            if settled is not None:
                raise settled
        else:
            health["fetched"] += 1
            payload = adapter.query(query, source)
        if not snapshot.is_file() or refresh:
            _write_snapshot(snapshot, code=query, source=source, result=payload)
    except MetadataProviderError as error:
        if not reused or refresh:
            _write_snapshot(snapshot, code=query, source=source, error=error)
        return None, error, reused
    return payload, None, reused


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
        allowed = sorted(set(CONTENT_GENRES.values()))
        marks = ",".join("?" * len(allowed))
        rows = connection.execute(
            "SELECT DISTINCT t.tag FROM asset a JOIN asset_tag t ON t.asset_id=a.id "
            f"WHERE a.medium='video' AND upper(trim(a.code))=upper(?) AND t.tag IN ({marks})",
            (code, *allowed),
        )
    return sorted({str(row[0]).strip() for row in rows if str(row[0] or "").strip()})


def _read_snapshot(path: Path, code: str) -> dict | None:
    """复用上一轮的成功记录，但先确认它和这个番号对得上。

    快照是在 `identifies_code` 之前落的盘，里面就有 dl.getchu 拿不相干同人商品
    当结果的记录。只看「有没有 result」而不看身份，等于把当初那次错配一路复用
    下去——封面域 2026-09-01 的跨片封套正是这么带到今天的。对不上就当没有快照，
    重新联网问一次，闸在 provider 那一侧会把它变成 not_found。
    """
    try:
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        result = wrapper.get("result")
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(result, dict) or not identifies_code(code, result):
        return None
    return result


#: 只有来源明确答「没有这部片」才算定论。`unknown` 是「这次没问出结果」，
#: 把它当定论复用过一次真实代价：2026-08-30 前 javinizer config 还没启用
#: mgstage/libredmm/dlgetchu/aventertainment，那一轮的错误快照全是
#: `scraper "mgstage" is not enabled`，本机配置问题被冻结成来源判决，之后
#: 每次续跑都直接跳过，10 个番号再也没被问过。
SETTLED_ERROR_KINDS = frozenset({"not_found"})

#: 连续多少次可重试失败才让来源进冷却，以及冷却多久（秒）。
#: 2026-09-01 的官方 tag 补抓实测：mgstage 在中途超时一次，旧逻辑当场把它
#: 「本批后续全部跳过」，剩下 122 个番号再也没被问过，dmm 同样丢了 150 个。
#: 一次超时是抖动不是封禁；真被限流会连续失败，那时再退让也来得及。冷却也
#: 必须会过期——长批次里一次抖动不该决定后面几百个番号的命运。
COOLDOWN_AFTER_FAILURES = 3
COOLDOWN_SECONDS = 300.0


def _read_settled_error(path: Path) -> MetadataProviderError | None:
    """复用确定失败，只让临时/可重试/结论不明的错误重新联网。"""
    try:
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        error = wrapper.get("error")
        if not isinstance(error, dict):
            return None
        if bool(error.get("retryable")) or bool(error.get("temporary")):
            return None
        if str(error.get("kind") or "") not in SETTLED_ERROR_KINDS:
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
    source_group.add_argument(
        "--profile",
        choices=("baseline", "censored", "uncensored", "fc2",
                 "official-backfill", "backfill"),
        help="explicit Peach source preset; default baseline")
    source_group.add_argument("--sources", help="compatible comma-separated Javinizer scraper names")
    parser.add_argument("--health", type=Path, default=None)
    parser.add_argument("--unmapped", type=Path, default=None,
                        help="未收录 genre 清单；不写这个文件等于把来源给过的值悄悄丢掉")
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


def _unmapped_output(output: Path) -> Path:
    name = output.name.replace("metadata-field-candidates-", "metadata-unmapped-genres-", 1)
    if name == output.name:
        name = output.stem + "-unmapped-genres.csv"
    return output.with_name(name)


def _write_unmapped(path: Path, seen: dict[tuple[str, str], list]) -> None:
    rows = [
        {"genre": genre, "source": source, "occurrences": count, "sample_code": sample}
        for (source, genre), (count, sample) in sorted(
            seen.items(), key=lambda item: (-item[1][0], item[0][0], item[0][1]),
        )
    ]
    write_rows(path, UNMAPPED_FIELDS, rows, atomic=True)


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
    unmapped_path = args.unmapped or _unmapped_output(output)
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
    unmapped_genres: dict[tuple[str, str], list] = {}
    adapter = provider or JavinizerGoProvider.create(args.binary, args.config)

    connection = open_readonly(args.db)
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

    cooldown_until: dict[str, float] = {}
    consecutive_failures: dict[str, int] = {}
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
            # `259LUXU-1642` 与 `LUXU-1642` 是同一部作品的两种写法，来源站各只索引
            # 其中一种。账本存哪种就只查哪种，会把「这个站没收录这种写法」误判成
            # 「这部作品查不到」。第一个永远是账本的规范写法，评审键不随回退漂移。
            variants = code_query_variants(code) or (query,)
            by_field: dict[str, list[dict]] = {}
            fetched_at = datetime.now(timezone.utc).isoformat()
            # 每个番号问哪几家由 policy 按发行面决定：日期形和 HEYZO 是无码站
            # 的编号法，拿去问 mgstage/dmm 只会得到「问了都没有」。
            for source in policy.sources_for_code(query):
                source_health = health[source]
                source_health["attempted"] += 1
                if time.monotonic() < cooldown_until.get(source, 0.0):
                    source_health["cooldown_skips"] += 1
                    continue
                started = time.perf_counter()
                snapshot = args.raw_dir / query / f"{source}.json"
                payload = error = None
                used_network = False
                for attempt in variants:
                    snapshot = args.raw_dir / attempt / f"{source}.json"
                    payload, error, reused = _fetch_source(
                        adapter, query=attempt, source=source, snapshot=snapshot,
                        refresh=args.refresh, health=source_health)
                    used_network = used_network or not reused
                    if payload is not None:
                        if attempt != query:
                            log(f"{query} 在 {source} 改用 {attempt} 命中")
                        break
                    # 限流、封禁和网络抖动与写法无关，换个写法只是再撞一次墙。
                    if error is not None and (error.retryable
                                              or error.status_code in {403, 429, 503}):
                        break
                source_health["elapsed_ms"] += round((time.perf_counter() - started) * 1000)
                if payload is None:
                    error = error or MetadataProviderError("no result", kind="empty")
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
                        consecutive_failures[source] = consecutive_failures.get(source, 0) + 1
                        if consecutive_failures[source] >= COOLDOWN_AFTER_FAILURES:
                            cooldown_until[source] = time.monotonic() + COOLDOWN_SECONDS
                            consecutive_failures[source] = 0
                            source_health["blocked"] += 1
                            log(f"{source} 连续 {COOLDOWN_AFTER_FAILURES} 次可重试失败，"
                                f"冷却 {COOLDOWN_SECONDS:.0f} 秒后自动恢复：{error}")
                    else:
                        consecutive_failures[source] = 0
                    # 失败那几次也真的发出去了，占的是同一个限流窗口：跳过间隔直接
                    # 问下一个番号，等于把重试挤在一起，来源只会更快把我们关掉。
                    if args.delay > 0 and used_network:
                        time.sleep(args.delay + random.uniform(0, min(0.4, args.delay / 3)))
                    continue
                consecutive_failures[source] = 0
                extracted_fields = extract_peach_fields(payload)
                catalog_evidence = extract_catalog_evidence(payload)
                for genre in map_genres(payload.get("genres") or [])[1]:
                    entry = unmapped_genres.setdefault((source, genre), [0, code])
                    entry[0] += 1
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
                if args.delay > 0 and used_network:
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
            _write_unmapped(unmapped_path, unmapped_genres)
            if index % 25 == 0:
                log(f"{index}/{len(codes)}：已落 {groups_written} 个字段组，错误 {errors_written}")
    connection.close()
    _write_health(health_path, health)
    _write_unmapped(unmapped_path, unmapped_genres)
    log(f"完成：{groups_written} 个字段候选组 → {output}")
    log(f"来源健康 → {health_path}")
    log(f"未收录 genre {len(unmapped_genres)} 种 → {unmapped_path}")
    if errors_written:
        log(f"来源错误 {errors_written} 条 → {errors_path}")
    close_log()
    return stopped.exit_code if stopped is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
