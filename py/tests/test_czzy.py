import unittest
from base64 import b64encode
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad


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

    def test_parse_detail_page_splits_direct_and_pan_sources(self):
        html = """
        <div class="dyxingq">
          <h1>繁花</h1>
          <img src="/poster.jpg" />
          <div class="moviedteail_list">
            <li>年份：2024</li>
            <li>地区：中国大陆</li>
            <li>导演：王家卫</li>
            <li>主演：胡歌</li>
          </div>
          <div class="yp_context">一段剧情简介</div>
        </div>
        <div class="paly_list_btn">
          <a href="/v_play/1.html">第1集</a>
          <a href="/v_play/2.html">第2集</a>
        </div>
        <div class="ypbt_down_list">
          <a href="https://www.alipan.com/s/demo">阿里云盘</a>
        </div>
        """

        detail = self.spider._parse_detail_page(html, "https://www.czzy89.com", "/movie/fanhua.html")
        vod = detail["list"][0]
        self.assertEqual(vod["vod_name"], "繁花")
        self.assertEqual(vod["vod_year"], "2024")
        self.assertEqual(vod["vod_play_from"], "厂长资源$$$网盘资源")
        self.assertIn("第1集$https://www.czzy89.com/v_play/1.html", vod["vod_play_url"])
        self.assertIn("阿里云盘$https://www.alipan.com/s/demo", vod["vod_play_url"])

    @patch.object(Spider, "_request_html")
    def test_detail_content_reads_from_vod_id_path(self, mock_request_html):
        mock_request_html.return_value = (
            """
            <h1>示例影片</h1>
            <div class="paly_list_btn"><a href="/play/x.html">立即播放</a></div>
            """,
            "https://www.czzy89.com",
        )

        result = self.spider.detailContent(["/movie/example.html"])
        self.assertEqual(result["list"][0]["vod_id"], "/movie/example.html")
        self.assertEqual(result["list"][0]["vod_name"], "示例影片")

    def test_extract_iframe_src(self):
        html = '<iframe src="/player-v2/test"></iframe>'
        self.assertEqual(
            self.spider._extract_iframe_src(html, "https://www.czzy89.com"),
            "https://www.czzy89.com/player-v2/test",
        )

    def test_extract_player_url_prefers_mysvg_then_art_url(self):
        self.assertEqual(
            self.spider._extract_player_url_from_iframe("var mysvg='https://video.example/a.m3u8';"),
            "https://video.example/a.m3u8",
        )
        self.assertEqual(
            self.spider._extract_player_url_from_iframe("art.url='https://video.example/b.m3u8';"),
            "https://video.example/b.m3u8",
        )

    def test_extract_player_url_decodes_data_payload(self):
        original = "https://video.example/data.m3u8"
        middle = len(original) // 2
        obfuscated = original[:middle] + "ABCDEFG" + original[middle:]
        encoded = "".join("{:02x}".format(ord(ch)) for ch in obfuscated)[::-1]
        html = 'var config = {"data":"%s"};' % encoded
        self.assertEqual(self.spider._extract_player_url_from_iframe(html), original)

    def test_extract_player_url_decrypts_player_payload(self):
        payload = '{"url":"https://video.example/encrypted.m3u8"}'
        key = b"VFBTzdujpR9FWBhe"
        iv = b"1234567890abcdef"
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = b64encode(cipher.encrypt(pad(payload.encode("utf-8"), AES.block_size))).decode("utf-8")
        html = 'var player="%s";var rand="%s";' % (encrypted, iv.decode("utf-8"))
        self.assertEqual(
            self.spider._extract_player_url_from_iframe(html),
            "https://video.example/encrypted.m3u8",
        )

    def test_extract_player_url_supports_wp_nonce_fallback(self):
        html = """
        <script>
        window.wp_nonce = "token";
        var config = { url: 'https://video.example/wp.m3u8' };
        </script>
        """
        self.assertEqual(
            self.spider._extract_player_url_from_iframe(html),
            "https://video.example/wp.m3u8",
        )


if __name__ == "__main__":
    unittest.main()
