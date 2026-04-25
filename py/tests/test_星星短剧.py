import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("xingxingduanju_spider", str(ROOT / "星星短剧.py")).load_module()
Spider = MODULE.Spider


class TestXingXingDuanJuSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_fixed_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(content["class"][0]["type_id"], "1287")
        self.assertEqual(content["class"][-1]["type_name"], "古代")
        self.assertEqual(content["filters"], {})

    @patch.object(Spider, "_get_json")
    def test_home_video_content_uses_default_category(self, mock_json):
        mock_json.return_value = {
            "data": {
                "datalist": [
                    {
                        "id": 1001,
                        "name": "闪婚后成了大佬心尖宠",
                        "icon": "http://img/1.jpg",
                        "introduction": "剧情简介",
                        "heat": 291.6,
                    }
                ],
                "page": {"totalCount": 34},
            }
        }
        result = self.spider.homeVideoContent()
        self.assertEqual(result["list"][0]["vod_id"], "1001@@闪婚后成了大佬心尖宠@@剧情简介")
        self.assertEqual(result["list"][0]["vod_name"], "闪婚后成了大佬心尖宠")
        self.assertEqual(result["list"][0]["vod_remarks"], "291.6万播放")
        self.assertIn("resourceId=1287", mock_json.call_args.args[0])
        self.assertIn("pageNum=1", mock_json.call_args.args[0])

    @patch.object(Spider, "_get_json")
    def test_category_content_builds_query_and_maps_items(self, mock_json):
        mock_json.return_value = {
            "data": {
                "datalist": [
                    {
                        "id": 2002,
                        "name": "宸王的复仇王妃",
                        "icon": "http://img/2.jpg",
                        "introduction": "王妃复仇记",
                        "heat": 398.3,
                    }
                ],
                "page": {"totalCount": 34},
            }
        }
        result = self.spider.categoryContent("1291", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["total"], 34)
        self.assertEqual(result["list"][0]["vod_id"], "2002@@宸王的复仇王妃@@王妃复仇记")
        self.assertNotIn("pagecount", result)
        self.assertIn("resourceId=1291", mock_json.call_args.args[0])
        self.assertIn("pageNum=2", mock_json.call_args.args[0])
        self.assertIn("pageSize=10", mock_json.call_args.args[0])

    @patch.object(Spider, "_get_json")
    def test_detail_content_builds_single_playlist(self, mock_json):
        mock_json.return_value = {
            "data": [
                {
                    "chapterName": "第1集",
                    "shortPlayList": [
                        {
                            "chapterShortPlayVoList": [
                                {"shortPlayUrl": "http://video/1.m3u8"}
                            ]
                        }
                    ],
                },
                {
                    "chapterName": "第2集",
                    "shortPlayList": [
                        {
                            "chapterShortPlayVoList": [
                                {"shortPlayUrl": "http://video/2.m3u8"}
                            ]
                        }
                    ],
                },
            ]
        }
        result = self.spider.detailContent(["422599939194881@@穿越诡计爱上你@@一段简介"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "422599939194881@@穿越诡计爱上你@@一段简介")
        self.assertEqual(vod["vod_name"], "穿越诡计爱上你")
        self.assertEqual(vod["vod_content"], "一段简介")
        self.assertEqual(vod["vod_play_from"], "星星短剧")
        self.assertIn("第1集$http://video/1.m3u8", vod["vod_play_url"])
        self.assertIn("第2集$http://video/2.m3u8", vod["vod_play_url"])
        self.assertIn("bookId=422599939194881", mock_json.call_args.args[0])

    @patch.object(Spider, "_get_json")
    def test_detail_content_returns_empty_when_id_missing(self, mock_json):
        self.assertEqual(self.spider.detailContent([""]), {"list": []})
        mock_json.assert_not_called()

    def test_search_content_returns_empty(self):
        self.assertEqual(
            self.spider.searchContent("任意关键词", False, "3"),
            {"page": 3, "limit": 0, "total": 0, "list": []},
        )

    def test_player_content_returns_direct_url(self):
        result = self.spider.playerContent("星星短剧", "http://video/play.m3u8", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "http://video/play.m3u8")
        self.assertIn("Mozilla/5.0", result["header"]["User-Agent"])

    def test_player_content_upgrades_known_cdn_to_https(self):
        result = self.spider.playerContent(
            "星星短剧",
            "http://img.novel.wsljf.xyz/shortPlay-mp4/demo/output.m3u8",
            {},
        )
        self.assertEqual(
            result["url"],
            "https://img.novel.wsljf.xyz/shortPlay-mp4/demo/output.m3u8",
        )

    @patch.object(Spider, "fetch")
    def test_get_json_returns_empty_on_invalid_json(self, mock_fetch):
        mock_fetch.return_value = MagicMock(status_code=200, text="<html>blocked</html>")
        self.assertEqual(self.spider._get_json("http://example.com/api"), {})


if __name__ == "__main__":
    unittest.main()
