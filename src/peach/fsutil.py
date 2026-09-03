"""落盘只有两种结果：旧内容或新内容，不会有半成品。

这套「先写临时文件再 `os.replace`」的手法在库里被抄了十几遍，每一遍都在同一批细节上
各自发挥：临时文件放哪、叫什么、失败了谁删。抄错任何一条的表现都不是报错，而是别的
请求读到一张半张的图或一段截断的 JSON——比崩掉难查得多。所以这里只留一份实现。

三条约束是这个模块存在的全部理由：

1. 临时文件必须和目标**同目录**。`os.replace` 只在同一个卷上才是原子的，而 `tempfile`
   的默认目录经常在另一个盘（Windows 上尤其如此），跨卷会退化成拷贝。
2. 临时文件名必须带随机段。两个线程同时生成同一个目标是常态（同一张封面被两个卡片
   同时请求），共用一个 `x.tmp` 会让其中一个删掉另一个正在写的文件。
3. 扩展名必须沿用目标的。FFmpeg 和 PIL 都按输出文件的扩展名决定编码格式，把临时名写成
   `x.tmp` 会让它们直接失败。
"""
from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def atomic_path(target: Path | str, *, suffix: str | None = None) -> Iterator[Path]:
    """产出一个同目录的临时路径；正常退出就原子替换 `target`，出错就把它删掉。

    给的是路径而不是文件句柄，因为一半的调用方是把这个路径交给 FFmpeg 或 PIL 去写，
    自己并不碰文件内容。`suffix` 默认沿用目标的扩展名，需要覆盖时（例如目标没有扩展名
    但工具要求有）再显式传。
    """
    destination = Path(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tail = destination.suffix if suffix is None else suffix
    temporary = destination.with_name(
        f".{destination.name}.{uuid.uuid4().hex[:12]}.tmp{tail}")
    try:
        yield temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    try:
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_write_bytes(target: Path | str, data: bytes, *,
                       mode: int | None = None) -> Path:
    """把 `data` 原子地写成 `target`。返回目标路径，方便接着链下去。"""
    with atomic_path(target) as temporary:
        temporary.write_bytes(data)
        _restrict(temporary, mode)
    return Path(target)


def atomic_write_text(target: Path | str, text: str, *, encoding: str = "utf-8",
                      mode: int | None = None) -> Path:
    """同上，但写文本。编码显式给默认值，避免落到平台默认编码上。"""
    with atomic_path(target) as temporary:
        temporary.write_text(text, encoding=encoding)
        _restrict(temporary, mode)
    return Path(target)


def _restrict(path: Path, mode: int | None) -> None:
    """在替换之前收紧权限位，这样目标从来没有一刻是宽权限的。

    Windows 上跳过：那里的 `chmod` 只能翻只读位，真正管事的是 ACL，调用它除了产生
    一个「已经设过权限」的错觉之外没有任何作用。
    """
    if mode is not None and os.name != "nt":
        path.chmod(mode)
