"""把厂牌自己的社交账号头像取成 Logo 候选。

社交头像天然是正方形，而且由品牌本人发布，比搜索引擎的同名结果可信得多——
Wikimedia 搜 `BAZOOKA` 会返回 16:9 的泡泡糖品牌图，这类错误无法靠人工一眼分辨。

handle 默认必须由 `--handles` 显式提供。脚本不猜 handle：猜错会产出一个"看起来很像
官方"的错误 Logo，和它要取代的搜索引擎猜测是同一种失败。`--guess-handles` 只用于
生成待人工确认的候选，产出一律标记 `needs_confirmation`，不得直接采用。

解析链路：handle → unavatar.io 解析出 `pbs.twimg.com` 的真实地址 → 从该地址下载 →
实测尺寸。unavatar 只用来解析地址，图片本身来自平台自己的 CDN，provenance 两者都记。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.http import HttpRequest, HttpxTransport      # noqa: E402
from peach.images import PAD, REJECT, classify, measure_image_size, pad_to_square  # noqa: E402

RESOLVER = "https://unavatar.io/{platform}/{handle}?json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Peach/0.6"
FIELDS = ("studio", "handle", "platform", "resolved_url", "width", "height",
          "aspect", "verdict", "saved", "accepted", "confirmation", "reason")


def safe_name(studio: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", studio)[:60]


def guess_handle(studio: str) -> str:
    """把厂牌名压成一个可能的 handle。只作候选，绝不直接采用。"""
    return re.sub(r"[^A-Za-z0-9_]", "", studio)[:15]


def load_handles(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (row.get("studio") or "").strip(): (row.get("handle") or "").strip()
            for row in csv.DictReader(handle)
            if (row.get("studio") or "").strip()
        }


def resolve(http, platform: str, handle: str, timeout: float) -> str:
    response = http(HttpRequest(
        "GET", RESOLVER.format(platform=platform, handle=handle),
        {"User-Agent": USER_AGENT}), timeout, 1 << 20)
    return str(json.loads(response.body).get("url") or "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True,
                        help="缺 Logo 的厂牌清单，需含 studio 列")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--handles", type=Path,
                        help="studio,handle 映射 CSV；没有它就不解析")
    parser.add_argument("--platform", default="x")
    parser.add_argument("--guess-handles", action="store_true",
                        help="按厂牌名猜 handle，产出一律标记 needs_confirmation")
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--image-dir", type=Path,
                        help="落盘目录；默认放在 output 同级的 studio-logos/")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.image_dir is None:
        args.image_dir = args.output.parent / "studio-logos"

    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        studios = [(row.get("studio") or "").strip()
                   for row in csv.DictReader(handle) if (row.get("studio") or "").strip()]
    if args.limit:
        studios = studios[: args.limit]
    mapping = load_handles(args.handles)

    rows: list[dict[str, object]] = []
    http = HttpxTransport()
    last = 0.0
    try:
        for studio in studios:
            handle = mapping.get(studio, "")
            confirmation = "confirmed-handle"
            if not handle and args.guess_handles:
                handle, confirmation = guess_handle(studio), "needs_confirmation"
            if not handle:
                rows.append({"studio": studio, "handle": "", "platform": args.platform,
                             "resolved_url": "", "width": "", "height": "", "aspect": "",
                             "verdict": "", "saved": "", "accepted": False,
                             "confirmation": "no-handle",
                             "reason": "未取得该厂牌的社交 handle"})
                continue
            wait = args.interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            record = {"studio": studio, "handle": handle, "platform": args.platform,
                      "resolved_url": "", "width": "", "height": "", "aspect": "",
                      "verdict": "", "saved": "", "accepted": False,
                      "confirmation": confirmation, "reason": ""}
            try:
                url = resolve(http, args.platform, handle, args.timeout)
                if not url:
                    record["reason"] = "解析不到头像地址"
                    rows.append(record)
                    continue
                record["resolved_url"] = url
                image = http(HttpRequest("GET", url, {"User-Agent": USER_AGENT}),
                             args.timeout, 8 << 20)
                size = measure_image_size(image.body)
            except Exception as exc:
                record["reason"] = f"取图失败：{type(exc).__name__}"
                rows.append(record)
                continue
            if size is None:
                record["reason"] = "无法解析为图片"
                rows.append(record)
                continue
            width, height = size
            verdict, aspect, reason = classify(width, height)
            payload = image.body
            if verdict == PAD:
                # 长条形 Logo 补背景填成正方形，而不是丢掉——界面本来就按方框渲染。
                padded = pad_to_square(payload)
                if padded is None:
                    verdict, reason = REJECT, "补方失败"
                else:
                    payload = padded
            saved = ""
            if verdict != REJECT:
                args.image_dir.mkdir(parents=True, exist_ok=True)
                suffix = ".png" if verdict == PAD else Path(url.split("?")[0]).suffix or ".img"
                destination = args.image_dir / f"{safe_name(studio)}{suffix}"
                destination.write_bytes(payload)
                saved = str(destination)
            record.update({"width": width, "height": height, "aspect": round(aspect, 3),
                           "verdict": verdict, "saved": saved,
                           "accepted": verdict != REJECT and confirmation != "needs_confirmation",
                           "reason": reason})
            rows.append(record)
    finally:
        http.close()

    rows.sort(key=lambda item: (not item["accepted"], item["aspect"] or 99))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    accepted = sum(1 for row in rows if row["accepted"])
    print({"total": len(rows), "accepted": accepted, "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
