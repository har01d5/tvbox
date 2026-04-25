# coding=utf-8
import json
import sys
from urllib.parse import urlencode

from base.spider import Spider as BaseSpider

sys.path.append("..")


HOST = "http://read.api.duodutek.com"
UA = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/50.0.2661.87 Safari/537.36"
)
COMMON_PARAMS = {
    "productId": "2a8c14d1-72e7-498b-af23-381028eb47c0",
    "vestId": "2be070e0-c824-4d0e-a67a-8f688890cadb",
    "channel": "oppo19",
    "osType": "android",
    "version": "20",
    "token": "202509271001001446030204698626",
}
CLASS_LIST = [
    {"type_id": "1287", "type_name": "甜宠"},
    {"type_id": "1288", "type_name": "逆袭"},
    {"type_id": "1289", "type_name": "热血"},
    {"type_id": "1290", "type_name": "现代"},
    {"type_id": "1291", "type_name": "古代"},
]


class Spider(BaseSpider):
    def __init__(self):
        self.name = "星星短剧"
        self.host = HOST
        self.headers = {"User-Agent": UA}
        self.classes = CLASS_LIST

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": {}}

    def homeVideoContent(self):
        return {"list": self._list_category_items("1287", 1)[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        page = max(1, int(pg))
        payload = self._get_json(
            self._build_url(
                "/novel-api/app/pageModel/getResourceById",
                {"resourceId": str(tid), "pageNum": str(page), "pageSize": "10"},
            )
        )
        data = payload.get("data") if isinstance(payload, dict) else {}
        items = [self._map_vod(item) for item in (data.get("datalist") or [])]
        total = self._coerce_int(
            data.get("total")
            or data.get("totalCount")
            or (data.get("page") or {}).get("totalCount")
            or payload.get("total")
        )
        return {"page": page, "limit": len(items), "total": total, "list": items}

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            if not vod_id:
                continue
            book_id, book_name, intro = self._split_vod_id(vod_id)
            payload = self._get_json(
                self._build_url(
                    "/novel-api/basedata/book/getChapterList",
                    {"bookId": book_id},
                )
            )
            chapters = payload.get("data") if isinstance(payload, dict) else []
            episodes = []
            for index, chapter in enumerate(chapters or [], start=1):
                play_url = self._extract_play_url(chapter)
                if not play_url:
                    continue
                chapter_name = str(chapter.get("chapterName") or f"第{index}集").strip()
                episodes.append(f"{chapter_name}${play_url}")
            result["list"].append(
                {
                    "vod_id": vod_id,
                    "vod_name": book_name,
                    "vod_content": intro,
                    "vod_remarks": f"共{len(episodes)}集" if episodes else "",
                    "vod_play_from": "星星短剧",
                    "vod_play_url": "#".join(episodes),
                }
            )
        return result

    def searchContent(self, key, quick, pg="1"):
        page = max(1, int(pg))
        return {"page": page, "limit": 0, "total": 0, "list": []}

    def playerContent(self, flag, id, vipFlags):
        play_url = self._normalize_play_url(id)
        if not play_url:
            return {"parse": 0, "jx": 0, "url": "", "header": {}}
        return {
            "parse": 0,
            "jx": 0,
            "url": play_url,
            "header": {"User-Agent": UA},
        }

    def _list_category_items(self, tid, page):
        payload = self._get_json(
            self._build_url(
                "/novel-api/app/pageModel/getResourceById",
                {"resourceId": str(tid), "pageNum": str(page), "pageSize": "10"},
            )
        )
        data = payload.get("data") if isinstance(payload, dict) else {}
        return [self._map_vod(item) for item in (data.get("datalist") or [])]

    def _map_vod(self, item):
        book_id = str(item.get("id") or "").strip()
        name = str(item.get("name") or "").strip()
        intro = str(item.get("introduction") or "").strip()
        heat = str(item.get("heat") or "").strip()
        return {
            "vod_id": f"{book_id}@@{name}@@{intro}",
            "vod_name": name,
            "vod_pic": str(item.get("icon") or "").strip(),
            "vod_remarks": f"{heat}万播放" if heat else "",
        }

    def _split_vod_id(self, vod_id):
        parts = vod_id.split("@@", 2)
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return parts[0], parts[1], ""
        return vod_id, "", ""

    def _extract_play_url(self, chapter):
        for play_group in chapter.get("shortPlayList") or []:
            for play in play_group.get("chapterShortPlayVoList") or []:
                play_url = self._normalize_play_url(play.get("shortPlayUrl"))
                if play_url:
                    return play_url
        return ""

    def _normalize_play_url(self, value):
        play_url = str(value or "").strip()
        if play_url.startswith("http://img.novel.wsljf.xyz/"):
            return "https://" + play_url[len("http://"):]
        return play_url

    def _build_url(self, path, params=None):
        query = urlencode({**COMMON_PARAMS, **(params or {})})
        return f"{self.host}{path}?{query}"

    def _coerce_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _get_json(self, url):
        response = self.fetch(url, headers=dict(self.headers), timeout=10, verify=False)
        if response.status_code != 200:
            return {}
        try:
            return json.loads(response.text or "{}")
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}
