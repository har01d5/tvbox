import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("ruyi_spider", str(ROOT / "如意资源.py")).load_module()
Spider = MODULE.Spider


class FakeResponse:
    def __init__(self, status_code=200, text="{}"):
        self.status_code = status_code
        self.text = text
        self.encoding = "utf-8"


class TestRuYiSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_returns_hardcoded_classes_and_filters(self):
        result = self.spider.homeContent(False)
        class_ids = [item["type_id"] for item in result["class"]]
        self.assertEqual(class_ids, ["1", "2", "3", "4", "35", "36"])
        self.assertEqual(result["filters"]["1"][0]["key"], "type")
        self.assertEqual(result["filters"]["1"][0]["value"][0], {"n": "动作片", "v": "7"})
        self.assertEqual(result["filters"]["2"][0]["value"][0], {"n": "国产剧", "v": "13"})
        self.assertEqual(result["filters"]["35"], [])
        self.assertEqual(result["list"], [])

    def test_get_pic_url_handles_empty_absolute_and_relative_values(self):
        self.assertEqual(self.spider._get_pic_url(""), "")
        self.assertEqual(self.spider._get_pic_url("<nil>"), "")
        self.assertEqual(
            self.spider._get_pic_url("https://img.example.com/poster.jpg"),
            "https://img.example.com/poster.jpg",
        )
        self.assertEqual(
            self.spider._get_pic_url("/upload/poster.jpg"),
            "https://ps.ryzypics.com/upload/poster.jpg",
        )

    @patch.object(Spider, "fetch")
    def test_request_json_falls_back_to_second_api_after_failure(self, mock_fetch):
        mock_fetch.side_effect = [
            FakeResponse(status_code=500, text=""),
            FakeResponse(
                text=(
                    '{"list":[{"vod_id":"9","vod_name":"后备命中","vod_pic":"/poster.jpg",'
                    '"vod_remarks":"HD","vod_year":"2026","type_id":"7"}]}'
                )
            ),
        ]
        result = self.spider._request_json({"ac": "list", "pg": "1", "pagesize": "20"})
        self.assertEqual(result["list"][0]["vod_name"], "后备命中")
        self.assertEqual(mock_fetch.call_count, 2)
        first_url = mock_fetch.call_args_list[0].args[0]
        second_url = mock_fetch.call_args_list[1].args[0]
        self.assertIn("https://cj.rycjapi.com/api.php/provide/vod", first_url)
        self.assertIn("https://cj.rytvapi.com/api.php/provide/vod", second_url)

    @patch.object(Spider, "_request_json")
    def test_home_video_content_maps_recommend_list(self, mock_request_json):
        mock_request_json.return_value = {
            "list": [
                {
                    "vod_id": "101",
                    "vod_name": "推荐影片",
                    "vod_pic": "/cover.jpg",
                    "vod_remarks": "更新至1集",
                    "vod_year": "2025",
                    "type_id": "7",
                }
            ]
        }
        result = self.spider.homeVideoContent()
        self.assertEqual(
            result,
            {
                "list": [
                    {
                        "vod_id": "101",
                        "vod_name": "推荐影片",
                        "vod_pic": "https://ps.ryzypics.com/cover.jpg",
                        "vod_remarks": "更新至1集",
                        "vod_year": "2025",
                        "type_id": "7",
                    }
                ]
            },
        )
        self.assertEqual(mock_request_json.call_args.args[0], {"ac": "list", "pg": "1", "pagesize": "20"})

    @patch.object(Spider, "_request_json")
    def test_home_video_content_enriches_missing_cover_from_videolist(self, mock_request_json):
        mock_request_json.side_effect = [
            {
                "list": [
                    {
                        "vod_id": "101",
                        "vod_name": "推荐影片",
                        "vod_pic": "",
                        "vod_remarks": "更新至1集",
                        "vod_year": "2025",
                        "type_id": "7",
                    }
                ]
            },
            {
                "list": [
                    {
                        "vod_id": "101",
                        "vod_pic": "/detail-cover.jpg",
                    }
                ]
            },
        ]
        result = self.spider.homeVideoContent()
        self.assertEqual(result["list"][0]["vod_pic"], "https://ps.ryzypics.com/detail-cover.jpg")
        self.assertEqual(
            mock_request_json.call_args_list[1].args[0],
            {"ac": "videolist", "ids": "101"},
        )

    @patch.object(Spider, "_request_json")
    def test_category_content_uses_default_sub_type_for_main_class(self, mock_request_json):
        mock_request_json.side_effect = [
            {
                "list": [
                    {
                        "vod_id": "202",
                        "vod_name": "动作电影",
                        "vod_pic": "",
                        "vod_remarks": "HD",
                        "vod_year": "2024",
                        "type_id": "7",
                    }
                ]
            },
            {"list": []},
        ]
        result = self.spider.categoryContent("1", "2", False, {})
        self.assertEqual(
            mock_request_json.call_args_list[0].args[0],
            {"ac": "list", "t": "7", "pg": "2", "pagesize": "20"},
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["limit"], 20)
        self.assertEqual(result["list"][0]["vod_id"], "202")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_json")
    def test_category_content_prefers_extend_type(self, mock_request_json):
        mock_request_json.return_value = {"list": []}
        self.spider.categoryContent("1", "1", False, {"type": "10"})
        self.assertEqual(mock_request_json.call_args.args[0]["t"], "10")

    def test_search_content_returns_empty_for_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "limit": 30, "total": 0, "list": []})

    @patch.object(Spider, "_request_json")
    def test_search_content_filters_titles_by_keyword(self, mock_request_json):
        mock_request_json.return_value = {
            "list": [
                {
                    "vod_id": "301",
                    "vod_name": "繁花",
                    "vod_pic": "/a.jpg",
                    "vod_remarks": "完结",
                    "vod_year": "2024",
                    "type_id": "13",
                },
                {
                    "vod_id": "302",
                    "vod_name": "狂飙",
                    "vod_pic": "/b.jpg",
                    "vod_remarks": "完结",
                    "vod_year": "2023",
                    "type_id": "13",
                },
            ]
        }
        result = self.spider.searchContent("繁花", False, "3")
        self.assertEqual(mock_request_json.call_args.args[0], {"ac": "list", "wd": "繁花", "pg": "3", "pagesize": "30"})
        self.assertEqual(result["page"], 3)
        self.assertEqual(
            result["list"],
            [
                {
                    "vod_id": "301",
                    "vod_name": "繁花",
                    "vod_pic": "https://ps.ryzypics.com/a.jpg",
                    "vod_remarks": "完结",
                    "vod_year": "2024",
                    "type_id": "13",
                }
            ],
        )

    @patch.object(Spider, "_request_json")
    def test_detail_content_maps_metadata_and_play_groups(self, mock_request_json):
        mock_request_json.return_value = {
            "list": [
                {
                    "vod_id": "888",
                    "vod_name": "示例剧",
                    "vod_pic": "/detail.jpg",
                    "type_name": "国产剧",
                    "vod_year": "2026",
                    "vod_area": "大陆",
                    "vod_remarks": "更新至2集",
                    "vod_actor": "张三,李四",
                    "vod_director": "导演甲",
                    "vod_content": "一段简介",
                    "vod_play_from": "如意线路,备用线路",
                    "vod_play_url": "第1集$https://cdn.example.com/1.m3u8#第2集$https://parser.example.com/play/2",
                }
            ]
        }
        result = self.spider.detailContent(["888"])
        vod = result["list"][0]
        self.assertEqual(mock_request_json.call_args.args[0], {"ac": "videolist", "ids": "888"})
        self.assertEqual(vod["vod_id"], "888")
        self.assertEqual(vod["vod_pic"], "https://ps.ryzypics.com/detail.jpg")
        self.assertEqual(vod["type_name"], "国产剧")
        self.assertEqual(vod["vod_play_from"], "如意线路$$$备用线路")
        self.assertEqual(
            vod["vod_play_url"],
            (
                "第1集$https://cdn.example.com/1.m3u8#第2集$https://parser.example.com/play/2$$$"
                "第1集$https://cdn.example.com/1.m3u8#第2集$https://parser.example.com/play/2"
            ),
        )

    def test_detail_content_returns_empty_for_blank_id(self):
        self.assertEqual(self.spider.detailContent([""]), {"list": []})

    def test_parse_play_groups_skips_invalid_entries_and_fills_missing_names(self):
        play_from, play_url = self.spider._parse_play_groups(
            "主线",
            "$https://cdn.example.com/a.m3u8#预告$#https://cdn.example.com/b.mp4",
        )
        self.assertEqual(play_from, "主线")
        self.assertEqual(play_url, "第1集$https://cdn.example.com/a.m3u8#第3集$https://cdn.example.com/b.mp4")

    def test_player_content_returns_direct_media_url(self):
        result = self.spider.playerContent("如意线路", "https://cdn.example.com/1.m3u8", {})
        self.assertEqual(
            result,
            {"parse": 0, "playUrl": "", "url": "https://cdn.example.com/1.m3u8", "header": {}},
        )

    def test_player_content_returns_parser_url_for_non_media_link(self):
        result = self.spider.playerContent("如意线路", "https://parser.example.com/play/2", {})
        self.assertEqual(
            result,
            {"parse": 1, "playUrl": "", "url": "https://parser.example.com/play/2", "header": {}},
        )

    @patch.object(Spider, "fetch")
    def test_request_json_returns_empty_dict_when_all_apis_fail(self, mock_fetch):
        mock_fetch.side_effect = [
            FakeResponse(status_code=500, text=""),
            FakeResponse(status_code=200, text="{bad json"),
            FakeResponse(status_code=404, text=""),
        ]
        self.assertEqual(self.spider._request_json({"ac": "list"}), {})

    @patch.object(Spider, "fetch")
    def test_request_json_continues_when_first_api_raises(self, mock_fetch):
        mock_fetch.side_effect = [
            RuntimeError("boom"),
            FakeResponse(text='{"list":[{"vod_id":"777","vod_name":"异常后命中"}]}'),
        ]
        result = self.spider._request_json({"ac": "list", "pg": "1"})
        self.assertEqual(result["list"][0]["vod_id"], "777")
        self.assertEqual(mock_fetch.call_count, 2)

    @patch.object(Spider, "_request_json")
    def test_home_video_content_filters_invalid_vod_rows(self, mock_request_json):
        mock_request_json.return_value = {
            "list": [
                {"vod_id": "0", "vod_name": "无效", "vod_pic": "", "vod_remarks": "", "vod_year": "", "type_id": ""},
                {"vod_id": "", "vod_name": "空ID", "vod_pic": "", "vod_remarks": "", "vod_year": "", "type_id": ""},
                {"vod_id": "501", "vod_name": "", "vod_pic": "null", "vod_remarks": "", "vod_year": "2022", "type_id": "7"},
            ]
        }
        result = self.spider.homeVideoContent()
        self.assertEqual(
            result["list"],
            [
                {
                    "vod_id": "501",
                    "vod_name": "未知标题",
                    "vod_pic": "",
                    "vod_remarks": "2022",
                    "vod_year": "2022",
                    "type_id": "7",
                }
            ],
        )

    def test_player_content_returns_empty_payload_for_blank_id(self):
        self.assertEqual(
            self.spider.playerContent("如意线路", "", {}),
            {"parse": 0, "playUrl": "", "url": "", "header": {}},
        )


if __name__ == "__main__":
    unittest.main()
