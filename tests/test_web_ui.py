import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

_WORD = re.compile(r"[A-Za-z0-9_$]")
_QUOTES = "'\"`"


def code_shape(source: str) -> str:
    """把 JS 源码压成「和排版无关」的形状。

    页面源断言里最脆的一类不是契约写错了，而是断言把缩进和换行一起写死了：
    `if(e.key===' '){\\n      e.preventDefault();` 这种一旦有人重排一行就红，
    红的原因和它想守的东西毫无关系。这里把字符串字面量外面的空白全部规范化——
    两侧都是标识符字符时留一个空格（保住 `const x`、`await f` 这类必需的间隔），
    否则删掉（`){ e.` 与 `){e.` 从此等价）。

    字符串和模板字面量原样保留：里面的空白是内容，不是排版。模板字面量里的换行
    尤其如此，HTML 片段的断言要靠它。扫描器认转义，遇到注释里的单引号或含引号的
    正则会跟丢，所以 `assertCode` 同时保留原样匹配的通路，跟丢只会让它退回今天的
    行为，不会把绿的判成红的。
    """
    out, index, size = [], 0, len(source)
    while index < size:
        char = source[index]
        if char in _QUOTES:
            out.append(char)
            index += 1
            while index < size:
                out.append(source[index])
                if source[index] == "\\":
                    index += 1
                    if index < size:
                        out.append(source[index])
                        index += 1
                    continue
                if source[index] == char:
                    index += 1
                    break
                index += 1
            continue
        if char.isspace():
            end = index
            while end < size and source[end].isspace():
                end += 1
            before = out[-1] if out else ""
            after = source[end] if end < size else ""
            if _WORD.match(before) and _WORD.match(after):
                out.append(" ")
            index = end
            continue
        out.append(char)
        index += 1
    return "".join(out)


def stylesheet_source() -> str:
    """`web/css/` 的全部分区按层叠顺序拼起来，等于 `/app.css` 交付的那一份。

    样式表按分区拆在 `web/css/` 下、由 `stylesheet_response()` 拼成一份交付，但断言
    守的仍是整份样式表这一个契约：分区边界只是文件边界，选择器和 token 要跨分区看。
    目录用 glob 而不是写死清单，再切出新分区时不必回头改这里。
    """
    web = Path(__file__).resolve().parents[1] / "web"
    return "".join(path.read_text(encoding="utf-8")
                   for path in sorted((web / "css").glob("*.css")))


class StylesheetPartitionTests(unittest.TestCase):
    """样式表分区：清单、层叠顺序，以及每份分区自身必须是完整的 CSS。

    拆分的全部目的是让两处改动落在不同文件上，不改变交付的字节。所以这里守两件事：
    清单和顺序不许悄悄变，切口不许落在规则或注释中间。
    """

    #: 层叠顺序就是这个顺序。加分区要同时改这里——glob 出来的新文件会自动进
    #: `stylesheet_source()`，但插在哪一档决定谁覆盖谁，那是判断而不是发现。
    PARTITIONS = (
        "01-base.css", "02-topbar.css", "03-filterbar.css", "04-manage.css",
        "05-insights.css", "06-index.css", "07-entity.css", "08-photos.css",
        "09-skeleton.css", "10-photolight.css", "11-identity.css", "12-cards.css",
        "13-stage.css", "14-player.css", "15-detail.css", "16-settings.css",
        "17-overlay.css", "18-drawer.css", "19-immersive.css", "20-offdisk.css",
        "21-online.css", "22-followmanage.css", "23-configuration.css",
        "24-miniplayer.css", "25-motion.css",
    )

    @classmethod
    def setUpClass(cls):
        cls.web = Path(__file__).resolve().parents[1] / "web"

    def test_partitions_are_the_pinned_set_in_cascade_order(self):
        names = [path.name for path in sorted((self.web / "css").glob("*.css"))]
        self.assertEqual(tuple(names), self.PARTITIONS)
        # 两位数前缀不是装饰：文件名排序就是层叠顺序，`stylesheet_response()` 只做
        # `sorted()`。少了前缀的文件会插到任意位置，样式表照样加载，只是错。
        for name in names:
            self.assertRegex(name, r"^\d{2}-[a-z0-9-]+\.css$")
        self.assertFalse((self.web / "app.css").exists(),
                         "整份 app.css 已经拆成 web/css/ 下的分区，不该再有这个文件")

    def test_each_partition_closes_its_own_braces_and_comments(self):
        """切口只许落在花括号深度 0、注释之外。

        规则或 `@media` 被切成两半时，拼起来仍然完全正确——两份分区各自都不是合法
        CSS，却只有单独看每一份才能发现。注释同理：`/*` 留在上一份、`*/` 落到下一份，
        中间那份的规则会被后来的编辑当成生效内容去改，实际上整段是注释。
        """
        for path in sorted((self.web / "css").glob("*.css")):
            depth, in_comment = 0, False
            body = path.read_text(encoding="utf-8")
            index = 0
            while index < len(body):
                if in_comment:
                    end = body.find("*/", index)
                    if end < 0:
                        break
                    in_comment, index = False, end + 2
                    continue
                if body.startswith("/*", index):
                    in_comment, index = True, index + 2
                    continue
                char = body[index]
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    # 先 `}` 再 `{` 的分区最终深度仍是 0，只有逐个字符看才会露出来。
                    self.assertGreaterEqual(depth, 0, f"{path.name} 多出一个右花括号")
                index += 1
            self.assertEqual(depth, 0, f"{path.name} 有没闭合的花括号，切口落在规则中间")
            self.assertFalse(in_comment, f"{path.name} 有没闭合的注释，切口落在注释中间")


class WebUiSourceTests(unittest.TestCase):
    def test_index_and_entity_visibility_targets_exist_in_the_page(self):
        html = (Path(__file__).resolve().parents[1] / "web/index.html").read_text(encoding="utf-8")
        for start, end in (("async function openIndex(", "  const title="),
                           ("async function openEntity(", "  /* 大位")):
            body = self.app_js.split(start, 1)[1]
            body = body.split(end, 1)[0]
            for target in re.findall(r"\$\('#([^']+)'\)\.hidden\s*=", body):
                with self.subTest(target=target):
                    self.assertIn(f'id="{target}"', html)

    @classmethod
    def setUpClass(cls):
        # 页面拆成 index.html + web/css 下的样式分区 + app.js + web/js 下的 ES module。这些断言
        # 守的是「Web 表面」这一个契约，不是某个文件，所以把所有源码接起来一起看。
        # 模块目录用 glob 而不是写死清单：再拆出新模块时不必回头改这里。写死的后果
        # 是断言悄悄扫不到新文件——它照样「通过」，但什么也没守住。
        web = Path(__file__).resolve().parents[1] / "web"
        # 顺序照旧（HTML、样式、脚本）：`code_shape` 是一个带引号状态的扫描器，
        # 把样式挪到脚本之后会改变整页的引号配平，它跟丢的位置也跟着变。
        sources = [web / "index.html"]
        sources.extend(sorted((web / "css").glob("*.css")))
        sources.append(web / "app.js")
        sources.extend(sorted((web / "js").glob("*.js")))
        cls.css = stylesheet_source()
        cls.app_js = (web / "app.js").read_text(encoding="utf-8")
        # 光晕的预设表与色板单独拎出来：断言要按色相角遍历那两张表，得先切到它们所在的
        # 那一份源码。它们现在住在 `web/js/home-glow.js`，不再由 app.js 定义。
        cls.glow_js = (web / "js" / "home-glow.js").read_text(encoding="utf-8")
        cls.page = chr(10).join(
            path.read_text(encoding="utf-8") for path in sources
        )
        # 排版无关的那份只算一次：整页四十万字符，按调用逐次重算会把这个文件
        # 从两秒拖到半分钟。
        cls.page_shape = code_shape(cls.page)
        # 「谁用到了这个类名」只能问模板一侧。样式表自己不算——把样式分区也接进来
        # 比对，每个选择器都会匹配到它自己的定义。
        # island（ADR-0022）也是模板一侧：高清版目标页的 DOM 现在由 frontend 里的
        # Preact 组件产出，样式仍留在 `web/css/`。不把它接进来的话，迁走的那几组类会
        # 被误判成没人用，然后有人真的把还在生效的样式删掉。
        markup = [web / "index.html", web / "app.js", *sorted((web / "js").glob("*.js"))]
        island_src = Path(__file__).resolve().parents[1] / "frontend" / "src"
        markup.extend(sorted(path for suffix in ("*.ts", "*.tsx")
                             for path in island_src.rglob(suffix)))
        cls.markup = chr(10).join(path.read_text(encoding="utf-8") for path in markup)

    # 页面源断言必须自带有界失败信息。assertIn 失败时会把整个 index.html（约 189 KB）
    # 原样塞进错误消息，一条失败就产出 195 KB 输出；工具管道遇到超大输出会转存成文件，
    # 看起来就像「整个会话输出消失」。真实成因是断言消息，不是测试竞态或运行器挂起。
    def assertPageContains(self, needle: str, message: str = ""):
        if needle not in self.page:
            self.fail(f"index.html 缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def assertPageLacks(self, needle: str, message: str = ""):
        if needle in self.page:
            self.fail(f"index.html 不应再出现：{needle!r}" + (f"（{message}）" if message else ""))

    def assertCode(self, needle: str, message: str = ""):
        """页面源里有这段代码，缩进和换行怎么排都算。

        守的还是同一件事，只是不再把排版一起写死；细节见 `code_shape`。
        """
        if needle in self.page:
            return
        if code_shape(needle) in self.page_shape:
            return
        self.fail(f"index.html 缺少这段代码（已忽略排版）：{needle!r}"
                  + (f"（{message}）" if message else ""))

    def read_react(self, relative: str) -> str:
        """React 子树里的一份源码（ADR-0031）。迁过去的页面正文不在 `web/` 里。"""
        return (Path(__file__).resolve().parents[1] / "frontend" / "src" / "react"
                / relative).read_text(encoding="utf-8")

    def test_the_format_insensitive_matcher_still_tells_code_from_content(self):
        """`code_shape` 本身也有逻辑，也得有人守。

        它松的是排版，不是内容：字符串字面量里的空白一个都不许动。放松到把
        `e.key===' '`（空格键）和 `e.key===''`（空串）看成一回事，这个断言机制就从
        「少写一点脆」变成「悄悄放过一类缺陷」。
        """
        # 缩进、换行、花括号后的空格：随便排。
        self.assertEqual(code_shape("if(a){\n      b();\n}"), code_shape("if(a){b();}"))
        self.assertEqual(code_shape("const  x = 1"), code_shape("const x=1"))
        # 关键字和标识符之间的那个空格是必需的，不许被压掉。
        self.assertIn(" ", code_shape("const x=1"))
        self.assertNotEqual(code_shape("const x=1"), code_shape("constx=1"))
        # 字符串和模板字面量里的空白是内容。
        self.assertNotEqual(code_shape("e.key===' '"), code_shape("e.key===''"))
        self.assertNotEqual(code_shape("`<b> </b>`"), code_shape("`<b></b>`"))
        # 跟丢引号时退回原样匹配，所以这条断言只保证「至少能原样命中」。
        self.assertPageContains("const $=s=>document.querySelector(s);")

    def route_entry(self, match: str) -> str:
        """路由表里 `match` 那一条的源码。

        「哪个路径进哪一屏」是用户能感知的契约；它是写成一张表还是写成一条
        二十五分支的 if 链，是实现细节。这些断言问的是「这条路径在不在、进去的是
        哪一屏」，所以换派发方式不该让它们变红——真把一条路径弄丢了才该红。
        """
        table = self.app_js.split("\nconst ROUTES=[", 1)[1].split("\n];", 1)[0]
        for entry in re.split(r"\n  (?=\{match:|\.\.\.)", table):
            if entry.lstrip().startswith("{match:'%s'" % match):
                return entry
        listed = ", ".join(re.findall(r"\{match:'([^']+)'", table))
        self.fail(f"路由表里没有 {match}（表里有：{listed}）")

    def assertRoute(self, match: str, *needles: str):
        entry = self.route_entry(match)
        for needle in needles:
            if needle not in entry:
                self.fail(f"路由 {match} 这一条缺少：{needle!r}")

    def test_module_level_bindings_are_declared_before_they_are_used(self):
        """模块级 `let`/`const` 不许在声明行之前被引用。

        `let`/`const` 有 TDZ：声明那一行执行之前读它是 ReferenceError，而不是
        undefined。前端曾有三十多处「函数写在上面、声明写在下面」，没炸只是因为
        那些函数恰好都在启动之后才第一次被调用——判据是运行时机，而不是能从代码上
        看出来的东西。谁把其中任意一个挪进启动路径，症状就是首屏整页空白，
        而改动本身看不出和它有关。

        修法只有两种：可变状态提到 app.js 顶部的「模块级可变状态」块，纯函数改写成
        会提升的 `function` 声明（或拆进 `web/js/`）。这里不做作用域分析，所以函数
        内部同名的局部变量要另起名字——`selectedQuality` 就是为此从 `selected`
        改过来的。
        """
        web = Path(__file__).resolve().parents[1] / "web"
        for path in [web / "app.js"] + sorted((web / "js").glob("*.js")):
            offenders = self._bindings_used_before_declaration(
                path.read_text(encoding="utf-8"))
            self.assertEqual(offenders, [], f"{path.name} 里这些绑定在声明前被引用：" + "；".join(
                f"{name} 声明在第 {decl} 行，第 {ref} 行已经在用" for name, decl, ref in offenders))

    @staticmethod
    def _bindings_used_before_declaration(source: str):
        """找出「声明行在后、引用行在前」的模块级 `let`/`const`。

        只认顶格（第 0 列）的 `let`/`const`：缩进的都在某个函数或块里，那是局部作用域，
        不属于这个契约。注释先剥掉——中文注释里提到标识符本来就很常见，不剥的话
        整条断言会被噪声淹没。
        """
        lines = source.split("\n")
        stripped, in_block = [], False
        for line in lines:
            text = line
            if in_block:
                if "*/" in text:
                    text, in_block = text.split("*/", 1)[1], False
                else:
                    stripped.append("")
                    continue
            while "/*" in text:
                head, rest = text.split("/*", 1)
                if "*/" in rest:
                    text = head + " " + rest.split("*/", 1)[1]
                else:
                    text, in_block = head, True
                    break
            comment = text.find("//")
            if comment >= 0 and not text[:comment].endswith(":"):
                text = text[:comment]
            stripped.append(text)

        names = []
        for index, text in enumerate(stripped):
            head = re.match(r"(?:let|const)\s+(.*)$", text)
            if not head:
                continue
            depth, current, chunks = 0, "", []
            for char in head.group(1):
                if char in "([{":
                    depth += 1
                elif char in ")]}":
                    depth -= 1
                if char == "," and depth == 0:
                    chunks.append(current)
                    current = ""
                else:
                    current += char
            chunks.append(current)
            for chunk in chunks:
                declared = re.match(r"\s*([A-Za-z_$][\w$]*)", chunk)
                if declared:
                    names.append((declared.group(1), index + 1))

        offenders, seen = [], set()
        for name, line_number in names:
            if name in seen:
                continue
            seen.add(name)
            # 前面挡掉 `.`（成员访问）和引号（字符串键与字面量），它们不是绑定引用。
            pattern = re.compile(r"(?<![\w$.'\"])" + re.escape(name) + r"(?![\w$])")
            for earlier in range(line_number - 1):
                if pattern.search(stripped[earlier]):
                    offenders.append((name, line_number, earlier + 1))
                    break
        return offenders

    def test_every_font_size_comes_from_the_one_type_scale(self):
        """全站只有一套字号刻度，任何写死的像素都要有理由。

        收敛之前样式表里散着 21 种字号（9…48px），相邻两档常常只差半个像素——
        既排不出层级，也没法复核「这里为什么是 12.5」。现在一律走 `--fs-*`。

        唯一的例外是移动端输入框那条 `16px!important`：那是 iOS 的自动放大阈值，
        不是刻度里的一档。让它跟着 `--fs-lg` 走的话，将来把 lg 调成 17 或 15
        都会悄悄破坏那个保护，而症状（在 iPhone 上聚焦输入框页面猛地放大）
        跟字号改动看不出任何关系。
        """
        css = stylesheet_source()
        literals = re.findall(r"font(?:-size)?:(?:\d+ )?([\d.]+)px", css)
        self.assertEqual(literals, ["16"],
                         f"除 iOS 防放大的 16px 外不该有写死字号，实际 {literals}")
        declared = re.findall(r"--fs-([a-z0-9]+):(\d+)px", css)
        self.assertEqual(declared,
                         [("xs", "12"), ("sm", "13"), ("md", "14"), ("lg", "16"),
                          ("xl", "20"), ("2xl", "24"), ("3xl", "32"), ("4xl", "48")])
        # 下限是 12px：更小的灰字在 vercel-report-design 里被点名为要拒绝的反射。
        self.assertNotIn("--fs-", css.split("--fs-xs")[0][-40:],
                         "刻度必须从 --fs-xs 开始，别在前面塞更小的档")

    # 强调色 --tungsten 的合法去处。选择器只要含其中任一片段，规则体就可以用蓝。
    TUNGSTEN_ALLOWED_SELECTORS = (
        ":focus",              # 焦点环：:focus / :focus-visible / :focus-within
        ".geist-progress", ".watchprogress", ".vjs-play-progress", ".vjs-progress-holder",
        ".trace .bar", ".tokbar",  # 进度与数据
        ".ptoggle:checked",  # Toggle 开态：Geist Toggle 实测轨道 rgb(0,112,243)
        ".entitylink", ".flink", ".tokauthor>a", ".taste-history-guide-content a",  # 真正的链接
    )

    def test_tungsten_is_reserved_for_focus_links_progress_and_toggle(self):
        """蓝色只给焦点环、链接、进度／数据和 Toggle 开态，选中态与主动作一律反相墨色。

        `vercel-report-design`（vercel.com/design.md）要求「Design in monochrome」，颜色只在
        对状态、动作或数据有显著意义时才用，并配非颜色线索。2026-09-03 实测 Geist：Tabs
        选中是墨色文字加 2px 墨色下划线，Switch 选中是抬起一档的灰面，Checkbox 选中是墨色
        勾，主按钮是 #EDEDED 底 #0A0A0A 字——都没有蓝；只有 Toggle 开态轨道是 rgb(0,112,243)。
        收敛前 Peach 有两套强调色：筛选 pill 选中反相成白，其它 40 多处选中／主按钮／悬停
        却是蓝，同一页上「被选中」和「可以按」长得一样。
        """
        css = stylesheet_source()
        self.assertNotIn("--tungsten-soft", css, "蓝色浅底 token 已退役，不得再引入")
        offenders = []
        selected_with_blue = []
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            selector, body = match.group(1).strip(), match.group(2)
            if "tungsten" not in body or "--tungsten:" in body:
                continue
            leaf = selector.split("{")[-1]  # 去掉 @media 前缀
            if any(token in leaf for token in self.TUNGSTEN_ALLOWED_SELECTORS):
                continue
            offenders.append(leaf)
            if any(state in leaf for state in (
                    'aria-pressed="true"', "aria-current", ".selected", ".current",
                    ".picked", ":checked", ".primary")):
                selected_with_blue.append(leaf)
        self.assertEqual(selected_with_blue, [],
                         f"选中态与主动作不得用蓝，改用 --ink／--ink-2 反相：{selected_with_blue}")
        self.assertEqual(offenders, [],
                         f"这些规则的 --tungsten 不在允许的焦点／链接／进度／Toggle 之列：{offenders}")

    def test_field_focus_rings_are_neutral_and_theme_aware(self):
        """输入框静止 1px 中性边、悬停与聚焦同一枚 2px inset ring 换灰档（BoardUI Input）。

        2026-09-05 实测 vercel.com 后台的 4px 中性辉光已被 BoardUI Input
        （2026-09-09 取证登记 boardui-input）接替：`ring-2 ring-inset` 在
        border-button-hover／-active 两档间换档，聚焦压过悬停。环画在静止那条边的
        内侧，三态边框同色——聚焦时把边改成透明只会露出控件自己的底，那正是环外
        那条亮边的来源。上游把 box-shadow 写进了 transition，环是渐出来的。
        """
        for palette in (":root{", '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){',
                        ':root[data-theme="dark"]{'):
            self.assertPageContains(palette)
        self.assertPageContains("--field-ring:rgba(0,0,0,.08);--field-ring-hover:rgba(0,0,0,.21);")
        self.assertPageContains("--field-ring-focus:rgba(0,0,0,.34);")

        self.assertPageContains("--field-ring:rgba(255,255,255,.14);--field-ring-hover:rgba(255,255,255,.24);")
        self.assertPageContains("--field-ring-focus:rgba(255,255,255,.51);")
        css = stylesheet_source()
        for stale in ("border-color:var(--field-ring-focus);box-shadow:0 0 0 4px var(--field-glow)",
                      ":hover{border-color:var(--field-ring-focus)",
                      "--field-glow"):
            self.assertNotIn(stale, css, f"焦点配方已接替：{stale}")
        self.assertNotIn("border-color:transparent;box-shadow:inset", css,
                         "环画在边的内侧，聚焦时不清空那条边")
        for rule in ('.geist-search input[type="search"]:hover{box-shadow:inset 0 0 0 2px var(--color-border-button-hover)}',
                     '.geist-search input[type="search"]:focus{outline:0;'
                     'box-shadow:inset 0 0 0 2px var(--color-border-button-active)}',
                     '.geist-input:hover{box-shadow:inset 0 0 0 2px var(--color-border-button-hover)}',
                     '.geist-input:focus{outline:0;box-shadow:inset 0 0 0 2px var(--color-border-button-active)}',
                     '.gselectfield[aria-expanded="true"]{box-shadow:inset 0 0 0 2px var(--color-border-button-active)}',
                     '.search:focus-within{box-shadow:inset 0 0 0 2px var(--color-border-button-active)}',
                     '.preference textarea:focus{box-shadow:inset 0 0 0 2px var(--color-border-button-active);outline:0}'):
            self.assertPageContains(rule)
        # 换档要渐出来：上游 field 的 transition 明确列了 box-shadow，只写
        # border-color 的话环是硬切的。带环的那几个控件都得把它列进去。
        for transition in ('line-height:20px;transition:box-shadow .12s ease}',
                           'font:inherit;font-size:var(--fs-md);line-height:20px;transition:box-shadow .12s ease}',
                           'transition:border-color .12s ease,background-color .12s ease,box-shadow .12s ease}'):
            self.assertPageContains(transition)

    def test_fieldsets_put_the_bright_face_on_the_content_and_the_bar_below_it(self):
        """操作条以中性透明灰叠在框体上，与骨架使用同一灰阶。"""
        self.assertPageContains("--page:#FAFAFA;")
        self.assertPageContains("--page:#04060A;")
        for selector in (".cleanupfieldset", ".fsec",
                         ".resourcesyncbox,.resourcepanel"):
            self.assertPageContains(selector + "{", f"{selector} 应有一条自己的规则")
        css = stylesheet_source()
        for name in (".cleanupfieldset>.geist-fieldset-footer",
                     ".fsechead", ".resourcesyncfooter,.resourceapplyrow"):
            start = css.index(name + "{")
            rule = css[start:css.index("}", start)]
            self.assertIn("background:var(--overlay-5)", rule, f"{name} 是操作条")
            self.assertIn("var(--line-soft)", rule, f"{name} 与正文之间是一条发丝线")

    def test_the_follow_job_panel_sits_on_the_card_tier_inside_the_section(self):
        """进度面板是灰面 `.fsec` 里的一张白卡，与查找结果卡同档。

        它承载的只是一段进度，和查找结果卡一样躺在 `--ground` 的灰面上；透明或
        同灰会让框只剩一圈边。面板不再与 `.fsec` 同灰，而是 CheckboxCard 那一档：
        `--field-ring` 发丝边配 primary 的白面。
        """
        css = stylesheet_source()
        panel = css[css.index(".followtask{"):]
        panel = panel[:panel.index("}")]
        section = css[css.index(".fsec{"):]
        section = section[:section.index("}")]
        self.assertIn("border:1px solid var(--field-ring)", panel, "发丝边跟分区对齐")
        self.assertIn("background:var(--color-background-primary-default)", panel,
                      "进度面板是灰面上的一张白卡")
        for token in ("border:1px solid var(--field-ring)", "background:var(--ground)"):
            self.assertIn(token, section, "分区容器是这一档的基准")
        jobs = (Path(__file__).resolve().parents[1] / 'frontend/src/jobs.ts').read_text(encoding='utf-8')
        self.assertIn('<section class="followtask" data-geist-fieldset aria-label="任务进度">', jobs)

    def test_buttons_keep_two_tiers_a_solid_primary_and_a_bright_secondary(self):
        """按钮只有两档：次级是比容器亮一档的实面，强调档那一面由 `board.css` 一处给；
        两档都不描边。

        2026-09-05 实测 vercel.com 的仪表盘工具行，两档同屏并排，次级是 `#FFFFFF` 底
        `#171717` 字。次级不是透明的——压在 `#FAFAFA` 的操作条上，
        透明会让按钮和条子连成一片。Geist 给次级另挂的那圈 `box-shadow:0 0 0 1px` 这里
        不画：描边档与实心档并排看着一大一小，差的是「一个是块面、一个是个框」，
        而次级只出现在操作条上，比条子亮一档本身就是边界。

        悬停按 Geist Button 源规则抬一档：secondary 走 gray-200（浅色 `#EBEBEB`、深色
        `#1F1F1F`），即自己那块面上压 8% 墨。每一颗次级按钮都用同一个值，白底上才看得出
        鼠标停在哪一颗。
        """
        css = stylesheet_source()
        secondary_hover = "background:color-mix(in srgb,var(--ink) 8%,var(--ground))"
        self.assertCode(".geist-button{box-sizing:border-box;height:32px;padding:0 14px;"
                        "border:0;border-radius:var(--control-radius);"
                        "background:var(--ground);color:var(--ink);display:inline-flex;")
        self.assertPageContains(f".geist-button:hover:not(:disabled){{{secondary_hover}}}")
        # 强调档那一面只有 `board.css` 一处（`test_the_primary_tier_has_one_face_and_crossfades_into_its_hover`）。
        # 这一层再写一份的话，它的 `:hover:not(:disabled)` 比 Board 那条静止规则重一个类，
        # 同一颗按钮的静止和悬停就分别由两处给出。
        self.assertNotIn(".geist-button.primary{", css)
        # 找的是这三条基样式本身，不是别处以同名结尾的派生规则（`.fsechead .fbtn{`
        # 也以 `.fbtn{` 收尾），所以选择器前面必须是上一条规则的边界。
        for name in (".cleanupfieldset button:where(:not(.gselectfield)){",
                     ".fbtn{", ".resourceaction{"):
            found = re.search(r"(?:^|[}\n])" + re.escape(name), css)
            self.assertIsNotNone(found, f"{name} 找不到基样式")
            start = found.end() - len(name)
            rule = css[start:css.index("}", start)]
            self.assertIn("background:var(--ground)", rule, f"{name} 是次级档，自己是一块亮面")
            self.assertIn("border:0", rule, f"{name} 跟次级档一样不描边")
        for name in (".cleanupfieldset button:where(:not(.gselectfield)):hover{",
                     ".fbtn:hover:not(:disabled){",
                     ".resourceaction:hover:not(:disabled){",
                     ".dupactions.fsechead button:hover{"):
            start = css.index(name)
            rule = css[start:css.index("}", start)]
            self.assertIn(secondary_hover, rule, f"{name} 的悬停与次级档同抬一档")

    def test_the_scrollbar_thumb_floats_over_the_content_and_takes_no_width(self):
        """滑块自绘、浮在内容上，一列宽度都不占；颜色取主题变量。

        原生滚动条自己占 15px 实宽，浅色一档的槽还是块比 `--page` 更亮的死白，窗口
        右边于是常年挂着一条从头贯到底的白带。滑块不写死灰值：写死一档只在一种主题
        下成立，深灰滑块落在浅色底上就是一条突兀的粗杠。几何按 2026-09-05 实测
        vercel.com 侧栏：轨道 12px 只是命中区，看得见的是 3px，悬停 6px。
        """
        css = stylesheet_source()
        rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertNotIn("--sb:", rules, "滚动条不需要专属颜色 token")
        self.assertIn("html{color-scheme:light;scroll-padding-top:calc(var(--topH) + 8px);"
                      "scrollbar-width:none}", rules)
        self.assertNotIn("scrollbar-color", rules, "原生滑块已经不画了，没有配色可调")
        self.assertIn(".ovtrack{position:absolute;z-index:2;pointer-events:none}", rules)
        self.assertIn(".ovtrack.ov-y{right:0;top:8px;bottom:8px;width:12px}", rules)
        self.assertIn(".ovtrack.ov-x{left:8px;right:8px;bottom:0;height:12px}", rules)
        self.assertIn(".ovthumb{position:absolute;border-radius:var(--pill-radius);"
                      "background:var(--field-ring-hover);", rules)
        self.assertIn(".ov-y .ovthumb{right:0;top:0;width:3px}", rules)
        self.assertIn(".ov-x .ovthumb{left:0;bottom:0;height:3px}", rules)
        self.assertIn("transition:width .15s cubic-bezier(.4,0,.2,1),height .15s cubic-bezier(.4,0,.2,1)}",
                      rules)
        self.assertIn(".ov-y:hover .ovthumb,.ov-y.dragging .ovthumb{width:6px}", rules)
        self.assertIn(".ov-x:hover .ovthumb,.ov-x.dragging .ovthumb{height:6px}", rules)
        # 原生那条只在覆盖式接上之后才藏：脚本没跑到的容器留着系统滚动条兜底。
        self.assertIn("[data-overlay-scrollbar]{scrollbar-width:none}", rules)
        self.assertIn("[data-overlay-scrollbar]::-webkit-scrollbar{display:none}", rules)
        self.assertNotIn("scrollbar-width:thin", rules, "细滚动条也是原生那条，统一交给覆盖式")
        # 粗指针没有悬停也没有可指的滑块，但滑块照画：原生的已经关掉，跟着一起收
        # 就等于触屏上读不出这一列有多长、自己在哪儿。
        self.assertIn("@media (pointer:fine){.ovtrack{pointer-events:auto}}", rules)
        self.assertNotIn("::-webkit-scrollbar-thumb", rules, "滑块是元素，不是伪元素")

    def test_the_page_track_only_takes_pointer_events_on_the_thumb_itself(self):
        """整页那条轨道横跨窗口右边，命中区必须收到 3px 的滑块上。

        侧栏轨道 12px 宽、只覆盖侧栏，吃掉的点击本来就是侧栏自己的。整页那条不一样：
        它从窗口顶贯到底，12px 的透明条会把右边缘所有点击一并吃掉，而设置面板正贴
        在那儿。宽出来的命中区换不到什么，丢掉的是右侧一整列控件。
        """
        css = stylesheet_source()
        rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertIn(".ovtrack.page{position:fixed;top:0;bottom:0;right:0;z-index:91;"
                      "pointer-events:none}", rules)
        self.assertIn("@media (pointer:fine){.ovtrack.page .ovthumb{pointer-events:auto}}", rules)
        self.assertIn(".ovtrack.page:hover .ovthumb{width:3px}", rules)
        self.assertIn(".ovtrack.page .ovthumb:hover,.ovtrack.page.dragging .ovthumb{width:6px}",
                      rules)

    def test_the_overlay_thumb_is_sized_and_moved_by_the_measured_ratio(self):
        """滑块高按可视高/内容高，位移按滚动进度×可走距离；不可滚就整条收起。

        2026-09-05 实测 vercel.com 侧栏：轨道 789px、可视 805、内容 851，滑块高
        746.35 —— 正好是 805/851×789，位移写在行内 `transform:translateY()` 上。
        另一半是自锁陷阱：藏起来的轨道 `clientHeight` 是 0，拿它当「量不到」就再也
        显不回来，所以顺序必须是先显再量。
        """
        self.assertPageContains("const thumbSize=Math.max(24,Math.min(trackSize,"
                                "size/content*trackSize));")
        self.assertPageContains("const offset=travel>0?at/range*travel:0;")
        self.assertPageContains("thumb.style[vertical?'height':'width']=`${thumbSize}px`;")
        self.assertPageContains("thumb.style.transform=`translate${vertical?'Y':'X'}(${offset}px)`;")
        self.assertPageContains("if(range<=1){track.hidden=true;return}")
        self.assertPageContains("track.hidden=false;")
        # 抽屉重建后内容长短变了，容器盒子没变；整页那条改看 body 的高度，避免在
        # documentElement 上挂 subtree 的 MutationObserver。
        self.assertPageContains("if(root)new ResizeObserver(sync).observe(document.body);")
        self.assertPageContains("else new MutationObserver(sync).observe("
                                "container,{childList:true,subtree:true});")

    def test_the_drawer_scrolls_in_an_inner_layer_so_the_track_can_stay_put(self):
        """抽屉自己不滚，滚的是里面那层：跟着内容一起滚的轨道等于没有轨道。"""
        # 光晕那一层是抽屉的第一个子元素，滚的仍然只有 .drawerscroll 那一层。
        self.assertPageContains('<aside class="drawer" id="drawer">'
                                '<div class="glowlayer" aria-hidden="true"></div>'
                                '<div class="drawerscroll" id="drawerScroll"></div></aside>')
        self.assertPageContains("$('#drawerScroll').innerHTML=")
        self.assertPageContains(".drawerscroll{height:100%;box-sizing:border-box;"
                                "padding:16px 12px 60px;")
        self.assertPageContains("overflow-y:auto;overflow-x:hidden;scrollbar-width:none}")
        self.assertPageContains(".drawer{position:fixed;top:0;bottom:0;left:0;width:360px;")
        self.assertPageContains("attachOverlayScrollbar(document.documentElement,{variant:'page'});")
        self.assertPageContains("attachOverlayScrollbar($('#drawerScroll'));")

    def test_every_drawer_repaint_writes_into_the_scroll_layer_not_the_host(self):
        """#drawer 是滚动容器和轨道的宿主：谁把它整块 innerHTML 换掉，buildBars() 要写的
        容器就没了，首页停在「正在读取作品」。所有重画只能落在 #drawerScroll 里。"""
        source = self.page
        self.assertNotIn("drawer.innerHTML=", source)
        self.assertNotIn("$('#drawer').innerHTML=", source)
        self.assertNotIn("$('#drawer').insertAdjacentHTML(", source)
        self.assertPageContains("const scroll=$('#drawerScroll'),key=surfacePath()+location.search;")
        self.assertPageContains("scroll.innerHTML=`<div style=\"display:flex;align-items:center;justify-content:space-between;margin-bottom:10px\">")
        self.assertPageContains("scroll.insertAdjacentHTML('beforeend',sidebarSectionHtml('内容标签',tagBody,'','online'));")
        # 换页面的判据记在滚动层上：syncSidebarSurface() 判定换页就 replaceChildren()，
        # 传宿主进去会连 #drawerScroll 一起清掉，和整块 innerHTML 是同一种失败。
        self.assertPageContains("syncSidebarSurface(scroll,key)")
        self.assertNotIn("syncSidebarSurface(drawer", source)
        self.assertNotIn("syncSidebarSurface($('#drawer')", source)

    def test_anchored_menus_open_in_the_top_layer_so_animated_ancestors_cannot_clip_them(self):
        """自绘下拉的面板进顶层，祖先上的 transform 与 overflow 都够不着它。

        `position:fixed` 只在没有被祖先接管时才相对视口：祖先上一个 transform、filter 或
        backdrop-filter 就会成为它的包含块，算好的视口坐标于是整体偏移，还要被那个祖先的
        overflow 裁掉。设置面板的卡片正是这种祖先——入场动画的 fill-mode 让 transform 一直
        挂在上面——菜单于是开在看不见的地方，从屏幕上读出来就是「下拉点不开」。
        """
        self.assertCode('<div class="popmenu gselectmenu" role="listbox" '
                        'aria-label="${esc(label)}" popover="manual" data-select-menu hidden>')
        self.assertPageContains("const inTopLayer=menu.hasAttribute('popover');")
        self.assertPageContains(
            "open=true;presentMenu(menu);if(inTopLayer&&!menu.matches(':popover-open'))menu.showPopover();position();")
        self.assertPageContains("if(inTopLayer&&menu.matches(':popover-open'))menu.hidePopover()});")
        # 浏览器给 [popover] 的是 inset:0 加 margin:auto 的居中盒，不拆掉的话菜单会被
        # 拉宽并落在屏幕正中，而定位算的是 left/top。
        self.assertPageContains(".popmenu[popover]{inset:auto;margin:0}")

    def test_every_full_page_overlay_dims_with_the_same_scrim_without_blur(self):
        """盖住整页的弹层用同一档遮罩，值只写在 `--scrim` 上，也不带模糊。

        设置面板和作品详情浮窗底下都是同一片馆藏，压成两种深浅只会让人以为自己打开的
        是两种东西。两档主题同值：Board UI 那一版的弹层就是一块黑纱，浅色主题下也不换。

        值只许有一处定义。同一个属性在两张表里各写一份实色时，后一张用双类名就能把前一张
        整条压掉，而断言仍可能守着那个已经不上屏的值——测试于是变成一份看着绿的假证据。
        """
        css = stylesheet_source()
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("--scrim:rgba(0,0,0,.7);", css)
        self.assertIn("background:var(--scrim);padding:18px;", css)
        self.assertIn(".stage::backdrop{background:var(--scrim)}", css)
        for source, label in ((css, "app.css"), (board, "board.css")):
            self.assertNotIn("rgba(0,0,0,.7)", source.replace("--scrim:rgba(0,0,0,.7)", ""),
                             f"{label} 里遮罩的值只能来自 --scrim")
        for name in (".settingspanel", ".settingscard", ".settingshead"):
            start = css.index(name + "{")
            rule = css[start:css.index("}", start)]
            self.assertNotIn("backdrop-filter", rule, f"{name} 不带模糊")

    def test_the_detail_overlay_moves_on_the_same_motion_as_the_settings_dialog(self):
        """作品详情浮窗和设置弹层用同一组进出场关键帧、同一个时长 token。

        一个缩放着淡进来、另一个直接闪出来的话，读起来像两种东西。遮罩也同一条淡入淡出。
        进场填充用 `backwards` 不用 `both`：终点帧留下的 `filter:blur(0)` 会另起一个
        backdrop root，浮窗里任何 `backdrop-filter` 从此只采样得到浮窗自己的内容。
        退场那条要 `both`，它的终点（透明）不是元素的自然状态。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".stage{animation:board-dialog-in var(--board-dialog-motion) backwards}", board)
        self.assertIn(".settingscard.settingscard{border:0;"
                      "animation:board-dialog-in var(--board-dialog-motion) backwards}", board)
        self.assertIn(".stage::backdrop{animation:settings-backdrop-in "
                      ".35s cubic-bezier(.4,0,.2,1) both}", board)
        self.assertIn(".settingspanel:not([hidden]){animation:settings-backdrop-in "
                      ".35s cubic-bezier(.4,0,.2,1) both}", stylesheet_source())
        self.assertIn(".stage.closing{animation:board-dialog-out var(--board-dialog-motion) both;"
                      "pointer-events:none}", board)
        self.assertIn(".stage.closing::backdrop{animation:settings-backdrop-out "
                      ".35s cubic-bezier(.4,0,.2,1) both}", board)
        self.assertIn(".settingspanel.closing .settingscard.settingscard{"
                      "animation:board-dialog-out var(--board-dialog-motion) both}", board)

    def test_closing_the_detail_overlay_waits_for_its_exit_before_tearing_it_down(self):
        """显式关闭详情的每条路径都先 `stageExit()` 演完退场，再拆解舞台。

        次序是硬的：拆解那一步把 `#stage` 放回 `#main` 的固定槽位，之后重画列表才不会
        把它一起删掉。所以动画只插在拆解前面，拆解与重画自身的先后原样不动。

        等待有上限，`animation` 被 reduced motion 一类的规则关掉时 animationend 不会来；
        拆解入口无条件摘掉 `closing`，被别的路径中途拆掉的浮窗下一次仍从进场那一帧起。
        """
        self.assertPageContains("stage.classList.add('closing')")
        self.assertPageContains("stage.classList.remove('closing')")
        self.assertPageContains("timer=setTimeout(done,380)")
        self.assertPageContains(
            "matchMedia('(prefers-reduced-motion: reduce)').matches)return Promise.resolve()")
        self.assertEqual(2, self.app_js.count("await stageExit();"),
                         "作品与关注两个 closeDetail 各等一次退场")
        self.assertPageContains("  stageExit().then(()=>{\n"
                                "    disposeStage(false,false,{miniplayer:false});",
                                "关闭键还没画出来时走的兜底那条也要演完退场")

    def test_clicking_outside_the_detail_overlay_leaves_it(self):
        """点浮窗外面退出详情，和关闭键、Escape 走同一条路。

        每个表面自己那份 `closeDetail` 挂在关闭键上，按它一下就把该还原的列表、筛选
        和路径一并带回去；退出另写一份必然漏掉其中一样，所以三个入口都按那一下。

        判「外面」取坐标不取事件 target：原生模态里遮罩归 dialog 自己，落在遮罩上的
        target 就是它本人，而浮窗 `overflow:auto` 的滚动条也长在它身上，按 target 判
        会把拖一下滚动条也算成点了外面。按下那一刻也要在外面——详情里进度条、音量条和
        队列都能拖，从控件上拖出边界再松手同样会收到一次 click。

        坐标之外还要求 target 是 dialog 本身：播放器全屏时铺满视口，浮窗矩形不变，
        点进度条右段会落在矩形外，只看坐标就会关掉详情、连带退出全屏并停播。
        """
        self.assertPageContains("const outside=event=>{\n    if(event.target!==stage)return false;",
                                "全屏播放器里的点击不算浮窗外面")
        self.assertPageContains("stage.oncancel=event=>{event.preventDefault();dismissStage()};")
        self.assertPageContains("stage.onpointerdown=event=>{stageDismissArmed=outside(event)};")
        self.assertPageContains(
            "stage.onclick=event=>{if(stageDismissArmed&&outside(event))dismissStage()};")
        self.assertPageContains("const box=stage.getBoundingClientRect();")
        self.assertPageContains("stage.classList.remove('closing');stageDismissArmed=false;",
                                "拆解舞台时把武装状态一并清掉")

    def test_opening_a_detail_leaves_the_surface_bars_where_they_were(self):
        """详情不重画顶部三层、标签条和抽屉；回到列表时数据没变也不重画。

        浮窗是盖住整页的模态，那几条在它开着的时候一格都看不见。为它们另取一趟这一部
        作品口径的聚合，换来的只是把列表那份缓存挤掉；关掉时整排头像连 `<img>` 一起
        重建、重解一遍码，人看到的就是「点进去又退出来，页面自己刷新了一次」。

        回来那一次比的是数据不是时间：详情看上十分钟再回来，取回的多半还是同一份。
        铺过骨架的那一次例外，骨架必须由一次真的绘制顶掉。
        """
        self.assertPageContains("if(barsContext.type==='item')return;",
                                "详情不碰表面的条")
        self.assertPageContains("const rendered=signature+'\\n'+JSON.stringify([facetData,tops]);")
        self.assertPageContains("if(rendered===barsRendered)return;")
        self.assertPageContains("if(!tiers.innerHTML||!views.innerHTML)barsRendered='';")

    def test_the_page_recedes_so_chrome_and_boxes_can_float_on_it(self):
        """页面底是退到后面那张面，顶栏、窄栏和页面上的盒子填浮在它上面那张。

        2026-09-05 实测 vercel.com 后台：页面底 `#FAFAFA`，部署行与设置 fieldset 正文
        `#FFFFFF` 配 1px 的 8% 黑、不带投影；暗色一档是纯黑页面配 `#0A0A0A` 的面，方向不变。
        两张面填成同一个颜色时，整页只剩文字在排层级，控件和内容分不出谁在前面。
        """
        self.assertPageContains("body{background:var(--page);")
        css = stylesheet_source()
        for name in (".top", ".edge"):
            start = css.index(chr(10) + name + "{")
            rule = css[start:css.index("}", start)]
            self.assertIn("var(--ground)", rule, f"{name} 浮在页面底之上")
        # 直接坐在页面上的盒子不能再填 --surface：它与 --page 在浅色一档是同一个 #FAFAFA，
        # 填上去等于没有盒子。--surface 只剩交互与内嵌那一档。
        for name in (".insightpanel", ".junkcard", ".managebar", ".emptystate"):
            start = css.index(name + "{")
            rule = css[start:css.index("}", start)]
            self.assertIn("var(--ground)", rule, f"{name} 是页面上的一个面")

    def test_only_the_home_filter_bar_draws_the_dashed_unapplied_edge(self):
        """虚线只在 `#tagbar` 那一排，别处的药丸一律实线；选中一律填 --picked。

        2026-09-05 实测 vercel.com/<team>/~/deployments 的筛选令牌：未生效
        `rgba(0,0,0,0)` 配 `1px dashed rgba(0,0,0,.21)`，已生效 `#FFFFFF` 配
        `1px solid rgba(0,0,0,.08)`，两个数正是 `--field-ring-hover` 与 `--field-ring`。
        只借这一处：虚线说的是「这条筛选还没加上去」，配得上它的只有恒常在场、
        可开可关的那一排；关注页和实体页的药丸随内容来去，全画成虚线，整页就是
        一片没生效的框。悬停只把虚线拉成实线，是 Peach 自己加的中间档——Vercel 的
        令牌可叠加，悬停预演成生效态没有代价；首页这一排是单选、恒有一颗生效。
        """
        css = stylesheet_source()
        for base in (".pill", ".brandpill"):
            start = css.index(chr(10) + base + "{")
            rule = css[start:css.index("}", start)]
            self.assertIn("background:transparent", rule, f"{base} 未生效不填色")
            self.assertIn("1px solid var(--field-ring)", rule, f"{base} 默认是实线")
            self.assertNotIn("dashed", rule, f"{base} 的默认态不画虚线")
            self.assertPageContains(base + ":hover{border-color:var(--field-ring-hover);color:var(--ink)}")
            self.assertPageContains(base + '[aria-pressed="true"]{border-color:var(--field-ring);'
                                           "background:var(--picked);color:var(--ink)}")
        self.assertPageContains('#tagbar .pill[data-tag]:not([aria-pressed="true"])'
                                "{border-style:dashed;border-color:var(--field-ring-hover)}")
        self.assertPageContains(
            '#tagbar .pill[data-tag]:not([aria-pressed="true"]):hover{border-style:solid}')
        # 药丸里的虚线只此一条：多一条就说明它不再指向「这条筛选还没加上去」。
        dashed_pills = [line for line in css.splitlines()
                        if "dashed" in line and "pill" in line and not line.startswith(" ")]
        self.assertEqual(len(dashed_pills), 1, dashed_pills)
        # 左边四枚视图胶囊四选一、恒有一枚生效，「这条筛选还没加上去」对它们从来不成立。
        self.assertNotIn("[data-state]", dashed_pills[0])
        # 交集条上那颗填同一份 --picked，但不穿药丸那身线：见下一条。
        start = css.index(".combo .cb{")
        applied = css[start:css.index("}", start)]
        self.assertIn("background:var(--picked)", applied)
        self.assertNotIn("dashed", applied)
        # 没有 JS 会挂 .act，留着只会让人以为选中态有两套写法。
        self.assertPageLacks(".pill.act{")

    def test_one_tag_wears_one_face_everywhere_it_shows_up(self):
        """标签只有一张脸：同一档圆角、一圈线、同一块填充、同一档字色。

        同一个词出现在卡片上、详情面板里、首页筛选条上和交集条里。四处各画各的时——
        交集条 4px 方角实心、筛选条 8px 描边、卡片整圆、详情面板 8px 加一层自己的
        面——读的人得先认出这是四种控件，再想明白它们说的是同一件事。用户点名以详情
        面板那一颗作基底，Board 主题下就是 8px 那一档，所以 `--tag-radius` 在这套里是
        8px，五处（连标签骨架）跟着一个 token 走。

        填充是唯一允许分叉的一处，因为它承担状态：陈述事实的那两处（卡片、详情面板）
        用 `--tag-fill`，已经加上去的筛选用 `--picked`，玻璃条上还没加的那些留透明，
        底下那块玻璃就是它的面。形状、边和字色不参与表意。
        """
        css = stylesheet_source()
        self.assertIn("--tag-fill:color-mix(in srgb,var(--surface) 82%,var(--ground));", css)
        for base in (".detailtag", ".tg"):
            start = css.index(chr(10) + base + "{")
            rule = css[start:css.index("}", start)]
            self.assertIn("border-radius:var(--tag-radius)", rule, f"{base} 取同一档圆角")
            self.assertIn("1px solid var(--line)", rule, f"{base} 画一圈线")
            self.assertIn("background:var(--tag-fill)", rule, f"{base} 共用同一块填充")
        # 字色：卡片那颗自己带，详情面板那颗落在里面那两枚按钮上。
        self.assertIn("color:var(--ink-2)", css[css.index("\n.tg{"):css.index("}", css.index("\n.tg{"))])
        self.assertPageContains(".detailtag button{border:0;background:transparent;color:var(--ink-2);")
        start = css.index(".combo .cb{")
        applied = css[start:css.index("}", start)]
        self.assertIn("border:1px solid var(--line)", applied)
        self.assertIn("border-radius:var(--tag-radius)", applied)
        self.assertIn("color:var(--ink-2)", applied)
        self.assertIn("min-height:30px", applied, "跟详情面板那一颗同样高")
        self.assertIn("background:var(--picked)", applied, "填充说的是这条已经加上去了")
        self.assertNotIn("var(--badge-radius)", applied, "它是标签不是元信息标记")
        # 移除键跟详情面板那颗同一副身量与同一种反馈：28px 方格，悬停转成撤销的红。
        self.assertPageContains(".combo .cb b{display:grid;place-items:center;width:28px;height:28px;")
        self.assertPageContains(
            ".combo .cb b:hover{color:var(--drop);background:color-mix(in srgb,var(--drop) 12%,transparent)}")
        # Board 这套的标签是圆角方片，一个 token 定死；详情面板那颗不再自带一份圆角和面。
        board = (Path(__file__).resolve().parents[1] / "web" / "board.css").read_text(encoding="utf-8")
        self.assertIn(":root{--tag-radius:8px}", board)
        self.assertNotIn(".detailtag{", board, "基底那颗的脸归 --tag-fill 与 --tag-radius 管")
        # 筛选条与资料页那两排也从同一个 token 取形状，只有描边换成玻璃上的那一档。
        self.assertIn(".board-filter-frame.board-filter-frame .tagbar .pill"
                      ":is([data-tag],[data-follow-tag],[data-follow-provider])"
                      "{border-radius:var(--tag-radius);border-color:var(--glass-low)}", board)
        self.assertIn("border-radius:var(--tag-radius);border:1px solid var(--glass-low)", board)

    def test_the_video_area_has_no_frame_and_the_portrait_strip_shares_the_card_face(self):
        """视频网格不画框：卡片直接摆在页面上，竖屏带和卡片同一张面。

        网格外面那一圈 `--field-ring` 框只是把一屏卡片再圈一次，用户点名去掉；
        卡片本身也不带框。
        """
        self.assertPageLacks(".grid:has(>.card:not(.junkcard))")
        css = stylesheet_source()
        start = css.index(chr(10) + ".card{")
        card = css[start:css.index("}", start)]
        self.assertNotIn("background:", card, "卡片不自带填色")
        self.assertNotIn("border:", card, "卡片不自带描边")
        start = css.index(chr(10) + ".shorts-inline{")
        strip = css[start:css.index("}", start)]
        self.assertIn("background:var(--ground)", strip, "竖屏带和视频段同一张面")
        self.assertNotIn("var(--page)", strip, "底色一退就读成陷进去的一格")

    # 选中态允许高对比反相的两处：都压在媒体画面上，画面本身会把 --hover 那层
    # 7% 白吃掉，读不出按没按。
    INVERTED_PRESSED_ALLOWED = (
        ".hovertools .laterbtn",   # 卡片悬停浮层「稍后看」
        ".tokbtns button",         # 沉浸页右侧竖排动作
        ".followimagedots button",  # 图集页码点
    )

    def test_pressed_states_lift_the_fill_instead_of_inverting_to_a_white_slab(self):
        """选中态是抬一档的面，不是反相白块。

        2026-09-03 实测 Geist：Switch 的选中项只是把 `#0A0A0A` 的容器面抬到
        `#1A1A1A`，Tabs 是墨色文字加下划线，Checkbox 是墨底白勾——整套里没有一处
        把控件刷成浅色实底。Peach 此前给所有 `aria-pressed="true"` 上 `--ink-2`
        (#C9CDD4) 底 `--ground` 字，一排筛选里被选中的那颗比主动作还抢眼。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(),
                     flags=re.S)
        self.assertNotIn("background:var(--ink-2)", css,
                         "--ink-2 是次级文字色，不该当作任何控件的底色")
        offenders = []
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            leaf, body = match.group(1).strip().split("{")[-1], match.group(2)
            if not any(state in leaf for state in (
                    'aria-pressed="true"', 'aria-selected="true"', "aria-current",
                    ".selected", ".picked")):
                continue
            if "background:var(--ink)" not in body:
                continue
            # 伪元素画的是 Tabs 那条 2px 墨色下划线，不是控件的面。
            if ":after" in leaf or ":before" in leaf:
                continue
            if any(allowed in leaf for allowed in self.INVERTED_PRESSED_ALLOWED):
                continue
            offenders.append(leaf)
        self.assertEqual(offenders, [],
                         f"选中态请改 --hover 底 --ink 字，别刷成浅色实底：{offenders}")

    def test_hover_lifts_the_fill_and_leaves_the_border_alone(self):
        """悬停只抬填充，不动边框。

        取自 Geist Button 的源规则（站点样式表 `0p9r363b8n-x2.css`）：primary
        `#EDEDED→#ccc`、secondary `#0A0A0A→--ds-gray-200`、ghost 走
        `--ds-gray-alpha-200`，没有任何一条 hover 改 border 或 ring。Peach 此前把边
        提到墨色 28%（`.fbtn` 甚至提到 `--ink-2`，接近 79% 白），一排按钮里被鼠标
        扫过的那颗看着像是被选中了。墨色 28% 的边现在只剩输入框一处。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(),
                     flags=re.S)
        offenders = []
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            leaf, body = match.group(1).strip().split("{")[-1], match.group(2)
            if ":hover" not in leaf:
                continue
            # 输入框不在此列：Geist Input 的悬停确实提边，靠边框告诉你哪个域可以写。
            if "search" in leaf or "input" in leaf:
                continue
            edge = re.search(r"border-color:([^;}]+)", body)
            if not edge:
                continue
            value = edge.group(1).strip()
            # 语义色（危险、标签本色）和主动作掉一档不算提边，它们换的是色相不是亮度。
            if value in ("var(--ink-2)",
                         "color-mix(in srgb,var(--ink) 28%,transparent)"):
                offenders.append(leaf)
        self.assertEqual(offenders, [],
                         f"这些 hover 在提亮边框，请改成只抬 background：{offenders}")

    def test_a_solid_tier_hover_spells_out_its_own_text_colour(self):
        """把填充换成实心一档的悬停规则必须自己写 `color`，不能指望静止那条留下来。

        `:hover` 只声明 background 时，同一组里更宽的通用悬停（`.tagselection
        button:hover`、`.junkactions button:hover` 都是）会把文字提到 `--ink`：
        它的选择器更弱，可 `color` 在实心档自己这条里没有对手，于是深色实底上落成
        深字深底，鼠标一压按钮上的字就没了。2026-09-04 用户在关注管理页第二次遇到
        同一个坑；靠「静止那条特指度更高」挡着不算数，那是算出来的巧合，加一条更宽的
        悬停就翻。
        """
        sources = [stylesheet_source(),
                   (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8"),
                   (Path(__file__).resolve().parents[1] / "web/board-entry.css").read_text(encoding="utf-8")]
        # 只看换成实心强调档或危险档的那几条：次级档的悬停压的是同一块面上的 8% 墨，
        # 文字色本来就不该跟着动。
        # `--board-blue-*` 与 `--color-accent-*` 现在由强调色那一组色阶给，实心档因此
        # 有三种写法：三档渐变、直接写 `linear-gradient(`，以及单取一级色阶当底。
        filled = re.compile(r"background:(var\(--board-blue-(hover|active)\)"
                            r"|var\(--color-accent-\d+\)|linear-gradient\()")
        offenders = []
        seen = 0
        for source in sources:
            css = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
            for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
                leaf, body = match.group(1).strip().split("{")[-1], match.group(2)
                if ":hover" not in leaf or not filled.search(body):
                    continue
                if ".pcheck" in leaf:
                    continue  # 勾选框里是一根勾线，没有字要保。
                seen += 1
                if not re.search(r"(?<![-\w])color:", body):
                    offenders.append(leaf)
        self.assertEqual(offenders, [],
                         f"实心档悬停请自己写 color，别把文字交给通用 hover：{offenders}")
        self.assertGreaterEqual(seen, 3, "实心档的悬停规则找不到了，检查断言是否还匹配得上")

    # 悬停允许照旧抬填充的两类控件。孤立开关：没有并排的同类邻居，鼠标压着的那颗
    # 就是你正在问的那颗，看不出「按没按」不构成误读。侧栏导航：Geist 自己就把分工
    # 反过来写，见 test_sidebar_nav_keeps_the_hover_fill_and_leaves_state_to_the_color。
    HOVER_FILL_ALLOWED = (
        ".ib",              # 顶栏图标按钮，八个里只有一个有按下态
        ".brandpill",       # 顶栏厂牌胶囊，全站一颗
        ".playerstatsbtn",  # 播放器覆盖层，悬停走 ::after 另一层
        ".fb .like",        # 这一排彩色反馈按钮的既有约定就是悬停预览按下后的颜色
        ".tagpickitem",     # 选中由图标换成对勾表达，填充留给悬停与键盘游标
        ".popmenu.gselectmenu button",  # 同上；2026-09-04 实测 vercel.com 后台的菜单行，悬停与选中共用同一枚 5% 填充
        ".edge button",     # 窄栏，实测 vercel.com/geist 左栏就是悬停抬填充
        ".dnav button",     # 抽屉是窄栏的展开态，同一条例外
    )

    STATE_TOKENS = ('[aria-pressed="true"]', '[aria-selected="true"]',
                    '[aria-current="page"]', '[aria-current="true"]', ".selected")

    def _leaf_rules(self):
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(),
                     flags=re.S)
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            yield match.group(1).strip().split("{")[-1], match.group(2)

    def test_selected_states_carry_no_ring_no_lifted_border_and_no_extra_weight(self):
        """选中态只有填充，不加边、不加内嵌一圈线、不加字重。

        2026-09-03 用户指出侧栏当前项在 Vercel 里既没有边框线也没有加粗。核对
        Geist 的类名（`class` 里的 Tailwind 前缀就是规则原文，不受悬停取证的限制）：
        Switch 分段项 `peer-checked:` 下只有 `text` 与 `bg`，`font-medium` 两态常驻；
        Tabs secondary 只有 `aria-selected:bg-gray-200` 与 `aria-selected:text-gray-1000`。
        我们此前那套「无边框补 inset 一圈、带边框提到墨色 28%、还要更强就加字重」
        是自造的强调阶梯，三个组件里一条都找不到。彩色标签控件的语义色边框不在此列，
        它换的是色相不是亮度。
        """
        offenders = []
        for leaf, body in self._leaf_rules():
            if not any(state in leaf for state in self.STATE_TOKENS):
                continue
            if ":after" in leaf or ":before" in leaf:
                continue
            # 只拦控件上那圈中性发丝线。压在缩略图上的 2px 白框（`.card.selected .pic`）
            # 是另一回事：媒体画面吃掉 7% 的填充，选中只能靠取景框描边。
            if "box-shadow:inset 0 0 0 1px var(--border-15)" in body:
                offenders.append((leaf, "inset 一圈线"))
            if "color-mix(in srgb,var(--ink) 28%" in body:
                offenders.append((leaf, "墨色 28% 提边"))
            if "font-weight" in body:
                offenders.append((leaf, "字重加档"))
        self.assertEqual(offenders, [],
                         f"选中态只留 --picked 底 --ink 字：{offenders}")

    def test_hover_yields_the_fill_to_selection_inside_a_group(self):
        """一组互斥选项里，填充专属选中，未选中项悬停只提文字色。

        去掉边框与字重之后，`:hover` 和 `[aria-pressed="true"]` 都是 `--hover`，
        鼠标划过邻居时就分不出哪个是当前项了。Geist 的解法在这三个组件里一致：
        `hover:text-[var(--ds-gray-1000)]`、`not-disabled:hover:text-gray-1000`——
        悬停只改文字色，背景留给 checked／aria-selected。这与 Button 的「悬停只抬
        填充」不冲突：Button 没有选中态，没有需要让位的信号。

        适用面只到「一排横向的选项组」。2026-09-04 实测证明侧栏导航不在此列，Geist
        自己把分工反过来写，见 HOVER_FILL_ALLOWED 里的两条和下一个测试。
        """
        selected_bases = set()
        for leaf, body in self._leaf_rules():
            if not any(fill in body for fill in
                       ("background:var(--hover)", "background:var(--picked)")):
                continue
            for part in leaf.split(","):
                part = part.strip()
                for state in self.STATE_TOKENS:
                    if part.endswith(state):
                        selected_bases.add(part[: -len(state)].strip())
        self.assertIn(".chip", selected_bases, "基线选择器没被认出来，测试本身失效了")
        self.assertIn(".pill", selected_bases, "换成 --picked 的那一批也要留在基线里")
        offenders = []
        for leaf, body in self._leaf_rules():
            if ":hover" not in leaf or "background:var(--hover)" not in body:
                continue
            for part in leaf.split(","):
                part = part.strip()
                if not part.endswith(":hover"):
                    continue
                base = part[: -len(":hover")].strip()
                if base in selected_bases and base not in self.HOVER_FILL_ALLOWED:
                    offenders.append(part)
        self.assertEqual(sorted(offenders), [],
                         f"这些控件有选中态，悬停请只提文字色到 --ink：{offenders}")

    #: 选中仍旧填 --hover 的全部去处：它们自己就站在 --ground 上，白面上再叠白等于没填。
    SELECTED_ON_GROUND = (
        '.chip[aria-pressed="true"]',                     # 抽屉是一整张磨砂近白面
        '.dnav button[aria-pressed="true"]',              # 同上，窄栏的展开态
        '.edge button[aria-pressed="true"]',              # 窄栏填 --ground
        '.glowpill[aria-pressed="true"]',                 # 色系胶囊站在色板弹层上，弹层填 --ground
        '.popmenu.gselectmenu button[aria-selected="true"]',  # 浮层菜单填 --ground
        '.ib[aria-pressed="true"]',                       # 顶栏填 --ground
        '.managebar button[aria-pressed="true"]',         # 管理导航容器填 --ground
        '.playerstatsbtn[aria-pressed="true"]',           # 播放器蒙层恒为深色
        '.sec.cat-meta .chip[aria-pressed="true"]',       # 抽屉中性类，跟基础 .chip 同一档
        '.sidebaraddmenu button[aria-selected="true"]',   # 浮层菜单
        ".tagpickitem.selected",                          # 选中由对勾表达，填充只是陪衬
    )

    def test_the_selected_face_is_one_token_that_flips_with_the_theme(self):
        """选中填 --picked，它就是 --inset 那一档中间色，两个主题各取各的值。

        判据是「跟脚下那张面不同」，不是「更亮」：选中格多半站在白卡上，往亮里填等于
        白叠白，一排 tab 里哪一枚被选中读不出来。2026-09-04 实测 vercel.com/geist 的
        Tabs：选中态只有一件事，`bg-gray-200`（#EBEBEB），比容器往下压一档。深色一档
        叠 9% 白后本来就比面亮，同一个 token 两边都成立，三处声明写法完全一致。

        例外只有一类：控件自己就站在 --ground 上（顶栏、窄栏、抽屉、浮层菜单）。那里
        选中靠 --hover 那一档暗加上 --ink 的字色，与实测的 Geist 左栏一致。这一类逐个
        登记在 SELECTED_ON_GROUND。
        """
        css = stylesheet_source()
        self.assertEqual(css.count("--picked:var(--inset);"), 3,
                         "浅色一处、深色两处（prefers-color-scheme 与 data-theme）各写一份")
        self.assertIn("--inset:#EBEBEB;", css, "浅色一档就是 Geist 的 gray-200")
        self.assertIn("--inset:rgba(255,255,255,.09);", css, "深色一档在面上叠一层白")
        self.assertNotIn("--picked:#", css, "选中面不写字面色，只引用已有的那张中间面")
        on_ground = sorted(" ".join(leaf.split()) for leaf, body in self._leaf_rules()
                           if any(state in leaf for state in self.STATE_TOKENS)
                           and "background:var(--hover)" in body)
        self.assertEqual(on_ground, sorted(self.SELECTED_ON_GROUND),
                         "站在 --page 或凹槽上的选中态一律填 --picked；"
                         "要留 --hover 的先登记进 SELECTED_ON_GROUND 并说明它脚下是哪张面")

    def test_the_duration_slider_is_a_control_in_ink_not_a_blue_progress_bar(self):
        """时长拉条走墨色：已选段 --ink，抓手填 --ground、描 --ink，蓝只剩焦点环。

        抓手必须填 --ground 而不是 --ink：--ink 自己也随主题翻面，深色下是白点、浅色下
        就成了压在轨道上的黑疙瘩，同一个控件读出两种东西。填 --ground 则两档同义——
        抓手永远和它坐落的那张面同色，读作从轨道上抠下来的一段。
        """
        self.assertPageContains(
            ".range-fill{left:var(--lo);right:calc(100% - var(--hi));background:var(--ink)}")
        for thumb in ("::-webkit-slider-thumb", "::-moz-range-thumb"):
            start = self.page.index(".dual-range input" + thumb + "{")
            rule = self.page[start:self.page.index("}", start)]
            self.assertIn("background:var(--ground)", rule, thumb + " 抓手跟着主题翻面")
            self.assertIn("border:2px solid var(--ink)", rule, thumb + " 描边是墨色")
        self.assertPageContains(
            ".dual-range input:focus-visible::-webkit-slider-thumb"
            "{outline:2px solid var(--tungsten);outline-offset:2px}")

    def test_the_star_rating_sits_between_the_title_and_the_spec_line(self):
        """五颗星在标题和那行规格之间，送出的是 20 的倍数，空实两档随主题各写各的琥珀。

        位置不是随手挑的：评分是对这一条作品的判断，和番号、标题一样属于它的身份，
        而反馈条那一排说的是「怎么处置它」（不合口味、看过、回收站）。两者混在一起，
        「我给它几分」就会读成又一个处置动作。

        再点当前那一颗是撤销，送 0；后端写回 NULL。悬停预演到指针那一颗，靠
        `:has(~ .star:hover)` 选中它左边的几颗——把 DOM 倒过来写也能做到同一件事，
        代价是 Tab 与读屏顺序跟着倒过来，五颗星从「评为 5 星」开始念。
        """
        self.assertPageContains("const RATING_STEP=20;")
        self.assertPageContains(
            """      ${it.location==='online'?'':`<span class="srcstate detailtitlestate" aria-live="polite"></span>`}
      ${ratingHtml(it.rating)}
      <div class="smeta mono" data-reveal-line>""")
        self.assertPageContains(
            "const value=picked===before?0:picked;")
        self.assertPageContains(
            "api('/api/feedback',{method:'POST',body:JSON.stringify({id:it.id,kind:'rate',value})})")
        self.assertPageContains("{undo:()=>postRating(before)}")
        # 标签是语义契约：撤销那一颗要说清它现在是几星，否则读屏只听到「星」。
        self.assertPageContains(
            "aria-label=\"${n===on?`取消评分（当前 ${n} 星）`:`评为 ${n} 星`}\"")
        self.assertPageContains('<symbol id="i-star" viewBox="0 0 24 24">')
        self.assertPageContains('.ratingstars .star[data-on="true"] svg{fill:currentColor}')
        self.assertPageContains(
            ".ratingstars:hover .star:hover svg,"
            ".ratingstars:hover .star:has(~ .star:hover) svg{fill:currentColor}")
        # 整排一种颜色，评没评只看填不填；换色那一档在浅色主题下凑不出两级都成立的灰。
        start = self.page.index(".ratingstars .star{")
        self.assertIn("color:var(--rating)", self.page[start:self.page.index("}", start)])
        self.assertPageLacks('.ratingstars .star[data-on="true"]{color:')
        self.assertPageLacks(".ratingstars:hover .star{color:")
        # 对齐按印出来的星形算：26px 的命中区里是 19px 的星，星形在 24 格视区里从第 2 格
        # 起笔，第一颗星的墨因此比标题的左边线右了约 4px；上边同样多出标题末行的行距。
        self.assertPageContains(".rating{display:flex;align-items:center;gap:8px;margin:-6px 0 10px}")
        self.assertPageContains(
            ".ratingstars{display:inline-flex;align-items:center;gap:2px;margin-left:-4px}")
        # 这个 token 两档各写各的值：借 --line 只在深色底上成立。
        self.assertIn("--rating:#B8860B;", self.css, "浅色一档的琥珀要压得住 #FAFAFA 的页面底")
        self.assertEqual(
            self.css.count("--rating:#E5B34A;"), 2,
            "深色两处声明（prefers-color-scheme 与 data-theme）各写一份")

    def test_every_button_in_the_feedback_bar_owns_a_hover_color(self):
        """详情页反馈条上每一枚都有自己的悬停配色，兜底填充用 token 不写死白。

        写死的 rgba(255,255,255,.12) 只在深色底上成立，浅色一档压在白面上什么都不发生；
        漏写配色的那一枚还会全程停在 --muted，看着像它不能点。加入播放列表开的是弹层、
        没有按下态，所以只有悬停这一档，和喜欢同走中性墨色——这一排的色相各自指向一种
        判断（红=不合口味、绿=看过、橙=回收），整理动作不占色相。
        """
        self.assertPageContains(".fb button:hover{transform:none;background:var(--hover)}")
        self.assertPageContains(".fb .fdownload:hover{background:var(--hover);color:var(--ink)}")
        self.assertPageContains(".fb .playlistadd:hover{color:var(--ink);background:var(--hover)}")
        for leaf, body in self._leaf_rules():
            if leaf.startswith(".fb"):
                self.assertNotIn("rgba(255,255,255", body, leaf + " 的填充写死了白，浅色一档不成立")
        buttons = {"like", "reason", "dislike", "seen", "dispose", "later", "upgrade", "playlistadd"}
        missing = {name for name in buttons if ".fb ." + name + ":hover" not in self.page}
        self.assertEqual(missing, set(), f"这几枚只能吃兜底填充，图标不换色：{missing}")

    def test_sidebar_nav_keeps_the_hover_fill_and_leaves_state_to_the_color(self):
        """侧栏窄栏与抽屉的悬停必须抬填充，当前项靠图标色区分。

        2026-09-04 实测 vercel.com/geist 左栏（`aside` 里那 82 条链接，读的是每条
        链接内层 `span` 的计算值与类名）：

        | 状态 | 背景 | 文字 |
        | --- | --- | --- |
        | 未选中 | `rgba(0,0,0,0)` | `rgb(161,161,161)` |
        | 未选中 + 悬停 | `rgb(26,26,26)`（`hover:bg-gray-100`） | `rgb(161,161,161)` 不动 |
        | 当前项 | `rgba(255,255,255,.06)`（`bg-gray-alpha-100`，无 hover 类） | `rgb(237,237,237)` |

        分工与横排选项组正好相反：填充表示「鼠标在这儿」，文字色才表示「你在这儿」。
        两个填充的合成亮度几乎相同（10% 对 9.4%），可见 Geist 并不指望用填充强弱
        区分二者。纯图标窄栏更需要这条：52px 方块里只有一个描边图标，光靠 --muted
        到 --ink 的换色近乎看不见，等于窄栏没有悬停反馈。

        这条曾被删过一次（`1367a9a` 把横排选项组的结论推广到了侧栏），所以这里用
        正向断言锁住，不只依赖 HOVER_FILL_ALLOWED 的豁免。
        """
        self.assertPageContains(".edge button:hover{background:var(--hover)}",
                                "窄栏悬停必须抬填充")
        self.assertPageContains(".dnav button:hover{background:var(--hover)}",
                                "抽屉是窄栏的展开态，走同一条")
        # 悬停不得把图标/文字提到 --ink：那是当前项的信号，抢过来两态就分不开了。
        self.assertPageLacks(".edge button:hover{color:var(--ink)}")
        self.assertPageLacks(".dnav button:hover svg{color:var(--ink)}")
        # 当前项这一侧必须仍然握着颜色，否则悬停和选中就真的同色了。
        self.assertPageContains('.edge button[aria-pressed="true"]'
                                "{background:var(--hover);color:var(--ink)}")
        self.assertPageContains('.dnav button[aria-pressed="true"]'
                                "{background:var(--hover);color:var(--ink)}")

    def test_form_buttons_do_not_shrink_on_press_and_disable_to_a_solid_gray(self):
        """表单里那一族按钮按下不缩放，禁用是实底灰而不是半透明。

        同一次实测：Geist Button 页面上全部按钮的 `transform` 都是 `none`。一屏表单上
        七八个按钮排在一起，各自按下去弹一下，读起来是整页在抖；缩放留给手指直接拨的
        那几类——竖屏那一条上的换一批、沉浸态右下角那一列。

        禁用则是 `rgb(26,26,26)` 底、`rgb(143,143,143)` 字、1px `rgb(46,46,46)` 环、
        `opacity:1`；半透明会让按钮连同它下面的底色一起变淡，在深色卡片和浅色卡片上
        淡出的程度还不一样。

        光标是 `not-allowed`（2026-09-07 复测，透明底的 tertiary 那档也是）。`default`
        说的是「这里没有交互」，禁用要说的是「有交互，现在不给」：移上去有没有那个禁止
        符号，是用户唯一能在点下去之前分辨这两件事的线索。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(),
                     flags=re.S)
        pressed = sorted(chunk.rsplit("}", 1)[-1].strip()
                         for chunk in css.split("{scale:.96")[:-1])
        self.assertEqual(pressed, [".shorts-inline h2 button:active", ".tokbtns button:active"],
                         "按下缩放只给手指直接拨的控件，表单按钮那一族不动")
        # 描边那一档连边一起变灰；不描边的动作按钮只换填充和字色。
        ringed = ("{background:var(--sunk);border-color:var(--line-soft);"
                  "color:var(--muted);cursor:not-allowed}")
        flat = "{background:var(--sunk);color:var(--muted);cursor:not-allowed}"
        for selector in (".srctools button:disabled",):
            self.assertPageContains(selector + ringed)
        for selector in (".geist-button:disabled", ".fbtn:disabled",
                         ".resourceaction:disabled", ".tagselection button:disabled"):
            self.assertPageContains(selector + flat)

    def test_the_secondary_tier_keeps_a_one_pixel_ring_so_it_reads_on_its_own_ground(self):
        """次级按钮挂一圈 1px 环，实心的三档不挂。

        2026-09-07 复测 vercel.com/geist/button：次级填 `#FFFFFF`、环
        `rgb(235,235,235) 0 0 0 1px`，primary（`#171717` 实底）、error、warning 三档
        `box-shadow:none`，禁用档填 `#F2F2F2`、字 `#8F8F8F`、环仍在。
        环用 `box-shadow` 而不是 `border`：不占盒子，和并排的实心档外沿仍然齐平。

        这一圈不是装饰。次级填的是 `--ground`，而面板、卡片和框体本身也是 `--ground`，
        「添加文件夹」「选择文件夹」这类键直接坐在上面，两块同色，没有环就一条边都
        读不出来——暗色一档 `--ground` 是 `#080A0D`，整颗键化在面里。换成实底亮色能看见，
        但那会让一颗次要动作抢过主动作的份量，所以照 Geist：填充不动，补一圈线。
        """
        ring = "box-shadow:0 0 0 1px var(--line-soft)"
        css = stylesheet_source()
        # 同一档的四个写法都得有环，否则一屏里同档按钮一半有边一半没边。
        for name in (".geist-button{", ".fbtn{", ".resourceaction{",
                     ".cleanupfieldset button:where(:not(.gselectfield)){"):
            found = re.search(r"(?:^|[}\n])" + re.escape(name), css)
            self.assertIsNotNone(found, f"{name} 找不到基样式")
            start = found.end() - len(name)
            rule = css[start:css.index("}", start)]
            self.assertIn(ring, rule, f"{name} 次级档要有那一圈 1px 环")
        # 实心档自己的填充就是边界，再挂环会在实底外面描出第二道轮廓。强调档不在这一层：
        # 它那一面连同 `box-shadow` 由 `board.css` 一处给（`test_the_primary_tier_has_one_face_and_crossfades_into_its_hover`）。
        for solid in (".geist-button.error{background:#da2f35;color:#fff;box-shadow:none}",
                      ".geist-button.warning{background:#ff990a;color:#000;box-shadow:none}"):
            self.assertPageContains(solid, "实心档不挂环")
        # 禁用把所有档收成同一块灰面，环要跟回来，否则禁用的主动作连轮廓都没有。
        for restored in (".geist-button.primary:disabled{background:var(--sunk);"
                         "color:var(--muted);" + ring + "}",
                         ".geist-button:is(.error,.warning):disabled{background:var(--sunk);"
                         "color:var(--muted);" + ring + "}",
                         "background:var(--sunk);color:var(--muted);" + ring + "}"):
            self.assertPageContains(restored, "禁用档的环要回来")
        # 悬停只动填充：Geist 的源规则里没有任何按钮 hover 改 border 或 ring。
        self.assertNotIn("box-shadow", css[css.index(".geist-button:hover:not(:disabled){"):
                                           css.index(".geist-button,.geist-button:hover{")],
                         "悬停不动那圈环")

    def test_every_button_filled_with_ground_carries_that_ring(self):
        """凡是填 `--ground` 的可点控件都要有一条 1px 的边，名单之外的也算。

        上一条按名单守四个写法，名单外的几处照样没边：关注页的动作键、重复页的操作条、
        评审的选片头、首页的标签选择条、垃圾卡的三颗动作、沉浸浮条。
        它们填的都是 `--ground`，又坐在同为 `--ground` 的卡片和面板上，暗色一档
        `#080A0D` 压在 `#080A0D` 上，整颗键化在面里。所以这里不数名单，直接扫。

        `.splitbutton>button` 是唯一的例外，环挂在 `.splitbutton` 盒子上——两半各挂
        一圈会在交界处与那根竖线叠成两条。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(), flags=re.S)
        exempt = {".splitbutton>button"}
        scanned = []
        for rule in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            selector = rule.group(1).strip().splitlines()[-1].strip()
            body = rule.group(2)
            if "background:var(--ground)" not in body or "cursor:pointer" not in body:
                continue
            if selector in exempt:
                continue
            self.assertTrue(
                "box-shadow:0 0 0 1px" in body or "border:1px solid" in body,
                f"{selector} 填 --ground 又没有边，坐在同色的面上就看不见了")
            scanned.append(selector)
        self.assertIn(".fbtn", scanned, "扫描要真的覆盖到关注页那组")
        start = css.index(".splitbutton{")
        self.assertIn("box-shadow:0 0 0 1px var(--line-soft)",
                      css[start:css.index("}", start)], "拆分按钮的环挂在盒子上")

    def test_disabled_controls_show_the_forbidden_cursor(self):
        """禁用的控件移上去是禁止符号，不是普通箭头。

        `cursor:default` 说的是「这里没有交互」，禁用态要说的是「有交互，现在不给」。
        站里曾有 14 处禁用规则写着 `default`：卸载按钮、静默启动那颗联动开关、侧栏
        排序的上下移动都在其中，看上去和一颗普通的静态方块没有区别。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(), flags=re.S)
        stale = re.findall(r"[^{}\n]*:disabled[^{]*\{[^}]*cursor:default[^}]*\}", css)
        self.assertEqual(stale, [], "禁用规则里不许再写 cursor:default")
        for selector in (".geist-button:disabled", ".fbtn:disabled", ".resourceaction:disabled",
                         ".gselectfield:disabled", ".sidebaradd .sidebaraddfield:disabled"):
            start = css.index(selector + "{")
            self.assertIn("cursor:not-allowed", css[start:css.index("}", start)],
                          f"{selector} 要给出禁止光标")

    def test_a_disabled_toggle_reads_grey_even_when_it_is_on(self):
        """开着又被禁的开关必须是灰的，不能还留着那抹蓝。

        「静默启动」只在「开机后启动 Peach」打开时才有意义，所以后者关着时它拿到
        `disabled`。可轨道此前照旧是蓝的，只有标签变灰：Toggle 的选择器写成
        `:is(#censorSetting,#detailAutoplaySetting,.ptoggle)`，而 `:is()` 取的是里面
        最强那一项的权重——混一个 id 进去，整组就是 (1,1,0)，同文件末尾追加的
        `.ptoggle:disabled` (0,2,0) 再也压不过 `:checked`。选择器里不许再有 id。
        """
        css = stylesheet_source()
        self.assertNotIn("#censorSetting", css, "Toggle 的样式不靠 id 选中")
        self.assertNotIn("#detailAutoplaySetting", css, "Toggle 的样式不靠 id 选中")
        self.assertPageContains(".ptoggle:disabled{background:var(--surface);cursor:not-allowed}")
        self.assertPageContains(".ptoggle:disabled::after{background:var(--muted)}")
        self.assertPageContains(".ptoggle:disabled:checked{background:var(--surface)}")
        # 禁用要写在开态之后，同权重下后写的赢。
        self.assertLess(css.index(".ptoggle:checked{"), css.index(".ptoggle:disabled{"),
                        "禁用规则排在开态之后才压得住它")
        # 两颗用 id 接线的开关也得带上这个类，否则它们一条样式都拿不到。
        for line in ('class="ptoggle" type="checkbox" id="censorSetting"',
                     'class="ptoggle" type="checkbox" id="detailAutoplaySetting"'):
            self.assertPageContains(line)

    def test_every_disclosure_title_carries_the_same_chevron(self):
        """折叠标题前面都有一枚 16px chevron，展开转 90°，全站一个写法。

        没有它的标题只是一行普通粗体字：`wireCollapse` 把原生 `<details>` 的三角
        `list-style` 去掉了（不去掉的话它和布局里的 flex 对不齐），于是「点这里会展开」
        这件事没有任何视觉线索，得靠鼠标移上去变成手型才发现。几何取自 Vercel：
        16px 字形、`stroke:currentColor`、展开转 90°，并且转要渐变。这一枚由
        `src/react/settings/section.tsx` 的 `Disclosure` 给，站里的折叠标题共用它。
        """
        section = self.read_react("settings/section.tsx")
        self.assertIn("import { RiArrowRightSLine, RiExternalLinkLine } from '@remixicon/react';", section)
        self.assertIn("className={open ? 'size-4 shrink-0 rotate-90 transition-transform'"
                      " : 'size-4 shrink-0 transition-transform'}", section)
        # 折叠态要报给读屏，展开的是哪一块也要指名。
        self.assertIn("<summary aria-expanded={open} aria-controls={id} onClick={toggle}", section)
        # 原生三角去掉了，所以这一枚字形是唯一的线索，不能连它一起去掉。
        self.assertIn("list-none", section)
        # 侧栏分组折叠还在旧壳里，转的角度与方向跟这一枚对齐。
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-section-toggle[aria-expanded=true] svg{transform:rotate(90deg)}", board)

    def test_a_spinner_announces_the_work_and_not_the_button_it_sits_in(self):
        """`spinnerHtml()` 的名字说正在做什么，不复读按钮自己的名字。

        这个 span 是 `role="status"`，装在一颗已经有可访问名的按钮里。传按钮名进去，
        屏幕阅读器就把同一串词念两遍——「换一批」「换一批」——读的人听不出发生了变化。
        Geist 的 Spinner 规格把这一条写成「等待超过约 1 秒要配上说明这次在做什么的
        文案」，所以判据是动词形态：进行中的说法，不是动作的名字。
        """
        source = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(
            encoding="utf-8")
        labels = re.findall(r"spinnerHtml\('([^']+)'\)", source)
        self.assertGreaterEqual(len(labels), 10, "调用点少得不像全站都在用")
        ongoing = ("正在", "中", "…")
        for label in labels:
            self.assertTrue(label.endswith(ongoing) or label.startswith("正在"),
                            f"「{label}」是动作名，不是进行中的说法")

    def test_the_danger_tier_is_defined_once_and_pages_do_not_re_state_it(self):
        """销毁键的红、悬停深一档和禁用灰只在 01-base 写一次，页面文件不再写第二份。

        写第二份的代价不是重复几行，是两份会悄悄分叉。配置页那一份把悬停压到
        `88%,#000`（01-base 是 `82%`），禁用填 `--surface`（01-base 是 `--sunk`）且不带
        环——「卸载 Peach」和弹层里的确认键于是和站内其他销毁键读起来不是一套，而它
        选择器更长、文件又在后面，永远赢。同一形状在 `.configrm` 上已经出现过一次。

        所以这里查两遍。只按选择器里有没有 `danger` 查的话，换个类名就绕过去了：
        `.junktrash` 和 `.fbtn.fquiet` 这类红底键各自填过同一块 `--drop`，选择器里一个
        `danger` 也没有。第二遍改按声明查——实底红配纯白字就是销毁档的样子，无论选择器
        叫什么。
        """
        css = stylesheet_source()
        base = Path(__file__).resolve().parents[1] / "web/css/01-base.css"
        for declaration in ("background:var(--drop);color:#fff",
                            "background:color-mix(in srgb,var(--drop) 82%,#000)",
                            "background:var(--sunk);color:var(--muted)"):
            self.assertIn(declaration, base.read_text(encoding="utf-8"),
                          "危险档的定义在 01-base")
        # 提到 `.danger` 又自己填背景的规则，全站只准有 01-base 那三条。
        restated = [rule for rule in re.findall(r"[^{}\n]*\{[^}]*\}", css)
                    if ".danger" in rule.split("{")[0]
                    and "background:" in rule.split("{", 1)[1]]
        self.assertEqual(len(restated), 3, "危险档又被写了第二份：\n"
                         + "\n".join(rule.split("{")[0] for rule in restated))
        for rule in restated:
            self.assertNotIn("border-color", rule, "危险档不画边，这条 border-color 是死的")
        # 禁用的键填 `--sunk` 再补一圈环；`--surface` 是输入框和轨道那一档的禁用底，
        # 两者不通用，所以这里只查危险档自己有没有换掉那块灰。
        disabled = next(rule for rule in restated
                        if rule.split("{")[0].rstrip().endswith(":disabled"))
        self.assertIn("background:var(--sunk)", disabled)
        self.assertIn("box-shadow:0 0 0 1px var(--line-soft)", disabled)
        # 第二遍：实底红配纯白字的规则，只准是危险档和 Geist 的 error 变体，且都在 01-base。
        # `--drop` 当状态点或低透明度衬底不在此列——那些地方的字色
        # 不是 `#fff`，它们标注的是状态，不是一颗按下去就不可逆的键。
        red = re.compile(r"background:(?:color-mix\(in srgb,)?(?:var\(--drop\)|#da2f35)")
        solid = sorted(rule.split("{")[0].strip()
                       for rule in re.findall(r"[^{}\n]*\{[^}]*\}", css)
                       if red.search(rule.split("{", 1)[1])
                       and re.search(r"color:\s*#fff\b", rule.split("{", 1)[1]))
        self.assertEqual(solid, [".geist-button.error",
                                 ".geist-button.error:hover:not(:disabled)",
                                 "button.danger.danger",
                                 "button.danger.danger:hover:not(:disabled)"],
                         "实底红配白字就是销毁档，页面不要用别的类名再填一份：\n"
                         + "\n".join(solid))
        for selector in solid:
            self.assertIn(selector + "{", base.read_text(encoding="utf-8"),
                          f"{selector} 的红要写在 01-base")
            # 键的 `border-width` 是 0，跟着红一起写的 border-color 一行都渲染不出来。
            self.assertNotIn("border-color", css.split(selector + "{", 1)[1].split("}")[0],
                             f"{selector} 里这条 border-color 是死的")

    def test_font_weights_stay_on_the_three_geist_steps(self):
        """字重只有 400／500／600 三档。

        `vercel-report-design`（vercel.com/design.md）明说不要自造数字字重，Geist 本身
        也只发 regular／medium／semibold。收敛前样式表里有 550、650、700、750、800
        五种自造值，同一级标题在不同页面粗细不一，却没有任何一处能说出「为什么这里是 650」。
        """
        css = stylesheet_source()
        weights = sorted(set(re.findall(r"font-weight:\s*([^;}]+)", css)))
        self.assertEqual(weights, ["400", "500", "600", "inherit"],
                         f"字重只能是三档之一，实际出现 {weights}")

    def test_every_border_radius_comes_from_the_radius_vocabulary(self):
        """圆角只有五个语义 token，加上 0 与 50%。

        收敛前样式表写着 1、2、3、5、7、9、10、11、14、16、18、24、28、40px 等
        二十来种字面圆角，相邻两档差一像素，谁也说不清 7 和 8 的区别。现在：
        `--badge-radius` 标记、`--control-radius` 控件、`--surface-radius` 不浮起的
        内嵌表面、`--floating-radius` 浮层与卡片、`--pill-radius` 连续的条与胶囊，
        圆形用 50%。嵌在带边框容器里的头尾条用 `calc(token - 1px)` 保持同心。
        """
        css = stylesheet_source()
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        token = (r"(?:0|50%|inherit|var\(--(?:badge|control|surface|floating|pill|tag)-radius\)"
                 r"|calc\(var\(--(?:surface|floating)-radius\) - 1px\))")
        allowed = re.compile(rf"^{token}(?: {token}){{0,3}}(?:!important)?$")
        offenders = sorted(
            value.strip() for value in re.findall(r"border-radius:\s*([^;}]+)", css)
            if not allowed.match(value.strip()))
        self.assertEqual(offenders, [], f"圆角不在词汇表里：{offenders}")
        self.assertIn("--surface-radius:8px", css)

    def test_every_class_selector_in_the_stylesheet_is_actually_used(self):
        """样式表里的每个类选择器都要有人用它。

        没人用的规则不会报错，只会一直被读、被改、被当成「现在的样子」来推理。
        实测一次就清出九组：`.fdetails` 那一整套折叠摘要、`.mediatabs`、
        `.edge .srcrow`、`.javhint`、`.photosets`、`.meta .whosep`、`.reviewhead`、
        `.resourceerror`——对应的 JS 早就删了或改了名，样式留在原地。

        两类例外，都必须是「前缀 + 运行时拼出来的一段」，不接受逐个类名的豁免：
        vendor 在运行时自己加的类（Video.js、Swiper），以及模板里用模板串拼出来的
        类名（`' cat-'+cat` 这种，源码里不会出现完整的 `cat-artist`）。
        """
        # 注释里会写类名当例子，`url()` 里的域名（www.w3.org）会被当成 `.org`。
        css = re.sub(r"/\*.*?\*/", "", self.css, flags=re.S)
        css = re.sub(r"url\([^)]*\)", "url()", css)
        selectors = set(re.findall(r"\.(-?[A-Za-z_][A-Za-z0-9_-]*)", css))
        vendor = ("vjs-", "swiper-")
        composed = ("cat-", "r34-", "idgroup-", "geist-note-", "skeleton-")
        # 前缀豁免要能兑现：拼接那一处必须真的在模板里。
        for prefix in composed:
            self.assertIn(prefix, self.markup, f"{prefix} 已经没人拼了，连同规则一起删")
        unused = sorted(
            name for name in selectors
            if name not in self.markup and not name.startswith(vendor + composed))
        self.assertEqual(unused, [], f"样式表里有没人用的类选择器：{unused}")

    def test_pill_shapes_are_reserved_for_things_that_are_actually_tags(self):
        """整圆胶囊有一个来源，普通元信息不许长成标签。

        `vercel-report-design` 点名要拒绝的反射之一是「把普通元信息做成胶囊徽章」：
        WIP、变体类型、最大/最长这些是状态标记，做成整圆就跟真标签抢同一种视觉身份，
        用户会以为可以点。它们改用 `--badge-radius`；按钮和分段器用 `--control-radius`
        （实测 Geist 的 6px）；只有真正的标签、筛选令牌和连续的条保留 `--pill-radius`。
        """
        css = stylesheet_source()
        self.assertEqual(re.findall(r"border-radius:9{2,}px", css), [],
                         "整圆一律走 --pill-radius，别再写字面值")
        for selector in (".fbadge{", ".fvkind{", ".dupmarks i{"):
            rule = css[css.index(selector):css.index("}", css.index(selector))]
            self.assertIn("var(--badge-radius)", rule, f"{selector} 是状态标记，不是标签")
        for selector in (".dupactions button,.dupbtns button{", ".indexmore,.entitymore{"):
            rule = css[css.index(selector):css.index("}", css.index(selector))]
            self.assertIn("var(--control-radius)", rule, f"{selector} 是按钮")

    def test_shared_geist_component_tokens_cover_the_whole_shell(self):
        """全站壳层、浮层和普通操作使用同一组语义 token。"""
        css = stylesheet_source()
        self.assertIn("--control-radius:6px; --badge-radius:4px; --floating-radius:12px; --surface-radius:8px", css)
        for selector, token in (
                (".ib{", "var(--control-radius)"),
                (".geist-button{", "var(--control-radius)"),
                (".searchmenu{", "var(--floating-radius)"),
                (".searchoption{", "var(--control-radius)"),
                (".cardmenupanel button{", "var(--control-radius)"),
                (".geist-modal{", "var(--floating-radius)"),
                (".pickrow{", "var(--control-radius)"),
                (".settingscard{", "var(--floating-radius)"),
                (".gselectfield{", "var(--control-radius)"),
        ):
            start = css.index(selector)
            rule = css[start:css.index("}", start)]
            self.assertIn(token, rule, f"{selector} 没使用 {token}")
        self.assertNotRegex(css, r"transition:\s*all(?:[; }])")

    def test_close_actions_share_geist_control_geometry(self):
        css = stylesheet_source()
        # 播放列表那几个弹层没有自己的关闭键：它们穿 Geist Modal，退出走操作条左端的
        # 取消、Escape 和点遮罩，右上角不再另摆一个叉。
        for selector in (".mixqueuehead button{", ".settingshead button{"):
            start = css.index(selector)
            rule = css[start:css.index("}", start)]
            self.assertIn("var(--control-radius)", rule,
                          f"{selector} 是关闭操作，不是圆形标签")
        stage_close = css[css.rindex(".closestage{"):]
        stage_close = stage_close[:stage_close.index("}")]
        self.assertIn("width:40px;height:40px", stage_close)
        self.assertIn("border-radius:50%", stage_close)
        media_close = css[css.index(".media-circle{"):]
        media_close = media_close[:media_close.index("}")]
        self.assertIn("border-radius:50%", media_close,
                      "全屏媒体关闭钮属于圆形媒体操作，不沿用普通 Dialog 关闭钮")
        self.assertIn(
            ".settingshead button:hover{background:var(--hover);color:var(--ink)}", css)
        # 纯图标按钮要进那条名单——`<button>` 的 UA 样式带 `padding:1px 6px`，24px 的键
        # 只剩 12px 内容宽，16px 的图标挤到一边，看着就是那个叉没居中。
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".settingscard .settingshead button{", board)
        icon_only = [line for line in board.splitlines()
                     if line.startswith(":is(.settingshead button,")]
        self.assertTrue(icon_only, "设置弹层的关闭键不在纯图标按钮那条名单里")
        self.assertIn("padding:0", icon_only[0])

    def test_an_open_collapse_stops_cropping_what_is_inside_it(self):
        """展开着不动时那道裁边摘掉：高度过渡需要它，展开完就只剩副作用。

        关注列表里最后一张来源卡的落影正好落在下沿外，留着裁边就被切掉半条，读出来是
        这一列没排完。收起那一下先装回去，否则内容会在高度收到 0 的过程中一直露在外面。
        """
        css = stylesheet_source()
        self.assertIn(".fcollapse.fcollapse-settled{overflow:visible}", css)
        components = (Path(__file__).resolve().parents[1]
                      / "web/js/ui-components.js").read_text(encoding="utf-8")
        self.assertIn("body.style.height='auto';body.classList.add('fcollapse-settled')", components)
        self.assertIn("body.inert=true;body.classList.remove('fcollapse-settled')", components)
        self.assertIn("if(expanded)body.classList.add('fcollapse-settled')", components,
                      "一开始就展开的那些没有过渡可等")

    def test_an_author_row_lines_its_site_marks_up_with_the_buttons(self):
        """站标和失败数靠右起排，跟「全选」「展开」在同一条竖线上。

        作者名长短不一，站标跟着名字走就每行一个位置，一列扫下来得逐行找。按钮上的字只写
        「全选」——它就在这位作者那一行里，说到底选的是谁由所在的行回答；完整的表述留在
        `aria-label` 上，读屏那边脱离了行的上下文。正文归 React（ADR-0031）：作者卡是
        `follow-manage/source-list.tsx` 的 `AuthorCard`，遗留层只剩同形状的骨架。
        """
        root = Path(__file__).resolve().parents[1]
        card = (root / "frontend/src/react/follow-manage/source-list.tsx").read_text(encoding="utf-8")
        board = (root / "web/board.css").read_text(encoding="utf-8")
        skeleton = (root / "frontend/src/board-skeleton.ts").read_text(encoding="utf-8")
        self.assertIn("aria-label={`${state.all ? '取消全选' : '全选'} ${name} 的来源`}", card)
        self.assertIn(">{state.all ? '取消全选' : '全选'}</Button>", card)
        self.assertIn("aria-label={`${open ? '收起' : '展开'} ${name} 的来源`}", card)
        self.assertIn('<span data-author-select-label>全选</span>', skeleton)
        self.assertIn('class="followtoolbaractions"', skeleton)
        self.assertIn(".fauthorhead>.fmeta{margin-left:auto}", board)
        self.assertIn(".fauthorhead>.fmeta~.fmeta,.fauthorhead>.fmeta~.board-author-actions"
                      "{margin-left:0}", board, "撑开的空当只交给第一个 .fmeta")

    def test_history_actions_are_one_split_button_with_the_primary_mirrored(self):
        """一件事的两种做法合成一个 Split Button，不摊成两颗地位相同的按钮。

        实测记在 `docs/reference-snapshots/vercel-geist-split-button.md`：主动作占左半、
        触发档占右半，两半拼成一个盒子，交界处一条 1px 竖线；触发档里只有一枚箭头，读屏名
        由 aria-label 给。这份几何现在的读者是数据管理页那张「扫描与采集」卡的骨架
        （`frontend/src/management.ts`），口味页的同一颗归 React（`HistoryActions`）。
        """
        skeleton = (Path(__file__).resolve().parents[1]
                    / "frontend/src/management.ts").read_text(encoding="utf-8")
        self.assertIn('<div class="splitbutton board-button-group primary">', skeleton)
        self.assertIn('class="splitmain geist-button primary"', skeleton)
        css = stylesheet_source()
        main_rule = css[css.index(".splitbutton>.splitmain{"):]
        self.assertIn("border-radius:var(--control-radius) 0 0 var(--control-radius)",
                      main_rule[:main_rule.index("}")])
        toggle_rule = css[css.index(".splitbutton>.splittoggle{"):]
        toggle_rule = toggle_rule[:toggle_rule.index("}")]
        self.assertIn("border-radius:0 var(--control-radius) var(--control-radius) 0",
                      toggle_rule)
        # 交界那条线是右半自己的左边界，上下顶满：一根浮在上面、两端各收进去几像素的竖线，
        # 压上左半时填充铺到交界，线的两端就各露出一截没被铺到的底色。
        self.assertIn("border-left:1px solid var(--border-15)", toggle_rule)

    def test_the_progress_bar_can_be_grabbed_well_above_the_coloured_line(self):
        """彩条 6px，命中区 18px，多出来的 12px 全在条上方。

        往下扩会盖住按钮那一排的顶边，读起来就是按钮时灵时不灵。彩条自己贴在命中区
        底边，所以加高不会把它挪走；缩略图浮层贴的是命中区上沿，得把这 12px 减回去。
        """
        css = stylesheet_source()
        rule = css[css.index(".vwrap .video-js .vjs-progress-control{"):]
        rule = rule[:rule.index("}")]
        self.assertIn("top:-12px", rule)
        self.assertIn("height:18px", rule)
        self.assertIn("align-items:flex-end", rule)
        holder = css[css.index(".vwrap .video-js .vjs-progress-control .vjs-progress-holder{"):]
        self.assertIn("height:6px", holder[:holder.index("}")], "彩条本身不变粗")
        self.assertPageContains(".vjs-peach-seek-preview{position:absolute;z-index:4;"
                                "bottom:calc(100% - 2px);")
        self.assertPageContains(".vjs-layout-x-small .vjs-progress-control"
                                "{left:0;right:0;top:-12px;height:18px;display:flex}")

    def test_picture_in_picture_gets_its_own_seek_keys(self):
        """画中画那个窗口由浏览器画，站内控制条一颗键都递不进去。

        Media Session 的动作处理器是唯一的入口：登记 `seekbackward` 和 `seekforward`
        之后那个窗口才画得出快退快进，步长取设置里那个秒数；`setPositionState` 让它自己
        那条进度条知道放到哪，`seekto` 让拖它生效。逐个动作单独 try——整块 try 会让一个
        浏览器不认识的动作带走后面全部处理器。站内的小窗是另一件事，见
        `test_the_small_window_gets_its_own_seek_keys`。
        """
        self.assertPageContains("function mountPlayerMediaSession(player,it){")
        self.assertPageContains("mountPlayerMediaSession(detailPlayer,it);")
        for needle in ("seekbackward:details=>seekTo(player.currentTime()-"
                       "(details?.seekOffset||step()))",
                       "seekforward:details=>seekTo(player.currentTime()+"
                       "(details?.seekOffset||step()))",
                       "seekto:details=>{if(typeof details?.seekTime==='number')"
                       "seekTo(details.seekTime)}",
                       "Math.max(1,Number(appSettings.seekSeconds)||10)",
                       "try{session.setActionHandler(action,handler);registered.push(action)}catch(_e){}",
                       "if(!duration||position>duration)return;"):
            self.assertPageContains(needle)
        # 换一条视频就换一份处理器：不摘掉的话那个窗口还按着上一条的进度条走。
        self.assertPageContains("registered.forEach(action=>{try{session.setActionHandler(action,null)}catch(_e){}});")

    def test_settings_overlay_owns_the_top_fixed_layer(self):
        self.assertPageContains("--layer-dialog:1000")
        self.assertPageContains(".settingspanel{position:fixed;z-index:var(--layer-dialog);inset:0;isolation:isolate")
        self.assertPageContains("body.settings-open{overflow:hidden}")
        self.assertPageContains("document.body.classList.add('settings-open')")
        self.assertPageContains("document.body.classList.remove('settings-open')")

    def test_settings_dialog_uses_the_evidenced_command_menu_motion(self):
        self.assertPageContains("animation:settings-dialog-in .35s cubic-bezier(.4,0,.2,1) both")
        self.assertPageContains("translate3d(0,-40px,0);opacity:0")
        self.assertPageContains("panel.classList.add('closing')")
        self.assertPageContains("prefers-reduced-motion: reduce")

    def test_ui_sounds_are_one_synthesised_module_behind_one_switch(self):
        """界面音效只有一个来源、一个开关，关着时连 AudioContext 都不建。

        声音由 `web/js/ui-sounds.js` 用 Web Audio 当场合成，别处不许再建第二个
        AudioContext：浏览器限制同时打开的路数，两份实现也会各带一套音量口径。
        开关在设置「界面」组，偏好存在 `appSettings.uiSounds`，默认开；页面进来先把
        它灌进模块再挂 document 监听，顺序反了首屏那几下点击就按默认的「关」处理。
        配方里 `exponentialRampToValueAtTime` 落到 0 会直接抛错，收尾一律 0.001。
        """
        web = Path(__file__).resolve().parents[1] / "web"
        sounds = (web / "js" / "ui-sounds.js").read_text(encoding="utf-8")
        for path in [web / "index.html", web / "app.js", *sorted((web / "js").glob("*.js"))]:
            if path.name == "ui-sounds.js":
                continue
            self.assertNotIn("AudioContext", path.read_text(encoding="utf-8"),
                             f"{path.name} 不该自己建 AudioContext，声音都从 ui-sounds.js 发")
        self.assertIn("if(!audioContext)audioContext=new Context();", sounds)
        self.assertIn("if(!enabled)return false;", sounds)
        self.assertNotRegex(sounds, r"exponentialRampToValueAtTime\(\s*0\s*,",
                            "指数斜坡不能落到 0")
        self.assertPageContains('class="ptoggle" type="checkbox" id="uiSoundsSetting" role="switch" aria-describedby="uiSoundsDescription"')
        self.assertPageContains('<b>界面音效</b><small id="uiSoundsDescription">')
        self.assertPageContains("appSettings.uiSounds=appSettings.uiSounds!==false;")
        self.assertCode("setUiSoundsEnabled(appSettings.uiSounds);\nwireUiSounds();")
        self.assertPageContains("$('#uiSoundsSetting').checked=appSettings.uiSounds;")
        self.assertPageContains("$('#uiSoundsSetting').onchange=")
        self.assertPageContains("if(appSettings.uiSounds)playUiSound('toggle-on');")
        # 回执、菜单、弹层、设置面板各在自己的入口响，点击与开关由 document 上的监听统一发。
        # 表状态的通知三档取音：默认按 warn 分成功与失败，部分来源失败这类提醒是警告。
        self.assertPageContains("playUiSound(sound||(alert?'error':'success'));")
        self.assertPageContains("{warn:!!failed,timeout:failed?8000:6000,sound:failed?'warning':'success',")
        self.assertPageContains("toast({text:'当前筛选下没有可直接播放的内容'},{sound:'warning'})")
        self.assertPageContains("if(menu.hidden)playUiSound('whoosh');")
        self.assertEqual(self.page.count("playUiSound('pop');"), 2, "formModal 与 confirmModal 各响一声")
        self.assertIn("},{capture:true});", sounds)

    def test_settings_titlebar_owns_the_full_width_above_its_scroll_container(self):
        self.assertPageContains(".settingsscroll{flex:1;min-height:0;overflow-y:auto;padding:0 20px 20px")
        self.assertPageContains("padding:0 20px 20px;overscroll-behavior:contain}")
        self.assertPageContains(".settingshead{z-index:2;display:flex")
        self.assertPageContains("border-bottom:1px solid var(--field-ring);background:var(--ground)")
        self.assertCode('<div class="settingscard">\n    <div class="settingshead">')
        self.assertCode('</div>\n    <div class="settingsscroll">')
        self.assertPageContains("@media(max-width:600px){.settingsscroll{padding:0 17px 17px}")

    def test_sidebar_glide_tracks_layout_and_resets_hover_on_toggle(self):
        self.assertPageContains("const navGlideResize=new ResizeObserver(resizeNavGlide);")
        self.assertPageContains("navGlideResize.observe($('#drawer'));")
        self.assertPageContains("navGlideResize.observe($('#drawerScroll'));")
        self.assertPageContains("syncNavGlide(false,navGlideTarget);")
        self.assertPageContains("document.addEventListener('board:sidebar',()=>{\n"
                                "  navGlideTarget=null;\n"
                                "  if(navGlideTick)cancelAnimationFrame(navGlideTick);")

    def test_studio_metadata_is_not_compiled_as_inline_javascript(self):
        self.assertPageLacks('onerror="this.parentNode.innerHTML=')
        self.assertPageLacks('onload="if(this.naturalWidth')
        self.assertPageContains("img.addEventListener('error',fallback")

    def test_brand_icon_declares_the_multi_size_ico_and_draws_the_square_png(self):
        """标签页角标和页面里的品牌标记同出一张原图，取的却是两份资源。

        角标最大用到 32px，声明指向 `/favicon.ico`：那一份装着 16 到 256 七档尺寸，
        浏览器挑一档就够。页面里的标记要按 CSS 尺寸缩放，用 PNG。
        """
        self.assertPageContains('<link rel="icon" href="/favicon.ico" type="image/x-icon">')
        self.assertPageContains('<img class="mark" src="/peach-logo.png" alt="">')

    def test_global_navigation_and_controls_have_accessible_context(self):
        self.assertPageContains('<a class="skiplink" href="#main">跳到正文</a>')
        self.assertPageContains('<main id="main" tabindex="-1">')
        self.assertPageContains(
            'id="filterBtn" title="导航与筛选" aria-label="展开导航与筛选"')
        self.assertPageContains('id="settingsBtn" title="设置" aria-label="打开设置"')
        self.assertPageContains('name="q" type="search"')
        self.assertPageContains('aria-label="搜索作品、女优、厂牌或标签"')
        self.assertPageContains('id="count" role="status" aria-live="polite" aria-atomic="true"')

    def test_browser_chrome_focus_and_mobile_inputs_follow_the_ui_checklist(self):
        self.assertPageContains('<meta name="theme-color" content="#FFFFFF"')
        self.assertPageContains('<meta name="theme-color" content="#080A0D"')
        # 聚焦环按 BoardUI Input：静止那条边内侧的 2px inset 灰环，仍是「看得见的焦点」。
        self.assertPageContains('.search:focus-within{box-shadow:inset 0 0 0 2px var(--color-border-button-active)}')
        self.assertPageContains('@media (max-width:760px){input,textarea,select{font-size:16px!important}}')
        self.assertPageContains('button,a,input,textarea,select,summary{touch-action:manipulation}')

    def test_search_inputs_share_one_component_with_a_visible_focus_ring(self):
        """带搜索语义的输入只有一份实现，点进去看得见焦点。

        Geist Search Input 的契约是：搜索图标占前缀位，输入框几何不变。索引页的筛选框
        曾是另一份私有样式——没有前缀图标、没有任何 focus 规则，点进去和没点一个样。
        关注管理那一处已经整页归 React（ADR-0031），用的是 BoardUI `Input`，查找中的
        说明落在它下面的 `LoadingDots` 上，不再靠换前缀位表达。
        """
        self.assertPageContains("export function searchInputHtml({label,id='',name='',value='',placeholder='',attrs=''}={})")
        self.assertCode("""const parts=[
    'type="search"',""")
        self.assertPageContains('<input ${parts}></div>')
        self.assertPageContains('<div class="geist-search" data-search-input>')
        self.assertPageContains(
            """<span class="geist-search-prefix" data-search-prefix>${icon('search')}</span>""")
        # 焦点环与顶部搜索框同一个配方：BoardUI Input 的 2px inset 灰环。
        self.assertCode('.geist-search input[type="search"]:focus{outline:0;'
                        'box-shadow:inset 0 0 0 2px var(--color-border-button-active)}')
        self.assertPageLacks("data-follow-search-prefix")
        self.assertPageLacks("fsearchprefix")
        # 遗留层剩下的调用点走组件；索引页的筛选框不再用 placeholder 当标签。
        self.assertPageContains("searchInputHtml({id:'iq',label:'过滤'+title,value:q||''})")
        self.assertPageLacks('<input id="iq" placeholder="过滤…"')
        # 关注管理的那一处：标签一字不差，查找中的说明是同一屏里的一段文字。
        add = (Path(__file__).resolve().parents[1]
               / "frontend/src/react/follow-manage/add-source.tsx").read_text(encoding="utf-8")
        self.assertIn('<Input aria-label="来源链接、名字或 id"', add)
        self.assertIn("<LoadingDots label={byName ? BY_NAME_HINT : BY_LINK_HINT} />", add)
        self.assertPageLacks(".isearch")

    def test_filtering_waits_for_the_chinese_ime_to_finish_composing(self):
        """选字过程中不查询：拿半截拼音去筛选，筛的是「zhon」这种不存在的词。

        `input` 在组字过程中照样发，事件上的 `isComposing` 是唯一可靠的判据；
        组完由 `compositionend` 接手。回车同理——那一下是定字，不是提交。
        """
        self.assertPageContains("iq.oninput=e=>{if(e.isComposing)return;refineIndex()};")
        self.assertPageContains("iq.oncompositionend=refineIndex;")
        self.assertPageContains("const handleSearchInput=e=>{\n  if(e.isComposing)return;")
        self.assertPageContains("$('#q').oninput=handleSearchInput;")
        self.assertPageContains("$('#q').addEventListener('compositionend',handleSearchInput);")
        self.assertPageContains("search.oninput=e=>{if(e.isComposing)return;renderPicker()};")
        self.assertPageContains("search.oncompositionend=renderPicker;")
        # 顶部搜索和标签选择器的键盘处理在最前面让位给输入法。
        self.assertPageLacks("$('#q').oninput=()=>{searchActive=-1;")
        self.assertPageLacks("search.oninput=renderPicker;")
        self.assertEqual(self.app_js.count("if(e.isComposing)return;"), 5,
                         "五处：索引筛选、顶部搜索的输入与键盘、标签选择器的输入与键盘")
        # 只读筛选没有提交按钮，回车必须自己接管：不接就是按了没反应。
        self.assertPageContains("iq.onkeydown=e=>{if(e.isComposing||e.key!=='Enter')return;")
        self.assertPageContains(
            "e.preventDefault();clearTimeout(it2);openIndex(kind,iq.value.trim(),true,true)};")

    def test_a_filter_rerun_keeps_the_input_alive_instead_of_repainting_the_page(self):
        """重画整屏会把正在打字的那个输入框换掉，光标和未定型的拼音一起丢。

        筛选框重跑不是一次页面进入：既不该铺骨架（同步就能给的控件不进骨架），
        也不该重画表头。表头里随查询变的只有计数，单独改它；标签页的读数住在浮层里，
        跟着浮层一起重画。
        """
        self.assertPageContains("async function openIndex(kind,q,push=true,refine=false)")
        self.assertPageContains("if(!refine)showIndexLoading('正在读取'+(INDEX_TITLES[kind]||'标签'),kind,q)")
        self.assertCode("""if($('#indexFilters')){
    $('#indexFilters').innerHTML=filters;
    if(people)popCount($('#indexCount'),countText);
    revealSkeleton($('#indexBody'),()=>{$('#indexBody').innerHTML=body});
    $('#indexMore').hidden=!d.has_more;
  }else""")
        # 分类筛选自己有容器，才能不动表头单独换掉。
        self.assertPageContains('<div id="indexFilters">${filters}</div>')
        self.assertPageContains("it2=setTimeout(()=>openIndex(kind,iq.value.trim(),true,true),300)")

    def test_route_titles_and_settings_dialog_manage_focus(self):
        # 标题跟着路由表走：每一屏的标签写在自己那条记录上，不再有第二份
        # 「路径 → 标题」映射跟路由分支各自演化。
        self.assertPageContains("const label=routeLabel(ROUTES,decodeURIComponent(url.pathname));")
        self.assertPageContains("document.title=label?`${label} · Peach`:'Peach · 蜜桃';")
        self.assertRoute('/follow-manage', "title:'关注管理'")
        # 目录页四个筛选态的标题就是筛选名本身，和侧栏取同一份 STATE_LABELS。
        self.assertPageContains("title:STATE_LABELS[key],open:()=>openCatalog(path)")
        self.assertPageContains('syncPageTitle(path);')
        self.assertPageContains('queueMicrotask(()=>{syncHeaderActions();paintListTitle();buildDrawerNavigation()})')
        self.assertPageContains("queueMicrotask(()=>$('#settingsClose').focus())")
        self.assertPageContains('if(settingsReturnFocus&&document.contains(settingsReturnFocus))')
        self.assertPageContains("if(e.key!=='Tab')return")

    def test_catalog_state_title_never_leaks_into_other_routes(self):
        self.assertPageContains("!manageSection()&&isCatalogPath(path)?STATE_LABELS[state.state]||'':''")

    # 标签显示名（改名而不造词、查不到就原样返回）改成拿真标签跑真函数验收，见
    # test_web_js.test_tag_labels_only_rename_and_never_invent。

    def test_entity_routes_are_semantic_and_not_model_shaped(self):
        self.assertPageLacks("route(`/entity/")
        self.assertPageContains("performer:'performers'")
        self.assertPageContains("studio:'studios'")
        self.assertPageContains("creator:'creators'")

    def test_hidden_load_more_buttons_are_actually_removed_from_layout(self):
        # 有显式 display 的元素不会被浏览器默认的 [hidden]{display:none} 隐藏；
        # 少了这条规则，按钮画在页面上但 requestMore 首行就 return，点了没反应。
        self.assertPageContains(".indexmore[hidden],.entitymore[hidden]{display:none}")

    def test_co_starred_cards_keep_one_name_and_the_total(self):
        # 多人合集保留头像提示，但文字只写第一位和总人数，避免名称折成多行。
        self.assertPageContains("const coStarred=performers.length>1&&!primaryCreator")
        self.assertPageContains('<div class="mavstack">')
        self.assertPageContains("performers.slice(0,5)")
        self.assertPageContains("data-entity-kind=\"performer\" data-entity-name=\"${esc(nm)}\"")
        self.assertPageContains("data-entity-name=\"${esc(performer)}\"")
        self.assertPageContains("等 ${performerTotal} 人")
        self.assertPageContains(".mavstack .mav+.mav{margin-left:-22px}")
        self.assertPageContains(".mavstack .mav:nth-child(n+6){display:none}")

    def test_card_tags_drop_whole_names_instead_of_ellipsizing_them(self):
        """卡片上宁可少放几个标签，也要把名字写全。

        截成「主…」「背…」之后那既不是标签，也认不出是哪一个。所以这一行可换行、
        只有一颗标签那么高：放不下的整颗落到第二行，被容器整颗切掉，切掉的是标签本身。
        `.tg` 只留 `max-width:100%` 这一层兜底——一颗标签自己就比整张卡还宽时，
        横着溢出会压到卡片外面，那时候省略号是唯一的出路。
        """
        css = stylesheet_source()
        start = css.index(chr(10) + ".ctags{")
        row = css[start:css.index("}", start)]
        self.assertIn("flex-wrap:wrap", row, "放不下的整颗换行，不横着截断")
        self.assertIn("align-content:flex-start", row)
        self.assertIn("overflow:hidden", row)
        self.assertIn("height:calc(var(--fs-xs)*1.45 + var(--tag-pad-y)*2 + 2px)", row,
                      "行高按 .tg 的三个 token 算，改字号时不用回来对第二个数")
        start = css.index(chr(10) + ".tg{")
        tag = css[start:css.index("}", start)]
        self.assertIn("max-width:100%", tag, "只兜底一颗标签比整张卡还宽的情形")
        self.assertNotIn("max-width:32%", tag)
        self.assertPageContains(
            'body[data-density="dense"] .card .ctags .tg{max-width:100%;'
            "overflow:hidden;text-overflow:ellipsis}")

    def test_dense_cards_use_three_fixed_rows_without_changing_jav_metadata_height(self):
        # 顶栏密集模式固定标题、身份、标签三行；JAV 小图和预览图只换图片来源，
        # 不再给其中一种额外加一行高度。
        self.assertPageContains('body[data-density="dense"] .grid>.card{padding-top:7px}')
        self.assertPageContains('body[data-density="dense"] .card .mtext{display:grid;grid-template-rows:1.35em 1.35em 30px;')
        self.assertPageContains('gap:3px;height:calc(2.7em + 36px);overflow:hidden}')
        self.assertPageContains('body[data-density="dense"] .card .meta .s{height:1.35em;min-height:0;flex-wrap:nowrap;overflow:hidden;white-space:nowrap}')
        self.assertPageContains('body[data-density="dense"] .card .ctags{height:30px;align-items:flex-start;flex-wrap:nowrap;overflow:hidden}')
        self.assertPageContains('body[data-density="dense"] .card .meta .watchcount{display:none}')
        self.assertPageContains('小图与预览图都是 16:9 横图，只更换图片来源；元数据 DOM 和高度必须完全相同。')
        self.assertPageLacks("jav-small")
        self.assertPageContains('<span class="watchcount">看过 ${it.play_count}</span>')

    def test_every_face_slot_builds_its_image_through_one_helper(self):
        # 顶栏圆头像、卡片署名、共演者、资料页大位共用 entityFaceImg；
        # `/entity-image` 和 `/avatar` 两个地址只在这一个函数里拼。
        self.assertPageContains(
            "function entityFaceImg({kind='performer',id=null,hasImage=false,rep=null,")
        self.assertPageContains("const useEntity=!!(id&&hasImage);")
        self.assertPageContains(
            "const entitySrc=useEntity?`/entity-image?kind=${kind}&id=${id}`:'';")
        self.assertPageContains("const avatarSrc=rep?`/avatar?id=${rep}`:'';")
        self.assertCode(
            "const src=useLogo?`/logo?studio=${encodeURIComponent(logo)}&variant=${logoVariant}`\n"
            "    :(entitySrc||avatarSrc||(mark?`/link-mark?id=${mark}`:''));")
        # 一环都取不到就一个 `<img>` 都不出，首字母垫底直接露出来。
        self.assertPageContains("if(!src)return '';")
        # kind 参数化后，创作者复核卡片也能走同一条链；默认仍是 performer，
        # 既有调用点不受影响。标识变体同理默认 icon：小圆框和窄格子是多数。
        self.assertCode(
            "function avatarInner(name,ref,repId,kind='performer',markId=null,logoName='',"
            "logoVariant='icon',focus=undefined)")
        # 兜底链声明在模板里，行为归 image-fallback 那条委托监听。
        self.assertCode("const fallbacks=useLogo?[entitySrc,avatarSrc].filter(Boolean)\n"
                        "    :(useEntity&&avatarSrc?[avatarSrc]:[]);")
        self.assertPageContains(
            "imageFallbackAttrs({dropStyle:(dropStyle||!!faceBox||!!framedStyle)&&framed,")

    def test_no_face_image_is_emitted_before_the_server_says_it_can_be_fetched(self):
        """先问再出图：没有可用性标志兜住的 `/entity-image`／`/avatar` 一处都不许有。

        无条件出图、等 404 再把图摘掉的代价是：一个作品详情页 9 个这样的 404（1 个
        厂牌实体图、4 个人物实体图、4 个头像），首页手机视口 2 个。两个端点的 404 都
        不带缓存头，每次重绘再打一整轮。
        """
        source = self.page
        gates = ("hasImage", "has_image", "useEntity", "has_avatar")
        for url in ("`/entity-image?kind=", "`/avatar?id="):
            start = 0
            while True:
                at = source.find(url, start)
                if at < 0:
                    break
                start = at + 1
                before = source[max(0, at - 200):at]
                self.assertTrue(
                    any(gate in before for gate in gates),
                    f"{url} 附近没有可用性判据，这是一个必然 404 的 `<img>`：\n"
                    f"{source[max(0, at - 200):at + 80]}")

    def test_the_remaining_face_slots_carry_the_flag_their_endpoint_sends(self):
        """索引页、口味榜、复核卡片和沉浸模式署名圈也走「先问过再出图」。

        这几处不自己拼地址，而是把身份引用交给 `avatarInner()`，所以上一条那种
        「地址附近有没有判据」的扫描扫不到它们：引用里没有 `has_image` 就等于无条件
        出图。`/performers` 桌面视口滚三屏实测 77 个取图请求里 5 个是这样的 404。
        """
        # 缺席按「没图」处理。宽容缺席会让下一个忘了挂标志的端点悄悄退回旧行为，
        # 而这种退化在页面上看不出来——图照样显示，代价全在 404 里。
        self.assertPageContains("hasImage:!!(ref&&ref.has_image)")
        # 索引页（`/api/index`）：实体图看 has_image、代表作头像看 has_avatar，kind
        # 跟着这一页的身份走——创作者的图写成 `performer-<id>.img` 是读不到的。
        self.assertPageContains("ref?{id:ref,has_image:x.has_image}:null,")
        self.assertPageContains(
            "x.has_avatar&&!company?x.rep:null, kind, x.mark, x.has_logo?x.k:'',")
        # 口味榜（`/api/taste`）归 React 档，判据仍是同一对：引用给 `avatarInner()`，
        # 代表作那一侧只有 `has_avatar` 为真才交。
        taste = (Path(__file__).resolve().parents[1]
                 / "frontend/src/react/taste/taste-page.tsx").read_text(encoding="utf-8")
        self.assertIn("{ id: row.entity_id, has_image: !!row.has_image,", taste)
        self.assertIn("row.has_avatar ? row.representative_asset_id ?? null : null,", taste)
        # 沉浸模式署名圈读 `/api/item` 的 entity_refs，标志随引用一起来；代表作那一侧
        # 读 REP，入表时已经按 has_avatar 筛过。
        self.assertPageContains(
            "const ownerRef=ownerKind?(full.entity_refs?.[ownerKind]?.[0]||null):null;")
        self.assertPageContains(
            "tops.performers.forEach(x=>{if(x.rep&&x.has_avatar)REP[x.k]=x.rep});")

    def test_face_fallback_chains_end_by_removing_the_broken_image(self):
        """还是取不到图的 <img> 必须被摘掉，不能只停在「不再重试」。

        标志能挡掉「装都没装」，挡不掉生成本身失败（没有 ffmpeg、六格全黑）那一种，
        所以兜底链一条都不能撤。留着它有两个后果：`.entityportrait:has(img)>span`
        仍然匹配，首字母垫底永远回不来；浏览器还会把 alt 当内容画出来——资料页上
        就是整个艺人名横在头像圈里溢出（loliburin 实测 /entity-image 与 /avatar 双 404）。
        """
        # 收场动作只有这一处实现，默认就是把 <img> 拿掉。
        self.assertPageContains("drop = 'self'")
        self.assertPageContains("image.remove();")
        self.assertPageLacks("this.onerror=null;this.src='/avatar?id=")

    def test_image_fallbacks_are_declarative_data_not_inline_handlers(self):
        """`<img>` 上不再有内联 `onerror`，回退链改成 `data-*` 声明。

        内联版的 URL 要同时穿过 HTML 属性转义和 JS 字符串两层，错一层不报错、
        只是这张图从此不再回退；同一条链在 app.js 里还有四种写法。
        """
        self.assertPageLacks(' onerror="', "模板里不能再出现内联 onerror 属性")
        self.assertPageContains("export function wireImageFallbacks(root)")
        self.assertPageContains("wireImageFallbacks(document.body)")
        # `error` 不冒泡，只有捕获阶段的监听能接住后代 <img>。
        self.assertCode("advanceImageFallback(event.target);\n  }, true);")
        # `data-drop` 是这套机制的开关：没有它的 <img> 一概不动——页面上另有一批
        # 靠 CSS 或父节点兜底的图（厂牌 `.mk`），把它们删掉反而是错的。
        self.assertPageContains("if (!image || !image.dataset || !image.dataset.drop) return '';")
        for attribute in ('data-drop="', "data-fallbacks=", "data-initial=", "data-drop-class="):
            self.assertPageContains(attribute)

    def test_entity_hero_avatar_frames_the_detected_face(self):
        # 资料页圆框按检出的人脸取景；换回落图时必须先摘掉内联 object-position——
        # 回落图是另一张照片，脸不在同一位置。
        self.assertPageContains("function facePos(f)")
        self.assertPageContains(
            "style:company?'':facePos(d.avatar_focus),focus:company?null:d.avatar_focus,")
        # 取景是按实体图算出来的，所以内联 style 和 data-drop-style 只贴给第一环。
        self.assertPageContains("${framed?framedStyle:''}")
        self.assertPageContains(
            "imageFallbackAttrs({dropStyle:(dropStyle||!!faceBox||!!framedStyle)&&framed,")
        self.assertPageContains("if ('dropStyle' in image.dataset) image.removeAttribute('style');")

    def test_every_avatar_slot_hands_the_face_box_to_the_page(self):
        """三处圆头像都要拿到脸框，倍数在页面上按各自的框算。

        判据一样、结论不一样：同一张 640×960、脸只有 67 px 的图，资料页 160 px 框
        只放得到 2 倍，顶栏 64 px 框放到 3 倍还没碰到源图 1:1。所以服务端只下发脸框，
        少给任何一处，那一处就停在「挪了一下但还是看不清」。
        """
        # 资料页大位、顶栏那排、索引页那格。索引页的 img 由共用的 avatarInner 拼，
        # 脸框得穿过它才到得了 img——平移挂容器、放大挂图，两件事各走各的。
        self.assertPageContains("focus:company?null:d.avatar_focus,")
        self.assertPageContains("style:facePos(x.avatar_focus),focus:x.avatar_focus}")
        self.assertPageContains("bigMark?'large':'icon', company?null:x.avatar_focus)")
        self.assertPageContains("logo:logoName,logoVariant,focus:hint}")
        # 五个数挤一个属性，回落时只要摘一样东西。
        self.assertPageContains(
            "data-facebox=\"${[b.cx,b.cy,b.faceW,b.imgW,b.imgH].map(Number).join(' ')}\"")
        self.assertPageContains("else if(img.dataset.facebox)avatarFrame(img);")

    def test_a_slot_that_only_has_the_focus_still_gets_the_shift(self):
        """给了取景就一定挪。`style` 是另一个参数，漏掉它不报错也不掉图。

        挪和放大是同一份 sidecar 的两半，换算只有 `facePos` 这一份，所以它落在出图
        这一处：调用点给了 `focus` 就够。漏掉挪那一半的后果在页面上和「这个人没算过
        取景」一模一样——图照出，只是几何居中，而人脸落在画面顶上的（`focus.pct`
        为 0）正好被裁掉脑袋。
        """
        self.assertPageContains("const framedStyle=style||facePos(focus);")
        # 挪出来的内联 style 也必须能撤：回落那张是另一张照片，脸不在同一位置。
        self.assertPageContains(
            "imageFallbackAttrs({dropStyle:(dropStyle||!!faceBox||!!framedStyle)&&framed,")

    def test_a_slot_that_only_has_the_ref_still_gets_the_focus(self):
        """取景不传就从 ref 上取：它和 `has_image` 出自服务端同一份下发。

        七个调用点各记一次的代价实测就是漏掉六个——播放详情的出镜者、卡片署名、
        顶栏、口味榜、播放列表、复核卡片全是几何居中。公司那一格要的是「明确不取景」，
        传 `null` 压过默认。
        """
        self.assertPageContains("const hint=focus===undefined?(ref&&ref.avatar_focus)||null:focus;")
        # 详情页的出镜者格子不走 avatarInner，自己把取景递进去。
        self.assertPageContains("{id:item.id,hasImage:item.has_image,focus:item.avatar_focus})}")

    def test_an_unlaid_out_frame_is_waited_for_instead_of_measured_as_zero(self):
        """图加载完时框还没布局，`load` 不会再来第二次。

        面板隐藏、`display:none` 的页签、缓存直出都会撞上这一刻：框是 0×0，算出来
        的倍数只能是 1，放大于是静默地永不生效。资料页实测复现过——框已经 160×160、
        图也 complete，style 里却只有平移。这类失效在页面上和「这张图不需要放大」
        长得一模一样，所以必须由代码等，不能指望肉眼发现。
        """
        self.assertPageContains("if(!(rect.width>0&&rect.height>0)){")
        self.assertPageContains("const watch=new ResizeObserver(()=>{")
        self.assertPageContains("watch.disconnect();")

    def test_a_fallback_image_never_inherits_the_previous_faces_box(self):
        # 回落图是另一张照片，脸不在同一位置、尺寸也不是那个尺寸。留着脸框，下一次
        # load 就会拿上一张的脸给这一张算放大倍数，页面上是一张明显错位的图。
        self.assertPageContains("delete image.dataset.facebox;")

    def test_entity_link_favicons_do_not_leak_the_page_url_to_the_linked_site(self):
        # 外链的 favicon 是向对方站点发出的真实请求。锚点上的 rel="noreferrer" 只管
        # 点击跳转，管不到这个 <img>——不设 referrerpolicy 的话，光是打开一位女优的
        # 资料页就会把 Peach 的页面地址报给 x.com、事务所站等每一个被链接的站点。
        # 同页的 taste 行早就是 no-referrer，这里此前漏了；资料页链接从 5 条涨到两百
        # 多条之后，漏的这一处才真正开始有代价。
        # 现在更进一步：图标由本机 `/link-mark` 提供，浏览器根本不再向对方站点发请求，
        # 也就无从泄露。referrerpolicy 仍然留着——它守的是这条约束本身。
        self.assertPageContains('class="entityfavicon" src="${esc(linkMarkUrl(x))}"')
        self.assertPageLacks("faviconUrl(", "外链图标不应再直接指向对方站点")
        anchor = self.app_js.index('class="entityfavicon"')
        self.assertIn('referrerpolicy="no-referrer"',
                      self.app_js[anchor:anchor + 260],
                      "资料页外链 favicon 必须带 no-referrer")

    def test_no_site_icon_is_fetched_by_the_browser_from_the_site_itself(self):
        """站点图标全部由本机给：浏览器不向对方站点要图，也不问第三方图标代理。

        第三方代理那一跳把这一列里的每个站逐个报出去，换回来的只是一枚 16px 位图；
        直连对方站点则只够拿到 `/favicon.ico`，站点自己备好的 apple-touch-icon 和
        SVG 问都不问，要代理才通的来源干脆空着。采集页和口味页同走 `/site-mark`，
        和资料页外链圆标是同一套挑图、合成与缓存。
        """
        for gone in ("google.com/s2/favicons", "faviconFallbackUrl", "SITE_FAVICONS"):
            self.assertPageLacks(gone, "站点图标不得由浏览器向站外取")
        react = Path(__file__).resolve().parents[1] / "frontend/src/react"
        scraping = (react / "scraping/scraping-page.tsx").read_text(encoding="utf-8")
        self.assertIn("<img src={siteMarkUrl({ source })}", scraping)
        self.assertNotIn("faviconUrl", scraping)
        taste = (react / "taste/taste-page.tsx").read_text(encoding="utf-8")
        self.assertIn('<img src={siteMarkUrl({ domain })} alt="" loading="lazy"', taste)
        self.assertNotIn("faviconUrl", taste)

    def test_no_caller_ever_hands_the_link_mark_endpoint_a_url(self):
        # 让前端把地址递给服务端去取，等于开一个任意地址抓取的口子。和 `/follow-stream`
        # 同一条规矩：服务端只取账本里已有的地址。`linkMarkUrl` 自己只吐 id 由
        # test_web_js.test_the_link_mark_endpoint_only_ever_carries_an_id 验收；
        # 这里守的是「没人绕过它另写一个带地址的调用」。
        self.assertPageLacks("/link-mark?url=", "外链图标端点不得接受前端给的地址")
        self.assertPageLacks("/site-mark?url=", "站点圆标端点同样只认键")

    def test_social_links_show_only_the_platform_mark_not_the_handle(self):
        # handle 是网址的一部分，写出来只是把 URL 抄一遍：`X @remu19971203` 里真正有
        # 信息量的只有那个 X。图标本身就说明了去哪，名字留给官网那种「点之前看不出是谁」
        # 的链接。纯图标没有可读文字，所以标签必须留给辅助技术，不能整个丢掉。
        self.assertPageContains('<a class="iconlink" href="${esc(x.url)}"')
        self.assertPageContains('<span class="sr-only">${esc(x.label)}</span></a>')
        self.assertPageContains('.entitylinks a.iconlink{width:36px;padding:0;gap:0;justify-content:center}')
        # 悬停只让药丸的边显出来：这一排是图标，底色一换就读成「选中了这一个」。
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("body .entitylinks a:hover{border-color:var(--line)}", board)

    def test_an_official_link_shows_its_domain_next_to_the_sites_own_mark(self):
        # 文字是域名——这条链接里唯一确定的东西；图标是站点自己那枚，说的是「这是哪家」。
        # 两句话不重复，所以官网这一格两样都给。名字不在这里重复：公司页的标题就是它，
        # 人物页的事务所名在别名行里，还带着通往那张资料页的链接。
        # 已知例外：事务所 ACT 的站标是旗下一位艺人的照片，那一条会在人物页上摆出一张
        # 别人的脸。取不到图时 `data-drop="self"` 撤掉 img，露出底下那枚地球。
        self.assertPageContains('<a class="urllink" href="${esc(x.url)}"')
        self.assertPageContains("${esc(linkHost(x.url)||x.label)}")
        self.assertPageContains(".entitylinks a.urllink{letter-spacing:.02em}")
        links = self.app_js[self.app_js.index("const links=(d.links||[]).map"):]
        links = links[:links.index(".join('');")]
        official = links.split('class="iconlink"')[-1]
        self.assertIn('<img class="entityfavicon" src="${esc(linkMarkUrl(x))}"', official)
        self.assertIn('data-drop="self"', official)

    def test_entity_loading_and_detail_autoplay_share_their_entry_contracts(self):
        self.assertPageContains("showEntityLoading(ROUTE_ENTITIES[path.split('/')[1]])")
        self.assertPageContains('showEntityLoading(kind);')
        self.assertPageContains('appSettings.detailAutoplay=appSettings.detailAutoplay!==false;')
        self.assertPageContains('mountDetailPlayer(it,vv,appSettings.detailAutoplay)')
        self.assertPageContains('mountDetailPlayer(item,followVideo,appSettings.detailAutoplay,{')
        self.assertPageContains('class="ptoggle" type="checkbox" id="detailAutoplaySetting"')

    def test_local_assets_get_their_sidecar_subtitles_as_closed_text_tracks(self):
        """外挂字幕挂成 text track，一条都不预先打开。

        同一部片常有简体、繁体、日语三条，自动打开某一条等于替用户选了语言；
        Video.js 的字幕菜单只在有轨时出现，让它自己出现就够了。关注条目没有 sidecar，
        那条路径不发这一次请求。
        """
        self.assertPageContains("if(!options.source)mountPlayerSubtitles(detailPlayer,it.id);")
        self.assertPageContains("api(`/api/assets/${assetId}/subtitles`)")
        self.assertPageContains("(payload?.subtitles||[]).filter(track=>track.playable)")
        self.assertPageContains("kind:'subtitles',src:track.src,srclang:track.language||''")
        self.assertPageContains("label:track.label,default:false},true);")

    def test_entity_links_have_no_external_arrow(self):
        # `target="_blank"` 已经是外链，箭头只是重复；一排链接里它还会挤掉本就不多的
        # 横向空间。整条 CSS 一并删掉，别留下没人用的类名。
        self.assertPageLacks('entitylinkarrow', "外链箭头应当已删除")
        self.assertPageLacks('↗', "外链箭头字符应当已删除")

    def test_links_that_leave_peach_carry_the_external_mark(self):
        """走出 Peach 的链接带一枚外链标，站内跳转不带，长相全站只有一个。

        2026-09-06 实测 vercel.com 团队页：站内链接（PR 号、部署 ID、项目名）一律裸
        文字，只有离站的部署域名挂一枚 external-link。标记的是「这一跳会离开当前
        应用」，不是「这是个链接」——每个链接都挂就等于谁都没标。
        尺寸和间距按同日实测的 vercel.com/geist/colors 的 `Learn More`：14px/20px 文字
        配 16×16 图标（16/14≈1.15em）、紧跟文字 2px、与文字行居中、吃链接自己的
        currentColor（docs/reference-snapshots/vercel-geist-external-link-mark.md）。
        尺寸写成 em 而不是常数：它每次说的是同一件事，跟着所在文字走比例才不变。
        """
        css = stylesheet_source()
        self.assertPageContains('<symbol id="i-external-link"')
        self.assertPageContains(".externallink{display:inline-flex;align-items:center;"
                                "gap:2px;min-width:0}")
        self.assertPageContains("svg.externalmark{width:1.15em;height:1.15em;flex:none;"
                                "align-self:center;")
        self.assertPageContains("stroke:currentColor;fill:none;stroke-width:2;"
                                "stroke-linecap:round;stroke-linejoin:round}")
        # 尺寸和间距不许再按页面分档：差的不是 1px，是同一个意思有八个长相。
        for stale in (".fsourcelink svg{", ".fcredget svg{", ".fpicksearch b svg{",
                      ".linktable .linkurl svg{", ".followorigin svg{",
                      ".scraping-fields .scraping-url svg{",
                      ".taste-history-guide-content a svg{", ".confighelp a svg{"):
            self.assertNotIn(stale, css, f"{stale} 已由 .externalmark 接管")

    def test_each_social_mark_wears_its_own_brand_colour(self):
        """七枚社媒标记是各家自己的场色铺满整格加白字形，不吃 currentColor。

        认出是哪一家靠的正是颜色：X 黑底白字、Instagram 那道粉紫、YouTube 正红。场色
        和白字形都是人家标识的一部分，不是界面 token，跟着主题变就认不出了。场色铺满
        24×24 的 viewBox，圆角由外面那层 `.entitylinkicon` 裁——官网那一格的 favicon 也是
        这么裁的，同一排里社媒标记和它于是是同一种圆角方片。字形按 24×.5/256 缩在中心，
        外圈裁掉的只是场色的角：社媒标记是拿来认牌子的，裁掉一角就不是那个牌子了。
        """
        fields = {
            "brand-x": '"#000000"', "brand-threads": '"#000000"', "brand-tiktok": '"#000000"',
            "brand-youtube": '"#FF0000"', "brand-facebook": '"#0866FF"',
            "brand-linktree": '"#43E660"',
            "brand-instagram": '"url(#brand-instagram-field)"',
        }
        for symbol, field in fields.items():
            self.assertPageContains(f'<symbol id="i-{symbol}" viewBox="0 0 24 24">')
            self.assertPageContains(
                f'<rect width="24" height="24" stroke="none" fill={field}/>'
                '<g fill="#fff" stroke="none" transform="translate(12 12) '
                'scale(.046875) translate(-128 -128)">')
        # Instagram 的场是渐变不是单色，那条 linearGradient 就住在它自己的 symbol 里。
        self.assertPageContains(
            '<linearGradient id="brand-instagram-field" x1="2" y1="22" x2="22" y2="2"'
            ' gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#FFDD55"/>'
            '<stop offset=".45" stop-color="#FF543E"/>'
            '<stop offset="1" stop-color="#C837AB"/></linearGradient>')
        for hosts in ("[['instagram.com'],'brand-instagram']",
                      "[['threads.com','threads.net'],'brand-threads']",
                      "[['tiktok.com'],'brand-tiktok']",
                      "[['youtube.com','youtu.be'],'brand-youtube']",
                      "[['facebook.com','fb.com'],'brand-facebook']",
                      "[['linktr.ee','linktree.com'],'brand-linktree']"):
            self.assertPageContains(hosts)
        self.assertPageLacks("knockout", "字形是白色实体，不是从圆盘里挖掉的洞")
        self.assertPageContains(
            '.entitylinkicon.brand svg{width:100%;height:100%;stroke:none;filter:none}')

    def test_only_the_profile_link_row_is_exempt_from_the_flat_external_link(self):
        """一句话那种外链是无边无底的蓝字；资料页那排外链是一圈药丸。

        豁免判的是那枚圆盘 `.entitylinkicon`，不是「这条链接里有没有 `<img>`」。社媒标记
        是内联 `<svg>`，按后一个判据会被当成文字外链，药丸的边和底被抹平，同一排里只有
        它们几个没有圈；而按 `<img>` 豁免又会把别处任何包着图的外链一起放走，那些本来
        就该是平的。判据一并消失时整排药丸都被抹平，所以三种写法都要钉。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        for rule in (
            "body a:is(.externallink,[target=_blank])"
            ":not(:has(.entitylinkicon)):not(.cardlink){",
            "body a:is(.externallink,[target=_blank])"
            ":not(:has(.entitylinkicon)):not(.cardlink):hover{",
        ):
            self.assertIn(rule, board)
        for weaker in (":not(:has(img)):not(.cardlink){", ":not(:has(img)):hover{",
                       ":not(:has(img,.entitylinkicon))",
                       "body a:is(.externallink,[target=_blank]):not(.cardlink){"):
            self.assertNotIn(weaker, board)

    def test_the_waiting_filter_frame_is_one_slab_not_two(self):
        """等待态的筛选条和作品抬头共用一块浮层，和内容回来之后是同一个形状。

        这两条各自带着玻璃材质和 22px 圆角，`mountFilterFrame` 在运行时把它们收进外框；
        骨架是一段字符串，进不了那条路径，外框和两个槽位的标记必须写在 HTML 里，
        否则等的那几秒钟里它们是上下两块独立浮层，中间一道缝。
        """
        source = (Path(__file__).resolve().parents[1]
                  / "frontend/src/entity-skeleton.ts").read_text(encoding="utf-8")
        self.assertIn('<div class="board-filter-frame" data-filter-frame>', source)
        self.assertIn('<section class="entitytagbar" data-filter-row="top">', source)
        self.assertIn("entitySkeletonHtml(kind: string, head: string, body: string)", source)
        self.assertPageContains(
            "collectionHeaderHtml({readout:'&nbsp;',loading:true,filterRow:'bottom'})")
        self.assertPageContains(
            '${filterRow?` data-filter-row="${esc(filterRow)}"`:\'\'}')

    def test_the_link_icon_disc_carries_no_plate_of_its_own(self):
        """内联品牌标记直接画在药丸上。垫一层 `--sunk` 会让它比周围暗一档，看着像
        这条链接被禁用了——而图标要说的是「去哪」，不是「能不能点」。"""
        self.assertPageContains(
            ".entitylinkicon{width:20px;height:20px;border-radius:var(--badge-radius);"
            "background:transparent;")

    def test_the_entity_hero_is_a_centred_single_column_on_phones(self):
        # 左像右文那套是给宽屏的：手机上 96px 头像旁边只剩两百多像素，别名和链接被挤成
        # 两三行，头像下面又空着一大片。按 beeg 的资料页改成单列居中；卡还是那张卡，
        # 变的只是卡里正文那一格的排法。
        self.assertPageContains(
            ".entityprofile{grid-template-columns:minmax(0,1fr);gap:12px;padding:16px;"
            "justify-items:center;text-align:center}")
        self.assertPageContains(".entityportrait{width:96px}")
        self.assertPageContains(".entityidentity{width:100%}")
        self.assertPageContains(".entityhero .entitylinks{justify-content:safe center")

    def test_the_profile_link_row_scrolls_sideways_on_phones(self):
        """十条外链在 390px 下换行要堆四行，把作品列表推到折线以外。

        收成一行加横滑，跟筛选条一个做法。居中必须是 `safe center`：普通 `center`
        在溢出时把前半排推到滚动起点之前，那几条够不着。竖直方向被 `overflow-x`
        连带压成 hidden，焦点环靠上下各 4px 的内边距留位置、再由负外边距收回。
        """
        self.assertPageContains(
            ".entityhero .entitylinks{justify-content:safe center;flex-wrap:nowrap;")
        self.assertPageContains(
            "margin-top:9px;margin-bottom:-4px;padding-block:4px;")
        self.assertPageContains(
            "overflow-x:auto;overflow-y:hidden;scrollbar-width:none;"
            "overscroll-behavior-inline:contain}")
        self.assertPageContains(".entityhero .entitylinks::-webkit-scrollbar{display:none}")
        self.assertPageContains(".entityhero .entitylinks>*{flex:none}")
        self.assertPageLacks(
            ".entityhero .entitylinks{justify-content:center",
            "溢出的那半会落在滚动起点之前，滑不到")

    def test_the_switch_centers_its_icon_instead_of_the_line_box(self):
        """svg 默认是 inline，行盒底下留着基线以下的空档。

        `place-items:center` 居中的是行盒不是图形，实测图标偏上 2.7px（26px 高的
        标签里上留 1.8px、下留 7.2px）。靠 `.sorts .javlayout` 上的一次性修补躲开它，别处用同一个开关就露馅，
        所以组件自己出 block。
        """
        self.assertPageContains(
            ".iconswitch svg{display:block;width:17px;height:17px;")
        self.assertPageLacks(".sorts .javlayout label{line-height:0}")
        self.assertPageLacks(".sorts .javlayout svg{display:block}")

    def test_every_checkbox_is_the_same_drawn_box_with_a_hover(self):
        """站内此前两种画法并排：原生 checkbox 和关注列表自绘的那份。

        原生的只调得动 `accent-color`（选中色），未选中态由浏览器自绘，没有悬停
        反馈可言。统一成一份自绘的，悬停只抬填充、不提边，与按钮同口径。
        """
        self.assertPageContains("export function checkboxHtml(inputAttrs='')")
        self.assertPageContains(
            '<span class="pcheck"><input type="checkbox" ${inputAttrs}>'
            '<span aria-hidden="true">${icon(\'check\')}</span></span>')
        self.assertPageContains(".pcheck:hover>span,label:hover>.pcheck>span{background:var(--hover)}")
        # 悬停不许提边：这条只写 background。
        rule = self.page[self.page.index(".pcheck:hover>span,"):]
        self.assertNotIn("border-color", rule[:rule.index("}")])
        # 遗留层剩下的调用点，一个都不许再留原生 checkbox 的 accent-color。关注管理的
        # 那几处随整页进了 React，画的是 BoardUI `Checkbox`。
        for attrs in ("data-pick-playlist=", "data-tag-match-any", 'id="groupCollapseSetting"'):
            self.assertPageContains(attrs)
        # 单选框仍归原生（`.metadatacandidate` 是 radio，不是同一个控件）。
        self.assertPageLacks(".fsrcmenu input{accent-color")
        self.assertPageLacks(".fpickitem input{accent-color")
        self.assertPageLacks(".tagselection input{width:18px")
        self.assertPageLacks(".settingrow input[type=checkbox]{width:20px")
        # 停用的候选不该显示成可点。
        self.assertPageContains(".pcheck:has(input:disabled){cursor:not-allowed}")
        self.assertPageContains(".pcheck:has(input:disabled)>span{background:var(--ground)}")

    def test_the_jav_layout_switch_cannot_be_squeezed_flat_in_the_sort_row(self):
        # `.sorts` 是不换行的横向滚动条，里面的项默认可收缩，而 `.iconswitch` 自己带着
        # `min-width:0`（fieldset 需要它才不撑破容器）。两条合起来允许它被压到内容宽度
        # 以下：窄屏上三个 34px 的版式按钮会叠在一起，还压住旁边的「发行时间」。
        # `.sorts button` 早有 `flex:0 0 auto`，但 fieldset 不是 button，选不到它。
        # 照片那一排的大小开关是同一个控件，规则按控件写而不是按版式开关写。
        self.assertPageContains(".sorts .iconswitch{display:inline-flex;gap:2px;margin:0 6px;flex:none}")

    def test_detail_identity_groups_by_kind_with_the_label_on_top(self):
        # 逐行一个名字在共演作品上会把整个侧栏撑满，左侧还重复一列标签。
        self.assertPageContains("const idGroup=(label,kind,list,extra='')=>list.length")
        self.assertPageContains('<section class="idgroup idgroup-${kind}">')
        self.assertPageContains('<h5 class="idlabel">${label}</h5>')
        self.assertPageContains(".idrow{display:flex;flex-wrap:wrap")
        self.assertPageContains('<div class="identityprimary">${primaryIdentity}</div>')
        self.assertPageContains(".identityprimary{display:flex;flex-wrap:wrap;gap:14px 26px")
        self.assertPageContains(".identityprimary>.idgroup{width:max-content;max-width:100%}")
        # 出镜者标签跟着作品形态走，不再写死「女优」——见 performerLabel。
        self.assertPageContains("idGroup(performerLabel(it),'performer',castList,")
        self.assertPageContains("idGroup('厂牌','studio',studioList)")
        self.assertPageLacks("const performerName=performerRef?.name")
        self.assertPageLacks(".identityrow", "旧的逐行布局必须整段删掉")

    def test_detail_only_links_canonical_entities(self):
        """旧标签可以作为显示回退，但不得伪造一个不存在的资料页。"""
        self.assertPageContains("if(!item.id)return `<span class=\"idcell")
        self.assertPageContains("const creatorList=(refs.creator||[])")
        self.assertPageContains("const seriesList=(refs.series||[])")
        self.assertPageContains(".idcell:not(.entitylink):not(.unownedlink){cursor:default}")
        self.assertPageContains(".idcell.entitylink:hover .idface")

    def test_detail_series_is_a_plain_icon_link_not_a_tag_pill(self):
        self.assertPageContains('class="serieslink entitylink" data-entity-kind="series"')
        self.assertPageContains('<div class="seriesrows">${list.map(seriesCell).join(\'\')}</div>')
        self.assertPageContains("const content=`${icon('tags')}<span>${esc(item.name)}</span>`")
        self.assertPageContains(".serieslink,.serieslink.entitylink{display:flex;width:100%")
        self.assertPageContains("white-space:normal;overflow-wrap:anywhere")
        self.assertPageContains("button.serieslink.entitylink:hover{color:var(--tungsten);text-decoration:none}")

    def test_detail_feedback_toolbar_never_shrinks_into_a_line(self):
        self.assertPageContains("width:max-content;overflow:hidden;flex:none")

    def test_mutating_detail_actions_share_terminal_toasts_and_undo(self):
        self.assertPageContains("const actionReceipt=(message,{undo=null,timeout=undo?8000:6000}={})")
        self.assertPageContains("action:undo?{label:'撤销'")
        self.assertPageContains("if(kind==='o')await postFeedback('o-undo')")
        self.assertPageContains("actionReceipt(messages[kind],{undo:async()=>")
        self.assertPageContains("actionReceipt(r.watch_later?'已加入稍后看':'已移出稍后看'")
        self.assertPageContains("actionReceipt(r.better_version?'已标记寻找更好版本':'已取消寻找更好版本'")
        self.assertPageContains("actionReceipt(`已删除标签「${tagLabel(tag)}」`,{undo:async()=>")
        self.assertPageContains("actionReceipt(r.liked?'已保存喜欢偏好':'已取消喜欢'")
        self.assertPageContains("if(later){e.stopPropagation();setActionBusy(later)")
        self.assertPageContains("if(kind==='o')await post('o-undo')")

    def test_toast_callers_declare_whether_they_pass_text_or_html(self):
        """回执里的标签名来自账本，含 `<` 时不能被当成标签插进 DOM。

        `toast()` 不接裸字符串：那样「这是文本还是 HTML」靠调用点自己记得转义，
        而 actionReceipt 传的是纯文本、followCheckToast 传的是带 `<b>` 的片段，
        签名上完全一样。调用点显式声明，默认按文本转义。
        """
        self.assertPageContains("const toastBody=message=>")
        self.assertPageContains("'html' in message")
        self.assertPageContains("esc(message&&typeof message==='object'?(message.text??''):message??'')")
        # 账本字段一律走 text；只有本地拼出来的计数片段走 html。
        self.assertPageContains("item=toast({text:message},{")
        self.assertCode("toast(\n  {text:`${message}失败：${error?.message||'请重试'}`},{warn:true})")
        self.assertPageContains("toast({html:`检查了 <b>${rows.length}</b> 个来源")

    def test_undo_reports_back_on_the_same_toast_instead_of_swapping_two(self):
        """撤销的结果写回同一条 toast，不另发一条。

        「关掉回执 + 另发一条已撤销」会让底部对齐的栈里一进一出，剩下那条整块跳
        一格；撤销请求快过退场动画时两条还会同时在场。
        """
        self.assertPageContains("item.replaceMessage=")
        self.assertPageContains("try{await undo();item.replaceMessage({text:'已撤销'})}")
        self.assertPageContains("if(act)act.onclick=()=>{setActionBusy(act);action.run()};")
        self.assertPageLacks("try{await undo();toast('已撤销')}")
        # 退场先把高度写死再过渡到 0；直接 remove() 会让上面那条瞬间落下来。
        self.assertPageContains("item.style.height=`${item.offsetHeight}px`;item.getBoundingClientRect();")
        self.assertPageContains(".toast.leaving{height:0!important;margin-top:0;padding-block:0;")
        # 行距改成每条自己的上外边距：gap 属于容器，收不进这次过渡。
        self.assertPageContains(".toast{pointer-events:auto;box-sizing:border-box;display:flex;align-items:center;")
        self.assertPageLacks(".toasts{position:fixed;right:16px;bottom:22px;z-index:var(--layer-popover);display:grid;gap:8px;")

    def test_leaving_a_surface_cancels_the_reads_it_started(self):
        """离开一个表面要撤掉它开的读请求，不能只把结果丢掉、让请求跑到底。

        切三四页就有三四份读请求同时占着浏览器对同一 host 的 6 条连接，最后停留
        的那一页反而排在队尾。写操作不带 signal——切页不能撤掉一次真实写入。
        """
        self.assertPageContains("surfaceRequests?.abort();")
        self.assertPageContains("surfaceRequests=new AbortController();")
        self.assertPageContains("const surfaceToken=path=>({epoch:surfaceEpoch,path,signal:surfaceRequests?.signal})")
        self.assertPageContains("const surfaceApi=(token,path,options)=>api(path,{...options,signal:token.signal})")
        # 取消不是失败：abort 只可能来自 claimSurface，而它已经推进了 epoch，
        # 调用点紧随其后的过期判定会接住它。
        self.assertPageContains("const isAbort=error=>error?.name==='AbortError'")
        self.assertPageContains("if(isAbort(error))return null;throw error")
        self.assertPageContains("if(signal)init.signal=signal")
        # 用响应体之前必须先过期判定：被取消时 surfaceApi 返回的是 null。
        load_body = self.page.split("async function load(reset)", 1)[1].split("function wireCatalogLoadMore", 1)[0]
        guard = load_body.index("if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;\n  offset=pageOffset")
        self.assertLess(guard, load_body.index("cache(d.items)"))

    def test_bulk_follow_updates_run_with_bounded_concurrency(self):
        """一千条串行 POST 全靠往返等，界面按住不放；一次全发出去又会挤满连接。

        闸门这一份实现留在遗留层（`web/js/core.js`），关注管理页整页归 React 之后按
        `@peach/legacy/core` 引它，两边不各写一份。
        """
        self.assertPageContains("const mapLimit=async(items,limit,run)=>")
        self.assertPageContains("const workers=Math.min(Math.max(1,limit),list.length)")
        # 某一项失败只记下原因，不中断整批。
        self.assertPageContains("catch(error){results[index]={ok:false,error}}")
        root = Path(__file__).resolve().parents[1]
        self.assertIn("export declare function mapLimit<T, R>(",
                      (root / "frontend/src/legacy/core.d.ts").read_text(encoding="utf-8"))
        source_list = (root / "frontend/src/react/follow-manage/source-list.tsx").read_text(encoding="utf-8")
        # 批量改状态与批量标记各有自己的并发档，都不是一条一条等着发。
        self.assertIn("await mapLimit(work.ids, 4, async (id: number) => {", source_list)
        self.assertIn("await mapLimit(ids, 6, (id: number) => markItem(id, to))", source_list)
        self.assertIn("setProblem(`批量更新 ${result.failed.length}/${result.ids.length} 项未完成`)",
                      source_list)

    def test_immerse_stream_does_not_pretend_to_paginate_a_random_sample(self):
        """`sort=rand` 在服务端是未加种子的 `RANDOM()`，偏移量在它上面没有意义。

        每续取一次把一个 `tokOffset` 加 60、再传给从不使用这个参数的
        `fetchTok(off)` 的话，读代码的人会以为这条流是翻页来的。
        """
        self.assertPageLacks("tokOffset")
        self.assertPageContains("async function fetchTok()")
        self.assertPageContains("const more=await fetchTok()")
        # 去重靠调用点的 seen 集合。
        self.assertPageContains("const seen=new Set(tokList.map(x=>x.id))")

    def test_no_gutter_is_reserved_because_nothing_disappears_when_scrolling_locks(self):
        """设置面板给 body 加 overflow:hidden 时，整页不再横向跳。

        `scrollbar-gutter:stable` 用永久扣下 15px 换「消失时不跳」。滑块浮在内容上，
        没有东西会消失，跳版的前提不成立，那一列也就不必留。
        """
        css = stylesheet_source()
        rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertNotIn("scrollbar-gutter:stable;", rules)
        self.assertPageContains("body.settings-open{overflow:hidden}")

    def test_closing_a_deep_linked_player_reloads_the_home_feed(self):
        """直接打开 /parts/28125/28125 后关闭播放器，首页停在骨架上再也不动。

        判据不能是「`#grid` 有没有子节点」：深链启动时网格里正躺着一个还没被
        替换掉的加载骨架——它也是子节点，于是「退回去有东西可看」被判成真，
        `route('/')` 只改了地址栏。卡片一定带 data-id，骨架没有。
        """
        self.assertPageContains("function hasReturnSurface()")
        self.assertPageContains("return !!$('#grid').querySelector('[data-id],[data-mix-seed]')")
        self.assertPageContains("const returnSurfaceReady=hasReturnSurface();")
        self.assertPageLacks("const returnSurfaceReady=$('#grid').children.length>0")

    def test_a_saved_online_asset_plays_where_it_is(self):
        """保存过的在线资产此前在馆藏详情里只给一道闸：「媒体与原始页面在关注详情中查看」。

        `path` 是来源作品页不假，但能播的那条代理一直都在
        （`/follow-stream?id=<follow_item>`），保存时写的就是 `follow_item.asset_id`。
        反查不到关注条目时才拦下来，并说清是什么拦的。
        """
        self.assertPageContains("function followStreamSource(it)")
        self.assertPageContains(
            "return it.location==='online'&&it.follow_item_id")
        self.assertPageContains("const proxied=followStreamSource(it);")
        self.assertPageContains("const onlineGated=online&&!it.follow_item_id;")
        self.assertPageContains("if(it.location==='online'&&it.follow_item_id){")
        self.assertPageContains('await openFollowDetail(it.follow_item_id,false,null,true)')
        self.assertPageContains("if(location.pathname!=='/follow'){await restoreRoute();return}")
        self.assertPageContains('it.follow_thumb_url')
        self.assertPageContains('it.follow_tags||it.tags||[]')
        self.assertPageLacks("这条内容从关注候选保存；媒体与原始页面在关注详情中查看。")

    def test_follow_detail_has_an_explicit_download(self):
        """下载到本地是显式动作，此前根本没有入口。用 `<a download>` 让浏览器落盘。"""
        self.assertPageContains('class="fdownload"')
        self.assertPageContains("download=1")
        self.assertPageContains('<symbol id="i-download"')
        self.assertPageContains(".fb .fdownload{box-sizing:border-box;width:44px;height:42px;")

    def test_detail_like_reason_is_an_icon_disclosure_without_idle_explanation(self):
        self.assertPageContains('id="preferenceToggle" aria-label="喜爱理由"')
        self.assertPageContains('id="preferencePanel" hidden')
        self.assertPageContains("preferenceToggle.onclick=()=>{const open=preferencePanel.hidden")
        self.assertPageContains('placeholder="为什么喜欢？"')
        self.assertPageContains('class="geist-button primary savepreference"')
        self.assertPageContains('aria-label="提交喜爱理由"><span>提交</span></button>')
        self.assertPageContains("setActionBusy(btn)")
        self.assertPageContains("spinnerHtml('正在提交喜爱理由')")
        self.assertPageContains("setActionBusy(btn,false);btn.innerHTML='<span>提交</span>'")
        self.assertPageContains('.preference-foot>span{margin-right:auto')
        self.assertPageLacks('aria-label="保存喜爱理由">${icon(\'check\')}</button>')
        self.assertPageLacks("仅保存在本机")
        self.assertPageLacks("回收站中的文件仍保留，清空回收站后才会永久删除。")

    def test_detail_progress_uses_only_titles_and_percentages(self):
        self.assertPageContains('<span>离开位置</span><span id="ratioTxt">0%</span>')
        self.assertPageContains('<span>真实观看</span><span id="realTxt">0%</span>')
        self.assertPageContains("if(t)t.textContent=(r*100).toFixed(0)+'%'")
        self.assertPageContains("rr.textContent=rp.toFixed(0)+'%'")
        self.assertPageLacks('class="ticks mono"')
        self.assertPageLacks("开头就走")
        self.assertPageLacks("真实看 ${rp.toFixed(0)}% · 到达")

    def test_performer_label_says_actress_only_for_jav(self):
        """「女优」是番号发行物的行业称谓。

        素人、创作者自制和网红内容里的出镜者是艺人：套上 JAV 称谓既不准确，
        也会和同名的 creator 身份混淆。形态判据只有后端 `is_jav_code` 一份。
        """
        # 断言的是判据与两个称谓，不是 performerLabel 写成箭头函数还是 function。
        self.assertPageContains("performerLabel(it)")
        self.assertPageContains("it&&it.is_jav?'女优':'艺人'")

    def test_narrow_top_bar_keeps_the_actions_on_the_right(self):
        """窄屏下搜索框绝对定位后脱离了流，动作按钮会挤在品牌名右侧、右半条留空。"""
        self.assertPageContains("#searchBtn{margin-left:auto}")

    def test_deleting_one_search_record_keeps_the_menu_open(self):
        """删除按钮不能抢焦点，也不能整段重建下拉栏。

        抢焦点会触发 `#q` 的 blur，那个 handler 140ms 后无条件关掉下拉栏；
        整段重建则会把推荐词重新洗牌，删一条历史却换了一批推荐。
        """
        self.assertPageContains("b.onmousedown=e=>e.preventDefault();")
        self.assertPageContains("if(group&&!group.querySelector('[data-search-value]'))group.remove();")

    def test_search_menu_closes_without_relying_on_the_input_keeping_focus(self):
        """下拉栏的收起不能只挂在输入框失焦上。

        它由 `#q` 的 focus 打开，而里面要等两个请求回来才渲染。请求在飞的时候用户
        点走，失焦那条 140ms 的兜底先把它收了，晚到的 then 再把它掀开——这一刻焦点
        已经不在输入框上，第二次失焦永远不会来，下拉栏就此钉在页面上。所以回调先
        确认焦点还在，另外补一条不问焦点的出口：`.search` 之外的按压一律收起。
        捕获期是必须的，被点的元素可能吃掉事件或当场把自己摘掉。
        """
        self.assertCode(".then(()=>{if(document.activeElement!==$('#q'))return;")
        # 补全那条隔着 150ms 才回来，同一个守卫在那里也必须成立。
        self.assertCode(
            "if(document.activeElement===$('#q'))renderSearchMenu()}),SUGGEST_DEBOUNCE)")
        self.assertPageContains("document.addEventListener('pointerdown',event=>{\n"
                                "  if(!event.target.closest('.search'))"
                                "hideSearchMenu();\n},true);")
        self.assertPageContains("const hadValue=!!$('#q').value,hadMenu=!$('#searchMenu').hidden;")
        self.assertPageContains("if(hadMenu){hideSearchMenu();searchActive=-1;e.preventDefault();return}")
        self.assertPageLacks("]).then(renderSearchMenu)});")

    def test_card_aspect_ratio_actually_reaches_the_element(self):
        """算出来的卡片比例必须写进 DOM。

        `ar` 从写下起就没有被使用过：`.pic` 写死 `aspect-ratio:16/9`，于是 JAV 的两种
        版式渲染出来一模一样，竖屏条的 `--card-ratio` 也永远取不到值。
        """
        self.assertPageContains('<div class="pic" style="--card-ratio:${ar}">')
        self.assertPageContains(".pic{position:relative;aspect-ratio:var(--card-ratio,16/9)")

    def test_card_hover_feedback_has_no_edge_over_the_cover(self):
        """整卡用底色与轻微明度反馈悬停，圆角上不再覆盖一圈深色像素。"""
        self.assertPageLacks('.card:hover .pic::after{content:""')
        self.assertPageContains(
            "body .card:not(.junkcard,.resourcecard):hover{background:var(--hover)}")
        self.assertPageContains(
            "body .card:not(.junkcard,.resourcecard):hover .pic{filter:saturate(.9) brightness(.94)}")

    def test_catalog_cards_skip_rendering_outside_the_viewport(self):
        """馆藏网格的卡片交给浏览器按视口取舍，一屏滚动只算屏上那几十张。

        连续加载到 1525 张时帧间隔 18.2 ms，仍在 16.7 ms 的帧预算附近（ADR-0031
        「馆藏网格连续加载的实测」）。`auto 320px` 只是占位，渲染过的卡记住自己的尺寸。

        四类卡在规则之外。Mix 卡和分卷／版次卡的叠层纸边靠 transform 抬到卡片盒外
        7px，跳过渲染连带的 paint containment 会把那一截裁掉；垃圾文件卡自己声明占位
        高度，这条选择器压过去会把它改矮；竖屏带的卡横着排在 `.srow` 里，320px 与
        9:16 的封面对不上。
        """
        cards = (Path(__file__).resolve().parents[1]
                 / "web/css/12-cards.css").read_text(encoding="utf-8")
        selector = "#grid article.card:not(.mixcard,.partcard,.junkcard,.scard){"
        self.assertIn(selector, cards, "跳过渲染只施加给馆藏网格里不带叠层的卡片")
        rule = cards[cards.index(selector) + len(selector):]
        rule = rule[:rule.index("}")]
        self.assertIn("content-visibility:auto", rule)
        self.assertIn("contain-intrinsic-size:auto 320px", rule)
        # 垃圾文件卡的占位高度归它自己，所以它留在上面那条的 `:not()` 里。
        self.assertIn("content-visibility:auto;contain-intrinsic-size:auto 360px", cards)

    def test_big_jav_layout_crops_to_the_front_cover(self):
        """大图＝宽度不变、高度拉长，只留封套右侧那块正封。

        `object-fit:cover` 只有在容器比图片更竖时才横向裁切；容器一旦宽过封套的
        1.48，就变成纵向裁切、整张封套原样铺满——这正是旧版式「只是撑满画布」的原因。
        所以裁切必须由容器比例决定，不能只靠 object-position。
        """
        self.assertPageContains("const COVER_FRONT_RATIO=0.75;")
        self.assertPageContains("(jav&&layout==='big'?COVER_FRONT_RATIO:16/9)")
        self.assertPageContains(
            '.poster.cover.front[data-frame="sleeve"]{object-position:100%',
            "没有折痕数据的封套贴最右边缘")
        self.assertPageContains("r>=1.65?'still':r>1.2?'sleeve':'front'",
                                "16:9 官方剧照不能当成双页封套裁到最右侧")
        # 判据是 `jav` 不是 `useCover`：缺封面的卡片也要拉长，用 16:9 预览图上下留黑边，
        # 否则一行里高矮混排会把网格撕成锯齿状。
        self.assertPageLacks("useCover&&layout==='big'")
        # 旧键要继续认，设置存在浏览器里，改名不能让用户的选择静默回落。
        self.assertPageContains("return normalizeJavLayout(appSettings.javLayout);")

    def test_front_cover_shows_only_the_panel_right_of_the_fold(self):
        """大图只摆折痕右边那块正封，封底一个像素都不露。

        正封的宽高比从 0.600 到 0.802 都有，而一行卡片必须等高，容器只能取一个数。
        `object-fit:cover` 做不到这件事：它总把图片铺满容器，容器比正封宽时多出来的
        那截只能由封底来填。改成按卡片高度铺满加 `clip-path`，容器宽出来的部分就成了
        留白，交给模糊背景。几何换算是纯函数，`frontend/test/jav-artwork.test.ts`
        按数值验收；这里守的是「框有没有送到元素上、算出来的值有没有写回去」这条链路。
        """
        self.assertPageContains("const pb=it.poster_box;")
        self.assertPageContains(' data-posterbox="')
        # 换回官方封面时换的是同一个 <img>，框必须跟着元素走，不能只贴在封面那份 HTML 上。
        self.assertPageContains('/ data-(?:c[xy]|posterbox)="[^"]*"/g')
        self.assertPageContains("posterPanel(img,car);")
        self.assertPageContains("const frame=panelFrame({x0,px:[imgW,imgH]},ratio);")
        self.assertPageContains("img.style.setProperty('--panel-clip',`${frame.clip}%`);")
        self.assertPageContains("img.style.setProperty('--panel-left',`${frame.left}%`);")
        self.assertPageContains(
            ".poster.cover.front.panel{inset:0 auto auto var(--panel-left,0%)",
            "正封的位置靠元素自身定位，不是 object-position")
        self.assertPageContains("clip-path:inset(0 0 0 var(--panel-clip,0%))")
        # 只有整张封套才有正封可切；竖版正封和 16:9 剧照走各自那条 object-position。
        self.assertPageContains("if(img.dataset.frame!=='sleeve')return;")
        # 没有框就一个字都不写，CSS 里那份贴右缘的回退照旧生效。
        self.assertPageContains("if(!frame)return;")
        # 框按那一版源图算；封面被更大的那张换掉之后，它描述的是另一张图。
        self.assertPageContains(
            "if(!matchesFaceSource(img.naturalWidth,img.naturalHeight,imgW,imgH))return;")

    def test_narrow_front_cover_fills_the_gap_with_a_blurred_backdrop(self):
        """正封窄于卡片时两侧的留白垫同一张封面的模糊放大版，不留黑边也不露封底。

        模糊层挂在 `.pic` 上而不是图片上：图片那时已经被 `clip-path` 切成正封那一块，
        铺不到留白处。换成预览图时它必须跟着撤，`removeAttribute('style')` 够不着
        另一个元素上的自定义属性，所以 `syncJavImages` 里单写了一句。
        """
        self.assertPageContains(
            "img.closest('.pic')?.style.setProperty('--cover-blur',"
            "`url(\"${img.currentSrc||img.src}\")`);")
        self.assertPageContains(
            ".pic::before{content:\"\";position:absolute;inset:-8%;pointer-events:none;")
        self.assertPageContains("background:var(--cover-blur,none) center/cover no-repeat;"
                                "filter:blur(26px) brightness(.5)}")
        # 待删卡片整块压暗，只有留白还亮着会很显眼；`filter` 不叠加，只能重写一遍 blur。
        self.assertPageContains(
            ".card.pending-delete .pic::before{filter:blur(26px) grayscale(.9) brightness(.27)")

    def test_wide_stills_frame_on_the_detected_face_instead_of_dead_centre(self):
        """16:9 官方剧照在大图容器里只会横向裁，横向锚点必须跟着人走。

        整幅剧照都是画面，没有「正封那一块」可推到右边缘；写死的 50% 只取画面中段，
        人偏在一侧就整个落到可见窗口外面。纵向锚点在这个容器里根本不生效——容器比
        所有封面都竖，`object-fit:cover` 裁的是横向那一轴。
        """
        self.assertPageContains(
            '.poster.cover.front[data-frame="still"]{object-position:var(--cover-x,50%)')
        self.assertPageContains('f.cx!=null?` data-cx="${f.cx}"`')
        # 没检出的那些居中，不能因为多了一个轴就把它们裁到边上去。
        self.assertPageContains("--cover-x,50%")

    def test_the_detected_face_lands_in_the_middle_of_the_visible_window(self):
        """`object-position` 的百分比是两侧对齐比例，不是「这个点落到正中」。

        人脸中心原样当锚点，只保证脸还在画面里：cx=0.81 会算出 81%，脸贴着窗口右缘，
        图片最右边那一截永远露不出来。可见窗口占图片 w 时，锚点得取
        (face - w/2) / (1 - w)，这样 0.81 会顶到 100%，右缘才进画面。
        w 由容器和图片两个比例决定，所以只能在图片加载后算。
        """
        self.assertPageContains("(face-visible/2)/(1-visible)")
        self.assertPageContains("if(face==null||!(visible>0&&visible<1))return;",
                                "整幅可见的那个轴不裁，锚点在那里是死值")
        self.assertPageContains("center('--cover-x',coverFace(img,'cx'),car/r);")
        self.assertPageContains("center('--cover-y',coverFace(img,'cy'),r/car);")
        # 容器比例只有 `--card-ratio` 知道；按 layout 再算一遍迟早和它分叉。
        self.assertPageContains("getComputedStyle(img).getPropertyValue('--card-ratio')")

    def test_image_hooks_are_delegated_because_inline_handlers_cannot_see_the_module(self):
        """内联 `onload="…"` 属性求值在全局作用域里。

        `index.html` 用 `type="module"` 加载 app.js，模块里的函数不在全局作用域，
        内联属性调它只会每张图报一次 ReferenceError，取景静默退回写死的锚点。
        `load` 不冒泡，所以只能在 document 上用捕获阶段收口。
        """
        self.assertPageContains('<script type="module" src="/app.js"></script>')
        self.assertPageContains("document.addEventListener('load',event=>{")
        self.assertPageContains(
            "if(img.classList.contains('cover'))coverAnchor(img);")
        self.assertPageContains("else if(img.dataset.facebox)avatarFrame(img);")
        self.assertPageContains("  fitNativeImage(img);")
        self.assertPageLacks('onload="', "模块作用域的函数在内联属性里取不到")

    def test_card_avatar_and_name_open_the_same_entity(self):
        """同一张卡上的头像和名字必须指向同一个身份。

        头像先看 performer、名字先看 creator 的话，碰上同名的 creator/performer
        重复实体（账本里 35 组）就会一个跳 /performers/x、另一个跳 /creators/x。
        """
        self.assertPageContains("const avatarKind=identity.kind;")
        self.assertPageContains("const avatarName=identity.name;")
        self.assertPageContains("const avatarRef=avatarKind==='performer'?performerRef:it.creator_entity;")
        self.assertPageContains("const inner=avatarInner(avatarName,avatarRef,")

    def test_missing_person_identity_uses_unassigned_on_cards_and_players(self):
        self.assertPageContains(":{kind:'',name:'未归属'});")
        self.assertPageContains("const ownerName=cast.length?cast[0]:(full.creator||'未归属');")
        self.assertPageLacks("it.creator||it.code")
        self.assertPageLacks("full.creator||it.code")

    def test_unassigned_is_a_collection_you_can_open(self):
        """「未归属」是馆藏里的一类，不是详情页上的一句说明文字。

        4566 部作品没有任何署名人。写成一行「归属　未归属」，标签和值念的是同一个
        词，读完就没有下一步；写成入口，它和女优、厂牌一样点得开、筛得出、清得掉。
        """
        # 详情页：和女优组同一个槽位、同一种版式，不是另起一行说明。
        self.assertPageContains('<section class="idgroup idgroup-unowned">'
                                '<h5 class="idlabel">归属</h5>')
        self.assertPageContains('<button class="idcell unownedlink" type="button" data-open-unowned')
        self.assertPageContains("const unowned=!castList.length&&!creatorList.length"
                                "&&!(it.creator||'').trim();")
        self.assertPageContains("(unowned?unownedGroup")
        self.assertPageContains('<div class="detailidentity">${identityRows}</div>')
        # 卡片：署名位上的「未归属」也点得开。
        self.assertPageContains(':linked?`<button class="who unownedlink" type="button" data-open-unowned>'
                                '${esc(who)}</button>`')
        # 三个表面共用一个落点，筛选写在 state.owner 上。
        self.assertPageContains("function openUnowned(){")
        self.assertPageContains("resetHomeState();state.owner='none';")
        self.assertPageContains("const unownedLink=e.target.closest('[data-open-unowned]');")
        self.assertPageContains("$('#stage').querySelectorAll('[data-open-unowned]')"
                                ".forEach(b=>b.onclick=()=>openUnowned());")
        self.assertPageContains("else openUnowned()};")
        self.assertPageLacks("else if(it.code){state.q=it.code",
                             "拿番号去搜只能搜回这一条自己，那不是「同类」")

    def test_unassigned_travels_through_url_chip_and_clear_like_any_filter(self):
        """归类要能被地址栏记住、在筛选条上出现、被「全部清除」清掉。"""
        self.assertPageContains("const HOME_QUERY_KEYS=['loc','creator','studio','owner',")
        self.assertPageContains("owner:initialParam('owner')==='none'?'none':'',")
        self.assertPageContains("if(filters.owner==='none')extra.push(['owner','未归属']);")
        self.assertPageContains("const COMBO_LABELS={creator:'创作者',studio:'厂牌',owner:'归属'};")
        self.assertPageContains("filters.tag='';filters.creator='';filters.studio='';filters.owner=''")

    def test_narrow_search_has_a_way_out(self):
        """窄屏展开搜索后必须有退出入口。

        失焦那条 140ms 的兜底只在输入框为空时才收起搜索栏，输入过内容就没有出口了。
        返回箭头无条件收起，并让整条顶栏恢复——展开期间筛选和品牌要让位，否则筛选
        按钮会和返回箭头叠在同一个位置上。
        """
        self.assertPageContains('id="searchBack"')
        self.assertPageContains("$('#searchBack').onclick=()=>{")
        self.assertPageContains(".top:has(.search.open) #filterBtn,")
        self.assertPageContains(".top:has(.search.open) .searchback{display:inline-flex")
        # 搜索框不铺满：左边留出返回按钮的位置。
        # 搜索和返回键共享顶栏中心线。
        self.assertPageContains(".search{position:absolute;left:48px;right:8px;top:calc(50% - 18px);height:36px")
        self.assertPageContains(".searchback{display:inline-flex;position:absolute;left:8px;top:calc(50% - 18px)")

    def test_narrow_search_order_and_interruptible_glass_transition(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "web/index.html").read_text(encoding="utf-8")
        board = (root / "web/board.css").read_text(encoding="utf-8")
        self.assertLess(html.index('id="searchBtn"'), html.index('id="immerseBtn"'))
        self.assertLess(html.index('id="immerseBtn"'), html.index('id="selectMode"'))
        self.assertIn(".top .search.search-morphing{contain:layout;overflow:hidden}", board)
        self.assertPageContains("const anchor=button.getBoundingClientRect();")
        self.assertPageContains("const from=interrupted?current:open?anchor:expanded,to=open?expanded:anchor;")
        self.assertPageContains("motion.onfinish=()=>{if(searchMorph===motion)finishSearchMorph()};")
        self.assertPageContains("if(document.activeElement===$('#q'))return;")
        self.assertPageContains("$('#searchBtn').setAttribute('aria-expanded',String(open));")
        self.assertPageContains("if(innerWidth>760||matchMedia('(prefers-reduced-motion:reduce)').matches)return;")

    def test_mobile_filter_frame_scroll_keeps_its_document_space(self):
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("document.querySelectorAll('[data-filter-frame]')")
        self.assertPageContains("const active=frames.find(frame=>frame.offsetParent!==null);")
        self.assertPageContains("mobileFilterScroll=filterScrollState(mobileFilterScroll,y,innerWidth<=760,hold);")
        # 收起和放出时 `top` 一步到位，滑动交给合成线程上的 translate；`top` 不进过渡，逐帧重排会卡。
        self.assertIn(".board-filter-frame.board-filter-frame.mobile-filter-free{top:var(--filter-free-top)}", board)
        self.assertNotIn("transition:top var(--board-motion)", board)
        self.assertPageContains("if(free===frame.classList.contains('mobile-filter-free'))continue;")
        self.assertPageContains("frame.getAnimations().forEach(a=>a.id==='filter-slide'&&a.cancel());")
        self.assertPageContains("frame.animate([{translate:`0 ${shift}px`},{translate:'0 0'}],{id:'filter-slide',duration:parseFloat(duration)*1000,easing});")
        self.assertPageContains("el.getBoundingClientRect().top-(parseFloat(css.translate.split(' ')[1])||0)<=top+1;")
        self.assertPageContains("document.documentElement.scrollHeight-innerHeight")

    def test_unlinked_identity_does_not_look_clickable(self):
        """渲染成 `<span>` 的归属不能长得像链接。

        队列行整行本身就是 `<button>`，里面嵌不了按钮，署名只能出文字；它和按钮共用
        `.who` 的强调色，看着能点，点下去落到卡片本身、打开的是视频详情。
        「未归属」不在此列——它有自己的集合可去，出的是 `.who.unownedlink` 按钮。
        """
        self.assertPageContains(".meta span.who{color:var(--ink-2);cursor:default}")
        self.assertPageContains(".idcell:not(.entitylink):not(.unownedlink){cursor:default}")
        self.assertPageContains(".entitylink,.unownedlink{border:0;background:none;padding:0;"
                                "color:var(--tungsten);cursor:pointer;text-decoration:none}")

    def test_random_is_the_default_and_each_home_visit_gets_a_fresh_batch(self):
        """每次进入首页换种子，同一次访问的分页继续稳定。"""
        self.assertPageLacks("const SEED_KEY='peach.seed.v2';")
        self.assertPageLacks("localStorage.getItem(SEED_KEY)")
        self.assertPageContains("seed:initialParam('seed')||rollSeed()")
        self.assertPageContains("sort:appSettings.defaultSort,dir:preferredDirection(appSettings.defaultSort,appSettings.defaultSort,appSettings.defaultSortDirection)")
        # 「从别处回到首页」才换种子，判据是上一屏的路径，所以 lastRoutePath
        # 必须等这一屏打开之后再更新。
        self.assertPageContains("const enteringHome=path==='/'&&lastRoutePath!=='/';")
        self.assertPageContains("}finally{lastRoutePath=path}")
        self.assertPageContains("enteringHome?rollSeed():state.seed||rollSeed()")
        self.assertPageContains("const SORTS=[['seed','随机'],['rating','评分']")
        self.assertPageContains("['seed','随机'],['rating','评分'],['o','高潮计数']")
        for option in ("['daily',", "['rand',"):
            self.assertPageLacks(option, "不使用会让分页重复的 SQL RANDOM 或重复的每日模式")
        self.assertPageLacks('id="rotateSetting"')
        self.assertPageContains("defaultSort:'seed',sortDefaultsVersion:3")
        self.assertPageContains("appSettings.defaultSort==='new'){")
        self.assertPageContains("if(sortDefaultsMigrated)saveSettings()")
        self.assertPageContains("const cleanSort=(value,fallback=appSettings.defaultSort)=>")
        # 手动换一批仍使用稳定种子，避免分页重复或漏项。
        self.assertPageContains("sortControlsHtml({shuffleId:'batchAction'")
        self.assertPageContains("state.sort='seed';state.dir='';state.seed=rollSeed()")
        # 刷新属于列表，不再占顶栏；JAV 共用同一计数/筛选行。
        self.assertPageLacks('id="refresh"')
        self.assertPageContains("extra:javActive()?javLayoutButtons():''")

    def test_sort_splits_into_a_column_and_a_direction_on_the_selected_chip(self):
        """排序拆成「列 + 方向」：箭头画在选中的那一枚里，再点一次翻方向。

        方向不进列键，`时长` 才能在同一枚控件上翻转，而不是分裂成两个互斥选项、
        其中一个方向在界面上永远点不到。旧键仍要认得：地址栏和书签里存着
        `sort=big`、`sort=short`，认不出来不会报错，只会静默换成另一种排序。
        """
        self.assertPageContains("['dur','时长']")
        self.assertPageContains("['new','入库时间'],['played','观看时间']")
        self.assertPageContains("const SORT_ALIASES={big:['size','desc'],short:['dur','asc'],long:['dur','desc']};")
        # 方向词按列各自定义：同一个 desc 在时间列上是「从新到旧」，在时长上是「从长到短」。
        self.assertPageContains("dur:['从长到短','从短到长']")
        self.assertPageContains("new:['从新到旧','从旧到新'],played:['从近到远','从远到近']")
        # 词表可换：关注页那几列（更新时间、热度、时长）方向词是另一套，默认方向、
        # 翻转和无障碍名称这三样的算法与目录完全相同，所以传进来而不是另写一份。
        self.assertPageContains("const defaultSortDir=(key,words=SORT_DIR_WORDS)=>words[key]?'desc':'';")
        self.assertPageContains("function resolveSort(rawSort,rawDir,fallback=appSettings.defaultSort){")
        # 点未选中项＝换列并用该列默认方向；点选中项＝翻方向；随机没有方向。
        self.assertPageContains("function nextSortState(key,current,dir,words=SORT_DIR_WORDS){")
        self.assertPageContains("if(key!==current)return{sort:key,dir:defaultSortDir(key,words)};")
        self.assertPageContains("if(!words[key])return null;")
        self.assertPageContains("return{sort:key,dir:dir==='asc'?'desc':'asc'};")
        self.assertPageContains("const next=nextSortState(b.dataset.sort,state.sort,state.dir);")
        self.assertPageContains("const next=nextSortState(button.dataset.entitySort,filters.sort||'new',filters.dir);")

    def test_sort_direction_arrow_is_decorative_and_the_name_announces_the_next_state(self):
        """箭头装饰、aria-pressed 表达当前项、无障碍名称播报下一步。

        2026-09-04 实测 vercel.com/geist/table 的正文原话：可排序表头是 button，
        方向箭头是装饰性的，按钮向辅助技术播报的是下一个排序状态。`icon()` 自带
        `aria-hidden`，所以箭头这一侧已经成立；名称必须取翻转后的方向词，
        照抄当前方向会让读屏用户以为点下去还是这个顺序。
        """
        self.assertPageContains(
            "next?` aria-label=\"按${label}${next.dir?sortDirWord(next.sort,next.dir,words):''}排序\"`:''")
        self.assertPageContains("icon(dir==='asc'?'arrow-up':'arrow-down','sortdir')")
        # 关注管理页的那一枚归 React：同一条规矩，箭头只是图标，名称取反方向的词。
        follow = Path(__file__).resolve().parents[1] / "frontend/src/react/follow-manage"
        self.assertIn("`按${SORT_LABELS[sort]}${SORT_DIR_WORDS[sort][dir === 'asc' ? 0 : 1]}排序`",
                      (follow / "follow-manage.ts").read_text(encoding="utf-8"))
        self.assertIn("leadingIcon={dir === 'asc' ? RiArrowUpLine : RiArrowDownLine}",
                      (follow / "source-list.tsx").read_text(encoding="utf-8"))
        # 箭头必须真在 sprite 里，否则选中项渲染出一个空 use，方向就完全看不见。
        self.assertPageContains('<symbol id="i-arrow-down" viewBox="0 0 24 24">')
        self.assertPageContains('<symbol id="i-arrow-up" viewBox="0 0 24 24">')
        # 自带 class 而不是选 `button>svg`：同一排里的批量键是方形图标键，
        # 那样写会给它的图标也加上左边距，把它顶偏。
        self.assertPageContains(".sortdir{width:14px;height:14px;flex:none;margin-left:5px;")

    def test_sort_direction_travels_in_the_url_and_the_stored_default(self):
        """方向进地址栏与设置：等于该列默认值时不写，旧默认值迁移到当前键。"""
        self.assertPageContains("'orient','region','sort','dir','q','jav']")
        self.assertPageContains("!(key==='dir'&&value===defaultSortDir(filters.sort))")
        self.assertPageContains("&&!(key==='dir'&&filters[key]===defaultSortDir(filters.sort))")
        self.assertPageContains("if(filters.dir)p.set('dir',filters.dir);")
        self.assertPageContains("...resolveSort(params.get('sort'),params.get('dir'))")
        self.assertPageContains("defaultSort:'seed',sortDefaultsVersion:3")
        self.assertPageContains(
            "if((+appSettings.sortDefaultsVersion||0)<3&&SORT_ALIASES[appSettings.defaultSort]){")
        # 设置里的默认排序与排序条同源：列名中性，方向由列自己的默认值决定。
        self.assertPageContains("['dur','时长'],['size','体积'],['new','入库时间'],['played','观看时间']")
        for legacy in ("['long','", "['short','"):
            self.assertPageLacks(legacy, "默认排序只列中性列名，不列把方向写进键名的值")

    def test_horizontal_choice_groups_start_from_the_muted_base_color(self):
        """横排互斥选项的未选中基态是 --muted。

        填充专属选中态，所以这些组的悬停只提文字色。基态停在 --ink-2（80% 墨）时
        悬停只剩一档可提，肉眼读不出鼠标停在哪一枚；Geist 横排选项实测的未选中态
        是 `rgb(161,161,161)`，也就是 63% 灰，对应 Peach 的 --muted。
        """
        for group, rule in (
            ("顶部标签胶囊 .pill",
             "color:var(--muted);cursor:pointer;font-size:var(--fs-lg);white-space:nowrap;text-decoration:none}"),
            ("排序条 .sorts button",
             "background:transparent;cursor:pointer;font-size:var(--fs-xs);color:var(--muted);"),
            ("管理页标签 .managebar button",
             "background:transparent;color:var(--muted);padding:0 14px;cursor:pointer;font-size:var(--fs-sm);"),
            ("复核页标签与垃圾筛选 .reviewtabs button,.junkfilters a",
             "border-radius:var(--control-radius);background:transparent;color:var(--muted);"),
            ("JAV 工具条 .javbar button",
             "background:transparent;color:var(--muted);cursor:pointer;padding:0}"),
            ("抽屉导航 .dnav button",
             "text-align:left;font-size:var(--fs-lg);color:var(--muted)}"),
        ):
            self.assertPageContains(rule, f"{group} 的未选中基态必须是 --muted")

    def test_loading_state_only_covers_the_count_and_leaves_the_filter_bar_in_place(self):
        """骨架只盖会变的计数，筛选条照常画成最终样子并接上事件。

        筛选条完全由当前 state 决定，这次请求不会改变它，所以没有可占位的东西：
        连它一起清空的话，刚点下的那一枚会在等数据的整段时间里失去高亮，看着像
        没点上；`.count:empty` 还会把整行折叠，网格跟着往上跳一截。
        """
        self.assertPageContains("const countSortsHtml=()=>!state?'':")
        # 加载态与最终态取同一份筛选条，两边不可能画得不一样。
        self.assertPageContains(
            "count.innerHTML=state&&state.state==='trash'?''\n"
            "    :`<span class=\"mono\"><span class=\"countskeleton\"></span></span>`+countSortsHtml();\n"
            "  wireCountRow();")
        self.assertPageContains("    +(trash?'':countSortsHtml());")
        # 读数那一格换值时按位错峰长出来，接事件仍在同一次重画的末尾。
        self.assertPageContains("    popCount(readout,lastCountReadout);\n  }\n  wireCountRow();")
        self.assertPageLacks("count.textContent=''",
                             "加载态不能清空整行，筛选条要留在原位")
        # 数据到位后摘掉忙碌标记，屏幕阅读器不再把这一行当成还在读取。
        self.assertPageContains(
            "$('#count').removeAttribute('aria-busy');$('#count').removeAttribute('aria-label');")

    def test_the_count_placeholder_and_the_redrawn_refresh_key_keep_the_row_height(self):
        """计数骨架宽高定死，等数据时只有换批键在画，行高不变。

        骨架跟着真实文本走的话，数字回来那一刻整行会横向弹一下；14px 远低于筛选条
        按钮的 32px，而两条计数行都有 `min-height:var(--sortH)` 兜底，所以换成真
        数字既不改行高也不产生位移。
        """
        self.assertPageContains(
            ".countskeleton{display:inline-block;width:150px;height:14px;"
            "border-radius:var(--control-radius);\n"
            "  background:var(--hover)}")
        self.assertPageContains(".entitycollectionhead h3 .countskeleton{width:96px}")
        self.assertPageContains("  min-height:var(--sortH);color:var(--ink-2);margin:0 -16px 16px;padding:8px 16px;")
        self.assertPageContains("  min-height:var(--sortH);margin:0 -16px 12px;padding:8px 16px;min-width:0;")
        # 图标拆成两条线，各自 pathLength 归一到 100，dash 的算法就与真实弧长无关了。
        self.assertPageContains(
            '<path class="strand strand-a" pathLength="100" '
            'd="M2 18h1.973a4 4 0 0 0 3.3-1.7l5.454-8.6a4 4 0 0 1 3.3-1.7H22M18 2l4 4-4 4" />')
        self.assertPageContains(
            '<path class="strand strand-b" pathLength="100" '
            'd="M2 6h1.972a4 4 0 0 1 3.6 2.2M22 18h-6.041a4 4 0 0 1-3.3-1.8l-.359-.45'
            'M18 14l4 4-4 4" />')
        # 一圈 2.2 秒：第一条画 748ms，第二条接着画 748ms，停 352ms，两条一起淡出 308ms。
        self.assertPageContains(
            "@keyframes peach-strand-draw{\n"
            "  0%{stroke-dashoffset:100;opacity:1}\n"
            "  34%,86%{stroke-dashoffset:0;opacity:1}\n"
            "  100%{stroke-dashoffset:0;opacity:0}}")
        self.assertPageContains(
            "@keyframes peach-strand-draw-late{\n"
            "  0%,36%{stroke-dashoffset:100;opacity:1}\n"
            "  70%,86%{stroke-dashoffset:0;opacity:1}\n"
            "  100%{stroke-dashoffset:0;opacity:0}}")
        # 忙态只传自定义属性：`<use>` 的影子树里选不到外层的忙态标记，继承的属性进得去。
        self.assertPageContains(
            "#i-shuffle .strand{stroke-dasharray:var(--strand-dash,none);\n"
            "  animation:peach-strand-draw var(--strand-cycle,0s) linear infinite}")
        self.assertPageContains(
            "#i-shuffle .strand-b{animation-name:peach-strand-draw-late}")
        self.assertPageContains(
            '.count[aria-busy="true"] :is(#batchAction,#followShuffle) svg,\n'
            'body.refreshing #batchAction svg,\n'
            '.entitycollectionhead[aria-busy="true"] .entitybatch svg{\n'
            "  --strand-dash:100;--strand-cycle:2.2s}")

    def test_data_page_scan_buttons_animate_their_own_glyphs_while_busy(self):
        """「扫一遍」的两枚键各自适配忙态，不统一转圈。

        检查文件的 git-compare 照 lucide-animated 的 GitCompare 逐笔描画（右下圆→两条
        枝→左上圆，画完停住再一起淡出）；扫描空文件夹的 scan-search 四角按对角两拍
        轮流亮，放大镜保持不动。动效只能挂在 symbol 自己的零件上：`<use>` 的影子树
        里选不到外层的忙态标记，继承的自定义属性进得去，所以忙态把动画名和周期传
        下去，空闲时名字是 none。这些标注上游不会带，补丁必须住在 vendor 脚本里，
        否则换版本一刷新就被抹掉。
        """
        self.assertPageContains(
            '<circle class="gc-part gc-end-a" pathLength="100" cx="18" cy="18" r="3"/>')
        self.assertPageContains(
            '<path class="gc-part gc-line-a" pathLength="100" d="M13 6h3a2 2 0 0 1 2 2v7"/>')
        self.assertPageContains(
            '<circle class="gc-part gc-end-b" pathLength="100" cx="6" cy="6" r="3"/>')
        self.assertPageContains(
            '<path class="scan-corner scan-corner-a" d="M3 7V5a2 2 0 0 1 2-2h2"/>')
        self.assertPageContains(
            '<path class="scan-corner scan-corner-b" d="M17 3h2a2 2 0 0 1 2 2v2"/>')
        self.assertPageContains(
            "@keyframes peach-gc-draw-a{\n"
            "  0%{stroke-dashoffset:100;opacity:1}\n"
            "  17%,86%{stroke-dashoffset:0;opacity:1}\n"
            "  100%{stroke-dashoffset:0;opacity:0}}")
        self.assertPageContains(
            "@keyframes peach-scan-corner-a{\n"
            "  0%,40%{opacity:1}\n"
            "  50%,90%{opacity:.25}\n"
            "  100%{opacity:1}}")
        self.assertPageContains(
            "#i-git-compare .gc-part{stroke-dasharray:var(--gc-dash,none);\n"
            "  animation-name:var(--gc-anim,none);animation-duration:var(--gc-cycle,1.8s);\n"
            "  animation-timing-function:linear;animation-iteration-count:infinite}")
        self.assertPageContains(
            "#i-git-compare .gc-line-a,#i-git-compare .gc-line-b{animation-name:var(--gc-anim-b,none)}")
        self.assertPageContains(
            "#i-git-compare .gc-end-b{animation-name:var(--gc-anim-c,none)}")
        self.assertPageContains(
            "#i-scan-search .scan-corner{animation-name:var(--scan-anim,none);\n"
            "  animation-duration:var(--scan-cycle,1.2s);animation-timing-function:ease-in-out;animation-iteration-count:infinite}")
        self.assertPageContains(
            '#resourceScan[aria-busy="true"] svg,[data-cleanup-empty-scan][aria-busy="true"] svg{\n'
            "  --gc-dash:100;--gc-anim:peach-gc-draw-a;--gc-anim-b:peach-gc-draw-b;--gc-anim-c:peach-gc-draw-c;\n"
            "  --scan-anim:peach-scan-corner-a;--scan-anim-b:peach-scan-corner-b}")
        vendor = (Path(__file__).resolve().parents[1] / "scripts/vendor_web_dependencies.mjs").read_text(encoding="utf-8")
        self.assertIn('if (symbol === "git-compare") inner = inner', vendor)
        self.assertIn('if (symbol === "scan-search") inner = inner', vendor)

    def test_resource_sync_sources_share_the_official_marks_and_board_stat_cards(self):
        """数据管理页「这是哪个网盘」的答案只有一份，结果照 Board 的 stat cards 排。

        115 与 PikPak 取 `MEDIA_SOURCE_ICONS` 的官方站标，不是 globe 字形：来源角标、
        媒体库切换器和配置页问的是同一件事，同一个答案不该因为取图入口不同而长成
        两枚图形（SRCICON 的注释）。结果读数和数据管理顶上一排同一副卡片，三个来源
        带站标 tile，缓存与回收站两张读数凑成同一行；清理内容 Note 与操作行独立成层。
        空文件夹卡片的来源行取同一份站标，扫描结果与失败都落在 Note 里。操作键统一
        Board primary，销毁键维持 danger 实底红；顶栏密度键与筛选框的版式开关问同一
        件事「现在是哪种排法」，字形取同一份 PHOTO_SIZES 映射，按下去换成当前状态的图标。
        """
        renderer = (Path(__file__).resolve().parents[1] / "frontend/src/resource-sync.ts").read_text(encoding="utf-8")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("selectOptionIconHtml(MEDIA_SOURCE_ICONS[location] ?? 'database')", renderer)
        self.assertNotIn("'globe'", renderer,
                         "115/PikPak 用官方站标，不退回 globe 字形")
        self.assertIn('class="board-plain-stat resourcestat"', renderer)
        self.assertIn('class="resourcestat-state', renderer)
        self.assertIn(".resourcestat-tile img{width:20px;height:20px;object-fit:contain}", board)
        self.assertIn(".resourcestat-state.online{color:var(--success)}", board)
        # 扫描中的环形进度独居在结果槽里，自己带框才和链接检查里住在面板中的进度一个形状。
        self.assertPageContains(
            "#resourceSyncResult>.board-job-progress{margin:0;padding:14px 16px;border:1px solid var(--line-soft);border-radius:var(--control-radius)}")
        # 空文件夹来源行取同一份站标；扫描结果与失败提示是 Note，不是裸文本。
        self.assertPageContains(
            'const sourceBadge=source=>`<span class="cleanupsourcemark">'
            "${selectOptionIconHtml(MEDIA_SOURCE_ICONS[source.location]||'database')}"
            '${sourceName(source)}</span>`;')
        self.assertIn(".cleanupsourcemark{display:inline-flex;align-items:center;gap:6px}", board)
        self.assertPageContains("status.innerHTML=noteHtml(`已检查 ${Number(result.scanned||0).toLocaleString()} 个目录，发现 ${Number(result.empty||0).toLocaleString()} 个空文件夹")
        self.assertPageContains("status.innerHTML=noteHtml(error.message,{variant:'error',label:'扫描失败'})")
        # 检查结果 Note 在空文件夹卡里顶满左右，状态容器也得是能装 Note 的块级元素。
        self.assertPageContains('<div class="cleanupstate" aria-live="polite"></div>')
        self.assertIn(".cleanupgrid>.cleanupemptyfolders .cleanupstate .geist-note{margin-inline:-24px;border-inline:0;border-radius:0}", board)
        # 操作键统一 Board primary；销毁键另有一副实底红，不掺进来。
        for needle in (
                'id="linkCheck">',
                'id="linkRetryPicked" disabled>',
                'id="linkRetryAll">',
                'id="resourceScan">'):
            self.assertIn(f'class="resourceaction primary" type="button" {needle}', self.app_js)
        self.assertIn('class="geist-button primary" data-cleanup-empty-scan', self.app_js)
        self.assertIn('class="danger" data-cleanup-empty hidden', self.app_js)
        self.assertIn("body .splitbutton.primary{border:0;box-shadow:none}", board)
        # 顶栏密度键跟筛选框的版式开关取同一份字形映射。
        self.assertPageContains("button.innerHTML=iconSwapHtml(big[2],small[2],")
        self.assertPageContains("}else setIconSwap(button,size===small[0]?'b':'a');")
        self.assertPageContains("syncDensityIcon(density==='big'?'big':'small')}")
        self.assertPageContains("  }else applyDensity();")

    def test_skeletons_shimmer_by_sweeping_instead_of_breathing(self):
        """微光是横向扫光，不是整块呼吸。

        2026-09-04 实测 vercel.com/geist/skeleton：Geist 不动元素自己的不透明度，而是
        在 `::after` 上铺一条比容器宽三倍的横向渐变，用 transform 左右扫，容器
        overflow 裁掉溢出。渐变只在 gray-100 与 gray-200 之间走，明度差两个百分点：
        微光靠移动被看见，不靠明暗跳变，一屏十几块同时闪不会比内容还抢眼。
        """
        self.assertPageContains("@keyframes skeleton-sweep{to{transform:translateX(-50%)}}")
        self.assertPageContains(
            "  visibility:visible;border-radius:inherit;\n"
            "  background:linear-gradient(to right,var(--hover),var(--skeleton-sheen) 50%,var(--hover));\n"
            "  background-size:50% 100%;\n"
            "  animation:skeleton-sweep 1.5s ease-in-out infinite reverse}")
        self.assertPageContains("--skeleton-sheen:rgba(255,255,255,.12);")
        self.assertPageContains("--skeleton-sheen:#EBEBEB;")
        self.assertPageLacks("skeleton-pulse", "呼吸已经换成扫光，不留死引用")
        # 框体（数据管理的操作条、关注管理的头部条）不是待填内容，不参与微光。
        self.assertPageContains(
            ".cleanup-skeleton .skeletoncard em::after,\n"
            ".review-skeleton .skeletoncard em::after,\n"
            ".followmanage-skeleton .skeletoncard i::after{content:none}")

    def test_index_skeletons_share_final_geometry_and_keep_the_header(self):
        self.assertPageContains('export function indexSkeletonHtml(')
        self.assertPageContains('class="icell"><span class="ring skeleton"')
        self.assertPageContains("company?'company':'people'")
        self.assertPageContains('class="tagwall index-tags"')
        self.assertPageContains('.index-skeleton[data-fill]>section>div')
        self.assertPageContains("indexHeaderHtml(kind,q,'<span class=\"countskeleton\"></span>')")
        self.assertPageContains("if($('#indexFilters')){")
        self.assertPageContains("showIndexLoading('正在读取索引',path.slice(1)")
        self.assertPageContains("querySelector('[data-skeleton]')?.dataset.skeleton!==next")

    def test_inline_portrait_cards_follow_dense_mode(self):
        self.assertPageContains('body[data-density="dense"] .shorts-inline .scard{width:calc(214px * 168 / 336)}')

    def test_the_top_bars_get_a_first_paint_skeleton_shaped_like_the_real_thing(self):
        """顶部三层与标签条的首屏骨架照真实几何画，形状按 Geist 的判据选。

        首屏这两处还没有内容：标签条有固定高度不塌，头像那一排只有 18px 内边距，
        内容到位时要长到一百多，会把整页往下推一截。骨架直接套 .av/.ring/.nm 与
        .brandpill、.pill 本身，宽高就是最终内容的宽高，不另算一套；头像因此是圆的
        （Geist 把 pill 变体指给头像），胶囊是圆角。
        """
        self.assertPageContains("function renderBarsLoading(filterState){")
        self.assertPageContains("  renderBarsLoading(filterState);")
        self.assertPageContains('<span class="av avskeleton"><span class="ring"></span>')
        self.assertPageContains(
            '`<span class="brandpill brandskeleton" style="width:${width}px">'
            '<span class="mk"></span></span>`')
        self.assertPageContains('`<span class="pill tagskeleton" style="width:${width}px"></span>`')
        self.assertPageContains(".avskeleton .ring,.avskeleton .nm{background:var(--hover)}")
        # 只在还空着时画：导航到已经有内容的页面不是从无到有，不该铺骨架。
        self.assertPageContains("  if(!tiers.innerHTML){")
        self.assertPageContains("  if(!views.innerHTML){")
        self.assertPageContains("  $('#tiers').removeAttribute('aria-busy');")
        self.assertPageContains("  $('#tagbar').removeAttribute('aria-busy');")
        # 四枚视图胶囊由 state 决定，加载期间就画成最终样子并接上事件，和排序条同规矩。
        self.assertPageContains("const viewPillsHtml=filterState=>VIEW_PILLS.map(v=>")
        self.assertPageContains("    wireViewPills();")
        # 宽度是定值，随机会让同一次冷启动在两台机器上长得不一样，也没法测。

    def test_the_metric_strip_compresses_before_it_starts_scrolling(self):
        """指标带在窄屏先压宽度，横向滚动留给手机和真放不下的时候。

        下限按内容实测取：一格里最宽的是 24px 的数字和那行 12px 的补充说明，加左右
        各 16px 内边距是 140px。四格因此到 645px 视口仍是一整条——实测每格 153px，
        标签、数字、说明三行都不截断。再窄由手机规则接手，改成露边滚动。
        """
        self.assertPageContains(
            ".metricstrip,.tastesummaries{display:grid;grid-auto-flow:column;"
            "grid-auto-columns:minmax(140px,1fr);")
        self.assertPageContains(
            ".metricstrip,.tastesummaries{grid-auto-columns:minmax(168px,82%)}")
        self.assertPageContains("@media(max-width:640px){.insighttoolbar,.tastehead{align-items:stretch}")
        # 下限是照这两行的字号算的，字号变了下限也得跟着重算。
        self.assertPageContains(
            ".tastesummary>b{font-size:var(--fs-2xl);line-height:1.15;")
        self.assertPageContains("padding:14px 16px;")

    def test_skeleton_slots_are_counted_from_the_container_instead_of_a_fixed_number(self):
        """枚数由容器当下的宽度算出来，不写死。

        写死的话宽屏最后一行留一截豁口——用户实测首页第二行只有一张卡；窄屏和手机端
        又多出一堆要横滑才看得见的占位。算出来就不必再为断点各写一套。
        """
        self.assertPageContains("export function fillSkeletonTier(row,kind){")
        self.assertPageContains(
            "    row.insertAdjacentHTML('beforeend',slot(widths[i%widths.length]));\n"
            "    if(row.scrollWidth>row.clientWidth)break;")
        self.assertPageContains("export function fitSkeleton(root){")
        self.assertPageContains(
            "    const columns=style.gridTemplateColumns.split(' ').filter(Boolean).length;")
        self.assertPageContains(
            "    const rows=Math.max(1,Math.min(maxRows,Math.ceil((room+rowGap)/(cardHeight+rowGap))));\n"
            "    const want=columns*rows;\n"
            "    while(grid.children.length>want)grid.lastElementChild.remove();\n"
            "    while(grid.children.length<want)grid.appendChild(first.cloneNode(true));")
        # 横排的推荐行不是网格，按整行补会把它裁成一张。
        self.assertPageContains("    if(!first||style.display!=='grid')continue;")
        # 每个铺骨架的表面都要接上，否则那一屏又回到写死的六张。
        for call in ("fitSkeleton($('#grid'));", "fitSkeleton($('#index'));",
                     "fitSkeleton(stats);", "fitSkeleton(tiers);"):
            self.assertPageContains("  " + call)
        self.assertPageContains("    fillSkeletonTier(tags,'pill');")
        # 一列 fieldset 的两张骨架照自己的轮廓排，补整行会把它们撑成海报网格。
        self.assertPageContains("'/data-cleanup':()=>cleanupSkeletonHtml()")
        self.assertPageContains("{cards:true,count:3,fill:false,className:'followmanage-skeleton'})}</div>`,")
        self.assertPageContains("""${kind==='cards'&&fill?' data-fill=""':''}""")
        self.assertPageContains(".skeletonpanel[data-fill]>div")

    def test_the_follow_skeleton_reuses_the_poster_card_shape_and_adds_its_own_rows(self):
        """关注页跟首页是同一种海报卡，几何共用一块；它自己多一条作者行和一块两排的浮层。

        作者行和浮层的形状取 `.tier`/`.tagbar`/`.count` 本身，跟首页顶栏是同一枚，不另画
        一套；外框 `mountFilterFrame` 是运行时才建的，骨架得自己写全，否则等的那几秒钟
        上下两排是两块各带圆角的浮层。真正的差别只有归属行：`.followitem .meta .s` 有
        min-height，比首页那条高 3.6px，一页十来行叠起来就是一屏的错位。
        """
        self.assertPageContains(
            '''  <div class="tier followauthors" data-skeleton-tier="av"></div>''')
        self.assertPageContains(
            '''  <div class="board-filter-frame" data-filter-frame>\n'''
            '''    <div class="tagbar followfilters" data-filter-row="top" data-skeleton-tier="pill"></div>\n'''
            '''    <div class="count followcount" data-filter-row="bottom">'''
            '''<span class="mono"><span class="countskeleton"></span></span></div></div>''')
        self.assertPageContains(
            "{cards:true,className:'follow-content-skeleton postercard-skeleton'})}</div>`;")
        self.assertPageContains(".follow-content-skeleton .skeletoncard em{height:21px}")
        self.assertPageContains(".follow-content-skeleton .skeletoncard{padding-bottom:8px}")
        self.assertPageContains('<span class="fstate" aria-live="polite"></span></article>`;')
        self.assertPageContains('.followitem .meta .s{min-height:21px}')
        # 真实页面就是这两个类名与这张网格，骨架照抄才可能不位移。
        self.assertPageContains('<div class="tier followauthors" aria-label="按创作者筛选">')
        self.assertPageContains('''<div class="tagbar followfilters" aria-label="${mediaControl?'媒体与关注筛选':'关注筛选'}">''')
        self.assertPageContains(
            ".followlist{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--tile),1fr));"
            "gap:16px 8px}")

    def test_a_deep_link_to_a_management_page_does_not_promise_the_home_bars(self):
        """顶部三层只属于首页：深链启动先画一遍再由路由收起来，等于承诺永不到货的横条。

        收起动作只有一处定义，中央清理函数也走它——手抄一份正是筛选条漏在关注页
        标题上方那个 bug 的来源。
        """
        self.assertPageContains(
            "const hideDiscoveryBars=()=>{$('#tiers').style.display='none';"
            "$('#tagbar').style.display='none'};")
        self.assertPageContains(
            "  loadRequestSeq++;listLoading=false;$('#combo').innerHTML='';\n"
            "  hideDiscoveryBars();")
        self.assertEqual(self.page.count("hideDiscoveryBars();"), 5,
                         "管理页、索引列表、实体资料页、详情页和中央清理函数各调一次，收起动作本身只写一处")

    def test_a_narrow_state_falls_back_to_the_whole_library_for_the_top_tiers(self):
        """状态页收窄到聚合为空时，顶部三层退回全库口径，不整块消失。

        收窄本身是对的：不收窄就会列出在这一页一个作品都没有的人和厂牌。但「已标记」
        这类集合常年只有几条，`/api/tops` 直接回两个空数组，收窄就把整排一起收走了——
        同一条筛选条上换一格，页面顶上凭空少两层，读起来是跳去了另一个页面。
        这一排点开的是实体页，本来就要离开当前状态，它回答的从来不是「这一页里有谁」。
        """
        self.assertPageContains("async function loadTops(params){")
        self.assertCode(
            "  const scoped=await api('/api/tops?'+params);\n"
            "  if(scoped.performers.length||scoped.studios.length||!params.has('state'))return scoped;\n"
            "  const wide=new URLSearchParams(params);wide.delete('state');\n"
            "  return api('/api/tops?'+wide)")
        # 取数只经这一条路：直接打 /api/tops 的调用会绕过回退。
        self.assertEqual(self.app_js.count("api('/api/tops?"), 2)
        self.assertPageContains("      loadTops(topsQueryParams(context))])")

    def test_the_page_chrome_paints_without_waiting_for_any_request(self):
        """左侧导航、管理条、标题和面包屑只认 location，不该排在网络请求后面。

        它们挂在 loadSourceStatus().then(buildBars) 那条链上时，实测深链进统计页要等
        /api/sources 和 /api/facets 共约 585ms 才出现标题，骨架先顶着一个没有标题的
        空壳。buildManageBar() 内部会一并建左侧导航，所以链外只调它一个。
        """
        boot = self.app_js.split("window.addEventListener('popstate',restoreRoute);", 1)[1]
        self.assertLess(boot.index("buildManageBar();"), boot.index("loadSourceStatus()"),
                        "管理条与标题要在派发请求之前画完")
        self.assertNotIn("\nbuildEdge();", boot,
                         "左侧导航由 buildManageBar() 建，链外不再单独调一次")

    def test_a_deep_link_that_hides_the_home_bars_skips_their_two_queries(self):
        """首页三条横条的聚合查询只服务首页，深链进管理页时它们的结果没人看。

        /api/facets 冷启动实测 547ms，排在这一页自己的数据前面。要不要跑问屏幕：
        判断只写在 renderInitialSurfaceLoading() 一处，两边各抄一张路径表迟早对不上。
        """
        self.assertPageContains("const wantsDiscoveryBars=()=>$('#tiers').style.display!=='none';")
        self.assertPageContains("  .then(()=>wantsDiscoveryBars()?buildBars():null)")
        self.assertPageLacks("  .then(buildBars)")
        # 回首页时横条要重新有内容：showHomeSurfaces 放开 display，buildBars 在那条路径上补画。
        self.assertPageContains("$('#tiers').style.display='';$('#tagbar').style.display='';")
        self.assertPageContains("buildManageBar();paintListTitle();")

    def test_the_dashboard_skeleton_reserves_the_metric_strip_it_stands_in_for(self):
        """统计与口味两页的第一屏内容是那条指标带，骨架从大区画起会让整页往下跳一次。

        四格的宽高不是新数字：下限 140px、单格 96px、内边距 14/16、间隙 4px 都取自
        .metricstrip / .tastesummaries，手机档同样露边滚动。
        """
        self.assertPageContains(
            '?`<span class="skeletondashstrip">${Array.from({length:4},\n'
            "          ()=>`<span><i></i><b></b><em></em></span>`).join('')}</span>")
        self.assertPageContains(
            ".skeletondashstrip{display:grid;grid-auto-flow:column;"
            "grid-auto-columns:minmax(140px,1fr);overflow-x:auto;")
        self.assertPageContains(
            ".skeletondashstrip>span{box-sizing:border-box;min-height:96px;min-width:0;"
            "display:grid;align-content:center;\n  gap:4px;padding:14px 16px;"
            "border-right:1px solid var(--line-soft)}")
        self.assertPageContains(
            "@media(max-width:640px){.skeletondashstrip{grid-auto-columns:minmax(168px,82%)}}")
        self.assertPageContains(".skeletondashstrip i::after,.skeletondashstrip b::after,"
                                ".skeletondashstrip em::after,")
        # 口味页与统计页同一套版式，占位也该是同一张。
        self.assertPageContains("pageSkeletonHtml('正在读取口味分析',{variant:'dashboard'})")

    def test_refreshing_wraps_the_tag_pills_instead_of_replacing_them(self):
        """换一批时标签胶囊走 wrap-children 骨架：真实元素留着，用 visibility 藏起来。

        框就是胶囊自己的框，所以零位移；visibility:hidden 的元素同时不可聚焦，正好
        满足规范里「加载期间不要把可聚焦控件放进骨架」。只盖会变的标签胶囊——四枚
        视图胶囊由 state 决定，这次请求不改它们。
        """
        self.assertPageContains(
            "body.refreshing #tagbar [data-tag]{visibility:hidden;"
            "background:var(--hover);border-color:transparent}")
        self.assertPageContains(
            "body.refreshing #tagbar [data-tag],body.refreshing #tiers .av .ring,\n"
            "body.refreshing #tiers .av .nm,body.refreshing #tiers .brandpill"
            "{position:relative;overflow:hidden}")
        self.assertPageContains(
            "body.refreshing #tagbar [data-tag]::after,body.refreshing #tiers .av .ring::after,\n"
            "body.refreshing #tiers .av .nm::after,\n"
            "body.refreshing #tiers .brandpill::after{content:'';position:absolute;inset:0;right:-200%;")
        self.assertPageLacks("body.refreshing #tagbar [data-state]",
                             "视图胶囊不随这次请求变，不进骨架")

    def test_refreshing_wraps_the_avatar_and_brand_tiers_the_same_way(self):
        """换一批换的是顶部三层的成员，所以三层一起走 wrap-children，不只标签条。

        头像那格分成圆片和名字条两块，尺寸取首屏骨架的同一组值，两条通道看起来是
        同一枚；`.av` 宽度写死，名字条居中收窄不动周围任何元素，厂牌胶囊保留自己的
        框，所以换批前后零位移。
        """
        self.assertPageContains(
            "body.refreshing #tiers .av .ring,body.refreshing #tiers .av .nm,\n"
            "body.refreshing #tiers .brandpill{visibility:hidden;background:var(--hover)}")
        self.assertPageContains(
            "body.refreshing #tiers .av .nm{width:52px;margin:0 auto;"
            "border-radius:var(--control-radius)}")
        self.assertPageContains("body.refreshing #tiers .brandpill{border-color:transparent}")
        # 首屏骨架的名字条同宽，两条通道才是同一枚。
        self.assertPageContains(".avskeleton .nm{width:52px;margin:0 auto;")

    def test_the_catalog_skeleton_card_is_built_to_the_real_card_height(self):
        """首页骨架一行和真卡一行等高，内容到位那一下下面不会往上跳。

        列宽、列距和行距沿用 .grid 的同一条算式，卡内每格的高度都由真卡同一枚 token
        算出：标题是 .meta .t 的 2.7em、归属行是 .mono 的一行 1.45em、标签行再加上
        .tg 的内边距与描边。封面到下面那组之间的 8px 拆成 3px 行距加 5px 上边距。
        """
        self.assertPageContains(
            ".postercard-skeleton>div{grid-template-columns:repeat(auto-fill,minmax(var(--tile),1fr));"
            "gap:16px 8px}")
        self.assertPageContains(".grid{display:grid;grid-template-columns:"
                                "repeat(auto-fill,minmax(var(--tile),1fr));gap:16px 8px}")
        self.assertPageContains(
            ".postercard-skeleton .skeletoncard{grid-template-columns:38px minmax(0,1fr);"
            "column-gap:10px;row-gap:3px;\n  align-content:start}")
        self.assertPageContains(
            ".postercard-skeleton .skeletoncard b{width:100%;margin-top:5px;"
            "font-size:var(--fs-md);height:2.7em}")
        self.assertPageContains(
            ".postercard-skeleton .skeletoncard em{width:58%;font-size:var(--fs-xs);height:1.45em}")
        self.assertPageContains(
            "  height:calc(1.45em + var(--tag-pad-y) * 2 + 2px);\n"
            "  border-radius:var(--tag-radius);background:var(--hover)}")
        # 三格的高度算式必须和真卡那三行同源，否则两边各改各的就会重新错开。
        self.assertPageContains("font-size:var(--fs-md);line-height:1.35;min-height:2.7em;")
        self.assertPageContains("--tag-pad-y:4px;")
        self.assertPageContains(".mtext{display:flex;flex-direction:column;gap:3px;")
        self.assertPageContains(".card{cursor:pointer;display:flex;flex-direction:column;gap:8px;")
        self.assertPageContains(".mav{width:38px;height:38px;border-radius:50%;")
        self.assertPageContains(".meta{display:flex;gap:10px;min-width:0}")

    def test_the_two_extra_card_slots_stay_off_outside_the_poster_grid(self):
        """头像格与标签格默认不画：行政界面的骨架是一列 fieldset，不是海报网格。

        默认开着的话，数据管理和关注管理那一列长条中间会凭空多出两块灰，而它们
        对应的真实界面里根本没有这两样东西。
        """
        self.assertPageContains(
            '<span class="skeletoncard"><i></i><s></s><b></b><em></em><u></u></span>')
        self.assertPageContains(".skeletoncard s,.skeletoncard u{display:none}")
        self.assertPageContains(".postercard-skeleton .skeletoncard s{display:block;")
        self.assertPageContains(".postercard-skeleton .skeletoncard u{display:block;")

    def test_the_profile_collection_head_switches_sort_before_the_request_returns(self):
        """资料页表头与首页同规矩：排序条立刻到位，只有 `视频 · N` 换成骨架。

        换列和翻方向在点下的那一刻就已确定，等一次请求才生效等于让选中态迟到一整
        个网络往返。标题两侧的标签条和已经铺好的网格不属于这次变化，一律不动。
        """
        self.assertPageContains(
            "  markEntityCollectionBusy(kind,name,filters);\n"
            "  const items=await fetchEntityItems(kind,name,filters);")
        self.assertPageContains("head.setAttribute('aria-busy','true');")
        self.assertPageContains("head.querySelector('.sorts').outerHTML=entityCollectionSortsHtml(filters);")
        self.assertPageContains(
            "head.querySelector('h3').innerHTML='<span class=\"countskeleton\"></span>';")
        # 表头只有一份写法和一处接线，重画忙碌态和重画结果不会走岔。
        self.assertPageContains(
            'section.innerHTML=`${collectionHeaderHtml({controls:entityCollectionSortsHtml(filters)})}')
        self.assertPageContains("    wireEntityCollectionHead(section,kind,name,filters);\n  }else{")

    def test_offline_sources_drop_out_of_the_default_filter(self):
        """脱盘的来源要从默认筛选里摘掉。

        留着的话首页照样按它筛，出来一屏点开就报脱盘的卡片。只动默认值——地址栏里
        显式写了 `loc=` 就是用户自己选的。全部脱盘时保持原样：清空会变成什么都不筛。
        """
        self.assertPageContains("function dropOfflineFromDefaultLoc(){")
        self.assertPageContains("if(initialParams.get('loc'))return;")
        self.assertPageContains("dropOfflineFromDefaultLoc();")

    def test_no_dropdown_falls_back_to_the_browser_control(self):
        """全站下拉都是自绘的 listbox，一个原生控件都不留。

        原生下拉的弹出层由操作系统画，不认站内色板：设置面板里那七个此前只能靠
        `color-scheme:dark` 把系统弹出层整个压成深色，浅色主题下就是白底页面上七块黑。
        2026-09-04 实测 vercel.com 后台：整站没有一个原生下拉，触发器是 button，面板是
        自绘 listbox，面板底色就是页面底色，箭头是触发器里的 chevron。
        """
        self.assertPageLacks("<select", "下拉一律走 Geist Select，不回落到浏览器控件")
        self.assertPageLacks("color-scheme:dark;", "只有 <html> 声明配色，控件不再各自钉死一档")
        self.assertCode(
            "<span data-select-label>${content(chosen)}</span>${icon('chevron-down')}")
        self.assertPageContains(
            ".gselectfield>svg{width:16px;height:16px;flex:none;stroke:currentColor;fill:none;color:var(--muted)}")

    def test_settings_panel_fits_the_visible_viewport_on_ios(self):
        """iOS 上 `vh` 算的是不减地址栏的「大视口」。

        按 90vh 撑出来的面板会顶到地址栏和状态栏底下，上半截被遮住——手机上实测过。
        `dvh` 跟着当前可见高度走；安全区内边距再把刘海和 Home 指示条让开。
        """
        self.assertPageContains("max-height:min(720px,90dvh)")
        self.assertPageContains("padding-top:max(18px,env(safe-area-inset-top))")
        self.assertPageContains("padding-bottom:max(18px,env(safe-area-inset-bottom))")

    def test_links_only_use_underlines_on_hover(self):
        """文字链接允许悬停下划线，默认状态保持清爽。"""
        self.assertPageContains(".entitylink:hover,.unownedlink:hover{color:var(--ink);text-decoration:none}")
        self.assertPageContains(".idcell.entitylink:hover,.idcell.unownedlink:hover,.mav.entitylink:hover{text-decoration:none}")
        for selector, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}', stylesheet_source()):
            if "text-decoration:underline" in declarations:
                self.assertTrue(":hover" in selector or selector.strip() == ".project-banner>a", selector)

    def test_every_identity_cell_can_carry_its_own_portrait(self):
        # 人物格走和顶栏圆头像同一个 entityFaceImg；这一格没有代表作头像可退，
        # 装了实体图才出 `<img>`，否则就是首字母垫底。
        self.assertPageContains("? `<span>${esc(item.name.slice(0,1))}</span>${entityFaceImg(")
        self.assertPageContains("{id:item.id,hasImage:item.has_image,focus:item.avatar_focus})}")
        self.assertPageContains(
            '${item.has_logo?`<img src="/logo?studio=${encodeURIComponent(item.name)}&variant=icon"')

    def test_large_casts_stay_in_the_dom_behind_one_expander(self):
        # 收起的格子必须留在 DOM 里，展开只是取消 hidden，不重新请求也不丢身份。
        self.assertPageContains("const CAST_SHOWN=8")
        self.assertPageContains("const castOverflow=Math.max(0,castList.length-CAST_SHOWN)")
        self.assertPageContains("还有 ${castOverflow} 位")
        self.assertPageContains("querySelectorAll('[data-castoverflow]').forEach(row=>row.hidden=false)")

    def test_playback_keys_reach_both_the_detail_player_and_immerse(self):
        # 沉浸模式没有 Video.js，详情播放器读的又是同一个原生元素，
        # 所以快捷键只认 video 元素，两边共用一条实现。
        self.assertPageContains("function activeVideo()")
        self.assertPageContains("if(!$('#tok').hidden)return $('#tokVid')")
        # Video.js 挂载后 #vid 是 <div class="video-js">，真媒体元素是 #vid_html5_api。
        # 按 id 取会静默失败：给 div 写 currentTime 读得回来，播放却纹丝不动。
        self.assertPageContains("stage&&!stage.hidden?stage.querySelector('video'):null")
        self.assertPageLacks("return stage&&!stage.hidden?$('#vid'):null")
        self.assertPageContains("seekVideoBy(video,appSettings.seekSeconds*(e.key==='ArrowRight'?1:-1))")
        self.assertPageContains("toggleVideoPlayback(video)")

    def test_immerse_click_toggles_playback_and_mobile_double_tap_seeks(self):
        self.assertPageContains("function toggleVideoPlayback(video)")
        self.assertPageContains("$('#tokTrack').onclick=()=>{")
        self.assertPageContains("if(Date.now()<tokIgnoreClickUntil)return")
        self.assertPageContains("const TOK_DOUBLE_TAP_MS=280")
        self.assertPageContains("const side=clientX<window.innerWidth/2?-1:1")
        self.assertPageContains("seekVideoBy(video,appSettings.seekSeconds*side)")
        self.assertPageContains("handleTokTap(end.clientX)")
        self.assertPageContains("touch-action:manipulation;cursor:pointer")

    def test_mobile_player_error_is_centred_away_from_the_network_badge(self):
        self.assertPageContains(
            ".vwrap .video-js.vjs-error .vjs-error-display .vjs-modal-dialog-content{")
        self.assertPageContains(
            "display:flex;align-items:center;justify-content:center;text-align:center")
        self.assertPageContains("transform:translate(-50%,-50%)}")

    def test_space_does_not_also_scroll_the_page(self):
        self.assertCode("if(e.key===' '||e.key==='k'||e.key==='K'){\n      e.preventDefault();")

    def test_playback_keys_never_steal_keystrokes_from_inputs(self):
        self.assertPageContains("function isTypingTarget(el)")
        self.assertPageContains("el.tagName==='INPUT'||el.tagName==='TEXTAREA'||el.isContentEditable")
        self.assertPageContains("if(isTypingTarget(e.target)||e.ctrlKey||e.metaKey||e.altKey)return")

    def test_seek_clamps_without_comparing_against_nan_duration(self):
        # duration 在元数据到位前是 NaN，Math.min(NaN,x) 会把 currentTime 写成 NaN。
        self.assertPageContains(
            "Number.isFinite(total)?Math.max(0,Math.min(total,target)):Math.max(0,target)")

    def test_search_menu_is_navigable_by_keyboard(self):
        self.assertPageContains("function moveSearchActive(step)")
        self.assertCode("if(e.key==='ArrowDown'||e.key==='ArrowUp'){\n    if(moveSearchActive(")
        self.assertPageContains("options[searchActive].scrollIntoView({block:'nearest'})")
        self.assertPageContains(".searchoption:hover,.searchoption.active{background:var(--hover)}")

    def test_search_active_index_resets_when_the_list_is_rebuilt(self):
        # 列表重建后旧索引会指向不存在的行；输入和重新渲染都必须归零。
        self.assertPageContains("if(menu.innerHTML)presentMenu(menu);else hideSearchMenu();searchActive=-1;")
        self.assertPageContains("const refreshSearchMenu=()=>{searchActive=-1;")

    def test_enter_uses_the_highlighted_option_before_the_suggestion(self):
        self.assertPageContains("const picked=searchOptions()[searchActive]")
        self.assertPageContains("runSearch(!picked,true)")

    def test_immerse_mode_names_the_whole_cast(self):
        self.assertPageContains("const cast=full.performers||[]")
        self.assertPageContains("cast.slice(0,3).join('、')")
        self.assertPageContains("$('#tokAvatar').innerHTML=avatarInner(ownerName,ownerRef,REP[ownerName],ownerKind||'performer')")

    def test_immerse_desktop_matches_the_youtube_shorts_layout_hierarchy(self):
        self.assertPageContains('class="tokstage"')
        self.assertPageContains('.tokstage{position:absolute;left:50%;top:50%;width:min(56.25vh,calc(100vw - 240px));aspect-ratio:9/16')
        self.assertPageContains('.toktrack{position:absolute;inset:0;overflow:hidden;border-radius:var(--floating-radius);background:#000')
        self.assertPageContains('.tokbtns{position:absolute;left:calc(100% + 12px);bottom:8px;width:72px')
        self.assertPageContains('class="media-circle" id="tokDislike"')
        self.assertPageContains('.media-circle{box-sizing:border-box;width:48px;height:48px;padding:0;border:0;border-radius:50%;')
        self.assertPageContains('.tokui{position:absolute;left:20px;bottom:20px;width:min(520px,calc(50% - 28.125vh - 36px))')
        self.assertPageContains('<div class="tokauthor"><button type="button" class="tokavatar"')
        self.assertPageContains('<button type="button" class="toktitle" id="tokTitle"></button>')

    def test_immerse_mobile_returns_to_a_full_viewport_player(self):
        self.assertPageContains('.tokstage,.tokstage.wide{inset:0;width:100%;height:100%;aspect-ratio:auto;transform:none}')
        self.assertPageContains('.toktrack{border-radius:0;box-shadow:none}')
        self.assertPageContains('.tokbtns{left:auto;right:max(8px,env(safe-area-inset-right));bottom:92px;width:56px')

    def test_immerse_centres_landscape_video_while_keeping_actions_inside(self):
        self.assertPageContains("const wide=source>=1")
        self.assertPageContains("track.closest('.tokstage')?.classList.toggle('wide',wide)")
        self.assertPageContains("$('#tok').classList.toggle('tok-wide',wide)")
        self.assertPageContains('.tokstage.wide{left:50%;right:auto;width:min(64vw,177.778vh);aspect-ratio:16/9;transform:translate(-50%,-50%)}')
        self.assertPageContains('.tokstage.wide .tokbtns{left:auto;right:12px;bottom:18px}')
        self.assertPageContains('.tok.tok-wide .tokui{width:min(500px,calc(36vw - 56px))}')

    def test_immerse_cancels_each_stream_when_switching_closing_or_leaving(self):
        self.assertPageContains('function tokStreamUrl(video,id)')
        self.assertPageContains('video.dataset.streamSession=session')
        self.assertPageContains('`/stream?id=${id}&session=${encodeURIComponent(session)}`')
        self.assertPageContains('function disposeTokVideo(video,remove=false)')
        self.assertPageContains('disposeTokVideo(old,true)')
        self.assertPageContains('disposeTokVideo(v,v.id!==\'tokVid\')')
        self.assertPageContains("querySelectorAll('#tokIncoming').forEach(video=>disposeTokVideo(video,true))")
        self.assertPageContains("addEventListener('pagehide',()=>{")
        self.assertPageContains("$('#tokTrack').querySelectorAll('video').forEach(cancelTokStream)")

    def test_nothing_a_surface_starts_outlives_the_surface(self):
        """离开一个表面时，它开的东西必须跟着结束。

        三处实际泄漏。共同点是都不报错：页面越用越慢，而且离开之后还在往后端打请求。

        - 横向拖动行的 `mouseup`：每 `wireDrag` 一个元素就往 window 上挂一条的话，
          麻烦在这些行是 innerHTML 重绘出来的，每次重绘换一批新节点，那些闭包连着
          已经脱离文档的元素永远不回收。
        - `wireTelemetry` 的十秒上报：只有 pause/ended 清定时器，而离开详情两者都不
          发生，于是 setInterval 连着已销毁的 video 一直往 /api/activity 打。
        - 标签选择器的 document 捕获监听：`stage.innerHTML=''` 只删 DOM，
          document 上那条监听留着。

        契约不是「写成哪几行」，而是三条出口：全局监听全站唯一、按元素调用的
        wire* 不往 window/document 上挂无人撤销的监听、舞台销毁跑一张收尾登记表。
        """
        app = self.app_js
        self.assertEqual(app.count("window.addEventListener('mouseup'"), 0,
                         "拖动监听归共享控件生命周期")
        self.assertPageContains("signal:abort.signal")
        self.assertPageContains("destroy(){abort.abort();resize.disconnect();horizontalControls.delete(el)")
        drag = app[app.index("function wireDrag(el){"):]
        drag = drag[:drag.index("function wireAllDrag")]
        self.assertNotIn("window.addEventListener", drag,
                         "wireDrag 按元素调用，在里面挂全局监听就是按元素泄漏")
        self.assertNotIn("document.addEventListener", drag)

        self.assertPageContains("function onStageDispose(dispose)")
        self.assertPageContains("function runStageDisposers()")
        dispose = app[app.index("function disposeStage("):]
        dispose = dispose[:dispose.index("\nfunction placeItemDetail")]
        self.assertIn("runStageDisposers();", dispose, "舞台销毁必须跑收尾登记表")

        telemetry = app[app.index("function wireTelemetry(it,v,sel){"):]
        telemetry = telemetry[:telemetry.index("\nfunction wireFollowTelemetry")]
        for needle in ("const stopTelemetry=", "'emptied'", "onStageDispose(stopTelemetry)"):
            self.assertIn(needle, telemetry,
                          f"详情遥测缺少 {needle}：离开详情后定时器还在上报")

        outside = app[app.index("function bindOutsideClose("):]
        outside = outside[:outside.index("\nfunction disposeStage(")]
        self.assertIn("document.addEventListener('pointerdown',handler,true)", outside)
        self.assertIn("document.removeEventListener('pointerdown',handler,true)", outside)
        self.assertIn("onStageDispose(detach)", outside,
                      "浮层没被关掉就离开详情时，要有舞台销毁兜底")
        self.assertPageContains("detachOutside=bindOutsideClose(plus,picker,closePicker)")

    def test_detail_close_disposes_playback_source(self):
        self.assertPageContains("function disposeStage")
        self.assertPageContains("video.pause();video.removeAttribute('src');video.load();video.remove()")
        self.assertPageContains("document.body.classList.remove('detail-open');current=null;activeQueue=null")
        self.assertPageContains("detailOriginAnchor=null;detailOriginAbove=false;detailReturnNeedsRestore=false")
        self.assertPageContains("scheduleStickySurfaces();")
        self.assertPageContains("const closeDetail=async()=>{const restore=cloneBarsContext(detailReturnBarsContext)")
        self.assertPageContains("$('#closeStage').onclick=closeDetail")
        self.assertPageContains("function cancelDetailStream()")
        self.assertPageContains("/api/stream-cancel?session=")
        self.assertPageContains("keepalive:true")
        self.assertPageContains("dataset.peachStreamCancel=JSON.stringify(result)")
        self.assertPageContains("/api/stream-plan?id=")
        self.assertNotIn("if(!['115','pikpak'].includes(it.location))return direct", self.app_js)
        self.assertPageContains("const source=()=>options.source?Promise.resolve(options.source):detailStreamSource(it)")
        self.assertPageContains("source().then(next=>")
        self.assertPageContains("fallbackUsed=false")
        self.assertPageContains("player.src(directDetailSource(it))")
        self.assertPageContains("detailPlayer.dispose()")

    def test_metered_stream_gate_occupies_the_player_until_clicked(self):
        # `.vwrap video{display:block}` 不能把 hidden 播放器提前画出来；否则入口和播放器
        # 会在同一个 flex 容器里各占一半。点击入口后再取消 hidden、移除入口并自动播放。
        self.assertPageContains(".vwrap>video[hidden]{display:none}")
        self.assertPageContains(".gate{aspect-ratio:16/9;width:100%")
        # 挂播放器现在要等 video.js 到位，入口回调因此是 async。
        self.assertCode(
            "else if(g)g.onclick=async()=>{vv.hidden=false;g.remove();"
            "const mounted=await mountDetailPlayer(it,vv,true)"
        )

    def test_detail_uses_pinned_videojs_and_authoritative_duration(self):
        self.assertPageContains('/vendor/videojs/8.24.0/video.min.js')
        self.assertPageContains('/vendor/videojs/8.24.0/video-js.min.css')

    def test_detail_opens_with_the_local_cover_before_the_video_loads(self):
        """详情开场先把本地封面挂上海报位。

        video.js 按需加载，流源又是一趟解析往返：这中间画面不该是黑的。移除
        交给播放器自己：挂载前是 `<video>` 的原生 poster，挂载后是 video.js 的
        海报层，开播即收，详情侧不另写一套收尾逻辑。
        """
        self.assertPageContains("function detailPosterUrl(it){")
        self.assertPageContains("const vv=$('#vid'),poster=detailPosterUrl(it);")
        self.assertPageContains("poster:options.poster||detailPosterUrl(it)")

    def test_detail_poster_follows_the_jav_image_preference(self):
        body = self.app_js.split('function detailPosterUrl(it){', 1)[1].split('\n}', 1)[0]
        self.assertIn("javImageKind(it,appSettings.javImage)==='cover'", body)
        self.assertIn("`/cover?code=${encodeURIComponent(it.code||'')}`", body)
        self.assertIn("/poster?id=${it.id}&c=4", body)

    def test_changing_the_jav_image_preference_repaints_the_open_detail(self):
        cover_body = self.app_js.split("wireIconSwitch(mount,'data-jav-image-choice',choice=>{", 1)[1].split('});', 1)[0]
        self.assertIn("repaintDetailPoster();", cover_body)
        repaint = self.app_js.split('function repaintDetailPoster(){', 1)[1].split('\n}', 1)[0]
        self.assertIn("detailPlayer.poster(poster)", repaint)
        self.assertIn("$('#vid')?.setAttribute('poster',poster)", repaint)
        # 海报层属于详情播放器，函数就排在它前面；开场判据里 current 是详情独有的状态。
        self.assertLess(self.app_js.index('function repaintDetailPoster(){'),
                        self.app_js.index('async function mountDetailPlayer('))

    def test_follow_detail_poster_survives_the_player_mount(self):
        """video.js 只认 options 里的海报，不读元素上的 poster 属性。

        关注视频的缩略图已经写在元素上，挂载那一刻却被丢掉：开播前又剩黑场。
        同一条 poster 递进 options，挂载前后看到的才是同一张图。
        """
        self.assertPageContains("poster:item.thumb_url")

    def test_the_player_script_is_fetched_on_demand_instead_of_in_the_first_paint(self):
        """video.js 676KB，只有开始看片才用得上，和 Swiper 同一口径不进首屏。

        语言包必须串在主脚本之后：`videojs.addLanguage` 要求先有 videojs，
        并行加载会随机丢掉中文界面。
        """
        self.assertCode("const ensureVideojs=()=>{")
        self.assertCode(
            "videojsLoader=loadScript('/vendor/videojs/8.24.0/video.min.js')"
            ".then(()=>loadScript('/vendor/videojs/8.24.0/lang/zh-CN.js'))")
        self.assertPageLacks('<script src="/vendor/videojs',
                             "播放器脚本才用得上，不进首屏")
        # 样式表留在首屏：它是 .video-js 的版式来源，等到点开才拉会先闪一帧裸 video。
        self.assertPageContains('<link rel="stylesheet" href="/vendor/videojs/8.24.0/video-js.min.css">')

    def test_detail_player_controls_use_two_rows_and_offer_real_quality_levels(self):
        self.assertPageContains(".vwrap .video-js .vjs-big-play-button{left:50%;top:50%;width:56px;height:56px")
        self.assertPageContains("border-top:.72em solid transparent;border-bottom:.72em solid transparent;border-left:1.05em solid #fff")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar{box-sizing:border-box;left:12px;right:12px;bottom:8px;width:auto;height:59px")
        self.assertPageContains("border-radius:0;background:transparent;backdrop-filter:none")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar>.vjs-play-control{position:relative;align-self:flex-end;flex:0 0 40px;width:40px;height:40px")
        # overflow 要放开：悬停提示挂在按钮里，裁掉溢出就等于把提示裁没。
        self.assertPageContains("border:0;border-radius:50%;background:rgba(0,0,0,.6);box-shadow:none;overflow:visible")
        self.assertPageContains("const playIcon=morphIcon(play,'player-play'),playPath=playIcon?.querySelector('path')")
        self.assertPageContains("id=\"i-player-play\"")
        self.assertPageContains("id=\"i-player-pause\"")
        self.assertPageContains(".vjs-peach-right-controls{box-sizing:border-box;position:relative;align-self:flex-end")
        self.assertPageContains("padding:0 4px;display:flex;align-items:center;border:0;border-radius:var(--pill-radius);background:rgba(0,0,0,.6);box-shadow:none")
        self.assertPageContains("overflow:visible;transition:width .2s")
        self.assertPageContains("opacity:0;visibility:hidden;pointer-events:none")
        self.assertPageContains("opacity:1;visibility:visible;pointer-events:auto")
        self.assertPageContains(".vjs-peach-right-controls>.vjs-control:hover>.vjs-peach-hover")
        self.assertPageContains("background:rgba(255,255,255,.1)")
        self.assertPageContains("function mountPlayerChromeLayout(player)")
        self.assertPageContains("group.className='vjs-peach-right-controls'")
        self.assertPageContains("controlBar.querySelector(':scope>.vjs-picture-in-picture-control')")
        self.assertPageContains("controlBar.querySelector(':scope>.vjs-fullscreen-control')")
        self.assertPageContains(".vwrap .video-js .vjs-progress-control{z-index:2;position:absolute;left:0;right:0;top:-12px;width:auto;height:18px")
        self.assertPageContains(".vwrap .video-js .vjs-play-progress{background:var(--tungsten)}")
        self.assertPageContains(".vwrap .video-js .vjs-play-progress:before{content:\"\"")
        self.assertPageContains("width:100%;height:6px;margin:0;border-radius:0")
        self.assertPageContains("transform:scaleY(.667);transition:transform .2s cubic-bezier(.05,0,0,1)")
        self.assertPageContains("transform:translateY(-50%) scale(1,1.5);box-shadow:none")
        self.assertPageContains("transform:translateY(-50%) scale(1.67)")
        self.assertPageContains(".vwrap .video-js .vjs-play-progress .vjs-time-tooltip{display:none!important}")
        self.assertPageContains(".vwrap .video-js .vjs-custom-control-spacer{display:block;flex:1 1 auto}")
        self.assertPageContains(".vwrap .video-js .vjs-time-control{display:none!important}")
        self.assertPageContains(".vwrap .video-js .vjs-peach-time{box-sizing:border-box;align-self:flex-end")
        self.assertPageContains("padding:0 16px;border:0;border-radius:var(--pill-radius);background:rgba(0,0,0,.6)")
        self.assertPageContains("time.type='button';time.className='vjs-peach-time vjs-control';time.dataset.playerTime=''")
        self.assertPageContains("remaining=!remaining;syncTime()")
        self.assertPageContains("time.innerHTML='<span class=\"vjs-peach-time-text\"></span>'")
        self.assertPageContains("timeText.textContent=`${shown} / ${fmtClock(duration)}`")
        self.assertPageContains(".vjs-peach-time:hover:after")
        self.assertPageContains(".vwrap .video-js.vjs-layout-x-small .vjs-progress-control")
        self.assertPageContains(".vwrap .video-js.vjs-layout-small .vjs-current-time")
        self.assertPageContains("currentTimeDisplay:true,timeDivider:true")
        self.assertPageContains("durationDisplay:true,remainingTimeDisplay:false")
        self.assertPageContains(".vjs-peach-settings [data-player-quality-badge]")
        self.assertPageContains("${icon('settings')}")
        self.assertPageContains("typeof player.qualityLevels==='function'?player.qualityLevels():null")
        self.assertPageContains("activePixels>=2160?'4K':activePixels>=720?'HD':''")
        # 「auto 开全部层级，选定某一档只留那一档」是契约；局部变量叫什么不是。
        self.assertPageContains("levels[index].enabled=selectedQuality==='auto'||selectedQuality===String(index)")
        self.assertPageContains("const mute=volume?.querySelector(':scope>.vjs-mute-control'),muteIcon=morphIcon(mute,'player-volume')")
        self.assertPageLacks("volume.insertAdjacentHTML('afterbegin','<span class=\"vjs-peach-hover\"")
        self.assertPageContains("z-index:1;position:relative!important;left:0!important;top:0!important;align-self:center;flex:0 0 40px")
        self.assertPageContains("const syncFullscreenState=()=>{")
        self.assertPageContains("id=\"i-player-volume\"")
        self.assertPageContains("id=\"i-player-volume-muted\"")
        self.assertPageContains("id=\"i-player-fullscreen-enter\"")
        self.assertPageContains("id=\"i-player-fullscreen-exit\"")
        self.assertPageContains(".vjs-peach-control-icon{position:absolute;z-index:2;left:50%;top:50%;width:24px;height:24px")
        self.assertPageContains("[data-peach-explicit-icon]:active>.vjs-peach-control-icon")
        self.assertPageContains("function mountDetailPlayer(it,video,autoplay,options={})")
        self.assertPageContains("detailPlayer.duration(expected)")
        self.assertPageContains("['loadstart','loadedmetadata','durationchange','error']")
        # 仍然是「先账本、后媒体元素」的回退，只是两边都先过 realDuration：
        # 账本里的 -1 是探测硬失败的哨兵，裸真值判断挡不住它。
        self.assertPageContains(
            "const d=realDuration(it.duration)||realDuration(v.duration)")
        self.assertPageLacks("skipButtons:{backward:appSettings.seekSeconds,forward:appSettings.seekSeconds}")

    def test_player_seek_preview_reuses_contact_sheet_cells_and_online_falls_back_to_time(self):
        self.assertPageContains("function mountPlayerSeekPreview(player,it,options={})")
        self.assertPageContains("preview.dataset.playerSeekPreview='';preview.hidden=true")
        self.assertPageContains("const nextCell=Math.min(8,Math.floor(ratio*9))")
        self.assertPageContains("image.src=`/poster?id=${encodeURIComponent(it.id)}&c=${nextCell}`")
        self.assertPageContains("mountPlayerSeekPreview(detailPlayer,it,{thumbnail:!options.source})")
        self.assertPageContains(".vjs-peach-seek-frame{position:relative;width:240px;aspect-ratio:16/9")

    def test_the_player_has_exactly_one_center_feedback_circle(self):
        """画面中心只有 `.vjs-peach-bezel` 这一块 78px 提示圆。

        两块同尺寸的提示圆各按自己的时机读播放状态时，点一下控制条的播放键，一块闪
        播放、另一块闪暂停，两个图标叠在同一个圆里。所以这里既钉住那一块圆的三个触发面
        （播放键、静音键、画面本身），也钉住第二块不再存在。
        """
        self.assertPageContains("player.el().addEventListener('click',event=>{")
        self.assertPageContains("event.target.closest('.vjs-play-control,.vjs-tech,.vjs-poster')")
        self.assertPageContains("event.target.closest('.vjs-mute-control')")
        self.assertPageLacks('data-center-seek=')
        self.assertPageLacks('data-center-toggle')
        self.assertPageLacks("vjs-peach-center-controls")
        self.assertPageLacks("vjs-peach-center-bezel")
        self.assertPageLacks("peach-player-bezel-fadeout")
        self.assertPageLacks("i-player-bezel-play")
        self.assertPageLacks("i-player-bezel-pause")
        self.assertPageContains(".vwrap .video-js:has(.vjs-peach-bezel) .vjs-big-play-button{display:none}")
        self.assertPageContains(".video-js.vjs-waiting .vjs-peach-bezel,.video-js.vjs-seeking .vjs-peach-bezel,")
        self.assertPageContains(".video-js.vjs-error .vjs-peach-bezel{display:none}")

    def test_player_spinner_replaces_the_videojs_arcs_with_the_four_part_dom(self):
        self.assertPageContains("function mountPlayerSpinner(player)")
        self.assertPageContains("mountPlayerSpinner(detailPlayer)")
        self.assertPageContains("vjs-peach-spinner-container")
        self.assertPageContains("animation:peach-spinner-linspin 1.5682352941176s linear infinite")
        self.assertPageContains("animation:peach-spinner-easespin 5332ms cubic-bezier(.4,0,.2,1) infinite both")
        self.assertPageContains("animation:peach-spinner-left-spin 1333ms cubic-bezier(.4,0,.2,1) infinite both")
        self.assertPageContains("animation:peach-spinner-right-spin 1333ms cubic-bezier(.4,0,.2,1) infinite both")

    def test_cards_show_blue_watched_progress_from_play_seconds(self):
        self.assertPageContains("const watchedRatio=!parts&&Number(it.play_seconds)>0&&Number(it.duration)>0")
        self.assertPageContains('class="watchprogress" role="progressbar" aria-label="观看进度"')
        self.assertPageContains(".watchprogress i{display:block;height:100%;background:var(--tungsten)}")

    def test_player_stats_button_matches_the_round_player_controls(self):
        self.assertPageContains(".playerstatsbtn{position:absolute;left:11px;top:11px;z-index:8;width:40px;height:40px")
        self.assertPageContains("display:grid;place-items:center;border:0;border-radius:50%")
        self.assertPageContains(".playerstatsbtn:after,.closestage:after{content:\"\";position:absolute;z-index:0;inset:4px;border-radius:50%")
        self.assertPageContains(".playerstatsbtn:hover:after,.playerstatsbtn:focus-visible:after,.closestage:hover:after,.closestage:focus-visible:after{background:rgba(255,255,255,.1)}")
        self.assertPageContains(".playernet{box-sizing:border-box;position:absolute;left:58px;top:11px;z-index:8;height:40px;min-height:40px")
        self.assertPageContains("display:flex;align-items:center;gap:7px;white-space:nowrap;border:0;border-radius:var(--floating-radius)")

    def test_load_rate_badge_reads_as_one_line_with_a_white_gauge(self):
        """徽标里只剩一个仪表盘图标加一段速率，两者在同一行。

        `white-space` 默认可断，`640 KB/s` 会在这条 flex 行里断成两行，把 40px 的胶囊顶破。
        图标一侧是本仓库反复出现的那个缺陷：sprite 里的仪表盘是描边图形，容器不声明
        stroke/fill 就按 SVG 默认的 fill 画成黑色实心块，压在 rgba(0,0,0,.6) 的底上
        等于没有图标。所以容器规则和图标本身要一起守。
        """
        self.assertPageContains(
            '<symbol id="i-gauge" viewBox="0 0 24 24"><path d="m12 14 4-4" />')
        self.assertPageContains(
            ".playernet svg{width:18px;height:18px;flex:none;stroke:currentColor;fill:none;"
            "stroke-width:2;stroke-linecap:round}")
        self.assertPageContains("align-items:center;gap:7px;white-space:nowrap;")
        self.assertPageLacks("${icon('download')}<span class=\"sr-only\">加载速度")

    def test_player_settings_match_real_ambient_speed_and_quality_capabilities(self):
        self.assertPageContains("class=\"vjs-peach-settings-menu\" role=\"menu\" aria-label=\"播放器设置\"")
        self.assertPageContains('role="menuitemcheckbox" data-player-ambient')
        self.assertPageContains("<span>氛围模式</span>")
        self.assertPageContains("<span>播放速度</span>")
        self.assertPageContains("<span>清晰度</span>")
        self.assertPageContains("setSpeed(Number(button.dataset.playerSpeedOption))")
        self.assertPageContains("applyAmbientMode(!appSettings.ambientMode)")
        self.assertPageContains("${icon('player-ambient')}")
        self.assertPageContains("${icon('player-speed')}")
        self.assertPageContains("${icon('player-quality')}")
        self.assertPageContains('id="i-player-ambient"')
        self.assertPageContains('id="i-player-speed"')
        self.assertPageContains('id="i-player-quality"')
        self.assertPageContains('id="i-player-menu-next"')
        self.assertPageContains('id="i-player-menu-back"')
        self.assertPageContains('id="i-player-option-check"')
        self.assertPageContains('M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z')
        self.assertPageContains("icon('player-option-check')")
        self.assertPageContains(".vjs-peach-settings-menu{box-sizing:border-box;position:absolute;z-index:2300;right:-100px;bottom:52px;width:min(274px")
        self.assertPageContains("padding:0;border:0;border-radius:var(--floating-radius);background:rgba(0,0,0,.6);box-shadow:none")
        self.assertPageContains(".vjs-peach-panel-menu{padding:8px}")
        self.assertPageContains("min-height:48px;padding:0;border:0;border-radius:var(--control-radius)")
        self.assertPageContains(".vjs-peach-menu-row>svg{justify-self:start;margin-left:8px;width:24px;height:24px")
        self.assertPageContains(".video-js .vjs-peach-menu-row{display:grid;grid-template-columns:56px minmax(0,1fr) minmax(0,max-content) 32px")
        self.assertPageContains(".vjs-peach-panel-header{box-sizing:border-box;height:57px;padding:8px 0;display:flex;align-items:center;gap:0;border-bottom:1px solid rgba(255,255,255,.2)")
        self.assertPageContains(".vjs-peach-settings-menu .vjs-peach-panel-header .vjs-peach-menu-back:before{inset:4px}")
        self.assertPageContains(".video-js .vjs-peach-menu-option{display:grid;grid-template-columns:35px minmax(0,1fr)")
        self.assertPageContains('class="vjs-peach-option-check"')
        self.assertPageContains('class="vjs-peach-option-label"')
        self.assertPageContains("class=\"vjs-peach-panel-header\"")
        self.assertPageContains('aria-label="返回上一个菜单"')
        self.assertPageContains("color:#eee")
        self.assertPageContains(".vjs-peach-switch{box-sizing:border-box;display:block;position:relative;width:40px;height:24px;border-radius:var(--floating-radius)")
        self.assertPageContains("background:rgba(0,0,0,.3)")
        self.assertPageContains("background:rgba(255,255,255,.7)")
        self.assertPageContains(".vjs-peach-settings-menu button:before{content:\"\";position:absolute;z-index:0;inset:0")
        self.assertPageLacks("睡眠定时")

    def test_player_play_hover_is_round_and_volume_matches_the_other_controls(self):
        """播放键是 40px 的圆，hover 高亮层却是 40×32 的胶囊，亮起来是个两头圆的方块。

        圆键的高亮统一是内缩 4px 的同心圆（音量键、时间钮已是），播放键、左上统计钮、
        右上关闭钮跟着走；统计钮和关闭钮的底色 .3、音量键的 .3 都和播放键的 .6 不是一档。
        """
        self.assertPageContains(
            ".vjs-control-bar>.vjs-play-control>.vjs-peach-hover{inset:4px;width:auto;height:auto;border-radius:50%}")
        for selector in (".playerstatsbtn{", ".closestage{"):
            start = self.css.rindex(selector)
            rule = self.css[start:self.css.index("}", start)]
            self.assertIn("background:rgba(0,0,0,.6)", rule, f"{selector} 和同屏的播放键不是一档黑")
            self.assertIn("isolation:isolate;overflow:hidden", rule)
        self.assertPageLacks(".playerstatsbtn:hover,.playerstatsbtn:focus-visible{background:rgba(255,255,255,.1)")
        self.assertPageLacks(".closestage:hover,.closestage:focus-visible{background:rgba(255,255,255,.1)")
        self.assertPageContains(
            "margin:0 0 8px 12px;padding:0;border:0;border-radius:var(--pill-radius);background:rgba(0,0,0,.6);box-shadow:none;")
        self.assertPageContains(
            "grid-template-columns:40px 52px;column-gap:3px;padding-right:16px;background:rgba(0,0,0,.6)}")
        self.assertPageLacks(".vjs-volume-panel{background:rgba(0,0,0,.3)!important")

    def test_player_text_uses_the_page_font_not_video_js_arial(self):
        """video.js 自带 Arial，加载速度徽章还写死了 Cascadia Mono：一个播放器里三种字。"""
        self.assertPageContains(".vwrap .video-js{font-family:inherit}")
        self.assertPageContains("font-weight:400;font-size:var(--fs-md);line-height:40px;font-family:inherit;")
        self.assertPageContains("font-weight:400;font-size:var(--fs-md);line-height:1.3;font-family:inherit}")
        self.assertPageContains("font-size:var(--fs-xs);line-height:1;font-family:inherit}")
        self.assertPageContains("font-size:var(--fs-xs);line-height:1.5;font-family:inherit}")
        self.assertPageLacks('"Cascadia Mono",monospace}')
        self.assertPageLacks("Arial,sans-serif")

    def test_player_volume_background_survives_theater_and_fullscreen(self):
        self.assertPageContains(".stage.theater-mode .vwrap .video-js .vjs-control-bar>.vjs-volume-panel")
        self.assertPageContains(".video-js.vjs-fullscreen .vjs-control-bar>.vjs-volume-panel")
        self.assertPageContains("background:rgba(0,0,0,.6)!important")
        self.assertPageContains("grid-template-columns:40px 52px;column-gap:3px;padding-right:16px")
        self.assertPageContains(".vjs-control-bar>.vjs-volume-panel:after{content:\"\";position:absolute;z-index:0;inset:4px")
        self.assertPageContains(".vjs-control-bar>.vjs-volume-panel.vjs-slider-active:after{background:rgba(255,255,255,.1)}")
        self.assertPageContains(".vjs-mute-control[data-peach-explicit-icon]>.vjs-icon-placeholder{display:none!important}")
        self.assertPageContains("display:block!important;align-self:center;flex:0 0 52px;width:52px!important")
        # 滑轨撑满面板那 40px 高，整条背景都接得住点击；那条 2px 的线画在它的竖直中线上。
        self.assertPageContains("top:0!important;width:52px!important;height:40px!important;margin:0!important")
        self.assertPageContains(".vjs-volume-bar.vjs-slider-horizontal::before{content:\"\";position:absolute;"
                                "left:0;right:0;top:50%;height:2px;margin-top:-1px;background:rgba(255,255,255,.3)}")
        self.assertPageContains(".vjs-volume-level{top:50%;bottom:auto;height:2px;margin-top:-1px;background:#fff}")
        # 鼠标位置那条 1px 线随滑轨一起有 40px 高，去掉底色；数字仍挂在它身上。
        self.assertPageContains(".vwrap .video-js .vjs-volume-panel .vjs-mouse-display{background:transparent}")
        self.assertPageContains(".vjs-control-bar>.vjs-volume-panel{box-sizing:border-box;z-index:3;position:relative")
        # 音量胶囊和右边那枚胶囊同一排、同一档底色，毛玻璃也必须同一档：只有一边磨砂，
        # 展开之后它就比邻居更透，画面颜色直接透上来。
        self.assertPageContains(
            "border-radius:var(--pill-radius);background:rgba(0,0,0,.6);box-shadow:none;\n"
            "  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);")
        # Video.js 每 30ms 往音量提示上写一句行内 `style.right=-Npx`。行内声明压过样式表里
        # 同名的普通声明，`left:50%` 和它同时成立时宽度改由两边反推，底色摊成一块比数字大
        # 得多的方块，而且它下一帧按新宽度重算 N，尺寸一直在飘。
        self.assertPageContains(".vjs-volume-panel .vjs-volume-tooltip{z-index:5!important;left:50%;right:auto!important;top:auto")

    def test_theater_mode_has_button_tooltip_keyboard_and_responsive_layout(self):
        self.assertPageContains("function mountPlayerTheaterControl(player,settingsRoot)")
        self.assertPageContains("data-player-theater aria-pressed=")
        self.assertPageContains(
            "theaterButton.peachTooltipSync=playerControlTooltip(theaterButton,'影院模式','T')")
        self.assertPageContains("function syncPlayerTheaterButton(button)")
        self.assertPageContains("appSettings.theaterMode?'默认视图':'影院模式'")
        self.assertPageContains("appSettings.theaterMode?'#i-theater-exit':'#i-theater-enter'")
        self.assertPageContains("if(e.key==='t'||e.key==='T')")
        self.assertPageContains(".stage.theater-mode .sgrid{grid-template-columns:minmax(0,1fr)}")
        self.assertPageContains('grid-template-areas:"media" "side" "queue"')
        self.assertPageContains('id="i-theater-enter"')
        self.assertPageContains('id="i-theater-exit"')

    def test_control_bar_buttons_share_one_tooltip_with_keyboard_badges(self):
        """控制条上每个按钮都有提示，样式取自 YouTube delhi-modern，带快捷键徽标。

        播放、静音、时间、画中画、设置、全屏、影院共用同一套提示与快捷键。提示层必须抹掉
        浏览器原生 title，否则两层提示会一前一后叠着弹。
        """
        self.assertPageContains("function playerControlTooltip(button,label,shortcut='')")
        self.assertPageContains("tip.innerHTML='<span class=\"vjs-peach-tooltip-text\"></span><kbd hidden></kbd>'")
        self.assertPageContains("if(shortcut)button.setAttribute('aria-keyshortcuts',shortcut)")
        self.assertPageContains("key.hidden=!shortcut")
        self.assertPageContains("button.removeAttribute('title')")
        self.assertPageContains("playerControlTooltip(play,'播放','K')")
        self.assertPageContains("playerControlTooltip(mute,'静音','M')")
        self.assertPageContains("playerControlTooltip(time,'显示剩余时间')")
        # i 键归迷你播放器（YouTube 的 aria-keyshortcuts="i"），画中画只留按钮不带徽标。
        self.assertPageContains("playerControlTooltip(pip,'画中画')")
        self.assertPageContains("playerControlTooltip(fullscreen,'全屏','F')")
        self.assertPageContains("playerControlTooltip(toggle,'设置')")
        # 快捷键走按钮自己的点击路径，全屏和画中画的兜底逻辑只写一份。
        self.assertPageContains("function clickPlayerControl(video,selector)")
        self.assertPageContains("if(e.key===' '||e.key==='k'||e.key==='K')")
        self.assertPageContains("if(e.key==='m'||e.key==='M'){e.preventDefault();clickPlayerControl(video,'.vjs-mute-control')")
        self.assertPageContains("if(e.key==='f'||e.key==='F'){e.preventDefault();clickPlayerControl(video,'.vjs-fullscreen-control')")
        self.assertPageContains("if(e.key==='i'||e.key==='I'){e.preventDefault();toggleMiniplayerShortcut();return}")
        # 提示外观与音量百分比共用一套毛玻璃，音量提示抬到控制条上方。
        self.assertPageContains(".vjs-peach-tooltip{position:absolute;z-index:5;right:50%;bottom:calc(100% + 12px)")
        self.assertPageContains("backdrop-filter:blur(16px)")
        self.assertPageContains(".vjs-peach-tooltip kbd{display:flex;justify-content:center;align-items:center;min-width:11px")
        self.assertPageContains(".vjs-peach-tooltip kbd[hidden]{display:none}")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar button:hover>.vjs-peach-tooltip")
        self.assertPageContains(".vjs-volume-tooltip{z-index:5!important;left:50%;right:auto!important;top:auto;bottom:calc(50% + 31px)")
        # 提示要露出控制条，播放键和时间钮不能再靠 overflow 裁。
        self.assertPageLacks("background:rgba(0,0,0,.6);box-shadow:none;overflow:hidden}")

    def test_miniplayer_keeps_the_playing_video_when_leaving_the_detail(self):
        """离开详情时正在放的视频缩到角落继续放，几何照 YouTube 桌面版 ytd-miniplayer 实测。

        证据在 `docs/reference-snapshots/youtube-miniplayer-measured.md`：fixed、离边 16px、宽 400、
        信息栏 76px、12px 圆角、双层阴影，吸附回角是 transform .5s cubic-bezier(.05,0,0,1)。播放器
        不销毁而是整块搬走，流会话跟着它；显式关闭、换详情和删条目才真的销毁。
        """
        self.assertPageContains('id="miniplayerSetting"')
        self.assertPageContains("appSettings.miniplayer=appSettings.miniplayer!==false;")
        self.assertPageContains("$('#miniplayerSetting').checked=appSettings.miniplayer;")
        self.assertPageContains('<aside class="miniplayer" id="miniplayer" data-corner="br" aria-label="小窗播放" hidden>')
        self.assertPageContains('id="miniplayerExpand" aria-label="展开到详情" aria-keyshortcuts="i"')
        self.assertPageContains('id="miniplayerClose" aria-label="关闭小窗"')
        self.assertPageContains('id="miniplayerPlay" aria-label="暂停" aria-keyshortcuts="k"')
        self.assertPageContains('<button type="button" class="miniplayerinfo" id="miniplayerInfo" aria-label="展开到详情">')
        self.assertPageContains("--layer-miniplayer:900; --layer-dialog:1000;")
        self.assertPageContains(".miniplayer{position:fixed;z-index:var(--layer-miniplayer);width:min(400px,calc(100vw - 32px))")
        self.assertPageContains('.miniplayer[data-corner="tr"]{right:16px;top:calc(var(--topH) + 16px)}')
        self.assertPageContains(".miniplayer.miniplayer-snapping{transition:transform .5s cubic-bezier(.05,0,0,1)}")
        self.assertPageContains("box-shadow:0 2px 5px rgba(0,0,0,.16),0 3px 6px rgba(0,0,0,.2)")
        self.assertPageContains("min-height:76px")
        # 播放器搬家而不是销毁：只有显式关闭、换详情和删条目传 miniplayer:false。
        self.assertPageContains("function disposeStage(push=false,preserveInlineOrigin=false,{miniplayer=true}={})")
        self.assertPageContains("if(toMini)enterMiniplayer(detailPlayer,meta);")
        self.assertPageContains("if(!toMini&&!owned)cancelDetailStream();")
        self.assertPageContains("disposeStage(false,true,{miniplayer:false});")
        self.assertPageContains("disposeStage(false,false,{miniplayer:false});")
        self.assertPageContains("disposeStage(true,false,{miniplayer:false});")
        # 小窗开着时普通视频卡直接换片；展开回详情从同一时刻接着放，深链 `?t=` 走同一口子。
        self.assertPageContains("function miniplayerTakesCard(it)")
        self.assertPageContains("miniplayerTakesCard(it)?miniplayerPlay(id):onClick?onClick(id,anchor)")
        self.assertPageContains("queueDetailResume(kind,item.id,player.currentTime(),!player.paused());")
        self.assertPageContains("const resume=takeDetailResume(options.source?'follow':'item',it.id);")
        self.assertPageContains("if(resume?.time>0)player.one('loadedmetadata'")
        # 拖到哪个象限就吸到哪个角；键盘 k / i 在小窗里同样有效。
        self.assertPageContains("const corner=(rect.top+rect.height/2<innerHeight/2?'t':'b')+(rect.left+rect.width/2<innerWidth/2?'l':'r');")
        self.assertPageContains("if((!stage||stage.hidden)&&miniplayerActive())return miniplayerVideo();")
        self.assertPageContains("function toggleMiniplayerShortcut()")

    def test_the_small_window_gets_its_own_seek_keys(self):
        """小窗里播放键两侧各一颗快退快进，步长跟设置里那个秒数走。

        上游 YouTube 的小窗没有这两颗。Peach 自己要：小窗一开就离开了详情，站内那条控制条
        一颗键都递不进来，只剩底下那条 5px 的进度条能拖，想跳十秒得先回详情。标签里带着
        秒数，读屏用户按之前听得到自己会跳多远；接手播放器时重写一遍，设置改完开的下一个
        小窗就是新的秒数。时长取不到时不封顶——直播和还没读到元数据的片子 `duration()` 是
        NaN，拿它去 `Math.min` 会把进度扔成 NaN，视频停在原地不动。
        """
        self.assertPageContains('<button type="button" class="miniplayerseek" id="miniplayerBack">'
                                '<svg viewBox="0 0 24 24" aria-hidden="true">'
                                '<use href="#i-rotate-ccw"/></svg></button>')
        self.assertPageContains('<button type="button" class="miniplayerseek" id="miniplayerAhead">'
                                '<svg viewBox="0 0 24 24" aria-hidden="true">'
                                '<use href="#i-rotate-cw"/></svg></button>')
        self.assertPageContains("function syncMiniplayerSeekLabels()")
        self.assertPageContains("[['#miniplayerBack',`后退 ${step} 秒`],"
                                "['#miniplayerAhead',`前进 ${step} 秒`]]")
        self.assertPageContains("const at=Math.max(0,(Number(player.currentTime())||0)+step*side);")
        self.assertPageContains("player.currentTime(total?Math.min(total,at):at);")
        self.assertPageContains("$('#miniplayerBack').onclick=seekBy(-1);")
        self.assertPageContains("$('#miniplayerAhead').onclick=seekBy(1);")
        # 按在这两颗上不能起手拖窗，否则一次点击变成一次挪位。
        self.assertPageContains("event.target.closest('.miniplayerbtn,.miniplayerplay,"
                                ".miniplayerseek,.vjs-control-bar')")
        self.assertPageContains(".miniplayerseek{width:36px;height:36px}")

    def test_player_context_menu_lists_only_the_actions_peach_can_do(self):
        """播放器右键菜单照 YouTube f572e43c 的 .ytp-contextmenu 取舍，只留 Peach 有能力的项。

        循环播放、迷你播放器／展开、画中画、复制视频网址、复制当前时间的视频网址、播放统计。
        嵌入代码、调试信息和排查播放问题没有对应能力，不列。外观与右下角设置面板同一份：
        --floating-radius 圆角、rgba(0,0,0,.6) 加 blur(16px)、无阴影、每项 48px、图标列 56px、
        白字、悬停 rgba(255,255,255,.1)。
        """
        self.assertPageContains('<div class="popmenu playermenu" id="playerMenu" role="menu" aria-label="播放器菜单" hidden></div>')
        self.assertPageContains("wirePlayerContextMenu(detailPlayer);")
        self.assertPageContains("event.preventDefault();openPlayerMenu(player,event.clientX,event.clientY);")
        for label in ("循环播放", "迷你播放器", "展开", "画中画", "复制视频网址", "复制当前时间的视频网址", "播放统计"):
            with self.subTest(label=label):
                self.assertPageContains(f"label:'{label}'")
        for absent in ("复制嵌入代码", "复制调试信息", "排查播放问题"):
            with self.subTest(label=absent):
                self.assertPageLacks(f"label:'{absent}'")
        self.assertPageContains("role=\"${checkable?'menuitemcheckbox':'menuitem'}\"")
        self.assertPageContains("link.searchParams.set('t',String(Math.floor(player.currentTime()||0)));")
        self.assertPageContains("#playerMenu.playermenu{padding:8px;border:0;gap:0;border-radius:var(--floating-radius);background:rgba(0,0,0,.6);")
        self.assertPageContains("grid-template-columns:56px minmax(0,1fr) 32px;gap:0;align-items:center;width:100%;min-height:48px;")
        self.assertPageContains("#playerMenu>.playermenuitem:hover,#playerMenu>.playermenuitem:focus-visible{background:rgba(255,255,255,.1);color:#fff;outline:0}")
        self.assertPageContains('.playermenuitem[aria-checked="true"]>.playermenucheck{visibility:visible}')

    def test_narrow_player_collapses_the_right_controls_instead_of_overflowing(self):
        """播放器窄到 528 以下时右侧只留设置与展开键，点开才铺开其余按钮。

        判据是播放器自己的宽度而不是视口：同一个视口下影院模式和普通视图的播放器宽度
        差一大截，用媒体查询会在影院模式下白折叠、在普通视图下继续超框。
        """
        self.assertPageContains("const box=player.el(),narrow=box.clientWidth<528;")
        self.assertPageContains("box.classList.toggle('vjs-peach-xsmall',narrow)")
        self.assertPageContains("const widthObserver=new ResizeObserver(syncWidthMode)")
        self.assertPageContains("player.on('dispose',()=>widthObserver.disconnect())")
        self.assertPageContains("expand.className='vjs-peach-expand vjs-control'")
        self.assertPageContains("icon('player-expand')")
        # 菜单行那个 `>` 是 24 视框、一个单位粗的细线，铺到展开键的 32px 只有 1.3px；上游
        # 展开键自带一个 32 视框、两个单位粗的箭头，同样 32px 渲染就是 2px。
        self.assertPageContains('<symbol id="i-player-expand" viewBox="0 0 32 32"')
        self.assertPageContains('m12.59 20.34 4.58-4.59-4.58-4.59L14 9.75l6 6-6 6z')
        # 展开键排在这一簇最左：`prepend` 而不是 append，否则它落在全屏键的右边。
        self.assertPageContains("group.prepend(expand)")
        # hover 高亮的规则是 `.vjs-control>.vjs-peach-hover`，高亮层必须是按钮的兄弟节点；
        # 塞进 <button> 里选择器就不命中，这个键会是整排里唯一没有反馈的那个。
        self.assertPageContains(
            '</button><span class="vjs-peach-hover" aria-hidden="true"></span>`;\n'
            '  group.prepend(expand);')
        # 窄屏其余键的 svg 缩到 18px，展开键排除在外并单独铺满 32px：跟着缩就几乎看不出
        # 是个可点的键。上游给这个按钮的 svg 内边距同样是 0。
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-right-controls>.vjs-control"
            ":not(.vjs-peach-expand)>button>svg{width:18px;height:18px}")
        # 窄屏这一排的悬停底是 32×32 的正圆，不是撑满 36px 一格的胶囊。
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-right-controls>.vjs-control>.vjs-peach-hover{")
        self.assertPageContains("left:2px;width:32px;height:32px;border-radius:50%}")
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-expand>button>svg{width:32px;height:32px}")
        self.assertPageContains("expandButton.setAttribute('aria-expanded',String(open))")
        self.assertPageContains("syncExpandTooltip(open?'收起控件':'展开控件')")
        self.assertPageContains("if(!narrow)setExpanded(false)")
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-right-controls>.vjs-control:not(.vjs-peach-settings):not(.vjs-peach-expand){display:none}")
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-expand{display:block}")
        # 展开那条要和折叠那条带同样两个 :not()：少两个类就权重不够，点开没反应。
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall.vjs-peach-right-expanded .vjs-peach-right-controls>.vjs-control"
            ":not(.vjs-peach-settings):not(.vjs-peach-expand){display:block}")
        # 展开后时间显示让出宽度：Peach 的控制条比 YouTube 窄，占着位就又超框。
        self.assertPageContains(".video-js.vjs-peach-xsmall.vjs-peach-right-expanded .vjs-peach-time{display:none}")
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-right-controls>.vjs-control{flex:0 0 36px")
        self.assertPageContains(".vjs-peach-expand>button>svg{transition:transform .3s cubic-bezier(.05,0,0,1);transform:rotate(180deg)}")
        self.assertPageContains(".video-js.vjs-peach-right-expanded .vjs-peach-expand>button>svg{transform:rotate(0)}")
        # 视口媒体查询不再另外藏画中画，折叠只有一套判据。
        self.assertPageLacks(".vjs-peach-right-controls>.vjs-picture-in-picture-control{display:none}")

    def test_settings_panel_fades_and_the_submenu_slides(self):
        """关闭态不能是 display:none——它没有可过渡的中间态，面板只会瞬间消失。

        淡入淡出改由 aria-hidden 驱动 opacity，visibility 延后到淡出结束：面板既退出
        无障碍树，也不再接命中测试。次级菜单按上游那份 .25s cubic-bezier(.4,0,.2,1)
        同时推容器高度和推面板，两块面板在同一个容器里错开走。
        """
        self.assertPageContains('aria-label="播放器设置" aria-hidden="true"></div>`')
        self.assertPageLacks(".vjs-peach-settings-menu[hidden]{display:none}")
        self.assertPageContains(
            ".vjs-peach-settings-menu{opacity:1;visibility:visible;"
            "transition:opacity .1s cubic-bezier(0,0,.2,1)}")
        self.assertPageContains(
            '.vjs-peach-settings-menu[aria-hidden="true"]{opacity:0;visibility:hidden;'
            'pointer-events:none;')
        self.assertPageContains("transition:opacity .1s cubic-bezier(.4,0,1,1),visibility 0s .1s}")
        self.assertPageContains(
            ".vjs-peach-settings-menu.vjs-peach-popup-animating{overflow:hidden;"
            "pointer-events:none;transition:height .25s cubic-bezier(.4,0,.2,1)}")
        self.assertPageContains(
            ".vjs-peach-popup-animating .vjs-peach-panel{"
            "transition:transform .25s cubic-bezier(.4,0,.2,1),opacity .25s cubic-bezier(.4,0,.2,1)}")
        self.assertPageContains(".vjs-peach-panel-leaving{position:absolute;left:0;top:0;width:100%}")
        self.assertPageContains(".vjs-peach-panel-animate-back{opacity:0;transform:translateX(-100%)}")
        self.assertPageContains(".vjs-peach-panel-animate-forward{opacity:0;transform:translateX(100%)}")
        self.assertPageContains("const isOpen=()=>menu.getAttribute('aria-hidden')!=='true';")
        self.assertPageContains("const renderPanel=(html,direction)=>{")
        # 动画期间容器里同时挂着两块面板，事件只能绑在这一次新建的那块上；绑在容器上
        # 会连正在退场的旧面板一起接命中，返回键点一次退两级。
        self.assertPageContains("const panel=renderPanel(")
        self.assertPageContains("panel.querySelector('[data-player-menu-back]').onclick=()=>showMain(-1);")
        self.assertPageContains("if(panelTimer)clearTimeout(panelTimer)")

    def test_narrow_player_keeps_both_overlays_inside_the_frame(self):
        """播放器的高度只由 16:9 和宽度决定，两个浮层各自按播放器高度收顶。

        390 宽的视口上 16:9 只有 200 出头的高，比两个浮层都矮。解法是让浮层收顶并内部
        滚动，不是给播放器垫一个像素高度——垫出来的那截在窄屏上是画面上下各一条黑边，
        比它保护的东西还显眼。窄屏的设置面板另外要撤掉 `right:-100px`：那个偏移是给
        设置键右边还有影院键和全屏键时留的位。
        """
        self.assertPageContains(
            ".vwrap>.video-js{width:100%;height:auto;max-height:76vh;"
            "aspect-ratio:16/9;background:#000}")
        self.assertPageContains(".gate{aspect-ratio:16/9;width:100%;background:var(--sunk)")
        self.assertPageContains(
            "max-height:calc(100% - 114px);overflow-y:auto;overscroll-behavior:contain;")
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-settings-menu{right:0;"
            "width:min(274px,calc(100vw - 48px));")
        self.assertPageContains("max-height:calc(var(--peach-player-h,420px) - 74px)}")
        # 面板的定位祖先只有 36px 高，百分比高度到不了播放器，得由布局脚本把高度写上来。
        self.assertPageContains("box.style.setProperty('--peach-player-h',`${box.clientHeight}px`)")

    def test_narrow_settings_panel_fits_the_longest_option_list_without_scrolling(self):
        """清晰度多到八档，单列要 57+16+8×48=457px，320px 高的播放器只给得出 246px。

        行高压到 44px、排成两列是 57+8+4×44=241px；只让选项多于四条的列表分两列，
        主面板那三行仍是单列。
        """
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-panel-menu{padding:4px 8px}")
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-menu-option{min-height:44px}")
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-panel-menu"
            ":has(>.vjs-peach-menu-option:nth-child(5)){display:grid;grid-template-columns:1fr 1fr}")

    def test_playback_speed_panel_matches_the_youtube_slider_layout(self):
        """播放速度是读数加滑条加预设胶囊，照 YouTube delhi-modern 的数值来。

        证据是 player 9470c977 的 www-player.css 与 base.js：内容区 24/16/16 内距，读数
        居中、下留 24px，滑条一行 gap 16px、加减键 32px 圆各动 0.05，胶囊 53×32、gap 8px，
        1.0 底下挂一行 14px 行高的说明。滑条两端取播放器支持的最低与最高倍速，步进 0.05。
        字号、字重和圆角走 Peach 的 token：上游读数那档 18px/900 与说明那档 10px 都不在
        Peach 的刻度上，胶囊和轨道的圆角大于自身高度的一半，`--pill-radius` 渲染结果相同。
        第五格 3.0 在上游要 Premium，本机装的 Peach 没有会员分级，那一格照上游留着，
        只是不画角标；滑条上限跟着抬到 3，不然点 3.0 会被收敛回 2。五格胶囊挤不进
        274px 的面板，所以按 53px 起算、放不下就一起收窄；伸缩量写在包裹层上，胶囊自己
        待在列向 flex 里，`flex-basis` 在那一层量的是高度。
        """
        self.assertPageContains(
            "const SPEED_RATES=[.25,.5,.75,1,1.25,1.5,1.75,2,3],SPEED_STEP=.05,SPEED_PRESETS=[1,1.25,1.5,2,3];")
        self.assertPageContains('<output data-player-speed-display></output>')
        self.assertPageContains(
            '<input type="range" class="vjs-peach-speed-range" data-player-speed-range '
            'min="${min}" max="${max}" step="${SPEED_STEP}" aria-label="播放速度">')
        self.assertPageContains('data-player-speed-step="-1" aria-label="播放速度减 0.05"')
        self.assertPageContains('data-player-speed-step="1" aria-label="播放速度加 0.05"')
        self.assertPageContains('<span class="vjs-peach-speed-preset-label">正常</span>')
        # player.playbackRate() 读的是 ratechange 之后才写的缓存，所以面板自己记住这一次的倍速。
        self.assertPageContains("let rate=clampSpeed(Number(player.playbackRate())||1);")
        self.assertPageContains("display.textContent=`${rate.toFixed(2)}x`;range.value=String(rate);")
        self.assertPageContains("const setSpeed=value=>{rate=clampSpeed(value);player.playbackRate(rate);syncSpeed()};")
        # 轨道已过的比例由脚本写成自定义属性，上游同样是自定义属性驱动那条渐变。
        self.assertPageContains(
            "range.style.setProperty('--peach-speed-percent',`${(rate-min)/(max-min)*100}%`);")
        self.assertPageContains(
            "setSpeed(rate+Number(button.dataset.playerSpeedStep)*SPEED_STEP))")
        self.assertPageContains(
            ".vjs-peach-speed-panel{box-sizing:border-box;display:flex;flex-direction:column;padding:24px 16px 16px}")
        self.assertPageContains("font-size:var(--fs-lg);font-weight:600;line-height:22px;color:#fff}")
        self.assertPageContains(
            ".vjs-peach-speed-slider{display:flex;align-items:center;gap:16px;margin-bottom:24px}")
        self.assertPageContains(".vjs-peach-speed-chips{display:flex;align-items:flex-start;gap:8px}")
        self.assertPageContains(
            ".vjs-peach-speed-preset{display:flex;flex:0 1 53px;min-width:0;"
            "flex-direction:column;align-items:center}")
        self.assertPageContains(
            ".vjs-peach-speed-preset-label{margin-top:4px;font-size:var(--fs-xs);font-weight:400;"
            "line-height:14px;color:rgba(255,255,255,.7)}")
        self.assertPageContains(
            "height:32px;min-height:32px;padding:0;border:0;border-radius:var(--pill-radius);"
            "background:rgba(255,255,255,.1);")
        # 加减键画图标不写字形：`−`／`+` 的墨迹绕数学轴排布，行盒居中后实测偏下 3.0px、
        # 偏左 1.8px，而减号墨迹只有 2px 高，这点位移在 32px 圆里一眼看得见。
        self.assertPageContains(
            ".vjs-peach-speed-slider .vjs-peach-speed-button{flex:none;width:32px}")
        self.assertPageContains(
            ".vjs-peach-speed-slider .vjs-peach-speed-button>svg{width:24px;height:24px;display:block;")
        self.assertPageContains(
            'data-player-speed-step="-1" aria-label="播放速度减 0.05">${icon(\'minus\')}</button>')
        self.assertPageContains(
            'data-player-speed-step="1" aria-label="播放速度加 0.05">${icon(\'plus\')}</button>')
        self.assertPageContains(
            ".vjs-peach-speed-chips .vjs-peach-speed-button{width:100%;gap:4px;font-size:var(--fs-xs)}")
        # 设置面板里的按钮统一是 100% 宽、48px 高、`:before` 铺满的高亮层，胶囊得单独退出这套。
        self.assertPageContains(".vjs-peach-settings-menu .vjs-peach-speed-button:before{content:none}")
        self.assertPageContains(
            "background:linear-gradient(to right,#fff 0,#fff var(--peach-speed-percent),"
            "#909090 var(--peach-speed-percent),#909090 100%)}")
        self.assertPageContains(
            ".vjs-peach-speed-range::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;"
            "width:16px;height:16px;")
        # 头 57px 加内容 192px 是 249px，比窄屏给的 246px 高，所以内距和两处间隔都收到 16px。
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-speed-panel{padding:16px}")
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-speed-slider{margin-bottom:16px}")

    def test_play_and_mute_icons_morph_in_place_like_youtube(self):
        """播放键与静音键的图标在原地形变。

        证据是 player 9470c977 的 base.js：`eST` 把路径的 `d` 拆成数字与分隔符再逐位插值
        200ms；`jjc` 让音量的两道弧各自缩放 250ms，内弧绕 (18,12)、外弧绕 (22,12)，走到
        q===1 时整块换成静音那张图标；`setVolume` 里外弧要音量过半才给 1；两处曲线都是
        `qn3`，也就是 cubic-bezier(.4,0,.2,1)。播放键那对是 `M2e` 里 case 1 的 `dD` 与 case 2
        的 `JBx`，暂停是两根竖杠，233 个记号里 116 个是数字、命令序列逐位相同，所以直接
        搬过来；`ABg`（case 4）是同结构的停止键圆角方块，不是暂停。
        """
        self.assertPageContains('<symbol id="i-player-play" viewBox="0 0 36 36"')
        self.assertPageContains('<symbol id="i-player-pause" viewBox="0 0 36 36"')
        self.assertPageContains('d="M 17 8.6 L 10.89 4.99 C 9.39 4.11 7.5 5.19 7.5 6.93')
        self.assertPageContains('d="M 12.75 4.5 L 9.75 4.5 C 9.15 4.5 8.58 4.73 8.15 5.15')
        self.assertPageContains('C 22.08 31.26 22.65 31.5 23.25 31.5 L 26.25 31.5')
        self.assertPageLacks('d="M 18 6 L 9 6 C 8.20 6 7.44 6.31 6.87 6.87')
        # `<use>` 克隆出来的影子树改不了 `d`，所以这两个键把 sprite 里的 <path> 搬进自己的 svg。
        self.assertPageContains("svg.setAttribute('class','vjs-peach-control-icon vjs-peach-morph-icon');")
        self.assertPageContains("svg.innerHTML=symbol.innerHTML;button.append(svg);return svg;")
        self.assertPageContains("if(playPath){if(cssPathD)playPath.style.d=`path(\"${d}\")`;else playPath.setAttribute('d',d)}")
        # WebKit 不认 CSS 的 `d`，只写 style 的话 iOS 上图标永远停在播放那一枚。
        self.assertPageContains("const cssPathD=CSS.supports('d','path(\"M0 0\")');")
        self.assertPageContains(".vjs-peach-morph-icon path{transition:d .2s cubic-bezier(.4,0,.2,1)}")
        self.assertPageContains(
            ".vwrap .video-js .vjs-control-bar>.vjs-play-control>.vjs-peach-control-icon{width:26px;height:26px}")
        self.assertPageContains('<path class="vjs-peach-volume-arc-inner"')
        self.assertPageContains('<path class="vjs-peach-volume-arc-outer"')
        self.assertPageContains('<path class="vjs-peach-volume-x"')
        self.assertPageContains(
            "if(muteIcon)spritePaths('player-volume-muted').forEach(path=>muteIcon.append(path.cloneNode(true)));")
        # 静音那张是挖空的喇叭：外框与实心那条同一串数字，后面接上游的挖空子路径。
        self.assertPageContains('<path class="vjs-peach-volume-speaker" d="M11.60 2.08L11.48 2.14L3.91 6.68')
        self.assertPageContains('<path class="vjs-peach-volume-speaker-muted" d="M11.60 2.08L11.48 2.14L3.91 6.68')
        self.assertPageContains('C11.92 1.98 11.75 2.01 11.60 2.08ZM4.94 8.4V8.40L11 4.76V19.23L4.94 15.6')
        self.assertPageContains('<path class="vjs-peach-volume-x" d="M21.29 8.29L19 10.58L16.70 8.29')
        self.assertPageContains(
            "muteIcon.dataset.silent=String(silent);muteIcon.dataset.loud=String(!silent&&player.volume()>.5)")
        # 缩放中心写在变换里，所以 transform-origin 必须归零，px 也要等于视框单位。
        self.assertPageContains("transform-box:view-box;transform-origin:0 0;")
        self.assertPageContains("transition:transform .25s cubic-bezier(.4,0,.2,1)}")
        self.assertPageContains(
            '.vjs-peach-morph-icon[data-silent="true"] .vjs-peach-volume-arc-inner'
            '{transform:translate(18px,12px) scale(0) translate(-18px,-12px)}')
        self.assertPageContains(
            '.vjs-peach-morph-icon[data-loud="false"] .vjs-peach-volume-arc-outer'
            '{transform:translate(22px,12px) scale(0) translate(-22px,-12px)}')
        self.assertPageContains(".vjs-peach-morph-icon .vjs-peach-volume-speaker{opacity:1;transition:opacity 0s linear}")
        self.assertPageContains(
            '.vjs-peach-morph-icon .vjs-peach-volume-speaker-muted,\n'
            '.vjs-peach-morph-icon .vjs-peach-volume-x{opacity:0;transition:opacity 0s linear}')
        self.assertPageContains(
            '.vjs-peach-morph-icon[data-silent="true"] .vjs-peach-volume-speaker'
            '{opacity:0;transition:opacity 0s linear .25s}')
        self.assertPageContains(
            '.vjs-peach-morph-icon[data-silent="true"] .vjs-peach-volume-speaker-muted,\n'
            '.vjs-peach-morph-icon[data-silent="true"] .vjs-peach-volume-x'
            '{opacity:1;transition:opacity 0s linear .25s}')
        # 图标只有 svg 这一份，CSS 不再另画一套三角与竖条。
        self.assertPageLacks("border-left:14px solid #fff;transform:translate(-38%,-50%)")
        self.assertPageLacks(".vjs-play-control .vjs-icon-placeholder:before{left:44%")

    def test_play_and_mute_clicks_flash_a_centered_bezel(self):
        """点播放键和静音键都在画面中心闪一下当前动作的图标。

        照 player 9470c977 的 `.ytp-delhi-modern .ytp-bezel`：78px 毛玻璃圆、54px 图标，
        1s cubic-bezier(.05,0,0,1) 走 0→1.33→1 的缩放淡出，窄屏收到 64px 配 48px 图标。
        """
        self.assertPageContains(
            "bezel.className='vjs-peach-bezel';bezel.setAttribute('role','status');bezel.hidden=true;")
        self.assertPageContains(
            "bezel.innerHTML=`<span class=\"vjs-peach-bezel-icon\">${icon('player-play')}</span>`;")
        # 重复点同一个键要重新播一次动画：撤类之后读一次布局强制回流，再挂回去。
        self.assertPageContains("void bezel.offsetWidth;bezel.classList.add('vjs-peach-bezel-run');")
        self.assertPageContains("player.el().insertBefore(bezel,controlBar);")
        self.assertPageContains("flashBezel(paused?'player-play':'player-pause',paused?'播放':'暂停');")
        self.assertPageContains(
            "flashBezel(silent?'player-volume':'player-volume-muted',silent?'取消静音':'静音');")
        # 捕获阶段挂在控制条上，一定早于按钮自己的 Video.js 监听，读到的是切换之前的状态，
        # 闪出来的正好是这一次做的事；冒泡阶段读到的已经是切换之后，图标会反。
        self.assertPageContains("    }\n  },true);")
        self.assertPageContains(
            ".vjs-peach-bezel{position:absolute;z-index:19;left:50%;top:50%;width:78px;height:78px;"
            "margin:-39px 0 0 -39px;")
        # 基础规则是 display:grid，不写这一条 hidden 属性压不住它。
        self.assertPageContains(".vjs-peach-bezel[hidden]{display:none}")
        self.assertPageContains(".vjs-peach-bezel-icon{display:grid;place-items:center;width:54px;height:54px}")
        self.assertPageContains(
            ".vjs-peach-bezel-run{animation:peach-bezel-fadeout 1s cubic-bezier(.05,0,0,1) 1 normal forwards}")
        self.assertPageContains(
            "@keyframes peach-bezel-fadeout{0%{opacity:0}25%,75%{opacity:1;transform:scale(1.33)}"
            "to{opacity:0;transform:scale(1)}}")
        self.assertPageContains(
            ".video-js.vjs-peach-xsmall .vjs-peach-bezel{width:64px;height:64px;margin:-32px 0 0 -32px}")
        self.assertPageContains(".video-js.vjs-peach-xsmall .vjs-peach-bezel-icon{width:48px;height:48px}")

    def test_opening_one_player_overlay_closes_the_other(self):
        """设置面板和播放统计都盖在画面上，同时开就互相遮挡，开哪个另一个自己收起。

        两块面板挂在不同作用域里，共享一个 document 事件名比互相持有引用干净。
        """
        self.assertPageContains("const PLAYER_PANEL_EVENT='peach-player-panel';")
        self.assertPageContains(
            "if(open)document.dispatchEvent(new CustomEvent(PLAYER_PANEL_EVENT,{detail:'settings'}))};")
        self.assertPageContains(
            "const closeSettingsForOtherPanel=event=>{if(event.detail!=='settings')close()};")
        self.assertPageContains(
            "document.dispatchEvent(new CustomEvent(PLAYER_PANEL_EVENT,{detail:'stats'}));")
        self.assertPageContains(
            "const closeStatsForOtherPanel=event=>{if(event.detail!=='stats')closeStats()};")
        # 两个监听都挂在 document 上，播放器销毁时必须摘掉，否则换条目后旧闭包继续收事件。
        self.assertPageContains(
            "document.removeEventListener(PLAYER_PANEL_EVENT,closeSettingsForOtherPanel);")
        self.assertPageContains(
            "detailPlayer.on('dispose',()=>document.removeEventListener(PLAYER_PANEL_EVENT,closeStatsForOtherPanel));")

    def test_control_tooltip_is_dark_enough_to_read_as_a_label(self):
        """按钮提示的底色和播放器其它悬浮件同一档黑。

        rgba(0,0,0,.3) 配 blur(16px) 落在亮画面上只剩一块低对比灰板，悬停时看着像
        凭空多出来一块阴影而不是一条说明。
        """
        for selector in (".vjs-peach-tooltip{", ".vjs-volume-tooltip{"):
            # 声明外观的那条规则在前，后面同名选择器只切 display，取第一处。
            start = self.css.index(selector)
            rule = self.css[start:self.css.index("}", start)]
            self.assertIn("background:rgba(0,0,0,.6)", rule, f"{selector} 和同屏的悬浮件不是一档黑")

    def test_filter_random_action_and_glass_polish(self):
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("const ordered=SORTS.filter(([key])=>key!=='seed');")
        self.assertPageContains("return javActive()?[JAV_RELEASE_SORT,...ordered]:ordered;")
        self.assertPageContains("state.sort='seed';state.dir='';state.seed=rollSeed();")
        self.assertPageContains("['defaultSortSetting','默认排序',[['seed','随机']")
        self.assertIn('@media(max-width:760px){.settingscard.settingscard .settingsscroll{padding-top:16px}}', board)
        # 浅色那档的两团自带反光是霁蓝配石灰，比深色那档浓一档、也大一圈：底下是一片
        # 近白的页面，照搬深色那组的 10% 白等于什么也看不见。色相由 `--glass-tint-a/b`
        # 给（默认就指回这两枚），浓淡和尺寸留在这一档自己身上。
        self.assertIn(':root[data-theme="light"]{--glass-native-a:#6686b8;'
                      '--glass-native-b:#8f98a4;--glass-drift-a:', board)
        self.assertIn('radial-gradient(32% 32% at 50% 50%,'
                      'color-mix(in srgb,var(--glass-tint-a) 30%,transparent),'
                      'color-mix(in srgb,var(--glass-tint-a) 16%,transparent) 42%,transparent 72%)', board)
        self.assertIn('radial-gradient(38% 38% at 50% 50%,'
                      'color-mix(in srgb,var(--glass-tint-b) 25%,transparent),'
                      'color-mix(in srgb,var(--glass-tint-b) 14%,transparent) 44%,transparent 74%)', board)
        # 这个双写的选择器在表里出现两次：靠前那处是主题切换那条材质过渡，玻璃本体在
        # 后面，而后面那条现在和配色弹层共用——两张从侧栏开出来的卡是同一种材质。
        menu = board.rsplit('.board-library-menu.board-library-menu,'
                            '.board-glow-menu.board-glow-menu{', 1)[1].split('}', 1)[0]
        self.assertIn('var(--glass-fill)', menu)
        self.assertIn('backdrop-filter:blur(22px) saturate(160%) var(--glass-lume)', menu)
        self.assertIn('var(--glass-shadow)', menu)

    def test_the_library_menu_marks_the_current_one_with_the_same_glass(self):
        """媒体库菜单标「当前是哪一个」也走那块会滑的玻璃，不自己再涂一层底。

        这张菜单本身就是玻璃，选中项再铺一层半透白等于白上加白：亮色下那块底和菜单
        底几乎同一个亮度，一排四个库看不出落在哪一个。共用 `.viewglide` 一起带来的
        是提亮、落影和那段位移——换库时玻璃从上一项滑过去，而不是在新的一行凭空亮起。
        选中既然由玻璃承担，按钮自己的填充和内描边就得撤掉，否则玻璃底下透出第二个
        选中态；未选中项压暗文字色，让玻璃盖住的那一行成为唯一的全黑字。
        底下那枚是这张菜单唯一的动作，用高亮实底，不套玻璃覆盖。
        """
        board = (Path(__file__).resolve().parents[1] / 'web/board.css').read_text(encoding='utf-8')
        self.assertIn('.board-library-menu .board-library-rows{position:relative}', board)
        self.assertIn('.board-library-menu .board-library-rows button:is(:hover,[aria-pressed=true])'
                      '{background:none;box-shadow:none;color:var(--glass-text)}', board)
        self.assertIn('.board-library-menu .board-library-rows>.viewglide{border-radius:10px}', board)
        self.assertNotIn('.board-library-menu footer button{background:var(--glass-pick-fill)', board)
        self.assertPageContains("libraryGlide=document.createElement('span');libraryGlide.className='viewglide';")
        self.assertPageContains("moveGlidePane(libraryGlide,animate?from:null,box,'y');")
        self.assertPageContains('<footer><button type="button" class="geist-button primary" '
                                'data-library-manage>管理媒体库</button></footer>')
        self.assertPageContains("libraryPicker.querySelector('[data-library-manage]').onclick=()=>{libraryFloating.setOpen(false);openDrawer(false);openSettings(true,'媒体')};")
        self.assertPageContains("findIndex(item=>item.title===settingsRequestedSection)")
        self.assertPageContains("settingsTabs?.select(requested>=0?requested:keep);")

    def test_mobile_search_focus_preserves_page_scroll(self):
        self.assertPageContains("$('#searchBtn').onclick=()=>{setNarrowSearchOpen(true);$('#q').focus({preventScroll:true})};")
        self.assertPageContains("$('#searchBtn').focus({preventScroll:true});")

    def test_narrow_topbar_is_fixed_and_the_page_makes_room_for_it(self):
        # 吸顶顶栏在文档流里，iPhone 聚焦搜索框时 Safari 会把整页往上滚；与 YouTube 手机版一样
        # 顶栏 fixed、正文让出同样高度。
        self.assertPageContains(".top{position:fixed;top:0;left:0;right:0}\n  body{padding-top:var(--topH)}")
        self.assertPageContains(".top:has(.search.open){overflow:visible}")
        self.assertPageLacks("syncSearchViewport")
        self.assertPageLacks("--search-viewport-top")

    def test_glass_compositing_covers_search_snapshots_and_disposed_panels(self):
        board = (Path(__file__).resolve().parents[1] / 'web/board.css').read_text(encoding='utf-8')
        self.assertIn('.top .search.search.search{--glass-optic:blur(22px)}', board)
        snapshot = board.split('html[data-theme-snapshot] :is(', 1)[1].split('}', 1)[0]
        for surface in ('.board-library-menu', '.board-filter-frame', '.search', '.drawer'):
            self.assertIn(surface, snapshot)
        self.assertIn('background-color:var(--ground)!important', snapshot)
        self.assertIn('backdrop-filter:none!important', snapshot)
        self.assertPageContains('observer.disconnect();filter.remove();attached.delete(node)')

    def test_a_theme_switch_does_not_flash_a_solid_slab_on_the_way_to_glass(self):
        """浮层从实底回到毛玻璃这一下是渐变的，不是一刀切。

        主题切换走 View Transition，而快照里采不到背景，浮层只能临时换成实底顶替；
        切换结束撤掉那个标记时，一整块底色瞬间变成透明玻璃，读出来像主题又切了第二次。
        所以过渡写在常态上，快照态那条规则自己把过渡关掉——正在拍旧状态的快照时，
        路上的中间色会被拍进去。
        """
        board = (Path(__file__).resolve().parents[1] / 'web/board.css').read_text(encoding='utf-8')
        self.assertIn('.board-filter-frame.board-filter-frame,.entitytagbar.entitytagbar,'
                      '.entitycollectionhead.entitycollectionhead,.board-library-menu.board-library-menu,'
                      '.board-glow-menu.board-glow-menu{\n'
                      '  transition:background-color .28s ease,backdrop-filter .28s ease,'
                      '-webkit-backdrop-filter .28s ease}', board)
        snapshot_rule = board.split('html[data-theme-snapshot] :is(.board-filter-frame,', 1)[1]
        self.assertIn('transition:none!important', snapshot_rule.split('}', 1)[0])

    def test_notes_and_navigation_links_keep_their_own_presentation(self):
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        note = self.css.split('.geist-note{', 1)[1].split('}', 1)[0]
        self.assertIn('align-items:center', note)
        self.assertIn('background:color-mix(in srgb,var(--feedback-color) 8%,var(--ground))', note)
        self.assertPageContains('.geist-note.geist-note>p{margin:0;color:inherit;font:inherit;align-self:center}')
        self.assertIn('body a:is(.externallink,[target=_blank]):not(:has(.entitylinkicon)):not(.cardlink):hover'
                      '{background:transparent;text-decoration:underline;box-shadow:none}', board)
        self.assertIn('.board-link-button:hover{background:transparent;text-decoration:underline;box-shadow:none}', board)

    def test_card_hover_and_view_glide_can_extend_outside_content(self):
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".card{overflow:visible;border-radius:var(--surface-radius)}", board)
        self.assertIn(".gridstack .card:not(.junkcard) .pic{border-radius:12px;overflow:hidden}", board)
        self.assertIn(".card:hover .pic::after,.card.selected .pic::after{box-sizing:border-box;border-radius:inherit}", board)
        self.assertIn(".board-filter-frame.board-filter-frame{border-radius:22px;isolation:isolate;color:var(--glass-text);overflow:visible}", board)
        self.assertPageContains("const host=pill.closest(within);if(!host)return null;")
        self.assertPageContains("x-=n.scrollLeft;y-=n.scrollTop;")
        self.assertPageContains("if(rect.right<=viewport.left||rect.left>=viewport.right)return null;")
        self.assertPageContains("if(scroller)scroller.onscroll=()=>syncViewGlide(false,null,kind);")
        self.assertPageContains("if(!box||!box.w){if(glide)glide.pane.hidden=true;return}")

    def test_player_tooltips_keep_theme_independent_youtube_style(self):
        board_css = (Path(__file__).resolve().parents[1] / "web" / "board.css").read_text(encoding="utf-8")
        self.assertNotIn(".vjs-peach-tooltip", board_css)
        self.assertNotIn(".vjs-volume-tooltip", board_css)
        self.assertIn(
            ".vjs-peach-tooltip,.vjs-volume-tooltip{--surface-radius:8px;--badge-radius:4px}",
            self.css)
        for selector in (".vjs-peach-tooltip{", ".vjs-volume-tooltip{"):
            start = self.css.index(selector)
            rule = self.css[start:self.css.index("}", start)]
            for declaration in ("color:#fff", "white-space:nowrap", "padding:5px 9px", "backdrop-filter:blur(16px)", "font-size:var(--fs-sm)"):
                self.assertIn(declaration, rule)

    def test_narrow_settings_keep_the_toggle_on_the_title_row(self):
        """窄屏那条单列是给 select 留的：148px 的下拉配上标题和说明挤不下。

        开关只有 36px，跟标题同一行绰绰有余，跟着换行只是白占一行高度。
        """
        self.assertPageContains(".settingrow{grid-template-columns:1fr;gap:9px}")
        self.assertPageContains(
            '.settingrow:has(input[type="checkbox"])'
            '{grid-template-columns:minmax(0,1fr) auto;gap:12px}')

    def test_media_error_reads_as_a_card_above_the_stats_panel(self):
        """报错文案本来就居中，压住它的是 z-index 8 的统计面板。

        所以修的不是居中，而是给报错一张自带底色、盖在统计面板上方的卡片；同时撤掉
        Video.js 铺满全画面的渐变——加载失败时正需要看统计里的编码、体积和请求方式。
        """
        self.assertPageContains(".vwrap .video-js.vjs-error .vjs-error-display{background:none}")
        self.assertPageContains("z-index:9;left:50%;top:50%;width:max-content;max-width:min(560px,calc(100% - 48px))")
        self.assertPageContains("transform:translate(-50%,-50%)}")
        self.assertPageContains("background:rgba(2,4,8,.86)")

    def test_player_stats_cover_direct_range_and_future_segmented_streams(self):
        self.assertPageContains('id="playerStatsBtn"')
        self.assertPageContains("HTTP Range")
        self.assertPageContains("bufferedAhead(video)")
        self.assertPageContains("getVideoPlaybackQuality")
        self.assertPageContains("?.vhs?.stats")
        self.assertPageContains("application/vnd.apple.mpegurl")
        self.assertPageContains("/stream/hls/")

    def test_progressive_sources_measure_the_buffer_instead_of_resource_timing(self):
        """本地文件和在线关注都是一条长连接边下边播，请求不结束就没有 resource timing 条目。

        实测本地 MP4 播到 37 秒时 performance 里仍只有挂载那两条、字节数停在 862 KB，
        面板于是长期显示「— · 0 请求」。渐进源改按缓冲推进量折算，只有 HLS 还查条目。
        """
        # 看的是缓冲前沿而不是缓冲区总长：播放时浏览器会驱逐播过的部分，总长几乎恒定，
        # 拿它当下载量只会一直读出 0——实测就是缓冲健康稳在 4.6 秒、已下载卡在 36 MB 不动。
        self.assertPageContains("function bufferedFrontier(video)")
        self.assertPageContains("const step=frontier-last.frontier")
        self.assertPageContains("if(!seeked&&step>0)advanced+=step")
        # seek 会把前沿整段挪走，那不是这一秒下载了几十分钟。
        self.assertPageContains("const seeked=Math.abs(ct-last.ct)>gap*4+1")
        self.assertPageContains("function createBufferMeter(bitrate)")
        self.assertPageContains("function averageBitrate(size,duration)")
        self.assertPageContains("let mediaSize=Number(options.size??it.size)||0;")
        self.assertPageContains("const meter=createBufferMeter(averageBitrate(mediaSize,it.duration))")
        # 关注条目的字节数比挂载晚一趟回来，码率要能后填，否则速度永远换不出来。
        self.assertPageContains("if(size>0&&!mediaSize){mediaSize=size;meter.bitrate=averageBitrate(size,it.duration)}")
        # 分片流才有可用的已完成请求；渐进源查了只会把别的会话的条目算进来。
        self.assertPageContains("const resources=segmented?streamEntries(it.id,detailStreamSession):[]")
        self.assertPageContains("playerSpeedBits(detailPlayer,it.id,detailStreamSession,segmented?null:meter)")
        self.assertPageContains("return meter?Number(meter.bits)||0:streamSpeedBits(id,session)")
        # 缓冲吃满后浏览器停拉，增量归零，读数保留上一次而不是跳回 0。
        self.assertPageContains("if(span>=.5&&gained>0&&this.bitrate>0)bits=gained*this.bitrate/span;")
        # 面板和角标都关着时没人采样，重开时的大跨度样本要丢掉。
        self.assertPageContains("if(gap*1000>BUFFER_METER_WINDOW_MS*2)samples.length=0")

    def test_progressive_stats_swap_the_request_counter_for_downloaded_bytes(self):
        """请求数对渐进源恒为 0，换成已下载量；码率未知的条目退到秒和已缓冲时长。

        「× 实时」这种口径不出现在界面上：它要用户先知道倍速是拿什么除什么才读得懂，
        而同一份数据里能直接用的读数是「现在断网还能往前放多久」。
        """
        self.assertPageContains("const loaded=segmented?bytes:(meter.bitrate>0?meter.bytes():meter.seconds)")
        self.assertPageContains("const byteScale=segmented||meter.bitrate>0")
        self.assertPageContains("请求`,")
        self.assertPageContains(":['已下载',byteScale?")
        self.assertPageContains("`${loaded.toFixed(0)} 秒`")
        self.assertPageContains("function fmtLoadRate(bits,ahead)")
        self.assertPageContains("return ahead>0?`已缓冲 ${Math.round(ahead)} 秒`:fmtSpeed(0);")
        self.assertPageContains("const speedText=speed?`${(speed/1e6).toFixed(1)} Mbps`:'—';")
        self.assertPageLacks("× 实时")

    def test_follow_detail_image_falls_back_to_the_card_thumbnail(self):
        """原图经代理取不到时换上缩略图，不留一块空画布。

        pawchive 的原文件主机挂着 ddos-guard，服务端去取一律 403；缩略图由浏览器直接读
        公开主机，照常能看。换上之后侧栏说明这是缩略图；缩略图也取不到才报没取回来。
        """
        self.assertCode("const detailThumb=selectedMedia?.thumb_url||item.thumb_url||'';")
        self.assertCode('${detailThumb&&detailThumb!==src?` data-fallback-src="${esc(detailThumb)}"`:\'\'} referrerpolicy="no-referrer">')
        # 画框比例跟整组图走：换图、原图没加载完、退回缩略图时详情都不忽高忽低。
        self.assertCode("const framedOwners=(imageCarousel?[...imageMedia,item]:[selectedMedia,item]).filter(owner=>owner?.width>0&&owner.height>0);")
        self.assertCode("${frameRatio?' framed':''}\"${frameRatio?` style=\"--follow-frame-ratio:${frameRatio.toFixed(4)}\"`:''}>")
        online = (Path(__file__).resolve().parents[1] / 'web/css/21-online.css').read_text(encoding='utf-8')
        self.assertIn(".followdetailmedia.framed .followdetailposter{width:100%;aspect-ratio:var(--follow-frame-ratio)}", online)
        self.assertCode("if(fallback&&el.getAttribute('src')!==fallback){")
        self.assertCode("el.src=fallback;if(thumbFallback)thumbFallback.hidden=false;return}")
        self.assertPageContains("data-media-thumb-fallback hidden>原图没取回来，这里先显示缩略图")
        # 灯箱里翻到的每一张同样退回它自己的缩略图。
        self.assertCode("box.querySelectorAll('.photomain img').forEach((img,at)=>img.addEventListener('error',()=>{")
        self.assertCode("if(thumb&&img.getAttribute('src')!==thumb)img.src=thumb},{once:true}));")

    def test_follow_detail_gets_the_same_player_stats_overlay(self):
        """作品详情与关注详情共用同一段统计模板，关注详情里的在线视频同样有统计入口。"""
        self.assertPageContains("function playerStatsOverlayHtml()")
        self.assertPageContains("${selectedKind==='video'?playerStatsOverlayHtml():''}")
        self.assertPageContains("size:selectedMedia?.size,")
        self.assertEqual(self.page.count('playerstatsbtn" id="playerStatsBtn"'), 1,
                         "统计三件套只能有一份模板，两个详情页共用")
        # 关注条目没有落盘文件名，容器格式从片源 MIME 反推，会话号也不该显示成空的。
        self.assertPageContains("const container=(named.includes('.')?named.split('.').pop()")
        self.assertPageContains("detailStreamSession&&!options.source?")

    def test_follow_image_cards_reserve_their_ratio_from_either_tier_and_learn_the_rest(self):
        """图片墙按卡片高度分列，图落地前就要知道比例，否则每张加载完整墙重排。

        只有图片视图摆成瀑布流，视频卡片不占位也不回写。比例是卡面那张图的，有两层：
        卡面是媒体清单里那张就落在那张上；卡面就是条目自己的缩略图时落在条目上。两层都
        没有的卡片不硬猜，加载完把 natural 尺寸回写给它的主人，下一次渲染就有了。
        """
        self.assertCode("const cardMedia=selectedMedia&&selectedMedia.thumb_url===thumbUrl?selectedMedia:null;")
        self.assertCode("const itemOwnsCard=!cardMedia||thumbUrl===item.thumb_url;")
        self.assertCode("const sized=imageView?[cardMedia,itemOwnsCard?item:null].find(owner=>owner?.width>0&&owner.height>0):null;")
        self.assertCode('const dims=sized?` width="${sized.width}" height="${sized.height}"`:\'\';')
        self.assertCode('const learn=imageView&&!sized&&thumbUrl?` data-learn-dims="${item.id}"${cardMedia?` data-learn-media="${cardMedia.index}"`:\'\'}`:\'\';')
        self.assertPageContains("function wireImageDimsLearning(root)")
        self.assertPageContains("wireImageDimsLearning(root);")
        self.assertPageContains("root.querySelectorAll('img[data-learn-dims]')")
        self.assertPageContains("if(!img.naturalWidth||!img.naturalHeight)return;")
        # 学习是顺手的事：攒一批再发，失败静默，同一张这次会话只报一次。
        self.assertPageContains("api('/api/follow/image-dims',{method:'POST',body:JSON.stringify({entries})}).catch(()=>{});")
        self.assertPageContains("if(followDimsReported.has(key))return;")
        self.assertPageContains("if(img.complete)record();else img.addEventListener('load',record,{once:true});")

    def test_player_stats_keep_a_rolling_history_instead_of_only_the_latest_value(self):
        """单个瞬时值看不出卡顿是刚发生还是一直如此，三条指标各留 24 秒采样窗口。"""
        self.assertPageContains("const PLAYER_STATS_HISTORY=24")
        self.assertPageContains("function playerStatsPlot(samples,kind,ceiling,label)")
        self.assertPageContains("pushPlayerStat(statsHistory.buffer,buffer)")
        self.assertPageContains("playerStatsPlot(statsHistory.buffer,'buffer',30")
        self.assertPageContains('class="playerstatsmetric"')
        self.assertPageContains(".playerstatsplot{height:20px")
        self.assertPageContains(
            "@media(max-width:600px){.playerstats dd.playerstatsmetric"
            "{grid-template-columns:96px minmax(0,1fr)}}")
        # 缓冲健康是唯一有阈值语义的一条：红 / 橙 / 浅绿分别对应 <5 秒、5-15 秒和健康。
        self.assertPageContains(".playerstatsplot.buffer i.low{background:#e16962}")
        self.assertPageContains(".playerstatsplot.buffer i.mid{background:#efb55f}")

    def test_fullscreen_uses_the_entire_player_and_reports_loading_speed(self):
        self.assertPageContains(".vwrap>.video-js.vjs-fullscreen")
        self.assertPageContains(".vwrap :is(.vwrap>.video-js.vjs-fullscreen")
        self.assertPageContains(".video-js[data-peach-fullscreen],body.vjs-full-window .video-js")
        self.assertPageContains(".video-js:-webkit-full-screen,.video-js:-moz-full-screen")
        self.assertPageContains(".vwrap:fullscreen>.video-js,.vwrap:-webkit-full-screen>.video-js,.vwrap:-moz-full-screen>.video-js")
        self.assertPageContains(") .vjs-tech{")
        self.assertPageContains("position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;padding:0!important")
        self.assertPageContains("position:absolute!important;inset:0!important;width:100vw!important;height:100vh!important")
        self.assertPageContains("max-height:none!important")
        self.assertPageContains("max-height:none!important;object-fit:cover!important")
        # 画面层不吃裸 `<video>` 那条 76vh：影院模式外框更高，画面要跟着撑满。
        self.assertPageContains(".vwrap .video-js .vjs-tech{object-fit:contain;max-height:none}")
        self.assertPageContains("const syncFullscreenState=()=>{")
        self.assertPageContains("player.el().toggleAttribute('data-peach-fullscreen',active)")
        self.assertPageContains("player.on(['fullscreenchange','enterFullWindow','exitFullWindow'],syncFullscreenState)")
        self.assertPageContains('id="playerNet"')
        self.assertPageContains("function streamSpeedBits(id,session='')")
        self.assertPageContains("function fmtSpeed(bits)")
        self.assertPageContains("const rate=segmented?fmtSpeed(bits):fmtLoadRate(bits,bufferedAhead(video));")
        self.assertPageContains(
            """netBadge.innerHTML=`${icon('gauge')}<span class="sr-only">加载速度</span><span>${esc(rate)}</span>`""")

    def test_immerse_mode_has_loading_state_and_full_viewport_cover(self):
        self.assertPageContains('id="tokLoader"')
        self.assertPageContains("$('#tokLoader').insertAdjacentHTML('afterbegin',spinnerHtml('媒体加载中'))")
        self.assertPageLacks('class="tokspinner"')
        self.assertPageContains("function setTokLoading(on,label='加载中…',it=null)")
        self.assertPageContains("function waitTokReady(video,timeout=15000)")
        self.assertPageContains("width:100%;height:100%;left:50%;transform:translateX(-50%);object-fit:cover")
        # cover 只是基线；片源与视口比例差得多时切到 contain 完整显示。
        # 判据本身由 test_immersive_fit_compares_source_against_the_viewport 覆盖，
        # 这里只确认沉浸模式仍然接着那条规则走。
        self.assertPageContains(".toktrack video.contain{object-fit:contain}")
        self.assertPageContains("function applyTokFit(v)")
        self.assertPageContains("v.addEventListener('loadedmetadata',fit,{once:true})")
        self.assertPageContains("<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-play\"/>")
        self.assertPageContains("await tokShow()")

    def test_tag_geometry_uses_shared_tokens(self):
        # 整圆现在只有一个来源。之前 999px / 99px / 9999px 三种写法并存，
        # 都是「整圆」的意思却看不出是不是同一个决定。
        self.assertPageContains("--pill-radius:999px")
        self.assertPageContains("--tag-radius:var(--pill-radius)")
        self.assertPageContains("border-radius:var(--tag-radius)")
        self.assertPageContains("--filterItemH:40px")
        self.assertPageContains("height:var(--filterItemH);padding:0 20px")
        self.assertPageContains("overflow-x:auto;overflow-y:hidden")

    def test_multiselect_has_explicit_mode_range_and_toggle_controls(self):
        self.assertPageContains('id="selectMode"')
        self.assertPageContains("e.shiftKey||e.ctrlKey||e.metaKey||selectMode")
        self.assertPageContains("visibleCardIds()")
        self.assertPageContains("lastSelectedId")
        self.assertPageContains('class="selectionMark"')
        self.assertPageContains("if(selectMode||e.shiftKey||e.ctrlKey||e.metaKey)")
        self.assertPageContains(".select-mode .cardopenhit,.select-mode .hovertools,.select-mode .previewcounter")
        self.assertPageContains("if(selectMode)releaseHoverPreviews()")

    def test_manage_collects_admin_entries_behind_one_top_level_icon(self):
        """统计、垃圾文件、回收站、人工复核各占一个顶层图标时，侧栏一半是管理入口。

        它们合并到「管理」下的二级导航；URL 保持原样，只是多了一条共用导航条。
        """
        self.assertPageContains("['manage','管理','wrench']")
        self.assertPageContains("const MANAGE_SECTIONS=[")
        for section in ("'stats','统计'", "'cleanup','数据管理'",
                        "'quality','高清版'", "'trash','回收站'", "'review','人工复核'",
                        "'taste','口味'"):
            self.assertPageContains(section)
        self.assertPageContains("function manageSection()")
        self.assertPageContains("function buildManageBar()")
        self.assertPageContains('id="managebar"')
        self.assertPageContains('class="managebar-toggle"')
        self.assertPageContains('aria-controls="managebar-menu"')
        self.assertPageContains("bar.classList.toggle('is-open')")
        self.assertPageContains('.managebar .managebar-toggle{display:none}')
        self.assertPageContains('.managebar.is-open .managebar-menu{display:grid}')
        self.assertPageContains("if(k==='manage'){openManage();return}")
        # 顶层图标里不再各自占位
        edge = self.page.split("const EDGE_ICONS=[", 1)[1].split("];", 1)[0]
        for gone in ("'trash'", "'ads'", "'stats'", "'review'"):
            self.assertNotIn(gone, edge, f"{gone} 应该已经收进管理，不再是顶层入口")
        self.assertIn("'manage'", edge)

    def test_manage_menu_only_offers_pages_that_are_not_inside_data_management(self):
        """人工复核、回收站、高清版都从数据管理进，管理菜单里不再各占一行。

        它们和垃圾文件、重复文件、空文件夹是同一件事的不同步骤。身份注册表仍然
        保留全部页面：URL 要能直达，用户也仍可把其中任何一个钉到顶层侧栏。

        活动页是菜单里的例外：它横跨扫描、追更、批量这几页，从其中任何一页进都会
        像是那一页的下一步，所以它只能和统计、口味一样自己占一行。
        """
        sections = self.page.split("const MANAGE_SECTIONS=[", 1)[1].split("];", 1)[0]
        order = [line.split("'")[1] for line in sections.splitlines() if line.strip().startswith("['")]
        self.assertEqual(
            order, ["stats", "taste", "review", "cleanup", "trash", "follow", "quality",
                    "activity", "configuration"],
            "身份注册表保留全部管理页，删掉哪一个就等于让它的标题和直达 URL 一起失效",
        )
        self.assertPageContains(
            "const MANAGE_MENU_SECTIONS=['stats','taste','cleanup','follow','activity'];")
        self.assertPageContains("manageMenuSections().map(([k,label,ic])=>")

    def test_this_computers_configuration_lives_in_the_settings_modal(self):
        """配置页讲的是这台电脑怎么跑 Peach，和「我的界面偏好」同一类，进设置弹层。

        管理菜单因此不再列它，判断也就不必再摊到菜单上。`/configuration` 这条 URL 留着：
        媒体库选单和首次配置引导都指向它，身份注册表也保留这一项。
        别的设备打开设置照样看得见这一格，里面换成一句话说清在哪儿改——服务端回过话之后
        它一定在列里，只是内容不同。判据是 `/healthz` 的 `configurable`。
        """
        self.assertPageContains("['configuration','配置','folder-cog'],")
        self.assertPageContains(
            "const manageMenuSections=()=>MANAGE_SECTIONS.filter(([key])=>MANAGE_MENU_SECTIONS.includes(key));")
        self.assertPageContains('<section class="settinggroup" id="machineGroup" hidden><h3>这台电脑</h3>')
        self.assertPageContains('<div id="machineSettings" class="machinesettings"></div>')
        # 每次打开都重新问一遍：这一格的答案随「从哪台设备打开」变，缓存下来就会骗人。
        self.assertPageContains("syncSettingsPanel();void syncMachineSettings();")
        self.assertPageContains("const runtime=await api('/healthz').catch(()=>null);")
        self.assertPageContains("if(runtime)runtimeConfigurable=!!runtime.configurable;")
        self.assertPageContains(
            "await mountIsland('configuration',host,{receipt:message=>actionReceipt(message)},{isCurrent:open});")
        self.assertPageContains("{label:'该配置需在服务端设备修改'}")
        # 弹层里那一份配置页已经由外面那圈分区页签管着，别再给它自己叠一排。
        self.assertPageContains("const config=document.querySelector('#stats .configpage');")
        # `runtimeConfigurable` 还有第二个用处：馆藏空态按它决定给不给「去配置媒体文件夹」。
        self.assertPageContains("let runtimeConfigurable=null;")
        self.assertPageContains("  bar.hidden=!current;\n  probeConfigurable();")
        self.assertPageContains(
            "api('/healthz').then(runtime=>{runtimeConfigurable=!!runtime.configurable}).catch(()=>{});")
        # 它不进可钉到侧栏的候选：侧栏顺序跨机同步，钉在手机上就是死链接。
        self.assertPageContains(
            "const OPTIONAL_EDGE_ICONS=MANAGE_SECTIONS.filter(([key])=>key!=='configuration')")
        self.assertPageLacks('href="/configuration"')
        self.assertPageLacks("媒体文件夹与服务配置")

    def test_this_computer_joins_the_rail_once_and_never_as_a_placeholder(self):
        """「这台电脑」在服务端回话之前不占位，回话之后一次性列出它最终的样子。

        它是「四个分区」还是「一句话」由服务端决定。先摆一条占位再改写的话，左栏那一列
        会先长出一条「这台电脑」、随后变成四条，弹层跟着跳一次高度——用户看到的是一次
        无缘无故的重排，而那一刻并没有任何新东西可读。

        两处配合：这一格开局就是 `hidden`，左栏只收不带 `hidden` 的那几格。少一边都不行——
        只藏内容而左栏照收，那一条就成了点不开的空壳。
        """
        self.assertPageContains('<section class="settinggroup" id="machineGroup" hidden>')
        self.assertPageContains(
            "const host=$('#machineSettings'),group=$('#machineGroup');")
        self.assertPageContains(
            "const list=()=>{if(group)group.hidden=false;refreshSettingsTabs?.()};")
        self.assertPageContains(
            "const groups=[...settings.querySelectorAll(':scope > .settinggroup:not([hidden])')];")
        # 两条分支各自列出来：读不到服务端时那一句话也得有人能看见。
        self.assertPageContains("{label:'该配置需在服务端设备修改'}")
        self.assertPageContains("    list();\n    return;\n  }")
        # 挂到一半被关掉的那次不算数，否则留下的是一条点开什么都没有的「这台电脑」。
        self.assertPageContains("if(!open()){machineSettingsMounted=false;return}")
        # 等待期间不铺占位文案：整格不在列里，没有地方放它。
        self.assertPageLacks("正在读取这台电脑的配置")

    def test_the_settings_rail_is_split_into_captioned_sections(self):
        """左栏按分区分块：一个小标题带一组条目，「设置」在上、「这台电脑」在下。

        形状照 BoardUI 的设置弹层。它的组件页只写怎么装，间距、字号与颜色未取得，
        小标题用本站自己那一档：13px、`--muted`。
        整块仍是一个 tablist：拆成两个之后方向键只在自己那一段里走，从「安全」按下去
        到不了「通用」，而这两段在用户眼里就是一列，所以小标题写成 presentation。
        配置页挂不上来时那一条排回上面一列的末尾——小标题和它下面唯一那一条同名，
        等于把一句话说两遍。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("const items=sections.flatMap(section=>section.items);")
        self.assertPageContains(
            "caption.className='board-local-nav-caption';caption.setAttribute('role','presentation');")
        self.assertPageContains("if(parts?.length)sections.push({caption:machine.querySelector('h3')"
                                ".textContent.trim(),items:parts});")
        self.assertPageContains("const sections=[{caption:'设置',items:groups.filter(node=>node!==machine)"
                                ".map(item)}];")
        # 方向键在整列上循环，不在某一段里打转。
        self.assertPageContains("next=(i+1)%items.length;")
        self.assertPageContains("next=(i+items.length-1)%items.length;")
        self.assertIn(".settingscard.settingscard>.board-local-nav .board-local-nav-caption"
                      "{margin:12px 0 0;font-size:13px;color:var(--muted);padding:4px 8px 8px}", board)
        self.assertIn(".settingscard.settingscard>.board-local-nav .board-local-nav-caption"
                      ":first-child{margin-top:0}", board)
        # 那句写死在样式里的「设置」退役：分块之后它只是其中一块的名字，得由 DOM 给。
        self.assertNotIn("content:'设置'", board)
        # 同一个节点会挂在好几条下面，一条一条 toggle 会把前面点亮的又抹掉。
        self.assertPageContains(
            "items.forEach(item=>item.nodes.forEach(node=>node.classList.remove('board-group-active')));")
        self.assertPageContains("items[index].nodes.forEach(node=>node.classList.add('board-group-active'));")

    def test_one_hairline_separates_the_settings_rows_from_the_block_under_them(self):
        """「左侧导航」那一块和它上面那行之间只有一条线，而且和上面几条一样长。

        两侧各画各的时，一条 1px 的下边线和一条 1px 的上边线落在同一个 y 上，看着就是
        一道 2px 的粗线；而这一块不让出滑块那 16px 的话，它的线还会比上面几行长一截，
        一直贴到卡片边上。线归行的下沿，右边这一格跟着行走。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".settingscard .settingsscroll .settingrow+.sidebarsetting{border-top:0}", board)
        self.assertIn(".settingscard .settingsscroll .sidebarsetting"
                      "{padding:16px 12px 12px 0!important;margin:0 16px 0 0!important}", board)
        self.assertIn(".settingscard .settingsscroll .settingrow{min-height:52px;"
                      "padding:10px 10px 10px 0;gap:16px;border-top:0;"
                      "border-bottom:1px solid var(--line-soft)}", board)

    def test_a_locked_page_does_not_keep_drawing_its_own_scrollbar(self):
        """弹层盖住页面时只剩弹层自己那条滚动条。

        页面这时是 `overflow:hidden`，整页那条轨道拖不动、也读不出任何进度，留着就是
        弹层旁边多一条竖线。判据跟着锁走：加 `overflow:hidden` 的就是这两个类。
        """
        base = (Path(__file__).resolve().parents[1] / "web/css/01-base.css").read_text(encoding="utf-8")
        self.assertIn("body.settings-open>.ovtrack.page,body.photolight-open>.ovtrack.page"
                      "{display:none}", base)
        settings = (Path(__file__).resolve().parents[1]
                    / "web/css/16-settings.css").read_text(encoding="utf-8")
        self.assertIn("body.settings-open{overflow:hidden}", settings)
        photos = (Path(__file__).resolve().parents[1]
                  / "web/css/08-photos.css").read_text(encoding="utf-8")
        self.assertIn("body.photolight-open{overflow:hidden}", photos)

    def test_the_this_computer_group_is_a_page_not_a_row_list(self):
        """「这台电脑」那一格装的是整张配置页，外壳自己不是面板。

        面板是里面那几段配置；里面没有一段亮着就说明用户在看上半列的某一项，这时整个
        外壳都不该占位置。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".settingscard .settingsscroll>.settinggroup:has(>.machinesettings)"
                      ":not(:has(.board-group-active)){display:none}", board)

    def test_each_settings_tab_takes_its_glyph_from_its_own_name(self):
        """字形按条目自己的名字取，不按它排第几。

        这一列的条数会变——「这台电脑」挂上配置页之后一条变四条——按下标取字形只会
        整排错位。两套字形也混在一排：`ri-` 实心靠 `fill` 画，`i-` 是线条靠 `stroke` 画，
        给线条件套上 `fill:currentColor` 会填成一坨黑块。
        下面四枚各说各的名词：`monitor` 是这台设备（和「跟随系统」同一个意思），
        `folder` 是媒体文件夹，`globe` 是网址那一类，`download` 是把更新下下来。
        """
        self.assertPageContains(
            "const SETTINGS_TAB_ICONS={'界面':'ri-palette-line','浏览':'ri-layout-grid-line',"
            "'播放':'ri-play-circle-line',\n"
            "  '搜索':'ri-search-line','关注':'ri-rss-line','安全':'ri-shield-check-line',"
            "'这台电脑':'i-hard-drive',\n"
            "  '通用':'i-monitor','媒体':'i-folder','网络与访问':'i-globe','更新与维护':'i-download'};")
        self.assertPageContains(
            "const solid=item.icon.startsWith('ri-');")
        self.assertPageContains(
            "svg.style.fill=solid?'currentColor':'none';svg.style.stroke=solid?'none':'currentColor';")
        for symbol in ("i-hard-drive", "i-monitor", "i-folder", "i-globe", "i-download"):
            self.assertPageContains(f'<symbol id="{symbol}" viewBox="0 0 24 24">')

    def test_the_follow_management_section_is_named_after_the_page_it_opens(self):
        """管理区那一项叫「关注管理」：它开的是 /follow-manage，不是关注更新流。

        叫「关注」时，管理菜单点进去是加来源、看凭据、移除来源那一屏，页标题也
        写着「关注」——两个不同的页面在界面上共用一个名字。侧栏可选图标本来就
        已经叫「关注管理」，身份注册表跟它对齐后不再各写一份文案。
        """
        sections = self.page.split("const MANAGE_SECTIONS=[", 1)[1].split("];", 1)[0]
        self.assertIn("['follow','关注管理','rss'],", sections)
        self.assertNotIn(
            "['follow','关注','rss'],", sections,
            "顶层 EDGE_ICONS 里的「关注」是更新流，管理区这一项不能跟它同名")
        self.assertPageContains("key==='follow'?['follow-manage',label,ic]")
        self.assertPageLacks("key==='follow'?['follow-manage','关注管理',ic]")
        # 页标题取的就是这份注册表；关注更新流的 h2 是它自己的，仍叫「关注」。
        self.assertPageContains("if(entry)el.textContent=pageLabel||entry[1]")
        self.assertPageContains('<div class="followhead"><h2 class="pagetitle">关注</h2></div>')

    def test_data_management_is_the_single_entry_for_tidying_the_library(self):
        """复核、回收站、高清版和链接管理、资源同步都归到数据管理这一页。

        资源同步和链接管理此前挂在统计页上——它们改的是账本和外部现实的对齐，
        跟「库里现在有多少」不是一件事。
        """
        self.assertPageContains("const DATA_MANAGEMENT_ENTRIES=[")
        for entry in ("['review','人工复核'", "['trash','回收站'", "['quality','高清版'"):
            self.assertPageContains(entry)
        self.assertPageContains("button.onclick=()=>openManage(button.dataset.cleanupGo)")
        self.assertPageContains("async function paintDataManagementCounts()")
        self.assertPageContains("api('/api/review?counts=1')")
        # 三个计数各自失败各自算：一个接口出错不该把另外两张卡也变成「—」。
        self.assertPageContains("catch(_error){write(section,'读取失败')}")
        cleanup = self.page.split("async function openDataCleanup(", 1)[1].split("let dupData=null;", 1)[0]
        self.assertIn("${linkManagerMarkup()}", cleanup)
        self.assertIn("${(sources.sources||[]).some(source=>['local','115','pikpak'].includes(source.location)&&source.roots?.length)?resourceSyncMarkup():''}", cleanup)
        stats = self.page.split("async function openStats(", 1)[1].split("function showHomeSurfaces(", 1)[0]
        self.assertNotIn("linkManagerMarkup()", stats,
                         "统计页只讲库里现在有多少，不该再挂对齐外部现实的面板")
        self.assertNotIn("resourceSyncMarkup()", stats)

    def test_scraping_is_reachable_from_the_library_processing_card(self):
        """来源和凭证自成一页，入口在数据管理那张「扫描与采集」卡上。

        这一页是 React 档（ADR-0031）：遗留层只铺骨架、交容器，正文在
        `frontend/src/react/scraping/` 里。所以这里断言的是外壳——路由、名字与入口。
        连接方式、Cookie 二选一、保存与撤销交什么、检查结果怎么说由
        `frontend/test/react/scraping.test.tsx` 守，页脚三键的外观与来源外链的
        `rel` 由 `frontend/e2e/design.test.ts` 读计算值守。
        """
        self.assertPageContains("'/scraping':'来源和凭证'")
        self.assertPageContains('id="libraryProcessing"')
        processing = (
            Path(__file__).resolve().parents[1]
            / 'frontend/src/react/library-processing/library-processing-card.tsx'
        ).read_text(encoding='utf-8')
        self.assertIn('href="/scraping"', processing)
        self.assertPageContains(
            "await ui.mountIsland('scraping',$('#stats'),{toast},"
            "{isCurrent:()=>surfaceCurrent(surface)})")
        # 正文归 React 子树：控件、来源外链与 Cookie 二选一用 BoardUI 的源码加 Tailwind，
        # 遗留样式表里只剩骨架要的那两条。
        self.assertPageLacks('.scraping-fields')
        self.assertPageLacks('.scraping-url')
        self.assertPageLacks('.scraping-cover-form')

    def test_data_management_subpages_carry_geist_breadcrumbs(self):
        """数据管理五张卡进的是它的子页，得有回去的路和自己的名字。

        垃圾文件、重复文件此前连 h2 都顶着「数据管理」，和 document.title
        （pageTitle 早就写了垃圾文件/重复文件）互相矛盾。breadcrumb 照
        vercel.com/geist/breadcrumbs 实测语义：nav[aria-label=Breadcrumb] > ol > li，
        当前项 aria-current="true" 渲染纯文本，上一级是 /data-cleanup 的链接；
        分隔符是每项自带的 chevron，最后一项由 CSS 隐藏。人工复核、回收站、
        高清版在侧栏保留直达入口，但层级上仍从数据管理进；空文件夹是 hub 上的
        就地操作，没有独立页面，不在此列。
        """
        self.assertPageContains(
            '<nav class="geist-breadcrumb" id="manageCrumb" aria-label="Breadcrumb" hidden></nav>')
        self.assertPageContains("export function breadcrumbHtml(items)")
        self.assertPageContains(
            'return `<li${item.current?\' aria-current="true"\':\'\'}>${inner}${icon(\'chevron-right\')}</li>`')
        self.assertPageContains(
            "el.innerHTML=breadcrumbHtml([{label:'数据管理',href:'/data-cleanup'},{label,current:true}])")
        pages = self.page.split("const MANAGE_CRUMB_PAGES={", 1)[1].split("};", 1)[0]
        for path, label in (("/junk-files", "垃圾文件"), ("/duplicates", "重复文件"),
                            ("/review", "人工复核"), ("/trash", "回收站"),
                            ("/quality-goals", "高清版")):
            self.assertIn(f"'{path}':'{label}'", pages, f"{path} 的面包屑层级名")
        # cleanup 分区的标题按路径再分一层；其余管理页仍用 MANAGE_SECTIONS 的名字。
        self.assertPageContains(
            "const pageLabel=current==='cleanup'?MANAGE_CRUMB_PAGES[decodeURIComponent(location.pathname)]:null")
        self.assertPageContains("function paintManageCrumb()")
        # CSS：当前页升到 --ink、分隔符钉在 --muted 不跟亮、最后一项隐藏、6px 间距。
        self.assertPageContains(".geist-breadcrumb ol{display:flex;align-items:center;gap:6px;margin:0;padding:0;list-style:none}")
        self.assertPageContains(".geist-breadcrumb li[aria-current]{color:var(--ink)}")
        self.assertPageContains(".geist-breadcrumb li svg{width:16px;height:16px;flex:none;stroke:var(--muted);fill:none")
        self.assertPageContains(".geist-breadcrumb li:last-child svg{display:none}")
        self.assertPageContains(
            ".cleanup-layout .geist-breadcrumb,.cleanup-layout .managetitle,.cleanup-layout .pagelede")

    def test_the_breadcrumb_link_routes_instead_of_reloading_the_page(self):
        """面包屑那个 `<a href>` 必须自己接路由。

        这个页面没有全局锚点拦截——`web/app.js` 里所有内部导航要么是按钮调
        `route()`，要么像 `#brandHome` 那样 `<a>` 自带 preventDefault。所以一个
        只写了 href 的面包屑点下去是整页重载：settings、sources、feed 全部重拉，
        SPA 的返回表面和已读位置一起丢掉。href 仍要留着，中键和右键菜单靠它。
        """
        crumb = self.page.split("function paintManageCrumb()", 1)[1].split(
            "function paintManageLede", 1)[0]
        self.assertIn("el.querySelectorAll('a[href]').forEach", crumb,
                      "面包屑链接没有接管左键")
        self.assertIn("event.preventDefault();openDataCleanup()", crumb)
        # 修饰键点击交回浏览器：那是「在新标签页打开」，不该被 SPA 吃掉。
        self.assertIn("if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||event.button)return",
                      crumb)
        self.assertIn("href=\"${esc(item.href)}\"", self.page,
                      "href 仍要渲染出来，中键和右键菜单靠它")

    def test_link_totals_get_one_cell_each_instead_of_one_crammed_line(self):
        """「社媒 373 · 官网 · 事务所 224」读不出哪个数字属于哪一类。

        类型名自己带间隔点（`官网 · 事务所`），和拼接用的间隔点撞在一起；挤成
        一行后标签与数字之间也只剩那个点。每类各占一格，类型名改用斜杠。
        """
        self.assertPageContains("official:'官网/事务所'")
        self.assertPageLacks("official:'官网 · 事务所'")
        self.assertPageContains("const stat=(label,value,note='')=>")
        self.assertPageContains(".map(([kind,count])=>stat(KINDS[kind]||kind,Number(count).toLocaleString())).join('');")
        self.assertPageContains(".linkstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))")
        self.assertPageContains('<div class="linkhosts"><span>主要站点</span>')
        # 类型名要能被没读过代码的人读懂：`catalog` 收的是 DMM、MGStage、JavLibrary
        # 这类作品检索站，`source_reference` 是这条资料的出处。
        self.assertPageContains("catalog:'作品资料站'")
        self.assertPageContains("source_reference:'资料出处'")
        self.assertPageContains("分布在 ${info.entities.toLocaleString()} 个女优、厂牌与系列")

    def test_taste_page_combines_private_exports_and_peach_behavior(self):
        """口味页是 React 档（ADR-0031）：遗留层只铺骨架、交容器与几样自己的能力。

        两套证据怎么切、换范围时留不留上一份、后台那一趟什么时候算数、导入与移除各走
        哪条路，由 `frontend/test/react/taste.test.tsx` 守；四条端点只声明一次、六种图
        都在 React 里由 `tests/test_frontend_build.py` 守。这里守的是外壳——路由、
        入口、交出去的那几样能力，以及正文标记确实已经不在遗留层。
        """
        self.assertRoute('/taste', "openTaste(push)", "section:'taste'")
        self.assertPageContains("async function openTaste(push=true)")
        self.assertPageContains("await ui.mountIsland('taste',$('#stats'),{")
        # 交出去的都是导航、查表或回执：页面不持有它们的状态，也不自己跳转。
        self.assertPageContains("onSignal:openTasteSignal")
        self.assertPageContains("navigate:path=>{route(path);restoreRoute()}")
        self.assertPageContains("toast:actionReceipt,avatarInner")
        self.assertPageContains("onboarding:new URLSearchParams(location.search).get('onboarding')==='1'")
        self.assertPageContains("{isCurrent:()=>surfaceCurrent(surface)}")
        # 四条端点、缓存、轮询与所有正文标记都归 React 子树，遗留层一条都不留。
        for gone in ("/api/taste", "TASTE_CACHE_KEY", "peach-taste-job", "wireTasteProgress",
                     "renderTaste", "tasteAnalysisSection", "data-taste-window",
                     "data-taste-evidence-panel", "data-taste-dimension", "data-taste-remove",
                     "data-taste-route"):
            self.assertPageLacks(gone)
        # 正文的样式跟着搬走：遗留样式表里只剩骨架读到的那几条层级。
        for gone in (".tasteranks", ".tasterank", ".tastesources", ".tastesource",
                     ".tasteleads", ".tastelede", ".tasteinsights", ".tasteconfidence",
                     ".insighttabs", ".taste-history-guide"):
            self.assertPageLacks(gone)

    def test_note_semantics_replace_empty_states_for_persistent_errors(self):
        for name in ("emptyStateHtml", "loadingDotsHtml", "mediaViewButtonsHtml", "noteHtml", "progressHtml",
                     "scrollerHtml", "setActionBusy", "skeletonHtml", "spinnerHtml",
                     "wireBusyActions", "wireScrollers"):
            self.assertPageContains(name)
        self.assertPageContains("from './js/ui-components.js'")
        self.assertPageContains("const NOTE_VARIANTS=new Set(['secondary','warning','error','success'])")
        self.assertPageContains("const symbol=kind==='secondary'?'info':kind==='success'?'check':'alert'")
        self.assertPageContains("const role=kind==='error'?' role=\"alert\"':' role=\"note\"'")
        self.assertPageContains("failure.innerHTML=noteHtml(error.message||'操作未完成',{variant:'error'})")
        self.assertPageContains("noteHtml(error.message,{variant:'error',label:'扫描失败'})")
        # 「没有更多内容」的抓取完摘要跟着检查完成的右下角 notification 走，页内只剩失败与取证缺档。
        self.assertPageLacks('个来源没有更多内容</b>')
        # 每一条失败都进 Note，没有第二套「红字一行」的写法：红色文字既没有图标
        # 也没有边框，在暗色底上和普通说明文字只差一个色相，扫读时整条会被跳过。
        self.assertPageContains('class="geist-note geist-note-error fwarn" role="alert"')
        # 关注管理页那两处同样是 Note，只是画在 React 档里（ADR-0031）。
        follow = Path(__file__).resolve().parents[1] / "frontend/src/react/follow-manage"
        self.assertIn('<Note tone="error" title={`${failures.length} 个来源检查失败`}',
                      (follow / "source-list.tsx").read_text(encoding="utf-8"))
        credentials = (follow / "credentials.tsx").read_text(encoding="utf-8")
        self.assertIn("const WORLD_READABLE = '文件权限过宽，请在运行 Peach 的 POSIX 主机上收紧为 0600。'",
                      credentials)
        self.assertIn('<Note tone="error" title="凭据文件权限过宽">{WORLD_READABLE}</Note>', credentials)
        self.assertPageLacks('class="fnote warn"')
        self.assertPageLacks(".fnote.warn{")
        self.assertPageLacks("geist-banner")

    def test_note_and_info_surfaces_reuse_the_photo_detail_info_icon(self):
        self.assertPageContains('<symbol id="i-info" viewBox="0 0 24 24">')
        self.assertPageContains('aria-label="图片详情" title="图片详情">${icon(\'info\')}</button>')
        # 凭据存放位置改由关注管理页自己的说明块直说，不再藏在一枚信息键后面。
        self.assertIn("{`凭据文件在 ${data.root}`}",
                      (Path(__file__).resolve().parents[1]
                       / "frontend/src/react/follow-manage/credentials.tsx").read_text(encoding="utf-8"))
        self.assertPageContains('.geist-note>svg{width:16px;height:24px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}')

    def test_the_ledger_gate_is_a_note_and_keeps_its_own_tone(self):
        # 账本只读那一条是 Note：色调由 --feedback-color 一处给出，底色、图标和正文
        # 出自同一个色调。自画一只框的写法会让底色说「注意」、字说「普通说明」。
        self.assertPageContains("function ledgerGateNote(runtime,message,actionLabel,actionHref){")
        self.assertPageContains("variant:runtime?.ledger_sync==='conflict'?'warning':'secondary'")
        self.assertPageContains("className:'runtimegate',actionLabel:actionHref?actionLabel:'',actionHref}")
        # 关注管理页那一条归 React（ADR-0031）：同一种盒子、同一档色调，去处仍是写入端。
        page = (Path(__file__).resolve().parents[1]
                / "frontend/src/react/follow-manage/follow-manage-page.tsx").read_text(encoding="utf-8")
        self.assertIn('<Note tone="warning" title="本机只能浏览"', page)
        self.assertIn('前往写入端管理关注', page)
        self.assertPageContains("readOnlyMessage:runtime?.ledger_read_only_message||'本机当前只能浏览'")
        self.assertPageContains('.geist-note.runtimegate{margin:0 0 12px}')
        # 这个类名只剩定位：框、字形和颜色再出现一份就又能和 Note 走散。
        self.assertPageLacks('.runtimegate{display:grid')
        self.assertPageLacks('.runtimegate a{')
        self.assertPageLacks('<div class="runtimegate">')
        # 四个色调各自给出前景与背景，前景既是文字色也是图标色（currentColor）。
        self.assertPageContains('.geist-note{--feedback-color:var(--muted);')
        self.assertPageContains('background:color-mix(in srgb,var(--feedback-color) 8%,var(--ground));color:var(--feedback-color)')
        self.assertPageContains('.geist-note-warning{--feedback-color:var(--meter);')
        self.assertPageContains('.geist-note-error{--feedback-color:var(--drop);')
        self.assertPageContains('.geist-note-success{--feedback-color:var(--feedback-success);')
        # 恢复动作在另一台机器上时是链接；两种形态占同一个格子。
        self.assertPageContains(
            '<a class="geist-button" href="${esc(actionHref)}" data-note-action>${esc(actionLabel)}</a>')
        self.assertPageContains(
            '<button type="button" class="geist-button primary" data-note-action>${esc(actionLabel)}</button>')
        # 横幅是第四个装这两枚字形的容器。圆点是长度 .01 的路径，缺了圆头就渲染成
        # 看不见的薄片，警告只剩上半截竖杠。选择器认直接子元素：带进度时横幅里那一枚
        # 圆环归 `.geist-gauge`，它的端点是弧的两头而不是字形笔画。
        css = stylesheet_source()
        start = css.index(".project-banner>div>svg{")
        banner_glyph = css[start:css.index("}", start)]
        self.assertIn("stroke-linecap:round", banner_glyph)
        self.assertIn("stroke-linejoin:round", banner_glyph)
        self.assertPageContains(
            "icon(kind==='error'||kind==='warning'?'alert':'info')")

    def test_the_project_banner_keeps_its_action_at_the_right_edge_on_a_phone(self):
        """窄屏上说明从左边起，动作在右端。

        桌面上整条居中，说明和动作是挨着的一组；窄屏一居中，两头就都不齐了，所以说明
        改成左对齐。动作跟着靠回右端，用 `auto` 而不是一个定值缩进：说明的长短随任务
        状态变，定值会让那个链接每次停在不同的地方，而它是这条横幅上唯一能点的东西。
        溢出换行之后它仍在这一横条的右端。
        """
        self.assertPageContains(
            "@media(max-width:600px){.project-banner{justify-content:flex-start}"
            ".project-banner>a{margin-left:auto}}")
        self.assertPageLacks(".project-banner>a{margin-left:24px}",
                             "定值缩进会让动作跟着说明的长短漂移")

    def test_taste_drilldown_and_legacy_duration_tags_never_leak_filter_state(self):
        self.assertPageContains("const cleanTagFilter=value=>")
        self.assertPageContains("tag:cleanTagFilter(initialParam('tag'))")
        self.assertPageContains("tag:cleanTagFilter(params.get('tag'))")
        self.assertPageContains("state={...state,creator:'',studio:'',tag:'',tag_match:'all'")
        self.assertPageContains("function enterManagementSurface()")
        self.assertPageContains("loadRequestSeq++;listLoading=false;$('#combo').innerHTML=''")

    def test_sidebar_add_row_wears_the_shared_input_and_primary_button(self):
        """这一行有三条判据：颜色只走 token、高度只引用 --control-h、主次动作分得开。

        触发器是 listbox 入口，穿 `.geist-input` 那身盒子；右边「添加」是这一屏的主动作，
        走 `.geist-button.primary`。写死的 `#181a1d` 在浅色主题下是深色控件配浅色面板，
        而图标键那条基样式一旦兼管这一行，两个控件就得靠三条规则叠回来。
        """
        self.assertPageContains("--control-h:38px;")
        self.assertPageContains(
            "/* 它是 listbox 触发器，不是按钮：穿输入框那身盒子，"
            "右边的实心档才是这一屏的主动作。 */")
        self.assertPageContains(
            ".sidebaradd .sidebaraddfield{display:grid;"
            "grid-template-columns:auto minmax(0,1fr) auto;width:100%;height:var(--control-h);"
            "box-sizing:border-box;align-items:center;justify-items:start;gap:9px;padding:0 11px;"
            "border:1px solid var(--field-ring);border-radius:var(--control-radius);"
            "background:var(--ground);color:var(--ink);text-align:left;font:inherit;"
            "cursor:pointer}")
        self.assertPageContains(
            ".sidebaradd .sidebaraddfield:hover:not(:disabled){border-color:var(--field-ring-hover)}"
            ".sidebaradd .sidebaraddfield:disabled{color:var(--muted);cursor:not-allowed}")
        self.assertPageContains(".sidebaradd .geist-button{height:var(--control-h);padding:0 14px}")
        self.assertPageContains(
            ".sidebaradd .sidebaraddmenu button{grid-template-columns:auto minmax(0,1fr);"
            "width:100%;height:var(--control-h);")
        self.assertPageContains(".sidebaraddfield svg:last-child{justify-self:end;color:var(--muted)}")
        self.assertPageContains(
            '<button type="button" class="geist-button primary" data-sidebar-add')
        # 「添加」两个字已经把动词说完，前面不挂 plus：判据见
        # docs/reference-snapshots/vercel-geist-button-icons.md。
        self.assertPageLacks("${icon('plus')}<span>添加</span>")
        # 图标键那条基样式只管排序行，不兼管添加行的触发器和主动作。
        self.assertPageLacks(".sidebaradd button{grid-template-columns:auto auto;")
        self.assertPageLacks(".sidebaradd>button{")
        self.assertPageLacks(".sidebarorderrow button,.sidebaradd button{")
        # 这一行的浮层与控件底色只走 token。
        self.assertPageLacks("background:#181a1d;box-shadow:0 16px 44px -20px #000}")
        self.assertPageContains(
            ".geist-button.primary:disabled{background:var(--sunk);color:var(--muted);box-shadow:0 0 0 1px var(--line-soft)}")

    def test_edge_and_drawer_share_one_navigation_dispatch(self):
        """窄栏和抽屉各写一份分支时，抽屉那份漏了追更和播放列表。

        漏掉的入口会落到兜底分支，把 state.state 设成一个后端不认识的值，
        表现就是抽屉里点「在线追更」没反应，点窄栏同一个图标却能进。
        """
        self.assertPageContains("function navTo(k){")
        # 有自己路径的入口一律从路由表进，两边点同一个键必然到同一屏。
        self.assertPageContains("const target=ROUTES.find(spec=>spec.nav===k&&!STATE_ROUTES[k]);")
        self.assertRoute('/follow', "nav:'follow'", "openFollow(push)")
        self.assertRoute('/playlists', "nav:'playlists'", "openPlaylists(push)")
        self.assertPageContains(
            "$('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));")
        self.assertPageContains("e.stopPropagation();navTo(b.dataset.nav)})")
        # 派发只能存在一处；再出现第二份就是下一次漂移。
        self.assertEqual(self.app_js.count("ROUTES.find(spec=>spec.nav===k"), 1,
                         "导航跳转只能查一次路由表")
        self.assertEqual(self.app_js.count("function navTo(k){"), 1)

    def test_one_route_table_owns_every_surface_dispatch(self):
        """「哪个路径进哪一屏」只有一份真相，七处副本不许回来。

        散成七份的话：restoreRoute 一条二十五分支的 if 链，navTo、navOn、openManage、
        manageSection、reloadCurrentSurface、refreshAll 各自再抄自己关心的那几条。
        加一屏要改七处，漏一处的症状还各不相同：URL 能进但侧栏不亮、点进去了但
        「换一批」把你扔回统计页、批量操作后回到首页而不是刚才那一屏。
        """
        for match in ('/', '/trash', '/playlists', '/playlists/:playlist/:item',
                      '/mix/:seed/:item', '/parts/:seed/:item', '/editions/:seed/:item',
                      '/item/:id', '/follow/item/:id', '/performers', '/creators', '/tags',
                      '/stats', '/taste', '/review', '/data-cleanup', '/duplicates',
                      '/resource-sync', '/quality-goals', '/follow', '/follow-manage',
                      '/configuration', '/activity', '/immerse'):
            self.route_entry(match)
        # 目录页四态和四种实体页由既有的映射生成：两边各写一份就会出现
        # 「路由认得、isCatalogPath 不认得」这种半死路径。
        self.assertPageContains("...Object.entries(STATE_ROUTES).map(([key,path])=>({")
        self.assertPageContains("...Object.entries(ROUTE_ENTITIES).map(([segment,kind])=>({")
        # 派发只有一处：匹配到哪条就打开哪条，没匹配上才回首页表面。
        self.assertPageContains("const hit=matchRoute(ROUTES,path);")
        self.assertPageContains("if(hit)await hit.route.open(hit.params,false);")
        self.assertPageContains("else{showHomeSurfaces();disposeStage(false)}")
        for revived in ("if(path==='/stats')", "if(path==='/taste')", "if(path==='/immerse')",
                        "if(path==='/follow-manage')", "if(parts[0]==='item'",
                        "const entityKind=ROUTE_ENTITIES[parts[0]]"):
            self.assertPageLacks(revived, "路径判定回到了 restoreRoute 的分支链")
        # 迁移期要能让 frontend/ 里的一屏自己登记，不必回来改这张表（ADR-0022）。
        self.assertPageContains("const registerRoute=spec=>{ROUTES.push(spec);return spec};")
        self.assertPageContains("window.peachRegisterRoute=registerRoute;")

    # 「动态段只吃数字、实体名吃掉剩下全部段」由真路径跑真的 matchPath 断言，不在
    # 这里比对源码文本，见
    # test_web_js.test_route_patterns_match_what_the_table_says_and_nothing_else。

    def test_immersive_mode_keeps_the_current_clip_in_the_url(self):
        """竖划切片也过 route()：刷新之后落回同一条片子，而不是重新抽一批。"""
        self.assertPageContains("route('/immerse?id='+it.id,true);")
        self.assertRoute('/immerse', "openTok(immerseStartId(),push)")
        self.assertPageContains("function immerseStartId(){")

    def test_online_assets_use_rss_and_open_the_saved_follow_surface(self):
        self.assertPageContains("online:icon('rss')")
        self.assertPageLacks("online:icon('globe')")
        self.assertPageContains('id="onlineGate"')
        # 直达「已保存」这一档。筛选现在由 URL 驱动，光设全局会被 openFollow 照
        # URL 推回未看，所以状态必须先写进 URL 再重取。
        self.assertPageContains("followFilter='saved';route(followViewPath());openFollow(false)}")

    def test_scrim_never_covers_the_drawer_it_dims(self):
        """遮罩铺满全屏。它排在抽屉之上时，抽屉里每一下点击都落在遮罩上，
        而遮罩的 onclick 是「收起抽屉」——表现就是能弹出、什么都点不到、一点就关。

        契约有两条，都不能各自拍数：

        1. 遮罩必须低于抽屉，否则抽屉里点不到任何东西。
        2. 抽屉打开时窄栏不得吃掉抽屉的点击——要么窄栏**严格**排在抽屉之下，要么它被显式停用。
           相等不算「在下面」：那时先后由 DOM 顺序决定，不是可依赖的契约。
           当前设计走后者：抽屉就是窄栏的展开态，展开时窄栏 `pointer-events:none` 让位。
        """
        import re as _re

        def layer(selector):
            # 同一个选择器可能声明多次（窄栏就是），生效的是最后一条。
            found = _re.findall(_re.escape(selector) + r"\{[^}]*?z-index:(\d+)", self.page)
            self.assertTrue(found, f"{selector} 应该显式写出 z-index")
            return int(found[-1])

        scrim, drawer, rail = layer(".scrim"), layer(".drawer"), layer(".edge")
        self.assertLess(scrim, drawer, "遮罩压在抽屉上面，抽屉就点不动了")
        # `>=` 而不是 `>`：两者相等时先后由 DOM 顺序决定，那不是任何人该依赖的契约，
        # 同样要求展开时让位。
        if rail >= drawer:
            self.assertIn("body.drawer-open .edge{opacity:0;pointer-events:none}",
                          self.page,
                          "窄栏排在抽屉之上时，展开必须让位，否则它会吃掉抽屉的点击")

    def test_detail_side_panel_never_scrolls_sideways(self):
        """`overflow-y:auto` 会把 overflow-x 从 visible 计算成 auto（CSS 规范）。

        于是侧栏内容宽出 1px 就冒一条横向滚动条。详情侧栏是一列竖排内容，
        横向永远不应该滚。
        """
        block = self.page.split(".sidecontent{", 1)[1].split("}", 1)[0]
        self.assertIn("overflow-y:auto", block)
        self.assertIn("overflow-x:hidden", block)

    def test_every_detail_side_surface_fills_its_grid_row(self):
        """详情背景与滚动内容分层，在线占位、图片和合集都不会再露出半截底色。"""
        self.assertPageContains(".side{min-width:0;min-height:0;align-self:stretch")
        self.assertPageContains(".sidecontent{box-sizing:border-box;width:100%;height:100%;max-height:76vh")
        self.assertPageContains('<div class="side"><div class="sidecontent">')
        self.assertPageContains('<div class="side followdetailside"><div class="sidecontent">')
        self.assertPageContains(".sidecontent{height:auto;max-height:none}")

    def test_state_pages_ask_for_facets_narrowed_to_that_state(self):
        """只改数据层不够：前端不把 state 传上去，顶部三层依旧是全库口径。"""
        self.assertPageContains(
            "if(context.type==='home'&&state.state)facetParams.set('state',state.state);")
        self.assertPageContains(
            "if(context.type==='home'&&state.state)params.set('state',state.state);")
        # 缓存键跟着 state 变，否则切到已标记会沿用首页那份。
        scope = self.page.split("const scope=facetParams.toString();", 1)[0]
        self.assertIn("facetParams.set('state'", scope)
        # 收窄到空时不能留下空带：实测已标记页上两排都没人，#tiers 仍占 28px。
        self.assertPageContains("$('#tiers').hidden=!(emptyLayout||perfRow||studioRow);")
        self.assertPageContains(".tiers[hidden]{display:none}")

    def test_empty_home_places_tags_after_view_filters_and_clips_identity_tracks(self):
        self.assertPageContains("$('#tiers').innerHTML=emptyLayout?emptyLayout.tiers:tier(perfRow)+tier(studioRow);")
        self.assertPageContains("$('#tagScroll').innerHTML=(emptyLayout?.tags||'')")
        self.assertPageContains(".tier.catalog-placeholder{overflow:hidden}")
        self.assertPageContains("flex:1 0 240px;min-width:240px;overflow:hidden")

    def test_the_view_pills_hold_still_while_only_the_tags_scroll(self):
        """筛选条左边钉住不动，横滚只发生在右半截；窄到手机宽度钉住的只剩最左那一档。

        四枚视图是四选一、恒有一枚生效，读的是「这一屏现在在看什么」；右边的标签才是
        可加可不加的筛选。两者装进同一个滚动容器时，往右翻几个标签就把读数推出视野，
        这条上再没有任何东西说明当前在哪一档。
        窄屏另算：四枚视图在 375 上要占掉两百多像素，钉住它们就没有一枚标签露得出来，
        那条看着满满一行，其实一枚可点的筛选都够不着。所以滚动整段上提到 `.filterscroll`，
        视图跟着标签一起走，只留最左那一档还钉着——资料页的媒体类型定的是这一页现在摆
        的是视频还是照片，滑走了余下的筛选就没有上下文，而它一共才六十来像素。
        关注那一条不在其列：它一整排都是可加可不加的筛选，没有这种分工，钉住开头几枚
        只会占掉本来就不宽的一行。
        """
        self.assertPageContains('<div class="tagbar" id="tagbar"><div class="filterscroll">'
                                '<div class="viewpills" id="viewPills"></div>'
                                '<div class="tagscroll" id="tagScroll"></div></div></div>')
        self.assertPageContains("  display:flex;gap:7px;overflow:hidden;align-items:center}")
        # 这一层定位不为自己，是给那块滑动玻璃当落脚点：窄屏时它就是横滚的那一层。
        self.assertPageContains(".filterscroll{display:flex;gap:7px;flex:1;min-width:0;"
                                "align-items:center;position:relative}")
        self.assertPageContains(".viewpills{display:flex;gap:7px;flex:none;align-items:center}")
        self.assertPageContains(".tagscroll{display:flex;gap:7px;flex:1;min-width:0;align-items:center;\n"
                                "  overflow-x:auto;overflow-y:hidden;scrollbar-width:none;"
                                "overscroll-behavior-inline:contain}")
        self.assertPageContains("@media(max-width:760px){\n"
                                "  .filterscroll{overflow-x:auto;overflow-y:hidden;scrollbar-width:none;"
                                "overscroll-behavior-inline:contain}")
        self.assertPageContains("  .filterscroll>.tagscroll{flex:0 0 auto;min-width:auto;overflow:visible}")
        # 关注页那条也是同一个分工：媒体类型和几枚状态钉在左边，来源图标与标签在右半截横滚。
        self.assertPageContains('''<div class="tagbar followfilters" aria-label="${mediaControl?'媒体与关注筛选':'关注筛选'}">'''
                                '''${mediaControl}${mediaControl?'<span class="sep" aria-hidden="true"></span>':''}'''
                                '<div class="filterscroll"><div class="viewpills followviews"')
        self.assertPageContains('<div class="tagscroll followtags">${extraFilters}</div></div></div>')
        self.assertPageLacks(".followfilters{position:relative")
        # 玻璃层只收间距，不改谁滚谁不滚：整条一起滚的话左端那一档也跟着走，而它正是
        # 这条上唯一离开就读不懂的东西。
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-filter-frame .entitytagbar .filterscroll{gap:6px}", board)
        self.assertNotIn(".board-filter-frame .entitytagbar{overflow-x:auto", board)

    def test_the_follow_states_are_four_plain_pills_without_counts(self):
        """关注页的状态只有全部、未看、已保存、已忽略，后面不挂数字。

        已看那一档不摆出来：看过就归档，要再翻出来是「全部」的事。状态本身照旧记，
        卡片和详情面板上都还能把一条标成已看，所以 `status=seen` 这类旧链接要落回
        全部，否则页面停在一个没有任何药丸按下去的筛选里。
        数字也不挂在药丸上：同一屏下排已经写着「N 项更新 · 显示 M」，一枚药丸上再写
        一个全库口径的数，两个数并排就是在问哪个才算数。
        """
        self.assertPageContains(
            "const FOLLOW_FILTERS=[['','全部'],['new','未看'],['saved','已保存'],['ignored','已忽略']];")
        self.assertPageContains(
            "filterChipHtml(label,{attr:'data-follow-filter',value:key,selected:key===followFilter})")
        self.assertPageContains(
            "followFilter=FOLLOW_FILTERS.some(([key])=>key&&key===status)?status:'';")
        # 状态本身没被删：卡片和详情面板照旧能把一条标成已看。
        self.assertPageContains('data-follow-detail-status="seen"')
        self.assertPageContains('data-follow-status="${item.id}" data-to="seen"')

    def test_the_follow_page_carries_the_home_two_rows_with_works_in_place_of_studios(self):
        """关注页顶上两排对着首页那两排：作者对女优，题材对厂牌。

        题材收来源记成 copyright 的作品与记成 character 的人物，不按词形猜——画师手柄
        在字面上跟作品名没有区别。作者、来源、题材点什么就只看什么，一维只按着一枚；
        标签那一维仍是交集。
        两页的头像和药丸共用 board.css 里同一份规则，只按 `#tiers` 写的话关注页会
        落回 flat 层那份 64px 头像加一圈描边，同一个人在两页大小都不一样。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains('<div class="tier followworks" aria-label="按题材筛选">')
        self.assertPageContains('<button class="brandpill" data-follow-work="${esc(key)}"')
        self.assertPageContains('<div class="tier followworks" data-skeleton-tier="brandpill"></div>')
        # 取样也对着首页：那两排按本次访问的种子随机取，进一次换一批。按条数取前 24
        # 的话，八十来个题材里永远只露出同样那二十几个。作者行和标签行本来就这么取。
        self.assertPageContains(
            "const workRows=followRandomOrder(facets.works||[],row=>row[0]).slice(0,ROW_FIRST);")
        self.assertPageContains("const randomizedAuthors=followRandomOrder([...authors],row=>row[0]);")
        self.assertPageContains("const pick=(set,key)=>{const again=set.has(key);set.clear();if(!again)set.add(key)};")
        self.assertPageContains("pick(followAuthors,button.dataset.followAuthor);applyFollowView()});")
        self.assertPageContains("pick(followProviders,button.dataset.followProvider);applyFollowView()});")
        self.assertPageContains("pick(followWorks,button.dataset.followWork);applyFollowView()});")
        self.assertPageContains("toggle(followTags,button.dataset.followTag);applyFollowView()});")
        self.assertPageContains("const one=key=>new Set([...csv(key)].slice(0,1));")
        self.assertPageContains("+(followWorks.size?`&work=${encodeURIComponent([...followWorks].join(','))}`:'')")
        self.assertPageContains("if(followWorks.size)params.set('work',[...followWorks].join(','));")
        self.assertPageContains("followWorks=one('work');")
        self.assertPageContains("wireDrag($('#stats').querySelector('.followworks'));")
        # 两排的形归 board.css 同一份规则，关注页那两排跟着一起写进选择器。
        self.assertIn("#tiers .av,:is(.followauthors,.followworks) .av{display:flex;"
                      "flex-direction:column;align-items:center;gap:6px;width:76px;", board)
        self.assertIn("#tiers .av .ring,:is(.followauthors,.followworks) .av .ring"
                      "{width:48px;height:48px;", board)
        self.assertIn(".followauthors .av .ring .favatar"
                      "{width:100%;height:100%;border-radius:0;object-fit:cover}", board)
        self.assertIn("#tiers .brandpill,:is(.followauthors,.followworks) .brandpill"
                      "{display:inline-flex;", board)
        self.assertIn("#tiers .brandpill .mk,:is(.followauthors,.followworks) .brandpill .mk"
                      "{width:28px;height:28px;", board)

    def test_the_work_row_asks_the_server_for_a_cover_and_never_hands_it_an_address(self):
        """题材头像的地址不经过页面。

        `/work-icon?work=` 递过去的是题材的身份，服务端自己在账本里挑最热的那几条、
        核对图床主机再存在本机。页面能递地址的话这里就是一个任意地址抓取的口子，
        浏览器也会直接向对方站点暴露正在看什么。挑不出图的题材由 facet 那一行的第四位
        说了算，直接出两个字母，不出一个注定 404 的 `<img>`——404 不可缓存，每次重绘
        都要再打一轮。第五位是服务端在那张图上检出的取景，和实体图同一个形状，所以挪
        走 `facePos`、放大走 `faceBoxAttrs` 递给 `avatarFrame` 的那条路：圆标只有
        28px，而这是一整张作品图，只挪不放大的话一排看下来仍是身体。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("function followWorkPill([key,label,,icon,focus]){")
        self.assertPageContains(
            'const mark=icon?`<img src="/work-icon?work=${encodeURIComponent(key)}"'
            ' alt="" loading="lazy"${facePos(focus)}${faceBoxAttrs(focus)}>`:fallback;')
        self.assertPageContains('<span class="mk" data-fallback="${fallback}">${mark}</span>')
        # 检不出脸的那些没有 focus，落在样式表这一档：上四分之一是人像里头最常落的位置。
        self.assertIn(".followworks .brandpill .mk img{object-position:50% 25%}", board)

    def test_selection_docks_only_show_up_once_something_is_picked(self):
        """批量条和标签选择条是同一种浮层，空着的时候整块不占位。

        条子常驻的话，一张没选时它在屏幕下沿横着一块空玻璃，读起来像是有东西待处理。
        """
        self.assertPageContains('class="batchbar selectiondock"')
        self.assertPageContains('class="tagselection selectiondock"')
        self.assertPageContains('panel.hidden=!selectMode||!selectedIndexTags.size;')
        self.assertPageContains('.selectiondock[hidden]{display:none}')
        self.assertNotIn("selection.active=selectMode", self.page)

    def test_collapsed_rail_is_divided_from_the_content_beside_it(self):
        """窄栏和内容区背景接近，没有分割线就看不出左边那一条到哪里为止。

        只管收起的状态：抽屉展开时从 `left:0` 盖住窄栏，分界由抽屉自己的右边框接管。
        """
        rail = self.page.split(".edge{position:fixed", 1)[1].split("}", 1)[0]
        self.assertIn("border-right:1px solid var(--line-soft)", rail)
        self.assertNotIn("border-right:0", rail)

    def test_every_page_title_uses_one_size(self):
        """管理区 26px、索引页 20px、播放列表 28px，从侧栏一路点过去就是三种大小。

        `/follow` 更是连标题都没有。
        """
        self.assertPageContains(
            ".pagetitle,.listtitle,.managetitle,.index .ihead h2,.playlistpage h2{")
        self.assertPageLacks(".index .ihead h2{margin:0;font-size:20px;font-weight:500}")
        self.assertPageLacks(".playlistpage h2{margin:0 0 5px;font-size:28px}")
        self.assertPageContains('<h2 class="disp pagetitle">关注</h2>')
        self.assertPageContains(".listtitle,.managetitle,.follow>.pagetitle{margin:0 0 20px}")
        self.assertPageContains('id="listTitle" hidden')
        # 索引页和关注页的标题外边距记在各自的头部容器上，三处必须是同一个值。
        self.assertPageContains(".index .ihead{display:flex;align-items:center;gap:12px;margin-bottom:20px}")
        self.assertPageContains(
            ".followhead{display:flex;align-items:center;justify-content:space-between;"
            "gap:14px;margin-bottom:20px}")

    def test_page_titles_step_down_twice_instead_of_falling_straight_to_phone_size(self):
        """标题分两级往下收：平板宽度走 24px，真手机才到 20px。

        一步从 32 掉到 20 会把页面标题压得比它下面 24px 的指标数字还小，层级整个
        翻过来——用户在 720px 的窗口里看到的就是那个 20px。24 这一档是 Geist 自己
        就有的 Heading 24，不是新开的字号；行高 1.25 也取自实测的 Heading 32。
        """
        self.assertPageContains(
            "  .pagetitle,.listtitle,.managetitle,.index .ihead h2,.playlistpage h2"
            "{font-size:var(--fs-2xl)}")
        self.assertPageContains(
            "@media (max-width:640px){\n"
            "  .pagetitle,.listtitle,.managetitle,.index .ihead h2,.playlistpage h2"
            "{font-size:var(--fs-xl)}\n}")
        # 三档都必须在既有刻度里，新增字号前先证明现有 8 档都不合适。
        self.assertPageContains("--fs-xl:20px; --fs-2xl:24px; --fs-3xl:32px;")

    def test_immersive_progress_bar_is_reachable_and_draggable(self):
        """4px 高、贴在屏幕最下沿、只能点不能拖——鼠标难瑞，手机几乎摸不到。"""
        self.assertPageContains(".tokbar{position:absolute;left:0;right:0;bottom:0;height:20px")
        self.assertPageContains("touch-action:none")
        self.assertPageContains(".tokbar:hover::before,.tokbar:hover i,")
        self.assertPageContains("function tokWireScrub(bar,prog,video,duration)")
        self.assertPageContains("bar.setPointerCapture(e.pointerId)")
        # 拖动中只画进度，松手才 seek：每帧 seek 会让远程源一直重新缓冲。
        self.assertPageContains("if(scrubbing)prog.style.width=")
        # 手机上任何位置横划都能拖进度，竖划仍然切片。
        self.assertPageContains("tokTouch.axis=Math.abs(dx)>Math.abs(dy)?'x':'y';")
        self.assertPageContains("{passive:false}")

    def test_immersive_title_opens_the_detail_page(self):
        """沉浸模式里只看得到文件名，标题要能点进详情页。

        标题不可点的话，想看标签、相关推荐或改东西得先退出再去列表里把它找回来，
        而旁边的创作者一直是可点的。
        """
        self.assertPageContains('<button type="button" class="toktitle" id="tokTitle">')
        self.assertPageContains(
            "$('#tokTitle').onclick=()=>{const id=it.id;$('#tokClose').click();openItem(id)};")
        # `.tokui` 整层 pointer-events:none，不把标题放行就是个点不到的按钮。
        self.assertPageContains("cursor:pointer;pointer-events:auto;")

    def test_surface_navigation_clears_stale_panels_and_ignores_late_responses(self):
        """跨页面请求返回较慢时，旧统计/复核响应不能覆盖当前页面。"""
        self.assertPageContains("const claimSurface=path=>{")
        self.assertPageContains("surfaceEpoch++;return surfaceToken(path)}")
        self.assertPageContains("const surfaceCurrent=token=>token.epoch===surfaceEpoch&&surfacePath()===token.path")
        self.assertPageContains("const surface=reset?claimSurface(surfacePath()):surfaceToken(surfacePath())")
        self.assertPageContains("if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return")
        self.assertPageContains("const surface=claimSurface('/review')")
        self.assertPageContains("if(!surfaceCurrent(surface))return")
        self.assertCode("async function restoreRoute(){\n  surfaceEpoch++")
        self.assertPageContains("if(requestSeq!==indexRequestSeq||location.pathname!=='/'+kind)return")
        self.assertPageContains("decodeURIComponent(location.pathname)!==decodeURIComponent(expectedPath)")
        index = self.page.split("async function openIndex", 1)[1].split("const d=await api", 1)[0]
        self.assertIn("showHomeSurfaces();", index)
        # 「换一批」在管理区的行为写在路由表的 refresh 上，不再每页一条分支。
        self.assertPageContains("if(hit?.route.refresh==='reopen'){await hit.route.open(hit.params,false);return}")
        self.assertRoute('/review', "refresh:'reopen'")

    def test_immersive_close_restores_the_home_surface(self):
        self.assertPageContains("document.body.style.overflow='';openHome()")

    def test_empty_states_keep_title_description_and_spacing_together(self):
        self.assertPageContains('export function emptyStateHtml(iconName,title,description')
        self.assertPageContains('data-geist-empty-state role="status"')
        self.assertPageContains('class="es-copy"><h3>${esc(title)}</h3><p>${esc(description)}</p>')
        self.assertPageContains('.emptystate{grid-column:1/-1;display:grid;justify-items:center;align-content:center;gap:8px')
        self.assertPageContains('.emptystate .es-copy{display:grid;justify-items:center;gap:8px}')
        self.assertPageContains('.playlistpage>header{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:16px}')
        self.assertPageContains('.followfilters .sourcepill{width:34px;padding:0}')
        self.assertPageContains("emptyState('trash','回收站是空的','删掉的内容会先到这里；确认不再需要后再清空。')")
        self.assertPageContains("$('#grid').innerHTML=catalogEmptyHtml(")
        self.assertPageContains("if(reset&&d.items.length)setGridCards(html)")
        self.assertPageLacks('class="trashempty"')

    def test_empty_follow_actions_open_the_add_workspace(self):
        """空态那条「添加关注」落在「添加关注」这一页签上，不是关注管理的首屏。

        页签在地址栏里（`?tab=add`），所以这条链接本身就是那一页的地址：外面发过来
        一样打得开。已经在这一页上时也走同一条路——壳接住这次点击，换地址、重挂岛。
        """
        self.assertPageContains('href="/follow-manage?tab=add">添加关注</a>')
        self.assertPageContains("const FOLLOW_MANAGE_TABS=['list','add','source'];")
        self.assertPageContains("if(params.tab&&params.tab!=='list')search.set('tab',params.tab)")
        self.assertPageContains("""a[href="/follow-manage?tab=add"]""")
        self.assertPageContains("void openFollowManage(true,'add')")
        self.assertPageContains('.emptystate .es-actions{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:8px}')

    def test_follow_author_actions_stay_in_the_heading_row(self):
        board = (Path(__file__).resolve().parents[1] / 'web/board.css').read_text(encoding='utf-8')
        self.assertIn('.followmanage .board-follow-list .fauthorhead{flex-wrap:nowrap}', board)
        self.assertIn('.followmanage .board-follow-list .board-author-actions{width:auto;flex:none}', board)
        self.assertNotIn('.board-author-actions{width:100%', board)

    def test_follow_fieldset_headers_share_one_control_height(self):
        self.assertPageContains('.fsechead{display:flex;align-items:center;gap:12px;flex-wrap:wrap;box-sizing:border-box;min-height:56px')

    def test_top_level_highlight_is_exclusive_and_covers_index_pages(self):
        """首页高亮只看 state.state 的话，进管理区和索引页时它仍然亮着，两个入口一起亮。"""
        # 高亮由「当前路径匹配到哪条路由」决定，索引页和实体页因此天然分开：
        # /performers 有 nav，/performers/<名字> 没有，不会两个入口一起亮。
        self.assertPageContains("const nav=matchRoute(ROUTES,path)?.route.nav||'';")
        self.assertPageContains("if(nav)return nav===k;")
        self.assertRoute('/performers', "nav:'performers'")
        self.assertRoute('/tags', "nav:'tags'")
        self.assertPageContains("if(k==='')return path==='/'&&!manageSection()&&!state.state")
        self.assertPageContains("buildEdge();     // 顶层高亮跟随管理区")

    def test_manage_surfaces_hide_the_home_rails(self):
        """回收站和垃圾文件是行政列表，不该顶着首页的人物/厂牌横条。

        `showHomeSurfaces` 会先把横条恢复出来，所以隐藏必须排在它之后，否则被立刻覆盖。
        """
        self.assertPageContains("if(current){$('#tiers').style.display='none';$('#tagbar').style.display='none'}")
        home = self.page.split("function showHomeSurfaces(){", 1)[1].split("}", 1)[0]
        self.assertLess(home.index("$('#tiers').style.display=''"), home.index("buildManageBar()"),
                        "buildManageBar 必须排在恢复首页横条之后，否则隐藏会被覆盖")

    def test_ads_queue_count_does_not_stick_and_disposal_reports_failures(self):
        """垃圾文件是处置队列；计数行不跟随滚动，写入冲突也不能伪装成成功。"""
        self.assertPageContains("countRow.classList.toggle('manage-static',staticManageCount)")
        self.assertPageContains("if(staticManageCount)countRow.classList.remove('is-stuck')")
        self.assertPageContains(".count.manage-static{position:relative;top:auto;z-index:1}")
        self.assertPageContains("if(!response.ok){")
        self.assertPageContains("throw new Error(requestErrorMessage(detail,response.status))")
        self.assertPageContains("catch(error){setActionBusy(button,false);throw error}")
        self.assertPageContains("wireJunkCards($('#grid'));paintSelection();wireCatalogLoadMore(surface);return")
        self.assertPageContains("actionFailure('操作',error)")
        self.assertPageContains("kind==='dispose'&&r.disposal==='trash'&&state.state==='ads'")

    def test_junk_empty_state_only_appears_after_the_loading_request_finishes(self):
        """待判断为空是请求终态；加载期间显示的是骨架，不能先闪空态。"""
        branch = self.app_js.split("if(state.state==='ads'){", 1)[1].split("adsBatch=null;", 1)[0]
        request = "const nextAds=await surfaceApi(surface,'/api/ads?'+junkQuery)"
        self.assertLess(branch.index(request), branch.index("emptyState('check'"))

    def test_junk_files_wait_on_a_structural_skeleton_not_loading_dots(self):
        """垃圾文件页等的是一屏同质卡片，不是后台任务的进度。

        `.claude/skills/peach-web-ui/SKILL.md` 的判据：整页或大区块首次等待内容结构用
        Skeleton，后台任务仍在推进才用 Loading Dots。垃圾文件页的正文就是一格一格的
        `.junkcard`，跟目录网格同形；这里画 Loading Dots 等于把「等下会出现几张什么形状
        的卡」换成了「还在跑」。两条进入路径——深链首屏和路由后的 `load(true)`——必须
        说同一句话，否则整页刷新会连播两段动画：先骨架，再 dots。
        """
        self.assertPageContains("renderCatalogLoading('正在读取垃圾文件');")
        self.assertPageContains("renderCatalogLoading(state.state==='ads'?'正在读取垃圾文件':'正在读取作品')")
        self.assertPageLacks("loadingDotsHtml('正在读取垃圾文件…')")
        self.assertPageLacks("junkloading")

    def test_category_switchers_are_geist_secondary_tabs_not_a_segmented_control(self):
        """复核分类和垃圾文件分类共用一套外观：带描边的 Geist Tabs secondary 几何。

        证据：`docs/reference-snapshots/vercel-geist-tabs-secondary-measured.md`，上游正文锁在
        `docs/reference-snapshots/upstream/vercel-geist-tabs.md` 与 `.../vercel-geist-switch.md`。
        分段器（Switch）只承担 2–3 项互斥视图，标签超过两三个字就要换 Tabs；复核分类 10 项、
        垃圾文件分类 7 项都在界外，所以这两条是 Tabs 不是分段器。几何取 secondary 变体：
        高 32px、左右 12px、6px 圆角、13px/400，hover 只换文字色，选中只抬底不动边框。
        两态都不描边，跟上游 secondary 一致：给每一枚都画一圈线之后，一排读起来是七个
        一模一样的框，选中那一枚只能靠填充说话，而线比填充响得多，浅色一档上「哪一枚被
        选中」根本读不出来。选中填 `--picked`，也就是 Geist 的 gray-200 那一档中间色。
        gap 留 5px：两枚填充块紧贴会连成一条，读成一个控件。
        """
        self.assertPageContains(
            ".reviewtabs,.junkfilters{display:flex;align-items:center;gap:5px;min-width:0;"
            "overflow-x:auto;scrollbar-width:none}")
        self.assertCode(
            ".reviewtabs button,.junkfilters a{box-sizing:border-box;height:32px;padding:0 12px;flex:none;"
            "display:inline-flex;align-items:center;gap:6px;border:0;"
            "border-radius:var(--control-radius);background:transparent;color:var(--muted);"
            "text-decoration:none;font:inherit;font-size:var(--fs-sm);font-weight:400;"
            "white-space:nowrap;cursor:pointer}")
        # 装不下时要能滚：这两条都靠覆盖式滑块给出可拖的抓手，系统滚动条已经关掉了。
        self.assertPageContains("'.reviewtabs','.junkfilters',")
        self.assertPageContains(
            '.junkfilters a[aria-current="page"]{background:var(--picked);color:var(--ink)}')
        # 反相底色不能回来。
        self.assertPageLacks('.junkfilters a[aria-current="page"]{border-color:var(--ink-2)')
        # 垃圾文件那条是同一批候选按 type 收窄，数据模型不变，当前项落在 URL 上，所以是
        # 导航链接而不是 tab。别为了「两条长得一样」把它也套上 tablist：屏幕阅读器会把
        # 筛选念成「标签页 3 of 7」，键盘上还会多出一层方向键漫游，Ctrl 点开新页也没了。
        self.assertPageContains('<nav class="junkfilters" aria-label="垃圾文件分类">')
        self.assertPageLacks('class="junkfilters" role="tablist"')
        self.assertPageContains('data-junk-kind-link="${esc(key)}"${current?' + repr(' aria-current="page"'))
        # 计数是徽标不是标题的一部分，为 0 时整枚去掉，两条一个口径。
        self.assertPageContains(
            'count?` <span class="n mono" data-count-badge="junk:${esc(key)}">'
            '${count.toLocaleString()}</span>`:' + repr(''))
        self.assertPageContains(
            'dismissedTotal?` <span class="n mono" data-count-badge="junk:dismissed">'
            '${dismissedTotal.toLocaleString()}</span>`:' + repr(''))
        self.assertPageLacks(" <span>${countFor(key).toLocaleString()}</span>")
        self.assertPageContains(".junkfilters .n{color:var(--muted);"
                                "font-size:var(--fs-xs);font-variant-numeric:tabular-nums}")
        # 40em 以下要抬高触摸目标；控件现在是定高，min-height 压不动它，两条 tab 一起抬。
        self.assertPageContains(".reviewtabs button,.junkfilters a{height:44px}")

    def test_junk_review_and_trash_render_every_physical_resource_type(self):
        """图片、网址快捷方式等不能复用视频播放器，但必须可预览、回收和还原。"""
        self.assertPageContains("const RESOURCE_MEDIUM_LABEL={image:'图片',audio:'音频',archive:'压缩包',other:'其它文件'}")
        self.assertPageContains("function resourceCardHtml(it)")
        self.assertPageContains("String(it.name||'').toLowerCase().endsWith('.url')?'网址快捷方式'")
        self.assertPageContains('src="/photo-thumb?id=${it.id}"')
        self.assertPageContains('data-resource-operation="${action}"')
        self.assertPageContains("await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[id],operation})})")
        self.assertPageContains("if(it&&(!it.medium||it.medium==='video'))wireHover(el,it)")
        self.assertPageContains("state.state==='trash'?d.items.map(resourceCardHtml).join('')")
        self.assertPageContains("wireCards($('#grid'),state.state==='trash'?openResourceCard:undefined)")
        self.assertPageContains("if(state.state==='trash')wireResourceCardActions($('#grid'))")
        self.assertPageContains("const emptyTrash=$('#emptyTrash');")
        self.assertPageContains("if(emptyTrash)emptyTrash.onclick=async(e)=>{")
        self.assertPageContains("function junkCardHtml(it)")
        self.assertPageContains('data-junk-operation="${decision[0]}" title="${esc(decision[1])}" aria-label="${esc(decision[1])}"')
        self.assertPageContains('data-junk-operation="dispose" title="移入回收站" aria-label="移入回收站"')
        self.assertPageContains('data-junk-reveal title="在资源管理器中显示"')
        self.assertPageContains("revealSource(id,status,{button:reveal})")
        self.assertPageContains('<span>打开位置</span>')
        self.assertPageContains("['dismiss-junk','不是垃圾','check']")
        self.assertPageContains("<span>移入回收站</span>")
        self.assertPageContains('body[data-density="dense"] .junkcard .junkactions button span{display:none}')
        # 三个按钮等宽，图标加标签在各自那一格里居中。
        junk_button = self.css.split(".junkactions button{", 1)[1].split("}", 1)[0]
        self.assertIn("justify-content:center", junk_button)
        self.assertNotIn("justify-content:flex-start", junk_button)
        self.assertPageContains("function renderJunkNavigation(data)")
        self.assertPageContains("['video','视频','play'],['image','图片','pics']")
        self.assertPageContains("['archive','压缩包','file-archive'],['audio','音频','file-audio']")
        self.assertPageContains("href=\"${junkPath(key,junkView)}\"")
        self.assertPageContains("${icon(glyph)}${esc(label)}")
        self.assertPageContains("${icon(junkView==='dismissed'?'rotate-ccw':'eye-off')}")
        junk_card = self.app_js.split("function junkCardHtml(it){", 1)[1].split("\n}", 1)[0]
        self.assertIn("selectionMark", junk_card)
        self.assertNotIn("data-later", junk_card)
        self.assertPageContains("const catalog=isCatalogPath(path)||path==='/trash'")
        self.assertPageContains("location.pathname==='/junk-files'?'junk':'catalog'")
        self.assertPageContains("wireJunkCards($('#grid'));paintSelection()")
        self.assertPageContains("data-junk-batch=\"dismiss-junk\"")
        self.assertPageContains("data-junk-batch=\"reconsider-junk\"")

    def test_resource_and_source_mutations_use_terminal_toasts_with_safe_undo(self):
        self.assertPageContains("actionReceipt(operation==='restore'?'已还原':'已移入回收站',{undo:async()=>")
        self.assertPageContains("actionReceipt(saving?'已保存到账本':(labels[to]||'已更新关注状态')")
        # 关注管理页的写操作归 React，回执仍是壳那一份 Toast（props 上的 `toast`）。
        follow = Path(__file__).resolve().parents[1] / "frontend/src/react/follow-manage"
        self.assertIn("toast(`已添加 ${result.sources.length} 个关注来源`)",
                      (follow / "add-source.tsx").read_text(encoding="utf-8"))
        self.assertIn("toast(`已${word} ${result.done.length} 个关注来源`)",
                      (follow / "source-list.tsx").read_text(encoding="utf-8"))
        self.assertPageContains("toast:actionReceipt,openFollow:()=>void openFollow()")
        self.assertPageContains("actionReceipt(`已把 ${r.removed} 项移入回收站`,{undo:ids.length?async()=>")
        self.assertPageContains("data-junk-batch=\"dispose\"")
        self.assertPageContains(".batchbar:has([data-junk-batch]:not([hidden]))")
        self.assertPageContains("#batchbar[hidden]{display:none}")
        self.assertPageContains("button[hidden]{display:none}")
        self.assertPageContains("querySelectorAll('[data-junk-batch]')")
        self.assertPageContains("toggleSelection(id,event.shiftKey)")
        self.assertPageContains(".resourcecardaction{position:absolute")

    def test_search_suggestions_come_from_real_data_in_bulk(self):
        """推荐取当前馆藏，并核对实际搜索命中。"""
        self.assertPageContains("async function loadSearchPool()")
        self.assertPageContains("await catalogSuggestions(state,api)")
        self.assertPageContains("searchPoolCache=[]")
        self.assertPageContains("Promise.all([loadSearchHistory(),loadSearchPool()])")
        self.assertPageContains("[...searchPool()]")

    def test_insight_surfaces_use_one_readable_measure(self):
        """统计和口味共享 Vercel 式阅读列；浏览型首页仍保持全宽。"""
        self.assertPageContains(".stats{padding:0 0 42px}")
        self.assertPageContains(".review{--review-card-height:440px;padding:0 0 42px}")
        self.assertPageLacks("max-width:1440px")
        self.assertPageContains(".insightpage,.tastepage{width:min(1100px,100%);margin:0 auto")
        self.assertPageContains("grid-template-columns:repeat(2,minmax(0,1fr))")
        self.assertPageContains(".managebar{margin-left:auto;margin-right:auto}")
        self.assertPageContains(".insight-layout .managetitle,.insight-layout .pagelede{width:min(1100px,100%)")
        self.assertPageLacks(".tasteprivacy{margin:16px 16px 0")
        self.assertPageLacks('<p class="tasteprivacy">')

    def test_duplicate_and_trash_descriptions_share_one_page_lede(self):
        self.assertPageContains('class="pagelede mono" id="manageLede" hidden')
        self.assertPageContains(".pagelede{margin:0 0 16px;color:var(--muted);font-size:var(--fs-sm);line-height:1.5}")
        self.assertPageContains("paintManageLede(`${d.total} 组 · ${d.files} 个文件 · 可回收 ${fmtSize(d.reclaimable)}`)")
        self.assertPageContains("if(trash)paintManageLede(`${total.toLocaleString()} 个符合 · 显示 ${n}`,")
        self.assertPageContains(".count.count-actions-only:empty{display:none}")
        self.assertPageLacks('class="dupsum mono"')

    def test_empty_trash_shares_the_lede_row_instead_of_taking_one_of_its_own(self):
        """「清空回收站」和它左边那句计数说的是同一批文件，同属说明行。

        回收站的说明搬进 `#manageLede` 之后，计数栏里就只剩这一个按钮：标题和网格之间
        因此空出一条只放一个按钮的带子。说明行支持右端动作后两者并成一行。`hidden` 的
        判据要同时看文本和动作——只看文本的话，总数为 0 时那句说明还在，判据却没变；
        真正的风险是反过来：有动作没文本时整行被藏掉，按钮跟着消失。
        """
        self.assertPageContains("function paintManageLede(text='',actionsHtml='')")
        self.assertPageContains("el.hidden=!text&&!actionsHtml;")
        self.assertPageContains("el.classList.toggle('pagelede-actions',!!actionsHtml);")
        self.assertPageContains("if(actionsHtml)el.insertAdjacentHTML('beforeend',actionsHtml);")
        lede = self.app_js.split("if(trash)paintManageLede(", 1)[1].split("$('#count')", 1)[0]
        self.assertIn('class="batchaction danger" id="emptyTrash"', lede,
                      "清空回收站要挂在说明行上，不是自己占一行")
        # 计数栏在回收站页只剩空壳，靠 :empty 收掉；按钮不能同时还留在 .sorts 里。
        sorts = self.app_js.split('const countSortsHtml=', 1)[1].split('});', 1)[0]
        self.assertNotIn('id="emptyTrash"', sorts)
        self.assertPageContains(
            ".pagelede-actions{display:flex;align-items:center;justify-content:space-between;gap:16px}")
        # 危险档只有 01-base 那一份，页面各自的 .danger 覆盖已经收掉了。
        self.assertPageContains("button.danger.danger{")
        self.assertPageLacks(".pagelede-actions .batchaction.danger{")
        self.assertPageLacks(".count .sorts .batchaction.danger{")
        # 桌面 32px 是 Geist 的控件高度，手机要回到本项目的 44px 命中区。
        self.assertPageContains(".pagelede-actions .batchaction{height:44px;padding-inline:16px}")

    def test_only_the_data_cleanup_hub_narrows_its_title_column(self):
        """812px 窄列是数据管理 hub 自己的正文宽度，不是整个数据管理区的。

        `.cleanuppage` 把 hub 那一页收进 812px，标题和面包屑跟着收才对得齐。但同一个
        section 底下的垃圾文件、重复文件正文都是全宽网格：跟着收就是宽屏上标题凭空左缩
        一截，标题左边缘和第一张卡的左边缘对不上。判据是「这条路径的正文是不是窄列」，
        不是 section——采集来源也是 812px 的窄列，它和 hub 归在同一个 section 下。
        """
        self.assertPageContains("const CENTERED_CLEANUP_PAGES=new Set(['/data-cleanup','/scraping']);")
        self.assertCode("document.body.classList.toggle('cleanup-layout',"
                        "CENTERED_CLEANUP_PAGES.has(decodeURIComponent(location.pathname)));")
        self.assertPageLacks("document.body.classList.toggle('cleanup-layout',current==='cleanup')")
        # 窄列本体仍在 hub 上，这两条规则本身不动。
        self.assertPageContains(".cleanuppage{width:min(812px,100%);margin:0 auto;display:grid;gap:32px}")
        self.assertPageContains(
            ".cleanup-layout .geist-breadcrumb,.cleanup-layout .managetitle,.cleanup-layout .pagelede")

    def test_every_management_page_body_shares_the_title_column(self):
        """管理区每一页的正文和它的标题一条中线，宽度都由 `--board-content` 说了算。

        Board 层把 `#manageTitle` 钉在 1120 上，正文各自声明的 812 窄列比它每边窄 154px：
        在宽屏上就是标题顶着左边、正文整块往右缩一截。四页写在同一条规则里，往管理区新加
        一页时照抄这一行，不要在页面自己的 CSS 里另定一个数。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".cleanuppage,.configpage,.scraping-page,.activitypage"
                      "{width:100%;max-width:var(--board-content)}", board)
        self.assertIn("body :is(#manageTitle,#manageCrumb,#manageLede)"
                      "{max-width:var(--board-content);width:100%;margin-left:auto;margin-right:auto}", board)
        self.assertIn(":root{--railW:88px;--board-content:1120px}", board)

    def test_returning_home_from_any_surface_moves_the_highlight(self):
        """Logo、侧栏和沉浸关闭都必须清掉隐藏筛选，不能让 `/` 继续请求 JAV。"""
        self.assertPageContains("function resetHomeState(){")
        self.assertPageContains("q:'',jav:'',thumb:'0'};")
        self.assertPageContains("function openHome(scroll=false){")
        self.assertPageContains("resetHomeState();route('/');clearSearchField();disposeStage(false);showHomeSurfaces();")
        self.assertPageContains("buildEdge();buildBars();load(true);")
        # 抽屉和窄栏已经共用 navTo，这一句只应该存在一处；
        # 两份副本正是当初把追更入口漏在抽屉里的原因。
        self.assertEqual(self.page.count("function navTo(k){"), 1,
                         "导航分支只能留一份 navTo")
        self.assertPageContains("if(k===''){openHome();return}")
        self.assertPageContains("$('#brandHome').onclick=e=>{e.preventDefault();openHome(true)};")
        self.assertPageContains("document.body.style.overflow='';openHome()")
        self.assertPageLacks("clearTokTap();route('/');")
        self.assertCode("state.state=k}\n  route(homePath());")

    def test_ads_icon_matches_the_lucide_stroke_style(self):
        """图标库里没有表示广告的图形，自绘的感叹号必须和其余图标同风格。"""
        self.assertPageContains('<symbol id="i-alert" viewBox="0 0 24 24">')
        self.assertPageContains("['cleanup','数据管理','hard-drive']")

    def test_pending_delete_is_visible_without_deleting_media(self):
        self.assertPageContains("it.disposal==='trash'?'pending-delete':''")
        self.assertPageContains(".card.pending-delete .poster")
        self.assertPageContains('<b>回收站</b>')

    def test_sidebar_glow_lives_inside_the_drawer_and_drifts_like_its_glass(self):
        """光晕是侧栏玻璃面自带的那两团慢漂反光换成的三枚，长在 `.drawer` 里面。

        铺在页面身后的那一版是背景不是光晕——正文和卡片压在它上面，字读不出来。所以这一层
        `position:absolute;inset:0` 待在抽屉内部，溢出连圆角一起被抽屉的 overflow 裁掉。
        位置由 drift 那两条动画推着走，和 board.css 给其余玻璃面的是同一套算法；抽屉自己
        那两团因此必须置为 none，否则两套光斑叠着漂。「玻璃原色」那一档例外，根上挂着
        `data-glow-native` 时抽屉要把自己那两团拿回来。
        两条时长按 `--glow-drift-scale` 同比缩放，41:67 的比例不变——两条一样长就退化成
        一条来回滑动的直线；拉到停住走 `animation-play-state`，淡入那一条不跟着停。
        """
        css = stylesheet_source() + (Path(__file__).resolve().parents[1]
                                     / "web/board.css").read_text(encoding="utf-8")
        self.assertIn('<aside class="drawer" id="drawer"><div class="glowlayer" aria-hidden="true">'
                      '</div>', self.page, "光晕层是抽屉的第一个子元素")
        layer = css.split(".glowlayer{", 1)[1].split("}", 1)[0]
        self.assertIn("position:absolute;inset:0;z-index:-2", layer,
                      "-1 已经归了 .navglide，光晕要在它下面、玻璃填充之上")
        self.assertIn(":root:not([data-glow-native]) .drawer.drawer"
                      "{--glass-drift-a:none;--glass-drift-b:none}", css)
        rule = css.split(".glowlayer::before{", 1)[1].split("}", 1)[0]
        self.assertEqual(rule.count("radial-gradient("), 3, "三枚光晕，不多也不少")
        self.assertIn("background-size:200% 200%", rule, "画布两倍大，drift 才推得动")
        self.assertIn("animation:glowdriftx calc(41s * var(--glow-drift-scale)) linear infinite,"
                      "glowdrifty calc(67s * var(--glow-drift-scale)) linear infinite,"
                      "ambient-in .8s ease .5s both", rule)
        self.assertIn("animation-play-state:var(--glow-drift-play),"
                      "var(--glow-drift-play),running", rule, "淡入那一条不跟着停")
        # 两条周期互质，合起来看不出循环点；和玻璃那两条同一个数，一眼读成同一种光。
        for name in ("@keyframes glowdriftx{", "@keyframes glowdrifty{"):
            self.assertIn(name, css)
        self.assertNotIn("linear-gradient", rule, "底色带与遮罩带都不属于这条规则")
        for gone in ("--glow-veil", "--glow-angle", "--glow-base", "--glow-h:",
                     "--glow-mask", "--glow-rail-fade", "--glow-spot-1-x"):
            self.assertPageLacks(gone, "这个变量已经没有使用者")

    def test_home_glow_reads_every_colour_and_radius_from_a_variable(self):
        """`.glowlayer::before` 里一个字面颜色都不许有。

        颜色是设置面板改得动的参数：写死一处，那一处就永远不跟着用户走，而症状是
        「换了配色但有一层没变」——没有报错，只是画面对不上。
        """
        css = stylesheet_source()
        rule = css.split(".glowlayer::before{", 1)[1].split("}", 1)[0]
        self.assertNotIn("#", rule, "光晕里不许再出现字面颜色")
        self.assertEqual(re.findall(r"rgba?\(", rule), [], "光晕里不许再出现字面颜色")
        for layer in ("--glow-lerp", "--glow-spot-1-color", "--glow-spot-2-w",
                      "--glow-spot-3-fade", "--ambient-opacity"):
            self.assertIn(f"var({layer})", rule, f"{layer} 没有被 .glowlayer::before 引用")

    def test_home_glow_defaults_match_the_default_preset(self):
        """样式表里的默认值就是 `ash` 那一档，两处一字不差。

        对不上的后果只出现在第一帧：`applyHomeGlow()` 跑完之前页面按样式表画，跑完之后
        按 JS 写的值画，中间会闪一次颜色。颜色是两处都有的那部分；半轴与收边的基准值只有
        这里一份，三枚大小各不相同——一样大就读成一团，不是三枚。用户那两条几何拉条按
        倍率乘在基准值上，倍率是变量、基准是字面值，存的因此始终是档位不是算完的百分比。
        """
        css = stylesheet_source()
        for declaration in (
                "--glow-spot-1-color:rgba(143,152,164,.52); "
                "--glow-spot-1-w:calc(20% * var(--glow-size)); "
                "--glow-spot-1-h:calc(20% * var(--glow-size)); "
                "--glow-spot-1-fade:calc(72% * var(--glow-soften))",
                "--glow-spot-2-color:rgba(182,188,196,.38); "
                "--glow-spot-2-w:calc(26% * var(--glow-size)); "
                "--glow-spot-2-h:calc(26% * var(--glow-size)); "
                "--glow-spot-2-fade:calc(74% * var(--glow-soften))",
                "--glow-spot-3-color:rgba(111,119,131,.50); "
                "--glow-spot-3-w:calc(23% * var(--glow-size)); "
                "--glow-spot-3-h:calc(23% * var(--glow-size)); "
                "--glow-spot-3-fade:calc(73% * var(--glow-soften))"):
            self.assertIn(declaration, css)
        self.assertIn("--glow-size:1; --glow-soften:1; --glow-drift-scale:1; "
                      "--glow-drift-play:running;", css, "默认那一档的倍率都是不动")
        # 强度是用户那一档，主题缩放是色板那一档，实际不透明度是两者相乘。
        self.assertIn("--glow-noise:0; --glow-strength:1; --glow-theme-scale:.6", css)
        self.assertIn("--ambient-opacity:calc(var(--glow-strength) * var(--glow-theme-scale))", css)
        # 浅色也开：两档各自的缩放都要在，否则浅色那一档要么是 0 要么和深色一样浓。
        self.assertEqual(css.count("--glow-theme-scale:1;}"), 2, "深色两块色板都要自己那一档")

    def test_home_glow_presets_are_distinct_and_fully_described(self):
        """预设表的形状：档名不重、每档三枚合法色、每档带一枚认得出的强调色。

        逐字钉死整张表没有意义——加一档、换一枚颜色都是产品决定，不是回归。要守住的是
        这张表自己不能坏：重复的档名会让 `glowPalette` 永远取到前一个，写歪的色号会让
        那一层渐变整条失效，不在清单里的强调色会在选中那一档时静默退回默认。
        照 feralui 那十二档扩过之后，档数与它相当，见
        docs/reference-snapshots/feralui-gradients-measured.md。
        """
        block = self.glow_js.split("const HOME_GLOW_PRESETS=[", 1)[1].split("\n];", 1)[0]
        entries = re.findall(r"\['?(\w+)'?,'(.+?)',\{(.*?)\},'(\w+)'\]", block, re.S)
        self.assertGreaterEqual(len(entries), 16, "四档原生加 feralui 那十二档，再加玻璃原色")
        keys = [key for key, _label, _palette, _accent in entries]
        self.assertEqual(len(set(keys)), len(keys), "档名不许重复")
        self.assertEqual(keys[0], "ash", "默认那一档排在最前")
        # 最后那一档的键名在源码里写成常量：`isNativeGlass` 和几处分支都要认它，
        # 散着写三遍 'native' 的话改名时必漏一处。
        self.assertEqual(keys[-1], "GLASS_NATIVE_PRESET", "玻璃原色排在最后")
        accents = re.findall(r"\['(\w+)','.+?'\]", self.glow_js.split("const ACCENTS=[", 1)[1]
                             .split("];", 1)[0])
        for key, label, palette, accent in entries:
            with self.subTest(preset=key):
                colours = re.findall(r"color:'(#[0-9a-f]{6})'", palette)
                self.assertEqual(len(colours), 3, "一档就是三枚光晕")
                self.assertEqual(len(set(colours)),
                                 len(colours) if key != "GLASS_NATIVE_PRESET" else 2,
                                 "同一档里两枚一样的颜色只会读成两团")
                self.assertTrue(2 <= len(label) <= 4, f"{label} 的档名写成两到四个字")
                self.assertIn(accent, accents, "搭配的强调色要在清单里")

    def test_every_preset_colour_has_a_name_in_the_palette(self):
        """每一档预设用到的颜色都在命名色板里。

        少一枚的后果不是报错：从侧栏选完预设再打开那一行的颜色弹层，选中环指不出任何
        一格，读起来像「当前颜色不是这里挑的」。
        """
        presets = self.glow_js.split("const HOME_GLOW_PRESETS=[", 1)[1].split("\n];", 1)[0]
        swatches = self.glow_js.split("const GLOW_SWATCHES=[", 1)[1].split("\n];", 1)[0]
        named = set(re.findall(r"'(#[0-9a-f]{6})'", swatches))
        missing = sorted(set(re.findall(r"color:'(#[0-9a-f]{6})'", presets)) - named)
        self.assertEqual(missing, [], f"这几枚预设色在色板里没有名字：{missing}")

    def test_every_glass_face_takes_its_drift_colour_from_the_same_two_variables(self):
        """每一块玻璃面上那两团漂动的反光都读同一对 `--glass-tint-a/b`，一个字面色都不写。

        侧栏那块交给光晕层，其余的（搜索框、顶栏图标钮、筛选浮层、实体条、设置卡的分区
        导航、媒体库弹层、配色弹层、窄栏）仍走自己那两团——只换色相。写死一处的后果是
        「换了配色但有一块玻璃没跟上」：没有报错，只是一排毛玻璃里有一块是别的颜色。
        尺寸与 alpha 档位留在各自主题那一档里，它们是这块材质自己的浓淡。

        React 那一侧的玻璃面（复核页的批量工具条）是 `styles.css` 里的一条 `@utility`，
        读的是同一批 `--glass-*`，一起在这里核对：两份样式表各画一块玻璃才是最容易走散的
        那种，同一屏上一块跟着配色走、另一块不跟。
        """
        css = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        for declaration in ("--glass-tint-a:var(--glass-native-a)",
                            "--glass-tint-b:var(--glass-native-b)",
                            "--glass-native-a:#6686b8;--glass-native-b:#8f98a4"):
            self.assertIn(declaration, css)
        # 多选那条悬浮坞、批处理条和标签选择条也读这两团：它们和侧栏同时在屏上，
        # 漏掉任何一条就是一屏里两种颜色的玻璃。
        for face in ("body .selectiondock{", ".batchbar,.tagselection{"):
            with self.subTest(face=face):
                rule = css.split(face, 1)[1].split("}", 1)[0]
                self.assertIn("var(--glass-drift-a),var(--glass-drift-b)", rule)
                self.assertIn("var(--glow-drift-scale)", rule, "速度那一条也跟着走")
        react = (Path(__file__).resolve().parents[1]
                 / "frontend/src/react/styles.css").read_text(encoding="utf-8")
        pane = react.split("@utility glass-pane {", 1)[1].split("\n}", 1)[0]
        self.assertIn("var(--glass-drift-a), var(--glass-drift-b)", pane)
        self.assertIn("var(--glow-drift-scale)", pane, "速度那一条也跟着走")
        drifts = re.findall(r"--glass-drift-[ab]:radial-gradient\((.*?)transparent \d\d%\)", css)
        self.assertEqual(len(drifts), 6, "深浅两档各两团，浅色那档还有跟随系统的一份")
        for drift in drifts:
            with self.subTest(drift=drift):
                self.assertNotIn("#", drift, "色相由变量给，这里不写字面色")
                self.assertIn("color-mix(in srgb,var(--glass-tint-", drift)
        # 配色弹层与媒体库弹层共用同一条玻璃规则，两张从侧栏开出来的卡才是同一种材质。
        self.assertIn(".board-library-menu.board-library-menu,.board-glow-menu.board-glow-menu"
                      "{background:var(--glass-drift-a),", css)
        self.assertIn(".board-glow-menu{box-sizing:border-box;width:248px;"
                      "max-width:calc(100vw - 32px);padding:10px;gap:0}", css,
                      "这张卡只留几何，材质归那条共用规则")
        # 速度那一条跟着走，两条时长同比缩放。
        self.assertIn("animation:glassdriftx calc(41s * var(--glow-drift-scale)) linear infinite,"
                      "glassdrifty calc(67s * var(--glow-drift-scale)) linear infinite;\n"
                      "  animation-play-state:var(--glow-drift-play);", css)

    def test_the_glass_native_preset_hands_every_face_back_to_the_theme(self):
        """「玻璃原色」那一档不走光晕层，直接让每块玻璃退回自带那两团。

        照三枚光晕重画一份仿制品是另一回事：自带那两团是两团、尺寸与轨迹各有出处、颜色还
        跟着明暗主题走，仿出来的必然是第三种东西。所以这一档把光晕整层算成 0、把色相变量
        摘掉，样式表里那一档因此生效。摘掉而不是写回主题色，是因为主题色有两套。
        """
        self.assertPageContains("const GLASS_NATIVE_PRESET='native';")
        self.assertPageContains("const isNativeGlass=key=>key===GLASS_NATIVE_PRESET;")
        self.assertCode("const live=glow.on&&!isNativeGlass(glow.preset);")
        self.assertCode("const native=!glow.on||isNativeGlass(glow.preset);")
        self.assertCode("el.toggleAttribute('data-glow-native',native);")
        self.assertCode("if(native){el.style.removeProperty('--glass-tint-a');"
                        "el.style.removeProperty('--glass-tint-b');return}")
        self.assertCode("el.style.setProperty('--glass-tint-a',glow.spot1.color);")
        # 这一档的圆球与钮上那颗点画的是当前主题下真在漂的那两色，不拿别的颜色顶。
        css = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-glow-ball[data-glow-native]{--glow-chip:conic-gradient"
                      "(from -90deg,var(--glass-native-a) 0 50%,var(--glass-native-b) 50% 100%)}", css)
        self.assertIn(".board-glow-toggle[data-glow-native] .board-glow-mark-glow{", css)
        # 界面上这一档只留漂移速度：其余几条管不着任何东西，留着就是按了不动的控件。
        self.assertPageContains("row.hidden=native&&row.dataset.glowField!=='speed');")
        self.assertPageContains('<p class="glownative" data-glow-native-note hidden>')
        # `.glowfield` 与 `.glowgroup` 自带 display，不补这一条的话 `hidden` 压根收不走它们：
        # 拉条照样摆在那里、拖得动，而那一档下它们什么也管不着。
        self.assertPageContains(".glowfield[hidden],.glowgroup[hidden]{display:none}")

    def test_accent_repoints_the_boardui_ramp_instead_of_recolouring_each_control(self):
        """换强调色就是把 `--color-accent-50…950` 整组指到另一个色相，组件规则一个字不改。

        机制照搬 BoardUI（`frontend/src/react/boardui/styles/theme.css` 第 25–45 行）：主按钮
        渐变、焦点环、链接与数据色全都引用同一组变量。逐个控件去改颜色的那条路走不通——
        React 子树在 `.peach-react` 上重新声明的语义 token 会盖住根上的值，而它们本来就
        引用 `--color-accent-*`，改这一组就顺着继承进去了，两边因此不会各说各话。
        """
        css = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(":root,:root[data-accent=blue],[data-accent-ball=blue]{--color-accent-50:", css)
        ramps = re.findall(r":root\[data-accent=(\w+)\],\[data-accent-ball=\1\]\{(.*?)\}", css)
        self.assertGreaterEqual(len(ramps) + 1, 12, "十二个色相绕色轮一圈")
        for name, body in ramps:
            with self.subTest(accent=name):
                self.assertEqual(len(re.findall(r"--color-accent-\d+:", body)), 11,
                                 "十一级少一级，引用那一级的控件就没有颜色")
        # 焦点环、链接与主按钮三档渐变全部从这组色阶派生，不再写死一枚蓝。
        self.assertIn("--color-border-focus-ring:var(--color-accent-500)", css)
        self.assertIn("--board-blue:linear-gradient(180deg,var(--color-accent-500),"
                      "var(--color-accent-600))", css)
        self.assertIn("--board-blue-hover:linear-gradient(180deg,var(--color-accent-400),"
                      "var(--color-accent-500))", css)
        self.assertIn("--board-blue-active:linear-gradient(180deg,var(--color-accent-600),"
                      "var(--color-accent-700))", css)
        # 跟随系统的深色没有 data-theme，01-base 那枚字面蓝比 `:root` 更具体，要按同样的
        # 具体度接回来，否则焦点环和链接只在手动选深色时跟着强调色走。
        self.assertIn("@media(prefers-color-scheme:dark){:root:not([data-theme])"
                      "{--tungsten:var(--color-border-focus-ring)}}", css)
        self.assertIn(".board-glow-ball[data-accent-ball]{--glow-chip:radial-gradient"
                      "(circle closest-side,var(--color-accent-400),var(--color-accent-600))}", css,
                      "圆球拿的就是这一档真会写上去的两级")
        # 开关、勾选框、滑轨填充与主操作键也是同一个意思。漏掉任何一个，换了强调色的页面
        # 上就会剩下几枚蓝件，读起来像是没换干净。
        self.assertIn(".ptoggle:checked{background:var(--board-blue);", css)
        self.assertIn(".pcheck input:is(:checked,:indeterminate)+span{color:#fff;"
                      "border-color:transparent;background:var(--board-blue);", css)
        self.assertIn("accent-color:var(--color-accent-600);", css)
        self.assertIn("#applyUISetting{grid-column:1/-1;width:100%;background:var(--board-blue);", css)
        for literal in ("#3986ff", "#1760ef", "#2473fe", "#bfdbfe", "#1e40af"):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, css, "这一枚蓝的字面值应当由强调色色阶给")

    def test_accent_is_stored_paired_with_a_preset_and_overridable_on_its_own(self):
        """强调色存一个档名，换光晕预设时跟着换，单点那一排又能把它覆盖掉。

        一档配色就是一副面：光晕暖着、按钮还是蓝的，读起来是两套皮叠在一起。但搭配是
        建议不是绑定，所以那一排强调色单独点得动，点完只改强调色、不动光晕。
        """
        self.assertPageContains("const DEFAULT_ACCENT='blue';")
        self.assertPageContains("const normalizeAccent=value=>ACCENTS.some(([key])=>key===value)"
                                "?value:DEFAULT_ACCENT;")
        self.assertPageContains("const glowAccent=key=>(HOME_GLOW_PRESETS.find(([name])=>name===key)"
                                "||[])[3]||DEFAULT_ACCENT;")
        self.assertPageContains("appSettings.accent=normalizeAccent(appSettings.accent)")
        self.assertCode("function applyAccent(){glowRoot.dataset.accent=appSettings.accent}")
        # 换预设：光晕、玻璃色相与强调色一起走。
        self.assertCode("appSettings.accent=glowAccent(key);")
        # 单点强调色：只写这一个。
        self.assertCode("appSettings.accent=normalizeAccent(chip.dataset.accent);")
        self.assertCode("saveSettings();applyAccent();syncGlowChrome();")
        # 「重置」把两者一起收回默认。
        self.assertCode("appSettings.accent=DEFAULT_ACCENT;")
        self.assertPageContains('<div class="board-glow-grid" data-accent-grid role="group" '
                                'aria-label="强调色"></div>')
        self.assertPageContains('class="board-glow-chip" data-accent="${key}"')
        self.assertPageContains('data-accent-ball="${key}"')

    def test_home_glow_interpolates_in_oklab_with_a_declared_fallback(self):
        """oklab 插值由 @supports 开启，认不出它的引擎退回 sRGB 而不是整层消失。"""
        css = stylesheet_source()
        self.assertIn("--glow-lerp: ;", css, "默认必须是空串，`in oklab` 只在 @supports 里给")
        self.assertIn("@supports (background:linear-gradient(in oklab,red,blue))"
                      "{:root{--glow-lerp:in oklab}}", css)

    def test_home_glow_grain_is_generated_not_a_bitmap_in_the_repository(self):
        """颗粒瓦片是 data URI，仓库里不落位图；强度 0 就是关。"""
        css = stylesheet_source()
        rule = css.split(".glowlayer::after{", 1)[1].split("}", 1)[0]
        self.assertIn("mix-blend-mode:overlay", rule)
        self.assertIn("opacity:var(--glow-noise)", rule)
        self.assertIn("data:image/svg+xml,", rule)
        self.assertIn("feTurbulence", rule)

    def test_home_glow_settings_are_stored_bounded_and_written_to_its_own_layer(self):
        """设置里存得住、读回来要夹回区间，改一下就写到光晕自己那一层上。

        用户面是三枚颜色、五条拉条和档名：光晕的形状基准（半轴、收边、两条轨迹的时长）
        全在样式表里，存的只是倍率的档位。几何一旦按算完的百分比进了 localStorage，改形状
        就再也改不动那些存过的机器。
        """
        self.assertPageContains("sidebarOrder:DEFAULT_SIDEBAR_ORDER,homeGlow:DEFAULT_HOME_GLOW,"
                                "accent:DEFAULT_ACCENT}")
        self.assertPageContains("const DEFAULT_HOME_GLOW={on:true,preset:'ash',strength:100,noise:0,"
                                "speed:100,soften:50,size:50,\n  ...glowPalette('ash')}")
        self.assertPageContains("appSettings.homeGlow=normalizeHomeGlow(appSettings.homeGlow)")
        self.assertCode("function normalizeHomeGlow(raw){")
        # 五条拉条的区间与默认值只有一张表，规范化按它逐项夹回去。
        self.assertCode("const GLOW_RANGES={strength:[0,100,100],noise:[0,100,0],speed:[0,300,100],"
                        "soften:[0,100,50],size:[0,100,50]};")
        self.assertCode("for(const [field,[min,max,fallback]] of Object.entries(GLOW_RANGES))")
        self.assertCode("glow[field]=glowNumber(+stored[field],min,max,fallback);")
        self.assertPageLacks("fade:glowNumber(+spot.fade", "收边是形状，不是偏好")
        self.assertPageContains("const glowColor=(value,fallback)=>/^#[0-9a-f]{6}$/i.test(String(value))")
        self.assertCode("function paintHomeGlow(el,glow){")
        self.assertCode("write('--glow-strength',String(live?glow.strength/100:0));")
        self.assertCode("write(`--glow-spot-${index+1}-color`,glowRgba(spot.color,spot.alpha));")
        # 三条几何拉条在这里换算成倍率；速度拉到 0 暂停漂移，不去算除以零的时长。
        self.assertCode("write('--glow-soften',(0.7+glow.soften/100*0.6).toFixed(3));")
        self.assertCode("write('--glow-size',(0.5+glow.size/100).toFixed(3));")
        self.assertCode("write('--glow-drift-scale',glow.speed?(100/glow.speed).toFixed(3):'1');")
        self.assertCode("write('--glow-drift-play',glow.speed?'running':'paused');")
        self.assertPageContains("applyHomeGlow();")
        # 预设给中文名，含当前默认那一档：灰雾配蓝，两者一起就是这个壳没被改过时的样子。
        self.assertPageContains("['ash','灰雾',{")
        self.assertPageContains("spot3:{color:'#6f7783',alpha:50}},'blue'],")
        self.assertPageContains("['amber','钨丝暖阁',{")
        self.assertPageContains("['custom','自定义']")

    def test_home_glow_data_lives_in_a_module_app_js_only_imports(self):
        """预设、色板、规范化和那一次绘制都在 `web/js/home-glow.js`，app.js 只 import。

        React 壳要的就是这一份：留在 app.js 里，迁移时同一张预设表、同一套色板和同一段
        规范化会被抄进组件再各自演化，而两份色板差一枚颜色是看不出来的。
        所以那个模块不认识 `appSettings`、`$`、`saveSettings`，`paintHomeGlow` 只写传进来的
        那枚元素；侧栏那枚配色钮、它的弹层和设置面板的装配仍旧留在 app.js。
        """
        self.assertIn("import { ACCENTS, DEFAULT_ACCENT, DEFAULT_HOME_GLOW, GLASS_NATIVE_PRESET, "
                      "GLOW_SPOT_LABELS, GLOW_SWATCHES, GLOW_SWATCH_FAMILIES, HOME_GLOW_CHOICES, "
                      "HOME_GLOW_PRESETS, HOME_GLOW_SPOTS, glowAccent, glowChipFill, glowColor, "
                      "glowPalette, glowPresetName, isNativeGlass, normalizeAccent, "
                      "normalizeHomeGlow, paintGlassFaces, paintHomeGlow } "
                      "from './js/home-glow.js';", self.app_js)
        for moved in ("const HOME_GLOW_PRESETS=[", "const GLOW_SWATCHES=[", "const ACCENTS=[",
                      "const GLOW_SPOT_LABELS=[", "const DEFAULT_HOME_GLOW=",
                      "function normalizeHomeGlow(", "function paintHomeGlow(",
                      "function paintGlassFaces("):
            self.assertNotIn(moved, self.app_js, f"{moved} 已经搬进 js/home-glow.js")
            self.assertIn(moved, self.glow_js)
        # 注释里说得出这几个名字（它讲的正是「这里没有它们」），代码里一次都不许出现。
        code = "\n".join(re.sub(r"/\*.*?\*/", "", self.glow_js, flags=re.S).splitlines())
        for forbidden in ("appSettings", "saveSettings(", "document.", "peach-ui.js"):
            self.assertNotIn(forbidden, code, "这一份不认识页面，只认参数")
        self.assertIn("paintHomeGlow(glowField,appSettings.homeGlow)", self.app_js)

    def test_home_glow_normalisation_replaces_a_retired_preset_wholesale(self):
        """存着的档名已经不在清单里时，连它那三枚颜色一起换成默认那一档。

        逐项夹回区间对这一种情形不管用：被清退的配色留在 `spot1..3` 上全是合法值，
        夹完原样还在，页面看上去根本没换过档。自定义不算——那三枚是用户自己挑的。
        旧版本多存的键（底色与角度）不必单独清理，这里只按当前模型逐项取值。
        """
        self.assertCode("const known=HOME_GLOW_CHOICES.some(([key])=>key===stored.preset);")
        self.assertCode("const preset=known?stored.preset:'ash';")
        self.assertCode("const seed=glowPalette(preset==='custom'?'ash':preset);")
        self.assertCode("const spot=known&&stored[key]&&typeof stored[key]==='object'"
                        "?stored[key]:{},fallback=seed[key];")
        self.assertPageLacks("angle:glowNumber", "角度已经不在模型里")
        self.assertPageLacks("base:seed.base.map", "底色已经不在模型里")

    def test_home_glow_panel_leads_with_the_preset_then_names_one_group(self):
        """强度与颗粒直接跟在当前配色后面，只有「颜色」自己占一个带名字的分组。

        强度和颗粒不归任何分组：两条拉条一条调整层的亮度、一条调它的颗粒，都是这一片光
        自己的事，套一个名字上去只会多出一个读不懂的词。三枚光晕要分组，是因为下面挂着
        三行各自能展开色板的行。
        """
        self.assertPageContains('<b>侧栏光晕</b>')
        self.assertPageContains('id="homeGlowSetting" class="ptoggle" role="switch"')
        self.assertPageContains('<section class="glowsetting" id="homeGlowControls"')
        self.assertCode("function renderHomeGlowSetting(){")
        self.assertPageContains("renderHomeGlowSetting();")
        self.assertPageLacks('<h4>场</h4>', "「场」不是这套界面的词")
        self.assertPageContains('<section class="glowgroup" data-glow-colours><h4>颜色</h4>')
        self.assertPageContains("glowFieldRowHtml('strength','强度',100)")
        self.assertPageContains("glowFieldRowHtml('noise','颗粒',60)")
        self.assertPageContains("glowFieldRowHtml('speed','漂移速度',300)")
        self.assertPageContains("glowFieldRowHtml('soften','柔化',100)")
        self.assertPageContains("glowFieldRowHtml('size','大小',100)")
        # 「光斑」留给 board.css 里玻璃面自带那两团反光，它是另一件东西；用户在这里配的
        # 三枚一律叫光晕，界面文案和注释都不再混用。
        self.assertPageContains("const GLOW_SPOT_LABELS=['光晕一','光晕二','光晕三'];")
        for stale in ("光斑一", "光斑二", "光斑三", "光斑色"):
            self.assertPageLacks(stale)
        self.assertPageContains('<button type="button" class="geist-button" data-glow-reset>恢复默认</button>')
        # 即时生效，不配「保存」键。
        self.assertPageLacks('data-glow-save')
        # 配色整档搬到侧栏那枚圆钮上了，面板里只留一行只读的当前档名。
        self.assertPageContains('<p class="glowcurrent">当前配色<b data-glow-preset-name></b></p>')
        self.assertPageLacks("selectFieldHtml(HOME_GLOW_CHOICES", "配色下拉已经搬到侧栏")
        self.assertPageLacks('class="glowrange"', "拉条换成自绘的 .dial-slider")

    def test_home_glow_colours_are_picked_from_a_named_palette_not_a_colour_well(self):
        """挑颜色走自绘色板：色系胶囊加圆色块，页面上一个原生取色器都没有。

        原生 `<input type="color">` 打开的是系统取色盘——那里没有这套界面的颜色词汇，
        挑出来的值也不受这套色板约束，等于把「配色」交给了另一套产品。
        """
        self.assertPageLacks('type="color"', "原生取色器已经换成自绘色板")
        self.assertPageContains("const GLOW_SWATCH_FAMILIES=[['all','全部'],['gray','灰'],['red','红'],"
                                "['yellow','黄'],\n  ['green','绿'],['cyan','青'],['blue','蓝'],"
                                "['purple','紫'],['brown','棕']];")
        self.assertPageContains('<div class="glowpalette" role="radiogroup"')
        self.assertPageContains('<div class="glowpills" role="group" aria-label="色系">')
        self.assertPageContains('class="glowpill" data-glow-pill="${key}" aria-pressed="${index===0}"')
        self.assertPageContains('class="glowswatch" role="radio" aria-checked="false" data-glow-swatch="${hex}"')
        self.assertPageContains('class="glowstopmain" data-glow-stop-toggle aria-haspopup="dialog" aria-expanded="false"')
        # 胶囊只管筛，不改值；改值的是色块，且立刻把档名转成自定义。
        self.assertCode("swatches.forEach(swatch=>{swatch.hidden=family!=='all'"
                        "&&swatch.dataset.glowFamily!==family});")
        self.assertCode("glow().preset='custom';")
        # 弹层与页面其它浮层同一套开合，不自己写一份定位。
        self.assertCode("wireAnchoredMenu(row,toggle,pop);")
        block = self.glow_js.split("const GLOW_SWATCHES=[", 1)[1].split("\n];", 1)[0]
        entries = re.findall(r"\['(\w+)','(.+?)','(#[0-9a-f]{6})'\]", block)
        self.assertGreaterEqual(len(entries), 42, "八个色系打底各六档，再加各档预设带进来的")
        families = set(re.findall(r"\['(\w+)',", self.glow_js.split(
            "const GLOW_SWATCH_FAMILIES=[", 1)[1].split("];", 1)[0]))
        # 名字按颜色本身取，一枚颜色一个名字：同名不同色、同色不同名，两种都会让色板
        # 里出现两格「同一样东西」。
        self.assertEqual(len(set(name for _f, name, _hex in entries)), len(entries))
        self.assertEqual(len(set(value for _f, _n, value in entries)), len(entries))
        for family, name, value in entries:
            with self.subTest(colour=value):
                self.assertIn(family, families, f"{name} 归的色系不在胶囊那一排里")

    def test_home_glow_dials_write_once_a_frame_and_save_on_release(self):
        """拖动只改参数、只排一帧重画，落盘留给松手那一下。

        每一步都写变量加 saveSettings() 的量过：一次 60 步拖动是 1320 次 setProperty
        和 60 次 localStorage 写入，全在主线程上。
        """
        self.assertCode("onInput:value=>{glow()[field]=value;applyHomeGlow()},")
        # 其余玻璃面跟着走的只有速度，而它只能写在根上：拖动期间不写，松手那一下才铺开。
        self.assertCode("onChange:()=>{saveSettings();if(field==='speed')applyGlassFaces()}}));")
        self.assertCode("glowFrame=requestAnimationFrame(()=>{glowFrame=0;"
                        "paintHomeGlow(glowField,appSettings.homeGlow)});")
        self.assertCode("if(written.get(name)===value)return;")
        # 面板 DOM 只建一次：重建会把正开着的颜色弹层、焦点和拖动状态一起扔掉。
        self.assertCode("if(mount.dataset.glowWired!=='true'){")

    def test_home_glow_variables_are_written_off_the_root(self):
        """光晕变量写在自己那一层上，不写 <html>。

        自定义属性是继承的：写在根上，整棵树都要重算样式。2026-09-16 在首页量过，
        写一次变量再强制布局，写在 <html> 上是每帧 12.7–16.6ms，写到一枚没有子节点的
        元素上是 0.09ms；16.7ms 的帧预算装不下前者，拖动必掉帧。
        """
        css = stylesheet_source()
        self.assertPageContains('<div class="glowlayer" aria-hidden="true"></div>')
        self.assertCode("const glowField=document.querySelector('.glowlayer');")
        self.assertCode("el.style.setProperty(name,value);")
        self.assertIn(".glowlayer{--ambient-opacity:calc(var(--glow-strength) * var(--glow-theme-scale));", css)
        self.assertNotIn("body::before{", css, "光晕不再挂在 body 的伪元素上")
        self.assertNotIn("body::after{", css, "光晕不再挂在 body 的伪元素上")

    def test_dial_slider_is_a_keyboard_operable_slider_control(self):
        """自绘拉条是通用控件，且自己把 slider 那套语义补齐。

        换掉原生 `<input type=range>` 的代价就是这些：角色、三个值、键盘四种走法和
        指针捕获全得自己写；少一样，它就只是一条能拖的装饰。
        """
        components = (Path(__file__).resolve().parents[1]
                      / "web/js/ui-components.js").read_text(encoding="utf-8")
        self.assertIn("export function dialSliderHtml(", components)
        self.assertIn("export function wireDialSlider(", components)
        self.assertIn('class="dial-slider" data-dial-slider role="slider" tabindex="0"', components)
        for attribute in ("aria-valuemin", "aria-valuemax", "aria-valuenow", "aria-valuetext"):
            self.assertIn(f'{attribute}="', components, f"{attribute} 缺了这条拉条就报不出自己的值")
        # 键盘：方向键一档、Shift 十档、Home／End 到两端。
        self.assertIn("const span=event.shiftKey?10:step;", components)
        self.assertIn("const moves={ArrowLeft:-span,ArrowDown:-span,ArrowRight:span,ArrowUp:span};", components)
        self.assertIn("else if(event.key==='Home')next=min;", components)
        self.assertIn("else if(event.key==='End')next=max;", components)
        # 指针：捕获加 touch-action，拖出控件和触屏滑动都不断。
        self.assertIn("slider.setPointerCapture(event.pointerId)", components)
        self.assertIn(".dial-slider{", stylesheet_source())
        self.assertIn("touch-action:none", stylesheet_source())
        # 轨道几何按下时量一次，拖动中不再逐次强制布局。
        self.assertIn("const rect=trackBox||track.getBoundingClientRect();", components)

    def test_sidebar_carries_the_glow_preset_button_next_to_the_theme_toggle(self):
        """侧栏底部那枚配色钮就是换配色的入口，收起时和主题键叠成一列。

        配色是随手换的东西，设置面板是调细节的地方：把它留在面板里，换一次要开面板、
        找分区、再找下拉。钮右下那枚点说的是现在这一档的第一枚光晕。
        它和旁边的设置钮长得一模一样：36px、8px 圆角、透明底、20px 图标。加一圈边和一层
        阴影的那一版是 BoardUI 给浮在内容上的按钮画的，这里它站在侧栏面上，紧挨着一枚
        没有任何框的设置钮——两枚并排却一枚带框，读起来是两种控件。
        """
        self.assertPageContains('class="board-glow-toggle" id="boardGlowBtn" aria-label="光晕配色"')
        self.assertPageContains('aria-haspopup="dialog" aria-expanded="false" aria-controls="boardGlowMenu"')
        # 钮上是调色盘字形，右下角两枚叠着的小圆报它管的那两样：光晕色、强调色压在上面。
        self.assertPageContains('<use href="#ri-palette-line"/></svg><span class="board-glow-mark" aria-hidden="true">'
                                '<span class="board-glow-mark-glow"></span><span class="board-glow-mark-accent"></span>'
                                '</span></button>')
        css = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-glow-mark-glow{left:0;top:0;background:var(--glow-swatch,var(--ink))}", css)
        self.assertIn(".board-glow-mark-accent{right:0;bottom:0;z-index:1;", css)
        self.assertIn(".board-glow-toggle[data-glow-off] .board-glow-mark-glow{display:none}", css)
        self.assertPageContains('<header class="board-glow-head" data-glow-presets><span>光晕</span>')
        self.assertPageContains('class="board-glow-reset" data-glow-preset-reset>重置</button>')
        self.assertPageContains('<p class="board-glow-head board-glow-sub"><span>强调色</span></p>')
        self.assertPageContains('<footer><button type="button" class="geist-button primary" data-glow-detail>详细设置</button></footer>')
        self.assertCode("const glowFloating=wireAnchoredMenu(boardFoot,glowButton,glowPicker);")
        # 选中那一档自己报出来，不靠一圈环让人猜。
        self.assertPageContains('aria-pressed="${key===current}"')
        css = stylesheet_source() + (Path(__file__).resolve().parents[1]
                                     / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-glow-toggle{position:relative;display:grid;place-items:center;"
                      "width:36px;height:36px;flex:none;\n  padding:0;border:0;border-radius:8px;"
                      "background:transparent;color:var(--muted);cursor:pointer}", css)
        # 这一排两枚图标键坐在侧栏那块玻璃上，悬停只提图标色：抬一层底就是在玻璃上补一块
        # 不透明的方片，那一格的玻璃在视觉上断掉。顶栏那批 `.ib` 站在实底上，不在此列。
        self.assertIn(".board-glow-toggle:hover,.board-foot-actions>#settingsBtn:hover"
                      "{background:transparent;color:var(--ink)}", css)
        # 明暗切换那一对反过来：它们没被选中时身上什么都没有，只提字色等于没有反馈。
        self.assertIn(".board-theme-toggle button:not([aria-pressed=true]):hover"
                      "{background:var(--hover);color:var(--ink)}", css)
        # 和设置钮对齐到一个数：两枚 36px 的方块在 60px 的收起态里才排得直。
        self.assertIn(".board-foot-actions>#settingsBtn{width:36px;height:36px;", css)
        # 两枚叠着的小圆就是「现在哪一档」，坐在钮的右下角，字形留在中间。
        self.assertIn(".board-glow-toggle svg{width:20px;height:20px;fill:currentColor;stroke:none}", css)
        self.assertIn(".board-glow-mark{position:absolute;right:0;bottom:0;display:block;width:16px;height:14px}", css)
        self.assertNotIn(".board-glow-dot{", css)
        # 收起时侧栏只有 60px，两枚键排成一列。
        self.assertIn(".drawer:not(.open) .board-foot-actions{flex-direction:column}", css)

    def test_the_colour_card_drops_the_glow_row_while_the_glow_is_off(self):
        """光晕关掉之后配色卡里只剩强调色，钮上那枚点改说强调色。

        那一组球和它的「重置」换的是一层现在不画的东西：点下去屏幕上没有任何反应，卡
        的上半张却还被它占着。整组连同标题一起收起来，卡就只说当前还管用的那一件事。
        开关在设置面板里、卡在侧栏底部，两处同时看得见，所以开关那一下要当场同步侧栏，
        不能等下一次刷新。
        """
        self.assertCode("glowButton.style.setProperty('--glow-swatch',"
                        "glow.on?glow.spot1.color:'var(--color-accent-500)');")
        self.assertCode("glowButton.toggleAttribute('data-glow-native',"
                        "glow.on&&isNativeGlass(glow.preset));")
        self.assertCode("glowButton.toggleAttribute('data-glow-off',!glow.on);")
        self.assertCode("glowPicker.querySelectorAll('[data-glow-presets],[data-glow-grid]')"
                        ".forEach(node=>node.hidden=!glow.on);")
        self.assertCode("toggle.onchange=()=>{glow.on=toggle.checked;mount.hidden=!glow.on;"
                        "saveSettings();applyHomeGlow();applyGlassFaces();syncGlowSidebar()};")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        # 类名里写死的 display 压得过 [hidden] 那条 UA 规则，收起来要自己说一遍。
        self.assertIn(".board-glow-head[hidden],.board-glow-grid[hidden]{display:none}", board)
        # 收起之后「强调色」成了卡里第一样东西，它那 12px 的上间距一起归零。
        self.assertIn(".board-glow-grid[hidden]+.board-glow-sub{margin-top:0}", board)

    def test_home_glow_parameter_block_cannot_overflow_the_settings_card(self):
        """参数区右侧必须自己让出设置卡那一圈留白，不靠 overflow 裁掉。

        `.glowsetting` 不是 `.settingrow`，board.css 给普通设置行的 16px 右外边距落不到
        它身上，于是整块压在分组 16px 的圆角上，读数、色块和「恢复默认」被切掉一截。
        裁掉不是修好：被切掉的仍然是用户要点的东西。
        """
        css = stylesheet_source()
        rule = css.split(".glowsetting{", 1)[1].split("}", 1)[0]
        self.assertIn("margin-right:16px", rule, "右侧那 16px 要自己让出来")
        self.assertNotIn("overflow:hidden", rule, "裁掉不算修好")
        self.assertIn("min-width:0", rule, "网格列不许被内容顶宽")
        # 读数是定宽的，定宽列旁边的那一列必须能压缩，否则整行只会往外顶。
        self.assertIn(".glowfield .dial{flex:1;min-width:0}", css)

    def test_detail_deduplicates_identity_and_supports_tag_editing(self):
        self.assertPageContains("const identitySeen=new Set()")
        self.assertPageContains("data-remove-tag")
        self.assertPageContains("/api/item-tag")
        self.assertPageContains('class="tagplus"')

    def test_tag_picker_supports_search_recent_selection_and_keyboard(self):
        self.assertPageContains('class="tagpicker"')
        self.assertPageContains("peach.recentTags")
        self.assertPageContains("最近使用")
        self.assertPageContains("e.key==='ArrowDown'||e.key==='ArrowUp'")
        self.assertPageContains("e.key==='Escape'")

    def test_source_icons_are_visible_in_detail_and_list_badges(self):
        self.assertPageContains(".srcbig svg{stroke:currentColor;fill:none")
        self.assertPageContains("local:icon('hard-drive')")
        self.assertPageContains('title="${esc(label)}" aria-label="${esc(label)}"')
        self.assertPageContains(".src{display:grid;place-items:center;width:20px;height:20px;padding:0;border:0;background:transparent}")
        self.assertPageContains(".srcbig{display:inline-grid;place-items:center;width:22px;height:22px;padding:0;border:0;background:transparent}")

    def test_beeg_evidence_driven_surfaces_are_translucent_and_rail_is_continuous(self):
        self.assertPageContains(".brandpill{")
        self.assertPageContains("background:var(--overlay-5);border:1px solid var(--border-10)")
        self.assertCode("border-radius:var(--pill-radius);background:transparent;"
                        "border:1px solid var(--field-ring)")
        self.assertPageContains("--overlay-5:rgba(245,250,255,.05)")
        self.assertPageContains("--border-15:rgba(245,250,255,.15)")
        # 窄栏要有右分割线（用户 2026-08-26 明确要求）：无边框时两边背景太接近，
        # 看不出左边那一条到哪里为止。
        self.assertPageContains("border-right:1px solid var(--line-soft)")
        self.assertPageContains("['performers','艺人','user-round']")
        self.assertPageContains("['tags','标签','tags']")

    def test_entity_profile_hides_home_facets_and_renders_context(self):
        self.assertPageContains("body.entity-open #tiers,body.entity-open #tagbar,")
        self.assertPageContains("logo:company&&d.has_logo?d.canonical_name:'',")
        self.assertPageContains('class="tagscroll entitytags"')
        self.assertPageContains("filterChipHtml(tagLabel(x.k),{attr:'data-entity-tag'")
        self.assertPageContains('class="relatedpeople"')
        self.assertPageContains("data-related-performer")
        profile = self.page[self.page.index("async function openEntity("):]
        self.assertLess(profile.index('<section class="entityhero" aria-label="资料">'),
                        profile.index('class="relatedpeople"'))
        self.assertLess(profile.index('class="relatedpeople"'),
                        profile.index('class="tagscroll entitytags"'))
        # 同台艺人是这个人的附注，收在资料卡底那条带里，不是这一页的正文。这一排是谁
        # 由 aria-label 说，不另画一枚小标签占位。
        self.assertPageContains('<div class="entityfoot" aria-label="同台艺人">'
                                '<div class="relatedpeople">${related}</div></div>')
        self.assertPageLacks("entityfootlabel")
        self.assertPageContains('class="entitytagbar" aria-label="媒体与标签"')
        self.assertPageContains("body.entity-open .index{overflow-x:visible}")
        self.assertNotIn("关联艺人", profile)
        self.assertNotIn("相关标签", profile)
        # 资料页只渲染可核对的身份、计数与链接，没有散文简介块，样式表里也不该
        # 留下对应选择器。
        self.assertPageLacks("entitysummary")

    def test_entity_people_and_tags_match_home_vertical_rhythm(self):
        # 同台艺人那条带是资料卡的卡脚：横滚的轨道吃掉整条宽度。
        self.assertPageContains(".entityfoot{display:flex;align-items:center;gap:16px;min-width:0;padding:12px 20px;")
        self.assertPageContains(".relatedpeople{display:flex;flex:1;min-width:0;gap:12px;overflow-x:auto;scrollbar-width:none")
        self.assertPageContains("height:var(--filterH);margin:0 -16px;padding:9px 16px")

    def test_horizontal_avatar_rails_leave_room_for_the_hover_ring(self):
        """圆头像的悬停圈和选中圈是外扩 `box-shadow`，横滚容器会把它削平。

        `overflow-x:auto` 把计算后的 `overflow-y` 一起变成 auto，头像贴着容器上沿
        时那一圈就被裁掉顶部。留 3px 上方余量再用等量负 margin 抵掉，位置不动。
        这两行是同一个缺陷重犯过多次的地方，写成一条共用规则。
        """
        self.assertPageContains(".tier,.relatedpeople{padding-top:3px;margin-top:-3px}")
        # `.tier` 后面那条不能再用 padding 简写，否则把上面的余量清回 0。
        self.assertPageContains("scrollbar-width:none;padding-inline:16px;padding-bottom:8px")
        self.assertPageLacks("scrollbar-width:none;padding:0 16px 8px")

    def test_every_home_navigation_restores_the_shared_facets(self):
        self.assertPageContains("function showHomeSurfaces()")
        self.assertPageContains("$('#tiers').style.display='';$('#tagbar').style.display=''")
        self.assertPageContains("function closeStats(push=true){if(push)route('/');showHomeSurfaces();load(true)}")
        self.assertPageContains("async function load(reset)")
        # 版次折叠的集合要和分卷那套一起清，见 test_both_collapse_sets_are_cleared_together。
        self.assertCode(
            "showHomeSurfaces();\n  if(reset){offset=0;"
            "renderedPartGroups.clear();renderedEditionGroups.clear()}")
        self.assertPageContains("showHomeSurfaces();disposeStage(false)")

    def test_entity_tags_filter_inside_the_current_entity_page(self):
        self.assertPageContains("ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&key!==kind&&key!=='sort')p.set(key,filters[key])})")
        self.assertPageContains("async function updateEntityCollection")
        # 资料页的标签走全站共用的那个开关，落在这一页的筛选上，不重开页面。
        self.assertCode("$('#index').querySelectorAll('[data-entity-tag]').forEach(b=>b.onclick=()=>\n"
                        "    toggleTag(b.dataset.entityTag));")
        self.assertPageContains("updateEntityCollection(barsContext.kind,barsContext.name,filters,true)")
        self.assertPageContains("renderEntityCollection(kind,name,items,filters)")
        self.assertPageLacks("openEntity(kind,name,true,next)")
        self.assertPageLacks(
            "document.body.classList.remove('entity-open');$('#index').hidden=true;state.tag=b.dataset.entityTag"
        )

    def test_every_entity_video_collection_reuses_applicable_sort_controls(self):
        self.assertPageContains("shuffleClass='entitybatch'")
        self.assertPageContains("filters.sort||'new',filters.dir,'data-entity-sort')")
        self.assertPageContains("p.set('sort',filters.sort||'new')")
        self.assertPageContains("if(filters.sort==='seed')p.set('seed',state.seed)")
        self.assertPageContains("const JAV_RELEASE_SORT=['release','发行时间']")
        self.assertPageContains("javActive()?[JAV_RELEASE_SORT,...ordered]:ordered")
        self.assertPageContains("items:sortOptions()")
        self.assertPageContains("renderItem:([key,label])=>sortButtonHtml")
        self.assertPageContains("renderItem:([k,l])=>sortButtonHtml")
        self.assertPageContains(
            "if(state.jav!=='1'&&state.sort==='release'){state.sort='seed';state.dir=''}")
        self.assertPageContains(
            "if(next)updateEntityCollection(kind,name,{...filters,...next},true)")
        self.assertPageContains("key==='sort'&&filters[key]==='new'")
        self.assertPageContains(".entitycollectionhead .sorts")
        self.assertPageContains(".entitytagbar{position:sticky;top:var(--topH);z-index:61")
        self.assertPageContains("height:var(--filterH);margin:0 -16px;padding:9px 16px")
        self.assertPageContains(".entitytags .pill{flex:none}")
        self.assertPageLacks(".entitytags button{height:34px")
        self.assertPageContains("mountFilterFrame(top,bottom,")
        self.assertPageContains(".entitycollectionhead{position:sticky;top:var(--topH);z-index:60")
        self.assertPageContains(
            ".tagbar.is-stuck,.count.is-stuck,.entitytagbar.is-stuck,.entitycollectionhead.is-stuck"
        )
        self.assertPageContains("['.board-filter-frame','#tagbar','#count','.entitytagbar','.entitycollectionhead']")
        self.assertPageContains("scheduleStickySurfaces();")
        # 照片墙没有视频排序语义，切换后直接渲染照片，不复用作品头。
        self.assertPageContains("if(media==='photos'){renderPhotoWall(kind,name,filters,entityPhotos);return}")

    def test_entity_profile_uses_display_aliases_not_search_identity_aliases(self):
        self.assertPageContains("(d.display_aliases||[]).length")
        self.assertPageLacks("(d.aliases||[]).length?'别名")

    def test_the_agency_reads_as_identity_and_leads_to_its_own_page(self):
        """事务所是这个人签在谁名下，和别名、作品数是同一类事实，不是一条外链。

        它在账本里有实体时给出去处：那条链接落在站内的事务所资料页，不是某个片商的站。
        """
        self.assertCode("const agencyHome=d.agency||null;")
        self.assertPageContains("entityPath('agency',agencyName)")
        self.assertPageContains("${memberHtml}${agencyHtml}")
        # 没有对应实体时仍写名字，但不做成链接——那会通向一个不存在的页面。
        self.assertCode(":` · ${esc(agencyName)}`;")
        # 公司名自己说明了它是什么，这一行只出名字，不加类别名占横向空间。
        self.assertPageLacks("· 事务所 ${esc(agencyName)}")
        # 链接标签写的是域名归谁，不是事务所名。
        self.assertPageContains("linkHost(x.url)||x.label")

    def test_the_agency_page_reuses_the_entity_route_table(self):
        """实体本来就只有 kind 不同，事务所加进同一张表就有了 `/agencies/<名字>`。"""
        self.assertPageContains("agency:'agencies'")
        self.assertPageContains("agencies:'agency'")

    def test_portrait_pixels_do_not_size_the_face_frame(self):
        self.assertPageContains(".entityportrait img{position:absolute;inset:0;grid-area:auto;")
        self.assertPageContains("if(!matchesFaceSource(img.naturalWidth,img.naturalHeight,imgW,imgH)){")
        self.assertPageContains("img.style.objectPosition='50% 50%';")

    def test_the_agency_page_gets_the_same_loading_skeleton(self):
        self.assertPageContains("performers|creators|studios|agencies")

    def test_the_agency_page_counts_people_not_only_videos(self):
        """事务所名下的视频是成员拍的，「这家有几个人」才是它独有的读数。"""
        self.assertPageContains("位艺人")

    def test_the_agency_face_is_its_own_mark_not_a_members_frame(self):
        """代表作截图是某位成员某部片的画面，当不了一家公司的门面。"""
        self.assertCode("const company=kind==='studio'||kind==='agency';")
        self.assertCode("rep:company||!d.has_avatar?null:d.representative_asset_id,")
        self.assertCode("mark:kind==='agency'?d.mark_link_id:null,")
        # 取图链最后一环是官网那条链接的站点圆标。
        self.assertPageContains("mark?`/link-mark?id=${mark}`")

    def test_the_agency_page_opens_on_its_roster(self):
        """这一页要回答的是「这家签了谁」，所以进页面先摆艺人，视频是另一个视图。"""
        self.assertPageContains("let agencyRosterView='people',agencyRoster=[];")
        self.assertCode("  agencyRosterView='people';\n  const seq=++entityRequestSeq;")
        self.assertCode("if(entityViewNow(kind)==='people')renderAgencyRoster(roster);")

    def test_the_agency_roster_reuses_the_people_index_cell_and_layout(self):
        """名册和艺人索引摆的是同一格人，模板与版式设置都只有一份。"""
        self.assertPageContains("function personCellHtml(x,kind,countText){")
        # 索引页那批行的实体 id 叫 entity_id，名册那批叫 id，取图链只认一个。
        self.assertPageContains("const ref=x.entity_id||x.id;")
        self.assertCode(
            '<div class="igrid" data-layout="${peopleIndexLayout()}">${\n'
            "      people.map(x=>personCellHtml(x,'performer',x.n.toLocaleString())).join('')}</div>")
        # 名册占的是正文那一整块，所以这批人不再挤进「同台艺人」那排小圆头像。
        self.assertCode("const roster=kind==='agency'?(d.related_performers||[]):[];")
        self.assertCode("const related=roster.length?'':(d.related_performers||[]).map(")
        # 圆框越小越需要取景：一张 3762×2535 的封面塞进 44px 的圆里，几何居中给出的是
        # 封面正中那块版式，脸在不在里面全看运气。
        self.assertPageContains(
            "{id:x.id,hasImage:x.has_image,rep:x.has_avatar?x.rep:null,")
        self.assertPageContains(
            "         style:facePos(x.avatar_focus),focus:x.avatar_focus})}</span>")

    def test_a_company_cell_is_square_because_it_holds_a_mark_not_a_face(self):
        """3:4 是给脸留的形状，方标铺进去左右各被 `object-fit:cover` 裁掉四分之一。"""
        self.assertCode(
            "const cells=entityKind==='studio'||entityKind==='agency'?'company':'people';")
        self.assertPageContains('<div class="igrid" data-cells="${cells}" data-layout="${')
        self.assertPageContains(
            '.igrid[data-cells="company"][data-layout="big"] .icell .ring{aspect-ratio:1}')
        # 省下的高度换成宽度：同一屏里公司格比人格宽一档。
        self.assertPageContains('.igrid[data-cells="company"]{grid-template-columns:'
                                'repeat(auto-fill,minmax(180px,1fr))}')
        # 手机上 343px 只装得下一列 180px，整块卡横着铺满而标识还是那 70px；窄屏收回人格那一档。
        self.assertPageContains('  .igrid[data-cells="company"]{grid-template-columns:'
                                'repeat(auto-fill,minmax(150px,1fr))}\n}')

    def test_the_roster_and_the_media_keys_are_one_button_group(self):
        """三个键问的是同一件事——这一页现在显示什么，所以在同一组里、同一个尺寸。"""
        self.assertCode(
            "${peopleValue?control(peopleValue,peopleLabel,peopleCount,'user-round','people'):''}")
        self.assertPageContains("peopleValue:roster.length?'people':'',peopleCount:roster.length,")
        # 当前视图只有一个来源，按下哪个键、下面画什么都读它。
        self.assertPageContains("function entityViewNow(kind){return kind==='agency'"
                                "&&agencyRosterView==='people'&&agencyRoster.length")
        self.assertCode("button.setAttribute('aria-pressed',String(now===media));")
        # 没有照片的实体不出照片键，不是出一个按下去什么都不显示的键。
        self.assertPageContains("imageValue:photoCount?'photos':'',imageLabel:'照片',")
        # 标签筛的是作品，点了就回到视频视图，否则开关和内容各说各的。
        self.assertCode("agencyRosterView='videos';")

    def test_the_profile_rows_that_overflow_get_the_shared_drag_and_wheel(self):
        """同台艺人和标签这两行没有滚动条，不接拖动就是看得见够不着。"""
        self.assertPageContains("wireDrag($('#index').querySelector('.relatedpeople'));")
        self.assertPageContains("wireDrag($('#index').querySelector('.entitytags'));")
        # 外链那排窄屏下横滚，作品集表头窄屏下整条横滚，两处都是同一件事。390px 实测
        # 分别溢出 667px 与 338px，不登记就只有滚动条被藏掉、滚轮又是竖向的那种死局。
        self.assertPageContains("wireDrag($('#index').querySelector('.entitylinks'));")
        self.assertPageContains("wireDrag(section.closest('.entitycollectionhead')"
                                "||section.querySelector('.entitycollectionhead'));")
        # 横向滚动行里的开关不能被压扁。
        self.assertPageContains(".entitytags .iconswitch{flex:none}")

    def test_the_maker_index_switch_moves_between_two_routes(self):
        """厂牌出片、事务所出人，是两种实体：开关切的是路径，不是同一批数据再筛一次。"""
        self.assertCode("const MAKER_INDEX_KINDS=[['studios','厂牌','clapperboard'],"
                        "['agencies','事务所','briefcase']];")
        self.assertPageContains("function makerModeHtml(kind){")
        # 两条地址是两页，所以这一排是 Board 的下划线 Tabs；切的是地址，不是给这一批加筛选。
        self.assertCode("  return boardTabsHtml(MAKER_INDEX_KINDS.map(([value,label,symbol])=>({value,label,symbol})),\n"
                        "    {active:kind,attr:'data-index-kind',label:'公司类型',className:'indextabs'});")
        self.assertCode("$('#index').querySelectorAll('[data-index-kind]').forEach(b=>b.onclick=()=>{")
        self.assertCode("openIndex(b.dataset.indexKind,$('#iq').value.trim(),true)});")
        # 蓝线按下去当场就挪：换页时页头不重画，不改属性那条线就停在旧的一档上。
        self.assertCode("const selectTab=button=>button.closest('[role=\"tablist\"]')?.querySelectorAll('[role=\"tab\"]')\n"
                        "    .forEach(tab=>tab.setAttribute('aria-selected',String(tab===button)));")
        # Tabs 里的前置图标是这一排独有的：厂牌是场记板、事务所是公文包，指的都是对象。
        self.assertPageContains("${symbol?icon(symbol):''}${esc(text)}${badge}")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-tabs button svg{width:16px;height:16px;margin-right:6px;", board)
        self.assertIn(".indextabs{margin:0 0 22px}", board)
        # 两条索引地址都在路由表里，直达和刷新都得开得出来。
        self.assertPageContains("{match:'/studios',nav:'studios',title:'厂牌',")
        self.assertPageContains("{match:'/agencies',title:'事务所',")
        # 侧栏那一项进的是厂牌索引。
        self.assertPageContains("['studios','厂牌','clapperboard'],")

    def test_the_studio_index_wears_the_same_logo_the_profile_does(self):
        """538 个标识在盘上，索引页却格格首字母的话，这一屏读不出是哪些牌子。"""
        self.assertPageContains("const useLogo=!!logo;")
        self.assertPageContains(
            "const src=useLogo?`/logo?studio=${encodeURIComponent(logo)}&variant=${logoVariant}`")
        # 变体由调用点决定：小圆框和窄格子要方形图标，索引页那格要 large。
        self.assertPageContains("logo:logoName,logoVariant,focus:hint}")
        self.assertPageContains("bigMark?'large':'icon', company?null:x.avatar_focus)")
        # 取不到标识就退回实体图、再退到头像，和资料页大位同一条链。
        self.assertPageContains("const fallbacks=useLogo?[entitySrc,avatarSrc].filter(Boolean)")
        # 公司这一格不退到代表作截图，和它自己的资料页同一条判据。
        self.assertPageContains("const company=kind==='studio'||kind==='agency';")
        # 索引页那格由服务端的 has_logo 决定走不走这一环。
        self.assertPageContains(
            "x.has_avatar&&!company?x.rep:null, kind, x.mark, x.has_logo?x.k:'',")
        # 标识不是人脸，取景和摘取景那套只贴给实体图。
        self.assertPageContains("const framed=useEntity&&!useLogo;")

    def test_the_big_studio_slots_ask_for_the_sharpest_file_on_disk(self):
        """索引页的厂牌大格和资料页大位都要 `large`。

        后缀说明不了清晰度：Prestige 的 `icon` 只有 42 px、MOODYZ 的只有 64 px，
        摆进 180 px 的大格就是一团糊，而它们的裸文件分别有 632 px 和 403 px。
        """
        self.assertPageContains("bigMark?'large':'icon', company?null:x.avatar_focus)")
        self.assertPageContains(
            "logo:company&&d.has_logo?d.canonical_name:'',logoVariant:'large',")
        # 小位仍要方形小标：卡片角标和顶栏那排只有二十来像素，取原图只是白下载。
        self.assertPageContains('variant=icon"')

    def test_the_compact_studio_ring_keeps_the_square_mark(self):
        """圆框里摆完整字标，看得清的部分比方标还少。

        两个版式于是各取各的一档，换版式时原地把地址里的变体换掉：重拼列表会丢掉
        滚动位置和已经取回的图，而多取一次标识在本机服务端上不值钱。
        """
        self.assertPageContains("const bigMark=company&&peopleIndexLayout()==='big';")
        self.assertPageContains("function retargetCompanyMarks(root){")
        self.assertPageContains(
            "const next=src.replace(/([?&]variant=)[^&]*/,`$1${big?'large':'icon'}`);")
        # 已经回落到实体图的格子不在 `/logo` 这条链上，改它的地址只会指向不存在的东西。
        self.assertPageContains("if(!src.startsWith('/logo?'))return;")
        # 圆框不按原尺寸摆，上一档留在容器上的三个度量要跟着撤，否则字标的尺寸会
        # 继续压着方标。
        self.assertPageContains("ring.setAttribute('data-fit-native','mark');")

    def test_a_mark_smaller_than_its_frame_is_not_blown_up(self):
        """图比框还小就不拉伸：原尺寸居中，空出来的一圈用同一张图放大模糊补底。

        `large` 已经先挑过最清晰的一份，剩下的是本来就没有大图的厂牌——Ienergy 只有
        112 px。把它拉满 180 px 的格子只是把糊放大给人看。
        """
        self.assertPageContains("function fitNativeImage(img){")
        self.assertPageContains("const box=img.closest('[data-fit-native]');")
        self.assertPageContains("if(!box||!img.naturalWidth)return;")
        self.assertPageContains(
            "box.style.setProperty('--markw',small?width+'px':'100%');")
        # 只比框小一点点的照旧铺满：按原尺寸摆只会在四周留一圈七八像素的生硬窄边。
        self.assertPageContains("nativeImageFit(img.naturalWidth,img.naturalHeight,box.clientWidth,box.clientHeight,window.devicePixelRatio||1)")
        self.assertPageContains("box.dataset.nativeSmall=String(small);")
        self.assertPageContains("if(ring.dataset.nativeSmall==='true')return;")
        self.assertPageContains(
            "box.style.setProperty('--markbg',small?`url(\"${src}\")`:'none');")
        # 用到它的两个容器自己声明意图，JS 只负责量。
        self.assertPageContains("data-fit-native=\"${company?'mark':'portrait'}\"")
        self.assertPageContains('"entityportrait ${people?\'\':\'square\'}" '
                                'data-fit-native="${company?\'mark\':\'portrait\'}"')
        # 两处容器各自写着 width:100% 和 object-fit:cover，选择器压不过它们就白改。
        # 尺寸不写 auto：还没度量过的图按 auto 是 0×0，`loading="lazy"` 见到 0×0 就
        # 认定它不在视口里、永远不去取，图不来就没有 load，两边互相等着。缺省铺满。
        self.assertCode(
            '.icell .ring[data-native-small="true"] img,.entityportrait[data-native-small="true"] img{\n'
            "  width:var(--markw,100%);height:var(--markh,100%);margin:auto;object-fit:contain;\n"
            "  max-width:100%;max-height:100%;z-index:1}")
        self.assertPageContains('[data-fit-native]::before{content:"";position:absolute;'
                                'inset:-14%;z-index:0;')
        # 图不再铺满框，首字母垫底会从旁边露出来。
        self.assertPageContains(".icell .ring[data-fit-native]:has(img) .ini{display:none}")

    def test_the_company_index_layout_control_says_what_it_shows(self):
        """厂牌那一格摆的是方形标识，提示不能照艺人页写「竖幅头像」。"""
        self.assertPageContains(
            "const COMPANY_LAYOUTS=[['big','大图 · 完整标识','maximize'],"
            "['compact','紧凑 · 圆形标识','layout-grid']];")
        self.assertCode(
            "function indexLayoutOptions(kind){\n"
            "  return kind==='studios'||kind==='agencies'?COMPANY_LAYOUTS:PEOPLE_LAYOUTS;\n"
            "}")
        # 档位仍是同一个设置值，分开的只有说法。
        self.assertPageContains(
            "allowedSetting(appSettings.peopleLayout,PEOPLE_LAYOUTS.map(([k])=>k),'big')")

    def test_the_index_count_skeleton_is_no_wider_than_its_answer(self):
        """索引页这一枚等的是「118 项」。150px 那条灰条长过答案，读着像还没回完。"""
        self.assertPageContains(".index .ihead .countskeleton{width:54px}")

    def test_the_maker_index_switch_and_the_tag_scope_switch_are_the_same_tabs(self):
        """厂牌／事务所与本地／在线都是页面级切换，同一排 Tabs、同一个类名；页头里没有
        自绘的开关底板，样式表里也没有它的类名。

        标签页和艺人页的本地／在线问的是同一件事——这一屏摆的是本机的还是来源上的——
        所以拼法也只有一份：两页各写一份的话，哪天换了字形就只会换掉其中一页。
        """
        self.assertPageLacks("tagmodes")
        self.assertPageLacks("viewmodes")
        self.assertCode("function scopeTabsHtml(active,attr,label){\n"
                        "  return boardTabsHtml(INDEX_SCOPES.map(([value,text,symbol])=>({value,label:text,symbol})),\n"
                        "    {active,attr,label,className:'indextabs'});\n"
                        "}")
        self.assertCode("function tagScopeTabsHtml(){return scopeTabsHtml(tagIndexScope,'data-tag-scope','词表')}")
        self.assertCode("function performerScopeTabsHtml(){\n"
                        "  return scopeTabsHtml(performerIndexScope,'data-performer-scope','名册');\n"
                        "}")
        self.assertCode("${kind==='tags'?tagScopeTabsHtml():kind==='performers'?performerScopeTabsHtml()\n"
                        "      :MAKER_INDEX_KINDS.some(([key])=>key===kind)?makerModeHtml(kind):''}")

    def test_the_index_head_keeps_only_the_layout_switch(self):
        """页头里只剩版式切换一组控件，它站在自己那块底板上、28px 高。"""
        self.assertPageContains("border-radius:var(--surface-radius);background:var(--overlay-5)}")
        self.assertPageContains(".iconswitch label{position:relative;display:inline-grid;"
                                "width:34px;height:28px;")
        self.assertPageContains("      ${people?peopleLayoutButtons(kind):''}\n")

    def test_entity_name_picker_offers_only_this_entity_existing_names(self):
        # 候选取的是身份契约 `aliases`（完整），不是收窄过的展示别名：罗马字也是
        # 这个人真的用过的写法，用户想拿它当统称就该能选。
        self.assertCode("const nameChoices=[d.canonical_name,...(d.aliases||[])]")
        self.assertCode(
            ".filter((option,index,all)=>option&&all.indexOf(option)===index);")
        self.assertPageContains('data-namepick-toggle aria-haspopup="menu"')
        self.assertPageContains('role="menuitemradio"')
        self.assertPageContains('aria-checked="${option===d.canonical_name}"')

    def test_entity_name_picker_is_there_even_for_someone_with_one_name(self):
        """只剩一个名字的人最需要补一个：图库按名字存图，少一个写法就少一批图。

        菜单恒在，末尾那一项才是添别名的入口；它不在「挑一个当统称」之列，所以是
        `menuitem` 而不是 `menuitemradio`。
        """
        self.assertCode('const namePick=`<div class="namepick" data-namepick>')
        self.assertPageContains('role="menuitem" data-namepick-alias')
        self.assertCode("menu.querySelector('[data-namepick-alias]').onclick=async()=>{")
        # 添别名写的是 `entity_alias`，跟在已有名字里挑统称是两个端点。
        self.assertCode("const alias=payload=>api('/api/entity-alias',")
        self.assertCode("onConfirm:()=>alias({alias:field.value.trim()})});")
        # 撤销只给自己添的那几个，服务端按来源守这条线。
        self.assertCode("form.dialog.querySelectorAll('[data-alias-drop]')")
        self.assertCode("wireNamePicker(kind,d.canonical_name,d.user_aliases||[]);")

    def test_entity_name_picker_reuses_the_shared_anchored_menu(self):
        self.assertPageContains("const anchored=wireAnchoredMenu(mount,toggle,menu);")
        self.assertPageContains('<div class="popmenu npmenu"')

    def test_an_open_anchored_menu_yields_to_the_settings_panel_and_to_its_neighbours(self):
        """开着的锚定弹层，点设置或点它那片祖先里别的控件，都要收掉。

        「点到别处就关」不能只按 `mount` 之外算，而 mount 是定位用的那一片祖先：配色弹层
        给的是侧栏底部那一条，媒体库弹层给的是整个抽屉——设置钮和侧栏里每一枚控件都在
        里面，于是点它们全算内点，弹层就挂在设置面板旁边不走。mount 缩到触发钮也不行，
        定位要按它算。判据因此改成「点的是不是这枚菜单自己的东西」。
        """
        self.assertPageContains("if(openedMenu.menu.contains(target)"
                                "||openedMenu.toggle.contains(target))return;")
        self.assertPageContains("if(openedMenu.mount.contains(target)"
                                "&&!(target instanceof Element&&target.closest(clickable)))return;")
        # 触发钮自己那一份要单独放行：它的 click 处理器停的是冒泡，这个监听在捕获阶段，
        # 停不掉——少这一句的话点开的同一下就被关回去了。
        self.assertPageContains("openedMenu=next?{mount,menu,toggle,setOpen}")
        # 设置那一屏盖住整页，进来第一件事就是收掉还开着的那一个。补在这里而不是逐个
        # 入口上：设置能从侧栏的钮、弹层底部的「详细设置」和快捷键三处进来。
        self.assertCode("closeAnchoredMenu();\n    settingsRequestedSection=section;")

    def test_anchored_menu_fits_the_room_it_has_instead_of_covering_its_toggle(self):
        # 资料页的统称菜单挂在标题上，上方只有一条顶栏的距离、下方也未必够高。
        # 两侧都放不下时压到宽的那一侧、内部滚，不横跨触发钮。
        self.assertCode("const naturalHeight=menu.scrollHeight+menu.offsetHeight-menu.clientHeight;")
        self.assertCode("const downward=under>=naturalHeight||under>=over;")
        self.assertCode(
            "const height=Math.min(naturalHeight,Math.max(downward?under:over,0));")
        self.assertCode("menu.style.maxHeight=height+'px';")
        self.assertCode(
            "menu.style.top=(downward?anchor.bottom+8:anchor.top-8-height)+'px'")
        # 可用上沿是固定顶栏的下缘，不是视口顶端。
        self.assertCode(
            "const viewportTop=()=>8+(parseFloat(getComputedStyle(document.documentElement)")
        self.assertCode(".getPropertyValue('--topH'))||0);")
        self.assertPageContains(
            "dismissMenu(menu,()=>{menu.style.left='';menu.style.top='';menu.style.maxHeight='';")

    def test_menus_open_and_close_with_the_boardui_dropdown_motion(self):
        """全站的下拉面板一个开合动效：boardui menu-styles.ts 的 150ms ease-out，透明度、
        scale .95 与 2px 模糊一起进出（证据登记在 docs/BOARD_UI.md）。

        进场由 Board 层 CSS 按 `:not([hidden])` 起；退场得等动画放完再 hidden，所以每个
        面板的关闭都走 `dismissMenu`，它读到 animation-name 为 none（旧界面、减少动态
        效果）就当场藏。开着没开着由 wireAnchoredMenu 自己记，不再看 `hidden`：退场那
        150ms 里 hidden 还是 false。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("@keyframes board-menu-in{from{opacity:0;transform:scale(.95);filter:blur(2px)}}", board)
        self.assertIn("@keyframes board-menu-out{to{opacity:0;transform:scale(.95);filter:blur(2px)}}", board)
        self.assertIn(":is(.popmenu,.context-card,.board-library-menu,.searchmenu,.tagpicker):not([hidden])"
                      "{animation:board-menu-in .15s ease-out backwards;transform-origin:top left}", board)
        self.assertIn(":is(.popmenu,.context-card,.board-library-menu,.searchmenu,.tagpicker).leaving"
                      "{animation:board-menu-out .15s ease-out forwards}", board)
        # 缩放原点跟着开的方向：向上开从下沿、侧开从左沿。
        self.assertIn(":is(.popmenu,.context-card,.board-library-menu)[data-placement=top],.sidebaraddmenu.sidebaraddmenu{transform-origin:bottom left}", board)
        self.assertIn(".board-library-menu[data-placement=right]{transform-origin:left}", board)
        self.assertNotIn("board-library-in", board, "媒体库菜单没有自己单独的一份动画")
        self.assertCode("menu.dataset.placement=downward?'bottom':'top';")
        self.assertCode("export function dismissMenu(menu,finish){")
        self.assertCode("if(getComputedStyle(menu).animationName==='none'){done();return}")
        self.assertCode("export function presentMenu(menu){\n  leavingMenus.delete(menu);menu.classList.remove('leaving');\n"
                        "  if(menu.hidden)playUiSound('whoosh');\n  menu.hidden=false;\n}")
        self.assertCode("let open=false;")
        self.assertCode("return {setOpen,isOpen:()=>open};")
        # 进场起手是 scale(.95)，定位量框只能读 offsetWidth。
        self.assertCode("const anchor=toggle.getBoundingClientRect(),width=menu.offsetWidth;")
        self.assertCode("event.stopPropagation();setOpen(!open)")
        # wireAnchoredMenu 之外自己开合的四个面板也从同一个口进出。
        self.assertPageContains("if(menu)dismissMenu(menu,()=>{menu.innerHTML=''});")
        self.assertPageContains("innerWidth-menu.offsetWidth-8")
        self.assertPageContains("function hideSearchMenu(){dismissMenu($('#searchMenu'))}")
        self.assertPageContains("if(menu.innerHTML)presentMenu(menu);else hideSearchMenu();")
        self.assertPageContains("const closeAddMenu=()=>{if(!addMenu)return;dismissMenu(addMenu);")
        self.assertPageContains("if(opening)presentMenu(addMenu);else dismissMenu(addMenu);")
        self.assertPageContains("const closePicker=()=>{dismissMenu(picker);")
        self.assertPageContains("plus.onclick=()=>{presentMenu(picker);")
        self.assertPageLacks("$('#searchMenu').hidden=true")

    def test_board_batch_three_aligns_ranks_buttons_and_the_sidebar_switcher(self):
        """管理页标题四种布局都对齐 1120；
        主按钮与 Board 按钮同一副 36px 盒子；批量条隐藏键真的隐藏、回收站键用 error 渐变；
        复核页宽度与内容列同宽、分类栏留在原地；通知的状态圆用 lucide circle-alert；
        侧栏切换器是 32px 圆标识加名字加箭头，悬停外描一圈线，收起键只有 20px 高。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".geist-fieldset-footer>a,.geist-fieldset-footer>button).primary{box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:4px;height:36px;min-height:36px;padding:8px 12px;border-radius:10px;font:var(--board-body-medium);", board)
        self.assertIn("body .review{width:100%;max-width:var(--board-content);margin:0 auto;box-sizing:border-box}", board)
        self.assertIn("body .review .reviewcontrols{position:static;", board)
        self.assertIn(".closestage,.closestage:hover{background:rgba(0,0,0,.6);color:#fff}", board)
        self.assertIn("body .batchbar button[hidden],body .batchbar button.danger[hidden]{display:none}", board)
        self.assertIn("body .batchbar button.danger{", board)
        # 这一颗只是不在上面那份尺寸名单里，面色跟站内每一颗危险键同一份，见
        # `test_the_danger_tier_has_one_face_and_crossfades_into_its_hover`。
        self.assertIn("height:36px;min-height:36px;padding:8px 12px;border-radius:10px;font:var(--board-body-medium)}", board)
        self.assertIn(".board-sidebar-head #brandHome::before{content:'';position:absolute;inset:-5px -6px;border:2px solid var(--color-border-button-default);border-radius:999px;", board)
        self.assertIn(".board-sidebar-head #brandHome .mark{width:32px;height:32px;border-radius:50%;background:var(--color-background-tertiary-default)}", board)
        self.assertIn(".drawer .board-sidebar-head #filterBtn{width:20px;height:20px;padding:0;background:none;box-shadow:none}", board)
        self.assertIn(".drawer:not(.open) .board-sidebar-head #filterBtn{width:36px;height:20px}", board)
        self.assertIn(".cleanupgrid>.board-processing-skeleton{grid-column:1/-1;display:grid;grid-template-columns:1fr auto;align-items:center;min-height:114px}", board)
        self.assertPageContains("${icon(alert?'circle-alert':'check')}")
        self.assertPageContains('<symbol id="i-circle-alert" viewBox="0 0 24 24">')

    def test_the_library_icon_choices_exist_on_the_server_and_in_the_sprite(self):
        """媒体库图标的 42 枚候选每一枚都在服务端白名单和雪碧图里。

        取值是雪碧图的字形名，服务端按 `peach.media_libraries.LIBRARY_ICONS` 校验：前端多出
        一枚，保存时被拒；雪碧图少一枚，格子里是空的。三份名单分属 Python、TSX 与 HTML，
        只有这里能同时读到。格子的排法与选择流程由 vitest 断言。
        """
        picker = (Path(__file__).resolve().parents[1]
                  / "frontend/src/react/settings/library-icon-picker.tsx").read_text(encoding="utf-8")
        choices = re.findall(r"\['([a-z0-9-]*)', ?'([^']+)'\]", picker.split("LIBRARY_ICON_CHOICES = [", 1)[1].split("] as const", 1)[0])
        self.assertEqual(len(choices), 42)
        from peach.media_libraries import LIBRARY_ICONS
        for key, _name in choices[1:]:
            self.assertIn(key, LIBRARY_ICONS)
            self.assertPageContains(f'<symbol id="i-{key}" viewBox="0 0 24 24">')

    def test_the_follow_list_is_one_card_and_its_checkboxes_draw_their_tick(self):
        """关注列表整段进框，和「添加关注」同一只卡；来源行是 boardui 的 CheckboxCard，勾选框照
        checkbox-glyph.tsx：未选 1px 边加 shadow-xs、悬停只深边线不换底，选中蓝渐变加内嵌高光，
        勾 200ms 从零画出。分区标题行里的视图开关与同排按钮同高，图标与 fbtn 的字形同粗。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertNotIn(".followmanage .fmain>.fsec:has(.fsources){background:none}", board)
        self.assertIn(".followmanage .fmain>.fsec:has(.fsources)>.fsechead{padding:20px 24px 8px}", board)
        self.assertIn(".followmanage .fsec:has(.board-follow-selection){padding:0;border-radius:18px;background:var(--ground);overflow:visible}"
                      ".followmanage .fsec>.board-follow-selection{padding:4px 24px 12px}", board)
        self.assertIn(".followmanage .fmain>.fsec>.fsources{padding:0 24px 24px;grid-template-columns:minmax(0,1fr);gap:16px}", board)
        self.assertIn(".followmanage .board-follow-list .fauthor{background:var(--color-background-primary-default);border-radius:var(--surface-radius);padding:16px}", board)
        self.assertIn(".followmanage .board-follow-list .fsource.frow{min-height:0;margin:0;padding:12px 20px 12px 16px;border:1px solid var(--color-border-button-default);"
                      "border-radius:10px;background:var(--color-background-primary-default);transition:background-color .15s ease,border-color .15s ease}", board)
        self.assertIn(".followmanage .board-follow-list .fsource.frow:hover{background:var(--color-background-primary-hover)}", board)
        self.assertIn(".followmanage .fsechead .iconswitch[data-board-segments]>label{width:34px;height:30px;border-radius:7px}", board)
        self.assertIn(".followmanage .fsechead .iconswitch svg{width:16px;height:16px;stroke-width:2}", board)
        self.assertIn("--color-border-checkbox-default:#d4d4d4;--color-border-checkbox-hover:#a3a3a3", board)
        self.assertIn("--color-border-checkbox-default:#404040;--color-border-checkbox-hover:#737373", board)
        self.assertIn(".pcheck:hover>span,label:hover>.pcheck>span{border-color:var(--color-border-checkbox-hover);background:var(--color-background-primary-default)}", board)
        self.assertIn(".pcheck input:is(:checked,:indeterminate)+span{border-color:transparent;background:var(--board-blue);"
                      "box-shadow:inset 0 2px 0 0 #ffffff40,inset 0 0 0 1px #3b82f6}", board)
        self.assertIn("@keyframes board-check-draw{from{stroke-dashoffset:23px}to{stroke-dashoffset:0}}", board)
        self.assertIn(".pcheck input:checked+span svg{animation:board-check-draw .2s cubic-bezier(.65,0,.35,1) forwards}", board)

    def test_the_board_layer_shares_one_tabs_segments_and_chart_motion(self):
        """管理页与首页工具栏的控件都用 Board 那一份：下划线 Tabs 的指示条会滑，
        证据切换与版式切换是同一枚分段滑块。

        随之对齐的还有：排序行里的分段控件与排序键同高（30px）；管理页标题只在 812px
        窄列页面居中，别处与面包屑同一条左边线；侧栏收起键 36px、10px 圆角；详情页门挡
        铺满播放器格、只圆左上角；首页女优与厂牌两排同一枚 34px 灰 Pill；沉浸模式的
        随机流不进脱盘来源的片子。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        controls = (Path(__file__).resolve().parents[1] / "frontend/src/board-controls.ts").read_text(encoding="utf-8")
        self.assertIn("const selector='.managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav)';", controls)
        self.assertIn("const selector='.iconswitch,.insightswitch,"
                      ".follow-workspace-switch';", controls)
        self.assertIn("wireBoardSegments(root);wireBoardTabs(root)", controls)
        self.assertIn(".insightswitch[data-board-segments]{position:relative;display:inline-flex;align-items:center;gap:2px;padding:4px;"
                      "border:0;border-radius:10px;background:var(--color-background-tertiary-default);box-shadow:none}", board)
        # 浮层上的分段器滑块就是整枚选项：30px 见方、8px 圆角，跟旁边那块滑动玻璃同一副尺寸。
        self.assertIn(".board-filter-frame.board-filter-frame .iconswitch[data-board-segments]>label,\n"
                      ".entitytagbar.entitytagbar .iconswitch[data-board-segments]>label,\n"
                      ".entitycollectionhead.entitycollectionhead .iconswitch[data-board-segments]>label"
                      "{height:30px;min-height:30px;width:30px;padding:0;border-radius:8px}", board)
        self.assertNotIn("{padding:3px;border-radius:8px;gap:2px}", board)
        # 横滚容器会裁掉滑块与玻璃的落影：上下各留 14px 再用负外边距收回，行高不变。
        self.assertIn(".count .sorts,.entitycollectionhead .sorts{padding:14px 2px;margin-block:-14px}", board)
        # 下划线只归管理导航与设置分区；两套证据的切换是分段控件，判据在
        # test_the_two_bodies_of_evidence_switch_as_a_segmented_control。
        self.assertIn(".insightpanel>header h3,.insightcopy>span{margin:0;font:var(--board-heading);color:var(--color-text-primary)}", board)
        self.assertIn("body :is(#manageTitle,#manageCrumb,#manageLede){max-width:var(--board-content);width:100%;margin-left:auto;margin-right:auto}", board)
        self.assertIn(".drawer .board-sidebar-head #filterBtn{border-radius:0;color:var(--color-text-secondary);", board)
        self.assertIn(".stage .vwrap{border-radius:var(--surface-radius) 0 0 0}", board)
        self.assertIn(".stage .vwrap>.gate{height:100%;aspect-ratio:auto;border-radius:inherit}", board)
        self.assertIn(".idface:not(:has(img)){background:color-mix(in srgb,var(--color-text-primary) 10%,var(--color-background-primary-default));", board)
        self.assertIn(".cleanupgrid>.board-processing-skeleton>.geist-fieldset-footer{background:none}", board)
        # 首页顶上两排：女优是竖排人像格（48px 圆头像在上、名字在下），厂牌是 40px 的灰 Pill（28px 圆标识在左）。
        # 关注页那两排是同一个控件，所以每条规则都把它们一起写进选择器。
        self.assertIn("#tiers .av,:is(.followauthors,.followworks) .av{display:flex;flex-direction:column;align-items:center;gap:6px;width:76px;max-width:none;height:auto;padding:6px 4px;border-radius:12px;text-align:center}", board)
        self.assertIn("#tiers .brandpill,:is(.followauthors,.followworks) .brandpill{display:inline-flex;align-items:center;gap:8px;width:auto;max-width:none;height:40px;padding:6px 12px 6px 6px;border-radius:12px;text-align:left}", board)
        self.assertIn("#tiers .av .ring,:is(.followauthors,.followworks) .av .ring{width:48px;height:48px;", board)
        self.assertIn("#tiers .brandpill .mk,:is(.followauthors,.followworks) .brandpill .mk{width:28px;height:28px;", board)
        self.assertIn("#tiers .av .nm,:is(.followauthors,.followworks) .av .nm{display:block;max-width:100%;font:var(--board-caption);", board)
        self.assertPageContains("const list=d.items.filter(x=>x.cost!=='metered' && x.duration && !sourceOffline(x.location));")

    def test_toasts_leave_like_a_boardui_notification(self):
        """Board 层的 Toast 退场按 Notification 的 exit：180ms ease-out，下沉 8px、缩到 .96、
        模糊 3px。高度收成 0 留着，栈里上面那条才是滑下来而不是跳下来。"""
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".toast.leaving{transform:translateY(8px) scale(.96);filter:blur(3px);"
                      "transition:height .18s ease-out,margin .18s ease-out,padding .18s ease-out,"
                      "border-width .18s ease-out,opacity .18s ease-out,transform .18s ease-out,filter .18s ease-out}", board)
        self.assertPageContains("item.classList.add('leaving');setTimeout(()=>item.remove(),200)")

    def test_the_countdown_bar_only_asks_whether_the_toast_expires(self):
        """倒计时条的判据只有一个：这条 toast 会不会自己消失。

        这一行排在 `root.prepend` 前面，所以它是整条 toast 的单点。判据里多搭一个
        标识符，那个标识符哪天没了定义就是 ReferenceError，回执连挂上去都挂不上去：
        写操作成功了、页面上什么都不出现，看起来像调用点忘了发回执。
        """
        self.assertPageContains("const progress=()=>{if(timeout){"
                                "const bar=document.createElement('span');")

    def test_anchored_menu_closes_on_page_scroll_but_not_on_its_own(self):
        # 菜单装不下时本来就要在内部滚；捕获阶段的 scroll 连它自己的也收得到。
        self.assertCode(
            "if(!(event.target instanceof Node&&menu.contains(event.target)))setOpen(false)")

    def test_entity_name_picker_keeps_a_touch_target_on_phones(self):
        """命中区 44px，画出来仍是 32px：那一层伸出去的方块不着墨。

        这枚开关紧挨着名字。把画出来的方块也撑到 44px，一屏里最先看见的就成了它，
        而它说的只是「这个人还有别的名字」。菜单项不在此列，行本来就该有 44px 高。
        """
        self.assertPageContains(".npbtn{position:relative}")
        self.assertPageContains(
            '.npbtn::after{content:"";position:absolute;top:50%;left:50%;'
            "width:44px;height:44px;")
        self.assertPageContains("transform:translate(-50%,-50%)}")
        self.assertPageLacks(".npbtn{width:44px;height:44px}")
        # 两个类一起写：任何一条 `.某工具条 button` 都比单类祖先更具体，会把菜单里的
        # 每一行也画成工具条按钮，连这条 44px 命中区一起压掉。
        self.assertPageContains(".npmenu button,.popmenu.gselectmenu button{min-height:44px}")

    def test_entity_name_picker_writes_through_the_server_before_repainting(self):
        self.assertCode("const rename=(from,to)=>api('/api/entity-name',")
        self.assertCode(
            "{method:'POST',body:JSON.stringify({kind,name:from,canonical:to})});")
        self.assertCode("onConfirm:()=>rename(current,chosen)});")
        self.assertCode("if(!confirmed||!result?.changed)return;")
        # 撤销是一次真实写回，不在本地把标题改回去。
        self.assertCode("await rename(result.canonical_name,result.previous_name);")

    def test_entity_name_picker_confirms_and_names_both_writings_first(self):
        # 换统称会重写整条实体的扁平投影，写之前必须让用户看见换成什么、旧写法去哪。
        self.assertCode("const {confirmed,result}=await confirmModal({")
        self.assertCode("title:'更改统称',")
        self.assertCode(
            "body:`「${chosen}」将成为这条实体的规范名，「${current}」留作别名。`")
        self.assertCode("+'作品上的署名、搜索和标签都会跟着改写。',")
        # Geist 的判据：主按钮是与标题同一个动词的「动词+名词」，成功回执共用那个动词。
        self.assertCode("confirmLabel:'更改统称',")
        self.assertCode("actionReceipt(`已把统称更改为 ${result.canonical_name}`,{undo:async()=>{")
        # 弹层顶上来之前先把菜单收掉，否则它固定在视口里会浮在遮罩上。
        self.assertCode("anchored.setOpen(false);")

    def test_confirm_modal_is_one_shared_component_on_a_native_dialog(self):
        # 焦点陷阱、Escape、背景 inert 和关掉后归还焦点都由原生 <dialog> 给。
        self.assertCode("export function confirmModal({title,body,confirmLabel,")
        self.assertPageContains("dialog.showModal();")
        self.assertPageContains('dialog.className=\'geist-modal\';')
        self.assertPageContains("dialog.setAttribute('aria-labelledby',titleId);")
        # 标题与正文是数据，走 textContent，不进 innerHTML。
        self.assertPageContains("dialog.querySelector('h3').textContent=title;")
        self.assertPageContains(
            "dialog.querySelector('.geist-modal-body p').textContent=body;")
        # 遮罩上的点击落在 <dialog> 自己身上；这个动作可撤销，允许点外面关掉。
        self.assertCode(
            "dialog.addEventListener('click',event=>{if(event.target===dialog&&!busy&&!danger)dialog.close()});")

    def test_confirm_modal_keeps_a_failed_write_in_place_with_its_reason(self):
        # 忙态落在主按钮上，不落在已经收起来的菜单项上。
        self.assertPageContains("setActionBusy(accept);")
        self.assertCode("settled={confirmed:true,result:await onConfirm()};")
        self.assertCode(
            "failure.innerHTML=noteHtml(error.message||'操作未完成',{variant:'error'});")
        self.assertPageContains("setActionBusy(accept,false);")
        # 取消、Escape 和点遮罩都走同一条出口，一律回 confirmed:false。
        self.assertCode("resolve(settled||{confirmed:false});")

    def test_confirm_modal_matches_the_measured_geist_modal(self):
        # 实测 https://vercel.com/geist/modal（2026-09-04），见
        # docs/reference-snapshots/vercel-geist-modal-measured.md。
        self.assertPageContains(
            ".geist-modal{box-sizing:border-box;width:min(540px,calc(100vw - 20px));")
        # <dialog> 的 UA 样式带一条更小的 max-width，窄屏上会把卡片再压窄十几像素。
        self.assertPageContains("max-width:min(540px,calc(100vw - 20px));max-height:min(800px,80vh);")
        self.assertPageContains("border-radius:var(--floating-radius);")
        # 遮罩纯黑不带模糊：Geist 的 backdrop 没有 blur。
        self.assertPageContains(".geist-modal::backdrop{background:#0009;opacity:0;")
        self.assertPageLacks(".geist-modal::backdrop{background:#000a;backdrop-filter")
        self.assertPageContains(
            ".geist-modal-body{padding:20px;font-size:var(--fs-md);line-height:20px;")
        self.assertPageContains(
            ".geist-modal-body h3{margin:0;font-size:var(--fs-xl);line-height:26px;"
            "font-weight:600;color:var(--ink)}")
        # 操作条粘在底、两端对齐；取消在左，主动作在右。
        self.assertPageContains(
            ".geist-modal-footer{position:sticky;bottom:0;display:flex;"
            "justify-content:space-between;gap:16px;")
        self.assertPageContains(".geist-modal-footer>div{display:flex;gap:16px}")
        # 两个键都走全站唯一那份 Geist Button，不另起一套尺寸。
        self.assertCode('<div><button type="button" class="geist-button" data-modal-cancel>')
        self.assertCode(
            '<div><button type="button" class="geist-button primary" data-modal-confirm>')
        # 手机上按本项目的 44px 命中区放大。
        self.assertPageContains(
            ".geist-modal-footer .geist-button{min-height:44px;padding:0 14px}")

    def test_entity_name_picker_marks_the_current_name_with_fill_and_a_check(self):
        self.assertPageContains(
            '.npmenu button[aria-checked="true"]{background:var(--hover);color:var(--ink)}')
        self.assertPageContains('.npmenu button[aria-checked="true"] svg{visibility:visible}')
        # 未选中那几行也占着勾的位置，切换时文字不横向跳。
        self.assertPageContains("visibility:hidden")
        # 窄屏的资料页整块居中，flex 标题行得自己居中。
        self.assertPageContains(".entitytitle{justify-content:center}")

    def test_jav_cards_prefer_the_canonical_performer_over_legacy_creator_text(self):
        self.assertPageContains("const primaryCreator=it.is_jav&&performer?'':it.creator")
        self.assertPageContains("const identity=primaryCreator?{kind:'creator',name:primaryCreator}")
        self.assertPageContains("const coStarred=performers.length>1&&!primaryCreator")
        self.assertPageContains("return (it.is_jav&&performer?performer:it.creator)||performer")

    def test_jav_detail_keeps_official_tags_visually_neutral(self):
        # 「日文标题优先」这条已经改成拿真输入跑真函数验收，见
        # test_web_js.test_official_title_prefers_the_japanese_one。
        self.assertPageContains('wrap.innerHTML=visible.map(t=>`<span class="detailtag">')
        self.assertPageLacks("<small>官方</small>")
        self.assertPageLacks(".detailtag.official{")
        # 左半边点下去是按这个标签筛选，和右边的删除键一样得有悬停反馈；
        # 它没有选中态，照孤立按钮的写法抬填充。
        self.assertPageContains(".detailtag .tagfilter:hover{background:var(--hover);color:var(--ink)}")
        self.assertPageContains("const byDisplay=new Map()")
        self.assertPageContains("foldName(t.k)===key&&foldName(previous.k)!==key")

    def test_drawer_filters_follow_entity_and_detail_context(self):
        self.assertPageContains('function buildDrawerNavigation()')
        self.assertPageContains('syncSidebarSurface(scroll,key)')
        self.assertCode('surfaceEpoch++;\n  barsRequestSeq++;')
        self.assertPageContains('key=surfacePath()+location.search')
        self.assertPageLacks("api('/api/follow/tags?limit=30')")
        self.assertPageContains('renderFollowDrawer(visible.flatMap(group=>followCollectionItems(group)))')
        self.assertPageContains('renderFollowDrawer([item])')
        self.assertPageContains("if(!sidebarHasCatalogContent(location.pathname))return;")
        # 实体页 facets 必须按当前实体取数；详情页则按单个作品取数，不能继续复用首页全库。
        self.assertPageContains("facetParams.set('scope_kind',context.kind)")
        self.assertPageContains("facetParams.set('scope_name',context.name)")
        self.assertPageContains("facetParams.set('id',String(context.id))")
        self.assertPageContains("barsContext={type:'item',id:it.id,filters:returnBars?.type==='entity'")
        self.assertPageContains("detailReturnBarsContext=returnBars")
        # 实体筛选走实体集合自己的更新路径；旧实现调用 load(true) 会把 #index 隐藏并重建首页。
        self.assertPageContains("updateEntityCollection(barsContext.kind,barsContext.name,filters,true)")
        self.assertPageContains("function commitContextFilter(mutate)")
        self.assertPageContains("const search=entityFilterSearch(filters)")
        # 没有数据的区块不渲染，画幅也必须来自 scoped API，不能硬画横屏/竖屏两个按钮。
        self.assertPageContains("sidebarSectionHtml(t,b,x,cat)")
        self.assertPageContains("const chips=(items,key,multi,limit)=>items.length?")
        self.assertPageContains("chips(facetData.orientations,'orient')")
        self.assertPageLacks("chips([{k:'竖屏'},{k:'横屏'}],'orient')")

    def test_changing_a_filter_takes_the_reader_back_to_the_top_of_the_new_list(self):
        """换筛选就回到新名单的开头，等数据的那一下铺骨架。

        第一屏是这份名单的开头。人停在半路时原地换掉，屏幕上那一段跟他刚才在读的既不连
        也不相干；新名单还常比旧的短，浏览器只好把他钳到别处，落点跟按之前不是同一个地
        方。滚动锚定这时也在帮倒忙：骨架换成卡片那一下它会照新内容再推一次，把正在走的
        这段滚动顶开，所以这一路上先关掉它。已经在顶上就什么都不做，减少动态效果时直接
        到位，不走那段滑行。

        资料页那一份名单同样要换掉：数字在转圈、底下几十张却还是上一次的答案，等的这一
        下人读到的是一份跟头上的筛选对不上的列表。
        """
        self.assertPageContains("function commitContextFilter(mutate){\n  scrollFilteredViewToTop();")
        self.assertPageContains("  if(scrollY<=0)return;")
        self.assertPageContains("  root.classList.add('refiltering');")
        self.assertPageContains("addEventListener('scrollend',done);")
        self.assertPageContains(
            "scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});")
        self.assertIn("html.refiltering{overflow-anchor:none}", stylesheet_source())
        # 目录那边的骨架由 load(true) 铺；资料页的集合自己铺一份同样的。
        self.assertCode("  if(grid){grid.innerHTML=pageSkeletonHtml('正在读取作品',\n"
                        "    {cards:true,className:'catalog-skeleton postercard-skeleton'});fitSkeleton(grid)}")
        self.assertPageContains("  if(more)more.hidden=true;")

    def test_adding_a_filter_only_changes_the_list_underneath(self):
        """点一条筛选，动的只有底下那份名单；上面那几排原地改按下态。

        整块重画的代价不是耗时，是把人读到一半的东西换掉：实测那排女优已经横着续到六十
        枚、停在第 600 像素上，重画一次退回二十四枚、滚回起点，标签条同理。而他按下这一
        下要看的是底下那份名单变成什么样，上面那几排跟这件事无关。

        侧栏那些数字仍要跟着当前筛选走，不刷新就是一列对不上的数；但刷新只改数字，整段
        重画会合上人展开的那几组、把这一列滚回顶上，那正是要避免的事。数请求回得慢，中
        途再按一条就有两份答案在路上，序号只认最后发的那次。
        """
        self.assertPageContains("function applyFilterStateInPlace(filters){")
        self.assertCode(
            "  mutate(state);route(homePath());\n"
            "  applyFilterStateInPlace(state);refreshFacetCounts(barsContext);\n"
            "  load(true);")
        self.assertCode(
            "    applyFilterStateInPlace(filters);refreshFacetCounts(barsContext);\n"
            "    updateEntityCollection(barsContext.kind,barsContext.name,filters,true);return")
        # 三处按下态：筛选条的药丸、卡片和资料页上的标签、侧栏那些芯片。
        self.assertPageContains(
            "    b.setAttribute('aria-pressed',String(tagPressed(filters.tag,b.dataset.tag))));")
        self.assertPageContains(
            "    b.setAttribute('aria-pressed',String(tagPressed(filters.tag,b.dataset.entityTag))));")
        self.assertPageContains("$('#drawer').querySelectorAll('.chip[data-key]')")
        # 轨道上那截填充由 oninput 算，改 value 不会自己触发。
        self.assertPageContains("    durMin.dispatchEvent(new Event('input'));")
        self.assertPageContains("  renderCombo();")
        self.assertCode(
            "  const seq=++facetCountsSeq;\n"
            "  const [facetData]=await getBarsData(context);\n"
            "  if(seq!==facetCountsSeq)return;")
        self.assertPageContains("  $('#drawer').querySelectorAll('.chip[data-key] .n').forEach(el=>{")
        # 从详情回到列表是换语境，不是换一条筛选：那几排本来就要照新语境重新画。
        detail = self.app_js.split("if(barsContext.type==='item'){", 1)[1]
        self.assertIn("buildBars();load(true);return", detail[:detail.index("\n}")])

    def test_the_intersection_bar_grows_into_place_instead_of_shoving_the_page(self):
        """交集条从无到有是长出来的：高度从 0 走到 auto，二百来毫秒。

        它一出现就把底下整块推下四十像素，而人这时正盯着底下那份名单换成新的。留着空位
        等它是另一种代价——一屏没有任何筛选时头顶白占一条。`interpolate-size` 是这段动画
        的前提，缺了它高度直接跳到终值。
        """
        base = stylesheet_source()
        self.assertIn("overflow:hidden;interpolate-size:allow-keywords;height:auto;", base)
        self.assertIn("transition:height .22s cubic-bezier(0,0,.2,1),"
                      "margin-bottom .22s cubic-bezier(0,0,.2,1)}", base)
        self.assertIn("@media(prefers-reduced-motion:reduce){.combo{transition:none}}", base)

    def test_the_processing_notice_stays_put_while_the_list_underneath_changes(self):
        """整理提示讲的是库里那趟后台任务，换一条筛选不该让它塌一下再撑回来。

        它跟着每次取数卸了再挂：卸载会把画过的内容清掉，重挂又要一整趟请求才画得回来。
        实测点一枚标签，底下整块先往上跳 62px，二十来毫秒后落回原处——那一下比它要说
        的那句话显眼得多。目录页之间它一直挂着，自己在轮询库那边的进度；离开目录页才
        收起，那些页面本来就不该有它。

        真该出现的那一次仍是从无到有：要不要画得等 `/api/library-processing` 回话。
        所以照交集条那样长出来，高度从 0 走到 auto。容器里常驻一个 `.peach-react`
        宿主（React 根挂在它里面），「有没有东西」就看那一层空不空。
        """
        self.assertPageContains("  if(!isCatalogPath(path))unmountIsland($('#libraryProcessingNotice'));")
        self.assertCode(
            "  if(reset&&isCatalogPath(location.pathname)&&!islandMounted($('#libraryProcessingNotice')))\n"
            "    void mountIsland('library-processing',$('#libraryProcessingNotice'),"
            "{toast,mode:'notice'},{isCurrent:()=>surfaceCurrent(surface)});")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("#libraryProcessingNotice{overflow:hidden;interpolate-size:allow-keywords;height:auto;",
                      board)
        self.assertIn(
            "#libraryProcessingNotice:empty,#libraryProcessingNotice:has(>.peach-react:empty)"
            "{height:0}", board)
        self.assertIn(
            "#libraryProcessingNotice:not(:empty):not(:has(>.peach-react:empty))"
            "{margin:0 0 22px}", board)
        self.assertIn("@media(prefers-reduced-motion:reduce){#libraryProcessingNotice{transition:none}}",
                      board)

    def test_changing_pages_unmounts_whatever_owns_the_management_body(self):
        """管理区正文那个容器上挂着的东西，换页时跟着页面一起走。

        React 档的页面是一棵自己管取数的根：不卸掉它，离开之后那棵根还活着，有轮询的
        页面照着原节律继续敲库。`claimSurface` 是所有页面共同经过的换页点，卸载落在这里
        才不会漏掉新迁过来的那一页；没挂过东西的容器 `unmountIsland` 直接返回。
        离场之后还有第二道闸：取数落地时 island 按 `isCurrent` 决定不画。
        """
        self.assertPageContains("  unmountIsland($('#stats'));")

    def test_the_top_discovery_bar_and_the_drawer_read_one_scope(self):
        """顶部发现栏按「换一批」的种子抽样，抽屉那一列读同一份 facets。

        口径只有一个，就是当前这张表面的。详情浮窗不另取一趟作品口径：它盖住整页，
        那两排头像、标签条和抽屉在它开着的时候一格都看不见，取回来只把列表那份缓存
        挤掉，关掉时整排头像连 `<img>` 一起重建。
        """
        self.assertPageContains("const pickedTags=seededSample(tagPool,TAGS_FIRST,`tags:${state.seed||''}`);")
        self.assertPageContains("+sec('内容标签',chips(facetData.tags,'tag',false,30)")
        self.assertPageLacks("if(context.type==='item'&&!topTags.length)")
        self.assertPageLacks("const recommendationFacets=await api('/api/facets'")

    def test_a_truncated_sidebar_list_says_so_at_its_own_end(self):
        """侧栏名单没列完时，末尾那枚箭头接着摊开，再按一下把整组放回去。

        它说的是「这张名单还没完」——要跟名单断掉的地方在一起。挂在标题上时，人得先把
        这一列读到底、再抬头回到标题去找它；而标题那一行的职责是开合这一组，旁边多一个
        按钮，点哪儿会展开就成了两件要分辨的事。

        身量取排名卡上那枚展开药丸：40×20 居中，14px 箭头随 `aria-expanded` 翻面。摊开
        之后按下去收的是整组——名单已经到最长，把它退回二十几条只是换一个断点，人还站
        在同一列读不完的东西前面。
        """
        self.assertPageContains(
            "scopedCreators.length>26?sidebarMoreHtml('creator','创作者'):''")
        self.assertPageContains("facetData.tags.length>30?sidebarMoreHtml('tag','内容标签'):''")
        self.assertPageContains(
            "<button class=\"sidemore\" data-more=\"${key}\" aria-expanded=\"false\""
            " aria-label=\"展开全部${group}\">"
            "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-chevron-down\"/></svg></button>")
        # 展开与收起是同一枚按钮的两面，不另开一处入口。
        self.assertPageContains("group.querySelector('.chips').outerHTML=chips(src,k,false,expanded?lim:999);")
        self.assertPageContains("b.setAttribute('aria-expanded',String(!expanded));")
        self.assertPageContains("if(expanded)group.querySelector('.board-section-toggle').click();")
        # 摊开那一下和分组 Collapse 走同一份高度过渡，不是整段名单瞬间铺出来。
        self.assertPageContains("if(!expanded&&body)growCollapse(body,before,()=>toggle.getAttribute('aria-expanded')==='true');")
        self.assertPageContains("export function growCollapse(body,start,isCurrent=()=>true){")
        # 摊开的内容全在按下的这个点以下，这一列停在哪儿归人自己管。
        self.assertPageContains("const scroller=$('#drawerScroll'),keep=scroller.scrollTop;")
        self.assertPageContains("bind();hold();requestAnimationFrame(hold);});")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(
            ".drawer .board-sidebar-body .sidemore{display:grid;place-items:center;"
            "width:40px;height:20px;margin:6px auto 2px;", board)
        self.assertIn(".drawer .board-sidebar-body .sidemore[aria-expanded=true] svg{transform:rotate(180deg)}",
                      board)
        self.assertNotIn(
            ".drawer .sec:has(.board-section-toggle[aria-expanded=false]) [data-more]", board,
            "它落在组的正文里，折叠时跟正文一起收走，不必单独藏")

    def test_the_discovery_tag_row_changes_with_the_batch_seed(self):
        """标签条跟着「换一批」的种子换成员，同一批内不动。

        `/api/facets` 给 44 个内容标签，第一屏只放得下 26 个，取前 26 的话后面 18 个
        永远排在这一屏之后；顶部三层本来就跟着同一个 state.seed 换人，标签条留在原地
        等于「换一批」只换了半个顶部。抽样不动顺序——条上照旧按数量从多到少读下来，
        换的是成员，不是位置。
        """
        self.assertPageContains("const pickedTags=seededSample(tagPool,TAGS_FIRST,`tags:${state.seed||''}`);")
        self.assertPageContains("+appliedTags.concat(pickedTags).map(tagPillHtml).join('');")
        self.assertPageLacks("topTags.slice(0,26)",
                             "取前 26 会把这一批的成员钉死在数量榜的头部")
        # 续在后面的是这一批之外的那些，抽样只决定开头露谁，不重排后面的数量序。
        self.assertPageContains("const pickedKeys=new Set(pickedTags.map(row=>row.k));")
        self.assertPageContains(
            "wireRowPaging($('#tagScroll'),tagPool.filter(row=>!pickedKeys.has(row.k)),tagPillHtml,wireTagPills);")
        # 同一个种子给同一套成员，所以这一批内翻页和刷新都不会让标签跳动。
        self.assertPageContains("const seededSample=(rows,count,seed,key=row=>row.k)=>{")
        self.assertPageContains("  if(rows.length<=count)return rows;")
        self.assertPageContains("  return rows.filter(row=>picked.has(key(row)));")
        # 种子随机只有一份算法，关注页的随机发现共用它。
        self.assertPageContains("const seededRank=(seed,value)=>{")
        self.assertPageContains("const followDiscoveryRank=value=>seededRank(followDiscoverySeed,value);")

    def test_the_applied_tags_sit_at_the_head_of_the_filter_row(self):
        """加上去的标签排在标签条最前面，按加的先后。

        这一排横着滚，一枚生效的标签落在第三十位跟没画出来是一回事：要撤掉刚加的那
        一条，人得先把整排推过去把它找回来。抽样也不该再抽它——它已经在屏幕上了，
        再抽一次就是同一个词出现两遍。

        名单里还可能有榜上没有的：标签是从卡片或详情页点进来的，`/api/facets` 的前
        几十名里不一定有它。缺的那几枚只有 key，标签条上照样要画出来。
        """
        self.assertPageContains("const appliedKeys=tagList(filterState.tag);")
        self.assertPageContains("const byTagKey=new Map(topTags.map(row=>[row.k,row]));")
        self.assertPageContains("const appliedTags=appliedKeys.map(k=>byTagKey.get(k)||{k});")
        self.assertPageContains("const tagPool=topTags.filter(row=>!appliedKeys.includes(row.k));")
        self.assertPageContains("+appliedTags.concat(pickedTags).map(tagPillHtml).join('');")

    def test_every_filter_row_tells_how_much_is_behind_each_tag(self):
        """标签后面带上这个标签下有多少，首页和资料页同一个口径。

        这一排每一枚都是可加可不加的筛选。加上去还剩几屏，是点之前就该看得到的——
        没有这个数，一排词读起来全都一样重，点进去才知道其中一半只剩三五条。

        生效的标签不一定在这一批抽样里，那时只有键、没有行，不印数字：印 0 会说成
        「这个标签下什么都没有」，而它此刻正筛着一屏内容。
        """
        self.assertPageContains("const tagPillHtml=t=>filterChipHtml(tagLabel(t.k),{attr:'data-tag',value:t.k,\n"
                                "    selected:tagPressed(filterState.tag,t.k),"
                                "count:t.n==null?undefined:t.n.toLocaleString()});")
        self.assertPageContains("filterChipHtml(tagLabel(x.k),{attr:'data-entity-tag',value:x.k,"
                                "selected:tagPressed(filters.tag,x.k),count:x.n.toLocaleString()})")

    def test_the_count_behind_a_tag_reads_as_a_footnote_not_part_of_the_name(self):
        """计数与标签之间要有间隔，字号和颜色也各降一档。

        同字号同色贴在一起时「巨乳63」读成一个词，那个数看着像这条标签自己就叫这个
        名字。间隔只能由 CSS 给：`.pill` 是 flex 容器，标签与计数之间写一个空格文本
        节点不参与布局，量出来仍然是零——所以模板里也不留那个空格，免得两处各存一份
        真相而其中一份从来没生效过。

        玻璃那一层要自己降档。flat 层降的是 `--muted`，而在 Board 里 `--muted` 和
        `--ink-2` 都映射到 `--color-text-secondary`，是同一个值；照搬过去，计数和标签
        仍然一样亮。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains('aria-pressed="${selected}">${esc(label)}${count==null?\'\':'
                                '`<span class="${esc(countClass)}" data-count-badge="${esc(value)}">'
                                '${esc(count)}</span>`}')
        self.assertPageContains(".pill .n{margin-left:7px;color:var(--muted);font-size:var(--fs-xs);"
                                "font-variant-numeric:tabular-nums}")
        self.assertPageContains('.pill[aria-pressed="true"] .n,.pill:hover .n{color:var(--ink-2)}')
        self.assertIn(".board-filter-frame.board-filter-frame .pill .n{margin-left:6px;font-size:11px;\n"
                      "  color:color-mix(in srgb,var(--glass-text) 55%,transparent)}", board)
        self.assertPageLacks(".followfilters .pill .n{margin-left:5px;color:inherit}",
                             "跟着标签同色同字号就是没有区分，而且只管关注页一处")

    def test_the_refresh_key_keeps_redrawing_until_the_bars_land_too(self):
        """忙态动效归「换一批」这一层，不挂在计数行上。

        网格和顶部三层一起换，两边耗时不一样。挂在计数行的 aria-busy 上时，网格
        先到就被 renderCount 摘掉，标签条还在等的那段时间按钮已经不动了。顶部三层
        与标签条不铺骨架：它们此刻有内容在屏幕上，撕成灰条再填回去比直接换掉更
        晃眼，骨架留给从无到有的首屏。
        """
        self.assertPageContains("  document.body.classList.add('refreshing');")
        self.assertPageContains("  try{await Promise.all([load(true),buildBars()])}")
        self.assertPageContains("  finally{document.body.classList.remove('refreshing')}")
        self.assertPageContains("body.refreshing #batchAction svg,")
        # 标签条和顶部三层照旧留着旧内容等新内容，不进骨架。
        self.assertPageLacks("tagbarSkeleton", "有内容在屏幕上时不铺骨架")

    def test_large_collections_render_in_bounded_batches(self):
        self.assertPageContains("p.set('limit','48')")
        self.assertPageContains("if(offset)p.set('count','0')")
        self.assertPageContains('class="entitymore"')
        self.assertPageContains("const indexLimit=people?120:180")
        self.assertPageContains('class="indexmore"')
        self.assertPageContains("adsBatch.items.slice(pageOffset,pageOffset+appSettings.batchSize)")
        self.assertPageContains("p.set('limit',appSettings.batchSize)")
        self.assertPageContains("const pageOffset=reset?0:offset+appSettings.batchSize")
        self.assertPageContains("if(!reset)p.set('count','0')")
        self.assertPageContains("enabled:()=>!listLoading&&$('#stats').hidden&&$('#index').hidden")
        self.assertPageContains("indexRequestSeq")
        self.assertPageContains("barsRequestSeq")
        self.assertPageContains("async function getBarsData(context=barsContext)")
        self.assertPageContains("Date.now()-barsDataAt<30000")
        self.assertPageLacks("p.set('limit','120')")
        # 观察器收进了共用的 wireLoadMore（见 test_infinite_scroll_is_wired_through_one_helper）；
        # 这里要保证的是实体合集确实接上了它，而不是自己又写一套。
        self.assertPageContains("read:signal=>fetchEntityItems(kind,name,filters,entityCollectionPage.items.length,signal)")
        self.assertPageContains("more.hidden=!entityCollectionPage.has_more")

    def test_mix_card_is_not_seeded_by_the_card_it_sits_next_to(self):
        """Mix 卡片插在第 8 位，seed 就不能再取本批第一张。

        旧写法是 `visible.find(有署名)`。馆藏里几乎每条都有 creator，那个
        `find` 实际上恒等于 `visible[0]`，于是 Mix 卡片总是顶着同屏第一张
        卡片的封面，看起来像渲染错了。它不是内容错（队列仍是 seed + related），
        错的只是代表图的选取，所以修在选 seed 这一步，不动队列。
        """
        self.assertPageContains("const MIX_SLOT=7;")
        self.assertPageContains("visible.slice(MIX_SLOT+8).find(named)")
        self.assertPageContains("||visible.slice(MIX_SLOT+1).find(named)")
        # 都没署名时宁可取末尾一张，也不回到第一张。
        self.assertPageContains("||visible[visible.length-1];")
        self.assertPageLacks(
            "visible.find(it=>it.creator||(it.performers||[]).length||it.studio)")

    def test_mix_card_flips_through_its_own_covers_on_hover(self):
        """悬浮 Mix 卡片翻动的是这个 Mix 里的封面，不是另做一套装饰动画。

        三件事必须同时成立：翻动的每一张和静止封面走同一个渲染函数（否则
        一翻就露出取景差别）；启动门槛和悬停预览完全一致，并能被
        `releaseHoverPreviews` 统一收掉；相关作品只取一次，悬浮预取后点开
        Mix 不再发第二个请求。
        """
        self.assertPageContains('<div class="mixfaces" data-mix-faces hidden></div>')
        self.assertPageContains(".mixface.on{opacity:1;z-index:2;transform:none;transition:none}")
        self.assertPageContains(".mixface.off{opacity:0;z-index:3;transform:translateY(-11%)")
        self.assertPageContains("function wireMixFlip(el,seedId){")
        self.assertPageContains("wireMixFlip(el,seedId);")
        # 翻动的封面必须 eager：它们插进的是一个 hidden 容器，lazy 图没有布局盒
        # 就不发请求，实测除第一张外四张全部 naturalWidth=0，一翻就是黑屏。
        self.assertPageContains(".map(x=>mixFacePoster(x,layout,true));")
        self.assertPageContains("const load=eager?'eager':'lazy';")
        # 能不能画出图只有一个判据，seed 选择和翻动共用。分开写就会翻出
        # 或选中一张「无预览」：非 JAV 模式下 `has_cover` 并不代表卡片会画封套。
        self.assertPageContains("function mixHasPicture(it,layout){")
        self.assertPageContains(".filter(x=>mixHasPicture(x,layout)).slice(0,MIX_FLIP_FACES)")
        self.assertPageContains("const named=it=>mixHasPicture(it,layout)&&(it.creator")
        self.assertPageContains("||visible.slice(MIX_SLOT+1).find(it=>mixHasPicture(it,layout))")
        self.assertCode('''loading="${eager?'eager':'lazy'}"''')
        self.assertPageContains(
            "if(selectMode||censorOn()||window.__scrolling||reduceMotion())return;")
        self.assertPageContains(
            "el.addEventListener('mouseleave',stop);" + chr(10)
            + "  el._stopHover=stop;")
        self.assertPageContains("const mixRelatedCache=new Map();")
        # 第一张不能等满一个完整间隔：那会把「鼠标停下到有反应」拉到两秒。
        self.assertPageContains(
            "lead=setTimeout(()=>{step();cycle=setInterval(step,MIX_FLIP_MS)},MIX_FLIP_LEAD_MS);")
        self.assertPageContains(
            "Promise.all([api('/api/item?id='+seedId),mixRelated(seedId)])")
        # 队列长度不能被悬浮预取剪短：两边用同一个 limit。
        self.assertPageContains("api('/api/related?id='+seedId+'&limit=28')")

    def test_multipart_cards_flip_through_their_parts_on_hover(self):
        """分卷卡悬浮翻各卷画面，版次卡继续走分段视频预览。

        有码、中字、无码是同一段画面的几个来源，翻过去前后两张几乎一样，看着像图
        卡住了；各卷是不同画面，翻动才说明这张卡代表不止一条。分卷卡因此也不带
        倒计时环和快退／快进那三颗——它们要操作的 `video.hv` 在这种卡上不存在。
        各卷只取一次，悬浮预取后点开分卷队列不再发第二个请求。
        """
        self.assertPageContains(
            """${parts?'<div class="mixfaces" data-mix-faces hidden></div>':''}""")
        self.assertPageContains("function wirePartFlip(el,it){")
        self.assertPageContains("if(it?.part_group)wirePartFlip(el,it);")
        self.assertPageContains(
            "else if(it&&(!it.medium||it.medium==='video'))wireHover(el,it);")
        # 和 Mix 共用同一套时序、门槛和面渲染，不另写一份动效。
        self.assertPageContains("wireStackFlip(el,async()=>{")
        self.assertPageContains(".filter(x=>mixHasPicture(x,layout)).slice(0,MIX_FLIP_FACES)")
        # 第一张是卡片自己的静止封面，翻进来的才不会跳取景。
        self.assertPageContains("return [it,...items.filter(x=>x.id!==it.id)]")
        self.assertPageContains("const tools=parts?laterTool:")
        self.assertPageContains("const partGroupCache=new Map();")
        self.assertPageContains("try{group=await partGroup(seedId)}catch(_e)")
        self.assertPageLacks("const group=await api('/api/parts?id='+seedId);")

    def test_stacked_cards_pile_upward_and_keep_the_row_bottom_aligned(self):
        """Mix、分卷、版次和关注合集的叠层往上溢出，卡片本体不为它留白。

        留白（padding-top）会把整张卡压低并加高，同一行里这几种卡的封面和
        下面的文字就比邻居矮一截。四种卡共用同一套叠层规则，不各调一份。
        """
        self.assertPageLacks(".mixcard,.partcard{padding-top:7px}")
        self.assertPageLacks(".followitem.collection{padding-top:7px}")
        self.assertPageContains(
            ".mixstack::before,.partstack::before{inset:0 12px 8px;transform:translateY(-7px)")
        self.assertPageContains(
            ".mixstack::after,.partstack::after{inset:0 6px 4px;transform:translateY(-4px)")
        # 密集模式给整个网格统一留 7px，那是所有卡片一起下移，不破坏平齐。
        self.assertPageContains('body[data-density="dense"] .grid>.card{padding-top:7px}')

    def test_follow_collections_flip_through_the_thumbs_they_already_have(self):
        """关注页的合集卡片和目录页的 Mix 用同一套翻动，不各写一份动效。

        时序、启动门槛和 `_stopHover` 收尾都在 `wireStackFlip` 里；关注页的
        几张缩略图卡片渲染时就在手上，悬浮不再为动画发一次请求。第一张是
        静止封面本身，翻起来才不会露出取景差别。
        """
        self.assertPageContains("function wireStackFlip(el,loadFaces){")
        self.assertPageContains("try{pool=await loadFaces()}catch(_e){return}")
        self.assertPageContains("function wireFollowStackFlip(card){")
        self.assertPageContains("wireStackFlip(card,async()=>urls.map(url=>")
        self.assertPageContains(
            "if(!card.dataset.flipWired){card.dataset.flipWired='1';wireFollowStackFlip(card)}")
        # 翻的必须是角标数的那一组，否则卡上写「9 个视频」翻的却是别处的图。
        self.assertPageContains(
            "const faceSource=embedded.length>1?embedded:"
            "(groupedVideos.length>1?groupedVideos:videos);")
        self.assertPageContains("const faceUrls=isMix?[...new Set([thumbUrl,...faceSource")
        self.assertPageContains(".filter(entry=>!imageView||entry.media_kind==='image')")
        self.assertPageContains(".map(entry=>entry.thumb_url)].filter(Boolean))].slice(0,MIX_FLIP_FACES):[];")
        self.assertPageContains(
            '${faceUrls.length>1?`<div class="mixfaces" '
            'data-mix-faces="${esc(JSON.stringify(faceUrls))}" hidden></div>`:\'\'}')
        # 遮住静止封面的底色跟着这张卡自己的底走：图片墙是浅底，视频卡是黑底。面板里每一张
        # 面也是 `.poster`，自带的黑底得一起换，否则浅底卡一悬浮留白就翻成黑的。
        self.assertPageContains(".followitem.imagecard :is(.mixfaces,.mixface .poster){background:var(--sunk)}")

    def test_follow_image_only_controls_are_scoped_and_reversible(self):
        self.assertPageContains('data-follow-images-only aria-pressed="${!!appSettings.followImagesOnly}"')
        self.assertPageContains('appSettings.followImagesOnly=!appSettings.followImagesOnly;saveSettings();syncPhotoWalls();')
        self.assertPageContains('.followphotowall[data-images-only="true"] .followitem :is(.meta,.badge,.mixbadge,.fstate){display:none}')
        self.assertPageLacks('data-photo-size')

    def test_mix_and_persistent_playlists_share_the_routed_side_queue(self):
        self.assertPageContains('class="card mixcard" data-mix-seed=')
        self.assertPageContains("cards.splice(MIX_SLOT,0,mixCardHtml(seed))")
        self.assertPageContains(".mixstack::before,.mixstack::after")
        # Mix 是同一网格里的同级卡片，JAV 大图不能让它单独掉回 16:9；有封面时
        # 也应和普通作品卡共用同一张官方封套，而不是永远显示视频九宫格。
        self.assertPageContains("? javArtwork(it,jav?layout:'small')")
        self.assertPageContains("const ar=jav&&layout==='big'?COVER_FRONT_RATIO:16/9;")
        self.assertPageContains('<div class="mixstack"><div class="pic" style="--card-ratio:${ar}">')
        self.assertPageContains("? javArtwork(it,jav?layout:'small')")
        self.assertPageContains("const thumb=mixFacePoster(it,layout);")
        self.assertPageContains('<span class="mixbadge">${icon(\'play\')}Mix</span>')
        self.assertPageContains("async function openMix(seedId,itemId=seedId,push=true,anchor=null)")
        self.assertPageContains("route(`/mix/${seedId}/${itemId}`)")
        self.assertPageContains('class="mixqueue"')
        self.assertPageContains('class="mixitem ${x.id===itemId?\'current\':\'\'}"')
        self.assertPageContains("data-queue-item")
        self.assertPageContains("if(!queueContext&&appSettings.relatedLimit>0)api('/api/related?id='")
        self.assertPageContains("async function openPlaylists(push=true)")
        self.assertPageContains("const surface=claimSurface('/playlists')")
        self.assertPageContains("async function openPlaylist(playlistId,itemId=null,push=true)")
        self.assertPageContains("route(`/playlists/${playlistId}/${chosen}`)")
        self.assertPageContains("action:'progress'")
        self.assertPageContains("action:'reorder'")
        self.assertPageContains("action:'remove'")
        self.assertPageContains("data-save-mix")
        self.assertPageContains("source_kind:'mix'")
        self.assertPageContains('id="addPlaylist"')
        # 一次能勾好几份列表：行前是勾选框，右下角那个保存才写库。
        self.assertPageContains("data-pick-playlist")
        self.assertPageContains("formModal({")
        self.assertPageLacks("class=\"playlistpickrow\"")
        self.assertPageContains("batchWithMix(d.items,isCatalogPath(decodeURIComponent(location.pathname))&&state.state!=='trash')")
        # 竖屏条只在首页出现。JAV 模式也排除：番号发行物是横版，竖屏是另一类内容，
        # 而主列表的 exclude_vertical 管不到这条——它是独立请求、独立插入的。
        self.assertPageContains("!isCatalogPath(decodeURIComponent(location.pathname))||javActive()||state.orient==='竖屏'")
        self.assertPageContains("||state.state==='ads'||state.state==='trash'")
        self.assertRoute('/trash', "section:'trash'", "openTrash(push)")
        self.assertPageContains("/api/trash/empty")

    def test_multipart_releases_use_a_distinct_group_card_and_queue(self):
        self.assertPageContains("function collapseMultipartItems(items)")
        self.assertPageContains("renderedPartGroups.clear()")
        self.assertPageContains("data-part-seed")
        self.assertPageContains('<span class="partbadge">${parts.count} 卷</span>')
        self.assertPageContains("async function openParts(seedId,itemId=seedId,push=true,anchor=null)")
        self.assertPageContains("api('/api/parts?id='+seedId)")
        self.assertPageContains("title:`分卷 · ${group.title}`")
        self.assertPageContains("route(`/parts/${seedId}/${chosen}`)")
        self.assertPageContains("queue.kind==='parts'?`${queue.items.length} 卷`")
        self.assertPageContains("queueContext.kind==='parts'?openParts")
        self.assertRoute('/parts/:seed/:item', "openParts(params.seed,params.item,push)")
        self.assertPageContains(".partstack::before,.partstack::after")
        self.assertPageLacks("Mix · ${group.title}")

    def test_filter_and_sort_rows_stay_visible_in_both_scroll_directions(self):
        self.assertPageContains("--filterH:58px")
        self.assertPageContains(".tagbar{position:sticky;top:var(--topH)")
        self.assertPageContains(".count{position:sticky;top:calc(var(--topH) + var(--filterH))")
        self.assertPageContains("border-bottom:1px solid transparent;background:transparent")
        self.assertPageContains("background:transparent;border-bottom:1px solid transparent")
        self.assertPageContains(
            ".tagbar.is-stuck,.count.is-stuck,.entitytagbar.is-stuck,.entitycollectionhead.is-stuck"
            "{background:color-mix(in srgb,var(--ground) 84%,transparent)"
        )
        self.assertPageLacks("color-mix(in srgb,#080A0D 84%,transparent)",
                             "吸顶条跟着 --ground 走，浅色主题下不许铺出一条黑带")
        self.assertPageContains("backdrop-filter:saturate(1.35) blur(16px)")
        self.assertPageContains("function updateStickySurfaces()")
        self.assertPageContains("css.position==='sticky'")
        self.assertPageContains("el.classList.toggle('is-stuck',stuck)")
        self.assertPageLacks(".tagbar.tuck")
        self.assertPageLacks("function onScrollFrame")
        self.assertPageContains(":root{--tile:168px;--topH:52px;--sortH:60px}")

    def test_mobile_count_and_sort_controls_share_one_scrollable_row(self):
        self.assertPageContains(".count{align-items:center;flex-direction:row")
        self.assertPageContains("overflow-x:auto;overflow-y:hidden;scrollbar-width:none")
        self.assertPageContains(".count>span:first-child{line-height:36px;white-space:nowrap}")
        self.assertPageContains(".count .sorts{width:max-content;margin-left:0;flex:0 0 auto;overflow:visible}")
        self.assertPageContains("flex:0 0 auto;white-space:nowrap")
        self.assertPageContains(".count .sorts button{min-height:36px}")
        # 这些行都没有滚动条（scrollbar-width:none），不登记拖动就只剩看得见够不着的半个按钮。
        # 筛选条里滚的那一层随宽度换：宽屏是右半截的标签，窄屏是连视图一起的 `.filterscroll`。
        # 两层都登记，少一层就会在某一个宽度上滚不动；登记在不滚的那层上是空转。
        self.assertPageContains("['#tagScroll','#tagbar .filterscroll','#nrow','#count']"
                                ".forEach(s=>wireDrag($(s)))")
        self.assertPageContains("document.querySelectorAll('.tier,.srow').forEach(wireDrag)")
        # 「接着看」每开一次详情就重建，启动时的登记落在旧节点上；推荐结果渲染完要当场再登记一次。
        self.assertPageContains("wireCards(n);wireDrag(n);});")
        self.assertPageContains(".nrow{display:flex;gap:11px;overflow-x:auto;overflow-y:hidden;overscroll-behavior-inline:contain;")
        # 同一个元素宽屏不溢出、窄屏才溢出，不判溢出就会在宽屏抢走滚轮和拖动。
        self.assertPageContains("event.button!==0||el.scrollWidth-el.clientWidth<=1")
        self.assertPageContains("Math.abs(event.deltaY)<=Math.abs(event.deltaX)||el.scrollWidth<=el.clientWidth")

    def test_entity_collection_posters_and_titles_open_item_details(self):
        self.assertPageContains('type="button" class="cardopenhit" data-open')
        self.assertPageContains('<button class="t cardtitle" data-open>')
        self.assertPageContains("const openCard=(id,anchor=el)=>miniplayerTakesCard(it)?miniplayerPlay(id):onClick?onClick(id,anchor):(it?.part_group")
        self.assertPageContains("if(e.target.closest('[data-open]')){e.stopPropagation();openCard(+el.dataset.id,el)")
        self.assertPageContains(".cardopenhit{position:absolute;inset:0;z-index:1")
        self.assertPageContains(".card>.pic,.card>.partstack,.card>.meta{position:relative;z-index:2}")
        self.assertPageContains("el.querySelectorAll('[data-open]').forEach(opener=>")
        self.assertPageContains("opener.dataset.openWired='1'")
        self.assertPageContains(".hovertools button{pointer-events:none")
        self.assertPageContains(".card.longhover .seektools button,.card:hover .later-tools button{pointer-events:auto}")
        self.assertPageContains("section.querySelector('h3').textContent=`视频 ·")
        self.assertPageLacks("的馆藏作品 ·")

    def test_hover_seek_controls_wear_the_watch_later_button_skin(self):
        """居中的快退／快进／全屏和右下角「稍后看」是同一种控件，只是尺寸不同。

        磨砂圆底、边框和悬停填充全部由 `.hovertools button` 一条规则给出，
        58px 圆配 34px 图标，与 36px 圆配 21px 图标同一个比例。
        秒数交给 `title`／`aria-label`，图标上不压数字。
        证据与「beeg 那一侧未取得」的结论见
        `docs/reference-snapshots/hover-seek-controls-user-screenshot.md`。
        """
        self.assertPageContains(
            ".hovertools button{pointer-events:none;width:58px;height:58px;border-radius:50%;"
            "border:1px solid rgba(255,255,255,.12);")
        self.assertPageContains("background:rgba(0,0,0,.24);color:#fff;backdrop-filter:saturate(180%) blur(12px);")
        self.assertPageContains(".hovertools button:hover{transform:scale(1.12);background:rgba(0,0,0,.34)}")
        self.assertPageContains(".hovertools.seektools button svg{width:34px;height:34px}")
        self.assertPageContains(".hovertools .laterbtn{width:36px;height:36px;padding:0;font-family:inherit}")
        self.assertPageContains(".hovertools .laterbtn svg{width:21px;height:21px}")
        # 这一层里没有第二套外观：不画底和边、靠投影描边的写法一处都不留。
        self.assertPageLacks(".hovertools.seektools button{border:0;background:none")
        self.assertPageLacks("filter:drop-shadow(0 1px 4px rgba(0,0,0,.6))")
        # 数字角标不在 DOM 里，样式也不留。
        self.assertPageLacks("<b>${appSettings.seekSeconds}</b>")
        self.assertPageLacks(".hovertools button b{")
        self.assertPageContains('title="后退 ${appSettings.seekSeconds} 秒"')
        self.assertPageContains('aria-label="前进 ${appSettings.seekSeconds} 秒"')

    def test_jav_titles_hide_media_suffix_and_emphasize_the_code(self):
        # 「后缀什么时候剥」「display_code 与 display_title 怎么取」「哪三个徽章算数」
        # 这些算法已经拆进 web/js/jav-title.js，改成拿真输入跑真函数验收，
        # 见 test_web_js.WebJsBehaviourTests。这里只留页面这一侧的契约：
        # 徽章的三种配色，以及卡片／详情／沉浸模式确实调了这两个函数。
        self.assertPageContains(".javedition.subtitle{color:var(--ink-2)}")
        self.assertPageContains(".javedition.uncensored{color:var(--meter)}")
        self.assertPageContains(".javedition.cracked{color:var(--drop)}")
        self.assertPageContains('<button class="t cardtitle" data-open>${shownTitle}</button>')
        self.assertPageContains("<span class=\"stitletext\" data-detail-title>${srcBadge(it.location,it.cost,'srcbig')}"
                                "${javTitleHtml(it)}")
        self.assertPageContains("$('#tokTitle').textContent=javDisplayName(it)")
        self.assertPageContains("<b data-middle-truncate>${esc(javDisplayName(x))}</b>")

    def test_remote_hover_previews_do_not_stream_full_media(self):
        self.assertPageContains("if(it.location!=='local')")
        self.assertPageContains("el.dataset.hoverMode=it.location==='local'?'video':'frames'")
        self.assertPageContains("function releaseHoverPreviews(root=document,except=null)")
        self.assertPageContains("releaseHoverPreviews(document,el)")
        self.assertPageContains("window.addEventListener('pagehide',()=>releaseHoverPreviews())")
        self.assertPageContains("if(document.hidden)releaseHoverPreviews()")
        self.assertPageContains("if(reset)releaseHoverPreviews($('#grid'))")
        self.assertPageContains("if(reset)releaseHoverPreviews($('#grid'))")

    def test_remote_hover_scan_is_an_overlay_so_every_jav_layout_has_it(self):
        """远端源的扫视图叠一层，不改任何已有 `<img>` 的 src。

        JAV 大图和小图版式里画面就是封面本身（`.poster.cover`），改它的 src 等于把封面
        当场换掉；按类名把封面排掉又等于这两种版式整个没有悬停预览——连 `.previewing`
        都不进，快退快进那三颗跟着永远不出现。叠一层对三种版式是同一条路。

        几何和本地视频的 `.hv` 逐字一致：不透明黑底加 contain。大图版式的容器是 0.75
        竖比例，16:9 的接触印相格子于是居中、上下留黑，这就是那一版式的预览外观。
        """
        self.assertPageContains("layer.className='hvframes';layer.alt=''")
        self.assertPageContains("pic.appendChild(layer)")
        self.assertPageLacks("pic.querySelector('.poster:not(.cover)')")
        self.assertPageContains("if(!it.has_thumb)return;")
        self.assertPageContains("if(layer){layer.remove();layer=null}i=4")
        # 卡片被重画过时旧元素上的 `_stopHover` 跟着旧 DOM 走了，只靠回调收不到
        # 留在画面上的扫视图，所以 release 还要按类名兜一遍。
        self.assertPageContains("root.querySelectorAll('img.hvframes')")
        css = stylesheet_source()
        self.assertIn("img.hvframes{position:absolute;inset:0;width:100%;height:100%;"
                      "object-fit:contain;", css)
        self.assertIn("background:#000;display:block}", css)
        # 待删卡片的灰化要连这一层一起，否则悬停时整卡「复活」成正常色。
        self.assertIn(".card.pending-delete .hvframes{", css)

    def test_the_next_frame_is_loaded_before_it_is_shown(self):
        """下一格先拉到手再换上去，没拉到就停在当前这格。

        直接把 src 指过去，图片在解码完成前是空的：网盘那边一格要几百毫秒，
        430 毫秒一跳的节奏下，看到的是一连串黑白闪烁。慢的时候少跳一格，比跳
        过去闪一下好。取图失败也要把闸放开，否则一次 404 之后这张卡再也不动。
        """
        self.assertPageContains("if(!layer||loading)return;")
        self.assertPageContains("pre.onload=()=>{if(layer){layer.src=pre.src;i=next}loading=false}")
        self.assertPageContains("pre.onerror=()=>{loading=false}")

    def test_detail_close_returns_to_the_collection_that_opened_it(self):
        self.assertPageContains("detailReturnPath='/'")
        self.assertPageContains("if(push)detailReturnPath=location.pathname+location.search")
        self.assertPageContains("const returnPath=detailReturnPath||'/',restoreSurface=detailReturnNeedsRestore")
        self.assertPageContains("if(restoreSurface)await restoreRoute()")

    def test_direct_detail_restores_the_home_list_and_uses_shared_dialog(self):
        self.assertPageContains("const needsReturnRestore=detailReturnNeedsRestore||(!push&&!returnSurfaceReady)")
        self.assertPageContains("function placeItemDetail(anchor,above=false)")
        self.assertPageContains('id="stage" aria-label="作品详情" hidden></dialog>')
        self.assertPageContains("if(stage.parentElement!==main)main.insertBefore(stage,combo);")
        self.assertPageContains("anchor.getBoundingClientRect().top+anchor.getBoundingClientRect().height/2>window.innerHeight/2")
        self.assertPageContains(".grid>.stage{grid-column:1/-1;width:100%;min-width:0}")

    def test_detail_dialog_uses_top_layer_and_preserves_list_position(self):
        """原生模态浮窗提供顶层、焦点与退出行为，列表不参与详情布局。"""
        self.assertPageContains("if(!stage.open)stage.showModal();")
        self.assertPageContains("  stageExit().then(()=>{\n"
                                "    disposeStage(false,false,{miniplayer:false});"
                                "route(detailReturnPath||'/');restoreRoute()});")
        self.assertPageContains("if(stage.open)stage.close();")
        self.assertPageContains("box.showModal();")
        self.assertPageContains("if(stage.open)stage.append(menu);")
        self.assertPageContains("max-height:calc(100dvh - 32px)")
        self.assertPageLacks("stage.scrollIntoView(")
        self.assertCode("buildBars();\n  scrollItemDetailIntoView();")

    def test_catalog_skeleton_collects_the_bottom_loading_dots(self):
        """一屏只能有一段等待态：铺骨架和收哨兵是同一件事的两半。

        `.claude/skills/peach-web-ui/SKILL.md`：同一次页面进入只呈现一段等待态。
        `#loadSentinel` 的 Loading Dots 说的是「上面已经有内容，还在往下接」，骨架说的是
        「等下会出现几张什么形状的卡」——目录 reset 时两段同时在场，而实际只有一次请求。
        收哨兵必须写在 renderCatalogLoading 里：各分支自己记得收的话，总有分支只做一半，
        垃圾文件那条就是这么补出来的。
        """
        body = self.app_js.split("function renderCatalogLoading(label='正在读取作品'){", 1)[1]
        body = body.split("\n}", 1)[0]
        self.assertIn("$('#loadSentinel').hidden=true;", body)
        self.assertLess(body.index("$('#loadSentinel').hidden=true;"),
                        body.index("setGridCards(pageSkeletonHtml"),
                        "哨兵要在骨架铺上之前收掉，别让 dots 和骨架同时存在一帧")
        # 目录这条链上收哨兵只有这一处：分支里再补一次就是又一个会漏掉的地方。
        ads = self.app_js.split("if(state.state==='ads'){", 1)[1].split("adsBatch=null;", 1)[0]
        self.assertNotIn("$('#loadSentinel').hidden=true", ads)
        boot = self.app_js.split("if(path==='/junk-files'){", 1)[1].split("return;", 1)[0]
        self.assertNotIn("$('#loadSentinel').hidden=true", boot)

    def test_page_loading_uses_one_structural_skeleton_phase(self):
        self.assertPageContains("function renderCatalogLoading(label='正在读取作品')")
        self.assertPageContains("setGridCards(pageSkeletonHtml(label,\n"
            "    {cards:true,className:'catalog-skeleton postercard-skeleton'}));")
        self.assertPageContains("count.setAttribute('aria-label',label);")
        self.assertPageContains(".grid>.skeletonpanel{grid-column:1/-1;width:100%;min-width:0}")
        self.assertPageContains("function renderInitialSurfaceLoading()")
        self.assertPageContains("const followSkeletonHtml=(label='正在读取关注内容')")
        self.assertPageContains('<div class="followhead"><h2 class="pagetitle">关注</h2></div>')
        # 第一次进这一页铺整张骨架；已经在页上、只是换一档筛选或排序的话，骨架只盖
        # 浮层下面那块列表——页头、两排头像和玻璃此刻就能给出最终样子，它们没在等。
        self.assertPageContains("placeholder:partial?'':renderForDetail?detailSkeletonHtml():followSkeletonHtml('正在读取关注内容')})")
        self.assertPageContains("const list=$('#stats').querySelector('.follow .followlist');\n"
                                "  const partial=!!list&&!list.closest('[data-skeleton]')&&!renderForDetail;")
        self.assertPageContains("list.outerHTML=pageSkeletonHtml('正在读取关注内容',\n"
                                "      {cards:true,className:'follow-content-skeleton postercard-skeleton'});")
        self.assertPageContains("pageSkeletonHtml('正在读取统计',{variant:'dashboard'})")
        self.assertPageContains(".skeletondashhero{min-height:330px;grid-template-columns:minmax(260px,36%) minmax(0,1fr)}")
        self.assertPageContains("if(!refine)showIndexLoading('正在读取'+(INDEX_TITLES[kind]||'标签'),kind,q)")
        self.assertPageContains("$('#loadSentinel').innerHTML=loadingDotsHtml('继续载入中…')")
        self.assertPageContains("pageSkeletonHtml('正在读取推荐',{cards:true,className:'related-skeleton'})")
        # 「接着看」没有内容就整块不出现：推荐条数设为 0 时不生成，取回空列表时整块拿掉。
        self.assertPageContains("${queueContext||!(appSettings.relatedLimit>0)?'':`<div class=\"next\"><h3>接着看</h3>")
        self.assertPageContains("if(!d.items.length){n.closest('.next')?.remove();return}")
        self.assertPageLacks("'<span class=\"empty\">暂无</span>'")
        self.assertPageLacks("count.innerHTML=`${spinnerHtml(label)}<span>载入中…</span>`")
        self.assertPageLacks("function showItemDetailLoading(anchor,above)")
        self.assertPageLacks("detailpending")
        self.assertPageLacks("showItemDetailLoading(origin,above)")

    def test_switching_an_index_tab_only_skeletons_the_content_below(self):
        """换一档词表或名册，骨架只盖下面那块内容。

        页头和筛选浮层此刻就能给出最终样子，它们从来没在等：整块重画的代价是过滤框
        连同里面的字和焦点一起被换掉，Tabs 那条蓝线从头起跑，浮层先消失再出现——换
        一次词表，上面两条全闪一遍。判据要两样都成立：外壳记的是同一个 kind，而且那块
        内容还在；资料页会把 `#index` 整个换掉，只看记号的话会往一个已经不存在的节点
        里塞骨架。
        """
        self.assertPageContains("const body=kind&&$('#index').dataset.indexShell===kind?$('#indexBody'):null;")
        self.assertCode("  if(body){\n"
                        "    const next=indexSkeletonHtml({kind,layout:peopleIndexLayout(),mode:tagIndexMode});\n"
                        "    if(skeletonKeyOf(body.innerHTML)!==skeletonKeyOf(next)){body.innerHTML=next;fitSkeleton(body)}\n"
                        "    return;\n"
                        "  }")
        # 记号跟着内容走：内容重画完才写，值不对下一次就整块重画。
        self.assertPageContains("$('#index').dataset.indexShell=kind;\n  wireIndexControls(kind);")
        # 蓝线按下去当场就挪——骨架键不变、页头不重画，不在这里改属性那条线会停在旧档上。
        self.assertPageContains("const selectTab=button=>button.closest('[role=\"tablist\"]')"
                                "?.querySelectorAll('[role=\"tab\"]')")

    def test_every_management_surface_paints_the_same_skeleton_on_boot_and_on_route(self):
        """整页刷新只能出现一段加载动画，不是先大布局骨架、再各页自己的加载态。

        深链启动和路由到位后各写各的占位时，`/data-cleanup` 刷新会先闪一张通用
        骨架、再换成 Loading Dots。占位只留一份定义、两处都从这里取；骨架带
        `data-skeleton` 身份，showManagementBody 认出屏幕上已经是同一张就不重画
        ——重画会换掉节点，shimmer 从头再放一遍，看上去就是同一段动画闪两次。
        """
        self.assertPageContains("const MANAGEMENT_PLACEHOLDERS={")
        self.assertPageContains("const managementPlaceholder=path=>")
        for path in ("'/stats'", "'/taste'", "'/data-cleanup'", "'/duplicates'",
                     "'/review'", "'/quality-goals'", "'/playlists'", "'/follow-manage'",
                     "'/configuration'", "'/activity'"):
            self.assertPageContains(f"  {path}:()=>", "占位没有收进唯一那份定义")
            self.assertPageContains(f"managementPlaceholder({path})", "路由没有取那份定义")
        # /resource-sync 只是数据管理页的锚点，启动占位得是数据管理那张。
        self.assertPageContains("'/resource-sync':()=>MANAGEMENT_PLACEHOLDERS['/data-cleanup']()")
        self.assertPageContains("stats.innerHTML=path.startsWith('/follow/item/')?detailSkeletonHtml():path.startsWith('/follow')&&path!=='/follow-manage'")
        self.assertCode('''data-skeleton="${esc(kind)}${className?`/${esc(className)}`:''}"''')
        self.assertPageContains(
            "const painted=$('#stats').querySelector('[data-skeleton]')?.dataset.skeleton||''")
        self.assertPageContains(
            "if(!next||next!==painted){$('#stats').innerHTML=placeholder;fitSkeleton($('#stats'))}")
        # 数据管理不在骨架之后再盖一层 Loading Dots：那就是第二段动画。
        self.assertPageLacks("loadingDotsHtml('正在读取数据管理状态…')")
        self.assertPageLacks(".cleanuploading")
        # 数据管理是一列 fieldset，骨架不能是三列海报网格。

    def test_follow_manage_skeleton_matches_its_single_column_sections(self):
        """关注管理的骨架是三个大区，不是六张 16:9 卡片。

        六张卡的网格说的是 feed 那种一屏同质内容（关注更新流、回收站）；关注管理
        是「添加关注 + 关注列表 + 凭据」一列三块，六张卡加载完整屏换掉，等于先给
        了一个假的结构预告。块数因此要可配，宽度也跟着 .followmanage 收到 812px。
        """
        self.assertCode(
            "'/follow-manage':()=>`<div class=\"follow\">${pageSkeletonHtml('正在读取关注管理',")
        self.assertPageContains("{cards:true,count:3,fill:false,className:'followmanage-skeleton'})}</div>`,")
        self.assertPageContains(
            "const pageSkeletonHtml=(label,{cards=false,className='',variant='',count,fill}={})=>")
        self.assertPageContains("skeletonHtml(label,{variant:variant||(cards?'cards':'panel'),className,")
        self.assertPageContains(
            "export function skeletonHtml(label='正在读取内容',{className='',variant='panel',count=6,fill=true,gridClass='',gridSize=''}={})")
        self.assertPageContains("?Array.from({length:Math.max(1,count)},")
        # 版式：一列对上 .followmanage，宽度也跟它一样是 812px 居中。
        self.assertPageContains(
            ".followmanage-skeleton>div{grid-template-columns:minmax(0,1fr);gap:16px;width:min(812px,100%)")
        self.assertNotIn("grid-area", self.page[self.page.index(".followmanage-skeleton>div{"):
                                                self.page.index(".followmanage-skeleton .skeletoncard em{")])
        # 第一块是那一行输入，不是带按钮的两行。
        self.assertPageContains(".followmanage-skeleton .skeletoncard:nth-child(1) b{height:38px}")
        # 头部条是框体不是待填内容：跟 .fsechead 一样 56px，不参与呼吸。
        self.assertPageContains(".followmanage-skeleton .skeletoncard i{aspect-ratio:auto;height:56px")
        self.assertPageContains("border-bottom:1px solid var(--border-10)}")
        # 关注更新流仍是同质卡片流，它那张骨架不受影响。
        self.assertPageContains("pageSkeletonHtml(label,{cards:true,className:'follow-content-skeleton postercard-skeleton'})")

    def test_loading_actions_are_inert_and_dimmed_without_losing_focus(self):
        """用户触发的等待态统一走 Geist loading button，而不是各页自造半套状态。"""
        self.assertPageContains("control.setAttribute('aria-busy','true')")
        self.assertPageContains("control.setAttribute('aria-disabled','true')")
        self.assertPageContains("control.removeAttribute('aria-disabled')")
        self.assertPageContains("wireBusyActions(document)")
        self.assertPageContains("event.stopImmediatePropagation()")
        self.assertPageContains('button[aria-busy="true"],[role="button"][aria-busy="true"]{')
        self.assertPageContains("cursor:wait!important;opacity:.55!important;filter:saturate(.35)")
        self.assertNotRegex(
            self.app_js,
            r"disabled\s*=\s*true;[^\n]{0,100}(?:setAttribute\('aria-busy'|setActionBusy)",
            "请求中的按钮必须保持可聚焦，不能再把 native disabled 和 busy 混用",
        )
        self.assertPageContains("setActionBusy(batch)")
        self.assertPageContains("setActionBusy(scan,busy)")
        self.assertPageContains("setActionBusy(btn)")
        # React 档里同一件事由 `busyProps()` 发：同样是 aria-busy 加 aria-disabled，
        # 按钮留在 tab 序列上。
        self.assertIn("{...busyProps(rowHandlers.busy)}",
                      (Path(__file__).resolve().parents[1]
                       / "frontend/src/react/follow-manage/source-list.tsx").read_text(encoding="utf-8"))

    def test_follow_separator_uses_the_same_border_token_as_tags(self):
        self.assertPageContains(".pill{flex:none;height:var(--filterItemH);padding:0 20px;border:1px solid var(--field-ring)")
        # 关注页的分隔线就是首页筛选条上那一道，不再自己画一份。
        self.assertPageContains(".sep{flex:none;width:1px;height:19px;background:var(--field-ring-hover)")
        self.assertPageLacks(".followfilters .sep{")

    def test_entity_profile_uses_logo_links_without_a_redundant_back_row(self):
        self.assertPageContains('class="entitylinkicon"')
        self.assertPageContains('class="entitylinklabel"')
        # favicon 取不到就把 <img> 摘掉，露出底下的 globe 图标；这条兜底由
        # image-fallback 的委托监听执行，不再给每个 .entityfavicon 各挂一个监听。
        self.assertPageContains('class="entityfavicon" src="${esc(linkMarkUrl(x))}')
        self.assertPageLacks(".entityfavicon').forEach(img=>img.addEventListener('error'")
        self.assertPageLacks('<span class="mono" style="color:var(--muted)">${labels[kind]||kind}资料页</span>')

    def test_studio_marks_fill_their_three_frames_with_cover(self):
        """厂牌标识文件是自带边距的不透明方图，三处取图位都把它铺满方框。

        边距烤在文件里（`peach.images.bake_square`）。页面再补 inset、padding 或
        换成 contain，就会在图自带的底之外多围出一圈框，三处还会各自不一致。
        """
        self.assertPageContains(
            ".brandpill .mk img{position:absolute;inset:0;width:100%;height:100%;\n"
            "  object-fit:cover;display:block}")
        # 厂牌识别色照原样出图：滤镜一挂，同一张标识在三处就是三个颜色。
        self.assertPageLacks("filter:saturate(.72) brightness(.84)")
        self.assertPageContains(
            ".idface img{position:absolute;inset:0;width:100%;height:100%;"
            "object-fit:cover;display:block}")
        self.assertPageContains(
            ".entityportrait img{position:absolute;inset:0;grid-area:auto;width:100%;height:100%;object-fit:cover;display:block")
        self.assertPageLacks(".idcell.logo .idface img{")
        self.assertPageLacks('style="width:100%;height:100%;object-fit:contain"')

    def test_no_image_asks_for_a_studio_mark_without_naming_the_studio(self):
        """`src="/logo"` 这种形态一定取不到图：`/logo` 不带 studio 就是 404。

        它没有别的症状——那个位置只是永远空着，而 DevTools 的 Name 列只显示路径
        末段，一整排 `logo` 看起来都像裸路径，肉眼分不出真裸的那一个。所以逐处扫
        `src`：厂牌标识的地址必须带上 studio，也必须带上 variant（哪个位置要哪份图
        是另一条契约，见 `test_studio_icon_variants`）。
        """
        marks = re.findall(r'src="(/logo[^"]*)"', self.page)
        self.assertTrue(marks, "页面里应当仍有厂牌标识取图位")
        for url in marks:
            with self.subTest(url=url):
                self.assertTrue(
                    url.startswith("/logo?studio="),
                    f"厂牌标识取图位没写 studio，这个请求必然 404：{url!r}")
                self.assertIn("variant=", url, f"缺 variant：{url!r}")

    def test_every_studio_mark_waits_until_the_logo_is_known_to_exist(self):
        """没装标识就一个 `<img>` 都不输出，不许靠 404 再把图换成首字母。

        三处取图位无条件出图的代价是：首页顶栏一排 30 个厂牌里 21 个是 404，而
        `/logo` 的 404 那条响应不可缓存，每次重绘再打一整轮。判据 `has_logo` 由
        `/api/tops`、`/api/item`、`/api/entity` 随身份一起下发，和取图共用
        `previews.logo_key`。
        """
        for match in re.finditer(r'src="/logo\?studio=([^"]*)"', self.page):
            preceding = self.page[max(0, match.start() - 240):match.start()]
            with self.subTest(url=match.group(0)):
                self.assertIn(
                    "has_logo", preceding,
                    "这处取图位没先问「装了没有」，缺标识时会打一个必然 404 的请求："
                    f"{match.group(0)!r}")

    def test_status_tags_are_separated_and_nonessential_states_are_hidden(self):
        self.assertPageContains(".sep{flex:none;width:1px;height:19px")
        self.assertPageContains("{k:'later',label:'稍后看'},{k:'flagged',label:'已标记'}")
        self.assertPageLacks("{k:'played',label:'看过'}")
        self.assertPageLacks("{k:'ads',label:'垃圾复核'}")

    def test_search_placeholder_is_an_actionable_recommendation(self):
        self.assertPageLacks("const SEARCH_HINTS=")
        self.assertPageContains("await catalogSuggestions(state,api)")
        self.assertPageContains("$('#q').dataset.suggestion=searchSuggestion")
        # 契约是「没有选中下拉项时，Enter 用当前推荐词」。下拉加了键盘导航后，
        # 这个条件由 `!picked` 表达：没有高亮项时它就是 true，与旧的字面 true 等价。
        self.assertPageContains("const picked=searchOptions()[searchActive]")
        self.assertPageContains("runSearch(!picked,true)")
        self.assertPageLacks("试试：")
        self.assertPageLacks("ABW 番号")

    def test_card_identity_is_not_repeated_as_a_content_tag(self):
        self.assertPageLacks("const perf=(it.performers||[])")
        self.assertPageContains('${tgs?`<div class="ctags">${tgs}</div>`')

    def test_compact_card_title_is_one_line_and_identity_kind_matches_name(self):
        self.assertPageContains('body[data-density="dense"] .card .meta .t{display:block;max-width:100%;min-height:1.35em;overflow:hidden;')
        self.assertPageContains("performer?{kind:'performer',name:performer}")
        self.assertPageContains(":{kind:'',name:'未归属'});")
        self.assertPageLacks("it.studio?{kind:'studio',name:it.studio}")
        self.assertPageLacks("const whoKind=it.creator?'creator':(it.studio?'studio':'')")

    def test_creator_name_is_single_line_and_ellipsized(self):
        self.assertPageContains('.meta .who{color:var(--ink-2);min-width:0;max-width:100%;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap')

    def test_every_card_kind_has_one_fixed_ratio(self):
        """三类卡片各自一个固定比例，卡片之间不能高低不齐。

        竖屏按每条视频的实际宽高算的话，素材从 0.5 到 0.9 都有，竖屏条和竖屏网格
        因此参差不齐。`.pic` 写死 16/9 时这段代码不生效，接上 `--card-ratio`
        才起作用。比例不同的用 contain 上下留黑边。
        """
        self.assertPageContains("const PORTRAIT_RATIO=9/16;")
        self.assertPageLacks("Math.min(0.9,Math.max(0.5,it.width/it.height))")
        # 比例由列表语境决定，不能由单条媒体决定：混着横竖屏的资料页、相关推荐、
        # 搜索结果都会因为逐条算而高低不齐。
        self.assertPageContains("const portrait=cls==='scard'||state.orient==='竖屏';")
        self.assertPageLacks("it.ctx_orient==='竖屏'||cls==='scard'")
        self.assertPageContains("(jav&&layout==='big'?COVER_FRONT_RATIO:16/9)")

    def test_the_portrait_strip_lands_at_a_random_row_boundary_on_every_page(self):
        """每接一页出现一条竖屏带，落点在这一页新增的那几行里随机取一个行边界。

        固定第几行的写法从第二屏起就成了可预期的栏目，而这条带子的作用正是打断节奏——
        位置可预期，节奏就不再被打断。只在行边界上剪，否则上一行会被截断留下一段空白；
        两端各留至少一行，剪在头尾就成了置顶或垫底，不是穿插。
        余位不另拉一批横屏视频来补——那批 id 不在分页序列里，翻下一页必然重复，
        而且被当作 `scard` 渲染会按竖屏比例压扁横屏画面。
        静态标记里不留一份用不到的 `#shortsSec`：这一段只由 `loadShorts` 现画。
        """
        self.assertPageLacks('id="shortsSec"')
        self.assertPageLacks('id="tokBtn"')
        self.assertPageLacks("SHORTS_ROW_OFFSET")
        # 每一页都插，不再只在 reset 时插一条。
        self.assertPageContains("loadShorts(requestSeq,surface,{reset,addedFrom});")
        self.assertPageContains("function splitGridForShorts(html,addedFrom){")
        self.assertPageContains(
            "  for(let i=Math.max(columns,Math.ceil(Math.max(0,addedFrom)/columns)*columns);"
            "i<cards.length;i+=columns)")
        self.assertPageContains(
            "  const at=cards[boundaries[Math.floor(Math.random()*boundaries.length)]];")
        # 剪开当前这段：剪点之后的卡整段搬进新的 .grid，带子插在两段之间。
        self.assertPageContains(
            "  for(let node=at;node;){const move=node;node=node.nextElementSibling;tail.append(move)}")
        self.assertPageContains("  section.after(tail);")
        self.assertPageContains("  tail.insertAdjacentHTML('beforebegin',html);")
        # 每条带子取不同的一批，翻下去不会反复看到同 18 个。
        self.assertPageContains("p.set('orient','竖屏');p.set('limit',SHORTS_BATCH);p.set('offset',shortsOffset);")
        self.assertPageContains("shortsOffset=d.has_more===false?0:shortsOffset+SHORTS_BATCH;")
        css = stylesheet_source()
        self.assertPageContains(".gridstack{display:flex;flex-direction:column;gap:16px}")
        start = css.index(chr(10) + ".shorts-inline{")
        strip = css[start:css.index("}", start)]
        for piece in ("background:var(--ground)", "border:1px solid var(--field-ring)",
                      "border-radius:var(--floating-radius)"):
            self.assertIn(piece, strip, "竖屏带是这一叠卡里的一张，和上下两段视频平级")
        self.assertNotIn("grid-column", strip, "它不是网格里的一格，是叠在网格旁边的一张卡")
        self.assertPageLacks("fillerParams")
        self.assertPageLacks('const remainder=')
        # 竖屏比例只给 `scard`（和显式筛了竖屏时）。按 `it.ctx_orient` 逐条算的话，
        # 任何混着横竖屏的网格都会高低不齐——资料页、相关推荐、搜索结果全中招。
        self.assertPageContains("const portrait=cls==='scard'||state.orient==='竖屏';")
        self.assertPageContains('grid-template-columns:repeat(auto-fill,minmax(var(--tile),1fr))')
        self.assertPageContains('.srow .scard{flex:none;width:214px;cursor:pointer}')

    def test_only_the_default_home_list_drops_portrait_videos(self):
        """搜索必须能命中竖屏作品；排除竖屏只是首页默认列表的取景，不是全局过滤。"""
        self.assertPageContains("if(isCatalogPath(decodeURIComponent(location.pathname))&&!state.q&&!state.orient)p.set('exclude_vertical','1')")
        self.assertPageLacks("if(!state.orient)p.set('exclude_vertical','1')")

    def test_grid_count_and_range_select_read_across_sections_but_skip_the_strip(self):
        """目录是一叠 `.grid`，不是一个；竖屏带里的卡既不计入「显示 N」，也不参与范围选中。

        判据统一写成 `#grid > .grid > .card[data-id]`：跨过分段这一层，同时把竖屏带
        排除在外——它的卡在 `.srow` 里，不属于任何一段。
        """
        self.assertPageContains(
            "const gridCards=()=>document.querySelectorAll('#grid > .grid > .card[data-id]');")
        self.assertPageContains(
            "function visibleCardIds(){return [...gridCards()].map(card=>+card.dataset.id)}")
        self.assertPageContains("const n=gridCards().length;")

    def test_recycle_bin_has_its_own_route_and_reports_undeletable_files(self):
        self.assertRoute('/trash', "section:'trash'", "openTrash(push)")
        self.assertPageContains("function openTrash(push){")
        self.assertPageContains("state:'trash',q:''};clearSearchField();")
        self.assertPageContains("/api/trash/empty")
        self.assertPageContains("r.blocked&&r.blocked.length")

    def test_closed_scrim_leaves_the_render_tree(self):
        """iOS 26 的 Safari 按贴边、铺满宽度的 fixed 元素底色给状态栏和地址栏取色，opacity:0 的也算。
        遮罩收起时必须 display:none，淡入淡出靠 allow-discrete 与 @starting-style 保住。"""
        self.assertPageContains(".scrim{position:fixed;inset:0;z-index:95;background:rgba(0,0,0,.42);opacity:0;pointer-events:none;display:none;")
        self.assertPageContains("transition:opacity .18s,display .18s allow-discrete}")
        self.assertPageContains(".scrim.on{display:block;opacity:1;pointer-events:auto}")
        self.assertPageContains("@starting-style{.scrim.on{opacity:0}}")

    def test_mobile_detail_stage_clears_status_bar_and_address_bar(self):
        """手机上详情浮窗上沿让出状态栏、下沿按 dvh 停在地址栏之上，吸顶的画面不钻到两条栏底下。"""
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("  .stage{inset:calc(env(safe-area-inset-top) + 8px) 8px auto;margin:0 auto;", board)
        self.assertIn("    max-height:calc(100dvh - env(safe-area-inset-top) - 16px)}", board)

    def test_mobile_scrim_shell_is_skipped_by_ios_status_bar_tinting(self):
        """窄屏侧栏遮罩铺满视口、底色半透明，iOS 26 的 Safari 会把它当压暗层给状态栏取色。暗色画在 ::before 上，
        遮罩外壳 visibility:hidden，Safari 跳过这层沿用顶栏的颜色，一开侧栏状态栏不整块变暗。"""
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("  .scrim.scrim.on{top:0;z-index:101;background:none;visibility:hidden}\n"
                      "  .scrim.scrim.on::before{content:'';position:absolute;inset:0;background:#0007;visibility:visible}\n", board)

    def test_card_hover_hides_source_and_duration_and_missing_size_is_explicit(self):
        self.assertPageContains('.card:hover .badge,.card:hover .dur{opacity:0}')
        # max-height 兜住 WebKit：标题里的番号块是 inline-flex，line-clamp 在那里不截。
        self.assertPageContains('.meta .t{font-size:var(--fs-md);line-height:1.35;min-height:2.7em;max-height:2.7em;')
        self.assertPageContains("const sizeText=Number(shownSize)>0?fmtSize(Number(shownSize)):'大小未知';")
        self.assertPageContains('<span class="size">${sizeText}</span>')

    def test_tags_page_has_cloud_and_alphabet_modes(self):
        # 两个视图是同一批标签的两种摆法，走 iconswitch；页面级的本地／在线才是 Tabs。
        self.assertCode("const TAG_VIEW_MODES=[['cloud','标签云','tags'],['alphabet','字母表','text-aa']];")
        self.assertCode("const view=iconSwitchHtml('tag-view','标签视图',TAG_VIEW_MODES,tagIndexMode,{attr:'data-tag-view'});")
        self.assertCode("wireIconSwitch($('#index'),'data-tag-view',value=>{\n"
                        "    tagIndexMode=value;openIndex('tags',$('#iq').value.trim(),true)});")
        self.assertPageContains('class="alphabet"')
        self.assertPageContains("attr:'data-tag-category'")
        self.assertPageContains("['meta','影片属性']")
        self.assertPageContains("['relationship','人物关系']")
        self.assertPageContains("['role','角色设定']")
        self.assertPageContains("['appearance','外貌身材']")
        self.assertPageContains("['scene','情境场所']")
        self.assertPageContains("['story','故事剧情']")
        self.assertPageContains("['position','性交体位']")
        self.assertPageContains("['general','其他内容']")
        self.assertPageContains("['copyright','作品']")
        self.assertPageLacks("['artist','人物']")
        self.assertPageContains("['character','角色']")
        self.assertPageContains("key==='all'||Number(d.categories?.[key]||0)>0")
        self.assertPageContains("'1080P':'1080p'")
        self.assertPageContains("'60fps':'60FPS'")
        self.assertPageContains("'AI去码':'AI解码'")
        # 显示名不能改成另一个已经存在的标签名，也不能把通行写法换成不通行的。
        self.assertPageLacks("'足系':'美腿'")
        self.assertPageLacks("'足交':'脚交'")
        self.assertPageContains("'骑乘':'骑乘位'")
        self.assertPageContains("category=params.get('category')")

    def test_state_routes_tag_multiselect_and_header_capabilities_are_explicit(self):
        self.assertPageContains("const STATE_ROUTES={fresh:'/unseen',later:'/watch-later',flagged:'/flagged',ads:'/junk-files'}")
        self.assertPageContains('href="${v.k?STATE_ROUTES[v.k]:\'/\'}" data-state="${v.k}"')
        self.assertPageContains("route(homePath());buildBars();load(true)")
        self.assertPageContains("const selectedIndexTags=new Set()")
        self.assertPageContains('data-tag-match-any')
        self.assertPageContains('广泛匹配')
        self.assertPageContains('data-tag-apply')
        self.assertPageContains("tag_match:tagIndexMatch")
        self.assertPageContains("const canSelect=catalog||entity||path==='/tags'")
        self.assertPageContains("$('#selectMode').hidden=!canSelect;$('#density').hidden=!canDensity")
        self.assertPageLacks("const canRefresh=")

    def test_censor_lives_in_settings_and_stays_off_by_default(self):
        """审查遮挡在设置面板，默认关闭；导航栏不出现。

        日常浏览不该被遮挡（用户回执）；截图会交给会审查内容的模型时才在
        设置里打开（AGENTS.md 工作规则）。规则按元素类型生效（img/video/
        videojs 海报层），开关一开仍然全站覆盖；悬停预览的启动路径必须查
        这个开关——动起来的画面比静帧更漏。
        """
        # 顶栏不出现独立开关，开关在设置面板「安全」组。
        self.assertPageLacks('id="censorBtn"')
        self.assertPageContains('class="ptoggle" type="checkbox" id="censorSetting" role="switch" aria-describedby="sfwDescription"')
        self.assertPageContains('<b>SFW 模式</b><small id="sfwDescription">')
        self.assertPageContains('模糊、降低饱和度并压暗全站图片和视频，包括封面、头像与详情预览；停止悬停预览。文字、品牌标识和来源图标保持可见。')
        self.assertPageLacks('共享屏幕或截图前开启，遮住全站封面与预览图。')
        # 默认关闭：localStorage 记 '1' 才开，没动过的会话一律不遮。
        self.assertPageContains("applyCensor(localStorage.getItem(CENSOR_KEY)==='1')")
        # 全站按元素类型盖：内容 img / video / videojs 海报层一个不落。
        self.assertCode("body.censor img,body.censor video,body.censor .vjs-poster{\n  filter:blur(30px) saturate(.3) brightness(.6)}")
        # 豁免只给与内容无关的界面小图：品牌标、来源徽章、favicon。
        self.assertPageContains("body.censor .brand .mark,body.censor .src img,body.censor .ficon{filter:none}")
        # 开关变化写回 localStorage 并撤掉正在飞的悬停预览。
        self.assertPageContains("$('#censorSetting').onchange=")
        self.assertPageContains("if(on)releaseHoverPreviews()")
        # 悬停预览三条启动路径（长按轮播、悬停起播、定时器到点）都要被拦。
        self.assertIn("if(selectMode||censorOn())return;armLong()", self.page)
        self.assertIn("if(selectMode||censorOn()||window.__scrolling)return;", self.page)
        self.assertIn("if(window.__scrolling||censorOn())return;", self.page)

    def test_management_surfaces_are_narrow_and_geist_semantics_hold(self):
        """语义色、状态徽章与导航激活重算对齐 Geist 实测。

        限宽布局已按用户回执整体改回：限宽列与上方导航和标题的版式不适配，
        在重排导航与标题之前不许再回来。检查失败报告是红发丝边 + 微红底的
        danger 语义块，不是左侧粗条；来源行状态用低饱和徽章；清空回收站是
        销毁类操作，用 danger 色而不是主色实底；组合标签时顶部 pill 按按下
        态逐个命中，combo 芯片显示显示名；导航激活态随路由重算。
        """
        # 限宽已回退：整条规则不许再出现（重排导航/标题前是已知的坏版式）。
        self.assertPageLacks("max-width:1004px;margin-inline:auto")
        self.assertPageContains("document.body.dataset.surface=url.pathname")
        # 导航激活态随路由重算：抽屉/窄栏按钮是 buildBars 时一次性画的，
        # 管理页不跑 buildBars，不重算就会停留在上一个页面的按下态。
        self.assertPageContains("paintNav();")
        self.assertPageContains("function paintNav(){")
        self.assertPageContains(".edge button[data-nav],#drawer .dnav button[data-nav]")
        # 组合标签：pill 按按下态逐个命中；combo 芯片显示显示名、操作用原始 key。
        self.assertPageContains("tagPressed(filterState.tag,t.k)")
        self.assertPageContains("${esc(tagLabel(t))} <b data-untag=\"${esc(t)}\">✕</b>")
        # fwarn 提供 dismiss（会话内记忆），关闭钮样式与 toast 关闭钮同量纲。
        self.assertPageLacks("data-fwarn-dismiss")
        self.assertPageContains(".fwarn{grid-template-columns:16px minmax(0,1fr);")
        self.assertPageContains(".geist-note-error{--feedback-color:var(--drop);")
        self.assertPageLacks("border-left:2px solid var(--drop)")
        # 来源行状态徽章：失败红、正常绿、暂停黄、未检查灰。关注管理页归 React 之后
        # 这一枚是 BoardUI `Chip`，档位由同一套判据给。
        source_view = self.read_react("follow-manage/source-view.tsx")
        self.assertIn("const color = isBroken(source) ? 'rose'", source_view)
        self.assertIn(": source.enabled && source.last_status === 'ok' ? 'lime'", source_view)
        self.assertIn(": source.enabled ? 'yellow' : 'neutral';", source_view)
        # 状态徽章只有 React 那一枚 Chip，遗留样式表里没有第二份。
        self.assertPageLacks(".sbadge")
        # 清空回收站：danger 语义色。
        self.assertPageContains('class="batchaction danger" id="emptyTrash"')
        self.assertPageContains("button.danger.danger{")
        # Geist 菜单：触发器和每个选项都有入口图标，菜单内部滚动；开合动效走 Board 层共用那一份。
        self.assertPageContains('data-sidebar-add-trigger aria-haspopup="listbox" aria-expanded="false"')
        self.assertPageContains('role="option" data-sidebar-add-option=')
        # 弹层盒子走共用的 .popmenu：发丝边、投影和 2px 行距只有一份定义，本页只接管定位。
        # 行距不能省——相邻两项一个悬停一个选中时，两块填充会连成一整条，看不出是两行。
        self.assertPageContains('<div class="popmenu sidebaraddmenu"')
        self.assertPageContains("background:var(--ground);display:grid;gap:2px;")
        self.assertPageContains(".sidebaraddmenu{position:absolute;z-index:4;left:0;right:0;bottom:calc(100% + 6px);max-height:min(312px,48vh)}")
        self.assertPageContains("if(e.key==='Escape'){e.preventDefault();closeAddMenu();addTrigger.focus();return}")
        # 设置分组用框体隔开（用户回执）：每组建卡，分隔线顶格到卡边，
        # 标题字号与行内边距对齐 Vercel 后台设置卡。
        self.assertPageContains(".settinggroup{margin:16px 0 0;border:1px solid var(--field-ring);border-radius:var(--floating-radius);")
        # 层级和首页一致：壳是退到后面的 --page，分组才是浮起来的 --ground 加一条发丝线。
        # 反过来写（白壳嵌灰块）会让同一套控件在设置里和在首页上读出相反的层级。
        self.assertPageContains("background:var(--ground);padding:0 16px 12px}")
        self.assertPageContains("border:1px solid var(--field-ring);border-radius:var(--floating-radius);background:var(--page)}")
        self.assertNotIn("box-shadow:0 8px 32px -12px", self.css, "浮层靠发丝线不靠投影")
        # 布尔开关是 Geist 中号 Toggle（36×20 轨道 + 17px 圆点），不是原生复选框；
        # Geist 的 Switch 是分段选择器，别用错控件。
        self.assertPageContains(".ptoggle{appearance:none;-webkit-appearance:none;width:36px;height:20px;flex:none;")
        self.assertPageContains(".ptoggle:checked{background:var(--tungsten)}")
        # 没有直接证据的 command-menu 入场动画与无有效高度约束的复核卡
        # Scroller 不应继续作为「Vercel 对齐」进入产品。
        self.assertPageLacks("animation:panel-in")
        self.assertPageLacks("@keyframes panel-in")
        self.assertPageLacks("wireReviewScrollers")
        self.assertPageLacks("reviewscrollbtns")
        self.assertPageContains(".settinggroup>h3{margin:0;padding:14px 0 10px;font-size:var(--fs-lg);font-weight:600;color:var(--ink)}")
        self.assertPageContains(".settinggroup .settingrow{margin:0;padding-left:0;padding-right:0}")
        self.assertCode(
            ".pagetitle,.listtitle,.managetitle,.index .ihead h2,.playlistpage h2{"
            "\n  font-size:var(--fs-3xl);line-height:1.25;letter-spacing:-.01em;font-weight:600}")
        # 全站字体栈必须有 CJK sans 兜底：Bahnschrift/Consolas 都没有中文字形，
        # generic sans-serif/monospace 在中文 Chrome 的默认可能落到宋体。
        css = stylesheet_source()
        for i, line in enumerate(css.splitlines(), 1):
            if "font-family" not in line or "inherit" in line:
                continue
            if "sans-serif" in line or "monospace" in line:
                self.assertIn("YaHei", line, f"样式表第 {i} 行字体栈缺 CJK 兜底：{line.strip()[:90]}")

    def test_no_page_grows_its_own_back_control(self):
        """索引页没有自己的返回按钮：顶栏入口本身就是返回路径。

        这条守的是「不要长出来」，以及别留下没人用的图标与样式——没有使用者的
        `i-arrow-left` symbol 和 `.backbtn` 就是死代码。
        """
        self.assertPageLacks("${icon('arrow-left')}")
        self.assertPageLacks('id="i-arrow-left"')
        self.assertPageLacks(".backbtn")
        self.assertPageLacks("${icon('chevron-left')}<span>返回</span>")

    def test_climax_uses_pinned_healthicons_symbol(self):
        self.assertPageContains('id="i-sperm"')
        self.assertPageContains("icon('sperm')")

    def test_settings_own_useful_experience_preferences(self):
        self.assertPageContains("const DEFAULT_SETTINGS={batchSize:60,defaultSort:'seed'")
        self.assertPageContains('id="settingsPanel"')
        self.assertPageLacks('id="rotateSetting"')
        self.assertPageContains("appSettings.hoverDelaySeconds")
        self.assertPageContains("appSettings.batchSize")
        self.assertPageContains("appSettings.defaultSort")
        self.assertPageContains("appSettings.seekSeconds")
        self.assertPageContains("appSettings.searchHistoryLimit")
        self.assertPageContains("appSettings.relatedLimit")
        self.assertPageContains("appSettings.ambientMode=appSettings.ambientMode!==false")
        self.assertPageContains("appSettings.theaterMode=appSettings.theaterMode===true")
        self.assertPageContains('id="followScheduleSetting"')
        self.assertPageContains("api('/api/follow/schedule'")
        self.assertPageContains('id="sidebarOrderSetting"')
        self.assertPageContains("appSettings.sidebarOrder")
        self.assertPageContains("if(!appSettings.sidebarOrder.length)appSettings.sidebarOrder=[...DEFAULT_SIDEBAR_ORDER]")
        self.assertPageContains("orderedEdgeIcons()")
        self.assertPageContains('draggable="true" data-sidebar-row=')
        # 拖动排序全站一份：侧栏这一列和播放队列都调它，落点判据、减淡和那条插入线
        # 不各留一套。
        self.assertPageContains("export function wireDragReorder(root,{selector,attribute,onMove}={})")
        self.assertPageContains("wireDragReorder(root,{selector:'[data-sidebar-row]',attribute:'data-sidebar-row',")
        self.assertPageContains("wireDragReorder(list,{selector:'[data-queue-row]',attribute:'data-queue-row',")
        self.assertPageContains("function wireNavigationDrag(root){")
        self.assertPageContains("wireNavigationDrag($('#edge'))")
        self.assertPageContains("wireNavigationDrag($('#drawer').querySelector('.dnav'))")
        self.assertPageContains('data-nav="${k}" draggable="true"')
        self.assertPageContains("data-sidebar-hide")
        self.assertPageContains("data-sidebar-add-option")
        self.assertPageLacks("data-sidebar-add-select")
        self.assertPageContains("const OPTIONAL_SIDEBAR_KEYS=['playlists','immerse','stats','review','data-cleanup','trash','follow-manage','quality']")
        self.assertPageContains("if(DIRECT_MANAGE_NAV[k]){openManage(DIRECT_MANAGE_NAV[k]);return}")
        self.assertPageContains(".settingscard{display:flex;flex-direction:column;width:min(520px,100%);max-height:min(720px,90vh);max-height:min(720px,90dvh);overflow:clip")
        self.assertPageContains(".settingsscroll{flex:1;min-height:0;overflow-y:auto")
        self.assertPageContains("document.dispatchEvent(new CustomEvent('peachambientchange'")
        self.assertPageContains(".settingrow .gselect{min-width:148px}")

    def test_the_thumbnail_density_is_this_machines_state_not_this_browsers(self):
        """档位跟着服务端走。跑的是这台机器上的一条长任务，从另一台设备打开设置要看到
        的是它正在按什么密度采集，所以这一行既不进 `appSettings` 也不进 localStorage。
        """
        self.assertPageContains('id="videoThumbnailSetting"')
        self.assertPageContains('id="videoThumbnailState" aria-live="polite"')
        self.assertPageLacks("appSettings.videoThumbnailMode")
        self.assertPageContains("['videoThumbnailSetting','视频缩略图采集',"
                                "[['off','关闭'],['precise','精准'],['coarse','粗略']],")
        self.assertPageContains("()=>'off',value=>saveVideoThumbnailMode(value)]")
        self.assertPageContains("const status=await api('/api/thumbnail-jobs');")
        self.assertPageContains("api('/api/thumbnail-jobs',{method:'POST',body:JSON.stringify({mode})})")
        self.assertPageContains("if(status.status==='running')void watchVideoThumbnailJob(request)")
        # 采集只覆盖本机磁盘上的片子，网盘上的每张都要回源拉一次。这一条是功能范围，
        # 说明里必须写出来，否则页面上「视频缩略图采集」读起来是全库。
        self.assertPageContains("只采集本机磁盘上的片子")

    def test_the_seek_preview_prefers_frames_that_match_where_the_pointer_is(self):
        """指到哪一秒就看到哪一秒。九宫格那九格是全片九等分，两小时的片子格与格之间
        隔着十几分钟，指的位置和看到的画面对不上；采集任务铺好了时间轴图就改用它，
        没铺到的退回九宫格。
        """
        self.assertPageContains("api(`/api/timeline?id=${encodeURIComponent(it.id)}`)")
        self.assertPageContains("if(meta&&meta.frames>0&&meta.interval>0)sheets=meta")
        self.assertPageContains("if(sheets){showSheetFrame(duration*ratio);return}")
        self.assertPageContains("const index=Math.min(sheets.frames-1,"
                                "Math.max(0,Math.floor(seconds/sheets.interval)))")
        self.assertPageContains("const sheet=Math.floor(index/per),slot=index%per")
        # 末张通常不满 10 行，行数按它自己剩下那几帧反算；按满行铺会把格子挪到图外面。
        self.assertPageContains("const rows=Math.ceil(Math.min(per,sheets.frames-sheet*per)/columns)")
        self.assertPageContains("image.src=`/poster?id=${encodeURIComponent(it.id)}&c=${nextCell}`")

    def test_theme_is_a_three_way_choice_that_defaults_to_the_system(self):
        """主题三档：跟随系统、浅色、深色。

        色板的两条分支（`prefers-color-scheme` 与 `[data-theme]`）本来就写在
        01-base.css 里，这里补的是「选哪一条」。三档互斥，所以是 Geist Switch——
        一组共享 name 的 radio，不是 Toggle；跟随系统等于不写属性，把判断还给媒体查询。
        """
        self.assertPageContains("const THEME_CHOICES=['system','light','dark']")
        self.assertPageContains(
            "const THEME_OPTIONS=[['system','跟随系统','monitor'],"
            "['light','浅色','sun'],['dark','深色','moon']]")
        self.assertPageContains("theaterMode:false,theme:'system',groupCollapse:true")
        self.assertPageContains(
            "appSettings.theme=allowedSetting(appSettings.theme,THEME_CHOICES,'system')")
        self.assertCode(
            "if(choice==='system')delete root.dataset.theme;else root.dataset.theme=choice;")
        self.assertCode("const dark=choice==='dark'||(choice==='system'&&prefersDark.matches);")
        # 地址栏色块也归这次调用：两枚 meta 各代表一档，选中的开到 all、另一枚关掉。
        self.assertCode("meta.media=(meta.dataset.themeColor==='dark')===dark?'all':'not all';")
        self.assertCode(
            "prefersDark.addEventListener('change',()=>{if(appSettings.theme==='system')applyTheme()});")
        self.assertPageContains(
            '<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)"'
            ' data-theme-color="light">')
        self.assertPageContains(
            '<meta name="theme-color" content="#080A0D" media="(prefers-color-scheme: dark)"'
            ' data-theme-color="dark">')
        # 面板里的控件复用卡片版式那份模板，只是形状另给。
        self.assertPageContains('<div id="themeSetting"></div>')
        self.assertCode(
            "mount.innerHTML=iconSwitchHtml('theme','主题',THEME_OPTIONS,appSettings.theme,"
            "{attr:'data-theme-choice',className:'themeswitch'});")
        self.assertCode(
            "wireIconSwitch(mount,'data-theme-choice',"
            "choice=>{appSettings.theme=choice;saveSettings();applyTheme()});")
        self.assertCode("renderThemeSetting();")

    def test_first_paint_already_knows_which_theme_was_chosen(self):
        """选择要在第一帧之前生效。

        `app.js` 是 module，等同 defer：轮到它跑的时候浏览器已经按系统色画过一帧，
        手动选浅色的人每次进页面都先看一下深色。所以 index.html 里有一段内联脚本
        只做「写 data-theme、切地址栏色块」这两件事，其余仍只有 applyTheme() 一份。
        """
        self.assertPageContains(
            "const choice=JSON.parse(localStorage.getItem('peach.settings.v1')||'{}').theme;")
        self.assertCode("if(choice!=='light'&&choice!=='dark')return;")
        self.assertCode("document.documentElement.dataset.theme=choice;")
        self.assertCode("meta.media=meta.dataset.themeColor===choice?'all':'not all';")
        # 色板不许在这里再写一份：内联脚本一个颜色字面量都不带。
        script = self.page.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("#", script)

    def test_theme_switch_wears_the_measured_vercel_theme_selector(self):
        """主题选择器是 Geist 里唯一给选中项加环的控件。

        三档的底色和它坐着的面板同色，光靠填充分不出当前是哪一档，所以选中项
        额外加一圈环——2026-09-04 实测 vercel.com 的 system／light／dark 三枚圆形按钮：
        外框 32px 高的无填充胶囊加 1px 环，每档 32×32 正圆、图标 16px。
        未选中不铺填充、悬停只提文字色，这两条由 `.iconswitch` 本体给。
        """
        self.assertCode(
            ".iconswitch.themeswitch{display:inline-flex;flex:none;padding:0;border:0;"
            "background:transparent;border-radius:var(--pill-radius);"
            "box-shadow:0 0 0 1px var(--border-15)}")
        self.assertCode(".iconswitch.themeswitch label{width:32px;height:32px;border-radius:50%}")
        self.assertCode(
            ".iconswitch.themeswitch label:has(input:checked){background:var(--ground);"
            "box-shadow:0 0 0 1px var(--line),0 1px 2px var(--overlay-5)}")
        self.assertCode(".iconswitch.themeswitch svg{width:16px;height:16px}")
        # 手机上三枚圆撑到 44px 命中区。
        self.assertCode(
            "@media (max-width:760px){.iconswitch.themeswitch label{width:44px;height:44px}}")
        # 分隔线属于整块卡片，铺到框边再断。
        self.assertCode(
            ".settinggroup :is(.settingrow,.glowsetting)+.sidebarsetting{margin:0;padding:14px 0 0;"
            "border-top:1px solid var(--line-soft)}")

    def test_search_menu_has_local_history_and_recommendations(self):
        self.assertPageContains("/api/search-history")
        self.assertPageContains("搜索记录")
        self.assertPageContains("recommendations.map")
        self.assertPageContains("rememberSearch(query)")
        self.assertPageContains("body:JSON.stringify({query})}).catch(()=>null)")
        self.assertPageContains(".top:has(.search.open){overflow:visible}")
        self.assertPageLacks("setTimeout(runSearch,320)")
        self.assertPageContains("runSearch(!picked,true)")

    def test_search_menu_completes_from_the_ledger_as_you_type(self):
        """敲字的同时给出馆藏里的身份与作品，不是聚焦时那一批固定推荐。"""
        self.assertPageContains("/api/suggest?q=")
        self.assertCode("const SUGGEST_DEBOUNCE=150;")
        # 慢的旧响应不许盖掉新的：连敲两个字时先发的那次完全可能后回来。
        self.assertCode("const request=++suggestRequest;")
        self.assertCode("if(request!==suggestRequest)return;")
        # 分组顺序和名字都由后端给，页面不另排一遍。
        self.assertCode("esc(group.label)")
        self.assertPageLacks("const SUGGEST_GROUPS=[")
        # 有输入时历史跟着筛，这一刻用户在找词而不是回顾搜过什么。
        self.assertCode("foldName(x).includes(foldName(query))")

    def test_a_completed_work_opens_instead_of_running_a_search(self):
        """整句标题填回搜索框，下一次搜索会因为任何一个字符对不上而落空。"""
        self.assertPageContains("data-open-item")
        self.assertCode("if(x.dataset.openItem){$('#q').blur();openItem(+x.dataset.openItem);return}")
        # 键盘选中的那一项走同一条路，回车不绕一趟搜索。
        self.assertCode(
            "if(picked&&picked.dataset.openItem){$('#q').blur();"
            "openItem(+picked.dataset.openItem);return}")

    def test_the_search_menu_scrolls_inside_itself(self):
        """七组补全装不进一屏，滚到底不把身后的列表一起翻走。"""
        self.assertCode("max-height:min(60vh,520px);overflow:auto;overscroll-behavior:contain;")
        self.assertCode(
            ".searchmenu{position:fixed;left:8px;right:8px;top:56px;max-height:70vh;"
            "overflow:auto;overscroll-behavior:contain}")

    def test_a_suggestion_keeps_its_alias_and_count_subordinate(self):
        """命中的别名和作品数都是这一行的注脚，不与统称争分量。"""
        self.assertCode(
            ".searchoption .matched{flex:0 8 auto;min-width:0;"
            "color:var(--muted);font-size:var(--fs-xs)}")
        self.assertCode(
            ".searchoption .n{margin-left:auto;flex:none;color:var(--muted);"
            "font-size:var(--fs-xs);font-variant-numeric:tabular-nums}")

    def test_detail_has_stats_ambient_and_better_version_goal(self):
        self.assertPageContains('class="ambientcanvas"')
        self.assertPageContains("requestVideoFrameCallback")
        self.assertPageContains("--video-glow")
        self.assertPageContains("function mountPlayerAmbient(video)")
        self.assertPageContains(".stage:not(.ambient-on) .ambientcanvas{display:none}")
        self.assertPageContains("视频 ID / 会话")
        self.assertPageContains("/api/quality-goal")
        self.assertPageContains('id="betterVersion"')
        self.assertPageLacks("prompt('要找哪种更好版本？")
        self.assertPageContains("body:JSON.stringify({id:it.id,wanted})")
        self.assertPageLacks('id="closeStage">收起')

    def test_ambient_mode_repaints_from_a_paused_frame_when_switched_back_on(self):
        """暂停时打开氛围模式要立刻取一帧：帧回调只在有新画面时才来，链上用 run 号判重。"""
        self.assertPageContains("const sample=()=>{if(video.readyState<2)return;")
        self.assertPageContains("const start=()=>{if(stopped||!appSettings.ambientMode)return;"
                                "sample();if(!video.paused)queue(++run)}")
        self.assertPageContains("if(event.detail.enabled)start();else{run++;clear()}")
        self.assertPageContains("video.addEventListener('play',start);"
                                "video.addEventListener('loadeddata',start);start();")
        self.assertPageContains("const paint=(id,now)=>{if(stopped||id!==run)return;")
        self.assertPageLacks("scheduled=false")

    def test_the_whole_detail_box_takes_one_ambient_tone(self):
        """右侧详情栏和「接着看」是同一格详情的两块，底色必须同源。

        半透明的氛围色叠在透明底上时，底下是 `.stage` 那圈只铺到 58% 的径向渐变，
        而它铺不到「接着看」这一条：那一块于是浅一档，整幅宽度上留下一道深浅不匀
        的色差，看着像两块面板拼起来的。氛围色定义在 `.stage` 上，两块引同一个值。
        两块之间的分界由 `--line-soft` 那条线负责：同色之后光留白读不出边界，
        「接着看」是和详情信息不同的一件事，得有一条线说清它从哪里开始。
        """
        self.assertPageContains(
            ".stage{--detail-surface:color-mix(in srgb,var(--video-glow,#15202a) 12%,"
            "var(--surface) 88%);")
        self.assertPageContains("  background:var(--detail-surface);backdrop-filter:blur(18px)}")
        self.assertPageContains(".next{border-top:1px solid var(--line-soft);"
                                "padding:11px 15px 12px;background:var(--detail-surface)}")

    def test_better_version_targets_have_a_management_page(self):
        """账本里标记为「还该有更好一版」的作品在管理区自成一页。

        它是 React 档（ADR-0031）：遗留层只铺骨架、交容器，再把自己独有的助手（番号标题、
        来源徽标、打开作品）作为 props 递进去，整页在 `frontend/src/react/quality-goals/` 里。
        所以这里断言的是外壳——路由、菜单入口、骨架与挂载契约。卡片上有什么、点哪里打开
        作品、进出这一页各发几次请求由 `frontend/test/react/quality-goals.test.tsx` 守，
        封面的宽度与比例、长标题的中间省略由 `frontend/e2e/design.test.ts` 读计算值守，
        数据契约由 `/api/quality-goals` 的路由测试守。
        """
        self.assertPageContains("['quality','高清版','sparkles']")
        self.assertRoute('/quality-goals', "section:'quality'", "openQualityGoals(push)")
        self.assertPageContains("async function openQualityGoals(push=true)")
        self.assertPageContains("const ui=await import('/dist/peach-ui.js')")
        self.assertPageContains(
            "await ui.mountIsland('quality-goals',$('#stats'),props,"
            "{isCurrent:()=>surfaceCurrent(surface)})")
        self.assertPageContains("const props={openItem,javTitleHtml,javDisplayName,srcBadge}")
        self.assertPageLacks("data-quality-open")
        # 正文归 React 子树：卡片、汇总行与按钮用 BoardUI 的源码加 Tailwind，
        # 遗留样式表里只剩骨架要的那几条。
        self.assertPageLacks(".qualityfallback{")
        self.assertPageLacks(".qualityreason{")

    def test_the_activity_page_is_the_one_place_that_shows_every_task(self):
        """任务中心的界面：谁在跑、谁被挡下了、刚跑完的怎么样，一屏三段。

        它是 React 档（ADR-0031）：遗留层只铺骨架、交容器，整页在
        `frontend/src/react/activity/` 里。所以这里断言的是外壳——路由、菜单入口与
        深链冷启动的骨架。三段怎么分、轮询节律和失败时留下什么由
        `frontend/test/react/activity.test.tsx` 守，徽章的三档颜色与失败卡的框线由
        `frontend/e2e/design.test.ts` 读计算值守，数据契约由 `/api/tasks` 的路由测试守。
        入口进管理菜单而不是挂在某一页下面：扫描、追更、批量都会出现在它上面，
        从其中任何一页进都像是那一页的下一步。
        """
        self.assertRoute('/activity', "section:'activity'", "title:'活动'",
                         "openActivity(push)")
        self.assertPageContains("async function openActivity(push=true)")
        self.assertPageContains(
            "await ui.mountIsland('activity',$('#stats'),{},"
            "{isCurrent:()=>surfaceCurrent(surface)})")
        self.assertPageContains("['activity','活动','history'],")
        self.assertPageContains("quality:'quality',activity:'activity'}")
        # 深链冷启动要铺的是这一页自己的骨架，不是默认那张。
        self.assertPageContains("'/activity':()=>pageSkeletonHtml('正在读取任务活动',")
        self.assertPageContains("'/configuration','/activity']);")
        # 骨架那几张空卡跟数据管理同一条 812px 窄列，React 子树接手后正文停在同一条中线。
        self.assertPageContains(
            ".activitypage{width:min(812px,100%);margin:0 auto;display:grid;gap:32px}")
        # 正文归 React 子树：卡片、徽章与进度用 BoardUI 的源码加 Tailwind，
        # 遗留样式表里只剩骨架要的那几条。
        self.assertPageLacks(".activity-run-head{")
        self.assertPageLacks(".activity-progress{")

    def test_the_stats_page_is_an_island_inside_the_management_shell(self):
        """统计是主站里的一屏，遗留层只铺骨架、交容器和它独有的那几个助手。

        它是 React 档（ADR-0031）：整页在 `frontend/src/react/stats/` 里。读数怎么分层、
        环形图的几何、排行的收展和三个空态由 `frontend/test/react/stats.test.tsx` 守，
        搬家之后语义标记还在不在由 `tests/test_frontend_build.py` 的 `StatsEndpointTests`
        守，数据契约由 `/api/stats` 的路由测试守。

        「点一个内容标签回目录并按它筛选」是整页换成目录，仍归遗留壳：页面只把标签键
        交回来，不自己调 `route` 或 `load`。
        """
        self.assertRoute('/stats', "section:'stats'", "title:'统计'", "openStats(push)")
        self.assertPageContains("async function openStats(push=true)")
        self.assertPageContains(
            "await ui.mountIsland('stats',$('#stats'),{\n"
            "    tagLabel,onTag:k=>{closeStats();toggleTag(k)},\n"
            "    openMediaSettings:()=>openSettings(true,'媒体'),configurable:!!runtimeConfigurable,\n"
            "  },{isCurrent:()=>surfaceCurrent(surface)});")
        # 正文归 React 子树：读数卡、环形图与排行用 BoardUI 的源码加 Tailwind，
        # 遗留样式表里只剩骨架要的那几条。
        self.assertPageLacks(".board-radial-card{")
        self.assertPageLacks(".insightranking{")
        self.assertPageLacks(".insightfacts{")
        self.assertPageLacks(".statmetric{")

    def test_the_configuration_page_is_an_island_inside_the_management_shell(self):
        """这台电脑的媒体文件夹与端口是主站里的一屏，不是另一套独立页面。

        遗留层只铺骨架、交容器、发回执；表单与校验回显在 frontend/ 的 island 里，
        数据契约由 tests/test_onboarding.py 对 `/api/configuration` 断言。
        """
        self.assertRoute('/configuration', "section:'configuration'", "title:'配置'",
                         "openConfiguration(push)")
        self.assertPageContains("async function openConfiguration(push=true)")
        self.assertPageContains(
            "await ui.mountIsland('configuration',$('#stats'),props,"
            "{isCurrent:()=>surfaceCurrent(surface)})")
        self.assertPageContains("const props={receipt:message=>actionReceipt(message)};")
        self.assertPageContains(
            "document.body.classList.toggle('configuration-layout',current==='configuration');")
        self.assertPageContains("'/configuration':()=>configurationSkeletonHtml()")
        self.assertPageContains('stats-lede-skeleton')
        self.assertPageContains("['网络与访问',2]")

    def test_review_page_is_a_separate_management_layer(self):
        """复核有自己的路由与分类表；正文归 React 岛（ADR-0031）。"""
        self.assertPageContains("const REVIEW_LABELS={metadata_fields:'元数据字段',creator_tags:'创作者标签'")
        self.assertPageContains("route('/review'+(params.category?'?category='"
                                "+encodeURIComponent(params.category):''))")
        self.assertRoute('/review', "section:'review'", "openReview(push)")
        # 分类是地址的一部分，别的筛法不是：队列判一条就少一条，页码指向的是另一批东西。
        self.assertPageContains("return {category:Object.hasOwn(REVIEW_LABELS,category)?category:''};")
        self.assertPageContains("await ui.mountIsland('review',$('#stats'),{...params,")

    def test_detail_title_folds_to_two_lines_with_the_file_actions_below(self):
        """标题默认折成两行，真溢出才给展开键；文件动作和它排成标题下面那一行。

        番号在前、正文在后，两行够认出是哪一部；正文动辄五六行，整段摊开会把评分、标签
        和动作全推到折叠线以下。展开键和定位、同步那两枚长得一样、排在同一行最前面——它们
        都是围着这条标题的动作，管标题本身的那一枚离标题最近。夹在被折的文字末尾的话会一起
        被裁掉，所以那排键不行内跟在文字后面。折叠态量 scrollHeight 判溢出，没溢出就不画
        展开键；能折的标题文字本身也接点击，选中文字那一下不算。
        """
        self.assertPageContains(
            '<div class="detailtitle"><div class="stitle" data-reveal-line><span class="stitletext" data-detail-title>'
            '${srcBadge(it.location,it.cost,\'srcbig\')}${javTitleHtml(it)}${partLabelBadge(it,queueContext)}</span>'
            '<span class="srctools detailtitletools"><button type="button" data-title-fold hidden '
            'aria-expanded="false" aria-label="展开标题" title="展开完整标题">${icon(\'chevron-down\')}</button>'
            '${it.location===\'online\'?\'\':sourceToolButtons(it.id)}</span></div></div>')
        self.assertPageContains(".stitletext[data-foldable]{cursor:pointer}")
        self.assertCode("titleText.toggleAttribute('data-foldable',!titleFold.hidden);")
        self.assertCode("if(titleFold.hidden||String(getSelection()||''))return;")
        self.assertPageContains(
            ".stitletext{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow:hidden}")
        self.assertPageContains(".stitletext[data-expanded]{display:block;-webkit-line-clamp:unset;line-clamp:unset}")
        self.assertPageContains(".detailtitletools{display:flex;margin:6px 0 0;flex-wrap:nowrap}")
        self.assertPageContains(".detailtitletools:not(:has(button:not([hidden]))){display:none}")
        self.assertPageContains(".detailtitle .stitle{min-width:0;margin:0;line-height:1.75}")
        self.assertCode("if(!expanded)titleFold.hidden=titleText.scrollHeight<=titleText.clientHeight+1;")
        self.assertCode("titleFold.setAttribute('aria-label',expanded?'收起标题':'展开标题');")
        self.assertCode("titleFold.querySelector('use').setAttribute('href',expanded?'#i-chevron-up':'#i-chevron-down');")
        self.assertCode("titleFold.onclick=()=>{titleText.toggleAttribute('data-expanded');syncTitleFold()};")
        # 影院模式与普通视图之间切换会改标题栏宽度，溢出要跟着重判。
        self.assertCode("new ResizeObserver(syncTitleFold).observe(titleText);")

    def test_detail_metadata_uses_icons_instead_of_release_copy(self):
        self.assertPageContains('<span class="detailmetaitem">${icon(\'monitor\')}')
        self.assertPageContains('<span class="detailmetaitem">${icon(\'hard-drive\')}')
        self.assertPageContains('<span class="detailmetaitem">${icon(\'calendar\')}')
        self.assertPageContains('id="i-monitor"')
        self.assertPageContains('id="i-calendar"')
        self.assertPageLacks("发行 ${esc(it.release_date)}")

    def test_duplicates_page_is_part_of_the_combined_cleanup_section(self):
        # 数据管理、重复文件、垃圾文件是同一件事的三步，共用一个管理身份，
        # 所以进任何一屏管理条都停在「数据管理」上。
        self.assertRoute('/data-cleanup', "section:'cleanup'")
        self.assertRoute('/duplicates', "section:'cleanup'", "openDuplicates(push)")
        self.assertPageContains("return hit?.route.section||(state.state==='ads'?'cleanup':'');")
        # openManage('cleanup') 该开数据管理本身：靠 /data-cleanup 在表里排在前面。
        self.assertPageContains("const target=ROUTES.find(spec=>spec.section===section);")
        self.assertPageContains("async function openDuplicates(push=true)")

    def test_data_cleanup_groups_junk_duplicates_and_empty_folders_in_fieldsets(self):
        self.assertPageContains("async function openDataCleanup(push=true)")
        self.assertPageContains("route('/data-cleanup')")
        self.assertPageContains("${(sources.sources||[]).some(source=>['local','115','pikpak'].includes(source.location)&&source.roots?.length)?resourceSyncMarkup():''}")
        self.assertPageContains("fieldsetTitle('resourceBoxTitle','文件与记录核对')")
        self.assertPageContains("按馆藏记录逐条查找本地磁盘与网盘上的文件")
        self.assertPageContains("cloudPreferenceLocations(g.files,d.cloudLocations||[])")
        for path in ("'/api/ads?limit=1'", "'/api/duplicates?limit=1'", "'/api/sources'"):
            self.assertPageContains(path)
        # 标题是正文区的第一行，不用原生 legend——legend 会在上边框上开个缺口，
        # 卡片内容高度不同时那道缺口的位置也跟着不齐。垃圾文件与重复文件是顶上一排的读数卡。
        self.assertPageContains("fieldsetTitle('cleanupEmptyTitle','空文件夹与失效条目')")
        self.assertPageContains("junk:statCard('垃圾文件','file-archive',")
        self.assertPageContains("duplicates:statCard('重复文件','file-stack',")
        self.assertPageLacks("<legend>垃圾文件</legend>")
        self.assertPageContains('class="cleanupfieldset" data-geist-fieldset aria-labelledby=')
        self.assertPageContains('class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset')
        self.assertPageContains("api('/api/data-cleanup/empty-folders',{method:'POST',body:'{}'})")
        self.assertPageContains("保留来源根目录")
        # 这一屏会删账本行，检查那一步就得把条数写在脸上，确认框里也要说清不可撤销。
        self.assertPageContains("条文件已不在盘上的记录")
        self.assertPageContains("这一步不可撤销")
        self.assertPageContains(".cleanupfieldset>.geist-fieldset-content{flex:1;min-height:0;padding:20px}")
        # Geist 的 Fieldset 全框只有一条线，在底部操作条上方；标题底下不划线。
        self.assertPageContains("--fieldset-bar-h:52px;")
        self.assertPageContains(".geist-fieldset-title{margin:0 0 8px;")
        self.assertPageLacks(".geist-fieldset-header")
        self.assertPageContains(".cleanupfieldset>.geist-fieldset-footer{box-sizing:border-box;"
                                "min-height:var(--fieldset-bar-h);")
        # 按钮一律靠右；左边有说明时说明推到最左。
        self.assertPageContains("justify-content:flex-end;gap:8px;")
        self.assertPageContains(".resourcesyncfooter>p,.resourceapplyrow>p{min-width:0;margin-right:auto}")
        self.assertRoute('/data-cleanup', "openDataCleanup(push)")

    def test_fieldset_bars_keep_one_row_and_one_button_shape_on_narrow_screens(self):
        """窄屏下操作条仍是一行，按钮按内容宽、填 --surface，不铺满也不换第二种样式。

        证据：`docs/reference-snapshots/vercel-geist-fieldset-scroller-empty-state.md`
        的 2026-09-02 追加块——375px 视口下 Geist 的 Fieldset footer 仍是
        `flex-direction:row`、`nowrap`，min-height 56px 按说明行数长到 65/85/105px，
        12 颗按钮宽 70–186px，没有一颗铺满。640px 以下把条子竖过来、按钮
        `width:100%` 是我们自己加的，不是 Geist 的做法。

        底色同理：条子是 `--page`，按钮填比它更亮的 `--ground` 才分得出来，
        与 `.geist-button` 的次级档、同一页「网盘与账本」的 `.resourceaction` 是同一颗按钮。
        """
        self.assertPageContains(".cleanupfieldset>.geist-fieldset-footer{box-sizing:border-box;"
                                "min-height:var(--fieldset-bar-h);")
        self.assertPageContains("padding:12px 12px 12px 20px;")
        self.assertPageContains(".resourcesyncfooter,.resourceapplyrow{box-sizing:border-box;"
                                "min-height:var(--fieldset-bar-h);")
        # 说明能被压窄并换行，按钮不参与压缩。
        self.assertPageContains(".resourcesyncfooter>p,.resourceapplyrow>p{min-width:0;margin-right:auto}")
        # 排除下拉触发器：它是 .cleanupfieldset 里的一个 button，但形状属于输入控件，
        # 那圈线要留着。零权重的 :where() 才不会反过来压过 .geist-button.primary。
        self.assertPageContains(".cleanupfieldset button:where(:not(.gselectfield)){"
                                "box-sizing:border-box;flex:none;min-height:32px;")
        self.assertPageContains("background:var(--ground);color:var(--ink-2);display:inline-flex;")
        self.assertPageContains(".cleanupfieldset button:where(:not(.gselectfield)):hover{"
                                "background:color-mix(in srgb,var(--ink) 8%,var(--ground));"
                                "color:var(--ink)}")
        self.assertPageLacks(".resourcesyncfooter button{width:100%;justify-content:center}")
        self.assertPageLacks(".resourcesync .resourcesyncfooter{align-items:stretch;flex-direction:column}")
        self.assertPageLacks(".resourcesync .resourceapplyrow{align-items:stretch;flex-direction:column}")
        self.assertPageLacks(".resourcesync #resourceApply{width:100%}")

    def test_each_cleanup_card_shows_the_breakdown_already_in_its_payload(self):
        """每张卡在主数字下再给一行分项，用的是同一份 payload 里已有的数字。

        卡片只有一个总数时，一列 fieldset 里剩下的全是空白；分项本来就在
        `/api/ads` 的 counts、`/api/duplicates` 的 reclaimable 和 `/api/review?counts=1`
        里，不必为第二行多发请求。空的分项行整行不占位——没有分项的卡不该
        比别人多留一段白。
        """
        cleanup = self.page.split("async function openDataCleanup(", 1)[1].split(
            "let dupData=null;", 1)[0]
        self.assertIn("JUNK_KIND_OPTIONS.filter(([key])=>key&&Number(junkCounts[key])>0)", cleanup,
                      "垃圾文件没有按类型给分项")
        self.assertIn("已忽略 ${Number(junk.dismissed_total).toLocaleString()}", cleanup)
        self.assertIn("可回收 ${fmtSize(duplicates.reclaimable||0)}", cleanup)
        self.assertIn("'没有重复内容'", cleanup, "0 组时别写成「0 组 · 0 个文件」")
        self.assertIn('<span class="cleanupmeta" data-cleanup-meta="${section}">', cleanup)
        counts = self.page.split("async function paintDataManagementCounts()", 1)[1].split(
            "let dupData=null;", 1)[0]
        self.assertIn("REVIEW_LABELS[key]||key", counts, "人工复核的分项得是分类名")
        self.assertIn("`其余 ${rest.toLocaleString()}`", counts)
        self.assertIn("`占用 ${fmtSize(data.bytes||0)}`", counts, "回收站要说清空能腾出多少")
        self.assertPageContains(".cleanupmeta:empty{display:none}")
        # 三个「· 在线」徽章换成一行来源名：在线与否是资源同步那块的读数，
        # 在空文件夹卡上只有离线时才改变结论。来源行带官方站标，离线的归到同一枚标记后。
        self.assertPageLacks("class=\"cleanupsource\"")
        self.assertPageLacks(".cleanupsources{")
        self.assertIn("offline.length?`${offline.map(sourceBadge).join('')}<span class=\"cleanupsourcemark cleanupsourcelost\">离线</span>`", cleanup)
        self.assertIn("<strong>${online.length.toLocaleString()} 个来源可扫描</strong>", cleanup)
        # 单列布局里高度由内容决定，和同页「网盘与账本」一致；三列时的对齐地板
        # 到了单列只剩下把每张卡撑出一段空白。
        self.assertPageLacks("min-height:176px")

    def test_duplicate_batch_keeps_one_per_cluster_not_one_per_code(self):
        # 每组各自选 keeper：合集与分卷已经在数据层拆成不同簇，界面不能再按番号合并。
        self.assertPageContains("function duplicateVictims(groups,keep)")
        self.assertPageContains("const flag=keep==='longest'?'is_longest':'is_largest'")
        self.assertPageContains("for(const f of g.files)if(f.id!==keeper.id)ids.push(f.id)")
        self.assertPageContains("g.files.filter(f=>f.location===keep)")
        self.assertPageContains('data-dup-all="${loc}"')
        self.assertPageContains('cloudPreferenceLocations(groups.flatMap(g=>g.files),d.cloudLocations||[])')

    def test_duplicate_group_can_be_entirely_recycled_when_every_file_is_an_ad(self):
        self.assertPageContains("if(keep==='all'){for(const f of g.files)ids.push(f.id);continue}")
        self.assertPageContains('data-dup-keep="all"')
        self.assertPageContains("all:'零个文件'")

    def test_duplicate_rows_show_the_full_path_without_losing_source_and_size(self):
        self.assertPageContains('class="mono duppath" data-middle-truncate title="${esc(f.path||\'\')}"')
        self.assertPageContains("${esc(f.path||'')}")
        self.assertPageContains('.duppath{grid-column:2/-1;min-width:0;overflow:hidden')

    def test_resource_identifiers_use_geist_middle_truncation(self):
        """文件名和路径保留首尾；标题、说明仍按语义使用末尾省略。"""
        self.assertPageContains("import { initMiddleTruncate } from './js/middle-truncate.js'")
        self.assertPageContains("initMiddleTruncate(document)")
        for consumer in (
                'class="dupname" data-middle-truncate',
                'class="mono duppath" data-middle-truncate',
                'id="photoDetailTitle" data-middle-truncate',
                '<b data-middle-truncate>${esc(javDisplayName(media))}</b>',
                '<b data-middle-truncate>${esc(javDisplayName(x))}</b>',
                'class="t resourcecardtitle" data-middle-truncate',
                'class="t junkcardtitle" type="button" data-junk-open data-middle-truncate',
                'class="t junkcardtitle" data-middle-truncate',
                # 死链表里的地址：`/official/talent/X` 与 `/talent/X` 的差别就在尾部，
                # 尾部省略会把这张表要回答的东西切掉。省略挂在里面那个 span 上，
                # 外链标才留得住：中缩靠改写 textContent 实现，同一节点里的图标会被抹掉。
                '<span data-middle-truncate>${esc(item.url)}</span>'):
            self.assertPageContains(consumer)
        # 高清版目标页、统计页与复核页归 React 子树，由 frontend 的用例覆盖。
        self.assertEqual(self.app_js.count("data-middle-truncate"), 9)
        self.assertEqual(self.app_js.count('class="mixitemtext"'), 3)
        self.assertEqual(self.app_js.count("data-truncate-end"), 4)
        self.assertPageContains("new Intl.Segmenter(undefined,{granularity:'grapheme'})")
        self.assertPageContains("resizeObserver=new ResizeObserver")
        self.assertPageContains("context.font=style.font||`${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`")
        self.assertPageContains("const ELLIPSIS='…'")
        self.assertPageContains("element.setAttribute('aria-label',state.full)")
        self.assertPageContains("event.clipboardData.setData('text/plain',state.full)")
        self.assertPageContains("export { initMiddleTruncate, middleTruncateText }")
        self.assertPageContains("*[data-middle-truncate]{min-width:0;overflow:hidden;white-space:nowrap;text-overflow:clip}")

    def test_every_end_truncation_selector_is_explicitly_reviewed(self):
        """新增 CSS 省略必须先决定它是语义文本，还是应改用 MiddleTruncate。"""
        reviewed_end_selectors = {
            ".alphatag span:first-of-type", ".av .nm",
            ".entitylinklabel",
            ".fauthor .fsource.frow>b", ".fauthorhead b",
            # 作者是展示名，尾部省略；完整身份保留在 title。
            ".followbyline .followauthor",
            ".followpageaction .fmeta",
            ".fsechead .fmeta",
            ".frow>b",
            ".fvkind", ".idname",
            ".meta .t", ".meta .who", ".mixcopy b,.mixcopy span",
            # 小窗信息栏与播放器右键菜单：标题、来源和菜单标签都是语义文本，尾部省略。
            ".miniplayertitle", ".miniplayersub", ".playermenuitem>span",
            ".mixitemtext [data-truncate-end]", ".mixqueuehead h2",
            ".ncard .meta .why",
            ".pickrowtext b",
            ".playerstats dd", ".playerstatsmetric>span",
            # 详情标题折成两行，尾部省略；溢出时旁边那枚展开键给出全文。
            ".stitletext",
            ".relatedperson .nm", ".searchoption span",
            ".sgrid.mixgrid>.mixqueue .mixqueuehead span", ".sidebarorderlabel>b",
            ".tastesummary>small",
            ".gselectfield>span",
            ".tagpickitem .pickname", ".tg",
            ".tokui .toktitle", "body[data-density=\"dense\"] .card .ctags .tg",
            "body[data-density=\"dense\"] .card .meta .t",
        }
        css_without_comments = re.sub(r"/\*.*?\*/", "", self.css, flags=re.S)
        actual = set()
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css_without_comments):
            truncates = re.search(
                r"text-overflow\s*:\s*ellipsis|-webkit-line-clamp\s*:(?!\s*unset)",
                body,
            )
            if truncates:
                actual.add(" ".join(selector.split()))
        self.assertEqual(reviewed_end_selectors, actual)

    def test_duplicate_removal_is_reversible(self):
        # 只能进回收站；永久删除仍得从回收站单独执行。
        self.assertPageContains("operation:'dispose'")
        self.assertPageLacks("operation:'delete'},{method:'POST'}")
        self.assertPageContains("记录可从回收站还原")

    def test_duplicate_batches_respect_the_two_hundred_id_cap(self):
        self.assertPageContains("for(let i=0;i<ids.length;i+=200)")

    def test_duplicate_rows_show_the_evidence_grade(self):
        # sha1 齐全才敢说「一致」，否则只是时长推断——界面必须把差别显示出来。
        self.assertPageContains("g.identical?'<span class=\"dupflag ok\">sha1 一致</span>'")
        self.assertPageContains("时长推断")

    def test_review_page_exposes_the_new_candidate_categories(self):
        # 这三类此前只落在 CSV 里没有入口，复核负担等于丢回给用户去翻文件。
        self.assertPageContains("western_identity:'西方身份回配'")
        self.assertPageContains("code_creators:'番号目录存疑'")
        self.assertPageLacks("cover_sources:'封面来源'")
        self.assertPageContains("fc2_markings:'FC2 评论标记'")
        self.assertPageContains("fc2_similarity:'FC2 跨号相似'")
        self.assertPageContains("video_endcards:'片尾/出处证据'")

    def test_reader_review_uses_the_writer_mirror_without_offering_fake_writes(self):
        """只读端也进得来：`/healthz` 的判定和写入端地址一起交给岛，由它决定能不能写。"""
        self.assertPageContains("import('/dist/peach-ui.js'),surfaceApi(surface,'/healthz')]);")
        self.assertPageContains("?new URL('/review',runtime.ledger_writer_origin).href:''")
        self.assertPageContains("readOnly:!!runtime?.ledger_read_only,")
        self.assertPageContains("readOnlyMessage:runtime?.ledger_read_only_message||'本机当前只能浏览',")
        self.assertPageContains("writerUrl:writer,")

    def test_index_pages_drop_the_home_filter_bars_and_back_button(self):
        # 艺人/标签索引和资料页一样是「专注看某一类实体」的表面。
        self.assertCode(
            "body.entity-open #tiers,body.entity-open #tagbar,\nbody.index-open #tiers,body.index-open #tagbar{display:none}")
        self.assertPageLacks('id="iClose"', "顶栏入口本身就是返回路径")
        self.assertPageLacks("$('#iClose').onclick")

    def test_entity_and_follow_pages_share_round_video_image_buttons(self):
        """资料页切视频、照片、名册和关注页切视频、图片是同一组圆键。

        资料页那一组住在筛选浮层最左端，隔一道竖杠再是四枚观看状态：它换掉的是整页内容，
        夹在视图和标签中间会被读成标签那排的第一枚。只有多于一档时才出——一枚孤零零的键
        没有可切的对象。关注页那两枚是浮层下排右端的控件，跟首页下排右端的排序键同一个位置。
        索引页的下划线 Tabs 是另一个控件，切的是地址。
        """
        self.assertPageContains('id="i-pics" viewBox="-1.6 -1.6 19.2 19.2" fill="currentColor" stroke="none"')
        self.assertPageContains('export function mediaViewButtonsHtml({')
        self.assertPageContains('class="mediaviewbutton" type="button" data-media-view="${esc(value)}"')
        self.assertPageContains("export function boardTabsHtml(items,{active='',attr='data-tab',label='页面视图',className='',panel=''}={}){")
        self.assertPageContains('<span class="board-tab-count">${esc(Number(count).toLocaleString())}</span>')
        self.assertPageContains('<div class="board-local-nav board-tabs${className?` ${esc(className)}`:\'\'}" role="tablist" aria-label="${esc(label)}">')
        self.assertCode("const mediaToggle=(photoCount||roster.length)?mediaViewButtonsHtml({\n"
                        "    active:entityViewNow(kind),")
        self.assertPageContains("videoCount:d.asset_count,imageCount:photoCount,")
        self.assertPageLacks("entitytabs")
        # 这一组是整条上唯一住在滚动层外面的东西——余下两格用的就是首页那两个类名，同一份摆法两页共一处。
        self.assertPageContains('<section class="entitytagbar" aria-label="媒体与标签">${mediaToggle}'
                                """${mediaToggle?'<span class="sep" aria-hidden="true"></span>':''}"""
                                '<div class="filterscroll"><div class="viewpills entityviews"')
        self.assertPageContains('<div class="tagscroll entitytags">${tags}</div></div></section>')
        # 关注页的读数照首页那条写，右端是这一页的动作键与排序键；媒体类型不在这一排，
        # 它跟资料页一样住在上排最左。
        self.assertPageContains('<div class="count followcount"><span class="mono">${total.toLocaleString()} 项更新 · 显示 ${visible.length.toLocaleString()}</span>'
                                "${followFeedControlsHtml()}</div>")
        self.assertPageContains("$('#stats').querySelectorAll('.followfilters [data-media-view]')")
        self.assertPageContains("button.dataset.mediaView")
        self.assertPageContains(".mediaviewbuttons .mediaviewbutton{display:grid;place-items:center;flex:0 0 var(--filterItemH);width:var(--filterItemH);height:var(--filterItemH);padding:0;")
        self.assertPageContains(".mediaviewbuttons .mediaviewbutton svg{width:20px;height:20px")
        self.assertPageContains("border:0;border-radius:50%;background:transparent")
        self.assertPageLacks(".entitytags .entitymediatoggle")
        self.assertPageLacks(".followmediaicons .entitymediatoggle")
        self.assertPageLacks('<div class="mediatabs" hidden></div>')

    def _js_function(self, name):
        """截出一个 JS 函数的正文，用于对「这个函数做了什么」下断言。

        按整页源码找子串很容易断在无关的地方；这里只取从函数头到下一个顶层函数
        之间的部分，断言的对象就是它自己的实现。
        """
        body = self.page[self.page.index("function " + name + "("):]
        stops = [at for at in (body.find(chr(10) + "async function "),
                               body.find(chr(10) + "function ")) if at > 0]
        return body[:min(stops)] if stops else body

    def test_the_tags_page_separates_the_local_and_online_vocabularies(self):
        """标签页有两套词表，必须分开。

        本地是 ledger 里的中文标签，在线是关注页那套 booru 英文标签：计数含义
        （作品数 / 更新数）、类别划分和点击后去哪儿三者都不同，混成一列只会互相
        说谎。字母表对在线那套正合适——实测 3582 个在线标签全是 ASCII，能分出
        # 和 A–V；本地全是中文，做字母表只会得到一个「中文」分组。
        """
        self.assertCode("const INDEX_SCOPES=[['local','本地','hard-drive'],['online','在线','rss']];")
        self.assertCode("function tagScopeTabsHtml(){return scopeTabsHtml(tagIndexScope,'data-tag-scope','词表')}")
        self.assertCode("$('#index').querySelectorAll('[data-tag-scope]').forEach(b=>b.onclick=()=>{\n"
                        "    if(tagIndexScope===b.dataset.tagScope)return;\n"
                        "    selectTab(b);\n"
                        "    tagIndexScope=b.dataset.tagScope;")
        self.assertPageContains("if(tagIndexScope==='online')tagIndexMode='alphabet';",
                                "切到在线应当直接给出字母表，那才是它的形态")
        self.assertPageContains("const onlineTags=kind==='tags'&&tagIndexScope==='online';")
        self.assertPageContains("'/api/follow/tags?types=all&limit='+indexLimit+'&offset='+offset")
        self.assertPageContains("const ONLINE_TAG_CATEGORIES=")
        self.assertPageContains("onlineTags?'r34-'+(x.cat||'unknown')")
        self.assertPageContains("const categoryOptions=onlineTags?ONLINE_TAG_CATEGORIES:TAG_CATEGORIES")
        # 多选面板是本地目录语义；分类栏两套词表都显示。
        self.assertPageContains("if(kind==='tags'&&!onlineTags){")
        self.assertPageContains(".alphatag.r34-artist")
        self.assertPageContains(".alphatag.r34-character")
        self.assertPageContains(".alphatag.r34-copyright")
        self.assertPageContains(".alphatag.r34-metadata")
        self.assertPageContains("indexheading")
        self.assertPageContains("['local','本地','hard-drive']")

    def test_the_performers_page_separates_the_local_and_online_rosters(self):
        """艺人页也有两套名册：本地是账本里绑了实体的人，在线是关注来源里的作者。

        两边数的不是同一样东西（本机片数 / 还没下载的更新数），点开去的也不是同一页
        ——在线那一档的人还没进账本，没有资料页可去，他名下那批东西全在关注页上。
        所以跟标签页一样用页面级的 Tabs 分开，而不是在同一列里混着排。
        """
        self.assertCode("let performerIndexScope='local';")
        self.assertCode("const onlineAuthors=kind==='performers'&&performerIndexScope==='online';")
        self.assertPageContains("if(onlineAuthors)indexQuery.set('scope','online');")
        self.assertPageContains("?'/api/follow/authors?limit='+indexLimit+'&offset='+offset+\n"
                                "      (q?'&q='+encodeURIComponent(q):'')")
        self.assertCode("$('#index').querySelectorAll('[data-performer-scope]').forEach(b=>b.onclick=()=>{\n"
                        "    if(performerIndexScope===b.dataset.performerScope)return;\n"
                        "    selectTab(b);\n"
                        "    performerIndexScope=b.dataset.performerScope;")
        # 选择模式拼的是目录批量操作，对还没进账本的人一条都不成立。
        self.assertPageContains("if(performerIndexScope==='online')setSelectMode(false,false);")
        # 刷新和后退都该回到同一档。
        self.assertPageContains("if(kind==='performers')performerIndexScope=params.get('scope')==='online'?'online':'local';")
        # 一格的形状跟本地那一格共用，只有圆里那张图换成来源站点给的地址。
        self.assertCode('''  return `<button class="icell" data-follow-author="${esc(x.key)}" data-kind="performer">''')
        self.assertPageContains('''<span class="ring" data-fit-native="portrait"><span class="ini">${esc(initial)}</span>${image}</span>''')
        self.assertPageContains("imageFallbackAttrs({fallbacks:[x.avatar_fallback||'']})")
        self.assertPageContains("const peopleHtml=items=>onlineAuthors?items.map(onlineAuthorCellHtml).join(''):items.map(x=>")
        # 点开去关注页，不是去一个不存在的资料页。
        self.assertCode("  root.querySelectorAll('[data-follow-author]').forEach(b=>b.onclick=()=>{\n"
                        "    followTags=new Set();followProviders=new Set();followWorks=new Set();\n"
                        "    followMediaView='videos';followFilter='';\n"
                        "    followAuthors=new Set([b.dataset.followAuthor]);\n"
                        "    $('#index').hidden=true;route(followViewPath());openFollow(false)});")
        self.assertPageContains("online:onlineTags||onlineAuthors")

    def test_the_follow_feed_controls_are_shuffle_then_the_sort_keys(self):
        """下排右端：换一批、图片墙上的「仅显示图片」，然后才是排序键。

        「换一批」换的是整页：三排取样和列表次序都读同一粒种子，列表归服务端排所以要
        重取；排序键上没有「随机」这一档，进随机就是三枚键都抬起来，按任一枚就离开。
        去问一遍来源那枚不在这一排：它是这一页唯一联网的动作，站在页头当主按钮。
        """
        self.assertCode("function followFeedControlsHtml(){\n"
                        "  return sortControlsHtml({\n"
                        "    shuffleId:'followShuffle',shuffleClass:'',items:FOLLOW_FEED_SORTS,")
        self.assertPageContains("    extra:followMediaView==='images'?photoControlsHtml({follow:true}):''});")
        self.assertPageLacks('class="followrecheck"')
        self.assertPageContains("followSeed=Number(rollSeed());followDiscoverySeed=followSeed;followSort=FOLLOW_RANDOM_SORT;applyFollowView()};")
        # 种子跟着地址走：刷新和后退回到的是同一批次序；没带种子的随机链接照样能开。
        self.assertPageContains("if(followSort===FOLLOW_RANDOM_SORT)params.set('seed',String(followSeed));")
        self.assertPageContains("followSort=sort===FOLLOW_RANDOM_SORT||FOLLOW_FEED_SORTS.some(([key])=>key===sort)?sort:'new';")
        self.assertPageContains("+(followSort===FOLLOW_RANDOM_SORT?`&seed=${followSeed}`:'')")
        # 槽位只剩 extra 一个：排序键一律排在最末，挨着它说明的那批内容。
        self.assertPageContains("export function sortControlsHtml({items=[],renderItem=String,extra='',"
                                "shuffleId='',shuffleClass='entitybatch'}={}){")
        self.assertPageLacks("${items.map(renderItem).join('')}${after}")
        # 三档排序，每一档的方向词各说各的那一列。
        self.assertCode("const FOLLOW_FEED_SORTS=[['new','更新时间'],['hot','热度'],['dur','时长']];")
        self.assertPageContains("dur:['从长到短','从短到长']")
        self.assertPageContains("const next=nextSortState(button.dataset.followSort,followSort,followDir,FOLLOW_FEED_DIR_WORDS);")
        # 排序归服务端：分页在它那一侧，浏览器只拿到当前这几页。
        self.assertPageContains("+(followSort!=='new'?`&sort=${followSort}`:'')")
        self.assertPageContains("+(followDir!=='desc'?`&dir=${followDir}`:'');")
        # 「仅显示图片」是一枚 30px 见方的图标开关，不是 `.batchaction`：蓝色留给换一批，开着时
        # 垫的是筛选条那块滑动玻璃（跟版式分段器、媒体那一档同一块料），关着走排序键的淡字。
        # 字形是「收起说明」，不跟左边媒体那一档的图片字形撞。
        self.assertPageContains('class="followimagesonly" data-follow-images-only aria-pressed="${!!appSettings.followImagesOnly}" title="仅显示图片" aria-label="仅显示图片">${icon(\'captions-off\')}</button>')
        self.assertPageContains('<symbol id="i-captions-off" viewBox="0 0 24 24">')
        self.assertPageContains(".count .sorts .followimagesonly{width:30px;padding:0;display:inline-grid;place-items:center;position:relative}")
        self.assertPageContains(".count .sorts .followimagesonly svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;position:relative;z-index:1}")
        # 玻璃挂在这枚键自己身上：旁边的分段器是插进文档后才由观察器换几何的，钉在外框坐标上
        # 的玻璃量早一步就跟键错开半个身位；挂在键上坐标恒为零。
        self.assertPageContains("imagesonly:{selector:'.followcount .sorts',host:'.followimagesonly',\n"
                                "              pressed:'[data-follow-images-only][aria-pressed=\"true\"]'},")
        self.assertPageContains("function viewGlideGeometry(pill,within='.board-filter-frame'){\n  const host=pill.closest(within);if(!host)return null;")
        self.assertPageContains("const box=viewGlideGeometry(active,GLIDE_ROWS[kind].host);")
        self.assertPageContains("imagesOnly.setAttribute('aria-pressed',String(appSettings.followImagesOnly));\n    syncViewGlide(false,null,'imagesonly')};")
        self.assertPageContains("Object.keys(GLIDE_ROWS).forEach(kind=>syncViewGlide(false,null,kind))},{passive:true});")
        # 落位在搭完外框之后：wirePhotoControls 跑在 mountFilterFrame 之前，那时量不到外框。
        self.assertPageContains("  syncViewGlide(false,null,'imagesonly');\n  scheduleStickySurfaces();")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertNotIn(".followimagesonly[aria-pressed=", board)
        self.assertNotIn("var(--board-blue);color:#fff;font-weight:600}", board)
        self.assertNotIn(".followrecheck", board)
        # 等数据时换批键自己画，跟首页同一个忙态：标记挂在读数那一排上，选择器认两页的键。
        self.assertPageContains("$('#stats').querySelector('.followcount')?.setAttribute('aria-busy','true');")
        self.assertPageContains('.count[aria-busy="true"] :is(#batchAction,#followShuffle) svg,')
        self.assertPageLacks("followconditionmenu")

    def test_check_updates_is_the_primary_action_in_the_follow_page_head(self):
        """页头右端两枚：「管理关注」次级，「检查更新」是这一页唯一联网的动作，也是唯一的
        主按钮。一个来源都没有时不出它——空态里那枚「添加关注」已经是主按钮。"""
        self.assertPageContains('<div class="followhead"><h2 class="disp pagetitle">关注</h2><span class="fheadactions">')
        self.assertPageContains('<button class="fbtn fcheck" data-follow-manage>${icon(\'settings\')}管理关注</button>${sources.length')
        self.assertPageContains('?`<button class="fbtn primary" data-follow-recheck aria-label="检查每个来源的更新">检查更新</button>`:\'\'}</span></div>')
        self.assertPageContains("wireFollowRecheck($('#stats').querySelector('[data-follow-recheck]'));")
        self.assertPageContains(".fheadactions{display:inline-flex;align-items:center;gap:8px;flex:none}")

    def test_the_follow_filters_in_effect_reuse_the_home_intersection_bar(self):
        """生效的筛选摊在浮层正下方，用的就是首页那条交集筛选条。

        三页问的是同一件事——现在这一屏被哪几个条件框住了——同一颗 `.cb`、同一枚撤销
        键、同一个「全部清除」，画成三种样子就得认三遍。位置也照首页：这一条从无到有
        会把下面的东西整块推下四十像素，放在浮层上面的话被推的是那块吸顶的玻璃和它
        上面的两排头像，按一枚标签半屏东西跟着挪。
        """
        watch = self.page.split("function renderFollow(){", 1)[1].split(
            "function followBackfillState", 1)[0]
        combo = watch.index('<div class="combo followcombo">')
        self.assertLess(watch.index('<div class="count followcount">'), combo,
                        "交集筛选条必须排在浮层下排之后，否则被推下去的是那块吸顶的玻璃")
        self.assertLess(combo, watch.index('<div class="followlist'))
        self.assertPageContains('''<span class="cb">${row.kind==='标签'?'':esc(row.kind)+' '}${esc(row.label)}'''
                                '''<b data-follow-drop="${esc(row.key)}" data-follow-drop-kind="${esc(row.kind)}">✕</b></span>''')
        self.assertPageContains("""+`<button class="clr" type="button">全部清除</button>`;""")
        # 四个维度各有自己的 Set，所以按键上带着 kind：同一个字符串在两个维度里都可能
        # 出现，只认 key 会撤错那一边。
        self.assertCode("    const row=followConditions().find(item=>item.key===button.dataset.followDrop\n"
                        "      &&item.kind===button.dataset.followDropKind);")
        self.assertPageContains("followAuthors.clear();followProviders.clear();followTags.clear();followWorks.clear();apply();")
        self.assertPageContains("wireFollowConditions($('#stats').querySelector('.followcombo'),applyFollowView);")

    def test_the_tag_filters_live_in_the_home_glass_frame(self):
        """标签页的类型药丸、读数、字母跳转和视图切换收进首页那块玻璃浮层。

        上排是类型药丸，下排是读数加按首字跳转加视图切换；外框直接写成带槽位标记
        的 HTML，随每次筛选整块重画。浮层住在 `#indexFilters` 里，那个父级只有浮层
        自己那么高，sticky 会被它卡死——`display:contents` 让它退出盒树。
        """
        self.assertPageContains("function tagFilterFrameHtml(categories,readout,groups){")
        self.assertCode("  const pills=categories.map(([key,label])=>filterChipHtml(label,\n"
                        "    {attr:'data-tag-category',value:key,selected:tagIndexCategory===key,className:key})).join('');")
        self.assertPageContains('<div class="board-filter-frame" data-filter-frame>\n'
                                '    <div class="tagbar tagcategories" data-filter-row="top" aria-label="标签类型">'
                                '<div class="filterscroll"><div class="tagscroll" data-filter-slot="tags">${pills}</div></div></div>\n'
                                '    <div class="count tagcount" data-filter-row="bottom">'
                                '<span class="mono" id="indexCount" data-filter-slot="readout">${readout}</span>${jump}'
                                '<div class="sorts" data-filter-slot="controls">${view}</div></div></div>')
        self.assertPageContains("#indexFilters{display:contents}")
        self.assertPageLacks("tagfilters")
        # 药丸上那枚色点说类型，选中那一枚的线和填充取自己的类型色。
        self.assertPageContains(".tagcategories .pill::before,.alphatag::before{content:\"\";width:7px;height:7px;border-radius:50%;")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-filter-frame .tagcategories .pill{border:1px solid var(--glass-low);background:transparent}", board)
        # 标签页的读数只住在浮层里，页头不再重复一遍。
        self.assertPageContains("${people?`<span class=\"mono\" id=\"indexCount\">${countText}</span>`:''}")
        self.assertCode("    if(people)popCount($('#indexCount'),countText);")

    def test_the_alphabet_is_one_card_per_letter_with_a_jump_row(self):
        """每个首字一张卡：字头是卡的标题，右边挂计数徽标；一行一枚标签、36px 高、8px
        圆角，取的是 Board 排名行那一档身量。浮层下排那排跳转键按首字排开，落点是卡。"""
        self.assertPageContains('`<section class="alphagroup" data-alpha-group="${i}"><h3>${letter}'
                                '<span class="board-tab-count">${items.length.toLocaleString()}</span></h3>'
                                '<div class="alphalist">')
        self.assertPageContains('<nav class="alphajump" aria-label="按首字跳转">')
        self.assertPageContains('`<button type="button" data-alpha-jump="${i}">${esc(letter)}</button>`')
        self.assertCode("$('#index').querySelectorAll('[data-alpha-jump]').forEach(b=>b.onclick=()=>{\n"
                        "    $('#index').querySelector(`[data-alpha-group=\"${b.dataset.alphaJump}\"]`)\n"
                        "      ?.scrollIntoView({block:'start',behavior:'smooth'})});")
        # 卡顶给吸顶的浮层让位；载入更多后首字可能变多，浮层整块重画让跳转键跟上。
        self.assertPageContains(".alphagroup{padding:16px 20px 12px;border-radius:var(--floating-radius);background:var(--ground);\n"
                                "  scroll-margin-top:calc(var(--topH) + 124px)}")
        self.assertPageContains(".alphatag{display:flex;align-items:center;justify-content:flex-start;gap:9px;height:36px;")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".alphagroup{border-radius:16px;box-shadow:none}", board)
        self.assertIn(".alphatag{border-radius:8px}", board)
        self.assertCode("$('#indexFilters').innerHTML=tagFilters();wireIndexControls(kind);paintTagIndexSelection()}")
        # 骨架照最终结构：字头占位加一张分组卡。
        self.assertPageContains('<section class="alphagroup"><span class="indexletterskeleton skeleton"></span>')

    def test_the_people_index_cells_are_board_cards(self):
        """索引格是 secondary 底、16px 圆角、12px 内边距的卡，名字 Body Medium、计数 Caption。
        大图版式里头像改 10px 圆角、文字左对齐。载入更多是 36px／10px 圆角的 secondary Button。"""
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".icell{gap:8px;padding:12px;border-radius:16px;background:var(--ground)}", board)
        self.assertIn(".icell .nm{font-size:14px;line-height:20px;font-weight:500}", board)
        self.assertIn(".icell .n{font:var(--board-caption);color:var(--muted)}", board)
        self.assertIn('.igrid[data-layout="big"] .icell .ring{border-radius:10px}', board)
        self.assertIn(".indexmore,.entitymore{min-height:36px;height:36px;padding:0 12px;border-radius:10px;", board)

    def test_an_alphabet_entry_stays_on_one_line(self):
        """一枚标签占一行，长名字截断。

        `text-overflow:ellipsis` 少了 `white-space:nowrap` 就永远不触发：实测在线
        词表里 clothed_female_nude_male 一类名字改成折行，同一行其它标签被拉高，
        两列的行高也对不齐。
        """
        self.assertPageContains(
            ".alphatag span:first-of-type{overflow:hidden;text-overflow:ellipsis;"
            "white-space:nowrap;flex:1}")

    def test_the_index_header_moves_the_switches_to_their_own_row_when_narrow(self):
        """表头一行放不下五样东西，挤在一行时每样都被压成竖排两行。

        实测 459px 视口：标题「标签」两字上下叠、计数叠成两行、四个开关按钮各自
        叠成两行、过滤框被压成 0 宽。760px 以下改成标题与过滤框一行、开关另起一行。
        """
        self.assertPageContains("@media (max-width:760px){\n  .index .ihead{flex-wrap:wrap}")
        self.assertPageContains("  .indexheading,#indexCount{white-space:nowrap}")
        # 换行位靠一个零高的伪元素占满整行，开关的 order 排在它之后。
        self.assertPageContains('  .index .ihead::after{content:"";order:2;flex-basis:100%;height:0}')
        self.assertPageContains("  .index .ihead .geist-search{order:1}")
        self.assertPageContains("  .index .ihead .iconswitch{order:3;flex:none}")

    def test_the_two_filled_glyph_icons_say_what_a_stroked_icon_cannot(self):
        """字母表是 Aa，播放列表是队列。

        `list-filter` 的本义是筛选，只有源筛选那一处该用它。这两枚取 Phosphor
        regular，填充声明写在 symbol 上——全局 svg 是
        `stroke:currentColor;fill:none`，只补 path 会让填充图标整枚不可见。
        """
        self.assertPageContains("['alphabet','字母表','text-aa']")
        self.assertPageContains("['playlists','播放列表','playlist'],")
        self.assertPageContains("emptyState('playlist','还没有播放列表'")
        self.assertPageContains('aria-label="编辑播放列表">${icon(\'playlist\')}')
        self.assertPageContains('title="加入播放列表">${icon(\'playlist\')}')
        # 关注管理的来源筛选归 React 之后用 Remix 的漏斗，含义还是筛选。
        self.assertIn("leadingIcon={RiFilter3Line}",
                      self.read_react("follow-manage/add-source.tsx"))
        for symbol in ("text-aa", "playlist"):
            self.assertRegex(
                self.page,
                rf'<symbol id="i-{symbol}" viewBox="[-\d. ]+" fill="currentColor" stroke="none">')
        self.assertPageContains("Phosphor 2.1.1 regular, MIT")
        self.assertPageLacks("i-a-large-small")

    def test_each_glyph_names_the_thing_it_sits_next_to(self):
        """一枚字形只代表一个意思，同一个意思也只有一枚字形。

        一枚字形背两个意思时，用户在一处学会的含义会在另一处骗他，所以各归各的：
        `refresh-cw` 只归「去问一遍来源有没有更新」，`database` 只归管理入口，
        `folder-open` 只归打开位置，`play` 只归真的起播，音量键不去标音频文件。
        这条逐枚钉住归属。

        `i-clock` 没有使用者，是用户点名留的备用件，不要当死代码清掉。
        """
        # 文件类型标的是文件，不是打开动作，也不是音量。
        self.assertPageContains("['archive','压缩包','file-archive'],['audio','音频','file-audio']")
        self.assertPageContains("archive:['压缩包','file-archive'],")
        self.assertPageContains("audio:['音频','file-audio'],")
        # 「加载更多」往下接一页，方向由字形给出。
        self.assertPageContains("data-follow-more>${icon('chevron-down')}加载更多</button>")
        # 转圈只剩「去问来源有没有更新」这一个意思。此前九处动作共用它，读下来全是
        # 「刷新」，可它们分别是洗牌、查链接、比差异、读历史和同步删除。
        for needle in (
                # 换一批洗的是这一批的成员，不是把同一批重新取一遍。
                'title="换一批" aria-label="换一批">${icon(\'shuffle\')}',
                # 检查死链找的是断掉的那条链。
                'id="linkCheck">${icon(\'unlink\')}<span>检查死链</span>',
                # 资源同步比的是盘上和账本的差异；跑过一轮之后那一枚才是「再跑一遍」。
                'id="resourceScan">${iconSwapHtml(\'git-compare\',\'rotate-cw\')}'
                '<span data-scan-label>检查文件</span>',
                "setIconSwap(scan,done?'b':'a');",
                # 同步删除把这个目录在盘上和账本里对齐。
                'aria-label="同步删除">${icon(\'folder-sync\')}',
                # 沉浸模式是一叠竖着翻的卡，保存为播放列表存的是一份列表。
                "icon('gallery-vertical-end')}<span>进入沉浸模式</span>",
                'aria-label="保存为播放列表">${icon(\'playlist\')}',
                # 打开详情把这一张摊开，不是把窗口最大化。
                'title="打开详情" aria-label="打开详情">${icon(\'expand\')}',
                # 缩放条两端步进的是倍数，加减号没说清加减的是什么。
                'data-zoom-step="-1" aria-label="缩小">${icon(\'zoom-out\')}',
                'data-zoom-step="1" aria-label="放大">${icon(\'zoom-in\')}'):
            self.assertPageContains(needle)
        # 关注来源那几处问的就是「有没有更新」，转圈归它们；页面归 React 之后是 Remix 的
        # 同一枚字形，全选仍是双勾。
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn("leadingIcon={RiRefreshLine}", source_list)
        self.assertIn("aria-label={`检查 ${name} 的全部来源`}", source_list)
        self.assertIn("leadingIcon={RiCheckDoubleLine}", source_list)
        # 骨架照着画，等数据时占的是同一块地方。
        self.assertIn("<span data-author-select-label>全选</span>", self.markup)
        # 两个空态各说自己那件事：筛不出结果，和一次比对没有发现。
        self.assertPageContains("emptyState('search-x','当前筛选下没有更新'")
        self.assertPageContains("emptyState('file-stack','没有找到重复文件'")
        # 本地是磁盘、在线是订阅源；标签页和艺人页共用这一对，和关注页的来源图标同一套。
        self.assertPageContains("const INDEX_SCOPES=[['local','本地','hard-drive'],['online','在线','rss']];")
        # 「喜爱理由」开的是一个写字面板，不是喜欢开关——那个是旁边的 thumbs-up。
        self.assertPageContains('data-has-reason="${!!it.like_reason}">${icon(\'notebook-pen\')}')
        self.assertPageContains('aria-label="${it.liked?\'取消喜欢\':\'喜欢\'}"')
        # 侧栏：已标记是书签，沉浸模式是一叠竖着翻的卡；`play` 留给真的起播。
        self.assertPageContains("['flagged','已标记','bookmark'],")
        self.assertPageContains("['immerse','沉浸模式','gallery-vertical-end'],")
        self.assertPageContains("<span>进入沉浸模式</span>")
        # 三个名字里都带「管」「设」的入口各归各的：左上角那枚开的是左栏，所以是一块
        # 被划出侧栏的面板；侧栏「管理」是收拾库里的东西，所以是扳手——圆柱只留给口味页
        # 那几处「数据源」；管理里的「配置」配的是这台电脑的媒体文件夹与端口，所以是
        # 一个待配置的文件夹。齿轮只剩右上角的界面偏好。
        self.assertPageContains(
            'id="filterBtn" title="导航与筛选" aria-label="展开导航与筛选"')
        self.assertPageContains('<use href="#i-panel-left"/>')
        self.assertPageContains("['manage','管理','wrench'],")
        self.assertPageContains('<symbol id="i-wrench" viewBox="0 0 24 24">')
        self.assertPageContains("['configuration','配置','folder-cog'],")
        self.assertPageContains('<symbol id="i-folder-cog" viewBox="0 0 24 24">')
        # 配置页每行文件夹的「选择文件夹」弹系统对话框去挑：`folder-search`。`folder-open` 归「打开位置」。
        self.assertPageContains('<symbol id="i-folder-search" viewBox="0 0 24 24">')
        # 数据管理页「空文件夹」那张卡说的是目录本身：不是打开它，也不是去里面找。
        self.assertPageContains("'空文件夹':'folder',")
        self.assertPageContains('<symbol id="i-folder" viewBox="0 0 24 24">')
        self.assertIn('href="#i-folder-search"', (Path(__file__).resolve().parents[1] / "frontend" / "src" / "react" / "settings" / "media-settings.tsx")
                      .read_text(encoding="utf-8"))
        # 主题三档各归各的：太阳是浅色、月亮是深色；跟随系统那档说的是「照这台设备走」，
        # 讲的是设备不是明暗，所以跟 vercel.com 后台一样用显示器。画面尺寸量的是画幅本身，
        # 分辨率同样使用显示器。
        self.assertPageContains(
            "[['system','跟随系统','monitor'],['light','浅色','sun'],['dark','深色','moon']]")
        self.assertPageContains("${icon('monitor')}<span>${it.width||'?'}×${it.height||'?'}</span>")
        # 换下来的这几枚没有别的使用者，雪碧图里也不留。星是有使用者的那一枚：
        # 详情页的五星评分，写进 `asset.rating`，不与任何别的意思共用。
        # 厂牌索引进去是出片的那些牌子，字形因此说「拍片」而不是说「一栋楼」；
        # 名下带人的事务所在同一个开关的另一半，走公文包。
        self.assertPageContains("['studios','厂牌','clapperboard'],")
        self.assertPageContains('<symbol id="i-clapperboard" viewBox="0 0 24 24">')
        # `ri-palette-line` 是「外观」这个意思：设置里的「界面」那一格和侧栏底部那枚配色钮
        # 共用它，两处说的是同一件事。
        self.assertPageContains("const SETTINGS_TAB_ICONS={'界面':'ri-palette-line'")
        self.assertPageContains('<symbol viewBox="0 0 24 24" id="ri-palette-line">')
        self.assertPageLacks("swatch-book", "换下来的这一枚没有别的使用者，雪碧图里也不留")
        for gone in ("i-monitor-cog", "i-volume-2", "i-sun-moon", "i-building",
                     "i-sliders-horizontal", "i-computer"):
            self.assertPageLacks(f'<symbol id="{gone}"')
        self.assertPageContains("${icon('star')}</button>")
        self.assertPageContains('<symbol id="i-clock" viewBox="0 0 24 24">')

    def test_mixed_icon_sets_land_on_one_optical_grid(self):
        """同样 15px 要画得一样大，靠的是把内容外框补到 Lucide 的 20/24 活区。

        每套图标在自己画格里留的白不一样：Phosphor 的框是 256、Health Icons 是 24、
        自绘的 pics 是 16 且满格出血。照抄 viewBox 的结果是 pics 比邻座大两成、
        Aa 矮一截。这几个框是量出内容外框后算的，换版本时由生成脚本重放。
        """
        for symbol, box in (
                ("pics", "-1.6 -1.6 19.2 19.2"),
                ("text-aa", "-7.3 32.8 262.5 182.9"),
                ("playlist", "10.4 10.5 259.2 259.2"),
                ("sperm", "1.5 1.2 21.2 21.2")):
            self.assertPageContains(f'<symbol id="i-{symbol}" viewBox="{box}"')
        # 框由生成脚本负责重放：`npm run vendor:web` 每次都写出同一份。
        generator = (Path(__file__).resolve().parents[1]
                     / "scripts" / "vendor_web_dependencies.mjs").read_text(encoding="utf-8")
        self.assertIn('viewBox: "-7.3 32.8 262.5 182.9"', generator)
        self.assertIn('viewBox: "10.4 10.5 259.2 259.2"', generator)
        self.assertIn('const SPERM_VIEWBOX = "1.5 1.2 21.2 21.2";', generator)

    def test_every_glyph_is_drawn_at_one_stroke_weight(self):
        """字形描边只有一档：2。粗细不是尺寸的调节旋钮。

        Lucide、Phosphor、Remix 都按 24 的画格、2 的描边出图，尺寸差异交给
        `width`/`height` 表达。同一行里并排的两枚字形必须一样粗，包括那些自己
        不写描边、会落到 SVG 默认 1 的规则。

        例外都不是字形：勾选、仪表弧、进度环、雷达底格和圆环本身，它们的线宽是
        图形语义的一部分，逐条点名。
        """
        # 线宽属于图形本身的那几处：勾的笔画、弧的粗细、底格的细线。
        # 勾收两个值是分层的结果：BoardUI 那一层把画格放到 14，笔画跟着收一档。
        not_a_glyph = {
            ".pcheck>span svg": {"2", "2.5"},
            ".geist-gauge svg": {"3"},
            ".board-job-progress circle": {"2.5"},
            ".board-radar-grid": {"1"},
        }
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", self.css + board, flags=re.S)
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            found = re.search(r"(?<![-\w])stroke-width:\s*([^;}]+)", body)
            if not found:
                continue
            selector, width = selector.strip(), found.group(1).strip()
            self.assertIn(width, not_a_glyph.get(selector, {"2"}),
                          f"{selector} 的描边是 {width}")
        # 下拉框的前缀图标自己写死一份，不靠继承。
        self.assertIn("stroke:currentColor;fill:none;stroke-width:2}", self.css)

    def test_the_home_glass_reads_by_luminosity_and_the_four_views_share_one_sliding_pane(self):
        """玻璃靠调背景亮度保可读，四枚视图共用一块会滑的玻璃。

        Apple 的 regular 变体是「blurs and adjusts the luminosity of background
        content」：底色薄到能看见身后的东西在动，可读性交给 `--glass-lume`。拿一层厚底
        盖掉的话，玻璃底下什么都看不见，等于一块磨砂塑料。
        折射链里模糊排在位移前面——先糊身后的内容，再由边缘法线场把糊掉的像素往外挤；
        反过来先位移再糊，折射出来的亮边会被第二步抹平。
        四枚视图自己不铺底：两边都铺，静止态就是一块不透明的 `--picked` 压在滑动的那块
        玻璃上面。那块玻璃必须写 `left:0`，只写 `top` 的话水平方向回落到静态位置，
        整块右移一个内边距，盖不住选中那枚的左半边。
        动画挂在指针进入，不是点击：指到哪一枚就滑过去，`aria-pressed` 全程不动——
        移过去不是选中，读屏和键盘那边不该跟着变。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        for theme in ("--glass-lume:brightness(1.32) saturate(.5)",
                      "--glass-lume:brightness(.5) contrast(1.1)"):
            self.assertIn(theme, board)
        self.assertIn("backdrop-filter:var(--glass-optic,blur(22px)) saturate(160%) var(--glass-lume);", board)
        self.assertIn('`blur(14px) url("#${id}")`', app)
        self.assertNotIn('`url("#${id}") blur(2px)`', app)
        # 选中那枚的填充只有一处，就是那块玻璃自己。
        self.assertNotIn('.board-filter-frame #tagbar .pill[data-state][aria-pressed="true"]{'
                         'background:var(--picked)', board)
        self.assertIn(".viewglide.viewglide,.drawer.drawer>.navglide,.board-local-nav>.navglide{"
                      "position:absolute;left:0;top:0;z-index:0;pointer-events:none;", board)
        self.assertIn("backdrop-filter:var(--glass-pick);", board)
        self.assertIn("pills.forEach(b=>b.onpointerenter=e=>"
                      "{if(e.pointerType!=='touch')syncViewGlide(true,b,kind)});", app)
        # 归位挂在那一排自己身上，不挂整条筛选条：两排共用一条 `pointerleave` 的话，
        # 指针从媒体那组挪到视图那组就算离开，媒体那块会先弹回去再被下一个悬停接住。
        self.assertIn("row.onpointerleave=e=>{if(e.pointerType!=='touch')syncViewGlide(true,null,kind)};", app)
        # 位移和形变各占一个独立属性：一条属性上只放得下一段动画，而这两下的时间
        # 形状不是同一条曲线。
        self.assertPageContains("pane.animate([{translate:axis==='y'?`${box.x}px ${from.y}px`"
                                ":`${from.x}px ${box.y}px`},")
        self.assertPageContains("{translate:settled}],{duration:ease.duration,easing:ease.easing,fill:'none'});")
        # 顶栏这一条本身不铺任何底，中间那片空处直接通到内容。
        self.assertIn(".top.top,body.board-scrolled .top.top{background:transparent;box-shadow:none;"
                      "backdrop-filter:none;border:0}", board)
        self.assertNotIn(".top.top::before", board)

    def test_the_entity_view_row_shares_the_home_sliding_pane(self):
        """资料页那四枚跟首页那四枚共用同一块滑动玻璃。

        在人眼里这两排就是同一个控件——同一套词、同一个位置、同一件事——「跟着指针滑
        过去」没有理由只在其中一页成立。

        两边的 DOM 对不上：首页那排是 `#viewPills` 里的链接，选中记在 `data-state` 上；
        资料页是 `.entityviews` 里的按钮，记在 `data-entity-state` 上。所以按结构找，
        不按 id 找。判据还得是「此刻量得出宽度」而不是「存在」：两排在同一份文档里一直
        都在，资料页开着的时候首页那排只是被祖先收起来了，`hidden` 上看不出来，写死
        `#viewPills` 于是一直取到那一排——资料页从来没有过玻璃，这就是原样。零宽度把
        这一种连同 `display:none` 和照片视图下那一排自己的 `hidden` 一起挡住。

        选中态的填充只有一处，就是那块玻璃自己，两排各自都不铺底：两边都铺的话，静止态
        是一块不透明的填充压在玻璃上面，切换时也只看得见它瞬间换位置，滑动的那块从头到
        尾被盖在下面。首页那四枚是同一个写法。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("views:{selector:'#viewPills,.entityviews,.followviews',")
        self.assertPageContains("if(row.offsetWidth&&row.closest('.board-filter-frame'))return row;")
        self.assertPageContains(
            "'[data-state][aria-pressed=\"true\"],[data-entity-state][aria-pressed=\"true\"],")
        # 两页共用同一段接线；玻璃要等外框搭好才量得到位置。
        self.assertPageContains("function wireViewGlideRow(row,pills,kind='views'){")
        self.assertPageContains("wireViewGlideRow(controls,buttons);")
        self.assertPageContains("  syncViewGlide(false);\n  scheduleStickySurfaces();")
        self.assertPageLacks("const tagbar=$('#tagbar'),views=$('#viewPills');if(!tagbar||!views)return;",
                             "写死首页那两个 id 就是资料页没有玻璃的原因")
        # 资料页那四枚跟左端两枚媒体圆键都不自己铺底，选中和悬停都只提字色。
        self.assertIn('.entitytagbar.entitytagbar .pill[data-entity-state],\n'
                      '.entitytagbar.entitytagbar .pill[data-entity-state]:hover,\n'
                      '.entitytagbar.entitytagbar .pill[data-entity-state][aria-pressed="true"],\n'
                      '.entitytagbar.entitytagbar .mediaviewbutton,\n'
                      '.entitytagbar.entitytagbar .mediaviewbutton:hover,\n'
                      '.entitytagbar.entitytagbar .mediaviewbutton[aria-pressed="true"]{\n'
                      '  border:0;background:none;backdrop-filter:none;'
                      '-webkit-backdrop-filter:none;box-shadow:none}', board)

    def test_the_view_pane_is_the_only_pane_and_the_follow_row_rides_it_too(self):
        """观看状态那一排的玻璃是一块，首页、资料页、关注页三处共用；资料页左端那一组
        媒体圆键另有一块圆的。

        两排问的不是同一件事，共用一块的话点一下照片，玻璃从「没看过」那儿飞过来，读出来
        是两排在抢同一个当前项。圆角跟着按钮走：那几枚是正圆，一块 8px 圆角的方玻璃扣上去，
        四个角先露出来。

        玻璃按用途存，不按元素存：资料页每换一次筛选就把整条重画一遍，拿节点当键等于
        每重画一次就新建一块，动画从头起跑，看到的只是瞬移。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("views:{selector:'#viewPills,.entityviews,.followviews',")
        self.assertPageContains("pressed:'[data-state][aria-pressed=\"true\"],[data-entity-state][aria-pressed=\"true\"],"
                                "[data-follow-filter][aria-pressed=\"true\"]'},")
        # 资料页和关注页的媒体那一组同形，共用这一块玻璃：选择器写在一处，不是两页各一份。
        self.assertPageContains("media:{selector:'.entitymediaview,.followmediaview',"
                                "pressed:'[data-media-view][aria-pressed=\"true\"]',")
        self.assertPageContains("className:'viewglide-round'")
        self.assertIn('.viewglide.viewglide-round{border-radius:50%}', board)
        self.assertPageContains("const viewGlides=new Map();")
        self.assertPageContains("function syncViewGlide(animate,target,kind='views'){")
        self.assertPageContains("let glide=viewGlides.get(kind);")
        # 按下去那一下玻璃就滑过去，不等换视图的活干完。
        self.assertPageContains("syncViewGlide(true,button,'media');\n"
                                "      switchEntityMedia(kind,name,filters,media);")
        self.assertPageContains("wireViewGlideRow(controls,buttons,'media');")
        self.assertPageContains("const controls=$('#index').querySelector('.entitymediaview');if(!controls)return;")
        # 照片视图下这条只剩左端那一组，分隔线没有东西可隔。
        self.assertIn('.entitytagbar[data-media-only] .sep{display:none}', board)
        # 关注页：先搭外框再量玻璃，点下去玻璃先走、数据后到。
        self.assertPageContains("wireViewGlideRow(filterRow.querySelector('.followviews'),statusPills);")
        self.assertPageContains("statusPills.forEach(p=>p.setAttribute('aria-pressed',String(p===button)));syncViewGlide(true,button);")
        # 计数徽标照 tabs.tsx：未选中黑 10% 底半透明，选中换成强调色。
        self.assertIn('.board-tab-count{display:inline-block;margin-left:6px;padding:1px 4px;border-radius:4px;', board)
        self.assertIn('.board-local-nav button[aria-selected="true"] .board-tab-count{background:color-mix(in srgb,var(--tungsten) 12%,transparent);color:var(--tungsten);opacity:1}', board)

    def test_every_current_item_slab_slides_with_the_same_spring(self):
        """标出「当前是哪一个」的那几块底板，动法只有一份。

        筛选条上那块玻璃、抽屉那一列、分段控件里那块白底，在人眼里是同一件事：一排里
        说明此刻落在哪一个。各写各的位移就会各自漂移成几种手感——这边冲过头再荡回来，
        那边两百毫秒匀速滑过去，同一个界面上读出来是两套做工。
        所以那段动作住在共享层里，谁要用谁取：曲线和时长仍只有 `board.css` 那一份，
        JS 读它。
        分段控件那块底板只把位移交出去，尺寸留给过渡：宽高是布局属性，跟着位移一起
        过冲的话，它会在停下之前先胖出去一圈。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        controls = (Path(__file__).resolve().parents[1]
                    / "frontend/src/board-controls.ts").read_text(encoding="utf-8")
        self.assertPageContains("export function moveGlidePane(pane,from,box,axis='x'){")
        self.assertPageContains("export function glideEase(){")
        self.assertIn("import { moveGlidePane } from '@peach/legacy/ui';", controls)
        self.assertIn("moveGlidePane(thumb,from,box,'x');", controls)
        self.assertNotIn("thumb.style.transform", controls)
        self.assertIn("will-change:translate,scale;background:var(--color-background-primary-default)", board)
        self.assertIn(".board-segments-ready>.board-segment-thumb{\n"
                      "  transition:width calc(var(--spring-pane-ms,200) * 1ms) ease,"
                      "height calc(var(--spring-pane-ms,200) * 1ms) ease}", board)
        # 管理导航那条指示条是伪元素，挂不上第二段独立形变；位移那一下仍走同一条弹簧。
        self.assertIn("  transition:transform calc(var(--spring-pane-ms,200) * 1ms) var(--spring-pane,ease),\n"
                      "             width calc(var(--spring-pane-ms,200) * 1ms) ease}", board)
        self.assertNotIn("transition:transform 200ms ease", board)

    def test_every_glass_panel_casts_three_layers_and_the_pane_overshoots_by_distance(self):
        """玻璃的落影分三层，选中那块玻璃冲过头的距离跟着这一跳的跨度走。

        一层管一件事：1px 那层是接触影，画出玻璃和它底下那张纸之间的缝；中间一层是本体
        投影；最远那层大而极淡，是环境光被这块板挡住留下的那片。单层做不到——同一个模糊
        半径既要贴着边缘又要铺开一大片，只能取中间值，出来是一圈均匀的灰晕。
        三层都用冷灰而不是纯黑：这一层底下多半是肤色和暖色封面，纯黑压上去发脏。
        吸顶那一档要压过玻璃那组规则的特异性，否则整条 `box-shadow` 归后者，抬起来的
        那一档看不出来。
        选中那块的保底填充是白：`brightness()` 乘零时得有东西垫着，而垫墨色等于蒙一层
        灰，浅色下选中那枚会成为整条上唯一发灰的地方。
        冲过落点这一下由那条弹簧曲线自己给：峰值 1.103，冲过头的距离就是这一跳跨度的
        一成——从最左跳到最后一枚甩得最开，跳到隔壁只是轻轻一顿。另算一份「按跨度乘个
        系数」等于同一件事上摆两处能各自漂移的数。形变只在这一列排布的方向上，另一根
        轴的尺寸是那一排给定的。
        它挂在 `.board-filter-frame` 上而不是 `#tagbar` 里：那一排横滚会裁掉越界的部分，
        住在里面的话跳到头一枚时那下回弹就在框沿被切平。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        for shadow in ("--glass-shadow:0 1px 2px #1118270f,0 8px 18px #11182714,0 24px 48px #11182710;",
                       "--glass-shadow:0 1px 2px #00000047,0 10px 22px #00000038,0 28px 56px #0000002b;",
                       "--glass-lift:0 2px 4px #11182714,0 12px 26px #1118271f,0 30px 60px #11182717;",
                       "--glass-lift:0 2px 4px #00000052,0 14px 30px #00000047,0 34px 68px #00000038;"):
            self.assertIn(shadow, board)
        self.assertIn(".board-filter-frame.board-filter-frame.board-filter-frame.board-is-stuck{"
                      "box-shadow:inset 0 1px 0 var(--glass-rim),", board)
        self.assertIn("var(--glass-lift)}", board)
        # 保底填充两档都是白，加光而不是蒙灰。
        self.assertIn("--glass-pick-fill:rgba(255,255,255,.52)", board)
        self.assertIn("--glass-pick-fill:rgba(255,255,255,.13)", board)
        self.assertIn("transparent 62%),var(--glass-pick-fill);", board)
        self.assertNotIn("transparent 62%),color-mix(in srgb,var(--ink) 12%,transparent);", board)
        # 描边走满一圈，不只压上缘那一道；外影取主题给的那一档。
        self.assertIn("box-shadow:inset 0 0 0 1px var(--glass-rim),var(--glass-pick-shadow)}", board)
        # 玻璃由外框承载，几何扣除横滚量，回弹和阴影允许溢出内容边沿。
        self.assertIn("const host=pill.closest(within);if(!host)return null;", app)
        self.assertIn("x-=n.scrollLeft;y-=n.scrollTop;", app)
        self.assertIn("for(let n=pill;n&&n!==host;n=n.offsetParent){x+=n.offsetLeft;y+=n.offsetTop}", app)
        self.assertIn("if(glide.pane.parentElement!==box.host)box.host.prepend(glide.pane);", app)
        # 视口变化时每一排的玻璃都按按钮的新位置重新落位，不只四枚视图那一排。
        self.assertIn("Object.keys(GLIDE_ROWS).forEach(kind=>syncViewGlide(false,null,kind))},{passive:true});", app)
        # 冲过落点再弹回：那条曲线是一次弹簧模拟的采样，峰值 1.103、313ms 收住。
        self.assertIn("--spring-pane:linear(0,0.1515,", board)
        self.assertIn(",1.0477,1.096,1.1029,1.0901,1.0641,", board)
        self.assertIn("--spring-pane-ms:313}", board)
        # 曲线和它的时长只有 CSS 那一份，JS 读它，不各写各的。
        self.assertPageContains("paneSpring={easing:css.getPropertyValue('--spring-pane').trim()||'ease',")
        self.assertPageContains("duration:parseFloat(css.getPropertyValue('--spring-pane-ms'))||300};")
        self.assertPageContains(
            "if(from&&from[head]!==box[head]&&!matchMedia('(prefers-reduced-motion:reduce)').matches){")
        # 抻开按这一跳跨了自己几个身位算，封在一个半身位。
        self.assertPageContains(
            "const reach=Math.min(Math.abs(box[head]-from[head])/box[span],1.5),grow=1+reach*.12;")

    def test_a_pressed_control_snaps_down_at_once_and_springs_back_on_release(self):
        """手指直接拨的控件按下即时缩一档，松手按弹簧弹回去。

        按下那一步不能有缓动：隔两百毫秒才动读成的是「点了没反应」，那一下是手要的
        回执。弹回来才交给弹簧，冲过原尺寸一点点再收住——手指离开以后那块东西还自己
        动了一下，捏着的就是软的。回弹这一档比滑板那一档硬得多：按钮上要走的距离只有
        几个百分点，313ms 挂上去会拖成一次缓慢的呼吸。

        缩放走独立的 `scale` 属性，不挤进 `transform`：那一格上还挂着别的位移。滑块
        手柄只在抓住时涨一圈，位置一律不参与过渡——给位置加缓动等于让手柄落在指针
        后面，滑块立刻变成拖不准的东西。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        # 208ms、峰值 1.088，同一支弹簧模拟跑出来的短程版。
        self.assertIn("--spring-press:linear(0,0.1659,", board)
        self.assertIn(",1.0066,1.084,1.0861,1.069,", board)
        self.assertIn("--spring-press-ms:208}", board)
        self.assertIn(".dnav button,.pill,.sorts button{"
                      "transition:scale calc(var(--spring-press-ms) * 1ms) var(--spring-press)}", board)
        # 窄栏自己带一段填充过渡，`transition` 是整份覆盖，漏掉它悬停的渐变就没了。
        self.assertIn(".edge button{transition:scale calc(var(--spring-press-ms) * 1ms) "
                      "var(--spring-press),background .12s}", board)
        self.assertIn(".dnav button:active,.pill:active,.sorts button:active,.edge button:active{"
                      "scale:.96;transition:scale .06s ease-out}", board)
        self.assertIn("#tiers .av:active,#tiers .brandpill:active,\n"
                      ":is(.followauthors,.followworks) .av:active,"
                      ":is(.followauthors,.followworks) .brandpill:active"
                      "{scale:.96;transition:scale .06s ease-out}", board)
        self.assertIn("cursor:grab;transition:scale calc(var(--spring-press-ms) * 1ms) "
                      "var(--spring-press),box-shadow .15s}", board)
        self.assertIn(":active::-webkit-slider-thumb{scale:1.18;transition:scale .06s ease-out}", board)
        # 关掉动效时两档弹簧一起归零，剩下的是瞬时到位；原地换态那三档也在同一条里。
        self.assertIn("--board-motion:0s;--board-dialog-motion:0s;--spring-pane-ms:0;"
                      "--spring-press-ms:0;--motion-swap:0s;--motion-count:0s;--motion-reveal:0s;"
                      "--motion-stagger:0ms;--motion-pop:0s}", board)

    def test_the_theme_sweep_masks_with_a_gradient_instead_of_a_filtered_svg(self):
        """明暗切换那圈扩散用一段 CSS 渐变当遮罩，柔边靠色标位置给。

        遮罩的尺寸每一帧都在变，每一帧就要照新尺寸把它重新光栅化一遍。一张挂着高斯
        模糊滤镜的 SVG 每次都得连滤镜一起重跑，整屏那么大的一层，一次切换要跑几十遍；
        渐变没有这一层。柔边本身要留着——一条硬边扫过整屏，读出来是一块板在推。
        """
        source = (Path(__file__).resolve().parents[1]
                  / "frontend/src/sidebar-groups.ts").read_text(encoding="utf-8")
        self.assertIn("const mask='radial-gradient(circle closest-side,"
                      "#000 78%,#0006 88%,transparent)';", source)
        self.assertNotIn("feGaussianBlur", source)
        self.assertIn("will-change:mask-position,mask-size;"
                      "animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}", source)

    def test_the_sidebar_current_item_is_a_pane_of_glass_that_slides_down_the_rail(self):
        """侧栏的当前项是压在侧栏那块玻璃上的又一块玻璃，它在这一列里滑。

        这一屏铺开玻璃之后，一块蓝实底就成了唯一不透光的地方，看着像贴上去的另一套
        控件；蓝色在这套配色里只归焦点环和链接，导航的当前项靠比邻居高出一层来说话。
        抽屉那一列的这块玻璃归 `.navglide` 一块，按钮自己只管字色：两边都铺的话，静止
        态是一块不动的底压在滑过来的玻璃上，切换时只看得见它瞬间换位置。窄栏那一列是
        图标，一列里认哪个亮着靠的就是那一格自己，它照旧各铺各的。
        它跟筛选条那一排是同一块玻璃、同一条弹簧，只是换了根轴：竖排缩 Y。
        `filter:none` 不能省：抽屉那边给当前项的悬停和按下写了 `brightness(1.08)`，
        留着会把这块玻璃连同它身后的内容一起推亮一档。
        抽屉那一列的悬停也归这块玻璃：指到哪一格它滑过去，指针离开这一列再滑回当前项。
        格子底下另垫一层薄白就是两套反馈同时说话——薄白说「鼠标在这儿」，玻璃说「你在
        这儿」，指针停在别的格上时这两句话指着两个地方。薄白留给窄栏，那一列没有会滑
        的玻璃。委托挂在 `#drawer` 上，那一列每次切页整块重画都不必再接一遍；用的是会
        冒泡的 `pointerover`／`pointerout`，enter／leave 委托接不到。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        self.assertIn('.drawer.drawer.drawer .dnav button[aria-pressed="true"],\n'
                      '.drawer.drawer.drawer .dnav button[aria-pressed="true"]:hover,\n'
                      '.drawer.drawer.drawer .dnav button[aria-pressed="true"]:active{\n'
                      "  background:none;backdrop-filter:none;-webkit-backdrop-filter:none;\n"
                      "  color:var(--glass-text);filter:none;box-shadow:none}", board)
        self.assertIn('.edge.edge.edge button[aria-pressed="true"],'
                      '.edge.edge.edge button[aria-pressed="true"]:hover{\n'
                      "  background:linear-gradient(180deg,var(--glass-sheen),transparent 62%),"
                      "var(--glass-pick-fill);\n"
                      "  backdrop-filter:var(--glass-pick);-webkit-backdrop-filter:var(--glass-pick);\n"
                      "  color:var(--glass-text);filter:none;", board)
        self.assertIn('.edge.edge.edge button:not([aria-pressed="true"]):hover{\n'
                      "  background:color-mix(in srgb,var(--glass-rim) 26%,transparent);"
                      "color:var(--glass-text)}", board)
        self.assertIn(".drawer.drawer.drawer .dnav button:hover{background:none;"
                      "color:var(--glass-text)}", board)
        self.assertIn("const active=(target&&target.isConnected?target:null)\n"
                      "    ||(scroll&&scroll.querySelector('.dnav button[aria-pressed=\"true\"]'));", app)
        self.assertIn("  const button=event.target.closest?.('.dnav button[data-nav]');\n"
                      "  if(button)syncNavGlide(true,button);", app)
        self.assertIn("  const column=event.target.closest?.('.dnav');\n"
                      "  if(column&&!column.contains(event.relatedTarget))syncNavGlide(true);", app)
        # 那块玻璃住在 `#drawer` 上：切页会把 `#drawerScroll` 整块重画，住在里面的话
        # 它跟着一起没，动画在第一个微任务里就断了。
        self.assertIn(".drawer.drawer>.navglide{border-radius:10px;z-index:-1}", board)
        self.assertIn("navGlide.className='navglide';", app)
        self.assertIn("navGlide.setAttribute('aria-hidden','true');host.prepend(navGlide);navGlideBox=null;", app)
        self.assertIn("const box={x:active.offsetLeft,y:active.offsetTop-scroll.scrollTop,", app)
        # 激活态只有 `paintNav` 这一个权威出口，玻璃从那里起跑。
        self.assertIn("    .forEach(b=>b.setAttribute('aria-pressed',String(navOn(b.dataset.nav))));", app)
        self.assertIn("  syncNavGlide(true);\n}", app)
        # 换的是轴，不是另一套动画：竖排缩 Y，走的还是那一块的搬运函数。
        self.assertIn("moveGlidePane(navGlide,animate?from:null,box,'y');", app)
        self.assertIn("moveGlidePane(glide.pane,animate?from:null,box,'x');", app)
        self.assertPageContains("{scale:axis==='y'?`1 ${grow}`:`${grow} 1`,offset:.3},{scale:'1 1',offset:1}],")
        self.assertIn("wireNavigationDrag($('#drawer').querySelector('.dnav'));\n  syncNavGlide(false);", app)

    def test_the_sidebar_pane_lands_on_the_layout_that_settles_not_the_one_mid_flight(self):
        """那块玻璃画完下一帧再对一次位置，对的是当次那一格自己。

        切一次页那一列要被画两遍：先是导航自己那一遍，跟着是发现栏连侧栏一起重画的那一
        遍，两遍的标题行相差 4px。同步落在第一遍的读数上，玻璃就钉在那儿——一次切页留
        下 4px，来回切几次它离当前那一格越来越远。

        复对认的是当次传进来的那一格，不重新去找按下态：指针悬在别的格上时，按下态是另
        一格，照它对等于把跟着指针走的那块玻璃拽回去。位移正在跑就等它跑完，改终点会把
        走到一半的那段掐掉；切页那次动画正好压在重画上，只看一帧就放弃的话，要对的正是
        这一次。
        """
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("let navGlide=null,navGlideBox=null,navGlideTarget=null;", app)
        self.assertIn("  navGlideTarget=active||null;", app)
        self.assertIn("    const scroll=$('#drawerScroll'),active=navGlideTarget;", app)
        self.assertIn("    if(navGlide.getAnimations().length){\n"
                      "      if(performance.now()<until)settleNavGlide(until);\n"
                      "      return;\n    }", app)
        self.assertIn("    if(box.x===navGlideBox.x&&box.y===navGlideBox.y\n"
                      "      &&box.w===navGlideBox.w&&box.h===navGlideBox.h)return;", app)
        self.assertIn("  moveGlidePane(navGlide,animate?from:null,box,'y');\n  settleNavGlide();", app)

    def test_two_soft_lights_drift_across_every_pane_on_two_coprime_clocks(self):
        """玻璃面上那两团光在极慢地挪，横竖两根轴各走各的钟。

        钉死的高光把玻璃变成一张贴图。真玻璃对着一屋子的光，人一动、窗外云一过，面上
        的亮斑就换个地方，正是这一点让它读成一块有厚度的实物。
        光斑铺在一张两倍大的画布上，靠 `background-position` 推着走——画布只有元素两倍
        大时，位置从 0% 到 100% 正好把光斑中心从元素的右下角推到左上角。半径写 20% 是
        画布的比例，落到元素上是 40%，跟着元素自己的长宽拉成椭圆。
        `background-position-x` 和 `-y` 是两个独立属性，各挂一条时长不同的动画，41 与
        67 互质，合起来四十多分钟不重样，看不出循环点在哪。
        这一层不改用伪元素加 `transform`：吸顶那条遮挡带是靠 `::before` 探出框外画的，
        要裁住一团飘出去的光就得给玻璃加 `overflow:hidden`，那条带子跟着一起没了。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        # 浓淡写成 `color-mix` 的百分比而不是带 alpha 的色值：色相由用户挑的光晕给，
        # 这里只说「这块玻璃的反光有多淡」。深色那档默认指回近白。
        self.assertIn("--glass-native-a:#ffffff;--glass-native-b:#ffffff;", board)
        self.assertIn("--glass-drift-a:radial-gradient(20% 20% at 50% 50%,"
                      "color-mix(in srgb,var(--glass-tint-a) 10%,transparent),"
                      "color-mix(in srgb,var(--glass-tint-a) 5%,transparent) 42%,transparent 72%)", board)
        self.assertIn("--glass-drift-b:radial-gradient(26% 26% at 50% 50%,"
                      "color-mix(in srgb,var(--glass-tint-b) 8%,transparent),"
                      "color-mix(in srgb,var(--glass-tint-b) 4%,transparent) 44%,transparent 74%)", board)
        # 两根钟的时长同乘一个倍率：41:67 的比例不动，轨迹就不会退化成一条往返线。
        self.assertIn("  background:var(--glass-drift-a),var(--glass-drift-b),"
                      "linear-gradient(125deg,var(--glass-sheen),transparent 42%,var(--glass-low)),"
                      "var(--glass-fill);\n"
                      "  background-size:200% 200%,200% 200%,auto;"
                      "background-repeat:no-repeat,no-repeat,repeat;\n"
                      "  background-position:50% 20%,80% 70%,0 0;\n"
                      "  animation:glassdriftx calc(41s * var(--glow-drift-scale)) linear infinite,"
                      "glassdrifty calc(67s * var(--glow-drift-scale)) linear infinite;", board)
        # 两团反着走：同一条轨迹上错开半个周期，面上才不是一只手电筒。
        self.assertIn("  25%{background-position-x:-10%,110%,0}", board)
        self.assertIn("  75%{background-position-x:110%,-10%,0}", board)
        # 竖轴上错开四分之一个周期，两团合出来的是李萨如轨迹，不是一条对角线。
        self.assertIn("  0%{background-position-y:-10%,50%,0}", board)
        self.assertIn("  25%{background-position-y:50%,-10%,0}", board)
        # 光停在 `background-position` 给的那一处：还是两团高光，只是这屋里的光不再走了。
        self.assertIn("@media(prefers-reduced-motion:reduce){"
                      ".board-filter-frame.board-filter-frame.board-filter-frame,", board)
        for fallback in ("@supports not (backdrop-filter:blur(1px)){",
                         "@media(prefers-reduced-transparency:reduce),(prefers-contrast:more){",
                         "html.board-high-contrast .board-filter-frame"):
            self.assertIn("animation:none", board.split(fallback, 1)[1].split("}", 1)[0],
                          f"{fallback} 换成实色后还在推一层看不见的光")

    def test_the_glass_pane_marks_a_place_and_sort_keys_speak_by_weight(self):
        """那块玻璃标的是位置，排序键靠字自己说当前值。

        资料页的标签和侧栏、视图那几处一样，回答的都是「你在哪儿」，坐在同一材质的
        浮层上；选中态只要还是一层墨色 `color-mix`，同一块玻璃上就会同时出现两种
        「被选中」——一处是提亮的白玻璃，一处是压暗的灰片。墨色那层在亮封面上是块脏斑，
        浅色主题下又成了整条里唯一发灰的地方。
        媒体视图那两个图标钮同属这一类，但填充由它们自己那块滑动玻璃给，不在这条规则
        里铺——两边都铺，静止态就是一块不透明的填充压在玻璃上面。
        白填充不能省：`brightness()` 乘的是零时那块玻璃跟着背景一起黑，得有东西垫着，
        而垫的必须是白——白往上加是加光，跟提亮同向。

        排序键回答的是「这一列按什么排」，是一个参数的当前值，不是一个位置。同一种
        材质担两种语义，那一排读起来就成了另一组导航。八九个候选值一起退到六成，生效
        的那枚回到满值再加半档字重；只差字重不够，一排等亮度的字里扫一眼看不出哪个粗
        一点。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn('.entitytagbar.entitytagbar .pill[aria-pressed="true"]{\n'
                      "  background:linear-gradient(180deg,var(--glass-sheen),transparent 62%),"
                      "var(--glass-pick-fill);\n"
                      "  backdrop-filter:var(--glass-pick);-webkit-backdrop-filter:var(--glass-pick);\n"
                      "  color:var(--glass-text);border-color:transparent;\n"
                      "  box-shadow:inset 0 0 0 1px var(--glass-rim),var(--glass-pick-shadow)}", board)
        self.assertIn(".entitycollectionhead.entitycollectionhead .sorts button:not(.batchaction),\n"
                      ".board-filter-frame.board-filter-frame .sorts button:not(.batchaction){\n"
                      "  color:color-mix(in srgb,var(--glass-text) 62%,transparent)}", board)
        self.assertIn('.entitycollectionhead.entitycollectionhead .sorts button[aria-pressed="true"],\n'
                      '.board-filter-frame.board-filter-frame .sorts button[aria-pressed="true"]{\n'
                      "  background:none;backdrop-filter:none;-webkit-backdrop-filter:none;\n"
                      "  color:var(--glass-text);border-color:transparent;box-shadow:none;"
                      "font-weight:500}", board)
        for stale in ('.entitycollectionhead .sorts button[aria-pressed="true"]{'
                      'background:color-mix(in srgb,var(--ink) 10%,transparent)}',
                      '.entitytags .pill[aria-pressed="true"]{border-color:transparent;',
                      '.board-filter-frame .sorts button[aria-pressed="true"]{background:var(--picked)}'):
            self.assertNotIn(stale, board)

    def test_a_selectable_follow_row_keeps_its_own_border_on_every_edge(self):
        """关注列表进选择态后，行与行之间那条线是卡片自己的上边框。

        卡片模式下作者卡内还有一条 `--line-soft` 的分隔线，选择器比卡片边框更长，
        压掉的正是第二行起的上边框——在深色底上 `--line-soft` 几乎看不见，读起来
        就是「横线没了」。表格模式下行是 `tr`，卡片那套边框圆角落上去会和外框画出
        两条重叠的竖线，所以那套只给非 `tr`。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".followmanage .fauthor .fsource.frow:not(:has([data-follow-select]))"
                      "+.fsource.frow:not(:has([data-follow-select])){border-top:1px solid var(--line-soft)}", board)
        self.assertIn(".followmanage .fsource:has([data-follow-select]):not(tr){"
                      "border:1px solid var(--color-border-button-default);border-radius:10px;", board)
        # 表格外框自己收口：它离卡片脚还有一层内边距，去掉下边框就没有收尾。
        self.assertNotIn(".followmanage .fmain>.fsec:has(>.fsecfoot) .ftableframe", board)

    def test_the_author_avatar_stays_a_circle_when_there_is_no_picture(self):
        """取不到头像时那个空位仍然是一个圆。

        兜底那一枚是 `<span>`，跟在一段会伸缩的名字后面；不钉住尺寸就会被拉成一颗
        药丸。有图那一枚是 `<img>`，所以只在取不到时才露馅。
        """
        view = self.read_react("follow-manage/source-view.tsx")
        self.assertIn('className="inline-grid size-8 shrink-0 place-items-center rounded-full', view)
        self.assertIn("{authorInitial(name)}", view)
        self.assertIn('className="size-8 shrink-0 rounded-full bg-background-tertiary-default object-cover"',
                      view)

    def test_the_data_cleanup_page_spaces_its_blocks_the_same_way(self):
        """数据管理页三块内容之间是同一个间距。

        页面此前是块级流：卡片网格靠自己的下内边距撑出 32px，底下两个 section 之间
        什么也没有，贴在一起。间距交给页面这一层的 `gap`，网格不再兼职。
        """
        self.assertIn(".cleanuppage{width:min(812px,100%);margin:0 auto;display:grid;gap:32px}", self.css)
        self.assertIn(".cleanupgrid{display:grid;grid-template-columns:minmax(0,1fr);gap:20px}", self.css)
        # 结果区空着时也占一条网格轨道，区块底部会凭空多出一个间距。
        self.assertIn("#linkCheckResult:empty,#resourceSyncResult:empty{display:none}", self.css)
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".cleanupgrid{gap:16px}", board)
        self.assertIn(".cleanupstats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}", board)
        # 这两个 section 的标题也走同一条字阶，不留浏览器默认的 700。
        self.assertIn(".followmanage .fsechead h3,.resourcesync>h2{font:var(--board-heading)", board)

    def test_a_scan_card_keeps_its_outcome_outside_the_box(self):
        """扫描与采集的结果和故障挂在卡片外面，和链接管理、资源同步一个写法。

        那三块讲的都是「这一趟任务的下场」，一块写在框里、两块写在框外，读起来是两种
        不同的东西。`#libraryProcessing` 因此是这一格本身，卡片是它的第一个孩子，
        提示是第二个，间距由这一格的 `gap` 给。进度条留在卡片里：它说的是卡片上那个
        按钮此刻在做什么。

        这一页是 React 档（ADR-0031），正文在 `frontend/src/react/library-processing/`；
        结果、故障与重试怎么说由 `frontend/test/react/library-processing.test.tsx` 守。
        """
        self.assertPageContains('<div class="cleanupscraping" id="libraryProcessing">')
        self.assertPageContains('<section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanupScrapingTitle">')
        card = self.read_react("library-processing/library-processing-card.tsx")
        # 提示排在 `Section` 之后，两块由外面这一层的 `gap` 分开。
        self.assertIn(
            "      </Section>\n"
            "      <Outcome state={state} problem={problem} settled={settled} onRetry={retry} />",
            card)
        # 空着时整块收起：`aria-live` 的容器留一条空轨道，卡片底下会凭空多出一个间距。
        self.assertIn('<div aria-live="polite" className="flex flex-col gap-4 empty:hidden">', card)
        # 进度条留在卡片里，和那颗按钮同一格。
        self.assertIn("<Progress label={line} value={state.checked || 0} max={state.total} />", card)
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".cleanupgrid>#libraryProcessing{grid-column:1/-1;display:grid;gap:16px}", board)

    def test_a_failed_scan_folds_its_issue_list_into_the_error_note(self):
        """处理失败先给一句结论，逐条明细收在这条 Note 自己的 details 里，默认折叠。

        一次扫描能攒下几千条问题，摊开写就把结论、重试键和下面两块面板全推走了。每条
        给标题、说明和路径三段：只给一个链接的话，是哪个文件得逐个点开才知道，而路径
        才是去磁盘上确认或改名时要用的。前 20 条之外的去完整日志里看，地址写在折叠底部。

        默认折叠、重试只交失败那些项由 `frontend/test/react/library-processing.test.tsx` 守。
        """
        data = self.read_react("library-processing/library-processing.ts")
        self.assertIn("label: issue.title || (issue.asset_id ? `视频 ${issue.asset_id}` : '媒体来源'),", data)
        self.assertIn("note: issue.message,", data)
        self.assertIn("hint: issue.path || '',", data)
        self.assertIn("footnote: state.issues_log ? `完整记录：${state.issues_log}` : '',", data)
        card = self.read_react("library-processing/library-processing-card.tsx")
        # 结论、重试键和这份清单都在同一条 Note 里：摆到外面就成了一句话加两块没有出处的东西。
        note, extra = card.split('<Note tone="error" extra={', 1)
        self.assertIn("重试未完成项", extra)
        self.assertIn("<Disclosure summary={details.label}>", extra)
        self.assertIn("{details.footnote", extra)
        self.assertNotIn("<Disclosure", note)

    def test_a_finished_scan_is_announced_once_even_if_it_ended_before_the_page_opened(self):
        """完成用通知报。首次引导那一趟常在跳到目录页之前就跑完，横幅从没见过「运行中」，
        所以刚结束的任务第一次读到也要报；目录页横幅和数据整理页卡片按任务号只报一次。"""
        data = self.read_react("library-processing/library-processing.ts")
        self.assertIn("Date.now() / 1000 - state.completed_at < FRESH_COMPLETION_SECONDS", data)
        self.assertIn("localStorage.getItem(ANNOUNCED_KEY) === state.job_id", data)
        self.assertIn("自动落库 ${state.auto_applied || 0} 条", data)
        self.assertNotIn("toast('已完成扫描与资料采集')", data)
        shared = self.read_react("library-processing/use-library-processing.ts")
        self.assertIn("if (witnessed || mode === 'notice') announceCompletion(state, toast, witnessed);", shared)

    def test_the_follow_batch_bar_only_carries_row_actions(self):
        """关注页的批量条只有保存、跳过这类按行动作：这一页是浏览用的，不配全选键。"""
        self.assertPageLacks('id="followBatchAll"')
        self.assertPageLacks("#followBatchAll")
        self.assertPageContains("$('#batchbar').querySelectorAll('[data-follow-batch]').forEach(button=>button.hidden=!followPage);")

    def test_the_data_management_page_opens_with_a_row_of_stat_cards(self):
        """数据管理页照 Board 的 dashboard 模板：一排读数卡打头，下面两张任务卡各占一行。

        读数卡是 stat-cards.tsx 的 plain 变体做成按钮（132px、圆角 16、secondary 底、内边距 16、
        32px 图标格里 20px 字形、读数 24/34），整张卡就是那一页的入口；五张在 1120 内一行摆下，
        窄了折两列、再折一列。扫描与采集和空文件夹是要做的事，不是读数，各占一整行、左说明右按钮。
        骨架复用同一套结构，页首因此和读数卡直接接上：同样五个入口再排一条链接条，是同一件事
        画两遍，而那条链接条连选中态都没有。
        """
        self.assertPageContains("const DATA_MANAGEMENT_STATS=['review','quality','duplicates','junk','trash'];")
        self.assertPageContains('<button type="button" class="board-plain-stat" ${attrs}>')
        self.assertPageContains('<span class="board-plain-stat-head"><span class="board-stat-tile">${icon(glyph)}</span>${esc(title)}</span>${body}</button>`;')
        self.assertPageContains('<div class="cleanuppage"><div class="cleanupstats">')
        self.assertPageLacks('cleanup-workspace-switch')
        self.assertPageContains('</div><div class="cleanupgrid">${cleanupCards.scraping}${cleanupCards.empty}</div>')
        # 样式也一起走：没有使用者的选择器留在 board.css 里，下一个人会当它是现役版式去改。
        self.assertNotIn("cleanup-workspace-switch",
                         (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8"))
        for entry in ("['review','人工复核','square-check-big']", "['trash','回收站','trash']", "['quality','高清版','sparkles']"):
            self.assertPageContains(entry)
        root = Path(__file__).resolve().parents[1]
        board = (root / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-plain-stat{display:flex;flex-direction:column;justify-content:space-between;gap:8px;min-width:0;min-height:132px;margin:0;padding:16px;border:0;border-radius:16px;background:var(--color-background-secondary-default);", board)
        self.assertIn(".board-stat-tile{display:grid;place-items:center;flex:none;width:32px;height:32px;border-radius:6px;", board)
        self.assertIn(".board-stat-tile svg{width:20px;height:20px;", board)
        self.assertIn(".board-plain-stat>strong{display:block;margin:auto 0 0;font:var(--board-figure);", board)
        self.assertIn(".board-plain-stat>.cleanupmeta{display:block;min-height:16px;margin:0;font:var(--board-caption);color:var(--color-text-tertiary);", board)
        self.assertIn("@media(max-width:1119px){.cleanupstats{grid-template-columns:repeat(2,minmax(0,1fr))}}", board)
        self.assertIn("@media(max-width:559px){.cleanupstats{grid-template-columns:minmax(0,1fr)}}", board)
        self.assertIn(".cleanupgrid>.cleanupemptyfolders{display:grid;grid-template-columns:1fr auto;align-items:center}", board)
        skeleton = (root / "frontend/src/management.ts").read_text(encoding="utf-8")
        self.assertIn('<div class="cleanupstats">${stats.map(([title, glyph]) => `', skeleton)
        self.assertIn('<section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">', skeleton)

    def test_the_toast_glyph_is_stroked_and_sits_level_with_its_line(self):
        """Toast 里那枚勾是描边件，和文字同一条中线。

        不写 `fill:none` 的话它按 `fill` 的初值涂黑，一个勾会糊成实心箭头。文字靠
        `align-items` 对齐，不靠给 `<p>` 加上下内边距去凑——字数换行时那个凑法就散了。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".toast{position:relative;align-items:center;", board)
        self.assertIn(".board-notification-icon svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2}", board)
        self.assertIn(".toast p{margin:0}", board)
        self.assertPageContains("""<span class="board-notification-icon${alert?'':' checkdraw'}" aria-hidden="true">${icon(alert?'circle-alert':'check')}</span>""")

    def test_the_shorts_band_is_told_apart_by_its_fill_not_a_line(self):
        """竖屏带靠底色和网格区分，不描一圈线。

        它嵌在两段无边框的网格中间，一条线会把它读成一个可以点开的容器。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".shorts-inline{border:0}", board)
        self.assertPageContains(".shorts-inline{padding:16px;background:var(--ground);")

    def test_the_home_rows_keep_their_left_edge_and_pass_under_the_sidebar(self):
        """首页那几排横滚到右边时从侧栏底下穿过去，往左滚到头仍停在原对齐线上。

        让出去的宽度和加回的内边距是同一个数（轨道宽 `--railW` 加这一屏的 16px），
        所以 `scrollLeft` 归零时第一枚站的位置跟不越界时一模一样，越界只发生在往右
        那一侧。竖屏那一条连同它的底一起铺过去，卡片才不会在面板边缘从自己的底上掉
        出来，铺到视口边的那一侧不留圆角。窄屏的抽屉是盖上来的，没有常驻轨道，这一
        段整体不开。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(
            "@media(min-width:761px){\n"
            "  #tiers .tier{margin-left:calc(-1 * var(--railW));padding-left:calc(var(--railW) + 16px)}",
            board,
        )
        self.assertIn(
            "  .shorts-inline{margin-left:calc(-1 * (var(--railW) + 16px));"
            "padding-left:calc(var(--railW) + 32px);\n"
            "    border-radius:0 var(--floating-radius) var(--floating-radius) 0}",
            board,
        )
        self.assertIn(
            "  .shorts-inline .srow{margin-left:calc(-1 * (var(--railW) + 32px));"
            "padding-left:calc(var(--railW) + 32px)}",
            board,
        )

    def test_the_home_rows_keep_loading_as_they_scroll_toward_their_right_end(self):
        """首页三排横滚到右端接着续，首屏只画一屏够用的量。

        一排里每个头像都是一张要解码的图，把手上这份全画出来等于让首屏替一个多半不会
        滚到那么远的人买单；而滚到头就没有了、还剩大半份在内存里没露面，那一排看起来
        就是「只有这些」。数据在首屏那一次请求里一并取回，续这一下不再发请求。

        续到这一排真的溢出为止再停：宽屏上一批可能还填不满一行，没溢出就滚不动，滚不
        动就再没有第二次 `scroll` 来接着续。空的那一排根本不画，`.tier` 的序号跟着往前
        挪，所以要按这一排画没画来认。

        手上这份用完再去要下一页：`/api/tops` 一次最多回六十个，而库里六百多位女优，
        没有续页那一排就停在第六十位。
        """
        self.assertPageContains("const ROW_FIRST=24,TAGS_FIRST=26,ROW_BATCH=12;")
        self.assertPageContains("const params=new URLSearchParams({n:'60',seed:state.seed||''});")
        self.assertPageContains("const perfRow=tops.performers.slice(0,ROW_FIRST).map(avHtml).join('');")
        self.assertCode(
            "    while(atEnd()){\n"
            "      if(cursor>=rest.length){\n"
            "        if(drained)break;\n"
            "        fetching=true;"
        )
        self.assertCode(
            "        const more=await nextPage().catch(()=>[]);\n"
            "        fetching=false;\n"
            "        if(!more.length){drained=true;break}\n"
            "        rest=rest.concat(more);\n"
            "      }\n"
            "      row.insertAdjacentHTML('beforeend',rest.slice(cursor,cursor+ROW_BATCH).map(itemHtml).join(''));\n"
            "      cursor+=ROW_BATCH;added=true;\n"
            "    }"
        )
        # 要页的这段时间里人还在滚：进得来第二遍就会把同一页要两次，续上来的成双。
        self.assertPageContains("    if(fetching)return;")
        self.assertPageContains("if(drained&&cursor>=rest.length)row.removeEventListener('scroll',fill);")
        self.assertPageContains("row.addEventListener('scroll',fill,{passive:true});")
        # 页号各排各记：共用一个的话，先到头的那排会替另一排把页翻过去。
        self.assertCode(
            "    const nextTopsPage=kind=>{let page=0;\n"
            "      return async()=>(await loadTops(topsQueryParams(context,++page)))[kind]||[]};"
        )
        self.assertPageContains("if(page)params.set('page',String(page));")
        self.assertCode(
            "    if(perfRow)wireRowPaging(rows[next++],tops.performers.slice(ROW_FIRST),avHtml,\n"
            "      wireTierEntities,nextTopsPage('performers'));\n"
            "    if(studioRow)wireRowPaging(rows[next++],tops.studios.slice(ROW_FIRST),bpHtml,\n"
            "      wireTierEntities,nextTopsPage('studios'));"
        )
        # 续上来的那几个要跟第一屏一样能点开、一样有图片兜底。
        self.assertPageContains("function wireTierEntities(root){")
        self.assertPageContains("root.querySelectorAll('.mk img:not([data-fallback-wired])')")

    def test_both_ends_of_a_range_slider_always_report_their_value(self):
        """时长两端的读数常显：这里是唯一报数的地方。

        藏到碰上去才出现的话，不动滑块就看不出当前筛的是哪一段；另起一行写
        「不限 — 不限」则是同一件事说第二遍，而且滑块不动时它永远是那句话。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("white-space:nowrap;box-shadow:0 1px 2px #0000000d;pointer-events:none}", board)
        self.assertNotIn(".board-range-tip[data-range-end=max]{opacity:1}", board)
        # 两端拖到一起时它们会叠，刚动过的那枚压在上面：底下那枚报的是自己停下的位置。
        self.assertIn(".board-range-tip[data-range-active]{z-index:2}", board)
        controls = (Path(__file__).resolve().parents[1] / "frontend/src/board-controls.ts").read_text(encoding="utf-8")
        self.assertIn("  group.querySelectorAll('.board-range-tip').forEach(node=>\n"
                      "    node.toggleAttribute('data-range-active',node===tip));", controls)
        self.assertIn("tip.textContent=value>=max&&end==='max'?'不限':`${value} 分钟`;", controls)
        for gone in ("durMinText", "durMaxText", "duration-readout"):
            self.assertPageLacks(gone, "时长读数只由手柄上那两枚气泡承担")

    def test_a_range_readout_never_hangs_off_the_rail_it_reports_for(self):
        """读数气泡越过轨道两端的那一截按实测收回来，不靠两端各写一个固定对齐。

        这一排住在侧栏里，侧栏只比轨道宽出一点点：气泡对着手柄居中，手柄推到端点时
        伸出去的半截会被侧栏裁掉，屏幕上只剩半个数。按端点写死 `translateX(-100%)`
        又会让气泡在中段偏出手柄一整个身位——两端对齐的是轨道，正在报数的却是手柄。
        量之前先把上一次的位移清掉，否则量到的是已经收过一次的位置，越拖越偏。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("transform:translateX(calc(-50% + var(--range-tip-shift,0px)))", board)
        for pinned in (".dual-range .board-range-tip[data-range-end=max]{transform:translateX(-100%)}",
                       ".board-range-tip[data-range-end=min]{transform:none}"):
            self.assertNotIn(pinned, board)
        controls = (Path(__file__).resolve().parents[1]
                    / "frontend/src/board-controls.ts").read_text(encoding="utf-8")
        self.assertIn("  tip.style.setProperty('--range-tip-shift','0px');\n"
                      "  const bounds=group.getBoundingClientRect(),box=tip.getBoundingClientRect();\n"
                      "  const shift=box.right>bounds.right?bounds.right-box.right\n"
                      "    :box.left<bounds.left?bounds.left-box.left:0;\n"
                      "  if(shift)tip.style.setProperty('--range-tip-shift',`${Math.round(shift)}px`);",
                      controls)

    def test_a_selected_tab_is_marked_in_the_accent_blue(self):
        """选中的 tab 是蓝字加蓝线，全站两处下划线 Tabs 共用同一枚指示条。

        boardui tabs.tsx 实测：选中标签 `text-accent-600`，指示条是 tablist 外面那个 span
        （`h-0.5 bg-accent-600`）。Geist 的单色规则不覆盖这一层——board.css 是 boardui
        适配层，它自己就把强调色花在了「你在这一页」上。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("width:var(--tab-width,0px);height:2px;background:var(--tungsten);", board)
        self.assertIn(".managebar .managebar-menu button[aria-pressed=\"true\"]{background:none;"
                      "color:var(--tungsten);border-bottom-color:var(--tungsten);"
                      "font-weight:500}", board)
        self.assertIn(".board-local-nav button[aria-selected=\"true\"]{border-bottom-color:var(--tungsten);"
                      "color:var(--tungsten);font-weight:500}", board)
        # 焦点环也是蓝的，两者靠形态分开：焦点是一圈 outline，当前项是底下那条线。
        self.assertIn(".board-local-nav button:focus-visible{outline:2px solid var(--tungsten);", board)

    def test_the_two_bodies_of_evidence_switch_as_a_segmented_control(self):
        """两套证据的切换是分段控件，不是下划线 Tabs。

        它们是同一件事的两份证据，一条横线会把它读成页面层级的导航。滑块复用
        `.board-segment-thumb`，深色下那一档更亮的底一并继承。遗留壳铺的那张骨架
        （`.insightswitch`）与 React 档画出来的那一排读的是同一份几何：内边距 4px、
        10px 圆角，滑块 6px 圆角、transform／width／height 各 200ms。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        controls = (Path(__file__).resolve().parents[1] / "frontend/src/board-controls.ts").read_text(encoding="utf-8")
        self.assertIn(".insightswitch[data-board-segments]{position:relative;display:inline-flex;"
                      "align-items:center;gap:2px;padding:4px;border:0;border-radius:10px;", board)
        self.assertIn("min-height:28px;height:auto;padding:4px 10px;border-radius:6px;", board)
        self.assertIn(":is(.iconswitch:not(.themeswitch),.insightswitch,"
                      ".follow-workspace-switch)>:is(.board-segment-thumb,.skeleton-segment-selected)",
                      board)
        self.assertIn("const selector='.iconswitch,.insightswitch,"
                      ".follow-workspace-switch';", controls)
        self.assertIn("'label:has(input:checked),button[aria-selected=true]'", controls)
        self.assertIn("mutation.observe(group,{subtree:true,attributes:true,attributeFilter:['aria-selected']})",
                      controls)
        # 它退出下划线 Tabs 那一族，否则滑块和指示条同时挂上去。
        self.assertIn("const selector='.managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav)';",
                      controls)

    def test_hovering_a_button_lights_the_fill_and_never_the_outline(self):
        """次级按钮悬停只换填充，那圈线一动不动，全站只有一条规则说这件事。

        照 BoardUI 的强调档（2026-09-12 实测 boardui.com/components/button，记在
        `docs/reference-snapshots/boardui-pro-access-card-measured.md`）：primary 悬停逐项
        不变，ghost 只把底色换深一档、全程没有边。它那档 secondary 是填充加描边一起变，
        Peach 不跟——上游的悬停填充在暗色里只是 60% 的 #404040 压上去，差几个色阶，
        才要靠边来补；`--control-hover` 直接给到下一档实色，边就不必跟着闪。
        实心的几档不参加：它们自己的填充就是边界，选择器里的
        `:not(.primary,.danger,.error,.warning)` 管这件事。

        药丸、标签和外链卡同样不改边：它们是一排并列的选项，不是一颗要按的键。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        hover = [line for line in board.splitlines()
                 if ":not(.primary,.danger,.error,.warning):hover:not(:disabled,"
                 "[aria-disabled=true]){" in line]
        self.assertEqual(len(hover), 1, "次级按钮的悬停只该有一条规则")
        self.assertIn("background:var(--control-hover)", hover[0])
        self.assertNotIn("border-color", hover[0])
        self.assertIn(":root,:root[data-theme=light]{--control-hover:"
                      "var(--color-background-tertiary-default)}", board)
        self.assertIn(":root[data-theme=dark]{--control-hover:"
                      "var(--color-border-button-default)}", board)
        for rule in re.findall(r"[^\n{}]*:hover[^\n{}]*\{[^}]*\}", board):
            selector, _, body = rule.partition("{")
            if not re.search(r"\.pill|\.brandpill|\.tg\b", selector):
                continue
            self.assertNotIn("--color-border-button-hover", body,
                             f"悬停不改药丸那圈线：{selector.strip()}")
        self.assertIn("body .pill:hover,body .brandpill:hover{border-color:var(--field-ring)}", board)
        # 边不动之后悬停还得剩点东西：玻璃条上的药丸提文字色。
        self.assertIn(".board-filter-frame.board-filter-frame .pill:hover{color:var(--ink)}", board)

    def test_the_primary_tier_has_one_face_and_crossfades_into_its_hover(self):
        """强调档全站一颗：三档渐变都在 board.css，悬停那一档铺在 `::before` 上淡入。

        照 `boardui.com/components/button` 的 `.bg-button-primary`（2026-09-12 实测）：
        静止 accent-500→600、悬停 400→500、按下 600→700，悬停那一层是宿主的 `::before`
        改 opacity 交叉淡入。不直接换 `background` 是因为渐变是 background-image，它没有
        插值可言，直接换就是硬切一下；按下那一下换回 `background` 并把那层压回 0，于是
        悬停着按下去也是一档一档地走。

        不带边：上游那颗是 `border:0`，补一圈透明边在 `box-sizing:border-box` 下会把内容盒
        压掉 2px，而 `background-origin` 是 padding-box，渐变被压到 34px 再延展到 36px，
        色标跟上游错开一像素——这就是用户看到的「偏移」。宿主要 `isolation:isolate`，
        不然 `z-index:-1` 会把那一层送到按钮所在层叠上下文的底下，铺到卡片背面去。

        面色分在两层写的后果不是「多一条规则」：`web/css/` 那一层的
        `.geist-button.primary:hover:not(:disabled)` 是四个类，比 Board 那条静止规则
        重一个类，于是同一颗按钮的静止由一处给、悬停由另一处给，鼠标一压就换成另一套配色。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        rule_re = re.compile(r"[^\n{}]*\.primary[^\n{}]*\{[^}]*\}")

        def primary_rules(source: str) -> list[str]:
            # `:not(.primary,.danger,…)` 是次级档在排除强调档，不是在给强调档写样式。
            return [rule for rule in rule_re.findall(source)
                    if ".primary" in re.sub(r":not\([^)]*\)", "", rule.partition("{")[0])]

        rules = primary_rules(board)
        face = [rule for rule in rules if "background:var(--board-blue)" in rule.partition("{")[2]]
        self.assertEqual(len(face), 1, "强调档那一面只该有一条规则")
        for declaration in ("border:0", "color:#fff", "box-shadow:0 1px 2px #0000000d",
                            "position:relative", "isolation:isolate"):
            self.assertIn(declaration, face[0])
        for rule in rules:
            self.assertNotIn("border:1px solid transparent", rule,
                             "强调档不补透明边，它会把渐变的色标挤开一像素")
        layer = [rule for rule in rules
                 if "background:var(--board-blue-hover)" in rule.partition("{")[2]]
        self.assertEqual(len(layer), 1, "悬停那一层底只该铺一次")
        for declaration in ("content:\"\"", "position:absolute", "inset:0", "z-index:-1",
                            "pointer-events:none", "border-radius:inherit", "opacity:0",
                            "transition:opacity .15s ease"):
            self.assertIn(declaration, layer[0])
        roster = face[0].partition("{")[0].strip()
        # 四条都得挂在同一份名单上，否则有的按钮压上去没反应、有的按下去不回弹。
        self.assertEqual(layer[0].partition("{")[0].strip(), roster + "::before")
        for suffix, body in ((":hover::before", "{opacity:1}"),
                             (":active", "{background:var(--board-blue-active)}"),
                             (":active::before", "{opacity:0}")):
            self.assertIn(roster + suffix + body, board)
        for rule in primary_rules(stylesheet_source()):
            selector = rule.partition("{")[0].strip()
            self.assertNotIn(":hover", selector, f"强调档的悬停不写在这一层：{selector}")
            self.assertNotIn(":active", selector, f"强调档的按下不写在这一层：{selector}")

    def test_the_danger_tier_has_one_face_and_crossfades_into_its_hover(self):
        """危险档全站一副面，做法跟强调档同一份，色阶换成 BoardUI 的红。

        照 `boardui.com/components/button` 的 `.bg-button-danger`（2026-09-12 实测，与
        `.bg-button-primary` 逐字同构）：静止 red-500→600、悬停 400→500、按下 600→700，
        悬停那一档铺在 `::before` 上淡入。

        「同一副面」不是整洁问题。批量条和卸载区都在说「按下去就回不来了」，同一句话
        在两个页面上读出两种红，用户要判断的是哪一次更重，而这个差别是没有意思的。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        roster = "body :is(button.danger,.batchbar button.danger):not(:disabled)"
        self.assertIn(roster + "{position:relative;isolation:isolate;background:var(--board-red);"
                      "border:0;color:#fff;box-shadow:0 1px 2px #0000000d;", board)
        self.assertIn(roster + "::before{content:\"\";position:absolute;inset:0;z-index:-1;"
                      "pointer-events:none;border-radius:inherit;background:var(--board-red-hover);"
                      "opacity:0;transition:opacity .15s ease}", board)
        for suffix, body in ((":hover::before", "{opacity:1}"),
                             (":active", "{background:var(--board-red-active)}"),
                             (":active::before", "{opacity:0}")):
            self.assertIn(roster + suffix + body, board)
        for stale in ("#ff3347", "#e60012", "#ff6471"):
            self.assertNotIn(stale, board, f"危险档的红只从 token 来，{stale} 是第二份")

    def test_the_entry_pages_keep_the_shared_geist_primary_rule(self):
        """入口页的主按钮跟站内是同一颗规则，不是抄一份色值。

        首启与登录表单从 `board-entry.css` 使用同一组渐变 token；带
        `.geist-button primary` 的独立错误页直接使用提取出的完整规则。
        """
        root = Path(__file__).resolve().parents[1]
        board = (root / "web/board.css").read_text(encoding="utf-8")
        entry = (root / "web/board-entry.css").read_text(encoding="utf-8")
        self.assertNotIn(".geist-button.primary{", entry, "入口页不留第二份强调档色值")
        self.assertNotIn("--board-blue:", entry, "那条渐变只在 board.css 声明")
        from peach.routes_pages import _board_button_rules
        rules = _board_button_rules()
        self.assertIn(":root,:root[data-accent=blue],[data-accent-ball=blue]{--color-accent-50:",
                      rules, "入口页必须取得默认蓝色色阶，渐变 token 才有实际色值")
        self.assertIn("--color-accent-500:", rules)
        # board.css 里这个 token 声明了两遍，Board 那一层的映射排在后面、也是实际生效的
        # 那一份；取过去的要是最后一处。
        gradient = re.findall(r"--board-blue:(linear-gradient\([^;}]+\))", board)[-1]
        self.assertIn(f"--board-blue:{gradient}", rules, "入口页那份渐变要跟站内逐字相同")
        primary = rules[rules.index(".primary:not(:disabled){"):]
        primary = primary[:primary.index("}")]
        for declaration in ("background:var(--board-blue)", "border:0",
                            "color:#fff", "box-shadow:0 1px 2px #0000000d",
                            "isolation:isolate"):
            self.assertIn(declaration, primary)
        self.assertIn("height:36px", rules, "尺寸那条也一起取过去")
        # 悬停铺的是 `::before` 那层底，淡入靠改 opacity：三条少一条这三页的按钮就要么
        # 压上去没反应，要么亮着不退。
        for suffix in (".primary:not(:disabled)::before{", ".primary:not(:disabled):hover::before{",
                       ".primary:not(:disabled):active{", ".primary:not(:disabled):active::before{"):
            self.assertIn(suffix, rules, "悬停和按下那几条也要跟过去")
        self.assertIn("--board-blue-hover:linear-gradient(", rules)
        self.assertIn("--board-blue-active:linear-gradient(", rules)

    def test_the_settings_drawer_column_is_the_same_glass_as_the_sidebar(self):
        """设置弹层左栏和左侧抽屉是同一件事的两种形态，玻璃并在同一条规则上。

        自己另配一份模糊和底色的结果是两块玻璃看着就不是一种材质。降级的三条路——
        不支持 backdrop-filter、用户要求减少透明度、高对比——也要一起覆盖到，否则那一栏
        会在这些环境里留着一块动个不停的半透明。

        卡片仍旧自己铺 --page：弹层底下压着一层 70% 的黑遮罩，透过去模糊出来的是被压暗的
        页面，浅色主题下整栏发灰、那一列的字读不出来。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        glass = next(line for line in board.splitlines()
                     if line.startswith(".board-filter-frame.board-filter-frame.board-filter-frame,")
                     and ".drawer.drawer," in line)
        self.assertIn(".settingscard.settingscard>.board-local-nav", glass)
        self.assertIn(".settingscard.settingscard{background:var(--page)}", board)
        self.assertNotIn("backdrop-filter:saturate(1.8) blur(20px)", board,
                         "左栏不再自己配一份模糊")
        for guard in ("@supports not (backdrop-filter:blur(1px))",
                      "@media(prefers-reduced-transparency:reduce)"):
            line = next(row for row in board.splitlines() if row.startswith(guard))
            self.assertIn(".settingscard.settingscard.settingscard>.board-local-nav", line,
                          f"{guard} 这一路要把左栏一起降级")
        contrast = next(row for row in board.splitlines()
                        if row.startswith("html.board-high-contrast .settingscard.settingscard>"))
        self.assertIn("animation:none", contrast, "高对比下那层漂移的光晕要停")

    def test_the_settings_groups_sit_on_the_same_card_as_the_machine_pages(self):
        """设置弹层上半列的每组开关行和「这台电脑」下的配置页坐在同一种卡上。

        配置页走 BoardUI `SettingsCard`：灰底、16px 圆角、左内边距 12px，行的分隔线在卡片
        左沿内收住。上半列照这张卡的尺寸画，标题与页底仍是 `--page`；「这台电脑」那一格的
        外壳不铺底，否则配置页自己的灰卡外面又套一层灰。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".settingscard .settingsscroll>.settinggroup"
                      "{background:var(--ground);border-radius:16px;padding:0 0 0 12px}", board)
        self.assertIn(".settingscard .settingsscroll>.settinggroup:has(>.machinesettings)"
                      "{background:none;border-radius:0;padding:0}", board)
        self.assertIn(".settingscard.settingscard>.settingshead,"
                      ".settingscard.settingscard>.settingsscroll{background:var(--page)}", board)
        self.assertIn(".settingscard .settingsscroll .settingrow{min-height:52px;"
                      "padding:10px 10px 10px 0;gap:16px;border-top:0;"
                      "border-bottom:1px solid var(--line-soft)}", board)

    def test_the_settings_title_casts_the_sidebar_shadow_once_the_gap_is_scrolled_away(self):
        """标题下那道影子跟左栏那块玻璃同一份，滚掉那段留白才点亮。

        那三层各带十几到几十像素的模糊，往上会糊在标题自己头上、往左会糊到左栏那一列
        上，要的只是往下那一半，所以裁掉另外三边。留白的值只写在 `--settings-gap` 一处，
        滚动量过了它减 4px 就算两块重合。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        self.assertIn(".settingscard .settingshead{position:relative;z-index:2;"
                      "clip-path:inset(0 0 -96px 0);transition:box-shadow .2s ease-out}", board)
        self.assertIn(".settingscard.board-settings-scrolled .settingshead"
                      "{box-shadow:var(--glass-shadow)}", board)
        # 那段留白长在滚动区的上内边距上，滚掉它就等于两块重合。
        self.assertIn(".settingscard.settingscard{--settings-gap:16px;", board)
        self.assertIn(".settingscard.settingscard .settingsscroll"
                      "{padding:var(--settings-gap) 32px 32px;min-height:0;overflow-y:auto}", board)
        self.assertIn(".settingscard.settingscard .settingsscroll"
                      "{padding:var(--settings-gap) 20px 20px;flex:1}", board)
        # 影子不再是一段从页底色渐隐的带子，两种做法并存就是两道。
        self.assertNotIn("background:linear-gradient(var(--page),transparent);"
                         "pointer-events:none;opacity:0", board)
        self.assertIn("const gap=parseFloat(getComputedStyle(card)"
                      ".getPropertyValue('--settings-gap'))||0;", app)
        self.assertIn("card.classList.toggle('board-settings-scrolled',"
                      "settings.scrollTop>Math.max(gap-4,0));", app)

    def test_the_settings_column_glass_follows_the_pointer_like_the_filter_row(self):
        """设置弹层左栏那块玻璃跟着指针走，跟筛选条那排药丸是同一条连线。

        一列里只有当前那格铺着面，鼠标停在哪一条得靠字色那一档去读，扫下来分不出自己停在
        了第几条。指针离开这一列就滑回当前那格；触点没有「悬停」，碰一下就滑过去等于替
        用户点了一次。
        """
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("buttons.forEach(button=>{button.onpointerenter=event=>{\n"
                      "    if(event.pointerType!=='touch')syncLocalNavGlide(nav,button,true)}});", app)
        self.assertIn("nav.onpointerleave=event=>{\n"
                      "    if(event.pointerType==='touch')return;\n"
                      "    const current=nav.querySelector('[role=tab][aria-selected=true]');\n"
                      "    if(current)syncLocalNavGlide(nav,current,true);\n"
                      "  };", app)
        # 配置页那一份没有玻璃，连线挂上去也不动任何东西。
        self.assertIn("if(!nav.closest('.settingscard'))return", app)

    def test_the_settings_column_drops_the_top_rim_the_floating_glass_keeps(self):
        """设置弹层左栏不留顶边那道高光：它嵌在卡片里，上边贴的是卡片自己的圆角。

        那道高光是给浮在页面上的玻璃打边用的，落在这一栏就是一条白线横在「设置」上面，
        读起来像卡片被切成了上下两截。其余三面的内描边和落影照旧。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".settingscard.settingscard.settingscard>.board-local-nav{\n"
                      "  box-shadow:inset 1px 0 0 var(--glass-low),inset -1px 0 0 var(--glass-low),"
                      "inset 0 -1px 0 var(--glass-low),var(--glass-shadow)}", board)
        glass = next(line for line in board.splitlines()
                     if line.startswith("  border:0;box-shadow:inset 0 1px 0 var(--glass-rim),"))
        self.assertIn("var(--glass-shadow)", glass, "浮层那几块玻璃照旧带顶边高光")

    def test_the_settings_drawer_column_marks_the_current_item_with_glass(self):
        """左栏当前项的填充由一块滑过去的玻璃给，跟抽屉那一列、筛选条那四枚同一套做法。

        两边都铺的话，静止态就是一块不透明的 --picked 压在玻璃上面，切换时只看得见它
        瞬间换位置，滑动的那块从头到尾被盖住。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        app = (Path(__file__).resolve().parents[1] / "web/app.js").read_text(encoding="utf-8")
        self.assertIn(".board-local-nav>.navglide", board, "那块玻璃要吃到 .navglide 的长相")
        selected = next(line for line in board.splitlines()
                        if line.startswith(".settingscard.settingscard>.board-local-nav "
                                           "button[aria-selected=true]{"))
        self.assertIn("background:none", selected, "当前项自己不铺底")
        self.assertIn("syncLocalNavGlide(nav,buttons[index],moved)", app,
                      "切分区时那块玻璃要跟过去")
        self.assertIn("if(!nav.closest('.settingscard'))return", app,
                      "管理区那份横排页签不加玻璃")

    def test_the_shuffle_key_is_the_accent_tier_among_the_sort_keys_beside_it(self):
        """换一批走强调档：这一排其余的是排序开关，只有它是动作。

        面色取全站那两个 token，压上去提亮一档；圆角随这一条上的按钮取 7px。排序键那条
        字色规则要把它排除掉，否则首页那枚读到白、资料页那枚读到六成的玻璃字色。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-filter-frame.board-filter-frame .sorts .batchaction,"
                      ".entitycollectionhead.entitycollectionhead .sorts .batchaction"
                      "{color:#fff;background:var(--board-blue);border:0;border-radius:7px;"
                      "box-shadow:0 1px 2px #0000000d}", board)
        # 选中态归排序键，换一批只有悬停。
        self.assertIn(".board-filter-frame.board-filter-frame .sorts .batchaction:hover,"
                      ".entitycollectionhead.entitycollectionhead .sorts .batchaction:hover"
                      "{background:var(--board-blue-hover);color:#fff}", board)
        for selector in (".entitycollectionhead.entitycollectionhead .sorts button:not(.batchaction),",
                         ".board-filter-frame.board-filter-frame .sorts button:not(.batchaction){",
                         ".entitycollectionhead.entitycollectionhead .sorts button:not(.batchaction):hover,",
                         ".board-filter-frame.board-filter-frame .sorts button:not(.batchaction):hover{"):
            self.assertIn(selector, board, "排序键的字色不能再盖到换一批身上")

    def test_profile_tags_are_the_same_pill_as_the_ones_on_the_home_filter_bar(self):
        """资料页的标签跟首页筛选条上的标签是同一个控件，只是换了个位置。

        它现在坐在玻璃上，描边和字色跟着玻璃那套读数走：`--line` 与 `--ink-2` 是配着
        页面底色调的，压到半透明的玻璃上比周围重一档。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".entitytags .pill{height:30px;padding:0 10px;font-size:13px;line-height:20px;"
                      "border-radius:var(--tag-radius);border:1px solid var(--glass-low);"
                      "color:var(--glass-text)}", board)
        self.assertIn(".board-filter-frame .tagbar .pill{height:30px;padding:0 10px;font-size:13px;", board)

    def test_the_profile_floating_panel_is_one_pane_measured_off_the_home_one(self):
        """资料页顶上那块浮层是一块玻璃，尺寸照首页那块量。

        标签行和排序行是两个兄弟，一个挂在 `.index` 上、一个在 `.entitysection` 里，
        而那一段的 innerHTML 每次重画都整块换掉，套不进首页那个 `.board-filter-frame`。
        所以两行自己都不铺底，整块玻璃由下半的 ::before 一次画完，圆角是整块的 22px。
        下半的吸顶位置是上半的下沿，那个高度只归这块浮层——基础层的 `--filterH` 是
        没有浮层时贴着顶栏的老尺寸，拿它算会差 10px。
        """
        root = Path(__file__).resolve().parents[1]
        board = (root / "web/board.css").read_text(encoding="utf-8")
        base = stylesheet_source()
        rail = re.search(r"\.tiers\{[^}]*?padding:10px 0 (\d+)px", base)
        gutter = re.search(r"\bmain\{[^}]*?padding:(\d+)px \d+px", base)
        self.assertTrue(rail and gutter, "读不到 .tiers 的收尾与 main 的上沿")
        gap = int(rail.group(1)) + int(gutter.group(1))
        self.assertIn(":root{--board-filterH:48px}", board)
        self.assertIn(".entitytagbar{position:sticky;top:calc(var(--topH) + 8px);margin:0;"
                      "height:var(--board-filterH);gap:6px;padding:8px 12px}", board)
        self.assertIn(f".entitycollectionhead{{position:sticky;top:calc(var(--topH) + 8px);margin:0 0 {gap}px;"
                      "padding:8px 12px;min-height:var(--board-filterH);gap:12px}", board)
        self.assertNotIn(".entitytagbar+.entitysection .entitycollectionhead", board)
        # 只剩一行时它自己就是整块，圆角跟首页那块同一档。
        self.assertIn(".entitytagbar.entitytagbar.entitytagbar,\n"
                      ".entitycollectionhead.entitycollectionhead.entitycollectionhead"
                      "{border-radius:22px;color:var(--glass-text)}", board)
        # 读数和排序键照首页那条 `10,471 个符合` 与它旁边那排写。
        self.assertIn(".entitycollectionhead h3{font-size:12px;font-weight:400;letter-spacing:normal;"
                      "color:var(--ink-2)}", board)
        self.assertIn(".entitycollectionhead .sorts button{height:30px;min-height:30px;font-size:12px;"
                      "padding:0 8px;border:0;border-radius:7px;background:transparent}", board)
        self.assertIn(".board-filter-frame .sorts button{height:30px;min-height:30px;font-size:12px;"
                      "padding:0 8px;border:0;border-radius:7px;background:transparent}", board)

    def test_a_two_piece_glass_panel_does_not_paint_the_diagonal_sheen(self):
        """资料页那两条各做一块，只铺一层平的底色，静止时不显出上下两层。

        那道 125° 高光是按盒子自己的对角线铺的：上下两条各铺一遍，接缝两边就成了亮的
        一段和灰的一段，读起来是两块叠在一起。漂移的两团光也不铺：光斑按盒子的百分比
        算，一条只有 48px 高，圆斑压成一道横光，在接缝处被截断。边上那圈高光仍由
        `inset` 描出来。首页那块是一整块玻璃，它照旧铺。
        兜底那三条（不支持 backdrop-filter、降低透明度／提高对比度、高对比开关）要和
        主选择器一起长：漏掉哪一条，那些用户看到的就是没有底色的一块。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertNotIn("background-image:none;background-color:var(--glass-fill);animation:none}", board)
        sheen = board.split("\n  background:var(--glass-drift-a),var(--glass-drift-b),"
                            "linear-gradient(125deg,var(--glass-sheen)", 1)[0].rsplit("}", 1)[1]
        for selector in (".board-filter-frame.board-filter-frame.board-filter-frame",
                         ".entitytagbar.entitytagbar.entitytagbar",
                         ".entitycollectionhead.entitycollectionhead.entitycollectionhead"):
            self.assertIn(selector, sheen, "玻璃那条主规则少了一个面")
        for fallback in ("@supports not (backdrop-filter:blur(1px)){",
                         "@media(prefers-reduced-transparency:reduce),(prefers-contrast:more){"):
            rule = board.split(fallback, 1)[1].split("}", 1)[0]
            for selector in (".entitytagbar.entitytagbar.entitytagbar",
                             ".entitycollectionhead.entitycollectionhead.entitycollectionhead"):
                self.assertIn(selector, rule, f"{fallback} 少了一个面")
        contrast = board.split("html.board-high-contrast .board-filter-frame", 1)[1].split("}", 1)[0]
        for selector in ("html.board-high-contrast .entitytagbar.entitytagbar.entitytagbar",
                         "html.board-high-contrast .entitycollectionhead"
                         ".entitycollectionhead.entitycollectionhead"):
            self.assertIn(selector, contrast, "高对比那条少了一个面")

    def test_a_horizontal_tag_row_fades_at_both_ends(self):
        """横着滚的标签行两端要渐隐，资料页和首页用同一段。

        不渐隐的话，浮层圆角那儿最后一个标签被直角硬切掉半个字，也看不出右边还有。
        """
        self.assertPageContains("function wireHorizontalScroller(el,")
        self.assertPageContains("wireDrag($('#index').querySelector('.entitytags'));")
        # 窄屏下滚的是外面那层，四枚观看状态跟着标签一起走；两层都登记，登记在不滚的
        # 那层上是空转，少登记一层就会在某一个宽度上滚不动。
        self.assertPageContains(
            "wireHorizontalScroller($('#index').querySelector('.entitytags'));"
            "\n  wireHorizontalScroller($('#index').querySelector('.entitytagbar .filterscroll'));")
        self.assertPageContains(
            "if(filterFrame)[boardTagbar,countbar.querySelector('.sorts')].forEach(el=>wireHorizontalScroller(el));")

    def test_the_board_layer_rows_that_can_overflow_are_all_registered(self):
        """board.css 与 `frontend/` 画出来的横滚层走名单，不走按 id 点名的那份清单。

        漏登记的表现全站一个样：滚动条被藏掉、滚轮是竖向的、两端也不渐隐，于是那边
        还有多少内容既看不出也够不着。390px 实测设置弹层那排分区溢出 244px，靠这份
        名单才拿得到提示。React 档的页面自己用 `overflow-x-auto`，不进这份清单。
        """
        page = self.page
        overlay = page.split("const OVERLAY_SCROLLERS=[", 1)[1].split("].join(',')", 1)[0]
        edge = page.split("const BOARD_EDGE_SCROLLERS=", 1)[1].split(";", 1)[0]
        for selector in (".board-local-nav", ".managebar-menu", ".follow-workspace-switch",
                         ".fmanagenav"):
            self.assertIn(selector, edge, f"{selector} 会横向溢出，要按横滚层登记")
        # 扫描只看前一份名单，只写进后一份等于没登记。
        scanned = set(re.findall(r"'(\.[a-z0-9-]+)'", overlay))
        unscanned = [s for s in re.findall(r"\.[a-z0-9-]+", edge) if s not in scanned]
        self.assertEqual(unscanned, [], "横滚层也要进 OVERLAY_SCROLLERS 才会被扫到")

    def test_the_detail_dialog_scrolls_an_inner_layer_so_it_gets_the_shared_scrollbar(self):
        """详情浮窗窄屏下滚的是 `.stagescroll`，滚动条和全站是同一条。

        `<dialog>` 在顶层，它自己滚就只剩系统滚动条：覆盖式那条的轨道必须是滚动容器的
        兄弟，挂到浮窗父级上会落进遮罩底下。所以内容统一装进一层，滚的是那一层。
        「接着看」是 `.sgrid` 的兄弟，也得装在同一层里，否则它会被浮窗那条 `overflow:clip`
        裁在外面、再也够不着。
        """
        page = self.page
        overlay = page.split("const OVERLAY_SCROLLERS=[", 1)[1].split("].join(',')", 1)[0]
        self.assertIn("'.stagescroll'", overlay, "滚的那一层要登记才接得上覆盖式滚动条")
        self.assertPageContains('<div class="stagescroll"><div class="sgrid ${queueContext?\'mixgrid\':\'\'}">')
        self.assertPageContains('<div class="stagescroll"><div class="sgrid followdetailgrid')
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".stage>.stagescroll{max-height:calc(100dvh - 34px);"
                      "overflow:hidden auto;overscroll-behavior:contain}", board)
        # 34px = 浮窗上下各 16px 留白加两条边线，减出来和浮窗自己那条上限落在同一个数上。
        self.assertIn("max-height:calc(100dvh - 32px)", stylesheet_source())
        # 手机上浮窗换了一条上限，滚动层跟着换，两边仍旧差两条边线。
        self.assertIn(".stage>.stagescroll{max-height:calc(100dvh - env(safe-area-inset-top) - 18px)}",
                      board)
        # 浮窗自己不再纵向滚：它一滚就是系统滚动条。
        self.assertNotIn(".stage{overflow:hidden auto}", board)

    def test_the_tidy_up_notice_keeps_the_panels_gap_below_it(self):
        """首页那条整理提示下面留和浮层一样宽的空当。

        它是正文列里的一条 Note，上下两条线是它自己的收口。少了这个空当，两条线一边
        挨着身份行、一边挨着筛选浮层，看着像三块东西粘在一起。上面那段由 `.tiers`
        的收尾和 `main` 的上沿凑够，所以只写下面这一个数，和浮层从同一处读出来。
        """
        root = Path(__file__).resolve().parents[1]
        board = (root / "web/board.css").read_text(encoding="utf-8")
        base = stylesheet_source()
        rail = re.search(r"\.tiers\{[^}]*?padding:10px 0 (\d+)px", base)
        gutter = re.search(r"\bmain\{[^}]*?padding:(\d+)px \d+px", base)
        self.assertTrue(rail and gutter, "读不到 .tiers 的收尾与 main 的上沿")
        gap = int(rail.group(1)) + int(gutter.group(1))
        self.assertIn(
            "#libraryProcessingNotice:not(:empty):not(:has(>.peach-react:empty))"
            f"{{margin:0 0 {gap}px}}", board)

    def test_a_progress_ring_lines_up_with_the_lists_under_it(self):
        """资源面板里的进度环和它下面那几组链接表对同一条左边。

        那张卡自己不留内边距，里面每块各带各的；进度环少了这一条就贴着卡片左沿。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-job-progress{display:flex;align-items:center;gap:12px;padding:12px 0;", board)
        self.assertIn(".resourcepanel>.board-job-progress{padding:12px 16px}", board)

    def test_cover_scraping_says_it_is_still_running(self):
        """抓封面这一趟在页面上留状态，不是只让按钮转一下。

        它要挨个问几家站点、还可能走代理，没有可数的总量，也不能编一个百分比出来，
        所以是 Loading Dots 不是 Progress。关掉页面它照样在跑、回来能接上，状态就得
        留在页面上——按钮的忙态随着重进页面一起没了。

        页面归 React 子树（ADR-0031）：轮询接不接得上、首屏读到的旧结果画不画、回执发
        几次由 `frontend/test/react/scraping.test.tsx` 守，等待点的外观由共用组件与
        `frontend/e2e/design.test.ts` 守。这里只钉「用哪一种等待态」这个选择。
        """
        page = (Path(__file__).resolve().parents[1]
                / "frontend/src/react/scraping/scraping-page.tsx").read_text(encoding="utf-8")
        self.assertIn("<LoadingDots label=\"正在抓取封面\" />", page)
        self.assertNotIn("<Progress", page)

    def test_the_floating_filter_panel_leaves_the_same_gap_above_and_below(self):
        """浮层上下留一样宽的空隙；上面那段由页面给，它自己就不再加一层。

        上沿是几段叠出来的：`.tiers` 收尾 8px、`main` 上沿 14px，浮层自己再要 8px，
        而空着的 `.combo` 那 10px 下边距把它顶成 10px——实测上面 32px、下面 20px，
        同一块浮层两头差 12px。前两段是每个页面共用的，改不动；所以浮层上面不加，
        下面照那两段的和写，两个数从同一处读出来，谁改了页面上沿测试就在这里说话。
        """
        root = Path(__file__).resolve().parents[1]
        board = (root / "web/board.css").read_text(encoding="utf-8")
        base = stylesheet_source()
        rail = re.search(r"\.tiers\{[^}]*?padding:10px 0 (\d+)px", base)
        gutter = re.search(r"\bmain\{[^}]*?padding:(\d+)px \d+px", base)
        self.assertTrue(rail and gutter, "读不到 .tiers 的收尾与 main 的上沿")
        gap = int(rail.group(1)) + int(gutter.group(1))
        self.assertIn(f"background:var(--ground);margin:0 0 {gap}px;", board)
        self.assertIn(".combo:empty{height:0;margin-bottom:0}", base)

    def test_a_profile_website_link_shows_the_sites_own_mark(self):
        """官网那一格的文字是域名，图标是站点自己的那枚；取不到才露出地球。"""
        app = self.app_js
        self.assertIn("<a class=\"urllink\"", app)
        urllink = app[app.index("<a class=\"urllink\""):]
        urllink = urllink[:urllink.index("</a>")]
        self.assertIn("linkMarkUrl(x)", urllink)
        self.assertIn("data-drop=\"self\"", urllink)
        self.assertIn("linkHost(x.url)", urllink)

    def test_a_collapsed_ranking_shows_a_fixed_preview_and_one_way_back(self):
        """收起的排名只露前十，展开与收起共用同一颗次要按钮。

        名次归 React 档（`frontend/src/react/taste/taste-page.tsx` 的 `RankList`）：二十条
        一次铺开会把下面几块整个顶到屏外，所以默认露十条，再由一颗 BoardUI 次要按钮
        来回切。行为由 `frontend/test/react/stats.test.tsx` 与 `taste.test.tsx` 守，
        这里守的是「这一条规矩只有一处实现」。
        """
        taste = (Path(__file__).resolve().parents[1]
                 / "frontend/src/react/taste/taste-page.tsx").read_text(encoding="utf-8")
        self.assertIn("const RANK_PREVIEW = 10;", taste)
        self.assertIn("expanded ? rows : rows.slice(0, RANK_PREVIEW)", taste)
        self.assertIn("{expanded ? '收起排名' : '展开更多排名'}", taste)
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertNotIn(".board-expand-ranks", board, "遗留层那套展开排名已经没有读者")
        self.assertIn(".fcollapse{overflow:hidden;transition:height .2s ease-in-out}", (
            Path(__file__).resolve().parents[1] / "web/css/08-photos.css").read_text(encoding="utf-8"))
        self.assertNotIn("overflow:hidden;transition:max-height", board)

    def test_the_library_switcher_menu_opens_against_the_control_it_belongs_to(self):
        """媒体库弹窗贴着切换器的右缘开，允许压住侧栏剩下的那一段。

        按侧栏右缘起算的话，展开态下切换器到侧栏边还有两百来像素，弹窗和它点开的那个
        控件之间隔着一片空白，读不出是谁弹出来的。
        """
        ui = (Path(__file__).resolve().parents[1] / "web/js/ui-components.js").read_text(encoding="utf-8")
        self.assertIn("menu.style.left=Math.max(16,Math.min(anchor.right+8,innerWidth-width-16))+'px';", ui)
        self.assertNotIn("Math.max(anchor.right,mount.getBoundingClientRect().right)", ui)

    def test_the_sidebar_switcher_clears_the_first_nav_row(self):
        """切换器和导航首项之间留 12px。

        切换器展开时自己带一圈 2px 描边，首项又会抬起 hover 底：留 4px 的话这两块底色
        是挨着的，读起来像切换器压在第一项上。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".drawer .dnav{margin-top:12px;gap:4px}", board)

    def test_a_filter_group_opens_only_when_something_in_it_is_active(self):
        """一进侧栏只有正在生效的那几组是展开的。

        挑两组常驻展开等于替人决定他这次要按哪个维度筛，而侧栏一屏就那么长，展开的
        部分把别的组挤到看不见的地方去。记住的选择仍然优先于这个默认。
        """
        groups = (Path(__file__).resolve().parents[1] / "frontend/src/sidebar-groups.ts").read_text(encoding="utf-8")
        self.assertIn("group.open=saved!==null?saved==='open':active;", groups)
        self.assertNotIn("group.classList.contains('cat-src')", groups)
        self.assertNotIn("group.dataset.sidebarGroup==='时长'", groups)

    def test_a_wide_glyph_gets_a_wide_slot_instead_of_being_shrunk_to_fit(self):
        """1.4:1 的字形锁死方形槽位只能按宽缩，画出来就比满格的邻座矮一截。

        外层 `<svg>` 的 viewBox 也得跟着 symbol 的比例，否则 `use` 仍旧 meet 进
        24×24 的方框，把 symbol 那侧的宽框白改了。宽度交给 CSS 按高推。
        """
        self.assertPageContains("const WIDE_ICONS={'text-aa':1.435};")
        self.assertPageContains(
            "const ratio=WIDE_ICONS[name],classes=[ratio?'iconwide':'',cls].filter(Boolean).join(' ');")
        self.assertPageContains(
            "const box=ratio?`0 0 ${(24*ratio).toFixed(2)} 24`:'0 0 24 24';")
        self.assertPageContains(".tagcount .iconswitch svg.iconwide{width:auto}")

    def test_plain_text_inputs_share_one_token_so_the_button_beside_them_matches(self):
        """控件高度只有一档：输入框 38px，同一行的按钮照抄这个数。

        窄屏那条 `font-size:16px!important` 会把没写死高度的输入框抬 3px，旁边的
        按钮不动，一行里两个控件差一截；播放列表那张表还因为 `flex:1 1 100%`
        把提交键顶到下一行。纯文本输入框全站共用 `.geist-input`。
        """
        self.assertPageContains(".geist-input{box-sizing:border-box;width:100%;min-width:0;height:var(--control-h);")
        self.assertPageContains(".playlistcreate .geist-button{height:38px;padding:0 13px}")
        # 提交键是主动作，实心档由共用的 .geist-button.primary 给，不再本地拼一套描边。
        # 弹层里的提交键由 Geist Modal 的操作条给，页面上自己拼的只剩这一枚。
        self.assertPageContains(
            '<button class="geist-button primary" type="submit">新建</button>')
        self.assertPageContains('<button type="submit" class="geist-button primary" data-modal-confirm>')
        self.assertPageLacks(".playlistcreate button,.playlistactions button{")
        self.assertPageContains(".playlistcreate label{display:grid;gap:8px;color:var(--muted);"
                                "font-size:var(--fs-xs);flex:1 1 200px;max-width:320px}")
        self.assertPageLacks(".playlistcreate label{flex:1 1 100%}")
        # 自己拼内边距的那几处已经并入 token，别再冒出第二份。
        self.assertPageLacks(".playlistcreate input,.playlistmeta input{min-width:220px;")
        self.assertPageLacks(".faliasform input{min-width:0;height:34px;")
        for needle in (
                '<label class="modalfield"><span>名称</span><input class="geist-input" name="name"',
                '<label>新播放列表<input class="geist-input" name="name"'):
            self.assertPageContains(needle)
        # 别名管理归 React 之后，这两格用同一档的 BoardUI `Input`，高度也还是那一档。
        alias = self.read_react("follow-manage/alias-manager.tsx")
        self.assertIn('<Input aria-label="规范创作者名"', alias)
        self.assertIn('<Input aria-label="平台别名"', alias)

    def test_an_online_tag_opens_the_follow_page_not_a_catalog_filter(self):
        """在线标签标注的是还没入库的在线更新，拿去筛目录必然一条不中。"""
        self.assertPageContains("if(onlineTags){")
        self.assertPageContains("followTags=new Set([b.dataset.k]);")
        self.assertPageContains("$('#index').hidden=true;route(followViewPath());openFollow(false);return}")

    def test_the_drawer_lists_follow_tags_without_the_catalog_binding_stealing_them(self):
        """抽屉里的关注标签必须保住自己的点击处理。

        它们用 chip 的样式，而抽屉底下那句通用绑定在更后面执行：选择器写成 `.chip`
        就会把它们一并接管，点下去等于按 undefined 筛目录，表现是跳回首页。目录芯片
        都带 data-key，选择器收窄到它才分得开——这个坑真踩过一次。
        """
        self.assertPageContains("$('#drawer').querySelectorAll('.chip[data-key]')",
                                "通用绑定会连关注标签一起接管")
        self.assertPageLacks("$('#drawer').querySelectorAll('.chip').forEach")
        self.assertPageContains("data-follow-drawer-tag=")
        self.assertPageContains("followTags=new Set([b.dataset.followDrawerTag]);")
        self.assertPageContains("openDrawer(false);route(followViewPath());openFollow(false)});")
        self.assertPageContains(".chip.online{")

    def test_catalog_filters_are_only_seeded_from_a_catalog_url(self):
        """查询参数属于它所在的路由。

        目录的筛选不能无条件从启动 URL 里读：那样 `/follow?tag=blender` 这样的链接
        会顺手把目录也筛成 blender，顶部画出「blender ✕ 全部清除」——一条目录筛选
        芯片挂在关注页上，回到首页还发现自己被筛住了。

        关注页的 tag 是 booru 英文标签，目录的 tag 是本地中文标签，两套词表撞在同一
        个键上，只能靠路由分开。`loc` 不在此列：它是跨页面的来源开关，不是目录筛选。
        """
        self.assertPageContains("const initialParam=key=>initialCatalogUrl?initialParams.get(key):null;")
        self.assertPageContains("isCatalogPath(path)||path==='/trash'")
        seeded = self.page[self.page.index("state={loc:"):self.page.index("const HOME_QUERY_KEYS")]
        for key in ("creator", "studio", "tag", "orient", "sort", "q", "jav"):
            self.assertIn("initialParam('" + key + "')", seeded,
                          key + " 仍在无条件读启动 URL，别的路由会顺手把目录筛住")
        self.assertNotIn("initialParams.get('tag')", seeded,
                         "tag 是关注页和目录共用的键，必须走按路由的闸门")

    #: 会整页接管的视图。新增一个整页视图时把它加进来——两个共用入口都要走。
    FULL_PAGE_VIEWS = ("openStats", "openTaste", "openPlaylists", "openDuplicates",
                       "openReview", "openQualityGoals", "openFollow", "openFollowManage")

    def test_every_full_page_view_enters_through_the_shared_helpers(self):
        """进入一个整页视图分两步，两步都必须走共用函数。

        `enterManagementSurface()` 是「离开目录」：收掉筛选芯片、隐藏分层与标签条，
        并 `loadRequestSeq++` 作废在途的目录请求。`showManagementBody()` 是「铺开新
        页面」：显隐那六个容器，再按 `manage` 决定顶部是管理条还是窄栏。

        两个不合并是因为时机真的不同——前者必须抢在任何 await 之前，后者有的入口在
        取数前铺（配 placeholder 给反馈）、有的在取数后铺（数据快时不闪骨架）。正因
        为分成两个，才容易只调一个，所以这里逐个视图断言两个都在。

        这段显隐此前在八个入口里各抄一份，抄漏 combo 就是用户报的那个 bug：在 /tags
        点一个标签再进关注页，标题上面还挂着「白虎 ✕ 全部清除」。
        """
        for name in self.FULL_PAGE_VIEWS:
            body = self._js_function(name)
            self.assertIn("enterManagementSurface()", body,
                          name + " 没有走「离开目录」，筛选芯片会留在新页面上")
            self.assertIn("showManagementBody(", body,
                          name + " 自己铺页面主体，多半又抄漏了一行")

    def test_infinite_scroll_is_wired_through_one_helper(self):
        """「载入更多」的观察器只许有一份实现。

        它此前抄了三份：关注流、实体合集、照片墙。已经开始漂——后两份有 `hidden`
        判断，关注那份没有。藏起来的按钮观察它没有意义，漏掉只是浪费一个观察器，
        但下一次抄漏的可能就不是这一行。

        重画会换掉按钮节点，所以 disconnect 不能省：旧观察器还盯着已脱离文档的节点，
        既不会触发也不会被回收。
        """
        body = self._js_function("wireLoadMore")
        self.assertIn("observer.disconnect()", body, "卸载必须断开观察器")
        self.assertIn("busy||button.hidden||!button.isConnected", body)
        self.assertIn("current.isCurrent?.()!==false", body)
        self.assertIn("request?.abort()", body)
        self.assertIn("rootMargin:'320px'", body)
        self.assertEqual(self.page.count("new IntersectionObserver"), 1,
                         "共享分页只有这一个观察器")
        for consumer in ("function renderFollow", "function renderEntityCollection", "function renderPhotoWall", "function wireCatalogLoadMore"):
            self.assertIn("wireLoadMore(", self._js_function(consumer.split()[-1]))

    def test_the_identity_name_leaves_room_for_descenders(self):
        """身份格子里的名字不能被行框切掉下伸部。

        用户实测：厂牌「Prestige」的 g 尾巴被切掉。`.idname` 的 line-height 是 1.25，
        12px 字号下只有 15px 行框，而这一格同时开着 `overflow:hidden` 做省略号——
        拉丁字母的下伸部就落在框外被裁掉了。中文看不出来，所以一直没人发现。
        """
        rule = self.page.split(".idname{", 1)[1].split("}", 1)[0]
        self.assertIn("line-height:1.5", rule, "行高要容得下下伸部")
        self.assertNotIn("line-height:1.25", rule)
        # 省略号仍然要有：名字长了得截断，只是不能连下伸部一起裁掉。
        self.assertIn("text-overflow:ellipsis", rule)
        self.assertIn("text-align:left", rule, "文字和头像共用左边缘")
        self.assertPageContains(".idgroup-performer .idname{text-align:center}")
        self.assertPageContains(".idgroup-performer .idcell{align-items:center}")

    def test_the_group_label_lines_up_with_the_avatar_below_it(self):
        """组标题、图标和名字都贴详情内容区左边缘。"""
        self.assertPageContains(".idgroup{--id-cell:62px;--id-face:46px}")
        self.assertPageContains(".idgroup-performer{--id-cell:58px}")
        self.assertPageContains(".idgroup-performer .idrow{gap:10px}")
        self.assertPageContains(".idlabel{margin:0 0 7px")
        self.assertPageContains("align-items:flex-start;gap:5px;width:var(--id-cell,62px)")
        self.assertPageContains("width:var(--id-cell,62px)")
        self.assertPageContains("width:var(--id-face,46px);height:var(--id-face,46px)")

    def test_detail_source_icon_starts_at_the_content_edge(self):
        # 徽标是标题第一行开头的行内块，随文字一起被两行折叠裁住。
        self.assertPageContains(
            ".detailtitle .srcbig{display:inline-grid;vertical-align:middle;width:17px;height:28px;"
            "margin:0 8px 0 0;place-items:center}")

    def test_official_tags_do_not_have_a_visible_marker(self):
        self.assertPageLacks(".detailtag .tagfilter small{")
    def test_editions_collapse_into_one_card_with_a_version_badge(self):
        """同番号的几个版次合成一张卡，角标写清有几个版本。"""
        self.assertPageContains("function collapseEditionGroups(items){")
        self.assertPageContains("const visible=collapseEditionGroups(collapseMultipartItems(items));")
        self.assertPageContains('${editions.count} 个版本')
        # 叠层纸边是「这张卡代表不止一条」的说法，分卷和版次都成立；只给分卷的话，
        # 同样被折叠过的版次卡长得和普通卡一模一样。
        self.assertPageContains("const stacked=parts||editions;")
        self.assertPageContains("${stacked?'<div class=\"partstack\">':''}")
        self.assertPageContains("${stacked?'</div>':''}")
        self.assertPageContains("openEditions(it.edition_group.seed_id,id,true,anchor)")
        self.assertRoute('/editions/:seed/:item', "openEditions(params.seed,params.item,push)")

    def test_entity_pages_collapse_edition_groups_too(self):
        """资料页的网格也要折叠版次组。

        只折叠分卷的话，女优页上 `ABF-187` 与 `ABF-187-UN` 仍旧并排两张卡，
        两张都挂着「2 个版本」角标——角标说已经合过，眼前却是没合的两张。
        """
        self.assertPageContains(
            "collapseEditionGroups(collapseMultipartItems(items.items)).map(it=>cardHtml(it))")

    def test_the_edition_queue_is_labelled_and_clickable(self):
        """版次队列要认自己这一类：标题、计数、每条的版次徽章和点击都得对上。

        点击没有 editions 分支的话会掉进播放列表分支，带着 undefined 的
        playlistId 去请求——点了没反应，控制台也只有一条被吞掉的失败。
        """
        self.assertPageContains(
            "kindLabel={mix:'Mix',parts:'分卷',editions:'版本',playlist:'播放列表'}")
        self.assertPageContains(":queue.kind==='editions'?`${queue.items.length} 个版本`")
        self.assertPageContains(
            ":queueContext.kind==='editions'?openEditions(queueContext.seedId,+b.dataset.queueItem,true)")
        self.assertPageContains("const edition=queue.kind==='editions'&&x.edition_label")
        self.assertPageContains(
            "EDITION_TONE={'中字':'subtitle','无码':'uncensored','无码破解':'cracked','有码':'censored'}")
        self.assertPageContains(
            '<span class="mixitemtext"><span class="mixitemhead">${edition}<b data-middle-truncate>')
        # 徽章和标题同一行，所以标题那一行要自己成为 flex 容器；`<i>` 默认斜体，
        # 徽章不是强调语气，font-style 必须写死。
        self.assertPageContains(
            ".mixitemtext .mixitemhead{display:flex;align-items:center;gap:5px;margin-top:0;color:var(--ink)}")
        self.assertPageContains(".mixitemtext .mixitemhead b{flex:1;min-width:0}")
        self.assertPageContains(".mixitemtext .qedition{flex:none;font-style:normal}")
        self.assertPageContains(".javedition.censored{color:var(--muted)}")

    def test_queue_thumbnails_fall_back_to_the_jav_cover(self):
        """没抽过帧的条目在队列里退回番号封套，而不是一个纯黑块。"""
        self.assertPageContains(
            "const thumb=mixFacePoster(x,'small');")

    def test_jav_image_preference_reaches_cards_mix_and_settings(self):
        self.assertPageContains('id="javImageSetting"')
        self.assertPageContains("Object.assign(appSettings,normalizeJavPreferences(appSettings));")
        self.assertPageContains("syncJavImages(document,appSettings.javImage);")
        self.assertPageContains("syncJavImages(staging,appSettings.javImage);")
        self.assertPageContains("? javArtwork(it,jav?layout:'small',eager)")

    def test_jav_cover_source_and_size_are_independent_settings(self):
        self.assertPageContains('JAV 默认封面')
        self.assertPageContains('JAV 封面默认大小')
        self.assertPageContains("[['cover','官方封面',''],['thumbnail','预览图','']]")
        self.assertPageContains("JAV_LAYOUTS,javLayout(),{attr:'data-jav-layout',className:'javimageswitch',text:true}")
        self.assertPageContains('id="javSizeSetting"')
        self.assertPageContains("wireJavLayoutButtons(size)")
        size_body = self.app_js.split('function setJavLayout(value){', 1)[1].split('\n}', 1)[0]
        self.assertNotIn('appSettings.javImage=', size_body)
        cover_body = self.app_js.split("wireIconSwitch(mount,'data-jav-image-choice',choice=>{", 1)[1].split('});', 1)[0]
        self.assertNotIn('setJavLayout(', cover_body)
        self.assertNotIn('appSettings.javLayout=', cover_body)

    def test_the_detail_title_names_which_volume_is_playing(self):
        """分卷队列里换一卷，右侧标题栏必须跟着变。

        同一部片的几卷共用文件名，标题、女优、厂牌逐字相同（实测 PPT-018 三卷）。
        标题栏不写卷号的话，点了队列里另一条，整栏看上去纹丝不动。卷号是「第几份
        文件」而不是版次，所以用中性灰，和无码／中字／破解三种版次色分开。
        """
        self.assertPageContains("const partLabelBadge=(it,queue)=>queue?.kind==='parts'&&it.part_label")
        self.assertPageContains(
            """? `<small class="javedition partlabel">第 ${esc(it.part_label)} 卷</small>`:'';""")
        self.assertPageContains("${javTitleHtml(it)}${partLabelBadge(it,queueContext)}")
        self.assertPageContains(".javedition.partlabel{color:var(--muted);margin-left:6px}")
        # `/api/item` 是单条口径，答不出「这是第几卷」；不从队列补，标题栏就一直空着。
        self.assertPageContains("if(queueContext?.kind==='parts')")
        self.assertPageContains(
            "it.part_label=queueContext.items.find(part=>part.id===it.id)?.part_label||'';")
        # 队列条目那一侧本来就写着卷号，两处用的是同一个字段。
        self.assertPageContains("queue.kind==='parts'?`第 ${esc(x.part_label)} 卷`")

    def test_the_edition_queue_head_only_states_the_count(self):
        """标题栏已经写着「版本」，番号又印在正上方的详情标题里，说明只留数量。

        别的队列标题带真信息（播放列表名、Mix 种子），不能跟着一起砍。
        """
        self.assertPageContains(
            "const summary=queue.kind==='editions'?countLabel:`${esc(queue.title)} · ${countLabel}`")
        self.assertPageContains("<h2>${kindLabel}</h2><span>${summary}</span>")

    def test_queue_rows_carry_the_same_signature_block_as_the_cards(self):
        """队列行和「接着看」并排出现在同一屏，署名层必须是同一套 DOM。

        身份推导也必须共用：各算各的迟早会在同名 creator/performer 上分叉，
        同一条作品在两处指向两个实体。队列整行是一个 <button>，所以头像层
        必须走不可点分支——嵌套 <button> 会被浏览器就地拆散。
        """
        self.assertPageContains("function cardIdentity(it,linked=true)")
        self.assertPageContains("const {avatar,whoHtml}=cardIdentity(it);")
        self.assertPageContains(
            '<span class="mixitemmeta">${cardIdentity(x,false).avatar}<span class="mixitemtext">')
        self.assertPageContains(
            "? `<button class=\"${cls} entitylink\" ${attrs}>${inner}</button>`")
        self.assertPageContains(": `<span class=\"${cls}\">${inner}</span>`")
        self.assertPageContains(
            ".mixitemmeta{display:flex;gap:10px;min-width:0;align-items:center}")
        self.assertPageContains(".mixitemmeta .mav:hover{box-shadow:none}")
        self.assertPageContains(
            ".sgrid.mixgrid>.mixqueue .mixitemmeta{width:100%;padding:0 2px;align-items:flex-start}")
        self.assertPageContains(".sgrid.mixgrid>.mixqueue .mixitemtext{flex:1;min-width:0}")

    def test_narrow_cards_drop_the_third_avatar_and_keep_the_meta_on_one_line(self):
        """216px 的窄卡上第三个头像挤掉的正是署名那一行，元数据会折成三四行。

        横向带的高度由最高的一张决定，于是矮的下面全是空。窄卡只放两个头像，
        元数据钉成一行：大小和观看次数不放，推荐理由留着截尾。不能拿固定高度
        去裁——行高凑不出整行，第三行会露半截字，用户看到的就是被切掉的「399 MB」。
        """
        self.assertCode(
            ".ncard .mavstack .mav:nth-child(n+3),\n"
            ".sgrid.mixgrid>.mixqueue .mavstack .mav:nth-child(n+3){display:none}")
        self.assertPageContains(
            ".ncard .meta .s{flex-wrap:nowrap;overflow:hidden}")
        self.assertPageContains(
            ".ncard .meta .why{flex:1 1 0;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}")
        self.assertPageContains(".ncard .meta .size,.ncard .meta .watchcount{display:none}")
        self.assertPageLacks(".ncard .meta .s{line-height:1.45;height:")

    def test_a_cold_deep_link_fills_the_catalog_below_the_detail(self):
        """深链冷启动时列表一次请求都没发过，排序条底下于是是一整屏空白。

        从列表里点进详情时下面就是那份列表，直接刷新详情页的地址也该有同样的东西。
        补的那一次请求必须走 `load(false)`：`reset` 那条开头就 `disposeStage()`，
        会把刚打开的这一屏详情一起收掉。
        """
        self.assertPageContains("function fillIdleCatalog()")
        self.assertPageContains("if(!grid.querySelector('.catalog-skeleton')&&!$('#stage').querySelector('[data-skeleton=\"detail\"]'))return;")
        self.assertPageContains("void load(false);")
        self.assertPageContains("if(!returnSurfaceReady)fillIdleCatalog();")
        self.assertPageContains("if(reset){barsContext={type:'home',filters:state};"
                                "detailReturnBarsContext=null;disposeStage(false);")

    def test_settings_sort_pair_and_hover_off(self):
        self.assertPageContains('class="settingrow settingrelated"')
        self.assertPageContains('.settingrow.settingrelated{border-top:0}')
        self.assertPageContains("['rating','评分']")
        self.assertPageContains("iconSwapHtml('arrow-up','arrow-down','a',")
        self.assertPageContains("setIconSwap(mark,ascending?'a':'b')")
        self.assertPageContains('class="settingsortcontrols"')
        self.assertPageContains("field.disabled=appSettings.defaultSort==='seed'")
        self.assertPageContains("['hoverDelaySetting','悬停放大',[['0','关闭']")
        self.assertPageContains('boundedPreference(+appSettings.hoverDelaySeconds,0,60,5)')
        self.assertPageContains('if(!appSettings.hoverDelaySeconds)return;')
        self.assertPageContains("if(appSettings.hoverDelaySeconds)el.classList.add('longhover')")

    def test_group_collapse_is_a_setting_and_defaults_to_on(self):
        """合并分卷与版本可以关掉，关掉后同番号的每一卷／每一版各占一张卡。

        折叠是渲染时做的，所以改完必须重取当前列表：不重画的话，之前被跳过的
        那些卡不会自己冒出来，看上去像开关没生效。
        """
        self.assertPageContains("groupCollapse:true,sidebarOrder:DEFAULT_SIDEBAR_ORDER,")
        self.assertPageContains("appSettings.groupCollapse=appSettings.groupCollapse!==false;")
        self.assertPageContains('<input type="checkbox" id="groupCollapseSetting" class="ptoggle" role="switch">')
        self.assertPageContains("$('#groupCollapseSetting').checked=appSettings.groupCollapse;")
        self.assertPageContains(
            "$('#groupCollapseSetting').onchange=e=>{appSettings.groupCollapse=!!e.target.checked;"
            "saveSettings();reloadCurrentSurface()};")
        self.assertEqual(self.page.count("if(!appSettings.groupCollapse)return items;"), 2,
                         "分卷和版次两套折叠都要认这个开关")

    def test_both_collapse_sets_are_cleared_together(self):
        """折叠用的集合必须和分卷那套一起清。

        漏掉的话，第一屏之后每次重画都会把版次卡当成「已经渲染过」直接过滤掉——
        卡片会凭空消失，而且只在翻页或换筛选之后才出现，最难对上原因。
        """
        self.assertEqual(self.page.count("renderedEditionGroups.clear()"),
                         self.page.count("renderedPartGroups.clear()"),
                         "两套折叠集合的重置点必须一一对应")

    def test_the_player_asks_the_one_duration_judge_instead_of_trusting_the_field(self):
        """播放器不许自己判「什么算真时长」，要问 realDuration。

        `-1` 是探测硬失败的哨兵；`Number(it.duration)||0` 对它求值仍是 -1，Video.js
        会把负时长转成 Infinity，然后给本地影片挂上「直播」。判据本身（-1、0、非数字
        都算 0）已经拿真值验收，见 test_web_js.py；这里守的是调用点。
        """
        self.assertPageContains("const expected=realDuration(it.duration);",
                                "播放器仍在拿未经判定的时长，负数会被 Video.js 转成直播")
        self.assertPageLacks("const expected=Number(it.duration)||0;")

    def test_duration_has_one_definition_of_real(self):
        """「什么算真时长」只许有一处说了算。

        散在各处的 `it.duration?` 和 `Number(it.duration)||0` 都挡不住 -1；漏一处，
        那个表面就会渲染出负时钟，或者把影片标成直播。
        """
        self.assertEqual(self.page.count("const realDuration="), 1)
        self.assertPageLacks("Number(player.duration())||Number(it.duration)||0")

    def test_the_page_takeover_block_exists_in_exactly_one_place(self):
        """六行显隐只允许存在一份。再出现第二份就是下一次抄漏的起点。"""
        self.assertEqual(self.page.count("$('#stats').hidden=false"), 1,
                         "又有人手抄了接管块，请改调 showManagementBody()")
        self.assertEqual(self.page.count("$('#managebar').hidden=true"), 1,
                         "隐藏管理条的分支也只能有一处，它是 showManagementBody 的 manage:false")

    def test_every_full_page_view_clears_the_catalog_chrome_through_one_helper(self):
        """整页视图必须走同一个清理函数，不许各自手抄一份。

        用户实测：在 /tags?view=alphabet 点一个标签（目录被它筛住），再点关注页，
        关注页标题上面还挂着「白虎 ✕ 全部清除」——那是目录的生效筛选条，跟关注页
        毫无关系。

        根因不是漏了一行。`enterManagementSurface()` 早就存在而且是对的，但关注、
        播放列表、复核三个页面各自手抄了它的一部分：抄走了 tiers 和 tagbar，漏掉了
        combo，也漏掉了 `loadRequestSeq++`——少了后者，一个在途的目录请求返回后
        还能把筛选条重新画到新页面上。所以这里断言「都调用它」，而不是逐个断言
        「都记得清 combo」：后者只会在下次有人再抄一份时接着漏。
        """
        for name in ("openStats", "openTaste", "openPlaylists", "openReview", "openFollow"):
            self.assertIn("enterManagementSurface()", self._js_function(name),
                          name + " 没有走中央清理函数，多半又手抄了一份不完整的")
        self.assertPageContains("loadRequestSeq++;listLoading=false;$('#combo').innerHTML='';",
                                "中央清理函数必须同时收掉筛选芯片和在途的目录请求")
        # 手抄正是这个 bug 的来源。除了清理函数自己，只有目录内部的管理条可以直接动
        # 这两个元素——它换的是目录自己的形态，而不是切去另一个页面。
        self.assertEqual(self.page.count("$('#tagbar').style.display='none'"), 2,
                         "又有地方手抄了清理逻辑，请改调 enterManagementSurface()")

    def test_the_filter_chips_paint_only_while_the_catalog_is_on_screen(self):
        """芯片的存在由屏幕决定，不由每个整页入口记得清一次决定。

        用户实测：首页筛住「网红主播」后点一个厂牌，资料页标题上面挂着
        「网红主播 ✕ 全部清除」——那条筛选对资料页的作品集不生效，点它的 ✕ 还会把人
        带回目录。三类整页视图都会碰上：资料页、索引页（/tags、/performers、
        /creators）和管理页。

        绘制侧和清除侧都要有。绘制侧管住「谁都别再画上去」：`openEntity` 结尾还会
        `buildBars()`，只在入口擦一次的话它转手就把芯片画回来。清除侧管住「当场擦掉」：
        索引页进去以后一次都不重画芯片，只有绘制侧判据的话，画在那儿的那条会一直留着。
        """
        self.assertPageContains("const catalogOnScreen=()=>$('#index').hidden&&$('#stats').hidden;",
                                "整页视图铺开的是这两个容器，它们就是「目录被盖住了」的判据")
        combo = self._js_function("renderCombo")
        self.assertIn("if(!catalogOnScreen()){$('#combo').innerHTML='';return}", combo,
                      "芯片必须先问过屏幕再画，否则每加一个整页视图就复发一次")
        # 资料页那条是它自己的，读的是这一页的筛选，不是目录的 `state`。
        self.assertIn("entityCombo.innerHTML=comboHtml(barsContext.filters);wireCombo(entityCombo)", combo)
        self.assertPageContains('<div class="combo entitycombo"></div>\n'
                                '    <section class="entitytagbar"',
                                "资料页的交集条挂在标签条正上方，跟首页那条挂在浮层上方是同一个位置")
        self.assertPageContains(".entitycombo:has(+.board-filter-frame .entitytagbar[data-media-only]){display:none}",
                                "交集条列的是作品筛选，照片视图下不成立")
        self.assertLess(combo.index("catalogOnScreen()"), combo.index("$('#combo').innerHTML=\n"),
                        "判据要在拼 HTML 之前，不能画完再擦")
        # 铺开索引页／资料页与进入管理页是同一件事的两侧，各自的共用函数都要收掉芯片。
        self.assertPageContains(
            "$('#stats').hidden=true;$('#index').hidden=false;$('#grid').innerHTML='';"
            "$('#combo').innerHTML='';",
            "索引页与资料页的共用铺开函数必须收掉目录的筛选芯片")
        for name, loader in (("openIndex", "showIndexLoading("), ("openEntity", "showEntityLoading(")):
            self.assertIn(loader, self._js_function(name),
                          name + " 自己铺索引页主体，多半又抄漏了一行")
        # 详情页内联在目录里，两个容器都还藏着：芯片在那里继续成立，不能被一起收掉。
        self.assertPageContains("if(push&&!queueContext)route('/item/'+id);")

    def test_tag_toggles_land_in_the_context_the_click_happened_in(self):
        """标签开关作用在当前这一屏的筛选上，读写用同一个判据。

        资料页顶部标签条的按下态读的是这一页的筛选（`filterState`），点击却直接改
        `state` 并跳回目录：同一枚标签的显示和行为说的不是一回事，点下去人就从
        「新有菜」被扔到 `/?tag=苗条`。抽屉筛选和详情页标签早就走
        `commitContextFilter`，标签条、卡片上的标签和芯片的 ✕ 也必须走它。

        「一个标签是否生效」同样只留一份判据：多处手写 `split(',')` 或
        `=== filters.tag` 时，按下态按多选算、点击按单选写，两边会各自漂开。
        """
        self.assertPageContains("const tagPressed=(value,tag)=>tagList(value).includes(String(tag));")
        self.assertPageContains("const withTagToggled=(value,tag)=>{")
        self.assertPageContains(
            "function toggleTag(t){commitContextFilter("
            "filters=>{filters.tag=t?withTagToggled(filters.tag,t):''})}")
        self.assertPageLacks("state.tag=tg.dataset.tag",
                             "卡片上的标签绕过语境，在资料页点一下就把人带回目录")
        # 顶部标签条、资料页标签、卡片标签、芯片的 ✕ 与「全部清除」：五个入口一个落点。
        self.assertPageContains("wireTagPills($('#tagScroll'));")
        self.assertPageContains("root.querySelectorAll('[data-tag]')"
                                ".forEach(b=>b.onclick=()=>{toggleTag(b.dataset.tag)});")
        self.assertCode("$('#index').querySelectorAll('[data-entity-tag]').forEach(b=>b.onclick=()=>\n"
                        "    toggleTag(b.dataset.entityTag));")
        self.assertCode("commitContextFilter(filters=>{\n"
                        "          filters.tag=tagPressed(filters.tag,tg.dataset.tag)?'':tg.dataset.tag});")
        # 卡片上的实体链接必须限定在卡片自己身上。资料页把 `data-entity-kind` 写在
        # `#index` 上，无界的 closest 会一路找到它：卡片上点标签只会把这一页重开一遍，
        # 标签分支永远轮不到。
        self.assertPageContains("if(ent&&el.contains(ent)){e.stopPropagation();"
                                "openEntity(ent.dataset.entityKind,ent.dataset.entityName);return}")
        self.assertPageContains("$('#index').dataset.entityKind=kind;$('#index').dataset.entityName=name;")
        self.assertPageContains("root.querySelectorAll('[data-untag]')"
                                ".forEach(b=>b.onclick=()=>toggleTag(b.dataset.untag));")
        self.assertCode("if(clear)clear.onclick=()=>commitContextFilter(filters=>{\n"
                        "    filters.tag='';filters.creator='';filters.studio='';filters.owner=''});")
        # 按下态与表头也读同一份判据，资料页的标签因此和目录一样能叠加。
        self.assertPageContains("tagPressed(filterState.tag,t.k)")
        self.assertPageContains("selected:tagPressed(filters.tag,x.k)")
        self.assertPageContains(
            "b.setAttribute('aria-pressed',String(tagPressed(filters.tag,b.dataset.entityTag)))")
        self.assertPageContains("const entityTags=tagList(filters.tag).map(tagLabel);")

    def test_the_follow_url_is_the_only_source_of_truth_for_its_filters(self):
        """关注页的五个筛选必须能在 URL 和界面之间原样往返。

        只把 author 和 media 放进 URL、让 provider、tag、status 活在模块级全局的话：
        离开再回来还按着（谁都不重置它们），刷新就丢，也没法从别处链到一个筛好的
        视图——而标签页要能点一个在线标签直接进「关注 · 这个标签」。

        重置也因此不是一串手写赋值：进入时照 URL 推导，漏一个就体现为往返对不上，
        而不是像从前那样安静地留着上一次的筛选。
        """
        writer = self._js_function("followViewPath")
        reader = self._js_function("readFollowView")
        for key in ("author", "provider", "tag", "work", "status", "media"):
            self.assertIn("'" + key + "'", writer,
                          "followViewPath 没把 " + key + " 写进 URL")
            self.assertIn("'" + key + "'", reader,
                          "readFollowView 没从 URL 读回 " + key)
        # 「全部」是默认视图，缺省即全部，所以它不写进 URL；只有收窄到某个状态才落
        # status。这一排上没有的那一档按全部读回，`status=all` 与 `status=seen` 都在内。
        self.assertIn("if(followFilter)params.set('status',followFilter);", writer)
        self.assertIn("followFilter=FOLLOW_FILTERS.some(([key])=>key&&key===status)?status:'';", reader)

    def test_entering_follow_afresh_derives_state_from_the_url(self):
        entry = self._js_function("openFollow")
        self.assertIn("if(push)route('/follow');", entry,
                      "从窄栏点进来应当回到干净的 /follow")
        self.assertIn("readFollowView()", entry,
                      "进入关注页没有照 URL 推导筛选状态")

    def test_follow_opens_on_the_all_view(self):
        """关注页的默认视图是「全部」，不是「未看」。

        默认「未看」意味着标完最后一条页面就空了，想回看刚才处理过的还得再点一次
        筛选；「全部」是这一页真正的常态。默认值同时决定 URL 形态：全部是默认，
        所以缺省即全部，`/follow` 不带 `status`。
        """
        self.assertPageContains("followFilter='',followBusy=false")
        self.assertPageLacks("followFilter='new'", "重置分支不得把筛选推回旧默认")
        # 从索引页进关注页有两个入口——在线标签那一档和在线名册那一档，两处重置
        # 都得落在同一个默认上。
        self.assertEqual(self.page.count(
            "followMediaView='videos';followFilter='';"), 2,
            "有重置分支还在把筛选推回旧默认")
        self.assertPageContains("[['','全部'],['new','未看']")

    def test_follow_detail_puts_the_actions_above_the_tag_cloud(self):
        """详情侧栏的顺序是正文 → 操作 → 状态 → 标签。

        来源站的标签动辄几十个。标签排在操作之前时，「已看／忽略／保存」被整片标签云
        推到侧栏底下，每处理一条都要先滚过去。标签是可选的参考信息，操作是每条都要用的。
        """
        side = self.page.split('<div class="side followdetailside">', 1)[1].split(
            "</div></div></div>`;", 1)[0]
        actions = side.index('class="fb followdetailactions"')
        state = side.index('class="fstate"')
        tags = side.index('class="stags followdetailtags"')
        self.assertLess(actions, state, "操作条必须在状态行之前")
        self.assertLess(state, tags, "标签必须沉到侧栏最后")
        self.assertPageContains(".followdetailside .followdetailtags{margin:16px 0 0}")
        # 窄屏通用规则会把 .fb 撑满整行，三四个动作键于是变成四个大得离谱的方块。
        self.assertPageContains(".fb.followdetailactions{width:max-content;max-width:100%}")
        self.assertPageContains(".fb.followdetailactions button,.fb.followdetailactions .fdownload{flex:0 0 auto}")

    def test_manage_sort_reads_as_a_select_without_a_loose_text_label(self):
        """排序框用框内前缀图标标明用途，标题行里不挂一个游离的「排序」二字。

        证据：Geist Select 的 prefix 是绝对定位在框内左侧的 16px 图标（`left-3`，输入区
        `pl-10`），而它的文字 Label 是块级、排在控件上方（`block ... mb-2`）——行内并排
        那种写法 Geist 没有。工具行没有上方空间，图标又足够把下拉框和普通按钮区分开。
        """
        # 页面正文归 React，排序是 BoardUI `Select`；骨架照着同一处画，等数据时不挪位。
        self.assertIn('<Select aria-label="关注列表排序" size="sm" selectedKey={sort}',
                      self.read_react("follow-manage/source-list.tsx"))
        self.assertIn("""<span class="fmanagesort" data-collapse-field>"""
                      """${icon('sort')}${selectFieldHtml(""", self.markup)
        self.assertPageContains('id="i-sort"')
        self.assertPageContains(".fmanagesort{position:relative;display:inline-flex;align-items:center")
        self.assertPageContains(".fmanagesort>svg{position:absolute;z-index:1;left:9px;width:16px;height:16px")
        self.assertPageContains(".fmanagesort .gselectfield{height:var(--control-h);padding:0 12px 0 33px")
        # 无障碍名称只剩 aria-label 一处，去掉标签后它必须留着；它由组件写到触发器上。
        self.assertIn("{label:'关注列表排序',attr:'disabled'}", self.markup)
        self.assertCode('aria-expanded="false" aria-label="${esc(label)}"')
        # 标题行里三个可缩项只有说明文字，排序框和动作键都保持完整宽度。
        self.assertPageContains(".fsechead .fbtn,.fsechead .fmanagesort{flex:none}")
        # 允许换行的一行里，说明文字必须以基准 0 参与排线，否则先断行再谈缩放。
        self.assertPageContains(".fsechead .fmeta{flex:1 1 0;min-width:0;overflow:hidden")
        self.assertPageContains("  .fsechead .fmeta{display:none}")

    def test_manage_sort_field_stays_in_the_page_palette(self):
        """排序框的选项列表由站内自绘，配色跟着当前主题走。

        原生下拉的弹出层由操作系统画，不认站内色板；控件各自钉一档 `color-scheme`，
        浅色主题下就是闭合的框浅底、展开的列表深底浅字两套配色。这里的面板底色就是
        页面底色，两条主题选择路径（prefers-color-scheme 与 `[data-theme]`）都落在
        `html` 上，控件靠继承拿到它。
        """
        css = stylesheet_source()
        start = css.index(".fmanagesort .gselectfield{")
        rule = css[start:css.index("}", start)]
        self.assertNotIn("color-scheme", rule, ".fmanagesort 的触发器不声明 color-scheme")
        self.assertPageContains("html{color-scheme:light")
        self.assertPageContains(
            '@media (prefers-color-scheme:dark){html:not([data-theme="light"]){color-scheme:dark}}')
        self.assertPageContains('html[data-theme="dark"]{color-scheme:dark}')
        # 这一行的三个控件——版式开关、排序框、动作键——共用 --control-h。下拉单独缩一档
        # 就是同一行里出现两种「同一种控件」，而缩的偏偏是唯一能改变列表内容的那个。
        self.assertIn("height:var(--control-h)", rule, ".fmanagesort 的触发器与标题行同高")
        self.assertPageContains(".fsechead .iconswitch label{width:34px;height:32px}")
        self.assertPageContains(".fsechead .fbtn{height:var(--control-h)}")

    def test_the_selection_mark_is_one_shape_that_does_not_flip_with_the_theme(self):
        """选中标记全站一个长相：正圆、一对固定的浅片深勾。

        它压在缩略图上，底下是媒体不是页面。取 --ink／--ground 的话，同一张照片上浅色
        一档是深片白勾、暗色一档是浅片深勾，同一个东西两副长相；卡面那圈选中环同理。
        未选态是一个空框，说的是「这里可以点」。
        """
        css = stylesheet_source()
        self.assertIn("--on-media:#F5F7FA; --on-media-ink:#090B0F;", css)
        # 两档同值，所以只在 :root 里声明一次，暗色那两块不重写。
        self.assertEqual(css.count("--on-media:"), 1, "这一对不跟主题分档")
        self.assertPageContains(".selectionMark{display:none;position:absolute;top:10px;right:10px;"
                                "z-index:8;width:26px;height:26px;border-radius:50%;")
        self.assertPageContains(".card.selected .selectionMark{background:var(--on-media);"
                                "color:var(--on-media-ink);")
        self.assertPageContains(".card.selected .pic,.card.selected:hover .pic"
                                "{box-shadow:inset 0 0 0 2px var(--on-media)}")
        for stale in ("background:#F5F7FA;color:#090B0F", "inset 0 0 0 2px rgba(245,247,250,.9)"):
            self.assertPageLacks(stale, "这一对只有 --on-media 一个来源")

    def test_links_that_leave_peach_all_carry_a_mark(self):
        """跳出 Peach 的链接都带标：外链标说「会离开」，站标说「哪个站」。

        2026-09-06 实测 vercel.com 团队页：站内链接（PR 号、部署 ID、项目名）一律裸文字，
        离站的部署域名带一枚 external-link；列表行左端的 provider 标是身份标记，不是动作
        图标。所以带了站标或品牌标的那一类（实体页的社媒、来源行）算已经有标，不再叠一枚。
        每一枚都走同一对类名，包括 `来源资料` 那一处：箭头字符说的是同一件事，
        但它不是那枚标，全站没有第二种写法。
        """
        self.assertPageContains('<a class="externallink" href="${esc(item.url)}"',
                                "死链表那一格整格就是外部地址")
        # 中缩靠改写 textContent 实现，图标留在被省略的节点外面才不会被抹掉。
        self.assertPageContains("<span data-middle-truncate>${esc(item.url)}</span>"
                                "${icon('external-link','externalmark')}")
        self.assertPageContains(".linktable .linkurl a{display:grid;"
                                "grid-template-columns:minmax(0,1fr) auto;")
        # 关注来源那一行已经有站标，链接本身不再叠一枚；同页会离开 Peach 的另外两处
        # （外链搜索建议、凭据的「去取」）走共用的 `ExternalLink`，标由它带。
        self.assertIn('target="_blank" rel="noreferrer noopener" title="打开原来源"',
                      self.read_react("follow-manage/source-view.tsx"))
        self.assertIn("<SourceIcon key={source.id} provider={source.provider} />",
                      self.read_react("follow-manage/source-list.tsx"))
        self.assertIn("<ExternalLink href={search.url}>",
                      self.read_react("follow-manage/add-source.tsx"))
        self.assertIn("<ExternalLink href={row.where}>去取</ExternalLink>",
                      self.read_react("follow-manage/credentials.tsx"))
        self.assertIn("trailingIcon={RiExternalLinkLine}",
                      self.read_react("settings/section.tsx"))
        # 复核卡上「打开原视频」那一处同理，箭头字符不是那枚标。
        review_evidence = self.read_react("review/review-evidence.tsx")
        self.assertIn("trailingIcon={RiExternalLinkLine}", review_evidence)
        self.assertNotIn('↗', review_evidence, "外链标只有图标一种写法")
        # 一处漏掉类名就又变成八档里的第九档，所以按调用点数，不按人工清单。
        self.assertEqual(self.app_js.count("icon('external-link'"),
                         self.app_js.count("icon('external-link','externalmark')"),
                         "web/app.js 里每一枚外链标都带 externalmark")
        root = Path(__file__).resolve().parents[1]
        # island 层的外链标还在拼 HTML 字符串，雪碧图那一枚必须带类名。
        management = (root / 'frontend/src/management.ts').read_text(encoding='utf-8')
        self.assertEqual(management.count('#i-external-link'),
                         management.count('class="externalmark" viewBox="0 0 24 24"'),
                         "management.ts 里每一枚外链标都带 externalmark")

    def test_action_keys_in_every_bar_are_flat_fills_not_outlines(self):
        """动作键一律不描边，自己是一块与条子／卡面不同的面。

        描边档与实心档并排时看着一大一小，差的不是那 1px，是「一个是块面、一个是个框」。
        筛选不在此列：`#tagbar` 那一排与标签分类靠边的虚实说「这条筛选生效没生效」，
        浮在缩略图上的纯图标键也不在此列，那圈半透明白边是它与照片之间唯一的分界。
        """
        css = stylesheet_source()
        for name in (".tagselection button{", ".batchbar button{",
                     ".junkactions button{", ".dupactions.fsechead button{"):
            found = re.search(r"(?:^|[}\n])" + re.escape(name), css)
            self.assertIsNotNone(found, f"{name} 找不到基样式")
            start = found.end() - len(name)
            rule = css[start:css.index("}", start)]
            self.assertIn("border:0", rule, f"{name} 不描边")
            self.assertIn("background:var(--ground)", rule, f"{name} 自己是一块面")
        # 筛选那一排保留边的虚实：它说的是「这条筛选加上去了没有」。
        self.assertPageContains(".tagcategories .pill[aria-pressed=\"true\"]{color:var(--ink);border-color:color-mix(in srgb,var(--tag-color,var(--ink)) 45%,transparent);")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertIn(".board-filter-frame .tagcategories .pill{border:1px solid var(--glass-low);background:transparent}", board)
        self.assertPageContains(".factions button{width:36px;height:36px;"
                                "border:1px solid rgba(255,255,255,.16);")
        # 资源同步那一族按钮的底色自己就画出了按钮，`border-color` 落在 `border:0` 上
        # 是空转的声明：读起来像还有一圈边，实际一像素都不画。
        for rule in re.findall(r"\.resourceaction[^{]*\{[^}]*\}", css):
            self.assertNotIn("border-color", rule, "动作键不描边")

    def test_destructive_buttons_are_solid_red_at_rest(self):
        """危险动作静止态就是 --drop 实底加白字，全站一个写法。

        只描红边、红字的话，静止态和悬停态在暗色底上几乎一样亮，按下去之前看不出这是
        不可逆动作。Geist 的 error Button 就是实心红填充（实测 `rgb(217,48,54)` 底、白字），
        静止态即红；Peach 按用户 2026-09-06 的取舍跟它走，悬停只把同一块红压深一档。
        挤在一行图标里的删除键不在此列：一块实底红在图标行里会炸出一块。判据是这一行里
        还有几颗销毁键，不是键上有没有文字——配置页「移除这个文件夹」同样只有一枚叉，
        可它旁边只有一颗「选择文件夹」，所以它走实底红。

        红只有一个入口，所以这几颗键在标记上带 `.danger`，选择器把类名写两遍换权重。
        页面另起一个单类承担不了这一档：`.resourceaction`、`.junkactions button` 这类容器
        规则自己就填底色，权重不低于页面单类、文件又排在 01-base 后面，红会被容器底色
        盖掉，两边的 CSS 单看都对。
        """
        self.assertPageContains("button.danger.danger{")
        self.assertPageContains("background:var(--drop);color:#fff;box-shadow:none}")
        # 复核卡的拒绝键走 Geist 的 error 变体，那是同一块红的另一个入口。
        self.assertPageContains(".geist-button.error{background:#da2f35;",
                                "销毁键静止态就是实底红")
        # 垃圾复核的「移入回收站」、失效链接的「删除 N 条」。
        for markup in ('class="danger" data-junk-operation="dispose"',
                       'class="resourceaction danger" type="button" id="linkPrune"'):
            self.assertPageContains(markup, "销毁键的红挂在 .danger 上")
        # React 那侧同一块红走 BoardUI 的 danger 变体：关注来源凭据行的「清除」是其中一颗。
        self.assertIn('<Button variant="danger" size="small" disabled={readOnly}',
                      self.read_react("follow-manage/credentials.tsx"))
        # 每个页面各写一份 .danger 的时代结束了：站里只留 01-base 那一条。
        for stale in (".pagelede-actions .batchaction.danger{", ".cleanupfieldset button.danger{",
                      ".playlistactions .danger{", ".dupbtns button.danger{", ".batchbar .danger{"):
            self.assertPageLacks(stale, "危险档只有 01-base 里那一份")

    def test_bulk_actions_read_as_one_group_with_the_count_at_the_left(self):
        """批量操作条只在选中了东西时出现，计数占住左端，动作键排在右端。

        这条是一组动作而不是一段文字，所以整块有 `role="group"` 和自己的名字；计数是
        选中数的播报位，用 `role="status"`，勾掉一行不必把焦点挪过去也能听见。计数靠
        `mr-auto` 吃掉空当，动作键因此贴右端起排，条子多宽都读作同一种版式。
        """
        source_list = self.read_react("follow-manage/source-list.tsx")
        self.assertIn('<div role="group" aria-label="关注来源批量操作"', source_list)
        self.assertIn('<span role="status" className="mr-auto text-body-2-regular text-text-primary">',
                      source_list)
        self.assertIn('{`已选 ${chosen.length} 个来源`}', source_list)
        # 删除是销毁类，红键并且要走确认弹层，不能点一下就没了。
        self.assertIn("<Button variant=\"danger\" size=\"small\" disabled={readOnly}", source_list)
        self.assertIn("confirmLabel: '删除所选来源', danger: true,", source_list)
        # 分区标题行是同一种行：一行里唯一可以缩的是说明文字，动作键要完整读出来。
        self.assertPageContains(".fsechead .fmeta{flex:1 1 0;min-width:0;overflow:hidden")
        self.assertPageContains(".fsechead .fbtn,.fsechead .fmanagesort{flex:none}")

    def test_the_add_form_runs_the_same_lookup_from_enter_and_from_its_button(self):
        """添加关注那一格，回车和「查找」键走同一个入口。

        查找只列候选、不写任何东西，所以在建议里选中一条直接回车也是安全的。两条路
        都收进 `search()`：分成两份实现的话，改了其中一处的人不会想到另一处还在。
        动作键是这一格的主动作，按项目惯例走 primary 实底。
        """
        add = self.read_react("follow-manage/add-source.tsx")
        self.assertIn("if (event.key !== 'Enter') return;", add)
        self.assertIn("search(options[active]?.value || line);", add)
        self.assertIn("onClick={() => search(line)}>查找</Button>", add)
        self.assertIn('<Button variant="primary" size="small" disabled={readOnly || !line.trim()}', add)
        # 输入法拼字途中的那个回车是在选字，不是在提交。
        self.assertIn("if (event.nativeEvent.isComposing) return;", add)
        # 别名表单那个保存键是活的，别顺手一起删。
        self.assertIn("保存别名", self.read_react("follow-manage/alias-manager.tsx"))

    def test_follow_filter_buttons_write_the_url_before_refetching(self):
        """先写 URL 再重取。反过来的话 openFollow 会照旧 URL 把状态推回去。"""
        self.assertPageContains(
            "const applyFollowView=()=>{route(followViewPath());openFollow(false)};")

    def test_photo_wall_uses_cached_thumbnails_and_only_the_lightbox_reads_originals(self):
        # 图片墙铺原图等于一屏付几十兆 PikPak 流量；缩略图由服务端缓存一次。
        self.assertPageContains('<img src="/photo-thumb?id=${item.id}"')
        # 取图口收进 photoSlide：灯箱现在也服务关注页的在线图，模板不能再写死本地口。
        self.assertPageContains(
            ':{src:`/photo?id=${item.id}`,thumb:`/photo-thumb?id=${item.id}`')
        self.assertPageLacks('<img src="/photo?id=${item.id}" class="photocell"')
        self.assertPageContains(
            ".photowall{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}")

    def test_photo_wall_columns_all_start_at_the_top_before_any_thumbnail_arrives(self):
        """固定比例格子和瀑布流图片都在懒加载前占位，防止零高分栏和连续自动翻页。"""
        self.assertPageContains(
            ".photowall{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}")
        self.assertPageContains(
            ".photocell{display:block;width:100%;aspect-ratio:1;border:0;padding:0;margin:0;"
            "background:var(--sunk);")
        self.assertPageContains(
            ".photocell img{width:100%;height:100%;object-fit:cover;display:block;"
            "background:var(--sunk);color:transparent}")
        # 窄屏两列也是网格；这条写在灯箱分区的断点里，和上面同优先级、排在后面。
        self.assertPageContains(
            "  .photowall{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}")
        for lacking, why in (
            (".photowall{column-count:5;column-gap:10px}", "多列流式排版会按零高摊格子"),
            (".photowall{column-count:2;column-gap:8px}", "窄屏那两列同样不能靠图片撑高"),
            (".photocell img{width:100%;height:auto", "高度得由格子给，不能等图片撑"),
        ):
            self.assertPageLacks(lacking, why)

    def test_a_photo_cell_waiting_for_its_thumbnail_is_an_empty_tile(self):
        """图还没到的格子是一块空底，不是一行文件名。

        `alt` 是这张图的文件名，留着给读屏；但格子按比例占好位置之后，浏览器就有地方
        把它画出来，一屏几十格同时在等图，看到的是满屏 `118abp00325pl.jpg`。格子高度
        是 0 的年代看不见它，纯粹是因为没地方画。

        隐去的办法是把字色调成透明，不是删掉 `alt`：删了读屏就只剩一个没有名字的按钮。
        这块 `--sunk` 底本身就是这里的骨架，不另画「正在读取」。
        """
        self.assertPageContains("background:var(--sunk);color:transparent}")
        self.assertPageContains('<img src="/photo-thumb?id=${item.id}" alt="${esc(item.name)}"')

    def test_photo_tab_opens_the_flat_wall_without_album_cover_cards(self):
        self.assertPageContains("if(media==='photos'){renderPhotoWall(kind,name,filters,entityPhotos);return}")
        self.assertPageContains("readout:`${back?esc(data.title)+' · ':'照片 · '}${(data.total||0).toLocaleString()} 张`")
        self.assertPageContains("/api/photos?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}&limit=120&offset=${photoWallItems.length}")
        self.assertPageLacks("renderPhotoSets")
        self.assertPageLacks(".photosetcover{display:block;aspect-ratio:3/4")

    def test_the_photo_view_keeps_the_lower_half_of_the_floating_panel(self):
        """照片这一栏跟视频那一栏是同一块浮层的下半：同一个壳，只是里面不放排序键。

        账本里图片只有文件名、体积和来源，视频那排排序键在这里没有对应的数。换一批跟
        视频那一排同一枚键、同一个位置；大小是列数，一次请求都不发。那排标签数的是视频，
        照片视图下收起来。等着的那一下骨架也带着下半，浮层不会缺一截。"""
        self.assertPageContains("const photoHeadHtml=(data,{back=false}={})=>collectionHeaderHtml({className:'photohead'")
        self.assertPageContains(
            "controls:sortControlsHtml({extra:photoControlsHtml()")
        self.assertPageLacks("photorefresh")
        self.assertPageContains("shufflePhotos(kind,name,filters,entityWide?0:data.id,event.currentTarget)")
        # 换过一批，后面几页沿用同一粒种子。
        self.assertPageContains("seed=data.seed?`&seed=${encodeURIComponent(data.seed)}`:'';")
        self.assertPageContains("offset=${photoWallItems.length}${seed}`")
        # 大小：存进设置，改的只是那面墙上的一个属性。
        self.assertPageContains("photoSize:'small',")
        self.assertPageContains("wall.dataset.size=photoSize();wall.dataset.layout=wall.closest('.skeletonpanel')?'fixed':photoLayout()")
        self.assertPageContains("setPhotoSize(photoSize()==='big'?'small':'big')")
        self.assertPageContains("wirePhotoControls(countRow);syncPhotoWalls()")
        self.assertPageContains("[data-layout=\"masonry\"]>.photocell img{height:auto;aspect-ratio:auto 1}")
        self.assertPageContains("break-inside:avoid;margin:0 0 14px")
        self.assertPageContains(
            '.photowall[data-size="big"]{grid-template-columns:repeat(3,minmax(0,1fr))}')
        self.assertPageContains(
            '  .photowall[data-size="big"]{grid-template-columns:repeat(1,minmax(0,1fr))}')
        # 标签只在视频视图里露面。
        self.assertPageContains("toggleAttribute('data-media-only',now!=='videos')")
        self.assertPageContains(".entitytagbar[data-media-only] .entitytags .pill{display:none}")
        self.assertPageContains(
            "const head=collectionHeaderHtml({readout:'&nbsp;',loading:true,filterRow:'bottom'});")

    def test_the_filter_panel_is_two_rows_on_a_phone(self):
        """手机上这块浮层是两行，两侧也留出跟内容一样的白。

        上半那排标签本来就横滚。下半再让读数和控件各占一行的话，浮层要吃掉三行高度，
        同一块玻璃上一半横滚一半换行，读起来是两个不同的东西。所以下半也保持一行，
        装不下就整条往右滚。首页和资料页是同一句规则，两页不该在这件事上分家。

        滚动开在这一条自己身上，不是里面的 `.sorts`：套两层横滚，触摸时两层抢同一个
        手势，而读数留在外层怎么滚都不走，控件却已经滑没了。控件那 `margin-left:auto`
        只在装得下时把它推到右端，溢出时自身失效，所以窄一点也不会在读数和第一枚键
        之间空出一块。

        左右那 16px 归首页那块：它住在 `body` 底下，两侧没有东西给它留白，22px 的圆角
        直接切在屏幕边沿上；资料页那块在 `#index` 里，`main` 的 16px 已经把它让开了。
        补的就是 `main` 自己那个数，两页的浮层因此和底下的网格对在同一条竖线上。
        """
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains("main{position:relative;z-index:1;padding:14px 16px 90px}")
        self.assertIn("body>.board-filter-frame{margin-inline:16px}", board)
        self.assertIn("  .board-filter-frame .count,.entitycollectionhead{display:flex;"
                      "flex-wrap:nowrap;align-items:center;gap:10px;\n", board)
        self.assertIn("    overflow-x:auto;overflow-y:hidden;scrollbar-width:none;\n", board)
        self.assertIn("  .board-filter-frame .count .sorts,.entitycollectionhead .sorts{flex:none;"
                      "width:max-content;max-width:none;min-width:0;\n    margin-left:auto;"
                      "overflow:visible;padding:0;margin-block:0}}", board)
        for lacking, why in (
            (".board-filter-frame .count{display:flex;flex-wrap:wrap;", "换行就是三行"),
            (".board-filter-frame .count>.mono{width:100%}", "读数不占满一行"),
            ("flex:1 1 100%;width:0;", "控件也不占满一行，宽度更不能被压成 0"),
        ):
            self.assertNotIn(lacking, board, why)
        self.assertPageLacks(".entitycollectionhead{align-items:flex-start;flex-direction:column}",
                             "资料页那一排在窄屏上同样不竖排")

    def test_the_entity_floating_panel_is_one_pane_of_glass(self):
        """首页与资料页使用共享外框，槽位内容保持透明。"""
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        pane = ".board-filter-frame.board-filter-frame.board-filter-frame"
        self.assertIn(pane + '.board-filter-frame>[data-filter-row]{position:relative;top:auto;left:auto;', board)
        self.assertIn('z-index:auto;border:0;box-shadow:none;background:none;', board)
        glass = board.split("\n  background:var(--glass-drift-a),var(--glass-drift-b),"
                            "linear-gradient(125deg,var(--glass-sheen)", 1)[0].rsplit("}", 1)[1]
        self.assertIn(pane, glass, "整块玻璃的材质要跟首页那块走同一条规则")
        for fallback in ("@supports not (backdrop-filter:blur(1px))", "@media(prefers-reduced-transparency:reduce)",
                         "@media(prefers-reduced-motion:reduce)", "html.board-high-contrast .board-filter-frame"):
            line = next(row for row in board.splitlines() if row.startswith(fallback))
            self.assertIn(pane, line, fallback + " 漏了整块玻璃")
        self.assertIn(pane + '.board-is-stuck{box-shadow:inset 0 1px 0 var(--glass-rim)', board)
        self.assertPageContains('mountFilterFrame(top,bottom,')
        self.assertPageContains('mountFilterFrame(boardTagbar,countbar,')
        self.assertPageContains("'tag','state','dur_min'")
        self.assertPageContains("state:button.dataset.entityState")
        self.assertNotIn(".entitytagbar.is-stuck::before{", board)
        self.assertNotIn(".entitytagbar.entitytagbar.entitytagbar,body .review .reviewbulktoolbar{", board)
        self.assertNotIn("body .review .reviewbulktoolbar{clip-path:", board)
        self.assertNotIn("background-image:none;background-color:var(--glass-fill);animation:none}", board)
        # 窄屏上这一排仍是一行，判据在 test_the_filter_panel_is_two_rows_on_a_phone。
        self.assertIn("--glass-pick-shadow:0 1px 2px #1118270f,0 4px 10px #11182714;", board)
        self.assertIn("--glass-pick-shadow:0 1px 2px #00000024,0 6px 14px #0000001f}", board)
        self.assertNotIn("var(--glass-rim),0 1px 2px #00000024", board)
        # 版式、大小这类分段开关在浮层上换材质：壳透明，滑块是选中态那块玻璃。
        self.assertIn(".board-filter-frame.board-filter-frame .iconswitch[data-board-segments]{background:none}", board)
        self.assertIn(".entitycollectionhead.entitycollectionhead.entitycollectionhead "
                      ".iconswitch[data-board-segments]>.board-segment-thumb,", board)

    def test_jav_entity_pages_render_and_wire_the_same_layout_buttons(self):
        self.assertPageContains(
            'section.innerHTML=`${collectionHeaderHtml({controls:entityCollectionSortsHtml(filters)})}')
        self.assertPageContains('entityCollectionSortsHtml=filters=>sortControlsHtml(')
        self.assertPageContains("extra:javActive()?javLayoutButtons():''")
        self.assertPageContains("wireJavLayoutButtons(section)")
        self.assertPageContains("renderEntityCollection(kind,name,{...entityCollectionPage,items:[...entityCollectionPage.items]}")
        # 版式开关和关注列表的紧凑开关是同一个控件：共用 iconSwitchHtml 与 .iconswitch
        # 样式，.javlayout 只留排序行里的位置微调。
        self.assertPageContains("iconSwitchHtml('jav-layout','JAV 卡片版式',JAV_LAYOUTS,javLayout(),")
        self.assertPageContains("{attr:'data-jav-layout',className:'javlayout'}")
        self.assertPageContains('type="radio" name="${esc(name)}" value="${esc(value)}" ${attr}')
        self.assertPageContains("${value===current?'checked':''}")
        self.assertPageContains("wireIconSwitch(root,'data-jav-layout',setJavLayout)")
        self.assertPageContains(".iconswitch label:has(input:checked){background:var(--surface);color:var(--ink)")
        self.assertPageContains("let entityRequestSeq=0,entityJavLayout=false")
        self.assertPageContains("(items.items||[]).some(item=>item.is_jav)")
        self.assertPageContains("return state.jav==='1'||entityJavLayout")
        self.assertPageContains("const jav=javActive()&&!!it.is_jav,layout=javLayout()")

    def test_switching_the_jav_layout_repaints_cards_without_a_request(self):
        """版式是纯展示层的开关：不发请求，也就没有等待态可放。

        卡片 HTML 完全由 CACHE 里那条媒体决定，`load(true)` 会先把整屏换成骨架、再取一遍
        同样的数据；用户点「大图」看到的是列表整屏消失、骨架闪一下、内容再回来。
        逐张换 outerHTML 而不是重跑 batchWithMix：顺序、Mix 落位和分卷／版次折叠都是前几批
        累积下来的，重跑分组会把它们重排。
        """
        body = self.app_js.split("function setJavLayout(value){", 1)[1].split("\n}", 1)[0]
        self.assertIn("repaintCatalogCards()", body)
        self.assertNotIn("load(true)", body)
        self.assertPageContains("function repaintCatalogCards(){")
        self.assertPageContains("if(state.state==='trash'||state.state==='ads')return;")
        self.assertPageContains(
            "grid.querySelectorAll('.card[data-id],.card[data-mix-seed]').forEach(card=>{")
        self.assertPageContains("if(it)card.outerHTML=seed?mixCardHtml(it):cardHtml(it);")
        self.assertPageContains("wireCards(grid);wireMixCards(grid);paintSelection();")
        repaint = self.app_js.split("function repaintCatalogCards(){", 1)[1].split("\n}", 1)[0]
        self.assertIn("releaseHoverPreviews(grid)", repaint)
        self.assertNotIn("renderCatalogLoading", repaint)
        self.assertNotIn("await", repaint)
        self.assertNotIn("batchWithMix", repaint)

    def test_the_people_index_offers_a_big_and_a_compact_layout(self):
        """艺人索引页的两个版式，与 JAV 大图同一条思路、同一个控件。"""
        self.assertPageContains(
            "const PEOPLE_LAYOUTS=[['big','大图 · 竖幅头像','maximize'],"
            "['compact','紧凑 · 圆形头像','layout-grid']];")
        self.assertPageContains(
            "iconSwitchHtml('people-layout',(INDEX_TITLES[kind]||'艺人')+'索引版式',")
        self.assertPageContains("indexLayoutOptions(kind),peopleIndexLayout(),"
                                "{attr:'data-people-layout'});")
        # 只有艺人和创作者是头像网格；标签页那一屏没有图可放大。
        self.assertPageContains("${people?peopleLayoutButtons(kind):''}")
        self.assertPageContains(
            "wireIconSwitch($('#index'),'data-people-layout',setPeopleIndexLayout);")
        self.assertCode('`<div class="igrid" data-cells="${cells}" data-layout="${\n'
                        '    peopleIndexLayout()}">${peopleHtml(d.items)}</div>`')
        self.assertPageContains("peopleLayout:'big'", "默认与 JAV 版式、密度一致：大图为主")

    def test_the_big_people_layout_only_stretches_the_frame_it_does_not_change_columns(self):
        # JAV 大图那条规矩：宽度不变、高度拉长。列宽跟着改的话，窄屏会掉成一列。
        self.assertPageContains(
            '.igrid[data-layout="big"] .icell .ring{width:100%;height:auto;aspect-ratio:3/4;')
        self.assertPageContains(".igrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr))")
        self.assertPageLacks('.igrid[data-layout="big"]{grid-template-columns',
                             "两个版式必须同列宽同列数")
        self.assertPageLacks('.igrid[data-layout="compact"]',
                             "紧凑就是基础样式那一屏，不该再写一份")

    def test_switching_the_people_layout_swaps_the_marks_without_repainting(self):
        # 版式基本是展示层的事：改容器上的一个属性就够，和关注列表版式同一个做法。
        # 例外只有厂牌标识——两个版式要的是不同的一档，那一批得原地换地址。
        self.assertCode(
            "function setPeopleIndexLayout(value){\n"
            "  appSettings.peopleLayout=value;\n"
            "  saveSettings();\n"
            "  document.querySelectorAll('.igrid')"
            ".forEach(grid=>{grid.dataset.layout=peopleIndexLayout()});\n"
            "  // 大格与圆框要的标识不是同一档，换版式就得把已经在页面上的那批换过来。\n"
            "  retargetCompanyMarks($('#index'));\n"
            "  // 框换了大小，「这张图要不要补底」得重算：图早加载完了，"
            "不会再自己发一次 load。\n"
            "  refitNativeImages($('#index'));\n"
            "  fitSkeleton($('#index'));\n"
            "}")

    def test_the_big_people_layout_frames_the_detected_face(self):
        # 3:4 竖幅按几何居中会把脸切掉。换算只有 faceOrigin 一份：资料页写进 img 的
        # style，索引页交给圆框上的 --face——那里的 img 是八处共用的 avatarInner 拼的。
        self.assertPageContains("function faceOrigin(f){")
        self.assertCode("  const origin=faceOrigin(f);\n"
                        "  return origin?` style=\"object-position:${origin}\"`:'';")
        self.assertPageContains("const face=faceOrigin(x.avatar_focus);")
        self.assertPageContains(
            '<span class="ring" data-fit-native="${company?\'mark\':\'portrait\'}"'
            '${face?` style="--face:${face}"`:\'\'}>')
        self.assertPageContains("object-position:var(--face,50% 50%)}")

    def test_photo_lightbox_loads_swiper_lazily_with_thumbs_and_keyboard(self):
        self.assertPageContains("'/vendor/swiper/14.2.0/swiper-bundle.min.js'")
        self.assertPageContains("swiperLoader=Promise.all([")
        self.assertPageContains("style.addEventListener('load',resolve,{once:true})")
        self.assertPageContains("]).then(([,SwiperCtor])=>SwiperCtor)")
        self.assertPageContains("thumbs:{swiper:strip}")
        self.assertPageContains("keyboard:{enabled:true}")
        self.assertPageContains(".photolight{position:fixed;inset:0;z-index:200;background:#000;display:block;overflow:hidden}")
        self.assertPageLacks('<script src="/vendor/swiper', "灯箱才用得上，不进首屏")

    def test_lightbox_image_is_capped_by_height_not_only_width(self):
        """竖图必须整张收进灯箱，不能上下被裁掉。

        主画布使用固定视口的绝对定位，不能再让 grid 行与 Swiper 的百分比高度互相
        依赖；否则超宽视口会把主图行收成 0，让原图按自然尺寸贴到左边溢出。
        """
        self.assertPageContains(
            ".photolight .photomain{position:absolute;inset:0;min-width:0;min-height:0;width:100%;height:100%;overflow:hidden}")
        self.assertPageContains(
            ".photolight .photomain>.swiper-wrapper{display:flex;width:100%;height:100%}")
        self.assertPageContains(
            ".photolight .photomain>.swiper-wrapper>.swiper-slide{flex:0 0 100%;width:100%;height:100%;min-width:0;")
        self.assertPageContains(
            ".photolight .photomain .swiper-zoom-container{width:100%;height:100%;"
            "min-height:0;min-width:0;")
        self.assertPageContains("box-sizing:border-box;display:grid;place-items:center;padding:24px 72px 76px")
        self.assertPageContains(".photolight.has-strip .photomain .swiper-zoom-container{padding-bottom:148px}")
        self.assertPageContains(
            ".photolight .photomain img{max-width:100%;max-height:100%;"
            "min-width:0;min-height:0;")
        self.assertPageContains("box.className='photolight'+(items.length>1?' has-strip':'')")
        self.assertPageContains(".photolight:not(.has-strip) .photostrip{display:none}")
        self.assertPageContains("e.target===box||e.target.classList.contains('swiper-zoom-container')")

    def test_lightbox_nav_classes_avoid_the_generic_next_rule(self):
        """翻页按钮不能叫 `.next`：详情页「接下来」那块用的就是无前缀 `.next`。

        两者同为 0-1-0 特指度且 `.next` 写在后面，padding、border-top 和背景色会
        整块盖过来，图标被挤得偏右下——实测偏移 5px/2px。
        """
        self.assertPageContains('class="media-circle media-overlay photonav back"')
        self.assertPageContains('class="media-circle media-overlay photonav fwd"')
        self.assertPageContains(".photonav.back{left:14px}.photonav.fwd{right:14px}")
        self.assertPageContains(".photonav.fwd svg{transform:rotate(180deg)}")
        self.assertPageLacks('class="photonav prev"')
        self.assertPageLacks('class="photonav next"')

    def test_sprite_icons_declare_stroke_and_no_fill(self):
        """Lucide 描边图标缺 `fill:none;stroke:currentColor` 就被按默认的
        fill:black/stroke:none 画成黑块——深色底上等于看不见，`i-x` 这种纯开放
        路径则整个消失（关闭按钮上「没有 x」就是这么来的）。
        """
        for rule in (
            ".photoback svg{width:15px;height:15px;stroke:currentColor;fill:none",
            ".media-circle svg{display:block;width:24px;height:24px;flex:none;stroke:currentColor;fill:none",
        ):
            self.assertPageContains(rule)

    def test_photo_navigation_reuses_one_overlay_button_treatment(self):
        self.assertPageContains(
            ".media-circle{box-sizing:border-box;width:48px;height:48px;padding:0;border:0;border-radius:50%;")
        self.assertPageContains(".media-circle.media-overlay{background:rgba(0,0,0,.6);color:#fff;backdrop-filter:blur(16px)}")
        self.assertPageContains('class="media-circle media-overlay followimagearrow prev"')
        self.assertPageContains('class="media-circle media-overlay followimagearrow next"')
        self.assertPageContains('class="media-circle media-overlay photoclose"')
        self.assertPageContains('class="media-circle media-overlay photonav back"')
        self.assertPageContains('class="media-circle" id="tokDislike"')
        self.assertPageContains(".followimagearrow{position:absolute;z-index:4;top:50%;transform:translateY(-50%)}")
        self.assertPageContains(".photonav.swiper-button-disabled{opacity:0;visibility:hidden;pointer-events:none}")

    def test_lightbox_offers_wheel_paging_and_an_explicit_zoom_bar(self):
        self.assertPageContains("mousewheel:{enabled:true,forceToAxis:false}")
        self.assertPageContains("const PHOTO_ZOOM_MIN=10,PHOTO_ZOOM_MAX=400,PHOTO_ZOOM_STEP=10")
        self.assertPageContains("return Math.min(100,img.offsetWidth/img.naturalWidth*100,img.offsetHeight/img.naturalHeight*100)")
        self.assertPageContains("else main.zoom.in(ratio)")
        self.assertPageContains('<input type="range" min="${PHOTO_ZOOM_MIN}" max="${PHOTO_ZOOM_MAX}"')
        # zoomChange 的第一个参数是 swiper 实例，倍数在第二个；接错了写进 NaN。
        self.assertPageContains("main.on('zoomChange',(_swiper,scale)=>")
        self.assertPageContains('data-photo-scale="fit" aria-label="适应窗口"')
        self.assertPageContains('data-photo-scale="original" aria-label="原大小"')
        # 文本字形受字体基线影响，会让圆按钮里的 +/- 肉眼偏上或偏下；SVG 几何才稳定居中。
        self.assertPageContains('data-zoom-step="-1" aria-label="缩小">${icon(\'zoom-out\')}')
        self.assertPageContains('data-zoom-step="1" aria-label="放大">${icon(\'zoom-in\')}')
        self.assertPageContains(".photozoom button svg{width:15px;height:15px;display:block;")
        self.assertPageContains(".photobar{position:absolute;z-index:4;bottom:14px;")
        self.assertPageContains(".photolight.has-strip .photobar{bottom:98px}")

    def test_lightbox_centers_the_active_thumbnail(self):
        self.assertPageContains("centeredSlides:true,slideToClickedSlide:true")
        self.assertPageContains("const centerThumb=(at,speed=200)=>strip.slideTo(at,speed)")
        self.assertPageContains("centerThumb(this.activeIndex)")
        self.assertPageContains("centerThumb(index,0)")
        self.assertPageLacks("centeredSlidesBounds:true")
        # 每一张只闭合自己的 slide；wrapper 必须等 map 完成后再闭合。
        # 若把 wrapper 的闭合标签写进循环，浏览器会把第二张起移到轨道外，
        # Swiper 无法切换或居中当前缩略图。
        self.assertPageContains(
            '<img src="${esc(item.thumb)}" alt="" loading="lazy" '
            'referrerpolicy="no-referrer"></div>`).join(\'\')}</div></div>`;'
        )
        self.assertPageLacks(
            '<img src="${esc(item.thumb)}" alt="" loading="lazy" '
            'referrerpolicy="no-referrer"></div></div>`).join(\'\')}'
        )

    def test_lightbox_photo_detail_reveals_by_asset_id_without_leaking_a_path(self):
        self.assertPageContains('aria-label="图片详情" title="图片详情">${icon(\'info\')}</button>')
        self.assertPageLacks("${icon('info')}<span>图片详情</span>",
                             "详情入口只显示圆圈 i，不再加文字按钮外框")
        self.assertPageContains('aria-expanded="false" aria-controls="photoDetail"')
        self.assertPageContains('aria-haspopup="dialog"')
        self.assertPageContains('<section class="photodetail" id="photoDetail" role="dialog" aria-modal="false"')
        self.assertPageContains('aria-labelledby="photoDetailTitle" hidden>')
        self.assertPageContains("LOC[asset.location]||asset.location||'来源未知'")
        self.assertPageContains("size<1024*1024?`${Math.max(1,Math.round(size/1024))} KB`")
        self.assertPageContains("reveal.dataset.photoReveal=String(asset.id)")
        self.assertPageContains("revealSource(Number(reveal.dataset.photoReveal),status,{button:reveal})")
        self.assertPageContains("toast({text:'已在资源管理器中显示'})")
        self.assertPageLacks("已在服务端弹出文件管理器",
                             "定位成功是短暂回执，不能在详情内容流里留下状态行")
        self.assertPageContains(".toasts{position:fixed;right:16px;bottom:22px;z-index:var(--layer-popover)")
        self.assertPageContains(
            "button.innerHTML=`${spinnerHtml('正在定位')}${label?`<span>${esc(label)}</span>`:''}`")
        self.assertPageContains("if(activeLightbox?.detail?.isOpen()){activeLightbox.detail.dismiss(true);return}")
        self.assertPageContains("if(returnFocus&&document.contains(toggle))toggle.focus()")
        # 打开详情要把焦点送进面板。reveal 是「在资源管理器中显示」，只对本地资产存在；
        # 在线图片上它是 hidden 的，焦点这时必须落到标题——对隐藏元素调 focus() 不生效，
        # 人会被留在 toggle 上。标题为此带 tabindex="-1" 才接得住。三条一起守：分支表达式、
        # 标题的 tabindex，以及无条件 reveal.focus() 不许回来。bcf112e 改了实现只更新了
        # tests/test_follow_web.py，这里的旧断言留在原地，master 上因此挂了一段时间。
        self.assertPageContains(
            "wireContextCard(")
        self.assertPageContains(
            '<h2 id="photoDetailTitle" data-middle-truncate tabindex="-1">',
            "标题要接得住焦点，缺 tabindex=-1 时 reveal 隐藏那条路径等于没聚焦")
        self.assertPageLacks(
            "queueMicrotask(()=>reveal.focus())",
            "不能无条件聚焦 reveal：在线图片上它是隐藏的")
        self.assertPageContains("const dismissOutside=target=>{if(panel.hidden||toggle.contains(target)||panel.contains(target))return false")
        self.assertPageContains("if(detail.dismissOutside(e.target))return")
        self.assertPageContains(".photodetail[hidden]{display:none}")
        self.assertPageContains("box-sizing:border-box;display:grid;align-items:start;gap:14px;padding:16px")
        self.assertPageContains(".photodetail .srcstate:empty{display:none}")
        self.assertPageContains(".photodetail>button{min-height:44px}")
        self.assertPageContains(".photodetailtoggle{width:40px;height:40px}")
        self.assertPageContains(".photodetailtoggle{justify-self:start;width:40px;height:40px;display:grid;place-items:center")
        # Lucide 的 info 圆点是长度 .01 的短线；没有圆头时会缩成几乎不可见的横杠。
        css = stylesheet_source()
        start = css.index(".photodetailtoggle svg{")
        rule = css[start:css.index("}", start)]
        self.assertIn("stroke-linecap:round", rule)
        self.assertPageContains('<symbol id="i-info" viewBox="0 0 24 24">')
        self.assertPageLacks("item.path", "图片详情不能取得或渲染 ledger 绝对路径")

    def test_lightbox_remeasures_when_the_window_resizes(self):
        # Swiper 只在构造那一刻量一次容器；灯箱是插进已布好版的页面里的，
        # 窗口一改大小 slide 就停在旧宽度，大图按错误的框缩放。
        self.assertPageContains("new ResizeObserver(()=>{main.update();strip.update();zoomBar.resize()})")
        self.assertPageContains("activeLightbox.resize?.disconnect()")

    def test_the_review_skeleton_is_built_from_the_real_page_containers(self):
        """骨架用最终容器的类名，分栏和列宽就都由页面自己那套规则给。

        两处各抄一份同样的数字，迟早有一处改了另一处没改，表现是读完数据整片版面跳一下。
        """
        self.assertPageContains('class="review review-workspace review-skeleton" data-skeleton="review"')
        self.assertPageContains('<div class="reviewcontrols"><h2 class="review-category-title">复核分类</h2>')
        self.assertPageContains('<div class="reviewbulkbar reviewbulktoolbar" aria-hidden="true">')
        self.assertPageContains("'/review':()=>reviewSkeletonHtml(),")
        # 分类名是静态文案，等的只是每类多少条。
        self.assertPageContains('<span class="skeleton reviewcountskeleton" aria-hidden="true">')
        # 深链冷启动时 `restoreRoute()` 排在骨架后面，`data-surface` 要提前写上。
        self.assertPageContains("document.body.dataset.surface=location.pathname;")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        # 骨架里没有分组条，上面那条玻璃自己封口，也不吸顶。
        self.assertIn("body .review-skeleton .reviewbulktoolbar{position:static;border-radius:16px;", board)
        # 占位卡和到货的卡圆角同一档，不然读完数据整片网格会跳一下。
        self.assertIn(".review-skeleton .skeletoncard{border:0;border-radius:16px;", board)

    def test_immersive_fit_compares_source_against_the_viewport(self):
        """竖屏沉浸模式看横屏视频必须完整显示。

        旧判据只看「片源是不是竖屏」：竖屏片源 contain、横屏一律 cover。于是
        16:9 进 9:19.5 的竖屏视口照样 cover，按高度放大到两边各裁掉一大半，
        也就是「看不全」。判据必须同时看视口比例。
        """
        self.assertPageContains("const source=v.videoWidth/v.videoHeight")
        self.assertPageContains("track.clientWidth/track.clientHeight")
        self.assertPageContains("const mismatch=source>box?source/box:box/source")
        self.assertPageContains("v.classList.toggle('contain',mismatch>TOK_FIT_TOLERANCE)")
        self.assertPageContains(".toktrack video.contain{object-fit:contain}")
        # 旧判据不能残留：它正是「横屏一律铺满」的来源。
        self.assertPageLacks("v.videoWidth<v.videoHeight")
        self.assertPageLacks(".toktrack video.portrait")

    def test_immersive_fit_tolerance_stays_tight_enough_to_not_crop_shorts(self):
        """容差放宽会顺手把竖屏短片改成 cover——那是没人要求的回退。

        9:16 片源在 9:19.5 手机上比例差 1.22；容差必须小于它，这类片源才继续
        完整显示。原代码对竖屏用 contain 是有意的选择，不该被这次修复带走。
        """
        self.assertPageContains("const TOK_FIT_TOLERANCE=1.05")

    def test_immersive_fit_is_recomputed_when_the_viewport_changes(self):
        # 视口比例随旋转和窗口尺寸变；只在 loadedmetadata 算一次，转屏后就错。
        self.assertPageContains("$('#tokTrack').querySelectorAll('video').forEach(tokFitOne)")

    def test_source_tools_never_take_a_path_from_the_client(self):
        """定位和对账都只发 asset id，路径由服务端查。

        `q_item` 是刻意不把 `path` 发给前端的；这两个入口不能反过来让前端把
        路径传进来，否则等于开了一个「任意路径」的接口。
        """
        self.assertPageContains("api('/api/reveal',{method:'POST',body:JSON.stringify({id})})")
        self.assertPageContains("status.textContent='';toast({text:'已在资源管理器中显示'})")
        self.assertPageContains("if(reveal)reveal.onclick=()=>revealSource(Number(reveal.dataset.reveal),status,{button:reveal})")
        reveal_source = self.page.split("async function revealSource", 1)[1].split("async function syncMissing", 1)[0]
        self.assertIn("setActionBusy(button)", reveal_source)
        self.assertIn("status.textContent=''", reveal_source)
        self.assertNotIn("status.textContent='正在定位…'", reveal_source,
                         "请求等待态必须留在按钮内，不能撑开详情内容流")
        self.assertNotIn("button.disabled", reveal_source,
                         "等待按钮应保持可聚焦，并由共享 busy 状态阻止重复请求")
        self.assertPageContains("api('/api/purge-missing',{method:'POST',body:JSON.stringify({id})})")
        self.assertPageContains('data-reveal="${id}"')
        self.assertPageContains('data-sync="${id}"')
        # 在线资产是 URL，没有本地文件可定位。
        self.assertPageContains('${icon(\'chevron-down\')}</button>${it.location===\'online\'?\'\':sourceToolButtons(it.id)}</span>')

    def test_resource_sync_lives_in_data_management_and_keeps_offline_sources_safe(self):
        self.assertPageContains("${(sources.sources||[]).some(source=>['local','115','pikpak'].includes(source.location)&&source.roots?.length)?resourceSyncMarkup():''}")
        self.assertRoute('/resource-sync', "openResourceSync(push)")
        self.assertPageContains("route('/data-cleanup#resource-sync',!push)")
        self.assertPageContains("api('/api/resource-sync/scan',{method:'POST'")
        self.assertPageContains("api('/api/resource-sync/apply',{method:'POST'")
        self.assertPageContains("resourceScanHtml(payload,fmtSize)")
        self.assertPageContains("background:true,restart:true")
        self.assertPageContains("payload.status==='running'")
        self.assertPageContains("location.pathname==='/data-cleanup'")
        self.assertPageContains("background:true,status_only:true")
        # 上一轮跑完的结果是那一刻的快照。进页面就铺开会被读成现在的账本状态，
        # 而页面上没有任何东西说它是旧的。
        self.assertPageContains("if(existing.status==='running')void followScan(existing)")
        self.assertPageContains("清理失效记录与缓存")
        self.assertPageContains('class="resourcesyncfooter geist-fieldset-footer"')
        self.assertPageContains('class="resourcepanel"')
        self.assertPageContains('class="resourceapplyrow"')
        self.assertPageContains(".resourceaction{box-sizing:border-box;height:36px")
        board = (Path(__file__).resolve().parents[1] / "web/board.css").read_text(encoding="utf-8")
        self.assertPageContains(".resourcesyncbox,.resourcepanel{overflow:clip;border:1px solid var(--field-ring);border-radius:var(--floating-radius)")
        self.assertIn(".resourcestat{cursor:default}", board,
                      "结果读数卡不是入口，不接悬停抬色")
        self.assertIn("#resourceSyncResult>.resourceapplyrow{margin:16px 0 0;min-height:0;border:0;background:none;padding:0}", board,
                      "读数卡、Note 与操作行各是独立一层，不再共享一只面板框")
        self.assertPageContains(".resourceapplyrow .resourcesyncok{color:var(--success)}")
        self.assertPageContains(".resourcesync{scroll-margin-top:calc(var(--topH) + 18px);display:grid;gap:16px}")
        self.assertPageLacks(".resourcesync{scroll-margin-top:calc(var(--topH) + 18px);display:grid;gap:16px;margin-top:32px;padding-top:24px;border-top:1px solid var(--line-soft)}")
        self.assertPageContains("border-radius:var(--control-radius)")
        self.assertPageContains("@keyframes geist-spinner-opacity")
        sections = self.page.split("const MANAGE_SECTIONS=[", 1)[1].split("];", 1)[0]
        self.assertNotIn("'resources'", sections)

    def test_source_tool_icons_declare_stroke_and_no_fill(self):
        self.assertPageContains(
            ".srctools button svg{width:15px;height:15px;stroke:currentColor;fill:none")
        self.assertPageContains('<symbol id="i-folder-open"')

    def test_offline_source_is_reported_as_a_refusal_not_a_failure(self):
        # 盘没挂上时拒绝对账，措辞必须让人看懂「不是出错，是我不敢删」。
        self.assertPageContains("'source offline':'来源不在线，已拒绝对账")

    def test_photo_view_is_addressable_and_survives_a_reload(self):
        self.assertPageContains("params.get('media')==='photos'?'photos':'videos'")
        self.assertPageContains("params.set('media','photos')")
        self.assertPageContains("entityMediaView=push?emptyMediaView():parseMediaView(location.search)")

    def test_index_open_is_applied_after_the_surface_reset(self):
        # showHomeSurfaces 会清掉这两个类；写在它前面等于自己加完自己删。
        self.assertCode(
            "  showHomeSurfaces();\n  // 必须在 showHomeSurfaces 之后加：")
        self.assertPageContains("document.body.classList.remove('entity-open','index-open')")


# void 元素没有结束标签，压进栈里只会制造假报错。
_VOID = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})


def tag_balance_problems(source: str) -> list:
    """返回 HTML 里开闭标签不配平的地方，配平时返回空列表。

    只做结构配平，不校验属性与语义：那是另一件事，也没有不引入依赖就能做的办法。
    """
    stack, problems = [], []

    class Balance(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag not in _VOID:
                stack.append((tag, self.getpos()[0]))

        def handle_endtag(self, tag):
            if tag in _VOID:
                return
            line = self.getpos()[0]
            if not stack:
                problems.append(f"第 {line} 行 </{tag}> 没有对应的开始标签")
                return
            if stack[-1][0] == tag:
                stack.pop()
                return
            for index in range(len(stack) - 1, -1, -1):
                if stack[index][0] == tag:
                    skipped = "、".join(
                        f"<{name}>（第 {at} 行）" for name, at in stack[index + 1:])
                    problems.append(
                        f"第 {line} 行 </{tag}> 跳过了仍然开着的 {skipped}，"
                        f"实际关掉的是第 {stack[index][1]} 行的 <{tag}>")
                    del stack[index:]
                    break
            else:
                problems.append(
                    f"第 {line} 行 </{tag}> 无处可配，"
                    f"当前开着的是第 {stack[-1][1]} 行的 <{stack[-1][0]}>")

    parser = Balance(convert_charrefs=True)
    parser.feed(source)
    parser.close()
    for name, line in stack:
        problems.append(f"第 {line} 行的 <{name}> 直到文件结束都没有关闭")
    return problems


class IndexHtmlTagBalanceTests(unittest.TestCase):
    """index.html 的开闭标签必须配平。

    2026-09-03：设置面板的「安全」分组后面多出一个 `</section>`。浏览器按 HTML5
    容错规则把它当成关闭最外层 `section.settingspanel`，随后那三行 `</div></div>
    </section>` 全部无处可配、被静默丢弃。这一处没有造成可见故障——多余标签后面
    只有结束标签、没有内容，已经插入的节点不会被回溯搬走，所以 DOM 与本意一致。
    换个位置就不是这样了：多余标签后面只要还有内容，那些内容就会落到错误的父节点
    下，而页面照样渲染、控制台照样安静。所以这里守的是配平本身，不是某一处症状。
    """

    def test_index_html_tags_are_balanced(self):
        page = Path(__file__).resolve().parents[1] / "web" / "index.html"
        problems = tag_balance_problems(page.read_text(encoding="utf-8"))
        if problems:
            self.fail("index.html 标签不配平：\n" + "\n".join(problems))

    def test_the_balance_checker_actually_catches_a_stray_end_tag(self):
        """门槛自己也要有人守：探测器写坏了会安静地永远通过。

        这里喂的就是 index.html 当时的形状——多余的 `</section>` 跨过两层还开着的
        div，后面跟着三个再也配不上的结束标签。
        """
        self.assertEqual([], tag_balance_problems("<section><div><div></div></div></section>"))
        problems = tag_balance_problems(
            "<section>\n<div>\n<div>\n</section>\n</div>\n</div>\n</section>")
        self.assertEqual(4, len(problems), problems)
        self.assertIn("第 4 行 </section> 跳过了仍然开着的", problems[0])
        self.assertIn("<div>（第 2 行）", problems[0])


class CoverSleeveThresholdTests(unittest.TestCase):
    def test_the_page_and_the_module_share_the_sleeve_thresholds(self):
        """页面按这对阈值决定取景，模块按它分档竖海报；两边的数必须是同一对。"""
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "peach" / "jav_poster_crop.py").read_text(encoding="utf-8")
        low = float(re.search(r"^SLEEVE_RATIO_MIN = ([\d.]+)", source, re.M).group(1))
        high = float(re.search(r"^SLEEVE_RATIO_MAX = ([\d.]+)", source, re.M).group(1))
        page = (root / "web" / "app.js").read_text(encoding="utf-8")
        anchor = re.search(r"r>=([\d.]+)\?'still':r>([\d.]+)\?'sleeve'", page)
        self.assertIsNotNone(anchor, "coverAnchor 的封套判定不见了")
        self.assertEqual((low, high), (float(anchor.group(2)), float(anchor.group(1))))
        self.assertLess(low, high)

    def test_the_face_script_takes_the_thresholds_from_the_module(self):
        """脚本按封套丢掉左半边的脸，用的必须是模块里那一份，不是自己抄的一份。"""
        root = Path(__file__).resolve().parents[1]
        script = (root / "scripts" / "detect_cover_faces.py").read_text(encoding="utf-8")
        source = (root / "src" / "peach" / "cover_artwork.py").read_text(encoding="utf-8")
        self.assertIn("from peach.cover_artwork import face_record", script)
        self.assertIn("jav_poster_crop.SLEEVE_RATIO_MIN <= ratio", source)
        self.assertIsNone(re.search(r"^SLEEVE_RATIO_M(?:IN|AX) = ", script + source, re.M),
                          "阈值抄成第二份就会和页面漂开")


class BoardStyleIsolationTests(unittest.TestCase):
    def test_the_board_layer_is_the_only_interface_and_ships_unconditionally(self):
        """board.css 随页面一起加载，页面上没有第二套界面可选。

        它是盖在 `web/css/` 上的覆盖层，两份一起才画得出一个界面。留一个开关把它摘掉，
        剩下的是一屏对不上的类名——`.board-*` 那些节点仍在 DOM 里，谁也不给它们样式。
        判据落在四处：入口 HTML 无条件引它、首屏那段脚本不再读任何界面偏好、
        `web/` 下没有 `peach.legacy-ui` 与 `original-design` 的消费者、设置里只剩对比度
        这一个开关。
        """
        root = Path(__file__).resolve().parents[1]
        html = (root / "web/index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="stylesheet" href="/board.css">', html)
        entry = (root / "src/peach/web_entry.py").read_text(encoding="utf-8")
        self.assertIn("return f'<style id=\"boardEntryStyles\">{css}</style>'", entry)
        for path in sorted((root / "web").rglob("*")):
            if path.suffix not in {".js", ".css", ".html"} or "dist" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for token in ("peach.legacy-ui", "original-design"):
                self.assertNotIn(token, text, f"{path.name} 仍在读第二套界面的开关")
        app = (root / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("if(!group||document.getElementById('glassContrastSetting'))return;", app)
        self.assertNotIn("legacyUISetting", app)

    def test_icon_centering_does_not_override_toolbar_visibility(self):
        root = Path(__file__).resolve().parents[1]
        css = (root / "web/board.css").read_text(encoding="utf-8")
        rules = re.findall(r'([^{}]+)\{([^{}]*)\}', css)
        centering = [selector for selector, body in rules
                     if 'display:inline-grid' in body and 'place-items:center' in body]
        self.assertTrue(any('.settingshead button' in selector for selector in centering))
        self.assertFalse(any('.ib,' in selector or '.sidebaraddmenu button' in selector
                             for selector in centering))


class MotionRecipeTests(unittest.TestCase):
    """原地换态的那一组动效：时长与缓动只读 token，形态只动合成属性。

    判据全部落在源码上，因为这几条要守的就是「没有写死的毫秒数」和「没有碰布局属性」
    这两件事——浏览器里看得到的是动了没有，看不到的是它凭什么这样动。

    不继承 `WebUiSourceTests`：继承会把它那几百条用例连同这一组再跑一遍，失败也会
    挂到这个类名下。自己读要看的那几份源码即可。
    """

    #: 这一组新增的动效类，每一条都必须只从 token 取时长。
    MOTION_TOKENS = ("--motion-swap", "--motion-reveal", "--motion-stagger")

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        web = cls.root / "web"
        cls.css = stylesheet_source()
        cls.page = chr(10).join(path.read_text(encoding="utf-8") for path in (
            [web / "index.html", *sorted((web / "css").glob("*.css")), web / "app.js",
             *sorted((web / "js").glob("*.js"))]))

    def assertPageContains(self, needle: str, message: str = ""):
        if needle not in self.page:
            self.fail(f"Web 表面缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def test_reduced_motion_zeroes_every_motion_token(self):
        """新加的三档时长跟原有的一样，由那一条全局规则一次关掉，不逐处补。

        `--motion-stagger` 尤其不能漏：时长归零而错峰延迟还在的话，`both` 会把后面
        几位数字按住不显示，读数看上去缺了几位。
        """
        # 三档 token 和原有的那几档住在同一处（board.css 的 `:root`），关掉它们的也是
        # 同一条规则；`stylesheet_source()` 只拼 `web/css/`，board.css 要单独读。
        board = (Path(__file__).resolve().parents[1]
                 / "web/board.css").read_text(encoding="utf-8")
        # board.css 里不止一条 reduced motion 规则，token 那一条认 `--board-motion:0s`。
        start = board.index("--board-motion:0s")
        reduced = board[start:board.index("}", start)]
        for token in self.MOTION_TOKENS:
            with self.subTest(token=token):
                self.assertIn(f"{token}:0", reduced, f"{token} 要在 reduced motion 下归零")

    def test_motion_recipes_only_animate_compositor_properties(self):
        """这几条都长在读数、按钮和整页占位上，一次重排就是一整棵子树。"""
        motion = (Path(__file__).resolve().parents[1]
                  / "web/css/25-motion.css").read_text(encoding="utf-8")
        allowed = {"opacity", "filter", "transform", "translate", "stroke-dashoffset"}
        frames = re.findall(r"@keyframes\s+[\w-]+\{(.*?)\}\s*\}", motion, re.S)
        self.assertTrue(frames, "这份分区里应当有关键帧")
        for body in frames:
            for prop in re.findall(r"([a-z-]+)\s*:", body):
                with self.subTest(prop=prop):
                    self.assertIn(prop, allowed, f"关键帧里不许动 {prop}")
        for declaration in re.findall(r"transition:([^;}]+)", motion):
            for prop in re.findall(r"\b([a-z-]+)\s+var\(", declaration):
                with self.subTest(prop=prop):
                    self.assertIn(prop, allowed, f"过渡里不许动 {prop}")

    def test_icon_swap_stacks_both_glyphs_in_one_cell(self):
        """换字形不重写 innerHTML：重写会把旧字形连同它的动画一起丢掉，读出来是硬切。"""
        self.assertPageContains('.iconswap{display:inline-grid')
        self.assertPageContains('.iconswap>[data-icon]{grid-area:1/1')
        # 退场那一枚还占着同一个格子，不收指针的话按钮上有两个可点区域。
        self.assertPageContains("transform:scale(.25);\n  pointer-events:none")
        self.assertPageContains("export function iconSwapHtml(a,b,state='a'")
        self.assertPageContains("export function setIconSwap(root,state)")

    def test_number_and_text_swaps_only_fire_when_the_value_really_changed(self):
        """首屏那一次不放动画，值没变也不放：同一次重绘里把同样的字再写一遍是常态。"""
        self.assertPageContains("if(previous===undefined||previous===next)return;")
        self.assertPageContains("if(previous===undefined||previous===next){write();return}")
        # 整行重画时读数那一格跟着重建，靠上一次的值判断自己是刚出现还是换了数。
        self.assertPageContains("if(lastCountReadout)readout.dataset.popCount=lastCountReadout;")
        self.assertPageContains(".digits.popping>span{animation:digit-pop-in var(--motion-count) both;")
        self.assertPageContains("animation-delay:calc(var(--motion-stagger) * var(--digit-at,0))")

    def test_skeleton_hands_over_to_content_with_a_cross_fade(self):
        """骨架淡出糊掉、内容同时清晰起来；内容换内容不走这条。"""
        self.assertPageContains("const hasSkeleton=container.querySelector("
                                "'.skeleton,[data-skeleton],.skeletoncard,.countskeleton');")
        self.assertPageContains("if(!hasSkeleton||!container.firstChild){write();return}")
        # 终点帧是内容本来的样子；留着它只多留下一个 filter，那会另起一个 backdrop root。
        self.assertPageContains(
            ".skelreveal>:not(.skelfade){animation:skel-reveal-in var(--motion-reveal) backwards}")

    def test_toggle_thumb_rides_the_shared_press_spring(self):
        """手柄那一下的两跳来自 `--spring-press` 本身，不另写一组带 55%／80% 停的关键帧。

        写成 transition 而不是 animation：animation 一挂上去，进设置页时已经是开态的
        那十几枚开关会当场各弹一次。
        """
        board = (Path(__file__).resolve().parents[1]
                 / "web/board.css").read_text(encoding="utf-8")
        for pseudo in (".ptoggle::after{", ".ptoggle::before{"):
            start = board.index(pseudo)
            rule = board[start:board.index("}", start)]
            with self.subTest(rule=pseudo):
                self.assertIn("transition:transform calc(var(--spring-press-ms)*1ms) "
                              "var(--spring-press)", rule)
                self.assertNotIn("transition:transform .2s", rule)

    def test_success_check_draws_itself_and_failure_does_not(self):
        """成功那一枚勾自己画出来；失败那一枚不画——错误要的是立刻看清。"""
        self.assertPageContains(
            'class="board-notification-icon${alert?\'\':\' checkdraw\'}"')
        self.assertPageContains("@keyframes check-draw{from{stroke-dashoffset:24}"
                                "to{stroke-dashoffset:0}}")
        # 荡那一下走按压弹簧，其余三条走站内那条通用缓动，都不是手写的毫秒数。
        self.assertPageContains("check-bob calc(var(--spring-press-ms)*1ms) var(--spring-press)")

    def test_error_shake_rides_on_the_existing_red_border(self):
        """抖动叠在已经有的红边上：不新增红字，也不改边框色。"""
        self.assertPageContains(':is(input,textarea,select)[aria-invalid="true"],\n'
                                '.board-number-control:has([aria-invalid="true"])'
                                '{animation:field-shake var(--board-motion)}')
        shake = self.css.split("@keyframes field-shake{", 1)[1].split("}}", 1)[0]
        self.assertNotIn("color", shake, "抖动只走 transform，颜色归原有的错误样式")
        self.assertNotIn("border", shake, "抖动只走 transform，边框归原有的错误样式")

    def test_avatar_lift_moves_only_transform_and_never_layout(self):
        """作品卡共演头像抬起一枚：邻座跟着让，但卡片几何一格也不动。

        改 margin 或 width 会推开卡片内容；进出两条缓动由整组的 `:has(:hover)` 切换，
        所以这里也钉住那一对，并排除首页头像与厂牌。
        """
        motion = (Path(__file__).resolve().parents[1]
                  / "web/css/25-motion.css").read_text(encoding="utf-8")
        # 注释本身就在说「不许碰 margin 和 width」，所以只取注释之后那几条声明。
        lift = motion.split("── 作品卡共演头像里指到的那一枚抬起来 ──", 1)[1].split("*/", 1)[1].split("/*", 1)[0]
        for banned in ("margin", "width:", "gap:", "padding"):
            with self.subTest(prop=banned):
                self.assertNotIn(banned, lift, f"抬起来那一下不许碰 {banned}")
        self.assertPageContains(
            "transform:translate(var(--lift-x,0),var(--lift-y,0)) scale(var(--lift-scale,1))")
        self.assertPageContains(
            ".card .mavstack:has(:is(:hover,:focus-visible)){--lift-motion:var(--board-motion)}")
        self.assertPageContains(
            ".card .mavstack .mav:is(:hover,:focus-visible)+.mav+.mav+.mav+.mav{--lift-x:40px}")
        self.assertNotIn("#tiers .tier", lift)
        self.assertNotIn(".brandpill", lift)
        self.assertNotIn("--lift-x:-", motion, "叠放头像不得向卡片左缘移动")
        # 落回走按压弹簧：站内已经有采样自真实弹簧的那一档，不另起一条近似。
        self.assertPageContains("--lift-motion:calc(var(--spring-press-ms) * 1ms) var(--spring-press)")

    def test_clearing_the_search_box_dissolves_the_old_text(self):
        """输入框的 value 是一瞬间没的，飘的是照着它摆的一份复制品。

        复制品先摆好、value 当场清空，光标与输入法一刻也不等这段动画；六个清空入口
        共用同一个函数，漏掉一个就是那条路径上硬切。
        """
        self.assertPageContains("export function dissolveValue(input,host=input&&input.parentElement,")
        self.assertPageContains("if(!next&&searchValueSnapshot.text)clearSearchField(searchValueSnapshot);")
        self.assertPageContains("$('#q').addEventListener('compositionstart',()=>{cancelSearchDissolve();")
        self.assertPageContains("$('#q').addEventListener('beforeinput'")
        self.assertPageContains(".search input.dissolving::placeholder{opacity:0}")
        self.assertPageContains("if(!host.querySelector(':scope > .cleardissolve'))input.classList.remove('dissolving')")
        self.assertPageContains("animation:clear-dissolve var(--motion-reveal) forwards")
        app = (Path(__file__).resolve().parents[1]
               / "web/app.js").read_text(encoding="utf-8")
        self.assertNotIn("$('#q').value='';", app, "清空搜索框只走 clearSearchField")
        self.assertGreaterEqual(app.count("clearSearchField();"), 6)

    def test_count_badges_pop_only_for_the_ones_that_really_changed(self):
        """这几排每换一个筛选都整块重画，按节点判等于每次筛选整列计数一起弹。"""
        self.assertPageContains("export function popBadges(root,scope='')")
        self.assertPageContains("if(previous===undefined||previous===next)return;\n    el.classList.add('popped');")
        # 整枚一起弹，不按位拆：徽标读的是有没有变多，按位拆是读数那一条的事。
        # 起点那一帧不带过渡：带的话挂上去只是开始朝零缩，同一次调用里摘掉时回程无处可走。
        self.assertPageContains(
            ".countbadge.popped{transform:scale(0);opacity:0;filter:blur(2px);transition:none}")
        for call in ("popBadges($('#tagScroll'),'tagbar')",
                     "popBadges($('#drawerScroll'),'drawer')",
                     "popBadges($('#count'),'junk')"):
            with self.subTest(call=call):
                self.assertPageContains(call)

    def test_titles_reveal_by_line_and_leave_no_filter_behind(self):
        """按行不按词：这几处标题正是最常被复制走的几段字，拆成一串 span 会散架。

        走完把类名一并摘掉。留着终点帧上那个 `filter:blur(0)`，非 none 的 filter 会
        另起一个 backdrop root，标题块里任何 backdrop-filter 从此只采样得到它自己。
        """
        self.assertPageContains("export function revealTexts(root,selector='[data-reveal-line]')")
        self.assertPageContains("transition-delay:calc(var(--motion-stagger) * var(--reveal-at,0))")
        self.assertPageContains(
            ".revealline{opacity:0;transform:translateY(12px);filter:blur(3px);transition:none}")
        self.assertPageContains(".revealline.revealing{opacity:1;transform:none;filter:blur(0);")
        self.assertPageContains("el.classList.remove('revealline','revealing')")
        motion = (Path(__file__).resolve().parents[1]
                  / "web/css/25-motion.css").read_text(encoding="utf-8")
        self.assertNotIn("word-break", motion.split(".revealline", 1)[1])
        # 换了页才揭示一遍；同一页里的每一次重画走的也是这个函数。
        self.assertPageContains("if(label===lastManagePageLabel)return;")
        self.assertPageContains("if(moved)revealTexts(heading.parentElement,'h2');")

    def test_the_new_pop_easing_is_a_token_and_reduced_motion_zeroes_it(self):
        """`animation` 里只能有一条缓动函数：token 已经带着一条，再写第二条整条无效。"""
        board = (Path(__file__).resolve().parents[1]
                 / "web/board.css").read_text(encoding="utf-8")
        self.assertIn("--motion-pop:.4s cubic-bezier(.34,1.36,.64,1)", board)
        self.assertIn("--motion-count:.25s cubic-bezier(.34,1.45,.64,1)", board)
        start = board.index("--board-motion:0s")
        self.assertIn("--motion-pop:0", board[start:board.index("}", start)])
        self.assertIn("--motion-count:0", board[start:board.index("}", start)])


if __name__ == "__main__":
    unittest.main()
