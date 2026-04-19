# coding=utf-8
import json
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "剧圈圈"
        self.host = "https://www.jqqzx.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "dianying", "type_name": "电影"},
            {"type_id": "juji", "type_name": "剧集"},
            {"type_id": "dongman", "type_name": "动漫"},
            {"type_id": "zongyi", "type_name": "综艺"},
            {"type_id": "duanju", "type_name": "短剧"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(text or ""))).strip()

    def _encode_vod_id(self, href):
        matched = re.search(r"/vod/([^/?#]+)\.html", self._build_url(href))
        return f"vod/{matched.group(1)}" if matched else ""

    def _decode_vod_id(self, vod_id):
        matched = re.search(r"^vod/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/vod/{matched.group(1)}.html") if matched else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/play/([^/?#]+)\.html", self._build_url(href))
        return f"play/{matched.group(1)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^play/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/play/{matched.group(1)}.html") if matched else ""

    def _parse_search_list(self, payload):
        try:
            data = json.loads(str(payload or "{}"))
        except Exception:
            return []
        items = []
        for item in data.get("list", []):
            item_id = self._clean_text(item.get("id"))
            item_name = self._clean_text(item.get("name"))
            if not item_id or not item_name:
                continue
            items.append(
                {
                    "vod_id": f"vod/{item_id}",
                    "vod_name": item_name,
                    "vod_pic": self._build_url(item.get("pic")),
                    "vod_remarks": "",
                }
            )
        return items

    def _request_html(self, path_or_url, headers=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        response = self.fetch(target, headers=request_headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for anchor in root.xpath("//a[contains(@class,'module-poster-item') and contains(@class,'module-item')]"):
            vod_id = self._encode_vod_id((anchor.xpath("./@href") or [""])[0])
            if not vod_id or vod_id in seen:
                continue
            title = self._clean_text(
                "".join(anchor.xpath(".//*[contains(@class,'module-poster-item-title')][1]//text()"))
                or (anchor.xpath("./@title") or [""])[0]
                or (anchor.xpath(".//img[1]/@alt") or [""])[0]
            )
            if not title:
                continue
            seen.add(vod_id)
            pic = (
                anchor.xpath(".//img[1]/@data-original")
                or anchor.xpath(".//img[1]/@src")
                or [""]
            )[0]
            note = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'module-item-note')][1]//text()")))
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": note,
                }
            )
        return items

    def homeVideoContent(self):
        return {"list": self._parse_cards(self._request_html(self.host))[:40]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._request_html(self._build_url(f"/type/{tid}/page/{page}.html")))
        return {
            "page": page,
            "pagecount": page + 1 if items else page,
            "total": page * len(items) + (1 if items else 0),
            "list": items,
        }

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "pagecount": 1, "total": 0, "list": []}
        items = self._parse_search_list(
            self._request_html(self._build_url(f"/index.php/ajax/suggest?mid=1&wd={quote(keyword)}"))
        )
        return {"page": page, "pagecount": 1, "total": len(items), "list": items}
