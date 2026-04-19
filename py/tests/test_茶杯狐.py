import base64
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("cupfox_spider", str(ROOT / "茶杯狐.py")).load_module()
Spider = MODULE.Spider


class TestCupfoxSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_encode_and_decode_ids_keep_short_paths(self):
        self.assertEqual(
            self.spider._encode_detail_id("/movie/test-slug.html"),
            "detail/test-slug",
        )
        self.assertEqual(
            self.spider._decode_detail_id("detail/test-slug"),
            "https://www.cupfox.ai/movie/test-slug.html",
        )
        self.assertEqual(
            self.spider._encode_play_id("/play/abc123.html"),
            "play/abc123",
        )
        self.assertEqual(
            self.spider._decode_play_id("play/abc123"),
            "https://www.cupfox.ai/play/abc123.html",
        )
        self.assertEqual(
            self.spider._encode_detail_id("/video/119983.html"),
            "detail/video/119983",
        )
        self.assertEqual(
            self.spider._decode_detail_id("detail/video/119983"),
            "https://www.cupfox.ai/video/119983.html",
        )

    def test_merge_set_cookie_and_cookie_header(self):
        jar = {}
        self.spider._merge_set_cookie(jar, ["foo=1; Path=/", "bar=2; HttpOnly"])
        self.assertEqual(jar, {"foo": "1", "bar": "2"})
        self.assertEqual(self.spider._cookie_header(jar), "foo=1; bar=2")

    def test_extract_firewall_token(self):
        html = '<script>var token = encrypt("abcXYZ");</script>'
        self.assertEqual(self.spider._extract_firewall_token(html), "abcXYZ")

    @patch("cupfox_spider.random.randint", side_effect=[0, 1, 2, 3])
    def test_firewall_encrypt_returns_base64_text(self, _mock_randint):
        encoded = self.spider._cupfox_firewall_encrypt("PX")
        self.assertEqual(base64.b64decode(encoded).decode("utf-8"), "PwXh7w")

    def test_request_with_firewall_retries_after_robot_verification(self):
        calls = []

        def fake_request(url, method="GET", body=None, headers=None):
            calls.append({"url": url, "method": method, "body": body, "headers": headers or {}})
            if len(calls) == 1:
                return {
                    "status_code": 200,
                    "text": '<div id="verifyBox"></div><script>var token = encrypt("seed");</script>',
                    "headers": {"set-cookie": ["session=abc; Path=/"]},
                }
            if "robot.php" in url:
                self.assertEqual(method, "POST")
                self.assertIn("Cookie", headers)
                self.assertIn("value=", body)
                self.assertIn("token=", body)
                return {
                    "status_code": 200,
                    "text": "ok",
                    "headers": {"set-cookie": ["shield=passed; Path=/"]},
                }
            return {
                "status_code": 200,
                "text": "<html><title>ok</title></html>",
                "headers": {},
            }

        self.spider._request_text = fake_request
        html = self.spider._request_with_firewall("https://www.cupfox.ai/search/test----------1---.html")

        self.assertEqual(html, "<html><title>ok</title></html>")
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[2]["headers"]["Cookie"], "session=abc; shield=passed")

    def test_request_with_firewall_accepts_capitalized_set_cookie_header(self):
        calls = []

        def fake_request(url, method="GET", body=None, headers=None):
            calls.append({"url": url, "method": method, "body": body, "headers": headers or {}})
            if len(calls) == 1:
                return {
                    "status_code": 200,
                    "text": '<div id="verifyBox"></div><script>var token = encrypt("seed");</script>',
                    "headers": {"Set-Cookie": "PHPSESSID=abc123; path=/"},
                }
            if "robot.php" in url:
                self.assertEqual(headers["Cookie"], "PHPSESSID=abc123")
                return {"status_code": 200, "text": '{"msg":"ok"}', "headers": {}}
            return {
                "status_code": 200,
                "text": "<html><title>ok</title></html>",
                "headers": {},
            }

        self.spider._request_text = fake_request
        html = self.spider._request_with_firewall("https://www.cupfox.ai/type/1-2.html")

        self.assertEqual(html, "<html><title>ok</title></html>")
        self.assertEqual(calls[2]["headers"]["Cookie"], "PHPSESSID=abc123")

    def test_extract_player_data_reads_embedded_json(self):
        html = '<script>player_aaaa={"url":"vid-1","from":"lineA","server":"no"};</script>'
        data = self.spider._extract_player_data(html)
        self.assertEqual(data["url"], "vid-1")
        self.assertEqual(data["from"], "lineA")

    def test_extract_player_data_supports_nested_object_literal(self):
        html = """
        <script>
        var player_aaaa={
          "flag":"play",
          "encrypt":0,
          "vod_data":{"vod_name":"八千里路云和月","vod_actor":"王阳,万茜"},
          "url":"DJP5QlL6j66wOTl+NrtIwkJCenh0ZVBlTHJzTWJWd0Y1eTNBd1crTmt5NmpjK05XOTFxb25iSTJ4d2RSUms4YllrVVhSU2xyK0JGcFFZZThibmVqU1BWUFlEMnVWTUpQVmR1Vm9FZHJJWlFaaHNaR3pmTHYwbjVyUE11dkdwbzVOMTJpRFpBK3cvYUl5RnNuQXNaelFZZ0plWVhWYitFenJOMHhUZz09",
          "from":"rb",
          "server":"no"
        };
        </script>
        """
        data = self.spider._extract_player_data(html)
        self.assertEqual(data["encrypt"], 0)
        self.assertEqual(data["vod_data"]["vod_name"], "八千里路云和月")
        self.assertEqual(data["from"], "rb")

    def test_decode2_recovers_shifted_text(self):
        encoded = "QXdCQ2tE"
        self.assertEqual(self.spider._decode2(encoded), "P0")

    def test_home_content_and_home_video_content_parse_cards(self):
        html = """
        <html>
          <nav class="bm-item-list">
            <a href="/type/1.html">电影</a>
            <a href="/type/2.html">电视剧</a>
          </nav>
          <div class="mobile-main">
            <div class="panel">
              <div class="tab-content">
                <div class="movie-list-item">
                  <a href="/movie/foo.html" title="首页片"></a>
                  <img class="Lazy" data-original="/img/foo.jpg" />
                  <span class="movie-item-note">更新至1集</span>
                </div>
                <div class="movie-list-item">
                  <a href="/movie/foo.html" title="首页片"></a>
                  <img class="Lazy" data-original="/img/foo.jpg" />
                </div>
              </div>
            </div>
          </div>
        </html>
        """
        self.spider._request_with_firewall = lambda url: html
        home = self.spider.homeContent(False)
        videos = self.spider.homeVideoContent()

        self.assertEqual(
            home["class"],
            [{"type_id": "1", "type_name": "电影"}, {"type_id": "2", "type_name": "电视剧"}],
        )
        self.assertEqual(len(videos["list"]), 1)
        self.assertEqual(videos["list"][0]["vod_id"], "detail/foo")

    def test_category_and_search_content_return_lists_without_pagecount(self):
        category_html = """
        <div class="movie-list-item">
          <a href="/movie/c1.html" title="分类片"></a>
          <img class="Lazy" data-original="/cate.jpg" />
          <span class="movie-item-score">9.0</span>
        </div>
        """
        search_html = """
        <div class="vod-search-list">
          <div class="box">
            <a class="cover-link" href="/movie/s1.html"></a>
            <img class="Lazy" data-original="/search.jpg" />
            <div class="movie-title">搜索片</div>
            <div class="meta getop">搜索备注</div>
          </div>
        </div>
        """

        self.spider._request_with_firewall = lambda url: category_html if "/type/" in url else search_html
        category = self.spider.categoryContent("1", "2", False, {})
        search = self.spider.searchContent("繁花", False, "3")

        self.assertEqual(category["page"], 2)
        self.assertEqual(category["limit"], 20)
        self.assertNotIn("pagecount", category)
        self.assertEqual(category["list"][0]["vod_id"], "detail/c1")
        self.assertEqual(search["page"], 3)
        self.assertEqual(search["list"][0]["vod_remarks"], "搜索备注")
        self.assertNotIn("pagecount", search)

    def test_category_content_uses_plain_type_path_for_first_page(self):
        seen = []

        def fake_request(url):
            seen.append(url)
            return """
            <div class="movie-list-item">
              <a href="/movie/c1.html" title="分类片"></a>
              <img class="Lazy" data-original="/cate.jpg" />
            </div>
            """

        self.spider._request_with_firewall = fake_request
        self.spider.categoryContent("1", "1", False, {})

        self.assertEqual(seen, ["https://www.cupfox.ai/type/1.html"])

    def test_parse_cards_supports_video_detail_links(self):
        html = """
        <div class="movie-list-item">
          <a href="/video/119983.html" title="挽救计划"></a>
          <div class="Lazy" data-original="/poster.jpg"></div>
          <span class="movie-item-note">正片</span>
        </div>
        """
        items = self.spider._parse_cards(html)

        self.assertEqual(
            items,
            [
                {
                    "vod_id": "detail/video/119983",
                    "vod_name": "挽救计划",
                    "vod_pic": "https://www.cupfox.ai/poster.jpg",
                    "vod_remarks": "正片",
                }
            ],
        )

    def test_detail_content_builds_play_sources(self):
        html = """
        <h1 class="movie-title">详情标题</h1>
        <div class="poster"><img src="/poster.jpg" /></div>
        <div class="summary detailsTxt">这是简介<span class="ectogg">展开</span></div>
        <div class="scroll-content"><a>2026</a></div>
        <div class="info-data">导演<a>张导</a><a>李导</a></div>
        <div class="info-data">演员<a>甲</a><a>乙</a></div>
        <div class="play_source_tab">
          <div class="swiper-slide">线路一</div>
          <div class="swiper-slide">线路二</div>
        </div>
        <div class="play_list_box">
          <ul class="content_playlist">
            <li><a href="/play/p1.html">第1集</a></li>
            <li><a href="/play/p2.html">第2集</a></li>
          </ul>
        </div>
        <div class="play_list_box">
          <ul class="content_playlist">
            <li><a href="/play/p3.html">正片</a></li>
          </ul>
        </div>
        """
        self.spider._request_with_firewall = lambda url: html
        detail = self.spider.detailContent(["detail/d1"])
        vod = detail["list"][0]

        self.assertEqual(vod["vod_name"], "详情标题")
        self.assertEqual(vod["vod_year"], "2026")
        self.assertEqual(vod["vod_director"], "张导,李导")
        self.assertEqual(vod["vod_actor"], "甲,乙")
        self.assertEqual(vod["vod_play_from"], "线路一$$$线路二")
        self.assertIn("第1集$play/p1", vod["vod_play_url"])
        self.assertIn("正片$play/p3", vod["vod_play_url"])

    def test_placeholder_url_detection(self):
        self.assertTrue(self.spider._is_placeholder_url("https://a.example/404.mp4"))
        self.assertTrue(self.spider._is_placeholder_url("https://a.example/v.m3u8?code=403"))
        self.assertFalse(self.spider._is_placeholder_url("https://media.example/video.m3u8"))

    def test_player_content_returns_decoded_api_url(self):
        play_html = '<script>player_aaaa={"url":"vid-99","from":"line","server":"no"};</script>'

        def fake_request(url, method="GET", body=None, headers=None):
            if "foxplay/api.php" in url:
                return {
                    "status_code": 200,
                    "text": '{"data":{"url":"https://media.example/video.m3u8","urlmode":0}}',
                    "headers": {},
                }
            raise AssertionError(url)

        self.spider._request_with_firewall = lambda url: play_html
        self.spider._request_text = fake_request
        result = self.spider.playerContent("线路一", "play/p99", [])

        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://media.example/video.m3u8")
        self.assertIn("muiplayer.php?vid=vid-99", result["header"]["Referer"])

    def test_player_content_falls_back_when_api_returns_placeholder(self):
        play_html = '<script>player_aaaa={"url":"vid-77","from":"line","server":"no"};</script>'

        def fake_request(url, method="GET", body=None, headers=None):
            return {
                "status_code": 200,
                "text": '{"data":{"url":"https://www.cupfox.ai/404.mp4","urlmode":0}}',
                "headers": {},
            }

        self.spider._request_with_firewall = lambda url: play_html
        self.spider._request_text = fake_request
        result = self.spider.playerContent("线路一", "play/p77", [])

        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["url"], "https://www.cupfox.ai/play/p77.html")

    def test_player_content_urlencodes_vid_for_api_request(self):
        play_html = '<script>player_aaaa={"url":"a+b/c==","from":"line","server":"no"};</script>'
        calls = []

        def fake_request(url, method="GET", body=None, headers=None):
            calls.append({"url": url, "method": method, "body": body, "headers": headers or {}})
            if "foxplay/api.php" in url:
                return {
                    "status_code": 200,
                    "text": '{"data":{"url":"https://media.example/video.m3u8","urlmode":0}}',
                    "headers": {},
                }
            raise AssertionError(url)

        self.spider._request_with_firewall = lambda url: play_html
        self.spider._request_text = fake_request
        result = self.spider.playerContent("线路一", "play/p88", [])

        self.assertEqual(result["parse"], 0)
        self.assertEqual(calls[0]["body"], "vid=a%2Bb%2Fc%3D%3D")
        self.assertIn("vid=a%2Bb%2Fc%3D%3D", calls[0]["headers"]["Referer"])

    def test_search_content_returns_empty_result_for_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})

    def test_player_content_falls_back_when_missing_player_data(self):
        self.spider._request_with_firewall = lambda url: "<html></html>"
        result = self.spider.playerContent("线路一", "play/p11", [])
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["url"], "https://www.cupfox.ai/play/p11.html")
