import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("maitian_spider", str(ROOT / "麦田影院.py")).load_module()
Spider = MODULE.Spider


class TestMaiTianSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_returns_expected_classes(self):
        result = self.spider.homeContent(False)
        self.assertEqual(
            result["class"],
            [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "电视剧"},
                {"type_id": "4", "type_name": "动漫"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "26", "type_name": "短剧"},
                {"type_id": "25", "type_name": "少儿"},
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_url_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="public-list-box">
          <a class="public-list-exp" href="/voddetail/123.html" title="分类影片">
            <img data-src="/cover.jpg" />
          </a>
          <span class="public-list-prb">更新至10集</span>
        </div>
        """
        result = self.spider.categoryContent("2", "3", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.mtyy5.com/vodshow/2--------3---.html",
        )
        self.assertEqual(
            result["list"],
            [
                {
                    "vod_id": "/voddetail/123.html",
                    "vod_name": "分类影片",
                    "vod_pic": "https://www.mtyy5.com/cover.jpg",
                    "vod_remarks": "更新至10集",
                }
            ],
        )
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_returns_empty_result_without_network(self, mock_request_html):
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(result, {"page": 2, "limit": 0, "total": 0, "list": []})
        mock_request_html.assert_not_called()

    @patch.object(Spider, "_request_html")
    def test_detail_content_parses_meta_and_play_groups(self, mock_request_html):
        mock_request_html.return_value = """
        <html><body>
        <h1>示例影片</h1>
        <div class="detail-pic"><img data-src="/detail.jpg" /></div>
        <div class="vod_content">这里是简介</div>
        <a class="swiper-slide">线路1</a>
        <a class="swiper-slide">线路2</a>
        <div class="anthology-list-box">
          <ul class="anthology-list-play">
            <li><a href="/vodplay/1-1-1.html">第1集</a></li>
            <li><a href="/vodplay/1-1-2.html">第2集</a></li>
          </ul>
        </div>
        <div class="anthology-list-box">
          <ul class="anthology-list-play">
            <li><a href="/vodplay/1-2-1.html">正片</a></li>
          </ul>
        </div>
        </body></html>
        """
        result = self.spider.detailContent(["/voddetail/1.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "/voddetail/1.html")
        self.assertEqual(vod["vod_name"], "示例影片")
        self.assertEqual(vod["vod_pic"], "https://www.mtyy5.com/detail.jpg")
        self.assertEqual(vod["vod_content"], "这里是简介")
        self.assertEqual(vod["vod_play_from"], "线路$$$线路")
        self.assertEqual(
            vod["vod_play_url"],
            "第1集$/vodplay/1-1-1.html#第2集$/vodplay/1-1-2.html$$$正片$/vodplay/1-2-1.html",
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_extracts_meta_and_keeps_intro_clean(self, mock_request_html):
        mock_request_html.return_value = """
        <html><body>
        <h1>示例影片</h1>
        <div class="detail-pic"><img data-src="/detail-meta.jpg" /></div>
        <ul class="slide-info">
          <li>名称: 示例影片</li>
          <li>类型: 剧情</li>
          <li>年代: 2026</li>
          <li>地区: 大陆</li>
          <li>语言: 国语</li>
          <li>评分: 8.8</li>
          <li>导演: 导演甲</li>
          <li>演员: 演员甲 / 演员乙</li>
          <li>豆瓣ID: 1234567</li>
        </ul>
        <div class="switch-box">
          <div class="text cor3">这里是正确简介</div>
          <div class="anthology-tab">
            <a class="swiper-slide">MT源6</a>
          </div>
          <div class="anthology-list">
            <div class="anthology-list-box">
              <ul class="anthology-list-play">
                <li><a href="/vodplay/2-1-1.html">第1集</a></li>
              </ul>
            </div>
          </div>
          <script>
            $(".anthology-tab a").eq(0).addClass("on nav-dt");
          </script>
        </div>
        </body></html>
        """
        result = self.spider.detailContent(["/voddetail/2.html"])
        vod = result["list"][0]
        self.assertEqual(vod["type_name"], "剧情")
        self.assertEqual(vod["vod_year"], "2026")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_lang"], "国语")
        self.assertEqual(vod["vod_douban_score"], "8.8")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_actor"], "演员甲 / 演员乙")
        self.assertEqual(vod["vod_douban_id"], "1234567")
        self.assertEqual(vod["vod_content"], "这里是正确简介")

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_request_html")
    def test_player_content_returns_direct_url(self, mock_request_html, mock_request_json):
        mock_request_html.return_value = """
        <script>var player_data={"url":"https://cdn.example.com/direct.m3u8"}</script>
        """
        result = self.spider.playerContent("线路", "/vodplay/1-1-1.html", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://cdn.example.com/direct.m3u8")
        mock_request_json.assert_not_called()

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_request_html")
    def test_player_content_resolves_signed_art_url(self, mock_request_html, mock_request_json):
        mock_request_html.return_value = """
        <script>var player_data={"url":"%2Fapi.php%3Fid%3D1"}</script>
        """
        mock_request_json.side_effect = [
            {"signed_url": "?url=/signed/abc"},
            {"jmurl": "https://cdn.example.com/final.m3u8"},
        ]
        result = self.spider.playerContent("线路", "/vodplay/1-1-2.html", {})
        self.assertEqual(result["url"], "https://cdn.example.com/final.m3u8")
        self.assertEqual(
            mock_request_json.call_args_list[0].args[0],
            "https://www.mtyy5.com/static/player/art.php?get_signed_url=1&url=/api.php?id=1",
        )
        self.assertEqual(
            mock_request_json.call_args_list[1].args[0],
            "https://www.mtyy5.com/static/player/art.php?url=/signed/abc",
        )

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_request_html")
    def test_player_content_falls_back_when_player_data_missing(self, mock_request_html, mock_request_json):
        mock_request_html.return_value = "<html><body>empty</body></html>"
        result = self.spider.playerContent("线路", "/vodplay/1-1-3.html", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["url"], "https://www.mtyy5.com/vodplay/1-1-3.html")
        mock_request_json.assert_not_called()
