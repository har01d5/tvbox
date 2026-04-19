# coding=utf-8
import json
import re
import sys
from urllib.parse import quote

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

    def _request_html(self, path_or_url, method="GET", data=None, headers=None, referer=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)
        merged_headers["Referer"] = referer or self.headers["Referer"]
        if method == "POST":
            response = self.post(target, data=data, headers=merged_headers, timeout=10)
        else:
            response = self.fetch(target, headers=merged_headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _parse_movie_cards(self, html, root_xpath="//*[contains(@class,'movie-card')]"):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for node in root.xpath(root_xpath):
            href = ((node.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            title = self._clean_text("".join(node.xpath(".//h3[1]//text()")))
            pic = (
                ((node.xpath(".//img[1]/@src") or [""])[0]).strip()
                or ((node.xpath(".//img[1]/@data-src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(node.xpath(".//*[contains(@class,'poster-badge')][1]//text()")))
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
        items = self._parse_movie_cards(self._request_html(self._build_category_url(tid, pg, extend)))
        return {
            "list": items,
            "page": page,
            "pagecount": page + 1 if items else page,
            "limit": 24,
            "total": page * 24 + len(items),
        }

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._stringify(key).strip()
        if not keyword:
            return {"page": page, "pagecount": 0, "total": 0, "list": []}
        html = self._request_html(
            self.host + "/search",
            method="POST",
            data=f"q={quote(keyword)}",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        items = self._parse_movie_cards(
            html,
            root_xpath="(//*[contains(@class,'mb-12')])[1]//*[contains(@class,'movie-card')]",
        )
        if not items:
            items = self._parse_movie_cards(html)
        return {"page": page, "pagecount": page + 1 if items else page, "total": len(items), "list": items}
