import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("libvio_spider", str(ROOT / "libvio.py")).load_module()
Spider = MODULE.Spider


class TestLibVioSpider(unittest.TestCase):
    def setUp(self):
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        class_ids = [item["type_id"] for item in content["class"]]
        self.assertEqual(class_ids, ["index", "movie", "series", "anime", "jpandkr", "euandus"])

    def test_parse_list_cards_extracts_compact_vod_id(self):
        html = """
        <div class="stui-vodlist__box">
          <a class="stui-vodlist__thumb" href="/detail/456.html" title="示例影片" data-original="/cover.jpg"></a>
          <span class="pic-text text-right">更新至10集</span>
        </div>
        """
        cards = self.spider._parse_list_cards(html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "456",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.libvio.la/cover.jpg",
                    "vod_remarks": "更新至10集",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_home_video_content_reuses_list_card_parser(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="stui-vodlist__box">
          <a class="stui-vodlist__thumb" href="/detail/111.html" title="最近更新" data-original="/recent.jpg"></a>
          <span class="pic-text text-right">HD</span>
        </div>
        """
        result = self.spider.homeVideoContent()
        self.assertEqual(result["list"][0]["vod_id"], "111")
        self.assertEqual(result["list"][0]["vod_name"], "最近更新")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="stui-vodlist__box">
          <a class="stui-vodlist__thumb" href="/detail/222.html" title="分类影片" data-original="/cate.jpg"></a>
          <span class="pic-text text-right">完结</span>
        </div>
        """
        result = self.spider.categoryContent("movie", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_id"], "222")

    @patch.object(Spider, "_request_html")
    def test_search_content_reuses_card_parser(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="stui-vodlist__box">
          <a class="stui-vodlist__thumb" href="/detail/333.html" title="搜索影片" data-original="/search.jpg"></a>
          <span class="pic-text text-right">抢先版</span>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(result["list"][0]["vod_id"], "333")
        self.assertEqual(result["list"][0]["vod_name"], "搜索影片")

    def test_parse_detail_page_extracts_fields_and_preserves_pan_sources(self):
        html = """
        <div class="stui-content__thumb">
          <img data-original="/poster.jpg" />
        </div>
        <div class="stui-content__detail">
          <h1 class="title">示例剧</h1>
          <p><span class="text-muted">类型：</span><a>剧情</a></p>
          <p><span class="text-muted">地区：</span><a>大陆</a></p>
          <p><span class="text-muted">年份：</span><a>2026</a></p>
          <p><span class="text-muted">导演：</span><a>张三</a></p>
          <p><span class="text-muted">主演：</span><a>李四</a><a>王五</a></p>
          <p><span class="text-muted">简介：</span>一段剧情简介</p>
        </div>
        <h3 class="title">在线播放</h3>
        <ul class="stui-content__playlist clearfix">
          <li><a href="/play/999-1-1.html">第1集</a></li>
          <li><a href="/play/999-1-2.html">第2集</a></li>
        </ul>
        <h3 class="title">夸克资源</h3>
        <ul class="stui-content__playlist clearfix">
          <li><a href="/play/pan-1.html">网盘</a></li>
        </ul>
        <div class="playlist-panel netdisk-panel">
          <div class="panel-head netdisk-head">
            <div class="netdisk-head-inner">
              <h3>视频下载(UC)</h3>
            </div>
          </div>
          <div class="netdisk-list">
            <a class="netdisk-item" href="https://drive.uc.cn/s/e1532998c2bf4?public=1" target="_blank">
              <span class="netdisk-name">合集</span>
              <span class="netdisk-url">https://drive.uc.cn/s/e1532998c2bf4?public=1</span>
            </a>
          </div>
        </div>
        """
        result = self.spider._parse_detail_page(html, "999")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "999")
        self.assertEqual(vod["path"], "https://www.libvio.la/detail/999.html")
        self.assertEqual(vod["vod_name"], "示例剧")
        self.assertEqual(vod["type_name"], "剧情")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_year"], "2026")
        self.assertEqual(vod["vod_director"], "张三")
        self.assertEqual(vod["vod_actor"], "李四,王五")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "LibVIO$$$UC")
        self.assertEqual(
            vod["vod_play_url"],
            "第1集$999-1-1#第2集$999-1-2$$$合集$https://drive.uc.cn/s/e1532998c2bf4?public=1",
        )

    def test_extract_netdisk_sources_deduplicates_same_link(self):
        html = """
        <div class="playlist-panel netdisk-panel">
          <div class="panel-head netdisk-head">
            <div class="netdisk-head-inner">
              <h3>视频下载(UC)</h3>
            </div>
          </div>
          <div class="netdisk-list">
            <a class="netdisk-item" href="https://drive.uc.cn/s/e1532998c2bf4?public=1" target="_blank">
              <span class="netdisk-name">合集</span>
              <span class="netdisk-url">https://drive.uc.cn/s/e1532998c2bf4?public=1</span>
            </a>
            <a class="netdisk-item" href="https://drive.uc.cn/s/e1532998c2bf4?public=1" target="_blank">
              <span class="netdisk-name">一键复制</span>
              <span class="netdisk-url">https://drive.uc.cn/s/e1532998c2bf4?public=1</span>
            </a>
          </div>
        </div>
        """
        self.assertEqual(
            self.spider._extract_netdisk_sources(html),
            [{"from": "UC", "urls": "合集$https://drive.uc.cn/s/e1532998c2bf4?public=1"}],
        )

    @patch.object(Spider, "_request_html")
    def test_detail_content_builds_detail_request_url_from_vod_id(self, mock_request_html):
        mock_request_html.return_value = """
        <h1 class="title">详情影片</h1>
        <ul class="stui-content__playlist">
          <li><a href="/play/123-1-1.html">第1集</a></li>
        </ul>
        """
        result = self.spider.detailContent(["123"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.libvio.la/detail/123.html")
        self.assertEqual(result["list"][0]["vod_id"], "123")

    def test_extract_player_config_reads_json_assignment(self):
        html = '<script>var player_aaaa={"url":"abc","from":"line","id":"1","nid":"2"};</script>'
        data = self.spider._parse_player_config(html)
        self.assertEqual(data["from"], "line")

    def test_extract_play_api_base_reads_player_js(self):
        body = 'var player={}; src="/player/api.php?url=";'
        self.assertEqual(self.spider._extract_play_api_base(body), "https://www.libvio.la/player/api.php?url=")

    @patch.object(Spider, "_request_html")
    def test_player_content_resolves_direct_api_url(self, mock_request_html):
        mock_request_html.side_effect = [
            '<script>var player_x={"url":"https://up.example/id","from":"line","id":"11","nid":"22","link_next":"next"};</script>',
            'src="/player/api.php?url="',
            'var urls="https://video.example/final.m3u8";',
        ]
        result = self.spider.playerContent("LibVIO", "999-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/final.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://www.libvio.la/")

    @patch.object(Spider, "_request_html")
    def test_player_content_returns_empty_for_pan_source(self, mock_request_html):
        mock_request_html.return_value = '<script>var player_x={"url":"abc","from":"kuake"};</script>'
        self.assertEqual(self.spider.playerContent("LibVIO", "999-1-1", {}), {"parse": 0, "playUrl": "", "url": ""})

    def test_player_content_returns_direct_netdisk_link(self):
        result = self.spider.playerContent("UC", "https://drive.uc.cn/s/e1532998c2bf4?public=1", {})
        self.assertEqual(
            result,
            {
                "parse": 0,
                "playUrl": "",
                "url": "https://drive.uc.cn/s/e1532998c2bf4?public=1",
            },
        )


if __name__ == "__main__":
    unittest.main()
