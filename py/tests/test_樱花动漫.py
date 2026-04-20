import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("yinghua_spider", str(ROOT / "樱花动漫.py")).load_module()
Spider = MODULE.Spider


SAMPLE_DETAIL_HTML = """
<html><body>
<div class="detail"><h2>进击的巨人</h2></div>
<div class="cover"><img data-original="https://pic.example.com/zr.jpg" /></div>
<div class="item"><span>状态:</span><em>已完结</em></div>
<div class="item"><span>年份:</span>2023</div>
<div class="item"><span>地区:</span>日本</div>
<div class="item"><span>类型:</span>热血</div>
<div class="item"><span>主演:</span>梶裕贵</div>
<li class="blurb"><span>简介</span>讲述巨人的故事</li>
<div class="module-tab-item">高清</div>
<div class="module-tab-item">ikun</div>
<div class="module-play-list">
  <a href="/play/12345-1-1/">第01集</a>
  <a href="/play/12345-1-2/">第02集</a>
  <a href="/play/12345-1-3/">第03集</a>
</div>
<div class="module-play-list">
  <a href="/play/12345-2-1/">第01集</a>
  <a href="/play/12345-2-2/">第02集</a>
</div>
</body></html>
"""

SAMPLE_LIST_HTML = """
<html><body>
<ul>
<li><a href="/detail/123/" title="进击的巨人"><img data-original="https://pic/1.jpg" /></a><p>已完结</p></li>
<li><a href="/detail/456/" title="鬼灭之刃"><img data-original="https://pic/2.jpg" /></a><p>更新中</p></li>
<li><a href="/other/" title="忽略项"></a></li>
</ul>
</body></html>
"""

SAMPLE_SEARCH_HTML = """
<html><body>
找到 <em>5</em> 条结果
<ul>
<li><a class="cover" href="/detail/123/" title="进击的巨人" data-original="https://pic/1.jpg">
<div class="item"><span>状态:</span>已完结</div>
</a></li>
<li><a class="cover" href="/detail/456/" title="鬼灭之刃" data-original="https://pic/2.jpg">
<div class="item"><span>状态:</span>更新中</div>
</a></li>
</ul>
</body></html>
"""

SAMPLE_PLAY_HTML = """
<html><body>
<script>
var art = new Artplayer({
  url: 'https://cdn.example.com/video/12345.m3u8?key=abc',
});
</script>
</body></html>
"""

SAMPLE_CATEGORY_HTML = """
<html><body>
<ul>
<li><a href="/detail/123/" title="进击的巨人"><img data-original="https://pic/1.jpg" /></a><p>已完结</p></li>
</ul>
<div class="pagination">
  <a href="/type/riman/3/">3</a>
  <a href="/type/riman/5/">5</a>
</div>
</body></html>
"""


class TestYingHuaSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_classes(self):
        content = self.spider.homeContent(False)
        ids = [c["type_id"] for c in content["class"]]
        self.assertEqual(len(content["class"]), 4)
        self.assertIn("guoman", ids)
        self.assertIn("riman", ids)
        self.assertIn("oman", ids)
        self.assertIn("dmfilm", ids)

    def test_get_name(self):
        self.assertEqual(self.spider.getName(), "樱花动漫")

    @patch.object(Spider, "_get_html")
    def test_home_video_content(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        result = self.spider.homeVideoContent()
        self.assertEqual(len(result["list"]), 2)
        self.assertEqual(result["list"][0]["vod_name"], "进击的巨人")
        self.assertEqual(result["list"][0]["vod_remarks"], "已完结")
        self.assertEqual(result["list"][1]["vod_name"], "鬼灭之刃")

    @patch.object(Spider, "_get_html")
    def test_home_video_dedup(self, mock_html):
        mock_html.return_value = """
        <ul>
        <li><a href="/detail/123/" title="A"><img src="p.jpg" /></a></li>
        <li><a href="/detail/123/" title="A"><img src="p.jpg" /></a></li>
        </ul>
        """
        result = self.spider.homeVideoContent()
        self.assertEqual(len(result["list"]), 1)

    @patch.object(Spider, "_get_html")
    def test_category_content(self, mock_html):
        mock_html.return_value = SAMPLE_CATEGORY_HTML
        result = self.spider.categoryContent("riman", "1", False, {})
        self.assertEqual(len(result["list"]), 1)
        self.assertEqual(result["list"][0]["vod_name"], "进击的巨人")
        self.assertEqual(result["pagecount"], 5)

    @patch.object(Spider, "_get_html")
    def test_category_page2_url(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        self.spider.categoryContent("riman", "2", False, {})
        mock_html.assert_called_with("https://www.dmvvv.com/type/riman/2/")

    @patch.object(Spider, "_get_html")
    def test_detail_content(self, mock_html):
        mock_html.return_value = SAMPLE_DETAIL_HTML
        result = self.spider.detailContent(["/detail/12345/"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "进击的巨人")
        self.assertEqual(vod["vod_pic"], "https://pic.example.com/zr.jpg")
        self.assertEqual(vod["vod_remarks"], "已完结")
        self.assertEqual(vod["vod_year"], "2023")
        self.assertEqual(vod["vod_area"], "日本")
        self.assertEqual(vod["vod_content"], "讲述巨人的故事")
        self.assertIn("高清", vod["vod_play_from"])
        self.assertIn("ikun", vod["vod_play_from"])
        self.assertIn("第01集$/play/12345-1-1/", vod["vod_play_url"])
        self.assertIn("第02集$/play/12345-1-2/", vod["vod_play_url"])

    @patch.object(Spider, "_get_html")
    def test_detail_multi_source_grouping(self, mock_html):
        mock_html.return_value = SAMPLE_DETAIL_HTML
        result = self.spider.detailContent(["/detail/12345/"])
        vod = result["list"][0]
        from_list = vod["vod_play_from"].split("$$$")
        url_groups = vod["vod_play_url"].split("$$$")
        self.assertEqual(len(from_list), 2)
        self.assertEqual(len(url_groups), 2)
        # 高清 source (sourceIdx=1)
        self.assertEqual(from_list[0], "高清")
        self.assertIn("第01集$/play/12345-1-1/", url_groups[0])
        self.assertIn("第03集$/play/12345-1-3/", url_groups[0])
        # ikun source (sourceIdx=2)
        self.assertEqual(from_list[1], "ikun")
        self.assertIn("第01集$/play/12345-2-1/", url_groups[1])
        self.assertIn("第02集$/play/12345-2-2/", url_groups[1])
        # ensure no cross-contamination
        self.assertNotIn("12345-2-", url_groups[0])
        self.assertNotIn("12345-1-", url_groups[1])

    @patch.object(Spider, "_get_html")
    def test_detail_title_from_title_tag(self, mock_html):
        mock_html.return_value = "<html><body><title>鬼灭之刃 - 樱花动漫</title></body></html>"
        result = self.spider.detailContent(["/detail/999/"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "鬼灭之刃")

    @patch.object(Spider, "_get_html")
    def test_detail_no_episodes(self, mock_html):
        mock_html.return_value = """
        <html><body>
        <div class="detail"><h2>测试</h2></div>
        </body></html>
        """
        result = self.spider.detailContent(["/detail/1/"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_play_from"], "default")
        self.assertEqual(vod["vod_play_url"], "")

    @patch.object(Spider, "_get_html")
    def test_search_content(self, mock_html):
        mock_html.return_value = SAMPLE_SEARCH_HTML
        result = self.spider.searchContent("巨人", False, "1")
        self.assertEqual(len(result["list"]), 2)
        self.assertEqual(result["list"][0]["vod_name"], "进击的巨人")
        self.assertEqual(result["pagecount"], 1)

    def test_search_empty_keyword(self):
        result = self.spider.searchContent("", False, "1")
        self.assertEqual(result["list"], [])

    @patch.object(Spider, "_get_html")
    def test_search_quick_mode(self, mock_html):
        mock_html.return_value = SAMPLE_SEARCH_HTML
        result = self.spider.searchContent("巨人", True, "1")
        self.assertEqual(len(result["list"]), 2)

    @patch.object(Spider, "_get_html")
    def test_player_content_artplayer(self, mock_html):
        mock_html.return_value = SAMPLE_PLAY_HTML
        result = self.spider.playerContent("高清", "/play/12345-1-1/", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://cdn.example.com/video/12345.m3u8?key=abc")
        self.assertIn("Referer", result["header"])

    @patch.object(Spider, "_get_html")
    def test_player_content_m3u8_fallback(self, mock_html):
        mock_html.return_value = '<html><script>var src = "https://cdn.example.com/stream.m3u8";</script></html>'
        result = self.spider.playerContent("高清", "/play/12345-1-1/", {})
        self.assertEqual(result["url"], "https://cdn.example.com/stream.m3u8")

    @patch.object(Spider, "_get_html")
    def test_player_content_no_match(self, mock_html):
        mock_html.return_value = "<html><body>no video</body></html>"
        result = self.spider.playerContent("高清", "/play/12345-1-1/", {})
        self.assertEqual(result["url"], "https://www.dmvvv.com/play/12345-1-1/")

    @patch.object(Spider, "_get_html")
    def test_detail_full_url(self, mock_html):
        mock_html.return_value = SAMPLE_DETAIL_HTML
        self.spider.detailContent(["https://www.dmvvv.com/detail/12345/"])
        mock_html.assert_called_with("https://www.dmvvv.com/detail/12345/")


if __name__ == "__main__":
    unittest.main()
