# coding=utf-8
import base64
import json
import sys
from datetime import datetime
from urllib.parse import unquote

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "黑猫APP"
        self.host = "http://app1-0-0.87333.cc"
        self.api_path = "/api.php/getappapi"
        self.user_agent = "okhttp/3.10.0"
        self.aes_key = "VwsHxkCViDXEExWa"
        self.aes_iv = "VwsHxkCViDXEExWa"
        self.category_config = {
            "blockedNames": ["伦理"],
            "renameMap": {},
            "forceOrder": ["电影", "连续剧", "综艺", "动漫", "短剧", "直播"],
        }
        self.area_merge_config = {
            "enabled": True,
            "displayName": "大陆",
            "mergeList": ["中国大陆", "大陆", "内地"],
        }
        self.line_config = {
            "高清线路1": {"displayName": "🐈‍⬛高清线路", "order": 301, "mode": "direct", "enabled": True},
            "标清线路2": {"displayName": "🐈‍⬛标清线路1", "order": 302, "mode": "direct", "enabled": True},
            "标清线路3": {"displayName": "🐈‍⬛标清线路2", "order": 303, "mode": "direct", "enabled": True},
        }

    def init(self, extend=""):
        self.search_api = "searchList"
        self.init_api = "initV119"
        self.search_verify = False
        return None

    def getName(self):
        return self.name

    def _headers(self):
        return {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip",
        }

    def homeVideoContent(self):
        return {"list": []}

    def _build_api_url(self, endpoint):
        path = str(endpoint or "").lstrip("/")
        return f"{self.host}{self.api_path}.index/{path}"

    def _api_post(self, endpoint, payload=None):
        data = {} if payload is None else dict(payload)
        response = self.post(
            self._build_api_url(endpoint),
            data=data,
            headers=self._headers(),
            timeout=10,
            verify=False,
        )
        body = json.loads(response.text or "{}")
        if not body.get("data"):
            return None
        return json.loads(self._aes_decrypt(body["data"]))

    def _aes_encrypt(self, text):
        padder = PKCS7(128).padder()
        data = padder.update(str(text).encode("utf-8")) + padder.finalize()
        cipher = Cipher(algorithms.AES(self.aes_key.encode("utf-8")), modes.CBC(self.aes_iv.encode("utf-8")))
        encryptor = cipher.encryptor()
        return base64.b64encode(encryptor.update(data) + encryptor.finalize()).decode("utf-8")

    def _aes_decrypt(self, text):
        data = base64.b64decode(str(text or ""))
        cipher = Cipher(algorithms.AES(self.aes_key.encode("utf-8")), modes.CBC(self.aes_iv.encode("utf-8")))
        decryptor = cipher.decryptor()
        padded = decryptor.update(data) + decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")

    def _replace_code(self, text):
        replacements = {
            "y": "9",
            "口": "0",
            "q": "0",
            "u": "0",
            "o": "0",
            ">": "1",
            "d": "0",
            "b": "8",
            "已": "2",
            "D": "0",
            "五": "5",
        }
        return "".join(replacements.get(char, char) for char in str(text or ""))

    def _process_classes(self, type_list):
        blocked = set(self.category_config.get("blockedNames", []))
        rename_map = self.category_config.get("renameMap", {})
        order_map = {name: index for index, name in enumerate(self.category_config.get("forceOrder", []))}
        classes = [
            {
                "type_id": item.get("type_id", ""),
                "type_name": rename_map.get(item.get("type_name", ""), item.get("type_name", "")),
            }
            for item in type_list
            if item.get("type_name") not in blocked
        ]
        classes.sort(key=lambda item: order_map.get(item["type_name"], 999))
        return classes

    def _merge_area_filter(self, values):
        merge_values = set(self.area_merge_config.get("mergeList", []))
        raw_values = list(values)
        if not self.area_merge_config.get("enabled") or not any(value in merge_values for value in raw_values):
            return raw_values
        result = [value for value in raw_values if value not in merge_values]
        index = result.index("全部") + 1 if "全部" in result else 0
        result.insert(index, self.area_merge_config.get("displayName", "大陆"))
        return result

    def _convert_filters(self, type_list):
        name_map = {"class": "类型", "area": "地区", "lang": "语言", "year": "年份", "sort": "排序"}
        current_year = str(datetime.now().year)
        filters = {}
        for item in type_list:
            entries = []
            for config in item.get("filter_type_list", []):
                raw_name = config.get("name", "")
                values = list(config.get("list", []))
                if raw_name == "area":
                    values = self._merge_area_filter(values)
                if raw_name == "year" and current_year not in values:
                    index = values.index("全部") + 1 if "全部" in values else 0
                    values.insert(index, current_year)
                entries.append(
                    {
                        "key": "by" if raw_name == "sort" else raw_name,
                        "name": name_map.get(raw_name, raw_name),
                        "value": [{"n": value, "v": value} for value in values],
                    }
                )
            filters[item.get("type_id", "")] = entries
        return filters

    def homeContent(self, filter):
        init_data = self._api_post(self.init_api) or {"type_list": [], "config": {}}
        self.search_verify = bool(init_data.get("config", {}).get("system_search_verify_status"))
        return {
            "class": self._process_classes(init_data.get("type_list", [])),
            "filters": self._convert_filters(init_data.get("type_list", [])),
            "list": [vod for item in init_data.get("type_list", []) for vod in item.get("recommend_list", [])],
        }

    def _page_result(self, items, pg, limit=90, total=None):
        page = int(pg)
        return {
            "page": page,
            "limit": limit,
            "total": len(items) if total is None else total,
            "list": items,
        }

    def _merge_area_search(self, tid, pg, extend):
        seen = set()
        merged = []
        for area in self.area_merge_config.get("mergeList", []):
            payload = {
                "type_id": str(tid),
                "page": str(pg),
                "area": area,
                "year": extend.get("year", "全部"),
                "sort": extend.get("by", "最新"),
                "lang": extend.get("lang", "全部"),
                "class": extend.get("class", "全部"),
            }
            result = self._api_post("typeFilterVodList", payload) or {}
            for item in result.get("recommend_list", []):
                vod_id = item.get("vod_id")
                if vod_id in seen:
                    continue
                seen.add(vod_id)
                merged.append(item)
        return merged

    def categoryContent(self, tid, pg, filter, extend):
        options = dict(extend or {})
        if options.get("area") == self.area_merge_config.get("displayName"):
            return self._page_result(self._merge_area_search(tid, pg, options), pg)
        payload = {
            "type_id": str(tid),
            "page": str(pg),
            "area": options.get("area", "全部"),
            "year": options.get("year", "全部"),
            "sort": options.get("by", "最新"),
            "lang": options.get("lang", "全部"),
            "class": options.get("class", "全部"),
        }
        result = self._api_post("typeFilterVodList", payload) or {}
        return self._page_result(result.get("recommend_list", []), pg)

    def searchContent(self, key, quick, pg="1"):
        payload = {
            "keywords": str(key or ""),
            "type_id": "0",
            "page": str(pg),
        }
        result = self._api_post(self.search_api, payload) or {}
        keyword = str(key or "").strip().lower()
        items = []
        for item in result.get("search_list", []):
            vod_class = str(item.get("vod_class", ""))
            text = " ".join(
                [
                    str(item.get("vod_name", "")),
                    str(item.get("vod_remarks", "")),
                    vod_class,
                ]
            ).lower()
            if "伦理" in vod_class:
                continue
            if keyword and keyword not in text:
                continue
            items.append(
                {
                    "vod_id": item.get("vod_id", ""),
                    "vod_name": item.get("vod_name", ""),
                    "vod_pic": item.get("vod_pic", ""),
                    "vod_remarks": " ".join(
                        value for value in [str(item.get("vod_year", "")), vod_class] if value
                    ).strip(),
                }
            )
        return self._page_result(items, pg)

    def _get_line_config(self, name):
        return self.line_config.get(str(name or ""))

    def _line_display(self, name):
        config = self._get_line_config(name)
        return config.get("displayName", name) if config else name

    def _line_order(self, name):
        config = self._get_line_config(name)
        return config.get("order", 999) if config else 999

    def _line_mode(self, name):
        config = self._get_line_config(name)
        return config.get("mode", "direct") if config else "direct"

    def _line_blocked(self, name):
        config = self._get_line_config(name)
        return bool(config) and config.get("enabled") is False

    def _player_headers(self):
        return {"User-Agent": "Dalvik/2.1.0 (Linux; Android 14)"}

    def detailContent(self, ids):
        items = []
        for vod_id in ids:
            payload = {"vod_id": str(vod_id)}
            data = self._api_post("vodDetail", payload) or self._api_post("vodDetail2", payload)
            if not data:
                continue
            lines = []
            name_count = {}
            fallback_index = 1
            for line in data.get("vod_play_list", []):
                player_info = line.get("player_info", {})
                raw_name = str(player_info.get("show", ""))
                if any(keyword in raw_name for keyword in ["防走丢", "群", "防失群", "官网"]):
                    raw_name = f"{fallback_index}线"
                    fallback_index += 1
                name_count[raw_name] = name_count.get(raw_name, 0) + 1
                line_name = raw_name if name_count[raw_name] == 1 else f"{raw_name}{name_count[raw_name]}"
                if self._line_blocked(line_name):
                    continue
                urls = []
                for vod in line.get("urls", []):
                    payload_text = ",".join(
                        [
                            str(player_info.get("parse", "")),
                            str(vod.get("url", "")),
                            "token+" + str(vod.get("token", "")),
                            str(player_info.get("player_parse_type", "")),
                            str(player_info.get("parse_type", "")),
                        ]
                    )
                    urls.append(f"{vod.get('name', '')}${line_name}@@{self._line_mode(line_name)}@@{payload_text}")
                if urls:
                    lines.append(
                        {
                            "display": self._line_display(line_name),
                            "order": self._line_order(line_name),
                            "urls": "#".join(urls),
                        }
                    )
            lines.sort(key=lambda item: item["order"])
            vod = data.get("vod", {})
            items.append(
                {
                    "vod_id": str(vod_id),
                    "vod_name": vod.get("vod_name", ""),
                    "vod_pic": vod.get("vod_pic", ""),
                    "vod_remarks": vod.get("vod_remarks", ""),
                    "vod_content": vod.get("vod_content", ""),
                    "vod_actor": str(vod.get("vod_actor", "")).replace("演员", ""),
                    "vod_director": str(vod.get("vod_director", "")).replace("导演", ""),
                    "vod_year": f"{vod.get('vod_year', '')}年" if vod.get("vod_year") else "",
                    "vod_area": vod.get("vod_area", ""),
                    "vod_play_from": "$$$".join(line["display"] for line in lines),
                    "vod_play_url": "$$$".join(line["urls"] for line in lines),
                }
            )
        return {"list": items}

    def playerContent(self, flag, id, vipFlags):
        parts = str(id or "").split("@@", 2)
        line_name = parts[0] if len(parts) > 0 else ""
        mode = parts[1] if len(parts) > 1 else "direct"
        payload = parts[2] if len(parts) > 2 else ""
        if self._line_blocked(line_name):
            return {"parse": 0, "jx": 0, "url": "", "header": {}}
        if mode == "auto":
            return {"parse": 0, "jx": 0, "url": "", "header": {}}
        fields = payload.split(",", 4)
        while len(fields) < 5:
            fields.append("")
        parse_api, play_url, token_with_prefix, player_parse_type, parse_type = fields
        real_url = unquote(play_url)
        token = token_with_prefix.replace("token+", "", 1)
        if parse_type == "0":
            return {"parse": 0, "jx": 0, "url": real_url, "header": self._player_headers()}
        if parse_type == "2":
            return {"parse": 1, "jx": 1, "url": parse_api + real_url, "header": self._player_headers()}
        if player_parse_type == "2":
            response = self.fetch(parse_api + real_url, headers=self._headers(), timeout=10, verify=False)
            data = json.loads(response.text or "{}")
            if data.get("url"):
                return {"parse": 0, "jx": 0, "url": data.get("url", ""), "header": {}}
        result = self._api_post(
            "vodParse",
            {
                "parse_api": parse_api,
                "url": self._aes_encrypt(real_url),
                "player_parse_type": player_parse_type,
                "token": token,
            },
        ) or {}
        try:
            inner = json.loads(result.get("json", "{}"))
        except Exception:
            inner = {}
        return {"parse": 0, "jx": 0, "url": inner.get("url", ""), "header": {}}
