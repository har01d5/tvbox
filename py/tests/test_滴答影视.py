import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


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

    def test_parse_cards_extracts_expected_fields(self):
        html = """
        <div class="myui-vodlist__box">
          <div class="title"><a href="/detail/888.html" title="示例影片"></a></div>
          <a class="lazyload" data-original="/cover.jpg"></a>
          <span class="pic-text">HD</span>
        </div>
        """
        cards = self.spider._parse_cards(html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "https://www.didahd.pro/detail/888.html",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.didahd.pro/cover.jpg",
                    "vod_remarks": "HD",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_built_url_and_returns_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="myui-vodlist__box">
          <div class="title"><a href="/detail/456.html" title="分类影片"></a></div>
          <a class="lazyload" data-original="/cate.jpg"></a>
          <span class="pic-text">完结</span>
        </div>
        """
        result = self.spider.categoryContent("1", "2", False, {"area": "香港", "sort": "score"})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.didahd.pro/show/1-香港-score------2---")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["pagecount"], 3)
        self.assertEqual(result["limit"], 12)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_search_url_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="myui-vodlist__box">
          <div class="title"><a href="/detail/321.html" title="搜索影片"></a></div>
          <a class="lazyload" data-original="/search.jpg"></a>
          <span class="pic-text">抢先版</span>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.didahd.pro/search/-------------.html?wd=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["list"][0]["vod_id"], "https://www.didahd.pro/detail/321.html")
        self.assertEqual(result["pagecount"], 2)


if __name__ == "__main__":
    unittest.main()
