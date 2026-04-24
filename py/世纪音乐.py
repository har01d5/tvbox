# coding=utf-8
import re
import sys
from urllib.parse import urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "世纪音乐"
        self.host = "https://www.4c44.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "home", "type_name": "首页推荐"},
            {"type_id": "rank_list", "type_name": "排行榜"},
            {"type_id": "playlist", "type_name": "歌单"},
            {"type_id": "singer", "type_name": "歌手"},
            {"type_id": "mv", "type_name": "MV"},
        ]

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

    def _encode_vod_id(self, href):
        href = str(href or "")
        if "/mp3/" in href:
            return "song:" + href.rsplit("/", 1)[-1].replace(".html", "")
        if "/mp4/" in href:
            return "mv:" + href.rsplit("/", 1)[-1].replace(".html", "")
        return ""

    def _build_filters(self):
        return {"singer": [], "mv": [], "playlist": []}

    def _parse_home_items(self, html):
        root = self._load_html(html)
        items = []
        for node in root.xpath("//*[@id='datalist']//li | //*[contains(@class,'video_list')]//li"):
            href = "".join(node.xpath(".//a[1]/@href")).strip()
            vod_id = self._encode_vod_id(href)
            if not vod_id:
                continue
            name = self._clean_text("".join(node.xpath(".//div[contains(@class,'name')]//a[1]//text()")))
            singer = self._clean_text("".join(node.xpath(".//*[contains(@class,'singer')][1]//text()")))
            pic = self._build_url("".join(node.xpath(".//img[1]/@src")))
            if vod_id.startswith("song:") and singer:
                name = f"{singer} - {name}"
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": "",
                }
            )
        return items

    def homeContent(self, filter):
        items = self._parse_home_items(self._fetch_html("/"))
        return {"class": list(self.classes), "filters": self._build_filters(), "list": items}

    def homeVideoContent(self):
        return {"list": self.homeContent(False).get("list", [])}
