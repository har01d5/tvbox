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

    def test_parse_detail_page_merges_direct_and_pan_sources(self):
        html = """
        <html>
          <h1 class="text-xl md:text-3xl">低端示例<span class="block">DDYS Example</span></h1>
          <img alt="低端示例" src="/poster-detail.jpg" />
          <div class="text-xs md:text-sm text-gray-600 dark:text-gray-400">2025 · 日本 · 动画</div>
          <div class="text-xs md:text-sm text-gray-700 dark:text-gray-300">导演：<span>导演甲</span></div>
          <div class="text-xs md:text-sm text-gray-700 dark:text-gray-300">主演：<span>主演乙</span></div>
          <div class="prose"><p>第一段简介。</p><p>第二段简介。</p></div>
          <button onclick="switchSource(1, '第1集$/play/ep1#第2集$/play/ep2', 'mp4')">DDYS</button>
          <div class="download-type-content" id="download-type-quark">
            <button onclick="trackAndOpenResource(atob('aHR0cHM6Ly9wYW4ucXVhcmsuY24vcy9hYmMxMjM='))">夸克查看</button>
          </div>
          <div class="download-type-content" id="download-type-baidu">
            <button onclick="trackAndOpenResource(atob('aHR0cHM6Ly9wYW4uYmFpZHUuY29tL3MvZGVtbw=='))">百度查看</button>
          </div>
        </html>
        """
        vod = self.spider._parse_detail_page(html, "https://ddys.io/anime/demo/")
        self.assertEqual(vod["vod_name"], "低端示例")
        self.assertEqual(vod["vod_pic"], "https://ddys.io/poster-detail.jpg")
        self.assertEqual(vod["vod_year"], "2025")
        self.assertEqual(vod["vod_area"], "日本")
        self.assertEqual(vod["vod_class"], "动画")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_actor"], "主演乙")
        self.assertEqual(vod["vod_content"], "第一段简介。\n第二段简介。")
        self.assertEqual(vod["vod_play_from"], "DDYS$$$quark$$$baidu")
        self.assertIn("第2集$/play/ep2", vod["vod_play_url"])
        self.assertIn("夸克查看$https://pan.quark.cn/s/abc123", vod["vod_play_url"])
        self.assertIn("百度查看$https://pan.baidu.com/s/demo", vod["vod_play_url"])

    def test_extract_pan_sources_deduplicates_same_link_with_different_labels(self):
        html = """
        <div class="download-type-content" id="download-type-quark">
          <button onclick="trackAndOpenResource(atob('aHR0cHM6Ly9wYW4ucXVhcmsuY24vcy8xNGE0MDVhOWJiMGQ='))">查看</button>
          <button onclick="trackAndOpenResource(atob('aHR0cHM6Ly9wYW4ucXVhcmsuY24vcy8xNGE0MDVhOWJiMGQ='))">一键复制</button>
        </div>
        """
        groups = self.spider._extract_pan_sources(html)
        self.assertEqual(groups, [{"from": "quark", "urls": "查看$https://pan.quark.cn/s/14a405a9bb0d"}])

    @patch.object(Spider, "_request_html")
    def test_detail_content_reads_detail_page_and_returns_single_vod(self, mock_request_html):
        mock_request_html.return_value = """
        <h1 class="text-xl md:text-3xl">详情标题</h1>
        <button onclick="switchSource(1, '/play/detail-demo', 'mp4')">直连</button>
        """
        result = self.spider.detailContent(["https://ddys.io/movie/demo/"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://ddys.io/movie/demo/")
        self.assertEqual(result["list"][0]["vod_id"], "https://ddys.io/movie/demo/")
        self.assertEqual(result["list"][0]["vod_name"], "详情标题")
        self.assertEqual(result["list"][0]["vod_play_from"], "直连")
        self.assertEqual(result["list"][0]["vod_play_url"], "全集$/play/detail-demo")

    def test_player_content_returns_full_url_for_direct_source(self):
        result = self.spider.playerContent("DDYS", "/play/ep1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://ddys.io/play/ep1")
        self.assertEqual(result["header"]["Referer"], "https://ddys.io/")

    def test_player_content_returns_pan_link_without_rewriting(self):
        result = self.spider.playerContent("quark", "https://pan.quark.cn/s/demo", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://pan.quark.cn/s/demo")
        self.assertEqual(result["header"], {})

    def test_player_content_treats_baidu_and_xunlei_as_pan_sources(self):
        baidu = self.spider.playerContent("baidu", "https://pan.baidu.com/s/demo", {})
        xunlei = self.spider.playerContent("xunlei", "https://pan.xunlei.com/s/demo", {})
        self.assertEqual(baidu["url"], "https://pan.baidu.com/s/demo")
        self.assertEqual(xunlei["url"], "https://pan.xunlei.com/s/demo")

    def test_home_content_keeps_reference_filter_values_for_movie(self):
        movie_filters = self.spider.homeContent(False)["filters"]["movie"]
        class_values = movie_filters[0]["value"]
        area_values = movie_filters[1]["value"]
        year_values = movie_filters[2]["value"]
        sort_values = movie_filters[3]["value"]
        self.assertIn({"n": "动作", "v": "/genre/action"}, class_values)
        self.assertIn({"n": "中国", "v": "/region/china"}, area_values)
        self.assertIn({"n": "2025", "v": "/year/2025"}, year_values)
        self.assertEqual(sort_values[1], {"n": "评分", "v": "rating/"})


if __name__ == "__main__":
    unittest.main()
