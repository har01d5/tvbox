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
        self.name = "飞快TV"
        self.host = "https://feikuai.tv"
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
            {"type_id": "2", "type_name": "剧集"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeContent(self, filter):
        return {"class": self.classes}

    def homeVideoContent(self):
        return {"list": []}

    def _build_url(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return urljoin(self.host + "/", raw)

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=self.headers, timeout=10)
        if response.status_code != 200:
            return ""
        return str(response.text or "")

    def _parse_category_cards(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        items = []
        for node in root.xpath("//a[contains(@class,'module-poster-item')]"):
            vod_id = self._clean_text("".join(node.xpath("./@href")))
            vod_name = self._clean_text("".join(node.xpath("./@title"))) or self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'module-poster-item-title')][1]//text()"))
            )
            vod_pic = self._clean_text(
                "".join(node.xpath(".//img[contains(@class,'lazy')][1]/@data-original"))
            )
            vod_remarks = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'module-item-note')][1]//text()"))
            )
            if vod_id and vod_name:
                items.append(
                    {
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": self._build_url(vod_pic),
                        "vod_remarks": vod_remarks,
                    }
                )
        return items

    def _parse_search_cards(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        items = []
        for node in root.xpath(
            "//*[contains(@class,'module-card-item') and contains(@class,'module-item')]"
        ):
            vod_id = self._clean_text(
                "".join(node.xpath(".//a[contains(@class,'module-card-item-poster')][1]/@href"))
            )
            vod_name = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'module-card-item-title')][1]//strong/text()"))
            )
            vod_pic = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'module-item-pic')]//img[1]/@data-original"))
            )
            vod_remarks = self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'module-item-note')][1]//text()"))
            )
            if vod_id and vod_name:
                items.append(
                    {
                        "vod_id": vod_id,
                        "vod_name": vod_name,
                        "vod_pic": self._build_url(vod_pic),
                        "vod_remarks": vod_remarks,
                    }
                )
        return items

    def _detect_pan_type(self, url):
        value = str(url or "").strip()
        if "pan.quark.cn" in value:
            return "quark"
        if "drive.uc.cn" in value:
            return "uc"
        if "alipan.com" in value or "aliyundrive.com" in value:
            return "aliyun"
        if "pan.baidu.com" in value:
            return "baidu"
        return "pan"

    def _join_group_urls(self, groups):
        return "$$$".join("#".join(group) for group in groups if group)

    def _base64decode(self, value):
        try:
            return base64.b64decode(str(value or "")).decode("utf-8")
        except Exception:
            return ""

    def _extract_player_data(self, html):
        body = str(html or "")
        matched = re.search(r"player_aaaa\s*=\s*\{", body)
        if not matched:
            return {}
        start = matched.end() - 1
        depth = 0
        in_string = False
        escape = False
        end = -1
        for index in range(start, len(body)):
            char = body[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                continue
            if char == "{":
                depth += 1
                continue
            if char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end < 0:
            return {}
        try:
            return json.loads(body[start:end])
        except Exception:
            return {}

    def categoryContent(self, tid, pg, filter, extend):
        page = max(1, int(pg))
        url = self.host + f"/vodshow/{tid}--------{page}---.html"
        items = self._parse_category_cards(self._request_html(url))
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = max(1, int(pg))
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        url = self.host + "/label/search_ajax.html?wd=" + quote(keyword) + f"&by=time&order=desc&page={page}"
        items = self._parse_search_cards(self._request_html(url))
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip()
        if not vod_id:
            return {"list": []}
        html = self._request_html(self.host + vod_id)
        root = self.html(html or "")
        if root is None:
            return {"list": []}

        title = self._clean_text("".join(root.xpath("//h1[1]//text()")))
        pic = self._clean_text(
            "".join(root.xpath("//*[contains(@class,'module-item-pic')]//img[1]/@data-original"))
        )
        content = self._clean_text(
            "".join(root.xpath("//*[contains(@class,'module-info-introduction-content')][1]//text()"))
        )

        play_from = []
        play_urls = []
        online_names = [
            self._clean_text("".join(node.xpath(".//text()")))
            for node in root.xpath(
                "//div[contains(@class,'module-tab-items-box')]/*[contains(@class,'module-tab-item')][not(@onclick)]"
            )
        ]
        online_lists = root.xpath(
            "//div[contains(@class,'module-list') and contains(@class,'tab-list')][not(contains(@class,'module-downlist'))]"
        )
        for index, node in enumerate(online_lists):
            episodes = []
            for item in node.xpath(".//a[contains(@class,'module-play-list-link')]"):
                name = self._clean_text("".join(item.xpath(".//text()")))
                href = self._clean_text("".join(item.xpath("./@href")))
                if name and href:
                    episodes.append(f"{name}${href}")
            if episodes:
                group_name = online_names[index] if index < len(online_names) and online_names[index] else f"线路{index + 1}"
                play_from.append(group_name)
                play_urls.append(episodes)

        pan_groups = {}
        for node in root.xpath("//div[contains(@class,'module-list')]/*[contains(@class,'tab-content')]"):
            raw_name = self._clean_text("".join(node.xpath(".//h4[1]//text()")))
            pan_name = raw_name.split("@", 1)[0].strip() if raw_name else "网盘资源"
            pan_url = self._clean_text("".join(node.xpath(".//p[1]//text()")))
            if not pan_url.startswith("http"):
                continue
            pan_type = self._detect_pan_type(pan_url)
            pan_groups.setdefault(pan_type, []).append(f"{pan_name}${pan_url}")

        for key, values in pan_groups.items():
            play_from.append(key)
            play_urls.append(values)

        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_content": content,
            "vod_remarks": "",
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": self._join_group_urls(play_urls),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw_id = str(id or "")
        if raw_id.startswith(("http://", "https://")) and any(
            raw_id.lower().split("?")[0].endswith(ext) for ext in [".m3u8", ".mp4", ".flv"]
        ):
            return {"parse": 0, "jx": 0, "url": raw_id}

        target = self.host + raw_id
        data = self._extract_player_data(self._request_html(target))
        raw_url = str(data.get("url") or "")
        encrypt = str(data.get("encrypt") or "")
        media_url = ""
        if encrypt == "1":
            media_url = unquote(raw_url)
        elif encrypt == "2":
            media_url = unquote(self._base64decode(raw_url))
        elif raw_url:
            media_url = raw_url

        if media_url.startswith("http"):
            return {"parse": 0, "jx": 0, "url": media_url}
        return {"parse": 1, "jx": 1, "url": target}
