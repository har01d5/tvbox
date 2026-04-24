import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("bbys_spider", str(ROOT / "布布影视.py")).load_module()
Spider = MODULE.Spider


class TestBuBuYingShiSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_classes_and_filters(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["1", "2", "3", "4"],
        )
        self.assertEqual(
            [item["key"] for item in content["filters"]["1"]],
            ["class", "area", "year", "by"],
        )

    @patch("bbys_spider.time.time", return_value=1713523200)
    @patch("bbys_spider.random.randint", side_effect=[8, 37])
    def test_build_app_headers_includes_signed_fields(self, mock_randint, mock_time):
        headers = self.spider._get_app_headers()
        self.assertEqual(headers["x-aid"], "com.sunshine.tv")
        self.assertEqual(headers["x-ave"], "4")
        self.assertEqual(headers["x-time"], "1713523200")
        self.assertEqual(headers["x-nonc"], "837")
        self.assertEqual(len(headers["x-sign"]), 64)

    @patch("bbys_spider.time.time", return_value=1713523200)
    @patch("bbys_spider.random.randint", side_effect=[8, 37])
    def test_build_web_headers_adds_web_specific_fields(self, mock_randint, mock_time):
        headers = self.spider._get_web_headers()
        self.assertEqual(headers["web-sign"], "f65f3a83d6d9ad6f")
        self.assertEqual(headers["X-Client"], "8f3d2a1c7b6e5d4c9a0b1f2e3d4c5b6a")

    def test_generate_years_for_movie_starts_with_current_year_and_includes_ranges(self):
        years = self.spider._generate_years("电影")
        self.assertEqual(years[0], {"n": "全部", "v": ""})
        self.assertEqual(years[1]["n"], str(self.spider.current_year))
        self.assertIn({"n": "2015-2011", "v": "2015-2011"}, years)

    def test_convert_json_to_vods_maps_common_fields(self):
        items = self.spider._convert_json_to_vods(
            [
                {
                    "vod_id": 11,
                    "vod_name": "首页片",
                    "vod_pic": "https://img.example/a.jpg",
                    "vod_duration": "更新至2集",
                    "vod_class": ["剧情", "悬疑"],
                    "vod_year": 2026,
                    "vod_area": "大陆",
                }
            ]
        )
        self.assertEqual(items[0]["vod_id"], "11")
        self.assertEqual(items[0]["type_name"], "剧情/悬疑")
        self.assertEqual(items[0]["vod_year"], "2026")

    @patch.object(Spider, "_request_json")
    def test_home_video_content_reads_home_categories(self, mock_request_json):
        mock_request_json.return_value = {
            "data": {
                "categories": [
                    {
                        "type_id": "1",
                        "type_name": "电影",
                        "videos": [{"vod_id": 7, "vod_name": "首页影片", "vod_pic": "/a.jpg"}],
                    }
                ]
            }
        }
        result = self.spider.homeVideoContent()
        self.assertEqual(result["list"][0]["vod_id"], "7")
        self.assertEqual(result["list"][0]["vod_name"], "首页影片")

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_get_class_list")
    def test_home_video_content_falls_back_to_main_categories(self, mock_get_class_list, mock_request_json):
        mock_request_json.return_value = {"data": {"categories": []}}
        mock_get_class_list.side_effect = [
            {"list": [{"vod_id": "1", "vod_name": "电影片"}]},
            {"list": [{"vod_id": "2", "vod_name": "剧集片"}]},
            {"list": []},
            {"list": []},
        ]
        result = self.spider.homeVideoContent()
        self.assertEqual([item["vod_id"] for item in result["list"]], ["1", "2"])

    @patch.object(Spider, "_request_json")
    def test_category_content_builds_expected_web_request_and_page_shape(self, mock_request_json):
        mock_request_json.return_value = {
            "data": [{"vod_id": 9, "vod_name": "分类片", "vod_pic": "/cate.jpg", "vod_remarks": "HD"}]
        }
        result = self.spider.categoryContent("电影", "2", False, {"area": "大陆", "year": "2025", "by": "score"})
        kwargs = mock_request_json.call_args.kwargs
        self.assertEqual(kwargs["headers"]["web-sign"], "f65f3a83d6d9ad6f")
        self.assertEqual(kwargs["params"]["type_name"], "电影")
        self.assertEqual(kwargs["params"]["page"], 2)
        self.assertEqual(kwargs["params"]["sort"], "score")
        self.assertEqual(result["page"], 2)
        self.assertNotIn("pagecount", result)
        self.assertEqual(result["list"][0]["vod_id"], "9")

    @patch.object(Spider, "_get_class_list")
    def test_category_content_unknown_type_falls_back_to_hot_aggregate(self, mock_get_class_list):
        mock_get_class_list.side_effect = [
            {"list": [{"vod_id": "1", "vod_name": "电影片"}]},
            {"list": [{"vod_id": "2", "vod_name": "剧集片"}]},
            {"list": [{"vod_id": "3", "vod_name": "综艺片"}]},
            {"list": [{"vod_id": "4", "vod_name": "动漫片"}]},
        ]
        result = self.spider.categoryContent("步步影视", "1", False, {})
        self.assertEqual([item["vod_id"] for item in result["list"]], ["1", "2", "3", "4"])

    @patch.object(Spider, "_request_json")
    def test_search_content_skips_blank_keyword_and_builds_app_request(self, mock_request_json):
        blank = self.spider.searchContent("", False, "1")
        self.assertEqual(blank, {"page": 1, "limit": 0, "total": 0, "list": []})
        mock_request_json.assert_not_called()

        mock_request_json.return_value = {
            "data": [{"vod_id": 13, "vod_name": "搜索片", "vod_pic": "/search.jpg"}]
        }
        result = self.spider.searchContent("繁花", False, "3")
        kwargs = mock_request_json.call_args.kwargs
        self.assertEqual(kwargs["params"]["wd"], "繁花")
        self.assertEqual(kwargs["params"]["page"], 3)
        self.assertEqual(kwargs["params"]["limit"], 15)
        self.assertEqual(result["list"][0]["vod_id"], "13")

    def test_clean_html_content_strips_tags_and_keeps_line_breaks(self):
        text = self.spider._clean_html_content("<p>第一段</p><p>第二段<br>第三行</p>")
        self.assertEqual(text, "第一段\n第二段\n第三行")

    def test_build_play_data_packs_group_names_and_urls(self):
        data = self.spider._build_play_data(
            "线路一$$$线路二",
            "第1集$/play/1#第2集$/play/2$$$正片$/movie/main",
        )
        self.assertEqual(data["vod_play_from"], "线路一(2)$$$线路二(1)")
        self.assertIn("第1集$线路一@1@/play/1", data["vod_play_url"])
        self.assertIn("正片$线路二@1@/movie/main", data["vod_play_url"])

    @patch.object(Spider, "_request_json")
    def test_detail_content_uses_vodplayer_from_codes_and_show_names(self, mock_request_json):
        mock_request_json.return_value = {
            "data": [
                {
                    "vod_id": 18,
                    "vod_name": "详情片",
                    "vod_pic": "/detail.jpg",
                    "vod_remarks": "更新至2集",
                    "vod_year": "2026",
                    "vod_area": "大陆",
                    "vod_actor": "甲/乙",
                    "vod_director": "丙",
                    "vod_content": "<p>一段简介</p>",
                    "vod_class": "剧情",
                    "vod_play_from": "rose",
                    "vod_play_url": "第1集$rose_token",
                }
            ],
            "vodplayer": [{"from": "rose", "show": "SE蓝光", "decode_status": "1"}],
        }
        result = self.spider.detailContent(["18"])
        detail = result["list"][0]
        self.assertEqual(detail["vod_id"], "18")
        self.assertEqual(detail["vod_content"], "一段简介")
        self.assertEqual(detail["type_name"], "剧情")
        self.assertEqual(detail["vod_play_from"], "SE蓝光(1)")
        self.assertEqual(detail["vod_play_url"], "第1集$rose@1@rose_token")

    def test_extract_decode_url_accepts_multiple_shapes(self):
        self.assertEqual(self.spider._extract_decode_url({"data": "https://a.example/m3u8"}), "https://a.example/m3u8")
        self.assertEqual(
            self.spider._extract_decode_url({"data": {"url": "https://b.example/m3u8"}}),
            "https://b.example/m3u8",
        )
        self.assertEqual(self.spider._extract_decode_url({"url": "https://c.example/m3u8"}), "https://c.example/m3u8")

    @patch.object(Spider, "_request_json")
    def test_player_content_decodes_encoded_play_id(self, mock_request_json):
        mock_request_json.return_value = {"data": {"url": "https://cdn.example/real.m3u8"}}
        result = self.spider.playerContent("线路一", "线路一@1@/play/1", {})
        kwargs = mock_request_json.call_args.kwargs
        self.assertEqual(kwargs["params"]["url"], "/play/1")
        self.assertEqual(kwargs["params"]["vodFrom"], "线路一")
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["playUrl"], "")
        self.assertEqual(result["url"], "https://cdn.example/real.m3u8")

    @patch.object(Spider, "_request_json")
    def test_player_content_parses_non_binary_decode_status(self, mock_request_json):
        mock_request_json.return_value = {"data": {"url": "https://cdn.example/jd4k.m3u8"}}
        result = self.spider.playerContent("JD蓝光", "JD4K@2@JD-a8fa0064", {})
        kwargs = mock_request_json.call_args.kwargs
        self.assertEqual(kwargs["params"]["url"], "JD-a8fa0064")
        self.assertEqual(kwargs["params"]["vodFrom"], "JD4K")
        self.assertEqual(result["url"], "https://cdn.example/jd4k.m3u8")

    @patch.object(Spider, "_request_json")
    def test_player_content_sets_jx_for_major_video_sites(self, mock_request_json):
        mock_request_json.return_value = {"data": {"url": "https://v.qq.com/x/cover/demo.html"}}
        result = self.spider.playerContent("线路一", "线路一@1@/play/1", {})
        self.assertEqual(result["jx"], 1)

    def test_player_content_passthrough_for_direct_url(self):
        result = self.spider.playerContent("直连", "https://cdn.example/direct.m3u8", {})
        self.assertEqual(result["url"], "https://cdn.example/direct.m3u8")
        self.assertEqual(result["jx"], 0)

    def test_home_content_keeps_reference_filter_values(self):
        movie_filters = self.spider.homeContent(False)["filters"]["1"]
        self.assertIn({"n": "动作", "v": "动作"}, movie_filters[0]["value"])
        self.assertIn({"n": "大陆", "v": "大陆"}, movie_filters[1]["value"])
        self.assertIn({"n": "评分", "v": "score"}, movie_filters[3]["value"])

    @patch.object(Spider, "_request_json")
    def test_detail_content_returns_empty_list_when_payload_missing(self, mock_request_json):
        mock_request_json.return_value = {"data": []}
        self.assertEqual(self.spider.detailContent(["404"]), {"list": []})

    @patch.object(Spider, "_request_json")
    def test_player_content_falls_back_to_raw_input_when_decode_fails(self, mock_request_json):
        mock_request_json.return_value = {}
        result = self.spider.playerContent("线路一", "线路一@1@/play/404", {})
        self.assertEqual(result["url"], "/play/404")

    @patch.object(Spider, "_request_json")
    def test_player_content_marks_disabled_decode_line_as_unplayable(self, mock_request_json):
        mock_request_json.return_value = {
            "code": 0,
            "msg": "线路暂时停用，请稍后再试",
            "data": "JD-2eb205f0c280bdb5b93e14c25d5e72140",
        }
        result = self.spider.playerContent("JD蓝光", "JD4K@2@JD-2eb205f0c280bdb5b93e14c25d5e72140", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "")


if __name__ == "__main__":
    unittest.main()
