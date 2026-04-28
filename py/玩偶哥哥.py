# coding=utf-8
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "玩偶哥哥"
        self.host = "http://wogg.xxooo.cf"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "1", "type_name": "玩偶电影"},
            {"type_id": "2", "type_name": "玩偶剧集"},
            {"type_id": "3", "type_name": "玩偶动漫"},
            {"type_id": "4", "type_name": "玩偶综艺"},
            {"type_id": "44", "type_name": "臻彩视界"},
            {"type_id": "6", "type_name": "玩偶短剧"},
            {"type_id": "5", "type_name": "玩偶音乐"},
            {"type_id": "46", "type_name": "玩偶纪录"},
        ]
        self.pan_patterns = [
            ("baidu", "百度资源", r"pan\.baidu\.com|yun\.baidu\.com"),
            ("a139", "139资源", r"yun\.139\.com"),
            ("a189", "天翼资源", r"cloud\.189\.cn"),
            ("a123", "123资源", r"123684\.com|123865\.com|123912\.com|123pan\.com"),
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

    def danmaku(self):
        return True

    def homeContent(self, filter):
        return {"class": self.categories}

    def homeVideoContent(self):
        return {"list": []}

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _fix_img_url(self, img_url):
        raw = str(img_url or "").strip()
        if not raw:
            return ""
        if raw.startswith("/db.php?url="):
            return self._build_url(raw)
        if re.search(r"^https?://[^/]*gimg\d*\.baidu\.com/gimg/", raw, re.I) and "src=data:image/" in raw:
            return ""
        return raw

    def _detect_pan_type(self, url):
        raw = str(url or "").strip()
        for pan_type, title, pattern in self.pan_patterns:
            if re.search(pattern, raw, re.I):
                return pan_type, title
        return "", ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=dict(self.headers), timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _page_result(self, items, pg):
        page = int(pg)
        return {"page": page, "limit": len(items), "total": page * 20 + len(items), "list": items}

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []

        items = []
        seen = set()
        for node in root.xpath(
            "//*[@id='main']//*[contains(concat(' ', normalize-space(@class), ' '), ' module-item ')]"
        ):
            href = ((node.xpath("(.//*[contains(@class,'module-item-pic')]//a[@href])[1]/@href") or [""])[0]).strip()
            title = ((node.xpath("(.//*[contains(@class,'module-item-pic')]//img[@alt])[1]/@alt") or [""])[0]).strip()
            pic = (
                ((node.xpath("(.//*[contains(@class,'module-item-pic')]//img[@data-src])[1]/@data-src") or [""])[0]).strip()
                or ((node.xpath("(.//*[contains(@class,'module-item-pic')]//img[@src])[1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(node.xpath("(.//*[contains(@class,'module-item-text')])[1]//text()")))
            if not href or not title or href in seen:
                continue
            seen.add(href)
            items.append(
                {
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": self._build_url(self._fix_img_url(pic)),
                    "vod_remarks": remarks,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        url = self._build_url(f"/vodshow/{tid}--------{int(pg)}---.html")
        return self._page_result(self._parse_cards(self._request_html(url)), pg)

    def searchContent(self, key, quick, pg="1"):
        keyword = self._clean_text(key)
        page = int(pg)
        if not keyword:
            return {"page": page, "total": 0, "list": []}

        url = self._build_url(f"/vodsearch/-------------.html?wd={quote(keyword)}&page={page}")
        root = self.html(self._request_html(url))
        if root is None:
            return {"page": page, "total": 0, "list": []}

        items = []
        for node in root.xpath("//*[contains(@class,'module-search-item')]"):
            href = "".join(node.xpath(".//*[contains(@class,'video-serial')][1]/@href")).strip()
            title = "".join(node.xpath(".//*[contains(@class,'video-serial')][1]/@title")).strip()
            pic = (
                ((node.xpath("(.//*[contains(@class,'module-item-pic')]//img[@data-src])[1]/@data-src") or [""])[0]).strip()
                or ((node.xpath("(.//*[contains(@class,'module-item-pic')]//img[@src])[1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'video-serial')][1]//text()"))
                or "".join(node.xpath(".//*[contains(@class,'module-item-text')][1]//text()"))
            )
            if not href or not title:
                continue
            items.append(
                {
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": self._build_url(self._fix_img_url(pic)),
                    "vod_remarks": remarks,
                }
            )
        return {"page": page, "total": len(items), "list": items}

    def _parse_detail_page(self, vod_id, html):
        root = self.html(html)
        if root is None:
            return {
                "vod_id": vod_id,
                "vod_name": "",
                "vod_pic": "",
                "vod_year": "",
                "vod_director": "",
                "vod_actor": "",
                "vod_content": "",
                "pan_urls": [],
            }

        detail = {
            "vod_id": vod_id,
            "vod_name": self._clean_text("".join(root.xpath("//*[contains(@class,'page-title')][1]//text()"))),
            "vod_pic": self._build_url(
                self._fix_img_url(
                    (
                        (root.xpath("//*[contains(@class,'mobile-play')]//*[contains(@class,'lazyload')][1]/@data-src") or [""])[0]
                    ).strip()
                    or (
                        (root.xpath("//*[contains(@class,'mobile-play')]//*[contains(@class,'lazyload')][1]/@src") or [""])[0]
                    ).strip()
                )
            ),
            "vod_year": "",
            "vod_director": "",
            "vod_actor": "",
            "vod_content": "",
            "pan_urls": [],
        }

        for label_node in root.xpath("//*[contains(@class,'video-info-itemtitle')]"):
            key = self._clean_text("".join(label_node.xpath(".//text()")))
            sibling = label_node.getnext()
            if sibling is None:
                continue
            values = [self._clean_text(text) for text in sibling.xpath(".//a//text()")]
            joined = ",".join([value for value in values if value])
            text_value = self._clean_text("".join(sibling.xpath(".//text()")))
            if "年代" in key:
                detail["vod_year"] = joined or text_value
            elif "导演" in key:
                detail["vod_director"] = joined or text_value
            elif "主演" in key:
                detail["vod_actor"] = joined or text_value
            elif "剧情" in key:
                detail["vod_content"] = text_value

        pan_urls = []
        for node in root.xpath("//*[contains(@class,'module-row-info')]//p"):
            text = self._clean_text("".join(node.xpath(".//text()")))
            if text:
                pan_urls.append(text)
        detail["pan_urls"] = pan_urls
        return detail

    def _build_pan_lines(self, detail):
        lines = []
        seen = set()
        for url in detail.get("pan_urls", []):
            pan_type, title = self._detect_pan_type(url)
            if not pan_type or url in seen:
                continue
            seen.add(url)
            lines.append((self.pan_priority.get(pan_type, 999), f"{pan_type}#玩偶哥哥", f"{title}${url}"))
        lines.sort(key=lambda item: item[0])
        return [(item[1], item[2]) for item in lines]

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            detail = self._parse_detail_page(vod_id, self._request_html(self._build_url(vod_id)))
            lines = self._build_pan_lines(detail)
            result["list"].append(
                {
                    "vod_id": vod_id,
                    "vod_name": detail["vod_name"],
                    "vod_pic": detail["vod_pic"],
                    "vod_year": detail["vod_year"],
                    "vod_director": detail["vod_director"],
                    "vod_actor": detail["vod_actor"],
                    "vod_content": detail["vod_content"],
                    "vod_play_from": "$$$".join([item[0] for item in lines]),
                    "vod_play_url": "$$$".join([item[1] for item in lines]),
                }
            )
        return result

    def playerContent(self, flag, id, vipFlags):
        pan_type, _ = self._detect_pan_type(id)
        if pan_type:
            return {"parse": 0, "playUrl": "", "url": id}
        return {"parse": 0, "playUrl": "", "url": ""}
