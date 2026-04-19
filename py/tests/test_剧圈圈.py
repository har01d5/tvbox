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

    def test_parse_detail_page_extracts_metadata_and_playlists(self):
        html = """
        <div class="module-info-heading"><h1>详情标题</h1></div>
        <div class="module-info-poster"><img data-original="/poster.jpg" /></div>
        <div class="module-info-item">
          <div class="module-info-item-title">导演</div>
          <div class="module-info-item-content"><a>导演甲</a></div>
        </div>
        <div class="module-info-item">
          <div class="module-info-item-title">主演</div>
          <div class="module-info-item-content"><a>演员甲</a><a>演员乙</a></div>
        </div>
        <div class="module-info-item">
          <div class="module-info-item-title">备注</div>
          <div class="module-info-item-content">更新至3集</div>
        </div>
        <div class="module-info-introduction-content">一段剧情简介</div>
        <div class="module-info-tag-link"><a>古装</a><a>剧情</a></div>
        <div id="y-playList">
          <div class="module-tab-item" data-dropdown-value="线路A"></div>
          <div class="module-tab-item" data-dropdown-value="线路B"></div>
        </div>
        <div class="his-tab-list">
          <a class="module-play-list-link" href="/play/123-1-1.html"><span>第1集</span></a>
          <a class="module-play-list-link" href="/play/123-1-2.html"><span>第2集</span></a>
        </div>
        <div class="his-tab-list">
          <a class="module-play-list-link" href="/play/123-2-1.html"><span>正片</span></a>
        </div>
        """
        result = self.spider._parse_detail_page(html, "vod/123")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "vod/123")
        self.assertEqual(vod["vod_name"], "详情标题")
        self.assertEqual(vod["vod_pic"], "https://www.jqqzx.cc/poster.jpg")
        self.assertEqual(vod["type_name"], "古装 / 剧情")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_actor"], "演员甲 / 演员乙")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "线路A$$$线路B")
        self.assertEqual(vod["vod_play_url"], "第1集$play/123-1-1#第2集$play/123-1-2$$$正片$play/123-2-1")

    @patch.object(Spider, "_request_html")
    def test_detail_content_decodes_compact_vod_id(self, mock_request_html):
        mock_request_html.return_value = '<div class="module-info-heading"><h1>详情标题</h1></div>'
        self.spider.detailContent(["vod/321"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.jqqzx.cc/vod/321.html")

    def test_extract_player_data_reads_player_aaaa(self):
        html = '<script>var player_aaaa={"url":"https://video.example/direct.m3u8"};</script>'
        self.assertEqual(self.spider._extract_player_data(html)["url"], "https://video.example/direct.m3u8")

    @patch.object(Spider, "_request_with_headers")
    def test_player_content_returns_direct_media_url(self, mock_request_with_headers):
        mock_request_with_headers.return_value = {
            "body": '<script>var player_aaaa={"url":"https://video.example/direct.m3u8"};</script>',
            "headers": {},
            "status_code": 200,
        }
        result = self.spider.playerContent("线路A", "play/123-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/direct.m3u8")

    @patch.object(Spider, "_request_with_headers")
    def test_player_content_uses_parse_api_when_player_vid_is_not_direct(self, mock_request_with_headers):
        mock_request_with_headers.side_effect = [
            {
                "body": '<script>var player_aaaa={"url":"https%3A%2F%2Fmiddle.example%2Fembed%3Fid%3D1"};</script>',
                "headers": {"set-cookie": ["foo=bar; Path=/"]},
                "status_code": 200,
            },
            {
                "body": "<html></html>",
                "headers": {"set-cookie": ["token=abc; Path=/"]},
                "status_code": 200,
            },
            {
                "body": '{"code":200,"data":{"url":"error://apiRes_dummy"}}',
                "headers": {},
                "status_code": 200,
            },
        ]
        self.spider._decode_url = lambda value: "https://video.example/fallback.m3u8"
        result = self.spider.playerContent("线路A", "play/123-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/fallback.m3u8")

    @patch.object(Spider, "_request_with_headers")
    def test_player_content_falls_back_to_play_page_when_player_data_missing(self, mock_request_with_headers):
        mock_request_with_headers.return_value = {"body": "<html></html>", "headers": {}, "status_code": 200}
        result = self.spider.playerContent("线路A", "play/123-1-1", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["url"], "https://www.jqqzx.cc/play/123-1-1.html")


if __name__ == "__main__":
    unittest.main()
