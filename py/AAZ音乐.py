# coding=utf-8
import re
import sys
from urllib.parse import urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "AAZ音乐"
        self.host = "https://www.aaz.cx"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "new", "type_name": "新歌榜"},
            {"type_id": "top", "type_name": "TOP榜单"},
            {"type_id": "singer", "type_name": "歌手"},
            {"type_id": "playtype", "type_name": "歌单"},
            {"type_id": "album", "type_name": "专辑"},
            {"type_id": "mv", "type_name": "高清MV"},
        ]
        self.category_paths = {
            "new": "/list/new.html",
            "top": "/list/top.html",
            "singer": "/singerlist/index/index/index/index.html",
            "playtype": "/playtype/index.html",
            "album": "/albumlist/index.html",
            "mv": "/mvlist/index.html",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _load_html(self, html):
        return self.html(str(html or "").strip() or "<html></html>")

    def _fetch_html(self, path):
        response = self.fetch(self._build_url(path), headers=dict(self.headers), timeout=10, verify=False)
        return response.text if getattr(response, "status_code", 0) == 200 else ""

    def _empty_result(self, page=1):
        return {"page": int(page), "limit": 0, "total": 0, "list": []}

    def _extract_song_id(self, href):
        matched = re.search(r"/m/([^.?#/]+)\.html", str(href or "").strip())
        return matched.group(1) if matched else ""

    def _extract_folder_id(self, href, prefix):
        matched = re.search(r"/%s/([^/?#]+)" % re.escape(prefix), str(href or "").strip())
        return matched.group(1) if matched else ""

    def _encode_vod_id(self, href):
        raw = str(href or "").strip()
        song_id = self._extract_song_id(raw)
        if song_id:
            return "song:" + song_id
        for prefix, label in [("s", "singer"), ("p", "playlist"), ("a", "album"), ("v", "mv")]:
            folder_id = self._extract_folder_id(raw, prefix)
            if folder_id:
                return label + ":" + folder_id
        return ""

    def _parse_song_cards(self, html):
        root = self._load_html(html)
        items = []
        seen = set()
        for node in root.xpath("//li"):
            href = "".join(node.xpath(".//div[contains(@class,'name')]//a[1]/@href")).strip()
            vod_id = self._encode_vod_id(href)
            if not vod_id.startswith("song:") or vod_id in seen:
                continue
            seen.add(vod_id)
            has_mv = bool(node.xpath(".//div[contains(@class,'mv')]//a"))
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text("".join(node.xpath(".//div[contains(@class,'name')]//a[1]/@title"))),
                    "vod_pic": "",
                    "vod_remarks": "高清MV" if has_mv else "",
                }
            )
        return items

    def _parse_folder_cards(self, html, expected_prefix):
        root = self._load_html(html)
        items = []
        seen = set()
        for node in root.xpath("//li"):
            href = "".join(node.xpath(".//div[contains(@class,'name')]//a[1]/@href")).strip()
            vod_id = self._encode_vod_id(href)
            if not vod_id.startswith(expected_prefix + ":") or vod_id in seen:
                continue
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text("".join(node.xpath(".//div[contains(@class,'name')]//a[1]/@title"))),
                    "vod_pic": self._build_url("".join(node.xpath(".//img[1]/@src"))),
                    "vod_remarks": "",
                }
            )
        return items

    def homeContent(self, filter):
        items = self._parse_song_cards(self._fetch_html(self.category_paths["new"]))
        return {"class": list(self.classes), "list": items}

    def homeVideoContent(self):
        return {"list": self.homeContent(False).get("list", [])}

    def categoryContent(self, tid, pg, filter, extend):
        if tid not in self.category_paths:
            return self._empty_result(pg)
        html = self._fetch_html(self.category_paths[tid])
        if tid in ("new", "top"):
            items = self._parse_song_cards(html)
        elif tid == "singer":
            items = self._parse_folder_cards(html, "singer")
        elif tid == "playtype":
            items = self._parse_folder_cards(html, "playlist")
        elif tid == "album":
            items = self._parse_folder_cards(html, "album")
        else:
            items = self._parse_folder_cards(html, "mv")
        return {"page": int(pg), "limit": len(items), "total": len(items), "list": items}
