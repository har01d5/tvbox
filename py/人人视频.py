# coding=utf-8
import base64
import hashlib
import hmac
import json
import sys
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from base.spider import Spider as BaseSpider

sys.path.append("..")


HOST = "https://m.yichengwlkj.com"
API_URL = "https://api.rrmj.plus"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
)
KY_ID = "BA21A0F5-7C57-41BA-8665-B7164A131832"
APP_SECRET = "ES513W0B1CsdUrR13Qk5EgDAKPeeKZY"
AES_KEY = "3b744389882a4067"
AES_IV = "b1da7878016e4e2b"


class Spider(BaseSpider):
    def __init__(self):
        self.name = "人人视频"
        self.class_name_map = {
            "TV": "剧集",
            "MOVIE": "电影",
            "VARIETY": "综艺",
            "COMIC": "动漫",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeVideoContent(self):
        return {"list": []}

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _build_api_url(self, path):
        return f"{API_URL}{str(path or '').strip()}"

    def _join_values(self, *values):
        return " ".join([self._stringify(value).strip() for value in values if self._stringify(value).strip()]).strip()

    def _generate_signature(self, text):
        digest = hmac.new(APP_SECRET.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _create_headers(self, url_path, params=None, method="GET"):
        payload = {
            self._stringify(key): self._stringify(value)
            for key, value in dict(params or {}).items()
        }
        timestamp = str(int(time.time() * 1000))
        sorted_params = "&".join([f"{key}={payload[key]}" for key in sorted(payload)])
        full_url = f"{url_path}?{sorted_params}" if sorted_params else url_path
        string_to_sign = "\n".join(
            [
                method.upper(),
                f"aliId:{KY_ID}",
                "ct:web_pc",
                "cv:1.0.0",
                f"t:{timestamp}",
                full_url,
            ]
        )
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": UA,
            "Origin": HOST,
            "Referer": HOST,
            "aliId": KY_ID,
            "clientType": "web_pc",
            "clientVersion": "1.0.0",
            "ct": "web_pc",
            "cv": "1.0.0",
            "deviceId": KY_ID,
            "t": timestamp,
            "token": "",
            "uet": "9",
            "umid": KY_ID,
            "x-ca-sign": self._generate_signature(string_to_sign),
        }
        if method.upper() == "POST":
            headers["Content-Type"] = "application/json;charset=UTF-8"
        return headers

    def _decrypt_aes_ecb(self, encrypted_data):
        text = self._stringify(encrypted_data).strip()
        if not text:
            return None
        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except Exception:
                return None
        try:
            clean = "".join(text.split())
            cipher = AES.new(AES_KEY.encode("utf-8"), AES.MODE_ECB)
            raw = base64.b64decode(clean)
            decoded = unpad(cipher.decrypt(raw), AES.block_size).decode("utf-8")
            return json.loads(decoded)
        except Exception:
            return None

    def _decrypt_aes_cbc(self, encrypted_text, new_sign):
        text = self._stringify(encrypted_text).strip()
        sign = self._stringify(new_sign).strip()
        if not text or len(sign) < 20:
            return ""
        try:
            key = sign[4:20].encode("utf-8")
            cipher = AES.new(key, AES.MODE_CBC, AES_IV.encode("utf-8"))
            decoded = unpad(cipher.decrypt(base64.b64decode(text)), AES.block_size).decode("utf-8")
            return decoded
        except Exception:
            return ""

    def _request_api(self, url_path, params=None, method="GET"):
        payload = dict(params or {})
        headers = self._create_headers(url_path, payload, method=method)
        try:
            if method.upper() == "POST":
                response = self.post(
                    self._build_api_url(url_path),
                    headers=headers,
                    json=payload,
                    timeout=10,
                    verify=False,
                )
            else:
                response = self.fetch(
                    self._build_api_url(url_path),
                    params=payload,
                    headers=headers,
                    timeout=10,
                    verify=False,
                )
        except Exception:
            return None
        if getattr(response, "status_code", 0) != 200:
            return None
        return self._decrypt_aes_ecb(getattr(response, "text", ""))

    def _build_filter_values(self, items):
        values = []
        for item in items or []:
            name = self._stringify(item.get("displayName"))
            value = self._stringify(item.get("value"))
            if not name:
                continue
            values.append({"n": name, "v": value})
        return values

    def _page_result(self, items, pg):
        page = int(pg)
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def homeContent(self, filter):
        payload = self._request_api("/m-station/drama/get_drama_filter") or {}
        groups = {
            self._stringify(item.get("filterType")): list(item.get("dramaFilterItemList") or [])
            for item in payload.get("data", [])
        }
        classes = []
        filters = {}
        for item in groups.get("dramaType", []):
            type_id = self._stringify(item.get("value"))
            if type_id not in self.class_name_map:
                continue
            classes.append({"type_id": type_id, "type_name": self.class_name_map[type_id]})
            filters[type_id] = [
                {"key": "area", "name": "地区", "value": self._build_filter_values(groups.get("area", []))},
                {"key": "class", "name": "类型", "value": self._build_filter_values(groups.get("plotType", []))},
                {"key": "year", "name": "年份", "value": self._build_filter_values(groups.get("year", []))},
                {"key": "by", "name": "排序", "value": self._build_filter_values(groups.get("sort", []))},
            ]
        return {"class": classes, "filters": filters}

    def categoryContent(self, tid, pg, filter, extend):
        params = {
            "area": self._stringify((extend or {}).get("area")),
            "sort": self._stringify((extend or {}).get("by") or "hot"),
            "year": self._stringify((extend or {}).get("year")),
            "dramaType": self._stringify(tid),
            "plotType": self._stringify((extend or {}).get("class")),
            "contentLabel": "",
            "page": int(pg),
            "rows": 30,
        }
        payload = self._request_api("/m-station/drama/drama_filter_search", params, method="POST") or {}
        items = []
        for vod in payload.get("data", []) or []:
            items.append(
                {
                    "vod_id": self._stringify(vod.get("dramaId") or vod.get("id")),
                    "vod_name": self._stringify(vod.get("title") or vod.get("name")),
                    "vod_pic": self._stringify(vod.get("coverUrl") or vod.get("cover")),
                    "vod_remarks": self._join_values(vod.get("year"), vod.get("subtitle")),
                }
            )
        return self._page_result(items, pg)

    def _episode_name(self, episode):
        title = self._stringify(episode.get("title")).strip()
        if title:
            return title
        text = self._stringify(episode.get("text")).strip()
        if text:
            return text
        number = self._stringify(episode.get("episodeNo")).strip()
        return f"第{number}集" if number else "正片"

    def detailContent(self, ids):
        items = []
        for raw_id in ids or []:
            drama_id = self._stringify(raw_id).strip()
            if not drama_id:
                continue
            payload = self._request_api(
                "/m-station/drama/page",
                {
                    "hsdrOpen": "0",
                    "isAgeLimit": "0",
                    "dramaId": drama_id,
                    "quality": "AI4K",
                    "hevcOpen": "0",
                    "tria4k": "1",
                },
            ) or {}
            data = payload.get("data") or {}
            info = data.get("dramaInfo") or {}
            play_urls = []
            for episode in data.get("episodeList", []) or []:
                episode_id = self._stringify(episode.get("sid") or episode.get("id")).strip()
                if not episode_id:
                    continue
                play_urls.append(f"{self._episode_name(episode)}${drama_id}@{episode_id}")
            items.append(
                {
                    "vod_id": drama_id,
                    "vod_name": self._stringify(info.get("title")),
                    "vod_pic": self._stringify(info.get("coverUrl") or info.get("cover") or info.get("cover3Url")),
                    "vod_remarks": self._stringify(info.get("playStatus")),
                    "vod_year": self._stringify(info.get("year")),
                    "vod_area": self._stringify(info.get("area")),
                    "vod_actor": self._stringify(info.get("actor") or info.get("subtitle")),
                    "vod_director": self._stringify(info.get("director")),
                    "vod_content": self._stringify(
                        info.get("introduction") or info.get("description") or info.get("subtitle")
                    ),
                    "type_name": self._stringify(info.get("plotType") or self.class_name_map.get(info.get("dramaType"), "")),
                    "vod_play_from": "人人专线" if play_urls else "",
                    "vod_play_url": "#".join(play_urls),
                }
            )
        return {"list": items}

    def playerContent(self, flag, id, vipFlags):
        raw = self._stringify(id).strip()
        if "@" not in raw:
            return {"parse": 1, "playUrl": "", "url": raw, "jx": 1}
        drama_id, episode_sid = raw.split("@", 1)
        payload = self._request_api(
            "/m-station/drama/play",
            {
                "dramaId": drama_id,
                "episodeSid": episode_sid,
                "hevcOpen": "0",
                "hsdrOpen": "0",
                "quality": "AI4K",
                "tria4k": "1",
            },
        ) or {}
        data = payload.get("data") or {}
        encrypted_url = self._stringify((data.get("m3u8") or {}).get("url") or (data.get("tria4kPlayInfo") or {}).get("url"))
        final_url = self._decrypt_aes_cbc(encrypted_url, data.get("newSign"))
        if not final_url:
            return {"parse": 1, "playUrl": "", "url": "", "jx": 1}
        try:
            response = self.fetch(
                final_url,
                headers={"User-Agent": UA},
                timeout=10,
                verify=False,
                allow_redirects=False,
            )
            final_url = self._stringify(getattr(response, "headers", {}).get("location") or final_url)
        except Exception:
            pass
        return {
            "parse": 0,
            "playUrl": "",
            "url": final_url,
            "jx": 0,
            "header": {"User-Agent": UA, "Referer": HOST},
        }

    def searchContent(self, key, quick, pg="1"):
        keyword = self._stringify(key).strip()
        if not keyword:
            return self._page_result([], pg)
        payload = self._request_api(
            "/search/comprehensive/precise-mixed",
            {"keywords": keyword, "size": "20", "searchAfter": ""},
        ) or {}
        data = payload.get("data") or {}
        source = list(data.get("seasonList") or []) or list(data.get("fuzzySeasonList") or [])
        items = []
        seen = set()
        for vod in source:
            vod_id = self._stringify(vod.get("id") or vod.get("dramaId"))
            if not vod_id or vod_id in seen:
                continue
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._stringify(vod.get("title") or vod.get("name")),
                    "vod_pic": self._stringify(vod.get("cover") or vod.get("coverUrl")),
                    "vod_remarks": self._join_values(vod.get("year"), vod.get("classify") or vod.get("cat")),
                }
            )
        return self._page_result(items, pg)
