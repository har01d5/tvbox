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

    def danmaku(self):
        return True

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

    def _type_name_by_id(self, type_id):
        raw = str(type_id or "")
        parent = self.subtype_parent_map.get(raw, raw)
        return self.type_name_map.get(parent, "")

    def _normalize_actor(self, value):
        return str(value or "").replace("&amp;#039;", "'").replace(" , ", ", ")

    def _normalize_vod(self, item):
        return {
            "vod_id": str(item.get("vod_id", "")),
            "vod_name": str(item.get("vod_name", "")),
            "vod_pic": str(item.get("vod_pic") or self.fallback_pic),
            "vod_remarks": str(item.get("vod_remarks", "")),
            "vod_year": str(item.get("vod_year", "")),
            "type_name": str(item.get("type_name") or self._type_name_by_id(item.get("type_id"))),
            "vod_actor": self._normalize_actor(item.get("vod_actor", "")),
        }

    def _page_result(self, items, page, total=0):
        return {
            "page": int(page),
            "limit": len(items),
            "total": int(total) if total else len(items),
            "list": items,
        }

    def _parse_play_groups(self, item):
        from_list = str(item.get("vod_play_from", "")).split("$$$")
        url_list = str(item.get("vod_play_url", "")).split("$$$")
        final_from = []
        final_url = []
        for index, raw_urls in enumerate(url_list):
            raw_urls = str(raw_urls or "").strip()
            if not raw_urls:
                continue
            line_name = str(from_list[index] if index < len(from_list) else "").strip() or f"线路{index + 1}"
            episodes = []
            for episode_index, part in enumerate(raw_urls.split("#")):
                chunks = str(part or "").split("$", 1)
                if len(chunks) > 1:
                    title = chunks[0].strip()
                    play_id = chunks[1].strip()
                else:
                    title = ""
                    play_id = chunks[0].strip() if chunks else ""
                title = title or f"第{episode_index + 1}集"
                if play_id:
                    episodes.append(f"{title}${play_id}")
            if episodes:
                final_from.append(line_name)
                final_url.append("#".join(episodes))
        return {"vod_play_from": "$$$".join(final_from), "vod_play_url": "$$$".join(final_url)}

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

    def categoryContent(self, tid, pg, filter, extend):
        page = max(int(pg), 1)
        values = dict(extend or {})
        params = {
            "ac": "detail",
            "t": str(values.get("subType") or tid),
            "pg": page,
            "by": str(values.get("sort") or "time"),
        }
        year = str(values.get("year") or "").strip()
        if year:
            params["h"] = year
        try:
            data = self._api_get(params)
        except ValueError:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        items = [self._normalize_vod(item) for item in data.get("list", [])]
        return self._page_result(items, data.get("page", page), data.get("total", 0))

    def searchContent(self, key, quick, pg="1"):
        page = max(int(pg), 1)
        keyword = str(key or "").strip()
        if not keyword:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        try:
            data = self._api_get({"ac": "detail", "wd": keyword, "pg": page})
        except ValueError:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        items = [self._normalize_vod(item) for item in data.get("list", [])]
        return self._page_result(items, data.get("page", page), data.get("total", 0))

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip()
        if not vod_id:
            return {"list": []}
        try:
            data = self._api_get({"ac": "detail", "ids": vod_id})
        except ValueError:
            return {"list": []}
        item = (data.get("list") or [None])[0]
        if not item:
            return {"list": []}
        normalized = self._normalize_vod(item)
        play_data = self._parse_play_groups(item)
        return {
            "list": [
                {
                    "vod_id": normalized["vod_id"],
                    "vod_name": normalized["vod_name"],
                    "vod_pic": normalized["vod_pic"],
                    "type_name": normalized["type_name"],
                    "vod_year": str(item.get("vod_year", "")),
                    "vod_area": str(item.get("vod_area", "")),
                    "vod_director": str(item.get("vod_director", "")),
                    "vod_actor": normalized["vod_actor"],
                    "vod_content": str(item.get("vod_blurb") or item.get("vod_content") or ""),
                    "vod_remarks": str(item.get("vod_remarks", "")),
                    "vod_play_from": play_data["vod_play_from"],
                    "vod_play_url": play_data["vod_play_url"],
                }
            ]
        }

    def playerContent(self, flag, id, vipFlags):
        play_id = str(id or "").strip()
        header = {
            "User-Agent": self.headers["User-Agent"],
            "Referer": self.host + "/",
        }
        if not play_id:
            return {"parse": 1, "jx": 1, "url": "", "header": header}
        if play_id.startswith("http://") or play_id.startswith("https://"):
            return {"parse": 0, "jx": 0, "url": play_id, "header": header}
        return {"parse": 1, "jx": 1, "url": play_id, "header": header}
