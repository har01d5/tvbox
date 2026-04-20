# coding=utf-8
import base64
import json
import re
import sys
from urllib.parse import quote, unquote, urljoin

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
        matched = re.search(r"/(vods|vod|detail)/([^/?#]+)\.html", self._build_url(href))
        return f"{matched.group(1)}/{matched.group(2)}" if matched else ""

    def _decode_vod_id(self, vod_id):
        matched = re.search(r"^(vods|vod|detail)/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/{matched.group(1)}/{matched.group(2)}.html") if matched else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/(vod|vodplay|play)/([^/?#]+)\.html", self._build_url(href))
        return f"{matched.group(1)}/{matched.group(2)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^(vod|vodplay|play)/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/{matched.group(1)}/{matched.group(2)}.html") if matched else ""

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

    def _build_category_url(self, tid, pg):
        page = int(pg)
        if page <= 1:
            return self._build_url(f"/type/{tid}.html")
        return self._build_url(f"/type/{tid}-{page}.html")

    def categoryContent(self, tid, pg, filter, extend):
        html = self._request_html(self._build_category_url(tid, pg))
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

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        if root is None:
            return {"list": []}
        info_nodes = root.xpath(
            "//*[contains(concat(' ', normalize-space(@class), ' '), ' no-margin ') and "
            "contains(concat(' ', normalize-space(@class), ' '), ' m ') and "
            "contains(concat(' ', normalize-space(@class), ' '), ' l ')]"
        )
        director = ""
        area = ""
        for node in info_nodes:
            classes = " ".join(node.xpath("./@class"))
            text = self._clean_text("".join(node.xpath(".//text()")))
            if not text:
                continue
            if "no-space" in classes and not director:
                director = text
            elif "no-space" not in classes and not area:
                area = text
        play_from = []
        play_urls = []
        tabs = [
            self._clean_text("".join(node.xpath(".//text()")))
            for node in root.xpath("//*[contains(@class,'tabs') and contains(@class,'left-align')]//a")
        ]
        groups = root.xpath("//*[contains(@class,'playno')]")
        for index, group in enumerate(groups):
            episodes = []
            for anchor in group.xpath(".//a[@href]"):
                play_id = self._encode_play_id("".join(anchor.xpath("./@href")))
                ep_name = self._clean_text("".join(anchor.xpath(".//text()")))
                if play_id and ep_name:
                    episodes.append(f"{ep_name}${play_id}")
            if episodes:
                play_from.append(tabs[index] if index < len(tabs) and tabs[index] else f"线路{index + 1}")
                play_urls.append("#".join(episodes))
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text("".join(root.xpath("//h1[1]//text()"))),
                    "vod_pic": self._build_url("".join(root.xpath("(//img/@src | //img/@data-src)[1]"))),
                    "type_name": self._clean_text(
                        "".join(root.xpath("(//*[contains(@class,'scroll') and contains(@class,'no-margin')]//a[1]//text())[1]"))
                    ),
                    "vod_actor": self._clean_text(
                        "".join(root.xpath("(//*[contains(@class,'scroll') and contains(@class,'no-margin')]//a[2]//text())[1]"))
                    ),
                    "vod_director": director,
                    "vod_area": area,
                    "vod_content": self._clean_text("".join(root.xpath("(//*[contains(@class,'responsive')]//p[last()]//text())[1]"))),
                    "vod_play_from": "$$$".join(play_from),
                    "vod_play_url": "$$$".join(play_urls),
                }
            ]
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            detail_url = self._decode_vod_id(vod_id) or self._build_url(vod_id)
            if not detail_url:
                continue
            parsed = self._parse_detail_page(self._request_html(detail_url), vod_id)
            result["list"].extend(parsed.get("list", []))
        return result

    def _base64_decode(self, value):
        text = re.sub(r"\s+", "", str(value or ""))
        text += "=" * ((4 - len(text) % 4) % 4)
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            return ""

    def _decode_rose_url(self, value):
        raw = str(value or "")[5:]
        decoded = self._base64_decode(unquote(raw))
        if decoded:
            return decoded
        return self._base64_decode(raw)

    def _extract_player_data(self, html):
        matched = re.search(r"player_[a-z0-9]+\s*=\s*(\{[\s\S]*?\})", str(html or ""), re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def playerContent(self, flag, id, vipFlags):
        play_url = self._decode_play_id(id) or self._build_url(id)
        body = self._request_html(play_url)
        try:
            payload = json.loads(body)
        except Exception:
            payload = None
        if isinstance(payload, dict) and str(payload.get("code")) == "200" and payload.get("url"):
            video_url = str(payload.get("url"))
            if video_url.startswith("rose_"):
                video_url = self._decode_rose_url(video_url)
            elif video_url.startswith("/"):
                video_url = self._build_url(video_url)
            if video_url:
                return {"parse": 0, "jx": 0, "url": video_url, "header": dict(self.headers)}
        player = self._extract_player_data(body)
        if player:
            video_url = str(player.get("url") or "")
            encrypt = str(player.get("encrypt") or "")
            if encrypt == "1":
                video_url = unquote(video_url)
            elif encrypt == "2":
                video_url = self._base64_decode(unquote(video_url))
            if video_url:
                return {"parse": 0, "jx": 0, "url": video_url, "header": dict(self.headers)}
        return {"parse": 1, "jx": 1, "url": play_url, "header": dict(self.headers)}
