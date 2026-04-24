from base64 import b64encode
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("lumman_spider", str(ROOT / "路漫漫.py")).load_module()
Spider = MODULE.Spider

SAMPLE_LIST_HTML = """
<html><body>
<div class="video-img-box">
  <a href="/vod/detail/1001.html">
    <img class="lazyload" data-src="/upload/1001.jpg" />
    <h6 class="title">海贼王</h6>
    <div class="label">更新至1123集</div>
  </a>
</div>
<div class="video-img-box">
  <a href="/vod/detail/1002.html">
    <img class="lazyload" src="https://img.example.com/1002.jpg" />
    <h6 class="title">你的名字</h6>
    <div class="label">全集</div>
  </a>
</div>
</body></html>
"""

SAMPLE_DETAIL_HTML = """
<html><body>
<h1 class="page-title">进击的巨人</h1>
<div class="module-item-pic"><img class="lazyload" src="/upload/jjdr.jpg" /></div>
<div class="video-info-items">状态：已完结</div>
<div class="video-info-items">地区：日本</div>
<div class="video-info-content">人类与巨人的战斗。</div>
<a class="module-tab-item tab-item" href="#line1">在线播放</a>
<a class="module-tab-item tab-item" href="#line2">云播</a>
<div id="line1" class="module-player-list">
  <a href="/vod/play/1001-1-1.html">第1集</a>
  <a href="/vod/play/1001-1-2.html">第2集</a>
</div>
<div id="line2" class="module-player-list">
  <a href="/vod/play/1001-2-1.html">HD</a>
</div>
</body></html>
"""


class TestLuManManSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_returns_only_animation_classes(self):
        result = self.spider.homeContent(False)
        self.assertEqual(
            result["class"],
            [
                {"type_id": "6", "type_name": "日本动漫"},
                {"type_id": "7", "type_name": "国产动漫"},
                {"type_id": "8", "type_name": "欧美动漫"},
                {"type_id": "3", "type_name": "日本动画电影"},
                {"type_id": "4", "type_name": "国产动画电影"},
                {"type_id": "5", "type_name": "欧美动画电影"},
            ],
        )

    @patch.object(Spider, "_get_html")
    def test_home_video_content_parses_cards(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        result = self.spider.homeVideoContent()
        self.assertEqual(len(result["list"]), 2)
        self.assertEqual(result["list"][0]["vod_id"], "vod/detail/1001.html")
        self.assertEqual(result["list"][0]["vod_pic"], "https://www.lmm85.com/upload/1001.jpg")
        self.assertEqual(result["list"][1]["vod_pic"], "https://img.example.com/1002.jpg")

    @patch.object(Spider, "_get_html")
    def test_category_content_builds_filtered_url(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        result = self.spider.categoryContent("6", "2", False, {"年代": "/year/2024", "排序": "/by/time"})
        self.assertEqual(result["page"], 2)
        self.assertEqual(len(result["list"]), 2)
        mock_html.assert_called_with("https://www.lmm85.com/vod/show/id/6/year/2024/by/time/page/2.html")

    @patch.object(Spider, "_get_html")
    def test_search_content_uses_search_path(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        result = self.spider.searchContent("海贼", False, "3")
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["list"][0]["vod_name"], "海贼王")
        mock_html.assert_called_with("https://www.lmm85.com/vod/search/page/3/wd/%E6%B5%B7%E8%B4%BC.html")

    @patch.object(Spider, "_get_html")
    def test_detail_content_parses_meta_and_playlists(self, mock_html):
        mock_html.return_value = SAMPLE_DETAIL_HTML
        result = self.spider.detailContent(["vod/detail/1001.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "进击的巨人")
        self.assertEqual(vod["vod_pic"], "https://www.lmm85.com/upload/jjdr.jpg")
        self.assertEqual(vod["vod_content"], "人类与巨人的战斗。")
        self.assertEqual(vod["vod_remarks"], "状态：已完结 / 地区：日本")
        self.assertEqual(vod["vod_play_from"], "在线播放$$$云播")
        self.assertIn("第1集$vod/play/1001-1-1.html#第2集$vod/play/1001-1-2.html", vod["vod_play_url"])
        self.assertIn("HD$vod/play/1001-2-1.html", vod["vod_play_url"])

    @patch.object(Spider, "_get_html")
    def test_detail_content_falls_back_to_direct_playlist_scan(self, mock_html):
        mock_html.return_value = """
        <html><body>
        <h1 class="page-title">测试</h1>
        <div class="module-player-list">
          <a href="/vod/play/1-1-1.html">正片</a>
        </div>
        </body></html>
        """
        result = self.spider.detailContent(["vod/detail/1.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_play_from"], "播放列表")
        self.assertEqual(vod["vod_play_url"], "正片$vod/play/1-1-1.html")

    def test_decrypt_token_returns_plaintext(self):
        key = b"ejjooopppqqqrwww"
        iv = b"1348987635684651"
        cipher = AES.new(key, AES.MODE_CBC, iv)
        token = b64encode(cipher.encrypt(pad(b"plain-token", AES.block_size))).decode("utf-8")
        self.assertEqual(self.spider._decrypt_token(token), "plain-token")

    def test_decrypt_token_handles_bad_ciphertext(self):
        self.assertEqual(self.spider._decrypt_token("not-valid"), "")

    @patch.object(Spider, "_resolve_player_url")
    def test_player_content_returns_direct_media_without_parse(self, mock_resolve):
        result = self.spider.playerContent("在线播放", "https://cdn.example.com/video.m3u8", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://cdn.example.com/video.m3u8")
        mock_resolve.assert_not_called()

    @patch.object(Spider, "_resolve_player_url")
    @patch.object(Spider, "_get_html")
    def test_player_content_decodes_encrypt_1_and_encrypt_2(self, mock_html, mock_resolve):
        encoded = b64encode("https://cdn.example.com/e2.m3u8".encode("utf-8")).decode("utf-8")
        mock_html.side_effect = [
            '<script>var player_aaaa={"url":"https%3A%2F%2Fcdn.example.com%2Fe1.m3u8","encrypt":"1","from":"line"};</script>',
            f'<script>var player_aaaa={{"url":"{encoded}","encrypt":"2","from":"line"}};</script>',
        ]
        mock_resolve.side_effect = ["https://cdn.example.com/e1.m3u8", "https://cdn.example.com/e2.m3u8"]
        first = self.spider.playerContent("在线播放", "vod/play/1001-1-1.html", {})
        second = self.spider.playerContent("在线播放", "vod/play/1001-1-2.html", {})
        self.assertEqual(first["url"], "https://cdn.example.com/e1.m3u8")
        self.assertEqual(second["url"], "https://cdn.example.com/e2.m3u8")

    @patch.object(Spider, "_resolve_player_url", return_value="")
    @patch.object(Spider, "_get_html", return_value="<html><body>missing player</body></html>")
    def test_player_content_falls_back_to_parse_when_player_missing(self, mock_html, mock_resolve):
        result = self.spider.playerContent("在线播放", "vod/play/1001-1-1.html", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["url"], "https://www.lmm85.com/vod/play/1001-1-1.html")


if __name__ == "__main__":
    unittest.main()
