import re
import unittest
from pathlib import Path


class WebUiSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 页面拆成 index.html + app.css + app.js + web/js 下的 ES module。这些断言
        # 守的是「Web 表面」这一个契约，不是某个文件，所以把所有源码接起来一起看。
        # 模块目录用 glob 而不是写死清单：再拆出新模块时不必回头改这里。写死的后果
        # 是断言悄悄扫不到新文件——它照样「通过」，但什么也没守住。
        web = Path(__file__).resolve().parents[1] / "web"
        sources = [web / "index.html", web / "app.css", web / "app.js"]
        sources.extend(sorted((web / "js").glob("*.js")))
        cls.css = (web / "app.css").read_text(encoding="utf-8")
        cls.app_js = (web / "app.js").read_text(encoding="utf-8")
        cls.page = chr(10).join(
            path.read_text(encoding="utf-8") for path in sources
        )

    # 页面源断言必须自带有界失败信息。assertIn 失败时会把整个 index.html（约 189 KB）
    # 原样塞进错误消息，一条失败就产出 195 KB 输出；工具管道遇到超大输出会转存成文件，
    # 看起来就像「整个会话输出消失」。真实成因是断言消息，不是测试竞态或运行器挂起。
    def assertPageContains(self, needle: str, message: str = ""):
        if needle not in self.page:
            self.fail(f"index.html 缺少：{needle!r}" + (f"（{message}）" if message else ""))

    def assertPageLacks(self, needle: str, message: str = ""):
        if needle in self.page:
            self.fail(f"index.html 不应再出现：{needle!r}" + (f"（{message}）" if message else ""))

    def test_every_font_size_comes_from_the_one_type_scale(self):
        """全站只有一套字号刻度，任何写死的像素都要有理由。

        收敛之前 `app.css` 里散着 21 种字号（9…48px），相邻两档常常只差半个像素——
        既排不出层级，也没法复核「这里为什么是 12.5」。现在一律走 `--fs-*`。

        唯一的例外是移动端输入框那条 `16px!important`：那是 iOS 的自动放大阈值，
        不是刻度里的一档。让它跟着 `--fs-lg` 走的话，将来把 lg 调成 17 或 15
        都会悄悄破坏那个保护，而症状（在 iPhone 上聚焦输入框页面猛地放大）
        跟字号改动看不出任何关系。
        """
        css = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text(
            encoding="utf-8")
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

    def test_pill_shapes_are_reserved_for_things_that_are_actually_tags(self):
        """整圆胶囊有一个来源，普通元信息不许长成标签。

        `vercel-report-design` 点名要拒绝的反射之一是「把普通元信息做成胶囊徽章」：
        WIP、变体类型、最大/最长这些是状态标记，做成整圆就跟真标签抢同一种视觉身份，
        用户会以为可以点。它们改用 `--badge-radius`；按钮和分段器用 `--control-radius`
        （实测 Geist 的 6px）；只有真正的标签、筛选令牌和连续的条保留 `--pill-radius`。
        """
        css = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text(
            encoding="utf-8")
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
        css = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text(
            encoding="utf-8")
        self.assertIn("--control-radius:6px; --badge-radius:4px; --floating-radius:12px", css)
        for selector, token in (
                (".ib{", "var(--control-radius)"),
                (".searchmenu{", "var(--floating-radius)"),
                (".searchoption{", "var(--control-radius)"),
                (".playlistcreate button,.playlistactions button{", "var(--control-radius)"),
                (".playlistdialog{", "var(--floating-radius)"),
                (".playlistpickrow{", "var(--control-radius)"),
                (".settingscard{", "var(--floating-radius)"),
                (".settingrow select{", "var(--control-radius)"),
        ):
            start = css.index(selector)
            rule = css[start:css.index("}", start)]
            self.assertIn(token, rule, f"{selector} 没使用 {token}")
        self.assertNotRegex(css, r"transition:\s*all(?:[; }])")

    def test_close_actions_share_geist_control_geometry(self):
        css = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text(
            encoding="utf-8")
        for selector in (".playlistdialoghead button{", ".photoclose{",
                         ".mixqueuehead button{", ".closestage{",
                         ".settingshead button{"):
            start = css.rindex(selector) if selector == ".closestage{" else css.index(selector)
            rule = css[start:css.index("}", start)]
            self.assertIn("var(--control-radius)", rule,
                          f"{selector} 是关闭操作，不是圆形标签")
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
        self.assertPageContains('<div class="settingscard">\n    <div class="settingshead">')
        self.assertPageContains('</div>\n    <div class="settingsscroll">')
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
        self.assertPageContains('<meta name="theme-color" content="#020408"')
        # 聚焦环用 color-mix 柔化：边框 72% 主调 + 26% 的外圈，仍是「看得见的焦点」。
        self.assertPageContains('.search:focus-within{border-color:color-mix(in srgb,var(--tungsten) 72%,transparent);box-shadow:')
        self.assertPageContains('@media (max-width:760px){input,textarea,select{font-size:16px!important}}')
        self.assertPageContains('button,a,input,textarea,select,summary{touch-action:manipulation}')

    def test_route_titles_and_settings_dialog_manage_focus(self):
        self.assertPageContains('const pageTitle=path=>{')
        self.assertPageContains("'follow-manage':'关注管理'")
        self.assertPageContains("unseen:'没看过','watch-later':'稍后看',flagged:'已标记'")
        self.assertPageContains('syncPageTitle(path);')
        self.assertPageContains('queueMicrotask(()=>{syncHeaderActions();paintListTitle()})')
        self.assertPageContains("queueMicrotask(()=>$('#settingsClose').focus())")
        self.assertPageContains('if(settingsReturnFocus&&document.contains(settingsReturnFocus))')
        self.assertPageContains("if(e.key!=='Tab')return")

    def test_catalog_state_title_never_leaks_into_other_routes(self):
        self.assertPageContains("!manageSection()&&isCatalogPath(path)?STATE_LABELS[state.state]||'':''")

    def test_reviewed_tag_labels_do_not_add_machine_translated_suffixes(self):
        self.assertPageLacks("'深喉':'深喉咙'")
        self.assertPageContains('const tagLabel=tag=>TAG_DISPLAY_NAMES[tag]||tag;')

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

    def test_every_card_avatar_falls_back_through_the_same_helper(self):
        # kind 参数化后，创作者复核卡片也能走同一个兜底链；默认仍是 performer，
        # 既有调用点不受影响。
        self.assertPageContains("function avatarInner(name,ref,repId,kind='performer')")
        self.assertPageContains("`/entity-image?kind=${kind}&id=${ref.id}`")
        self.assertPageContains("this.dataset.f='1';this.src='/avatar?id=${repId}'")

    def test_avatar_fallback_chains_end_by_removing_the_broken_image(self):
        """取不到图的 <img> 必须被摘掉，不能只停在 onerror=null。

        留着它有两个后果：`.entityportrait:has(img)>span` 仍然匹配，首字母垫底
        永远回不来；浏览器还会把 alt 当内容画出来——资料页上就是整个艺人名横在
        头像圈里溢出（loliburin 实测 /entity-image 与 /avatar 双 404）。
        """
        for chain in (
            # 卡片头像、资料页大圆框、关联艺人小圆框三处用的是同一套兜底。
            "this.dataset.f='1';this.src='/avatar?id=${repId}'}else{this.remove()}",
            "this.dataset.f='1';this.src='/avatar?id=${d.representative_asset_id}'}"
            "else{this.remove()}",
            "this.dataset.f='1';this.src='/avatar?id=${x.rep}'}else{this.remove()}",
        ):
            self.assertPageContains(chain)
        self.assertPageLacks("this.onerror=null;this.src='/avatar?id=")

    def test_entity_hero_avatar_frames_the_detected_face(self):
        # 资料页圆框按检出的人脸取景；换回落图时必须先摘掉内联 object-position——
        # 回落图是另一张照片，脸不在同一位置。
        self.assertPageContains("function facePos(f)")
        self.assertPageContains('"${facePos(d.avatar_focus)}')
        self.assertPageContains("onerror=\"this.removeAttribute('style')")

    def test_detail_identity_groups_by_kind_with_the_label_on_top(self):
        # 逐行一个名字在共演作品上会把整个侧栏撑满，左侧还重复一列标签。
        self.assertPageContains("const idGroup=(label,kind,list,extra='')=>list.length")
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

    def test_detail_like_reason_is_an_icon_disclosure_without_idle_explanation(self):
        self.assertPageContains('id="preferenceToggle" aria-label="喜爱理由"')
        self.assertPageContains('id="preferencePanel" hidden')
        self.assertPageContains("preferenceToggle.onclick=()=>{const open=preferencePanel.hidden")
        self.assertPageContains('placeholder="为什么喜欢？"')
        self.assertPageContains('aria-label="保存喜爱理由">${icon(\'check\')}</button>')
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
        self.assertPageContains("const performerLabel=it=>it&&it.is_jav?'女优':'艺人';")
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

    def test_big_jav_layout_crops_to_the_front_cover(self):
        """大图＝宽度不变、高度拉长，只留封套右侧那块正封。

        `object-fit:cover` 只有在容器比图片更竖时才横向裁切；容器一旦宽过封套的
        1.48，就变成纵向裁切、整张封套原样铺满——这正是旧版式「只是撑满画布」的原因。
        所以裁切必须由容器比例决定，不能只靠 object-position。
        """
        self.assertPageContains("const COVER_FRONT_RATIO=0.7;")
        self.assertPageContains("(jav&&layout==='big'?COVER_FRONT_RATIO:16/9)")
        self.assertPageContains('.poster.cover.front[data-frame="sleeve"]{object-position:100%')
        # 判据是 `jav` 不是 `useCover`：缺封面的卡片也要拉长，用 16:9 预览图上下留黑边，
        # 否则一行里高矮混排会把网格撕成锯齿状。
        self.assertPageLacks("useCover&&layout==='big'")
        # 旧键要继续认，设置存在浏览器里，改名不能让用户的选择静默回落。
        self.assertPageContains("const JAV_LAYOUT_ALIASES={cover:'big',sleeve:'small'};")

    def test_card_avatar_and_name_open_the_same_entity(self):
        """同一张卡上的头像和名字必须指向同一个身份。

        头像原来先看 performer、名字先看 creator，碰上同名的 creator/performer 重复
        实体（账本里 35 组）就会一个跳 /performers/x、另一个跳 /creators/x。
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

    def test_shuffle_sorts_are_removed_but_manual_refresh_keeps_stable_batches(self):
        """换批是列表动作，不再伪装成三种排序或自动轮换设置。"""
        self.assertPageContains("const SEED_KEY='peach.seed.v2';")
        self.assertPageContains("seed:initialParams.get('seed')||persistedSeed()")
        self.assertPageContains("const SORTS=[['rating','评分'],['o','高潮计数']")
        for option in ('<option value="seed">', '<option value="daily">',
                       '<option value="rand">'):
            self.assertPageLacks(option)
        self.assertPageLacks('id="rotateSetting"')
        self.assertPageContains("defaultSort:'new'")
        self.assertPageContains("const cleanSort=(value,fallback=appSettings.defaultSort)=>")
        # 手动换一批仍使用稳定种子，避免分页重复或漏项。
        self.assertPageContains('id="batchAction" type="button"')
        self.assertPageContains("state.sort='seed';state.seed=rollSeed()")
        # 刷新属于列表，不再占顶栏；JAV 共用同一计数/筛选行。
        self.assertPageLacks('id="refresh"')
        self.assertPageContains("+(javActive()?javLayoutButtons():'')")

    def test_offline_sources_drop_out_of_the_default_filter(self):
        """脱盘的来源要从默认筛选里摘掉。

        留着的话首页照样按它筛，出来一屏点开就报脱盘的卡片。只动默认值——地址栏里
        显式写了 `loc=` 就是用户自己选的。全部脱盘时保持原样：清空会变成什么都不筛。
        """
        self.assertPageContains("function dropOfflineFromDefaultLoc(){")
        self.assertPageContains("if(initialParams.get('loc'))return;")
        self.assertPageContains("dropOfflineFromDefaultLoc();")

    def test_select_arrow_is_drawn_by_us_and_hugs_the_border(self):
        """箭头必须自绘。

        原来留了 34px 右内边距却不画箭头、交给系统控件：Safari 把箭头画在内边距里侧，
        离右边框差一大截，和桌面 Chromium 的样子也对不上。
        """
        self.assertPageContains("appearance:none;-webkit-appearance:none")
        self.assertPageContains("background-position:right 10px center")

    def test_settings_panel_fits_the_visible_viewport_on_ios(self):
        """iOS 上 `vh` 算的是不减地址栏的「大视口」。

        按 90vh 撑出来的面板会顶到地址栏和状态栏底下，上半截被遮住——手机上实测过。
        `dvh` 跟着当前可见高度走；安全区内边距再把刘海和 Home 指示条让开。
        """
        self.assertPageContains("max-height:min(720px,90dvh)")
        self.assertPageContains("padding-top:max(18px,env(safe-area-inset-top))")
        self.assertPageContains("padding-bottom:max(18px,env(safe-area-inset-bottom))")

    def test_avatar_tiles_do_not_inherit_the_text_link_underline(self):
        """取消规则必须真的压过 `.entitylink:hover`，不能只是写在文件里。

        原来的断言只查子串在不在。取消规则当时排在被覆盖的规则之前，两者特异度
        同为 0-2-0，后来者胜，下划线照旧出现，测试却一直是绿的。
        """
        cancel = ".idcell.entitylink:hover,.mav.entitylink:hover{text-decoration:none}"
        underline = ".entitylink:hover{text-decoration:underline}"
        self.assertPageContains(cancel)
        # 行内文字身份仍然要保留下划线，别把 entitylink 整条规则删掉。
        self.assertPageContains(underline)
        # 取消规则同时靠更高特异度和更靠后的位置压住它；位置这一半在这里守住。
        if self.page.index(cancel) < self.page.index(underline):
            self.fail("头像格子的取消规则排在 .entitylink:hover 之前，会被后者覆盖")

    def test_every_identity_cell_can_carry_its_own_portrait(self):
        self.assertPageContains('item.id?`<img src="/entity-image?kind=performer&id=${item.id}"')
        self.assertPageContains('<img src="/logo?studio=${encodeURIComponent(item.name)}"')

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
            "display:flex;align-items:center;justify-content:center;padding:56px 24px;text-align:center")

    def test_space_does_not_also_scroll_the_page(self):
        self.assertPageContains("if(e.key===' '){\n      e.preventDefault();")

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
        self.assertPageContains("if(e.key==='ArrowDown'||e.key==='ArrowUp'){\n    if(moveSearchActive(")
        self.assertPageContains("options[searchActive].scrollIntoView({block:'nearest'})")
        self.assertPageContains(".searchoption:hover,.searchoption.active{background:var(--hover)}")

    def test_search_active_index_resets_when_the_list_is_rebuilt(self):
        # 列表重建后旧索引会指向不存在的行；输入和重新渲染都必须归零。
        self.assertPageContains("menu.hidden=false;searchActive=-1;")
        self.assertPageContains("$('#q').oninput=()=>{searchActive=-1;")

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
        self.assertPageContains('.toktrack{position:absolute;inset:0;overflow:hidden;border-radius:12px;background:#000')
        self.assertPageContains('.tokbtns{position:absolute;left:calc(100% + 12px);bottom:8px;width:72px')
        self.assertPageContains('width:48px;height:48px;padding:0;border-radius:50%;border:0')
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

    def test_detail_close_disposes_playback_source(self):
        self.assertPageContains("function disposeStage")
        self.assertPageContains("video.pause();video.removeAttribute('src');video.load();video.remove()")
        self.assertPageContains(
            "document.body.classList.remove('detail-open');current=null;activeQueue=null;\n  scheduleStickySurfaces();"
        )
        self.assertPageContains("const closeDetail=()=>{const restore=cloneBarsContext(detailReturnBarsContext)")
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
        self.assertPageContains(
            "else if(g)g.onclick=()=>{vv.hidden=false;g.remove();mountDetailPlayer(it,vv,true)"
        )

    def test_detail_uses_pinned_videojs_and_authoritative_duration(self):
        self.assertPageContains('/vendor/videojs/8.24.0/video.min.js')
        self.assertPageContains('/vendor/videojs/8.24.0/video-js.min.css')

    def test_detail_player_controls_use_two_rows_and_offer_real_quality_levels(self):
        self.assertPageContains(".vwrap .video-js .vjs-big-play-button{left:50%;top:50%;width:3.4em;height:3.4em")
        self.assertPageContains("border-top:.72em solid transparent;border-bottom:.72em solid transparent;border-left:1.05em solid #fff")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar{box-sizing:border-box;left:.8em;right:.8em;bottom:.7em;width:auto;height:7em")
        self.assertPageContains("border-radius:0;background:transparent;backdrop-filter:none")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar>.vjs-play-control,")
        self.assertPageContains("border:1px solid rgba(255,255,255,.2);border-radius:50%;background:rgba(0,0,0,.56)")
        self.assertPageContains(".vwrap .video-js .vjs-control-bar>.vjs-picture-in-picture-control,")
        self.assertPageContains("border-radius:2em 0 0 2em")
        self.assertPageContains("border-radius:0 2em 2em 0")
        self.assertPageContains(".vwrap .video-js .vjs-progress-control{position:absolute;left:1.2em;right:1.2em;top:.45em")
        self.assertPageContains(".vwrap .video-js .vjs-play-progress{background:var(--tungsten)}")
        self.assertPageContains(".vwrap .video-js .vjs-play-progress:before{content:\"\"")
        self.assertPageContains(".vwrap .video-js .vjs-custom-control-spacer{display:block;flex:1 1 auto}")
        self.assertPageContains(".vwrap .video-js .vjs-current-time{display:flex;margin-left:.35em")
        self.assertPageContains(".vwrap .video-js .vjs-duration{display:flex")
        self.assertPageContains("border-radius:0 2em 2em 0")
        self.assertPageContains(".vwrap .video-js.vjs-layout-x-small .vjs-progress-control")
        self.assertPageContains(".vwrap .video-js.vjs-layout-small .vjs-current-time")
        self.assertPageContains("currentTimeDisplay:true,timeDivider:true")
        self.assertPageContains("durationDisplay:true,remainingTimeDisplay:false")
        self.assertPageContains(".vjs-peach-quality [data-player-quality-badge]")
        self.assertPageContains("${icon('settings')}")
        self.assertPageContains("typeof player.qualityLevels==='function'?player.qualityLevels():null")
        self.assertPageContains("activePixels>=2160?'4K':activePixels>=720?'HD':''")
        self.assertPageContains("levels[index].enabled=selected==='auto'||selected===String(index)")
        self.assertPageContains("function mountDetailPlayer(it,video,autoplay,options={})")
        self.assertPageContains("detailPlayer.duration(expected)")
        self.assertPageContains("['loadstart','loadedmetadata','durationchange','error']")
        self.assertPageContains("const d=it.duration||v.duration||0")
        self.assertPageLacks("skipButtons:{backward:appSettings.seekSeconds,forward:appSettings.seekSeconds}")

    def test_player_seek_preview_reuses_contact_sheet_cells_and_online_falls_back_to_time(self):
        self.assertPageContains("function mountPlayerSeekPreview(player,it,options={})")
        self.assertPageContains("preview.dataset.playerSeekPreview='';preview.hidden=true")
        self.assertPageContains("const nextCell=Math.min(8,Math.floor(ratio*9))")
        self.assertPageContains("image.src=`/poster?id=${encodeURIComponent(it.id)}&c=${nextCell}`")
        self.assertPageContains("mountPlayerSeekPreview(detailPlayer,it,{thumbnail:!options.source})")
        self.assertPageContains(".vjs-peach-seek-preview img{width:240px;aspect-ratio:16/9")

    def test_center_player_controls_are_round_and_toggle_play_pause(self):
        self.assertPageContains("function mountPlayerCenterControls(player,seconds=10)")
        self.assertPageContains("root.className='vjs-peach-center-controls';root.dataset.playerCenterControls=''")
        self.assertPageContains('data-center-seek="-${seconds}"')
        self.assertPageContains('data-center-seek="${seconds}"')
        self.assertPageContains("toggle.setAttribute('aria-label',playing?'暂停':'播放')")
        self.assertPageContains("if(player.paused()||player.ended())player.play().catch(()=>{});else player.pause()")
        self.assertPageContains(".vjs-peach-center-controls button{position:relative;width:4.8em;height:4.8em")
        self.assertPageContains("border-radius:50%;display:grid;place-items:center")
        self.assertPageContains('.vjs-peach-center-controls[data-state="pause"] .vjs-peach-center-pause{display:flex}')
        self.assertPageContains("mountPlayerCenterControls(detailPlayer,appSettings.seekSeconds)")

    def test_cards_show_blue_watched_progress_from_play_seconds(self):
        self.assertPageContains("const watchedRatio=!parts&&Number(it.play_seconds)>0&&Number(it.duration)>0")
        self.assertPageContains('class="watchprogress" role="progressbar" aria-label="观看进度"')
        self.assertPageContains(".watchprogress i{display:block;height:100%;background:var(--tungsten)}")

    def test_player_stats_button_matches_the_round_player_controls(self):
        self.assertPageContains(".playerstatsbtn{position:absolute;left:11px;top:11px;z-index:8;width:40px;height:40px")
        self.assertPageContains("border:1px solid rgba(255,255,255,.2);border-radius:50%")
        self.assertPageContains(".playerstatsbtn:hover{background:rgba(0,0,0,.76)")

    def test_player_stats_cover_direct_range_and_future_segmented_streams(self):
        self.assertPageContains('id="playerStatsBtn"')
        self.assertPageContains("HTTP Range")
        self.assertPageContains("bufferedAhead(video)")
        self.assertPageContains("getVideoPlaybackQuality")
        self.assertPageContains("?.vhs?.stats")
        self.assertPageContains("application/vnd.apple.mpegurl")
        self.assertPageContains("/stream/hls/")

    def test_fullscreen_uses_the_entire_player_and_reports_loading_speed(self):
        self.assertPageContains(".vwrap>.video-js.vjs-fullscreen")
        self.assertPageContains("max-height:none!important")
        self.assertPageContains('id="playerNet"')
        self.assertPageContains("function streamSpeedBits(id,session='')")
        self.assertPageContains("function fmtSpeed(bits)")
        self.assertPageContains("加载速度 ${fmtSpeed")

    def test_immerse_mode_has_loading_state_and_full_viewport_cover(self):
        self.assertPageContains('id="tokLoader"')
        self.assertPageContains('class="tokspinner"')
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
        self.assertPageContains("height:40px;padding:0 20px")
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
        """统计、垃圾复核、回收站、人工复核各占一个顶层图标时，侧栏一半是管理入口。

        它们合并到「管理」下的二级导航；URL 保持原样，只是多了一条共用导航条。
        """
        self.assertPageContains("['manage','管理','database']")
        self.assertPageContains("const MANAGE_SECTIONS=[")
        for section in ("'stats','统计'", "'ads','垃圾复核'", "'dupes','重复文件'",
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

    def test_manage_sections_follow_the_order_work_actually_happens_in(self):
        """导航条的顺序就是做事顺序：先收拾库里已有的，再看要往外拿什么。

        关注（原「追更来源」）曾夹在高清版和回收站中间，人工复核掉到最末尾，
        两者都不挨着自己那一组。
        """
        sections = self.page.split("const MANAGE_SECTIONS=[", 1)[1].split("];", 1)[0]
        order = [line.split("'")[1] for line in sections.splitlines() if line.strip().startswith("['")]
        self.assertEqual(
            order, ["stats", "taste", "review", "ads", "dupes", "trash", "follow", "quality"],
            "管理导航的顺序是语义契约：现状 → 复核 → 清理 → 回收站 → 往外拿",
        )

    def test_taste_page_combines_private_exports_and_peach_behavior(self):
        self.assertPageContains("if(path==='/taste'){await openTaste(false);return}")
        self.assertPageContains("/api/taste?window=")
        self.assertPageContains("/api/taste/import")
        self.assertPageContains("/api/taste/refresh")
        self.assertPageContains("/api/taste/source")
        self.assertPageContains("原始 URL、标题与搜索内容不会显示在页面")
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
        self.assertPageContains("sourceTabs('browser',[['tags','Tag']")
        self.assertPageContains("sourceTabs('peach',[['tags','Tag'],['creators','创作者'],['performers','女优']])")
        self.assertPageContains("不自动给 Tag 降权")
        self.assertPageContains("rank.browser_tags||[]")
        self.assertPageContains("rank.peach_performers||rank.performers||[]")
        self.assertPageContains("visual==='domain'")
        self.assertPageContains("avatarInner(row.name,ref,rep,visual)")
        self.assertPageContains("'simpcity.cr':'https://simpcity.cr/data/assets/logo/favicon.png'")
        self.assertPageContains("'hanime1.me':'https://vdownload.hembed.com/image/icon/tab_logo.png")
        self.assertPageContains("'kemono.cr':'https://kemono.cr/assets/favicon-CPB6l7kH.ico'")
        self.assertPageContains("const faviconFallbackUrl=domain=>`https://www.google.com/s2/favicons")
        self.assertPageContains("支持 macOS / Windows 的 Zen、Safari、Firefox、Chrome")
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
        self.assertPageContains("border-right:1px solid var(--line-soft);border-bottom:1px solid var(--line-soft);border-radius:0")
        self.assertPageContains(".tasterank-tag{min-height:54px;padding:8px 10px;border:1px solid var(--line-soft);border-radius:var(--control-radius)")
        self.assertPageContains(".tasterank:is(button):hover{background:var(--overlay-5)}")
        self.assertPageLacks("box-shadow:inset 3px 0 var(--tungsten)")
        self.assertPageContains(".tastesources .insightpanelbody>div{display:grid;grid-template-columns:repeat(3")

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
        for name in ("emptyStateHtml", "loadingDotsHtml", "noteHtml", "progressHtml",
                     "scrollerHtml", "spinnerHtml", "wireScrollers"):
            self.assertPageContains(name)
        self.assertPageContains("from './js/ui-components.js'")
        self.assertPageContains("const NOTE_VARIANTS=new Set(['secondary','warning','error','success'])")
        self.assertPageContains("const role=kind==='error'?' role=\"alert\"':' role=\"note\"'")
        self.assertPageContains("noteHtml(error.message,{variant:'error',label:'同步失败'})")
        self.assertPageContains("noteHtml(error.message,{variant:'error',label:'扫描失败'})")
        self.assertPageContains("noteHtml(error.message||'分析未取得',{variant:'error',label:'分析未取得'})")
        self.assertPageContains('class="geist-note geist-note-error fcheckreport" role="alert"')
        self.assertPageContains('class="geist-banner fwarn"')

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
        self.assertIn("Empty State", rules)
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(".claude/skills/peach-web-ui/SKILL.md", agents)

    def test_taste_drilldown_and_legacy_duration_tags_never_leak_filter_state(self):
        self.assertPageContains("const cleanTagFilter=value=>")
        self.assertPageContains("tag:cleanTagFilter(initialParams.get('tag'))")
        self.assertPageContains("tag:cleanTagFilter(params.get('tag'))")
        self.assertPageContains("state={...state,creator:'',studio:'',tag:'',tag_match:'all'")
        self.assertPageContains("function enterManagementSurface()")
        self.assertPageContains("loadRequestSeq++;listLoading=false;$('#combo').innerHTML=''")

    def test_sidebar_add_controls_have_one_explicit_height(self):
        self.assertPageContains(".sidebaradd .sidebaraddfield{display:grid;grid-template-columns:auto minmax(0,1fr) auto;width:100%;height:42px;box-sizing:border-box;align-items:center;justify-items:start")
        self.assertPageContains(".sidebaraddfield svg:last-child{justify-self:end;color:var(--muted)}")
        self.assertPageContains(".sidebaradd>button{height:42px;box-sizing:border-box}")

    def test_edge_and_drawer_share_one_navigation_dispatch(self):
        """窄栏和抽屉各写一份分支时，抽屉那份漏了追更和播放列表。

        漏掉的入口会落到兜底分支，把 state.state 设成一个后端不认识的值，
        表现就是抽屉里点「在线追更」没反应，点窄栏同一个图标却能进。
        """
        self.assertPageContains("function navTo(k){")
        self.assertPageContains("if(k==='follow'){openFollow();return}")
        self.assertPageContains("if(k==='playlists'){openPlaylists();return}")
        self.assertPageContains(
            "$('#drawer').querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>navTo(b.dataset.nav));")
        self.assertPageContains("e.stopPropagation();navTo(b.dataset.nav)})")
        # 分支只能存在一处；再出现第二份就是下一次漂移。
        self.assertEqual(self.page.count("if(k==='immerse'){openTok();return}"), 1)

    def test_online_assets_use_rss_and_open_the_saved_follow_surface(self):
        self.assertPageContains("online:icon('rss')")
        self.assertPageLacks("online:icon('globe')")
        self.assertPageContains('id="onlineGate"')
        self.assertPageContains("$('#openSavedFollow').onclick=()=>{followFilter='saved';openFollow()}")

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
        self.assertPageContains(".listtitle,.managetitle,.follow>.pagetitle{margin:0 0 12px}")
        self.assertPageContains('id="listTitle" hidden')

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
        """沉浸模式里只看得到文件名。想看标签、相关推荐或改东西，
        原来得先退出再去列表里把它找回来。旁边的创作者一直是可点的，标题不是。
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
        self.assertPageContains("const claimSurface=path=>{surfaceEpoch++;return surfaceToken(path)}")
        self.assertPageContains("const surfaceCurrent=token=>token.epoch===surfaceEpoch&&surfacePath()===token.path")
        self.assertPageContains("const surface=reset?claimSurface(surfacePath()):surfaceToken(surfacePath())")
        self.assertPageContains("if(requestSeq!==loadRequestSeq||!surfaceCurrent(surface))return")
        self.assertPageContains("const surface=claimSurface('/review')")
        self.assertPageContains("if(!surfaceCurrent(surface))return")
        self.assertPageContains("async function restoreRoute(){\n  surfaceEpoch++")
        self.assertPageContains("if(requestSeq!==indexRequestSeq||location.pathname!=='/'+kind)return")
        self.assertPageContains("decodeURIComponent(location.pathname)!==decodeURIComponent(expectedPath)")
        index = self.page.split("async function openIndex", 1)[1].split("const d=await api", 1)[0]
        self.assertIn("showHomeSurfaces();", index)
        self.assertPageContains("if(!$('#stats').hidden){\n    if(location.pathname==='/review'){await openReview(false);return}")

    def test_immersive_close_restores_the_home_surface(self):
        self.assertPageContains("document.body.style.overflow='';showHomeSurfaces();load(true)")

    def test_review_asset_picker_wraps_instead_of_scrolling_sideways(self):
        """一个创作者可能有几十条候选，横向滚动条要一直拉才能看完。"""
        self.assertPageContains(".reviewasset-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr))")
        self.assertPageContains(".reviewasset.picked{opacity:1;outline:2px solid var(--tungsten)")
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
        """首页原来只看 state.state，进管理区和索引页时它仍然亮着，两个入口同时高亮。"""
        self.assertPageContains("if(k==='performers'||k==='tags')return path==='/'+k")
        self.assertPageContains("if(k==='')return path==='/'&&!manageSection()&&!state.state")
        self.assertPageContains("buildEdge();     // 顶层高亮跟随管理区")

    def test_manage_surfaces_hide_the_home_rails(self):
        """回收站和垃圾复核是行政列表，不该顶着首页的人物/厂牌横条。

        `showHomeSurfaces` 会先把横条恢复出来，所以隐藏必须排在它之后，否则被立刻覆盖。
        """
        self.assertPageContains("if(current){$('#tiers').style.display='none';$('#tagbar').style.display='none'}")
        home = self.page.split("function showHomeSurfaces(){", 1)[1].split("}", 1)[0]
        self.assertLess(home.index("$('#tiers').style.display=''"), home.index("buildManageBar()"),
                        "buildManageBar 必须排在恢复首页横条之后，否则隐藏会被覆盖")

    def test_ads_queue_count_does_not_stick_and_disposal_reports_failures(self):
        """垃圾复核是处置队列；计数行不跟随滚动，写入冲突也不能伪装成成功。"""
        self.assertPageContains("countRow.classList.toggle('manage-static',staticManageCount)")
        self.assertPageContains("if(staticManageCount)countRow.classList.remove('is-stuck')")
        self.assertPageContains(".count.manage-static{position:relative;top:auto;z-index:1}")
        self.assertPageContains("if(!response.ok){")
        self.assertPageContains("throw new Error(detail||`请求失败（${response.status}）`)")
        self.assertPageContains("catch(error){alert(`操作失败：${error.message||'未知错误'}`)}")
        self.assertPageContains("wireCards($('#grid'),openResourceCard);wireResourceCardActions($('#grid'));paintSelection();return")
        self.assertPageContains("b.dataset.kind==='dispose'&&r.disposal==='trash'&&state.state==='ads'")

    def test_junk_review_and_trash_render_every_physical_resource_type(self):
        """图片、网址快捷方式等不能复用视频播放器，但必须可预览、回收和还原。"""
        self.assertPageContains("const RESOURCE_MEDIUM_LABEL={image:'图片',audio:'音频',archive:'压缩包',other:'其它文件'}")
        self.assertPageContains("function resourceCardHtml(it)")
        self.assertPageContains("String(it.name||'').toLowerCase().endsWith('.url')?'网址快捷方式'")
        self.assertPageContains('src="/photo-thumb?id=${it.id}"')
        self.assertPageContains('data-resource-operation="${action}"')
        self.assertPageContains("await api('/api/batch',{method:'POST',body:JSON.stringify({ids:[+card.dataset.id],operation})})")
        self.assertPageContains("if(it&&(!it.medium||it.medium==='video'))wireHover(el,it)")
        self.assertPageContains("state.state==='trash'?d.items.map(resourceCardHtml).join('')")
        self.assertPageContains("wireCards($('#grid'),state.state==='trash'?openResourceCard:undefined)")
        self.assertPageContains("if(state.state==='trash')wireResourceCardActions($('#grid'))")
        self.assertPageContains("const emptyTrash=$('#emptyTrash');")
        self.assertPageContains("if(emptyTrash)emptyTrash.onclick=async(e)=>{")
        self.assertPageContains("视频、图片和网址快捷方式都只进入复核，不会直接删除")
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
        self.assertPageContains("metricTab('disk','系统盘可用'")

    def test_duplicate_and_trash_descriptions_share_one_page_lede(self):
        self.assertPageContains('class="pagelede mono" id="manageLede" hidden')
        self.assertPageContains(".pagelede{margin:0 0 16px;color:var(--muted);font-size:var(--fs-sm);line-height:1.5}")
        self.assertPageContains("paintManageLede(`${d.total} 组 · ${d.files} 个文件 · 可回收 ${fmtSize(d.reclaimable)}`)")
        self.assertPageContains("if(trash)paintManageLede(`${total.toLocaleString()} 个符合 · 显示 ${n}`)")
        self.assertPageContains(".count.count-actions-only:empty{display:none}")
        self.assertPageLacks('class="dupsum mono"')

    def test_returning_home_from_any_surface_moves_the_highlight(self):
        """点回首页时路径还停在 /review 之类上，navOn('') 仍然为假，高亮不切换。"""
        self.assertPageContains("route(homePath());")
        # 抽屉和窄栏已经共用 navTo，这一句只应该存在一处；
        # 两份副本正是当初把追更入口漏在抽屉里的原因。
        self.assertEqual(self.page.count("function navTo(k){"), 1,
                         "导航分支只能留一份 navTo")
        self.assertPageContains("if(k==='')state.jav='';")
        self.assertPageContains("state.state=k}\n  route(homePath());")

    def test_ads_icon_matches_the_lucide_stroke_style(self):
        """图标库里没有表示广告的图形，自绘的感叹号必须和其余图标同风格。"""
        self.assertPageContains('<symbol id="i-alert" viewBox="0 0 24 24">')
        self.assertPageContains("['ads','垃圾复核','alert']")

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
        self.assertPageContains(".edge .srcrow button{width:52px;height:44px")

    def test_beeg_evidence_driven_surfaces_are_translucent_and_rail_is_continuous(self):
        self.assertPageContains(".brandpill{")
        self.assertPageContains("background:var(--overlay-5);border:1px solid var(--border-10)")
        self.assertPageContains("border:1px solid var(--border-15);\n  border-radius:var(--pill-radius);background:transparent")
        self.assertPageContains("--overlay-5:rgba(245,250,255,.05)")
        self.assertPageContains("--border-15:rgba(245,250,255,.15)")
        # 窄栏原本无边框、与内容区连成一片。用户 2026-08-26 明确要求加分割线：
        # 两边背景太接近，看不出左边那一条到哪里为止。其余取证结论不变，只改这一条。
        self.assertPageContains("border-right:1px solid var(--line-soft)")
        self.assertPageContains("['performers','艺人','user-round']")
        self.assertPageContains("['tags','标签','tags']")

    def test_entity_profile_hides_home_facets_and_renders_context(self):
        self.assertPageContains("body.entity-open #tiers,body.entity-open #tagbar,")
        self.assertPageContains('src="/logo?studio=${encodeURIComponent(d.canonical_name)}"')
        self.assertPageContains('class="entitytags"')
        self.assertPageContains('class="relatedpeople"')
        self.assertPageContains("data-related-performer")
        profile = self.page[self.page.index("async function openEntity("):]
        self.assertLess(profile.index("<div class=\"entityhero\">"),
                        profile.index('class="relatedpeople"'))
        self.assertLess(profile.index('class="relatedpeople"'),
                        profile.index('class="entitytags"'))
        self.assertNotIn("关联艺人", profile)
        self.assertNotIn("相关标签", profile)

    def test_every_home_navigation_restores_the_shared_facets(self):
        self.assertPageContains("function showHomeSurfaces()")
        self.assertPageContains("$('#tiers').style.display='';$('#tagbar').style.display=''")
        self.assertPageContains("function closeStats(push=true){if(push)route('/');showHomeSurfaces();load(true)}")
        self.assertPageContains("async function load(reset)")
        self.assertPageContains("showHomeSurfaces();\n  if(reset){offset=0;renderedPartGroups.clear()}")
        self.assertPageContains("showHomeSurfaces();disposeStage(false)")

    def test_entity_tags_filter_inside_the_current_entity_page(self):
        self.assertPageContains("ENTITY_FILTER_KEYS.forEach(key=>{if(filters[key]&&key!==kind&&key!=='sort')p.set(key,filters[key])})")
        self.assertPageContains("async function updateEntityCollection")
        self.assertPageContains("updateEntityCollection(kind,name,nextFilters,true)")
        self.assertPageContains("renderEntityCollection(kind,name,items,filters)")
        self.assertPageLacks("openEntity(kind,name,true,next)")
        self.assertPageLacks(
            "document.body.classList.remove('entity-open');$('#index').hidden=true;state.tag=b.dataset.entityTag"
        )

    def test_every_entity_video_collection_reuses_applicable_sort_controls(self):
        self.assertPageContains("const ENTITY_LABELS={performer:'艺人',studio:'厂牌',creator:'创作者',series:'系列'}")
        self.assertPageContains('class="batchaction entitybatch"')
        self.assertPageContains('data-entity-sort="${key}"')
        self.assertPageContains("p.set('sort',filters.sort||'new')")
        self.assertPageContains("if(filters.sort==='seed')p.set('seed',state.seed)")
        self.assertPageContains("updateEntityCollection(kind,name,{...filters,sort},true)")
        self.assertPageContains("key==='sort'&&filters[key]==='new'")
        self.assertPageContains(".entitycollectionhead .sorts")
        # 照片瀑布流没有视频排序语义，切换后直接渲染照片，不复用作品头。
        self.assertPageContains("if(media==='photos'){renderPhotoWall(kind,name,filters,entityPhotos);return}")

    def test_entity_profile_uses_display_aliases_not_search_identity_aliases(self):
        self.assertPageContains("(d.display_aliases||[]).length")
        self.assertPageLacks("(d.aliases||[]).length?'别名")

    def test_jav_cards_prefer_the_canonical_performer_over_legacy_creator_text(self):
        self.assertPageContains("const primaryCreator=it.is_jav&&performer?'':it.creator")
        self.assertPageContains("const identity=primaryCreator?{kind:'creator',name:primaryCreator}")
        self.assertPageContains("const coStarred=performers.length>1&&!primaryCreator")
        self.assertPageContains("return (it.is_jav&&performer?performer:it.creator)||performer")

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
        self.assertPageContains("more._observer=new IntersectionObserver")
        self.assertPageContains("more.hidden=!entityCollectionPage.has_more")

    def test_mix_and_persistent_playlists_share_the_routed_side_queue(self):
        self.assertPageContains('class="card mixcard" data-mix-seed=')
        self.assertPageContains("cards.splice(7,0,mixCardHtml(seed))")
        self.assertPageContains(".mixstack::before,.mixstack::after")
        # Mix 是同一网格里的同级卡片，JAV 大图不能让它单独掉回 16:9；有封面时
        # 也应和普通作品卡共用同一张官方封套，而不是永远显示视频接触表。
        self.assertPageContains("const useCover=jav&&layout!=='preview'&&it.has_cover;")
        self.assertPageContains("const ar=jav&&layout==='big'?COVER_FRONT_RATIO:16/9;")
        self.assertPageContains('<div class="mixstack"><div class="pic" style="--card-ratio:${ar}">')
        self.assertPageContains("? coverImage(it,layout)")
        self.assertPageContains('<span class="mixbadge">${icon(\'play\')}Mix</span>')
        self.assertPageContains("async function openMix(seedId,itemId=seedId,push=true)")
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
        self.assertPageContains("route(section==='trash'?'/trash':'/')")
        self.assertPageContains("if(path==='/trash')")
        self.assertPageContains("/api/trash/empty")

    def test_multipart_releases_use_a_distinct_group_card_and_queue(self):
        self.assertPageContains("function collapseMultipartItems(items)")
        self.assertPageContains("renderedPartGroups.clear()")
        self.assertPageContains("data-part-seed")
        self.assertPageContains('<span class="partbadge">${parts.count} 卷</span>')
        self.assertPageContains("async function openParts(seedId,itemId=seedId,push=true)")
        self.assertPageContains("api('/api/parts?id='+seedId)")
        self.assertPageContains("title:`分卷 · ${group.title}`")
        self.assertPageContains("route(`/parts/${seedId}/${chosen}`)")
        self.assertPageContains("queue.kind==='parts'?`${queue.items.length} 卷`")
        self.assertPageContains("queueContext.kind==='parts'?openParts")
        self.assertPageContains("if(parts[0]==='parts'")
        self.assertPageContains(".partstack::before,.partstack::after")
        self.assertPageLacks("Mix · ${group.title}")

    def test_filter_and_sort_rows_stay_visible_in_both_scroll_directions(self):
        self.assertPageContains("--filterH:58px")
        self.assertPageContains(".tagbar{position:sticky;top:var(--topH)")
        self.assertPageContains(".count{position:sticky;top:calc(var(--topH) + var(--filterH))")
        self.assertPageContains("border-bottom:1px solid transparent;background:transparent")
        self.assertPageContains("background:transparent;border-bottom:1px solid transparent")
        self.assertPageContains(".tagbar.is-stuck,.count.is-stuck{background:color-mix(in srgb,#020408 84%,transparent)")
        self.assertPageContains("background:color-mix(in srgb,#020408 84%,transparent)")
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

    def test_entity_collection_posters_and_titles_open_item_details(self):
        self.assertPageContains('class="cardopenhit" data-open')
        self.assertPageContains('<button class="t cardtitle" data-open>')
        self.assertPageContains("const openCard=id=>onClick?onClick(id):(it?.part_group?openParts")
        self.assertPageContains("if(e.target.closest('[data-open]')){e.stopPropagation();openCard(+el.dataset.id)")
        self.assertPageContains(".cardopenhit{position:absolute;inset:0;z-index:3")
        self.assertPageContains("el.querySelectorAll('[data-open]').forEach(opener=>")
        self.assertPageContains("opener.dataset.openWired='1'")
        self.assertPageContains(".hovertools button{pointer-events:none")
        self.assertPageContains(".card.longhover .seektools button,.card:hover .later-tools button{pointer-events:auto}")
        self.assertPageContains("section.querySelector('h3').textContent=`视频 ·")
        self.assertPageLacks("的馆藏作品 ·")

    def test_remote_hover_previews_do_not_stream_full_media(self):
        self.assertPageContains("if(it.location!=='local')")
        self.assertPageContains("el.dataset.hoverMode=it.location==='local'?'video':'frames'")
        self.assertPageContains("function releaseHoverPreviews(root=document,except=null)")
        self.assertPageContains("releaseHoverPreviews(document,el)")
        self.assertPageContains("window.addEventListener('pagehide',()=>releaseHoverPreviews())")
        self.assertPageContains("if(document.hidden)releaseHoverPreviews()")
        self.assertPageContains("if(reset)releaseHoverPreviews($('#grid'))")
        self.assertPageContains("releaseHoverPreviews($('#srow'))")

    def test_detail_close_returns_to_the_collection_that_opened_it(self):
        self.assertPageContains("detailReturnPath='/'")
        self.assertPageContains("if(push)detailReturnPath=location.pathname+location.search")
        self.assertPageContains("if(push)route(detailReturnPath||'/')")

    def test_entity_profile_uses_logo_links_without_a_redundant_back_row(self):
        self.assertPageContains("const faviconUrl=url=>")
        self.assertPageContains('class="entitylinkicon"')
        self.assertPageContains('class="entitylinklabel"')
        self.assertPageContains("img.dataset.studio&&!img.dataset.fallback")
        self.assertPageLacks('<span class="mono" style="color:var(--muted)">${labels[kind]||kind}资料页</span>')

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
        self.assertPageContains('.meta .who{color:var(--tungsten);min-width:0;max-width:100%;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap')

    def test_every_card_kind_has_one_fixed_ratio(self):
        """三类卡片各自一个固定比例，卡片之间不能高低不齐。

        竖屏曾经按每条视频的实际宽高算，素材从 0.5 到 0.9 都有，竖屏条和竖屏网格
        因此参差不齐。这段代码写下后一直没生效（`.pic` 写死 16/9），接上
        `--card-ratio` 才暴露出来。比例不同的用 contain 上下留黑边。
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
        self.assertPageContains("route(section==='trash'?'/trash':'/')")
        self.assertPageContains("if(path==='/trash'){")
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
        self.assertPageLacks("['copyright','作品']")
        self.assertPageLacks("['artist','人物']")
        self.assertPageLacks("['character','角色']")
        self.assertPageContains("key==='all'||Number(d.categories?.[key]||0)>0")
        self.assertPageContains("'1080P':'1080p'")
        self.assertPageContains("'60fps':'60FPS'")
        self.assertPageContains("'AI去码':'AI解码'")
        self.assertPageContains("'足交':'脚交'")
        self.assertPageContains("'骑乘':'骑乘位'")
        self.assertPageContains("category=params.get('category')")

    def test_state_routes_tag_multiselect_and_header_capabilities_are_explicit(self):
        self.assertPageContains("const STATE_ROUTES={fresh:'/unseen',later:'/watch-later',flagged:'/flagged'}")
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
        # 默认关闭：localStorage 记 '1' 才开，没动过的会话一律不遮。
        self.assertPageContains("applyCensor(localStorage.getItem(CENSOR_KEY)==='1')")
        # 全站按元素类型盖：内容 img / video / videojs 海报层一个不落。
        self.assertPageContains("body.censor img,body.censor video,body.censor .vjs-poster{\n  filter:blur(30px) saturate(.3) brightness(.6)}")
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
        self.assertPageContains("document.body.dataset.surface=new URL(path,location.origin).pathname")
        # 导航激活态随路由重算：抽屉/窄栏按钮是 buildBars 时一次性画的，
        # 管理页不跑 buildBars，不重算就会停留在上一个页面的按下态。
        self.assertPageContains("paintNav();")
        self.assertPageContains("function paintNav(){")
        self.assertPageContains(".edge button[data-nav],#drawer .dnav button[data-nav]")
        # 组合标签：pill 按按下态逐个命中；combo 芯片显示显示名、操作用原始 key。
        self.assertPageContains("String(filterState.tag||'').split(',').includes(String(t.k))")
        self.assertPageContains("${esc(tagLabel(t))} <b data-untag=\"${esc(t)}\">✕</b>")
        # fwarn 提供 dismiss（会话内记忆），关闭钮样式与 toast 关闭钮同量纲。
        self.assertPageContains("data-fwarn-dismiss")
        self.assertPageContains("sessionStorage.setItem('peach-fwarn-dismissed','1')")
        self.assertPageContains(".fwarn .wclose,.fcheckreport .wclose{flex:none;width:24px;height:24px;margin-left:auto;padding:0;border:0;")
        # 报告条：danger 语义（红发丝边 + 微红底），不再是左侧粗条。
        self.assertPageContains("background:color-mix(in srgb,var(--drop) 7%,transparent);\n  border:1px solid color-mix(in srgb,var(--drop) 30%,transparent);")
        self.assertPageLacks("border-left:2px solid var(--drop)")
        # 来源行状态徽章（ok 绿 tint / 失败红 tint / 未检查灰）。
        self.assertPageContains('<span class="sbadge ${badge}" title="${esc(stateTitle)}"><i aria-hidden="true"></i>')
        self.assertPageContains(".sbadge i{width:6px;height:6px;border-radius:50%;background:var(--muted);flex:none}")
        self.assertPageContains(".sbadge.ok i{background:var(--success)}")
        self.assertPageContains(".sbadge.error i{background:var(--drop)}")
        # 清空回收站：danger 语义色。
        self.assertPageContains('class="batchaction danger" id="emptyTrash"')
        self.assertPageContains(".count .sorts .batchaction.danger{background:var(--drop);border-color:var(--drop);color:#fff;font-weight:500}")
        # Geist 菜单：触发器和每个选项都有入口图标，菜单内部滚动且不加猜测动画。
        self.assertPageContains('data-sidebar-add-trigger aria-haspopup="listbox" aria-expanded="false"')
        self.assertPageContains('role="option" data-sidebar-add-option=')
        self.assertPageContains(".sidebaraddmenu{position:absolute;z-index:4;left:0;right:0;bottom:calc(100% + 6px);max-height:min(312px,48vh);overflow:auto;overscroll-behavior:contain")
        self.assertPageContains("if(e.key==='Escape'){e.preventDefault();closeAddMenu();addTrigger.focus();return}")
        # 设置分组用框体隔开（用户回执）：每组建卡，分隔线顶格到卡边，
        # 标题字号与行内边距对齐 Vercel 后台设置卡。
        self.assertPageContains(".settinggroup{margin:16px 0 0;border:1px solid var(--line-soft);border-radius:12px;")
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
        self.assertPageContains(
            ".pagetitle,.listtitle,.managetitle,.index .ihead h2,.playlistpage h2{"
            "\n  font-size:var(--fs-3xl);line-height:1.15;letter-spacing:-.01em;font-weight:650}")
        # 全站字体栈必须有 CJK sans 兜底：Bahnschrift/Consolas 都没有中文字形，
        # generic sans-serif/monospace 在中文 Chrome 的默认可能落到宋体。
        css = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text(
            encoding="utf-8")
        for i, line in enumerate(css.splitlines(), 1):
            if "font-family" not in line or "inherit" in line:
                continue
            if "sans-serif" in line or "monospace" in line:
                self.assertIn("YaHei", line, f"app.css:{i} 字体栈缺 CJK 兜底：{line.strip()[:90]}")

    def test_taste_dashboard_is_persisted_and_refreshed_without_blocking(self):
        """口味仪表跨页面刷新复用旧结果，过期更新也不阻塞打开页面。

        口味数据来自浏览器历史聚合，24 小时内无需重读。过期时仍先显示
        持久缓存，再后台更新；请求带序号，慢响应不能覆盖别的窗口或页面。
        """
        self.assertPageContains("const TASTE_CACHE_KEY='peach-taste-dashboard-v2',TASTE_CACHE_FRESH_MS=24*60*60*1000;")
        self.assertPageContains("let tasteWindow='all',tasteEvidence='browser',tasteDimension={browser:'tags',peach:'tags'};")
        self.assertPageContains("let tasteCache=readTasteCache(),tasteRequest=0;")
        self.assertPageContains("localStorage.getItem(TASTE_CACHE_KEY)")
        self.assertPageContains("localStorage.setItem(TASTE_CACHE_KEY,JSON.stringify(Object.fromEntries(tasteCache)))")
        self.assertPageContains("const cachedEntry=tasteCache.get(tasteWindow),cached=cachedEntry?.dashboard;")
        self.assertPageContains("const cacheFresh=cached&&Date.now()-cachedEntry.at<TASTE_CACHE_FRESH_MS;")
        self.assertPageContains("if(cached)renderTaste(cached);")
        self.assertPageContains("if(!cacheFresh)")
        self.assertPageContains("void api('/api/taste?window='+requestedWindow).then(data=>")
        self.assertPageContains("tasteCacheSet(requestedWindow,data);")
        self.assertPageContains("if(request===tasteRequest&&tasteWindow===requestedWindow&&surfaceCurrent(surface))renderTaste(data)")
        self.assertPageContains("if(!cached&&request===tasteRequest&&surfaceCurrent(surface))")
        # 三个写路径都更新缓存，别让缓存变陈旧。
        self.assertPageContains("tasteCacheSet(tasteWindow,result.dashboard);renderTaste(result.dashboard)")
        self.assertPageContains("tasteWindow='all';tasteCacheSet('all',payload.dashboard);renderTaste(payload.dashboard)")

    def test_no_page_grows_its_own_back_control(self):
        """索引页原本有个返回按钮，现在顶栏入口本身就是返回路径。

        这条守的是「不要再长回来」，以及别留下没人用的图标与样式——
        唯一使用者删掉后，`i-arrow-left` symbol 和 `.backbtn` 都成了死代码。
        """
        self.assertPageLacks("${icon('arrow-left')}")
        self.assertPageLacks('id="i-arrow-left"')
        self.assertPageLacks(".backbtn")
        self.assertPageLacks("${icon('chevron-left')}<span>返回</span>")

    def test_climax_uses_pinned_healthicons_symbol(self):
        self.assertPageContains('id="i-sperm"')
        self.assertPageContains("icon('sperm')")

    def test_settings_own_useful_experience_preferences(self):
        self.assertPageContains("const DEFAULT_SETTINGS={batchSize:60,defaultSort:'new'")
        self.assertPageContains('id="settingsPanel"')
        self.assertPageLacks('id="rotateSetting"')
        self.assertPageContains("appSettings.hoverDelaySeconds")
        self.assertPageContains("appSettings.batchSize")
        self.assertPageContains("appSettings.defaultSort")
        self.assertPageContains("appSettings.seekSeconds")
        self.assertPageContains("appSettings.searchHistoryLimit")
        self.assertPageContains("appSettings.relatedLimit")
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
        self.assertPageContains("const OPTIONAL_SIDEBAR_KEYS=['stats','review','ads','dupes','trash','follow-manage','quality']")
        self.assertPageContains("if(DIRECT_MANAGE_NAV[k]){openManage(DIRECT_MANAGE_NAV[k]);return}")
        self.assertPageContains(".settingscard{display:flex;flex-direction:column;width:min(520px,100%);max-height:min(720px,90vh);max-height:min(720px,90dvh);overflow:hidden")
        self.assertPageContains(".settingsscroll{flex:1;min-height:0;overflow-y:auto")
        self.assertPageLacks('id="ambientSetting"')
        self.assertPageContains("color:#f5f7fa;color-scheme:dark")

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
        self.assertPageContains("视频 ID / 会话")
        self.assertPageContains("/api/quality-goal")
        self.assertPageContains('id="betterVersion"')
        self.assertPageLacks("prompt('要找哪种更好版本？")
        self.assertPageContains("body:JSON.stringify({id:it.id,wanted})")
        self.assertPageLacks('id="closeStage">收起')

    def test_better_version_targets_have_a_management_page(self):
        self.assertPageContains("['quality','高清版','sparkles']")
        self.assertPageContains("if(path==='/quality-goals')return 'quality'")
        self.assertPageContains("async function openQualityGoals(push=true)")
        self.assertPageContains("/api/quality-goals?limit=200")

    def test_review_page_is_a_separate_management_layer(self):
        self.assertPageContains("route('/review')")
        self.assertPageContains("const REVIEW_LABELS={metadata_fields:'元数据字段',creator_tags:'创作者标签'")
        self.assertPageContains("candidate_key:candidateKey")
        self.assertPageContains("class=\"metadatacandidate\"")
        self.assertPageContains("candidate.official?' · 官方优先':''")
        self.assertPageContains("/api/review/decision")
        self.assertPageContains("if(path==='/review')")
        self.assertPageContains('class="revieworigin"')
        self.assertPageContains('data-review-open-item="${row.asset_id}"')
        self.assertPageContains("openItem(+button.dataset.reviewOpenItem)")

    def test_jav_release_date_is_visible_in_detail(self):
        self.assertPageContains("发行 ${esc(it.release_date)}")

    def test_duplicates_page_is_a_management_section(self):
        self.assertPageContains("['dupes','重复文件','hard-drive']")
        self.assertPageContains("if(path==='/duplicates')return 'dupes'")
        self.assertPageContains("if(section==='dupes'){openDuplicates();return}")
        self.assertPageContains("async function openDuplicates(push=true)")

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
                '<button data-middle-truncate data-quality-open=',
                'id="photoDetailTitle" data-middle-truncate',
                '<div><b data-middle-truncate title="${esc(asset.name||\'\')}"',
                '<div><b data-middle-truncate title="${esc(row.asset_name||\'\')}"',
                '<b data-middle-truncate>${esc(media.name)}</b>',
                '<b data-middle-truncate>${esc(x.name)}</b>',
                'class="t resourcecardtitle" data-middle-truncate'):
            self.assertPageContains(consumer)
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
        self.assertPageContains(".qualityitem h3 button{display:block;width:100%")
        self.assertPageLacks(".qualityitem h3 button{max-width:100%;border:0;background:transparent;padding:0;color:inherit;text-align:left;cursor:pointer;overflow-wrap:anywhere;display:-webkit-box")

    def test_every_end_truncation_selector_is_explicitly_reviewed(self):
        """新增 CSS 省略必须先决定它是语义文本，还是应改用 MiddleTruncate。"""
        reviewed_end_selectors = {
            ".alphatag span:first-of-type", ".av .nm", ".entitylinklabel",
            ".entitytags button", ".fauthor .fsource.frow>b", ".fauthorhead b",
            ".fchip", ".folderfoot .fmeta", ".fpickactions [data-pick-state]",
            ".frow>b", ".fvkind", ".idname", ".kv>span:first-child",
            ".meta .t", ".meta .who", ".mixcopy b,.mixcopy span",
            ".mixitemtext [data-truncate-end]", ".mixqueuehead h2",
            ".playerstats dd", ".relatedperson .nm", ".reviewentity b",
            ".reviewitem h4", ".searchoption span",
            ".sgrid.mixgrid>.mixqueue .mixqueuehead span", ".sidebarorderlabel>b",
            ".insighttablerow span", ".metricstrip small,.tastesummary>small",
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
        self.assertPageContains("const runtime=await api('/healthz')")
        self.assertPageContains("reviewRuntime=runtime;reviewData=next")
        self.assertPageContains("正在显示写入端的实时复核队列")
        self.assertPageContains("前往写入端复核")
        self.assertPageContains("canApprove&&!locked")
        self.assertPageContains("${locked?' disabled':''}>跳过")

    def test_index_pages_drop_the_home_filter_bars_and_back_button(self):
        # 艺人/标签索引和资料页一样是「专注看某一类实体」的表面。
        self.assertPageContains(
            "body.entity-open #tiers,body.entity-open #tagbar,\nbody.index-open #tiers,body.index-open #tagbar{display:none}")
        self.assertPageLacks('id="iClose"', "顶栏入口本身就是返回路径")
        self.assertPageLacks("$('#iClose').onclick")

    def test_beeg_photo_toggle_precedes_tags_and_only_appears_with_images(self):
        self.assertPageContains('id="i-pics" viewBox="0 0 16 16" fill="currentColor" stroke="none"')
        self.assertPageContains('class="entitymediatoggle" type="button" data-media-toggle')
        self.assertPageContains("const mediaToggle=photoCount?")
        self.assertPageContains('<div class="entitytags">${mediaToggle}${tags}</div>')
        self.assertPageContains("button.hidden=!photos")
        self.assertPageContains("selected?'videos':'photos'")
        self.assertPageContains(".entitytags .entitymediatoggle{display:grid;place-items:center;flex:0 0 32px;width:32px;height:32px")
        self.assertPageLacks('<div class="mediatabs" hidden></div>')

    def test_photo_wall_uses_cached_thumbnails_and_only_the_lightbox_reads_originals(self):
        # 瀑布流铺原图等于一屏付几十兆 PikPak 流量；缩略图由服务端缓存一次。
        self.assertPageContains('<img src="/photo-thumb?id=${item.id}"')
        self.assertPageContains('<img src="/photo?id=${item.id}"')
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
        self.assertPageContains('<div class="entitycollectionhead"><h3></h3><span class="sorts">')
        self.assertPageContains("${javActive()?javLayoutButtons():''}")
        self.assertPageContains("wireJavLayoutButtons(section)")
        self.assertPageContains("renderEntityCollection(kind,name,{...entityCollectionPage,items:[...entityCollectionPage.items]}")
        self.assertPageContains('<fieldset class="javlayout"><legend class="sr-only">JAV 卡片版式</legend>')
        self.assertPageContains('type="radio" name="jav-layout" value="${k}" data-jav-layout')
        self.assertPageContains("${k===javLayout()?'checked':''}")
        self.assertPageContains("b.onchange=()=>{if(b.checked)setJavLayout(b.value)}")
        self.assertPageContains(".javlayout label:has(input:checked){background:var(--surface);color:var(--tungsten)")
        self.assertPageContains("let entityRequestSeq=0,entityJavLayout=false")
        self.assertPageContains("(items.items||[]).some(item=>item.is_jav)")
        self.assertPageContains("return state.jav==='1'||entityJavLayout")
        self.assertPageContains("const jav=javActive()&&!!it.is_jav,layout=javLayout()")

    def test_photo_lightbox_loads_swiper_lazily_with_thumbs_and_keyboard(self):
        self.assertPageContains("'/vendor/swiper/14.2.0/swiper-bundle.min.js'")
        self.assertPageContains("thumbs:{swiper:strip}")
        self.assertPageContains("keyboard:{enabled:true}")
        self.assertPageContains(".photolight{position:fixed;inset:0;z-index:200;background:#000")
        self.assertPageLacks('<script src="/vendor/swiper', "灯箱才用得上，不进首屏")

    def test_lightbox_image_is_capped_by_height_not_only_width(self):
        """竖图必须整张收进灯箱，不能上下被裁掉。

        `max-height:100%` 只在祖先高度确定时才算数，而 grid 子项的自动最小尺寸
        （min-height:auto）是「不得小于内容」：3072x4096 按宽度铺开有 2533px 高，
        那个下限会盖掉 height:100%，容器被撑成图片原高，max-height 再按它算就等于
        没限制。所以从 slide 到图片本身每一层都要显式写 min-height:0。
        """
        self.assertPageContains(
            ".photolight .photomain{min-height:0;height:100%;width:100%}")
        self.assertPageContains(
            ".photolight .photomain .swiper-slide{height:100%;min-height:0;")
        self.assertPageContains(
            ".photolight .photomain .swiper-zoom-container{width:100%;height:100%;"
            "min-height:0;min-width:0;")
        self.assertPageContains(
            ".photolight .photomain img{max-width:100%;max-height:100%;"
            "min-width:0;min-height:0;")

    def test_lightbox_nav_classes_avoid_the_generic_next_rule(self):
        """翻页按钮不能叫 `.next`：详情页「接下来」那块用的就是无前缀 `.next`。

        两者同为 0-1-0 特指度且 `.next` 写在后面，padding、border-top 和背景色会
        整块盖过来，图标被挤得偏右下——实测偏移 5px/2px。
        """
        self.assertPageContains('class="photonav back"')
        self.assertPageContains('class="photonav fwd"')
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
            ".mediatabs button svg{width:16px;height:16px;stroke:currentColor;fill:none",
            ".photoback svg{width:15px;height:15px;stroke:currentColor;fill:none",
            ".photoclose svg{width:20px;height:20px;stroke:currentColor;fill:none",
            ".photonav svg{width:24px;height:24px;stroke:currentColor;fill:none",
        ):
            self.assertPageContains(rule)

    def test_lightbox_offers_wheel_paging_and_an_explicit_zoom_bar(self):
        # zoom 模块只有 in/out/toggle，没有「缩到这个倍数」；`in()` 用的就是
        # maxRatio，所以先改上限再 in 等于设定值。
        self.assertPageContains("mousewheel:{enabled:true,forceToAxis:false}")
        self.assertPageContains("main.params.zoom.maxRatio=scale;main.zoom.in()")
        self.assertPageContains('<input type="range" min="1" max="${ZOOM_MAX}"')
        # zoomChange 的第一个参数是 swiper 实例，倍数在第二个；接错了写进 NaN。
        self.assertPageContains("main.on('zoomChange',(_swiper,scale)=>")
        # 文本字形受字体基线影响，会让圆按钮里的 +/- 肉眼偏上或偏下；SVG 几何才稳定居中。
        self.assertPageContains('data-zoom-step="-1" aria-label="缩小">${icon(\'minus\')}')
        self.assertPageContains('data-zoom-step="1" aria-label="放大">${icon(\'plus\')}')
        self.assertPageContains(".photozoom button svg{width:15px;height:15px;display:block;")

    def test_lightbox_photo_detail_reveals_by_asset_id_without_leaking_a_path(self):
        self.assertPageContains('aria-label="图片详情" title="图片详情">${icon(\'info\')}</button>')
        self.assertPageLacks("${icon('info')}<span>图片详情</span>",
                             "详情入口只显示圆圈 i，不再加文字按钮外框")
        self.assertPageContains('aria-expanded="false" aria-controls="photoDetail"')
        self.assertPageContains('aria-haspopup="dialog"')
        self.assertPageContains('<section class="photodetail" id="photoDetail" role="dialog" aria-modal="false"')
        self.assertPageContains('aria-labelledby="photoDetailTitle" hidden>')
        self.assertPageContains("LOC[item.location]||item.location||'来源未知'")
        self.assertPageContains("size<1024*1024?`${Math.max(1,Math.round(size/1024))} KB`")
        self.assertPageContains("reveal.dataset.photoReveal=String(item.id)")
        self.assertPageContains("revealSource(Number(reveal.dataset.photoReveal),status,{toastSuccess:true,button:reveal})")
        self.assertPageContains("toast('已在资源管理器中显示')")
        self.assertPageContains(".toasts{position:fixed;right:16px;bottom:22px;z-index:var(--layer-popover)")
        self.assertPageContains("button.innerHTML=`${spinnerHtml('正在定位')}<span>${esc(label)}</span>`")
        self.assertPageContains("if(activeLightbox?.detail?.isOpen()){activeLightbox.detail.dismiss(true);return}")
        self.assertPageContains("if(returnFocus&&document.contains(toggle))toggle.focus()")
        self.assertPageContains("queueMicrotask(()=>reveal.focus())")
        self.assertPageContains("const dismissOutside=target=>{if(panel.hidden||toggle.contains(target)||panel.contains(target))return false")
        self.assertPageContains("if(detail.dismissOutside(e.target))return")
        self.assertPageContains(".photodetail[hidden]{display:none}")
        self.assertPageContains("box-sizing:border-box;display:grid;align-items:start;gap:14px;padding:16px")
        self.assertPageContains(".photodetail .srcstate:empty{display:none}")
        self.assertPageContains(".photodetail>button{min-height:44px}")
        self.assertPageContains(".photodetailtoggle{width:44px;height:44px}")
        self.assertPageContains(".photodetailtoggle{justify-self:start;width:30px;height:30px;display:grid;place-items:center")
        # Lucide 的 info 圆点是长度 .01 的短线；没有圆头时会缩成几乎不可见的横杠。
        css = (Path(__file__).resolve().parents[1] / "web" / "app.css").read_text(
            encoding="utf-8")
        start = css.index(".photodetailtoggle svg{")
        rule = css[start:css.index("}", start)]
        self.assertIn("stroke-linecap:round", rule)
        self.assertPageContains('<symbol id="i-info" viewBox="0 0 24 24">')
        self.assertPageLacks("item.path", "图片详情不能取得或渲染 ledger 绝对路径")

    def test_lightbox_remeasures_when_the_window_resizes(self):
        # Swiper 只在构造那一刻量一次容器；灯箱是插进已布好版的页面里的，
        # 窗口一改大小 slide 就停在旧宽度，大图按错误的框缩放。
        self.assertPageContains("new ResizeObserver(()=>{main.update();strip.update()})")
        self.assertPageContains("activeLightbox.resize?.disconnect()")

    def test_failed_review_decisions_are_shown_instead_of_silently_swallowed(self):
        """「点了没反应」的真身：失败被吞掉，按钮还卡在 disabled。

        `api()` 在任何非 2xx 都 throw，而这个 async onclick 原来没有 catch：
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
        # 头像走同一个兜底链，取不到图时回落首字母。
        self.assertPageContains("row.entity_id?{id:row.entity_id}:null,null,subjectKind)")
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
        self.assertPageContains("api('/api/purge-missing',{method:'POST',body:JSON.stringify({id})})")
        self.assertPageContains('data-reveal="${id}"')
        self.assertPageContains('data-sync="${id}"')
        # 在线资产是 URL，没有本地文件可定位。
        self.assertPageContains("it.location==='online'?'':sourceTools(it.id)")

    def test_resource_sync_is_embedded_in_stats_and_keeps_offline_sources_safe(self):
        self.assertPageContains("${resourceSyncMarkup()}")
        self.assertPageContains("if(path==='/resource-sync'){await openResourceSync(false);return}")
        self.assertPageContains("route('/stats#resource-sync',true)")
        self.assertPageContains("api('/api/resource-sync/scan',{method:'POST'")
        self.assertPageContains("api('/api/resource-sync/apply',{method:'POST'")
        self.assertPageContains("source.unreadable")
        self.assertPageContains("background:true,restart:true")
        self.assertPageContains("payload.status==='running'")
        self.assertPageContains("location.pathname==='/stats'")
        self.assertPageContains("background:true,status_only:true")
        self.assertPageContains("void followScan(existing)")
        self.assertPageContains("离线来源会整库跳过")
        self.assertPageContains("同步并清理")
        self.assertPageContains('class="resourcesyncfooter"')
        self.assertPageContains('class="resourcepanel"')
        self.assertPageContains('class="resourceapplyrow"')
        self.assertPageContains("候选 CSV、来源证据、女优头像和厂牌 Logo 不会删除")
        self.assertPageContains(".resourceaction{box-sizing:border-box;height:36px")
        self.assertPageContains("@media(max-width:640px){.resourcesync .resourcesyncfooter{align-items:stretch;flex-direction:column")
        self.assertPageContains(".resourcesync .resourcesources{grid-template-columns:1fr}")
        self.assertPageContains(".resourcesyncbox,.resourcepanel{overflow:clip;border:1px solid var(--line-soft);border-radius:12px")
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
        self.assertPageContains(
            "  showHomeSurfaces();\n  // 必须在 showHomeSurfaces 之后加：")
        self.assertPageContains("document.body.classList.remove('entity-open','index-open')")


if __name__ == "__main__":
    unittest.main()
