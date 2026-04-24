import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("fktv_spider", str(ROOT / "凡客TV.py")).load_module()
Spider = MODULE.Spider


class TestFKTVSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_returns_expected_classes(self):
        result = self.spider.homeContent(False)
        self.assertEqual(
            result["class"],
            [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "剧集"},
                {"type_id": "4", "type_name": "动漫"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "8", "type_name": "短剧"},
                {"type_id": "6", "type_name": "纪录片"},
                {"type_id": "7", "type_name": "解说"},
                {"type_id": "5", "type_name": "音乐"},
            ],
        )

    def test_encode_and_decode_play_id_round_trip(self):
        encoded = self.spider._encode_play_id(
            {
                "movie_id": "9001",
                "link_id": "ep-1",
                "line_id": "line-a",
                "line_name": "线路A",
                "episode_name": "第1集",
                "type": "switch",
                "page": "https://fktv.me/movie/detail/9001",
            }
        )
        payload = self.spider._decode_play_id(encoded)
        self.assertEqual(payload["movie_id"], "9001")
        self.assertEqual(payload["link_id"], "ep-1")
        self.assertEqual(payload["line_id"], "line-a")
        self.assertEqual(payload["episode_name"], "第1集")
        self.assertEqual(payload["page"], "https://fktv.me/movie/detail/9001")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_url_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="card-wrap">
          <div class="meta-wrap">
            <a class="normal-title" href="/movie/detail/abc123" title="示例电影">示例电影</a>
            <img class="lazy-load" data-src="/poster.jpg" />
            <span class="tag">电影</span>
            <span class="tag">更新中</span>
          </div>
        </div>
        """
        result = self.spider.categoryContent("1", "2", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://fktv.me/channel?page=2&cat_id=1&page_size=32&order=new",
        )
        self.assertEqual(
            result["list"],
            [
                {
                    "vod_id": "abc123",
                    "vod_name": "示例电影",
                    "vod_pic": "https://fktv.me/poster.jpg",
                    "vod_remarks": "电影 | 更新中",
                    "type_name": "电影",
                }
            ],
        )
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_builds_url_and_handles_blank_keyword(self, mock_request_html):
        blank = self.spider.searchContent("", False, "1")
        self.assertEqual(blank, {"page": 1, "limit": 0, "total": 0, "list": []})
        mock_request_html.assert_not_called()

        mock_request_html.return_value = """
        <div class="hover-wrap">
          <a class="hover-title" href="/movie/detail/xyz789" title="搜索影片">搜索影片</a>
          <img class="lazy-load" data-src="https://img.example/search.jpg" />
          <span class="tag">剧集</span>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "3")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://fktv.me/search?keyword=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["list"][0]["vod_id"], "xyz789")

    @patch.object(Spider, "_request_html")
    def test_detail_content_extracts_state_and_builds_multiline_playlist(self, mock_request_html):
        mock_request_html.return_value = """
        <html>
          <head>
            <title>示例详情 -免费在线观看-凡客影视</title>
            <meta name="description" content="这里是剧情简介" />
            <meta property="og:image" content="https://img.example/detail.jpg" />
          </head>
          <body>
            <div class="item-wrap" data-line="line-a">线路A</div>
            <div class="item-wrap" data-line="line-b">线路B</div>
            <script>
              let movieId = '9001';
              let linkId = 'ep-1';
              var links = [{"id":"ep-1","name":"第1集"},{"id":"ep-2","title":"第2集"}];
              var play_links = [{"id":"line-a","name":"线路A"},{"id":"line-b","name":"线路B"}];
              var play_error_type = '';
            </script>
          </body>
        </html>
        """
        result = self.spider.detailContent(["9001"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "9001")
        self.assertEqual(vod["vod_name"], "示例详情")
        self.assertEqual(vod["vod_pic"], "https://img.example/detail.jpg")
        self.assertEqual(vod["vod_content"], "这里是剧情简介")
        self.assertEqual(vod["vod_play_from"], "线路A$$$线路B")
        self.assertIn("第1集$", vod["vod_play_url"])
        self.assertIn("第2集$", vod["vod_play_url"])

    @patch.object(Spider, "_request_html")
    def test_detail_content_falls_back_to_play_links_when_line_tabs_missing(self, mock_request_html):
        mock_request_html.return_value = """
        <html>
          <head><title>无线路tab</title></head>
          <body>
            <script>
              let movieId = '9002';
              let linkId = 'ep-9';
              var links = [{"id":"ep-9","id2":"unused"}];
              var play_links = [{"id":"line-z","name":"备用线路"}];
              var play_error_type = 'need_vip';
            </script>
          </body>
        </html>
        """
        result = self.spider.detailContent(["9002"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_play_from"], "备用线路")
        self.assertIn("ep-9", vod["vod_play_url"])
        self.assertIn("VIP", vod["vod_remarks"])

    def test_player_content_returns_direct_media_without_request(self):
        result = self.spider.playerContent("fktv", "https://cdn.example.com/demo.m3u8", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://cdn.example.com/demo.m3u8")

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_request_html")
    def test_player_content_uses_switch_api_and_filters_by_line_id(
        self, mock_request_html, mock_request_json
    ):
        play_id = self.spider._encode_play_id(
            {
                "movie_id": "9001",
                "link_id": "ep-2",
                "line_id": "line-b",
                "line_name": "线路B",
                "episode_name": "第2集",
                "type": "switch",
                "page": "https://fktv.me/movie/detail/9001",
            }
        )
        mock_request_html.return_value = """
        <script>
          let movieId = '9001';
          let linkId = 'ep-1';
          var links = [{"id":"ep-1","name":"第1集"},{"id":"ep-2","name":"第2集"}];
          var play_links = [];
          var play_error_type = '';
        </script>
        """
        mock_request_json.return_value = {
            "status": True,
            "data": {
                "play_links": [
                    {"id": "line-a", "name": "线路A", "m3u8_url": "/media/a.m3u8"},
                    {"id": "line-b", "name": "线路B", "m3u8_url": "https://cdn.example.com/b.m3u8"},
                ]
            },
        }
        result = self.spider.playerContent("fktv", play_id, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://cdn.example.com/b.m3u8")
        self.assertEqual(mock_request_json.call_args.args[0], "https://fktv.me/movie/detail/9001")
        self.assertEqual(
            mock_request_json.call_args.kwargs["data"],
            {"link_id": "ep-2", "is_switch": 1},
        )

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_request_html")
    def test_player_content_returns_all_lines_when_line_not_specified(
        self, mock_request_html, mock_request_json
    ):
        play_id = self.spider._encode_play_id(
            {
                "movie_id": "9003",
                "link_id": "ep-8",
                "line_id": "",
                "line_name": "",
                "episode_name": "正片",
                "type": "switch",
                "page": "https://fktv.me/movie/detail/9003",
            }
        )
        mock_request_html.return_value = (
            "<script>let movieId='9003';let linkId='ep-8';var links=[];"
            "var play_links=[];var play_error_type='';</script>"
        )
        mock_request_json.return_value = {
            "status": True,
            "data": {
                "play_links": [
                    {"id": "line-a", "name": "线路A", "m3u8_url": "/media/a.m3u8"},
                    {"id": "line-b", "name": "线路B", "preview_m3u8_url": "/media/b.m3u8"},
                ]
            },
        }
        result = self.spider.playerContent("fktv", play_id, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(len(result["urls"]), 2)
        self.assertEqual(result["url"], "https://fktv.me/media/a.m3u8")

    @patch.object(Spider, "_request_json")
    @patch.object(Spider, "_request_html")
    def test_player_content_falls_back_to_detail_page_when_api_has_no_url(
        self, mock_request_html, mock_request_json
    ):
        play_id = self.spider._encode_play_id(
            {
                "movie_id": "9004",
                "link_id": "ep-3",
                "line_id": "line-z",
                "line_name": "线路Z",
                "episode_name": "第3集",
                "type": "switch",
                "page": "https://fktv.me/movie/detail/9004",
            }
        )
        mock_request_html.return_value = (
            "<script>let movieId='9004';let linkId='ep-3';var links=[];"
            "var play_links=[];var play_error_type='need_vip';</script>"
        )
        mock_request_json.return_value = {
            "status": True,
            "data": {"play_links": [], "play_error_type": "need_vip"},
        }
        result = self.spider.playerContent("fktv", play_id, {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["url"], "https://fktv.me/movie/detail/9004")


if __name__ == "__main__":
    unittest.main()
