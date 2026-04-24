import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("sjmusic_spider", str(ROOT / "世纪音乐.py")).load_module()
Spider = MODULE.Spider


HOME_HTML = """
<html>
  <body>
    <ul id="datalist">
      <li>
        <div class="name"><a class="url" href="/mp3/123.html">夜曲</a></div>
        <div class="singer">周杰伦</div>
        <div class="pic"><img src="/img/song.jpg"></div>
      </li>
    </ul>
    <ul class="video_list">
      <li>
        <div class="name"><a href="/mp4/456.html">稻香MV</a></div>
        <div class="pic"><img src="/img/mv.jpg"></div>
      </li>
    </ul>
  </body>
</html>
"""


class TestSJMusicSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    @patch.object(Spider, "fetch")
    def test_home_content_returns_classes_filters_and_home_items(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(status_code=200, text=HOME_HTML)
        result = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in result["class"]],
            ["home", "rank_list", "playlist", "singer", "mv"],
        )
        self.assertIn("singer", result["filters"])
        self.assertEqual(result["list"][0]["vod_id"], "song:123")
        self.assertEqual(result["list"][0]["vod_name"], "周杰伦 - 夜曲")
        self.assertEqual(result["list"][1]["vod_id"], "mv:456")

    @patch.object(Spider, "fetch")
    def test_home_video_content_reuses_home_list(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(status_code=200, text=HOME_HTML)
        result = self.spider.homeVideoContent()
        self.assertEqual([item["vod_id"] for item in result["list"]], ["song:123", "mv:456"])


if __name__ == "__main__":
    unittest.main()
