import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("duanjuyx_spider", str(ROOT / "短剧优选.py")).load_module()
Spider = MODULE.Spider


class TestDuanjuYouxuanSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.xingya_headers = {"authorization": "token"}

    def test_home_content_has_active_platforms(self):
        content = self.spider.homeContent(False)
        ids = [c["type_id"] for c in content["class"]]
        self.assertEqual(ids, ["七猫", "星芽", "星星", "西饭", "锦鲤", "红果", "微观", "短剧网"])
        self.assertNotIn("七星", ids)

    def test_home_content_has_filters(self):
        content = self.spider.homeContent(False)
        self.assertIn("七猫", content["filters"])
        self.assertIn("星星", content["filters"])
        self.assertIn("锦鲤", content["filters"])
        self.assertIn("微观", content["filters"])
        self.assertIn("短剧网", content["filters"])
        self.assertEqual(content["filters"]["锦鲤"][0]["key"], "area")

    def test_home_video_content_returns_empty(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    @patch.object(Spider, "_get_json")
    def test_player_hongguo_uses_video_api_result(self, mock_json):
        mock_json.return_value = {"url": "https://media.example.com/play.mp4"}
        result = self.spider.playerContent("红果短剧", "vid123", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://media.example.com/play.mp4")

    def test_player_xingya_passthrough(self):
        result = self.spider.playerContent("星芽短剧", "https://example.com/video.m3u8", {})
        self.assertEqual(result["url"], "https://example.com/video.m3u8")

    def test_player_duanjuwang_passthrough(self):
        result = self.spider.playerContent("短剧网", "push://pan.quark.cn/abc", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "push://pan.quark.cn/abc")

    def test_player_weiguan_passthrough(self):
        result = self.spider.playerContent("1080P", "https://media.example.com/1080.mp4", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://media.example.com/1080.mp4")

    @patch.object(Spider, "_post_json")
    def test_category_jinli(self, mock_post_json):
        mock_post_json.return_value = {
            "data": {
                "list": [
                    {"vod_id": "j1", "vod_name": "重生逆袭遇良人", "vod_pic": "http://pic/j1.jpg", "vod_total": 88}
                ]
            }
        }
        result = self.spider.categoryContent("锦鲤", "1", False, {"area": ""})
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_id"], "锦鲤@j1")
        self.assertEqual(result["list"][0]["vod_name"], "重生逆袭遇良人")
        self.assertGreater(result["total"], 0)

    @patch.object(Spider, "_get_json")
    def test_category_xingxing(self, mock_get_json):
        mock_get_json.return_value = {
            "data": {
                "datalist": [
                    {
                        "id": "420424102051841",
                        "name": "穿越诡计爱上你",
                        "introduction": "简介",
                        "icon": "http://pic/xx.jpg",
                        "heat": "42",
                    }
                ],
                "total": 10,
            }
        }
        result = self.spider.categoryContent("星星", "1", False, {"area": "1287"})
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_id"], "星星@420424102051841@@穿越诡计爱上你@@简介")
        self.assertEqual(result["list"][0]["vod_remarks"], "42万播放")

    @patch.object(Spider, "_get_json")
    def test_category_hongguo(self, mock_get_json):
        mock_get_json.return_value = {
            "data": [
                {"book_id": "b1", "title": "逆袭人生", "cover": "http://pic/1.jpg", "sub_title": "60集"},
                {"book_id": "b2", "title": "霸总归来", "cover": "http://pic/2.jpg", "sub_title": "80集"},
            ]
        }
        result = self.spider.categoryContent("红果", "1", False, {"area": "逆袭"})
        self.assertEqual(len(result["list"]), 2)
        self.assertEqual(result["list"][0]["vod_id"], "红果@b1")
        self.assertEqual(result["page"], 1)

    @patch.object(Spider, "_post_json")
    def test_category_weiguan(self, mock_post_json):
        mock_post_json.return_value = {
            "data": [
                {
                    "oneId": "wg1",
                    "title": "重生后我爆锤渣男",
                    "horzPoster": "http://pic/w1.jpg",
                    "episodeCount": "72集",
                }
            ]
        }
        result = self.spider.categoryContent("微观", "1", False, {"area": "逆袭"})
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_id"], "微观@wg1")
        self.assertEqual(result["list"][0]["vod_pic"], "http://pic/w1.jpg")
        self.assertIn("version_code=1500", mock_post_json.call_args.args[0])
        self.assertEqual(mock_post_json.call_args.kwargs["body"]["subject"], "逆袭")

    @patch.object(Spider, "_get_text")
    def test_category_duanjuwang(self, mock_get_text):
        mock_get_text.return_value = """
        <li class="col-6">
          <h3 class="f-14"><a href="/?id=123">短剧名（60集完结）</a></h3>
          <img class="lazy" data-original="/cover.jpg" />
        </li>
        """
        result = self.spider.categoryContent("短剧网", "1", False, {"area": "1"})
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_id"], "短剧网@https://sm3.cc/?id=123")
        self.assertEqual(result["page"], 1)

    @patch.object(Spider, "_get_json")
    def test_detail_jinli(self, mock_get_json):
        mock_get_json.return_value = {
            "data": {
                "vod_name": "重生逆袭遇良人",
                "vod_class": "重生",
                "vod_pic": "http://pic/j1.jpg",
                "vod_remarks": "88集",
                "vod_blurb": "剧情简介",
                "player": {"第1集": "https://player.example.com/?url=abc"},
            }
        }
        result = self.spider.detailContent(["锦鲤@j1"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "重生逆袭遇良人")
        self.assertEqual(vod["vod_play_from"], "锦鲤短剧")
        self.assertIn("第1集$https://player.example.com/?url=abc", vod["vod_play_url"])

    @patch.object(Spider, "_get_json")
    def test_detail_xingxing(self, mock_get_json):
        mock_get_json.return_value = {
            "data": [
                {
                    "chapterName": "第1集",
                    "shortPlayList": [
                        {"chapterShortPlayVoList": [{"shortPlayUrl": "http://img.novel.wsljf.xyz/video.mp4"}]}
                    ],
                }
            ]
        }
        result = self.spider.detailContent(["星星@420424102051841@@穿越诡计爱上你@@简介"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "穿越诡计爱上你")
        self.assertEqual(vod["vod_play_from"], "星星短剧")
        self.assertIn("第1集$https://img.novel.wsljf.xyz/video.mp4", vod["vod_play_url"])

    @patch.object(Spider, "_get_json")
    def test_detail_hongguo(self, mock_get_json):
        mock_get_json.return_value = {
            "book_name": "甜剧1号",
            "book_pic": "http://pic/t.jpg",
            "desc": "剧情简介",
            "duration": "60分钟",
            "author": "作者",
            "time": "2025-01-01",
            "data": [
                {"title": "第1集", "video_id": "v1"},
                {"title": "第2集", "video_id": "v2"},
            ],
        }
        result = self.spider.detailContent(["红果@b1"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "甜剧1号")
        self.assertEqual(vod["vod_play_from"], "红果短剧")
        self.assertIn("第1集$v1", vod["vod_play_url"])
        self.assertIn("第2集$v2", vod["vod_play_url"])

    @patch.object(Spider, "_get_json")
    def test_detail_weiguan(self, mock_get_json):
        mock_get_json.return_value = {
            "title": "重生后我爆锤渣男",
            "vertPoster": "http://pic/wg.jpg",
            "description": "剧情简介",
            "data": [
                {
                    "playOrder": "第1集",
                    "videoClarityList": [
                        {"name": "1080P", "url": "https://media.example.com/1-1080.mp4"},
                        {"name": "720P", "url": "https://media.example.com/1-720.mp4"},
                    ],
                },
                {
                    "playOrder": "第2集",
                    "videoClarityList": [
                        {"name": "1080P", "url": "https://media.example.com/2-1080.mp4"},
                    ],
                },
            ],
        }
        result = self.spider.detailContent(["微观@wg1"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "重生后我爆锤渣男")
        self.assertEqual(vod["vod_play_from"], "1080P$$$720P")
        self.assertEqual(
            vod["vod_play_url"],
            "第1集$https://media.example.com/1-1080.mp4#第2集$https://media.example.com/2-1080.mp4"
            "$$$第1集$https://media.example.com/1-720.mp4",
        )
        self.assertIn("oneId=wg1", mock_get_json.call_args.args[0])
        self.assertIn("queryAll=true", mock_get_json.call_args.args[0])

    @patch.object(Spider, "_get_text")
    def test_detail_duanjuwang(self, mock_get_text):
        mock_get_text.return_value = """
        <html><body>
        <h1>网盘短剧名</h1>
        <img class="lazy" data-original="/poster.jpg" />
        <div class="content">
          <a href="https://pan.quark.cn/s/abc123">夸克链接</a>
          <a href="https://pan.baidu.com/s/xyz789">百度链接</a>
        </div>
        </body></html>
        """
        result = self.spider.detailContent(["短剧网@https://sm3.cc/?id=123"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "网盘短剧名")
        self.assertEqual(vod["vod_content"], "此为推送网盘规则")
        self.assertIn("quark", vod["vod_play_from"])
        self.assertIn("baidu", vod["vod_play_from"])
        self.assertIn("quark$https://pan.quark.cn/s/abc123", vod["vod_play_url"])

    @patch.object(Spider, "_get_json")
    def test_detail_failure_returns_error_vod(self, mock_get_json):
        mock_get_json.side_effect = Exception("network error")
        result = self.spider.detailContent(["红果@missing"])
        vod = result["list"][0]
        self.assertIn("详情加载失败", vod["vod_name"])

    @patch.object(Spider, "_aggregate_search")
    def test_search_filters_by_keyword(self, mock_search):
        mock_search.return_value = [
            {"vod_id": "红果@1", "vod_name": "逆袭人生", "vod_pic": "", "vod_remarks": ""},
            {"vod_id": "锦鲤@2", "vod_name": "霸道总裁", "vod_pic": "", "vod_remarks": ""},
        ]
        result = self.spider.searchContent("逆袭", False, "1")
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_name"], "逆袭人生")

    @patch.object(Spider, "_aggregate_search")
    def test_search_empty_keyword(self, mock_search):
        result = self.spider.searchContent("", False, "1")
        self.assertEqual(result["list"], [])
        mock_search.assert_not_called()

    def test_filter_defaults(self):
        self.assertEqual(self.spider.filter_defaults["锦鲤"]["area"], "")
        self.assertEqual(self.spider.filter_defaults["星星"]["area"], "1287")
        self.assertEqual(self.spider.filter_defaults["微观"]["area"], "")
        self.assertEqual(self.spider.filter_defaults["短剧网"]["area"], "1")

    def test_identify_disk(self):
        self.assertEqual(self.spider._identify_disk("https://pan.quark.cn/s/abc"), "quark")
        self.assertEqual(self.spider._identify_disk("https://pan.baidu.com/s/xyz"), "baidu")
        self.assertEqual(self.spider._identify_disk("https://drive.uc.cn/s/123"), "uc")
        self.assertEqual(self.spider._identify_disk("https://example.com/video.mp4"), "")


if __name__ == "__main__":
    unittest.main()
