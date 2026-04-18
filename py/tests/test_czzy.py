import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("czzy_spider", str(ROOT / "厂长资源.py")).load_module()
Spider = MODULE.Spider


class TestCZZYSpider(unittest.TestCase):
    def setUp(self):
        self.spider = Spider()
        self.spider.init()

    def test_default_host_prefers_czzy89(self):
        self.assertEqual(self.spider.hosts[0], "https://www.czzy89.com")
        self.assertEqual(self.spider.current_host, "https://www.czzy89.com")

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        class_ids = [item["type_id"] for item in content["class"]]
        self.assertEqual(class_ids[:3], ["movie", "tv", "anime"])
        self.assertIn("cn_drama", class_ids)

    def test_parse_media_cards_extracts_basic_fields(self):
        html = """
        <ul class="mi_ne_kd">
          <li>
            <a href="/movie/abc.html" title="链接标题">
              <img data-original="https://img.example/cover.jpg" alt="测试影片" />
            </a>
            <span class="jidi">更新至10集</span>
          </li>
        </ul>
        """
        cards = self.spider._parse_media_cards(html, "https://www.cz01.org")
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "/movie/abc.html",
                    "vod_name": "测试影片",
                    "vod_pic": "https://img.example/cover.jpg",
                    "vod_remarks": "更新至10集",
                }
            ],
        )

    @patch.object(Spider, "fetch")
    def test_request_html_falls_back_to_second_host(self, mock_fetch):
        class FakeResponse:
            def __init__(self, text, status_code=200):
                self.text = text
                self.status_code = status_code
                self.encoding = "utf-8"

        mock_fetch.side_effect = [
            Exception("first host down"),
            FakeResponse("<html><body>ok</body></html>"),
        ]

        html, host = self.spider._request_html("/movie_bt/page/1", expect_xpath="//body")
        self.assertIn("ok", html)
        self.assertEqual(host, "https://www.cz01.org")
        self.assertEqual(self.spider.current_host, "https://www.cz01.org")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_media_list(self, mock_request_html):
        mock_request_html.return_value = (
            """
            <ul>
              <li>
                <a href="/movie/abc.html"><img src="/cover.jpg" alt="分类影片" /></a>
                <span class="hdinfo">HD</span>
              </li>
            </ul>
            """,
            "https://www.czzy89.com",
        )

        result = self.spider.categoryContent("movie", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")
        self.assertEqual(result["list"][0]["vod_pic"], "https://www.czzy89.com/cover.jpg")

    @patch.object(Spider, "_request_html")
    def test_search_content_reuses_media_card_parser(self, mock_request_html):
        mock_request_html.return_value = (
            """
            <div>
              <li>
                <a href="/movie/search-hit.html" title="搜索影片"></a>
                <img data-src="https://img.example/search.jpg" />
              </li>
            </div>
            """,
            "https://www.czzy89.com",
        )

        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(result["list"][0]["vod_id"], "/movie/search-hit.html")
        self.assertEqual(result["list"][0]["vod_name"], "搜索影片")


if __name__ == "__main__":
    unittest.main()
