import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("shuangxing_spider", str(ROOT / "双星.py")).load_module()
Spider = MODULE.Spider


class FakeResponse:
    def __init__(self, status_code=200, text="", cookies=None):
        self.status_code = status_code
        self.text = text
        self.cookies = cookies or {}
        self.headers = {}
        self.url = ""


class TestShuangXingSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()

    def test_home_content_exposes_reference_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("ju", "国剧"),
                ("zy", "综艺"),
                ("mv", "电影"),
                ("rh", "日韩"),
                ("ym", "英美"),
                ("wj", "外剧"),
                ("dm", "动漫"),
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    @patch.object(Spider, "fetch")
    def test_init_collects_cookie_pairs_and_headers_include_cookie(self, mock_fetch):
        mock_fetch.return_value = FakeResponse(cookies={"foo": "bar", "token": "xyz"})
        self.spider.init()
        self.assertEqual(self.spider.cookie, "foo=bar; token=xyz")
        self.assertEqual(self.spider._headers()["cookie"], "foo=bar; token=xyz")

    def test_headers_without_cookie_keep_base_headers_only(self):
        self.assertEqual(
            self.spider._headers(),
            {
                "User-Agent": Spider.UA,
                "Referer": Spider.BASE_URL,
            },
        )

    def test_detect_pan_type_returns_expected_keys(self):
        self.assertEqual(self.spider._detect_pan_type("https://pan.quark.cn/s/demo"), "quark")
        self.assertEqual(self.spider._detect_pan_type("https://www.alipan.com/s/demo"), "ali")
        self.assertEqual(self.spider._detect_pan_type("https://example.com/video"), "")


if __name__ == "__main__":
    unittest.main()
