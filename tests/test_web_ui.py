import unittest
from pathlib import Path


class WebUiSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_text(
            encoding="utf-8"
        )

    def test_studio_metadata_is_not_compiled_as_inline_javascript(self):
        self.assertNotIn('onerror="this.parentNode.innerHTML=', self.page)
        self.assertNotIn('onload="if(this.naturalWidth', self.page)
        self.assertIn("img.addEventListener('error',fallback", self.page)

    def test_entity_routes_are_semantic_and_not_model_shaped(self):
        self.assertNotIn("route(`/entity/", self.page)
        self.assertIn("performer:'performers'", self.page)
        self.assertIn("studio:'studios'", self.page)
        self.assertIn("creator:'creators'", self.page)

    def test_detail_close_disposes_playback_source(self):
        self.assertIn("function disposeStage", self.page)
        self.assertIn("video.pause();video.removeAttribute('src');video.load();video.remove()", self.page)
        self.assertIn("$('#closeStage').onclick=()=>disposeStage(true)", self.page)
        self.assertIn("function cancelDetailStream()", self.page)
        self.assertIn("/api/stream-cancel?session=", self.page)
        self.assertIn("keepalive:true", self.page)
        self.assertIn("dataset.peachStreamCancel=JSON.stringify(result)", self.page)
        self.assertIn("detailPlayer.src({src:detailStreamUrl(it.id)", self.page)
        self.assertIn("detailPlayer.dispose()", self.page)

    def test_detail_uses_pinned_videojs_and_authoritative_duration(self):
        self.assertIn('/vendor/videojs/8.23.9/video.min.js', self.page)
        self.assertIn('/vendor/videojs/8.23.9/video-js.min.css', self.page)
        self.assertIn("function mountDetailPlayer(it,video,autoplay)", self.page)
        self.assertIn("detailPlayer.duration(expected)", self.page)
        self.assertIn("['loadstart','loadedmetadata','durationchange','error']", self.page)
        self.assertIn("const d=it.duration||v.duration||0", self.page)
        self.assertIn("skipButtons:{backward:10,forward:10}", self.page)

    def test_player_stats_cover_direct_range_and_future_segmented_streams(self):
        self.assertIn('id="playerStatsBtn"', self.page)
        self.assertIn("HTTP Range", self.page)
        self.assertIn("bufferedAhead(video)", self.page)
        self.assertIn("getVideoPlaybackQuality", self.page)
        self.assertIn("?.vhs?.stats", self.page)

    def test_tag_geometry_uses_shared_tokens(self):
        self.assertIn("--tag-radius:999px", self.page)
        self.assertIn("border-radius:var(--tag-radius)", self.page)
        self.assertIn("height:40px;padding:0 20px", self.page)
        self.assertIn("overflow-x:auto;overflow-y:hidden", self.page)

    def test_multiselect_has_explicit_mode_range_and_toggle_controls(self):
        self.assertIn('id="selectMode"', self.page)
        self.assertIn("e.shiftKey||e.ctrlKey||e.metaKey||selectMode", self.page)
        self.assertIn("visibleCardIds()", self.page)
        self.assertIn("lastSelectedId", self.page)
        self.assertIn('class="selectionMark"', self.page)

    def test_pending_delete_is_visible_without_deleting_media(self):
        self.assertIn("it.disposal==='pending'?'pending-delete':''", self.page)
        self.assertIn(".card.pending-delete .poster", self.page)
        self.assertIn('<b>待删</b>', self.page)

    def test_surface_has_measured_beeg_glow_geometry(self):
        self.assertIn("height:49vh", self.page)
        self.assertIn("animation:ambient-in .8s ease .5s both", self.page)

    def test_detail_deduplicates_identity_and_supports_tag_editing(self):
        self.assertIn("const identitySeen=new Set()", self.page)
        self.assertIn("data-remove-tag", self.page)
        self.assertIn("/api/item-tag", self.page)
        self.assertIn('class="tagplus"', self.page)

    def test_tag_picker_supports_search_recent_selection_and_keyboard(self):
        self.assertIn('class="tagpicker"', self.page)
        self.assertIn("peach.recentTags", self.page)
        self.assertIn("最近使用", self.page)
        self.assertIn("e.key==='ArrowDown'||e.key==='ArrowUp'", self.page)
        self.assertIn("e.key==='Escape'", self.page)

    def test_source_icons_are_visible_in_detail_and_list_badges(self):
        self.assertIn(".srcbig svg{stroke:currentColor;fill:none", self.page)
        self.assertIn("local:icon('hard-drive')", self.page)

    def test_beeg_evidence_driven_surfaces_are_translucent_and_rail_is_continuous(self):
        self.assertIn(".brandpill{", self.page)
        self.assertIn("background:var(--overlay-5);border:1px solid var(--border-10)", self.page)
        self.assertIn("border:1px solid var(--border-15);\n  border-radius:999px;background:transparent", self.page)
        self.assertIn("--overlay-5:rgba(245,250,255,.05)", self.page)
        self.assertIn("--border-15:rgba(245,250,255,.15)", self.page)
        self.assertIn("background:var(--ground);\n  border-right:0", self.page)
        self.assertIn("['performers','艺人','user-round']", self.page)
        self.assertIn("['tags','标签','tags']", self.page)

    def test_entity_profile_hides_home_facets_and_renders_context(self):
        self.assertIn("body.entity-open #tiers,body.entity-open #tagbar{display:none}", self.page)
        self.assertIn('src="/logo?studio=${encodeURIComponent(d.canonical_name)}"', self.page)
        self.assertIn('class="entitytags"', self.page)
        self.assertIn('class="relatedpeople"', self.page)
        self.assertIn("data-related-performer", self.page)

    def test_every_home_navigation_restores_the_shared_facets(self):
        self.assertIn("function showHomeSurfaces()", self.page)
        self.assertIn("$('#tiers').style.display='';$('#tagbar').style.display=''", self.page)
        self.assertIn("function closeStats(push=true){if(push)route('/');showHomeSurfaces();load(true)}", self.page)
        self.assertIn("async function load(reset)", self.page)
        self.assertIn("showHomeSurfaces();\n  if(reset)offset=0", self.page)
        self.assertIn("showHomeSurfaces();disposeStage(false)", self.page)

    def test_entity_tags_filter_inside_the_current_entity_page(self):
        self.assertIn("if(entityTag)p.set('tag',entityTag)", self.page)
        self.assertIn("async function updateEntityCollection", self.page)
        self.assertIn("updateEntityCollection(kind,name,next,true)", self.page)
        self.assertIn("renderEntityCollection(kind,name,items,entityTag)", self.page)
        self.assertNotIn("openEntity(kind,name,true,next)", self.page)
        self.assertNotIn(
            "document.body.classList.remove('entity-open');$('#index').hidden=true;state.tag=b.dataset.entityTag",
            self.page,
        )

    def test_large_collections_render_in_bounded_batches(self):
        self.assertIn("p.set('limit','48')", self.page)
        self.assertIn("if(offset)p.set('count','0')", self.page)
        self.assertIn('class="entitymore"', self.page)
        self.assertIn("const indexLimit=people?120:180", self.page)
        self.assertIn('class="indexmore"', self.page)
        self.assertIn("adsBatch.items.slice(offset,offset+60)", self.page)
        self.assertIn("if(!reset)p.set('count','0')", self.page)
        self.assertIn("!listLoading&&!$('#loadSentinel').hidden", self.page)
        self.assertIn("indexRequestSeq", self.page)
        self.assertIn("barsRequestSeq", self.page)
        self.assertIn("async function getBarsData()", self.page)
        self.assertIn("Date.now()-barsDataAt<30000", self.page)
        self.assertNotIn("p.set('limit','120')", self.page)

    def test_filter_and_sort_rows_stay_visible_in_both_scroll_directions(self):
        self.assertIn("--filterH:58px", self.page)
        self.assertIn(".tagbar{position:sticky;top:var(--topH)", self.page)
        self.assertIn(".count{position:sticky;top:calc(var(--topH) + var(--filterH))", self.page)
        self.assertIn("border-bottom:1px solid transparent;background:transparent", self.page)
        self.assertIn("background:transparent;border-bottom:1px solid transparent", self.page)
        self.assertIn(".tagbar.is-stuck,.count.is-stuck{background:color-mix(in srgb,#020408 84%,transparent)", self.page)
        self.assertIn("background:color-mix(in srgb,#020408 84%,transparent)", self.page)
        self.assertIn("backdrop-filter:saturate(1.35) blur(16px)", self.page)
        self.assertIn("function updateStickySurfaces()", self.page)
        self.assertIn("css.position==='sticky'", self.page)
        self.assertIn("el.classList.toggle('is-stuck',stuck)", self.page)
        self.assertNotIn(".tagbar.tuck", self.page)
        self.assertNotIn("function onScrollFrame", self.page)
        self.assertIn(":root{--tile:168px;--topH:52px;--sortH:96px}", self.page)
        self.assertIn(".count{align-items:stretch;flex-direction:column", self.page)
        self.assertIn(".count .sorts button{flex:0 0 auto", self.page)

    def test_entity_collection_posters_and_titles_open_item_details(self):
        self.assertIn('class="cardopenhit" data-open', self.page)
        self.assertIn('<button class="t cardtitle" data-open>', self.page)
        self.assertIn("if(e.target.closest('[data-open]')){e.stopPropagation();(onClick||openItem)(+el.dataset.id)", self.page)
        self.assertIn(".cardopenhit{position:absolute;inset:0;z-index:3", self.page)
        self.assertIn("el.querySelectorAll('[data-open]').forEach(opener=>", self.page)
        self.assertIn("opener.dataset.openWired='1'", self.page)
        self.assertIn(".hovertools button{pointer-events:none", self.page)
        self.assertIn(".card.longhover .seektools button,.card:hover .later-tools button{pointer-events:auto}", self.page)

    def test_remote_hover_previews_do_not_stream_full_media(self):
        self.assertIn("if(it.location!=='local')", self.page)
        self.assertIn("el.dataset.hoverMode=it.location==='local'?'video':'frames'", self.page)
        self.assertIn("function releaseHoverPreviews(root=document,except=null)", self.page)
        self.assertIn("releaseHoverPreviews(document,el)", self.page)
        self.assertIn("window.addEventListener('pagehide',()=>releaseHoverPreviews())", self.page)
        self.assertIn("if(document.hidden)releaseHoverPreviews()", self.page)
        self.assertIn("if(reset)releaseHoverPreviews($('#grid'))", self.page)
        self.assertIn("releaseHoverPreviews($('#srow'))", self.page)

    def test_detail_close_returns_to_the_collection_that_opened_it(self):
        self.assertIn("detailReturnPath='/'", self.page)
        self.assertIn("if(push)detailReturnPath=location.pathname+location.search", self.page)
        self.assertIn("if(push)route(detailReturnPath||'/')", self.page)

    def test_entity_profile_uses_logo_links_without_a_redundant_back_row(self):
        self.assertIn("const faviconUrl=url=>", self.page)
        self.assertIn('class="entitylinkicon"', self.page)
        self.assertIn('class="entitylinklabel"', self.page)
        self.assertIn("img.dataset.studio&&!img.dataset.fallback", self.page)
        self.assertNotIn('<span class="mono" style="color:var(--muted)">${labels[kind]||kind}资料页</span>', self.page)

    def test_status_tags_are_separated_and_nonessential_states_are_hidden(self):
        self.assertIn(".sep{flex:none;width:1px;height:19px", self.page)
        self.assertIn("{k:'later',label:'稍后看'},{k:'flagged',label:'已标记'}", self.page)
        self.assertNotIn("{k:'played',label:'看过'}", self.page)
        self.assertNotIn("{k:'ads',label:'疑似广告'}", self.page)

    def test_search_placeholder_is_an_actionable_recommendation(self):
        self.assertIn("const SEARCH_HINTS=['Prestige','FC2','Sakura Misaki','丝袜','足交','ABW']", self.page)
        self.assertIn("$('#q').dataset.suggestion=searchSuggestion", self.page)
        self.assertIn("runSearch(true,true)", self.page)
        self.assertNotIn("试试：", self.page)
        self.assertNotIn("ABW 番号", self.page)

    def test_card_identity_is_not_repeated_as_a_content_tag(self):
        self.assertNotIn("const perf=(it.performers||[])", self.page)
        self.assertIn('${tgs?`<div class="ctags">${tgs}</div>`', self.page)

    def test_tags_page_has_cloud_and_alphabet_modes(self):
        self.assertIn('data-tag-view="cloud"', self.page)
        self.assertIn('data-tag-view="alphabet"', self.page)
        self.assertIn('class="alphabet"', self.page)
        self.assertIn('data-tag-category=', self.page)
        self.assertIn("['general','内容']", self.page)
        self.assertIn("['artist','人物']", self.page)
        self.assertIn("category=params.get('category')", self.page)

    def test_secondary_back_controls_are_icon_only(self):
        self.assertIn('id="i-arrow-left"', self.page)
        self.assertIn("${icon('arrow-left')}</button>", self.page)
        self.assertNotIn("${icon('chevron-left')}<span>返回</span>", self.page)

    def test_climax_uses_pinned_healthicons_symbol(self):
        self.assertIn('id="i-sperm"', self.page)
        self.assertIn("icon('sperm')", self.page)

    def test_settings_own_refresh_hover_and_ambient_preferences(self):
        self.assertIn("const DEFAULT_SETTINGS={autoRefresh:true,refreshMinutes:5", self.page)
        self.assertIn('id="settingsPanel"', self.page)
        self.assertIn("scheduleAutoRefresh()", self.page)
        self.assertIn("refreshAll(true)", self.page)
        self.assertIn("appSettings.hoverDelaySeconds", self.page)

    def test_search_menu_has_local_history_and_recommendations(self):
        self.assertIn("peach.search.history.v1", self.page)
        self.assertIn("搜索记录", self.page)
        self.assertIn("recommendations.map", self.page)
        self.assertIn("rememberSearch(query)", self.page)
        self.assertIn(".top:has(.search.open){overflow:visible}", self.page)
        self.assertNotIn("setTimeout(runSearch,320)", self.page)
        self.assertIn("runSearch(true,true)", self.page)

    def test_detail_has_stats_ambient_and_better_version_goal(self):
        self.assertIn('class="ambientcanvas"', self.page)
        self.assertIn("requestVideoFrameCallback", self.page)
        self.assertIn("--video-glow", self.page)
        self.assertIn("视频 ID / 会话", self.page)
        self.assertIn("/api/quality-goal", self.page)
        self.assertIn('id="betterVersion"', self.page)
        self.assertNotIn('id="closeStage">收起', self.page)


if __name__ == "__main__":
    unittest.main()
