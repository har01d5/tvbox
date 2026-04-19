# coding=utf-8
import base64
import hashlib
import json
import re
import sys
from urllib.parse import quote, unquote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "剧圈圈"
        self.host = "https://www.jqqzx.cc"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        self.categories = [
            {"type_id": "dianying", "type_name": "电影"},
            {"type_id": "juji", "type_name": "剧集"},
            {"type_id": "dongman", "type_name": "动漫"},
            {"type_id": "zongyi", "type_name": "综艺"},
            {"type_id": "duanju", "type_name": "短剧"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(text or ""))).strip()

    def _encode_vod_id(self, href):
        matched = re.search(r"/vod/([^/?#]+)\.html", self._build_url(href))
        return f"vod/{matched.group(1)}" if matched else ""

    def _decode_vod_id(self, vod_id):
        matched = re.search(r"^vod/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/vod/{matched.group(1)}.html") if matched else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/play/([^/?#]+)\.html", self._build_url(href))
        return f"play/{matched.group(1)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^play/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/play/{matched.group(1)}.html") if matched else ""

    def _parse_search_list(self, payload):
        try:
            data = json.loads(str(payload or "{}"))
        except Exception:
            return []
        items = []
        for item in data.get("list", []):
            item_id = self._clean_text(item.get("id"))
            item_name = self._clean_text(item.get("name"))
            if not item_id or not item_name:
                continue
            items.append(
                {
                    "vod_id": f"vod/{item_id}",
                    "vod_name": item_name,
                    "vod_pic": self._build_url(item.get("pic")),
                    "vod_remarks": "",
                }
            )
        return items

    def _request_html(self, path_or_url, headers=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        response = self.fetch(target, headers=request_headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for anchor in root.xpath("//a[contains(@class,'module-poster-item') and contains(@class,'module-item')]"):
            vod_id = self._encode_vod_id((anchor.xpath("./@href") or [""])[0])
            if not vod_id or vod_id in seen:
                continue
            title = self._clean_text(
                "".join(anchor.xpath(".//*[contains(@class,'module-poster-item-title')][1]//text()"))
                or (anchor.xpath("./@title") or [""])[0]
                or (anchor.xpath(".//img[1]/@alt") or [""])[0]
            )
            if not title:
                continue
            seen.add(vod_id)
            pic = (
                anchor.xpath(".//img[1]/@data-original")
                or anchor.xpath(".//img[1]/@src")
                or [""]
            )[0]
            note = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'module-item-note')][1]//text()")))
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": note,
                }
            )
        return items

    def homeVideoContent(self):
        return {"list": self._parse_cards(self._request_html(self.host))[:40]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._request_html(self._build_url(f"/type/{tid}/page/{page}.html")))
        return {
            "page": page,
            "pagecount": page + 1 if items else page,
            "total": page * len(items) + (1 if items else 0),
            "list": items,
        }

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "pagecount": 1, "total": 0, "list": []}
        items = self._parse_search_list(
            self._request_html(self._build_url(f"/index.php/ajax/suggest?mid=1&wd={quote(keyword)}"))
        )
        return {"page": page, "pagecount": 1, "total": len(items), "list": items}

    def _parse_info_items(self, root):
        info = {}
        for item in root.xpath("//*[contains(@class,'module-info-item')]"):
            title = self._clean_text(
                "".join(item.xpath(".//*[contains(@class,'module-info-item-title')][1]//text()"))
            ).rstrip("：:")
            if not title:
                continue
            links = [
                self._clean_text("".join(node.xpath(".//text()")))
                for node in item.xpath(".//*[contains(@class,'module-info-item-content')][1]//a")
            ]
            links = [value for value in links if value]
            if links:
                info[title] = " / ".join(links)
                continue
            info[title] = self._clean_text(
                "".join(item.xpath(".//*[contains(@class,'module-info-item-content')][1]//text()"))
            )
        return info

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        if root is None:
            return {"list": []}
        info = self._parse_info_items(root)
        tab_names = []
        for node in root.xpath("//*[@id='y-playList']//*[contains(@class,'module-tab-item')]"):
            tab_names.append(
                self._clean_text(
                    (node.xpath("./@data-dropdown-value") or [""])[0]
                    or "".join(node.xpath(".//span[1]//text()"))
                    or "".join(node.xpath(".//text()"))
                )
            )
        groups = []
        for index, box in enumerate(root.xpath("//*[contains(@class,'his-tab-list')]")):
            episodes = []
            for anchor in box.xpath(".//a[contains(@class,'module-play-list-link') and @href]"):
                play_id = self._encode_play_id((anchor.xpath("./@href") or [""])[0])
                ep_name = self._clean_text(
                    "".join(anchor.xpath(".//span[1]//text()")) or "".join(anchor.xpath(".//text()"))
                )
                if play_id and ep_name:
                    episodes.append(f"{ep_name}${play_id}")
            if episodes:
                groups.append(
                    {
                        "from": tab_names[index] if index < len(tab_names) and tab_names[index] else f"线路{index + 1}",
                        "urls": "#".join(episodes),
                    }
                )
        type_name = " / ".join(
            [
                self._clean_text("".join(node.xpath(".//text()")))
                for node in root.xpath("//*[contains(@class,'module-info-tag-link')]//a")
                if self._clean_text("".join(node.xpath(".//text()")))
            ]
        )
        pic = (
            root.xpath(
                "(//*[contains(@class,'module-item-pic')]//img/@data-original | "
                "//*[contains(@class,'module-info-poster')]//img/@data-original | "
                "//*[contains(@class,'module-item-pic')]//img/@src | "
                "//*[contains(@class,'module-info-poster')]//img/@src)[1]"
            )
            or [""]
        )[0]
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text(
                        "".join(root.xpath("//*[contains(@class,'module-info-heading')]//h1[1]//text()"))
                    ),
                    "vod_pic": self._build_url(pic),
                    "type_name": type_name,
                    "vod_remarks": info.get("备注") or info.get("状态", ""),
                    "vod_actor": info.get("主演", ""),
                    "vod_director": info.get("导演", ""),
                    "vod_content": self._clean_text(
                        "".join(root.xpath("//*[contains(@class,'module-info-introduction-content')][1]//text()"))
                    ),
                    "vod_play_from": "$$$".join(group["from"] for group in groups),
                    "vod_play_url": "$$$".join(group["urls"] for group in groups),
                }
            ]
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            detail_url = self._decode_vod_id(vod_id)
            if not detail_url:
                continue
            parsed = self._parse_detail_page(self._request_html(detail_url), vod_id)
            result["list"].extend(parsed.get("list", []))
        return result

    def _request_with_headers(self, path_or_url, headers=None, data=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        response = self.fetch(target, headers=request_headers, data=data, timeout=10)
        return {
            "body": response.text or "",
            "headers": getattr(response, "headers", {}) or {},
            "status_code": response.status_code,
        }

    def _get_set_cookies(self, headers):
        raw = headers.get("set-cookie") or headers.get("Set-Cookie") or []
        items = raw if isinstance(raw, list) else [raw]
        return [str(item).split(";", 1)[0] for item in items if str(item).strip()]

    def _merge_cookies(self, *groups):
        values = {}
        for group in groups:
            items = group if isinstance(group, list) else [group]
            for item in items:
                text = str(item or "").strip()
                if "=" not in text:
                    continue
                key, val = text.split("=", 1)
                values[key] = val
        return [f"{key}={val}" for key, val in values.items()]

    def _base64_decode(self, value):
        text = re.sub(r"\s+", "", str(value or ""))
        if not text:
            return ""
        text += "=" * ((4 - len(text) % 4) % 4)
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            return ""

    def _decode_url(self, value):
        raw = str(value or "").replace("error://apiRes_", "").strip()
        if not raw:
            return ""
        key = hashlib.md5("test".encode("utf-8")).hexdigest()
        first = self._base64_decode(raw)
        mixed = "".join(chr(ord(ch) ^ ord(key[index % len(key)])) for index, ch in enumerate(first))
        decoded = self._base64_decode(mixed)
        parts = decoded.split("/")
        if len(parts) < 3:
            return ""
        try:
            from_map = json.loads(self._base64_decode(parts[1]))
            to_map = json.loads(self._base64_decode(parts[0]))
        except Exception:
            return ""
        body = self._base64_decode("/".join(parts[2:]))
        mapped = re.sub(
            r"[a-zA-Z]",
            lambda match: to_map[from_map.index(match.group(0))]
            if match.group(0) in from_map and from_map.index(match.group(0)) < len(to_map)
            else match.group(0),
            body,
        )
        matched = re.search(r"https?://[^\s'\"<>]+", mapped)
        return matched.group(0) if matched else mapped.strip()

    def _extract_player_data(self, html):
        matched = re.search(r"player_aaaa\s*=\s*(\{[\s\S]*?\})\s*;?\s*</script>", str(html or ""), re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _is_media_url(self, value):
        return bool(re.search(r"^https?://.*\.(m3u8|mp4|flv|m4s)(\?.*)?$", str(value or ""), re.I))

    def playerContent(self, flag, id, vipFlags):
        play_url = self._decode_play_id(id)
        if not play_url:
            return {"parse": 1, "jx": 1, "url": "", "header": dict(self.headers)}
        try:
            play_res = self._request_with_headers(play_url, headers={"Referer": self.host + "/"})
            player = self._extract_player_data(play_res["body"])
            if not player:
                return {"parse": 1, "jx": 1, "url": play_url, "header": dict(self.headers)}
            vid = unquote(str(player.get("url") or "")).strip()
            if vid and not self._is_media_url(vid):
                decoded = self._decode_url(vid)
                if decoded.startswith("http"):
                    vid = decoded
            if self._is_media_url(vid):
                return {"parse": 0, "jx": 0, "url": vid, "header": {**self.headers, "Referer": play_url}}
            cookies = self._get_set_cookies(play_res["headers"])
            player_page = self._build_url(f"/jx/player.php?vid={quote(vid)}")
            player_res = self._request_with_headers(
                player_page,
                headers={"Referer": play_url, **({"Cookie": "; ".join(cookies)} if cookies else {})},
            )
            cookies = self._merge_cookies(cookies, self._get_set_cookies(player_res["headers"]))
            api_res = self._request_with_headers(
                self._build_url("/jx/api.php"),
                headers={
                    "Referer": player_page,
                    "Origin": self.host,
                    "X-Requested-With": "XMLHttpRequest",
                    **({"Cookie": "; ".join(cookies)} if cookies else {}),
                },
                data=f"vid={quote(vid)}",
            )
            payload = json.loads(api_res["body"] or "{}")
            real_url = self._decode_url(payload.get("data", {}).get("url"))
            if real_url.startswith("http"):
                return {"parse": 0, "jx": 0, "url": real_url, "header": {**self.headers, "Referer": player_page}}
            return {"parse": 1, "jx": 1, "url": play_url, "header": {**self.headers, "Referer": player_page}}
        except Exception:
            return {"parse": 1, "jx": 1, "url": play_url, "header": dict(self.headers)}
