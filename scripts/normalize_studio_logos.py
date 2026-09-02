"""把已经安装的长条厂牌 Logo 补成方图。

候选抓取早已按方图策略处理，但历史安装文件没有回溯。默认只报告；显式
``--apply`` 时必须提供独立备份目录，原图和边车会先备份，再原子替换。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR
from peach.scripting import BACKUP_REQUIRED
from peach.images import MAX_ASPECT, measure_image_size, pad_to_square
from peach.review_csv import write_rows


FIELDS = (
    "file", "width", "height", "aspect", "action", "before_sha256",
    "after_sha256", "backup",
)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _atomic_bytes(path: Path, payload: bytes) -> None:
    staging = path.with_name(f"{path.name}.tmp")
    staging.write_bytes(payload)
    os.replace(staging, path)


def _backup_family(source: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for candidate in (source, Path(f"{source}.ct"), Path(f"{source}.provenance.json")):
        if candidate.is_file():
            shutil.copy2(candidate, backup_dir / candidate.name)


def normalize(root: Path, *, apply: bool = False,
              backup_dir: Path | None = None) -> list[dict[str, object]]:
    root = root.resolve()
    if apply:
        if backup_dir is None:
            raise ValueError(BACKUP_REQUIRED)
        backup_dir = backup_dir.resolve()
        if backup_dir == root or root in backup_dir.parents:
            raise ValueError("备份目录必须在 Logo 目录之外")
    rows: list[dict[str, object]] = []
    for path in sorted(root.glob("*.img")):
        payload = path.read_bytes()
        size = measure_image_size(payload)
        if not size:
            rows.append({"file": path.name, "width": "", "height": "", "aspect": "",
                         "action": "invalid", "before_sha256": _digest(payload),
                         "after_sha256": "", "backup": ""})
            continue
        width, height = size
        aspect = max(width, height) / min(width, height)
        if aspect <= MAX_ASPECT:
            continue
        squared = pad_to_square(payload)
        if squared is None:
            rows.append({"file": path.name, "width": width, "height": height,
                         "aspect": round(aspect, 3), "action": "invalid",
                         "before_sha256": _digest(payload), "after_sha256": "", "backup": ""})
            continue
        action = "would-pad"
        backup = ""
        if apply:
            assert backup_dir is not None
            _backup_family(path, backup_dir)
            _atomic_bytes(path, squared)
            _atomic_bytes(Path(f"{path}.ct"), b"image/png")
            evidence = {
                "action": "pad-to-square", "normalized_at": datetime.now(timezone.utc).isoformat(),
                "original_width": width, "original_height": height,
                "original_sha256": _digest(payload), "normalized_sha256": _digest(squared),
                "backup": str(backup_dir / path.name),
            }
            _atomic_bytes(Path(f"{path}.normalization.json"),
                          json.dumps(evidence, ensure_ascii=False, indent=2).encode("utf-8"))
            action = "padded"
            backup = str(backup_dir / path.name)
        rows.append({"file": path.name, "width": width, "height": height,
                     "aspect": round(aspect, 3), "action": action,
                     "before_sha256": _digest(payload), "after_sha256": _digest(squared),
                     "backup": backup})
    return rows


def _write_report(path: Path, rows: list[dict[str, object]]) -> None:
    write_rows(path, FIELDS, rows, atomic=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把已安装的长条厂牌 Logo 补成方图")
    parser.add_argument("--root", type=Path, default=GENERATED_DIR / "logos")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path,
                        help="原图备份目录；--apply 必需")
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = normalize(args.root, apply=args.apply, backup_dir=args.backup)
    except (OSError, ValueError) as error:
        print(str(error))
        return 2
    if args.report:
        _write_report(args.report, rows)
    changed = sum(row["action"] in {"would-pad", "padded"} for row in rows)
    print({"mode": "apply" if args.apply else "dry-run", "long_logos": changed,
           "report": str(args.report) if args.report else ""})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
