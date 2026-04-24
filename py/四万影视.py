# coding=utf-8
import json
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "四万影视"
        self.host = "https://40000.me"
        self.api = self.host + "/api/maccms"
        self.fallback_pic = self.host + "/public/favicon.png"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
            ),
            "Referer": self.host + "/",
            "Accept": "*/*",
        }
        self.classes = [
            {"type_id": "20", "type_name": "电影"},
            {"type_id": "30", "type_name": "电视剧"},
            {"type_id": "39", "type_name": "动漫"},
            {"type_id": "45", "type_name": "综艺"},
            {"type_id": "32", "type_name": "欧美"},
        ]
        self.filter_type_options = {
            "20": [
                {"n": "全部", "v": "20"},
                {"n": "动作片", "v": "21"},
                {"n": "喜剧片", "v": "22"},
                {"n": "恐怖片", "v": "23"},
                {"n": "科幻片", "v": "24"},
                {"n": "爱情片", "v": "25"},
                {"n": "剧情片", "v": "26"},
                {"n": "战争片", "v": "27"},
                {"n": "纪录片", "v": "28"},
                {"n": "理论片", "v": "29"},
                {"n": "预告片", "v": "52"},
                {"n": "电影解说", "v": "51"},
            ],
            "30": [
                {"n": "全部", "v": "30"},
                {"n": "国产剧", "v": "31"},
                {"n": "欧美剧", "v": "32"},
                {"n": "香港剧", "v": "33"},
                {"n": "韩国剧", "v": "34"},
                {"n": "台湾剧", "v": "35"},
                {"n": "日本剧", "v": "36"},
                {"n": "海外剧", "v": "37"},
                {"n": "泰国剧", "v": "38"},
                {"n": "短剧大全", "v": "58"},
            ],
            "39": [
                {"n": "全部", "v": "39"},
                {"n": "国产动漫", "v": "40"},
                {"n": "日韩动漫", "v": "41"},
                {"n": "欧美动漫", "v": "42"},
                {"n": "港台动漫", "v": "43"},
                {"n": "海外动漫", "v": "44"},
                {"n": "动画片", "v": "50"},
            ],
            "45": [
                {"n": "全部", "v": "45"},
                {"n": "大陆综艺", "v": "46"},
                {"n": "港台综艺", "v": "47"},
                {"n": "日韩综艺", "v": "48"},
                {"n": "欧美综艺", "v": "49"},
            ],
            "32": [
                {"n": "全部", "v": "32"},
                {"n": "欧美剧", "v": "32"},
                {"n": "欧美动漫", "v": "42"},
                {"n": "欧美综艺", "v": "49"},
                {"n": "海外剧", "v": "37"},
            ],
        }
        self.type_name_map = {item["type_id"]: item["type_name"] for item in self.classes}
        self.subtype_parent_map = {
            "20": "20",
            "21": "20",
            "22": "20",
            "23": "20",
            "24": "20",
            "25": "20",
            "26": "20",
            "27": "20",
            "28": "20",
            "29": "20",
            "51": "20",
            "52": "20",
            "30": "30",
            "31": "30",
            "32": "32",
            "33": "30",
            "34": "30",
            "35": "30",
            "36": "30",
            "37": "32",
            "38": "30",
            "58": "30",
            "39": "39",
            "40": "39",
            "41": "39",
            "42": "32",
            "43": "39",
            "44": "39",
            "50": "39",
            "45": "45",
            "46": "45",
            "47": "45",
            "48": "45",
            "49": "32",
        }
        self.filters = self._build_filters()

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _build_filters(self):
        years = [{"n": "全部", "v": ""}]
        for year in range(2026, 1999, -1):
            years.append({"n": str(year), "v": str(year)})
        sort_values = [
            {"n": "时间", "v": "time"},
            {"n": "人气", "v": "hits"},
            {"n": "评分", "v": "score"},
            {"n": "点赞", "v": "up"},
        ]
        filters = {}
        for item in self.classes:
            type_id = item["type_id"]
            filters[type_id] = [
                {"key": "subType", "name": "分类", "init": type_id, "value": self.filter_type_options[type_id]},
                {"key": "year", "name": "年代", "init": "", "value": years},
                {"key": "sort", "name": "排序", "init": "time", "value": list(sort_values)},
            ]
        return filters

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        return {"list": []}

    def _api_get(self, params):
        response = self.fetch(
            self.api,
            params=params,
            headers=dict(self.headers),
            timeout=10,
        )
        if response.status_code != 200:
            raise ValueError("api request failed")
        data = json.loads(response.text or "{}")
        if not isinstance(data, dict):
            raise ValueError("api response is not object")
        return data
