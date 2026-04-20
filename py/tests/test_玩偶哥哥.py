import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("wanougege_spider", str(ROOT / "玩偶哥哥.py")).load_module()
Spider = MODULE.Spider


class TestWanOuGeGeSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_all_eight_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("1", "玩偶电影"),
                ("2", "玩偶剧集"),
                ("3", "玩偶动漫"),
                ("4", "玩偶综艺"),
                ("44", "臻彩视界"),
                ("6", "玩偶短剧"),
                ("5", "玩偶音乐"),
                ("46", "玩偶纪录"),
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_and_fix_urls(self):
        self.assertEqual(self.spider._build_url("/voddetail/1.html"), "http://wogg.xxooo.cf/voddetail/1.html")
        self.assertEqual(
            self.spider._fix_img_url("/db.php?url=https://img.example/poster.jpg"),
            "http://wogg.xxooo.cf/db.php?url=https://img.example/poster.jpg",
        )
        self.assertEqual(
            self.spider._fix_img_url("https://gimg1.baidu.com/gimg/?src=data:image/png;base64,AAAA"),
            "",
        )

    def test_detect_pan_type_returns_type_and_title(self):
        self.assertEqual(self.spider._detect_pan_type("https://pan.baidu.com/s/demo"), ("baidu", "百度资源"))
        self.assertEqual(self.spider._detect_pan_type("https://pan.quark.cn/s/demo"), ("quark", "夸克资源"))
        self.assertEqual(self.spider._detect_pan_type("https://example.com/video"), ("", ""))

    def test_parse_cards_extracts_short_path_ids(self):
        html = """
        <div id="main">
          <div class="module-item">
            <div class="module-item-pic">
              <a href="/voddetail/123.html"></a>
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
                    "vod_id": "/voddetail/123.html",
                    "vod_name": "示例影片",
                    "vod_pic": "http://wogg.xxooo.cf/poster.jpg",
                    "vod_remarks": "HD",
                }
            ],
        )

    def test_parse_cards_ignores_module_items_container_and_uses_first_card_cover(self):
        html = """
        <div id="main">
          <div class="module-items">
            <div class="module-item">
              <div class="module-item-pic">
                <a href="/voddetail/123.html"></a>
                <img data-src="/poster-a.jpg" alt="示例影片A" />
              </div>
              <div class="module-item-text">HD</div>
            </div>
            <div class="module-item">
              <div class="module-item-pic">
                <a href="/voddetail/456.html"></a>
                <img data-src="/poster-b.jpg" alt="示例影片B" />
              </div>
              <div class="module-item-text">更新至10集</div>
            </div>
          </div>
        </div>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "/voddetail/123.html",
                    "vod_name": "示例影片A",
                    "vod_pic": "http://wogg.xxooo.cf/poster-a.jpg",
                    "vod_remarks": "HD",
                },
                {
                    "vod_id": "/voddetail/456.html",
                    "vod_name": "示例影片B",
                    "vod_pic": "http://wogg.xxooo.cf/poster-b.jpg",
                    "vod_remarks": "更新至10集",
                },
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_reference_url_and_returns_page_payload(self, mock_request_html):
        mock_request_html.return_value = """
        <div id="main">
          <div class="module-item">
            <div class="module-item-pic">
              <a href="/voddetail/456.html"></a>
              <img data-src="/cate.jpg" alt="分类影片" />
            </div>
            <div class="module-item-text">更新至10集</div>
          </div>
        </div>
        """
        result = self.spider.categoryContent("2", "3", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "http://wogg.xxooo.cf/vodshow/2--------3---.html",
        )
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_builds_reference_search_url_and_parses_results(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="module-search-item">
          <a class="video-serial" href="/voddetail/789.html" title="搜索影片">抢先版</a>
          <div class="module-item-pic">
            <img data-src="/search.jpg" alt="搜索影片" />
          </div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "http://wogg.xxooo.cf/vodsearch/-------------.html?wd=%E7%B9%81%E8%8A%B1&page=2",
        )
        self.assertEqual(
            result["list"][0],
            {
                "vod_id": "/voddetail/789.html",
                "vod_name": "搜索影片",
                "vod_pic": "http://wogg.xxooo.cf/search.jpg",
                "vod_remarks": "抢先版",
            },
        )

    def test_search_content_returns_empty_list_for_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})

    def test_build_pan_lines_deduplicates_and_sorts_supported_links(self):
        detail = {
            "pan_urls": [
                "https://pan.quark.cn/s/q1",
                "https://pan.baidu.com/s/b1",
                "https://pan.baidu.com/s/b1",
                "https://example.com/ignored",
            ]
        }
        self.assertEqual(
            self.spider._build_pan_lines(detail),
            [
                ("baidu#玩偶哥哥", "百度资源$https://pan.baidu.com/s/b1"),
                ("quark#玩偶哥哥", "夸克资源$https://pan.quark.cn/s/q1"),
            ],
        )

    def test_parse_detail_page_extracts_meta_content_and_pan_urls(self):
        html = """
        <div class="page-title">示例剧</div>
        <div class="mobile-play"><img class="lazyload" data-src="/poster.jpg" /></div>
        <div class="video-info-itemtitle">年代</div><div><a>2024</a></div>
        <div class="video-info-itemtitle">导演</div><div><a>导演甲</a></div>
        <div class="video-info-itemtitle">主演</div><div><a>演员甲</a><a>演员乙</a></div>
        <div class="video-info-itemtitle">剧情</div><div><p>一段剧情简介</p></div>
        <div class="module-row-info">
          <p>https://pan.quark.cn/s/q1</p>
          <p>https://pan.baidu.com/s/b1</p>
        </div>
        """
        detail = self.spider._parse_detail_page("/voddetail/123.html", html)
        self.assertEqual(detail["vod_name"], "示例剧")
        self.assertEqual(detail["vod_pic"], "http://wogg.xxooo.cf/poster.jpg")
        self.assertEqual(detail["vod_year"], "2024")
        self.assertEqual(detail["vod_director"], "导演甲")
        self.assertEqual(detail["vod_actor"], "演员甲,演员乙")
        self.assertEqual(detail["vod_content"], "一段剧情简介")
        self.assertEqual(detail["pan_urls"], ["https://pan.quark.cn/s/q1", "https://pan.baidu.com/s/b1"])

    @patch.object(Spider, "_request_html")
    def test_detail_content_builds_pan_play_fields(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="page-title">示例剧</div>
        <div class="mobile-play"><img class="lazyload" data-src="/poster.jpg" /></div>
        <div class="video-info-itemtitle">年代</div><div><a>2024</a></div>
        <div class="video-info-itemtitle">导演</div><div><a>导演甲</a></div>
        <div class="video-info-itemtitle">主演</div><div><a>演员甲</a></div>
        <div class="video-info-itemtitle">剧情</div><div><p>一段剧情简介</p></div>
        <div class="module-row-info">
          <p>https://pan.quark.cn/s/q1</p>
          <p>https://pan.baidu.com/s/b1</p>
        </div>
        """
        result = self.spider.detailContent(["/voddetail/123.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "示例剧")
        self.assertEqual(vod["vod_play_from"], "baidu#玩偶哥哥$$$quark#玩偶哥哥")
        self.assertEqual(
            vod["vod_play_url"],
            "百度资源$https://pan.baidu.com/s/b1$$$夸克资源$https://pan.quark.cn/s/q1",
        )

    def test_player_content_passthroughs_supported_pan_urls(self):
        self.assertEqual(
            self.spider.playerContent("baidu#玩偶哥哥", "https://pan.baidu.com/s/demo", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.baidu.com/s/demo"},
        )

    def test_player_content_rejects_non_pan_url(self):
        self.assertEqual(
            self.spider.playerContent("site", "/vodplay/1-1-1.html", {}),
            {"parse": 0, "playUrl": "", "url": ""},
        )
