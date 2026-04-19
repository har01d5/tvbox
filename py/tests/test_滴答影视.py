import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("dida_spider", str(ROOT / "滴答影视.py")).load_module()
Spider = MODULE.Spider


class TestDidaSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_classes_and_filters(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["1", "2", "5", "4", "3"],
        )
        self.assertEqual(
            [item["key"] for item in content["filters"]["1"]],
            ["class", "area", "year", "lang", "sort"],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_category_url_applies_default_and_selected_filters(self):
        url = self.spider._build_category_url(
            "1",
            "2",
            {"area": "香港", "sort": "score", "class": "动作", "lang": "粤语", "year": "2025"},
        )
        self.assertEqual(url, "https://www.didahd.pro/show/1-香港-score-动作-粤语----2---2025")

    def test_build_category_url_for_first_page_keeps_page_segment(self):
        url = self.spider._build_category_url("2", "1", {})
        self.assertEqual(url, "https://www.didahd.pro/show/2--time------1---")


if __name__ == "__main__":
    unittest.main()
