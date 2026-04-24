# coding=utf-8
import json
import sys
from urllib.parse import urlencode

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "博看听书"
        self.api_host = "https://api.bookan.com.cn"
        self.search_host = "https://es.bookan.com.cn"
        self.instance_id = "25304"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        self.classes = [
            {"type_id": "1305", "type_name": "少年读物"},
            {"type_id": "1304", "type_name": "儿童文学"},
            {"type_id": "1320", "type_name": "国学经典"},
            {"type_id": "1306", "type_name": "文艺少年"},
            {"type_id": "1309", "type_name": "育儿心经"},
            {"type_id": "1310", "type_name": "心理哲学"},
            {"type_id": "1307", "type_name": "青春励志"},
            {"type_id": "1312", "type_name": "历史小说"},
            {"type_id": "1303", "type_name": "故事会"},
            {"type_id": "1317", "type_name": "音乐戏剧"},
            {"type_id": "1319", "type_name": "相声评书"},
        ]
        self.force_order = [
            "相声评书",
            "国学经典",
            "故事会",
            "历史小说",
            "音乐戏剧",
            "青春励志",
            "少年读物",
            "儿童文学",
            "文艺少年",
            "育儿心经",
            "心理哲学",
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _sort_classes(self):
        order_map = {name: index for index, name in enumerate(self.force_order)}
        return sorted(self.classes, key=lambda item: order_map.get(item["type_name"], 999))

    def _to_int(self, value, default=0):
        try:
            return int(str(value))
        except Exception:
            return default

    def _build_url(self, base_url, params=None):
        query = {
            str(key): value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        return f"{base_url}?{urlencode(query)}" if query else base_url

    def _api_get(self, path, params=None, host=None):
        target_host = str(host or self.api_host).rstrip("/")
        target = self._build_url(f"{target_host}/{str(path or '').lstrip('/')}", params or {})
        try:
            response = self.fetch(target, headers=self.headers, timeout=10, verify=False)
        except Exception:
            return {}
        if response.status_code != 200:
            return {}
        try:
            return json.loads(response.text or "{}")
        except Exception:
            return {}

    def _search_get(self, path, params=None):
        return self._api_get(path, params=params, host=self.search_host)

    def _fetch_category_books(self, category_id, page=1, limit=24):
        payload = self._api_get(
            "/voice/book/list",
            {
                "instance_id": self.instance_id,
                "page": page,
                "category_id": category_id,
                "num": limit,
            },
        )
        return ((payload.get("data") or {}).get("list") or [])

    def _fetch_album_info(self, album_id):
        payload = self._api_get("/voice/album/get", {"album_id": album_id})
        data = payload.get("data") or {}
        if not isinstance(data, dict) or not data:
            return {"success": False, "data": None}
        return {
            "success": True,
            "data": {
                "vod_name": str(data.get("title") or data.get("name") or "未知标题"),
                "vod_pic": str(data.get("cover") or ""),
                "vod_author": str(data.get("author") or ""),
                "vod_desc": str(data.get("description") or "暂无简介"),
                "created_at": str(data.get("created_at") or ""),
                "updated_at": str(data.get("updated_at") or ""),
            },
        }

    def _fetch_album_units(self, album_id):
        per_page = 200
        first = self._api_get(
            "/voice/album/units",
            {"album_id": album_id, "page": 1, "num": per_page, "order": 1},
        )
        first_data = first.get("data") or {}
        items = list(first_data.get("list") or [])
        total = self._to_int(first_data.get("total"), len(items))
        if total <= per_page:
            return items
        page_count = (total + per_page - 1) // per_page
        for page in range(2, page_count + 1):
            payload = self._api_get(
                "/voice/album/units",
                {"album_id": album_id, "page": page, "num": per_page, "order": 1},
            )
            items.extend(((payload.get("data") or {}).get("list") or []))
        return items

    def _find_album_from_categories(self, album_id):
        for cls in self._sort_classes():
            for page in range(1, 6):
                books = self._fetch_category_books(cls["type_id"], page, 24)
                if not books:
                    break
                hit = next((item for item in books if str((item or {}).get("id") or "") == str(album_id)), None)
                if hit:
                    return {
                        "vod_name": str(hit.get("name") or hit.get("title") or ""),
                        "vod_pic": str(hit.get("cover") or ""),
                        "vod_author": str(hit.get("author") or ""),
                        "found": True,
                    }
                if len(books) < 24:
                    break
        return {"vod_name": "", "vod_pic": "", "vod_author": "", "found": False}

    def _format_book(self, item, fallback_remark=""):
        row = item or {}
        vod_id = str(row.get("id") or "")
        if not vod_id:
            return None
        return {
            "vod_id": vod_id,
            "vod_name": str(row.get("name") or row.get("title") or ""),
            "vod_pic": str(row.get("cover") or ""),
            "vod_remarks": str(row.get("author") or fallback_remark or ""),
        }

    def homeContent(self, filter):
        classes = self._sort_classes()
        videos = []
        for cls in classes:
            for item in self._fetch_category_books(cls["type_id"], 1, 24):
                row = self._format_book(item, cls["type_name"])
                if not row:
                    continue
                row["vod_remarks"] = f"{str((item or {}).get('author') or '').strip()} {cls['type_name']}".strip()
                videos.append(row)
        return {"class": classes, "list": videos}

    def homeVideoContent(self):
        return {"list": self.homeContent(False).get("list", [])}

    def categoryContent(self, tid, pg, filter, extend):
        if not any(item["type_id"] == str(tid) for item in self.classes):
            return {"page": 1, "limit": 24, "total": 0, "list": []}
        page = self._to_int(pg, 1)
        payload = self._api_get(
            "/voice/book/list",
            {
                "instance_id": self.instance_id,
                "page": page,
                "category_id": tid,
                "num": 24,
            },
        )
        data = payload.get("data") or {}
        items = [self._format_book(item) for item in (data.get("list") or [])]
        return {
            "page": page,
            "limit": 24,
            "total": self._to_int(data.get("total"), len(items)),
            "list": [item for item in items if item],
        }

    def detailContent(self, ids):
        album_id = str((ids or [""])[0] or "").strip()
        if not album_id:
            return {"list": []}
        category_info = self._find_album_from_categories(album_id)
        album_info = self._fetch_album_info(album_id)
        detail = album_info.get("data") if album_info.get("success") else {}
        units = self._fetch_album_units(album_id)
        if not units:
            return {"list": []}

        episodes = []
        for index, chapter in enumerate(units, start=1):
            play_id = str((chapter or {}).get("file") or "").strip()
            if not play_id:
                continue
            title = str((chapter or {}).get("title") or f"第{index}集").strip()
            episodes.append(f"{index}.{title}${play_id}")
        if not episodes:
            return {"list": []}

        detail = detail or {}
        vod_name = str(
            category_info.get("vod_name")
            or detail.get("vod_name")
            or ((units[0] or {}).get("album_title") or "")
            or ((units[0] or {}).get("title") or "未知标题")
        )
        vod_pic = str(
            category_info.get("vod_pic")
            or detail.get("vod_pic")
            or ((units[0] or {}).get("cover") or "")
        )
        vod_author = str(category_info.get("vod_author") or detail.get("vod_author") or "")
        created_at = str(detail.get("created_at") or (units[0] or {}).get("created_at") or "")
        updated_at = str(detail.get("updated_at") or (units[0] or {}).get("updated_at") or "")
        vod_desc = str(detail.get("vod_desc") or (units[0] or {}).get("description") or "暂无简介")

        return {
            "list": [
                {
                    "vod_id": album_id,
                    "vod_name": vod_name,
                    "vod_pic": vod_pic,
                    "vod_remarks": f"{vod_author + ' ' if vod_author else ''}共{len(episodes)}集",
                    "vod_content": vod_desc,
                    "vod_actor": f"▶️创建于 {created_at}" if created_at else "",
                    "vod_director": f"▶️更新于 {updated_at}" if updated_at else "",
                    "vod_year": f"{created_at.split('-')[0]}年" if created_at else "",
                    "vod_play_from": "博看听书",
                    "vod_play_url": "#".join(episodes),
                }
            ]
        }

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        if not keyword:
            return {"page": 1, "limit": 0, "total": 0, "list": []}
        page = self._to_int(pg, 1)
        payload = self._search_get(
            "/api/v3/voice/book",
            {
                "instanceId": self.instance_id,
                "keyword": keyword,
                "pageNum": page,
                "limitNum": 20,
            },
        )
        data = payload.get("data") or {}
        items = [self._format_book(item) for item in (data.get("list") or [])]
        return {
            "page": page,
            "limit": 20,
            "total": self._to_int(data.get("total"), len(items)),
            "list": [item for item in items if item],
        }

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0,
            "url": str(id or ""),
            "header": {"User-Agent": self.headers["User-Agent"]},
        }
