"""把已安装的厂牌 Logo 归一成不透明方图。

页面三处取图位都用 `object-fit: cover` 铺满方框，所以文件本身必须是不透明方图：
带透明像素的独立图标烤上白底，不透明的长条按边缘主色补方，已经是不透明方图的
跳过。目录下所有 `*.img` 都在范围内，`<safe>.icon.img` 与 `<safe>.logo.img` 一样算。
矢量标识（`image/svg+xml`）走同样的边距，方底由外层 SVG 包出来，不栅格化，底色按
内容明暗判；连内容框都没声明、比例无从算起的原样留着并在复核件上记 `vector`。

默认只报告；显式 ``--apply`` 时必须提供独立备份目录，原图和边车会先备份，
再原子替换。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from peach.config import GENERATED_DIR
from peach.scripting import BACKUP_REQUIRED
from peach.images import (MARK, bake_square, bake_square_vector, classify_plate,
                          measure_image_size, vector_image_size)
from peach.review_csv import write_rows


FIELDS = (
    "file", "width", "height", "aspect", "kind", "action", "before_sha256",
    "after_sha256", "backup",
)

# 边车里记的动作名。`harvest_studio_icons.padded_studios` 按 PAD_ACTION 认「这一张
# 的源图是条状字标」，改名等于把那份名单清空。
BAKE_ACTION = "bake-white-plate"
PAD_ACTION = "pad-to-square"
# 矢量标识包白底方框，是 SVG 进 SVG 出，和位图的两个动作分开记。
PLATE_ACTION = "plate-vector"
# 量不出内容框的矢量标识：没动，在复核件上单列。
VECTOR = "vector"
CHANGED_ACTIONS = frozenset({"would-bake", "baked", "would-pad", "padded",
                             "would-plate", "plated"})


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _atomic_bytes(path: Path, payload: bytes) -> None:
    staging = path.with_name(f"{path.name}.tmp")
    staging.write_bytes(payload)
    os.replace(staging, path)


def _is_vector(path: Path, payload: bytes) -> bool:
    """SVG。`.ct` 边车是第一判据，缺边车时再嗅探开头几个字节。"""
    sidecar = Path(f"{path}.ct")
    if sidecar.is_file():
        return "svg" in sidecar.read_text(encoding="utf-8", errors="replace").lower()
    return payload.lstrip().lower().startswith((b"<svg", b"<?xml"))


def _backup_family(source: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for candidate in (source, Path(f"{source}.ct"), Path(f"{source}.provenance.json"),
                      Path(f"{source}.normalization.json")):
        if candidate.is_file():
            shutil.copy2(candidate, backup_dir / candidate.name)


def _install(path: Path, payload: bytes, normalized: bytes, *, kind: str,
             sidecar_action: str, width: float, height: float, content_type: bytes,
             backup_dir: Path) -> str:
    """备份原图，原子替换，留下复核用的边车；返回备份路径。"""
    _backup_family(path, backup_dir)
    _atomic_bytes(path, normalized)
    _atomic_bytes(Path(f"{path}.ct"), content_type)
    evidence = {
        "action": sidecar_action,
        "normalized_at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "original_width": width, "original_height": height,
        "original_sha256": _digest(payload), "normalized_sha256": _digest(normalized),
        "backup": str(backup_dir / path.name),
    }
    _atomic_bytes(Path(f"{path}.normalization.json"),
                  json.dumps(evidence, ensure_ascii=False, indent=2).encode("utf-8"))
    return str(backup_dir / path.name)


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
        kind = classify_plate(payload)
        if _is_vector(path, payload):
            # 矢量不栅格化：白底和边距由外层 SVG 包出来，原文档一个节点都不动。
            # 包不出来的（不是 SVG、或者连内容框都没声明）原样留着并单列，不冒充已归一。
            plated = bake_square_vector(payload)
            box = vector_image_size(payload)
            if plated is None or box is None:
                rows.append({"file": path.name, "width": "", "height": "", "aspect": "",
                             "kind": VECTOR, "action": "vector",
                             "before_sha256": _digest(payload),
                             "after_sha256": "", "backup": ""})
                continue
            if plated == payload:
                # 已经包过方底，一个字节都不用动。
                continue
            box_width, box_height = box
            action = "would-plate"
            backup = ""
            if apply:
                assert backup_dir is not None
                backup = _install(path, payload, plated, kind=VECTOR,
                                  sidecar_action=PLATE_ACTION, width=box_width,
                                  height=box_height, content_type=b"image/svg+xml",
                                  backup_dir=backup_dir)
                action = "plated"
            rows.append({"file": path.name, "width": box_width, "height": box_height,
                         "aspect": round(max(box) / min(box), 3), "kind": VECTOR,
                         "action": action, "before_sha256": _digest(payload),
                         "after_sha256": _digest(plated), "backup": backup})
            continue
        if not size or kind is None:
            rows.append({"file": path.name, "width": "", "height": "", "aspect": "",
                         "kind": kind or "", "action": "invalid",
                         "before_sha256": _digest(payload),
                         "after_sha256": "", "backup": ""})
            continue
        width, height = size
        aspect = max(width, height) / min(width, height)
        baked = bake_square(payload)
        if baked is None:
            rows.append({"file": path.name, "width": width, "height": height,
                         "aspect": round(aspect, 3), "kind": kind, "action": "invalid",
                         "before_sha256": _digest(payload), "after_sha256": "",
                         "backup": ""})
            continue
        if baked == payload:
            # 已经是不透明方图，一个字节都不用动。
            continue
        planned, done, sidecar_action = (
            ("would-bake", "baked", BAKE_ACTION) if kind == MARK
            else ("would-pad", "padded", PAD_ACTION))
        action = planned
        backup = ""
        if apply:
            assert backup_dir is not None
            backup = _install(path, payload, baked, kind=kind,
                              sidecar_action=sidecar_action, width=width, height=height,
                              content_type=b"image/png", backup_dir=backup_dir)
            action = done
        rows.append({"file": path.name, "width": width, "height": height,
                     "aspect": round(aspect, 3), "kind": kind, "action": action,
                     "before_sha256": _digest(payload), "after_sha256": _digest(baked),
                     "backup": backup})
    return rows


def _write_report(path: Path, rows: list[dict[str, object]]) -> None:
    write_rows(path, FIELDS, rows, atomic=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把已安装的厂牌 Logo 归一成不透明方图")
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
    counts = Counter(str(row["action"]) for row in rows)
    print({"mode": "apply" if args.apply else "dry-run",
           "changed": sum(counts[action] for action in CHANGED_ACTIONS),
           "by_action": dict(sorted(counts.items())),
           "report": str(args.report) if args.report else ""})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
