# LibVIO Spider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的 LibVIO 爬虫，支持 `home/category/detail/search/player` 全链路。

**Architecture:** 采用单文件站点脚本 `libvio.py` 承担 LibVIO 规则，内部拆分为 URL 归一化、列表卡片解析、详情字段解析、播放配置提取与播放器 API 解析几组辅助方法。测试沿用当前仓库 `unittest + SourceFileLoader + mock` 风格，优先覆盖纯解析函数和高层方法的 mock 网络流程，不依赖真实站点网络。

**Tech Stack:** Python 3, `requests`, `lxml`, `unittest`, `unittest.mock`, `json`, `re`, `urllib.parse`

---

## File Structure

- Create: `libvio.py`
  - LibVIO 站点实现，继承 `base.spider.Spider`
  - 暴露 `init`、`homeContent`、`homeVideoContent`、`categoryContent`、`detailContent`、`searchContent`、`playerContent`
  - 私有方法负责 URL/ID 归一化、列表卡片解析、详情解析、播放配置与 API 解析
- Create: `tests/test_libvio.py`
  - 用 `SourceFileLoader` 加载 `libvio.py`
  - 用 HTML/JS 片段与 mock response 测试首页、分类、搜索、详情和播放器解析

### Task 1: Scaffold Spider, Home Flow, And List/Search Parsing

**Files:**
- Create: `tests/test_libvio.py`
- Create: `libvio.py`

- [ ] **Step 1: Write the failing test**

```python
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
            [{
                "vod_id": "456",
                "vod_name": "示例影片",
                "vod_pic": "https://libvio.site/cover.jpg",
                "vod_remarks": "更新至10集",
            }],
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_libvio.TestLibVioSpider -v`
Expected: FAIL with `FileNotFoundError` for `libvio.py` or missing methods.

- [ ] **Step 3: Write minimal implementation**

```python
# coding=utf-8
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "LibVIO"
        self.host = "https://libvio.site"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.categories = [
            {"type_name": "最近更新", "type_id": "index"},
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "电视剧", "type_id": "series"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "日韩剧", "type_id": "jpandkr"},
            {"type_name": "欧美剧", "type_id": "euandus"},
        ]
        self.category_paths = {
            "index": "/",
            "movie": "/type/1-{pg}.html",
            "series": "/type/2-{pg}.html",
            "anime": "/type/4-{pg}.html",
            "jpandkr": "/type/15-{pg}.html",
            "euandus": "/type/16-{pg}.html",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def _build_url(self, href):
        raw = str(href or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return self.host + "/" + raw.lstrip("/")

    def _extract_vod_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/detail/(\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"\d+", raw):
            return raw
        return ""

    def _parse_list_cards(self, html):
        root = self.html(html)
        results = []
        if root is None:
            return results
        for card in root.xpath("//*[contains(@class,'stui-vodlist__box')]"):
            href = ((card.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            vod_id = self._extract_vod_id(href)
            title = ((card.xpath(".//a[@title][1]/@title") or [""])[0]).strip()
            pic = (
                (card.xpath(".//a[@data-original][1]/@data-original") or [""])[0].strip()
                or (card.xpath(".//img[@data-original][1]/@data-original") or [""])[0].strip()
                or (card.xpath(".//img[@src][1]/@src") or [""])[0].strip()
            )
            remarks = "".join(card.xpath(".//*[contains(@class,'pic-text')][1]//text()")).strip()
            if not vod_id or not title:
                continue
            results.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": self._build_url(pic),
                "vod_remarks": remarks,
            })
        return results

    def _request_html(self, path_or_url, expect_xpath=None, referer=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or (self.host + "/")
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _page_result(self, items, pg):
        page = int(pg)
        pagecount = page + 1 if items else page
        return {"list": items, "page": page, "pagecount": pagecount, "limit": len(items), "total": pagecount * max(len(items), 1)}

    def homeVideoContent(self):
        html = self._request_html("/", expect_xpath="//*[contains(@class,'stui-vodlist__box')]")
        return {"list": self._parse_list_cards(html)}

    def categoryContent(self, tid, pg, filter, extend):
        path = self.category_paths.get(tid, self.category_paths["movie"]).format(pg=pg)
        html = self._request_html(path, expect_xpath="//*[contains(@class,'stui-vodlist__box')]")
        return self._page_result(self._parse_list_cards(html), pg)

    def searchContent(self, key, quick, pg="1"):
        path = "/search/-------------.html?wd={0}".format(quote(key))
        html = self._request_html(path, expect_xpath="//*[contains(@class,'stui-vodlist__box')]")
        return self._page_result(self._parse_list_cards(html), pg)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_libvio.TestLibVioSpider -v`
Expected: PASS for the five new tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_libvio.py libvio.py
git commit -m "feat: scaffold libvio list parsing"
```

### Task 2: Add Detail Parsing And Compact Play IDs

**Files:**
- Modify: `tests/test_libvio.py`
- Modify: `libvio.py`

- [ ] **Step 1: Write the failing test**

```python
class TestLibVioSpider(unittest.TestCase):
    def test_parse_detail_page_extracts_fields_and_filters_pan_sources(self):
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
        """
        result = self.spider._parse_detail_page(html, "999")
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "999")
        self.assertEqual(vod["path"], "https://libvio.site/detail/999.html")
        self.assertEqual(vod["vod_name"], "示例剧")
        self.assertEqual(vod["type_name"], "剧情")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_year"], "2026")
        self.assertEqual(vod["vod_director"], "张三")
        self.assertEqual(vod["vod_actor"], "李四,王五")
        self.assertEqual(vod["vod_content"], "一段剧情简介")
        self.assertEqual(vod["vod_play_from"], "LibVIO")
        self.assertEqual(vod["vod_play_url"], "第1集$999-1-1#第2集$999-1-2")

    @patch.object(Spider, "_request_html")
    def test_detail_content_builds_detail_request_url_from_vod_id(self, mock_request_html):
        mock_request_html.return_value = '<h1 class="title">详情影片</h1><ul class="stui-content__playlist"><li><a href="/play/123-1-1.html">第1集</a></li></ul>'
        result = self.spider.detailContent(["123"])
        self.assertEqual(mock_request_html.call_args.args[0], "https://libvio.site/detail/123.html")
        self.assertEqual(result["list"][0]["vod_id"], "123")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_libvio.TestLibVioSpider.test_parse_detail_page_extracts_fields_and_filters_pan_sources tests.test_libvio.TestLibVioSpider.test_detail_content_builds_detail_request_url_from_vod_id -v`
Expected: FAIL with missing `_parse_detail_page`, `detailContent`, or incorrect field values.

- [ ] **Step 3: Write minimal implementation**

```python
    def _extract_play_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/play/([^./]+-\d+-\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"[^./]+-\d+-\d+", raw):
            return raw
        return ""

    def _build_detail_request_url(self, vod_id):
        return f"{self.host}/detail/{self._extract_vod_id(vod_id)}.html"

    def _build_play_request_url(self, play_id):
        return f"{self.host}/play/{self._extract_play_id(play_id)}.html"

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _extract_detail_field(self, root, label, joiner=""):
        nodes = root.xpath(f'.//span[contains(normalize-space(.), "{label}：")]')
        if not nodes:
            return ""
        values = []
        for sibling in nodes[0].itersiblings():
            if sibling.tag == "span" and "text-muted" in " ".join(sibling.xpath("./@class")):
                break
            text = self._clean_text("".join(sibling.xpath(".//text()")))
            if text:
                values.append(text)
        values = [value for index, value in enumerate(values) if value and value not in values[:index]]
        return joiner.join(values) if joiner else "".join(values)

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        detail_root = (root.xpath("//*[contains(@class,'stui-content__detail')][1]") or [root])[0]
        title = ((detail_root.xpath(".//*[contains(@class,'title')][1]//text()") or [""])[0]).strip()
        pic = (
            (root.xpath("//*[contains(@class,'stui-content__thumb')]//img/@data-original") or [""])[0].strip()
            or (root.xpath("//*[contains(@class,'stui-content__thumb')]//img/@src") or [""])[0].strip()
        )
        episodes = []
        for playlist in root.xpath("//*[contains(@class,'stui-content__playlist')]"):
            heading = self._clean_text("".join(playlist.xpath("./preceding-sibling::*[1]//text()")))
            if any(keyword in heading for keyword in ("夸克", "UC", "网盘")):
                continue
            for anchor in playlist.xpath(".//a[@href]"):
                play_id = self._extract_play_id((anchor.xpath("./@href") or [""])[0])
                name = self._clean_text("".join(anchor.xpath(".//text()")))
                if play_id and name:
                    episodes.append(f"{name}${play_id}")
        vod = {
            "vod_id": vod_id,
            "path": self._build_detail_request_url(vod_id),
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_tag": "",
            "vod_time": "",
            "vod_remarks": "",
            "vod_play_from": "LibVIO",
            "vod_play_url": "#".join(episodes),
            "type_name": self._extract_detail_field(detail_root, "类型"),
            "vod_content": self._extract_detail_field(detail_root, "简介"),
            "vod_year": self._extract_detail_field(detail_root, "年份"),
            "vod_area": self._extract_detail_field(detail_root, "地区"),
            "vod_lang": "",
            "vod_director": self._extract_detail_field(detail_root, "导演", joiner=","),
            "vod_actor": self._extract_detail_field(detail_root, "主演", joiner=","),
        }
        return {"list": [vod]}

    def detailContent(self, ids):
        vod_id = ids[0]
        html = self._request_html(self._build_detail_request_url(vod_id), expect_xpath="//*[contains(@class,'stui-content__playlist')]")
        return self._parse_detail_page(html, vod_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_libvio.TestLibVioSpider.test_parse_detail_page_extracts_fields_and_filters_pan_sources tests.test_libvio.TestLibVioSpider.test_detail_content_builds_detail_request_url_from_vod_id -v`
Expected: PASS for the two new tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_libvio.py libvio.py
git commit -m "feat: add libvio detail parsing"
```

### Task 3: Add Player Config Parsing And Final URL Resolution

**Files:**
- Modify: `tests/test_libvio.py`
- Modify: `libvio.py`

- [ ] **Step 1: Write the failing test**

```python
class TestLibVioSpider(unittest.TestCase):
    def test_extract_player_config_reads_json_assignment(self):
        html = '<script>var player_aaaa={"url":"abc","from":"line","id":"1","nid":"2"};</script>'
        data = self.spider._parse_player_config(html)
        self.assertEqual(data["from"], "line")

    def test_extract_play_api_base_reads_player_js(self):
        body = 'var player={}; src="/player/api.php?url=";'
        self.assertEqual(self.spider._extract_play_api_base(body), "https://libvio.site/player/api.php?url=")

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
        self.assertEqual(result["header"]["Referer"], "https://libvio.site/")

    @patch.object(Spider, "_request_html")
    def test_player_content_returns_empty_for_pan_source(self, mock_request_html):
        mock_request_html.return_value = '<script>var player_x={"url":"abc","from":"kuake"};</script>'
        self.assertEqual(self.spider.playerContent("LibVIO", "999-1-1", {}), {"parse": 0, "playUrl": "", "url": ""})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_libvio.TestLibVioSpider.test_extract_player_config_reads_json_assignment tests.test_libvio.TestLibVioSpider.test_extract_play_api_base_reads_player_js tests.test_libvio.TestLibVioSpider.test_player_content_resolves_direct_api_url tests.test_libvio.TestLibVioSpider.test_player_content_returns_empty_for_pan_source -v`
Expected: FAIL with missing player helpers or unresolved final URL.

- [ ] **Step 3: Write minimal implementation**

```python
import json

    def _parse_player_config(self, html):
        matched = re.search(r"player_[a-z0-9_]+\s*=\s*(\{[\s\S]*?\})\s*;?", html, re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _extract_play_api_base(self, body):
        matched = re.search(r'src\s*=\s*["\']([^"\']+)["\']', body, re.I)
        if not matched:
            return ""
        return self._build_url(matched.group(1))

    def _extract_playable_url(self, body):
        patterns = [
            r'["\']?urls?["\']?\s*:\s*["\']([^"\']+)["\']',
            r'(?:var|let|const)\s+urls?\s*=\s*["\']([^"\']+)["\']',
            r'["\']url["\']\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'url\s*=\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
        ]
        for pattern in patterns:
            matched = re.search(pattern, body, re.I)
            if matched:
                return self._build_url(matched.group(1).replace("\\/", "/").replace("&amp;", "&"))
        return ""

    def _request_player_js(self, source):
        return self._request_html(f"/static/player/{source}.js", referer=self.host + "/")

    def playerContent(self, flag, id, vipFlags):
        play_page_url = self._build_play_request_url(id)
        detail_html = self._request_html(play_page_url, referer=self.host + "/")
        config = self._parse_player_config(detail_html)
        if not config or config.get("from") in ("kuake", "uc"):
            return {"parse": 0, "playUrl": "", "url": ""}
        if config.get("from") == "ty_new1":
            api_body = self._request_html(f"/vid/ty4.php?url={config.get('url', '')}", referer=self.host + "/")
            final_url = self._extract_playable_url(api_body)
        else:
            player_js = self._request_player_js(config.get("from", ""))
            api_base = self._extract_play_api_base(player_js)
            api_url = "{base}{url}&next={next}&id={id}&nid={nid}".format(
                base=api_base,
                url=config.get("url", ""),
                next=config.get("link_next", ""),
                id=config.get("id", ""),
                nid=config.get("nid", ""),
            )
            api_body = self._request_html(api_url, referer=self.host + "/")
            final_url = self._extract_playable_url(api_body)
        if not final_url:
            return {"parse": 0, "playUrl": "", "url": ""}
        return {
            "parse": 0,
            "playUrl": "",
            "url": final_url,
            "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"},
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_libvio.TestLibVioSpider.test_extract_player_config_reads_json_assignment tests.test_libvio.TestLibVioSpider.test_extract_play_api_base_reads_player_js tests.test_libvio.TestLibVioSpider.test_player_content_resolves_direct_api_url tests.test_libvio.TestLibVioSpider.test_player_content_returns_empty_for_pan_source -v`
Expected: PASS for the four new tests.

- [ ] **Step 5: Run the full suite**

Run: `python -m unittest tests.test_libvio -v`
Expected: PASS with all `libvio` tests green.

- [ ] **Step 6: Commit**

```bash
git add tests/test_libvio.py libvio.py
git commit -m "feat: add libvio player parsing"
```
