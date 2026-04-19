# 乌云影视 Spider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的乌云影视爬虫，支持 `home/homeVideo/category/detail/search/player` 全链路。

**Architecture:** 采用单文件站点脚本 `乌云影视.py` 承担乌云影视的 JSON API 适配逻辑，内部拆分为请求封装、分类与筛选构造、列表映射、详情聚合、播放载荷编解码与剧集回查几个 helper。测试沿用当前仓库 `unittest + SourceFileLoader + mock` 风格，优先覆盖纯函数与高层 mock 网络流程，不依赖真实站点网络。

**Tech Stack:** Python 3, `requests`, `unittest`, `unittest.mock`, `json`, `base64`, `math`, `urllib.parse`, `base.spider.Spider`

---

## File Structure

- Create: `乌云影视.py`
  - 乌云影视站点实现，继承 `base.spider.Spider`
  - 暴露 `init`、`homeContent`、`homeVideoContent`、`categoryContent`、`detailContent`、`searchContent`、`playerContent`
  - 私有方法负责 JSON 请求、分类筛选构造、列表映射、详情聚合、播放载荷编解码、剧集直链回查
- Create: `tests/test_乌云影视.py`
  - 用 `SourceFileLoader` 加载 `乌云影视.py`
  - 用 mock JSON 返回覆盖首页、分类、详情、搜索和播放解析

### Task 1: Scaffold Spider, Request Helpers, And Menu Parsing

**Files:**
- Create: `tests/test_乌云影视.py`
- Create: `乌云影视.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("wooyun_spider", str(ROOT / "乌云影视.py")).load_module()
Spider = MODULE.Spider


class TestWooyunSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def test_home_content_builds_classes_and_filters_from_menu(self):
        menu = [
            {"code": "movie", "name": "电影"},
            {"code": "tv_series", "name": "电视剧"},
            {"code": "animation", "name": "动画"},
            {"code": "variety", "name": "综艺"},
            {"code": "short_drama", "name": "短剧"},
            {
                "nameEn": "year",
                "children": [
                    {"code": "THIS_YEAR", "name": "今年"},
                    {"code": "LAST_YEAR", "name": "去年"},
                    {"code": "2024", "name": "2024"},
                ],
            },
            {
                "nameEn": "region",
                "children": [{"code": "CN", "name": "大陆"}],
            },
            {
                "nameEn": "genre",
                "children": [{"code": "COMEDY", "name": "喜剧"}],
            },
            {
                "nameEn": "language",
                "children": [{"code": "ZH", "name": "国语"}],
            },
        ]

        self.spider._request_json = lambda path, method="GET", data=None, headers=None: menu
        content = self.spider.homeContent(False)

        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["movie", "tv_series", "animation", "variety", "short_drama", "THIS_YEAR", "LAST_YEAR"],
        )
        self.assertEqual(content["filters"]["movie"][0]["key"], "year")
        self.assertEqual(content["filters"]["movie"][1]["key"], "region")
        self.assertEqual(content["filters"]["movie"][2]["key"], "genre")
        self.assertEqual(content["filters"]["movie"][3]["key"], "lang")
        self.assertEqual(content["filters"]["movie"][4]["key"], "sort")

    def test_request_json_uses_post_for_json_payload(self):
        calls = {}

        class FakeResponse:
            def __init__(self):
                self.status_code = 200
                self.text = ""

            def json(self):
                return {"data": {"records": []}}

        def fake_post(url, json=None, headers=None, timeout=5, verify=True, stream=False, allow_redirects=True, params=None, data=None, cookies=None):
            calls["url"] = url
            calls["json"] = json
            calls["headers"] = headers
            return FakeResponse()

        self.spider.post = fake_post
        result = self.spider._request_json(
            "/movie/media/search",
            method="POST",
            data={"pageIndex": "1"},
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(calls["url"], "https://wooyun.tv/movie/media/search")
        self.assertEqual(calls["json"], {"pageIndex": "1"})
        self.assertEqual(calls["headers"]["Origin"], "https://wooyun.tv")
        self.assertEqual(result, {"records": []})

    def test_build_category_body_handles_year_shortcuts_and_filters(self):
        body = self.spider._build_category_body(
            "THIS_YEAR",
            "3",
            {"region": "CN", "year": "2025", "lang": "ZH", "sort": "hot"},
        )
        self.assertEqual(body["menuCodeList"], ["THIS_YEAR", "CN", "2025", "ZH"])
        self.assertEqual(body["pageIndex"], "3")
        self.assertEqual(body["sortCode"], "hot")
        self.assertEqual(body["topCode"], "movie")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: FAIL with `FileNotFoundError` for `乌云影视.py` or missing `Spider` attributes.

- [ ] **Step 3: Write minimal implementation**

```python
# coding=utf-8
import base64
import json
import math
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "乌云影视"
        self.host = "https://wooyun.tv"
        self.page_size = 24
        self.home_limit = 12
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": self.host,
            "Referer": self.host + "/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        self.sort_options = [
            {"n": "默认", "v": "default"},
            {"n": "最新", "v": "latest"},
            {"n": "最热", "v": "hot"},
            {"n": "评分", "v": "score"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _ensure_list(self, value):
        return value if isinstance(value, list) else []

    def _normalize_ext(self, extend):
        if isinstance(extend, dict):
            return extend
        if not extend:
            return {}
        try:
            return json.loads(str(extend))
        except Exception:
            return {}

    def _full_url(self, path):
        raw = self._stringify(path).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _request_json(self, path, method="GET", data=None, headers=None):
        url = path if str(path).startswith("http") else self.host + path
        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)

        if method == "POST":
            response = self.post(url, json=data, headers=merged_headers, timeout=15)
        else:
            response = self.fetch(url, headers=merged_headers, timeout=15)

        if response.status_code < 200 or response.status_code >= 300:
            raise ValueError(f"{method} {path} => HTTP {response.status_code}")

        payload = response.json()
        if payload.get("code") not in (None, 200) and payload.get("isSuccess") is False:
            raise ValueError(payload.get("resultMsg") or str(payload.get("code")))
        return payload.get("data")

    def _build_classes(self, menu):
        classes = []
        for code, fallback in [
            ("movie", "电影"),
            ("tv_series", "电视剧"),
            ("animation", "动画"),
            ("variety", "综艺"),
            ("short_drama", "短剧"),
        ]:
            found = next((item for item in self._ensure_list(menu) if item.get("code") == code), None)
            classes.append({"type_id": code, "type_name": self._stringify((found or {}).get("name") or fallback)})

        year_group = next((item for item in self._ensure_list(menu) if item.get("nameEn") == "year"), {})
        year_children = self._ensure_list(year_group.get("children"))
        this_year = next((item for item in year_children if item.get("code") == "THIS_YEAR"), {})
        last_year = next((item for item in year_children if item.get("code") == "LAST_YEAR"), {})
        classes.append({"type_id": "THIS_YEAR", "type_name": self._stringify(this_year.get("name") or "今年")})
        classes.append({"type_id": "LAST_YEAR", "type_name": self._stringify(last_year.get("name") or "去年")})
        return classes

    def _build_filters(self, menu, classes):
        option_map = {"genre": [], "region": [], "year": [], "language": []}
        for group in self._ensure_list(menu):
            values = []
            for item in self._ensure_list(group.get("children")):
                code = self._stringify(item.get("code"))
                name = self._stringify(item.get("name") or item.get("nameEn") or code)
                if code and name and code not in ("THIS_YEAR", "LAST_YEAR"):
                    values.append({"n": name, "v": code})
            if group.get("nameEn") in option_map:
                option_map[group.get("nameEn")] = values

        filters = {}
        for cls in classes:
            items = []
            if option_map["year"]:
                items.append({"key": "year", "name": "年份", "init": "", "value": [{"n": "全部", "v": ""}] + option_map["year"]})
            if option_map["region"]:
                items.append({"key": "region", "name": "地区", "init": "", "value": [{"n": "全部", "v": ""}] + option_map["region"]})
            if option_map["genre"] and cls["type_id"] in ("movie", "tv_series", "animation", "variety", "short_drama"):
                items.append({"key": "genre", "name": "类型", "init": "", "value": [{"n": "全部", "v": ""}] + option_map["genre"]})
            if option_map["language"]:
                items.append({"key": "lang", "name": "语言", "init": "", "value": [{"n": "全部", "v": ""}] + option_map["language"]})
            items.append({"key": "sort", "name": "排序", "init": "default", "value": self.sort_options})
            filters[cls["type_id"]] = items
        return filters

    def _map_top_code(self, category_id):
        mapping = {
            "movie": "movie",
            "tv_series": "tv_series",
            "animation": "animation",
            "variety": "variety",
            "short_drama": "short_drama",
            "THIS_YEAR": "movie",
            "LAST_YEAR": "movie",
        }
        return mapping.get(category_id, "movie")

    def _build_category_body(self, category_id, page, extend):
        filters = self._normalize_ext(extend)
        menu_code_list = []
        if category_id not in ("movie", "tv_series", "animation", "variety", "short_drama"):
            menu_code_list.append(category_id)
        for key in ("genre", "region", "year", "lang", "other"):
            value = self._stringify(filters.get(key))
            if value and value not in menu_code_list:
                menu_code_list.append(value)
        return {
            "menuCodeList": menu_code_list,
            "pageIndex": self._stringify(page or 1),
            "pageSize": self.page_size,
            "searchKey": "",
            "sortCode": "" if filters.get("sort") in (None, "", "default") else self._stringify(filters.get("sort")),
            "topCode": self._map_top_code(category_id),
        }

    def homeContent(self, filter):
        menu = self._request_json("/movie/category/menu")
        classes = self._build_classes(menu)
        return {"class": classes, "filters": self._build_filters(menu, classes)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: PASS for the three new tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_乌云影视.py 乌云影视.py
git commit -m "feat: scaffold wooyun spider menu parsing"
```

### Task 2: Add Home Video, Category, And Search Flows

**Files:**
- Modify: `tests/test_乌云影视.py`
- Modify: `乌云影视.py`

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import patch


class TestWooyunSpider(unittest.TestCase):
    def test_extract_home_list_deduplicates_media_resources(self):
        home_blocks = {
            "records": [
                {
                    "mediaResources": [
                        {"id": 1, "title": "影片A", "posterUrl": "/a.jpg"},
                        {"id": 1, "title": "影片A", "posterUrl": "/a.jpg"},
                    ]
                },
                {
                    "mediaResources": [
                        {"id": 2, "title": "影片B", "posterUrlS3": "https://img.example/b.jpg"},
                    ]
                },
            ]
        }
        items = self.spider._extract_home_list(home_blocks)
        self.assertEqual([item["id"] for item in items], ["1", "2"])

    def test_map_vod_picks_expected_fields(self):
        item = {
            "id": 7,
            "title": "示例片",
            "posterUrl": "/poster.jpg",
            "mediaType": {"code": "movie", "name": "电影"},
            "episodeStatus": "更新至4集",
            "releaseYear": "2026",
            "rating": "8.8",
            "actors": ["甲", "乙"],
            "directors": ["丙"],
        }
        vod = self.spider._map_vod(item)
        self.assertEqual(vod["vod_id"], "7")
        self.assertEqual(vod["vod_pic"], "/poster.jpg")
        self.assertEqual(vod["vod_actor"], "甲/乙")
        self.assertEqual(vod["vod_director"], "丙")

    @patch.object(Spider, "_request_json")
    def test_home_video_content_reads_home_blocks(self, mock_request_json):
        mock_request_json.return_value = {
            "records": [
                {"mediaResources": [{"id": 1, "title": "首页片", "posterUrl": "/a.jpg"}]}
            ]
        }
        result = self.spider.homeVideoContent()
        self.assertEqual(result["list"][0]["vod_id"], "1")
        self.assertEqual(result["list"][0]["vod_name"], "首页片")

    @patch.object(Spider, "_request_json")
    def test_category_content_posts_search_body_and_returns_page_data(self, mock_request_json):
        mock_request_json.return_value = {
            "records": [{"id": 9, "title": "分类片", "posterUrl": "/cate.jpg"}],
            "total": 30,
            "pages": 2,
        }
        result = self.spider.categoryContent("movie", "2", False, {"sort": "latest"})
        kwargs = mock_request_json.call_args.kwargs
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["data"]["pageIndex"], "2")
        self.assertEqual(kwargs["data"]["sortCode"], "latest")
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["pagecount"], 2)
        self.assertEqual(result["limit"], 24)
        self.assertEqual(result["total"], 30)

    @patch.object(Spider, "_request_json")
    def test_search_content_returns_empty_result_for_blank_keyword(self, mock_request_json):
        result = self.spider.searchContent("", False, "1")
        self.assertEqual(result, {"page": 1, "pagecount": 0, "total": 0, "list": []})
        mock_request_json.assert_not_called()

    @patch.object(Spider, "_request_json")
    def test_search_content_posts_keyword_body(self, mock_request_json):
        mock_request_json.return_value = {
            "records": [{"id": 15, "title": "搜索片", "posterUrl": "/search.jpg"}],
            "total": 1,
            "pages": 1,
        }
        result = self.spider.searchContent("繁花", False, "1")
        body = mock_request_json.call_args.kwargs["data"]
        self.assertEqual(body["searchKey"], "繁花")
        self.assertEqual(body["topCode"], "")
        self.assertEqual(result["list"][0]["vod_id"], "15")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: FAIL with missing `_extract_home_list` / `_map_vod` / `homeVideoContent` / `categoryContent` / `searchContent`.

- [ ] **Step 3: Write minimal implementation**

```python
    def _join_text(self, value):
        return "/".join([self._stringify(item) for item in self._ensure_list(value) if self._stringify(item)])

    def _pick_poster(self, item):
        return self._stringify(
            item.get("posterUrlS3") or item.get("posterUrl") or item.get("thumbUrlS3") or item.get("thumbUrl")
        )

    def _extract_home_list(self, home_blocks):
        blocks = self._ensure_list((home_blocks or {}).get("records") if isinstance(home_blocks, dict) else home_blocks)
        seen = set()
        items = []
        for block in blocks:
            for item in self._ensure_list(block.get("mediaResources")):
                vod_id = self._stringify(item.get("id"))
                if not vod_id or vod_id in seen:
                    continue
                seen.add(vod_id)
                copied = dict(item)
                copied["id"] = vod_id
                items.append(copied)
        return items

    def _map_vod(self, item):
        return {
            "vod_id": self._stringify(item.get("id")),
            "vod_name": self._stringify(item.get("title")),
            "vod_pic": self._pick_poster(item),
            "type_id": self._stringify((item.get("mediaType") or {}).get("code")),
            "type_name": self._stringify((item.get("mediaType") or {}).get("name")),
            "vod_remarks": self._stringify(item.get("episodeStatus") or item.get("remark")),
            "vod_year": self._stringify(item.get("releaseYear")),
            "vod_douban_score": self._stringify(item.get("rating")),
            "vod_actor": self._join_text(item.get("actors")),
            "vod_director": self._join_text(item.get("directors")),
        }

    def homeVideoContent(self):
        data = self._request_json(f"/movie/media/home/custom/classify/1/3?limit={self.home_limit}")
        return {"list": [self._map_vod(item) for item in self._extract_home_list(data)[: self.home_limit]]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        data = self._request_json(
            "/movie/media/search",
            method="POST",
            data=self._build_category_body(self._stringify(tid or "movie"), page, extend),
            headers={"Content-Type": "application/json"},
        ) or {}
        records = [self._map_vod(item) for item in self._ensure_list(data.get("records"))]
        total = int(data.get("total") or 0)
        pagecount = int(data.get("pages") or (math.ceil(total / self.page_size) if total else (page if records else 0)))
        return {"page": page, "pagecount": pagecount, "limit": self.page_size, "total": total, "list": records}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._stringify(key).strip()
        if not keyword:
            return {"page": page, "pagecount": 0, "total": 0, "list": []}

        data = self._request_json(
            "/movie/media/search",
            method="POST",
            data={
                "menuCodeList": [],
                "pageIndex": self._stringify(page),
                "pageSize": self.page_size,
                "searchKey": keyword,
                "sortCode": "",
                "topCode": "",
            },
            headers={"Content-Type": "application/json"},
        ) or {}
        records = [self._map_vod(item) for item in self._ensure_list(data.get("records"))]
        total = int(data.get("total") or 0)
        pagecount = int(data.get("pages") or (math.ceil(total / self.page_size) if total else (page if records else 0)))
        return {"page": page, "pagecount": pagecount, "total": total, "list": records}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: PASS for the new home/category/search tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_乌云影视.py 乌云影视.py
git commit -m "feat: add wooyun list and search flows"
```

### Task 3: Add Detail Aggregation And Multi-Season Playlists

**Files:**
- Modify: `tests/test_乌云影视.py`
- Modify: `乌云影视.py`

- [ ] **Step 1: Write the failing test**

```python
class TestWooyunSpider(unittest.TestCase):
    def test_build_play_sources_encodes_multiple_seasons(self):
        seasons = [
            {
                "seasonNo": 1,
                "videoList": [
                    {"id": 101, "epNo": 1, "remark": "", "playUrl": "/play-1.m3u8"},
                    {"id": 102, "epNo": 2, "remark": "加更", "playUrl": "/play-2.m3u8"},
                ],
            },
            {
                "seasonNo": 2,
                "videoList": [
                    {"id": 201, "epNo": 1, "remark": "", "playUrl": "/play-3.m3u8"},
                ],
            },
        ]
        payload = self.spider._build_play_sources(seasons, "99")
        self.assertEqual(payload["vod_play_from"], "第1季$$$第2季")
        self.assertIn("第1集$", payload["vod_play_url"])
        self.assertIn("第2集 加更$", payload["vod_play_url"])

    def test_decode_play_id_round_trips_base64url_payload(self):
        encoded = self.spider._encode_play_payload(
            {"mediaId": "88", "seasonNo": 1, "epNo": 3, "videoId": 12, "playUrl": "/video.m3u8", "name": "第3集"}
        )
        decoded = self.spider._decode_play_id(encoded)
        self.assertEqual(decoded["mediaId"], "88")
        self.assertEqual(decoded["seasonNo"], 1)
        self.assertEqual(decoded["epNo"], 3)
        self.assertEqual(decoded["playUrl"], "/video.m3u8")

    @patch.object(Spider, "_request_json")
    def test_detail_content_merges_detail_apis_and_videos(self, mock_request_json):
        mock_request_json.side_effect = [
            {"id": 300, "title": "基础标题", "posterUrl": "/base.jpg"},
            {
                "id": 300,
                "title": "完整标题",
                "posterUrlS3": "https://img.example/detail.jpg",
                "mediaType": {"code": "tv_series", "name": "电视剧"},
                "episodeStatus": "更新至2集",
                "releaseYear": "2026",
                "region": "大陆",
                "actors": ["张三", "李四"],
                "directors": ["王五"],
                "overview": "一段简介",
                "rating": "9.1",
            },
            [
                {
                    "seasonNo": 1,
                    "videoList": [
                        {"id": 901, "epNo": 1, "remark": "", "playUrl": "/ep1.m3u8"},
                        {"id": 902, "epNo": 2, "remark": "超前", "playUrl": "/ep2.m3u8"},
                    ],
                }
            ],
        ]
        result = self.spider.detailContent(["300"])
        vod = result["list"][0]
        self.assertEqual(vod["vod_id"], "300")
        self.assertEqual(vod["vod_name"], "完整标题")
        self.assertEqual(vod["vod_pic"], "https://img.example/detail.jpg")
        self.assertEqual(vod["type_name"], "电视剧")
        self.assertEqual(vod["vod_area"], "大陆")
        self.assertEqual(vod["vod_actor"], "张三/李四")
        self.assertEqual(vod["vod_director"], "王五")
        self.assertEqual(vod["vod_content"], "一段简介")
        self.assertEqual(vod["vod_douban_score"], "9.1")
        self.assertEqual(vod["vod_play_from"], "乌云影视")
        self.assertIn("第2集 超前$", vod["vod_play_url"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: FAIL with missing `_build_play_sources` / `_encode_play_payload` / `_decode_play_id` / `detailContent`.

- [ ] **Step 3: Write minimal implementation**

```python
    def _encode_play_payload(self, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    def _decode_play_id(self, play_id):
        raw = self._stringify(play_id).strip()
        padding = "=" * (-len(raw) % 4)
        try:
            return json.loads(base64.urlsafe_b64decode((raw + padding).encode("utf-8")).decode("utf-8"))
        except Exception:
            return {"mediaId": raw, "playUrl": raw}

    def _build_play_sources(self, seasons, media_id):
        season_list = self._ensure_list(seasons)
        multiple = len(season_list) > 1
        from_list = []
        url_list = []
        for index, season in enumerate(season_list, start=1):
            season_no = season.get("seasonNo") or index
            episode_entries = []
            for video_index, video in enumerate(self._ensure_list(season.get("videoList")), start=1):
                ep_no = int(video.get("epNo") or video_index)
                remark = self._stringify(video.get("remark")).strip()
                if ep_no > 0:
                    name = f"第{ep_no}集" if not remark else f"第{ep_no}集 {remark}"
                else:
                    name = remark or "正片"
                payload = self._encode_play_payload(
                    {
                        "mediaId": self._stringify(media_id),
                        "seasonNo": season_no,
                        "epNo": ep_no,
                        "videoId": video.get("id"),
                        "playUrl": video.get("playUrl"),
                        "name": name,
                    }
                )
                episode_entries.append(f"{name}${payload}")
            if episode_entries:
                from_list.append(f"第{season_no}季" if multiple else self._stringify(season.get("lineName") or season.get("title") or self.name))
                url_list.append("#".join(episode_entries))
        return {"vod_play_from": "$$$".join(from_list), "vod_play_url": "$$$".join(url_list)}

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            media_id = self._stringify(raw_id).strip()
            if not media_id:
                continue
            base_detail = self._request_json(f"/movie/media/base/detail?mediaId={media_id}") or {}
            detail = self._request_json(f"/movie/media/detail?mediaId={media_id}") or {}
            seasons = self._request_json(f"/movie/media/video/list?mediaId={media_id}&lineName=&resolutionCode=") or []
            merged = detail or base_detail
            play_data = self._build_play_sources(seasons, media_id)
            result["list"].append(
                {
                    "vod_id": self._stringify(merged.get("id") or media_id),
                    "vod_name": self._stringify(merged.get("title") or base_detail.get("title")),
                    "vod_pic": self._pick_poster(merged or base_detail),
                    "type_id": self._stringify((merged.get("mediaType") or {}).get("code")),
                    "type_name": self._stringify((merged.get("mediaType") or {}).get("name")),
                    "vod_remarks": self._stringify(merged.get("episodeStatus")),
                    "vod_year": self._stringify(merged.get("releaseYear")),
                    "vod_area": self._stringify(merged.get("region")),
                    "vod_actor": self._join_text(merged.get("actors")),
                    "vod_director": self._join_text(merged.get("directors")),
                    "vod_content": self._stringify(merged.get("overview") or merged.get("description")),
                    "vod_douban_score": self._stringify(merged.get("rating")),
                    **play_data,
                }
            )
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: PASS for the new detail and playlist tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_乌云影视.py 乌云影视.py
git commit -m "feat: add wooyun detail aggregation"
```

### Task 4: Add Player Resolution And Fallback Logic

**Files:**
- Modify: `tests/test_乌云影视.py`
- Modify: `乌云影视.py`

- [ ] **Step 1: Write the failing test**

```python
class TestWooyunSpider(unittest.TestCase):
    def test_find_play_url_matches_video_id_then_ep_no(self):
        seasons = [
            {
                "seasonNo": 1,
                "videoList": [
                    {"id": 10, "epNo": 1, "playUrl": "/ep1.m3u8"},
                    {"id": 11, "epNo": 2, "playUrl": "/ep2.m3u8"},
                ],
            }
        ]
        self.assertEqual(self.spider._find_play_url(seasons, {"seasonNo": 1, "videoId": 11}), "/ep2.m3u8")
        self.assertEqual(self.spider._find_play_url(seasons, {"seasonNo": 1, "epNo": 1}), "/ep1.m3u8")

    def test_player_content_returns_direct_url_when_payload_has_play_url(self):
        play_id = self.spider._encode_play_payload(
            {"mediaId": "100", "seasonNo": 1, "epNo": 1, "videoId": 10, "playUrl": "/direct.m3u8", "name": "第1集"}
        )
        result = self.spider.playerContent("乌云影视", play_id, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["jx"], 0)
        self.assertEqual(result["url"], "https://wooyun.tv/direct.m3u8")
        self.assertEqual(result["header"]["Referer"], "https://wooyun.tv/")

    @patch.object(Spider, "_request_json")
    def test_player_content_refetches_video_list_when_payload_missing_play_url(self, mock_request_json):
        mock_request_json.return_value = [
            {
                "seasonNo": 1,
                "videoList": [
                    {"id": 77, "epNo": 3, "playUrl": "/refetched.m3u8"},
                ],
            }
        ]
        play_id = self.spider._encode_play_payload(
            {"mediaId": "100", "seasonNo": 1, "epNo": 3, "videoId": 77, "playUrl": "", "name": "第3集"}
        )
        result = self.spider.playerContent("乌云影视", play_id, {})
        self.assertEqual(result["parse"], 0)
        self.assertEqual(result["url"], "https://wooyun.tv/refetched.m3u8")

    def test_player_content_falls_back_to_external_parse_when_no_url_found(self):
        result = self.spider.playerContent("乌云影视", "raw-play-id", {})
        self.assertEqual(result["parse"], 1)
        self.assertEqual(result["jx"], 1)
        self.assertEqual(result["url"], "raw-play-id")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: FAIL with missing `_find_play_url` or incorrect `playerContent` fallback behavior.

- [ ] **Step 3: Write minimal implementation**

```python
    def _find_play_url(self, seasons, target):
        for season in self._ensure_list(seasons):
            if target.get("seasonNo") is not None and int(season.get("seasonNo") or 0) != int(target.get("seasonNo")):
                continue
            for video in self._ensure_list(season.get("videoList")):
                if target.get("videoId") is not None and int(video.get("id") or 0) == int(target.get("videoId")):
                    return self._stringify(video.get("playUrl"))
                if target.get("epNo") is not None and int(video.get("epNo") or 0) == int(target.get("epNo")):
                    return self._stringify(video.get("playUrl"))

        first_season = self._ensure_list(seasons)[0] if self._ensure_list(seasons) else {}
        first_video = self._ensure_list(first_season.get("videoList"))[0] if self._ensure_list(first_season.get("videoList")) else {}
        return self._stringify(first_video.get("playUrl"))

    def playerContent(self, flag, id, vipFlags):
        payload = self._decode_play_id(self._stringify(id).strip())
        final_url = self._stringify(payload.get("playUrl"))
        if not final_url and payload.get("mediaId"):
            seasons = self._request_json(
                f"/movie/media/video/list?mediaId={payload['mediaId']}&lineName=&resolutionCode="
            ) or []
            final_url = self._find_play_url(seasons, payload)

        if not final_url:
            return {"parse": 1, "jx": 1, "url": self._stringify(id), "header": dict(self.headers)}

        return {
            "parse": 0,
            "jx": 0,
            "url": self._full_url(final_url),
            "header": {
                "Referer": self.host + "/",
                "Origin": self.host,
                "User-Agent": self.headers["User-Agent"],
            },
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_乌云影视.TestWooyunSpider -v`
Expected: PASS for the new player tests and all previous tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_乌云影视.py 乌云影视.py
git commit -m "feat: add wooyun player resolution"
```

### Task 5: Full Verification And Cleanup

**Files:**
- Modify: `tests/test_乌云影视.py`
- Modify: `乌云影视.py`

- [ ] **Step 1: Run the focused spider test suite**

Run: `python -m unittest tests.test_乌云影视 -v`
Expected: All tests PASS with no import or syntax errors.

- [ ] **Step 2: Run adjacent regression tests**

Run: `python -m unittest tests.test_dbku tests.test_剧迷 tests.test_橘子TV tests.test_youknow tests.test_libvio -v`
Expected: Existing spider tests still PASS.

- [ ] **Step 3: Run syntax verification**

Run: `python -m py_compile 乌云影视.py tests/test_乌云影视.py`
Expected: Command exits successfully with no output.

- [ ] **Step 4: Review git diff for scope**

Run: `git diff -- 乌云影视.py tests/test_乌云影视.py docs/superpowers/plans/2026-04-19-wooyun-spider.md`
Expected: Diff only contains the new spider, its tests, and the implementation plan.

- [ ] **Step 5: Commit**

```bash
git add 乌云影视.py tests/test_乌云影视.py docs/superpowers/plans/2026-04-19-wooyun-spider.md
git commit -m "feat: add wooyun spider"
```
