# coding=utf-8
import base64
import json
import sys
from urllib.parse import unquote, urlencode, urljoin

import requests

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    DRIVE_ORDER = {"baidu": 1, "quark": 2, "xunlei": 3, "aliyun": 4, "a123": 5, "other": 99}

    def __init__(self):
        self.name = "不太灵"
        self.api_base = "https://web5.mukaku.com/prod/api/v1/"
        self.app_id = "83768d9ad4"
        self.identity = "23734adac0301bccdcb107c4aa21f96c"
        self.timeout = 10
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": self.api_base,
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "近日热门"},
            {"type_id": "4", "type_name": "本周热门"},
            {"type_id": "5", "type_name": "本月热门"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _build_api_url(self, endpoint, params=None):
        query = {"app_id": self.app_id, "identity": self.identity}
        query.update(params or {})
        return urljoin(self.api_base, endpoint) + "?" + urlencode(query)

    def _parse_payload(self, text):
        raw = str(text or "").strip()
        if raw.startswith("callback(") and raw.endswith(")"):
            raw = raw[9:-1]
        return json.loads(raw) if raw else {}

    def _request_api(self, endpoint, params=None):
        response = requests.get(
            self._build_api_url(endpoint, params),
            headers=dict(self.headers),
            timeout=self.timeout,
            verify=False,
        )
        if response.status_code != 200:
            return [] if endpoint in {"getVideoList", "getVideoMovieList"} else None
        payload = self._parse_payload(response.text)
        if not payload or payload.get("success") is not True or payload.get("code") != 200:
            return [] if endpoint in {"getVideoList", "getVideoMovieList"} else None
        data = payload.get("data")
        if endpoint in {"getVideoList", "getVideoMovieList"}:
            if isinstance(data, dict) and isinstance(data.get("data"), list):
                return data.get("data")
            if isinstance(data, dict) and isinstance(data.get("list"), list):
                return data.get("list")
            return []
        return data

    def _map_filter_values(self, items):
        values = [{"n": "不限", "v": "0"}]
        for item in items or []:
            title = str((item or {}).get("title") or "").strip()
            if title:
                values.append({"n": title, "v": title})
        return values

    def _build_filters(self, type_data):
        if not isinstance(type_data, dict):
            return {}
        common = [
            {"key": "sc", "name": "影视类型", "value": self._map_filter_values(type_data.get("t1"))},
            {"key": "sd", "name": "制片地区", "value": self._map_filter_values(type_data.get("t2"))},
            {"key": "se", "name": "上映年份", "value": self._map_filter_values(type_data.get("t3"))},
            {"key": "sf", "name": "资源画质", "value": self._map_filter_values(type_data.get("t4"))},
            {"key": "sh", "name": "影视标签", "value": self._map_filter_values(type_data.get("t5"))},
        ]
        return {
            "1": common,
            "2": common + [{"key": "status", "name": "剧集状态", "value": [{"n": "不限", "v": "0"}]}],
        }

    def _normalize_video(self, item):
        data = item or {}
        return {
            "vod_id": str(data.get("doub_id") or data.get("id") or ""),
            "vod_name": data.get("title") or "未知标题",
            "vod_pic": data.get("image") or data.get("epic") or "",
            "vod_remarks": data.get("ejs") or data.get("zqxd") or "",
            "vod_year": data.get("years") or "",
            "vod_content": data.get("abstract") or "",
            "vod_actor": data.get("performer") or "",
            "vod_director": data.get("director") or "",
            "vod_area": data.get("production_area") or "",
        }

    def _parse_ext_object(self, ext):
        candidates = [ext]
        try:
            decoded = base64.b64decode(str(ext or "")).decode("utf-8")
            if decoded and decoded != ext:
                candidates.append(decoded)
        except Exception:
            pass
        for raw in list(candidates):
            try:
                decoded = unquote(str(raw))
                if decoded != raw:
                    candidates.append(decoded)
            except Exception:
                pass
        for raw in candidates:
            try:
                value = json.loads(raw)
                if isinstance(value, dict):
                    return value
            except Exception:
                continue
        return {}

    def _normalize_filter_value(self, value):
        text = str(value or "").strip()
        return "" if text in {"", "0", "不限", "all"} else text

    def _to01(self, value, fallback=0):
        text = str(value if value is not None else fallback).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return 1
        if text in {"0", "false", "no", "off", ""}:
            return 0
        return fallback

    def _dedupe_by_vod_id(self, items):
        result = []
        seen = set()
        for item in items or []:
            vod_id = str((item or {}).get("doub_id") or (item or {}).get("id") or "")
            if not vod_id or vod_id in seen:
                continue
            seen.add(vod_id)
            result.append(item)
        return result

    def _paginate_items(self, items, page, limit):
        page_num = max(1, int(page))
        size = max(1, int(limit))
        total = len(items)
        start = (page_num - 1) * size
        return {"page": page_num, "limit": size, "total": total, "list": items[start:start + size]}

    def _build_movie_params(self, tid, pg, ext):
        ext_obj = self._parse_ext_object(ext)
        return {
            "sa": int(tid),
            "page": int(pg),
            "sc": self._normalize_filter_value(ext_obj.get("sc")),
            "sd": self._normalize_filter_value(ext_obj.get("sd")),
            "se": self._normalize_filter_value(ext_obj.get("se")),
            "sf": self._normalize_filter_value(ext_obj.get("sf")),
            "sh": self._normalize_filter_value(ext_obj.get("sh")),
            "sg": self._normalize_filter_value(ext_obj.get("sg")) or "1",
            "iswp": self._to01(ext_obj.get("iswp"), 0),
        }

    def _normalize_drive_key(self, value):
        text = str(value or "").strip().lower()
        if text in {"alipan", "aliyun", "aliyundrive", "ali", "阿里"}:
            return "aliyun"
        if "quark" in text or "夸克" in text:
            return "quark"
        if "baidu" in text or "百度" in text:
            return "baidu"
        if "xunlei" in text or "迅雷" in text:
            return "xunlei"
        if "123" in text:
            return "a123"
        return "other"

    def _detect_drive_type_by_url(self, url):
        text = str(url or "").lower()
        if "pan.quark.cn" in text:
            return "quark"
        if "pan.baidu.com" in text:
            return "baidu"
        if "pan.xunlei.com" in text:
            return "xunlei"
        if "alipan.com" in text or "aliyundrive.com" in text:
            return "aliyun"
        if "123865.com" in text or "123684.com" in text or "123pan.com" in text:
            return "a123"
        return "other"

    def _is_supported_pan_url(self, url):
        text = str(url or "").strip().lower()
        return any(
            token in text
            for token in [
                "pan.quark.cn",
                "pan.baidu.com",
                "pan.xunlei.com",
                "alipan.com",
                "aliyundrive.com",
                "123865.com",
                "123684.com",
                "123pan.com",
                "drive.uc.cn",
            ]
        )

    def _extract_pan_sources(self, detail):
        groups = (detail or {}).get("movies_online_seed")
        if not isinstance(groups, dict):
            return "", ""
        seen = set()
        counters = {}
        entries = []
        for group_name, items in groups.items():
            for item in items or []:
                link = str((item or {}).get("link") or "").strip()
                if not link or link in seen:
                    continue
                seen.add(link)
                kind = self._detect_drive_type_by_url(link)
                if kind == "other":
                    kind = self._normalize_drive_key(group_name)
                counters[kind] = counters.get(kind, 0) + 1
                line_name = f"{kind}@{counters[kind]}"
                entries.append((line_name, link))
        entries.sort(
            key=lambda pair: (
                self.DRIVE_ORDER.get(pair[0].split("@")[0], 999),
                int(pair[0].split("@")[1]),
                pair[0],
            )
        )
        return "$$$".join(name for name, _ in entries), "$$$".join(f"{name}${url}" for name, url in entries)

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self._build_filters(self._request_api("getVideoTypeList", {}))}

    def homeVideoContent(self):
        items = self._request_api("getVideoList", {"sc": "3", "limit": 20}) or []
        return {"list": [self._normalize_video(item) for item in items]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        if str(tid) in {"1", "2"}:
            items = self._dedupe_by_vod_id(
                self._request_api("getVideoMovieList", self._build_movie_params(tid, page, extend)) or []
            )
            return {
                "page": page,
                "limit": len(items) or 20,
                "total": page * 20 + len(items),
                "list": [self._normalize_video(item) for item in items],
            }
        items = self._dedupe_by_vod_id(self._request_api("getVideoList", {"sc": str(tid), "page": 1, "limit": 300}) or [])
        paged = self._paginate_items(items, page, 20)
        paged["list"] = [self._normalize_video(item) for item in paged["list"]]
        return paged

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = int(pg)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        items = self._request_api("getVideoList", {"sb": keyword, "page": 1, "limit": 300}) or []
        matched = [item for item in items if keyword.lower() in str((item or {}).get("title") or "").lower()]
        paged = self._paginate_items(self._dedupe_by_vod_id(matched), page, 20)
        paged["list"] = [self._normalize_video(item) for item in paged["list"]]
        return paged

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip()
        if not vod_id:
            return {"list": []}
        data = self._request_api("getVideoDetail", {"id": vod_id})
        if not isinstance(data, dict):
            return {"list": []}
        vod = self._normalize_video(data)
        play_from, play_url = self._extract_pan_sources(data)
        vod["vod_play_from"] = play_from
        vod["vod_play_url"] = play_url
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        url = raw[7:] if raw.startswith("push://") else raw
        if self._is_supported_pan_url(url):
            return {"parse": 0, "playUrl": "", "url": url}
        return {"parse": 0, "playUrl": "", "url": ""}
