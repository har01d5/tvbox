# coding=utf-8
import base64
import hashlib
import json
import sys
import time
from urllib.parse import quote_plus

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ModuleNotFoundError:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad, unpad

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "即看影视"
        self.host_config_url = "https://skyappdata-1321528676.cos.accelerate.myqcloud.com/4kapp/appipr.txt"
        self.aes_key = "ygcnbckhcuvygdyb"
        self.aes_iv = "4023892775143708"
        self.ck_key = "ygcnbcrvaervztmw"
        self.ck_iv = "1212164105143708"
        self.user_agent = "Dart/2.10 (dart:io)"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip",
        }
        self.api_host = ""
        self.auth_token = ""
        self.config_data = {}
        self.is_ready = False

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _resolve_api_host(self):
        response = self.fetch(self.host_config_url, headers=self.headers, timeout=10, verify=False)
        return str(getattr(response, "text", "")).strip().rstrip("/")

    def _md5(self, text):
        return hashlib.md5(str(text).encode("utf-8")).hexdigest()

    def _sk_decrypt(self, text):
        value = str(text or "")
        prefix = "FROMSKZZJM"
        if not value.startswith(prefix):
            return value
        encrypted_hex = value[len(prefix):]
        cipher = AES.new(self.aes_key.encode("utf-8"), AES.MODE_CBC, self.aes_iv.encode("utf-8"))
        return unpad(cipher.decrypt(bytes.fromhex(encrypted_hex)), AES.block_size).decode("utf-8")

    def _ck_encrypt(self, text):
        first = base64.b64encode(str(text).encode("utf-8"))
        second = base64.b64encode(first)
        cipher = AES.new(self.ck_key.encode("utf-8"), AES.MODE_CBC, self.ck_iv.encode("utf-8"))
        encrypted = cipher.encrypt(pad(second, AES.block_size)).hex()
        return base64.b64encode(encrypted.encode("utf-8")).decode("utf-8")

    def _safe_json(self, text, default=None):
        try:
            return json.loads(text)
        except (TypeError, json.JSONDecodeError):
            return {} if default is None else default

    def _fetch_auth_token(self):
        sign = self._md5(self.aes_key + self.aes_iv)
        ck = self._ck_encrypt(f"{self.api_host}##5483##{int(time.time() * 1000)}##ckzmbc")
        response = self.post(
            f"{self.api_host}/get_config",
            json={"sign": sign, "ck": ck},
            headers=dict(self.headers, **{"Content-Type": "application/json"}),
            timeout=15,
            verify=False,
        )
        self.auth_token = self._sk_decrypt(getattr(response, "text", ""))

    def _fetch_app_config(self):
        response = self.fetch(
            f"{self.api_host}/app/config",
            headers=dict(self.headers, **{"Authorization": f"Bearer {self.auth_token}"}),
            timeout=15,
            verify=False,
        )
        self.config_data = self._safe_json(self._sk_decrypt(getattr(response, "text", "")), default={})

    def _ensure_ready(self):
        if self.is_ready:
            return
        self.api_host = self._resolve_api_host()
        if len(self.aes_key) != 16 or len(self.aes_iv) != 16:
            raise ValueError("invalid aes config")
        self._fetch_auth_token()
        self._fetch_app_config()
        self.is_ready = True

    def _fetch_api(self, path, params=None):
        self._ensure_ready()
        query = []
        for key, value in (params or {}).items():
            if value in (None, ""):
                continue
            query.append(f"{quote_plus(str(key))}={quote_plus(str(value))}")
        url = f"{self.api_host}{path}"
        if query:
            url += "?" + "&".join(query)
        response = self.fetch(
            url,
            headers=dict(self.headers, **{"Authorization": f"Bearer {self.auth_token}"}),
            timeout=15,
            verify=False,
        )
        return self._safe_json(self._sk_decrypt(getattr(response, "text", "")), default={})

    def _fetch_filters(self, classes):
        result = {}
        mappings = {
            "extendtype": ("class", "类型"),
            "area": ("area", "地区"),
            "lang": ("lang", "语言"),
            "year": ("year", "年份"),
        }
        for item in classes or []:
            payload = self._fetch_api("/sk-api/type/alltypeextend", {"typeId": item.get("type_id")})
            data = payload.get("data") or {}
            entries = []
            for source_key, (target_key, label) in mappings.items():
                raw = str(data.get(source_key) or "").strip()
                if not raw:
                    continue
                values = [{"n": "全部", "v": ""}]
                values.extend({"n": value.strip(), "v": value.strip()} for value in raw.split(",") if value.strip())
                entries.append({"key": target_key, "name": label, "init": "", "value": values})
            entries.append(
                {
                    "key": "sort",
                    "name": "排序",
                    "init": "updateTime",
                    "value": [
                        {"n": "最新", "v": "updateTime"},
                        {"n": "人气", "v": "hot"},
                        {"n": "评分", "v": "score"},
                    ],
                }
            )
            result[str(item.get("type_id"))] = entries
        return result

    def homeVideoContent(self):
        data = self._fetch_api("/sk-api/vod/list", {"page": 1, "limit": 12, "type": "randomlikeindex"})
        return {"list": data.get("data") or []}

    def homeContent(self, filter):
        home = self._fetch_api("/sk-api/type/list", {})
        classes = []
        for item in home.get("data") or []:
            if isinstance(item, dict) and item.get("type_id"):
                classes.append({"type_id": item.get("type_id"), "type_name": item.get("type_name", "")})
        return {
            "class": classes,
            "filters": self._fetch_filters(classes),
            "list": self.homeVideoContent()["list"],
        }

    def _page_result(self, items, pg, limit):
        values = list(items or [])
        return {
            "page": int(pg),
            "limit": limit,
            "total": len(values),
            "list": values,
        }

    def categoryContent(self, tid, pg, filter, extend):
        options = dict(extend or {})
        try:
            data = self._fetch_api(
                "/sk-api/vod/list",
                {
                    "typeId": str(tid),
                    "page": int(pg),
                    "limit": 18,
                    "type": options.get("sort", "updateTime"),
                    "area": options.get("area", ""),
                    "lang": options.get("lang", ""),
                    "year": options.get("year", ""),
                    "mtype": "",
                    "extendtype": options.get("class", ""),
                },
            )
            return self._page_result(data.get("data") or [], pg, 18)
        except Exception:
            return self._page_result([], pg, 18)

    def searchContent(self, key, quick, pg="1"):
        try:
            data = self._fetch_api(
                "/sk-api/search/pages",
                {"keyword": str(key or ""), "page": int(pg), "limit": 10, "typeId": -1},
            )
            return self._page_result(data.get("data") or [], pg, 10)
        except Exception:
            return self._page_result([], pg, 10)
