# coding=utf-8
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    BASE_URL = "https://1.star2.cn"
    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
    )
    CATEGORIES = [
        ("ju", "国剧"),
        ("zy", "综艺"),
        ("mv", "电影"),
        ("rh", "日韩"),
        ("ym", "英美"),
        ("wj", "外剧"),
        ("dm", "动漫"),
    ]

    def __init__(self):
        self.name = "双星"
        self.cookie = ""

    def init(self, extend=""):
        response = self.fetch(
            self.BASE_URL,
            headers={"User-Agent": self.UA, "Referer": self.BASE_URL},
            allow_redirects=False,
            timeout=15,
        )
        if response.status_code != 200:
            return None
        self.cookie = "; ".join([f"{name}={value}" for name, value in dict(response.cookies).items()])
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": [{"type_id": type_id, "type_name": type_name} for type_id, type_name in self.CATEGORIES]}

    def homeVideoContent(self):
        return {"list": []}

    def _headers(self):
        headers = {"User-Agent": self.UA, "Referer": self.BASE_URL}
        if self.cookie:
            headers["cookie"] = self.cookie
        return headers

    def _detect_pan_type(self, link):
        text = str(link or "").strip().lower()
        if "quark" in text:
            return "quark"
        if "115.com" in text:
            return "115"
        if "cloud.189.cn" in text:
            return "tianyi"
        if "drive.uc.cn" in text or "uc.cn" in text:
            return "uc"
        if "pan.baidu.com" in text:
            return "baidu"
        if "xunlei" in text:
            return "xunlei"
        if "123pan" in text:
            return "123pan"
        if "caiyun" in text or "139.com" in text:
            return "yd"
        if "aliyundrive" in text or "alipan" in text:
            return "ali"
        return ""
