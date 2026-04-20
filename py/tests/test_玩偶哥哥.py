import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("wanougege_spider", str(ROOT / "玩偶哥哥.py")).load_module()
Spider = MODULE.Spider


class TestWanOuGeGeSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_all_eight_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("1", "玩偶电影"),
                ("2", "玩偶剧集"),
                ("3", "玩偶动漫"),
                ("4", "玩偶综艺"),
                ("44", "臻彩视界"),
                ("6", "玩偶短剧"),
                ("5", "玩偶音乐"),
                ("46", "玩偶纪录"),
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_and_fix_urls(self):
        self.assertEqual(self.spider._build_url("/voddetail/1.html"), "http://wogg.xxooo.cf/voddetail/1.html")
        self.assertEqual(
            self.spider._fix_img_url("/db.php?url=https://img.example/poster.jpg"),
            "http://wogg.xxooo.cf/db.php?url=https://img.example/poster.jpg",
        )
        self.assertEqual(
            self.spider._fix_img_url("https://gimg1.baidu.com/gimg/?src=data:image/png;base64,AAAA"),
            "",
        )

    def test_detect_pan_type_returns_type_and_title(self):
        self.assertEqual(self.spider._detect_pan_type("https://pan.baidu.com/s/demo"), ("baidu", "百度资源"))
        self.assertEqual(self.spider._detect_pan_type("https://pan.quark.cn/s/demo"), ("quark", "夸克资源"))
        self.assertEqual(self.spider._detect_pan_type("https://example.com/video"), ("", ""))
