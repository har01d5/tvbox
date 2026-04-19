# 剧圈圈 Spider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `剧圈圈.py` 与 `tests/test_剧圈圈.py`，实现首页、分类、详情、搜索和播放解析，并统一使用压缩后的站内 id。

**Architecture:** 沿用当前仓库“单站点单文件 + 单测”的 Spider 结构，在站点文件内部封装文本清洗、短 id 编解码、列表/详情解析和播放解码 helper。播放逻辑优先从播放页直接解出媒体直链，失败时再请求站内解析接口，并在异常场景回退到播放页。

**Tech Stack:** Python 3、`base.spider.Spider`、`self.fetch`、lxml/XPath、regex、`json`、`hashlib`、`base64`、`urllib.parse`

---

## File Structure

- Create: `剧圈圈.py`
  - 新 Spider 实现，包含站点配置、id 编解码、列表/详情/搜索/播放解析
- Create: `tests/test_剧圈圈.py`
  - 覆盖首页、分类、搜索、详情、多线路播放与回退逻辑
- Reference: `剧迷.py`
  - 参考同仓库现有 Spider 的接口组织方式
- Reference: `tests/test_剧迷.py`
  - 参考同仓库 unittest 风格与 mock 方式

### Task 1: Scaffold Spider And Core Helpers

**Files:**
- Create: `剧圈圈.py`
- Test: `tests/test_剧圈圈.py`

- [ ] **Step 1: Write the failing tests for name, categories, id helpers, and search-id compression**

```python
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("juquanquan_spider", str(ROOT / "剧圈圈.py")).load_module()
Spider = MODULE.Spider


class TestJuQuanQuanSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["dianying", "juji", "dongman", "zongyi", "duanju"],
        )

    def test_encode_and_decode_detail_and_play_ids(self):
        self.assertEqual(self.spider._encode_vod_id("/vod/123.html"), "vod/123")
        self.assertEqual(self.spider._decode_vod_id("vod/123"), "https://www.jqqzx.cc/vod/123.html")
        self.assertEqual(self.spider._encode_play_id("/play/123-1-2.html"), "play/123-1-2")
        self.assertEqual(self.spider._decode_play_id("play/123-1-2"), "https://www.jqqzx.cc/play/123-1-2.html")

    def test_parse_search_list_maps_items_to_compact_vod_ids(self):
        payload = '{"list":[{"id":"888","name":"搜索影片","pic":"https://img.example/888.jpg"}]}'
        self.assertEqual(
            self.spider._parse_search_list(payload),
            [
                {
                    "vod_id": "vod/888",
                    "vod_name": "搜索影片",
                    "vod_pic": "https://img.example/888.jpg",
                    "vod_remarks": "",
                }
            ],
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_home_content_exposes_expected_categories tests.test_剧圈圈.TestJuQuanQuanSpider.test_encode_and_decode_detail_and_play_ids tests.test_剧圈圈.TestJuQuanQuanSpider.test_parse_search_list_maps_items_to_compact_vod_ids -v`

Expected: `FAIL` or `ERROR` because `剧圈圈.py` and helper methods do not exist yet.

- [ ] **Step 3: Write the minimal Spider skeleton and helper implementation**

```python
# coding=utf-8
import json
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "剧圈圈"
        self.host = "https://www.jqqzx.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "dianying", "type_name": "电影"},
            {"type_id": "juji", "type_name": "剧集"},
            {"type_id": "dongman", "type_name": "动漫"},
            {"type_id": "zongyi", "type_name": "综艺"},
            {"type_id": "duanju", "type_name": "短剧"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _encode_vod_id(self, href):
        matched = re.search(r"/vod/([^/?#]+)\.html", self._build_url(href))
        return f"vod/{matched.group(1)}" if matched else ""

    def _decode_vod_id(self, vod_id):
        matched = re.search(r"^vod/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/vod/{matched.group(1)}.html") if matched else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/play/([^/?#]+)\.html", self._build_url(href))
        return f"play/{matched.group(1)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^play/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/play/{matched.group(1)}.html") if matched else ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(text or ""))).strip()

    def _parse_search_list(self, payload):
        try:
            data = json.loads(str(payload or "{}"))
        except Exception:
            return []
        items = []
        for item in data.get("list", []):
            vod_id = f"vod/{item.get('id')}".rstrip("/")
            if vod_id == "vod/" or not self._clean_text(item.get("name")):
                continue
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text(item.get("name")),
                    "vod_pic": self._build_url(item.get("pic")),
                    "vod_remarks": "",
                }
            )
        return items
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_home_content_exposes_expected_categories tests.test_剧圈圈.TestJuQuanQuanSpider.test_encode_and_decode_detail_and_play_ids tests.test_剧圈圈.TestJuQuanQuanSpider.test_parse_search_list_maps_items_to_compact_vod_ids -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add 剧圈圈.py tests/test_剧圈圈.py
git commit -m "feat: scaffold juquanquan spider"
```

### Task 2: Implement Home, Category, Search, And Shared Card Parsing

**Files:**
- Modify: `剧圈圈.py`
- Modify: `tests/test_剧圈圈.py`

- [ ] **Step 1: Write the failing tests for homepage recommendations, category paging, and search flow**

```python
from unittest.mock import patch

    def test_parse_cards_extracts_compact_vod_ids(self):
        html = """
        <a class="module-poster-item module-item" href="/vod/123.html">
          <img data-original="/cover.jpg" />
          <div class="module-poster-item-title">示例影片</div>
          <div class="module-item-note">更新至1集</div>
        </a>
        """
        self.assertEqual(
            self.spider._parse_cards(html),
            [
                {
                    "vod_id": "vod/123",
                    "vod_name": "示例影片",
                    "vod_pic": "https://www.jqqzx.cc/cover.jpg",
                    "vod_remarks": "更新至1集",
                }
            ],
        )

    @patch.object(Spider, "_request_html")
    def test_home_video_content_limits_recommendations(self, mock_request_html):
        mock_request_html.return_value = "".join(
            f'<a class="module-poster-item module-item" href="/vod/{i}.html"><div class="module-poster-item-title">影片{i}</div></a>'
            for i in range(1, 45)
        )
        result = self.spider.homeVideoContent()
        self.assertEqual(len(result["list"]), 40)
        self.assertEqual(result["list"][0]["vod_id"], "vod/1")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <a class="module-poster-item module-item" href="/vod/456.html">
          <div class="module-poster-item-title">分类影片</div>
        </a>
        """
        result = self.spider.categoryContent("juji", "2", False, {})
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.jqqzx.cc/type/juji/page/2.html")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["pagecount"], 3)
        self.assertEqual(result["list"][0]["vod_id"], "vod/456")

    @patch.object(Spider, "_request_html")
    def test_search_content_uses_suggest_api(self, mock_request_html):
        mock_request_html.return_value = '{"list":[{"id":"777","name":"搜索结果","pic":"/pic.jpg"}]}'
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(
            mock_request_html.call_args.args[0],
            "https://www.jqqzx.cc/index.php/ajax/suggest?mid=1&wd=%E7%B9%81%E8%8A%B1",
        )
        self.assertEqual(result["list"][0]["vod_id"], "vod/777")
        self.assertEqual(result["pagecount"], 1)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_parse_cards_extracts_compact_vod_ids tests.test_剧圈圈.TestJuQuanQuanSpider.test_home_video_content_limits_recommendations tests.test_剧圈圈.TestJuQuanQuanSpider.test_category_content_builds_page_result tests.test_剧圈圈.TestJuQuanQuanSpider.test_search_content_uses_suggest_api -v`

Expected: `FAIL` or `ERROR` because `_parse_cards` and high-level methods are incomplete.

- [ ] **Step 3: Implement shared request and list parsing methods**

```python
    def _request_html(self, path_or_url, headers=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        merged = dict(self.headers)
        if headers:
            merged.update(headers)
        response = self.fetch(target, headers=merged, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for anchor in root.xpath("//a[contains(@class,'module-poster-item') and contains(@class,'module-item')]"):
            vod_id = self._encode_vod_id((anchor.xpath("./@href") or [""])[0])
            if not vod_id or vod_id in seen:
                continue
            seen.add(vod_id)
            title = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'module-poster-item-title')][1]//text()"))) or self._clean_text((anchor.xpath("./@title") or [""])[0])
            if not title:
                continue
            pic = (anchor.xpath(".//img[1]/@data-original") or anchor.xpath(".//img[1]/@src") or [""])[0]
            note = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'module-item-note')][1]//text()")))
            items.append({"vod_id": vod_id, "vod_name": title, "vod_pic": self._build_url(pic), "vod_remarks": note})
        return items

    def homeVideoContent(self):
        return {"list": self._parse_cards(self._request_html(self.host))[:40]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._request_html(self._build_url(f"/type/{tid}/page/{page}.html")))
        return {"page": page, "pagecount": page + 1 if items else page, "total": page * len(items) + (1 if items else 0), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "pagecount": 1, "total": 0, "list": []}
        url = self._build_url(f"/index.php/ajax/suggest?mid=1&wd={quote(keyword)}")
        items = self._parse_search_list(self._request_html(url))
        return {"page": page, "pagecount": 1, "total": len(items), "list": items}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_parse_cards_extracts_compact_vod_ids tests.test_剧圈圈.TestJuQuanQuanSpider.test_home_video_content_limits_recommendations tests.test_剧圈圈.TestJuQuanQuanSpider.test_category_content_builds_page_result tests.test_剧圈圈.TestJuQuanQuanSpider.test_search_content_uses_suggest_api -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add 剧圈圈.py tests/test_剧圈圈.py
git commit -m "feat: add juquanquan list and search flows"
```

### Task 3: Implement Detail Parsing With Multi-Line Playlists

**Files:**
- Modify: `剧圈圈.py`
- Modify: `tests/test_剧圈圈.py`

- [ ] **Step 1: Write the failing tests for detail metadata and compact play ids**

```python
    def test_parse_detail_page_extracts_metadata_and_playlists(self):
        html = """
        <div class="module-info-heading"><h1>详情标题</h1></div>
        <div class="module-info-poster"><img data-original="/poster.jpg" /></div>
        <div class="module-info-item">
          <div class="module-info-item-title">导演</div>
          <div class="module-info-item-content"><a>导演甲</a></div>
        </div>
        <div class="module-info-item">
          <div class="module-info-item-title">主演</div>
          <div class="module-info-item-content"><a>演员甲</a><a>演员乙</a></div>
        </div>
        <div class="module-info-item">
          <div class="module-info-item-title">备注</div>
          <div class="module-info-item-content">更新至3集</div>
        </div>
        <div class="module-info-introduction-content">一段剧情简介</div>
        <div class="module-info-tag-link"><a>古装</a><a>剧情</a></div>
        <div id="y-playList">
          <div class="module-tab-item" data-dropdown-value="线路A"></div>
          <div class="module-tab-item" data-dropdown-value="线路B"></div>
        </div>
        <div class="his-tab-list">
          <a class="module-play-list-link" href="/play/123-1-1.html"><span>第1集</span></a>
          <a class="module-play-list-link" href="/play/123-1-2.html"><span>第2集</span></a>
        </div>
        <div class="his-tab-list">
          <a class="module-play-list-link" href="/play/123-2-1.html"><span>正片</span></a>
        </div>
        """
        result = self.spider._parse_detail_page(html, "vod/123")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "vod/123")
        self.assertEqual(vod["vod_name"], "详情标题")
        self.assertEqual(vod["vod_pic"], "https://www.jqqzx.cc/poster.jpg")
        self.assertEqual(vod["type_name"], "古装 / 剧情")
        self.assertEqual(vod["vod_director"], "导演甲")
        self.assertEqual(vod["vod_actor"], "演员甲 / 演员乙")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "线路A$$$线路B")
        self.assertEqual(vod["vod_play_url"], "第1集$play/123-1-1#第2集$play/123-1-2$$$正片$play/123-2-1")

    @patch.object(Spider, "_request_html")
    def test_detail_content_decodes_compact_vod_id(self, mock_request_html):
        mock_request_html.return_value = '<div class="module-info-heading"><h1>详情标题</h1></div>'
        self.spider.detailContent(["vod/321"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://www.jqqzx.cc/vod/321.html")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_parse_detail_page_extracts_metadata_and_playlists tests.test_剧圈圈.TestJuQuanQuanSpider.test_detail_content_decodes_compact_vod_id -v`

Expected: `FAIL` or `ERROR` because detail parsing is not implemented.

- [ ] **Step 3: Implement detail metadata parsing and playlist extraction**

```python
    def _parse_info_items(self, root):
        info = {}
        for item in root.xpath("//*[contains(@class,'module-info-item')]"):
            title = self._clean_text("".join(item.xpath(".//*[contains(@class,'module-info-item-title')][1]//text()"))).rstrip("：:")
            if not title:
                continue
            values = [self._clean_text("".join(node.xpath(".//text()"))) for node in item.xpath(".//*[contains(@class,'module-info-item-content')][1]//a")]
            if values:
                info[title] = " / ".join([value for value in values if value])
            else:
                info[title] = self._clean_text("".join(item.xpath(".//*[contains(@class,'module-info-item-content')][1]//text()")))
        return info

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        if root is None:
            return {"list": []}
        info = self._parse_info_items(root)
        tab_names = [self._clean_text((node.xpath("./@data-dropdown-value") or [""])[0] or "".join(node.xpath(".//span[1]//text()"))) for node in root.xpath("//*[@id='y-playList']//*[contains(@class,'module-tab-item')]")]
        groups = []
        for index, box in enumerate(root.xpath("//*[contains(@class,'his-tab-list')]")):
            episodes = []
            for anchor in box.xpath(".//a[contains(@class,'module-play-list-link') and @href]"):
                play_id = self._encode_play_id((anchor.xpath("./@href") or [""])[0])
                title = self._clean_text("".join(anchor.xpath(".//span[1]//text()")) or "".join(anchor.xpath(".//text()")))
                if play_id and title:
                    episodes.append(f"{title}${play_id}")
            if episodes:
                groups.append({"from": tab_names[index] if index < len(tab_names) and tab_names[index] else f"线路{index + 1}", "urls": "#".join(episodes)})
        type_name = " / ".join([self._clean_text("".join(node.xpath(".//text()"))) for node in root.xpath("//*[contains(@class,'module-info-tag-link')]//a") if self._clean_text("".join(node.xpath(".//text()")))])
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text("".join(root.xpath("//*[contains(@class,'module-info-heading')]//h1[1]//text()"))),
                    "vod_pic": self._build_url((root.xpath("(//*[contains(@class,'module-item-pic')]//img/@data-original | //*[contains(@class,'module-info-poster')]//img/@data-original | //*[contains(@class,'module-item-pic')]//img/@src | //*[contains(@class,'module-info-poster')]//img/@src)[1]") or [""])[0]),
                    "type_name": type_name,
                    "vod_remarks": info.get("备注") or info.get("状态", ""),
                    "vod_actor": info.get("主演", ""),
                    "vod_director": info.get("导演", ""),
                    "vod_content": self._clean_text("".join(root.xpath("//*[contains(@class,'module-info-introduction-content')][1]//text()"))),
                    "vod_play_from": "$$$".join([group["from"] for group in groups]),
                    "vod_play_url": "$$$".join([group["urls"] for group in groups]),
                }
            ]
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw in ids:
            vod_id = str(raw or "").strip()
            url = self._decode_vod_id(vod_id)
            if not url:
                continue
            parsed = self._parse_detail_page(self._request_html(url), vod_id)
            result["list"].extend(parsed.get("list", []))
        return result
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_parse_detail_page_extracts_metadata_and_playlists tests.test_剧圈圈.TestJuQuanQuanSpider.test_detail_content_decodes_compact_vod_id -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add 剧圈圈.py tests/test_剧圈圈.py
git commit -m "feat: add juquanquan detail parsing"
```

### Task 4: Implement Player Decoding, Direct Media Priority, And Parse Fallback

**Files:**
- Modify: `剧圈圈.py`
- Modify: `tests/test_剧圈圈.py`

- [ ] **Step 1: Write the failing tests for direct URL playback, parse API fallback, and missing-player fallback**

```python
    def test_extract_player_data_reads_player_aaaa(self):
        html = '<script>var player_aaaa={"url":"https://video.example/direct.m3u8"};</script>'
        self.assertEqual(self.spider._extract_player_data(html)["url"], "https://video.example/direct.m3u8")

    @patch.object(Spider, "_request_with_headers")
    def test_player_content_returns_direct_media_url(self, mock_request_with_headers):
        mock_request_with_headers.return_value = {
            "body": '<script>var player_aaaa={"url":"https://video.example/direct.m3u8"};</script>',
            "headers": {},
            "status_code": 200,
        }
        result = self.spider.playerContent("线路A", "play/123-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/direct.m3u8")

    @patch.object(Spider, "_request_with_headers")
    def test_player_content_uses_parse_api_when_player_vid_is_not_direct(self, mock_request_with_headers):
        mock_request_with_headers.side_effect = [
            {
                "body": '<script>var player_aaaa={"url":"https%3A%2F%2Fmiddle.example%2Fembed%3Fid%3D1"};</script>',
                "headers": {"set-cookie": ["foo=bar; Path=/"]},
                "status_code": 200,
            },
            {"body": "<html></html>", "headers": {"set-cookie": ["token=abc; Path=/"]}, "status_code": 200},
            {"body": '{"code":200,"data":{"url":"error://apiRes_dummy"}}', "headers": {}, "status_code": 200},
        ]
        self.spider._decode_url = lambda value: "https://video.example/fallback.m3u8"
        result = self.spider.playerContent("线路A", "play/123-1-1", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/fallback.m3u8")

    @patch.object(Spider, "_request_with_headers")
    def test_player_content_falls_back_to_play_page_when_player_data_missing(self, mock_request_with_headers):
        mock_request_with_headers.return_value = {"body": "<html></html>", "headers": {}, "status_code": 200}
        result = self.spider.playerContent("线路A", "play/123-1-1", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["url"], "https://www.jqqzx.cc/play/123-1-1.html")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_extract_player_data_reads_player_aaaa tests.test_剧圈圈.TestJuQuanQuanSpider.test_player_content_returns_direct_media_url tests.test_剧圈圈.TestJuQuanQuanSpider.test_player_content_uses_parse_api_when_player_vid_is_not_direct tests.test_剧圈圈.TestJuQuanQuanSpider.test_player_content_falls_back_to_play_page_when_player_data_missing -v`

Expected: `FAIL` or `ERROR` because playback helpers are missing.

- [ ] **Step 3: Implement request-with-headers, player extraction, decode helpers, and playerContent**

```python
import base64
import hashlib
import json
from urllib.parse import quote, unquote

    def _request_with_headers(self, path_or_url, headers=None, data=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        merged = dict(self.headers)
        if headers:
            merged.update(headers)
        response = self.fetch(target, headers=merged, data=data, timeout=10)
        return {"body": response.text or "", "headers": getattr(response, "headers", {}) or {}, "status_code": response.status_code}

    def _get_set_cookies(self, headers):
        raw = headers.get("set-cookie") or headers.get("Set-Cookie") or []
        items = raw if isinstance(raw, list) else [raw]
        return [str(item).split(";", 1)[0] for item in items if str(item).strip()]

    def _merge_cookies(self, *groups):
        values = {}
        for group in groups:
            for item in (group if isinstance(group, list) else [group]):
                text = str(item or "").strip()
                if "=" not in text:
                    continue
                key, val = text.split("=", 1)
                values[key] = val
        return [f"{key}={val}" for key, val in values.items()]

    def _base64_decode(self, value):
        text = re.sub(r"\s+", "", str(value or ""))
        if not text:
            return ""
        text += "=" * ((4 - len(text) % 4) % 4)
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            return ""

    def _decode_url(self, value):
        raw = str(value or "").replace("error://apiRes_", "").strip()
        if not raw:
            return ""
        key = hashlib.md5("test".encode("utf-8")).hexdigest()
        first = self._base64_decode(raw)
        mixed = "".join(chr(ord(ch) ^ ord(key[index % len(key)])) for index, ch in enumerate(first))
        decoded = self._base64_decode(mixed)
        parts = decoded.split("/")
        if len(parts) < 3:
            return ""
        from_map = json.loads(self._base64_decode(parts[1]))
        to_map = json.loads(self._base64_decode(parts[0]))
        body = self._base64_decode("/".join(parts[2:]))
        mapped = re.sub(r"[a-zA-Z]", lambda match: to_map[from_map.index(match.group(0))] if match.group(0) in from_map else match.group(0), body)
        matched = re.search(r"https?://[^\s'\"<>]+", mapped)
        return matched.group(0) if matched else mapped.strip()

    def _extract_player_data(self, html):
        matched = re.search(r"player_aaaa\\s*=\\s*(\\{[\\s\\S]*?\\})\\s*;?\\s*</script>", str(html or ""), re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _is_media_url(self, value):
        return bool(re.search(r"^https?://.*\\.(m3u8|mp4|flv|m4s)(\\?.*)?$", str(value or ""), re.I))

    def playerContent(self, flag, id, vipFlags):
        play_url = self._decode_play_id(id)
        if not play_url:
            return {"parse": 1, "jx": 1, "url": "", "header": dict(self.headers)}
        try:
            play_res = self._request_with_headers(play_url, headers={"Referer": self.host + "/"})
            player = self._extract_player_data(play_res["body"])
            if not player:
                return {"parse": 1, "jx": 1, "url": play_url, "header": dict(self.headers)}
            vid = unquote(str(player.get("url") or "")).strip()
            if vid and not self._is_media_url(vid):
                decoded = self._decode_url(vid)
                if decoded.startswith("http"):
                    vid = decoded
            if self._is_media_url(vid):
                return {"parse": 0, "jx": 0, "url": vid, "header": {**self.headers, "Referer": play_url}}
            cookies = self._get_set_cookies(play_res["headers"])
            player_page = self._build_url(f"/jx/player.php?vid={quote(vid)}")
            player_res = self._request_with_headers(player_page, headers={"Referer": play_url, **({"Cookie": "; ".join(cookies)} if cookies else {})})
            cookies = self._merge_cookies(cookies, self._get_set_cookies(player_res["headers"]))
            api_res = self._request_with_headers(
                self._build_url("/jx/api.php"),
                headers={
                    "Referer": player_page,
                    "Origin": self.host,
                    "X-Requested-With": "XMLHttpRequest",
                    **({"Cookie": "; ".join(cookies)} if cookies else {}),
                },
                data=f"vid={quote(vid)}",
            )
            payload = json.loads(api_res["body"] or "{}")
            real_url = self._decode_url(payload.get("data", {}).get("url"))
            if real_url.startswith("http"):
                return {"parse": 0, "jx": 0, "url": real_url, "header": {**self.headers, "Referer": player_page}}
            return {"parse": 1, "jx": 1, "url": play_url, "header": {**self.headers, "Referer": player_page}}
        except Exception:
            return {"parse": 1, "jx": 1, "url": play_url, "header": dict(self.headers)}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_剧圈圈.TestJuQuanQuanSpider.test_extract_player_data_reads_player_aaaa tests.test_剧圈圈.TestJuQuanQuanSpider.test_player_content_returns_direct_media_url tests.test_剧圈圈.TestJuQuanQuanSpider.test_player_content_uses_parse_api_when_player_vid_is_not_direct tests.test_剧圈圈.TestJuQuanQuanSpider.test_player_content_falls_back_to_play_page_when_player_data_missing -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add 剧圈圈.py tests/test_剧圈圈.py
git commit -m "feat: add juquanquan player parsing"
```

### Task 5: Run Focused Verification And Clean Up

**Files:**
- Modify: `剧圈圈.py`
- Modify: `tests/test_剧圈圈.py`

- [ ] **Step 1: Run the full dedicated test file**

Run: `python -m unittest tests.test_剧圈圈 -v`

Expected: all tests in `tests/test_剧圈圈.py` pass.

- [ ] **Step 2: Fix any isolated assertion mismatches found by the dedicated test file**

```python
# Only make the smallest change required by the failing assertion.
# Typical examples:
# - adjust XPath fallback order
# - normalize whitespace in actor/director strings
# - preserve compact id format in a return payload
```

- [ ] **Step 3: Re-run the full dedicated test file**

Run: `python -m unittest tests.test_剧圈圈 -v`

Expected: `OK`

- [ ] **Step 4: Review the final diff for accidental scope creep**

Run: `git diff -- 剧圈圈.py tests/test_剧圈圈.py`

Expected: diff only touches the new spider and its tests.

- [ ] **Step 5: Commit**

```bash
git add 剧圈圈.py tests/test_剧圈圈.py
git commit -m "feat: finalize juquanquan spider"
```
