import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("feikuai_spider", str(ROOT / "飞快TV.py")).load_module()
Spider = MODULE.Spider


class TestFeikuaiSpider(unittest.TestCase):
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
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    @patch.object(Spider, "_request_html")
    def test_category_content_parses_short_vod_id(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item" href="/voddetail/12345.html" title="分类影片">
          <img class="lazy" data-original="/cover.jpg" />
          <div class="module-item-note">更新至10集</div>
        </a>
        """
        result = self.spider.categoryContent("2", "3", False, {})
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://feikuai.tv/vodshow/2--------3---.html",
        )
        self.assertEqual(
            result["list"],
            [
                {
                    "vod_id": "/voddetail/12345.html",
                    "vod_name": "分类影片",
                    "vod_pic": "https://feikuai.tv/cover.jpg",
                    "vod_remarks": "更新至10集",
                }
            ],
        )
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_request_html")
    def test_search_content_parses_cards_and_blank_keyword(self, mock_request_html):
        blank = self.spider.searchContent("", False, "1")
        self.assertEqual(blank, {"page": 1, "limit": 0, "total": 0, "list": []})
        mock_request_html.assert_not_called()

        mock_request_html.return_value = """
        <div class="module-card-item module-item">
          <a class="module-card-item-poster" href="/voddetail/67890.html"></a>
          <div class="module-item-pic"><img data-original="/search.jpg" /></div>
          <div class="module-card-item-title"><strong>搜索命中</strong></div>
          <div class="module-item-note">HD</div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://feikuai.tv/label/search_ajax.html?wd=%E7%B9%81%E8%8A%B1&by=time&order=desc&page=2",
        )
        self.assertEqual(result["list"][0]["vod_id"], "/voddetail/67890.html")

    @patch.object(Spider, "_request_html")
    def test_detail_content_merges_online_and_pan_groups(self, mock_request_html):
        mock_request_html.return_value = """
        <h1>示例影片</h1>
        <div class="module-item-pic"><img data-original="/detail.jpg" /></div>
        <div class="module-info-introduction-content">这里是简介</div>
        <div class="module-tab-items-box">
          <div class="module-tab-item"><span>线路A</span></div>
          <div class="module-tab-item"><span>线路B</span></div>
        </div>
        <div class="module-list tab-list">
          <a class="module-play-list-link" href="/vodplay/1-1-1.html">第1集</a>
          <a class="module-play-list-link" href="/vodplay/1-1-2.html">第2集</a>
        </div>
        <div class="module-list tab-list">
          <a class="module-play-list-link" href="/vodplay/1-2-1.html">第1集</a>
        </div>
        <div class="module-list">
          <div class="tab-content">
            <h4>夸克资源@分享一</h4>
            <p>https://pan.quark.cn/s/demo1</p>
          </div>
          <div class="tab-content">
            <h4>百度合集@分享二</h4>
            <p>https://pan.baidu.com/s/demo2</p>
          </div>
        </div>
        """
        result = self.spider.detailContent(["/voddetail/1.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "/voddetail/1.html")
        self.assertEqual(vod["vod_name"], "示例影片")
        self.assertEqual(vod["vod_pic"], "https://feikuai.tv/detail.jpg")
        self.assertEqual(vod["vod_content"], "这里是简介")
        self.assertEqual(vod["vod_play_from"], "线路A$$$线路B$$$quark$$$baidu")
        self.assertEqual(
            vod["vod_play_url"],
            "第1集$/vodplay/1-1-1.html#第2集$/vodplay/1-1-2.html$$$第1集$/vodplay/1-2-1.html$$$夸克资源$https://pan.quark.cn/s/demo1$$$百度合集$https://pan.baidu.com/s/demo2",
        )
