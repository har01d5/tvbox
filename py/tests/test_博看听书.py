import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("bookan_tingshu_spider", str(ROOT / "博看听书.py")).load_module()
Spider = MODULE.Spider


class TestBookanTingShuSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    @patch.object(Spider, "_fetch_category_books")
    def test_home_content_returns_sorted_classes_and_aggregated_list(self, mock_fetch_category_books):
        mock_fetch_category_books.side_effect = [
            [{"id": "11", "name": "相声一", "cover": "11.jpg", "author": "甲"}],
            [{"id": "12", "name": "国学一", "cover": "12.jpg", "author": "乙"}],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ]
        result = self.spider.homeContent(False)
        self.assertEqual(result["class"][0], {"type_id": "1319", "type_name": "相声评书"})
        self.assertEqual(result["class"][1], {"type_id": "1320", "type_name": "国学经典"})
        self.assertEqual([item["vod_id"] for item in result["list"]], ["11", "12"])
        self.assertEqual(result["list"][0]["vod_remarks"], "甲 相声评书")

    @patch.object(Spider, "homeContent")
    def test_home_video_content_reuses_home_content_list(self, mock_home_content):
        mock_home_content.return_value = {"class": [], "list": [{"vod_id": "1"}]}
        self.assertEqual(self.spider.homeVideoContent(), {"list": [{"vod_id": "1"}]})

    @patch.object(Spider, "_api_get")
    def test_category_content_maps_books_and_total(self, mock_api_get):
        mock_api_get.return_value = {
            "data": {
                "list": [{"id": "21", "name": "故事书", "cover": "21.jpg", "author": "丙"}],
                "total": 30,
            }
        }
        result = self.spider.categoryContent("1303", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["limit"], 24)
        self.assertEqual(result["total"], 30)
        self.assertEqual(result["list"][0]["vod_id"], "21")
        self.assertEqual(mock_api_get.call_args.args[0], "/voice/book/list")
        self.assertEqual(mock_api_get.call_args.args[1]["page"], 2)

    def test_category_content_returns_empty_for_unknown_category(self):
        result = self.spider.categoryContent("9999", "1", False, {})
        self.assertEqual(result, {"page": 1, "limit": 24, "total": 0, "list": []})

    @patch.object(Spider, "_search_get")
    def test_search_content_maps_results(self, mock_search_get):
        mock_search_get.return_value = {
            "data": {
                "list": [
                    {"id": "31", "name": "三国演义", "cover": "31.jpg", "author": "播讲A"},
                    {"id": "32", "title": "水浒传", "cover": "32.jpg", "author": "播讲B"},
                ],
                "total": 25,
            }
        }
        result = self.spider.searchContent("名著", False, "2")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["limit"], 20)
        self.assertEqual(result["total"], 25)
        self.assertEqual([item["vod_id"] for item in result["list"]], ["31", "32"])
        self.assertEqual(mock_search_get.call_args.args[0], "/api/v3/voice/book")
        self.assertEqual(mock_search_get.call_args.args[1]["keyword"], "名著")

    def test_search_content_returns_empty_for_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "limit": 0, "total": 0, "list": []})

    @patch.object(Spider, "fetch")
    def test_api_get_builds_url_and_parses_json(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(status_code=200, text='{"data":{"list":[{"id":"41"}]}}')
        payload = self.spider._api_get("/voice/book/list", {"page": 3, "category_id": "1303"})
        self.assertEqual(payload["data"]["list"][0]["id"], "41")
        self.assertIn("page=3", mock_fetch.call_args.args[0])
        self.assertEqual(mock_fetch.call_args.kwargs["headers"]["User-Agent"], self.spider.headers["User-Agent"])

    @patch.object(Spider, "_api_get")
    def test_fetch_album_units_merges_multiple_pages(self, mock_api_get):
        mock_api_get.side_effect = [
            {"data": {"list": [{"title": "第一集", "file": "https://audio/1.mp3"}], "total": 201}},
            {"data": {"list": [{"title": "第二集", "file": "https://audio/2.mp3"}], "total": 201}},
        ]
        items = self.spider._fetch_album_units("99")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1]["title"], "第二集")
        self.assertEqual(mock_api_get.call_args_list[1].args[1]["page"], 2)

    @patch.object(Spider, "_fetch_album_info")
    @patch.object(Spider, "_find_album_from_categories")
    @patch.object(Spider, "_fetch_album_units")
    def test_detail_content_builds_play_url(self, mock_fetch_album_units, mock_find_album, mock_fetch_album_info):
        mock_find_album.return_value = {"vod_name": "分类标题", "vod_pic": "cover.jpg", "vod_author": "作者甲", "found": True}
        mock_fetch_album_info.return_value = {
            "success": True,
            "data": {
                "vod_name": "接口标题",
                "vod_pic": "api.jpg",
                "vod_author": "接口作者",
                "vod_desc": "简介",
                "created_at": "2026-03-07",
                "updated_at": "2026-03-08",
            },
        }
        mock_fetch_album_units.return_value = [
            {"title": "第一集", "file": "https://audio/1.mp3"},
            {"title": "第二集", "file": "https://audio/2.mp3"},
        ]
        result = self.spider.detailContent(["88"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "88")
        self.assertEqual(vod["vod_name"], "分类标题")
        self.assertEqual(vod["vod_play_from"], "博看听书")
        self.assertEqual(vod["vod_play_url"], "1.第一集$https://audio/1.mp3#2.第二集$https://audio/2.mp3")
        self.assertEqual(vod["vod_year"], "2026年")
        self.assertEqual(vod["vod_remarks"], "作者甲 共2集")

    @patch.object(Spider, "_fetch_album_info")
    @patch.object(Spider, "_find_album_from_categories")
    @patch.object(Spider, "_fetch_album_units")
    def test_detail_content_falls_back_to_album_info_when_category_misses(
        self,
        mock_fetch_album_units,
        mock_find_album,
        mock_fetch_album_info,
    ):
        mock_find_album.return_value = {"vod_name": "", "vod_pic": "", "vod_author": "", "found": False}
        mock_fetch_album_info.return_value = {
            "success": True,
            "data": {
                "vod_name": "接口标题",
                "vod_pic": "api.jpg",
                "vod_author": "接口作者",
                "vod_desc": "简介",
                "created_at": "2026-03-07",
                "updated_at": "2026-03-08",
            },
        }
        mock_fetch_album_units.return_value = [{"title": "第一集", "file": "https://audio/1.mp3"}]
        vod = self.spider.detailContent(["89"])["list"][0]
        self.assertEqual(vod["vod_name"], "接口标题")
        self.assertEqual(vod["vod_pic"], "api.jpg")
        self.assertEqual(vod["vod_remarks"], "接口作者 共1集")

    def test_player_content_returns_direct_audio_url(self):
        result = self.spider.playerContent("博看听书", "https://audio/1.mp3", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://audio/1.mp3")
        self.assertEqual(result["header"]["User-Agent"], self.spider.headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()
