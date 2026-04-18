import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("youknow_spider", str(ROOT / "youknow.py")).load_module()
Spider = MODULE.Spider


class TestYouKnowSpider(unittest.TestCase):
    def setUp(self):
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        class_ids = [item["type_id"] for item in content["class"]]
        self.assertEqual(class_ids, ["index", "drama", "movie", "variety", "anime", "short", "doc"])

    def test_parse_list_cards_extracts_compact_vod_id(self):
        html = """
        <a class="module-poster-item" href="/d/1234/" title="示例影片" data-original="/cover.jpg">
          <div class="module-item-note">更新至10集</div>
        </a>
        """
        cards = self.spider._parse_list_cards(html)
        self.assertEqual(
            cards,
            [
                {
                    "vod_id": "1234",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.youknow.tv/cover.jpg",
                    "vod_remarks": "更新至10集",
                }
            ],
        )

    def test_parse_list_cards_prefers_nested_lazyload_original_over_placeholder_src(self):
        html = """
        <a class="module-poster-item" href="/d/5678/" title="一念梦离">
          <div class="module-item-pic">
            <img
              class="lazy lazyload"
              data-original="/upload/vod/20260409-1/f1d0233129bc59adb6d2e8fa6396e681.jpg"
              alt="一念梦离"
              src="/upload/mxprocms/20230815-1/8a218aed43eb11efa5a045d21a46d601.webp"
            />
          </div>
          <div class="module-item-note">更新中</div>
        </a>
        """
        cards = self.spider._parse_list_cards(html)
        self.assertEqual(cards[0]["vod_pic"], "https://www.youknow.tv/upload/vod/20260409-1/f1d0233129bc59adb6d2e8fa6396e681.jpg")

    @patch.object(Spider, "_request_html")
    def test_home_video_content_uses_today_updates_page(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item" href="/d/111/" title="今日更新" data-original="/recent.jpg">
          <div class="module-item-note">HD</div>
        </a>
        """
        result = self.spider.homeVideoContent()
        self.assertEqual(result["list"][0]["vod_id"], "111")
        self.assertEqual(result["list"][0]["vod_name"], "今日更新")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item" href="/d/222/" title="分类影片" data-original="/cate.jpg">
          <div class="module-item-note">完结</div>
        </a>
        """
        result = self.spider.categoryContent("movie", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(mock_request_html.call_args.args[0], "/show/2--------2---/")
        self.assertEqual(result["list"][0]["vod_id"], "222")

    @patch.object(Spider, "_request_html")
    def test_category_content_uses_page1_path_without_page_number(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item" href="/d/555/" title="分类第一页" data-original="/page1.jpg">
          <div class="module-item-note">HD</div>
        </a>
        """
        result = self.spider.categoryContent("movie", "1", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "/show/2-----------/")
        self.assertEqual(result["list"][0]["vod_id"], "555")

    @patch.object(Spider, "_request_html")
    def test_search_content_reuses_card_parser(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item" href="/d/333/" title="搜索影片" data-original="/search.jpg">
          <div class="module-item-note">抢先版</div>
        </a>
        """
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(result["list"][0]["vod_id"], "333")
        self.assertEqual(result["list"][0]["vod_name"], "搜索影片")

    def test_parse_detail_page_extracts_fields_and_aligns_episode_sources(self):
        html = """
        <div class="module-info-poster">
          <img data-original="/poster.jpg" />
        </div>
        <div class="module-info-heading">
          <h1>示例剧</h1>
        </div>
        <div class="module-info-content">
          <div><span>类型：</span><a>剧情</a></div>
          <div><span>地区：</span><a>大陆</a></div>
          <div><span>年份：</span><a>2026</a></div>
          <div><span>导演：</span><a>张三</a></div>
          <div><span>主演：</span><a>李四</a><a>王五</a></div>
          <div><span>语言：</span><a>国语</a></div>
          <div><span>备注：</span><span>更新至2集</span></div>
          <div><span>简介：</span><p>一段剧情简介</p></div>
        </div>
        <div data-dropdown-value="线路A"></div>
        <div data-dropdown-value="线路B"></div>
        <div class="module-play-list">
          <a href="/p/888-1-1/">第1集</a>
          <a href="/p/888-1-2/">第2集</a>
        </div>
        <div class="module-play-list">
          <a href="/p/888-2-1/">第1集</a>
          <a href="/p/888-2-2/">第2集</a>
        </div>
        """
        result = self.spider._parse_detail_page(html, "888")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "888")
        self.assertEqual(vod["path"], "https://www.youknow.tv/d/888/")
        self.assertEqual(vod["vod_name"], "示例剧")
        self.assertEqual(vod["type_name"], "剧情")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_year"], "2026")
        self.assertEqual(vod["vod_lang"], "国语")
        self.assertEqual(vod["vod_remarks"], "更新至2集")
        self.assertEqual(vod["vod_director"], "张三")
        self.assertEqual(vod["vod_actor"], "李四,王五")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "YouKnowTV")
        first_episode = vod["vod_play_url"].split("#")[0]
        self.assertTrue(first_episode.startswith("第1集$"))
        payload = self.spider._decode_episode_payload(first_episode.split("$", 1)[1])
        self.assertEqual(payload["vod_id"], "888")
        self.assertEqual(payload["episode_index"], 1)
        self.assertEqual(len(payload["candidates"]), 2)

    @patch.object(Spider, "_request_html")
    def test_detail_content_builds_detail_request_url_from_vod_id(self, mock_request_html):
        mock_request_html.return_value = '<h1>详情影片</h1><div class="module-play-list"><a href="/p/123-1-1/">第1集</a></div>'
        result = self.spider.detailContent(["123"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.youknow.tv/d/123/")
        self.assertEqual(result["list"][0]["vod_id"], "123")

    def test_extract_player_config_reads_player_aaaa(self):
        html = '<script>var player_aaaa={"url":"https%3A%2F%2Fcdn.example%2Fa.m3u8","encrypt":"1"};</script>'
        data = self.spider._parse_player_config(html)
        self.assertEqual(data["encrypt"], "1")

    def test_extract_player_config_supports_nested_object_literal(self):
        html = """
        <script>
        var player_aaaa={
          "flag":"play",
          "encrypt":2,
          "vod_data":{"vod_name":"示例影片","vod_actor":"甲,乙"},
          "url":"JTY4JTc0JTc0JTcwJTczJTNBJTJGJTJGJTc2JTY5JTc0JTY0JTJFJTYzJTY0JTZFJTJFJTY1JTc4JTYxJTZEJTcwJTZDJTY1JTJGJTYxJTJGJTY5JTZFJTY0JTY1JTc4JTJFJTZEJTMzJTc1JTM4"
        };
        </script>
        """
        data = self.spider._parse_player_config(html)
        self.assertEqual(data["encrypt"], 2)
        self.assertEqual(data["vod_data"]["vod_name"], "示例影片")

    def test_decode_player_url_supports_encrypt_1_and_2(self):
        self.assertEqual(
            self.spider._decode_player_url("https%3A%2F%2Fvideo.example%2Fa.m3u8", "1"),
            "https://video.example/a.m3u8",
        )
        encoded = "aHR0cHMlM0ElMkYlMkZ2aWRlby5leGFtcGxlJTJGYi5tM3U4"
        self.assertEqual(
            self.spider._decode_player_url(encoded, "2"),
            "https://video.example/b.m3u8",
        )

    @patch.object(Spider, "_request_html")
    def test_player_content_collects_candidates_from_page_and_iframe(self, mock_request_html):
        payload = self.spider._encode_episode_payload(
            {
                "vod_id": "888",
                "episode_index": 1,
                "title": "第1集",
                "candidates": [
                    {"source": "线路A", "source_id": "1", "episode_url": "https://www.youknow.tv/p/888-1-1/"}
                ],
            }
        )
        mock_request_html.side_effect = [
            '<script>var player_aaaa={"url":"https%3A%2F%2Fvideo.example%2Fpage.m3u8","encrypt":"1"};</script><iframe class="embed-responsive-item" src="/embed/player.html?url=https%3A%2F%2Fvideo.example%2Fiframe.m3u8"></iframe>',
            '<html><body>https://video.example/iframe-final.m3u8</body></html>',
        ]
        result = self.spider.playerContent("YouKnowTV", payload, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/page.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://www.youknow.tv/")

    @patch.object(Spider, "_request_html")
    def test_player_content_handles_nested_real_world_player_config(self, mock_request_html):
        payload = self.spider._encode_episode_payload(
            {
                "vod_id": "202774",
                "episode_index": 1,
                "title": "HD中字",
                "candidates": [
                    {"source": "线路1", "source_id": "1", "episode_url": "https://www.youknow.tv/p/202774-1-1/"}
                ],
            }
        )
        mock_request_html.return_value = """
        <script>
        var player_aaaa={"flag":"play","encrypt":2,"vod_data":{"vod_name":"机动战士高达闪光的哈萨维"},"url":"JTY4JTc0JTc0JTcwJTczJTNBJTJGJTJGJTc2JTY5JTcwJTJFJTY0JTc5JTc0JTc0JTJEJTZFJTY1JTc0JTc3JTZGJTcyJTZCJTJFJTYzJTZGJTZEJTJGJTMyJTMwJTMyJTM2JTMwJTMzJTMyJTM1JTJGJTMyJTMxJTMzJTMzJTM0JTVGJTMxJTM4JTM4JTM1JTM2JTYyJTM0JTM3JTJGJTY5JTZFJTY0JTY1JTc4JTJFJTZEJTMzJTc1JTM4"};
        </script>
        <iframe src="/template/mxpro/html/vod/adsterra_iframe.html"></iframe>
        """
        result = self.spider.playerContent("YouKnowTV", payload, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://vip.dytt-network.com/20260325/21334_18856b47/index.m3u8")

    @patch.object(Spider, "_request_html")
    def test_player_content_tries_next_candidate_when_first_fails(self, mock_request_html):
        payload = self.spider._encode_episode_payload(
            {
                "vod_id": "888",
                "episode_index": 1,
                "title": "第1集",
                "candidates": [
                    {"source": "线路A", "source_id": "1", "episode_url": "https://www.youknow.tv/p/888-1-1/"},
                    {"source": "线路B", "source_id": "2", "episode_url": "https://www.youknow.tv/p/888-2-1/"},
                ],
            }
        )
        mock_request_html.side_effect = [
            "<html><body>empty</body></html>",
            "<html><body>https://video.example/backup.m3u8</body></html>",
        ]
        result = self.spider.playerContent("YouKnowTV", payload, {})
        self.assertEqual(result["url"], "https://video.example/backup.m3u8")


if __name__ == "__main__":
    unittest.main()
