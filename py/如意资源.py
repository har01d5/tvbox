# coding=utf-8
import json
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "如意资源"
        self.api_urls = [
            "https://cj.rycjapi.com/api.php/provide/vod",
            "https://cj.rytvapi.com/api.php/provide/vod",
            "https://bycj.rytvapi.com/api.php/provide/vod",
        ]
        self.img_hosts = [
            "https://ps.ryzypics.com",
            "https://ry-pic.com",
            "https://img.lzzyimg.com",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://cj.rycjapi.com/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影片"},
            {"type_id": "2", "type_name": "连续剧"},
            {"type_id": "3", "type_name": "综艺片"},
            {"type_id": "4", "type_name": "动漫片"},
            {"type_id": "35", "type_name": "电影解说"},
            {"type_id": "36", "type_name": "体育"},
        ]
        self.sub_class_map = {
            "1": ["7", "6", "8", "9", "10", "11", "12", "20", "34", "45", "47"],
            "2": ["13", "14", "15", "16", "21", "22", "23", "24", "46"],
            "3": ["25", "26", "27", "28"],
            "4": ["29", "30", "31", "32", "33"],
            "35": [],
            "36": ["37", "38", "39", "40"],
        }
        self.type_options = {
            "1": [
                {"n": "动作片", "v": "7"},
                {"n": "喜剧片", "v": "8"},
                {"n": "爱情片", "v": "9"},
                {"n": "科幻片", "v": "10"},
                {"n": "恐怖片", "v": "11"},
                {"n": "剧情片", "v": "12"},
                {"n": "战争片", "v": "6"},
                {"n": "记录片", "v": "20"},
                {"n": "伦理片", "v": "34"},
                {"n": "预告片", "v": "45"},
                {"n": "动画电影", "v": "47"},
            ],
            "2": [
                {"n": "国产剧", "v": "13"},
                {"n": "香港剧", "v": "14"},
                {"n": "韩国剧", "v": "15"},
                {"n": "欧美剧", "v": "16"},
                {"n": "台湾剧", "v": "21"},
                {"n": "日本剧", "v": "22"},
                {"n": "海外剧", "v": "23"},
                {"n": "泰国剧", "v": "24"},
                {"n": "短剧", "v": "46"},
            ],
            "3": [
                {"n": "大陆综艺", "v": "25"},
                {"n": "港台综艺", "v": "26"},
                {"n": "日韩综艺", "v": "27"},
                {"n": "欧美综艺", "v": "28"},
            ],
            "4": [
                {"n": "国产动漫", "v": "29"},
                {"n": "日韩动漫", "v": "30"},
                {"n": "欧美动漫", "v": "31"},
                {"n": "港台动漫", "v": "32"},
                {"n": "海外动漫", "v": "33"},
            ],
            "35": [],
            "36": [
                {"n": "足球", "v": "37"},
                {"n": "篮球", "v": "38"},
                {"n": "网球", "v": "39"},
                {"n": "斯诺克", "v": "40"},
            ],
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _build_query(self, params=None):
        parts = []
        for key, value in (params or {}).items():
            if value in ("", None):
                continue
            parts.append(f"{key}={value}")
        return "&".join(parts)

    def _request_json(self, params=None, url=""):
        if url:
            targets = [url]
        else:
            query = self._build_query(params)
            targets = [f"{base}?{query}" if query else base for base in self.api_urls]
        for target in targets:
            try:
                response = self.fetch(target, headers=self.headers, timeout=10)
            except Exception:
                continue
            if response.status_code != 200:
                continue
            try:
                return json.loads(response.text or "{}")
            except Exception:
                continue
        return {}

    def _get_pic_url(self, value):
        raw = str(value or "").strip()
        if raw in ("", "<nil>", "nil", "null"):
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("/"):
            return self.img_hosts[0] + raw
        return raw

    def _format_vod_list(self, items):
        result = []
        for item in items or []:
            current = item or {}
            vod_id = str(current.get("vod_id", "")).strip()
            if not vod_id or vod_id == "0":
                continue
            vod_year = str(current.get("vod_year", "")).strip()
            result.append(
                {
                    "vod_id": vod_id,
                    "vod_name": str(current.get("vod_name", "")).strip() or "未知标题",
                    "vod_pic": self._get_pic_url(current.get("vod_pic", "")),
                    "vod_remarks": str(current.get("vod_remarks", "")).strip() or vod_year,
                    "vod_year": vod_year,
                    "type_id": str(current.get("type_id", "")).strip(),
                }
            )
        return result

    def _enrich_missing_covers(self, items):
        missing_ids = [item["vod_id"] for item in items if not item.get("vod_pic")]
        if not missing_ids:
            return items
        data = self._request_json({"ac": "videolist", "ids": ",".join(missing_ids)})
        cover_map = {}
        for item in data.get("list", []) or []:
            current = item or {}
            vod_id = str(current.get("vod_id", "")).strip()
            if not vod_id:
                continue
            cover = (
                self._get_pic_url(current.get("vod_pic", ""))
                or self._get_pic_url(current.get("vod_img", ""))
                or self._get_pic_url(current.get("pic", ""))
            )
            if cover:
                cover_map[vod_id] = cover
        for item in items:
            if not item.get("vod_pic") and item["vod_id"] in cover_map:
                item["vod_pic"] = cover_map[item["vod_id"]]
        return items

    def _build_filters(self):
        filters = {}
        for cls in self.classes:
            tid = cls["type_id"]
            filters[tid] = []
            values = self.type_options.get(tid, [])
            if values:
                filters[tid].append({"key": "type", "name": "类型", "value": values})
        return filters

    def _resolve_type_id(self, tid, extend=None):
        current = dict(extend or {})
        if current.get("type"):
            return str(current["type"])
        values = self.sub_class_map.get(str(tid), [])
        if values:
            return values[0]
        return str(tid)

    def _page_result(self, items, pg, limit):
        page = max(int(str(pg or 1)), 1)
        return {"page": page, "limit": limit, "total": page * limit + len(items), "list": items}

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self._build_filters(), "list": []}

    def homeVideoContent(self):
        data = self._request_json({"ac": "list", "pg": "1", "pagesize": "20"})
        items = self._format_vod_list(data.get("list", []))
        return {"list": self._enrich_missing_covers(items)}

    def categoryContent(self, tid, pg, filter, extend):
        params = {"ac": "list", "t": self._resolve_type_id(tid, extend), "pg": str(pg), "pagesize": "20"}
        data = self._request_json(params)
        items = self._enrich_missing_covers(self._format_vod_list(data.get("list", [])))
        return self._page_result(items, pg, 20)

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = max(int(str(pg or 1)), 1)
        if not keyword:
            return {"page": page, "limit": 30, "total": 0, "list": []}
        data = self._request_json({"ac": "list", "wd": keyword, "pg": str(page), "pagesize": "30"})
        items = [
            item
            for item in self._format_vod_list(data.get("list", []))
            if keyword.lower() in item["vod_name"].lower()
        ]
        items = self._enrich_missing_covers(items)
        return self._page_result(items, page, 30)

    def _parse_play_groups(self, play_from, play_url):
        episodes = []
        for index, item in enumerate(str(play_url or "").split("#"), start=1):
            raw = str(item or "").strip()
            if not raw:
                continue
            if "$" in raw:
                name, url = raw.split("$", 1)
            else:
                name, url = "", raw
            name = str(name or "").strip() or f"第{index}集"
            url = str(url or "").strip()
            if not url:
                continue
            episodes.append(f"{name}${url}")
        line_names = [value.strip() for value in str(play_from or "").split(",") if value.strip()]
        if not line_names:
            line_names = ["如意资源"]
        urls = "#".join(episodes)
        return "$$$".join(line_names), "$$$".join([urls for _ in line_names])

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip()
        if not vod_id:
            return {"list": []}
        data = self._request_json({"ac": "videolist", "ids": vod_id})
        items = data.get("list", [])
        if not items:
            return {"list": []}
        item = items[0] or {}
        play_from, play_url = self._parse_play_groups(item.get("vod_play_from", ""), item.get("vod_play_url", ""))
        return {
            "list": [
                {
                    "vod_id": str(item.get("vod_id", vod_id)),
                    "vod_name": str(item.get("vod_name", "")),
                    "vod_pic": self._get_pic_url(item.get("vod_pic", "")),
                    "type_name": str(item.get("type_name", "")),
                    "vod_year": str(item.get("vod_year", "")),
                    "vod_area": str(item.get("vod_area", "")),
                    "vod_remarks": str(item.get("vod_remarks", "")),
                    "vod_actor": str(item.get("vod_actor", "")),
                    "vod_director": str(item.get("vod_director", "")),
                    "vod_content": str(item.get("vod_content", "")).strip(),
                    "vod_play_from": play_from,
                    "vod_play_url": play_url,
                }
            ]
        }

    def _is_direct_media_url(self, value):
        raw = str(value or "").lower()
        for suffix in (".m3u8", ".mp4", ".flv", ".avi", ".mkv", ".ts"):
            if suffix in raw:
                return True
        return False

    def playerContent(self, flag, id, vipFlags):
        play_id = str(id or "").strip()
        if not play_id:
            return {"parse": 0, "playUrl": "", "url": "", "header": {}}
        if self._is_direct_media_url(play_id):
            return {"parse": 0, "playUrl": "", "url": play_id, "header": {}}
        return {"parse": 1, "playUrl": "", "url": play_id, "header": {}}
