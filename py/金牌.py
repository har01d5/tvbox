# coding=utf-8
import hashlib
import json
import sys
import time

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "金牌"
        self.host = "https://m.jiabaide.cn"
        self.app_key = "cb808529bae6b6be45ecfab29a4889bc"
        self.mobile_ua = (
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.91 Mobile Safari/537.36"
        )
        self.headers = {
            "User-Agent": self.mobile_ua,
            "Referer": self.host + "/",
        }
        self.class_name_map = {
            "typeList": ("type", "类型"),
            "plotList": ("class", "剧情"),
            "districtList": ("area", "地区"),
            "languageList": ("lang", "语言"),
            "yearList": ("year", "年份"),
            "serialList": ("by", "排序"),
        }
        self.sort_values = [
            {"n": "最近更新", "v": "1"},
            {"n": "添加时间", "v": "2"},
            {"n": "人气高低", "v": "3"},
            {"n": "评分高低", "v": "4"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeVideoContent(self):
        return {"list": []}

    def _obj_to_form(self, obj=None):
        pairs = []
        for key, value in (obj or {}).items():
            if value in ("", None):
                continue
            pairs.append(f"{key}={value}")
        return "&".join(pairs)

    def _signed_headers(self, params=None):
        current = str(int(time.time() * 1000))
        sign_obj = dict(params or {})
        sign_obj["key"] = self.app_key
        sign_obj["t"] = current
        obj_str = self._obj_to_form(sign_obj)
        md5_value = hashlib.md5(obj_str.encode("utf-8")).hexdigest()
        sign = hashlib.sha1(md5_value.encode("utf-8")).hexdigest()
        headers = dict(self.headers)
        headers["t"] = current
        headers["sign"] = sign
        return headers

    def _fetch_json(self, path, params=None):
        target = self.host + str(path)
        query = self._obj_to_form(params or {})
        if query:
            target = target + "?" + query
        response = self.fetch(target, headers=self._signed_headers(params or {}), timeout=10, verify=False)
        if response.status_code != 200:
            return {}
        try:
            data = json.loads(response.text or "{}")
        except Exception:
            return {}
        if str(data.get("code", "200")) not in ("200", "0", ""):
            return {}
        return data

    def _map_vod(self, item):
        item = item or {}
        pubdate = str(item.get("vodPubdate", "")).strip()
        year = pubdate.split("-")[0] if pubdate else ""
        remarks = [str(item.get("vodRemarks", "")).strip(), str(item.get("vodDoubanScore", "")).strip()]
        return {
            "vod_id": str(item.get("vodId", "")),
            "vod_name": str(item.get("vodName", "")),
            "vod_pic": str(item.get("vodPic", "")),
            "vod_remarks": "_".join([value for value in remarks if value]),
            "vod_year": year,
            "type_id": str(item.get("typeId", "")),
            "type_name": str(item.get("typeName", "")),
        }

    def _build_filters(self):
        classes = []
        filters = {}
        type_res = self._fetch_json("/api/mw-movie/anonymous/get/filer/type")
        for item in type_res.get("data", []):
            classes.append(
                {
                    "type_id": str(item.get("typeId", "")),
                    "type_name": str(item.get("typeName", "")),
                }
            )
        filter_res = self._fetch_json("/api/mw-movie/anonymous/v1/get/filer/list")
        filter_data = filter_res.get("data", {})
        for cls in classes:
            tid = cls["type_id"]
            filters[tid] = []
            current = (filter_data or {}).get(tid, {})
            for raw_key, (key, name) in self.class_name_map.items():
                values = [{"n": "全部", "v": ""}]
                if raw_key == "serialList":
                    values.extend(self.sort_values)
                else:
                    for item in current.get(raw_key, []):
                        label = str(item.get("itemText", "")).strip()
                        if not label:
                            continue
                        value_key = "itemValue" if raw_key == "typeList" else "itemText"
                        values.append({"n": label, "v": str(item.get(value_key, "")).strip()})
                if len(values) > 1:
                    filters[tid].append({"key": key, "name": name, "value": values})
        return classes, filters

    def _page_result(self, items, pg, limit=30):
        page = max(int(str(pg or 1)), 1)
        return {"page": page, "limit": limit, "total": page * limit + len(items), "list": items}

    def homeContent(self, filter):
        classes, filters = self._build_filters()
        home = self._fetch_json("/api/mw-movie/anonymous/home/hotSearch")
        return {
            "class": classes,
            "filters": filters,
            "list": [self._map_vod(item) for item in home.get("data", [])],
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = max(int(str(pg or 1)), 1)
        values = dict(extend or {})
        payload = {
            "area": str(values.get("area", "")),
            "lang": str(values.get("lang", "")),
            "pageNum": str(page),
            "pageSize": "30",
            "sort": str(values.get("by", "1")),
            "sortBy": "1",
            "type": str(values.get("type", "")),
            "type1": str(tid),
            "v_class": str(values.get("class", "")),
            "year": str(values.get("year", "")),
        }
        result = self._fetch_json("/api/mw-movie/anonymous/video/list", payload)
        items = [self._map_vod(item) for item in ((result.get("data") or {}).get("list") or [])]
        return self._page_result(items, page, 30)

    def searchContent(self, key, quick, pg="1"):
        page = max(int(str(pg or 1)), 1)
        keyword = str(key or "").strip()
        if not keyword:
            return {"page": page, "limit": 30, "total": 0, "list": []}
        result = self._fetch_json(
            "/api/mw-movie/anonymous/video/searchByWordPageable",
            {"keyword": keyword, "pageNum": str(page), "pageSize": "30"},
        )
        items = [self._map_vod(item) for item in ((result.get("data") or {}).get("list") or [])]
        return self._page_result(items, page, 30)

    def _build_play_id(self, vod_id, nid):
        return f"{str(vod_id).strip()}@{str(nid).strip()}"

    def _parse_play_id(self, value):
        parts = str(value or "").split("@", 1)
        if len(parts) != 2:
            return {"id": "", "nid": ""}
        sid = parts[0].strip()
        nid = parts[1].strip()
        if not sid or not nid:
            return {"id": "", "nid": ""}
        return {"id": sid, "nid": nid}

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip()
        if not vod_id:
            return {"list": []}
        result = self._fetch_json("/api/mw-movie/anonymous/video/detail", {"id": vod_id})
        data = result.get("data") or {}
        if not data:
            return {"list": []}
        episodes = []
        for item in data.get("episodeList", []):
            name = str(item.get("name", "")).strip()
            nid = str(item.get("nid", "")).strip()
            if not name or not nid:
                continue
            episodes.append(f"{name}${self._build_play_id(data.get('vodId', vod_id), nid)}")
        vod = {
            "vod_id": str(data.get("vodId", vod_id)),
            "vod_name": str(data.get("vodName", "")),
            "vod_pic": str(data.get("vodPic", "")),
            "type_name": str(data.get("vodClass", "")),
            "vod_remarks": str(data.get("vodRemarks", "")),
            "vod_year": str(data.get("vodYear", "")),
            "vod_area": str(data.get("vodArea", "")),
            "vod_lang": str(data.get("vodLang", "")),
            "vod_director": str(data.get("vodDirector", "")),
            "vod_actor": str(data.get("vodActor", "")),
            "vod_content": str(data.get("vodContent", "")),
            "vod_play_from": "金牌线路" if episodes else "",
            "vod_play_url": "#".join(episodes),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        parsed = self._parse_play_id(id)
        if not parsed["id"] or not parsed["nid"]:
            return {"parse": 0, "playUrl": "", "url": "", "header": {}}
        result = self._fetch_json(
            "/api/mw-movie/anonymous/v2/video/episode/url",
            {"clientType": "3", "id": parsed["id"], "nid": parsed["nid"]},
        )
        for item in ((result.get("data") or {}).get("list") or []):
            url = str(item.get("url", "")).strip()
            if url:
                return {
                    "parse": 0,
                    "playUrl": "",
                    "url": url,
                    "header": {"User-Agent": self.mobile_ua},
                }
        return {"parse": 0, "playUrl": "", "url": "", "header": {}}
