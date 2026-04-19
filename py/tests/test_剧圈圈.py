import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("juquanquan_spider", str(ROOT / "剧圈圈.py")).load_module()
Spider = MODULE.Spider


class TestJuQuanQuanSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["dianying", "juji", "dongman", "zongyi", "duanju"],
        )

    def test_encode_and_decode_detail_and_play_ids(self):
        self.assertEqual(self.spider._encode_vod_id("/vod/123.html"), "vod/123")
        self.assertEqual(self.spider._decode_vod_id("vod/123"), "https://www.jqqzx.cc/vod/123.html")
        self.assertEqual(self.spider._encode_play_id("/play/123-1-2.html"), "play/123-1-2")
        self.assertEqual(self.spider._decode_play_id("play/123-1-2"), "https://www.jqqzx.cc/play/123-1-2.html")

    def test_parse_search_list_maps_items_to_compact_vod_ids(self):
        payload = '{"list":[{"id":"888","name":"搜索影片","pic":"https://img.example/888.jpg"}]}'
        self.assertEqual(
            self.spider._parse_search_list(payload),
            [
                {
                    "vod_id": "vod/888",
                    "vod_name": "搜索影片",
                    "vod_pic": "https://img.example/888.jpg",
                    "vod_remarks": "",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
