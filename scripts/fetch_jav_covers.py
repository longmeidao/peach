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
import json
import re
import sqlite3
import time
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, UnidentifiedImageError

from peach.config import COVER_DIR, DATABASE_PATH, GENERATED_DIR
from peach.http import HttpRequest, HttpTransport, HttpxTransport
from peach.jobs import DiskGuard, JobPolicyError
from peach.platform import system_volume
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
AVBASE_MAIN_CLASSES = frozenset(("max-h-[28rem]", "max-w-full"))


@dataclass(frozen=True)
class Candidate:
    source: str
    url: str
    referer: str = "https://www.avbase.net/"


class Unavailable(RuntimeError):
    pass


class _AvbaseMainCoverParser(HTMLParser):
    """只读取作品页主封面，拒绝相关推荐、剧照和演员头像。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        values = dict(attrs)
        classes = frozenset((values.get("class") or "").split())
        if not AVBASE_MAIN_CLASSES.issubset(classes):
            return
        url = values.get("src") or values.get("data-src")
        if url and IMAGE_URL.fullmatch(url):
            self.urls.append(url)


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


def r18_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """读取 r18 返回的官方封套，并保留旧数字版高清 URL 探测。

    `content_id` 不是稳定的数字版路径。Prestige 的 ABW 系列会返回
    `118abw232`，对应 `pics.dmm.co.jp/mono/.../118abw232pl.jpg`；把它补零后
    拼到 `awsimgsrc.../digital/video` 只会得到 404。r18 已在
    `images.jacket_image` 给出官方原图 URL，必须优先把这个证据加入候选。
    """
    for variant in code_variants(code):
        try:
            payload = json.loads(_fetch(
                transport, R18_DETAIL.format(code=urllib.parse.quote(variant)),
                referer="https://r18.dev/", limit=2 * 1024 * 1024,
            ).decode("utf-8", "ignore"))
        except (Unavailable, ValueError):
            continue
        found: list[Candidate] = []
        jacket = ((payload.get("images") or {}).get("jacket_image") or {})
        if isinstance(jacket, dict):
            for raw_url in jacket.values():
                url = raw_url.strip() if isinstance(raw_url, str) else ""
                if url and IMAGE_URL.fullmatch(url) and not THUMBNAIL.search(url):
                    found.append(Candidate(urlparse(url).netloc, url, "https://r18.dev/"))
        cid = str(payload.get("content_id") or "")
        found.extend(
            Candidate(urlparse(AWS_HIRES).netloc, AWS_HIRES.format(cid=value),
                      "https://r18.dev/")
            for value in cid_variants(cid)
        )
        seen: set[str] = set()
        return [candidate for candidate in found
                if not (candidate.url in seen or seen.add(candidate.url))]
    return []


def avbase_images(transport: HttpTransport, code: str) -> list[Candidate]:
    """读取 avbase 当前作品的主封面，不扫描整页关联作品图片。"""
    for variant in code_variants(code):
        try:
            page = _fetch(transport, AVBASE_WORK.format(code=urllib.parse.quote(variant)),
                          referer="https://www.avbase.net/", limit=4 * 1024 * 1024,
                          ).decode("utf-8", "ignore")
        except Unavailable:
            continue
        parser = _AvbaseMainCoverParser()
        parser.feed(page)
        found: list[Candidate] = []
        seen: set[str] = set()
        for url in parser.urls:
            if THUMBNAIL.search(url) or url in seen:
                continue
            seen.add(url)
            found.append(Candidate(urlparse(url).netloc, url))
        if found:
            return found
    return []


def probe_size(transport: HttpTransport, candidate: Candidate) -> tuple[int, int]:
    head = _fetch(transport, candidate.url, referer=candidate.referer,
                  limit=PROBE_BYTES * 2, ranged=True)
    return Image.open(io.BytesIO(head)).size


def best_cover(transport: HttpTransport, code: str, delay: float
               ) -> tuple[Candidate, tuple[int, int], bytes]:
    # 来源一律记主机名。构造的和 avbase 发现的常是同一个主机，记成两个名字会让
    # 覆盖率统计凭空多出一个「渠道」。
    candidates = r18_images(transport, code)
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
    data = _fetch(transport, winner.url, referer=winner.referer,
                  limit=16 * 1024 * 1024)
    return winner, size, data


FIELDS = ("code", "result", "source", "width", "height", "kb", "url", "note")


#: 判定为「所有渠道都没有」的落空，续跑时不必重来；连接类失败必须重试。
#: 三态口径：一次超时不等于确认没有，不能靠它把番号永久踢出队列。
TRANSIENT = re.compile(r"(Error|Timeout|SSL|Connect|Proxy|Protocol)", re.I)


def settled_misses(log: Path) -> set[str]:
    """上一轮已经把所有源探完、确认没有封套的番号。

    这类落空是最贵的：每条都要把全部候选源挨个试完才能确定。实测 194 条里
    150 条落空，重探一遍就是好几个小时，而结论不会变。
    """
    rows = logged_rows(log)
    return {str(row.get("code") or "").strip() for row in rows
            if row.get("result") == "未取得"
            and not TRANSIENT.search(str(row.get("note") or ""))
            and str(row.get("code") or "").strip()}


def carried_rows(log: Path, keep: set[str]) -> list[dict]:
    """把这轮跳过的番号的上轮记录原样带进新日志。"""
    if not keep:
        return []
    return [{field: row.get(field, "") for field in FIELDS}
            for row in logged_rows(log)
            if str(row.get("code") or "").strip() in keep]


def logged_rows(log: Path) -> list[dict]:
    if not log.is_file():
        return []
    with log.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def restore_logged_successes(transport: HttpTransport, log: Path, root: Path,
                             delay: float = 0.0, guard: DiskGuard | None = None) -> dict:
    """Re-download missing covers from the exact successful URLs already in the audit log.

    This is intentionally narrower than a fresh scrape: it makes no discovery requests,
    preserves the existing audit log and refuses an upstream image whose dimensions changed.
    """
    root.mkdir(parents=True, exist_ok=True)
    restored = skipped = 0
    failed: list[dict[str, str]] = []
    successes = [row for row in logged_rows(log)
                 if row.get("result") == "取得" and row.get("code") and row.get("url")]
    for index, row in enumerate(successes, 1):
        if guard is not None:
            guard.check()
        code = normalise_code(str(row["code"]))
        target = root / f"{code}.jpg"
        if target.is_file():
            skipped += 1
            continue
        temporary = target.with_suffix(".restore.tmp")
        try:
            data = _fetch(transport, str(row["url"]), referer="https://www.avbase.net/",
                          limit=16 * 1024 * 1024)
            with Image.open(io.BytesIO(data)) as image:
                size = image.size
                image.verify()
            expected = (int(row["width"]), int(row["height"]))
            if size != expected or size[0] < MIN_WIDTH:
                raise Unavailable(f"尺寸变化：日志 {expected[0]}x{expected[1]}，当前 {size[0]}x{size[1]}")
            temporary.write_bytes(data)
            temporary.replace(target)
            restored += 1
            print(f"[{index}/{len(successes)}] 恢复 {code}  {size[0]}x{size[1]}", flush=True)
        # 与完整抓取同一条长跑边界：单张网络异常降级成失败记录，不能让余下恢复归零；
        # KeyboardInterrupt 等 BaseException 仍会正常中断。
        except Exception as exc:
            failed.append({"code": code, "error": f"{type(exc).__name__}: {exc}"[:120]})
            print(f"[{index}/{len(successes)}] 未恢复 {code}：{type(exc).__name__} {exc}",
                  flush=True)
        finally:
            temporary.unlink(missing_ok=True)
            if delay:
                time.sleep(delay)
    return {"logged": len(successes), "restored": restored, "skipped": skipped,
            "failed": failed}


def pending(database: Path, root: Path, only_shaped: bool,
            location: str | None = None) -> list[str]:
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        location_sql = " AND location=?" if location else ""
        parameters: tuple[object, ...] = (location,) if location else ()
        rows = connection.execute(
            "SELECT code, COUNT(*) FROM asset WHERE medium='video' "
            "AND code IS NOT NULL AND code<>''" + location_sql
            + " GROUP BY code ORDER BY 2 DESC",
            parameters,
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
    parser.add_argument("--min-free", type=float, default=40.0,
                        help="系统盘最低可用 GiB；运行中每隔一段时间复查")
    parser.add_argument("--disk-check-secs", type=float, default=20.0)
    parser.add_argument("--location",
                        help="只抓指定来源的番号封套，例如 pikpak；封套仍按番号共享")
    parser.add_argument("--retry-misses", action="store_true",
                        help="连上轮确认没有封套的番号也重探一遍")
    parser.add_argument("--restore-successes", action="store_true",
                        help="只按成功日志中的原 URL 恢复缺失封套，不重新探测来源")
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
    guard = DiskGuard(system_volume(), args.min_free, args.disk_check_secs)
    try:
        free_gb = guard.check(force=True)
    except JobPolicyError as exc:
        print(f"[stop] {exc}")
        return exc.exit_code
    print(f"系统盘可用 {free_gb:.1f} GiB，运行期阈值 {args.min_free:.1f} GiB")
    if args.restore_successes:
        transport = HttpxTransport()
        try:
            result = restore_logged_successes(
                transport, args.log, args.out, args.delay, guard=guard,
            )
        except JobPolicyError as exc:
            print(f"[stop] {exc}")
            return exc.exit_code
        finally:
            transport.close()
        print(f"成功日志 {result['logged']}，恢复 {result['restored']}，"
              f"已存在 {result['skipped']}，失败 {len(result['failed'])} → {args.out}")
        return 2 if result["failed"] else 0

    todo = pending(args.db, args.out, not args.all_codes, args.location)
    skipped = set()
    if not args.retry_misses:
        skipped = settled_misses(args.log) & set(todo)
        todo = [code for code in todo if code not in skipped]
    if args.limit:
        todo = todo[:args.limit]
    selected = set(todo)
    print(f"待抓番号 {len(todo)} 个（已落盘的跳过，"
          f"上轮确认没有的跳过 {len(skipped)} 个，--retry-misses 可重试）")

    transport = HttpxTransport()
    # 日志是整份重写：这轮只跑 pikpak 或只跑 --limit 时，未选中的旧记录也必须保留；
    # 只删除本轮会重新生成的番号。否则一次来源小批次就会抹掉其他来源的复核证据。
    rows: list[dict] = [
        {field: row.get(field, "") for field in FIELDS}
        for row in logged_rows(args.log)
        if str(row.get("code") or "").strip() not in selected
    ]
    stats = {"ok": 0, "miss": 0}
    stopped: JobPolicyError | None = None
    try:
        for index, code in enumerate(todo, 1):
            try:
                guard.check()
            except JobPolicyError as exc:
                stopped = exc
                print(f"[stop] {exc}", flush=True)
                break
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
            else:
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
            # 落空的行也要落盘。原来这句只在取得分支里，连续落空时 CSV 整段不动；
            # 被强杀时 finally 也来不及跑，那一串判定就白做了——而「查不到」恰恰
            # 是最贵的一类：每条都要把所有候选源挨个探完才能确定。
            _write_log(args.log, rows)
    finally:
        transport.close()
        _write_log(args.log, rows)

    print(f"\n取得 {stats['ok']}，未取得 {stats['miss']} → {args.out}")
    print(f"逐条记录 → {args.log}")
    return stopped.exit_code if stopped is not None else 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
