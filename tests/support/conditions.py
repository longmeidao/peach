"""按设计只在某个平台上成立的用例条件。"""

from __future__ import annotations

import os
import unittest

#: 声明根（`[media.locations]`）一律是 Windows 盘符，扫描与落库也只在 Windows 上
#: 发生（ADR-0023、`peach-cross-platform`）。拿临时目录当声明根的用例因此只在 Windows 上
#: 跑得通：那里的临时路径本身就是 Windows 形态，`resolve_root` 认得；POSIX 临时路径
#: 不是账本口径的路径，写入侧门槛会把它当成「不在任何声明根下」拒掉。要让这些用例在
#: macOS 上也跑，得先让 `translate_ledger_path` 在 Windows 上也过 `[media.mounts]`——那是
#: 产品行为的改动，不是测试的事。
windows_ledger_roots = unittest.skipUnless(os.name == "nt", "声明根是 Windows 盘符")
