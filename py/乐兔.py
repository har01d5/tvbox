# coding=utf-8
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "乐兔"
        self.host = "https://www.letu.me"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/144.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "5", "type_name": "短剧"},
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

    def _encode_vod_id(self, href):
        matched = re.search(r"/detail/([^/?#]+)\.html", self._build_url(href))
        return f"detail/{matched.group(1)}" if matched else ""

    def _decode_vod_id(self, vod_id):
        matched = re.search(r"^detail/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/detail/{matched.group(1)}.html") if matched else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/play/([^/?#]+)\.html", self._build_url(href))
        return f"play/{matched.group(1)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^play/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/play/{matched.group(1)}.html") if matched else ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=dict(self.headers), timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'grid') and contains(@class,'container_list')]//*[contains(@class,'s6')]"):
            href = "".join(node.xpath(".//a[1]/@href")).strip()
            vod_id = self._encode_vod_id(href)
            if not vod_id or vod_id in seen:
                continue
            name = self._clean_text("".join(node.xpath(".//a[1]/@title")) or "".join(node.xpath(".//a[1]//text()")))
            if not name:
                continue
            pic = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'large')][1]/@data-src | .//*[contains(@class,'large')][1]/@src"))
            )
            remark = self._clean_text("".join(node.xpath(".//*[contains(@class,'small-text')][1]//text()")))
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remark,
                }
            )
        return items

    def _page_result(self, items, pg):
        page = int(pg)
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def categoryContent(self, tid, pg, filter, extend):
        html = self._request_html(self._build_url(f"/type/{tid}-{int(pg)}.html"))
        return self._page_result(self._parse_cards(html), pg)

    def searchContent(self, key, quick, pg="1"):
        keyword = self._clean_text(key)
        if not keyword:
            return self._page_result([], pg)
        html = self._request_html(self._build_url(f"/vodsearch/-------------.html?wd={quote(keyword)}"))
        root = self.html(html)
        if root is None:
            return self._page_result([], pg)
        items = []
        for node in root.xpath("//*[contains(@class,'result-list')]//*[contains(@class,'result-item')]"):
            href = "".join(node.xpath(".//a[1]/@href")).strip()
            vod_id = self._encode_vod_id(href)
            name = self._clean_text("".join(node.xpath(".//a[1]//text()")))
            if not vod_id or not name:
                continue
            pic = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'large')][1]/@data-src | .//*[contains(@class,'large')][1]/@src"))
            )
            remark = self._clean_text("".join(node.xpath(".//*[contains(@class,'small-text')][1]//text()")))
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remark,
                }
            )
        return self._page_result(items, pg)
