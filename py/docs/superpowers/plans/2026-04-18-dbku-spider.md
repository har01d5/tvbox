# 独播库 Spider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的独播库爬虫，支持分类、详情、搜索和站内播放解析。

**Architecture:** 以单文件站点脚本 `独播库.py` 承担独播库站点逻辑，内部拆分为 URL 归一化、卡片解析、详情解析和 `player_data` 解码几组辅助方法。测试沿用当前仓库 `unittest + SourceFileLoader + mock` 风格，优先覆盖纯解析函数和高层方法的 mock 网络流程，不依赖真实站点网络。

**Tech Stack:** Python 3, `requests`, `lxml`, `unittest`, `unittest.mock`, `base64`, `json`, `urllib.parse`

---

## File Structure

- Create: `独播库.py`
  - 独播库站点实现，继承 `base.spider.Spider`
  - 暴露 `init`、`homeContent`、`homeVideoContent`、`categoryContent`、`detailContent`、`searchContent`、`playerContent`
  - 私有方法负责 URL 归一化、列表卡片解析、搜索结果解析、详情解析、`player_data` 提取与解码
- Create: `tests/test_dbku.py`
  - 用 `SourceFileLoader` 加载 `独播库.py`
  - 用 HTML 片段与 mock response 测试分类、搜索、详情和播放器解析
- Modify: `docs/superpowers/plans/2026-04-18-dbku-spider.md`
  - 仅用于勾选执行状态

### Task 1: Scaffold Spider And List Card Parsing

**Files:**
- Create: `tests/test_dbku.py`
- Create: `独播库.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("dbku_spider", str(ROOT / "独播库.py")).load_module()
Spider = MODULE.Spider


class TestDBKUSpider(unittest.TestCase):
    def setUp(self):
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_expected_categories(self):
        content = self.spider.homeContent(False)
        class_ids = [item["type_id"] for item in content["class"]]
        self.assertEqual(class_ids, ["index", "movie", "variety", "anime", "hk", "luju"])

    def test_parse_list_cards_extracts_detail_url_title_cover_and_description(self):
        html = """
        <div class="myui-vodlist__box">
          <a class="thumb" href="/voddetail/123.html" title="示例影片" data-original="https://img.example/dbku.jpg"></a>
          <span class="pic-text">更新至10集</span>
        </div>
        """
        cards = self.spider._parse_list_cards(html)
        self.assertEqual(
            cards,
            [{
                "vod_id": "https://www.dbku.tv/voddetail/123.html",
                "vod_name": "示例影片",
                "vod_pic": "https://img.example/dbku.jpg",
                "vod_remarks": "更新至10集",
            }],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider -v`
Expected: FAIL with `FileNotFoundError` for `独播库.py` or missing methods.

- [ ] **Step 3: Write minimal implementation**

```python
# coding=utf-8
import sys
from urllib.parse import urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "独播库"
        self.host = "https://www.dbku.tv"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.categories = [
            {"type_name": "连续剧", "type_id": "index"},
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "综艺", "type_id": "variety"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "港剧", "type_id": "hk"},
            {"type_name": "陆剧", "type_id": "luju"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def homeVideoContent(self):
        return {"list": []}

    def _build_url(self, href):
        raw = str(href or "").strip()
        if not raw:
            return ""
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _parse_list_cards(self, html):
        root = self.html(html)
        results = []
        if root is None:
            return results

        cards = root.xpath("//*[contains(@class,'myui-vodlist__box')]")
        seen = set()
        for card in cards:
            href = ""
            title = ""
            pic = ""
            for anchor in card.xpath(".//a[@href]"):
                raw_href = (anchor.xpath("./@href") or [""])[0].strip()
                if "/voddetail/" in raw_href:
                    href = self._build_url(raw_href)
                    title = (
                        (anchor.xpath("./@title") or [""])[0].strip()
                        or "".join(anchor.xpath(".//text()")).strip()
                    )
                    pic = (
                        (anchor.xpath("./@data-original") or [""])[0].strip()
                        or (anchor.xpath("./@src") or [""])[0].strip()
                    )
                    break
            if not href or href in seen or not title:
                continue
            remarks = "".join(card.xpath(".//*[contains(@class,'pic-text')][1]//text()")).strip()
            seen.add(href)
            results.append({
                "vod_id": href,
                "vod_name": title,
                "vod_pic": self._build_url(pic),
                "vod_remarks": remarks,
            })
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider -v`
Expected: PASS for the two new tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_dbku.py 独播库.py
git commit -m "feat: scaffold dbku spider parsing"
```

### Task 2: Add Category And Search Flows

**Files:**
- Modify: `tests/test_dbku.py`
- Modify: `独播库.py`

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import patch


class TestDBKUSpider(unittest.TestCase):
    @patch.object(Spider, "fetch")
    def test_request_html_uses_dbku_headers(self, mock_fetch):
        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.status_code = 200
                self.encoding = "utf-8"

        mock_fetch.return_value = FakeResponse("<html><body>ok</body></html>")
        html = self.spider._request_html("/vodtype/1--------1---.html", expect_xpath="//body")
        self.assertIn("ok", html)
        called_headers = mock_fetch.call_args.kwargs["headers"]
        self.assertEqual(called_headers["Referer"], "https://www.dbku.tv")
        self.assertEqual(called_headers["Origin"], "https://www.dbku.tv")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_page_result(self, mock_request_html):
        mock_request_html.return_value = """
        <div class="myui-vodlist__box">
          <a href="/voddetail/456.html" title="分类影片" data-original="/cover.jpg"></a>
          <span class="pic-text">HD</span>
        </div>
        """
        result = self.spider.categoryContent("movie", "2", False, {})
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_name"], "分类影片")
        self.assertEqual(result["list"][0]["vod_pic"], "https://www.dbku.tv/cover.jpg")

    def test_parse_search_cards_prefers_search_list_container(self):
        html = """
        <div id="searchList">
          <div class="myui-vodlist__box">
            <a href="/voddetail/789.html" title="搜索命中" data-original="/search.jpg"></a>
          </div>
        </div>
        <div class="myui-vodlist__box">
          <a href="/voddetail/999.html" title="回退结果" data-original="/fallback.jpg"></a>
        </div>
        """
        results = self.spider._parse_search_cards(html)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["vod_name"], "搜索命中")

    @patch.object(Spider, "_request_html")
    def test_search_content_reuses_search_parser(self, mock_request_html):
        mock_request_html.return_value = """
        <div id="searchList">
          <div class="myui-vodlist__box">
            <a href="/voddetail/321.html" title="搜索影片" data-original="/search.jpg"></a>
          </div>
        </div>
        """
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual(result["list"][0]["vod_id"], "https://www.dbku.tv/voddetail/321.html")
        self.assertEqual(result["list"][0]["vod_name"], "搜索影片")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_request_html_uses_dbku_headers tests.test_dbku.TestDBKUSpider.test_category_content_builds_page_result tests.test_dbku.TestDBKUSpider.test_parse_search_cards_prefers_search_list_container tests.test_dbku.TestDBKUSpider.test_search_content_reuses_search_parser -v`
Expected: FAIL with missing `_request_html`, `categoryContent`, `searchContent`, or `_parse_search_cards`.

- [ ] **Step 3: Write minimal implementation**

```python
from urllib.parse import quote
from lxml import etree


class Spider(BaseSpider):
    def __init__(self):
        self.name = "独播库"
        self.host = "https://www.dbku.tv"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.categories = [
            {"type_name": "连续剧", "type_id": "index"},
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "综艺", "type_id": "variety"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "港剧", "type_id": "hk"},
            {"type_name": "陆剧", "type_id": "luju"},
        ]
        self.category_paths = {
            "index": "/vodtype/2--------{pg}---.html",
            "movie": "/vodtype/1--------{pg}---.html",
            "variety": "/vodtype/3--------{pg}---.html",
            "anime": "/vodtype/4--------{pg}---.html",
            "hk": "/vodtype/20--------{pg}---.html",
            "luju": "/vodtype/13--------{pg}---.html",
        }

    def _request_html(self, path_or_url, expect_xpath=None, referer=None):
        target = path_or_url if path_or_url.startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.host
        headers["Origin"] = self.host
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        html = response.text or ""
        if expect_xpath:
            root = self.html(html)
            if root is None or not root.xpath(expect_xpath):
                return ""
        return html

    def _parse_search_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        search_list = root.xpath("//*[@id='searchList']")
        if search_list:
            cards = search_list[0].xpath(".//*[contains(@class,'myui-vodlist__box')]")
            parsed = self._parse_cards_from_nodes(cards)
            if parsed:
                return parsed
        return self._parse_list_cards(html)

    def _parse_cards_from_nodes(self, nodes):
        results = []
        seen = set()
        for card in nodes:
            snippet = self._parse_list_cards(etree.tostring(card, encoding='unicode'))
            for item in snippet:
                if item["vod_id"] in seen:
                    continue
                seen.add(item["vod_id"])
                results.append(item)
        return results

    def _page_result(self, items, pg):
        page = int(pg)
        pagecount = page + 1 if items else page
        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": len(items),
            "total": pagecount * max(len(items), 1),
        }

    def categoryContent(self, tid, pg, filter, extend):
        path = self.category_paths.get(tid, self.category_paths["index"]).format(pg=pg)
        html = self._request_html(path, expect_xpath="//*[contains(@class,'myui-vodlist__box')]")
        return self._page_result(self._parse_list_cards(html), pg)

    def searchContent(self, key, quick, pg="1"):
        path = "/vodsearch/-------------.html?wd={0}&submit=".format(quote(key))
        html = self._request_html(path, expect_xpath="//*[@id='searchList']|//*[contains(@class,'myui-vodlist__box')]")
        return self._page_result(self._parse_search_cards(html), pg)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_request_html_uses_dbku_headers tests.test_dbku.TestDBKUSpider.test_category_content_builds_page_result tests.test_dbku.TestDBKUSpider.test_parse_search_cards_prefers_search_list_container tests.test_dbku.TestDBKUSpider.test_search_content_reuses_search_parser -v`
Expected: PASS for all four tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_dbku.py 独播库.py
git commit -m "feat: add dbku category and search flow"
```

### Task 3: Add Detail Parsing And Episode List Extraction

**Files:**
- Modify: `tests/test_dbku.py`
- Modify: `独播库.py`

- [ ] **Step 1: Write the failing test**

```python
class TestDBKUSpider(unittest.TestCase):
    def test_parse_detail_page_extracts_meta_and_episodes(self):
        html = """
        <div class="myui-content__thumb">
          <img data-original="/poster.jpg" />
        </div>
        <div class="myui-content__detail">
          <h1 class="title">独播剧</h1>
          <p>年份：2025</p>
          <p>地区：大陆</p>
          <p>导演：张三</p>
          <p>主演：李四</p>
        </div>
        <span class="data">一段剧情简介</span>
        <a href="/vodplay/100-1-1.html">第1集</a>
        <a href="/vodplay/100-1-2.html">第2集</a>
        """
        result = self.spider._parse_detail_page(html, "https://www.dbku.tv/voddetail/100.html")
        vod = result["list"][0]
        self.assertEqual(vod["vod_name"], "独播剧")
        self.assertEqual(vod["vod_year"], "2025")
        self.assertEqual(vod["vod_play_from"], "独播库")
        self.assertIn("第1集$https://www.dbku.tv/vodplay/100-1-1.html", vod["vod_play_url"])

    @patch.object(Spider, "_request_html")
    def test_detail_content_reads_from_vod_id_url(self, mock_request_html):
        mock_request_html.return_value = """
        <h1 class="title">详情影片</h1>
        <a href="/vodplay/200-1-1.html">第1集</a>
        """
        result = self.spider.detailContent(["https://www.dbku.tv/voddetail/200.html"])
        self.assertEqual(result["list"][0]["vod_id"], "https://www.dbku.tv/voddetail/200.html")
        self.assertEqual(result["list"][0]["vod_name"], "详情影片")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_parse_detail_page_extracts_meta_and_episodes tests.test_dbku.TestDBKUSpider.test_detail_content_reads_from_vod_id_url -v`
Expected: FAIL with missing `_parse_detail_page` or `detailContent`.

- [ ] **Step 3: Write minimal implementation**

```python
import re


class Spider(BaseSpider):
    def _extract_text_by_prefix(self, html, prefixes):
        texts = re.findall(r">([^<>]+)<", html)
        for text in texts:
            clean = text.strip()
            for prefix in prefixes:
                if clean.startswith(prefix):
                    return clean.split("：", 1)[-1].strip()
        return ""

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        title = ((root.xpath("//*[contains(@class,'title')][1]//text()") or [""])[0]).strip()
        pic = (
            (root.xpath("//*[contains(@class,'myui-content__thumb')]//img/@data-original") or [""])[0].strip()
            or (root.xpath("//*[contains(@class,'myui-content__thumb')]//img/@src") or [""])[0].strip()
        )
        content = "".join(root.xpath("//*[contains(@class,'data')][1]//text()")).strip()

        episodes = []
        seen = set()
        for href, label in re.findall(r'<a[^>]+href=["\\\']([^"\\\']*/vodplay/\\d+-\\d+-\\d+\\.html[^"\\\']*)["\\\'][^>]*>([\\s\\S]*?)</a>', html, re.I):
            url = self._build_url(href)
            name = re.sub(r"<[^>]*>", "", label).strip()
            if not url or not name or "立即播放" in name or url in seen:
                continue
            seen.add(url)
            episodes.append(f"{name}${url}")

        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_year": self._extract_text_by_prefix(html, ["年份："]),
            "vod_area": self._extract_text_by_prefix(html, ["地区："]),
            "vod_actor": self._extract_text_by_prefix(html, ["主演："]),
            "vod_director": self._extract_text_by_prefix(html, ["导演："]),
            "vod_content": content,
            "vod_play_from": "独播库",
            "vod_play_url": "#".join(episodes),
        }
        return {"list": [vod]}

    def detailContent(self, ids):
        vod_id = ids[0]
        html = self._request_html(vod_id, expect_xpath="//*[contains(@class,'title')]|//a[contains(@href,'/vodplay/')]")
        return self._parse_detail_page(html, vod_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_parse_detail_page_extracts_meta_and_episodes tests.test_dbku.TestDBKUSpider.test_detail_content_reads_from_vod_id_url -v`
Expected: PASS for both detail tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_dbku.py 独播库.py
git commit -m "feat: add dbku detail parsing"
```

### Task 4: Add player_data Extraction And Encrypt Decoders

**Files:**
- Modify: `tests/test_dbku.py`
- Modify: `独播库.py`

- [ ] **Step 1: Write the failing test**

```python
import base64


class TestDBKUSpider(unittest.TestCase):
    def test_parse_player_data_reads_json_block(self):
        html = '<script>var player_data = {"url":"https://video.example/a.m3u8","encrypt":"0"};</script>'
        data = self.spider._parse_player_data(html)
        self.assertEqual(data["url"], "https://video.example/a.m3u8")

    def test_decode_play_url_by_encrypt_supports_modes_0_1_2_3(self):
        self.assertEqual(
            self.spider._decode_play_url_by_encrypt("https://video.example/raw.m3u8", 0),
            "https://video.example/raw.m3u8",
        )
        self.assertEqual(
            self.spider._decode_play_url_by_encrypt("https%3A//video.example/escape.m3u8", 1),
            "https://video.example/escape.m3u8",
        )
        mode2 = base64.b64encode("https://video.example/base64.m3u8".encode("utf-8")).decode("utf-8")
        self.assertEqual(
            self.spider._decode_play_url_by_encrypt(mode2, 2),
            "https://video.example/base64.m3u8",
        )
        mode3_raw = "ABCDEFGHhttps://video.example/trimmed.m3u8HGFEDCBA"
        mode3 = base64.b64encode(mode3_raw.encode("utf-8")).decode("utf-8")
        self.assertEqual(
            self.spider._decode_play_url_by_encrypt("12345678" + mode3, 3),
            "https://video.example/trimmed.m3u8",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_parse_player_data_reads_json_block tests.test_dbku.TestDBKUSpider.test_decode_play_url_by_encrypt_supports_modes_0_1_2_3 -v`
Expected: FAIL with missing `_parse_player_data` or `_decode_play_url_by_encrypt`.

- [ ] **Step 3: Write minimal implementation**

```python
import base64
import json
from urllib.parse import unquote


class Spider(BaseSpider):
    def _parse_player_data(self, html):
        matched = re.search(r"var\\s+player_data\\s*=\\s*(\\{[\\s\\S]*?\\})\\s*</script>", html, re.I)
        if not matched:
            matched = re.search(r"var\\s+player_[^=]*\\s*=\\s*(\\{[\\s\\S]*?\\})\\s*</script>", html, re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _decode_play_url_by_encrypt(self, value, encrypt):
        raw = str(value or "")
        mode = int(encrypt or 0)
        if not raw:
            return ""
        try:
            if mode == 1:
                return unquote(raw)
            if mode == 2:
                decoded = base64.b64decode(raw).decode("utf-8")
                return unquote(decoded)
            if mode == 3:
                text = raw[8:] if len(raw) > 16 else raw
                text = base64.b64decode(text).decode("utf-8")
                if len(text) > 16:
                    text = text[8:-8]
                return text
            return raw
        except Exception:
            return raw
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_parse_player_data_reads_json_block tests.test_dbku.TestDBKUSpider.test_decode_play_url_by_encrypt_supports_modes_0_1_2_3 -v`
Expected: PASS for both decoder tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_dbku.py 独播库.py
git commit -m "feat: add dbku player decoders"
```

### Task 5: Wire High-Level playerContent And Full Regression

**Files:**
- Modify: `tests/test_dbku.py`
- Modify: `独播库.py`

- [ ] **Step 1: Write the failing test**

```python
class TestDBKUSpider(unittest.TestCase):
    @patch.object(Spider, "_request_html")
    def test_player_content_returns_decoded_direct_url(self, mock_request_html):
        mock_request_html.return_value = """
        <script>
        var player_data = {"url":"https://video.example/final.m3u8","encrypt":"0"};
        </script>
        """
        result = self.spider.playerContent("独播库", "https://www.dbku.tv/vodplay/100-1-1.html", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/final.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://www.dbku.tv/vodplay/100-1-1.html")

    @patch.object(Spider, "_request_html")
    def test_player_content_follows_internal_jump(self, mock_request_html):
        mock_request_html.side_effect = [
            '<script>var player_data = {"url":"/vodplay/100-1-2.html","encrypt":"0"};</script>',
            '<script>var player_data = {"url":"https://video.example/jump-final.m3u8","encrypt":"0"};</script>',
        ]
        result = self.spider.playerContent("独播库", "https://www.dbku.tv/vodplay/100-1-1.html", {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://video.example/jump-final.m3u8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_player_content_returns_decoded_direct_url tests.test_dbku.TestDBKUSpider.test_player_content_follows_internal_jump -v`
Expected: FAIL with missing `playerContent` or incorrect return payload.

- [ ] **Step 3: Write minimal implementation**

```python
class Spider(BaseSpider):
    def _build_player_headers(self, referer):
        return {
            "User-Agent": self.headers["User-Agent"],
            "Referer": referer,
        }

    def playerContent(self, flag, id, vipFlags):
        current = id
        for _ in range(3):
            html = self._request_html(current, referer=self.host)
            data = self._parse_player_data(html)
            if not data:
                return {"parse": 0, "playUrl": "", "url": ""}
            decoded = self._decode_play_url_by_encrypt(data.get("url", ""), data.get("encrypt", 0))
            play_url = self._build_url(decoded)
            if not play_url:
                return {"parse": 0, "playUrl": "", "url": ""}
            if self.host in play_url and "/vodplay/" in play_url and play_url != current:
                current = play_url
                continue
            return {
                "parse": 0,
                "playUrl": "",
                "url": play_url,
                "header": self._build_player_headers(current),
            }
        return {"parse": 0, "playUrl": "", "url": ""}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_dbku.TestDBKUSpider.test_player_content_returns_decoded_direct_url tests.test_dbku.TestDBKUSpider.test_player_content_follows_internal_jump -v`
Expected: PASS for both player tests.

- [ ] **Step 5: Run the full regression suite**

Run: `python -m unittest tests.test_dbku -v`
Expected: PASS for the complete `tests/test_dbku.py` suite.

- [ ] **Step 6: Commit**

```bash
git add tests/test_dbku.py 独播库.py
git commit -m "feat: finish dbku spider implementation"
```
