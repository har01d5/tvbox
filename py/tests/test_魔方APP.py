import unittest
from datetime import datetime
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("mofang_spider", str(ROOT / "魔方APP.py")).load_module()
Spider = MODULE.Spider


class TestMoFangAppSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_api_url_uses_default_getappapi_path(self):
        self.assertEqual(
            self.spider._build_api_url("initV119"),
            "http://www.613mf4k12.top/api.php/getappapi.index/initV119",
        )

    def test_aes_encrypt_and_decrypt_round_trip(self):
        encrypted = self.spider._aes_encrypt('{"msg":"ok"}')
        self.assertNotEqual(encrypted, '{"msg":"ok"}')
        self.assertEqual(self.spider._aes_decrypt(encrypted), '{"msg":"ok"}')

    def test_replace_code_normalizes_common_ocr_misreads(self):
        self.assertEqual(self.spider._replace_code("5y6口"), "5960")

    @patch.object(Spider, "post")
    def test_api_post_returns_none_when_upstream_payload_is_not_json(self, mock_post):
        mock_post.return_value = SimpleNamespace(text="<html>blocked</html>")
        self.assertIsNone(self.spider._api_post("initV119"))

    @patch.object(Spider, "_api_post")
    def test_home_content_filters_categories_merges_area_and_inserts_current_year(self, mock_api_post):
        mock_api_post.return_value = {
            "type_list": [
                {
                    "type_id": "0",
                    "type_name": "全部",
                    "recommend_list": [],
                    "filter_type_list": [],
                },
                {
                    "type_id": "3",
                    "type_name": "综艺",
                    "recommend_list": [{"vod_id": "z1"}],
                    "filter_type_list": [
                        {"name": "area", "list": ["全部", "中国大陆", "香港"]},
                        {"name": "year", "list": ["全部", "2025", "2024"]},
                        {"name": "sort", "list": ["最新", "最热"]},
                    ],
                },
                {
                    "type_id": "1",
                    "type_name": "电影",
                    "recommend_list": [{"vod_id": "m1"}],
                    "filter_type_list": [],
                },
            ],
            "config": {},
        }
        content = self.spider.homeContent(False)
        self.assertEqual([item["type_name"] for item in content["class"]], ["电影", "综艺"])
        self.assertEqual(content["list"], [{"vod_id": "z1"}, {"vod_id": "m1"}])
        area_values = content["filters"]["3"][0]["value"]
        year_values = content["filters"]["3"][1]["value"]
        self.assertEqual(area_values[1], {"n": "大陆", "v": "大陆"})
        self.assertIn({"n": str(datetime.now().year), "v": str(datetime.now().year)}, year_values)
        self.assertEqual(content["filters"]["3"][2]["key"], "by")

    @patch.object(Spider, "_api_post")
    def test_category_content_maps_by_to_sort_and_omits_pagecount(self, mock_api_post):
        mock_api_post.return_value = {"recommend_list": [{"vod_id": "movie-1", "vod_name": "分类片"}]}
        result = self.spider.categoryContent(
            "1",
            "2",
            False,
            {"area": "香港", "year": "2025", "by": "最热", "lang": "粤语", "class": "动作"},
        )
        self.assertEqual(
            mock_api_post.call_args.args,
            (
                "typeFilterVodList",
                {
                    "type_id": "1",
                    "page": "2",
                    "area": "香港",
                    "year": "2025",
                    "sort": "最热",
                    "lang": "粤语",
                    "class": "动作",
                },
            ),
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_id"], "movie-1")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_api_post")
    def test_category_content_merges_mainland_results_and_deduplicates(self, mock_api_post):
        mock_api_post.side_effect = [
            {"recommend_list": [{"vod_id": "a"}, {"vod_id": "b"}]},
            {"recommend_list": [{"vod_id": "b"}, {"vod_id": "c"}]},
            {"recommend_list": [{"vod_id": "c"}, {"vod_id": "d"}]},
        ]
        result = self.spider.categoryContent("1", "1", False, {"area": "大陆"})
        self.assertEqual([item["vod_id"] for item in result["list"]], ["a", "b", "c", "d"])
        self.assertEqual(
            [call.args[1]["area"] for call in mock_api_post.call_args_list],
            ["中国大陆", "大陆", "内地"],
        )

    @patch.object(Spider, "_api_post")
    def test_search_content_filters_reserved_category_and_non_matching_items(self, mock_api_post):
        mock_api_post.return_value = {
            "search_list": [
                {"vod_id": "1", "vod_name": "繁花", "vod_pic": "p1", "vod_year": "2024", "vod_class": "剧情"},
                {"vod_id": "2", "vod_name": "别的片", "vod_pic": "p2", "vod_year": "2024", "vod_class": "屏蔽预留"},
                {"vod_id": "3", "vod_name": "完全无关", "vod_pic": "p3", "vod_year": "2023", "vod_class": "动作"},
            ]
        }
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(
            result["list"],
            [{"vod_id": "1", "vod_name": "繁花", "vod_pic": "p1", "vod_remarks": "2024 剧情"}],
        )
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_get_verification_code")
    @patch.object(Spider, "_api_post")
    def test_search_content_returns_empty_list_when_verify_required_but_ocr_fails(self, mock_api_post, mock_verify):
        mock_api_post.return_value = {"config": {"system_search_verify_status": 1}, "type_list": []}
        mock_verify.return_value = None
        self.spider.search_verify = True
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(result["list"], [])
        self.assertEqual(result.get("msg"), "验证码获取失败")

    @patch.object(Spider, "_api_post")
    def test_detail_content_falls_back_to_second_endpoint_sorts_lines_and_blocks_disabled_lines(self, mock_api_post):
        mock_api_post.side_effect = [
            None,
            {
                "vod": {
                    "vod_name": "示例影片",
                    "vod_pic": "poster.jpg",
                    "vod_remarks": "更新至10集",
                    "vod_content": "一段剧情",
                    "vod_actor": "演员甲/演员乙",
                    "vod_director": "导演甲",
                    "vod_year": "2025",
                    "vod_area": "中国大陆",
                },
                "vod_play_list": [
                    {
                        "player_info": {
                            "show": "腾讯视频",
                            "parse": "https://parser-a/?url=",
                            "player_parse_type": "1",
                            "parse_type": "1",
                        },
                        "urls": [{"name": "正片", "url": "https%3A%2F%2Fplay-a", "token": "tk-a"}],
                    },
                    {
                        "player_info": {
                            "show": "防走丢加群",
                            "parse": "https://parser-b/?url=",
                            "player_parse_type": "1",
                            "parse_type": "0",
                        },
                        "urls": [{"name": "备用", "url": "https%3A%2F%2Fplay-b", "token": "tk-b"}],
                    },
                    {
                        "player_info": {
                            "show": "YY",
                            "parse": "https://parser-c/?url=",
                            "player_parse_type": "2",
                            "parse_type": "2",
                        },
                        "urls": [{"name": "蓝光", "url": "https%3A%2F%2Fplay-c", "token": "tk-c"}],
                    },
                ],
            },
        ]
        result = self.spider.detailContent(["123"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "123")
        self.assertEqual(vod["vod_name"], "示例影片")
        self.assertEqual(vod["vod_year"], "2025年")
        self.assertEqual(vod["vod_play_from"], "⭐️腾讯视频$$$1线")
        self.assertEqual(
            vod["vod_play_url"],
            "正片$腾讯视频@@direct@@https://parser-a/?url=,https%3A%2F%2Fplay-a,token+tk-a,1,1"
            "$$$备用$1线@@direct@@https://parser-b/?url=,https%3A%2F%2Fplay-b,token+tk-b,1,0",
        )

    @patch.object(Spider, "fetch")
    def test_get_verification_code_fetches_image_calls_ocr_and_returns_digits(self, mock_fetch):
        image_response = SimpleNamespace(content=b"fake-image")
        ocr_response = SimpleNamespace(text="5y6口")
        mock_fetch.side_effect = [image_response, ocr_response]
        result = self.spider._get_verification_code()
        self.assertEqual(result["code"], "5960")
        self.assertIn("uuid", result)

    def test_player_content_returns_direct_url_for_parse_type_zero(self):
        result = self.spider.playerContent(
            "⭐️腾讯视频",
            "腾讯视频@@direct@@https://parser/?url=,https%3A%2F%2Fvideo.example%2Fraw.m3u8,token+abc,1,0",
            "",
        )
        self.assertEqual(
            result,
            {
                "parse": 0,
                "jx": 0,
                "url": "https://video.example/raw.m3u8",
                "header": {"User-Agent": "Dalvik/2.1.0 (Linux; Android 14)"},
            },
        )

    def test_player_content_returns_parser_url_for_parse_type_two(self):
        result = self.spider.playerContent(
            "⭐️腾讯视频",
            "腾讯视频@@direct@@https://parser/?url=,https%3A%2F%2Fvideo.example%2Fneed-jx.m3u8,token+abc,1,2",
            "",
        )
        self.assertEqual(
            result,
            {
                "parse": 1,
                "jx": 1,
                "url": "https://parser/?url=https://video.example/need-jx.m3u8",
                "header": {"User-Agent": "Dalvik/2.1.0 (Linux; Android 14)"},
            },
        )

    @patch.object(Spider, "fetch")
    def test_player_content_uses_player_parse_type_two_direct_json(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(text='{"url":"https://video.example/direct.m3u8"}')
        result = self.spider.playerContent(
            "⭐️腾讯视频",
            "腾讯视频@@direct@@https://parser/?url=,https%3A%2F%2Fvideo.example%2Fwrapped,token+abc,2,1",
            "",
        )
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://video.example/direct.m3u8")

    @patch.object(Spider, "_api_post")
    def test_player_content_falls_back_to_vod_parse(self, mock_api_post):
        mock_api_post.return_value = {"json": '{"url":"https://video.example/final.m3u8"}'}
        result = self.spider.playerContent(
            "⭐️腾讯视频",
            "腾讯视频@@direct@@https://parser/?url=,https%3A%2F%2Fvideo.example%2Fencrypted,token+abc,1,1",
            "",
        )
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://video.example/final.m3u8")
        self.assertEqual(mock_api_post.call_args.args[0], "vodParse")
