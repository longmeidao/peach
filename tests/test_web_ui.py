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


if __name__ == "__main__":
    unittest.main()
