# coding=utf-8
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "人人电影"
        self.host = "https://www.rrdynb.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "movie/list_2", "type_name": "电影"},
            {"type_id": "dianshiju/list_6", "type_name": "电视剧"},
            {"type_id": "dongman/list_13", "type_name": "动漫"},
            {"type_id": "zongyi/list_10", "type_name": "老电影"},
        ]
        self.supported_pan_patterns = [
            r"pan\.baidu\.com|yun\.baidu\.com",
            r"pan\.quark\.cn",
            r"drive\.uc\.cn",
            r"115\.com",
            r"123pan\.com|123684\.com|123865\.com|123912\.com",
            r"cloud\.189\.cn",
            r"yun\.139\.com",
        ]
        self.excluded_pan_patterns = [
            r"pan\.xunlei\.com",
            r"aliyundrive\.com",
            r"alipan\.com",
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
        raw = str(path or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        return urljoin(self.host + "/", raw)

    def _clean_search_title(self, text):
        return str(text or "").replace("<font color='red'>", "").replace("</font>", "").strip()

    def _normalize_title(self, raw_title):
        cleaned = self._clean_search_title(raw_title)
        matched = re.search(r"《(.*?)》|「(.*?)」", cleaned)
        if matched:
            return (matched.group(1) or matched.group(2) or "").strip()
        return cleaned.strip()

    def _is_supported_pan_url(self, url):
        raw = str(url or "").strip()
        if not raw:
            return False
        if any(re.search(pattern, raw, re.I) for pattern in self.excluded_pan_patterns):
            return False
        return any(re.search(pattern, raw, re.I) for pattern in self.supported_pan_patterns)

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=dict(self.headers), timeout=10)
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
        for node in root.xpath("//*[@id='movielist']//li"):
            href = "".join(node.xpath(".//*[contains(@class,'intro')]//h2//a[1]/@href")).strip()
            title = (
                "".join(node.xpath(".//*[contains(@class,'intro')]//h2//a[1]/@title")).strip()
                or "".join(node.xpath(".//*[contains(@class,'intro')]//h2//a[1]//text()")).strip()
            )
            pic = (
                "".join(node.xpath(".//*[contains(@class,'pure-img')][1]/@data-original")).strip()
                or "".join(node.xpath(".//*[contains(@class,'pure-img')][1]/@src")).strip()
                or "".join(node.xpath(".//*[contains(@class,'pure-img')]//img[1]/@data-original")).strip()
                or "".join(node.xpath(".//*[contains(@class,'pure-img')]//img[1]/@src")).strip()
                or "".join(node.xpath(".//*[contains(@class,'pure-u-5-24')]//img[1]/@data-original")).strip()
                or "".join(node.xpath(".//*[contains(@class,'pure-u-5-24')]//img[1]/@src")).strip()
            )
            remarks = self._clean_text("".join(node.xpath(".//*[contains(@class,'dou')][1]//text()")))
            if not href or not title or href in seen:
                continue
            seen.add(href)
            items.append(
                {
                    "vod_id": href,
                    "vod_name": self._normalize_title(title),
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        class_path = str(tid or "").lstrip("/")
        url = self._build_url(f"{class_path}_{page}.html")
        items = self._parse_cards(self._request_html(url))
        return {"page": page, "limit": len(items), "total": page * 20 + len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}

        url = self._build_url(f"/plus/search.php?q={quote(keyword)}&pagesize=10&submit=")
        if page > 1:
            url += f"&PageNo={page}"

        items = self._parse_cards(self._request_html(url))
        return {"page": page, "total": len(items), "list": items}

    def _extract_pan_links(self, html):
        root = self.html(html)
        if root is None:
            return []

        items = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'movie-txt')]//a[@href]"):
            href = "".join(node.xpath("./@href")).strip()
            title = self._clean_text("".join(node.xpath(".//text()"))) or "网盘资源"
            if not self._is_supported_pan_url(href) or href in seen:
                continue
            seen.add(href)
            items.append((title, href))
        return items

    def _parse_detail(self, vod_id, html):
        root = self.html(html)
        if root is None:
            return {
                "vod_id": vod_id,
                "vod_name": "",
                "vod_pic": "",
                "vod_content": "",
                "vod_play_from": "",
                "vod_play_url": "",
            }

        vod_name = self._clean_text("".join(root.xpath("//*[contains(@class,'movie-des')]//h1[1]//text()")))
        vod_pic = self._build_url("".join(root.xpath("//*[contains(@class,'movie-img')]//img[1]/@src")).strip())
        vod_content = self._clean_text("".join(root.xpath("//*[contains(@class,'movie-txt')][1]//text()")))
        pan_links = self._extract_pan_links(html)
        play_url = "#".join([f"{title}${url}" for title, url in pan_links])
        return {
            "vod_id": vod_id,
            "vod_name": vod_name,
            "vod_pic": vod_pic,
            "vod_content": vod_content,
            "vod_play_from": "网盘" if play_url else "",
            "vod_play_url": play_url,
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            detail = self._parse_detail(vod_id, self._request_html(self._build_url(vod_id)))
            result["list"].append(detail)
        return result

    def playerContent(self, flag, id, vipFlags):
        url = str(id or "").strip()
        if self._is_supported_pan_url(url):
            return {"parse": 0, "playUrl": "", "url": url}
        return {"parse": 0, "playUrl": "", "url": ""}
