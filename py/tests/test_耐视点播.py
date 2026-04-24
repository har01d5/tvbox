import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("nsvod_spider", str(ROOT / "耐视点播.py")).load_module()
Spider = MODULE.Spider


class TestNSVodSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_fixed_classes(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("1", "电影"),
                ("2", "连续剧"),
                ("3", "综艺"),
                ("4", "动漫"),
                ("37", "Netflix"),
                ("40", "纪录片"),
            ],
        )

    def test_build_url_and_extract_vod_id_handle_relative_paths(self):
        self.assertEqual(
            self.spider._build_url("/index.php/vod/detail/id/7.html"),
            "https://nsvod.me/index.php/vod/detail/id/7.html",
        )
        self.assertEqual(
            self.spider._build_url("//img.example/poster.jpg"),
            "https://img.example/poster.jpg",
        )
        self.assertEqual(self.spider._extract_vod_id("/index.php/vod/detail/id/99.html"), "99")
        self.assertEqual(self.spider._extract_vod_id("/bad/path"), "")

    def test_parse_cards_extracts_unique_videos(self):
        html = """
        <a href="/index.php/vod/detail/id/11.html" title="示例A">
          <img data-src="/a.jpg" />
          <span class="public-list-prb">更新至01集</span>
        </a>
        <a href="/index.php/vod/detail/id/12.html" title="示例B">
          <img src="/b.jpg" />
          <div class="public-list-subtitle">HD</div>
        </a>
        <a href="/index.php/vod/detail/id/11.html" title="示例A">
          <img data-src="/dup.jpg" />
        </a>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "11",
                    "vod_name": "示例A",
                    "vod_pic": "https://nsvod.me/a.jpg",
                    "vod_remarks": "更新至01集",
                },
                {
                    "vod_id": "12",
                    "vod_name": "示例B",
                    "vod_pic": "https://nsvod.me/b.jpg",
                    "vod_remarks": "HD",
                },
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_home_video_content_reads_home_page(self, mock_request_html):
        mock_request_html.return_value = """
        <a href="/index.php/vod/detail/id/88.html" title="首页片">
          <img data-src="/home.jpg" />
          <span class="public-list-prb">热播</span>
        </a>
        """
        result = self.spider.homeVideoContent()
        self.assertEqual(mock_request_html.call_args.args[0], "https://nsvod.me/")
        self.assertEqual(
            result,
            {
                "list": [
                    {
                        "vod_id": "88",
                        "vod_name": "首页片",
                        "vod_pic": "https://nsvod.me/home.jpg",
                        "vod_remarks": "热播",
                    }
                ]
            },
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_reads_category_page(self, mock_request_html):
        mock_request_html.return_value = """
        <a href="/index.php/vod/detail/id/21.html" title="分类片">
          <img data-src="/cate.jpg" />
          <span class="public-list-prb">更新中</span>
        </a>
        """
        result = self.spider.categoryContent("2", "3", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://nsvod.me/index.php/vod/show/id/2.html?page=3",
        )
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["list"][0]["vod_id"], "21")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_category_content_falls_back_to_home_sections(self, mock_request_html):
        mock_request_html.side_effect = [
            "<html></html>",
            """
            <div class="title-h cor4">最新综艺</div>
            <a href="/index.php/vod/detail/id/31.html" title="综艺回退">
              <img data-src="/variety.jpg" />
              <span class="public-list-prb">第1期</span>
            </a>
            <div class="title-h cor4">最新纪录片</div>
            """,
        ]
        result = self.spider.categoryContent("3", "1", False, {})
        self.assertEqual([item["vod_id"] for item in result["list"]], ["31"])

    @patch.object(Spider, "_request_html")
    def test_search_content_short_circuits_blank_keyword_and_parses_results(self, mock_request_html):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})
        mock_request_html.assert_not_called()

        mock_request_html.return_value = """
        <div class="module-search-item">
          <a class="video-serial" href="/index.php/vod/detail/id/45.html" title="搜索片">抢先版</a>
          <div class="module-item-pic"><img data-src="/search.jpg" alt="搜索片" /></div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://nsvod.me/index.php/vod/search.html?wd=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(
            result["list"][0],
            {
                "vod_id": "45",
                "vod_name": "搜索片",
                "vod_pic": "https://nsvod.me/search.jpg",
                "vod_remarks": "抢先版",
            },
        )

    def test_parse_detail_page_extracts_metadata_and_play_groups(self):
        html = """
        <title>《耐视示例》在线观看</title>
        <div class="detail-pic"><img data-src="/poster-detail.jpg" /></div>
        <div>年份</em><span>2025</span></div>
        <div>地区</em><span>中国香港</span></div>
        <div>导演</em> 导演甲 </div>
        <div>主演</em> 演员甲 / 演员乙 </div>
        <div id="height_limit"><p>这是一段简介。</p></div>
        <div class="anthology-tab">
          <div class="swiper-slide">线路A 2集</div>
          <div class="swiper-slide">线路B 1集</div>
        </div>
        <div class="anthology-list">
          <div class="anthology-list-box">
            <a href="/index.php/vod/play/id/70/sid/1/nid/1.html">第1集</a>
            <a href="/index.php/vod/play/id/70/sid/1/nid/2.html">第2集</a>
          </div>
          <div class="anthology-list-box">
            <a href="/index.php/vod/play/id/70/sid/2/nid/1.html">正片</a>
          </div>
        </div>
        """
        vod = self.spider._parse_detail_page("70", html)
        self.assertEqual(vod["vod_name"], "耐视示例")
        self.assertEqual(vod["vod_pic"], "https://nsvod.me/poster-detail.jpg")
        self.assertEqual(vod["vod_year"], "2025")
        self.assertEqual(vod["vod_area"], "中国香港")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_actor"], "演员甲 / 演员乙")
        self.assertEqual(vod["vod_content"], "这是一段简介。")
        self.assertEqual(vod["vod_play_from"], "线路A$$$线路B")
        self.assertEqual(
            vod["vod_play_url"],
            "第1集$/index.php/vod/play/id/70/sid/1/nid/1.html#第2集$/index.php/vod/play/id/70/sid/1/nid/2.html$$$正片$/index.php/vod/play/id/70/sid/2/nid/1.html",
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_reads_detail_url_and_returns_single_vod(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="slide-info-title">详情标题</div>
        <div class="anthology-list">
          <div class="anthology-list-box">
            <a href="/index.php/vod/play/id/80/sid/1/nid/1.html">正片</a>
          </div>
        </div>
        """
        result = self.spider.detailContent(["80"])
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://nsvod.me/index.php/vod/detail/id/80.html",
        )
        self.assertEqual(result["list"][0]["vod_id"], "80")
        self.assertEqual(result["list"][0]["vod_name"], "详情标题")
        self.assertEqual(result["list"][0]["vod_play_from"], "线路1")
        self.assertEqual(result["list"][0]["vod_play_url"], "正片$/index.php/vod/play/id/80/sid/1/nid/1.html")

    @patch.object(Spider, "_request_html")
    def test_player_content_returns_player_aaaa_url(self, mock_request_html):
        mock_request_html.return_value = """
        <script>
        var player_aaaa={"url":"https://cdn.example/direct.m3u8","encrypt":"0"}
        </script>
        """
        result = self.spider.playerContent("线路A", "/index.php/vod/play/id/70/sid/1/nid/1.html", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://cdn.example/direct.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://nsvod.me/index.php/vod/play/id/70/sid/1/nid/1.html")

    @patch.object(Spider, "_request_html")
    def test_player_content_supports_nested_player_aaaa_object(self, mock_request_html):
        mock_request_html.return_value = """
        <script type="text/javascript">
        var player_aaaa={"flag":"play","encrypt":0,"vod_data":{"vod_name":"阿爸请你嘛嘛吼","vod_actor":"甲,乙","vod_class":"剧情"},"url":"https:\\/\\/vip.dytt-kan.com\\/20260423\\/13858_751d8d46\\/index.m3u8","from":"dyttm3u8","id":"22663","sid":1,"nid":1}
        </script>
        """
        result = self.spider.playerContent("DY线路", "/index.php/vod/play/id/22663/sid/1/nid/1.html", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://vip.dytt-kan.com/20260423/13858_751d8d46/index.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://nsvod.me/index.php/vod/play/id/22663/sid/1/nid/1.html")

    @patch.object(Spider, "_request_html")
    def test_player_content_falls_back_to_inline_m3u8(self, mock_request_html):
        mock_request_html.return_value = '<script>var now="https://cdn.example/fallback.m3u8?token=1"</script>'
        result = self.spider.playerContent("线路A", "/index.php/vod/play/id/71/sid/1/nid/1.html", {})
        self.assertEqual(result["url"], "https://cdn.example/fallback.m3u8?token=1")
        self.assertEqual(result["jx"], 0)

    @patch.object(Spider, "_request_html")
    def test_player_content_returns_play_page_when_no_media_url_found(self, mock_request_html):
        mock_request_html.return_value = "<html><body>empty</body></html>"
        result = self.spider.playerContent("线路A", "/index.php/vod/play/id/72/sid/1/nid/1.html", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["playUrl"], "")
        self.assertEqual(result["url"], "https://nsvod.me/index.php/vod/play/id/72/sid/1/nid/1.html")
        self.assertEqual(result["header"]["Referer"], "https://nsvod.me/")


if __name__ == "__main__":
    unittest.main()
