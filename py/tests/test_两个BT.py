import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("lianggebt_spider", str(ROOT / "两个BT.py")).load_module()
Spider = MODULE.Spider


class TestLiangGeBTSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            [
                "zgjun",
                "meiju",
                "jpsrtv",
                "movie_bt_tags/xiju",
                "movie_bt_tags/aiqing",
                "movie_bt_tags/adt",
                "movie_bt_tags/at",
                "movie_bt_tags/donghua",
                "movie_bt_tags/qihuan",
                "movie_bt_tags/xuanni",
                "movie_bt_tags/kehuan",
                "movie_bt_tags/juqing",
                "movie_bt_tags/kongbu",
                "gf",
            ],
        )
        self.assertNotIn("filters", content)

    def test_extract_cards_supports_short_ids_and_relative_images(self):
        html = """
        <ul class="item">
          <li>
            <a href="/movie/123.html" title="示例影片">
              <img data-original="/cover.jpg" />
            </a>
            <h3><a href="/movie/123.html">示例影片</a></h3>
            <span class="status">更新至10集</span>
          </li>
        </ul>
        """
        cards = self.spider._extract_cards(html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "123",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.bttwoo.com/cover.jpg",
                    "vod_remarks": "更新至10集",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_home_video_content_requests_home_page(self, mock_request_html):
        mock_request_html.return_value = """
        <li>
          <a href="/movie/200.html" title="首页影片">
            <img src="/home.jpg" />
          </a>
          <h3>首页影片</h3>
        </li>
        """
        result = self.spider.homeVideoContent()
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.bttwoo.com")
        self.assertEqual(result["list"][0]["vod_id"], "200")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_expected_urls(self, mock_request_html):
        mock_request_html.return_value = """
        <li>
          <a href="/movie/301.html" title="分类影片">
            <img src="/cate.jpg" />
          </a>
          <h3>分类影片</h3>
          <span class="rating">HD</span>
        </li>
        """
        page_one = self.spider.categoryContent("meiju", "1", False, {})
        page_three = self.spider.categoryContent("movie_bt_tags/xiju", "3", False, {})
        self.assertEqual(mock_request_html.call_args_list[0].args[0], "https://www.bttwoo.com/meiju")
        self.assertEqual(
            mock_request_html.call_args_list[1].args[0],
            "https://www.bttwoo.com/movie_bt_tags/xiju?paged=3",
        )
        self.assertEqual(page_one["page"], 1)
        self.assertEqual(page_one["list"][0]["vod_name"], "分类影片")
        self.assertNotIn("pagecount", page_one)
        self.assertEqual(page_three["page"], 3)

    @patch.object(Spider, "_request_html")
    def test_search_content_builds_query_and_filters_irrelevant_results(self, mock_request_html):
        mock_request_html.return_value = """
        <li>
          <a href="/movie/401.html" title="繁花">
            <img src="/match.jpg" />
          </a>
          <h3>繁花</h3>
        </li>
        <li>
          <a href="/movie/402.html" title="无关结果">
            <img src="/other.jpg" />
          </a>
          <h3>无关结果</h3>
        </li>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.bttwoo.com/xssssearch?q=%E7%B9%81%E8%8A%B1&p=2",
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(
            result["list"],
            [
                {
                    "vod_id": "401",
                    "vod_name": "繁花",
                    "vod_pic": "https://www.bttwoo.com/match.jpg",
                    "vod_remarks": "",
                }
            ],
        )

    def test_encode_and_decode_play_id_round_trip(self):
        payload = self.spider._decode_play_id(self.spider._encode_play_id("play-1", "900", "第1集"))
        self.assertEqual(payload, {"pid": "play-1", "sid": "900", "name": "第1集"})

    @patch.object(Spider, "_request_html")
    def test_detail_content_extracts_meta_and_playlist(self, mock_request_html):
        mock_request_html.return_value = """
        <html>
          <head><title>两个BT详情页</title></head>
          <body>
            <h1>示例详情</h1>
            <div class="poster"><img src="/detail.jpg" /></div>
            <div class="description">这里是剧情简介</div>
            <li>主演：演员甲 / 演员乙</li>
            <li>导演：导演甲</li>
            <a href="/v_play/play-1.html">第1集</a>
            <a href="/v_play/play-2.html">第2集</a>
          </body>
        </html>
        """
        result = self.spider.detailContent(["900"])
        vod = result["list"][0]
        first_name, first_id = vod["vod_play_url"].split("#")[0].split("$", 1)
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.bttwoo.com/movie/900.html")
        self.assertEqual(vod["vod_id"], "900")
        self.assertEqual(vod["vod_name"], "示例详情")
        self.assertEqual(vod["vod_pic"], "https://www.bttwoo.com/detail.jpg")
        self.assertEqual(vod["vod_content"], "这里是剧情简介")
        self.assertEqual(vod["vod_actor"], "演员甲 / 演员乙")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_play_from"], "两个BT")
        self.assertEqual(first_name, "第1集")
        self.assertEqual(self.spider._decode_play_id(first_id)["pid"], "play-1")
        self.assertEqual(self.spider._decode_play_id(first_id)["sid"], "900")

    def test_player_content_passthroughs_direct_media_url(self):
        result = self.spider.playerContent("两个BT", "https://media.example/direct.m3u8", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://media.example/direct.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://www.bttwoo.com/")

    @patch.object(Spider, "_request_html")
    def test_player_content_extracts_media_from_play_page(self, mock_request_html):
        mock_request_html.return_value = """
        <script>
        var player_data = {"url":"https://media.example/final.mp4"};
        </script>
        """
        play_id = self.spider._encode_play_id("play-100", "900", "第1集")
        result = self.spider.playerContent("两个BT", play_id, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.bttwoo.com/v_play/play-100.html")
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://media.example/final.mp4")
        self.assertEqual(result["header"]["Referer"], "https://www.bttwoo.com/v_play/play-100.html")

    @patch.object(Spider, "_request_html")
    def test_player_content_extracts_media_from_iframe(self, mock_request_html):
        mock_request_html.side_effect = [
            '<iframe src="/embed/demo.html"></iframe>',
            '<script>var source = "https://media.example/iframe.m3u8";</script>',
        ]
        play_id = self.spider._encode_play_id("play-200", "900", "第2集")
        result = self.spider.playerContent("两个BT", play_id, {})
        self.assertEqual(mock_request_html.call_args_list[0].args[0], "https://www.bttwoo.com/v_play/play-200.html")
        self.assertEqual(mock_request_html.call_args_list[1].args[0], "https://www.bttwoo.com/embed/demo.html")
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://media.example/iframe.m3u8")

    @patch.object(Spider, "_request_html")
    def test_player_content_falls_back_to_parse_when_no_media_found(self, mock_request_html):
        mock_request_html.return_value = "<html><body>empty</body></html>"
        play_id = self.spider._encode_play_id("play-300", "900", "第3集")
        result = self.spider.playerContent("两个BT", play_id, {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["url"], "https://www.bttwoo.com/v_play/play-300.html")
        self.assertEqual(result["header"]["Referer"], "https://www.bttwoo.com/v_play/play-300.html")


if __name__ == "__main__":
    unittest.main()
