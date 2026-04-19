# coding=utf-8
import base64
import hashlib
import json
import random
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "茶杯狐"
        self.host = "https://www.cupfox.ai"
        self.page_limit = 20
        self.firewall_chars = "PXhw7UT1B0a9kQDKZsjIASmOezxYG4CHo5Jyfg2b8FLpEvRr3WtVnlqMidu6cN"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 "
                "Mobile/15E148 Safari/604.1"
            ),
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _encode_detail_id(self, href):
        movie_match = re.search(r"/movie/([^/?#]+)\.html", self._build_url(href))
        if movie_match:
            return f"detail/{movie_match.group(1)}"
        video_match = re.search(r"/video/([^/?#]+)\.html", self._build_url(href))
        if video_match:
            return f"detail/video/{video_match.group(1)}"
        return ""

    def _decode_detail_id(self, vod_id):
        raw = str(vod_id or "").strip()
        video_match = re.search(r"^detail/video/([^/?#]+)$", raw)
        if video_match:
            return self._build_url(f"/video/{video_match.group(1)}.html")
        movie_match = re.search(r"^detail/(?:movie/)?([^/?#]+)$", raw)
        return self._build_url(f"/movie/{movie_match.group(1)}.html") if movie_match else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/play/([^/?#]+)\.html", self._build_url(href))
        return f"play/{matched.group(1)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^play/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/play/{matched.group(1)}.html") if matched else ""

    def _merge_set_cookie(self, cookie_jar, headers):
        values = headers if isinstance(headers, list) else [headers]
        for item in values:
            first = str(item or "").split(";")[0]
            if "=" not in first:
                continue
            name, value = first.split("=", 1)
            if name.strip():
                cookie_jar[name.strip()] = value.strip()

    def _cookie_header(self, cookie_jar):
        return "; ".join([f"{key}={value}" for key, value in cookie_jar.items()])

    def _header_value(self, headers, name, default=None):
        if not isinstance(headers, dict):
            return default
        lowered = str(name or "").lower()
        for key, value in headers.items():
            if str(key).lower() == lowered:
                return value
        return default

    def _extract_firewall_token(self, html_text):
        matched = re.search(r'var\s+token\s*=\s*encrypt\("([^"]+)"\)', str(html_text or ""))
        return matched.group(1) if matched else ""

    def _cupfox_firewall_encrypt(self, value):
        encoded = ""
        for char in str(value or ""):
            index = self.firewall_chars.find(char)
            mapped = char if index == -1 else self.firewall_chars[(index + 3) % 62]
            encoded += (
                self.firewall_chars[random.randint(0, 61)]
                + mapped
                + self.firewall_chars[random.randint(0, 61)]
            )
        return base64.b64encode(encoded.encode("utf-8")).decode("utf-8")

    def _request_text(self, url, method="GET", body=None, headers=None):
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        if method == "POST":
            response = self.post(url, data=body, headers=request_headers, timeout=15)
        else:
            response = self.fetch(url, headers=request_headers, timeout=15)
        return {
            "status_code": response.status_code,
            "text": response.text or "",
            "headers": {str(key).lower(): value for key, value in dict(response.headers or {}).items()},
        }

    def _request_with_firewall(self, url):
        cookie_jar = {}
        first = self._request_text(url)
        self._merge_set_cookie(cookie_jar, self._header_value(first["headers"], "set-cookie", []))
        if not re.search(r"人机验证|verifyBox", first["text"] or ""):
            if int(first["status_code"] or 0) != 200:
                raise ValueError(f"HTTP {first['status_code']} @ {url}")
            return first["text"]

        token_raw = self._extract_firewall_token(first["text"])
        if not token_raw:
            return first["text"]

        verify_body = (
            "value="
            + quote(self._cupfox_firewall_encrypt(url))
            + "&token="
            + quote(self._cupfox_firewall_encrypt(token_raw))
        )
        verify_headers = {
            "Referer": url,
            "Origin": self.host,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        cookie_text = self._cookie_header(cookie_jar)
        if cookie_text:
            verify_headers["Cookie"] = cookie_text
        verify = self._request_text(
            self.host + "/robot.php",
            method="POST",
            body=verify_body,
            headers=verify_headers,
        )
        self._merge_set_cookie(cookie_jar, self._header_value(verify["headers"], "set-cookie", []))

        second_headers = {}
        solved_cookie = self._cookie_header(cookie_jar)
        if solved_cookie:
            second_headers["Cookie"] = solved_cookie
        second = self._request_text(url, headers=second_headers)
        if int(second["status_code"] or 0) != 200:
            raise ValueError(f"HTTP {second['status_code']} @ {url}")
        return second["text"]

    def _extract_player_data(self, html_text):
        matched = re.search(r"player_aaaa\s*=\s*(\{[\s\S]*?\})\s*;?", str(html_text or ""))
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _decode2(self, encoded):
        if not encoded:
            return ""
        lookup = {}
        for index, char in enumerate(self.firewall_chars):
            lookup[char] = self.firewall_chars[(index + 59) % 62]
        try:
            raw = base64.b64decode(str(encoded).encode("utf-8")).decode("utf-8")
        except Exception:
            return ""
        result = ""
        for index in range(1, len(raw), 3):
            result += lookup.get(raw[index], raw[index])
        return result

    def _node_text(self, value):
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def _pick_first(self, values):
        return values[0] if values else ""

    def _full_url(self, path):
        raw = str(path or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return self._build_url(raw)

    def _parse_home_classes(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        classes = []
        for node in root.xpath("//nav[contains(@class,'bm-item-list')]//a[@href]"):
            href = self._pick_first(node.xpath("./@href"))
            matched = re.search(r"/type/(\d+)\.html", href or "")
            name = self._node_text("".join(node.xpath(".//text()")))
            if matched and name:
                classes.append({"type_id": matched.group(1), "type_name": name})
        return classes

    def _parse_cards(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        items = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'movie-list-item')]"):
            href = self._pick_first(node.xpath(".//a[1]/@href"))
            vod_id = self._encode_detail_id(href)
            if not vod_id or vod_id in seen:
                continue
            name = self._node_text(
                self._pick_first(node.xpath(".//a[1]/@title")) or "".join(node.xpath(".//a[1]//text()"))
            )
            pic = self._full_url(
                self._pick_first(node.xpath(".//*[contains(@class,'Lazy')][1]/@data-original"))
                or self._pick_first(node.xpath(".//*[contains(@class,'Lazy')][1]/@src"))
            )
            note = self._node_text("".join(node.xpath(".//*[contains(@class,'movie-item-note')][1]//text()")))
            if not note:
                note = self._node_text("".join(node.xpath(".//*[contains(@class,'movie-item-score')][1]//text()")))
            if name:
                seen.add(vod_id)
                items.append(
                    {"vod_id": vod_id, "vod_name": name, "vod_pic": pic, "vod_remarks": note}
                )
        return items

    def _parse_search_cards(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        items = []
        for node in root.xpath("//*[contains(@class,'vod-search-list')]//*[contains(@class,'box')]"):
            href = self._pick_first(node.xpath(".//a[contains(@class,'cover-link')][1]/@href"))
            vod_id = self._encode_detail_id(href)
            name = self._node_text("".join(node.xpath(".//*[contains(@class,'movie-title')][1]//text()")))
            pic = self._full_url(
                self._pick_first(node.xpath(".//*[contains(@class,'Lazy')][1]/@data-original"))
                or self._pick_first(node.xpath(".//*[contains(@class,'Lazy')][1]/@src"))
            )
            note = self._node_text("".join(node.xpath(".//*[contains(@class,'movie-item-note')][1]//text()")))
            if not note:
                note = self._node_text(
                    "".join(node.xpath(".//*[contains(@class,'meta') and contains(@class,'getop')][1]//text()"))
                )
            if vod_id and name:
                items.append(
                    {"vod_id": vod_id, "vod_name": name, "vod_pic": pic, "vod_remarks": note}
                )
        return items

    def homeContent(self, filter):
        html = self._request_with_firewall(self.host)
        return {"class": self._parse_home_classes(html)}

    def homeVideoContent(self):
        html = self._request_with_firewall(self.host)
        return {"list": self._parse_cards(html)[: self.page_limit]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        path = f"/type/{tid}.html" if page == 1 else f"/type/{tid}-{page}.html"
        html = self._request_with_firewall(self._build_url(path))
        items = self._parse_cards(html)
        return {"page": page, "limit": self.page_limit, "total": page * len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._node_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        html = self._request_with_firewall(self._build_url(f"/search/{keyword}----------{page}---.html"))
        items = self._parse_search_cards(html)
        if quick:
            items = items[:10]
        return {"page": page, "limit": self.page_limit, "total": page * len(items), "list": items}

    def detailContent(self, ids):
        result = {"list": []}
        for vod_id in ids:
            url = self._decode_detail_id(vod_id)
            if not url:
                continue
            root = self.html(self._request_with_firewall(url) or "")
            if root is None:
                continue
            lines = []
            tabs = root.xpath("//*[contains(@class,'play_source_tab')]//*[contains(@class,'swiper-slide')]")
            for index, box in enumerate(root.xpath("//*[contains(@class,'play_list_box')]")):
                from_name = ""
                if index < len(tabs):
                    from_name = self._node_text("".join(tabs[index].xpath(".//text()")))
                if not from_name:
                    from_name = f"线路{index + 1}"
                episodes = []
                for anchor in box.xpath(".//*[contains(@class,'content_playlist')]//a[@href]"):
                    name = self._node_text("".join(anchor.xpath(".//text()")))
                    play_id = self._encode_play_id(self._pick_first(anchor.xpath("./@href")))
                    if name and play_id:
                        episodes.append(f"{name}${play_id}")
                if episodes:
                    lines.append((from_name, "#".join(episodes)))
            summary_nodes = root.xpath("//*[contains(@class,'summary') and contains(@class,'detailsTxt')][1]")
            vod_content = ""
            if summary_nodes:
                summary = summary_nodes[0]
                texts = []
                for text in summary.xpath(".//text()[not(ancestor::*[contains(@class,'ectogg')])]"):
                    cleaned = self._node_text(text)
                    if cleaned:
                        texts.append(cleaned)
                vod_content = self._node_text(" ".join(texts))
            years = [
                self._node_text(text)
                for text in root.xpath("//*[contains(@class,'scroll-content')]//a/text()")
            ]
            year = next((value for value in years if re.match(r"^\d{4}$", value)), "")
            result["list"].append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._node_text(
                        "".join(root.xpath("//h1[contains(@class,'movie-title')][1]//text()"))
                    ),
                    "vod_pic": self._full_url(
                        self._pick_first(root.xpath("//*[contains(@class,'poster')]//img[1]/@src"))
                    ),
                    "vod_content": vod_content,
                    "vod_year": year,
                    "vod_director": ",".join(
                        [
                            self._node_text(text)
                            for text in root.xpath(
                                "//*[contains(@class,'info-data')][contains(.,'导演')]//a/text()"
                            )
                            if self._node_text(text)
                        ]
                    ),
                    "vod_actor": ",".join(
                        [
                            self._node_text(text)
                            for text in root.xpath(
                                "//*[contains(@class,'info-data')][contains(.,'演员')]//a/text()"
                            )
                            if self._node_text(text)
                        ]
                    ),
                    "vod_play_from": "$$$".join([item[0] for item in lines]),
                    "vod_play_url": "$$$".join([item[1] for item in lines]),
                }
            )
        return result

    def _base64_decode(self, value):
        if not value:
            return ""
        try:
            cleaned = str(value).replace("\n", "").replace("\r", "")
            return base64.b64decode(cleaned.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

    def _md5(self, value):
        return hashlib.md5(str(value or "").encode("utf-8")).hexdigest()

    def _decode1_sign(self, encoded):
        try:
            first = self._base64_decode(encoded)
            key = self._md5("test")
            xor_text = "".join(
                [chr(ord(first[index]) ^ ord(key[index % len(key)])) for index in range(len(first))]
            )
            decoded = self._base64_decode(xor_text)
            parts = decoded.split("/")
            if len(parts) < 3:
                return ""
            plain_map = json.loads(self._base64_decode(parts[0]))
            cipher_map = json.loads(self._base64_decode(parts[1]))
            path = self._base64_decode("/".join(parts[2:]))
            output = ""
            for char in path:
                if char.isalpha() and char in plain_map:
                    index = cipher_map.index(char) if char in cipher_map else -1
                    output += plain_map[index] if index != -1 else char
                else:
                    output += char
            return output
        except Exception:
            return ""

    def _decode_play_url(self, data):
        url = str((data or {}).get("url") or "").strip()
        mode = int((data or {}).get("urlmode") or 0)
        if not url:
            return ""
        if mode == 1:
            return self._decode1_sign(url)
        if mode == 2:
            return self._decode2(url)
        return url

    def _is_placeholder_url(self, url):
        value = str(url or "").strip()
        if not value:
            return True
        if not re.match(r"^(https?:)?//", value) and not value.startswith("magnet:"):
            return True
        return (
            "baidu.com/404.mp4" in value
            or re.search(r"/404\.mp4($|[?#])", value) is not None
            or re.search(r"(^|[?&])code=403($|&)", value) is not None
            or "forbidden" in value.lower()
        )

    def playerContent(self, flag, id, vipFlags):
        play_url = self._decode_play_id(id)
        if not play_url:
            return {"parse": 1, "url": str(id or ""), "header": dict(self.headers)}
        try:
            html = self._request_with_firewall(play_url)
            player = self._extract_player_data(html) or {}
            vid = str(player.get("url") or "").strip()
            if not vid:
                raise ValueError("missing player url")

            muiplayer_url = self.host + "/foxplay/muiplayer.php?vid=" + quote(vid)
            api = self._request_text(
                self.host + "/foxplay/api.php",
                method="POST",
                body="vid=" + quote(vid),
                headers={
                    "User-Agent": self.headers["User-Agent"],
                    "Referer": muiplayer_url,
                    "Origin": self.host,
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "*/*",
                },
            )
            payload = json.loads(api["text"] or "{}")
            real_url = self._decode_play_url(payload.get("data") or {})
            if real_url and not self._is_placeholder_url(real_url):
                return {
                    "parse": 0,
                    "url": real_url,
                    "header": {
                        "User-Agent": self.headers["User-Agent"],
                        "Referer": muiplayer_url,
                    },
                }
        except Exception:
            pass
        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": self.headers["User-Agent"],
                "Referer": play_url,
            },
        }
