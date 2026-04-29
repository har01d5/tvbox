# 双星 Spider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前 Python 仓库中新增独立单站 `双星` 蜘蛛，支持固定分类、cookie 初始化、分类列表、搜索、详情页网盘线路整理和网盘分享链接透传。

**Architecture:** 采用单文件站点脚本 `py/双星.py` 承担全部站点逻辑，内部拆分为 cookie 初始化、请求头生成、HTML 请求、卡片解析、网盘识别和线路组装几个 helper。测试沿用现有 `unittest + SourceFileLoader + mock` 风格，先锁定分类与 cookie 行为，再覆盖列表、搜索、详情和 `playerContent`，全程按 TDD 推进。

**Tech Stack:** Python 3, `unittest`, `unittest.mock`, `sys`, `re`, `urllib.parse`, `base.spider.Spider`

---

## File Structure

- Create: `py/双星.py`
  - 实现 `Spider` 类和站点全部逻辑
  - 暴露 `init`、`getName`、`homeContent`、`homeVideoContent`、`categoryContent`、`searchContent`、`detailContent`、`playerContent`
  - 私有方法负责 cookie 初始化、请求头构建、HTML 请求、文本清洗、卡片解析、网盘识别和播放线路拼装
- Create: `py/tests/test_双星.py`
  - 使用 `SourceFileLoader` 加载 `py/双星.py`
  - 通过内联 HTML 与 `mock` 覆盖分类、cookie、列表、搜索、详情、线路排序和播放透传

### Task 1: Scaffold Spider, Categories, Cookie Init, And Pan Detection

**Files:**
- Create: `py/tests/test_双星.py`
- Create: `py/双星.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("shuangxing_spider", str(ROOT / "双星.py")).load_module()
Spider = MODULE.Spider


class FakeResponse:
    def __init__(self, status_code=200, text="", cookies=None):
        self.status_code = status_code
        self.text = text
        self.cookies = cookies or {}
        self.headers = {}
        self.url = ""


class TestShuangXingSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()

    def test_home_content_exposes_reference_categories(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [(item["type_id"], item["type_name"]) for item in content["class"]],
            [
                ("ju", "国剧"),
                ("zy", "综艺"),
                ("mv", "电影"),
                ("rh", "日韩"),
                ("ym", "英美"),
                ("wj", "外剧"),
                ("dm", "动漫"),
            ],
        )

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    @patch.object(Spider, "fetch")
    def test_init_collects_cookie_pairs_and_headers_include_cookie(self, mock_fetch):
        mock_fetch.return_value = FakeResponse(cookies={"foo": "bar", "token": "xyz"})
        self.spider.init()
        self.assertEqual(self.spider.cookie, "foo=bar; token=xyz")
        self.assertEqual(self.spider._headers()["cookie"], "foo=bar; token=xyz")

    def test_headers_without_cookie_keep_base_headers_only(self):
        self.assertEqual(
            self.spider._headers(),
            {
                "User-Agent": Spider.UA,
                "Referer": Spider.BASE_URL,
            },
        )

    def test_detect_pan_type_returns_expected_keys(self):
        self.assertEqual(self.spider._detect_pan_type("https://pan.quark.cn/s/demo"), "quark")
        self.assertEqual(self.spider._detect_pan_type("https://www.alipan.com/s/demo"), "ali")
        self.assertEqual(self.spider._detect_pan_type("https://example.com/video"), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run from `py/`: `python -m unittest tests.test_双星.TestShuangXingSpider -v`
Expected: FAIL with `FileNotFoundError` for `双星.py` or missing `Spider` attributes.

- [ ] **Step 3: Write minimal implementation**

```python
# coding=utf-8
import re
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    BASE_URL = "https://1.star2.cn"
    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
    )
    CATEGORIES = [
        ("ju", "国剧"),
        ("zy", "综艺"),
        ("mv", "电影"),
        ("rh", "日韩"),
        ("ym", "英美"),
        ("wj", "外剧"),
        ("dm", "动漫"),
    ]

    def __init__(self):
        self.name = "双星"
        self.cookie = ""

    def init(self, extend=""):
        response = self.fetch(
            self.BASE_URL,
            headers={"User-Agent": self.UA, "Referer": self.BASE_URL},
            allow_redirects=False,
            timeout=15,
        )
        if response.status_code != 200:
            return None
        self.cookie = "; ".join([f"{name}={value}" for name, value in dict(response.cookies).items()])
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": [{"type_id": type_id, "type_name": type_name} for type_id, type_name in self.CATEGORIES]}

    def homeVideoContent(self):
        return {"list": []}

    def _headers(self):
        headers = {"User-Agent": self.UA, "Referer": self.BASE_URL}
        if self.cookie:
            headers["cookie"] = self.cookie
        return headers

    def _detect_pan_type(self, link):
        text = str(link or "").strip().lower()
        if "quark" in text:
            return "quark"
        if "115.com" in text:
            return "115"
        if "cloud.189.cn" in text:
            return "tianyi"
        if "drive.uc.cn" in text or "uc.cn" in text:
            return "uc"
        if "pan.baidu.com" in text:
            return "baidu"
        if "xunlei" in text:
            return "xunlei"
        if "123pan" in text:
            return "123pan"
        if "caiyun" in text or "139.com" in text:
            return "yd"
        if "aliyundrive" in text or "alipan" in text:
            return "ali"
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run from `py/`: `python -m unittest tests.test_双星.TestShuangXingSpider -v`
Expected: PASS for the scaffold tests.

- [ ] **Step 5: Commit**

```bash
git add py/双星.py py/tests/test_双星.py
git commit -m "feat: scaffold shuangxing spider"
```

### Task 2: Add Category/Search Requests And Card Parsing

**Files:**
- Modify: `py/tests/test_双星.py`
- Modify: `py/双星.py`

- [ ] **Step 1: Write the failing test**

```python
from urllib.parse import quote


class TestShuangXingSpider(unittest.TestCase):
    @patch.object(Spider, "_get_html")
    def test_category_content_builds_reference_url_and_parses_cards(self, mock_get_html):
        mock_get_html.return_value = """
        <body>
          <div><div><main><div><ul>
            <li><div class="a"><a href="/post/alpha">示例国剧</a></div></li>
            <li><div class="a"><a href="/post/beta">示例综艺</a></div></li>
          </ul></div></main></div></div>
        </body>
        """
        result = self.spider.categoryContent("ju", "3", False, {})
        self.assertEqual(mock_get_html.call_args.args[0], "https://1.star2.cn/ju_3/")
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 15)
        self.assertEqual(result["total"], 32)
        self.assertEqual(
            result["list"],
            [
                {"vod_id": "/post/alpha", "vod_name": "示例国剧", "vod_pic": "", "vod_remarks": ""},
                {"vod_id": "/post/beta", "vod_name": "示例综艺", "vod_pic": "", "vod_remarks": ""},
            ],
        )

    @patch.object(Spider, "_get_html")
    def test_search_content_builds_reference_url_and_parses_results(self, mock_get_html):
        mock_get_html.return_value = """
        <body>
          <div><div><main><div><ul>
            <li><div class="a"><a href="/post/search">搜索结果</a></div></li>
          </ul></div></main></div></div>
        </body>
        """
        result = self.spider.searchContent("繁花", False, "2")
        self.assertEqual(
            mock_get_html.call_args.args[0],
            f"https://1.star2.cn/search/?keyword={quote('繁花')}&page=2",
        )
        self.assertEqual(result["page"], 2)
        self.assertEqual(
            result["list"],
            [{"vod_id": "/post/search", "vod_name": "搜索结果", "vod_pic": "", "vod_remarks": ""}],
        )

    def test_search_content_short_circuits_blank_keyword(self):
        self.assertEqual(self.spider.searchContent("", False, "1"), {"page": 1, "total": 0, "list": []})
```

- [ ] **Step 2: Run test to verify it fails**

Run from `py/`: `python -m unittest tests.test_双星.TestShuangXingSpider -v`
Expected: FAIL with missing `_get_html`, `categoryContent`, `searchContent`, or wrong payload shape.

- [ ] **Step 3: Write minimal implementation**

```python
from urllib.parse import quote


    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _get_html(self, url):
        response = self.fetch(url, headers=self._headers(), timeout=15)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        for node in root.xpath("/html/body/div/div/main/div/ul/li"):
            href = "".join(node.xpath(".//div[contains(@class,'a')]//a[1]/@href")).strip()
            title = self._clean_text("".join(node.xpath(".//div[contains(@class,'a')]//a[1]//text()")))
            if not href or not title:
                continue
            items.append({"vod_id": href, "vod_name": title, "vod_pic": "", "vod_remarks": ""})
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._get_html(f"{self.BASE_URL}/{str(tid).strip()}_{page}/"))
        return {"page": page, "limit": 15, "total": (page - 1) * 15 + len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        items = self._parse_cards(self._get_html(f"{self.BASE_URL}/search/?keyword={quote(keyword)}&page={page}"))
        return {"page": page, "total": len(items), "list": items}
```

- [ ] **Step 4: Run test to verify it passes**

Run from `py/`: `python -m unittest tests.test_双星.TestShuangXingSpider -v`
Expected: PASS for scaffold plus list/search tests.

- [ ] **Step 5: Commit**

```bash
git add py/双星.py py/tests/test_双星.py
git commit -m "feat: add shuangxing list and search parsing"
```

### Task 3: Add Detail Parsing, Play-Line Assembly, And Player Passthrough

**Files:**
- Modify: `py/tests/test_双星.py`
- Modify: `py/双星.py`

- [ ] **Step 1: Write the failing test**

```python
class TestShuangXingSpider(unittest.TestCase):
    @patch.object(Spider, "_get_html")
    def test_detail_content_extracts_title_and_sorted_deduplicated_pan_lines(self, mock_get_html):
        mock_get_html.return_value = """
        <body>
          <div>
            <div class="s20erx erx-m-bot erx-content">
              <main><article><h1>双星示例</h1></article></main>
            </div>
          </div>
          <div id="maximg">
            <div class="dlipp-cont-wp"><div><div class="dlipp-cont-bd">
              <a href="https://pan.baidu.com/s/b-demo"></a>
              <a href="https://pan.quark.cn/s/q-demo"></a>
              <a href="https://pan.baidu.com/s/b-demo"></a>
              <a href="https://example.com/ignored"></a>
            </div></div></div>
          </div>
        </body>
        """
        result = self.spider.detailContent(["/post/demo"])
        self.assertEqual(mock_get_html.call_args.args[0], "https://1.star2.cn/post/demo")
        self.assertEqual(
            result,
            {
                "list": [
                    {
                        "vod_id": "/post/demo",
                        "vod_name": "双星示例",
                        "vod_pic": "",
                        "vod_remarks": "",
                        "vod_content": "",
                        "vod_director": "",
                        "vod_actor": "",
                        "vod_play_from": "quark$$$baidu",
                        "vod_play_url": "夸克资源$https://pan.quark.cn/s/q-demo$$$百度资源$https://pan.baidu.com/s/b-demo",
                    }
                ]
            },
        )

    @patch.object(Spider, "_get_html")
    def test_detail_content_returns_empty_list_for_blank_html(self, mock_get_html):
        mock_get_html.return_value = ""
        self.assertEqual(self.spider.detailContent(["/post/missing"]), {"list": []})

    def test_player_content_passthroughs_supported_pan_links(self):
        self.assertEqual(
            self.spider.playerContent("quark", "https://pan.quark.cn/s/demo", {}),
            {"parse": 0, "playUrl": "", "url": "https://pan.quark.cn/s/demo"},
        )

    def test_player_content_rejects_unknown_links(self):
        self.assertEqual(
            self.spider.playerContent("site", "https://example.com/video", {}),
            {"parse": 0, "playUrl": "", "url": ""},
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run from `py/`: `python -m unittest tests.test_双星.TestShuangXingSpider -v`
Expected: FAIL with missing `detailContent`, `playerContent`, or wrong `vod_play_from` / `vod_play_url`.

- [ ] **Step 3: Write minimal implementation**

```python
from urllib.parse import urljoin


    PAN_TITLES = {
        "quark": "夸克资源",
        "ali": "阿里资源",
        "115": "115资源",
        "tianyi": "天翼资源",
        "uc": "UC资源",
        "baidu": "百度资源",
        "xunlei": "迅雷资源",
        "123pan": "123资源",
        "yd": "移动云盘资源",
    }
    PAN_ORDER = ["quark", "ali", "115", "tianyi", "uc", "baidu", "xunlei", "123pan", "yd"]

    def _build_pan_lines(self, share_links):
        groups = {}
        seen = set()
        for link in share_links:
            raw = str(link or "").strip()
            pan_type = self._detect_pan_type(raw)
            if not raw or not pan_type or raw in seen:
                continue
            seen.add(raw)
            groups.setdefault(pan_type, []).append(f"{self.PAN_TITLES[pan_type]}${raw}")
        if not groups:
            return {"vod_play_from": "", "vod_play_url": ""}
        names = [name for name in self.PAN_ORDER if name in groups]
        return {
            "vod_play_from": "$$$".join(names),
            "vod_play_url": "$$$".join("#".join(groups[name]) for name in names),
        }

    def detailContent(self, ids):
        vod_id = str((ids or [""])[0] or "").strip()
        if not vod_id:
            return {"list": []}
        html = self._get_html(urljoin(self.BASE_URL, vod_id))
        root = self.html(html)
        if root is None:
            return {"list": []}
        title = self._clean_text(
            "".join(root.xpath("/html/body/div/div[contains(@class,'s20erx') and contains(@class,'erx-content')]/main/article/h1//text()"))
        )
        share_links = [
            str(value).strip()
            for value in root.xpath("//*[@id='maximg']//div[contains(@class,'dlipp-cont-bd')]//a[@href]/@href")
        ]
        play = self._build_pan_lines(share_links)
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": "",
                    "vod_remarks": "",
                    "vod_content": "",
                    "vod_director": "",
                    "vod_actor": "",
                    "vod_play_from": play["vod_play_from"],
                    "vod_play_url": play["vod_play_url"],
                }
            ]
        }

    def playerContent(self, flag, id, vipFlags):
        target = str(id or "").strip()
        if self._detect_pan_type(target):
            return {"parse": 0, "playUrl": "", "url": target}
        return {"parse": 0, "playUrl": "", "url": ""}
```

- [ ] **Step 4: Run test to verify it passes**

Run from `py/`: `python -m unittest tests.test_双星.TestShuangXingSpider -v`
Expected: PASS for the complete `tests.test_双星` suite.

- [ ] **Step 5: Commit**

```bash
git add py/双星.py py/tests/test_双星.py
git commit -m "feat: complete shuangxing spider"
```
