"""复核产物 CSV 的读写口径。

AGENTS.md 把 CSV 定为「复核产物」：可机读、可重放，结论必须落在这里而不是只存在于
对话。既然要被反复读写，它的编码就不是风格问题：

- `utf-8-sig` 的 BOM 决定 Excel 打开时中文是不是乱码；少了它，一份复核表在 Excel
  里就是一屏问号，而写它的脚本一切正常。
- `newline=""` 决定 Windows 下每条记录之间会不会多出一个空行；漏了它，csv 模块写的
  `\\r\\n` 会再被文本层翻译一次。

这两条此前在 46 个读写点各写一遍。新脚本照抄时漏掉任一条，都要等到有人真的用 Excel
打开那份表才会发现——而那通常是几天以后，脚本早就跑完了。
"""
from __future__ import annotations

import csv
import os
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

#: 复核 CSV 的编码。改它等于改所有复核产物的可读性，不要在调用处覆盖。
ENCODING = "utf-8-sig"


def read_rows(path: Path | str, *, missing_ok: bool = False) -> list[dict[str, str]]:
    """读一份复核 CSV。

    默认在文件缺失时抛 `FileNotFoundError`，和直接 `open()` 一样——这不是多余的严格。
    脚本分两种：一种自己先判 `is_file()` 再读（续跑文件不存在是正常起点），另一种就指望这个
    异常把「输入没给全」变成一次带健康报告的失败退出。把「缺文件返回空表」设成默认，
    等于让第二种脚本安静地拿一张空表跑完并返回成功——错误被吞掉，而且没有任何提示。

    想要容错的调用方显式写 `missing_ok=True`。
    """
    target = Path(path)
    if missing_ok and not target.is_file():
        return []
    with target.open(encoding=ENCODING, newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(
    path: Path | str,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
    *,
    atomic: bool = False,
    fill_missing: bool = False,
) -> None:
    """写一份复核 CSV，并按需保证原子替换。

    `atomic` 走临时文件加 `os.replace`：长跑任务被打断时，读的人拿到的要么是替换前
    那份完整文件、要么是替换后那份，不会是写了一半的。异常路径删掉临时文件再原样抛出，
    不把中断伪装成成功。

    `fill_missing` 用空串补齐缺的列。默认关掉是有意的：`DictWriter` 遇到多余的键会抛
    `ValueError`，那几乎总是字段名真的写错了；无条件补齐会把这个错误变成一列静默的
    空值，等到复核的人对着空列发呆时已经查不回来了。
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = list(fieldnames)

    def dump(handle) -> None:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        if fill_missing:
            writer.writerows({field: row.get(field, "") for field in fields}
                             for row in rows)
        else:
            writer.writerows(rows)

    if not atomic:
        with target.open("w", encoding=ENCODING, newline="") as handle:
            dump(handle)
        return

    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding=ENCODING, newline="") as handle:
            dump(handle)
        os.replace(temporary, target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
