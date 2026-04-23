import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("butailing_spider", str(ROOT / "不太灵.py")).load_module()
Spider = MODULE.Spider


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"


class TestBuTaiLingSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_returns_fixed_categories_and_filters(self):
        with patch.object(
            Spider,
            "_request_api",
            return_value={"t1": [{"title": "动作"}], "t2": [{"title": "中国"}], "t3": [], "t4": [], "t5": []},
        ):
            content = self.spider.homeContent(False)

        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["1", "2", "3", "4", "5"],
        )
        self.assertIn("1", content["filters"])
        self.assertIn("2", content["filters"])
        self.assertEqual(content["filters"]["1"][0]["key"], "sc")

    @patch.object(Spider, "_request_api")
    def test_home_video_content_requests_recent_hot_list(self, mock_request_api):
        mock_request_api.return_value = [
            {"doub_id": 11, "title": "示例电影", "image": "https://img.test/poster.jpg", "ejs": "HD"}
        ]
        content = self.spider.homeVideoContent()
        self.assertEqual(mock_request_api.call_args.args[0], "getVideoList")
        self.assertEqual(mock_request_api.call_args.args[1]["sc"], "3")
        self.assertEqual(content["list"][0]["vod_id"], "11")
        self.assertEqual(content["list"][0]["vod_remarks"], "HD")

    def test_build_api_url_appends_credentials(self):
        url = self.spider._build_api_url("getVideoList", {"page": 2, "limit": 24})
        self.assertIn("getVideoList", url)
        self.assertIn("app_id=83768d9ad4", url)
        self.assertIn("identity=23734adac0301bccdcb107c4aa21f96c", url)
        self.assertIn("page=2", url)

    @patch("requests.get")
    def test_request_api_parses_json_and_callback_payload(self, mock_get):
        mock_get.return_value = FakeResponse('callback({"success":true,"code":200,"data":{"data":[{"doub_id": 1}]}})')
        result = self.spider._request_api("getVideoList", {"page": 1})
        self.assertEqual(result, [{"doub_id": 1}])

    def test_parse_ext_object_supports_plain_urlencoded_and_base64_json(self):
        plain = self.spider._parse_ext_object('{"sc":"动作"}')
        encoded = self.spider._parse_ext_object("%7B%22sd%22%3A%22中国%22%7D")
        wrapped = self.spider._parse_ext_object("eyJzZSI6IjIwMjYifQ==")
        self.assertEqual(plain["sc"], "动作")
        self.assertEqual(encoded["sd"], "中国")
        self.assertEqual(wrapped["se"], "2026")

    @patch.object(Spider, "_request_api")
    def test_category_content_movie_uses_filter_params(self, mock_request_api):
        mock_request_api.return_value = [
            {"doub_id": 21, "title": "电影A", "image": "a.jpg", "ejs": "4K"},
            {"doub_id": 21, "title": "电影A", "image": "a.jpg", "ejs": "4K"},
        ]
        result = self.spider.categoryContent("1", "2", False, '{"sc":"动作","sd":"中国","iswp":"1","status":"更新中"}')
        self.assertEqual(mock_request_api.call_args.args[0], "getVideoMovieList")
        self.assertEqual(
            mock_request_api.call_args.args[1],
            {"sa": 1, "page": 2, "sc": "动作", "sd": "中国", "se": "", "sf": "", "sh": "", "sg": "1", "iswp": 1},
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(len(result["list"]), 1)
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_api")
    def test_category_content_hot_uses_local_dedupe_and_pagination(self, mock_request_api):
        mock_request_api.return_value = [
            {"doub_id": 1, "title": "A"},
            {"doub_id": 1, "title": "A"},
            {"doub_id": 2, "title": "B"},
        ]
        result = self.spider.categoryContent("3", "1", False, {})
        self.assertEqual(mock_request_api.call_args.args[0], "getVideoList")
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["list"]), 2)

    @patch.object(Spider, "_request_api")
    def test_search_content_filters_by_name_and_dedupes(self, mock_request_api):
        mock_request_api.return_value = [
            {"doub_id": 1, "title": "繁花", "image": "1.jpg"},
            {"doub_id": 2, "title": "繁花幕后", "image": "2.jpg"},
            {"doub_id": 2, "title": "繁花幕后", "image": "2.jpg"},
            {"doub_id": 3, "title": "别的内容", "image": "3.jpg"},
        ]
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(mock_request_api.call_args.args[0], "getVideoList")
        self.assertEqual(result["total"], 2)
        self.assertEqual([item["vod_id"] for item in result["list"]], ["1", "2"])

    def test_detect_drive_type_by_url(self):
        self.assertEqual(self.spider._detect_drive_type_by_url("https://pan.baidu.com/s/abc"), "baidu")
        self.assertEqual(self.spider._detect_drive_type_by_url("https://pan.quark.cn/s/abc"), "quark")
        self.assertEqual(self.spider._detect_drive_type_by_url("https://pan.xunlei.com/s/abc"), "xunlei")
        self.assertEqual(self.spider._detect_drive_type_by_url("https://www.alipan.com/s/abc"), "aliyun")
        self.assertEqual(self.spider._detect_drive_type_by_url("https://www.123pan.com/s/abc"), "a123")
        self.assertEqual(self.spider._detect_drive_type_by_url("https://example.com/file"), "other")

    def test_extract_pan_sources_creates_independent_lines_and_ignores_magnet_groups(self):
        detail = {
            "title": "示例详情",
            "movies_online_seed": {
                "夸克": [
                    {"seed_name": "夸克资源A", "link": "https://pan.quark.cn/s/q1"},
                    {"seed_name": "夸克资源A", "link": "https://pan.quark.cn/s/q1"},
                ],
                "百度网盘": [{"seed_name": "百度资源", "link": "https://pan.baidu.com/s/b1"}],
                "未知": [{"seed_name": "未知资源", "link": "https://example.com/file"}],
            },
            "ecca": {"WEB-4K": [{"zlink": "magnet:?xt=1"}]},
        }
        play_from, play_url = self.spider._extract_pan_sources(detail)
        self.assertEqual(play_from, "baidu#1$$$quark#1$$$other#1")
        self.assertEqual(
            play_url,
            "baidu#1$https://pan.baidu.com/s/b1$$$quark#1$https://pan.quark.cn/s/q1$$$other#1$https://example.com/file",
        )

    @patch.object(Spider, "_request_api")
    def test_detail_content_maps_metadata_and_pan_lines(self, mock_request_api):
        mock_request_api.return_value = {
            "doub_id": 88,
            "title": "详情标题",
            "image": "https://img.test/detail.jpg",
            "ejs": "全 12 集",
            "years": "2026",
            "abstract": "这是一段剧情简介",
            "performer": "演员甲/演员乙",
            "director": "导演甲",
            "production_area": "中国",
            "movies_online_seed": {
                "阿里": [{"seed_name": "阿里资源", "link": "https://www.alipan.com/s/ali1"}]
            },
        }
        result = self.spider.detailContent(["88"])
        vod = result["list"][0]
        self.assertEqual(mock_request_api.call_args.args[0], "getVideoDetail")
        self.assertEqual(mock_request_api.call_args.args[1], {"id": "88"})
        self.assertEqual(vod["vod_id"], "88")
        self.assertEqual(vod["vod_name"], "详情标题")
        self.assertEqual(vod["vod_play_from"], "aliyun#1")
        self.assertEqual(vod["vod_play_url"], "aliyun#1$https://www.alipan.com/s/ali1")

    def test_player_content_passthroughs_share_links_with_tvbox_shape(self):
        self.assertEqual(
            self.spider.playerContent("quark#1", "https://pan.quark.cn/s/q1", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.quark.cn/s/q1"},
        )
        self.assertEqual(
            self.spider.playerContent("quark#1", "push://https://pan.quark.cn/s/q1", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.quark.cn/s/q1"},
        )

    def test_player_content_returns_empty_url_for_non_pan_links(self):
        self.assertEqual(
            self.spider.playerContent("other#1", "https://example.com/file", {}),
            {"parse": 0, "playUrl": "", "url": ""},
        )


if __name__ == "__main__":
    unittest.main()
