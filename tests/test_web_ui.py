import unittest
from pathlib import Path


class WebUiSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 页面已拆成 index.html + app.css + app.js。这些断言守的是「Web 表面」
        # 这一个契约，不是某个文件，所以把三份源码接起来一起看。
        web = Path(__file__).resolve().parents[1] / "web"
        cls.page = chr(10).join(
            (web / name).read_text(encoding="utf-8")
            for name in ("index.html", "app.css", "app.js")
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

    def test_studio_metadata_is_not_compiled_as_inline_javascript(self):
        self.assertPageLacks('onerror="this.parentNode.innerHTML=')
        self.assertPageLacks('onload="if(this.naturalWidth')
        self.assertPageContains("img.addEventListener('error',fallback")

    def test_brand_icon_uses_shared_square_png(self):
        self.assertPageContains('<link rel="icon" href="/peach-logo.png" type="image/png">')
        self.assertPageContains('<img class="mark" src="/peach-logo.png" alt="">')

    def test_entity_routes_are_semantic_and_not_model_shaped(self):
        self.assertPageLacks("route(`/entity/")
        self.assertPageContains("performer:'performers'")
        self.assertPageContains("studio:'studios'")
        self.assertPageContains("creator:'creators'")

    def test_hidden_load_more_buttons_are_actually_removed_from_layout(self):
        # 有显式 display 的元素不会被浏览器默认的 [hidden]{display:none} 隐藏；
        # 少了这条规则，按钮画在页面上但 requestMore 首行就 return，点了没反应。
        self.assertPageContains(".indexmore[hidden],.entitymore[hidden]{display:none}")

    def test_co_starred_cards_show_every_performer_not_only_the_first(self):
        # 卡片不能再只取 performers[0]：共演作品要叠头像、列名字并给出总数。
        self.assertPageContains("const coStarred=performers.length>1&&!it.creator")
        self.assertPageContains('<div class="mavstack">')
        self.assertPageContains("performers.slice(0,3)")
        self.assertPageContains("data-entity-kind=\"performer\" data-entity-name=\"${esc(nm)}\"")
        self.assertPageContains("等 ${performerTotal} 人")
        self.assertPageContains(".mavstack .mav+.mav{margin-left:-14px}")

    def test_every_card_avatar_falls_back_through_the_same_helper(self):
        self.assertPageContains("function avatarInner(name,ref,repId)")
        self.assertPageContains("`/entity-image?kind=performer&id=${ref.id}`")
        self.assertPageContains("this.onerror=null;this.src='/avatar?id=${repId}'")

    def test_detail_identity_groups_by_kind_with_the_label_on_top(self):
        # 逐行一个名字在共演作品上会把整个侧栏撑满，左侧还重复一列标签。
        self.assertPageContains("const idGroup=(label,kind,list,extra='')=>list.length")
        self.assertPageContains('<h5 class="idlabel">${label}</h5>')
        self.assertPageContains(".idrow{display:flex;flex-wrap:wrap")
        # 出镜者标签跟着作品形态走，不再写死「女优」——见 performerLabel。
        self.assertPageContains("idGroup(performerLabel(it),'performer',castList,")
        self.assertPageContains("idGroup('厂牌','studio',studioList)")
        self.assertPageLacks("const performerName=performerRef?.name")
        self.assertPageLacks(".identityrow", "旧的逐行布局必须整段删掉")

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
            "(it.creator?'creator':(it.studio?'studio':'')));")
        self.assertPageContains(
            "const avatarName=identity.kind?identity.name:"
            "(performer||it.creator||it.studio||who);")

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
        self.assertPageContains("if(video.paused)video.play().catch(()=>{});else video.pause()")

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

    def test_detail_close_disposes_playback_source(self):
        self.assertPageContains("function disposeStage")
        self.assertPageContains("video.pause();video.removeAttribute('src');video.load();video.remove()")
        self.assertPageContains(
            "document.body.classList.remove('detail-open');current=null;activeMix=null;\n  scheduleStickySurfaces();"
        )
        self.assertPageContains("$('#closeStage').onclick=()=>disposeStage(true)")
        self.assertPageContains("function cancelDetailStream()")
        self.assertPageContains("/api/stream-cancel?session=")
        self.assertPageContains("keepalive:true")
        self.assertPageContains("dataset.peachStreamCancel=JSON.stringify(result)")
        self.assertPageContains("/api/stream-plan?id=")
        self.assertPageContains("detailStreamSource(it).then(source=>")
        self.assertPageContains("fallbackUsed=false")
        self.assertPageContains("player.src(directDetailSource(it))")
        self.assertPageContains("detailPlayer.dispose()")

    def test_detail_uses_pinned_videojs_and_authoritative_duration(self):
        self.assertPageContains('/vendor/videojs/8.23.9/video.min.js')
        self.assertPageContains('/vendor/videojs/8.23.9/video-js.min.css')
        self.assertPageContains("function mountDetailPlayer(it,video,autoplay)")
        self.assertPageContains("detailPlayer.duration(expected)")
        self.assertPageContains("['loadstart','loadedmetadata','durationchange','error']")
        self.assertPageContains("const d=it.duration||v.duration||0")
        self.assertPageContains("skipButtons:{backward:appSettings.seekSeconds,forward:appSettings.seekSeconds}")

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
        self.assertPageContains("<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-play\"/>")
        self.assertPageContains("await tokShow()")

    def test_tag_geometry_uses_shared_tokens(self):
        self.assertPageContains("--tag-radius:999px")
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

    def test_manage_collects_the_four_admin_entries_behind_one_top_level_icon(self):
        """统计、疑似广告、回收站、人工复核各占一个顶层图标时，侧栏一半是管理入口。

        它们合并到「管理」下的二级导航；URL 保持原样，只是多了一条共用导航条。
        """
        self.assertPageContains("['manage','管理','settings']")
        self.assertPageContains("const MANAGE_SECTIONS=[")
        for section in ("'stats','统计'", "'ads','疑似广告'", "'trash','回收站'", "'review','人工复核'"):
            self.assertPageContains(section)
        self.assertPageContains("function manageSection()")
        self.assertPageContains("function buildManageBar()")
        self.assertPageContains('id="managebar"')
        self.assertPageContains("if(k==='manage'){openManage();return}")
        # 顶层图标里不再各自占位
        edge = self.page.split("const EDGE_ICONS=[", 1)[1].split("];", 1)[0]
        for gone in ("'trash'", "'ads'", "'stats'", "'review'"):
            self.assertNotIn(gone, edge, f"{gone} 应该已经收进管理，不再是顶层入口")
        self.assertIn("'manage'", edge)

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
        self.assertPageContains("const canApprove=reviewCategory!=='creator_tags'||String(row.status||'').trim()==='candidate'")
        self.assertPageContains("${canApprove?'':' disabled'}")

    def test_surface_navigation_clears_stale_panels_and_ignores_late_responses(self):
        """跨页面请求返回较慢时，旧统计/复核响应不能覆盖当前页面。"""
        self.assertPageContains("if(location.pathname!=='/review')return")
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

    def test_top_level_highlight_is_exclusive_and_covers_index_pages(self):
        """首页原来只看 state.state，进管理区和索引页时它仍然亮着，两个入口同时高亮。"""
        self.assertPageContains("if(k==='performers'||k==='tags')return path==='/'+k")
        self.assertPageContains("if(k==='')return path==='/'&&!manageSection()&&!state.state")
        self.assertPageContains("buildEdge();     // 顶层高亮跟随管理区")

    def test_manage_surfaces_hide_the_home_rails(self):
        """回收站和疑似广告是行政列表，不该顶着首页的人物/厂牌横条。

        `showHomeSurfaces` 会先把横条恢复出来，所以隐藏必须排在它之后，否则被立刻覆盖。
        """
        self.assertPageContains("if(current){$('#tiers').style.display='none';$('#tagbar').style.display='none'}")
        home = self.page.split("function showHomeSurfaces(){", 1)[1].split("}", 1)[0]
        self.assertLess(home.index("$('#tiers').style.display=''"), home.index("buildManageBar()"),
                        "buildManageBar 必须排在恢复首页横条之后，否则隐藏会被覆盖")

    def test_search_suggestions_come_from_real_data_in_bulk(self):
        """写死的 6 个词翻两次就重复。顶部聚合只有几十条，也不够；索引接口一次给近千条。"""
        self.assertPageContains("async function loadSearchPool()")
        self.assertPageContains("['performers','creators','tags'].map(")
        self.assertPageContains("`/api/index?kind=${kind}&limit=400`")
        self.assertPageContains("Promise.all([loadSearchHistory(),loadSearchPool()])")
        self.assertPageContains("[...searchPool()]")

    def test_admin_surfaces_fill_wide_screens(self):
        """统计和复核是信息密集的行政界面，宽屏下居中会浪费两侧空间。"""
        self.assertPageContains(".stats{padding:8px 0 42px}")
        self.assertPageContains(".review{padding:8px 0 42px}")
        self.assertPageLacks("max-width:1440px")

    def test_returning_home_from_any_surface_moves_the_highlight(self):
        """点回首页时路径还停在 /review 之类上，navOn('') 仍然为假，高亮不切换。"""
        self.assertPageContains("if(location.pathname!=='/')route('/');")
        self.assertEqual(self.page.count("if(location.pathname!=='/')route('/');"), 2,
                         "抽屉和窄栏两处导航都要修")

    def test_ads_icon_matches_the_lucide_stroke_style(self):
        """图标库里没有表示广告的图形，自绘的感叹号必须和其余图标同风格。"""
        self.assertPageContains('<symbol id="i-alert" viewBox="0 0 24 24">')
        self.assertPageContains("['ads','疑似广告','alert']")

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

    def test_beeg_evidence_driven_surfaces_are_translucent_and_rail_is_continuous(self):
        self.assertPageContains(".brandpill{")
        self.assertPageContains("background:var(--overlay-5);border:1px solid var(--border-10)")
        self.assertPageContains("border:1px solid var(--border-15);\n  border-radius:999px;background:transparent")
        self.assertPageContains("--overlay-5:rgba(245,250,255,.05)")
        self.assertPageContains("--border-15:rgba(245,250,255,.15)")
        self.assertPageContains("background:var(--ground);\n  border-right:0")
        self.assertPageContains("['performers','艺人','user-round']")
        self.assertPageContains("['tags','标签','tags']")

    def test_entity_profile_hides_home_facets_and_renders_context(self):
        self.assertPageContains("body.entity-open #tiers,body.entity-open #tagbar,")
        self.assertPageContains('src="/logo?studio=${encodeURIComponent(d.canonical_name)}"')
        self.assertPageContains('class="entitytags"')
        self.assertPageContains('class="relatedpeople"')
        self.assertPageContains("data-related-performer")

    def test_every_home_navigation_restores_the_shared_facets(self):
        self.assertPageContains("function showHomeSurfaces()")
        self.assertPageContains("$('#tiers').style.display='';$('#tagbar').style.display=''")
        self.assertPageContains("function closeStats(push=true){if(push)route('/');showHomeSurfaces();load(true)}")
        self.assertPageContains("async function load(reset)")
        self.assertPageContains("showHomeSurfaces();\n  if(reset)offset=0")
        self.assertPageContains("showHomeSurfaces();disposeStage(false)")

    def test_entity_tags_filter_inside_the_current_entity_page(self):
        self.assertPageContains("if(entityTag)p.set('tag',entityTag)")
        self.assertPageContains("async function updateEntityCollection")
        self.assertPageContains("updateEntityCollection(kind,name,next,true)")
        self.assertPageContains("renderEntityCollection(kind,name,items,entityTag)")
        self.assertPageLacks("openEntity(kind,name,true,next)")
        self.assertPageLacks(
            "document.body.classList.remove('entity-open');$('#index').hidden=true;state.tag=b.dataset.entityTag"
        )

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
        self.assertPageContains("async function getBarsData()")
        self.assertPageContains("Date.now()-barsDataAt<30000")
        self.assertPageLacks("p.set('limit','120')")
        self.assertPageContains("more._observer=new IntersectionObserver")
        self.assertPageContains("more.hidden=append?!items.has_more")

    def test_mix_cards_share_the_home_flow_and_open_a_routed_side_queue(self):
        self.assertPageContains('class="card mixcard" data-mix-seed=')
        self.assertPageContains("cards.splice(7,0,mixCardHtml(seed))")
        self.assertPageContains(".mixstack::before,.mixstack::after")
        self.assertPageContains('<span class="mixbadge">${icon(\'play\')}Mix</span>')
        self.assertPageContains("async function openMix(seedId,itemId=seedId,push=true)")
        self.assertPageContains("route(`/mix/${seedId}/${itemId}`)")
        self.assertPageContains('class="mixqueue"')
        self.assertPageContains('class="mixitem ${x.id===itemId?\'current\':\'\'}"')
        self.assertPageContains("data-mix-item")
        self.assertPageContains("if(!mixContext)api('/api/related?id='")
        self.assertPageContains("batchWithMix(d.items,location.pathname==='/'&&state.state!=='trash')")
        # 竖屏条只在首页出现。JAV 模式也排除：番号发行物是横版，竖屏是另一类内容，
        # 而主列表的 exclude_vertical 管不到这条——它是独立请求、独立插入的。
        self.assertPageContains("location.pathname!=='/'||javActive()||state.orient==='竖屏'")
        self.assertPageContains("||state.state==='ads'||state.state==='trash'")
        self.assertPageContains("route(section==='trash'?'/trash':'/')")
        self.assertPageContains("if(path==='/trash')")
        self.assertPageContains("/api/trash/empty")

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
        self.assertPageContains("if(e.target.closest('[data-open]')){e.stopPropagation();(onClick||openItem)(+el.dataset.id)")
        self.assertPageContains(".cardopenhit{position:absolute;inset:0;z-index:3")
        self.assertPageContains("el.querySelectorAll('[data-open]').forEach(opener=>")
        self.assertPageContains("opener.dataset.openWired='1'")
        self.assertPageContains(".hovertools button{pointer-events:none")
        self.assertPageContains(".card.longhover .seektools button,.card:hover .later-tools button{pointer-events:auto}")

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
        self.assertPageLacks("{k:'ads',label:'疑似广告'}")

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
        self.assertPageContains("const ar=(it.ctx_orient==='竖屏'||cls==='scard')")
        self.assertPageContains("const PORTRAIT_RATIO=9/16;")
        self.assertPageContains("    ? PORTRAIT_RATIO")
        self.assertPageLacks("Math.min(0.9,Math.max(0.5,it.width/it.height))")
        self.assertPageContains("(jav&&layout==='big'?COVER_FRONT_RATIO:16/9)")

    def test_portrait_strip_sits_on_a_row_boundary_without_borrowing_extra_items(self):
        """竖屏条整行占位，必须插在行边界上，而不是另拉一批横屏视频补满余位。

        补位的那批 id 不在分页序列里，翻下一页必然重复；而且它们被当作 `scard`
        渲染会按竖屏比例压扁横屏画面。行边界插入既不额外请求也不会重复。
        """
        self.assertPageContains('.shorts-inline{grid-column:1/-1;margin:28px 0 8px;padding-top:0}')
        self.assertPageContains("it.ctx_orient==='竖屏'||cls==='scard'")
        self.assertPageContains('grid-template-columns:repeat(auto-fill,minmax(var(--tile),1fr))')
        self.assertPageContains('const anchor=cards[Math.min(cards.length,columns*SHORTS_ROW_OFFSET)]')
        self.assertPageContains("anchor.insertAdjacentHTML('beforebegin',inline)")
        self.assertPageLacks("fillerParams")
        self.assertPageLacks('const remainder=')
        self.assertPageContains('.srow .scard{flex:none;width:214px;cursor:pointer}')

    def test_only_the_default_home_list_drops_portrait_videos(self):
        """搜索必须能命中竖屏作品；排除竖屏只是首页默认列表的取景，不是全局过滤。"""
        self.assertPageContains("if(location.pathname==='/'&&!state.q&&!state.orient)p.set('exclude_vertical','1')")
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
        self.assertPageContains('.meta .t{font-size:14px;line-height:1.35;min-height:2.7em;')
        self.assertPageContains("const sizeText=Number(it.size)>0?fmtSize(Number(it.size)):'大小未知';")
        self.assertPageContains('<span class="size">${sizeText}</span>')

    def test_tags_page_has_cloud_and_alphabet_modes(self):
        self.assertPageContains('data-tag-view="cloud"')
        self.assertPageContains('data-tag-view="alphabet"')
        self.assertPageContains('class="alphabet"')
        self.assertPageContains('data-tag-category=')
        self.assertPageContains("['general','内容']")
        self.assertPageContains("['artist','人物']")
        self.assertPageContains("category=params.get('category')")

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
        self.assertPageContains("const DEFAULT_SETTINGS={autoRefresh:true,refreshMinutes:5")
        self.assertPageContains('id="settingsPanel"')
        self.assertPageContains("scheduleAutoRefresh()")
        self.assertPageContains("refreshAll(true)")
        self.assertPageContains("appSettings.hoverDelaySeconds")
        self.assertPageContains("appSettings.batchSize")
        self.assertPageContains("appSettings.defaultSort")
        self.assertPageContains("appSettings.seekSeconds")
        self.assertPageContains("appSettings.searchHistoryLimit")
        self.assertPageContains("appSettings.relatedLimit")
        self.assertPageLacks('id="ambientSetting"')
        self.assertPageContains("color:#f5f7fa;color-scheme:dark")

    def test_search_menu_has_local_history_and_recommendations(self):
        self.assertPageContains("/api/search-history")
        self.assertPageContains("搜索记录")
        self.assertPageContains("recommendations.map")
        self.assertPageContains("rememberSearch(query)")
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
        self.assertPageLacks('id="closeStage">收起')

    def test_review_page_is_a_separate_management_layer(self):
        self.assertPageContains("route('/review')")
        self.assertPageContains("const REVIEW_LABELS={creator_tags:'创作者标签'")
        self.assertPageContains("/api/review/decision")
        self.assertPageContains("if(path==='/review')")

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
        self.assertPageContains("cover_sources:'封面来源'")
        self.assertPageContains("fc2_markings:'FC2 评论标记'")

    def test_index_pages_drop_the_home_filter_bars_and_back_button(self):
        # 艺人/标签索引和资料页一样是「专注看某一类实体」的表面。
        self.assertPageContains(
            "body.entity-open #tiers,body.entity-open #tagbar,\nbody.index-open #tiers,body.index-open #tagbar{display:none}")
        self.assertPageLacks('id="iClose"', "顶栏入口本身就是返回路径")
        self.assertPageLacks("$('#iClose').onclick")

    def test_index_open_is_applied_after_the_surface_reset(self):
        # showHomeSurfaces 会清掉这两个类；写在它前面等于自己加完自己删。
        self.assertPageContains(
            "  showHomeSurfaces();\n  // 必须在 showHomeSurfaces 之后加：")
        self.assertPageContains("document.body.classList.remove('entity-open','index-open')")


if __name__ == "__main__":
    unittest.main()
