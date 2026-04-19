# coding=utf-8
import json
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "低端影视"
        self.host = "https://ddys.io"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "series", "type_name": "剧集"},
            {"type_id": "movie", "type_name": "电影"},
            {"type_id": "variety", "type_name": "综艺"},
            {"type_id": "anime", "type_name": "动漫"},
        ]
        self.filter_def = {
            "movie": {"cateId": "movie"},
            "series": {"cateId": "series"},
            "variety": {"cateId": "variety"},
            "anime": {"cateId": "anime"},
        }
        self.filters = {
            key: [
                {"key": "class", "name": "剧情", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "area", "name": "地区", "init": "", "value": [{"n": "全部", "v": ""}]},
                {"key": "year", "name": "年份", "init": "", "value": [{"n": "全部", "v": ""}]},
                {
                    "key": "by",
                    "name": "排序",
                    "init": "",
                    "value": [
                        {"n": "时间", "v": ""},
                        {"n": "评分", "v": "rating/"},
                        {"n": "热门", "v": "popular/"},
                    ],
                },
            ]
            for key in ["movie", "series", "variety", "anime"]
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
        values = dict(self.filter_def.get(str(tid), {"cateId": str(tid)}))
        values.update(self._normalize_ext(extend))
        path = (
            f"{values.get('by', '')}"
            f"{values.get('cateId', tid)}"
            f"{values.get('class', '')}"
            f"{values.get('area', '')}"
            f"{values.get('year', '')}"
            f"/page/{int(pg)}"
        )
        return self._build_url(path)
