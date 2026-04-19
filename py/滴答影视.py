# coding=utf-8
import json
import re
import sys
from urllib.parse import quote

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

    def _request_html(self, path_or_url, referer=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.headers["Referer"]
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//*[contains(@class,'myui-vodlist__box')]"):
            href = ((card.xpath(".//*[contains(@class,'title')]//a[@href][1]/@href") or [""])[0]).strip()
            title = (
                ((card.xpath(".//*[contains(@class,'title')]//a[@title][1]/@title") or [""])[0]).strip()
                or self._clean_text("".join(card.xpath(".//*[contains(@class,'title')]//a[1]//text()")))
            )
            pic = (
                ((card.xpath(".//*[contains(@class,'lazyload')][1]/@data-original") or [""])[0]).strip()
                or ((card.xpath(".//*[contains(@class,'lazyload')][1]/@src") or [""])[0]).strip()
                or ((card.xpath(".//img[1]/@data-original") or [""])[0]).strip()
                or ((card.xpath(".//img[1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(card.xpath(".//*[contains(@class,'pic-text')][1]//text()")))
            vod_id = self._build_url(href)
            if not vod_id or not title or vod_id in seen:
                continue
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._request_html(self._build_category_url(tid, pg, extend)))
        return {
            "list": items,
            "page": page,
            "pagecount": page + 1 if items else page,
            "limit": 12,
            "total": page * 12 + len(items),
        }

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._stringify(key).strip()
        if not keyword:
            return {"page": page, "pagecount": 0, "total": 0, "list": []}
        url = f"{self.host}/search/-------------.html?wd={quote(keyword)}"
        items = self._parse_cards(self._request_html(url))
        return {"page": page, "pagecount": page + 1 if items else page, "total": len(items), "list": items}
