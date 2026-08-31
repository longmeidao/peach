"""下载并实测候选图片，按「接近正方形」排序后写复核队列。

界面里 Logo 和头像都渲染成正方形（厂牌方图、女优 160×160 圆头像），所以候选必须按
实际像素比例挑选，而不是拿到一个 URL 就当合格。宽幅横图缩进方框会被裁掉两侧或留白。

本脚本只负责「给定候选 URL → 实测 → 排序 → 写 CSV」，不决定去哪里找。
来源由 `--input` 提供；没有可信来源时不要用搜索引擎的猜测结果充数。
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.images import REJECT, classify, measure_image_size   # noqa: E402
from peach.review_csv import read_rows, write_rows

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True,
                        help="含 studio/entity 与候选 url 列的 CSV")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url-column", default="source_url")
    parser.add_argument("--key-column", default="studio")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    rows = read_rows(args.input)

    results: list[dict[str, object]] = []
    with httpx.Client(
        timeout=args.timeout,
        headers={"User-Agent": "Peach review candidate collector/0.6"},
        follow_redirects=True,
    ) as client:
        last = 0.0
        for row in rows:
            url = (row.get(args.url_column) or "").strip()
            key = (row.get(args.key_column) or "").strip()
            if not url:
                results.append({"key": key, "url": "", "width": "", "height": "",
                                "aspect": "", "verdict": "", "accepted": False, "reason": "未取得候选 URL"})
                continue
            wait = args.interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                response = client.get(url)
                response.raise_for_status()
                size = measure_image_size(response.content)
            except Exception as exc:
                results.append({"key": key, "url": url, "width": "", "height": "",
                                "aspect": "", "verdict": "", "accepted": False,
                                "reason": f"下载失败：{type(exc).__name__}"})
                continue
            if size is None:
                results.append({"key": key, "url": url, "width": "", "height": "",
                                "aspect": "", "verdict": "", "accepted": False, "reason": "无法解析为图片"})
                continue
            width, height = size
            verdict, aspect, reason = classify(width, height)
            results.append({"key": key, "url": url, "width": width, "height": height,
                            "aspect": round(aspect, 3), "verdict": verdict,
                            "accepted": verdict != REJECT, "reason": reason})

    # 合格的排前面，同为合格时越接近正方形越靠前；复核页第一眼看到的就是最合适的。
    results.sort(key=lambda item: (not item["accepted"], item["aspect"] or 99))
    write_rows(args.output,
               ("key", "url", "width", "height", "aspect", "verdict", "accepted", "reason"),
               results)
    accepted = sum(1 for item in results if item["accepted"])
    print({"total": len(results), "accepted": accepted, "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
