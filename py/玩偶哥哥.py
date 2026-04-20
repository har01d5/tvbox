# coding=utf-8
import re
import sys
from urllib.parse import urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "玩偶哥哥"
        self.host = "http://wogg.xxooo.cf"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "1", "type_name": "玩偶电影"},
            {"type_id": "2", "type_name": "玩偶剧集"},
            {"type_id": "3", "type_name": "玩偶动漫"},
            {"type_id": "4", "type_name": "玩偶综艺"},
            {"type_id": "44", "type_name": "臻彩视界"},
            {"type_id": "6", "type_name": "玩偶短剧"},
            {"type_id": "5", "type_name": "玩偶音乐"},
            {"type_id": "46", "type_name": "玩偶纪录"},
        ]
        self.pan_patterns = [
            ("baidu", "百度资源", r"pan\.baidu\.com|yun\.baidu\.com"),
            ("a139", "139资源", r"yun\.139\.com"),
            ("a189", "天翼资源", r"cloud\.189\.cn"),
            ("a123", "123资源", r"123684\.com|123865\.com|123912\.com|123pan\.com"),
            ("a115", "115资源", r"115\.com"),
            ("quark", "夸克资源", r"pan\.quark\.cn"),
            ("xunlei", "迅雷资源", r"pan\.xunlei\.com"),
            ("aliyun", "阿里资源", r"aliyundrive\.com|alipan\.com"),
            ("uc", "UC资源", r"drive\.uc\.cn"),
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def homeVideoContent(self):
        return {"list": []}

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _fix_img_url(self, img_url):
        raw = str(img_url or "").strip()
        if not raw:
            return ""
        if raw.startswith("/db.php?url="):
            return self._build_url(raw)
        if re.search(r"^https?://[^/]*gimg\d*\.baidu\.com/gimg/", raw, re.I) and "src=data:image/" in raw:
            return ""
        return raw

    def _detect_pan_type(self, url):
        raw = str(url or "").strip()
        for pan_type, title, pattern in self.pan_patterns:
            if re.search(pattern, raw, re.I):
                return pan_type, title
        return "", ""
