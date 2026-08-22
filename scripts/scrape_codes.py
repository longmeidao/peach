#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番号刮削 —— 给 ledger 里带 code 的资产补女优、厂牌、内容标签。

输入直接来自 ledger（不依赖任何中间 CSV）；结果写回 ledger，
并落一份 CSV 到 generated/ 供人工核对。

多源级联（单源必被限流，实测 javbus 打到第 25 个就 403）：
  1. r18.dev   JSON API，无 Cloudflare，有码主力，附带 categories 可直接转标签
  2. avsox     无码 / FC2 主力
  3. javbus    兜底，易 403，带 5 分钟冷却

可随时中断重启：CSV 里已有的番号直接跳过。
只写 asset.studio / asset.creator（当其为空时）与 asset_tag(source='r18')，
不覆盖已有的人工或视觉标注。

用法:
    python scripts/scrape_codes.py [--limit N] [--delay 1.2] [--apply]
    不带 --apply 只抓取并落 CSV，不写库。
"""
from __future__ import annotations

import csv
import argparse
import json
import os
import random
import re
import sqlite3
import time
import urllib.parse

from bs4 import BeautifulSoup

from peach.entities import canonicalize_entity_name, normalize_entity_name, upsert_asset_entity
from peach.http import HttpRequest, HttpTransport, HttpxTransport

DEFAULT_DB = r"R:\peach-data\database\ledger.db"
DEFAULT_OUT = r"R:\peach-data\generated\code-scrape.csv"
DEFAULT_LOG_DIR = r"R:\peach-data\logs"
_logf = None


def configure_log(log_dir: str) -> None:
    global _logf
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, time.strftime("scrape-codes-%Y%m%d-%H%M%S.log"))
    _logf = open(path, "w", encoding="utf-8", buffering=1)


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if _logf is not None:
        _logf.write(line + "\n")


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


class SourceHttpError(RuntimeError):
    def __init__(self, status: int):
        super().__init__(f"source returned HTTP {status}")
        self.status = status


def _get(
    url: str,
    headers: dict | None = None,
    timeout: int = 25,
    transport: HttpTransport | None = None,
) -> str:
    hdrs = {"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8"}
    hdrs.update(headers or {})
    owns_transport = transport is None
    http = transport or HttpxTransport()
    try:
        response = http(HttpRequest("GET", url, hdrs), timeout, 8 * 1024 * 1024)
        if response.status < 200 or response.status >= 300:
            raise SourceHttpError(response.status)
        return response.body.decode("utf-8", "ignore")
    finally:
        if owns_transport and isinstance(http, HttpxTransport):
            http.close()


def _name_of(value) -> str:
    if isinstance(value, dict):
        return value.get("name", "") or ""
    return value or ""


BLANK = {"performers": "", "studio": "", "label": "", "series": "",
         "title": "", "categories": "", "source": ""}


def from_r18(code: str, transport: HttpTransport | None = None) -> dict | None:
    payload = json.loads(_get(
        "https://r18.dev/videos/vod/movies/detail/-/dvd_id="
        f"{urllib.parse.quote(code)}/json", transport=transport))
    actors = [a.get("name", "").strip() for a in (payload.get("actresses") or []) if a.get("name")]
    if not actors and not payload.get("maker"):
        return None
    return {
        "performers": "|".join(actors),
        "studio": _name_of(payload.get("maker")),
        "label": _name_of(payload.get("label")),
        "series": _name_of(payload.get("series")),
        "title": (payload.get("title") or "")[:200],
        "categories": "|".join(c.get("name", "") for c in (payload.get("categories") or []))[:300],
        "source": "r18",
    }


def _linked_value(soup: BeautifulSoup, labels: tuple[str, ...]) -> str:
    label = soup.find(string=lambda value: bool(value) and any(name in value for name in labels))
    if label is None:
        return ""
    for parent in label.parents:
        link = parent.find("a", href=True)
        if link is not None:
            return link.get_text(" ", strip=True)
        if parent.name in {"body", "html"}:
            break
    return ""


def avsox_movie_url(html: str, base_url: str = "https://avsox.click") -> str:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one('a[href*="/cn/movie/"]')
    return urllib.parse.urljoin(base_url, link.get("href", "")) if link else ""


def parse_avsox(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    actors = [node.get_text(" ", strip=True) for node in soup.select(".avatar-box span")]
    maker = _linked_value(soup, ("制作商", "製作商"))
    title = soup.find("h3")
    if not (actors or maker):
        return None
    out = dict(BLANK)
    out.update({
        "performers": "|".join(dict.fromkeys(a for a in actors if a)),
        "studio": maker,
        "title": title.get_text(" ", strip=True)[:200] if title else "",
        "source": "avsox",
    })
    return out


def from_avsox(code: str, transport: HttpTransport | None = None) -> dict | None:
    search = _get(
        "https://avsox.click/cn/search/" + urllib.parse.quote(code), transport=transport,
    )
    url = avsox_movie_url(search)
    return parse_avsox(_get(url, transport=transport)) if url else None


def _clean_performer_names(values) -> list[str]:
    names: dict[str, str] = {}
    for value in values:
        name = canonicalize_entity_name("performer", value)
        if not name:
            continue
        names.setdefault(normalize_entity_name(name), name)
    return list(names.values())


def parse_javbus(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    actors = _clean_performer_names(
        node.get_text(" ", strip=True) for node in soup.select(".star-name")
    )
    if not actors:
        actors = _clean_performer_names(
            node.get_text(" ", strip=True) for node in soup.select('a[href*="/star/"]')
        )
    out = dict(BLANK)
    out["performers"] = "|".join(actors)
    out["studio"] = _linked_value(soup, ("製作商", "制作商"))
    out["label"] = _linked_value(soup, ("發行商", "发行商"))
    out["series"] = _linked_value(soup, ("系列",))
    title = soup.find("h3")
    if title:
        out["title"] = title.get_text(" ", strip=True)[:200]
    out["source"] = "javbus"
    return out if (out["performers"] or out["studio"]) else None


def from_javbus(code: str, transport: HttpTransport | None = None) -> dict | None:
    page = _get(
        "https://www.javbus.com/" + urllib.parse.quote(code),
        headers={"Cookie": "existmag=all"},
        transport=transport,
    )
    return parse_javbus(page)


def normalise(code: str) -> str:
    """FC2PPV-1234567 → FC2-PPV-1234567 ; ABW123 → ABW-123 ; IPVR00296 → IPVR-296"""
    value = code.upper().replace("_", "-").replace(" ", "-")
    if value.startswith("FC2"):
        digits = re.search(r"(\d{5,})", value)
        return f"FC2-PPV-{digits.group(1)}" if digits else value
    shape = re.match(r"^([A-Z]+)-?(\d+)$", value)
    if not shape:
        return value
    digits = shape.group(2)
    if len(digits) > 3 and digits.startswith("0"):
        digits = digits.lstrip("0").zfill(3)
    return f"{shape.group(1)}-{digits}"


def chain(code: str):
    """FC2 / 无码走 avsox 优先，其余 r18 优先。"""
    if code.startswith("FC2") or re.match(r"^\d{6}[-_]\d{3}$", code):
        return (("avsox", from_avsox), ("javbus", from_javbus), ("r18", from_r18))
    return (("r18", from_r18), ("avsox", from_avsox), ("javbus", from_javbus))


# r18 分类 → 本地内容标签（只映射有意义的，其余丢弃）
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
    "Incest": "近亲", "Cheating Wife": "绿帽NTR",
}

FIELDS = ["code", "query", "performers", "studio", "label", "series",
          "title", "categories", "source", "status", "size_gb", "videos"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="scrape code metadata into a review CSV")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=1.2)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-fc2", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    configure_log(args.log_dir)
    conn = sqlite3.connect("file:" + os.path.abspath(args.db).replace("\\", "/") + "?mode=ro", uri=True)
    codes = [(row[0].upper().strip(), float(row[1]), int(row[2])) for row in conn.execute(
        "SELECT code, COALESCE(sum(size),0)/1073741824.0, count(*) FROM asset "
        "WHERE medium='video' AND code IS NOT NULL AND code<>'' "
        "GROUP BY code ORDER BY 2 DESC")]
    conn.close()

    done: set[str] = set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8-sig") as handle:
            done = {row["code"] for row in csv.DictReader(handle)}
        log(f"已有结果 {len(done)} 条，跳过")

    todo = [c for c in codes if c[0] not in done]
    if not args.include_fc2:
        before = len(todo)
        todo = [c for c in todo if not c[0].upper().startswith("FC2")]
        if before != len(todo):
            log(f"跳过 {before - len(todo)} 个 FC2（历史命中率 0%，要跑加 --include-fc2）")
    if args.limit:
        todo = todo[:args.limit]
    log(f"库里番号 {len(codes)} 个，待查 {len(todo)} 个，间隔 {args.delay}s，"
        f"预计 {len(todo) * args.delay * 1.4 / 60:.0f} 分钟")

    handle = open(args.out, "a", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if not done:
        writer.writeheader()

    cooldown: dict[str, float] = {}
    hit = miss = 0
    by_source: dict[str, int] = {}
    started = time.time()

    http = HttpxTransport()
    try:
        for index, (code, size_gb, videos) in enumerate(todo, 1):
            query = normalise(code)
            record = dict(BLANK)
            record.update({"code": code, "query": query, "status": "",
                           "size_gb": round(size_gb, 2), "videos": videos})
            for source_name, fetch in chain(query):
                if time.time() < cooldown.get(source_name, 0):
                    continue
                try:
                    found = fetch(query, http)
                except SourceHttpError as exc:
                    if exc.status in (403, 429, 503):
                        cooldown[source_name] = time.time() + 300
                        log(f"  {source_name} 限流 {exc.status}，冷却 5 分钟")
                    continue
                except Exception:
                    continue
                if found:
                    record.update(found)
                    record["status"] = "ok" if found["performers"] else "no_actress"
                    by_source[source_name] = by_source.get(source_name, 0) + 1
                    break
                time.sleep(0.4)
            if record["performers"]:
                hit += 1
            else:
                miss += 1
                record["status"] = record["status"] or "not_found"
            writer.writerow(record)
            handle.flush()
            if index % 25 == 0:
                elapsed = time.time() - started
                log(f"{index}/{len(todo)}  命中 {hit}  未果 {miss}  "
                    f"剩余 {(len(todo) - index) * elapsed / index / 60:.0f} 分钟  源:{by_source}")
            time.sleep(args.delay + random.uniform(0, 0.5))
    finally:
        http.close()

    handle.close()
    total = hit + miss
    log(f"完成：查 {total} 个，拿到女优 {hit} 个"
        f"（{hit / max(total, 1) * 100:.0f}%）  源分布:{by_source}")
    log(f"→ {args.out}")

    if not args.apply:
        log("未加 --apply，只落 CSV 未写库。")
        return 0

    return write_back(args.db, args.out)


def write_back(db_path: str = DEFAULT_DB, out_path: str = DEFAULT_OUT) -> int:
    """把已复核 CSV 双写为兼容投影和规范实体关系。"""
    with open(out_path, encoding="utf-8-sig") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("status") in ("ok", "no_actress")]
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    cur = conn.cursor()
    studios = performers = series_count = tags = 0
    for row in rows:
        code = row["code"]
        ids = [r[0] for r in cur.execute(
            "SELECT id FROM asset WHERE medium='video' AND code=?", (code,))]
        if not ids:
            continue
        marks = ",".join("?" * len(ids))
        if row.get("studio"):
            studios += cur.execute(
                f"UPDATE asset SET studio=? WHERE id IN ({marks}) "
                "AND (studio IS NULL OR studio='')",
                [row["studio"], *ids]).rowcount
        performer_names = _clean_performer_names(
            (row.get("performers") or "").split("|")
        )
        lead = performer_names[0] if performer_names else ""
        if lead:
            performers += cur.execute(
                f"UPDATE asset SET creator=? WHERE id IN ({marks}) "
                "AND (creator IS NULL OR creator='')",
                [lead, *ids]).rowcount
        if row.get("series"):
            series_count += cur.execute(
                f"UPDATE asset SET series=? WHERE id IN ({marks}) "
                "AND (series IS NULL OR series='')",
                [row["series"], *ids]).rowcount
        mapped = [CATEGORY_MAP[c] for c in (row.get("categories") or "").split("|")
                  if c in CATEGORY_MAP]
        mapped = list(dict.fromkeys(mapped))
        if mapped:
            cur.executemany(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                "VALUES(?,?,?,?)",
                [(aid, tag, 0.9, "r18") for aid in ids for tag in mapped])
            tags += len(ids) * len(mapped)
        source = row.get("source") or "external"
        metadata = {"code": code, "query": row.get("query", ""), "source": source}
        for aid in ids:
            upsert_asset_entity(
                conn, kind="studio", name=row.get("studio"), asset_id=aid,
                role="studio", source=f"{source}:studio", confidence=0.9,
                metadata=metadata,
            )
            upsert_asset_entity(
                conn, kind="series", name=row.get("series"), asset_id=aid,
                role="series", source=f"{source}:series", confidence=0.9,
                metadata=metadata,
            )
            for name in performer_names:
                cur.execute(
                    "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) "
                    "VALUES(?,?,?,?)", (aid, "演员:" + name, 0.9, f"{source}:performer"),
                )
                upsert_asset_entity(
                    conn, kind="performer", name=name, asset_id=aid,
                    role="performer", source=f"{source}:performer", confidence=0.9,
                    metadata=metadata,
                )
            for tag in mapped:
                upsert_asset_entity(
                    conn, kind="tag", name=tag, asset_id=aid, role="tag",
                    source="r18", confidence=0.9, metadata=metadata,
                )
    conn.commit()
    log(f"写回 ledger：厂牌 {studios} 行，创作者 {performers} 行，"
        f"系列 {series_count} 行，标签约 {tags} 条")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
