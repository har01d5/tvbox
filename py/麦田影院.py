# coding=utf-8
import json
import re
import sys
from urllib.parse import unquote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "麦田影院"
        self.host = "https://www.mtyy5.com"
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        )
        self.headers = {
            "User-Agent": self.user_agent,
            "Referer": self.host + "/",
            "Origin": self.host,
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "26", "type_name": "短剧"},
            {"type_id": "25", "type_name": "少儿"},
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

    def _clean_text(self, text):
        raw = self._stringify(text).replace("&nbsp;", " ").replace("\xa0", " ")
        return re.sub(r"\s+", " ", raw).strip()

    def _build_url(self, value):
        raw = self._stringify(value).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return urljoin(self.host + "/", raw)

    def _request_html(self, path_or_url, referer=None):
        target = path_or_url if self._stringify(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.headers["Referer"]
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(self._stringify(html))
        if root is None:
            return []
        items = []
        for node in root.xpath("//div[contains(@class,'public-list-box')]"):
            href = self._clean_text("".join(node.xpath(".//a[contains(@class,'public-list-exp')][1]/@href")))
            title = self._clean_text("".join(node.xpath(".//a[contains(@class,'public-list-exp')][1]/@title")))
            pic = self._clean_text(
                "".join(node.xpath(".//a[contains(@class,'public-list-exp')]//img[1]/@data-src"))
            ) or self._clean_text(
                "".join(node.xpath(".//a[contains(@class,'public-list-exp')]//img[1]/@src"))
            )
            remarks = self._clean_text("".join(node.xpath(".//*[contains(@class,'public-list-prb')][1]//text()")))
            if href and title:
                items.append(
                    {
                        "vod_id": href,
                        "vod_name": title,
                        "vod_pic": self._build_url(pic),
                        "vod_remarks": remarks,
                    }
                )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = max(int(self._stringify(pg) or "1"), 1)
        url = self.host + f"/vodshow/{tid}--------{page}---.html"
        items = self._parse_cards(self._request_html(url))
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = max(int(self._stringify(pg) or "1"), 1)
        return {"page": page, "limit": 0, "total": 0, "list": []}

    def _extract_detail_pic(self, root):
        return self._clean_text(
            "".join(root.xpath("//*[contains(@class,'detail-pic') or contains(@class,'vod-img')]//img[1]/@data-src"))
        ) or self._clean_text(
            "".join(root.xpath("//*[contains(@class,'detail-pic') or contains(@class,'vod-img')]//img[1]/@src"))
        )

    def _extract_detail_content(self, root):
        candidates = [
            "//*[@id='height_limit'][1]",
            "//*[contains(@class,'vod_content')][1]",
            "//*[contains(@class,'detail-content')][1]",
            "//*[contains(@class,'switch-box')]//*[contains(@class,'text') or contains(@class,'desc') or contains(@class,'content')][1]",
        ]
        for xpath in candidates:
            nodes = root.xpath(xpath)
            if not nodes:
                continue
            text = self._clean_text("".join(nodes[0].xpath(".//text()")))
            if text:
                return text
        return ""

    def _parse_meta_by_labels(self, root, labels):
        if root is None:
            return ""
        values = labels if isinstance(labels, (list, tuple)) else [labels]
        patterns = [str(item or "").rstrip(":：").strip() for item in values if str(item or "").strip()]
        for node in root.xpath("//li|//p|//span|//div"):
            text = self._clean_text("".join(node.xpath(".//text()")))
            if not text:
                continue
            for label in patterns:
                matched = re.match(rf"^{re.escape(label)}\s*[:：]?\s*(.*)$", text)
                if matched:
                    return self._clean_text(matched.group(1))
        return ""

    def _parse_play_groups(self, root):
        names = []
        for node in root.xpath("//a[contains(@class,'swiper-slide')]"):
            label = re.sub(r"\d", "", self._clean_text("".join(node.xpath(".//text()")))).strip()
            names.append(label)

        groups = []
        for index, box in enumerate(root.xpath("//div[contains(@class,'anthology-list-box')]")):
            episodes = []
            for item in box.xpath(".//ul[contains(@class,'anthology-list-play')]/li"):
                name = self._clean_text("".join(item.xpath(".//text()")))
                href = self._clean_text("".join(item.xpath("./*[1]/@href")))
                if name and href:
                    episodes.append(f"{name}${href}")
            if episodes:
                title = names[index] if index < len(names) and names[index] else f"线路{index + 1}"
                groups.append((title, "#".join(episodes)))
        return groups

    def detailContent(self, ids):
        vod_id = self._clean_text(ids[0] if isinstance(ids, list) and ids else ids)
        if not vod_id:
            return {"list": []}
        root = self.html(self._request_html(self.host + vod_id))
        if root is None:
            return {"list": []}
        groups = self._parse_play_groups(root)
        vod = {
            "vod_id": vod_id,
            "vod_name": self._clean_text("".join(root.xpath("//h1[1]//text()"))),
            "vod_pic": self._build_url(self._extract_detail_pic(root)),
            "type_name": self._parse_meta_by_labels(root, ["类型"]),
            "vod_year": self._parse_meta_by_labels(root, ["年份", "年代"]),
            "vod_area": self._parse_meta_by_labels(root, ["地区"]),
            "vod_lang": self._parse_meta_by_labels(root, ["语言"]),
            "vod_douban_score": self._parse_meta_by_labels(root, ["豆瓣", "评分"]),
            "vod_douban_id": self._parse_meta_by_labels(root, ["豆瓣ID"]),
            "vod_director": self._parse_meta_by_labels(root, ["导演"]),
            "vod_actor": self._parse_meta_by_labels(root, ["主演", "演员"]),
            "vod_content": self._extract_detail_content(root),
            "vod_remarks": self._parse_meta_by_labels(root, ["状态", "备注", "更新"]),
            "vod_play_from": "$$$".join(item[0] for item in groups),
            "vod_play_url": "$$$".join(item[1] for item in groups),
        }
        return {"list": [vod]}

    def _request_json(self, url, referer=None):
        target = self._build_url(url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.headers["Referer"]
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return {}
        try:
            return json.loads(response.text or "")
        except Exception:
            return {}

    def _build_player_headers(self, referer):
        return {"User-Agent": self.user_agent, "Referer": referer}

    def _extract_player_data(self, html):
        matched = re.search(r"player_data\s*=\s*(\{.*?\})\s*</script>", self._stringify(html), re.S)
        if not matched:
            return {}
        try:
            return json.loads(matched.group(1))
        except Exception:
            return {}

    def playerContent(self, flag, id, vipFlags):
        play_id = self._clean_text(id)
        play_url = self.host + play_id if play_id.startswith("/") else self._build_url(play_id)
        player_data = self._extract_player_data(self._request_html(play_url, referer=self.host + "/"))
        direct_url = self._clean_text(player_data.get("url"))
        if direct_url.startswith(("http://", "https://")):
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": direct_url,
                "header": self._build_player_headers(play_url),
            }

        decoded = unquote(direct_url)
        if decoded:
            signed = self._request_json(
                self.host + f"/static/player/art.php?get_signed_url=1&url={decoded}",
                referer=play_url,
            )
            signed_url = self._clean_text(signed.get("signed_url"))
            if signed_url:
                final_data = self._request_json(
                    self.host + f"/static/player/art.php{signed_url}",
                    referer=play_url,
                )
                final_url = self._clean_text(final_data.get("jmurl"))
                if final_url:
                    return {
                        "parse": 0,
                        "jx": 0,
                        "playUrl": "",
                        "url": final_url,
                        "header": self._build_player_headers(play_url),
                    }

        return {
            "parse": 1,
            "jx": 1,
            "playUrl": "",
            "url": play_url,
            "header": self._build_player_headers(play_url),
        }
