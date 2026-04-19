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

    def test_extract_player_data_reads_embedded_json(self):
        html = '<script>player_aaaa={"url":"vid-1","from":"lineA","server":"no"};</script>'
        data = self.spider._extract_player_data(html)
        self.assertEqual(data["url"], "vid-1")
        self.assertEqual(data["from"], "lineA")

    def test_decode2_recovers_shifted_text(self):
        encoded = "QXdCQ2tE"
        self.assertEqual(self.spider._decode2(encoded), "P0")
