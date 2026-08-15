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

    def test_detail_deduplicates_identity_and_supports_tag_editing(self):
        self.assertIn("const identitySeen=new Set()", self.page)
        self.assertIn("data-remove-tag", self.page)
        self.assertIn("/api/item-tag", self.page)
        self.assertIn('class="tagplus"', self.page)

    def test_tags_page_has_cloud_and_alphabet_modes(self):
        self.assertIn('data-tag-view="cloud"', self.page)
        self.assertIn('data-tag-view="alphabet"', self.page)
        self.assertIn('class="alphabet"', self.page)

    def test_climax_uses_pinned_healthicons_symbol(self):
        self.assertIn('id="i-sperm"', self.page)
        self.assertIn("icon('sperm')", self.page)


if __name__ == "__main__":
    unittest.main()
