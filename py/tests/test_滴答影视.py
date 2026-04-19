import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("dida_spider", str(ROOT / "滴答影视.py")).load_module()
Spider = MODULE.Spider


class TestDidaSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_classes_and_filters(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["1", "2", "5", "4", "3"],
        )
        self.assertEqual(
            [item["key"] for item in content["filters"]["1"]],
            ["class", "area", "year", "lang", "sort"],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    def test_build_category_url_applies_default_and_selected_filters(self):
        url = self.spider._build_category_url(
            "1",
            "2",
            {"area": "香港", "sort": "score", "class": "动作", "lang": "粤语", "year": "2025"},
        )
        self.assertEqual(url, "https://www.didahd.pro/show/1-香港-score-动作-粤语----2---2025")

    def test_build_category_url_for_first_page_keeps_page_segment(self):
        url = self.spider._build_category_url("2", "1", {})
        self.assertEqual(url, "https://www.didahd.pro/show/2--time------1---")

    def test_parse_cards_extracts_expected_fields(self):
        html = """
        <div class="myui-vodlist__box">
          <div class="title"><a href="/detail/888.html" title="示例影片"></a></div>
          <a class="lazyload" data-original="/cover.jpg"></a>
          <span class="pic-text">HD</span>
        </div>
        """
        cards = self.spider._parse_cards(html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "https://www.didahd.pro/detail/888.html",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.didahd.pro/cover.jpg",
                    "vod_remarks": "HD",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_built_url_and_returns_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="myui-vodlist__box">
          <div class="title"><a href="/detail/456.html" title="分类影片"></a></div>
          <a class="lazyload" data-original="/cate.jpg"></a>
          <span class="pic-text">完结</span>
        </div>
        """
        result = self.spider.categoryContent("1", "2", False, {"area": "香港", "sort": "score"})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.didahd.pro/show/1-香港-score------2---")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["pagecount"], 3)
        self.assertEqual(result["limit"], 12)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_search_url_and_parses_cards(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="myui-vodlist__box">
          <div class="title"><a href="/detail/321.html" title="搜索影片"></a></div>
          <a class="lazyload" data-original="/search.jpg"></a>
          <span class="pic-text">抢先版</span>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.didahd.pro/search/-------------.html?wd=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["list"][0]["vod_id"], "https://www.didahd.pro/detail/321.html")
        self.assertEqual(result["pagecount"], 2)

    def test_extract_netdisk_groups_deduplicates_links_and_sorts_by_priority(self):
        html = """
        <div class="myui-content__detail">
          <h1 class="title">滴答示例</h1>
          <p class="data"><span class="text-muted">分类：</span><a>动作</a></p>
          <p class="data"><span class="text-muted">地区：</span><a>大陆</a></p>
          <p class="data"><span class="text-muted">年份：</span><a>2025</a></p>
          <p class="data"><span class="text-muted">导演：</span><a>导演甲</a></p>
          <p class="data"><span class="text-muted">主演：</span><a>主演甲</a><a>主演乙</a></p>
        </div>
        <div class="myui-panel clearfix">
          <p class="text-muted">剧情简介：一段剧情简介</p>
        </div>
        <div class="download-panel">
          <p class="text-muted col-pd"><b>夸克：</b><a href="https://pan.quark.cn/s/q1">查看</a></p>
          <p class="text-muted col-pd"><b>百度：</b><a href="https://pan.baidu.com/s/b1">合集</a></p>
          <p class="text-muted col-pd"><b>夸克：</b><a href="https://pan.quark.cn/s/q1">一键复制</a></p>
          <p class="text-muted col-pd"><b>迅雷：</b><a href="https://pan.xunlei.com/s/x1">迅雷资源</a></p>
        </div>
        """
        vod = self.spider._parse_detail_page(html, "https://www.didahd.pro/detail/demo.html")
        self.assertEqual(vod["vod_name"], "滴答示例")
        self.assertEqual(vod["vod_year"], "2025")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_class"], "动作")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_actor"], "主演甲,主演乙")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "baidu$$$quark$$$xunlei")
        self.assertEqual(
            vod["vod_play_url"],
            "合集$https://pan.baidu.com/s/b1$$$查看$https://pan.quark.cn/s/q1$$$迅雷资源$https://pan.xunlei.com/s/x1",
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_keeps_only_netdisk_sources(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="myui-content__detail"><h1 class="title">详情标题</h1></div>
        <div class="download-panel">
          <p class="text-muted col-pd"><b>UC 网盘：</b><a href="https://drive.uc.cn/s/u1">合集</a></p>
        </div>
        <ul class="myui-content__list"><li><a href="/play/111-1-1.html">正片</a></li></ul>
        """
        result = self.spider.detailContent(["https://www.didahd.pro/detail/111.html"])
        self.assertEqual(result["list"][0]["vod_id"], "https://www.didahd.pro/detail/111.html")
        self.assertEqual(result["list"][0]["vod_play_from"], "uc")
        self.assertEqual(result["list"][0]["vod_play_url"], "合集$https://drive.uc.cn/s/u1")

    def test_player_content_returns_direct_netdisk_link(self):
        result = self.spider.playerContent("quark", "https://pan.quark.cn/s/demo", {})
        self.assertEqual(result, {"parse": 0, "playUrl": "", "url": "https://pan.quark.cn/s/demo"})

    def test_player_content_supports_uc_baidu_xunlei_aliyun_links(self):
        self.assertEqual(
            self.spider.playerContent("uc", "https://drive.uc.cn/s/u1", {})["url"],
            "https://drive.uc.cn/s/u1",
        )
        self.assertEqual(
            self.spider.playerContent("baidu", "https://pan.baidu.com/s/b1", {})["url"],
            "https://pan.baidu.com/s/b1",
        )
        self.assertEqual(
            self.spider.playerContent("xunlei", "https://pan.xunlei.com/s/x1", {})["url"],
            "https://pan.xunlei.com/s/x1",
        )
        self.assertEqual(
            self.spider.playerContent("aliyun", "https://www.alipan.com/s/a1", {})["url"],
            "https://www.alipan.com/s/a1",
        )

    def test_player_content_returns_empty_for_non_netdisk_input(self):
        result = self.spider.playerContent("播放线路", "/play/111-1-1.html", {})
        self.assertEqual(result, {"parse": 0, "playUrl": "", "url": ""})

    def test_home_content_keeps_reference_filter_values(self):
        movie_filters = self.spider.homeContent(False)["filters"]["1"]
        self.assertIn({"n": "动作", "v": "动作"}, movie_filters[0]["value"])
        self.assertIn({"n": "香港", "v": "香港"}, movie_filters[1]["value"])
        self.assertIn({"n": "2025", "v": "2025"}, movie_filters[2]["value"])
        self.assertIn({"n": "粤语", "v": "粤语"}, movie_filters[3]["value"])
        self.assertEqual(movie_filters[4]["value"][1], {"n": "人气", "v": "hits"})


if __name__ == "__main__":
    unittest.main()
