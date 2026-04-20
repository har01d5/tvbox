# coding=utf-8
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "短剧网"
        self.host = "https://sm3.cc"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "短剧大全"},
            {"type_id": "2", "type_name": "更新短剧"},
        ]

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

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=dict(self.headers), timeout=10, verify=False)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//li[contains(@class,'col-6')]"):
            anchors = card.xpath(".//h3[contains(@class,'f-14')]//a[@href]")
            if not anchors:
                continue
            anchor = anchors[0]
            name = self._clean_text("".join(anchor.xpath(".//text()")))
            href = self._stringify((anchor.xpath("./@href") or [""])[0]).strip()
            title_attr = self._stringify((anchor.xpath("./@title") or [""])[0]).strip()
            if not name or not href:
                continue
            url = self._build_url(href)
            if url in seen:
                continue
            seen.add(url)
            pic = self._build_url(
                (card.xpath(".//img[contains(@class,'lazy')]/@data-original") or [""])[0]
            )
            remarks = ""
            if title_attr:
                m = re.search(r"（(.+?)）", title_attr)
                if m:
                    remarks = m.group(1)
            items.append(
                {
                    "vod_id": url,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remarks,
                }
            )
        return items

    def _page_result(self, items, pg):
        page = int(pg)
        return {
            "list": items,
            "page": page,
            "pagecount": page + 1 if items else page,
            "limit": len(items) or 20,
            "total": (page + 1 if items else page) * (len(items) or 20),
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        url = f"{self.host}/?cate={tid}&page={page}"
        items = self._parse_cards(self._request_html(url))
        return self._page_result(items, pg)

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return self._page_result([], pg)
        url = f"{self.host}/search.php?q={quote(keyword)}&page={page}"
        items = self._parse_cards(self._request_html(url))
        return self._page_result(items, pg)

    def _is_netdisk_url(self, value):
        text = self._stringify(value).strip().lower()
        return any(
            token in text
            for token in [
                "drive.uc.cn",
                "pan.quark.cn",
                "pan.baidu.com",
                "pan.xunlei.com",
                "alipan.com",
                "aliyundrive.com",
            ]
        )

    def _normalize_disk_name_from_url(self, value):
        text = self._stringify(value).strip().lower()
        if "pan.baidu.com" in text:
            return "baidu"
        if "pan.quark.cn" in text:
            return "quark"
        if "drive.uc.cn" in text:
            return "uc"
        if "alipan.com" in text or "aliyundrive.com" in text:
            return "aliyun"
        if "pan.xunlei.com" in text:
            return "xunlei"
        return ""

    def _disk_priority(self, name):
        order = {"baidu": 1, "quark": 2, "uc": 3, "aliyun": 4, "xunlei": 5}
        return order.get(name, 999)

    def _extract_share_links(self, html):
        root = self.html(html)
        if root is None:
            return []
        links = []
        seen = set()
        for anchor in root.xpath("//*[contains(@class,'content')]//a[@href]"):
            href = self._build_url((anchor.xpath("./@href") or [""])[0])
            if not href or href in seen:
                continue
            seen.add(href)
            links.append(href)
        return links

    def _build_play_from_links(self, share_links):
        if not share_links:
            return {"vod_play_from": "短剧网", "vod_play_url": ""}
        grouped = {}
        order_seen = []
        for link in share_links:
            disk_name = self._normalize_disk_name_from_url(link)
            if not disk_name:
                continue
            if disk_name not in grouped:
                grouped[disk_name] = []
                order_seen.append(disk_name)
            title = disk_name
            urls_in_group = {item.split("$", 1)[1] for item in grouped[disk_name]}
            if link not in urls_in_group:
                grouped[disk_name].append(f"{title}${link}")
        if not grouped:
            fallback = "#".join(
                f"{i + 1}$push://{url}" for i, url in enumerate(share_links)
            )
            return {"vod_play_from": "短剧网", "vod_play_url": fallback}
        names = sorted(order_seen, key=self._disk_priority)
        return {
            "vod_play_from": "$$$".join(names),
            "vod_play_url": "$$$".join("#".join(grouped[n]) for n in names),
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            url = self._build_url(raw_id)
            if not url:
                continue
            html = self._request_html(url)
            root = self.html(html)
            if root is None:
                continue
            title = self._clean_text("".join(root.xpath("//h1[1]//text()")))
            if not title:
                title_text = self._clean_text("".join(root.xpath("//title[1]//text()")))
                title = title_text.split("(")[0].strip() or "短剧"
            pic = self._build_url(
                (root.xpath("(//img[contains(@class,'lazy')]/@data-original)[1]") or [""])[0]
                or (root.xpath("(//img/@src)[1]") or [""])[0]
            )
            share_links = self._extract_share_links(html)
            play_data = self._build_play_from_links(share_links)
            result["list"].append(
                {
                    "vod_id": url,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_content": "此为推送网盘规则",
                    "vod_play_from": play_data["vod_play_from"],
                    "vod_play_url": play_data["vod_play_url"],
                }
            )
        return result

    def playerContent(self, flag, id, vipFlags):
        raw = self._stringify(id).strip()
        if raw.startswith("push://"):
            return {"parse": 0, "url": raw[7:]}
        if self._is_netdisk_url(raw):
            return {"parse": 0, "url": raw}
        return {"parse": 0, "url": raw}
