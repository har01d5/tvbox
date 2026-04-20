import base64
import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("wanou_aggregate_spider", str(ROOT / "玩偶聚合.py")).load_module()
Spider = MODULE.Spider


class TestWanouAggregateSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_site_classes_and_category_filter(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"][:3]],
            ["site_wanou", "site_muou", "site_labi"],
        )
        self.assertEqual(content["class"][0]["type_name"], "玩偶")
        self.assertEqual(content["filters"]["site_wanou"][0]["key"], "categoryId")
        self.assertEqual(content["filters"]["site_wanou"][0]["value"][1], {"n": "电影", "v": "1"})

    def test_home_content_exposes_zhizhen_site_and_categories(self):
        content = self.spider.homeContent(False)
        type_ids = [item["type_id"] for item in content["class"]]
        self.assertIn("site_zhizhen", type_ids)
        self.assertEqual(
            content["filters"]["site_zhizhen"][0]["value"][1:],
            [
                {"n": "电影", "v": "1"},
                {"n": "剧集", "v": "2"},
                {"n": "动漫", "v": "3"},
                {"n": "综艺", "v": "4"},
                {"n": "短剧", "v": "5"},
                {"n": "老剧", "v": "24"},
                {"n": "严选", "v": "26"},
            ],
        )

    def test_home_content_exposes_ouge_site_and_categories(self):
        content = self.spider.homeContent(False)
        type_ids = [item["type_id"] for item in content["class"]]
        self.assertIn("site_ouge", type_ids)
        self.assertEqual(
            content["filters"]["site_ouge"][0]["value"][1:],
            [
                {"n": "电影", "v": "1"},
                {"n": "剧集", "v": "2"},
                {"n": "动漫", "v": "3"},
                {"n": "综艺", "v": "4"},
                {"n": "短剧", "v": "5"},
                {"n": "综合", "v": "21"},
            ],
        )

    @patch.object(
        Spider,
        "_load_local_filter_groups",
        return_value=[
            {
                "key": "year",
                "name": "年份",
                "init": "",
                "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}],
            }
        ],
    )
    def test_home_content_appends_local_filter_groups_after_category_filter(self, mock_load_local_filter_groups):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["key"] for item in content["filters"]["site_wanou"][:2]],
            ["categoryId", "year"],
        )

    def test_encode_and_decode_site_vod_id_round_trip(self):
        vod_id = self.spider._encode_site_vod_id("wanou", "/voddetail/12345.html")
        self.assertEqual(vod_id, "site:wanou:/voddetail/12345.html")
        self.assertEqual(
            self.spider._decode_site_vod_id(vod_id),
            {"site": "wanou", "path": "/voddetail/12345.html"},
        )

    def test_encode_and_decode_aggregate_vod_id_round_trip(self):
        payload = [
            {"site": "wanou", "path": "/voddetail/1.html", "name": "繁花", "year": "2024"},
            {"site": "muou", "path": "/voddetail/2.html", "name": "繁花", "year": "2024"},
        ]
        vod_id = self.spider._encode_aggregate_vod_id(payload)
        self.assertTrue(vod_id.startswith("agg:"))
        decoded = self.spider._decode_aggregate_vod_id(vod_id)
        self.assertEqual(decoded, payload)

    def test_normalize_title_removes_spaces_punctuation_and_resolution_tags(self):
        self.assertEqual(
            self.spider._normalize_title(" 繁花 4K.HDR-玩偶 "),
            "繁花",
        )

    def test_is_same_title_rejects_year_conflict(self):
        left = {"vod_name": "繁花", "vod_year": "2024"}
        right = {"vod_name": "繁花", "vod_year": "2023"}
        self.assertFalse(self.spider._is_same_title(left, right))

    def test_build_category_url_uses_selected_category_and_filters(self):
        site = {
            "id": "wanou",
            "domains": ["https://www.wogg.net"],
            "category_url": "/vodshow/{categoryId}--------{page}---.html",
            "category_url_with_filters": "/vodshow/{categoryId}-{area}-{by}-{class}-----{page}---{year}.html",
        }
        url = self.spider._build_category_url(
            site,
            "1",
            "2",
            {"categoryId": "1", "area": "香港", "by": "score", "class": "动作", "year": "2025"},
        )
        self.assertEqual(
            url,
            "https://www.wogg.net/vodshow/1-%E9%A6%99%E6%B8%AF-score-%E5%8A%A8%E4%BD%9C-----2---2025.html",
        )

    @patch.object(Spider, "fetch")
    def test_request_with_failover_tries_next_domain_when_first_fails(self, mock_fetch):
        def fake_fetch(url, headers=None, timeout=10):
            if url.startswith("https://bad.example"):
                raise RuntimeError("boom")
            return SimpleNamespace(status_code=200, text="<html><body>ok</body></html>")

        mock_fetch.side_effect = fake_fetch
        site = {"domains": ["https://bad.example", "https://good.example"]}
        html = self.spider._request_with_failover(site, "/vodshow/1--------1---.html")
        self.assertIn("ok", html)
        self.assertEqual(site["domains"][0], "https://good.example")

    def test_parse_cards_extracts_short_site_vod_id_title_cover_and_remarks(self):
        site = {"id": "wanou", "domains": ["https://www.wogg.net"], "list_xpath": "//*[contains(@class,'module-item')]"}
        html = """
        <div class="module-item">
          <div class="module-item-pic">
            <a href="/voddetail/123.html"></a>
            <img data-src="/poster.jpg" alt="示例影片" />
          </div>
          <div class="module-item-text">HD</div>
        </div>
        """
        cards = self.spider._parse_cards(site, html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "site:wanou:/voddetail/123.html",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.wogg.net/poster.jpg",
                    "vod_remarks": "HD",
                    "vod_year": "",
                    "_site": "wanou",
                    "_detail_path": "/voddetail/123.html",
                }
            ],
        )

    @patch.object(Spider, "_request_with_failover")
    def test_category_content_uses_default_category_when_extend_missing(self, mock_request_with_failover):
        mock_request_with_failover.return_value = """
        <div class="module-item">
          <div class="module-item-pic">
            <a href="/voddetail/456.html"></a>
            <img data-src="/cate.jpg" alt="分类影片" />
          </div>
          <div class="module-item-text">更新至10集</div>
        </div>
        """
        result = self.spider.categoryContent("site_wanou", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")

    def test_aggregate_search_results_merges_same_title_and_keeps_highest_priority_source(self):
        raw_results = [
            {
                "vod_id": "site:muou:/voddetail/2.html",
                "vod_name": "繁花",
                "vod_pic": "https://img.example/m.jpg",
                "vod_remarks": "木偶版",
                "vod_year": "2024",
                "_site": "muou",
                "_detail_path": "/voddetail/2.html",
            },
            {
                "vod_id": "site:wanou:/voddetail/1.html",
                "vod_name": "繁花",
                "vod_pic": "https://img.example/w.jpg",
                "vod_remarks": "玩偶版",
                "vod_year": "2024",
                "_site": "wanou",
                "_detail_path": "/voddetail/1.html",
            },
        ]
        aggregated = self.spider._aggregate_search_results(raw_results)
        self.assertEqual(len(aggregated), 1)
        self.assertEqual(aggregated[0]["vod_name"], "繁花")
        self.assertEqual(aggregated[0]["vod_pic"], "https://img.example/w.jpg")
        self.assertEqual(aggregated[0]["vod_remarks"], "玩偶版")
        self.assertTrue(aggregated[0]["vod_id"].startswith("agg:"))

    def test_aggregate_search_results_keeps_year_conflict_as_two_items(self):
        raw_results = [
            {
                "vod_id": "site:wanou:/voddetail/1.html",
                "vod_name": "倚天屠龙记",
                "vod_year": "2019",
                "_site": "wanou",
                "_detail_path": "/voddetail/1.html",
            },
            {
                "vod_id": "site:muou:/voddetail/2.html",
                "vod_name": "倚天屠龙记",
                "vod_year": "2022",
                "_site": "muou",
                "_detail_path": "/voddetail/2.html",
            },
        ]
        aggregated = self.spider._aggregate_search_results(raw_results)
        self.assertEqual(len(aggregated), 2)

    @patch.object(Spider, "_fetch_site_search")
    def test_search_content_queries_sites_and_returns_aggregated_items(self, mock_fetch_site_search):
        mock_fetch_site_search.side_effect = [
            [
                {
                    "vod_id": "site:wanou:/voddetail/1.html",
                    "vod_name": "繁花",
                    "vod_pic": "https://img.example/w.jpg",
                    "vod_remarks": "玩偶版",
                    "vod_year": "2024",
                    "_site": "wanou",
                    "_detail_path": "/voddetail/1.html",
                }
            ],
            [
                {
                    "vod_id": "site:muou:/voddetail/2.html",
                    "vod_name": "繁花",
                    "vod_pic": "https://img.example/m.jpg",
                    "vod_remarks": "木偶版",
                    "vod_year": "2024",
                    "_site": "muou",
                    "_detail_path": "/voddetail/2.html",
                }
            ],
            [],
        ]
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_name"], "繁花")
        self.assertNotIn("pagecount", result)

    def test_parse_detail_page_extracts_meta_and_netdisk_links(self):
        site = {
            "id": "wanou",
            "name": "玩偶",
            "domains": ["https://www.wogg.net"],
            "detail_pan_xpath": "//*[contains(@class,'module-row-info')]//p",
        }
        html = """
        <div class="page-title">示例剧</div>
        <div class="mobile-play"><img class="lazyload" data-src="/poster.jpg" /></div>
        <div class="video-info-itemtitle">导演</div><div><a>导演甲</a></div>
        <div class="video-info-itemtitle">主演</div><div><a>演员甲</a><a>演员乙</a></div>
        <div class="video-info-itemtitle">剧情</div><div><p>一段剧情简介</p></div>
        <div class="module-row-info">
          <p>https://pan.quark.cn/s/q1</p>
          <p>https://pan.baidu.com/s/b1</p>
        </div>
        """
        detail = self.spider._parse_detail_page(site, "/voddetail/123.html", html)
        self.assertEqual(detail["vod_name"], "示例剧")
        self.assertEqual(detail["vod_pic"], "https://www.wogg.net/poster.jpg")
        self.assertEqual(detail["vod_director"], "导演甲")
        self.assertEqual(detail["vod_actor"], "演员甲,演员乙")
        self.assertEqual(detail["pan_urls"], ["https://pan.quark.cn/s/q1", "https://pan.baidu.com/s/b1"])

    @patch.object(Spider, "_fetch_site_detail")
    def test_detail_content_for_aggregate_id_merges_lines_from_multiple_sites(self, mock_fetch_site_detail):
        mock_fetch_site_detail.side_effect = [
            {
                "vod_name": "繁花",
                "vod_pic": "https://img.example/w.jpg",
                "vod_year": "2024",
                "vod_director": "导演甲",
                "vod_actor": "演员甲",
                "vod_content": "玩偶简介",
                "pan_urls": ["https://pan.baidu.com/s/b1", "https://pan.quark.cn/s/q1"],
                "_site_name": "玩偶",
            },
            {
                "vod_name": "繁花",
                "vod_pic": "https://img.example/m.jpg",
                "vod_year": "2024",
                "vod_director": "导演乙",
                "vod_actor": "演员乙",
                "vod_content": "木偶简介",
                "pan_urls": ["https://pan.quark.cn/s/q2", "https://pan.baidu.com/s/b1"],
                "_site_name": "木偶",
            },
        ]
        payload = [
            {"site": "wanou", "path": "/voddetail/1.html", "name": "繁花", "year": "2024"},
            {"site": "muou", "path": "/voddetail/2.html", "name": "繁花", "year": "2024"},
        ]
        result = self.spider.detailContent([self.spider._encode_aggregate_vod_id(payload)])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "繁花")
        self.assertEqual(vod["vod_pic"], "https://img.example/w.jpg")
        self.assertEqual(vod["vod_play_from"], "baidu#玩偶$$$quark#玩偶$$$quark#木偶")
        self.assertEqual(
            vod["vod_play_url"],
            "百度资源$https://pan.baidu.com/s/b1$$$夸克资源$https://pan.quark.cn/s/q1$$$夸克资源$https://pan.quark.cn/s/q2",
        )

    def test_player_content_passthroughs_known_pan_domains(self):
        self.assertEqual(
            self.spider.playerContent("quark#玩偶", "https://pan.quark.cn/s/demo", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.quark.cn/s/demo"},
        )
        self.assertEqual(
            self.spider.playerContent("baidu#玩偶", "https://pan.baidu.com/s/demo", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.baidu.com/s/demo"},
        )

    def test_player_content_rejects_non_pan_url(self):
        self.assertEqual(
            self.spider.playerContent("zxzj", "/vodplay/1-1-1.html", {}),
            {"parse": 0, "playUrl": "", "url": ""},
        )

    @patch.object(Spider, "_request_with_failover")
    def test_fetch_site_search_builds_search_url_and_parses_results(self, mock_request_with_failover):
        mock_request_with_failover.return_value = """
        <div class="module-search-item">
          <div class="video-serial" href="/voddetail/789.html" title="搜索影片"></div>
          <div class="module-item-pic"><img data-src="/search.jpg" alt="搜索影片" /></div>
          <div class="module-item-text">抢先版</div>
        </div>
        """
        site = {
            "id": "wanou",
            "domains": ["https://www.wogg.net"],
            "list_xpath": "//*[contains(@class,'module-item')]",
            "search_xpath": "//*[contains(@class,'module-search-item')]",
            "search_url": "/vodsearch/-------------.html?wd={keyword}&page={page}",
        }
        results = self.spider._fetch_site_search(site, "繁花", 1)
        self.assertEqual(results[0]["vod_id"], "site:wanou:/voddetail/789.html")
        self.assertEqual(results[0]["vod_name"], "搜索影片")

    @patch.object(Spider, "_request_with_failover")
    def test_fetch_site_search_builds_zhizhen_search_url_and_parses_results(self, mock_request_with_failover):
        mock_request_with_failover.return_value = """
        <div class="module-search-item">
          <a class="video-serial" href="/index.php/vod/detail/id/789.html" title="至臻影片">抢先版</a>
          <div class="module-item-pic"><img data-src="/search.jpg" alt="至臻影片" /></div>
        </div>
        """
        site = self.spider._get_site("zhizhen")
        results = self.spider._fetch_site_search(site, "繁花", 1)
        self.assertEqual(
            mock_request_with_failover.call_args.args[1],
            "/index.php/vod/search/page/1/wd/%E7%B9%81%E8%8A%B1.html",
        )
        self.assertEqual(
            results[0],
            {
                "vod_id": "site:zhizhen:/index.php/vod/detail/id/789.html",
                "vod_name": "至臻影片",
                "vod_pic": "http://www.miqk.cc/search.jpg",
                "vod_remarks": "",
                "vod_year": "",
                "_site": "zhizhen",
                "_detail_path": "/index.php/vod/detail/id/789.html",
            },
        )

    @patch.object(Spider, "_request_with_failover")
    def test_fetch_site_search_builds_ouge_search_url_and_parses_results(self, mock_request_with_failover):
        mock_request_with_failover.return_value = """
        <div class="module-search-item">
          <a class="video-serial" href="/index.php/vod/detail/id/789.html" title="欧歌影片">抢先版</a>
          <div class="module-item-pic"><img data-src="/search.jpg" alt="欧歌影片" /></div>
          <div class="module-item-text">抢先版</div>
        </div>
        """
        site = self.spider._get_site("ouge")
        results = self.spider._fetch_site_search(site, "繁花", 1)
        self.assertEqual(
            mock_request_with_failover.call_args.args[1],
            "/index.php/vod/search/page/1/wd/%E7%B9%81%E8%8A%B1.html",
        )
        self.assertEqual(
            results[0],
            {
                "vod_id": "site:ouge:/index.php/vod/detail/id/789.html",
                "vod_name": "欧歌影片",
                "vod_pic": "https://woog.nxog.eu.org/search.jpg",
                "vod_remarks": "抢先版",
                "vod_year": "",
                "_site": "ouge",
                "_detail_path": "/index.php/vod/detail/id/789.html",
            },
        )

    @patch.object(Spider, "_fetch_site_search")
    def test_search_content_skips_site_errors(self, mock_fetch_site_search):
        mock_fetch_site_search.side_effect = [
            RuntimeError("boom"),
            [
                {
                    "vod_id": "site:muou:/voddetail/2.html",
                    "vod_name": "繁花",
                    "vod_pic": "",
                    "vod_remarks": "",
                    "vod_year": "2024",
                    "_site": "muou",
                    "_detail_path": "/voddetail/2.html",
                }
            ],
            [],
            [],
        ]
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["list"][0]["vod_name"], "繁花")

    def test_home_content_does_not_expose_content_first_categories(self):
        content = self.spider.homeContent(False)
        self.assertNotIn("movie", [item["type_id"] for item in content["class"]])

    def test_search_content_returns_empty_list_for_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})

    @patch.object(Spider, "_fetch_site_detail")
    def test_detail_content_for_aggregate_id_merges_zhizhen_pan_lines(self, mock_fetch_site_detail):
        mock_fetch_site_detail.side_effect = [
            {
                "vod_name": "繁花",
                "vod_pic": "https://img.example/w.jpg",
                "vod_year": "2024",
                "vod_director": "导演甲",
                "vod_actor": "演员甲",
                "vod_content": "玩偶简介",
                "pan_urls": ["https://pan.baidu.com/s/b1"],
                "_site_name": "玩偶",
            },
            {
                "vod_name": "繁花",
                "vod_pic": "http://www.miqk.cc/poster.jpg",
                "vod_year": "2024",
                "vod_director": "导演乙",
                "vod_actor": "演员乙",
                "vod_content": "至臻简介",
                "pan_urls": ["https://pan.quark.cn/s/z1", "https://pan.baidu.com/s/b1"],
                "_site_name": "至臻",
            },
        ]
        payload = [
            {"site": "wanou", "path": "/voddetail/1.html", "name": "繁花", "year": "2024"},
            {"site": "zhizhen", "path": "/index.php/vod/detail/id/2.html", "name": "繁花", "year": "2024"},
        ]
        result = self.spider.detailContent([self.spider._encode_aggregate_vod_id(payload)])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "繁花")
        self.assertEqual(vod["vod_play_from"], "baidu#玩偶$$$quark#至臻")
        self.assertEqual(
            vod["vod_play_url"],
            "百度资源$https://pan.baidu.com/s/b1$$$夸克资源$https://pan.quark.cn/s/z1",
        )

    @patch.object(Spider, "_fetch_site_detail")
    def test_detail_content_for_aggregate_id_merges_ouge_pan_lines(self, mock_fetch_site_detail):
        mock_fetch_site_detail.side_effect = [
            {
                "vod_name": "繁花",
                "vod_pic": "https://img.example/w.jpg",
                "vod_year": "2024",
                "vod_director": "导演甲",
                "vod_actor": "演员甲",
                "vod_content": "玩偶简介",
                "pan_urls": ["https://pan.baidu.com/s/b1"],
                "_site_name": "玩偶",
            },
            {
                "vod_name": "繁花",
                "vod_pic": "https://woog.nxog.eu.org/poster.jpg",
                "vod_year": "2024",
                "vod_director": "导演乙",
                "vod_actor": "演员乙",
                "vod_content": "欧歌简介",
                "pan_urls": ["https://pan.quark.cn/s/o1", "https://pan.baidu.com/s/b1"],
                "_site_name": "欧歌",
            },
        ]
        payload = [
            {"site": "wanou", "path": "/voddetail/1.html", "name": "繁花", "year": "2024"},
            {"site": "ouge", "path": "/index.php/vod/detail/id/2.html", "name": "繁花", "year": "2024"},
        ]
        result = self.spider.detailContent([self.spider._encode_aggregate_vod_id(payload)])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "繁花")
        self.assertEqual(vod["vod_play_from"], "baidu#玩偶$$$quark#欧歌")
        self.assertEqual(
            vod["vod_play_url"],
            "百度资源$https://pan.baidu.com/s/b1$$$夸克资源$https://pan.quark.cn/s/o1",
        )

    @patch.object(Spider, "_request_with_failover")
    def test_category_content_builds_zhizhen_category_url(self, mock_request_with_failover):
        mock_request_with_failover.return_value = """
        <div class="module-item">
          <div class="module-item-pic">
            <a href="/index.php/vod/detail/id/456.html"></a>
            <img data-src="/cate.jpg" alt="至臻分类片" />
          </div>
          <div class="module-item-text">HD</div>
        </div>
        """
        result = self.spider.categoryContent("site_zhizhen", "2", False, {"categoryId": "24"})
        self.assertEqual(
            mock_request_with_failover.call_args.args[1],
            "http://www.miqk.cc/index.php/vod/show/id/24/page/2.html",
        )
        self.assertEqual(result["list"][0]["vod_id"], "site:zhizhen:/index.php/vod/detail/id/456.html")

    @patch.object(Spider, "_request_with_failover")
    def test_category_content_builds_ouge_category_url(self, mock_request_with_failover):
        mock_request_with_failover.return_value = """
        <div class="module-item">
          <div class="module-item-pic">
            <a href="/index.php/vod/detail/id/456.html"></a>
            <img data-src="/cate.jpg" alt="欧歌分类片" />
          </div>
          <div class="module-item-text">HD</div>
        </div>
        """
        result = self.spider.categoryContent("site_ouge", "2", False, {"categoryId": "21"})
        self.assertEqual(
            mock_request_with_failover.call_args.args[1],
            "https://woog.nxog.eu.org/index.php/vod/show/id/21/page/2.html",
        )
        self.assertEqual(result["list"][0]["vod_id"], "site:ouge:/index.php/vod/detail/id/456.html")
