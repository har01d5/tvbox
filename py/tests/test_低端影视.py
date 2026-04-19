import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from urllib.parse import quote
from unittest.mock import patch


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

    def test_parse_movie_cards_extracts_expected_fields(self):
        html = """
        <div class="movie-card">
          <a href="/movie/test-title/">
            <img src="/poster.jpg" />
            <span class="poster-badge">HD</span>
            <h3>测试电影</h3>
          </a>
        </div>
        """
        cards = self.spider._parse_movie_cards(html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "https://ddys.io/movie/test-title/",
                    "vod_name": "测试电影",
                    "vod_pic": "https://ddys.io/poster.jpg",
                    "vod_remarks": "HD",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_built_url_and_returns_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="movie-card">
          <a href="/series/demo/">
            <img src="/series.jpg" />
            <span class="poster-badge">更新至3集</span>
            <h3>示例剧</h3>
          </a>
        </div>
        """
        result = self.spider.categoryContent("series", "2", False, {"area": "/region/japan"})
        self.assertEqual(mock_request_html.call_args.args[0], "https://ddys.io/series/region/japan/page/2")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["pagecount"], 3)
        self.assertEqual(result["limit"], 24)
        self.assertEqual(result["list"][0]["vod_name"], "示例剧")

    def test_request_html_posts_form_data_for_search(self):
        calls = {}

        class FakeResponse:
            def __init__(self):
                self.status_code = 200
                self.text = (
                    '<div class="movie-card"><a href="/movie/hit/">'
                    '<img src="/search.jpg" /><h3>命中结果</h3></a></div>'
                )
                self.encoding = "utf-8"

        def fake_post(
            url,
            params=None,
            data=None,
            json=None,
            cookies=None,
            headers=None,
            timeout=5,
            verify=True,
            stream=False,
            allow_redirects=True,
        ):
            calls["url"] = url
            calls["data"] = data
            calls["headers"] = headers
            return FakeResponse()

        self.spider.post = fake_post
        html = self.spider._request_html(
            self.spider.host + "/search",
            method="POST",
            data=f"q={quote('繁花')}",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertIn("命中结果", html)
        self.assertEqual(calls["url"], "https://ddys.io/search")
        self.assertEqual(calls["data"], "q=%E7%B9%81%E8%8A%B1")
        self.assertEqual(calls["headers"]["Content-Type"], "application/x-www-form-urlencoded")

    @patch.object(Spider, "_request_html")
    def test_search_content_posts_keyword_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="mb-12">
          <div class="movie-card">
            <a href="/anime/result/">
              <img src="/anime.jpg" alt="搜索动漫" />
              <span class="poster-badge">全集</span>
              <h3>搜索动漫</h3>
            </a>
          </div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "1")
        kwargs = mock_request_html.call_args.kwargs
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["data"], "q=%E7%B9%81%E8%8A%B1")
        self.assertEqual(result["list"][0]["vod_id"], "https://ddys.io/anime/result/")
        self.assertEqual(result["pagecount"], 2)


if __name__ == "__main__":
    unittest.main()
