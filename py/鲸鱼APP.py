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
