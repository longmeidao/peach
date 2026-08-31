#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""从 fc2cmadb 抓 FC2 作品元数据与评论区的人工标记。

FC2 没有 JAV 那样的番号体系，官方页面只有卖家自己填的标题，演员基本不写。
fc2cmadb 的价值不在正文而在**评论区**：那里有用户长期维护的两类标记。

演员标记，`<video_id>　<名前>`，全角空格分隔，一行可以有多个演员：

    2724256　未歩なな　皐月
    1934545　ゆう

等价标记，把同一段内容在不同 video_id 下的发布对应起来：

    3312576-4 = 2471432 = 3090722-1 = 4605413

等价关系是合集的判据，也是本脚本存在的主要理由。`FC2PPV-3312576` 是一个
21 段的合集，本地就按 `FC2PPV-3312576-1.mp4` 分片存着。**合集封面绝不能套给
每个分片**——那会让 21 个不同内容的视频显示同一张图。所以判定为合集时
`cover_url` 留空并在 note 里写明，让分片回落到自己的缩略图。

页面是 Laravel + Inertia，数据在 `<script type="application/json">` 里，
不用解析 HTML。需要登录：cookie 走 `--cookies` 传入沙盒里的 Netscape 文件，
绝不入库入仓。

评论是匿名用户写的，一律只作候选：产出 CSV 交人工复核，不碰真相字段。
同一个演员名被两条以上独立评论提到时置信度更高，写在 `performer_votes` 里。

**只抓库里有的作品页，但每页评论全量留存。** 一页评论往往给几十个 video_id
标了演员，本地只对上其中两三个；只留对得上的那几条，等于把评论区的价值丢掉。
所以产出三份：按本地资产的候选 CSV（复核页用）、按 video_id 汇总的全量收获
CSV、以及原始评论 JSONL。留原文是因为下面这些正则一定会漏掉某种写法，
有原文就不必为此重爬一遍。
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import sqlite3
import time
from pathlib import Path

import httpx

from peach.review_csv import write_rows
from peach.config import DATABASE_PATH, GENERATED_DIR

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
ARTICLE_URL = "https://fc2cmadb.com/articles/{video_id}"
#: Inertia 把整个 props 树放在这个 script 标签里，正文 HTML 反而是空壳。
PAGE_JSON = re.compile(r'type="application/json">(\{.*?\})</script>', re.S)
#: FC2 的 video_id 是 6-8 位纯数字，短于这个长度的多半是楼层号或年份。
VIDEO_ID = re.compile(r"\d{6,8}")
#: `2724256　未歩なな　皐月`：ID 开头，其后全是名字，中间只允许空白。
PERFORMER_LINE = re.compile(r"^(\d{6,8})[\s　]+(\S.*)$")
#: 等价项形如 `3312576-4`、`3312576_4`、`2471432`。
EQUIV_TOKEN = re.compile(r"(\d{6,8})(?:[-_](\d{1,2}))?")
#: 评论里用 `bad:` 起一段列对不上的分片，那之后的 `=` 不是等价断言。
BAD_HEADER = re.compile(r"^\s*bad\s*[:：]", re.I)
#: 另一种演员标记：一行名字，后面跟若干作品链接（多指向姊妹站 fc2ppvdb）。
ARTICLE_LINK = re.compile(r"https?://[\w.]*fc2(?:ppvdb|cmadb)\.com/articles/(\d{6,8})")
#: 日文输入法打出的是全角等号，占实际写法的一部分，不认就整条读不到。
FULLWIDTH = str.maketrans("＝－＿０１２３４５６７８９", "=-_0123456789")
#: 判定合集所需的最少分片映射数。一两条可能只是同一段内容的重复投稿。
COLLECTION_MIN_PARTS = 3


def load_cookies(path: Path) -> http.cookiejar.MozillaCookieJar:
    jar = http.cookiejar.MozillaCookieJar(str(path))
    jar.load(ignore_discard=True, ignore_expires=True)
    return jar


def parse_performers(body: str) -> dict[str, list[str]]:
    """取演员标记，返回 {video_id: [名字]}。两种写法都算数。

    行内式 `2724256　未歩なな`，以及「一行名字 + 若干作品链接」式——后者多指向
    姊妹站 fc2ppvdb，语义是同一个人的作品集，同样是人工攒出来的标记。
    """
    body = body.translate(FULLWIDTH)
    found: dict[str, list[str]] = {}
    linked = ARTICLE_LINK.findall(body)
    if linked:
        heads = [line.strip() for line in body.splitlines()
                 if line.strip() and not line.strip().startswith("http")
                 and not VIDEO_ID.search(line) and "=" not in line]
        if len(heads) == 1:
            for video_id in linked:
                found.setdefault(video_id, []).append(heads[0])
    for line in body.splitlines():
        line = line.strip()
        # 带 `=` 的是等价标记，不是演员标记；`*` 是分隔用的装饰行。
        if not line or "=" in line or line == "*":
            continue
        match = PERFORMER_LINE.match(line)
        if not match:
            continue
        names = [name for name in re.split(r"[\s　]+", match.group(2).strip())
                 if name and not VIDEO_ID.fullmatch(name)]
        if names:
            found.setdefault(match.group(1), []).extend(names)
    return found


def parse_equivalences(body: str, subject: str = "") -> list[list[tuple[str, str]]]:
    """取等价组，每组是 [(video_id, part)]，part 缺省为空串。

    `3312576-1` 与紧跟其后的 `= 3090722-3` 是同一个断言写成了两行，所以以
    `=` 开头的行要并回上一行，否则整张合集映射表会一条都读不出来。

    整条评论只有 `＝2407240` 时主语被省略了，就是当前这一页；没有 `subject`
    就只能把这种断言丢掉。
    """
    body = body.translate(FULLWIDTH)
    lines: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if BAD_HEADER.match(line):
            break                      # `bad:` 之后全是否定标记，停止解析
        if not line:
            continue
        if line.startswith("=") and lines:
            lines[-1] = f"{lines[-1]} {line}"
        elif line.startswith("=") and subject:
            lines.append(f"{subject} {line}")
        else:
            lines.append(line)
    groups = []
    for line in lines:
        if "=" not in line or line.startswith("#"):
            continue
        tokens = [(m.group(1), m.group(2) or "") for m in EQUIV_TOKEN.finditer(line)]
        if len(tokens) >= 2:
            groups.append(tokens)
    return groups


def collection_parts(video_id: str, groups: list[list[tuple[str, str]]]) -> dict[str, str]:
    """本 ID 的分片 -> 对应的独立 video_id。够多才算合集。"""
    parts: dict[str, str] = {}
    for group in groups:
        mine = [tok for tok in group if tok[0] == video_id and tok[1]]
        others = [tok for tok in group if tok[0] != video_id]
        if len(mine) == 1 and others:
            parts.setdefault(mine[0][1], others[0][0])
    return parts


def fetch_article(client: httpx.Client, video_id: str) -> dict:
    response = client.get(ARTICLE_URL.format(video_id=video_id), timeout=30)
    if response.status_code == 404:
        raise LookupError("站上无此作品")
    response.raise_for_status()
    match = PAGE_JSON.search(response.text)
    if not match:
        raise LookupError("页面没有 Inertia 数据，可能被挡在登录或人机验证外")
    return json.loads(match.group(1))["props"]


def page_comments(props: dict) -> list[dict]:
    """按 id 去重。`comments.data` 与 `article.comments` 两份是重叠的，直接相加
    会让同一条评论投两票，把「两条独立评论都这么说」这个置信度信号做废。"""
    seen: dict[object, dict] = {}
    both = list((props.get("comments") or {}).get("data") or [])
    both += list((props.get("article") or {}).get("comments") or [])
    for index, comment in enumerate(both):
        seen.setdefault(comment.get("id", f"#{index}"), comment)
    return list(seen.values())


def summarise(video_id: str, props: dict) -> dict:
    article = props.get("article") or {}
    comments = page_comments(props)

    votes: dict[str, int] = {}
    equivalences: list[list[tuple[str, str]]] = []
    for comment in comments:
        body = str(comment.get("body") or "")
        for name in parse_performers(body).get(video_id, []):
            votes[name] = votes.get(name, 0) + 1
        equivalences.extend(parse_equivalences(body, subject=video_id))

    parts = collection_parts(video_id, equivalences)
    is_collection = len(parts) >= COLLECTION_MIN_PARTS
    # 同一段内容在别的 video_id 下的发布，供跨号去重与演员回填使用。
    aliases = sorted({tok[0] for group in equivalences for tok in group
                      if any(t[0] == video_id for t in group) and tok[0] != video_id})

    ranked = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))
    writer = article.get("writer") or {}
    return {
        "title": article.get("title") or "",
        "release_date": article.get("release_date") or "",
        "duration": article.get("duration") or "",
        "censored": article.get("censored") or "",
        "writer": writer.get("name") or "",
        "writer_slug": writer.get("slug") or "",
        "tags": " ".join(str(t.get("name") or t) for t in (article.get("tags") or [])),
        "performers": " ".join(name for name, _ in ranked),
        "performer_votes": " ".join(f"{name}:{n}" for name, n in ranked),
        "is_collection": "1" if is_collection else "",
        "collection_parts": str(len(parts)) if is_collection else "",
        "equivalents": " ".join(aliases),
        # 合集封面套给每个分片会让 21 个不同内容显示同一张图，所以留空。
        "cover_url": "" if is_collection else (article.get("image_url") or ""),
        "note": (f"合集，{len(parts)} 个分片各自独立，封面不下发" if is_collection
                 else ("FC2 官方页已下架" if article.get("not_found") else "")),
    }


HARVEST_FIELDS = ("video_id", "owned", "performers", "performer_votes",
                  "equivalents", "seen_on")


def harvest(video_id: str, props: dict, into: dict) -> None:
    """把一页评论里**所有** video_id 的标记并进全局收获表。

    本地只对得上其中两三个，其余的先存着：库随时会加片子，重爬一遍页面要几小时。
    """
    for comment in page_comments(props):
        body = str(comment.get("body") or "")
        for other_id, names in parse_performers(body).items():
            slot = into.setdefault(other_id, {"votes": {}, "equiv": set(), "seen": set()})
            for name in names:
                slot["votes"][name] = slot["votes"].get(name, 0) + 1
            slot["seen"].add(video_id)
        for group in parse_equivalences(body, subject=video_id):
            members = {token[0] for token in group}
            for other_id in members:
                slot = into.setdefault(other_id, {"votes": {}, "equiv": set(), "seen": set()})
                slot["equiv"].update(members - {other_id})
                slot["seen"].add(video_id)


def harvest_rows(collected: dict, owned: set[str]) -> list[dict]:
    rows = []
    for video_id in sorted(collected):
        slot = collected[video_id]
        ranked = sorted(slot["votes"].items(), key=lambda kv: (-kv[1], kv[0]))
        rows.append({
            "video_id": video_id,
            "owned": "1" if video_id in owned else "",
            "performers": " ".join(name for name, _ in ranked),
            "performer_votes": " ".join(f"{name}:{n}" for name, n in ranked),
            "equivalents": " ".join(sorted(slot["equiv"])),
            "seen_on": " ".join(sorted(slot["seen"])),
        })
    return rows


def backfill(rows: list[dict], collected: dict) -> list[dict]:
    """用全站收获补候选行的演员与等价关系。

    一个作品的演员常常标在**别的作品页**的评论里：`4176112` 那条「剛毛マキちゃん +
    四条链接」同时认领了 `3701252` 和 `4078398`。只看本页评论，这两条候选就会写着
    「无演员标记」，而收获表里明明有。
    """
    for row in rows:
        slot = collected.get(row.get("video_id"))
        if not slot:
            continue
        ranked = sorted(slot["votes"].items(), key=lambda kv: (-kv[1], kv[0]))
        if ranked:
            row["performers"] = " ".join(name for name, _ in ranked)
            row["performer_votes"] = " ".join(f"{name}:{n}" for name, n in ranked)
        merged = set(slot["equiv"]) | set((row.get("equivalents") or "").split())
        if merged:
            row["equivalents"] = " ".join(sorted(merged))
    return rows


FIELDS = ("code", "video_id", "result", "title", "release_date", "duration",
          "censored", "writer", "writer_slug", "tags", "performers",
          "performer_votes", "is_collection", "collection_parts",
          "equivalents", "cover_url", "note")


def pending(database: Path, limit: int) -> list[tuple[str, str]]:
    """库里的 FC2 资产，按 (code, video_id) 去重。"""
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT DISTINCT code FROM asset "
            "WHERE code LIKE 'FC2%' AND code IS NOT NULL AND code<>'' ORDER BY code"
        ).fetchall()
    finally:
        connection.close()
    seen: dict[str, str] = {}
    for (code,) in rows:
        match = VIDEO_ID.search(code or "")
        if match:
            seen.setdefault(match.group(0), code)
    ordered = [(code, video_id) for video_id, code in seen.items()]
    return ordered[:limit] if limit else ordered


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    write_rows(path, fields, rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--cookies", type=Path, required=True,
                        help="Netscape 格式 cookie 文件，放沙盒，别入仓")
    parser.add_argument("--log", type=Path,
                        default=GENERATED_DIR / "fc2-candidate-log.csv")
    parser.add_argument("--harvest", type=Path,
                        default=GENERATED_DIR / "fc2-comment-harvest.csv",
                        help="评论里出现过的所有 video_id，不限于库里有的")
    parser.add_argument("--raw", type=Path,
                        default=GENERATED_DIR / "fc2-comments-raw.jsonl",
                        help="原始评论存档；解析规则以后改了不必重爬")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=2.0)
    return parser


def run(args: argparse.Namespace) -> int:
    todo = pending(args.db, args.limit)
    owned = {video_id for _, video_id in todo}
    jar = load_cookies(args.cookies)
    rows: list[dict] = []
    collected: dict = {}
    stats = {"hit": 0, "miss": 0}
    args.raw.parent.mkdir(parents=True, exist_ok=True)
    raw_log = args.raw.open("w", encoding="utf-8")
    print(f"待抓 {len(todo)} 个 FC2 作品", flush=True)
    with httpx.Client(cookies=jar, headers={"User-Agent": UA},
                      follow_redirects=True) as client:
        for index, (code, video_id) in enumerate(todo, 1):
            try:
                props = fetch_article(client, video_id)
                data = summarise(video_id, props)
            # 长跑任务不能因为一个作品的网络问题整体退出；按条记「未取得」继续。
            # Ctrl-C 是 BaseException，不受影响。
            except Exception as exc:
                stats["miss"] += 1
                reason = f"{type(exc).__name__}: {exc}"
                rows.append({"code": code, "video_id": video_id,
                             "result": "未取得", "note": reason[:120]})
                print(f"[{index}/{len(todo)}] 未取得 {code}：{reason[:70]}", flush=True)
            else:
                stats["hit"] += 1
                rows.append({"code": code, "video_id": video_id,
                             "result": "取得", **data})
                harvest(video_id, props, collected)
                # 原文照存。这些是用户多年攒下的标记，我的正则漏掉哪种写法都不该
                # 意味着要重爬一遍。
                raw_log.write(json.dumps({"video_id": video_id, "code": code,
                                          "comments": page_comments(props)},
                                         ensure_ascii=False) + "\n")
                raw_log.flush()
                mark = "合集" if data["is_collection"] else (data["performers"] or "无演员标记")
                print(f"[{index}/{len(todo)}] 取得 {code} {mark}", flush=True)
            # 每条都落盘：上次抓取死在半路时进度全丢，重来一遍是三小时。
            _write_csv(args.log, FIELDS, backfill(rows, collected))
            _write_csv(args.harvest, HARVEST_FIELDS, harvest_rows(collected, owned))
            time.sleep(args.delay)
    raw_log.close()
    extra = sum(1 for vid in collected if vid not in owned)
    print(f"完成：取得 {stats['hit']}，未取得 {stats['miss']} -> {args.log}")
    print(f"评论收获 {len(collected)} 个 video_id，其中 {extra} 个库里还没有 -> {args.harvest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
