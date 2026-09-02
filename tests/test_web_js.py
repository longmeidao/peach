"""跑真的 JS：`web/js/` 里的纯模块按行为验收，不按源码文本验收。

页面源断言（`test_web_ui.py`）能守住「这段代码还在」，守不住「它算得对」。
以 JAV 标题为例，以前的断言是
`self.assertPageContains("return it?.is_jav?name.replace(JAV_MEDIA_SUFFIX,''):name")`——
把三元表达式的写法一起写死了，改成 `if` 就红，而真把条件写反了它照样绿。

所以纯模块（不碰 DOM、不读 state、输入输出都是值）改用 Node 直接执行：这里给输入
和期望，Node 那边 `import` 真模块、调真函数、把结果按 JSON 交回来。契约从此是
「同样的输入算出同样的结果」，实现怎么写都行。

只覆盖纯模块。碰 DOM 的那些没有 headless 浏览器就跑不了，继续留在页面源断言里，
不要为了「都能跑」给它们塞一层假 document——那验收的就成了那层假的。
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_JS = ROOT / "web" / "js"
NODE = shutil.which("node")

# Node 那边的入口。模块按绝对 file:// URL 引入，所以驱动脚本放临时目录也能找到它们；
# 用例从 argv 进来，期望值全留在 Python 这边，避免同一张表在两种语言里各写一份。
DRIVER = """
import { pathToFileURL } from 'node:url';

const [, , base, payload] = process.argv;
const cases = JSON.parse(payload);
const cache = new Map();
const results = [];
for (const [module, fn, args] of cases) {
  try {
    if (!cache.has(module)) {
      cache.set(module, await import(pathToFileURL(base + '/' + module).href));
    }
    const target = cache.get(module)[fn];
    if (typeof target !== 'function' && typeof target !== 'object') {
      results.push({ ok: false, error: `${module} 没有导出 ${fn}` });
      continue;
    }
    results.push({ ok: true, value: typeof target === 'function' ? target(...args) : target });
  } catch (error) {
    results.push({ ok: false, error: String(error && error.stack || error) });
  }
}
process.stdout.write(JSON.stringify(results));
"""


@unittest.skipUnless(NODE, "没装 Node，纯模块的行为验收跳过")
class WebJsBehaviourTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._driver = Path(cls._tmp.name) / "driver.mjs"
        cls._driver.write_text(DRIVER, encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def run_js(self, cases):
        """按顺序执行 `[模块, 导出名, 参数列表]`，返回结果列表。"""
        done = subprocess.run(
            [NODE, str(self._driver), WEB_JS.as_posix(), json.dumps(cases)],
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        if done.returncode != 0:
            self.fail(f"Node 跑不起来（exit {done.returncode}）：{done.stderr.strip()[:2000]}")
        results = json.loads(done.stdout)
        for case, result in zip(cases, results):
            if not result["ok"]:
                self.fail(f"{case[0]}.{case[1]}{tuple(case[2])} 抛异常：{result['error'][:800]}")
        return [result["value"] for result in results]

    def assertJsResults(self, table):
        """`table` 是 `(模块, 导出名, 参数, 期望)`，一次全跑完再逐条比。

        一次起一个 Node 进程要几百毫秒，逐条起会把这个文件拖成十几秒。
        """
        cases = [[module, fn, list(args)] for module, fn, args, _ in table]
        for (module, fn, args, want), got in zip(table, self.run_js(cases)):
            self.assertEqual(got, want, f"{module}.{fn}{tuple(args)}")

    # ── 路由匹配 ────────────────────────────────────────────────────────────

    def test_route_patterns_match_what_the_table_says_and_nothing_else(self):
        routes = [
            {"match": "/", "title": "首页"},
            {"match": "/item/:id", "title": "作品"},
            {"match": "/playlists/:playlist/:item"},
            {"match": "/performers/:name*", "title": None},
        ]
        self.assertJsResults([
            # 精确路径：多一段少一段都不算。
            ("routes.js", "matchPath", ["/", "/"], {}),
            ("routes.js", "matchPath", ["/", "/item/7"], None),
            ("routes.js", "matchPath", ["/stats", "/stats"], {}),
            ("routes.js", "matchPath", ["/stats", "/stats/7"], None),
            # `:id` 只吃数字，且吃完就得刚好用完。非数字必须落空——以前每条动态路由
            # 自己写这条正则，漏写的那条会把 `/item/abc` 当合法 id 送进 `+parts[1]`。
            ("routes.js", "matchPath", ["/item/:id", "/item/42"], {"id": 42}),
            ("routes.js", "matchPath", ["/item/:id", "/item/abc"], None),
            ("routes.js", "matchPath", ["/item/:id", "/item/"], None),
            ("routes.js", "matchPath", ["/item/:id", "/item/42/x"], None),
            ("routes.js", "matchPath", ["/playlists/:a/:b", "/playlists/3/9"],
             {"a": 3, "b": 9}),
            # `:name*` 吃掉剩下全部：女优名字里有斜杠，只吃一段会把人名切两半。
            ("routes.js", "matchPath", ["/performers/:name*", "/performers/A/B"],
             {"name": "A/B"}),
            ("routes.js", "matchPath", ["/performers/:name*", "/performers/A"],
             {"name": "A"}),
            # 尾段为空不算命中，否则 `/performers` 索引页会被实体页抢走。
            ("routes.js", "matchPath", ["/performers/:name*", "/performers"], None),
            # 先登记先匹配，表里的顺序就是优先级。
            ("routes.js", "matchRoute", [routes, "/item/7"],
             {"route": {"match": "/item/:id", "title": "作品"}, "params": {"id": 7}}),
            ("routes.js", "matchRoute", [routes, "/nowhere"], None),
            # 标题：字符串直接用，没有 title 的路由给空串（由调用方兜底文案），
            # 匹配不上也是空串。
            ("routes.js", "routeLabel", [routes, "/item/7"], "作品"),
            ("routes.js", "routeLabel", [routes, "/playlists/1/2"], ""),
            ("routes.js", "routeLabel", [routes, "/performers/A/B"], ""),
            ("routes.js", "routeLabel", [routes, "/nowhere"], ""),
        ])

    # ── JAV 标题 ────────────────────────────────────────────────────────────

    def test_media_suffix_is_stripped_only_for_jav(self):
        # 番号作品的文件名后缀是噪声；创作者作品的文件名里点号可能有意义，
        # 一律剥会把 `clip.2024.1080p` 削短。
        self.assertJsResults([
            ("jav-title.js", "javFileDisplayName",
             [{"is_jav": True, "name": "ABC-123.mp4"}], "ABC-123"),
            ("jav-title.js", "javFileDisplayName",
             [{"is_jav": True, "name": "ABC-123.RMVB"}], "ABC-123"),
            ("jav-title.js", "javFileDisplayName",
             [{"is_jav": False, "name": "clip.2024.1080p.mp4"}],
             "clip.2024.1080p.mp4"),
            ("jav-title.js", "javFileDisplayName", [None], ""),
        ])

    def test_official_title_prefers_the_japanese_one(self):
        # catalog_title 有时是英文机翻，original_title 才是原始日文；两条都没日文
        # 就按顺序取第一条，都没有就空。
        self.assertJsResults([
            ("jav-title.js", "javPreferredTitle",
             [{"catalog_title": "Some English", "original_title": "日本語タイトル"}],
             "日本語タイトル"),
            ("jav-title.js", "javPreferredTitle",
             [{"catalog_title": "Some English", "original_title": ""}],
             "Some English"),
            ("jav-title.js", "javPreferredTitle", [{}], ""),
        ])

    def test_code_prefix_is_taken_off_the_title_but_only_when_it_is_a_prefix(self):
        self.assertJsResults([
            # 番号 + 分隔符开头的才算前缀，剥掉之后再清掉残留的分隔符。
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "name": "ABC-123 一个标题"}],
             {"code": "ABC-123", "title": "一个标题", "badges": []}),
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "name": "ABC-123.一个标题.mp4"}],
             {"code": "ABC-123", "title": "一个标题", "badges": []}),
            # 番号只是恰好出现在开头、后面直接接字母，那不是前缀，别切。
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC", "name": "ABCDEF 别切我"}],
             {"code": "ABC", "title": "ABCDEF 别切我", "badges": []}),
            # display_code 是对外显示的写法，前缀判定和输出都用它。
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC123", "display_code": "ABC-123",
               "name": "ABC-123 标题"}],
             {"code": "ABC-123", "title": "标题", "badges": []}),
            # 不是 JAV，或者没有番号，就只有一个标题，连 badges 字段都不给。
            ("jav-title.js", "javTitleParts",
             [{"is_jav": False, "name": "普通作品"}],
             {"code": "", "title": "普通作品"}),
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "", "name": "没番号"}],
             {"code": "", "title": "没番号"}),
        ])

    def test_an_explicitly_empty_display_title_is_an_answer_not_a_miss(self):
        # API 返回空 display_title 是「清洗后确认无标题」，不是「没查到」。
        # 回退到脏文件名等于把清洗结果丢掉——这条踩过。
        self.assertJsResults([
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "display_title": "",
               "name": "ABC-123 hhd800.com@脏文件名"}],
             {"code": "ABC-123", "title": "", "badges": []}),
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "display_title": "干净标题",
               "name": "ABC-123 脏文件名"}],
             {"code": "ABC-123", "title": "干净标题", "badges": []}),
            # 键不存在才回退到文件名推出来的标题。
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "name": "ABC-123 文件名标题"}],
             {"code": "ABC-123", "title": "文件名标题", "badges": []}),
            # 官方标题优先于任何 display_title。
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "display_title": "干净标题",
               "original_title": "日本語", "name": "ABC-123"}],
             {"code": "ABC-123", "title": "日本語", "badges": []}),
        ])

    def test_only_the_three_edition_badges_survive(self):
        # 版本徽章是白名单：其它 edition_badges（画质、分卷之类）不进标题行。
        self.assertJsResults([
            ("jav-title.js", "javTitleParts",
             [{"is_jav": True, "code": "ABC-123", "name": "ABC-123 标题",
               "edition_badges": ["中字", "4K", "无码破解"]}],
             {"code": "ABC-123", "title": "标题", "badges": ["中字", "无码破解"]}),
            ("jav-title.js", "javDisplayName",
             [{"is_jav": True, "code": "ABC-123", "name": "ABC-123 标题",
               "edition_badges": ["中字"]}],
             "ABC-123 中字 标题"),
            # 没标题就只剩番号，不留下尾随空格。
            ("jav-title.js", "javDisplayName",
             [{"is_jav": True, "code": "ABC-123", "display_title": "",
               "name": "ABC-123"}],
             "ABC-123"),
        ])

    def test_title_html_escapes_everything_it_interpolates(self):
        # 标题来自刮削结果，是不可信输入。番号、徽章、标题三处都得转义。
        self.assertJsResults([
            ("jav-title.js", "javTitleHtml",
             [{"is_jav": False, "name": "<script>x</script>"}],
             "&lt;script&gt;x&lt;/script&gt;"),
            ("jav-title.js", "javTitleHtml",
             [{"is_jav": True, "code": "ABC-123", "display_title": "<b>x</b>",
               "name": "ABC-123"}],
             '<span class="javidentity"><strong class="javcode">ABC-123</strong>'
             '</span> <span class="javtitle">&lt;b&gt;x&lt;/b&gt;</span>'),
            ("jav-title.js", "javTitleHtml",
             [{"is_jav": True, "code": "ABC-123", "display_title": "",
               "name": "ABC-123", "edition_badges": ["无码"]}],
             '<span class="javidentity"><strong class="javcode">ABC-123</strong>'
             '<small class="javedition uncensored">无码</small></span>'),
        ])

    # ── 标签显示名 ──────────────────────────────────────────────────────────

    def test_tag_labels_only_rename_and_never_invent(self):
        # 映射只做「显示名」，不做同义词归并：账本里的标签名是真相。查不到就原样
        # 返回，绝不能顺手补一个机翻后缀（`深喉` 曾被显示成 `深喉咙`）。
        self.assertJsResults([
            ("tags.js", "tagLabel", ["足系"], "美腿"),
            ("tags.js", "tagLabel", ["1080P"], "1080p"),
            ("tags.js", "tagLabel", ["深喉"], "深喉"),
            ("tags.js", "tagLabel", ["无码"], "无码"),
            ("tags.js", "tagLabel", ["没有别名的标签"], "没有别名的标签"),
            ("tags.js", "tagLabel", [""], ""),
        ])

    # ── core 里的格式化 ─────────────────────────────────────────────────────

    def test_the_minus_one_duration_sentinel_never_becomes_a_duration(self):
        """账本里的 `-1` 是探测硬失败的哨兵，不是时长。

        用户实测 /item/86287（ABF-234-UN.mp4，duration=-1）：播放器顶上标着「直播」，
        总时长显示 `0:NaN`。链条是——`Number(it.duration)||0` 对 -1 求值仍是 -1，通过了
        真值判断，于是强行 `player.duration(-1)`；而 Video.js 的 setter 写着
        `parseFloat(e)<0 ? Infinity : e`，随后 `=== Infinity` 就 `addClass("vjs-live")`。
        一部本地影片因此被当成直播流。全库有 1440 个视频资产 duration<=0（其中 1101 个
        正好是 -1）。`fmtDur(-1)` 同样算过 `0:-1`，用户在卡片上看到过。

        所以判据是「有限且大于零」，不是「非空」。这条以前按源码文本断言，现在直接
        拿 -1 去问函数——把三元换成 if 不该让它红，把条件写反才该红。
        """
        self.assertJsResults([
            ("core.js", "realDuration", [-1], 0),
            ("core.js", "realDuration", [0], 0),
            ("core.js", "realDuration", [None], 0),
            ("core.js", "realDuration", ["不是数字"], 0),
            ("core.js", "realDuration", [12.5], 12.5),
            ("core.js", "fmtDur", [-1], "—"),
        ])

    def test_formatters_round_the_way_the_ui_reads_them(self):
        self.assertJsResults([
            ("core.js", "esc", ["<a href='x'>&"], "&lt;a href=&#39;x&#39;&gt;&amp;"),
            ("core.js", "esc", [None], ""),
            # 时长缺失显示破折号，不显示 0:00——那会被读成「零秒的视频」。
            ("core.js", "fmtDur", [0], "—"),
            ("core.js", "fmtDur", [None], "—"),
            ("core.js", "fmtDur", [-5], "—"),
            ("core.js", "fmtDur", [59], "0:59"),
            ("core.js", "fmtDur", [61], "1:01"),
            ("core.js", "fmtDur", [3661], "1:01:01"),
            # fmtClock 是播放器时间轴，0 秒是真的 0 秒。
            ("core.js", "fmtClock", [0], "0:00"),
            ("core.js", "fmtClock", [-5], "0:00"),
            ("core.js", "fmtSize", [1024 * 1024], "1 MB"),
            ("core.js", "fmtSize", [3 * 1024 * 1024 * 1024], "3.0 GB"),
            ("core.js", "fmtSize", [2 * 1024 ** 4], "2.00 TB"),
        ])


if __name__ == "__main__":
    unittest.main()
