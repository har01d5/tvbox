import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("kuwo_tingshu_spider", str(ROOT / "酷我听书.py")).load_module()
Spider = MODULE.Spider


class TestKuWoTingShuSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_returns_fixed_classes_and_filters(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["2", "37", "5", "62"],
        )
        self.assertEqual([item["key"] for item in content["filters"]["2"]], ["class", "vip", "sort"])
        self.assertEqual(content["filters"]["2"][0]["value"][0], {"n": "都市传说", "v": "42"})
        self.assertEqual(content["filters"]["37"][1]["value"][2], {"n": "会员权限", "v": "1"})

    def test_format_play_count_and_paid_track_helpers(self):
        self.assertEqual(self.spider._format_play_count(1234), "1234")
        self.assertEqual(self.spider._format_play_count(12000), "1.2万")
        self.assertEqual(self.spider._format_play_count(230000000), "2.3亿")
        self.assertTrue(self.spider._is_paid_track({"payInfo": {"feeType": {"bookvip": "1"}}}))
        self.assertFalse(self.spider._is_paid_track({"payInfo": {"feeType": {"bookvip": "0"}}}))

    def test_parse_search_payload_accepts_single_quotes_json(self):
        payload = self.spider._parse_search_payload("{'albumlist':[{'name':'示例'}],'TOTAL':1}")
        self.assertEqual(payload["albumlist"][0]["name"], "示例")
        self.assertEqual(payload["TOTAL"], 1)

    @patch.object(Spider, "fetch")
    def test_api_get_uses_fetch_and_parses_json(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(status_code=200, text='{"data":{"data":[{"albumId":1}]}}')
        result = self.spider._api_get("/v2/api/search/filter/albums", {"categoryId": "2"})
        self.assertEqual(result["data"]["data"][0]["albumId"], 1)
        self.assertEqual(mock_fetch.call_args.args[0], "http://tingshu.kuwo.cn/v2/api/search/filter/albums")
        self.assertEqual(mock_fetch.call_args.kwargs["params"]["categoryId"], "2")
        self.assertEqual(mock_fetch.call_args.kwargs["headers"]["User-Agent"], "kwplayer_ar_9.1.8.1_tvivo.apk")

    @patch.object(Spider, "_api_get")
    def test_home_video_content_aggregates_default_categories(self, mock_api_get):
        mock_api_get.side_effect = [
            {"data": {"data": [{"albumId": 1, "albumName": "小说A", "coverImg": "a.jpg", "vip": 0, "playCnt": 3200}]}},
            {"data": {"data": [{"albumId": 2, "albumName": "音乐B", "coverImg": "b.jpg", "vip": 1, "playCnt": 54000}]}},
            {"data": {"data": []}},
            {"data": {"data": [{"albumId": 4, "albumName": "原声D", "coverImg": "d.jpg", "vip": 0, "playCnt": 780000000}]}},
        ]
        result = self.spider.homeVideoContent()
        self.assertEqual([item["vod_id"] for item in result["list"]], ["1", "2", "4"])
        self.assertEqual(result["list"][0]["vod_remarks"], "免费 | 3200次播放 | 有声小说")
        self.assertEqual(result["list"][1]["vod_remarks"], "会员 | 5.4万次播放 | 音乐金曲")
        self.assertEqual(result["list"][2]["vod_remarks"], "免费 | 7.8亿次播放 | 影视原声")
        first_call_params = mock_api_get.call_args_list[0].args[1]
        self.assertEqual(first_call_params["classifyId"], "42")
        self.assertEqual(first_call_params["sortType"], "tsScore")
        self.assertEqual(first_call_params["rn"], 12)

    @patch.object(Spider, "_api_get")
    def test_category_content_skips_empty_pages_and_filters_vip(self, mock_api_get):
        mock_api_get.side_effect = [
            {"data": {"data": []}},
            {"data": {"data": [
                {"albumId": 10, "albumName": "免费书", "coverImg": "a.jpg", "vip": 0, "playCnt": 1},
                {"albumId": 11, "albumName": "会员书", "coverImg": "b.jpg", "vip": 1, "playCnt": 2},
            ]}},
        ]
        result = self.spider.categoryContent("2", "3", False, {"class": "42", "vip": "0", "sort": "pubDate"})
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 21)
        self.assertEqual([item["vod_id"] for item in result["list"]], ["10"])
        self.assertGreaterEqual(result["total"], 1)
        self.assertNotIn("pagecount", result)
        params = mock_api_get.call_args_list[1].args[1]
        self.assertEqual(params["categoryId"], "2")
        self.assertEqual(params["classifyId"], "42")
        self.assertEqual(params["sortType"], "pubDate")
        self.assertEqual(params["pn"], 4)

    @patch.object(Spider, "_api_get")
    def test_category_content_returns_empty_result_for_unknown_tid(self, mock_api_get):
        result = self.spider.categoryContent("999", "1", False, {})
        self.assertEqual(result, {"page": 1, "limit": 21, "total": 0, "list": []})
        mock_api_get.assert_not_called()

    @patch.object(Spider, "_search_get")
    def test_search_content_maps_search_results(self, mock_search_get):
        mock_search_get.return_value = {
            "albumlist": [
                {"DC_TARGETID": "100", "name": "三体", "img": "a.jpg", "vip": "1", "artist": "播音甲"},
                {"DC_TARGETID": "101", "name": "凡人修仙传", "img": "b.jpg", "vip": "0", "artist": "播音乙"},
            ],
            "TOTAL": 25,
        }
        result = self.spider.searchContent("修仙", False, "2")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["limit"], 21)
        self.assertEqual(result["total"], 25)
        self.assertEqual([item["vod_id"] for item in result["list"]], ["100", "101"])
        self.assertEqual(result["list"][0]["vod_remarks"], "会员 | 播音甲")

    def test_search_content_returns_empty_result_for_blank_keyword(self):
        self.assertEqual(
            self.spider.searchContent("", False, "1"),
            {"page": 1, "limit": 0, "total": 0, "list": []},
        )

    @patch.object(Spider, "_search_get")
    def test_detail_content_maps_album_and_tracks(self, mock_search_get):
        mock_search_get.return_value = {
            "name": "鬼吹灯",
            "img": "20260307/abc.jpg",
            "info": "摸金冒险故事",
            "artist": "艾宝良",
            "company": "酷我出品",
            "pub": "2026-03-07",
            "lang": "普通话",
            "finished": "1",
            "vip": "1",
            "songnum": "2",
            "musiclist": [
                {"name": "第一集", "musicrid": "MUSIC_1", "playcnt": "300", "payInfo": {"feeType": {"bookvip": "0"}}},
                {"name": "第二集", "musicrid": "MUSIC_2", "playcnt": "500", "payInfo": {"feeType": {"bookvip": "1"}}},
            ],
        }
        result = self.spider.detailContent(["123"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "123")
        self.assertEqual(vod["vod_name"], "鬼吹灯")
        self.assertEqual(vod["vod_pic"], "http://img3.sycdn.kuwo.cn/star/albumcover/240/20260307/abc.jpg")
        self.assertEqual(vod["vod_year"], "2026年")
        self.assertEqual(vod["vod_play_from"], "酷我听书")
        self.assertEqual(vod["vod_play_url"], "1.第一集$free|MUSIC_1#2.💎第二集$vip|MUSIC_2")
        self.assertEqual(vod["vod_remarks"], "会员 | 已完结 | 共2集 | 800播放")

    @patch.object(Spider, "_search_get")
    def test_detail_content_paginates_tracks_beyond_2000(self, mock_search_get):
        first_page_tracks = [
            {"name": f"第{i}集", "musicrid": f"MUSIC_{i}", "playcnt": "1", "payInfo": {"feeType": {"bookvip": "0"}}}
            for i in range(1, 2001)
        ]
        second_page_tracks = [
            {"name": f"第{i}集", "musicrid": f"MUSIC_{i}", "playcnt": "1", "payInfo": {"feeType": {"bookvip": "0"}}}
            for i in range(2001, 2006)
        ]
        mock_search_get.side_effect = [
            {
                "name": "长篇评书",
                "img": "cover.jpg",
                "info": "超长连载",
                "artist": "播音员",
                "company": "酷我出品",
                "pub": "2026-04-24",
                "lang": "普通话",
                "finished": "0",
                "vip": "0",
                "songnum": "2005",
                "musiclist": first_page_tracks,
            },
            {
                "name": "长篇评书",
                "songnum": "2005",
                "musiclist": second_page_tracks,
            },
        ]

        result = self.spider.detailContent(["999"])

        vod = result["list"][0]
        play_items = vod["vod_play_url"].split("#")
        self.assertEqual(len(play_items), 2005)
        self.assertEqual(play_items[0], "1.第1集$free|MUSIC_1")
        self.assertEqual(play_items[-1], "2005.第2005集$free|MUSIC_2005")
        self.assertEqual(vod["vod_remarks"], "免费 | 连载中 | 共2005集 | 2005播放")
        self.assertEqual(mock_search_get.call_args_list[0].args[1]["pn"], 0)
        self.assertEqual(mock_search_get.call_args_list[1].args[1]["pn"], 1)
        self.assertEqual(mock_search_get.call_args_list[0].args[1]["rn"], 2000)
        self.assertEqual(mock_search_get.call_args_list[1].args[1]["rn"], 2000)

    @patch.object(Spider, "_api_get")
    def test_player_content_resolves_free_track(self, mock_api_get):
        mock_api_get.return_value = {"data": {"url": "https://audio.example/free.mp3"}}
        result = self.spider.playerContent("酷我听书", "free|MUSIC_1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://audio.example/free.mp3")
        self.assertEqual(result["header"]["Referer"], self.spider.api_host)

    @patch.object(Spider, "_api_get")
    def test_player_content_resolves_vip_track(self, mock_api_get):
        mock_api_get.return_value = {"url": "https://audio.example/vip.mp3"}
        result = self.spider.playerContent("酷我听书", "vip|MUSIC_2", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://audio.example/vip.mp3")
        self.assertEqual(result["header"]["Referer"], "https://music-api.gdstudio.xyz")

    @patch.object(Spider, "_api_get")
    def test_player_content_falls_back_to_generated_urls(self, mock_api_get):
        mock_api_get.return_value = {}
        free_result = self.spider.playerContent("酷我听书", "free|MUSIC_9", {})
        vip_result = self.spider.playerContent("酷我听书", "vip|MUSIC_8", {})
        self.assertIn("rid=MUSIC_9", free_result["url"])
        self.assertIn("source=kuwo", vip_result["url"])


if __name__ == "__main__":
    unittest.main()
