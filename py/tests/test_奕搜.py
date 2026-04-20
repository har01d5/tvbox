import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from urllib.parse import quote
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("yisou_spider", str(ROOT / "奕搜.py")).load_module()
Spider = MODULE.Spider


class TestYiSouSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["dy", "dsj", "zy", "dm", "jlp", "dj"],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_extract_remark_from_title_prefers_update_score_then_year(self):
        self.assertEqual(self.spider._extract_remark_from_title("片名 [更12] [8.5分] [2025]"), "更新至12集")
        self.assertEqual(self.spider._extract_remark_from_title("片名 [8.5分] [2025]"), "评分:8.5")
        self.assertEqual(self.spider._extract_remark_from_title("片名 [2025]"), "首播:2025")

    def test_clean_title_text_removes_bracket_tags(self):
        self.assertEqual(self.spider._clean_title_text("片名 [更12] [2025]"), "片名")

    def test_parse_list_boxes_extracts_short_ids_and_remark(self):
        html = """
        <div class="list-boxes">
          <a class="text_title_p" href="/resource/demo-1">示例影片 [更12] [8.2分]</a>
          <div class="left_ly"><a href="/resource/fallback-1">备链</a></div>
          <img class="image_left" src="/cover.jpg" />
          <div class="list-actions"><span>列表备注</span></div>
        </div>
        """
        self.assertEqual(
            self.spider._parse_list_boxes(html),
            [
                {
                    "vod_id": "/resource/demo-1",
                    "vod_name": "示例影片",
                    "vod_pic": "https://ysso.cc/cover.jpg",
                    "vod_remarks": "更新至12集",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_expected_url(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="list-boxes">
          <a class="text_title_p" href="/resource/demo-2">分类影片 [2025]</a>
          <img class="image_left" src="/cat.jpg" />
        </div>
        """
        result = self.spider.categoryContent("dy", "3", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://ysso.cc/dy.html?page=3")
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["list"][0]["vod_id"], "/resource/demo-2")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_encoded_keyword(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="list-boxes">
          <a class="text_title_p" href="/resource/search-1">搜索影片 [8.9分]</a>
          <img class="image_left" src="/search.jpg" />
        </div>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            f"https://ysso.cc/search.html?keyword={quote('繁花')}&page=2",
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_remarks"], "评分:8.9")

    def test_search_content_empty_keyword_returns_empty_list(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})

    def test_identify_disk(self):
        self.assertEqual(self.spider._identify_disk("https://pan.baidu.com/s/demo"), "baidu")
        self.assertEqual(self.spider._identify_disk("https://pan.quark.cn/s/demo"), "quark")
        self.assertEqual(self.spider._identify_disk("https://drive.uc.cn/s/demo"), "uc")
        self.assertEqual(self.spider._identify_disk("https://www.alipan.com/s/demo"), "aliyun")
        self.assertEqual(self.spider._identify_disk("https://pan.xunlei.com/s/demo"), "xunlei")
        self.assertEqual(self.spider._identify_disk("https://example.com/file"), "")

    def test_build_play_data_groups_and_sorts_share_links(self):
        play = self.spider._build_play_data(
            [
                "https://pan.quark.cn/s/quark1",
                "https://pan.baidu.com/s/baidu1",
                "https://pan.quark.cn/s/quark1",
                "https://pan.xunlei.com/s/xl1",
            ]
        )
        self.assertEqual(play["vod_play_from"], "baidu$$$quark$$$xunlei")
        self.assertIn("baidu$https://pan.baidu.com/s/baidu1", play["vod_play_url"])
        self.assertIn("quark$https://pan.quark.cn/s/quark1", play["vod_play_url"])

    def test_build_play_data_falls_back_to_push_urls_for_unknown_links(self):
        play = self.spider._build_play_data(
            ["https://example.com/file1", "https://example.com/file2"]
        )
        self.assertEqual(play["vod_play_from"], "奕搜")
        self.assertEqual(
            play["vod_play_url"],
            "1$push://https://example.com/file1#2$push://https://example.com/file2",
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_extracts_metadata_and_netdisk_links(self, mock_request_html):
        mock_request_html.return_value = """
        <html><body>
          <h1 class="articl_title">示例详情 [更12] [2025]</h1>
          <div class="tc-box article-box"><img src="/poster.jpg" /></div>
          <div id="info">
            <span><span class="pl">导演：</span><span class="attrs"><a>导演甲</a><a>编剧乙</a></span></span>
            <span><span class="pl">主演：</span><span class="attrs"><a>演员甲</a><a>演员乙</a></span></span>
          </div>
          <p style="color: rgb(51, 51, 51)">这是一段足够长的剧情简介，用于测试详情页内容提取逻辑。</p>
          <a target="_blank" href="https://pan.quark.cn/s/abc123">夸克</a>
          <a target="_blank" href="https://pan.baidu.com/s/demo456">百度</a>
          <div>提取码：a1b2</div>
        </body></html>
        """
        result = self.spider.detailContent(["/resource/demo-1"])
        vod = result["list"][0]
        self.assertEqual(mock_request_html.call_args.args[0], "https://ysso.cc/resource/demo-1")
        self.assertEqual(vod["vod_id"], "/resource/demo-1")
        self.assertEqual(vod["vod_name"], "示例详情")
        self.assertEqual(vod["vod_pic"], "https://ysso.cc/poster.jpg")
        self.assertEqual(vod["vod_director"], "导演甲, 编剧乙")
        self.assertEqual(vod["vod_actor"], "演员甲, 演员乙")
        self.assertIn("剧情简介", vod["vod_content"])
        self.assertEqual(vod["vod_play_from"], "baidu$$$quark")
        self.assertIn("提取码: a1b2", vod["vod_remarks"])

    def test_player_content_strips_push_prefix(self):
        result = self.spider.playerContent("奕搜", "push://https://pan.quark.cn/s/abc123", {})
        self.assertEqual(result, {"parse": 0, "url": "https://pan.quark.cn/s/abc123"})

    def test_player_content_passthroughs_http_url(self):
        result = self.spider.playerContent("quark", "https://pan.quark.cn/s/abc123", {})
        self.assertEqual(result, {"parse": 0, "url": "https://pan.quark.cn/s/abc123"})

    @patch.object(Spider, "_request_html")
    def test_detail_content_returns_empty_list_when_html_missing(self, mock_request_html):
        mock_request_html.return_value = ""
        self.assertEqual(self.spider.detailContent(["/resource/missing"]), {"list": []})


if __name__ == "__main__":
    unittest.main()
