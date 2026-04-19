# coding=utf-8
import json
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "滴答影视"
        self.host = "https://www.didahd.pro"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "5", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "纪录片"},
        ]
        self.filter_def = {
            "1": {"cateId": "1", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "2": {"cateId": "2", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "3": {"cateId": "3", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "4": {"cateId": "4", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "5": {"cateId": "5", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
        }
        self.filters = {
            "1": [
                {"key": "class", "name": "按剧情", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "area", "name": "按地区", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "year", "name": "按年份", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "lang", "name": "按语言", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "sort", "name": "按排序", "init": "time", "value": [{"n": "时间", "v": "time"}]},
            ],
            "2": [
                {"key": "class", "name": "按剧情", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "area", "name": "按地区", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "year", "name": "按年份", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "lang", "name": "按语言", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "sort", "name": "按排序", "init": "time", "value": [{"n": "时间", "v": "time"}]},
            ],
            "3": [
                {"key": "year", "name": "按年份", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "lang", "name": "按语言", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "sort", "name": "按排序", "init": "time", "value": [{"n": "时间", "v": "time"}]},
            ],
            "4": [
                {"key": "year", "name": "按年份", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "lang", "name": "按语言", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "sort", "name": "按排序", "init": "time", "value": [{"n": "时间", "v": "time"}]},
            ],
            "5": [
                {"key": "class", "name": "按剧情", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "year", "name": "按年份", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "lang", "name": "按语言", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "sort", "name": "按排序", "init": "time", "value": [{"n": "时间", "v": "time"}]},
            ],
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        return {"list": []}

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _normalize_ext(self, extend):
        if isinstance(extend, dict):
            return extend
        if not extend:
            return {}
        try:
            return json.loads(str(extend))
        except Exception:
            return {}

    def _build_url(self, path):
        raw = self._stringify(path).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _build_category_url(self, tid, pg, extend):
        values = dict(self.filter_def.get(str(tid), {"cateId": str(tid), "sort": "time"}))
        values.update(self._normalize_ext(extend))
        path = (
            f"show/{values.get('cateId', tid)}-{values.get('area', '')}-{values.get('sort', 'time')}-"
            f"{values.get('class', '')}-{values.get('lang', '')}-{values.get('letter', '')}---{int(pg)}---"
            f"{values.get('year', '')}"
        )
        return self._build_url(path)
