import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


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

    def test_parse_cards_extracts_compact_vod_ids(self):
        html = """
        <a class="module-poster-item module-item" href="/vod/123.html">
          <img data-original="/cover.jpg" />
          <div class="module-poster-item-title">示例影片</div>
          <div class="module-item-note">更新至1集</div>
        </a>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "vod/123",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.jqqzx.cc/cover.jpg",
                    "vod_remarks": "更新至1集",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_home_video_content_limits_recommendations(self, mock_request_html):
        mock_request_html.return_value = "".join(
            f'<a class="module-poster-item module-item" href="/vod/{index}.html"><div class="module-poster-item-title">影片{index}</div></a>'
            for index in range(1, 45)
        )
        result = self.spider.homeVideoContent()
        self.assertEqual(len(result["list"]), 40)
        self.assertEqual(result["list"][0]["vod_id"], "vod/1")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item module-item" href="/vod/456.html">
          <div class="module-poster-item-title">分类影片</div>
        </a>
        """
        result = self.spider.categoryContent("juji", "2", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.jqqzx.cc/type/juji/page/2.html")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["pagecount"], 3)
        self.assertEqual(result["list"][0]["vod_id"], "vod/456")

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_suggest_api(self, mock_request_html):
        mock_request_html.return_value = '{"list":[{"id":"777","name":"搜索结果","pic":"/pic.jpg"}]}'
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.jqqzx.cc/index.php/ajax/suggest?mid=1&wd=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["list"][0]["vod_id"], "vod/777")
        self.assertEqual(result["pagecount"], 1)


if __name__ == "__main__":
    unittest.main()
