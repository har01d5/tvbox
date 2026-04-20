# coding=utf-8
import re
import sys
from urllib.parse import quote
from urllib.parse import urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "欧歌"
        self.host = "https://woog.nxog.eu.org"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "欧歌电影"},
            {"type_id": "2", "type_name": "欧哥剧集"},
            {"type_id": "3", "type_name": "欧歌动漫"},
            {"type_id": "4", "type_name": "欧歌综艺"},
            {"type_id": "5", "type_name": "欧歌短剧"},
            {"type_id": "21", "type_name": "欧歌综合"},
        ]
        self.pan_patterns = [
            ("baidu", "百度资源", r"pan\.baidu\.com|yun\.baidu\.com"),
            ("a139", "139资源", r"yun\.139\.com"),
            ("a189", "天翼资源", r"cloud\.189\.cn"),
            ("a123", "123资源", r"123pan\.com|123684\.com|123865\.com|123912\.com"),
            ("a115", "115资源", r"115\.com"),
            ("quark", "夸克资源", r"pan\.quark\.cn"),
            ("xunlei", "迅雷资源", r"pan\.xunlei\.com"),
            ("aliyun", "阿里资源", r"aliyundrive\.com|alipan\.com"),
            ("uc", "UC资源", r"drive\.uc\.cn"),
        ]
        self.pan_priority = {
            "baidu": 1,
            "a139": 2,
            "a189": 3,
            "a123": 4,
            "a115": 5,
            "quark": 6,
            "xunlei": 7,
            "aliyun": 8,
            "uc": 9,
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes}

    def homeVideoContent(self):
        return {"list": []}

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", self._stringify(text).replace("\xa0", " ")).strip()

    def _build_url(self, path):
        raw = self._stringify(path).strip()
        if not raw:
            return ""
        return urljoin(self.host + "/", raw)

    def _request_html(self, path_or_url, headers=None, referer=None):
        target = path_or_url if self._stringify(path_or_url).startswith("http") else self._build_url(path_or_url)
        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)
        merged_headers["Referer"] = referer or self.headers["Referer"]
        response = self.fetch(target, headers=merged_headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _detect_pan_type(self, url):
        raw = self._stringify(url).strip()
        for pan_type, title, pattern in self.pan_patterns:
            if re.search(pattern, raw, re.I):
                return pan_type, title
        return "", ""

    def _fix_img_url(self, img_url):
        raw = self._stringify(img_url).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        return self._build_url(raw)

    def _build_category_url(self, tid, pg):
        return self._build_url(f"/index.php/vod/show/id/{self._stringify(tid).strip()}/page/{int(pg)}.html")

    def _build_search_url(self, key, pg):
        return self._build_url(f"/index.php/vod/search/page/{int(pg)}/wd/{quote(self._stringify(key).strip())}.html")

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//*[@id='main']//*[contains(@class,'module-item')]"):
            href = ((card.xpath(".//*[contains(@class,'module-item-pic')]//a[@href][1]/@href") or [""])[0]).strip()
            title = ((card.xpath(".//*[contains(@class,'module-item-pic')]//img[@alt][1]/@alt") or [""])[0]).strip()
            pic = (
                ((card.xpath(".//*[contains(@class,'module-item-pic')]//img[@data-src][1]/@data-src") or [""])[0]).strip()
                or ((card.xpath(".//*[contains(@class,'module-item-pic')]//img[@src][1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(card.xpath(".//*[contains(@class,'module-item-text')][1]//text()")))
            if not href or not title or href in seen:
                continue
            seen.add(href)
            items.append(
                {
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": self._fix_img_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def _parse_search_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//*[contains(@class,'module-search-item')]"):
            href = ((card.xpath(".//*[contains(@class,'video-serial')][1]/@href") or [""])[0]).strip()
            title = (
                ((card.xpath(".//*[contains(@class,'video-serial')][1]/@title") or [""])[0]).strip()
                or ((card.xpath(".//*[contains(@class,'module-item-pic')]//img[@alt][1]/@alt") or [""])[0]).strip()
            )
            pic = (
                ((card.xpath(".//*[contains(@class,'module-item-pic')]//img[@data-src][1]/@data-src") or [""])[0]).strip()
                or ((card.xpath(".//*[contains(@class,'module-item-pic')]//img[@src][1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(card.xpath(".//*[contains(@class,'video-serial')][1]//text()")))
            if not remarks:
                remarks = self._clean_text("".join(card.xpath(".//*[contains(@class,'module-item-text')][1]//text()")))
            if not href or not title or href in seen:
                continue
            seen.add(href)
            items.append(
                {
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": self._fix_img_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._request_html(self._build_category_url(tid, pg)))
        return {"list": items, "page": page, "limit": len(items), "total": page * 20 + len(items)}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._stringify(key).strip()
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        items = self._parse_search_cards(self._request_html(self._build_search_url(keyword, pg)))
        return {"page": page, "total": len(items), "list": items}

    def _blank_detail(self, vod_id):
        return {
            "vod_id": vod_id,
            "vod_name": "",
            "vod_pic": "",
            "vod_year": "",
            "vod_director": "",
            "vod_actor": "",
            "vod_content": "",
            "vod_play_from": "",
            "vod_play_url": "",
        }

    def _extract_share_url(self, text):
        matched = re.search(r"https?://[^\s'\"<>]+", self._stringify(text), re.I)
        return matched.group(0).strip() if matched else ""

    def _join_people(self, node):
        values = [self._clean_text(text) for text in node.xpath(".//a//text()")]
        if not any(values):
            values = [self._clean_text(text) for text in node.xpath(".//text()")]
        values = [value for value in values if value]
        return ",".join(values)

    def _extract_pan_groups(self, root):
        groups = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'module-row-info')]//p"):
            text = self._clean_text("".join(node.xpath(".//text()")))
            share_url = self._extract_share_url(text)
            pan_type, title = self._detect_pan_type(share_url)
            if not share_url or not pan_type or share_url in seen:
                continue
            seen.add(share_url)
            groups.append((pan_type, f"{title}${share_url}"))
        groups.sort(key=lambda item: self.pan_priority.get(item[0], 999))
        return groups

    def _parse_detail_page(self, html, vod_id):
        if not self._stringify(html).strip():
            return self._blank_detail(vod_id)
        root = self.html(html)
        if root is None:
            return self._blank_detail(vod_id)

        vod = self._blank_detail(vod_id)
        vod["vod_name"] = self._clean_text("".join(root.xpath("(//*[contains(@class,'page-title')])[1]//text()")))
        pic = (
            ((root.xpath("//*[contains(@class,'mobile-play')]//*[contains(@class,'lazyload')][1]/@data-src") or [""])[0]).strip()
            or ((root.xpath("//*[contains(@class,'mobile-play')]//*[contains(@class,'lazyload')][1]/@src") or [""])[0]).strip()
        )
        vod["vod_pic"] = self._fix_img_url(pic)
        vod["vod_year"] = self._clean_text(
            ((root.xpath("(//*[contains(@class,'module-item-caption')]//span[1]/text())") or [""])[0])
        )

        for label_node in root.xpath("//*[contains(@class,'video-info-itemtitle')]"):
            label = self._clean_text("".join(label_node.xpath(".//text()")))
            siblings = label_node.xpath("./following-sibling::*[1]")
            if not siblings:
                continue
            block = siblings[0]
            if "导演" in label:
                vod["vod_director"] = self._join_people(block)
            elif "主演" in label:
                vod["vod_actor"] = self._join_people(block)
            elif "剧情" in label:
                texts = block.xpath(".//p//text()") or block.xpath(".//text()")
                vod["vod_content"] = self._clean_text("".join(texts))

        pan_groups = self._extract_pan_groups(root)
        vod["vod_play_from"] = "$$$".join(item[0] for item in pan_groups)
        vod["vod_play_url"] = "$$$".join(item[1] for item in pan_groups)
        return vod

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = self._stringify(raw_id).strip()
            if not vod_id:
                continue
            html = self._request_html(self._build_url(vod_id))
            result["list"].append(self._parse_detail_page(html, vod_id))
        return result

    def _is_supported_pan_link(self, url):
        return bool(self._detect_pan_type(url)[0])

    def playerContent(self, flag, id, vipFlags):
        target = self._stringify(id).strip()
        if target and self._is_supported_pan_link(target):
            return {"parse": 0, "jx": 0, "playUrl": "", "url": target, "header": {}}
        return {"parse": 0, "jx": 0, "playUrl": "", "url": "", "header": {}}
