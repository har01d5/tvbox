import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("rrdy_spider", str(ROOT / "人人电影.py")).load_module()
Spider = MODULE.Spider


class TestRenRenDianYingSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_reference_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("movie/list_2", "电影"),
                ("dianshiju/list_6", "电视剧"),
                ("dongman/list_13", "动漫"),
                ("zongyi/list_10", "老电影"),
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_url_and_pan_detection_helpers(self):
        self.assertEqual(self.spider._build_url("/movie/1.html"), "https://www.rrdynb.com/movie/1.html")
        self.assertEqual(
            self.spider._build_url("https://pan.baidu.com/s/demo"),
            "https://pan.baidu.com/s/demo",
        )
        self.assertTrue(self.spider._is_supported_pan_url("https://pan.baidu.com/s/demo"))
        self.assertTrue(self.spider._is_supported_pan_url("https://pan.quark.cn/s/demo"))
        self.assertFalse(self.spider._is_supported_pan_url("https://pan.xunlei.com/s/demo"))

    def test_clean_search_title_and_normalize_title(self):
        self.assertEqual(
            self.spider._clean_search_title("<font color='red'>剑来</font> 第二季"),
            "剑来 第二季",
        )
        self.assertEqual(self.spider._normalize_title("《繁花》"), "繁花")
        self.assertEqual(self.spider._normalize_title("「诛仙」特别篇"), "诛仙")
        self.assertEqual(self.spider._normalize_title("普通标题"), "普通标题")

    def test_parse_cards_extracts_expected_fields(self):
        html = """
        <ul id="movielist">
          <li>
            <div class="pure-img"><img class="pure-img" data-original="/poster.jpg" /></div>
            <div class="intro">
              <h2><a href="/movie/123.html" title="《示例电影》">《示例电影》</a></h2>
            </div>
            <div class="dou"><b>8.8</b></div>
          </li>
        </ul>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "/movie/123.html",
                    "vod_name": "示例电影",
                    "vod_pic": "https://www.rrdynb.com/poster.jpg",
                    "vod_remarks": "8.8",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_reference_url_and_page_payload(self, mock_request_html):
        mock_request_html.return_value = """
        <ul id="movielist">
          <li>
            <img class="pure-img" data-original="/cate.jpg" />
            <div class="intro"><h2><a href="/movie/456.html" title="分类影片">分类影片</a></h2></div>
            <div class="dou"><b>更新中</b></div>
          </li>
        </ul>
        """
        result = self.spider.categoryContent("movie/list_2", "3", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.rrdynb.com/movie/list_2_3.html",
        )
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_builds_reference_url_and_cleans_highlight_title(self, mock_request_html):
        mock_request_html.return_value = """
        <ul id="movielist">
          <li class="pure-g shadow">
            <div class="pure-u-5-24"><img data-original="/search.jpg" /></div>
            <div class="intro">
              <h2><a href="/movie/789.html" title="<font color='red'>剑来</font> 第二季">抢先看</a></h2>
            </div>
            <div class="dou"><b>9.2</b></div>
          </li>
        </ul>
        """
        result = self.spider.searchContent("剑来", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.rrdynb.com/plus/search.php?q=%E5%89%91%E6%9D%A5&pagesize=10&submit=&PageNo=2",
        )
        self.assertEqual(
            result["list"][0],
            {
                "vod_id": "/movie/789.html",
                "vod_name": "剑来 第二季",
                "vod_pic": "https://www.rrdynb.com/search.jpg",
                "vod_remarks": "9.2",
            },
        )

    def test_search_content_returns_empty_list_for_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})

    def test_extract_pan_links_filters_xunlei_and_aliyun(self):
        html = """
        <div class="movie-txt">
          <a href="https://pan.baidu.com/s/b1">百度网盘</a>
          <a href="https://pan.quark.cn/s/q1">夸克资源</a>
          <a href="https://pan.xunlei.com/s/x1">迅雷资源</a>
          <a href="https://www.alipan.com/s/a1">阿里资源</a>
        </div>
        """
        self.assertEqual(
            self.spider._extract_pan_links(html),
            [
                ("百度网盘", "https://pan.baidu.com/s/b1"),
                ("夸克资源", "https://pan.quark.cn/s/q1"),
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_extracts_meta_and_builds_single_pan_line(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="movie-des"><h1>人人示例片</h1></div>
        <div class="movie-img"><img src="/poster-detail.jpg" /></div>
        <div class="movie-txt">
          <p>一段简介</p>
          <a href="https://pan.baidu.com/s/b1">百度网盘</a>
          <a href="https://pan.quark.cn/s/q1">夸克资源</a>
          <a href="https://pan.xunlei.com/s/x1">迅雷资源</a>
        </div>
        """
        result = self.spider.detailContent(["/movie/123.html"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.rrdynb.com/movie/123.html")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "/movie/123.html")
        self.assertEqual(vod["vod_name"], "人人示例片")
        self.assertEqual(vod["vod_pic"], "https://www.rrdynb.com/poster-detail.jpg")
        self.assertIn("一段简介", vod["vod_content"])
        self.assertEqual(vod["vod_play_from"], "网盘")
        self.assertEqual(
            vod["vod_play_url"],
            "百度网盘$https://pan.baidu.com/s/b1#夸克资源$https://pan.quark.cn/s/q1",
        )

    def test_player_content_passthroughs_supported_pan_urls(self):
        self.assertEqual(
            self.spider.playerContent("网盘", "https://pan.baidu.com/s/demo", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.baidu.com/s/demo"},
        )

    def test_player_content_rejects_non_pan_url(self):
        self.assertEqual(
            self.spider.playerContent("站内", "/movie/123.html", {}),
            {"parse": 0, "playUrl": "", "url": ""},
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_leaves_play_fields_empty_when_no_pan_url_exists(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="movie-des"><h1>无网盘影片</h1></div>
        <div class="movie-img"><img src="/poster.jpg" /></div>
        <div class="movie-txt"><p>仅有简介，没有网盘。</p></div>
        """
        result = self.spider.detailContent(["/movie/empty.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "无网盘影片")
        self.assertEqual(vod["vod_play_from"], "")
        self.assertEqual(vod["vod_play_url"], "")
