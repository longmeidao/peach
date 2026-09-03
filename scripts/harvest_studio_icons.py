"""给「只有宽幅字标」的厂牌补一枚方形小标，作为 `/logo?variant=icon` 的那一份。

已安装的厂牌图里有一部分本来是宽条字标，被 `normalize_studio_logos.py` 补白成了方图。
补白让它在 160px 的厂牌页大位上好看，但塞进筛选片那种 28px 的小圆里就只剩一条糊字。
社媒头像早就分 icon / logo 两用，厂牌该按同一条判断走。

取哪一份交给 `site_icons`：官网首页声明的 apple-touch-icon / SVG / manifest 优先，
都没有才落到 `/favicon.ico`。合格与否**不能**直接用 `link_marks.render_mark`：
它是为 `/link-mark` 那种 128px 圆标写的，`MIN_DESIGNED_SIZE=96` 会把 32×32、64×64 的
favicon 一律退回。实测七个 JAV 厂牌站，六个的 favicon 内容比在 1.0～1.84 之间——
是方标，只是小。退给一个 28px 的筛选片用绰绰有余，按「不是标识」退掉是判错了。

所以这里只借 `link_marks` 里真正表达 icon / 字标之分的那一条：`content_aspect` 与
`MAX_CONTENT_ASPECT`。尺寸另设自己的下限，因为要顶的位置本来就只有 28～32px。
`MIN_DESIGNED_SIZE` 不动：那是另一个调用方的正确取值。

默认只出复核 CSV 和候选 PNG，不碰已安装的目录。`--install` 才写
`<safe>.icon.img`，那是一个新文件名，不覆盖也不删除现有的 `<safe>.img`。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach import link_marks, site_icons  # noqa: E402
from peach.config import GENERATED_DIR, REVIEW_DIR
from peach.review_csv import write_rows


FIELDS = ("entity_id", "studio", "safe", "installed", "original_size", "link_kind",
          "url", "verdict", "mark_size", "content_aspect", "sha256", "candidate",
          "evidence")

#: 和 `/link-mark` 用同一个 UA：站点按它决定给不给图标，两处不一致会取到不同的东西。
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

OK, WORDMARK, TOOSMALL = "ok", "仍是字标", "只有小图标"
MISSING, SKIP = "未取得", "无官网链接"

#: 小标要顶的位置是 28px 的筛选片和 32px 的圆。短边到不了这个数，缩下去只是一团糊，
#: 还不如继续用现在那张补白字标——至少它是清晰的。FC2 全站只有 16×16，就卡在这。
MIN_SHORT_EDGE = 32


def safe_name(studio: str) -> str:
    """和 `PreviewService.logo` 同一套文件名规则，两边必须一致。"""
    return re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]


def padded_studios(logo_root: Path) -> dict[str, dict[str, object]]:
    """已安装图里哪些是补白过的字标。

    判据是 `normalize_studio_logos.py` 当时留下的边车，不是现在的像素比例——补白之后
    每一张都是方的，从成品上再也看不出原来是不是条状。
    """
    found: dict[str, dict[str, object]] = {}
    for sidecar in sorted(logo_root.glob("*.img.normalization.json")):
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("action") != "pad-to-square":
            continue
        safe = sidecar.name[: -len(".img.normalization.json")]
        found[safe] = {"width": data.get("original_width", ""),
                       "height": data.get("original_height", "")}
    return found


#: 能拿来找图标的链接类型。`social` 不在内：那是另一条线的头像，混进来会把厂牌小标
#: 换成运营的自拍。`catalog` 在内，因为发行平台（FC2-PPV、myfans 这类）按
#: `docs/SOURCING.md` 的判据不登记 official——它们不是厂牌，没有厂牌官网——可它们照样
#: 占着筛选片和卡片徽标那几个位置，需要一枚图标。只认 official 的话，这些实体会在复核件上
#: 记成「无官网链接」，看起来像是漏采，其实是查都没查。
ICON_LINK_KINDS = ("official", "catalog")


def studio_links(connection: sqlite3.Connection) -> dict[str, list[dict[str, str]]]:
    """按 safe 文件名归拢厂牌的站点链接；社媒不算，那是另一条线的头像。"""
    placeholders = ",".join("?" * len(ICON_LINK_KINDS))
    rows = connection.execute(
        "SELECT e.id, e.canonical_name, l.link_kind, l.url"
        " FROM entity e JOIN entity_link l ON l.entity_id = e.id"
        f" WHERE e.kind = 'studio' AND l.link_kind IN ({placeholders})"
        " ORDER BY e.canonical_name, l.id", ICON_LINK_KINDS).fetchall()
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(safe_name(row["canonical_name"]), []).append(
            {"entity_id": row["id"], "studio": row["canonical_name"],
             "link_kind": row["link_kind"], "url": row["url"]})
    return grouped


class Fetcher:
    """注入给 `site_icons.discover` 的取数闭包，顺带限流，并记下取回了几份。

    `best_mark` 返回 None 有两种完全不同的原因：一份都没取回来（站点不可达），
    和取回来了但都被闸门退掉（确实只有字标）。前者是**未取得**，下一步是换个时间
    或换条链接再试；后者是结论，下一步是人工找图。只看返回值分不出来，所以在这里数。
    """

    def __init__(self, client: httpx.Client, timeout: float, interval: float,
                 retries: int = 2, backoff: float = 2.0):
        self.client = client
        self.timeout = timeout
        self.interval = interval
        self.retries = retries
        self.backoff = backoff
        self.fetched = 0
        self.retried = 0
        self._last = 0.0

    def __call__(self, target: str):
        for attempt in range(self.retries + 1):
            wait = self.interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                response = self.client.get(target, headers={"User-Agent": USER_AGENT},
                                           timeout=self.timeout, follow_redirects=True)
            except (OSError, httpx.HTTPError):
                # 和 `page_cache.Site` 同一条规矩：这些站的 TLS 大约三次断一次，重试即成。
                # 上一轮 Fitch、Idea Pocket、Wanz Factory 都取到了，这一轮四个全断，
                # 一次失败就写「未取得」会把纯抖动记成结论。
                if attempt >= self.retries:
                    return None
                self.retried += 1
                time.sleep(self.backoff * (attempt + 1))
                continue
            # 状态码不重试：404 重试三次还是 404。
            if response.status_code != 200 or not response.content:
                return None
            self.fetched += 1
            return response.content, response.headers.get("content-type", "")
        return None


class SquareMark:
    """一份图标字节 → 一枚方形小标，同时留下每次退回的理由。

    `best_mark` 只把结果传回来，退回的原因就地丢失了。可这两种退回的下一步完全不同：
    「还是条字标」是结论，「站上只有 16×16」是去找更大的资产。所以在这里记。

    原样保留像素，不放大：存 128 会把 32×32 插值成一团，而这份图最终只显示在 28px。
    重编码成 PNG 是为了统一——.ico 里可能有多帧，浏览器挑哪一帧不归我们管。
    """

    def __init__(self):
        self.reasons: list[str] = []
        self.size = ""
        #: 通过的那一份的内容比。1.0 是正方的标识，越接近 2.2 越可能是一条字标
        #: 侥幸压线——复核时这个数比看文件名有用得多。
        self.aspect = ""

    def __call__(self, data: bytes, size: int = 0, content_type: str = "") -> bytes | None:
        image = link_marks.decode(data, content_type)
        if image is None:
            self.reasons.append("解不开")
            return None
        aspect = link_marks.content_aspect(image)
        if aspect == 0.0 or aspect > link_marks.MAX_CONTENT_ASPECT:
            self.reasons.append(f"内容比 {aspect:.2f} 是字标")
            return None
        if min(image.size) < MIN_SHORT_EDGE:
            self.reasons.append(f"只有 {image.size[0]}x{image.size[1]}")
            return None
        buffer = io.BytesIO()
        image.convert("RGBA").save(buffer, format="PNG")
        self.size = f"{image.size[0]}x{image.size[1]}"
        self.aspect = f"{aspect:.2f}"
        return buffer.getvalue()


def harvest(padded: dict[str, dict[str, object]],
            links: dict[str, list[dict[str, str]]],
            fetch, candidate_dir: Path) -> list[dict[str, object]]:
    """每个字标厂牌出一行。一个厂牌可能挂多条官网，第一条做出圆标就停。"""
    rows: list[dict[str, object]] = []
    for safe in sorted(padded):
        original = padded[safe]
        size = f'{original["width"]}x{original["height"]}'
        entries = links.get(safe, [])
        if not entries:
            rows.append({"entity_id": "", "studio": safe.replace("_", " "), "safe": safe,
                         "installed": f"{safe}.img", "original_size": size, "link_kind": "",
                         "url": "", "verdict": SKIP, "mark_size": "", "content_aspect": "",
                         "sha256": "",
                         "candidate": "",
                         "evidence": "账本里这个厂牌没有 official／catalog 链接"})
            continue
        attempts: list[str] = []
        reachable = False
        policy = SquareMark()
        for entry in entries:
            before = getattr(fetch, "fetched", 0)
            made = site_icons.best_mark(entry["url"], fetch, policy)
            reachable = reachable or getattr(fetch, "fetched", 0) > before
            if not made:
                attempts.append(entry["url"])
                continue
            candidate_dir.mkdir(parents=True, exist_ok=True)
            path = candidate_dir / f"{safe}.png"
            path.write_bytes(made)
            rows.append({"entity_id": entry["entity_id"], "studio": entry["studio"],
                         "safe": safe, "installed": f"{safe}.img", "original_size": size,
                         "link_kind": entry["link_kind"], "url": entry["url"], "verdict": OK,
                         "mark_size": policy.size, "content_aspect": policy.aspect,
                         "sha256": hashlib.sha256(made).hexdigest(),
                         "candidate": str(path), "evidence": ""})
            break
        else:
            entry = entries[0]
            tried = "、".join(attempts)
            if not reachable:
                verdict = MISSING
                evidence = f"试过 {tried}，一份字节都没取回来"
            elif policy.reasons and all("只有 " in reason for reason in policy.reasons):
                # 是方标，只是站上没有够大的那一份。下一步是找更大的资产，不是放弃。
                verdict = TOOSMALL
                evidence = f"试过 {tried}：" + "、".join(policy.reasons)
            else:
                verdict = WORDMARK
                evidence = f"试过 {tried}：" + "、".join(policy.reasons or ["没有候选"])
            rows.append({"entity_id": entry["entity_id"], "studio": entry["studio"],
                         "safe": safe, "installed": f"{safe}.img", "original_size": size,
                         "link_kind": entry["link_kind"], "url": entry["url"],
                         "verdict": verdict, "mark_size": "", "content_aspect": "",
                         "sha256": "", "candidate": "", "evidence": evidence})
    return rows


def install(rows: list[dict[str, object]], logo_root: Path) -> list[str]:
    """把通过的候选落成 `<safe>.icon.img`。新文件名，不动 `<safe>.img`。"""
    written: list[str] = []
    logo_root.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if row["verdict"] != OK or not row["candidate"]:
            continue
        payload = Path(str(row["candidate"])).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError(f'候选文件与复核记录哈希不一致，拒绝安装：{row["safe"]}')
        destination = logo_root / f'{row["safe"]}.icon.img'
        staging = destination.with_name(f"{destination.name}.{uuid.uuid4().hex}.tmp")
        staging.write_bytes(payload)
        os.replace(staging, destination)
        Path(f"{destination}.ct").write_text("image/png", encoding="utf-8")
        Path(f"{destination}.provenance.json").write_text(json.dumps({
            "source": "studio icon harvest",
            "source_url": row["url"],
            "sha256": row["sha256"],
            "variant": "icon",
            "installed_beside": f'{row["safe"]}.img',
            "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "purpose": "small-surface studio mark",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(destination.name)
    return written


def run(args: argparse.Namespace) -> dict[str, object]:
    logo_root = args.logo_root.resolve()
    padded = padded_studios(logo_root)
    if args.only:
        wanted = {safe_name(name) for name in args.only}
        padded = {key: value for key, value in padded.items() if key in wanted}
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        links = studio_links(connection)
    finally:
        connection.close()

    client = httpx.Client(trust_env=True, follow_redirects=True)
    try:
        rows = harvest(padded, links, Fetcher(client, args.timeout, args.interval),
                       args.candidate_dir.resolve())
    finally:
        client.close()

    order = {OK: 0, TOOSMALL: 1, WORDMARK: 2, MISSING: 3, SKIP: 4}
    rows.sort(key=lambda row: (order.get(row["verdict"], 9), row["safe"]))
    write_rows(args.output, FIELDS, rows)
    stats = {"字标厂牌": len(rows), "复核行": len(rows),
             "ok": sum(1 for row in rows if row["verdict"] == OK),
             "只有小图标": sum(1 for row in rows if row["verdict"] == TOOSMALL),
             "仍是字标": sum(1 for row in rows if row["verdict"] == WORDMARK),
             "未取得": sum(1 for row in rows if row["verdict"] == MISSING),
             "无官网链接": sum(1 for row in rows if row["verdict"] == SKIP),
             "output": str(args.output)}
    if args.install:
        stats["已安装"] = install(rows, logo_root)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        default=REVIEW_DIR / "studio-icons.csv")
    parser.add_argument("--logo-root", type=Path, default=GENERATED_DIR / "logos")
    parser.add_argument("--candidate-dir", type=Path,
                        default=REVIEW_DIR / "studio-icons")
    parser.add_argument("--only", nargs="*", default=[],
                        help="只处理这几个厂牌，按 canonical_name 给")
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--install", action="store_true",
                        help="把通过的候选写成 <safe>.icon.img；不覆盖现有文件")
    args = parser.parse_args(argv)
    print(run(args))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
