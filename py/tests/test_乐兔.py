import unittest
import base64
from importlib.machinery import SourceFileLoader
from pathlib import Path
from urllib.parse import quote
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
        self.assertEqual(self.spider._encode_vod_id("/vods/305741.html"), "vods/305741")
        self.assertEqual(self.spider._decode_vod_id("vods/305741"), "https://www.letu.me/vods/305741.html")
        self.assertEqual(self.spider._encode_play_id("/vod/305741-1-1.html"), "vod/305741-1-1")
        self.assertEqual(self.spider._decode_play_id("vod/305741-1-1"), "https://www.letu.me/vod/305741-1-1.html")

    def test_parse_cards_extracts_compact_vod_ids(self):
        html = """
        <div class="grid container_list">
          <div class="s6">
            <a href="/vods/305741.html" title="示例影片"></a>
            <img class="large" data-src="/cover.jpg" />
            <div class="small-text">更新至1集</div>
          </div>
        </div>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "vods/305741",
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
            <a href="/vods/90001.html" title="分类片"></a>
            <img class="large" data-src="/cat.jpg" />
            <div class="small-text">HD</div>
          </div>
        </div>
        """
        result = self.spider.categoryContent("2", "5", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.letu.me/type/2-5.html")
        self.assertEqual(result["page"], 5)
        self.assertEqual(result["limit"], 1)
        self.assertNotIn("pagecount", result)
        self.assertEqual(result["list"][0]["vod_id"], "vods/90001")

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_plain_type_path_for_first_page(self, mock_request_html):
        mock_request_html.return_value = ""
        self.spider.categoryContent("1", "1", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.letu.me/type/1.html")

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_search_url_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="result-list">
          <div class="result-item">
            <a href="/vods/70001.html">搜索影片</a>
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
        self.assertEqual(result["list"][0]["vod_id"], "vods/70001")
        self.assertNotIn("pagecount", result)

    def test_parse_detail_page_extracts_metadata_and_playlists(self):
        html = """
        <h1>详情标题</h1>
        <img src="/poster.jpg" />
        <div class="scroll no-margin">
          <a>电影</a>
          <a>演员甲</a>
        </div>
        <div class="no-space no-margin m l">导演甲</div>
        <div class="no-margin m l">中国</div>
        <div class="responsive"><p>第一段</p><p>一段剧情简介</p></div>
        <div class="tabs left-align">
          <a>线路A</a>
          <a>线路B</a>
        </div>
        <div class="playno">
          <a href="/vod/305741-1-1.html">第1集</a>
          <a href="/vod/305741-1-2.html">第2集</a>
        </div>
        <div class="playno">
          <a href="/vod/305741-2-1.html">正片</a>
        </div>
        """
        result = self.spider._parse_detail_page(html, "vods/305741")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "vods/305741")
        self.assertEqual(vod["vod_name"], "详情标题")
        self.assertEqual(vod["vod_pic"], "https://www.letu.me/poster.jpg")
        self.assertEqual(vod["type_name"], "电影")
        self.assertEqual(vod["vod_actor"], "演员甲")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_area"], "中国")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "线路A$$$线路B")
        self.assertEqual(
            vod["vod_play_url"],
            "第1集$vod/305741-1-1#第2集$vod/305741-1-2$$$正片$vod/305741-2-1",
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_decodes_compact_vod_id(self, mock_request_html):
        mock_request_html.return_value = "<h1>详情标题</h1>"
        self.spider.detailContent(["vods/305741"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.letu.me/vods/305741.html")

    @patch.object(Spider, "_request_html")
    def test_player_content_returns_direct_json_url(self, mock_request_html):
        mock_request_html.return_value = '{"code":200,"url":"https://video.example/direct.m3u8"}'
        result = self.spider.playerContent("线路A", "vod/305741-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://video.example/direct.m3u8")

    @patch.object(Spider, "_request_html")
    def test_player_content_decodes_rose_base64_url(self, mock_request_html):
        encoded = quote(base64.b64encode(b"https://video.example/rose.m3u8").decode("utf-8"))
        mock_request_html.return_value = '{"code":200,"url":"rose_' + encoded + '"}'
        result = self.spider.playerContent("线路A", "vod/305741-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/rose.m3u8")

    def test_extract_player_data_reads_player_json(self):
        html = '<script>var player_aaaa={"url":"https%3A%2F%2Fvideo.example%2Fenc1.m3u8","encrypt":"1"};</script>'
        self.assertEqual(self.spider._extract_player_data(html)["encrypt"], "1")

    @patch.object(Spider, "_request_html")
    def test_player_content_supports_encrypt_1_and_encrypt_2(self, mock_request_html):
        encoded = quote(base64.b64encode(b"https://video.example/enc2.m3u8").decode("utf-8"))
        mock_request_html.side_effect = [
            '<script>var player_aaaa={"url":"https%3A%2F%2Fvideo.example%2Fenc1.m3u8","encrypt":"1"};</script>',
            '<script>var player_aaaa={"url":"' + encoded + '","encrypt":"2"};</script>',
        ]
        encrypt_1 = self.spider.playerContent("线路A", "vod/305741-1-1", {})
        encrypt_2 = self.spider.playerContent("线路A", "vod/305741-1-2", {})
        self.assertEqual(encrypt_1["url"], "https://video.example/enc1.m3u8")
        self.assertEqual(encrypt_2["url"], "https://video.example/enc2.m3u8")

    @patch.object(Spider, "_request_html")
    def test_player_content_falls_back_to_system_parse(self, mock_request_html):
        mock_request_html.return_value = "<html></html>"
        result = self.spider.playerContent("线路A", "vod/305741-1-1", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["url"], "https://www.letu.me/vod/305741-1-1.html")


if __name__ == "__main__":
    unittest.main()
