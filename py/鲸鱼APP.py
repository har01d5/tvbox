# coding=utf-8
import base64
import json
import re
import sys
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base.spider import Spider as BaseSpider

sys.path.append("..")

AES_KEY = "AAdgrdghjfgsABC1"
AES_IV = "AAdgrdghjfgsABC1"


class Spider(BaseSpider):
    def __init__(self):
        self.name = "鲸鱼APP"
        self.host = ""
        self.ua = "okhttp/3.10.0"
        self.api_path = "/api.php/qijiappapi.index"
        self.init_endpoint = "initV122"
        self.search_endpoint = "searchList"
        self.search_verify = False
        self.init_data = None

    def getName(self):
        return self.name

    SITE_URL = "https://jingyu4k-1312635929.cos.ap-nanjing.myqcloud.com/juyu3.json"

    def init(self, extend=""):
        if self.host:
            return
        headers = {"User-Agent": self.ua}
        try:
            rsp = self.fetch(self.SITE_URL, headers=headers, timeout=10, verify=False)
            host = rsp.text.strip().rstrip("/")
            if not host.startswith("http"):
                host = "http://" + host
            self.host = host
        except Exception as e:
            self.log(f"获取host失败: {e}")
            raise
        try:
            data = self._api_post(self.init_endpoint)
            if data and data.get("config", {}).get("system_search_verify_status"):
                self.search_verify = True
            self.init_data = data
        except Exception as e:
            self.log(f"初始化数据失败: {e}")

    def _aes_encrypt(self, plaintext):
        key = AES_KEY.encode("utf-8")
        iv = AES_IV.encode("utf-8")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded = pad(plaintext.encode("utf-8"), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode("utf-8")

    def _aes_decrypt(self, ciphertext):
        key = AES_KEY.encode("utf-8")
        iv = AES_IV.encode("utf-8")
        raw = base64.b64decode(ciphertext)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(raw), AES.block_size)
        return decrypted.decode("utf-8")

    def _api_post(self, endpoint, payload=None):
        if payload is None:
            payload = {}
        ep = f"/{endpoint}" if not endpoint.startswith("/") else endpoint
        url = f"{self.host}{self.api_path}{ep}"
        headers = {
            "User-Agent": self.ua,
            "Accept-Encoding": "gzip",
        }
        rsp = self.post(url, json=payload, headers=headers, timeout=15, verify=False)
        data = rsp.json().get("data")
        if not data:
            return None
        try:
            return json.loads(self._aes_decrypt(data))
        except Exception as e:
            self.log(f"JSON解析失败: {e}")
            return None

    CATEGORY_BLOCKED = ["全部"]
    CATEGORY_FORCE_ORDER = ["电影", "电视剧", "综艺", "动漫", "短剧"]
    AREA_MERGE_DISPLAY = "大陆"
    AREA_MERGE_LIST = ["中国大陆", "大陆", "内地"]

    def _process_classes(self, type_list):
        order_map = {n: i for i, n in enumerate(self.CATEGORY_FORCE_ORDER)}
        classes = [
            {"type_id": t["type_id"], "type_name": t["type_name"]}
            for t in type_list
            if t["type_name"] not in self.CATEGORY_BLOCKED
        ]
        classes.sort(key=lambda c: order_map.get(c["type_name"], 999))
        return classes

    def _process_area_filter(self, area_list):
        if not area_list:
            return area_list
        merge_set = set(self.AREA_MERGE_LIST)
        filtered = [a for a in area_list if a not in merge_set]
        has_merge = any(a in merge_set for a in area_list)
        if has_merge:
            try:
                idx = filtered.index("全部")
                filtered.insert(idx + 1, self.AREA_MERGE_DISPLAY)
            except ValueError:
                filtered.insert(0, self.AREA_MERGE_DISPLAY)
        return filtered

    def _convert_filters(self, type_list):
        name_map = {"class": "类型", "area": "地区", "lang": "语言", "year": "年份", "sort": "排序"}
        current_year = str(time.localtime().tm_year)
        filters = {}
        for t in type_list:
            arr = []
            for f in t.get("filter_type_list", []):
                key = "by" if f["name"] == "sort" else f["name"]
                values = list(f.get("list", []))
                if f["name"] == "area":
                    values = self._process_area_filter(values)
                if f["name"] == "year" and current_year not in values:
                    try:
                        idx = values.index("全部")
                        values.insert(idx + 1, current_year)
                    except ValueError:
                        values.insert(0, current_year)
                arr.append({
                    "key": key,
                    "name": name_map.get(f["name"], f["name"]),
                    "value": [{"n": v, "v": v} for v in values],
                })
            filters[t["type_id"]] = arr
        return filters

    def homeContent(self, filter):
        self.init()
        data = self.init_data
        if not data:
            return {"class": [], "filters": {}}
        classes = self._process_classes(data.get("type_list", []))
        filters = self._convert_filters(data.get("type_list", []))
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        self.init()
        if not self.init_data:
            return {"list": []}
        videos = []
        for t in self.init_data.get("type_list", []):
            for item in t.get("recommend_list", []):
                videos.append({
                    "vod_id": str(item.get("vod_id", "")),
                    "vod_name": item.get("vod_name", ""),
                    "vod_pic": item.get("vod_pic", ""),
                    "vod_remarks": item.get("vod_remarks", ""),
                })
        return {"list": videos}

    def _merge_area_search(self, type_id, page, base_filters):
        all_results = []
        seen = set()
        for area_val in self.AREA_MERGE_LIST:
            try:
                payload = {"type_id": type_id, "page": page, "area": area_val}
                payload.update(base_filters)
                res = self._api_post("typeFilterVodList", payload)
                for item in (res or {}).get("recommend_list", []):
                    vid = str(item.get("vod_id", ""))
                    if vid not in seen:
                        seen.add(vid)
                        all_results.append({
                            "vod_id": vid,
                            "vod_name": item.get("vod_name", ""),
                            "vod_pic": item.get("vod_pic", ""),
                            "vod_remarks": item.get("vod_remarks", ""),
                        })
            except Exception as e:
                self.log(f"聚合搜索地区[{area_val}]失败: {e}")
        return all_results

    def categoryContent(self, tid, pg, filter, extend):
        self.init()
        page = int(pg)
        ext = extend or {}

        if ext.get("area") == self.AREA_MERGE_DISPLAY:
            base = {k: v for k, v in ext.items() if k != "area"}
            base.setdefault("year", "全部")
            base.setdefault("sort", "最新")
            base.setdefault("lang", "全部")
            base.setdefault("class", "全部")
            merged = self._merge_area_search(tid, page, base)
            return {"list": merged, "page": page, "limit": 90, "total": 999999}

        payload = {
            "type_id": tid,
            "page": page,
            "area": ext.get("area", "全部"),
            "year": ext.get("year", "全部"),
            "sort": ext.get("by", ext.get("sort", "最新")),
            "lang": ext.get("lang", "全部"),
            "class": ext.get("class", "全部"),
        }
        res = self._api_post("typeFilterVodList", payload)
        items = []
        for item in (res or {}).get("recommend_list", []):
            items.append({
                "vod_id": str(item.get("vod_id", "")),
                "vod_name": item.get("vod_name", ""),
                "vod_pic": item.get("vod_pic", ""),
                "vod_remarks": item.get("vod_remarks", ""),
            })
        return {"list": items, "page": page, "limit": 90, "total": 999999}

    JUNK_KEYWORDS = ["防走丢", "群", "防失群", "官网"]

    def detailContent(self, ids):
        self.init()
        vod_id = ids[0]
        data = None
        for endpoint in ["vodDetail", "vodDetail2"]:
            try:
                data = self._api_post(endpoint, {"vod_id": vod_id})
                if data:
                    break
            except Exception:
                continue
        if not data:
            return {"list": []}

        vod = data.get("vod", {})
        lines = []
        name_count = {}
        line_id = 1

        for line in data.get("vod_play_list", []):
            info = line.get("player_info", {})
            name = info.get("show", "")

            if any(kw in name for kw in self.JUNK_KEYWORDS):
                name = f"{line_id}线"
                info["show"] = name

            count = name_count.get(name, 0) + 1
            name_count[name] = count
            if count > 1:
                name = f"{name}{count}"
                info["show"] = name

            urls = line.get("urls", [])
            if not urls:
                line_id += 1
                continue

            play_items = []
            for ep in urls:
                payload = ",".join([
                    info.get("parse", ""),
                    ep.get("url", ""),
                    "token+" + ep.get("token", ""),
                    str(info.get("player_parse_type", "")),
                    str(info.get("parse_type", "")),
                ])
                play_items.append(f"{ep.get('name', '')}${name}@@direct@@{payload}")

            if play_items:
                lines.append({
                    "display": name,
                    "urls": "#".join(play_items),
                })
            line_id += 1

        return {
            "list": [{
                "vod_id": vod_id,
                "vod_name": vod.get("vod_name", ""),
                "vod_pic": vod.get("vod_pic", ""),
                "vod_remarks": vod.get("vod_remarks", ""),
                "vod_content": vod.get("vod_content", ""),
                "vod_actor": (vod.get("vod_actor") or "").replace("演员", ""),
                "vod_director": (vod.get("vod_director") or "").replace("导演", ""),
                "vod_year": (vod.get("vod_year") or "") + "年" if vod.get("vod_year") else "",
                "vod_area": vod.get("vod_area", ""),
                "vod_play_from": "$$$".join(l["display"] for l in lines),
                "vod_play_url": "$$$".join(l["urls"] for l in lines),
            }]
        }
