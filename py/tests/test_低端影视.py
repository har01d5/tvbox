import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("ddys_spider", str(ROOT / "低端影视.py")).load_module()
Spider = MODULE.Spider


class TestDDYSSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_classes_and_filter_keys(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["series", "movie", "variety", "anime"],
        )
        self.assertEqual(
            [item["key"] for item in content["filters"]["movie"]],
            ["class", "area", "year", "by"],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_category_url_applies_default_and_selected_filters(self):
        url = self.spider._build_category_url("movie", "2", {"class": "/genre/action", "year": "/year/2025"})
        self.assertEqual(url, "https://ddys.io/movie/genre/action/year/2025/page/2")

    def test_build_category_url_for_first_page_keeps_page_segment(self):
        url = self.spider._build_category_url("series", "1", {})
        self.assertEqual(url, "https://ddys.io/series/page/1")


if __name__ == "__main__":
    unittest.main()
