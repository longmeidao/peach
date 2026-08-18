#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""按番号抓官方封套：把所有候选量一遍，留像素最多的那张。

**不用固定优先级链**，因为实测证明没有哪个源恒定最好：

    GYAN-017   awsimgsrc 2184x1464   有数字版，DMM 自己的高清路径最好
    ABW-232    duga      1000x674    没有数字版，awsimgsrc 四种写法全 404
    PPT-018    pics.dmm   800x539    只有低清

同一个 DMM 有两条路径，差 7.4 倍像素——之前一直用的是低清那条：

    低清  pics.dmm.co.jp/mono/movie/adult/<cid>/<cid>pl.jpg            800x539
    高清  awsimgsrc.dmm.co.jp/pics_dig/digital/video/<cid>/<cid>pl.jpg 2184x1464

候选来自两处：`awsimgsrc` 按 `content_id` 构造（r18.dev 提供 cid），以及 avbase 的
作品页——它一次请求就同时给出 duga、pics.dmm、mgstage 三个主机的图。

两条番号改写规则，都由实测得出：

- cid 数字段必须补到 5 位。`waaa415` 404，`waaa00415` 命中 2184x1468。
- 素人系要去掉三位厂牌前缀。`278GYAN-017` 查不到，`GYAN-017` 能查到。

为省流量，先用 Range 只取前 64 KiB 量尺寸，只有胜出的那张才整张下载。

存原图不裁：4:3 与 16:9 两种版式在界面上靠 `object-fit` / `object-position` 取景，
切版式零成本也不重新下载。官方那张独立正封 `ps.jpg` 只有 147x200，比裁出来的还小。
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sqlite3
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, UnidentifiedImageError

from peach.config import COVER_DIR, DATABASE_PATH, GENERATED_DIR
from peach.http import HttpRequest, HttpTransport, HttpxTransport
from peach.web_contract import is_jav_code

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
AWS_HIRES = "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/{cid}/{cid}pl.jpg"
AVBASE_WORK = "https://www.avbase.net/works/{code}"
R18_DETAIL = "https://r18.dev/videos/vod/movies/detail/-/dvd_id={code}/json"

#: 低于这个宽度的是缩略图或占位图，不当封套。实测最低的正片封套是 800 宽。
MIN_WIDTH = 700
#: 量尺寸只需要 JPEG 头部，别把整张 1 MB 的图拉下来。
PROBE_BYTES = 64 * 1024
#: avbase 页面里混着剧照与缩略图，按文件名排除。
THUMBNAIL = re.compile(r"(thumb|small|icon|/ts/|-s\d|_s\.)", re.I)
IMAGE_URL = re.compile(r"https?://[^\"'\\ )]+?\.(?:jpg|jpeg|png|webp)")


@dataclass(frozen=True)
class Candidate:
    source: str
    url: str


class Unavailable(RuntimeError):
    pass


def _fetch(transport: HttpTransport, url: str, *, referer: str,
           limit: int, ranged: bool = False) -> bytes:
    headers = {"User-Agent": UA, "Referer": referer,
               "Accept-Language": "ja,en;q=0.9"}
    if ranged:
        headers["Range"] = f"bytes=0-{PROBE_BYTES - 1}"
    response = transport(HttpRequest("GET", url, headers), 30, limit)
    if response.status not in (200, 206):
        raise Unavailable(f"HTTP {response.status}")
    return response.body


def normalise_code(code: str) -> str:
    """`abw232` / `ABW-0232` 一律归一成 `ABW-232`，与 scrape_codes 同口径。"""
    value = (code or "").upper().replace("_", "-").replace(" ", "-").strip()
    if value.startswith("FC2"):
        digits = re.search(r"(\d{5,})", value)
        return f"FC2-PPV-{digits.group(1)}" if digits else value
    shape = re.match(r"^(\d{3})?([A-Z]+)-?(\d+)$", value)
    if not shape:
        return value
    prefix = shape.group(1) or ""
    return f"{prefix}{shape.group(2)}-{int(shape.group(3)):03d}"


def code_variants(code: str) -> list[str]:
    """素人系番号带三位厂牌前缀，去掉才查得到：`278GYAN-017` -> `GYAN-017`。"""
    value = normalise_code(code)
    out = [value]
    stripped = re.sub(r"^\d{3}(?=[A-Z])", "", value)
    if stripped != value:
        out.append(stripped)
    return out


def cid_variants(content_id: str) -> list[str]:
    """数字段补到 5 位是必须的；带厂牌数字前缀的多半没有数字版，但仍试一次。"""
    cid = (content_id or "").strip().lower()
    if not cid:
        return []
    out = [cid]
    shape = re.match(r"^(\d{2,4})?([a-z]+)(\d+)$", cid)
    if shape:
        letters, digits = shape.group(2), shape.group(3)
        out.append(f"{letters}{int(digits):05d}")
        out.append(f"{letters}{digits}")
    seen: set[str] = set()
    return [c for c in out if not (c in seen or seen.add(c))]


def content_ids(transport: HttpTransport, code: str) -> list[str]:
    for variant in code_variants(code):
        try:
            import json
            payload = json.loads(_fetch(
                transport, R18_DETAIL.format(code=urllib.parse.quote(variant)),
                referer="https://r18.dev/", limit=2 * 1024 * 1024,
            ).decode("utf-8", "ignore"))
        except (Unavailable, ValueError):
            continue
        cid = payload.get("content_id") or ""
        if cid:
            return cid_variants(cid)
    return []


def avbase_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """avbase 一次请求给出 duga / pics.dmm / mgstage 三个主机的图。"""
    for variant in code_variants(code):
        try:
            page = _fetch(transport, AVBASE_WORK.format(code=urllib.parse.quote(variant)),
                          referer="https://www.avbase.net/", limit=4 * 1024 * 1024,
                          ).decode("utf-8", "ignore")
        except Unavailable:
            continue
        found: list[Candidate] = []
        seen: set[str] = set()
        for url in IMAGE_URL.findall(page):
            if THUMBNAIL.search(url) or url in seen:
                continue
            seen.add(url)
            found.append(Candidate(urlparse(url).netloc, url))
        if found:
            return found
    return []


def probe_size(transport: HttpTransport, candidate: Candidate) -> tuple[int, int]:
    head = _fetch(transport, candidate.url, referer="https://www.avbase.net/",
                  limit=PROBE_BYTES * 2, ranged=True)
    return Image.open(io.BytesIO(head)).size


def best_cover(transport: HttpTransport, code: str, delay: float
               ) -> tuple[Candidate, tuple[int, int], bytes]:
    # 来源一律记主机名。构造的和 avbase 发现的常是同一个主机，记成两个名字会让
    # 覆盖率统计凭空多出一个「渠道」。
    candidates: list[Candidate] = [
        Candidate(urlparse(AWS_HIRES).netloc, AWS_HIRES.format(cid=cid))
        for cid in content_ids(transport, code)
    ]
    time.sleep(delay)
    candidates += avbase_images(transport, code)
    if not candidates:
        raise Unavailable("所有渠道都没有候选")

    measured: list[tuple[int, Candidate, tuple[int, int]]] = []
    for candidate in candidates:
        try:
            width, height = probe_size(transport, candidate)
        except (Unavailable, UnidentifiedImageError, OSError):
            continue
        finally:
            time.sleep(delay)
        if width >= MIN_WIDTH:
            measured.append((width * height, candidate, (width, height)))
    if not measured:
        raise Unavailable("候选都不是可用封套")

    _, winner, size = max(measured, key=lambda item: item[0])
    data = _fetch(transport, winner.url, referer="https://www.avbase.net/",
                  limit=16 * 1024 * 1024)
    return winner, size, data


FIELDS = ("code", "result", "source", "width", "height", "kb", "url", "note")


def pending(database: Path, root: Path, only_shaped: bool) -> list[str]:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT code, COUNT(*) FROM asset WHERE medium='video' "
            "AND code IS NOT NULL AND code<>'' GROUP BY code ORDER BY 2 DESC"
        ).fetchall()
    finally:
        connection.close()
    result = []
    for code, _count in rows:
        # 判形态必须看原值。`normalise_code` 会补上分隔符，把 `RAIKUN325`
        # （myfans 账号名，241 个文件）改写成 `RAIKUN-325` 并通过形态检查，
        # 于是队列里全是查不到的账号名。判据与 web_contract 共用一份实现。
        if only_shaped and not is_jav_code(str(code)):
            continue
        # FC2 在 r18/avsox/javbus 三源实测零命中（见 HANDOFF），本抓取器用的是
        # 同一批来源。默认跳过 400 个必然落空的请求；`--all-codes` 仍可强制尝试。
        if only_shaped and str(code).upper().startswith("FC2"):
            continue
        key = normalise_code(str(code))
        if not (root / f"{key}.jpg").is_file():
            result.append(key)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按番号抓最高清的官方封套")
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--out", type=Path, default=COVER_DIR)
    parser.add_argument("--log", type=Path,
                        default=GENERATED_DIR / "cover-fetch-log.csv")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--all-codes", action="store_true",
                        help="连 FC2/日期番号一起试；默认只跑片商与素人形态")
    return parser


def _write_log(path: Path, rows: list[dict]) -> None:
    """每条都落盘：这个任务要跑三四个小时，只在结束时写等于全程看不见进度。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> int:
    args.out.mkdir(parents=True, exist_ok=True)
    todo = pending(args.db, args.out, not args.all_codes)
    if args.limit:
        todo = todo[:args.limit]
    print(f"待抓番号 {len(todo)} 个（已存在的跳过）")

    transport = HttpxTransport()
    rows: list[dict] = []
    stats = {"ok": 0, "miss": 0}
    try:
        for index, code in enumerate(todo, 1):
            try:
                winner, (width, height), data = best_cover(transport, code, args.delay)
            # 网络异常必须按条吞掉。一次 SSL 抖动
            # （httpx.ConnectError: UNEXPECTED_EOF_WHILE_READING）此前直接打死了
            # 整个三小时的任务，而且死得很安静——日志停在半路，看起来像跑完了。
            # 长跑批处理不能因为一个番号的连接问题就整体退出。
            # `Exception` 已涵盖 Unavailable 与网络异常；Ctrl-C 是 BaseException
            # 的另一支，不会被这里吞掉，仍能正常中断。
            except Exception as exc:
                stats["miss"] += 1
                rows.append({"code": code, "result": "未取得", "source": "",
                             "width": "", "height": "", "kb": "", "url": "",
                             "note": f"{type(exc).__name__}: {exc}"[:80]})
                print(f"[{index}/{len(todo)}] 未取得 {code}：{type(exc).__name__} {exc}",
                      flush=True)
                continue
            target = args.out / f"{code}.jpg"
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(target)
            stats["ok"] += 1
            rows.append({"code": code, "result": "取得", "source": winner.source,
                         "width": width, "height": height, "kb": len(data) // 1024,
                         "url": winner.url, "note": ""})
            print(f"[{index}/{len(todo)}] {code}  {width}x{height} "
                  f"{len(data)//1024} KB  <- {winner.source}", flush=True)
            _write_log(args.log, rows)
    finally:
        transport.close()
        _write_log(args.log, rows)

    print(f"\n取得 {stats['ok']}，未取得 {stats['miss']} → {args.out}")
    print(f"逐条记录 → {args.log}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
