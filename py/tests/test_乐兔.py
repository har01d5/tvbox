import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("letu_spider", str(ROOT / "乐兔.py")).load_module()
Spider = MODULE.Spider


class TestLeTuSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["1", "2", "3", "4", "5"],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_encode_and_decode_detail_and_play_ids(self):
        self.assertEqual(self.spider._encode_vod_id("/detail/demo.html"), "detail/demo")
        self.assertEqual(self.spider._decode_vod_id("detail/demo"), "https://www.letu.me/detail/demo.html")
        self.assertEqual(self.spider._encode_play_id("/play/123-1-1.html"), "play/123-1-1")
        self.assertEqual(self.spider._decode_play_id("play/123-1-1"), "https://www.letu.me/play/123-1-1.html")

    def test_parse_cards_extracts_compact_vod_ids(self):
        html = """
        <div class="grid container_list">
          <div class="s6">
            <a href="/detail/demo.html" title="示例影片"></a>
            <img class="large" data-src="/cover.jpg" />
            <div class="small-text">更新至1集</div>
          </div>
        </div>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "detail/demo",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.letu.me/cover.jpg",
                    "vod_remarks": "更新至1集",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_type_page_url(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="grid container_list">
          <div class="s6">
            <a href="/detail/cat-demo.html" title="分类片"></a>
            <img class="large" data-src="/cat.jpg" />
            <div class="small-text">HD</div>
          </div>
        </div>
        """
        result = self.spider.categoryContent("2", "3", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.letu.me/type/2-3.html")
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertNotIn("pagecount", result)
        self.assertEqual(result["list"][0]["vod_id"], "detail/cat-demo")

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_search_url_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="result-list">
          <div class="result-item">
            <a href="/detail/search-demo.html">搜索影片</a>
            <img class="large" data-src="/search.jpg" />
            <div class="small-text">全集</div>
          </div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.letu.me/vodsearch/-------------.html?wd=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["list"][0]["vod_id"], "detail/search-demo")
        self.assertNotIn("pagecount", result)


if __name__ == "__main__":
    unittest.main()
