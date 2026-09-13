"""旧壳 `web/app.js` 的路由表只许减不许增：新页面做成 `frontend/` 的 island。

ADR-0022 的迁移方向是逐屏搬出 app.js，可 2026-09-13 盘点时它已长到 10818 行，比立项
时多出四成——每一轮新功能都往旧壳里加一屏。行数拦不住这种增长（拦住的只是注释），
拦得住的是「旧壳里登记了哪些页面」：这张表冻结之后，再想加一屏只能在 island 里登记。
表里的条目搬走一条就从这里删一条。
"""
import pathlib
import re
import unittest

import peach

REPO = pathlib.Path(peach.__file__).resolve().parents[2]
APP = REPO / "web" / "app.js"

#: `const ROUTES=[` 里以字面量写出的 `match`；由 `STATE_ROUTES`、`ROUTE_ENTITIES` 展开的
#: 那两组不在此列，它们的数量由下面的 `SPREADS` 钉住。
FROZEN_ROUTES = frozenset({
    "/", "/trash", "/playlists", "/playlists/:playlist/:item", "/mix/:seed/:item",
    "/parts/:seed/:item", "/editions/:seed/:item", "/item/:id", "/follow/item/:id",
    "/performers", "/creators", "/studios", "/agencies", "/tags", "/stats", "/taste",
    "/review", "/data-cleanup", "/duplicates", "/resource-sync", "/quality-goals",
    "/scraping", "/follow", "/follow-manage", "/configuration", "/activity", "/immerse",
})
SPREADS = 2


def routes_table(source: str) -> str:
    start = source.index("const ROUTES=[")
    return source[start:source.index("\n];", start)]


class LegacyShellRouteTests(unittest.TestCase):
    def test_the_shell_registers_no_route_outside_the_frozen_table(self):
        source = APP.read_text(encoding="utf-8")
        table = routes_table(source)
        literal = set(re.findall(r"match:\s*'([^']*)'", table))
        added = sorted(literal - FROZEN_ROUTES)
        self.assertEqual(added, [],
                         "旧壳里多出了路由；新页面请做成 frontend/ 的 island，"
                         "在它自己的入口里 `window.peachRegisterRoute` 登记：" + "、".join(added))
        gone = sorted(FROZEN_ROUTES - literal)
        self.assertEqual(gone, [], "这些路由已经搬出旧壳，请把它们从 FROZEN_ROUTES 里删掉：" + "、".join(gone))
        self.assertEqual(table.count("...Object.entries("), SPREADS,
                         "ROUTES 里展开的路由组数量变了；新增一组同样算往旧壳里加页面")
        self.assertEqual(len(re.findall(r"\bregisterRoute\(", source)), 0,
                         "app.js 自己不该调用 registerRoute：那是给 island 入口用的")


if __name__ == "__main__":
    unittest.main()
