# 电影人生 Spider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前 Python 仓库中新增一个 `电影人生` spider，支持首页推荐、分类筛选、搜索精排、详情多线路解析和 `/api/m3u8` 播放链路。

**Architecture:** 使用单文件 `Spider` 实现，内部按 URL 构造、HTML 请求、卡片解析、详情解析、搜索精排和播放器解析拆成 helper。测试采用 `unittest + SourceFileLoader + unittest.mock`，按 TDD 逐步覆盖列表、详情和播放逻辑，不依赖真实网络。

**Tech Stack:** Python 3, `re`, `json`, `urllib.parse`, `base.spider.Spider`, `unittest`, `unittest.mock`

---

## File Structure

- Create: `py/电影人生.py`
  - 站点实现，负责分类与筛选定义、HTML 请求、列表/详情/搜索/播放解析
- Create: `py/tests/test_电影人生.py`
  - 离线测试，使用 `SourceFileLoader` 加载 spider，并 mock `fetch` 与 `_request_html`

### Task 1: Scaffold Spider, Filters, And Card Parsing

**Files:**
- Create: `py/tests/test_电影人生.py`
- Create: `py/电影人生.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("dyrs_spider", str(ROOT / "电影人生.py")).load_module()
Spider = MODULE.Spider

SAMPLE_LIST_HTML = """
<a data-url="/dyrscom-foo.html" href="/dyrscom-foo.html" title="片名A">
  <img data-src="/cover/a.jpg" />
  <div class="text-[10px]">更新至10集</div>
</a>
<div class="items-center flex mt-1"><span>2025</span><span>剧情</span></div>
<a data-url="/dyrscom-bar.html" href="/dyrscom-bar.html" title="片名B">
  <img src="https://img.example/b.jpg" />
</a>
"""


class TestDYRSSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_exposes_classes_and_filters(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["dianying", "dianshiju", "dongman", "zongyi"],
        )
        self.assertEqual(
            [item["key"] for item in content["filters"]["dianying"]],
            ["class", "sort_field"],
        )

    def test_parse_cards_extracts_short_id_title_pic_and_remarks(self):
        cards = self.spider._parse_vod_cards(SAMPLE_LIST_HTML)
        self.assertEqual(cards[0]["vod_id"], "dyrscom-foo.html")
        self.assertEqual(cards[0]["vod_name"], "片名A")
        self.assertEqual(cards[0]["vod_pic"], "https://dyrsok.com/cover/a.jpg")
        self.assertEqual(cards[0]["vod_year"], "2025")
        self.assertEqual(cards[0]["type_name"], "剧情")
        self.assertEqual(cards[0]["vod_remarks"], "更新至10集")

    @patch.object(Spider, "_request_html")
    def test_category_content_builds_query_string(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        result = self.spider.categoryContent(
            "dianying",
            "2",
            False,
            {"class": "动作", "sort_field": "update_time"},
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["list"][0]["vod_id"], "dyrscom-foo.html")
        mock_html.assert_called_with(
            "https://dyrsok.com/dianying.html?class=%E5%8A%A8%E4%BD%9C&sort_field=update_time&page=2"
        )

    @patch.object(Spider, "_request_html")
    def test_home_video_content_reads_home_page(self, mock_html):
        mock_html.return_value = SAMPLE_LIST_HTML
        result = self.spider.homeVideoContent()
        self.assertEqual(len(result["list"]), 2)
        mock_html.assert_called_with("https://dyrsok.com/")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_home_content_exposes_classes_and_filters -v`
Expected: FAIL with `FileNotFoundError` for `py/电影人生.py`

- [ ] **Step 3: Write minimal implementation**

```python
# coding=utf-8
import json
import re
import sys
from urllib.parse import urlencode, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "电影人生"
        self.host = "https://dyrsok.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "dianying", "type_name": "电影"},
            {"type_id": "dianshiju", "type_name": "电视剧"},
            {"type_id": "dongman", "type_name": "动漫"},
            {"type_id": "zongyi", "type_name": "综艺"},
        ]
        common_movie_tv = [
            {"key": "class", "name": "类型", "init": "", "value": [{"n": "全部", "v": ""}, {"n": "剧情", "v": "剧情"}]},
            {"key": "sort_field", "name": "排序", "init": "", "value": [{"n": "默认", "v": ""}, {"n": "更新时间", "v": "update_time"}]},
        ]
        self.filters = {
            "dianying": common_movie_tv,
            "dianshiju": common_movie_tv,
            "dongman": common_movie_tv,
            "zongyi": common_movie_tv,
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        return {"list": self._parse_vod_cards(self._request_html(self.host + "/"))[:24]}

    def _abs_url(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        return urljoin(self.host + "/", raw)

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _request_html(self, url, headers=None):
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        response = self.fetch(url, headers=request_headers, timeout=10, verify=False)
        return response.text if response.status_code == 200 else ""

    def _parse_vod_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        cards = []
        seen = set()
        for node in root.xpath("//a[@data-url and @title]"):
            href = ((node.xpath("./@href") or [""])[0]).strip()
            title = ((node.xpath("./@title") or [""])[0]).strip()
            if not href or not title or "/dyrscom-" not in href:
                continue
            vod_id = href.lstrip("/")
            if vod_id in seen:
                continue
            seen.add(vod_id)
            parent = node.getparent()
            year = self._clean_text("".join(parent.xpath(".//*[contains(@class,'items-center')][1]/span[1]//text()"))) if parent is not None else ""
            type_name = self._clean_text("".join(parent.xpath(".//*[contains(@class,'items-center')][1]/span[last()]//text()"))) if parent is not None else ""
            remarks = self._clean_text("".join(node.xpath(".//*[contains(@class,'text-[10px]')][1]//text()")))
            pic = ((node.xpath(".//img[1]/@data-src") or node.xpath(".//img[1]/@src") or [""])[0]).strip()
            cards.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._abs_url(pic),
                    "vod_url": self._abs_url(href),
                    "vod_year": year,
                    "type_name": type_name,
                    "vod_remarks": remarks,
                }
            )
        return cards

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        values = extend if isinstance(extend, dict) else {}
        qs = {}
        if values.get("class"):
            qs["class"] = values["class"]
        if values.get("sort_field"):
            qs["sort_field"] = values["sort_field"]
        if page > 1:
            qs["page"] = page
        url = self.host + f"/{tid}.html"
        if qs:
            url += "?" + urlencode(qs)
        return {"page": page, "total": 0, "list": self._parse_vod_cards(self._request_html(url))}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_home_content_exposes_classes_and_filters -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add py/电影人生.py py/tests/test_电影人生.py
git commit -m "feat: add dyrs spider scaffold"
```

### Task 2: Add Detail Parsing And Play List Assembly

**Files:**
- Modify: `py/tests/test_电影人生.py`
- Modify: `py/电影人生.py`

- [ ] **Step 1: Write the failing test**

```python
DETAIL_HTML = """
<meta property="og:image" content="/poster.jpg" />
<meta name="description" content="简介描述" />
<h1>电影人生示例</h1>
<div><span>年份</span><span>2025</span></div>
<div><span>地区</span><span>大陆</span></div>
<div><span>语言</span><span>国语</span></div>
<h3>导演</h3><div><a><span>张三</span></a></div>
<h3>主演</h3><div><a><span>李四</span></a><a><span>王五</span></a></div>
<h3>标签</h3><div><a><span>#剧情</span></a><a><span>#悬疑</span></a></div>
<h3>剧情简介</h3><div><div class="text-sm">这是一段剧情。</div></div>
<div id="originTabs">
  <a href="/dyrscom-foo.html?origin=line1"><button data-origin="线路一">线路一</button></a>
  <a href="/dyrscom-foo.html?origin=line2"><button data-origin="线路二">线路二</button></a>
</div>
"""
LINE1_HTML = """
<div class="seqlist">
  <a href="/dyrscom-foo.html?origin=line1&play=1" data-title="第1集" data-origin="线路一">第1集</a>
  <a href="/dyrscom-foo.html?origin=line1&play=2" data-title="第2集" data-origin="线路一">第2集</a>
</div>
"""
LINE2_HTML = """
<div class="seqlist">
  <a href="/dyrscom-foo.html?origin=line2&play=1" data-title="正片" data-origin="线路二">正片</a>
</div>
"""

    @patch.object(Spider, "_request_html")
    def test_detail_content_extracts_meta_and_lines(self, mock_html):
        mock_html.side_effect = [DETAIL_HTML, LINE1_HTML, LINE2_HTML]
        result = self.spider.detailContent(["dyrscom-foo.html"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "dyrscom-foo.html")
        self.assertEqual(vod["vod_name"], "电影人生示例")
        self.assertEqual(vod["vod_pic"], "https://dyrsok.com/poster.jpg")
        self.assertEqual(vod["vod_year"], "2025")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_lang"], "国语")
        self.assertEqual(vod["vod_director"], "张三")
        self.assertEqual(vod["vod_actor"], "李四,王五")
        self.assertEqual(vod["type_name"], "剧情 / 悬疑")
        self.assertEqual(vod["vod_play_from"], "线路一$$$线路二")
        self.assertIn("第1集$", vod["vod_play_url"])
        self.assertIn("正片$", vod["vod_play_url"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_detail_content_extracts_meta_and_lines -v`
Expected: FAIL with `AttributeError: 'Spider' object has no attribute 'detailContent'`

- [ ] **Step 3: Write minimal implementation**

```python
    def _pick_meta_value(self, html, label):
        matched = re.search(rf"{label}</span>\\s*<span[^>]*>([^<]+)</span>", html)
        return self._clean_text(matched.group(1)) if matched else ""

    def _extract_link_texts(self, html, title):
        root = self.html(html)
        if root is None:
            return []
        values = []
        for node in root.xpath(f"//h3[contains(normalize-space(.), '{title}')]/following-sibling::*[1]//a//span"):
            text = self._clean_text(''.join(node.xpath('.//text()'))).replace("#", "")
            if text:
                values.append(text)
        return values

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids).strip()
        if not vod_id:
            return {"list": []}
        url = self._abs_url(vod_id)
        html = self._request_html(url)
        root = self.html(html)
        if root is None:
            return {"list": []}
        vod_name = self._clean_text(''.join(root.xpath("(//h1|//h2)[1]//text()")))
        vod_pic = self._abs_url(((root.xpath("//meta[@property='og:image']/@content") or [""])[0]).strip())
        vod_content = self._clean_text(''.join(root.xpath("//h3[contains(.,'剧情简介')]/following-sibling::*[1]//*[contains(@class,'text-sm')][1]//text()"))) or self._clean_text(((root.xpath("//meta[@name='description']/@content") or [""])[0]))
        vod_year = self._pick_meta_value(html, "年份")
        vod_area = self._pick_meta_value(html, "地区")
        vod_lang = self._pick_meta_value(html, "语言")
        vod_director = ",".join(self._extract_link_texts(html, "导演"))
        vod_actor = ",".join(self._extract_link_texts(html, "主演"))
        tags = self._extract_link_texts(html, "标签")
        line_nodes = root.xpath("//*[@id='originTabs']//a[@href]") or []
        from_list = []
        url_list = []
        for line_node in line_nodes:
            href = ((line_node.xpath("./@href") or [""])[0]).strip()
            name = self._clean_text(
                ((line_node.xpath(".//button[@data-origin]/@data-origin") or [""])[0])
                or ''.join(line_node.xpath(".//text()"))
            )
            line_html = html if self._abs_url(href) == url else self._request_html(self._abs_url(href))
            line_root = self.html(line_html)
            episodes = []
            if line_root is not None:
                for episode in line_root.xpath("//*[contains(@class,'seqlist')]//a[@href]"):
                    ep_href = ((episode.xpath("./@href") or [""])[0]).strip()
                    ep_title = self._clean_text(((episode.xpath("./@data-title") or [""])[0]) or ''.join(episode.xpath('.//text()'))) or "播放"
                    payload = json.dumps(
                        {"title": ep_title, "origin": name, "page": self._abs_url(ep_href), "vodName": vod_name, "pic": vod_pic},
                        ensure_ascii=False,
                    )
                    episodes.append(f"{ep_title}${payload}")
            if episodes:
                from_list.append(name)
                url_list.append("#".join(episodes))
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_content": vod_content,
                    "vod_year": vod_year,
                    "vod_area": vod_area,
                    "vod_lang": vod_lang,
                    "vod_director": vod_director,
                    "vod_actor": vod_actor,
                    "type_name": " / ".join(tags),
                    "vod_play_from": "$$$".join(from_list),
                    "vod_play_url": "$$$".join(url_list),
                }
            ]
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_detail_content_extracts_meta_and_lines -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add py/电影人生.py py/tests/test_电影人生.py
git commit -m "feat: add dyrs detail parsing"
```

### Task 3: Add Search Parsing And Result Refinement

**Files:**
- Modify: `py/tests/test_电影人生.py`
- Modify: `py/电影人生.py`

- [ ] **Step 1: Write the failing test**

```python
SEARCH_HTML = """
<a data-url="/dyrscom-c.html" href="/dyrscom-c.html" title="繁花2023"></a>
<a data-url="/dyrscom-a.html" href="/dyrscom-a.html" title="繁花"></a>
<a data-url="/dyrscom-b.html" href="/dyrscom-b.html" title="阿凡达"></a>
"""

    @patch.object(Spider, "_request_html")
    def test_search_content_refines_exact_match_first(self, mock_html):
        mock_html.return_value = SEARCH_HTML
        result = self.spider.searchContent("繁花", False, "1")
        self.assertEqual([item["vod_name"] for item in result["list"][:2]], ["繁花", "繁花2023"])
        mock_html.assert_called_with("https://dyrsok.com/s.html?name=%E7%B9%81%E8%8A%B1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_search_content_refines_exact_match_first -v`
Expected: FAIL with `AttributeError: 'Spider' object has no attribute 'searchContent'`

- [ ] **Step 3: Write minimal implementation**

```python
    def _normalize_keyword(self, value):
        return re.sub(r"[\\s\\-_—–·•:：,，.。!?！？'\"“”‘’()（）\\[\\]【】{}]", "", str(value or "")).lower()

    def _search_score(self, vod_name, keyword):
        name = self._normalize_keyword(vod_name)
        key = self._normalize_keyword(keyword)
        if not name or not key:
            return 0
        if name == key:
            return 1000
        if name.startswith(key):
            return 800
        if key in name:
            return 600
        return 0

    def _refine_search_results(self, items, keyword):
        scored = []
        for item in items:
            scored.append((self._search_score(item.get("vod_name"), keyword), item))
        matched = [item for score, item in sorted(scored, key=lambda pair: (-pair[0], pair[1].get("vod_name", ""))) if score > 0]
        return matched or items

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        url = self.host + "/s.html?name=" + __import__("urllib.parse").parse.quote(keyword)
        if page > 1:
            url += "&page=" + str(page - 1)
        items = self._parse_vod_cards(self._request_html(url))
        return {"page": page, "total": len(items), "list": self._refine_search_results(items, keyword)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_search_content_refines_exact_match_first -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add py/电影人生.py py/tests/test_电影人生.py
git commit -m "feat: add dyrs search refinement"
```

### Task 4: Add Player Resolution, Redirect Follow, And Fallback

**Files:**
- Modify: `py/tests/test_电影人生.py`
- Modify: `py/电影人生.py`

- [ ] **Step 1: Write the failing test**

```python
    @patch.object(Spider, "_request_html")
    @patch.object(Spider, "_request_response")
    def test_player_content_resolves_api_m3u8_and_raw_playlist(self, mock_response, mock_html):
        mock_html.side_effect = [
            '<script>fetch("/api/m3u8?origin=line1&url=abc123")</script>',
            "#EXTM3U\n/api/m3u8?id=xyz&raw=1\n",
        ]

        class FakeResponse:
            status_code = 302
            headers = {"Location": "https://media.example/master.m3u8"}
            text = ""

        mock_response.return_value = FakeResponse()
        play_id = '{"title":"第1集","origin":"线路一","page":"https://dyrsok.com/dyrscom-foo.html?play=1","vodName":"电影人生示例","pic":"https://dyrsok.com/poster.jpg"}'
        result = self.spider.playerContent("线路一", play_id, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://media.example/api/m3u8?id=xyz&raw=1")

    @patch.object(Spider, "_request_html")
    def test_player_content_falls_back_to_parse_when_no_api_link(self, mock_html):
        mock_html.return_value = "<html><body>empty</body></html>"
        result = self.spider.playerContent("线路一", '{"page":"https://dyrsok.com/dyrscom-foo.html?play=1"}', {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["url"], "https://dyrsok.com/dyrscom-foo.html?play=1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_player_content_resolves_api_m3u8_and_raw_playlist -v`
Expected: FAIL with `AttributeError: 'Spider' object has no attribute 'playerContent'`

- [ ] **Step 3: Write minimal implementation**

```python
    def _request_response(self, url, headers=None, allow_redirects=False):
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        return self.fetch(url, headers=request_headers, timeout=10, verify=False, allow_redirects=allow_redirects)

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if not raw:
            return {"parse": 1, "playUrl": "", "url": "", "header": {}, "jx": 1}
        try:
            meta = json.loads(raw)
        except Exception:
            meta = {"page": raw}
        page_url = self._abs_url(meta.get("page", ""))
        headers = {
            "User-Agent": self.headers["User-Agent"],
            "Referer": page_url or self.host + "/",
            "Origin": self.host,
        }
        html = self._request_html(page_url, headers={"Referer": self.host + "/"}) if page_url else ""
        matched = re.search(r"/api/m3u8\\?origin=([^\"'\\\\\\s&]+|[^\"'\\\\\\s]+?)(&amp;|&)url=([a-zA-Z0-9]+)", html)
        if not matched:
            return {"parse": 1, "playUrl": "", "url": page_url, "header": headers, "jx": 1}
        api_url = self.host + "/api/m3u8?origin=" + matched.group(1) + "&url=" + matched.group(3)
        probe = self._request_response(api_url, headers=headers, allow_redirects=False)
        final_url = api_url
        location = probe.headers.get("Location") or probe.headers.get("location") if hasattr(probe, "headers") else ""
        if location:
            final_url = self._abs_url(location)
            playlist = self._request_html(final_url, headers={"Referer": self.host + "/"})
            raw_line = next((line.strip() for line in playlist.splitlines() if "/api/m3u8?id=" in line and "raw=1" in line), "")
            if raw_line:
                final_url = urljoin(final_url, raw_line)
        return {"parse": 0, "playUrl": "", "url": final_url, "header": headers, "jx": 0}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd py && python -m unittest tests.test_电影人生.TestDYRSSpider.test_player_content_resolves_api_m3u8_and_raw_playlist -v`
Expected: PASS

- [ ] **Step 5: Run module verification**

Run: `cd py && python -m unittest tests.test_电影人生 -v`
Expected: PASS with all tests green

- [ ] **Step 6: Commit**

```bash
git add py/电影人生.py py/tests/test_电影人生.py
git commit -m "feat: add dyrs playback resolution"
```
