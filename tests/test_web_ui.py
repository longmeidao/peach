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
        "21-online.css", "22-followmanage.css",
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
        ".range-fill", "slider-thumb", "range-thumb", ".trace .bar", ".tokbar",  # 进度与数据
        "#censorSetting:checked",  # Toggle 开态：Geist Toggle 实测轨道 rgb(0,112,243)
        ".entitylink", ".flink", ".fsourcelink", ".fcred a", ".tokauthor>a",  # 真正的链接
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

    def test_the_primary_hover_spells_out_its_own_text_colour(self):
        """主动作的悬停规则必须自己写 `color`，不能指望静止态那条留下来。

        `:hover` 只声明 background 时，同一组里更宽的通用悬停（`.fpickactions
        button:hover`、`.tagselection button:hover` 都是）会把文字提到 `--ink`：
        它的选择器更弱，可 `color` 在主动作这条里没有对手，于是浅色实底上落成
        白字白底，鼠标一压按钮上的字就没了。2026-09-04 用户在关注管理页的
        「添加选中」上第二次遇到同一个坑。

        取值只能是静止态那个 `--ground`：Geist Button 的 primary 悬停只把 #EDEDED
        掉一档到 #ccc，文字色不动（`vercel-geist-semantics-measured.md`
        「Button 全变体与状态」）。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(), flags=re.S)
        primary_hover = "background:color-mix(in srgb,var(--ink) 88%,var(--ground))"
        offenders = []
        seen = 0
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            leaf, body = match.group(1).strip().split("{")[-1], match.group(2)
            if ":hover" not in leaf or primary_hover not in body:
                continue
            seen += 1
            if not re.search(r"(?<![-\w])color:var\(--ground\)", body):
                offenders.append(leaf)
        self.assertEqual(offenders, [],
                         f"主动作悬停请补 color:var(--ground)，别把文字交给通用 hover：{offenders}")
        self.assertGreaterEqual(seen, 6, "主动作悬停规则少于预期，检查断言是否还找得到它们")

    # 悬停允许照旧抬填充的两类控件。孤立开关：没有并排的同类邻居，鼠标压着的那颗
    # 就是你正在问的那颗，看不出「按没按」不构成误读。侧栏导航：Geist 自己就把分工
    # 反过来写，见 test_sidebar_nav_keeps_the_hover_fill_and_leaves_state_to_the_color。
    HOVER_FILL_ALLOWED = (
        ".ib",              # 顶栏图标按钮，八个里只有一个有按下态
        ".brandpill",       # 顶栏厂牌胶囊，全站一颗
        ".playerstatsbtn",  # 播放器覆盖层，悬停走 ::after 另一层
        ".fb .like",        # 这一排彩色反馈按钮的既有约定就是悬停预览按下后的颜色
        ".tagpickitem",     # 选中由图标换成对勾表达，填充留给悬停与键盘游标
        ".gselectmenu button",  # 同上；2026-09-04 实测 vercel.com 后台的菜单行，悬停与选中共用同一枚 5% 填充
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
                         f"选中态只留 --hover 底 --ink 字：{offenders}")

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
            if "background:var(--hover)" not in body:
                continue
            for part in leaf.split(","):
                part = part.strip()
                for state in self.STATE_TOKENS:
                    if part.endswith(state):
                        selected_bases.add(part[: -len(state)].strip())
        self.assertIn(".pill", selected_bases, "基线选择器没被认出来，测试本身失效了")
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

    def test_buttons_do_not_shrink_on_press_and_disable_to_a_solid_gray(self):
        """按下不缩放，禁用是实底灰而不是半透明。

        同一次实测：Geist Button 页面上全部按钮的 `transform` 都是 `none`——按下缩放
        是 Peach 自己加的。禁用则是 `rgb(26,26,26)` 底、`rgb(143,143,143)` 字、
        1px `rgb(46,46,46)` 环、`opacity:1`；半透明会让按钮连同它下面的底色一起变淡，
        在深色卡片和浅色卡片上淡出的程度还不一样。
        """
        css = re.sub(r"/\*.*?\*/", "", stylesheet_source(),
                     flags=re.S)
        self.assertNotIn("scale:.96", css, "Geist 按下没有缩放，别再加回来")
        disabled = ("{background:var(--surface);border-color:var(--border-15);"
                    "color:var(--muted);cursor:default}")
        for selector in (".geist-button:disabled", ".fbtn:disabled",
                         ".tagselection button:disabled", ".fpickactions button:disabled",
                         ".fcredactions button:disabled", ".srctools button:disabled",
                         ".frowicon:disabled", ".resourceaction:disabled"):
            self.assertPageContains(selector + disabled)

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
                (".playlistactions button{", "var(--control-radius)"),
                (".playlistdialog{", "var(--floating-radius)"),
                (".playlistpickrow{", "var(--control-radius)"),
                (".settingscard{", "var(--floating-radius)"),
                (".gselectfield{", "var(--control-radius)"),
        ):
            start = css.index(selector)
            rule = css[start:css.index("}", start)]
            self.assertIn(token, rule, f"{selector} 没使用 {token}")
        self.assertNotRegex(css, r"transition:\s*all(?:[; }])")

    def test_close_actions_share_geist_control_geometry(self):
        css = stylesheet_source()
        for selector in (".playlistdialoghead button{",
                         ".mixqueuehead button{", ".settingshead button{"):
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
        self.assertIn(".settingshead button:hover{background:var(--hover);color:var(--ink)}",
                      css)

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

    def test_settings_titlebar_owns_the_full_width_above_its_scroll_container(self):
        self.assertPageContains(".settingsscroll{flex:1;min-height:0;overflow-y:auto;padding:0 20px 20px")
        self.assertPageContains("scrollbar-gutter:stable both-edges;overscroll-behavior:contain")
        self.assertPageContains(".settingshead{z-index:2;display:flex")
        self.assertPageContains("border-bottom:1px solid var(--line-soft);background:var(--frost-panel)")
        self.assertCode('<div class="settingscard">\n    <div class="settingshead">')
        self.assertCode('</div>\n    <div class="settingsscroll">')
        self.assertPageContains("@media(max-width:600px){.settingsscroll{padding:0 17px 17px}")

    def test_studio_metadata_is_not_compiled_as_inline_javascript(self):
        self.assertPageLacks('onerror="this.parentNode.innerHTML=')
        self.assertPageLacks('onload="if(this.naturalWidth')
        self.assertPageContains("img.addEventListener('error',fallback")

    def test_brand_icon_uses_shared_square_png(self):
        self.assertPageContains('<link rel="icon" href="/peach-logo.png" type="image/png">')
        self.assertPageContains('<img class="mark" src="/peach-logo.png" alt="">')

    def test_global_navigation_and_controls_have_accessible_context(self):
        self.assertPageContains('<a class="skiplink" href="#main">跳到正文</a>')
        self.assertPageContains('<main id="main" tabindex="-1">')
        self.assertPageContains('id="filterBtn" title="筛选" aria-label="筛选"')
        self.assertPageContains('id="settingsBtn" title="设置" aria-label="打开设置"')
        self.assertPageContains('name="q" type="search"')
        self.assertPageContains('aria-label="搜索作品、女优、厂牌或标签"')
        self.assertPageContains('id="count" role="status" aria-live="polite" aria-atomic="true"')

    def test_browser_chrome_focus_and_mobile_inputs_follow_the_ui_checklist(self):
        self.assertPageContains('<meta name="theme-color" content="#FFFFFF"')
        self.assertPageContains('<meta name="theme-color" content="#080A0D"')
        # 聚焦环用 color-mix 柔化：边框 72% 主调 + 26% 的外圈，仍是「看得见的焦点」。
        self.assertPageContains('.search:focus-within{border-color:color-mix(in srgb,var(--tungsten) 72%,transparent);box-shadow:')
        self.assertPageContains('@media (max-width:760px){input,textarea,select{font-size:16px!important}}')
        self.assertPageContains('button,a,input,textarea,select,summary{touch-action:manipulation}')

    def test_search_inputs_share_one_component_with_a_visible_focus_ring(self):
        """带搜索语义的输入只有一份实现，点进去看得见焦点。

        Geist Search Input 的契约是：搜索图标占前缀位，查找中原位换 Spinner，
        输入框几何不变。关注页先有了这套，索引页的筛选框却是另一份私有样式——
        没有前缀图标、没有任何 focus 规则，点进去和没点一个样。
        """
        self.assertPageContains("export function searchInputHtml({label,id='',name='',value='',placeholder='',attrs=''}={})")
        self.assertCode("""const parts=[
    'type="search"',""")
        self.assertPageContains('<input ${parts}></div>')
        self.assertPageContains('<div class="geist-search" data-search-input>')
        self.assertPageContains(
            """<span class="geist-search-prefix" data-search-prefix>${icon('search')}</span>""")
        # 焦点环与顶部搜索框同一个配方，不是第二种蓝。
        self.assertCode('.geist-search input[type="search"]:focus{outline:0;'
                        'border-color:color-mix(in srgb,var(--tungsten) 72%,transparent);'
                        'box-shadow:0 0 0 3px color-mix(in srgb,var(--tungsten) 26%,transparent)}')
        # 忙态换的是前缀位，输入框自己不动；hook 跟着组件走，不留关注页专属的名字。
        self.assertPageContains("form.querySelector('[data-search-prefix]')")
        self.assertPageContains("if(prefix)prefix.innerHTML=spinnerHtml('查找中');")
        self.assertPageLacks("data-follow-search-prefix")
        self.assertPageLacks("fsearchprefix")
        # 两个调用点都走组件；索引页的筛选框不再用 placeholder 当标签。
        self.assertPageContains("searchInputHtml({id:'iq',label:'过滤'+title,value:q||''})")
        self.assertPageContains("searchInputHtml({name:'line',label:'来源链接、名字或 id',")
        self.assertPageLacks('<input id="iq" placeholder="过滤…"')
        self.assertPageLacks(".isearch")

    def test_filtering_waits_for_the_chinese_ime_to_finish_composing(self):
        """选字过程中不查询：拿半截拼音去筛选，筛的是「zhon」这种不存在的词。

        `input` 在组字过程中照样发，事件上的 `isComposing` 是唯一可靠的判据；
        组完由 `compositionend` 接手。回车同理——那一下是定字，不是提交。
        """
        self.assertPageContains("iq.oninput=e=>{if(e.isComposing)return;refineIndex()};")
        self.assertPageContains("iq.oncompositionend=refineIndex;")
        self.assertPageContains("$('#q').oninput=e=>{if(e.isComposing)return;refreshSearchMenu()};")
        self.assertPageContains("$('#q').oncompositionend=refreshSearchMenu;")
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
        也不该重画表头。表头里随查询变的只有计数，单独改它。
        """
        self.assertPageContains("async function openIndex(kind,q,push=true,refine=false)")
        self.assertPageContains("if(!refine)showIndexLoading(people?'正在读取作者':'正在读取标签')")
        self.assertCode("""if(refine&&$('#iq')){
    $('#indexCount').textContent=countText;
    $('#indexFilters').innerHTML=filters;
    $('#indexBody').innerHTML=body;
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
        self.assertPageContains('queueMicrotask(()=>{syncHeaderActions();paintListTitle()})')
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
        self.assertPageContains("performers.slice(0,3)")
        self.assertPageContains("data-entity-kind=\"performer\" data-entity-name=\"${esc(nm)}\"")
        self.assertPageContains("data-entity-name=\"${esc(performer)}\"")
        self.assertPageContains("等 ${performerTotal} 人")
        self.assertPageContains(".mavstack .mav+.mav{margin-left:-14px}")

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
            "const src=useEntity?`/entity-image?kind=${kind}&id=${id}`:(rep?`/avatar?id=${rep}`:'');")
        # 一环都取不到就一个 `<img>` 都不出，首字母垫底直接露出来。
        self.assertPageContains("if(!src)return '';")
        # kind 参数化后，创作者复核卡片也能走同一条链；默认仍是 performer，
        # 既有调用点不受影响。
        self.assertPageContains("function avatarInner(name,ref,repId,kind='performer')")
        # 兜底链声明在模板里，行为归 image-fallback 那条委托监听。
        self.assertPageContains("const fallbacks=useEntity&&rep?[`/avatar?id=${rep}`]:[];")
        self.assertPageContains("imageFallbackAttrs({dropStyle:dropStyle&&useEntity,fallbacks})")

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
        self.assertPageContains("x.entity_id?{id:x.entity_id,has_image:x.has_image}:null,")
        self.assertPageContains("x.has_avatar?x.rep:null, entityKind)")
        # 口味榜（`/api/taste`）：两列直接长在榜行上，判据仍是同一对。
        self.assertPageContains(
            "const ref=row.entity_id?{id:row.entity_id,has_image:row.has_image}:null,")
        self.assertPageContains("rep=row.has_avatar?row.representative_asset_id||null:null;")
        # 沉浸模式署名圈读 `/api/item` 的 entity_refs，标志随引用一起来；代表作那一侧
        # 读 REP，入表时已经按 has_avatar 筛过。
        self.assertPageContains(
            "const ownerRef=ownerKind?(full.entity_refs?.[ownerKind]?.[0]||null):null;")
        self.assertPageContains(
            "tops.performers.forEach(x=>{if(x.rep&&x.has_avatar)REP[x.k]=x.rep});")

    def test_review_face_kinds_agree_between_the_page_and_the_endpoint(self):
        """复核卡片那张脸的 kind 两边各存一份，必须逐字一致。

        页面按 `ENTITY_REVIEW_CATEGORIES` 拼 `/entity-image?kind=`，服务端按
        `web_review.ENTITY_REVIEW_KINDS` 判「这个实体有没有图」。一边判成 creator、
        另一边按 performer 取图，就是标志说有图而请求照样 404：两份表各自都不会报错，
        页面上看到的只是又一张碎图。
        """
        # 这个文件其余断言只读页面源；这一条守的正是页面与服务端的对不上，
        # 所以必须两边都看。
        from peach.web_review import ENTITY_REVIEW_KINDS

        declared = re.search(r"const ENTITY_REVIEW_CATEGORIES=\{([^}]*)\}", self.app_js)
        self.assertIsNotNone(declared, "页面那份表不在了；改名的话服务端也得跟着改")
        self.assertEqual(dict(re.findall(r"(\w+):'(\w+)'", declared.group(1))),
                         ENTITY_REVIEW_KINDS)

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
        self.assertPageContains("style:facePos(d.avatar_focus),dropStyle:true")
        # 取景是按实体图算出来的，所以内联 style 和 data-drop-style 只贴给第一环。
        self.assertPageContains("${useEntity?style:''}")
        self.assertPageContains("imageFallbackAttrs({dropStyle:dropStyle&&useEntity,fallbacks})")
        self.assertPageContains("if ('dropStyle' in image.dataset) image.removeAttribute('style');")

    def test_entity_link_favicons_do_not_leak_the_page_url_to_the_linked_site(self):
        # 外链的 favicon 是向对方站点发出的真实请求。锚点上的 rel="noreferrer" 只管
        # 点击跳转，管不到这个 <img>——不设 referrerpolicy 的话，光是打开一位女优的
        # 资料页就会把 Peach 的页面地址报给 x.com、事务所站等每一个被链接的站点。
        # 同页的 taste 行早就是 no-referrer，这里此前漏了；资料页链接从 5 条涨到两百
        # 多条之后，漏的这一处才真正开始有代价。
        # 现在更进一步：图标由本机 `/link-mark` 提供，浏览器根本不再向对方站点发请求，
        # 也就无从泄露。referrerpolicy 仍然留着——它守的是这条约束本身。
        self.assertPageContains('class="entityfavicon" src="${esc(linkMarkUrl(x))}"')
        self.assertPageLacks('src="${esc(faviconUrl(x.url))}"',
                             "外链图标不应再直接指向对方站点")
        anchor = self.app_js.index('class="entityfavicon"')
        self.assertIn('referrerpolicy="no-referrer"',
                      self.app_js[anchor:anchor + 260],
                      "资料页外链 favicon 必须带 no-referrer")

    def test_no_caller_ever_hands_the_link_mark_endpoint_a_url(self):
        # 让前端把地址递给服务端去取，等于开一个任意地址抓取的口子。和 `/follow-stream`
        # 同一条规矩：服务端只取账本里已有的地址。`linkMarkUrl` 自己只吐 id 由
        # test_web_js.test_the_link_mark_endpoint_only_ever_carries_an_id 验收；
        # 这里守的是「没人绕过它另写一个带地址的调用」。
        self.assertPageLacks("/link-mark?url=", "外链图标端点不得接受前端给的地址")

    def test_social_links_show_only_the_platform_mark_not_the_handle(self):
        # handle 是网址的一部分，写出来只是把 URL 抄一遍：`X @remu19971203` 里真正有
        # 信息量的只有那个 X。图标本身就说明了去哪，名字留给官网那种「点之前看不出是谁」
        # 的链接。纯图标没有可读文字，所以标签必须留给辅助技术，不能整个丢掉。
        self.assertPageContains('<a class="iconlink" href="${esc(x.url)}"')
        self.assertPageContains('<span class="sr-only">${esc(x.label)}</span></a>')
        self.assertPageContains('.entitylinks a.iconlink{padding:4px;gap:0;border-radius:50%}')

    def test_a_studio_official_link_shows_its_url_and_no_icon(self):
        # 厂牌页的头像就是厂牌 logo，旁边再放一枚同品牌的小图标只是把同一个东西说两遍；
        # 域名本身就是名字，比图标说得清楚。女优页不一样：那里的头像是人，事务所图标
        # 不构成重复，标签也是事务所名而非域名。
        self.assertPageContains("if(kind==='studio')")
        self.assertPageContains('<a class="urllink" href="${esc(x.url)}"')
        self.assertPageContains("${esc(linkHost(x.url)||x.label)}")
        self.assertPageContains(".entitylinks a.urllink{padding:4px 14px")

    def test_entity_links_have_no_external_arrow(self):
        # `target="_blank"` 已经是外链，箭头只是重复；一排链接里它还会挤掉本就不多的
        # 横向空间。整条 CSS 一并删掉，别留下没人用的类名。
        self.assertPageLacks('entitylinkarrow', "外链箭头应当已删除")
        self.assertPageLacks('↗', "外链箭头字符应当已删除")

    def test_x_links_use_an_inline_brand_mark_instead_of_a_fetched_favicon(self):
        # favicon 是别人服务器上的一张小位图：X 直接挡掉爬取（资料页上那个空白白圆就是
        # 它），取到的也多是 16×16，放进 32px 的圆里必然糊。416 条社媒链接里 372 条是
        # x.com／twitter.com，只给它一个内联标记就覆盖了 89%，还省一次跨站请求。
        # 哪些主机走内联标记（含子域、且只认后缀边界）由
        # test_web_js.test_brand_marks_cover_the_host_and_its_subdomains_only 验收。
        self.assertPageContains('<symbol id="i-brand-x"')
        # 填充字形不吃通用的 stroke:currentColor;fill:none。
        self.assertPageContains('.entitylinkicon.brand svg{width:15px;height:15px;fill:currentColor;stroke:none}')

    def test_the_entity_hero_is_a_centred_single_column_on_phones(self):
        # 左像右文那套是给宽屏的：手机上 92px 头像旁边只剩两百多像素，别名和链接被挤成
        # 两三行，头像下面又空着一大片。按 beeg 的资料页改成单列居中。
        self.assertPageContains(
            ".entityhero{grid-template-columns:minmax(0,1fr);gap:12px;padding:8px 0 18px;"
            "justify-items:center;text-align:center}")
        self.assertPageContains(".entityhero .entitylinks{justify-content:center")

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
        # 五个调用点，一个都不许再留原生 checkbox 的 accent-color。
        for attrs in ("data-follow-enabled=", "data-srcfilter=", "data-pick=",
                      "data-tag-match-any", 'id="groupCollapseSetting"'):
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
        # `.sorts` 是不换行的横向滚动条，里面的项默认可收缩，而 `.javlayout` 自己带着
        # `min-width:0`（fieldset 需要它才不撑破容器）。两条合起来允许它被压到内容宽度
        # 以下：窄屏上三个 34px 的版式按钮会叠在一起，还压住旁边的「发行时间」。
        # `.sorts button` 早有 `flex:0 0 auto`，但 fieldset 不是 button，选不到它。
        self.assertPageContains(".sorts .javlayout{display:inline-flex;gap:2px;margin:0 6px;flex:none}")

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
        self.assertPageContains(".idcell:not(.entitylink){cursor:default}")
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
        load_body = self.page.split("async function load(reset)", 1)[1].split("const loadObserver", 1)[0]
        guard = load_body.index("if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return;\n  cache")
        self.assertLess(guard, load_body.index("cache(d.items)"))

    def test_bulk_follow_updates_run_with_bounded_concurrency(self):
        """一千条串行 POST 全靠往返等，界面按住不放；一次全发出去又会挤满连接。"""
        self.assertPageContains("const mapLimit=async(items,limit,run)=>")
        self.assertPageContains("const workers=Math.min(Math.max(1,limit),list.length)")
        # 某一项失败只记下原因，不中断整批。
        self.assertPageContains("catch(error){results[index]={ok:false,error}}")
        bulk = self.app_js.split("root.querySelectorAll('[data-follow-bulk]')", 1)[1]
        bulk = bulk.split("root.querySelectorAll('[data-follow-view]')", 1)[0]
        self.assertIn("await mapLimit(ids,6,id=>", bulk)
        # 撤销那两处仍是单条 POST，不该被这条契约波及。
        self.assertNotIn("for(const id of ids)", bulk)
        self.assertPageContains("actionFailure(`批量更新 ${failed.length}/${ids.length} 项`")

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

    def test_scrollbar_gutter_is_reserved_so_overlays_do_not_shift_the_page(self):
        """设置面板给 body 加 overflow:hidden，滚动条一消失整页就横向跳一次。"""
        self.assertPageContains("scrollbar-gutter:stable}")
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
        self.assertPageContains('.geist-button.primary{border-color:var(--ink);background:var(--ink);color:var(--ground)}')
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
        self.assertPageContains("const ENTITY_LABELS={performer:'艺人'")

    def test_narrow_top_bar_keeps_the_actions_on_the_right(self):
        """窄屏下搜索框绝对定位后脱离了流，动作按钮会挤在品牌名右侧、右半条留空。"""
        self.assertPageContains("#immerseBtn{margin-left:auto}")

    def test_deleting_one_search_record_keeps_the_menu_open(self):
        """删除按钮不能抢焦点，也不能整段重建下拉栏。

        抢焦点会触发 `#q` 的 blur，那个 handler 140ms 后无条件关掉下拉栏；
        整段重建则会把推荐词重新洗牌，删一条历史却换了一批推荐。
        """
        self.assertPageContains("b.onmousedown=e=>e.preventDefault();")
        self.assertPageContains("if(group&&!group.querySelector('[data-search-value]'))group.remove();")

    def test_card_aspect_ratio_actually_reaches_the_element(self):
        """算出来的卡片比例必须写进 DOM。

        `ar` 从写下起就没有被使用过：`.pic` 写死 `aspect-ratio:16/9`，于是 JAV 的两种
        版式渲染出来一模一样，竖屏条的 `--card-ratio` 也永远取不到值。
        """
        self.assertPageContains('<div class="pic" style="--card-ratio:${ar}">')
        self.assertPageContains(".pic{position:relative;aspect-ratio:var(--card-ratio,16/9)")

    def test_card_hover_edge_sits_above_the_cover_and_leaves_layout_alone(self):
        """悬停描边由覆盖层伪元素承担，有没有封面都是同一条线。

        `.pic` 是 `border-box`：描边写成 `border` 会把内容盒收窄 1px，里面 `contain`
        的封面跟着缩一圈、两侧多露一截黑底。写成 `outline` 不占布局，但它落在 padding
        box 最外一圈，铺满 `inset:0` 的封面和悬停视频是定位子元素，会把它盖掉——
        缺封面的卡有线、有封面的没有，同一个网格里两种卡的悬停反馈对不上。
        """
        self.assertPageContains(
            '.card:hover .pic::after{content:"";position:absolute;z-index:6;inset:0;'
            'pointer-events:none;')
        self.assertPageContains(
            "  border:1px solid color-mix(in srgb,var(--ink) 48%,transparent);"
            "border-radius:inherit}")
        self.assertNotIn(
            ".card:hover .pic{", self.css,
            "描边落在 `.pic` 自己身上就会参与布局或被封面盖住，只能写在伪元素上")
        # 回收站卡片的缩略图不描边，抵消的对象也得跟着是伪元素。
        self.assertPageContains(".junkcard:hover .pic::after{content:none}")

    def test_big_jav_layout_crops_to_the_front_cover(self):
        """大图＝宽度不变、高度拉长，只留封套右侧那块正封。

        `object-fit:cover` 只有在容器比图片更竖时才横向裁切；容器一旦宽过封套的
        1.48，就变成纵向裁切、整张封套原样铺满——这正是旧版式「只是撑满画布」的原因。
        所以裁切必须由容器比例决定，不能只靠 object-position。
        """
        self.assertPageContains("const COVER_FRONT_RATIO=0.7;")
        self.assertPageContains("(jav&&layout==='big'?COVER_FRONT_RATIO:16/9)")
        self.assertPageContains('.poster.cover.front[data-frame="sleeve"]{object-position:100%')
        self.assertPageContains("r>=1.65?'still':r>1.2?'sleeve':'front'",
                                "16:9 官方剧照不能当成双页封套裁到最右侧")
        # 判据是 `jav` 不是 `useCover`：缺封面的卡片也要拉长，用 16:9 预览图上下留黑边，
        # 否则一行里高矮混排会把网格撕成锯齿状。
        self.assertPageLacks("useCover&&layout==='big'")
        # 旧键要继续认，设置存在浏览器里，改名不能让用户的选择静默回落。
        self.assertPageContains("const JAV_LAYOUT_ALIASES={cover:'big',sleeve:'small'};")

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
            "if(img instanceof HTMLImageElement&&img.classList.contains('cover'))coverAnchor(img);")
        self.assertPageLacks('onload="', "模块作用域的函数在内联属性里取不到")

    def test_card_avatar_and_name_open_the_same_entity(self):
        """同一张卡上的头像和名字必须指向同一个身份。

        头像先看 performer、名字先看 creator 的话，碰上同名的 creator/performer
        重复实体（账本里 35 组）就会一个跳 /performers/x、另一个跳 /creators/x。
        """
        self.assertPageContains(
            "const avatarKind=identity.kind||(performer?'performer':"
            "(primaryCreator?'creator':(it.studio?'studio':'')));")
        self.assertPageContains(
            "const avatarName=identity.kind?identity.name:"
            "(performer||primaryCreator||it.studio||who);")

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
        # 左右 8、两者间距 4、同高 36、纵向各 8——全部取自 `.top` 自己的 padding/gap。
        self.assertPageContains(".search{position:absolute;left:48px;right:8px;top:8px;height:36px")
        self.assertPageContains(".searchback{display:inline-flex;position:absolute;left:8px;top:8px")

    def test_unlinked_identity_does_not_look_clickable(self):
        """没有实体链接的归属不能长得像链接。

        番号、「未归属」这类值没有资料页可去，渲染成 `<span>`；但它和按钮共用
        `.who` 的强调色，看着能点，点下去落到卡片本身、打开的是视频详情。
        """
        self.assertPageContains(".meta span.who{color:var(--ink-2);cursor:default}")

    def test_random_is_the_default_and_each_home_visit_gets_a_fresh_batch(self):
        """每次进入首页换种子，同一次访问的分页继续稳定。"""
        self.assertPageLacks("const SEED_KEY='peach.seed.v2';")
        self.assertPageLacks("localStorage.getItem(SEED_KEY)")
        self.assertPageContains("seed:initialParam('seed')||rollSeed()")
        self.assertPageContains("sort:appSettings.defaultSort,dir:defaultSortDir(appSettings.defaultSort)")
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
        self.assertPageContains('id="batchAction" type="button"')
        self.assertPageContains("state.sort='seed';state.dir='';state.seed=rollSeed()")
        # 刷新属于列表，不再占顶栏；JAV 共用同一计数/筛选行。
        self.assertPageLacks('id="refresh"')
        self.assertPageContains("+(javActive()?javLayoutButtons():'')")

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
        self.assertPageContains("const defaultSortDir=key=>SORT_DIR_WORDS[key]?'desc':'';")
        self.assertPageContains("function resolveSort(rawSort,rawDir,fallback=appSettings.defaultSort){")
        # 点未选中项＝换列并用该列默认方向；点选中项＝翻方向；随机没有方向。
        self.assertPageContains("function nextSortState(key,current,dir){")
        self.assertPageContains("if(key!==current)return{sort:key,dir:defaultSortDir(key)};")
        self.assertPageContains("if(!SORT_DIR_WORDS[key])return null;")
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
            "next?` aria-label=\"按${label}${next.dir?sortDirWord(next.sort,next.dir):''}排序\"`:''")
        self.assertPageContains("icon(dir==='asc'?'arrow-up':'arrow-down','sortdir')")
        self.assertPageContains("const followSortLabel=()=>`按${FOLLOW_SORT_LABELS[followManageSort]||'关注列表'}${")
        # 箭头必须真在 sprite 里，否则选中项渲染出一个空 use，方向就完全看不见。
        self.assertPageContains('<symbol id="i-arrow-down" viewBox="0 0 24 24">')
        self.assertPageContains('<symbol id="i-arrow-up" viewBox="0 0 24 24">')
        # 自带 class 而不是选 `button>svg`：同一排里的批量键是方形图标键，
        # 那样写会给它的图标也加上左边距，把它顶偏。
        self.assertPageContains(".sortdir{width:14px;height:14px;flex:none;margin-left:5px;")

    def test_sort_direction_travels_in_the_url_and_the_stored_default(self):
        """方向进地址栏与设置：等于该列默认值时不写，旧默认值迁移到当前键。"""
        self.assertPageContains("'orient','sort','dir','q','jav']")
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

    def test_insight_tables_follow_the_bordered_variant_with_the_empty_state_outside(self):
        """三张表用分隔线变体，空态在表外，数字列数位对齐。

        2026-09-04 实测 vercel.com/geist/table：隔栏异色与分隔线是两个互斥变体
        （Striped 示例没有行线，Bordered 示例没有行填充），悬停填充是第三个独立
        开关。Peach 三张表统一走分隔线，所以不叠加隔栏异色；悬停只给可点的行，
        不可点的行加悬停等于给一个不存在的动作画反馈。
        """
        self.assertPageContains(".insighttablerow:last-child{border-bottom:0}")
        self.assertPageContains(".insighttablerow:is(button):hover{background:var(--overlay-5)}")
        self.assertPageLacks(".insighttablerow:hover{",
                             "不可点的行不给悬停填充")
        self.assertPageLacks(".insighttablerow:nth-child(odd)",
                             "分隔线变体不叠加隔栏异色")
        # 空态渲染在表格外面：留一张只有列头的空表等于让人对着两个列名找不存在的行。
        self.assertPageContains("const table=(head,rows,empty)=>rows?")
        self.assertPageContains("emptyStateHtml('history','还没有观看记录'")
        self.assertPageContains("emptyStateHtml('tags','还没有标签来源'")
        # 数字列 tabular numerals，各行数位对齐才好跨行比较。
        self.assertPageContains(".insighttablerow b{font-weight:500;color:var(--ink-2);font-variant-numeric:tabular-nums}")
        self.assertPageContains(".insightdatatable td{font-variant-numeric:tabular-nums}")

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
        self.assertPageContains("    +(trash?'':countSortsHtml());\n  wireCountRow();")
        self.assertPageLacks("count.textContent=''",
                             "加载态不能清空整行，筛选条要留在原位")
        # 数据到位后摘掉忙碌标记，屏幕阅读器不再把这一行当成还在读取。
        self.assertPageContains(
            "$('#count').removeAttribute('aria-busy');$('#count').removeAttribute('aria-label');")

    def test_the_count_placeholder_and_the_spinning_refresh_key_keep_the_row_height(self):
        """计数骨架宽高定死，等数据时只有换批键在转，行高不变。

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
        # 转动复用既有的转圈关键帧；全局 prefers-reduced-motion 规则会把它关掉。
        self.assertPageContains(
            '.count[aria-busy="true"] #batchAction svg,\n'
            'body.refreshing #batchAction svg,\n'
            '.entitycollectionhead[aria-busy="true"] .entitybatch svg{\n'
            "  animation:peach-spinner-linspin .9s linear infinite}")
        self.assertPageContains("@keyframes peach-spinner-linspin{to{transform:rotate(1turn)}}")

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
            ".followmanage-skeleton .skeletoncard i::after{content:none}")

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
        self.assertPageContains("  if(!tagbar.innerHTML){")
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
            ".metricstrip b,.tastesummary>b{font-size:var(--fs-2xl);line-height:1.15;")
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
            "    const rows=Math.max(1,Math.min(4,Math.ceil((room+rowGap)/(cardHeight+rowGap))));\n"
            "    const want=columns*rows;\n"
            "    while(grid.children.length>want)grid.lastElementChild.remove();\n"
            "    while(grid.children.length<want)grid.appendChild(first.cloneNode(true));")
        # 横排的推荐行不是网格，按整行补会把它裁成一张。
        self.assertPageContains("    if(!first||style.display!=='grid')continue;")
        # 每个铺骨架的表面都要接上，否则那一屏又回到写死的六张。
        for call in ("fitSkeleton($('#grid'));", "fitSkeleton($('#index'));",
                     "fitSkeleton(stats);", "fitSkeleton(tiers);"):
            self.assertPageContains("  " + call)
        self.assertPageContains("    fillSkeletonTier(tagbar,'pill');")
        # 一列 fieldset 的两张骨架照自己的轮廓排，补整行会把它们撑成海报网格。
        self.assertPageContains("{cards:true,fill:false,className:'cleanup-skeleton'})}</div>`,")
        self.assertPageContains("{cards:true,count:3,fill:false,className:'followmanage-skeleton'})}</div>`,")
        self.assertPageContains("""${kind==='cards'&&fill?' data-fill=""':''}""")
        self.assertPageContains(".skeletonpanel[data-fill]>div")

    def test_the_follow_skeleton_reuses_the_poster_card_shape_and_adds_its_own_rows(self):
        """关注页跟首页是同一种海报卡，几何共用一块；它自己多两条横排。

        作者行和筛选行的形状取 `.tier`/`.tagbar` 本身，跟首页顶栏是同一枚，不另画
        一套。真正的差别只有归属行：`.followitem .meta .s` 有 min-height，比首页那条
        高 3.6px，一页十来行叠起来就是一屏的错位。
        """
        self.assertPageContains(
            '''  <div class="tier followauthors" data-skeleton-tier="av"></div>''')
        self.assertPageContains(
            '''  <div class="tagbar followfilters" data-skeleton-tier="pill"></div>''')
        self.assertPageContains(
            "{cards:true,className:'follow-content-skeleton postercard-skeleton'})}</div>`;")
        self.assertPageContains(".follow-content-skeleton .skeletoncard em{height:21px}")
        self.assertPageContains(".follow-content-skeleton .skeletoncard{padding-bottom:8px}")
        self.assertPageContains('<span class="fstate" aria-live="polite"></span></article>`;')
        self.assertPageContains('.followitem .meta .s{min-height:21px}')
        # 真实页面就是这两个类名与这张网格，骨架照抄才可能不位移。
        self.assertPageContains('<div class="tier followauthors" aria-label="按作者筛选">')
        self.assertPageContains('<div class="tagbar followfilters" aria-label="关注筛选">')
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
        self.assertEqual(self.page.count("hideDiscoveryBars();"), 3,
                         "管理页、索引页和中央清理函数各调一次，收起动作本身只写一处")

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
            'section.innerHTML=`<div class="entitycollectionhead"><h3></h3>'
            "${entityCollectionSortsHtml(filters)}</div>")
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
            "<span data-select-label>${esc(chosen[1])}</span>${icon('chevron-down')}")
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

    def test_links_never_use_underlines(self):
        """Peach 的链接反馈只用颜色、背景或描边，任何表面都不画下划线。"""
        self.assertPageContains(".entitylink:hover{color:var(--ink);text-decoration:none}")
        self.assertPageContains(".idcell.entitylink:hover,.mav.entitylink:hover{text-decoration:none}")
        self.assertPageLacks("text-decoration:underline")

    def test_every_identity_cell_can_carry_its_own_portrait(self):
        # 人物格走和顶栏圆头像同一个 entityFaceImg；这一格没有代表作头像可退，
        # 装了实体图才出 `<img>`，否则就是首字母垫底。
        self.assertPageContains("? `<span>${esc(item.name.slice(0,1))}</span>${entityFaceImg(")
        self.assertPageContains("{id:item.id,hasImage:item.has_image})}")
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
        self.assertPageContains("menu.hidden=false;searchActive=-1;")
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
        self.assertEqual(app.count("window.addEventListener('mouseup'"), 1,
                         "松开鼠标结束拖动，全站只需要一条 window 监听")
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
        self.assertPageContains(".vwrap .video-js .vjs-progress-control{z-index:2;position:absolute;left:0;right:0;top:0;width:auto;height:6px")
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
        self.assertPageContains(".vjs-peach-seek-preview img{width:240px;aspect-ratio:16/9")

    def test_center_player_feedback_waits_for_a_user_gesture_and_never_overlaps_loading(self):
        self.assertPageContains("function mountPlayerCenterControls(player)")
        self.assertPageContains("root.className='vjs-peach-center-controls';root.dataset.playerCenterControls=''")
        self.assertPageLacks('data-center-seek=')
        self.assertPageLacks('data-center-toggle')
        self.assertPageContains("let gesture=false,gestureTimer=0")
        self.assertPageContains("playerRoot.addEventListener('pointerdown',arm,true)")
        self.assertPageContains("if(gesture){gesture=false;clearTimeout(gestureTimer);feedback()}")
        self.assertPageContains("root.classList.add('is-feedback')")
        self.assertPageContains(".vjs-peach-center-controls.is-feedback{visibility:visible;animation:peach-player-bezel-fadeout 1s cubic-bezier(.05,0,0,1) both}")
        self.assertPageContains("25%,75%{opacity:1;transform:translate(-50%,-50%) scale(1.33)}")
        self.assertPageContains(".vjs-peach-center-bezel{width:78px;height:78px;border-radius:50%;display:grid;place-items:center;background:rgba(0,0,0,.6)")
        self.assertPageContains('.vjs-peach-center-controls[data-state="pause"] .vjs-peach-center-pause{display:block}')
        self.assertPageContains(".video-js.vjs-waiting .vjs-peach-center-controls,.video-js.vjs-seeking .vjs-peach-center-controls{visibility:hidden!important}")
        self.assertPageContains("vjs-peach-spinner-container")
        self.assertPageContains("animation:peach-spinner-linspin 1.5682352941176s linear infinite")
        self.assertPageContains("animation:peach-spinner-easespin 5332ms cubic-bezier(.4,0,.2,1) infinite both")
        self.assertPageContains("animation:peach-spinner-left-spin 1333ms cubic-bezier(.4,0,.2,1) infinite both")
        self.assertPageContains("animation:peach-spinner-right-spin 1333ms cubic-bezier(.4,0,.2,1) infinite both")
        self.assertPageContains('id="i-player-bezel-play"')
        self.assertPageContains('id="i-player-bezel-pause"')
        self.assertPageContains("mountPlayerCenterControls(detailPlayer)")

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
        self.assertPageContains("top:50%!important;width:52px!important;height:2px!important;margin:0!important")
        self.assertPageContains(".vjs-control-bar>.vjs-volume-panel{box-sizing:border-box;z-index:3;position:relative")
        self.assertPageContains(".vjs-volume-panel .vjs-volume-tooltip{z-index:5!important;left:50%;right:auto;top:auto")

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
        self.assertPageContains("playerControlTooltip(pip,'画中画','I')")
        self.assertPageContains("playerControlTooltip(fullscreen,'全屏','F')")
        self.assertPageContains("playerControlTooltip(toggle,'设置')")
        # 快捷键走按钮自己的点击路径，全屏和画中画的兜底逻辑只写一份。
        self.assertPageContains("function clickPlayerControl(video,selector)")
        self.assertPageContains("if(e.key===' '||e.key==='k'||e.key==='K')")
        self.assertPageContains("if(e.key==='m'||e.key==='M'){e.preventDefault();clickPlayerControl(video,'.vjs-mute-control')")
        self.assertPageContains("if(e.key==='f'||e.key==='F'){e.preventDefault();clickPlayerControl(video,'.vjs-fullscreen-control')")
        self.assertPageContains("if(e.key==='i'||e.key==='I'){e.preventDefault();clickPlayerControl(video,'.vjs-picture-in-picture-control')")
        # 提示外观与音量百分比共用一套毛玻璃，音量提示抬到控制条上方。
        self.assertPageContains(".vjs-peach-tooltip{position:absolute;z-index:5;right:50%;bottom:calc(100% + 12px)")
        self.assertPageContains("backdrop-filter:blur(16px)")
        self.assertPageContains(".vjs-peach-tooltip kbd{display:flex;justify-content:center;align-items:center;min-width:11px")
        self.assertPageContains(".vjs-peach-tooltip kbd[hidden]{display:none}")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar button:hover>.vjs-peach-tooltip")
        self.assertPageContains(".vjs-volume-tooltip{z-index:5!important;left:50%;right:auto;top:auto;bottom:calc(100% + 32px)")
        # 提示要露出控制条，播放键和时间钮不能再靠 overflow 裁。
        self.assertPageLacks("background:rgba(0,0,0,.6);box-shadow:none;overflow:hidden}")

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
        """390 宽的视口上 16:9 的播放器只有 200 出头的高，设置面板要 212、统计面板要 256。

        所以先给播放器一个 320px 的最低高度，窄屏改成上下留黑边；再让两个浮层各自
        按播放器高度收顶，谁都不可能超过播放器本身。窄屏的设置面板还要撤掉
        `right:-100px`——那个偏移是给设置键右边还有影院键和全屏键时留的位。
        """
        self.assertPageContains(
            ".vwrap>.video-js{width:100%;height:auto;min-height:320px;max-height:76vh;"
            "aspect-ratio:16/9;background:#000}")
        self.assertPageContains(".gate{aspect-ratio:16/9;width:100%;min-height:320px")
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
        self.assertPageContains(
            ".vjs-peach-speed-slider .vjs-peach-speed-button{flex:none;width:32px;font-size:var(--fs-2xl)}")
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
        self.assertPageContains('if(playPath)playPath.style.d=`path("${paused?playD:pauseD}")`;')
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
        self.assertPageContains("const meter=createBufferMeter(averageBitrate(options.size??it.size,it.duration))")
        # 分片流才有可用的已完成请求；渐进源查了只会把别的会话的条目算进来。
        self.assertPageContains("const resources=segmented?streamEntries(it.id,detailStreamSession):[]")
        self.assertPageContains("playerSpeedBits(detailPlayer,it.id,detailStreamSession,segmented?null:meter)")
        self.assertPageContains("return meter?Number(meter.bits)||0:streamSpeedBits(id,session)")
        # 缓冲吃满后浏览器停拉，增量归零，读数保留上一次而不是跳回 0。
        self.assertPageContains("if(span>=.5&&gained>0){ratio=gained/span;")
        # 面板和角标都关着时没人采样，重开时的大跨度样本要丢掉。
        self.assertPageContains("if(gap*1000>BUFFER_METER_WINDOW_MS*2)samples.length=0")

    def test_progressive_stats_swap_the_request_counter_for_downloaded_bytes(self):
        """请求数对渐进源恒为 0，换成已下载量；码率未知的在线条目退到秒和推进倍速。"""
        self.assertPageContains("const loaded=segmented?bytes:(meter.bitrate>0?meter.bytes():meter.seconds)")
        self.assertPageContains("const byteScale=segmented||meter.bitrate>0")
        self.assertPageContains("请求`,")
        self.assertPageContains(":['已下载',byteScale?")
        self.assertPageContains("`${loaded.toFixed(0)} 秒`")
        self.assertPageContains("function fmtLoadRate(bits,ratio)")
        self.assertPageContains("`${ratio.toFixed(1)}× 实时`")
        self.assertPageContains(":(!segmented&&meter.ratio>0?`${meter.ratio.toFixed(1)}× 实时`:'—')")

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
        self.assertPageContains(".vwrap .video-js .vjs-tech{object-fit:contain}")
        self.assertPageContains("const syncFullscreenState=()=>{")
        self.assertPageContains("player.el().toggleAttribute('data-peach-fullscreen',active)")
        self.assertPageContains("player.on(['fullscreenchange','enterFullWindow','exitFullWindow'],syncFullscreenState)")
        self.assertPageContains('id="playerNet"')
        self.assertPageContains("function streamSpeedBits(id,session='')")
        self.assertPageContains("function fmtSpeed(bits)")
        self.assertPageContains("const rate=segmented?fmtSpeed(bits):fmtLoadRate(bits,meter.ratio);")
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
        self.assertPageContains("['manage','管理','database']")
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
        """
        sections = self.page.split("const MANAGE_SECTIONS=[", 1)[1].split("];", 1)[0]
        order = [line.split("'")[1] for line in sections.splitlines() if line.strip().startswith("['")]
        self.assertEqual(
            order, ["stats", "taste", "review", "cleanup", "trash", "follow", "quality"],
            "身份注册表保留全部管理页，删掉哪一个就等于让它的标题和直达 URL 一起失效",
        )
        self.assertPageContains(
            "const MANAGE_MENU_SECTIONS=['stats','taste','cleanup','follow'];")
        self.assertPageContains("manageMenuSections().map(([k,label,ic])=>")

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
        self.assertIn("${resourceSyncMarkup()}", cleanup)
        stats = self.page.split("async function openStats(", 1)[1].split("function showHomeSurfaces(", 1)[0]
        self.assertNotIn("linkManagerMarkup()", stats,
                         "统计页只讲库里现在有多少，不该再挂对齐外部现实的面板")
        self.assertNotIn("resourceSyncMarkup()", stats)

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
        self.assertPageContains('<div class="linkhosts"><span>最多的站点</span>')

    def test_taste_page_combines_private_exports_and_peach_behavior(self):
        self.assertRoute('/taste', "openTaste(push)", "section:'taste'")
        self.assertPageContains("/api/taste?window=")
        self.assertPageContains("/api/taste/import")
        self.assertPageContains("/api/taste/refresh")
        self.assertPageContains("/api/taste/source")
        # 口径与免责说明整体清退：这些句子解释的是数字怎么算出来的，
        # 而这个库只有一个用户，他本人就是定这套口径的人。
        self.assertPageLacks("原始 URL、标题与搜索内容不会显示在页面")
        self.assertPageLacks("浏览器记录是当前分析主体")
        self.assertPageLacks("按真实挂载位置汇总")
        self.assertPageLacks("播放、评分与明确反馈保持独立")
        self.assertPageLacks("不自动给标签降权")
        self.assertPageContains("data-taste-window")
        self.assertPageContains("data-taste-remove")
        self.assertPageContains('role="radiogroup" aria-label="口味证据来源"')
        self.assertPageContains('name="taste-evidence" value="browser"')
        self.assertPageContains('name="taste-evidence" value="peach"')
        self.assertPageContains('data-taste-evidence-panel="browser"')
        self.assertPageContains('data-taste-evidence-panel="peach"')
        self.assertPageContains("[data-taste-evidence-panel][hidden]")
        self.assertPageContains("[data-taste-dimension-panel][hidden]")
        self.assertPageContains('data-taste-dimension="${source}:${key}"')
        self.assertPageContains("sourceTabs('browser',[['tags','标签']")
        self.assertPageContains("sourceTabs('peach',[['tags','标签'],['creators','创作者'],['performers','女优']])")
        self.assertPageContains("rank.browser_tags||[]")
        self.assertPageContains("rank.peach_performers||rank.performers||[]")
        self.assertPageContains("visual==='domain'")
        self.assertPageContains("avatarInner(row.name,ref,rep,visual)")
        self.assertPageContains("visual==='creator'&&!ref&&!rep&&sourceDomain")
        # 两处站点头像（域名榜、无实体的创作者）共用一个 siteAvatar；来源提示仍是
        # 「来源：<域名>」，转义在 siteAvatar 里做一次。
        self.assertPageContains("siteAvatar(row.name,sourceDomain,`来源：${sourceDomain}`)")
        self.assertPageContains('title?` title="${esc(title)}"`')
        self.assertPageContains("'simpcity.cr':'https://simpcity.cr/data/assets/logo/favicon.png'")
        self.assertPageContains("'hanime1.me':'https://vdownload.hembed.com/image/icon/tab_logo.png")
        self.assertPageContains("'kemono.cr':'https://kemono.cr/assets/favicon-CPB6l7kH.ico'")
        self.assertPageLacks("negative_tags")
        self.assertPageContains(".tastehero{margin-bottom:16px}")
        self.assertPageContains(".tasteranks{display:grid;grid-template-columns:repeat(3")
        self.assertPageContains(".tasteranks-tags{grid-template-columns:repeat(4")
        self.assertPageContains(".tasterank{width:100%;min-width:0;min-height:58px")
        self.assertPageContains("@media(max-width:640px){.insighttoolbar,.tastehead")
        self.assertPageContains(".insightdetailbody,.tastehero{min-height:0;grid-template-columns:minmax(0,1fr)}")
        self.assertPageContains("data-taste-dimension-panel=\"${source}:${key}\"")
        self.assertPageContains("class=\"tasterank${kind==='tag'?' tasterank-tag':''}")
        self.assertPageContains("grid-template-columns:32px minmax(0,1fr) 18px")
        self.assertPageContains(".tasterank-visual{grid-template-columns:32px 30px minmax(0,1fr) 18px}")
        self.assertPageContains(".tasterank>svg{justify-self:end")
        self.assertPageContains(".tasteranks{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}")
        self.assertPageContains("padding:9px 12px;border:1px solid var(--line-soft);border-radius:var(--control-radius);background:var(--overlay-5)")
        self.assertPageContains(".tasterank-tag{min-height:54px;padding:8px 10px}")
        self.assertPageContains(".tasterank:is(button):hover{border-color:var(--border-15);background:var(--hover)}")
        self.assertPageLacks("box-shadow:inset 3px 0 var(--tungsten)")
        self.assertPageContains(".tastesources .insightpanelbody>div{display:grid;grid-template-columns:repeat(3")
        self.assertPageContains(".tastesources>header{min-height:0;padding-block:14px}")
        self.assertPageContains(".tastesources .insightpanelbody{padding:16px}")
        self.assertPageContains(".tastesource{display:grid;grid-template-columns:34px minmax(0,1fr) 34px;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--line-soft);border-radius:var(--control-radius);background:var(--overlay-5)}")
        self.assertPageContains(".insighttablerow:last-child{border-bottom:0}")
        self.assertPageContains("tasteAnalysisSection(d.analysis)")
        self.assertPageContains('<section class="insightpanel tasteleads">')
        self.assertPageContains("<h3>口味总结</h3>")
        self.assertPageContains('class="tasteconfidence ${esc(confidence.level')
        self.assertPageContains('data-taste-route="${esc(item.route)}"')
        self.assertPageContains("route(button.dataset.tasteRoute);restoreRoute()")
        self.assertPageContains(".tasteinsights{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px")
        self.assertPageContains(".tastelead:hover{border-color:var(--border-15);background:var(--hover)}")
        self.assertPageLacks(".tasteanalysisbody")

    def test_stats_use_analytics_panels_and_real_determinate_progress(self):
        self.assertPageContains('class="metricstrip" role="tablist" aria-label="统计视图"')
        self.assertPageContains('role="tab" data-stats-metric="${key}"')
        self.assertPageContains('role="tabpanel" data-stats-detail="inventory"')
        self.assertPageContains('class="insighttabs" role="tablist" aria-label="统计维度"')
        self.assertPageContains('data-stats-tab="tags" aria-selected="true"')
        self.assertPageContains('data-stats-panel="recent" hidden')
        self.assertPageContains("panel.hidden=panel.dataset.statsDetail!==button.dataset.statsMetric")
        self.assertPageContains('role="progressbar" aria-label="${esc(label)}"')
        self.assertPageContains('aria-valuemin="0" aria-valuemax="${ceiling}" aria-valuenow="${current}"')
        self.assertPageContains(".statmetric{padding:3px 0 12px;border-bottom:1px solid var(--line-soft)}")
        self.assertPageContains(".geist-progress{height:8px;margin-top:7px;overflow:hidden;border-radius:var(--pill-radius);background:var(--line-soft)}")
        self.assertPageContains("${progressHtml(`${k}：${v.toLocaleString()} / ${max.toLocaleString()}`,v,max)}")
        self.assertPageContains(".metricstrip button[aria-selected=\"true\"]:after")
        self.assertPageContains(".insightdetailbody[hidden]")
        self.assertPageContains("[data-stats-panel][hidden]")
        self.assertPageLacks("const card=(t,body,size='third')")
        self.assertPageLacks('<div class="statshead"></div>')
        self.assertPageLacks('class="prog"')

    def test_note_semantics_replace_empty_states_for_persistent_errors(self):
        for name in ("emptyStateHtml", "loadingDotsHtml", "mediaViewButtonsHtml", "noteHtml", "progressHtml",
                     "scrollerHtml", "setActionBusy", "skeletonHtml", "spinnerHtml",
                     "wireBusyActions", "wireScrollers"):
            self.assertPageContains(name)
        self.assertPageContains("from './js/ui-components.js'")
        self.assertPageContains("const NOTE_VARIANTS=new Set(['secondary','warning','error','success'])")
        self.assertPageContains("const symbol=kind==='secondary'?'info':kind==='success'?'check':'alert'")
        self.assertPageContains("const role=kind==='error'?' role=\"alert\"':' role=\"note\"'")
        self.assertPageContains("noteHtml(error.message,{variant:'error',label:'同步失败'})")
        self.assertPageContains("noteHtml(error.message,{variant:'error',label:'扫描失败'})")
        self.assertPageContains("noteHtml(error.message||'分析未取得',{variant:'error',label:'分析未取得'})")
        self.assertPageContains('class="geist-note geist-note-error fcheckreport" role="alert"')
        self.assertPageContains('class="geist-note geist-note-secondary fcheckreport" role="note"')
        # 每一条失败都进 Note，没有第二套「红字一行」的写法：红色文字既没有图标
        # 也没有边框，在暗色底上和普通说明文字只差一个色相，扫读时整条会被跳过。
        self.assertPageContains('class="geist-note geist-note-error fwarn" role="alert"')
        self.assertPageContains(
            "noteHtml(`${broken.length} 个来源上次检查失败，原因见对应那一行。`,{variant:'error'})")
        self.assertPageContains(
            "noteHtml('文件权限过宽，请在运行 Peach 的 POSIX 主机上收紧为 0600。',{variant:'error'})")
        self.assertPageLacks('class="fnote warn"')
        self.assertPageLacks(".fnote.warn{")
        self.assertPageLacks("geist-banner")

    def test_note_and_info_surfaces_reuse_the_photo_detail_info_icon(self):
        self.assertPageContains('<symbol id="i-info" viewBox="0 0 24 24">')
        self.assertPageContains('<div class="runtimegate">${icon(\'info\')}<span>${esc(mirrorText)}</span>')
        self.assertPageContains('<div class="runtimegate">${icon(\'info\')}<span>${esc(followRuntime.ledger_read_only_message')
        self.assertPageContains("${icon('info')}<div><p><b>${exhausted.length} 个来源没有更多内容</b>")
        self.assertPageContains('aria-label="凭据存放位置说明">${icon(\'info\')}</button>')
        self.assertPageContains('aria-label="图片详情" title="图片详情">${icon(\'info\')}</button>')
        self.assertPageContains('.runtimegate{display:grid;grid-template-columns:16px minmax(0,1fr) auto;align-items:center;gap:12px')
        self.assertPageContains('.runtimegate>svg{width:16px;height:16px;flex:none;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}')
        self.assertPageContains('.geist-note>svg{width:16px;height:16px;margin-top:2px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}')
        self.assertPageContains('.runtimegate a{grid-column:2/-1}')

    def test_project_web_ui_skill_keeps_future_changes_on_shared_primitives(self):
        root = Path(__file__).resolve().parents[1]
        skill = root / ".claude" / "skills" / "peach-web-ui" / "SKILL.md"
        self.assertTrue(skill.is_file())
        rules = skill.read_text(encoding="utf-8")
        self.assertIn("优先扩展 `web/js/ui-components.js`", rules)
        self.assertIn("Progress 必须有真实 `value/max`", rules)
        self.assertIn("Switch 必须共享 radio `name`", rules)
        self.assertIn("Fieldset", rules)
        self.assertIn("Scroller", rules)
        self.assertIn("整页或大区块首次等待内容结构", rules)
        self.assertIn("同一次页面进入只呈现一段等待态", rules)
        self.assertIn("Skeleton 只覆盖真正等待的内容区", rules)
        self.assertIn("Skeleton 只保留给辅助技术的状态名", rules)
        self.assertIn("Empty State", rules)
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(".claude/skills/peach-web-ui/SKILL.md", agents)

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
            "border:1px solid var(--border-15);border-radius:var(--control-radius);"
            "background:var(--ground);color:var(--ink);text-align:left;font:inherit;"
            "cursor:pointer}")
        self.assertPageContains(
            ".sidebaradd .sidebaraddfield:hover:not(:disabled){border-color:var(--line)}"
            ".sidebaradd .sidebaraddfield:disabled{color:var(--muted);cursor:default}")
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
            ".geist-button.primary:disabled{border-color:var(--border-15);"
            "background:var(--surface);color:var(--muted)}")

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
                      '/immerse'):
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
            "if(context.type==='home'&&state.state)topsParams.set('state',state.state);")
        # 缓存键跟着 state 变，否则切到已标记会沿用首页那份。
        scope = self.page.split("const scope=facetParams.toString();", 1)[0]
        self.assertIn("facetParams.set('state'", scope)
        # 收窄到空时不能留下空带：实测已标记页上两排都没人，#tiers 仍占 28px。
        self.assertPageContains("$('#tiers').hidden=!(perfRow||studioRow);")
        self.assertPageContains(".tiers[hidden]{display:none}")

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

    def test_review_reuses_the_standard_selection_instead_of_its_own_mode(self):
        """复核页曾自造「多选模式」按钮加框选，只在这一页生效，用户得先发现再记住。

        现在与主网格一致：点一下切换，Shift 选一段。
        """
        self.assertPageLacks("reviewSelectMode")
        self.assertPageLacks("reviewmarquee")
        self.assertPageLacks("review-select-mode")
        self.assertPageContains("function wireReviewAssets(root)")
        self.assertPageContains("if(e.shiftKey&&anchor!==null)")
        self.assertPageContains("[data-pick-all]")
        self.assertPageContains("[data-pick-none]")
        self.assertPageContains('[data-review-asset][aria-pressed="true"]')
        self.assertPageContains("const canApprove=metadata?candidates.length>0:(reviewCategory!=='creator_tags'||String(row.status||'').trim()==='candidate')")
        self.assertPageContains("${canApprove&&!locked?'':' disabled'}")

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

    def test_review_asset_picker_wraps_instead_of_scrolling_sideways(self):
        """一个创作者可能有几十条候选，横向滚动条要一直拉才能看完。"""
        self.assertPageContains(".reviewasset-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr))")
        self.assertPageContains(".reviewasset.picked{opacity:1;outline:2px solid var(--ink)")
        self.assertPageContains('.reviewitem[data-decision="approved"]::before{background:var(--keep)}')

    def test_review_cards_use_equal_height_fieldsets_and_one_shared_scroller(self):
        self.assertPageContains('class="reviewitem" data-geist-fieldset')
        self.assertPageContains('class="geist-fieldset-content">${scrollerHtml(body')
        self.assertPageContains('class="reviewactions geist-fieldset-footer" data-geist-fieldset-footer')
        self.assertPageContains('.review{--review-fieldset-height:440px')
        self.assertPageContains('height:var(--review-fieldset-height);margin:0;padding:0')
        self.assertPageContains('.reviewitem>.geist-fieldset-content{flex:1;min-height:0;padding:20px}')
        self.assertPageContains('min-height:56px;margin:0;padding:12px 12px 12px 20px')
        self.assertPageContains('.reviewactions button{box-sizing:border-box;height:32px')
        self.assertPageContains('.reviewstate:empty{display:none}')
        self.assertPageContains('export function scrollerHtml(content')
        self.assertPageContains("wireScrollers($('#stats'))")
        self.assertPageLacks('max-height:268px;overflow-y:auto')

    def test_empty_states_keep_title_description_and_spacing_together(self):
        self.assertPageContains('export function emptyStateHtml(iconName,title,description')
        self.assertPageContains('data-geist-empty-state role="status"')
        self.assertPageContains('class="es-copy"><h3>${esc(title)}</h3><p>${esc(description)}</p>')
        self.assertPageContains('.emptystate{grid-column:1/-1;display:grid;justify-items:center;align-content:center;gap:8px')
        self.assertPageContains('.emptystate .es-copy{display:grid;justify-items:center;gap:8px}')
        self.assertPageContains('.playlistpage>header{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:16px}')
        self.assertPageContains('.followfilters{position:relative;top:auto;z-index:1;height:auto;min-height:58px;margin:0 0 16px')
        self.assertPageContains("emptyState('trash','回收站是空的','删掉的内容会先到这里；确认不再需要后再清空。')")
        self.assertPageContains("emptyState('search','没有符合条件的作品','调整筛选或搜索条件后再试。')")
        self.assertPageLacks('class="trashempty"')

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
        self.assertPageContains("throw new Error(detail||`请求失败（${response.status}）`)")
        self.assertPageContains("catch(error){actionFailure('批量操作',error)}")
        self.assertPageContains("wireJunkCards($('#grid'));paintSelection();return")
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
        描边是记录在案的有意偏离：上游 secondary 不描边，但它没有「必须放在容器内」这类
        条款（未取得），而 Peach 这两条直接坐在页面顶部、四周没有容器边线，不描边时只有
        选中那一枚有底色。描边一旦被后来的「对齐规范」顺手删掉，这个判据就没人记得了。
        描边之后相邻两枚不能再紧贴，否则两条 1px 边粘成一条 2px 的，所以 gap 从 0 抬到 5px。
        """
        self.assertPageContains(
            ".reviewtabs,.junkfilters{display:flex;align-items:center;gap:5px;min-width:0;"
            "overflow-x:auto;scrollbar-width:none}")
        self.assertCode(
            ".reviewtabs button,.junkfilters a{box-sizing:border-box;height:32px;padding:0 12px;flex:none;"
            "display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border-15);"
            "border-radius:var(--control-radius);background:transparent;color:var(--muted);"
            "text-decoration:none;font:inherit;font-size:var(--fs-sm);font-weight:400;"
            "white-space:nowrap;cursor:pointer}")
        self.assertPageContains(
            '.reviewtabs button[aria-selected="true"],.junkfilters a[aria-current="page"]'
            '{background:var(--hover);color:var(--ink)}')
        # 反相底色不能回来；描边只到 --border-15 那一档，不跟着选中态提亮。
        self.assertPageLacks('.reviewtabs button[aria-pressed="true"]{background:var(--ink-2)')
        self.assertPageLacks('.junkfilters a[aria-current="page"]{border-color:var(--ink-2)')
        # 外观一样不代表语义一样。复核那条切的是 10 个互不相同的候选数据集，每个分类换掉
        # 整个面板的数据模型，也没有独立 URL，所以是真 tablist：方向键漫游焦点，tabindex
        # 只留在选中项上。
        self.assertPageContains('<div class="reviewtabs" role="tablist" aria-label="复核分类">')
        self.assertPageContains('<button role="tab" id="reviewtab-${key}" aria-controls="reviewpanel"')
        self.assertPageContains('aria-selected="${on}" tabindex="${on?' + repr('0') + ':' + repr('-1') + '}"')
        self.assertPageContains('<section class="reviewsection" id="reviewpanel" role="tabpanel" '
                                'aria-labelledby="reviewtab-${reviewCategory}">')
        self.assertPageLacks('<button data-review-tab="${key}" aria-pressed=')
        self.assertPageContains("const step=event.key==='ArrowRight'?1:event.key==='ArrowLeft'?-1:0;")
        self.assertPageContains(
            ":event.key==='Home'?reviewTabs[0]:event.key==='End'?reviewTabs[reviewTabs.length-1]:null;")
        # 垃圾文件那条是同一批候选按 type 收窄，数据模型不变，当前项落在 URL 上，所以是
        # 导航链接而不是 tab。别为了「两条长得一样」把它也套上 tablist：屏幕阅读器会把
        # 筛选念成「标签页 3 of 7」，键盘上还会多出一层方向键漫游，Ctrl 点开新页也没了。
        self.assertPageContains('<nav class="junkfilters" aria-label="垃圾文件分类">')
        self.assertPageLacks('class="junkfilters" role="tablist"')
        self.assertPageContains('data-junk-kind-link="${esc(key)}"${current?' + repr(' aria-current="page"'))
        # 计数是徽标不是标题的一部分，为 0 时整枚去掉，两条一个口径。
        self.assertPageContains(
            'count?` <span class="n mono">${count.toLocaleString()}</span>`:' + repr(''))
        self.assertPageContains(
            'dismissedTotal?` <span class="n mono">${dismissedTotal.toLocaleString()}</span>`:' + repr(''))
        self.assertPageLacks(" <span>${countFor(key).toLocaleString()}</span>")
        self.assertPageContains(".reviewtabs .n,.junkfilters .n{color:var(--muted);"
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
        # 三个按钮等宽，各自居中就让图标横向参差；靠左起排它们才落在一条竖线上。
        # 紧凑密度隐掉标签后只剩图标，那时才回到居中。
        junk_button = self.css.split(".junkactions button{", 1)[1].split("}", 1)[0]
        self.assertIn("justify-content:flex-start", junk_button)
        self.assertNotIn("justify-content:center", junk_button)
        self.assertPageContains(
            'body[data-density="dense"] .junkcard .junkactions button{justify-content:center}')
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
        self.assertPageContains("actionReceipt(`已添加 ${picked.length} 个关注来源`)")
        self.assertPageContains("actionReceipt(saving?'已保存到账本':(labels[to]||'已更新关注状态')")
        self.assertPageContains("actionReceipt(`已把 ${r.removed} 项移入回收站`,{undo:ids.length?async()=>")
        self.assertPageContains("data-junk-batch=\"dispose\"")
        self.assertPageContains(".batchbar:has([data-junk-batch]:not([hidden]))")
        self.assertPageContains("#batchbar[hidden]{display:none}")
        self.assertPageContains("button[hidden]{display:none}")
        self.assertPageContains("querySelectorAll('[data-junk-batch]')")
        self.assertPageContains("toggleSelection(id,event.shiftKey)")
        self.assertPageContains(".resourcecardaction{position:absolute")

    def test_search_suggestions_come_from_real_data_in_bulk(self):
        """写死的 6 个词翻两次就重复。顶部聚合只有几十条，也不够；索引接口一次给近千条。"""
        self.assertPageContains("async function loadSearchPool()")
        self.assertPageContains("['performers','creators','tags'].map(")
        self.assertPageContains("`/api/index?kind=${kind}&limit=400`")
        self.assertPageContains("Promise.all([loadSearchHistory(),loadSearchPool()])")
        self.assertPageContains("[...searchPool()]")

    def test_insight_surfaces_use_one_readable_measure(self):
        """统计和口味共享 Vercel 式阅读列；浏览型首页仍保持全宽。"""
        self.assertPageContains(".stats{padding:0 0 42px}")
        self.assertPageContains(".review{--review-fieldset-height:440px;padding:0 0 42px}")
        self.assertPageLacks("max-width:1440px")
        self.assertPageContains(".insightpage,.tastepage{width:min(1100px,100%);margin:0 auto")
        self.assertPageContains("metricTab('storage','使用空间'")
        self.assertPageContains('class="insightdatatable"')
        self.assertPageContains('<th>位置</th><th>已用</th><th>可用</th><th>使用率</th>')
        self.assertPageContains('class="insightranking"')
        self.assertPageContains("grid-template-columns:repeat(2,minmax(0,1fr))")
        self.assertPageContains("border-top:1px solid var(--line-soft);border-left:1px solid var(--line-soft);list-style:none")
        self.assertPageContains(".insighttable{border-top:0}")
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
        sorts = self.app_js.split('<span class="sorts">', 1)[1].split('</span>', 1)[0]
        self.assertNotIn('id="emptyTrash"', sorts)
        self.assertPageContains(
            ".pagelede-actions{display:flex;align-items:center;justify-content:space-between;gap:16px}")
        self.assertPageContains(
            ".pagelede-actions .batchaction.danger{background:var(--drop);border-color:var(--drop);color:#fff}")
        self.assertPageLacks(".count .sorts .batchaction.danger{")
        # 桌面 32px 是 Geist 的控件高度，手机要回到本项目的 44px 命中区。
        self.assertPageContains(".pagelede-actions .batchaction{height:44px;padding-inline:16px}")

    def test_only_the_data_cleanup_hub_narrows_its_title_column(self):
        """812px 窄列是数据管理 hub 自己的正文宽度，不是整个数据管理区的。

        `.cleanuppage` 把 hub 那一页收进 812px，标题和面包屑跟着收才对得齐。但同一个
        section 底下的垃圾文件、重复文件正文都是全宽网格：跟着收就是宽屏上标题凭空左缩
        一截，标题左边缘和第一张卡的左边缘对不上。判据必须是路径，不是 section。
        """
        self.assertCode("document.body.classList.toggle('cleanup-layout',"
                        "current==='cleanup'&&decodeURIComponent(location.pathname)==='/data-cleanup')")
        self.assertPageLacks("document.body.classList.toggle('cleanup-layout',current==='cleanup')")
        # 窄列本体仍在 hub 上，这两条规则本身不动。
        self.assertPageContains(".cleanuppage{width:min(812px,100%);margin:0 auto}")
        self.assertPageContains(
            ".cleanup-layout .geist-breadcrumb,.cleanup-layout .managetitle,.cleanup-layout .pagelede")

    def test_returning_home_from_any_surface_moves_the_highlight(self):
        """Logo、侧栏和沉浸关闭都必须清掉隐藏筛选，不能让 `/` 继续请求 JAV。"""
        self.assertPageContains("function resetHomeState(){")
        self.assertPageContains("q:'',jav:'',thumb:'1'};")
        self.assertPageContains("function openHome(scroll=false){")
        self.assertPageContains("resetHomeState();route('/');$('#q').value='';disposeStage(false);showHomeSurfaces();")
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

    def test_surface_has_measured_beeg_glow_geometry(self):
        self.assertPageContains("height:49vh")
        self.assertPageContains("linear-gradient(to bottom,rgba(0,0,0,.6),var(--ground))")
        self.assertPageContains("animation:ambient-in .8s ease .5s both")

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
        self.assertCode("border:1px solid var(--border-15);\n  border-radius:var(--pill-radius);background:transparent")
        self.assertPageContains("--overlay-5:rgba(245,250,255,.05)")
        self.assertPageContains("--border-15:rgba(245,250,255,.15)")
        # 窄栏要有右分割线（用户 2026-08-26 明确要求）：无边框时两边背景太接近，
        # 看不出左边那一条到哪里为止。
        self.assertPageContains("border-right:1px solid var(--line-soft)")
        self.assertPageContains("['performers','艺人','user-round']")
        self.assertPageContains("['tags','标签','tags']")

    def test_entity_profile_hides_home_facets_and_renders_context(self):
        self.assertPageContains("body.entity-open #tiers,body.entity-open #tagbar,")
        self.assertPageContains('src="/logo?studio=${encodeURIComponent(d.canonical_name)}&variant=logo"')
        self.assertPageContains('class="entitytags"')
        self.assertPageContains('class="pill" data-entity-tag=')
        self.assertPageContains('class="relatedpeople"')
        self.assertPageContains("data-related-performer")
        profile = self.page[self.page.index("async function openEntity("):]
        self.assertLess(profile.index("<div class=\"entityhero\">"),
                        profile.index('class="relatedpeople"'))
        self.assertLess(profile.index('class="relatedpeople"'),
                        profile.index('class="entitytags"'))
        self.assertPageContains('class="entitytagbar" aria-label="媒体与标签"')
        self.assertPageContains("body.entity-open .index{overflow-x:visible}")
        self.assertNotIn("关联艺人", profile)
        self.assertNotIn("相关标签", profile)
        # 资料页只渲染可核对的身份、计数与链接，没有散文简介块，样式表里也不该
        # 留下对应选择器。
        self.assertPageLacks("entitysummary")

    def test_entity_people_and_tags_match_home_vertical_rhythm(self):
        # 首页末层按钮到标签为 18.5px；人物行保留 4px 滚动留白后只需 6px 外边距。
        self.assertPageContains(".entitymeta{display:grid;gap:22px;margin:0 0 6px;min-width:0}")
        self.assertPageContains(".relatedpeople{display:flex;gap:14px;overflow-x:auto;padding-bottom:4px")
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
        self.assertPageContains("const ENTITY_LABELS={performer:'艺人',studio:'厂牌',creator:'创作者',series:'系列'}")
        self.assertPageContains('class="batchaction entitybatch"')
        self.assertPageContains("filters.sort||'new',filters.dir,'data-entity-sort')")
        self.assertPageContains("p.set('sort',filters.sort||'new')")
        self.assertPageContains("if(filters.sort==='seed')p.set('seed',state.seed)")
        self.assertPageContains("const JAV_RELEASE_SORT=['release','发行时间']")
        self.assertPageContains("javActive()?[JAV_RELEASE_SORT,...SORTS]:SORTS")
        self.assertPageContains("sortOptions().map(([key,label])=>")
        self.assertPageContains("sortOptions().map(([k,l])=>")
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
        self.assertPageContains(
            ".entitytagbar+.entitysection .entitycollectionhead{top:calc(var(--topH) + var(--filterH))}"
        )
        self.assertPageContains(".entitycollectionhead{position:sticky;top:var(--topH);z-index:60")
        self.assertPageContains(
            ".tagbar.is-stuck,.count.is-stuck,.entitytagbar.is-stuck,.entitycollectionhead.is-stuck"
        )
        self.assertPageContains("['#tagbar','#count','.entitytagbar','.entitycollectionhead']")
        self.assertPageContains("scheduleStickySurfaces();")
        # 照片瀑布流没有视频排序语义，切换后直接渲染照片，不复用作品头。
        self.assertPageContains("if(media==='photos'){renderPhotoWall(kind,name,filters,entityPhotos);return}")

    def test_entity_profile_uses_display_aliases_not_search_identity_aliases(self):
        self.assertPageContains("(d.display_aliases||[]).length")
        self.assertPageLacks("(d.aliases||[]).length?'别名")

    def test_the_agency_reads_as_identity_not_as_a_link(self):
        """事务所此前寄居在官方链接的标签里，那个控件于是同时替两家公司说话。

        它没有网址，做不成链接；它是这个人签在谁名下，和别名、作品数是同一类事实。
        """
        self.assertCode("const agencyName=(d.metadata||{}).agency?.name||'';")
        self.assertPageContains("agencyName?` · 事务所 ${esc(agencyName)}`:''")
        # 链接标签写的是域名归谁，不是事务所名。
        self.assertPageContains("标签写的是这个域名归谁")

    def test_entity_name_picker_offers_only_this_entity_existing_names(self):
        # 候选取的是身份契约 `aliases`（完整），不是收窄过的展示别名：罗马字也是
        # 这个人真的用过的写法，用户想拿它当统称就该能选。
        self.assertCode("const nameChoices=[d.canonical_name,...(d.aliases||[])]")
        self.assertCode(
            ".filter((option,index,all)=>option&&all.indexOf(option)===index);")
        # 只有一种写法时没有可选的东西，控件不出。
        self.assertCode("const namePick=nameChoices.length>1?")
        self.assertPageContains('data-namepick-toggle aria-haspopup="menu"')
        self.assertPageContains('role="menuitemradio"')
        self.assertPageContains('aria-checked="${option===d.canonical_name}"')

    def test_entity_name_picker_reuses_the_shared_anchored_menu(self):
        self.assertPageContains("const anchored=wireAnchoredMenu(mount,toggle,menu);")
        self.assertPageContains('<div class="popmenu npmenu"')

    def test_anchored_menu_fits_the_room_it_has_instead_of_covering_its_toggle(self):
        # 资料页的统称菜单挂在标题上，上方只有一条顶栏的距离、下方也未必够高。
        # 两侧都放不下时压到宽的那一侧、内部滚，不横跨触发钮。
        self.assertCode("const downward=under>=menu.scrollHeight||under>=over;")
        self.assertCode(
            "const height=Math.min(menu.scrollHeight,Math.max(downward?under:over,0));")
        self.assertCode("menu.style.maxHeight=height+'px';")
        self.assertCode(
            "menu.style.top=(downward?anchor.bottom+8:anchor.top-8-height)+'px'")
        # 可用上沿是固定顶栏的下缘，不是视口顶端。
        self.assertCode(
            "const viewportTop=()=>8+(parseFloat(getComputedStyle(document.documentElement)")
        self.assertCode(".getPropertyValue('--topH'))||0);")
        self.assertPageContains(
            "menu.hidden=true;menu.style.left='';menu.style.top='';menu.style.maxHeight='';")

    def test_anchored_menu_closes_on_page_scroll_but_not_on_its_own(self):
        # 菜单装不下时本来就要在内部滚；捕获阶段的 scroll 连它自己的也收得到。
        self.assertCode(
            "if(!(event.target instanceof Node&&menu.contains(event.target)))setOpen(false)")

    def test_entity_name_picker_keeps_a_touch_target_on_phones(self):
        self.assertPageContains(".npbtn{width:44px;height:44px}")
        self.assertPageContains(".npmenu button,.gselectmenu button{min-height:44px}")

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
            "dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});")

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
        self.assertPageContains("const sec=(t,b,x,cat)=>b?")
        self.assertPageContains("const chips=(items,key,multi,limit)=>items.length?")
        self.assertPageContains("chips(facetData.orientations,'orient')")
        self.assertPageLacks("chips([{k:'竖屏'},{k:'横屏'}],'orient')")

    def test_untagged_detail_uses_home_tags_only_in_the_top_discovery_bar(self):
        # 作品没有内容标签时，顶部发现栏回退首页口径；详情抽屉仍使用作品 scoped facets。
        self.assertPageContains("if(context.type==='item'&&!topTags.length)")
        self.assertPageContains("const recommendationFacets=await api('/api/facets'")
        self.assertCode("if(requestSeq!==barsRequestSeq)return;\n    topTags=recommendationFacets.tags||[]")
        self.assertPageContains("+seededSample(topTags,26,`tags:${state.seed||''}`).map(t=>")
        self.assertPageContains("+sec('内容标签',chips(facetData.tags,'tag',false,30)")

    def test_the_discovery_tag_row_changes_with_the_batch_seed(self):
        """标签条跟着「换一批」的种子换成员，同一批内不动。

        `/api/facets` 给 44 个内容标签，条上只放得下 26 个，取前 26 的话后面 18 个
        永远轮不到；顶部三层本来就跟着同一个 state.seed 换人，标签条留在原地等于
        「换一批」只换了半个顶部。抽样不动顺序——条上照旧按数量从多到少读下来，
        换的是成员，不是位置。
        """
        self.assertPageContains("+seededSample(topTags,26,`tags:${state.seed||''}`).map(t=>")
        self.assertPageLacks("topTags.slice(0,26)",
                             "取前 26 会让第 27 名之后的标签永远露不出来")
        # 同一个种子给同一套成员，所以这一批内翻页和刷新都不会让标签跳动。
        self.assertPageContains("const seededSample=(rows,count,seed,key=row=>row.k)=>{")
        self.assertPageContains("  if(rows.length<=count)return rows;")
        self.assertPageContains("  return rows.filter(row=>picked.has(key(row)));")
        # 种子随机只有一份算法，关注页的随机发现共用它。
        self.assertPageContains("const seededRank=(seed,value)=>{")
        self.assertPageContains("const followDiscoveryRank=value=>seededRank(followDiscoverySeed,value);")

    def test_the_refresh_key_keeps_spinning_until_the_bars_land_too(self):
        """转圈归「换一批」这一层，不挂在计数行上。

        网格和顶部三层一起换，两边耗时不一样。挂在计数行的 aria-busy 上时，网格
        先到就被 renderCount 摘掉，标签条还在等的那段时间按钮已经停了。顶部三层
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
        self.assertPageContains("adsBatch.items.slice(offset,offset+appSettings.batchSize)")
        self.assertPageContains("p.set('limit',appSettings.batchSize)")
        self.assertPageContains("offset+=appSettings.batchSize")
        self.assertPageContains("if(!reset)p.set('count','0')")
        self.assertPageContains("!listLoading&&!$('#loadSentinel').hidden")
        self.assertPageContains("indexRequestSeq")
        self.assertPageContains("barsRequestSeq")
        self.assertPageContains("async function getBarsData(context=barsContext)")
        self.assertPageContains("Date.now()-barsDataAt<30000")
        self.assertPageLacks("p.set('limit','120')")
        # 观察器收进了共用的 wireLoadMore（见 test_infinite_scroll_is_wired_through_one_helper）；
        # 这里要保证的是实体合集确实接上了它，而不是自己又写一套。
        self.assertPageContains("wireLoadMore(more,requestMore);")
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
        self.assertPageContains(".mixface.on{opacity:1;z-index:2;transform:none}")
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
        # 遮住静止封面的底色跟着这张卡自己的底走：图片墙是浅底，视频卡是黑底。
        self.assertPageContains(".followitem.imagecard .mixfaces{background:var(--sunk)}")

    def test_mix_and_persistent_playlists_share_the_routed_side_queue(self):
        self.assertPageContains('class="card mixcard" data-mix-seed=')
        self.assertPageContains("cards.splice(MIX_SLOT,0,mixCardHtml(seed))")
        self.assertPageContains(".mixstack::before,.mixstack::after")
        # Mix 是同一网格里的同级卡片，JAV 大图不能让它单独掉回 16:9；有封面时
        # 也应和普通作品卡共用同一张官方封套，而不是永远显示视频接触表。
        self.assertPageContains("const useCover=jav&&layout!=='preview'&&it.has_cover;")
        self.assertPageContains("const ar=jav&&layout==='big'?COVER_FRONT_RATIO:16/9;")
        self.assertPageContains('<div class="mixstack"><div class="pic" style="--card-ratio:${ar}">')
        self.assertPageContains("? coverImage(it,layout)")
        self.assertPageContains("const thumb=mixFacePoster(it,layout);")
        self.assertPageContains('<span class="mixbadge">${icon(\'play\')}Mix</span>')
        self.assertPageContains("async function openMix(seedId,itemId=seedId,push=true,anchor=null)")
        self.assertPageContains("route(`/mix/${seedId}/${itemId}`)")
        self.assertPageContains('class="mixqueue"')
        self.assertPageContains('class="mixitem ${x.id===itemId?\'current\':\'\'}"')
        self.assertPageContains("data-queue-item")
        self.assertPageContains("if(!queueContext)api('/api/related?id='")
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
        self.assertPageContains("data-add-playlist")
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
        # 这一行没有滚动条（scrollbar-width:none），不登记拖动就只剩看得见够不着的半个按钮。
        self.assertPageContains("['#tagbar','#srow','#nrow','#count'].forEach(s=>wireDrag($(s)))")
        # 同一个元素宽屏不溢出、窄屏才溢出，不判溢出就会在宽屏抢走滚轮和拖动。
        self.assertPageContains("const scrollable=()=>el.scrollWidth-el.clientWidth>1;")
        self.assertPageContains("if(e.button!==0||!scrollable())return;")
        self.assertPageContains("if(scrollable()&&Math.abs(e.deltaY)>Math.abs(e.deltaX))")

    def test_entity_collection_posters_and_titles_open_item_details(self):
        self.assertPageContains('class="cardopenhit" data-open')
        self.assertPageContains('<button class="t cardtitle" data-open>')
        self.assertPageContains("const openCard=(id,anchor=el)=>onClick?onClick(id,anchor):(it?.part_group")
        self.assertPageContains("if(e.target.closest('[data-open]')){e.stopPropagation();openCard(+el.dataset.id,el)")
        self.assertPageContains(".cardopenhit{position:absolute;inset:0;z-index:3")
        self.assertPageContains("el.querySelectorAll('[data-open]').forEach(opener=>")
        self.assertPageContains("opener.dataset.openWired='1'")
        self.assertPageContains(".hovertools button{pointer-events:none")
        self.assertPageContains(".card.longhover .seektools button,.card:hover .later-tools button{pointer-events:auto}")
        self.assertPageContains("section.querySelector('h3').textContent=`视频 ·")
        self.assertPageLacks("的馆藏作品 ·")

    def test_hover_seek_controls_are_bare_icons_over_the_frame(self):
        """悬停放大时居中的快退／快进／全屏是裸图标，不是压在画面上的磨砂圆饼。

        三个 58px 的实心圆落在封面正中，遮住的画面比按钮本身还多，而这一层出现的时机
        恰恰是用户在看画面。命中区域仍留 58px（触摸目标不缩），只是不再画出底和边；
        秒数交给 `title`／`aria-label`，图标上不再压一个数字。
        证据与「beeg 那一侧未取得」的结论见
        `docs/reference-snapshots/hover-seek-controls-user-screenshot.md`。
        """
        self.assertPageContains(
            ".hovertools.seektools button{border:0;background:none;backdrop-filter:none;")
        self.assertPageContains(".hovertools.seektools button svg{width:34px;height:34px;stroke-width:1.5}")
        self.assertPageContains(".hovertools.seektools button:hover{background:none}")
        # 命中区域仍由共用规则给出 58px 圆，裸图标只是不画它。
        self.assertPageContains(".hovertools button{pointer-events:none;width:58px;height:58px;border-radius:50%")
        # 数字角标随之退役：DOM 里不再有它，样式也不该留着。
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
        self.assertPageContains('<div class="stitle">${javTitleHtml(it)}')
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
        self.assertPageContains("releaseHoverPreviews($('#srow'))")

    def test_remote_hover_scan_is_an_overlay_so_every_jav_layout_has_it(self):
        """远端源的扫视图叠一层，不改任何已有 `<img>` 的 src。

        JAV 大图和小图版式里画面就是封面本身（`.poster.cover`），改它的 src 等于把封面
        当场换掉；按类名把封面排掉又等于这两种版式整个没有悬停预览——连 `.previewing`
        都不进，快退快进那三颗跟着永远不出现。叠一层对三种版式是同一条路。

        几何和本地视频的 `.hv` 逐字一致：不透明黑底加 contain。大图版式的容器是 0.7
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

    def test_detail_close_returns_to_the_collection_that_opened_it(self):
        self.assertPageContains("detailReturnPath='/'")
        self.assertPageContains("if(push)detailReturnPath=location.pathname+location.search")
        self.assertPageContains("const returnPath=detailReturnPath||'/',restoreSurface=detailReturnNeedsRestore")
        self.assertPageContains("if(restoreSurface)await restoreRoute()")

    def test_direct_detail_restores_the_home_list_and_card_details_open_inline(self):
        self.assertPageContains("const needsReturnRestore=detailReturnNeedsRestore||(!push&&!returnSurfaceReady)")
        self.assertPageContains("function placeItemDetail(anchor,above=false)")
        self.assertPageContains("getComputedStyle(container).display==='grid'")
        self.assertPageContains("container.insertBefore(stage,above?edge:edge.nextSibling)")
        self.assertPageContains("anchor.getBoundingClientRect().top+anchor.getBoundingClientRect().height/2>window.innerHeight/2")
        self.assertPageContains(".grid>.stage{grid-column:1/-1;width:100%;min-width:0}")

    def test_inline_detail_stays_below_the_visible_sticky_navigation(self):
        self.assertPageLacks("body.detail-open .tagbar{position:relative;top:auto;z-index:1}")
        self.assertPageContains("function itemDetailStickyOffset()")
        self.assertPageContains("['.top','#tagbar','#count','.entitytagbar','.entitycollectionhead']")
        self.assertPageContains("el.compareDocumentPosition(stage)&Node.DOCUMENT_POSITION_FOLLOWING")
        self.assertPageContains("el.offsetParent===null||css.position!=='sticky'")
        self.assertPageContains("stage.style.scrollMarginTop=`${itemDetailStickyOffset()+8}px`")
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
                        body.index("$('#grid').innerHTML=pageSkeletonHtml"),
                        "哨兵要在骨架铺上之前收掉，别让 dots 和骨架同时存在一帧")
        # 目录这条链上收哨兵只有这一处：分支里再补一次就是又一个会漏掉的地方。
        ads = self.app_js.split("if(state.state==='ads'){", 1)[1].split("adsBatch=null;", 1)[0]
        self.assertNotIn("$('#loadSentinel').hidden=true", ads)
        boot = self.app_js.split("if(path==='/junk-files'){", 1)[1].split("return;", 1)[0]
        self.assertNotIn("$('#loadSentinel').hidden=true", boot)

    def test_page_loading_uses_one_structural_skeleton_phase(self):
        self.assertPageContains("function renderCatalogLoading(label='正在读取作品')")
        self.assertPageContains("$('#grid').innerHTML=pageSkeletonHtml(label,\n"
            "    {cards:true,className:'catalog-skeleton postercard-skeleton'});")
        self.assertPageContains("count.setAttribute('aria-label',label);")
        self.assertPageContains(".grid>.skeletonpanel{grid-column:1/-1;width:100%;min-width:0}")
        self.assertPageContains("function renderInitialSurfaceLoading()")
        self.assertPageContains("const followSkeletonHtml=(label='正在读取关注内容')")
        self.assertPageContains('<div class="followhead"><h2 class="pagetitle">关注</h2></div>')
        self.assertPageContains("placeholder:followSkeletonHtml('正在读取关注内容')")
        self.assertPageContains("pageSkeletonHtml('正在读取统计',{variant:'dashboard'})")
        self.assertPageContains(".skeletondashhero{min-height:330px;grid-template-columns:minmax(260px,36%) minmax(0,1fr)}")
        self.assertPageContains("if(!refine)showIndexLoading(people?'正在读取作者':'正在读取标签')")
        self.assertPageContains("$('#loadSentinel').innerHTML=loadingDotsHtml('继续载入中…')")
        self.assertPageContains("pageSkeletonHtml('正在读取推荐',{cards:true,className:'related-skeleton'})")
        self.assertPageLacks("count.innerHTML=`${spinnerHtml(label)}<span>载入中…</span>`")
        self.assertPageLacks("function showItemDetailLoading(anchor,above)")
        self.assertPageLacks("detailpending")
        self.assertPageLacks("showItemDetailLoading(origin,above)")

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
                     "'/review'", "'/quality-goals'", "'/playlists'", "'/follow-manage'"):
            self.assertPageContains(f"  {path}:()=>", "占位没有收进唯一那份定义")
            self.assertPageContains(f"managementPlaceholder({path})", "路由没有取那份定义")
        # /resource-sync 只是数据管理页的锚点，启动占位得是数据管理那张。
        self.assertPageContains("'/resource-sync':()=>MANAGEMENT_PLACEHOLDERS['/data-cleanup']()")
        self.assertPageContains("stats.innerHTML=path.startsWith('/follow')&&path!=='/follow-manage'")
        self.assertCode('''data-skeleton="${esc(kind)}${className?`/${esc(className)}`:''}"''')
        self.assertPageContains(
            "const painted=$('#stats').querySelector('[data-skeleton]')?.dataset.skeleton||''")
        self.assertPageContains(
            "if(!next||next!==painted){$('#stats').innerHTML=placeholder;fitSkeleton($('#stats'))}")
        # 数据管理不在骨架之后再盖一层 Loading Dots：那就是第二段动画。
        self.assertPageLacks("loadingDotsHtml('正在读取数据管理状态…')")
        self.assertPageLacks(".cleanuploading")
        # 数据管理是一列 fieldset，骨架不能是三列海报网格。
        self.assertPageContains(".cleanup-skeleton>div{grid-template-columns:minmax(0,1fr);gap:16px}")
        self.assertPageContains(".cleanup-skeleton .skeletoncard em{width:100%;height:var(--fieldset-bar-h)")

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
            "export function skeletonHtml(label='正在读取内容',{className='',variant='panel',count=6,fill=true}={})")
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
        self.assertPageContains("setActionBusy(addButton)")
        self.assertPageContains("setActionBusy(btn)")

    def test_follow_separator_uses_the_same_border_token_as_tags(self):
        self.assertPageContains(".pill{flex:none;height:var(--filterItemH);padding:0 20px;border:1px solid var(--border-15)")
        self.assertPageContains(".followfilters .sep{flex:none;width:1px;height:24px;background:var(--border-15)")

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
            ".brandpill .mk img{position:absolute;inset:0;width:100%;height:100%;")
        self.assertPageContains(
            "object-fit:cover;display:block;filter:saturate(.72) brightness(.84)",
            "小圆片的去饱和保留，但图必须铺满")
        self.assertPageContains(
            ".idface img{position:absolute;inset:0;width:100%;height:100%;"
            "object-fit:cover;display:block}")
        self.assertPageContains(
            ".entityportrait img{width:100%;height:100%;object-fit:cover;display:block")
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

        `studio=115` 那处例外：它取的是来源角标那份固定资产，不按厂牌名找图。
        """
        for match in re.finditer(r'src="/logo\?studio=([^"]*)"', self.page):
            if match.group(1).startswith("115&"):
                continue
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
        self.assertPageContains("const SEARCH_HINTS=['Prestige','FC2','Sakura Misaki','丝袜','足交','ABW']")
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
        self.assertPageContains("it.code?{kind:'',name:it.code}")
        self.assertPageContains("it.studio?{kind:'studio',name:it.studio}")
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

    def test_portrait_strip_sits_on_a_row_boundary_without_borrowing_extra_items(self):
        """竖屏条整行占位，必须插在行边界上，而不是另拉一批横屏视频补满余位。

        补位的那批 id 不在分页序列里，翻下一页必然重复；而且它们被当作 `scard`
        渲染会按竖屏比例压扁横屏画面。行边界插入既不额外请求也不会重复。
        """
        self.assertPageContains('.shorts-inline{grid-column:1/-1;margin:28px 0 8px;padding-top:0}')
        # 竖屏比例只给 `scard`（和显式筛了竖屏时）。按 `it.ctx_orient` 逐条算的话，
        # 任何混着横竖屏的网格都会高低不齐——资料页、相关推荐、搜索结果全中招。
        self.assertPageContains("const portrait=cls==='scard'||state.orient==='竖屏';")
        self.assertPageContains('grid-template-columns:repeat(auto-fill,minmax(var(--tile),1fr))')
        self.assertPageContains('const anchor=cards[Math.min(cards.length,columns*SHORTS_ROW_OFFSET)]')
        self.assertPageContains("anchor.insertAdjacentHTML('beforebegin',inline)")
        self.assertPageLacks("fillerParams")
        self.assertPageLacks('const remainder=')
        self.assertPageContains('.srow .scard{flex:none;width:214px;cursor:pointer}')

    def test_only_the_default_home_list_drops_portrait_videos(self):
        """搜索必须能命中竖屏作品；排除竖屏只是首页默认列表的取景，不是全局过滤。"""
        self.assertPageContains("if(isCatalogPath(decodeURIComponent(location.pathname))&&!state.q&&!state.orient)p.set('exclude_vertical','1')")
        self.assertPageLacks("if(!state.orient)p.set('exclude_vertical','1')")

    def test_grid_count_and_range_select_ignore_the_portrait_strip(self):
        """竖屏条嵌在网格里，但它既不是「显示 N」的一员，也不该被 Shift 范围选中。"""
        self.assertPageContains("$('#grid').querySelectorAll(':scope > .card[data-id]').length")
        self.assertPageContains("document.querySelectorAll('#grid > .card[data-id]')")

    def test_recycle_bin_has_its_own_route_and_reports_undeletable_files(self):
        self.assertRoute('/trash', "section:'trash'", "openTrash(push)")
        self.assertPageContains("function openTrash(push){")
        self.assertPageContains("state:'trash',q:''};$('#q').value='';")
        self.assertPageContains("/api/trash/empty")
        self.assertPageContains("r.blocked&&r.blocked.length")

    def test_card_hover_hides_source_and_duration_and_missing_size_is_explicit(self):
        self.assertPageContains('.card:hover .badge,.card:hover .dur{opacity:0}')
        self.assertPageContains('.meta .t{font-size:var(--fs-md);line-height:1.35;min-height:2.7em;')
        self.assertPageContains("const sizeText=Number(shownSize)>0?fmtSize(Number(shownSize)):'大小未知';")
        self.assertPageContains('<span class="size">${sizeText}</span>')

    def test_tags_page_has_cloud_and_alphabet_modes(self):
        self.assertPageContains('data-tag-view="cloud"')
        self.assertPageContains('data-tag-view="alphabet"')
        self.assertPageContains('class="alphabet"')
        self.assertPageContains('data-tag-category=')
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
        self.assertPageContains("'足交':'脚交'")
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
        self.assertPageContains('<input type="checkbox" id="censorSetting">')
        self.assertPageContains('<span><b>审查遮挡</b></span><input type="checkbox" id="censorSetting">')
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
        self.assertPageContains("data-fwarn-dismiss")
        self.assertPageContains("sessionStorage.setItem('peach-fwarn-dismissed','1')")
        self.assertPageContains(".fwarn .wclose,.fcheckreport .wclose{width:24px;height:24px;padding:0;border:0;")
        # 报告条的红发丝边和微红底由共用 Note 提供，本页只补关闭键那一列。
        self.assertPageContains(
            ".fcheckreport,.fwarn{grid-template-columns:16px minmax(0,1fr) 24px;margin:10px 0 14px}")
        self.assertPageContains(
            ".geist-note-error{border-color:color-mix(in srgb,var(--drop) 30%,transparent);"
            "background:color-mix(in srgb,var(--drop) 7%,transparent)}")
        self.assertPageLacks("border-left:2px solid var(--drop)")
        # 来源行状态徽章（ok 绿 tint / 失败红 tint / 未检查灰）。
        self.assertPageContains('<span class="sbadge ${badge}" title="${esc(stateTitle)}"><i aria-hidden="true"></i>')
        self.assertPageContains(".sbadge i{width:6px;height:6px;border-radius:50%;background:var(--muted);flex:none}")
        self.assertPageContains(".sbadge.ok i{background:var(--success)}")
        self.assertPageContains(".sbadge.error i{background:var(--drop)}")
        # 清空回收站：danger 语义色。
        self.assertPageContains('class="batchaction danger" id="emptyTrash"')
        self.assertPageContains(".pagelede-actions .batchaction.danger{background:var(--drop);border-color:var(--drop);color:#fff}")
        # Geist 菜单：触发器和每个选项都有入口图标，菜单内部滚动且不加猜测动画。
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
        self.assertPageContains(".settinggroup{margin:16px 0 0;border:1px solid var(--line-soft);border-radius:var(--floating-radius);")
        # 组卡面与全站卡片同源（--surface 实底），不用白色透明叠加。
        self.assertPageContains("background:var(--surface);padding:0 16px 12px}")
        # 布尔开关是 Geist 中号 Toggle（36×20 轨道 + 17px 圆点），不是原生复选框；
        # Geist 的 Switch 是分段选择器，别用错控件。
        self.assertPageContains("#censorSetting{appearance:none;-webkit-appearance:none;width:36px;height:20px;flex:none;")
        self.assertPageContains("#censorSetting:checked{background:var(--tungsten)}")
        # 没有直接证据的 command-menu 入场动画与无有效高度约束的复核卡
        # Scroller 不应继续作为「Vercel 对齐」进入产品。
        self.assertPageLacks("animation:panel-in")
        self.assertPageLacks("@keyframes panel-in")
        self.assertPageLacks("wireReviewScrollers")
        self.assertPageLacks("reviewscrollbtns")
        self.assertPageContains(".settinggroup>h3{margin:0;padding:14px 0 10px;font-size:var(--fs-lg);font-weight:600;color:var(--ink)}")
        self.assertPageContains(".settinggroup .settingrow{margin:0 -16px;padding-left:16px;padding-right:16px}")
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

    def test_taste_dashboard_is_persisted_and_refreshed_without_blocking(self):
        """口味仪表跨页面刷新复用旧结果，过期更新也不阻塞打开页面。

        口味数据来自浏览器历史聚合，24 小时内无需重读。过期时仍先显示
        持久缓存，再后台更新；请求带序号，慢响应不能覆盖别的窗口或页面。
        """
        self.assertPageContains("const TASTE_CACHE_KEY='peach-taste-dashboard-v3',TASTE_CACHE_FRESH_MS=24*60*60*1000;")
        self.assertPageContains("let tasteWindow='all',tasteEvidence='browser',tasteDimension={browser:'tags',peach:'tags'};")
        self.assertPageContains("let tasteCache=readTasteCache(),tasteRequest=0;")
        self.assertPageContains("localStorage.getItem(TASTE_CACHE_KEY)")
        self.assertPageContains("localStorage.setItem(TASTE_CACHE_KEY,JSON.stringify(Object.fromEntries(tasteCache)))")
        self.assertPageContains("const cachedEntry=tasteCache.get(tasteWindow),cached=cachedEntry?.dashboard;")
        self.assertPageContains("const cacheFresh=cached&&Date.now()-cachedEntry.at<TASTE_CACHE_FRESH_MS;")
        self.assertPageContains("if(cached)renderTaste(cached);")
        self.assertPageContains("if(!cacheFresh)")
        self.assertPageContains("void surfaceApi(surface,'/api/taste?window='+requestedWindow).then(data=>")
        self.assertPageContains("tasteCacheSet(requestedWindow,data);")
        self.assertPageContains("if(request===tasteRequest&&tasteWindow===requestedWindow&&surfaceCurrent(surface))renderTaste(data)")
        self.assertPageContains("if(!cached&&request===tasteRequest&&surfaceCurrent(surface))")
        # 三个写路径都更新缓存，别让缓存变陈旧。
        self.assertPageContains("tasteCacheSet(tasteWindow,result.dashboard);renderTaste(result.dashboard)")
        self.assertPageContains("tasteWindow='all';tasteCacheSet('all',payload.dashboard);renderTaste(payload.dashboard)")

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
        self.assertPageContains("row.ondragstart=e=>")
        self.assertPageContains("row.ondragover=e=>")
        self.assertPageContains("row.ondrop=e=>")
        self.assertPageContains("function wireNavigationDrag(root){")
        self.assertPageContains("clearTimeout(edgeT);edgeT=null;drawerSuppressUntil=Date.now()+900")
        self.assertPageContains("wireNavigationDrag($('#edge'))")
        self.assertPageContains("wireNavigationDrag($('#drawer').querySelector('.dnav'))")
        self.assertPageContains('data-nav="${k}" draggable="true"')
        self.assertPageContains("data-sidebar-hide")
        self.assertPageContains("data-sidebar-add-option")
        self.assertPageLacks("data-sidebar-add-select")
        self.assertPageContains("const OPTIONAL_SIDEBAR_KEYS=['stats','review','data-cleanup','trash','follow-manage','quality']")
        self.assertPageContains("if(DIRECT_MANAGE_NAV[k]){openManage(DIRECT_MANAGE_NAV[k]);return}")
        self.assertPageContains(".settingscard{display:flex;flex-direction:column;width:min(520px,100%);max-height:min(720px,90vh);max-height:min(720px,90dvh);overflow:hidden")
        self.assertPageContains(".settingsscroll{flex:1;min-height:0;overflow-y:auto")
        self.assertPageContains("document.dispatchEvent(new CustomEvent('peachambientchange'")
        self.assertPageContains(".settingrow .gselect{min-width:148px}")

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
            ".settinggroup .settingrow+.sidebarsetting{margin:0 -16px;padding:14px 16px 0;"
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

    def test_better_version_targets_have_a_management_page(self):
        self.assertPageContains("['quality','高清版','sparkles']")
        self.assertRoute('/quality-goals', "section:'quality'", "openQualityGoals(push)")
        self.assertPageContains("async function openQualityGoals(push=true)")
        # 这一页已经迁到 Preact island（ADR-0022）：取数与渲染在 frontend/ 里，遗留层
        # 只剩外壳。所以这里断言的是挂载契约，而不是端点字符串——端点由
        # frontend/test/quality-goals.test.tsx 与 web_contract 的路由测试各自守着。
        self.assertPageContains("const ui=await import('/dist/peach-ui.js')")
        self.assertPageContains(
            "await ui.mountIsland('quality-goals',$('#stats'),props,"
            "{isCurrent:()=>surfaceCurrent(surface)})")
        self.assertPageContains("const props={openItem,javTitleHtml,javDisplayName,srcBadge}")
        self.assertPageLacks("data-quality-open")

    def test_review_page_is_a_separate_management_layer(self):
        self.assertPageContains("route('/review')")
        self.assertPageContains("const REVIEW_LABELS={metadata_fields:'元数据字段',creator_tags:'创作者标签'")
        self.assertPageContains("candidate_key:candidateKey")
        self.assertPageContains("class=\"metadatacandidate\"")
        self.assertPageContains("candidate.official?' · 官方优先':''")
        self.assertPageContains("candidate.catalog_evidence||{}")
        self.assertPageContains('class="metadataevidence"')
        self.assertPageContains("candidate.content_id||candidate.provider_id")
        self.assertPageContains(".metadataevidence>div{display:grid;grid-template-columns:68px minmax(0,1fr)")
        self.assertPageContains("/api/review/decision")
        self.assertRoute('/review', "section:'review'", "openReview(push)")
        self.assertPageContains('class="revieworigin"')
        self.assertPageContains('data-review-open-item="${row.asset_id}"')
        self.assertPageContains("openItem(+button.dataset.reviewOpenItem)")

    def test_detail_title_keeps_source_and_file_actions_inline(self):
        """来源徽标浮左只缩进标题的第一行，定位文件与刷新跟在标题文字末尾。

        三者并排参与弹性布局时，徽标那一列会把标题的每一行都缩进；浮动只缩短第一行的
        行盒，折行后的第二行顶到内容左边缘。两个动作是行内块，上下各 3px 外边距把它们
        所在那一行的行盒撑到 32px，26px 的按钮和上下两行文字各留 3px。
        """
        self.assertPageContains(
            '<div class="detailtitle">${srcBadge(it.location,it.cost,\'srcbig\')}\n'
            '        <div class="stitle">${javTitleHtml(it)}'
            '${it.location===\'online\'?\'\':`<span class="srctools detailtitletools">'
            '${sourceToolButtons(it.id)}</span>`}</div></div>')
        self.assertPageContains(".detailtitle{display:flow-root;margin-bottom:10px}")
        self.assertPageContains(
            ".detailtitletools{display:inline-flex;vertical-align:middle;margin:3px 0 3px 8px;flex-wrap:nowrap}")
        # 徽标那个浮动块整好一行高（28px），所以第二行起是整行宽。
        self.assertPageContains(".detailtitle .stitle{min-width:0;margin:0;line-height:1.75}")

    def test_detail_metadata_uses_icons_instead_of_release_copy(self):
        self.assertPageContains('<span class="detailmetaitem">${icon(\'ratio\')}')
        self.assertPageContains('<span class="detailmetaitem">${icon(\'hard-drive\')}')
        self.assertPageContains('<span class="detailmetaitem">${icon(\'calendar\')}')
        self.assertPageContains('id="i-ratio"')
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
        for path in ("'/api/ads?limit=1'", "'/api/duplicates?limit=1'", "'/api/sources'"):
            self.assertPageContains(path)
        # 标题是正文区的第一行，不用原生 legend——legend 会在上边框上开个缺口，
        # 三张卡内容高度不同时那道缺口的位置也跟着不齐。
        for title in ("fieldsetTitle('cleanupJunkTitle','垃圾文件')",
                      "fieldsetTitle('cleanupDupTitle','重复文件')",
                      "fieldsetTitle('cleanupEmptyTitle','空文件夹')"):
            self.assertPageContains(title)
        self.assertPageLacks("<legend>垃圾文件</legend>")
        self.assertPageContains('class="cleanupfieldset" data-geist-fieldset aria-labelledby=')
        self.assertPageContains('class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset')
        self.assertPageContains("api('/api/data-cleanup/empty-folders',{method:'POST',body:'{}'})")
        self.assertPageContains("来源根目录不会删除")
        self.assertPageContains(".cleanupfieldset>.geist-fieldset-content{flex:1;min-height:0;padding:20px}")
        # Geist 的 Fieldset 全框只有一条线，在底部操作条上方；标题底下不划线。
        self.assertPageContains("--fieldset-bar-h:52px;")
        self.assertPageContains(".geist-fieldset-title{margin:0 0 10px;")
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

        底色同理：条子是 `--overlay-5`，按钮填比它更深的 `--surface` 才分得出来。
        数据管理那六颗此前是透明底，和同一页「网盘与账本」的 `.resourceaction`
        并排时是两种按钮。
        """
        self.assertPageContains(".cleanupfieldset>.geist-fieldset-footer{box-sizing:border-box;"
                                "min-height:var(--fieldset-bar-h);")
        self.assertPageContains("padding:8px 16px 8px 20px;")
        self.assertPageContains(".resourcesyncfooter,.resourceapplyrow{box-sizing:border-box;"
                                "min-height:var(--fieldset-bar-h);")
        # 说明能被压窄并换行，按钮不参与压缩。
        self.assertPageContains(".resourcesyncfooter>p,.resourceapplyrow>p{min-width:0;margin-right:auto}")
        self.assertPageContains(".cleanupfieldset button{box-sizing:border-box;flex:none;min-height:32px;")
        self.assertPageContains("background:var(--surface);color:var(--ink-2);display:inline-flex;")
        self.assertPageContains(".cleanupfieldset button:hover{background:var(--hover);"
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
        self.assertIn('<p class="cleanupmeta" data-cleanup-meta="${section}">', cleanup)
        counts = self.page.split("async function paintDataManagementCounts()", 1)[1].split(
            "let dupData=null;", 1)[0]
        self.assertIn("REVIEW_LABELS[key]||key", counts, "人工复核的分项得是分类名")
        self.assertIn("`其余 ${rest.toLocaleString()}`", counts)
        self.assertIn("`占用 ${fmtSize(data.bytes||0)}`", counts, "回收站要说清空能腾出多少")
        self.assertPageContains(".cleanupmeta:empty{display:none}")
        # 三个「· 在线」徽章换成一行来源名：在线与否是资源同步那块的读数，
        # 在空文件夹卡上只有离线时才改变结论。
        self.assertPageLacks("class=\"cleanupsource\"")
        self.assertPageLacks(".cleanupsources{")
        self.assertIn("`${offline.map(sourceName).join(' · ')} 离线`", cleanup)
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
        self.assertPageContains('data-dup-all="115"')
        self.assertPageContains('data-dup-all="pikpak"')

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
                '<div><b data-middle-truncate title="${esc(asset.name||\'\')}"',
                '<div><b data-middle-truncate title="${esc(row.asset_name||\'\')}"',
                '<b data-middle-truncate>${esc(javDisplayName(media))}</b>',
                '<b data-middle-truncate>${esc(javDisplayName(x))}</b>',
                'class="t resourcecardtitle" data-middle-truncate',
                'class="t junkcardtitle" type="button" data-junk-open data-middle-truncate',
                'class="t junkcardtitle" data-middle-truncate',
                # 死链表里的地址：`/official/talent/X` 与 `/talent/X` 的差别就在尾部，
                # 尾部省略会把这张表要回答的东西切掉。
                'rel="noreferrer" data-middle-truncate>${esc(item.url)}</a>'):
            self.assertPageContains(consumer)
        # 11 而不是 12：高清版目标页的标题按钮搬进了 island，那一处由
        # tests/test_frontend_build.py 断言。
        self.assertEqual(self.app_js.count("data-middle-truncate"), 11)
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
        self.assertPageContains(".qualityitem h3 button{display:block;width:100%")
        self.assertPageLacks(".qualityitem h3 button{max-width:100%;border:0;background:transparent;padding:0;color:inherit;text-align:left;cursor:pointer;overflow-wrap:anywhere;display:-webkit-box")

    def test_every_end_truncation_selector_is_explicitly_reviewed(self):
        """新增 CSS 省略必须先决定它是语义文本，还是应改用 MiddleTruncate。"""
        reviewed_end_selectors = {
            ".alphatag span:first-of-type", ".av .nm", ".entitylinklabel",
            ".fauthor .fsource.frow>b", ".fauthorhead b",
            # 四段计数按重要性从左排（未看在最前），尾部省略切掉的正是最不影响判断的那几段；
            # 它不是标识符，中间截断只会把「未看 3」也切开。
            ".fbulkcounts",
            ".fchip", ".followpageaction .fmeta", ".fpickactions [data-pick-state]",
            ".fsechead .fmeta",
            ".frow>b", ".fvkind", ".idname", ".kv>span:first-child",
            ".meta .t", ".meta .who", ".mixcopy b,.mixcopy span",
            ".mixitemtext [data-truncate-end]", ".mixqueuehead h2",
            ".ncard .meta .why",
            ".playerstats dd", ".playerstatsmetric>span",
            ".relatedperson .nm", ".reviewentity b",
            ".reviewitem h4", ".searchoption span",
            ".sgrid.mixgrid>.mixqueue .mixqueuehead span", ".sidebarorderlabel>b",
            ".insightrankrow>span:nth-child(2)", ".insighttablerow span", ".metricstrip small,.tastesummary>small",
            ".gselectfield>span",
            ".tagpickitem .pickname", ".tasterank b,.tasterank small",
            ".tastesource b,.tastesource small", ".tg",
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
        self.assertPageContains("文件仍在回收站里，可以还原")

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
        self.assertPageContains("const comparison=row.comparison_assets||[];")
        self.assertPageContains('class="reviewcompare"')
        self.assertPageContains("reviewCategory==='fc2_similarity'?''")

    def test_reader_review_uses_the_writer_mirror_without_offering_fake_writes(self):
        self.assertPageContains("const runtime=await surfaceApi(surface,'/healthz')")
        self.assertPageContains("reviewRuntime=runtime;reviewData=next")
        self.assertPageContains("正在显示写入端的实时复核队列")
        self.assertPageContains("前往写入端复核")
        self.assertPageContains("canApprove&&!locked")
        self.assertPageContains("${locked?' disabled':''}>跳过")

    def test_index_pages_drop_the_home_filter_bars_and_back_button(self):
        # 艺人/标签索引和资料页一样是「专注看某一类实体」的表面。
        self.assertCode(
            "body.entity-open #tiers,body.entity-open #tagbar,\nbody.index-open #tiers,body.index-open #tagbar{display:none}")
        self.assertPageLacks('id="iClose"', "顶栏入口本身就是返回路径")
        self.assertPageLacks("$('#iClose').onclick")

    def test_entity_and_follow_pages_share_round_video_image_buttons(self):
        self.assertPageContains('id="i-pics" viewBox="-1.6 -1.6 19.2 19.2" fill="currentColor" stroke="none"')
        self.assertPageContains('export function mediaViewButtonsHtml({')
        self.assertPageContains('class="mediaviewbutton" type="button" data-media-view="${esc(value)}"')
        self.assertPageContains("const mediaToggle=photoCount?mediaViewButtonsHtml({active:mediaSelected?'photos':'videos'")
        self.assertPageContains("imageValue:'photos',imageLabel:'照片',videoCount:d.asset_count,imageCount:photoCount")
        self.assertPageContains('<section class="entitytagbar" aria-label="媒体与标签"><div class="entitytags">${mediaToggle}${tags}</div></section>')
        self.assertPageContains("controls.hidden=!photos")
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
        self.assertPageContains('<button data-tag-scope="local"')
        self.assertPageContains('<button data-tag-scope="online"')
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
        self.assertPageContains("${icon('hard-drive')}本地")

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
        self.assertPageContains("  .indexheading,#indexCount,.tagmodes button{white-space:nowrap}")
        # 换行位靠一个零高的伪元素占满整行，开关的 order 排在它之后。
        self.assertPageContains('  .index .ihead::after{content:"";order:2;flex-basis:100%;height:0}')
        self.assertPageContains("  .index .ihead .geist-search{order:1}")
        self.assertPageContains(
            "  .index .ihead .tagmodes,.index .ihead .iconswitch{order:3;flex:none}")

    def test_the_two_filled_glyph_icons_say_what_a_stroked_icon_cannot(self):
        """字母表是 Aa，播放列表是队列。

        `list-filter` 的本义是筛选，只有源筛选那一处该用它。这两枚取 Phosphor
        regular，填充声明写在 symbol 上——全局 svg 是
        `stroke:currentColor;fill:none`，只补 path 会让填充图标整枚不可见。
        """
        self.assertPageContains("${icon('text-aa')}字母表")
        self.assertPageContains("['playlists','播放列表','playlist'],")
        self.assertPageContains("emptyState('playlist','还没有播放列表'")
        self.assertPageContains('aria-label="编辑播放列表">${icon(\'playlist\')}')
        self.assertPageContains('title="加入播放列表">${icon(\'playlist\')}')
        # 剩下的那一处 list-filter 是真的筛选，不能一起换掉。
        self.assertPageContains("${icon('list-filter')}<span data-srcfilter-label>")
        for symbol in ("text-aa", "playlist"):
            self.assertRegex(
                self.page,
                rf'<symbol id="i-{symbol}" viewBox="[-\d. ]+" fill="currentColor" stroke="none">')
        self.assertPageContains("Phosphor 2.1.1 regular, MIT")
        self.assertPageLacks("i-a-large-small")

    def test_each_glyph_names_the_thing_it_sits_next_to(self):
        """一枚字形只代表一个意思，同一个意思也只有一枚字形。

        一枚字形背两个意思时，用户在一处学会的含义会在另一处骗他，所以各归各的：
        `refresh-cw` 只归原地换一批，`database` 只归管理入口，`folder-open` 只归
        打开位置，`play` 只归真的起播，音量键不去标音频文件。这条逐枚钉住归属。

        `i-clock` 没有使用者，是用户点名留的备用件，不要当死代码清掉。
        """
        # 文件类型标的是文件，不是打开动作，也不是音量。
        self.assertPageContains("['archive','压缩包','file-archive'],['audio','音频','file-audio']")
        self.assertPageContains("archive:['压缩包','file-archive'],")
        self.assertPageContains("audio:['音频','file-audio'],")
        # 「加载更多」往下接一页，方向由字形给出；`refresh-cw` 是原地换一批。
        self.assertPageContains("data-follow-more>${icon('chevron-down')}加载更多</button>")
        self.assertPageContains('title="换一批" aria-label="换一批">${icon(\'refresh-cw\')}')
        # 两个空态各说自己那件事：筛不出结果，和一次比对没有发现。
        self.assertPageContains("emptyState('search-x','当前筛选下没有更新'")
        self.assertPageContains("emptyState('file-stack','没有找到重复文件'")
        # 本地是磁盘、在线是订阅源；标签条这一对和关注页的来源图标同一套。
        self.assertPageContains('data-tag-scope="local" aria-pressed="${!onlineTags}">${icon(\'hard-drive\')}本地')
        self.assertPageContains('data-tag-scope="online" aria-pressed="${onlineTags}">${icon(\'rss\')}在线')
        # 「喜爱理由」开的是一个写字面板，不是喜欢开关——那个是旁边的 thumbs-up。
        self.assertPageContains('data-has-reason="${!!it.like_reason}">${icon(\'notebook-pen\')}')
        self.assertPageContains('aria-label="${it.liked?\'取消喜欢\':\'喜欢\'}"')
        # 侧栏：已标记是书签，沉浸模式是一叠竖着翻的卡；`play` 留给真的起播。
        self.assertPageContains("['flagged','已标记','bookmark'],")
        self.assertPageContains("['immerse','沉浸模式','gallery-vertical-end'],")
        self.assertPageContains("<span>进入沉浸模式</span>")
        self.assertPageContains("class=\"shorts-enter\" type=\"button\">${icon('play')}")
        # 主题三档各归各的：太阳是浅色、月亮是深色；跟随系统那档说的是「照这台设备走」，
        # 讲的是设备不是明暗，所以跟 vercel.com 后台一样用显示器。画面尺寸量的是画幅本身，
        # 归 `ratio`。
        self.assertPageContains(
            "[['system','跟随系统','monitor'],['light','浅色','sun'],['dark','深色','moon']]")
        self.assertPageContains("${icon('ratio')}<span>${it.width||'?'}×${it.height||'?'}</span>")
        # 换下来的三枚没有别的使用者，雪碧图里也不留。
        for gone in ("i-monitor-cog", "i-star", "i-volume-2", "i-sun-moon"):
            self.assertPageLacks(f'<symbol id="{gone}"')
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
                ("sperm", "1.5 1.2 21.2 21.2"),
                ("brand-x", "-0.9 -0.9 25.9 25.9")):
            self.assertPageContains(f'<symbol id="i-{symbol}" viewBox="{box}"')
        # 框由生成脚本负责重放：`npm run vendor:web` 每次都写出同一份。
        generator = (Path(__file__).resolve().parents[1]
                     / "scripts" / "vendor_web_dependencies.mjs").read_text(encoding="utf-8")
        self.assertIn('viewBox: "-7.3 32.8 262.5 182.9"', generator)
        self.assertIn('viewBox: "10.4 10.5 259.2 259.2"', generator)
        self.assertIn('const SPERM_VIEWBOX = "1.5 1.2 21.2 21.2";', generator)

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
        self.assertPageContains(".tagmodes button svg.iconwide{width:auto}")

    def test_plain_text_inputs_share_one_token_so_the_button_beside_them_matches(self):
        """控件高度只有一档：输入框 38px，同一行的按钮照抄这个数。

        窄屏那条 `font-size:16px!important` 会把没写死高度的输入框抬 3px，旁边的
        按钮不动，一行里两个控件差一截；播放列表那张表还因为 `flex:1 1 100%`
        把提交键顶到下一行。纯文本输入框全站共用 `.geist-input`。
        """
        self.assertPageContains(".geist-input{box-sizing:border-box;width:100%;min-width:0;height:var(--control-h);")
        self.assertPageContains(".playlistcreate .geist-button{height:38px;padding:0 13px}")
        # 提交键是主动作，实心档由共用的 .geist-button.primary 给，不再本地拼一套描边。
        for label in ("保存 ${mix.items.length} 个视频", "新建并加入", "新建"):
            self.assertPageContains(
                f'<button class="geist-button primary" type="submit">{label}</button>')
        self.assertPageLacks(".playlistcreate button,.playlistactions button{")
        self.assertPageContains(".faliasform .fbtn{height:38px;min-height:38px}")
        self.assertPageContains(".playlistcreate label{display:grid;gap:5px;color:var(--muted);"
                                "font-size:var(--fs-xs);flex:1 1 200px;max-width:320px}")
        self.assertPageLacks(".playlistcreate label{flex:1 1 100%}")
        # 自己拼内边距的那几处已经并入 token，别再冒出第二份。
        self.assertPageLacks(".playlistcreate input,.playlistmeta input{min-width:220px;")
        self.assertPageLacks(".faliasform input{min-width:0;height:34px;")
        for needle in (
                '<label>名称<input class="geist-input" name="name"',
                '<label>新播放列表<input class="geist-input" name="name"',
                '<input class="geist-input" data-playlist-name',
                '<input class="geist-input" name="canonical"',
                '<input class="geist-input" name="alias"'):
            self.assertPageContains(needle)

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
        self.assertIn("button._observer?.disconnect();", body, "重画后必须先断开旧观察器")
        self.assertIn("if(button.hidden)return;", body, "藏起来的按钮不该被观察")
        self.assertIn("rootMargin:'320px'", body)
        self.assertEqual(self.page.count("new IntersectionObserver"), 2,
                         "观察器只允许存在两处：wireLoadMore 与首页自己的 loadObserver")
        self.assertEqual(self.page.count("wireLoadMore("), 4,
                         "1 处定义加 3 处调用；对不上就是又有人自己写了一套")

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
        self.assertPageContains(
            ".detailtitle>.srcbig{float:left;width:17px;height:28px;margin:0 8px 0 0;place-items:center}")

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
            ':(x.is_jav&&x.code?`<img src="/cover?code=${encodeURIComponent(x.code)}"')

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
            ".ncard .mavstack .mav:nth-child(3),\n"
            ".sgrid.mixgrid>.mixqueue .mavstack .mav:nth-child(3){display:none}")
        self.assertPageContains(
            ".ncard .meta .s{flex-wrap:nowrap;overflow:hidden}")
        self.assertPageContains(
            ".ncard .meta .why{flex:1 1 0;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}")
        self.assertPageContains(".ncard .meta .size,.ncard .meta .watchcount{display:none}")
        self.assertPageLacks(".ncard .meta .s{line-height:1.45;height:")

    def test_a_cold_deep_link_clears_the_catalog_skeleton(self):
        """深链冷启动时列表一次请求都没发过，那张「正在读取作品」会永远停在详情下方。

        它和 `hasReturnSurface` 是同一张骨架的两半：那边负责关掉详情后补装列表，
        这边负责在详情打开期间不谎报「正在读取」。
        """
        self.assertPageContains("function clearIdleCatalogLoading()")
        self.assertPageContains("if(!grid.querySelector('.catalog-skeleton'))return;")
        self.assertPageContains("if(!returnSurfaceReady)clearIdleCatalogLoading();")

    def test_group_collapse_is_a_setting_and_defaults_to_on(self):
        """合并分卷与版本可以关掉，关掉后同番号的每一卷／每一版各占一张卡。

        折叠是渲染时做的，所以改完必须重取当前列表：不重画的话，之前被跳过的
        那些卡不会自己冒出来，看上去像开关没生效。
        """
        self.assertPageContains("groupCollapse:true,sidebarOrder:DEFAULT_SIDEBAR_ORDER};")
        self.assertPageContains("appSettings.groupCollapse=appSettings.groupCollapse!==false;")
        self.assertPageContains('<input type="checkbox" id="groupCollapseSetting">')
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
        self.assertLess(combo.index("catalogOnScreen()"), combo.index("$('#combo').innerHTML=\n"),
                        "判据要在拼 HTML 之前，不能画完再擦")
        # 铺开索引页／资料页与进入管理页是同一件事的两侧，各自的共用函数都要收掉芯片。
        self.assertPageContains(
            "$('#stats').hidden=true;$('#index').hidden=false;$('#grid').innerHTML='';"
            "$('#combo').innerHTML='';",
            "索引页与资料页的共用铺开函数必须收掉目录的筛选芯片")
        for name in ("openIndex", "openEntity"):
            self.assertIn("showIndexLoading(", self._js_function(name),
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
        self.assertPageContains("$('#tagbar').querySelectorAll('[data-tag]')"
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
        self.assertPageContains("$('#combo').querySelectorAll('[data-untag]')"
                                ".forEach(b=>b.onclick=()=>toggleTag(b.dataset.untag));")
        self.assertCode("$('#clrAll').onclick=()=>commitContextFilter(filters=>{\n"
                        "    filters.tag='';filters.creator='';filters.studio=''});")
        # 按下态与表头也读同一份判据，资料页的标签因此和目录一样能叠加。
        self.assertPageContains("tagPressed(filterState.tag,t.k)")
        self.assertPageContains("aria-pressed=\"${tagPressed(filters.tag,x.k)}\"")
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
        for key in ("author", "provider", "tag", "status", "media"):
            self.assertIn("'" + key + "'", writer,
                          "followViewPath 没把 " + key + " 写进 URL")
            self.assertIn("'" + key + "'", reader,
                          "readFollowView 没从 URL 读回 " + key)
        # 「全部」现在是默认视图，缺省即全部，所以它不写进 URL；只有收窄到某个
        # 状态才落 status。旧链接里的 status=all 仍按全部读回。
        self.assertIn("if(followFilter)params.set('status',followFilter);", writer)
        self.assertIn("(status===null||status==='all')?'':status", reader)

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
        # 「返回关注页」和「回到关注首屏」两处重置也得落在同一个默认上。
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
        self.assertPageContains(
            """<span class="fmanagesort">${icon('sort')}${selectFieldHtml(FOLLOW_SORT_OPTIONS,followManageSort,""")
        self.assertPageContains('id="i-sort"')
        self.assertPageContains(".fmanagesort{position:relative;display:inline-flex;align-items:center")
        self.assertPageContains(".fmanagesort>svg{position:absolute;z-index:1;left:9px;width:16px;height:16px")
        self.assertPageContains(".fmanagesort .gselectfield{height:32px;padding:0 10px 0 31px")
        # 无障碍名称只剩 aria-label 一处，去掉标签后它必须留着；它由组件写到触发器上。
        self.assertPageContains("{label:'关注列表排序',attr:'data-follow-sort'}")
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
        # 高度不收进 --control-h：这一行的按钮和版式开关都在 32px 上，排序框单独抬一档
        # 就是同一行里出现两种「同一种控件」。
        self.assertIn("height:32px", rule, ".fmanagesort 的触发器与标题行同高")
        self.assertPageContains("gap:6px;height:32px")

    def test_destructive_buttons_fill_red_on_hover(self):
        """危险动作的悬停态一律是 --drop 实底加白字，全站一个写法。

        只描红边、红字的话，静止态和悬停态在暗色底上几乎一样亮，按下去之前看不出这是
        不可逆动作。Geist 的 error Button 同样是实心红填充（oklch(.5801 .227 25.12) 底、
        白字），只是它静止态就红，Peach 把红留到悬停。
        """
        fill = "background:var(--drop);border-color:var(--drop);color:#fff}"
        for selector in (".fbtn.fquiet:hover{", ".fcredactions button.fquiet:hover{",
                         ".cleanupfieldset button.danger:hover{",
                         ".dupbtns button.danger:hover{", ".resourcedanger:hover:not(:disabled){",
                         ".junkactions .junktrash:hover:not(:disabled){",
                         ".playlistactions .danger:hover{",
                         ".reviewactions .reject:hover{"):
            self.assertPageContains(selector + fill, f"{selector} 的悬停态要填 --drop")

    def test_bulk_footer_keeps_one_line_and_ellipsises_its_counts(self):
        """底部批量条保持一行，宽度不够时省略说明文字，而不是把动作键甩到第二行。

        它和分区标题行是同一种行：一行里唯一可以缩的是说明文字，动作键要完整读出来。
        允许换行的话，窄屏上四段计数加两个键一定放不下，键落到第二行、底栏白长一截。
        基准取 0 而不是 auto：按内容宽度参与排线的话，它先把整行挤断，缩放轮不到发生。
        """
        self.assertPageContains(".fnote.fbulkrow{display:flex;align-items:center;gap:4px 10px}")
        self.assertPageLacks(".fnote.fbulkrow{display:flex;align-items:center;flex-wrap:wrap",
                             "换行是这条行长成两行的原因")
        self.assertPageContains(".fbulkcounts{flex:1 1 0;min-width:0;overflow:hidden;"
                                "text-overflow:ellipsis;white-space:nowrap}")
        self.assertPageContains(".fbulk{display:inline-flex;gap:8px;margin-left:auto;flex:none}")
        # 标题行早就是这个写法，同一种行的两处行为要对得上。
        self.assertPageContains(".fsechead .fmeta{flex:1 1 0;min-width:0;overflow:hidden")
        self.assertPageContains(".fsechead .fbtn,.fsechead .fmanagesort{flex:none}")

    def test_add_form_only_sizes_the_one_button_it_actually_has(self):
        """`.faddform` 里唯一的按钮是来源筛选触发器，高度由它自己那条给。

        这个表单没有提交键——只读查询回车即执行。再留一条按 `.faddform .fbtn` 写的通用
        高度，读的人会以为旁边还有个提交键；而它被更具体的那条完全盖住，改它不会有任何
        效果，是一条只会误导人的死规则。
        """
        self.assertPageContains(
            ".faddform .fsrcfilter .fbtn{width:auto;height:38px;min-height:38px;padding:0 11px}")
        self.assertPageLacks(".faddform .fbtn{height:38px;min-height:38px}",
                             "被更具体那条完全盖住的死规则")
        start = self.app_js.index('<form class="faddform" id="followAdd">')
        form = self.app_js[start:self.app_js.index("</form>", start)]
        self.assertNotIn('type="submit"', form, "添加表单没有提交键，回车即执行")
        self.assertIn('<div class="fsrcfilter" id="followSrcFilter"></div>', form)
        # 别名表单那个提交键是活的，别顺手一起删。
        self.assertPageContains(".faliasform .fbtn{height:38px;min-height:38px}")
        self.assertPageContains('<button class="fbtn" type="submit">保存别名</button>')

    def test_follow_filter_buttons_write_the_url_before_refetching(self):
        """先写 URL 再重取。反过来的话 openFollow 会照旧 URL 把状态推回去。"""
        self.assertPageContains(
            "const applyFollowView=()=>{route(followViewPath());openFollow(false)};")

    def test_photo_wall_uses_cached_thumbnails_and_only_the_lightbox_reads_originals(self):
        # 瀑布流铺原图等于一屏付几十兆 PikPak 流量；缩略图由服务端缓存一次。
        self.assertPageContains('<img src="/photo-thumb?id=${item.id}"')
        # 取图口收进 photoSlide：灯箱现在也服务关注页的在线图，模板不能再写死本地口。
        self.assertPageContains(
            ':{src:`/photo?id=${item.id}`,thumb:`/photo-thumb?id=${item.id}`')
        self.assertPageLacks('<img src="/photo?id=${item.id}" class="photocell"')
        self.assertPageContains(".photowall{column-count:5;column-gap:10px}")
        self.assertPageContains("break-inside:avoid")

    def test_photo_tab_opens_the_flat_waterfall_without_fixed_ratio_album_cards(self):
        self.assertPageContains("if(media==='photos'){renderPhotoWall(kind,name,filters,entityPhotos);return}")
        self.assertPageContains("<h3>照片 · ${(data.total||0).toLocaleString()} 张</h3>")
        self.assertPageContains("/api/photos?kind=${encodeURIComponent(kind)}&name=${encodeURIComponent(name)}&limit=120&offset=${photoWallItems.length}")
        self.assertPageLacks("renderPhotoSets")
        self.assertPageLacks(".photosetcover{display:block;aspect-ratio:3/4")

    def test_jav_entity_pages_render_and_wire_the_same_layout_buttons(self):
        self.assertPageContains(
            'section.innerHTML=`<div class="entitycollectionhead"><h3></h3>')
        self.assertPageContains('entityCollectionSortsHtml=filters=>`<span class="sorts">')
        self.assertPageContains("${javActive()?javLayoutButtons():''}")
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
            "iconSwitchHtml('people-layout','艺人索引版式',PEOPLE_LAYOUTS,peopleIndexLayout(),")
        self.assertPageContains("{attr:'data-people-layout'}")
        # 只有艺人和创作者是头像网格；标签页那一屏没有图可放大。
        self.assertPageContains("${people?peopleLayoutButtons():''}")
        self.assertPageContains(
            "wireIconSwitch($('#index'),'data-people-layout',setPeopleIndexLayout);")
        self.assertPageContains(
            '`<div class="igrid" data-layout="${peopleIndexLayout()}">${peopleHtml(d.items)}</div>`')
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

    def test_switching_the_people_layout_neither_repaints_the_grid_nor_refetches(self):
        # 版式是纯展示层的事：改容器上的一个属性就够，和关注列表版式同一个做法。
        self.assertCode(
            "function setPeopleIndexLayout(value){\n"
            "  appSettings.peopleLayout=value;\n"
            "  saveSettings();\n"
            "  document.querySelectorAll('.igrid')"
            ".forEach(grid=>{grid.dataset.layout=peopleIndexLayout()});\n"
            "}")

    def test_the_big_people_layout_frames_the_detected_face(self):
        # 3:4 竖幅按几何居中会把脸切掉。换算只有 faceOrigin 一份：资料页写进 img 的
        # style，索引页交给圆框上的 --face——那里的 img 是八处共用的 avatarInner 拼的。
        self.assertPageContains("function faceOrigin(f){")
        self.assertCode("  const origin=faceOrigin(f);\n"
                        "  return origin?` style=\"object-position:${origin}\"`:'';")
        self.assertPageContains("const face=faceOrigin(x.avatar_focus);")
        self.assertPageContains('<span class="ring"${face?` style="--face:${face}"`:\'\'}>')
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
        self.assertPageContains('data-zoom-step="-1" aria-label="缩小">${icon(\'minus\')}')
        self.assertPageContains('data-zoom-step="1" aria-label="放大">${icon(\'plus\')}')
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
            "queueMicrotask(()=>{const target=reveal.hidden?title:reveal;target.focus()})")
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

    def test_failed_review_decisions_are_shown_instead_of_silently_swallowed(self):
        """「点了没反应」的真身：失败被吞掉，按钮还卡在 disabled。

        `api()` 在任何非 2xx 都 throw，而这个 async onclick 漏掉 catch 的话：
        异常成了 unhandled rejection，`button.disabled=false` 永远到不了，于是
        按钮永久禁用、界面一句话都不给。失败必须说出来并把按钮放开让人重试。
        """
        self.assertPageContains('<span class="reviewstate" aria-live="polite"></span>')
        self.assertPageContains("if(state)state.textContent=result.error||'服务端拒绝了这次判定'")
        self.assertPageContains("if(state)state.textContent=e.message")
        # 成功路径 return，其余出口都必须回到放开按钮那一行。
        self.assertPageContains("button.disabled=false;")

    def test_entity_subject_reviews_lead_with_the_creator_not_one_sample(self):
        """创作者标签和西方身份判的是「这个人」，不是某一条作品。

        `_attach_review_asset_context` 会退回到 `preview_assets[0]`，于是卡片顶上
        挂着随便一条样本、写着「打开原视频」：下面 60 个样本上面 1 个视频，
        西方身份更极端——772 部作品配 1 个。顶部必须是创作者入口。
        """
        self.assertPageContains(
            "const ENTITY_REVIEW_CATEGORIES={creator_tags:'creator',western_identity:'creator'}")
        self.assertPageContains("const subjectKind=ENTITY_REVIEW_CATEGORIES[reviewCategory]")
        self.assertPageContains('<div class="reviewentity">')
        # 作品数取 video_count（创作者标签）或 videos（西方身份），两批候选列名不同。
        self.assertPageContains("const works=Number(row.video_count||row.videos||0)")
        self.assertPageContains("部作品")
        # 头像走同一条链，装了实体图才出 `<img>`，取不到就是首字母。
        self.assertPageContains(
            "row.entity_id?{id:row.entity_id,has_image:row.has_image}:null,null,subjectKind)")
        # 复核页没有全局委托，必须自己接线，否则入口点了没反应。
        self.assertPageContains(
            "$('#stats').querySelectorAll('[data-entity-kind]').forEach(button=>button.onclick=()=>")

    def test_review_page_applies_the_certain_part_before_loading_the_queue(self):
        """ADR-0018：无可判断的条目不该在队列里白占一轮。"""
        self.assertPageContains("api('/api/review/auto-apply',{method:'POST',body:'{}'})")
        # 只读端本来就会 409，那是正常状态：失败不拦页面，但也不静默吞掉。
        self.assertPageContains("console.info('自动落库未执行：'+e.message)")

    def test_entity_cards_do_not_print_the_name_twice(self):
        """创作者入口里已经写了名字，卡片顶上再来一个 h4 就是同一行字上下两遍。"""
        self.assertPageContains("subjectKind&&subjectName?'':`<h4>${esc(titleText)}</h4>`")
        # 作品数同理：创作者入口里已经写了「115 部作品」，上面不该再来一行「样本/资产：115」。
        self.assertPageContains("subjectKind&&subjectName?'':`<p>${esc(row.board||row.assets")
        # 卡片里只有这一个主体，衬底和居中只会把它推离左边缘，和下面的样本网格对不齐。
        self.assertPageLacks(
            ".reviewentity{display:grid;grid-template-columns:132px minmax(0,1fr)")
        self.assertPageContains("justify-content:start}")
        self.assertPageContains(".reviewentityface{position:relative;width:44px;height:44px;justify-self:start")

    def test_sole_metadata_candidate_is_shown_not_offered_as_a_choice(self):
        """只有一个候选时没什么可选的，单选圈会让人以为还有别的选项。

        但 radio 必须留在 DOM 里：提交路径读的就是 `[name^="metadata-"]:checked`，
        删掉它会让「通过」退化成「必须选择一个来源值」的报错。
        """
        self.assertPageContains("candidates.length===1")
        self.assertPageContains('<div class="metadatasole">')
        self.assertPageContains('value="${esc(candidates[0].candidate_key)}" checked')
        self.assertPageContains(".metadatasole input{display:none}")
        # 提交路径没变，仍然只认 :checked。
        self.assertPageContains(
            "item.querySelector('[name^=\"metadata-\"]:checked')?.value")

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
        self.assertPageContains("it.location==='online'?'':`<span class=\"srctools detailtitletools\">${sourceToolButtons(it.id)}</span>`")

    def test_resource_sync_lives_in_data_management_and_keeps_offline_sources_safe(self):
        self.assertPageContains("${resourceSyncMarkup()}")
        self.assertRoute('/resource-sync', "openResourceSync(push)")
        self.assertPageContains("route('/data-cleanup#resource-sync',!push)")
        self.assertPageContains("api('/api/resource-sync/scan',{method:'POST'")
        self.assertPageContains("api('/api/resource-sync/apply',{method:'POST'")
        self.assertPageContains("source.unreadable")
        self.assertPageContains("background:true,restart:true")
        self.assertPageContains("payload.status==='running'")
        self.assertPageContains("location.pathname==='/data-cleanup'")
        self.assertPageContains("background:true,status_only:true")
        # 上一轮跑完的结果是那一刻的快照。进页面就铺开会被读成现在的账本状态，
        # 而页面上没有任何东西说它是旧的。
        self.assertPageContains("if(existing.status==='running')void followScan(existing);")
        self.assertPageContains("同步并清理")
        self.assertPageContains('class="resourcesyncfooter geist-fieldset-footer"')
        self.assertPageContains('class="resourcepanel"')
        self.assertPageContains('class="resourceapplyrow"')
        self.assertPageContains(".resourceaction{box-sizing:border-box;height:36px")
        self.assertPageContains("@media(max-width:640px){.resourcesync .resourcesources{grid-template-columns:1fr}")
        self.assertPageContains(".resourcesyncbox,.resourcepanel{overflow:clip;border:1px solid var(--line-soft);border-radius:var(--floating-radius)")
        self.assertPageContains(".resourcesources article+article{border-left:1px solid var(--line-soft)}")
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

if __name__ == "__main__":
    unittest.main()
