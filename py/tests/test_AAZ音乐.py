import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("aaz_music_spider", str(ROOT / "AAZ音乐.py")).load_module()
Spider = MODULE.Spider


HOME_HTML = """
<html><body>
  <ul>
    <li>
      <div class="name"><a href="/m/1001.html" title="晴天">晴天</a></div>
      <div class="mv"><a href="/v/mv1001">MV</a></div>
    </li>
    <li>
      <div class="name"><a href="/m/1002.html" title="七里香">七里香</a></div>
    </li>
  </ul>
</body></html>
"""

SINGER_HTML = """
<html><body>
  <li>
    <div class="pic"><img src="/img/singer.jpg"></div>
    <div class="name"><a href="/s/jay" title="周杰伦">周杰伦</a></div>
  </li>
</body></html>
"""

PLAYLIST_HTML = """
<html><body>
  <li>
    <div class="pic"><img src="/img/playlist.jpg"></div>
    <div class="name"><a href="/p/top100" title="华语热歌">华语热歌</a></div>
  </li>
</body></html>
"""

ALBUM_HTML = """
<html><body>
  <li>
    <div class="pic"><img src="/img/album.jpg"></div>
    <div class="name"><a href="/a/fantasy" title="范特西">范特西</a></div>
  </li>
</body></html>
"""

MV_HTML = """
<html><body>
  <li>
    <div class="pic"><img src="/img/mv.jpg"></div>
    <div class="name"><a href="/v/qingtianmv" title="晴天MV">晴天MV</a></div>
  </li>
</body></html>
"""


class TestAAZMusicSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    @patch.object(Spider, "fetch")
    def test_home_content_returns_fixed_classes_and_song_cards(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(status_code=200, text=HOME_HTML)
        result = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in result["class"]],
            ["new", "top", "singer", "playtype", "album", "mv"],
        )
        self.assertEqual([item["vod_id"] for item in result["list"]], ["song:1001", "song:1002"])
        self.assertEqual(result["list"][0]["vod_name"], "晴天")
        self.assertEqual(result["list"][0]["vod_remarks"], "高清MV")

    @patch.object(Spider, "fetch")
    def test_home_video_content_reuses_home_list(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(status_code=200, text=HOME_HTML)
        result = self.spider.homeVideoContent()
        self.assertEqual([item["vod_id"] for item in result["list"]], ["song:1001", "song:1002"])

    @patch.object(Spider, "fetch")
    def test_category_content_maps_song_and_folder_types(self, mock_fetch):
        mock_fetch.side_effect = [
            SimpleNamespace(status_code=200, text=HOME_HTML),
            SimpleNamespace(status_code=200, text=HOME_HTML),
            SimpleNamespace(status_code=200, text=SINGER_HTML),
            SimpleNamespace(status_code=200, text=PLAYLIST_HTML),
            SimpleNamespace(status_code=200, text=ALBUM_HTML),
            SimpleNamespace(status_code=200, text=MV_HTML),
        ]
        self.assertEqual(self.spider.categoryContent("new", "1", False, {})["list"][0]["vod_id"], "song:1001")
        self.assertEqual(self.spider.categoryContent("top", "1", False, {})["list"][1]["vod_id"], "song:1002")
        self.assertEqual(self.spider.categoryContent("singer", "1", False, {})["list"][0]["vod_id"], "singer:jay")
        self.assertEqual(self.spider.categoryContent("playtype", "1", False, {})["list"][0]["vod_id"], "playlist:top100")
        self.assertEqual(self.spider.categoryContent("album", "1", False, {})["list"][0]["vod_id"], "album:fantasy")
        self.assertEqual(self.spider.categoryContent("mv", "1", False, {})["list"][0]["vod_id"], "mv:qingtianmv")

    def test_category_content_returns_empty_for_unknown_type(self):
        self.assertEqual(
            self.spider.categoryContent("bad", "1", False, {}),
            {"page": 1, "limit": 0, "total": 0, "list": []},
        )


if __name__ == "__main__":
    unittest.main()
