# coding=utf-8
import base64
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
        matched = re.search(r"/movie/([^/?#]+)\.html", self._build_url(href))
        return f"detail/{matched.group(1)}" if matched else ""

    def _decode_detail_id(self, vod_id):
        matched = re.search(r"^detail/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/movie/{matched.group(1)}.html") if matched else ""

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
            "headers": dict(response.headers or {}),
        }

    def _request_with_firewall(self, url):
        cookie_jar = {}
        first = self._request_text(url)
        self._merge_set_cookie(cookie_jar, first["headers"].get("set-cookie", []))
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
        self._merge_set_cookie(cookie_jar, verify["headers"].get("set-cookie", []))

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
