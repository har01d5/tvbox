import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("ouge_spider", str(ROOT / "欧歌.py")).load_module()
Spider = MODULE.Spider


class TestOuGeSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_reference_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("1", "欧歌电影"),
                ("2", "欧哥剧集"),
                ("3", "欧歌动漫"),
                ("4", "欧歌综艺"),
                ("5", "欧歌短剧"),
                ("21", "欧歌综合"),
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_url_joins_relative_paths_against_host(self):
        self.assertEqual(
            self.spider._build_url("/index.php/vod/detail/id/1.html"),
            "https://woog.nxog.eu.org/index.php/vod/detail/id/1.html",
        )
        self.assertEqual(
            self.spider._build_url("https://cdn.example.com/poster.jpg"),
            "https://cdn.example.com/poster.jpg",
        )

    def test_detect_pan_type_returns_expected_type_and_label(self):
        self.assertEqual(
            self.spider._detect_pan_type("https://pan.baidu.com/s/demo"),
            ("baidu", "百度资源"),
        )
        self.assertEqual(
            self.spider._detect_pan_type("https://pan.quark.cn/s/demo"),
            ("quark", "夸克资源"),
        )
        self.assertEqual(
            self.spider._detect_pan_type("https://example.com/video"),
            ("", ""),
        )

    def test_parse_cards_extracts_short_path_id_and_cover(self):
        html = """
        <div id="main">
          <div class="module-item">
            <div class="module-item-pic">
              <a href="/index.php/vod/detail/id/123.html"></a>
              <img data-src="/poster.jpg" alt="示例影片" />
            </div>
            <div class="module-item-text">HD</div>
          </div>
        </div>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "/index.php/vod/detail/id/123.html",
                    "vod_name": "示例影片",
                    "vod_pic": "https://woog.nxog.eu.org/poster.jpg",
                    "vod_remarks": "HD",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_reference_url_and_returns_page_payload(self, mock_request_html):
        mock_request_html.return_value = """
        <div id="main">
          <div class="module-item">
            <div class="module-item-pic">
              <a href="/index.php/vod/detail/id/456.html"></a>
              <img data-src="/cate.jpg" alt="分类影片" />
            </div>
            <div class="module-item-text">更新至10集</div>
          </div>
        </div>
        """
        result = self.spider.categoryContent("2", "3", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://woog.nxog.eu.org/index.php/vod/show/id/2/page/3.html",
        )
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_builds_reference_url_and_parses_results(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="module-search-item">
          <a class="video-serial" href="/index.php/vod/detail/id/789.html" title="搜索影片">抢先版</a>
          <div class="module-item-pic">
            <img data-src="/search.jpg" alt="搜索影片" />
          </div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://woog.nxog.eu.org/index.php/vod/search/page/2/wd/%E7%B9%81%E8%8A%B1.html",
        )
        self.assertEqual(
            result["list"][0],
            {
                "vod_id": "/index.php/vod/detail/id/789.html",
                "vod_name": "搜索影片",
                "vod_pic": "https://woog.nxog.eu.org/search.jpg",
                "vod_remarks": "抢先版",
            },
        )
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_short_circuits_blank_keyword(self, mock_request_html):
        result = self.spider.searchContent("", False, "1")
        self.assertEqual(result, {"page": 1, "total": 0, "list": []})
        mock_request_html.assert_not_called()

    def test_parse_detail_page_extracts_metadata_and_deduplicated_pan_groups(self):
        html = """
        <div class="page-title">欧歌示例</div>
        <div class="mobile-play">
          <img class="lazyload" data-src="/poster-detail.jpg" />
        </div>
        <div class="module-item-caption"><span>2025</span></div>
        <div class="video-info-itemtitle">导演</div>
        <div><a>导演甲</a><a>导演乙</a></div>
        <div class="video-info-itemtitle">主演</div>
        <div><a>演员甲</a><a>演员乙</a></div>
        <div class="video-info-itemtitle">剧情</div>
        <div><p>这是一段剧情简介。</p></div>
        <div class="module-row-info"><p>https://pan.quark.cn/s/q-demo</p></div>
        <div class="module-row-info"><p>百度合集 https://pan.baidu.com/s/b-demo</p></div>
        <div class="module-row-info"><p>https://pan.quark.cn/s/q-demo</p></div>
        """
        vod = self.spider._parse_detail_page(html, "/index.php/vod/detail/id/999.html")
        self.assertEqual(vod["vod_id"], "/index.php/vod/detail/id/999.html")
        self.assertEqual(vod["vod_name"], "欧歌示例")
        self.assertEqual(vod["vod_pic"], "https://woog.nxog.eu.org/poster-detail.jpg")
        self.assertEqual(vod["vod_year"], "2025")
        self.assertEqual(vod["vod_director"], "导演甲,导演乙")
        self.assertEqual(vod["vod_actor"], "演员甲,演员乙")
        self.assertEqual(vod["vod_content"], "这是一段剧情简介。")
        self.assertEqual(vod["vod_play_from"], "baidu$$$quark")
        self.assertEqual(
            vod["vod_play_url"],
            "百度资源$https://pan.baidu.com/s/b-demo$$$夸克资源$https://pan.quark.cn/s/q-demo",
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_reads_detail_page_and_returns_single_vod(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="page-title">详情标题</div>
        <div class="module-row-info"><p>https://pan.quark.cn/s/detail-demo</p></div>
        """
        result = self.spider.detailContent(["/index.php/vod/detail/id/1000.html"])
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://woog.nxog.eu.org/index.php/vod/detail/id/1000.html",
        )
        self.assertEqual(result["list"][0]["vod_id"], "/index.php/vod/detail/id/1000.html")
        self.assertEqual(result["list"][0]["vod_name"], "详情标题")
        self.assertEqual(result["list"][0]["vod_play_from"], "quark")
        self.assertEqual(result["list"][0]["vod_play_url"], "夸克资源$https://pan.quark.cn/s/detail-demo")

    def test_parse_detail_page_returns_empty_shell_for_blank_html(self):
        self.assertEqual(
            self.spider._parse_detail_page("", "/index.php/vod/detail/id/404.html"),
            {
                "vod_id": "/index.php/vod/detail/id/404.html",
                "vod_name": "",
                "vod_pic": "",
                "vod_year": "",
                "vod_director": "",
                "vod_actor": "",
                "vod_content": "",
                "vod_play_from": "",
                "vod_play_url": "",
            },
        )

    def test_player_content_transparently_returns_supported_pan_link(self):
        result = self.spider.playerContent("quark", "https://pan.quark.cn/s/demo", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://pan.quark.cn/s/demo")
        self.assertEqual(result["header"], {})

    def test_player_content_returns_empty_url_for_unknown_link(self):
        result = self.spider.playerContent("unknown", "/index.php/vod/play/id/1.html", {})
        self.assertEqual(result, {"parse": 0, "jx": 0, "playUrl": "", "url": "", "header": {}})


if __name__ == "__main__":
    unittest.main()
