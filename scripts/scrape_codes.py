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

from peach.config import DATABASE_PATH, GENERATED_DIR, LOG_DIR, SOURCES_DIR, STATE_DIR
from peach.jobs import DiskGuard, JobPolicyError
from peach.metadata import (
    JAVINIZER_GO_VERSION,
    JavinizerGoProvider,
    MetadataProviderError,
    extract_peach_fields,
)
from peach.metadata_policy import (
    PEACH_FIELDS,
    MetadataPolicy,
    resolve_policy,
    sort_candidates,
)
from peach.platform import system_volume


_logf = None
FIELD_LABELS = {
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
    *PEACH_FIELDS, "last_error_kind", "last_error_status", "last_error_message",
]


# Javinizer r18dev genre -> Peach's reviewed content taxonomy. Unknown source values
# remain in the raw snapshot instead of becoming unreviewable free-form tags.
CATEGORY_MAP = {
    "Foot Fetish": "足系", "Legs": "美腿", "Pantyhose": "丝袜", "Stockings": "丝袜",
    "Creampie": "中出内射", "Squirting": "潮吹", "Blowjob": "口交", "Deep Throat": "深喉",
    "Facial": "颜射", "Cum Swallowing": "吞精", "Handjob": "手交",
    "Big Tits": "乳系", "Beautiful Tits": "乳系", "Small Tits": "贫乳", "Titty Fuck": "乳交",
    "Slender": "苗条", "Chubby": "丰满", "Beautiful Girl": "高颜值",
    "Office Lady": "秘书OL", "School Girls": "学生", "Nurse": "护士",
    "Uniform": "制服", "Cosplay": "角色扮演", "Maid": "女仆", "Swimsuit": "泳装",
    "Married Woman": "人妻", "Mature Woman": "人妻", "Big Tits Lover": "乳系",
    "Threesome / Foursome": "多人", "Orgy": "多人", "Lesbian": "百合",
    "Anal": "肛交", "Bondage": "调教", "Torture": "调教", "Training": "调教",
    "Slut": "痴女", "Nymphomaniac": "痴女", "Cuckold": "绿帽NTR", "Voyeur": "偷拍偷窥",
    "Hidden Camera": "偷拍偷窥", "Amateur": "素人", "Massage": "按摩", "Bath": "浴室",
    "Outdoor": "户外露出", "Car Sex": "车震", "Ass Lover": "美臀", "Butt": "美臀",
    "Glasses": "眼镜", "Virtual Reality": "VR", "POV": "主观视角", "Restraint": "调教",
    "Incest": "近亲", "Cheating Wife": "绿帽NTR", "4K": "4K",
    "Digital Mosaic": "有码", "Cowgirl": "骑乘",
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


def normalise(code: str) -> str:
    """Normalize only the movie-code spellings Peach explicitly accepts."""
    value = str(code or "").upper().replace("_", "-").replace(" ", "-").strip()
    if value.startswith("FC2"):
        digits = re.search(r"(\d{5,})", value)
        return f"FC2-PPV-{digits.group(1)}" if digits else value
    shape = re.match(r"^(\d{3})?([A-Z]+)-?(\d+)$", value)
    if not shape:
        return value
    digits = str(int(shape.group(3))).zfill(3)
    return f"{shape.group(1) or ''}{shape.group(2)}-{digits}"


def _is_explicit_code(code: str) -> bool:
    value = str(code or "").upper().strip()
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
    if field in {"studio", "series", "release_date"}:
        if field == "release_date" and field not in {
            str(row[1]) for row in connection.execute("PRAGMA table_info(asset)")
        }:
            return []
        rows = connection.execute(
            f"SELECT DISTINCT trim({field}) FROM asset WHERE medium='video' "
            f"AND upper(trim(code))=upper(?) AND {field} IS NOT NULL AND trim({field})<>''",
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
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        value = raw.split("#", 1)[0].strip()
        if not value:
            continue
        query = normalise(value)
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
        query = normalise(code)
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
        **{field: 0 for field in PEACH_FIELDS},
        "last_error_kind": "", "last_error_status": "", "last_error_message": "",
    } for source in policy.sources}


def _write_health(path: Path, rows: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEALTH_FIELDS)
        writer.writeheader()
        for source in rows:
            writer.writerow(rows[source])
    os.replace(temporary, path)


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
    if args.limit:
        codes = codes[:max(args.limit, 0)]
    log(f"字段候选批次：profile {policy.profile}，番号 {len(codes)}，来源 {','.join(sources)}；只读查询，不写 ledger")

    blocked_sources: set[str] = set()
    groups_written = errors_written = 0
    stopped: JobPolicyError | None = None
    with output.open("w", encoding="utf-8-sig", newline="") as candidate_handle, \
            errors_path.open("w", encoding="utf-8-sig", newline="") as error_handle:
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
            query = normalise(code)
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
                source_health["succeeded"] += 1
                if not extracted_fields:
                    source_health["empty"] += 1
                for field, extracted in extracted_fields.items():
                    source_health[field] += 1
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
                        "value": extracted["value"],
                        "display_value": extracted["display_value"],
                        "warnings": extracted["warnings"],
                        "raw_snapshot": str(snapshot),
                    }
                    by_field.setdefault(field, []).append(candidate)
                # 续跑重建候选时会读取数百个本地快照；它们没有网络请求，不该
                # 消耗来源限流窗口。只给本次真实 fetch 留间隔，既保持 r18dev
                # 的长跑节流，也让熔断后的恢复立即越过已完成部分。
                if args.delay > 0 and not reused:
                    time.sleep(args.delay + random.uniform(0, min(0.4, args.delay / 3)))
            for field, candidates in by_field.items():
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
