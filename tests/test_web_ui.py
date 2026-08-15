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

    def test_tag_geometry_uses_shared_tokens(self):
        self.assertIn("--tag-radius:999px", self.page)
        self.assertIn("border-radius:var(--tag-radius)", self.page)
        self.assertIn("height:40px;padding:0 20px", self.page)

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
        self.assertIn("background:var(--frost-panel);border:1px solid transparent", self.page)
        self.assertIn("background:var(--ground);\n  border-right:0", self.page)
        self.assertIn("['performers','艺人','user-round']", self.page)
        self.assertIn("['tags','标签','tags']", self.page)

    def test_tags_page_has_cloud_and_alphabet_modes(self):
        self.assertIn('data-tag-view="cloud"', self.page)
        self.assertIn('data-tag-view="alphabet"', self.page)
        self.assertIn('class="alphabet"', self.page)

    def test_climax_uses_pinned_healthicons_symbol(self):
        self.assertIn('id="i-sperm"', self.page)
        self.assertIn("icon('sperm')", self.page)


if __name__ == "__main__":
    unittest.main()
