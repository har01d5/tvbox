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

    def init(self, extend=""):
        pass

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
