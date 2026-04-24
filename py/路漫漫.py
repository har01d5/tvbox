# coding=utf-8
import base64
import json
import re
import sys
from urllib.parse import quote, unquote, urljoin

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "路漫漫"
        self.host = "https://www.lmm85.com"
        self.mobile_ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 "
            "Mobile/15E148 Safari/604.1"
        )
        self.headers = {
            "User-Agent": self.mobile_ua,
            "Referer": "http://www.lmm50.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.classes = [
            {"type_id": "6", "type_name": "日本动漫"},
            {"type_id": "7", "type_name": "国产动漫"},
            {"type_id": "8", "type_name": "欧美动漫"},
            {"type_id": "3", "type_name": "日本动画电影"},
            {"type_id": "4", "type_name": "国产动画电影"},
            {"type_id": "5", "type_name": "欧美动画电影"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes}

    def _abs_url(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        return urljoin(self.host + "/", raw)

    def _encode_vod_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"(/vod/detail/[^?#]+\.html)", raw)
        return matched.group(1).lstrip("/") if matched else raw.lstrip("/")

    def _decode_vod_id(self, vod_id):
        raw = str(vod_id or "").strip().lstrip("/")
        return self._abs_url(raw)

    def _encode_play_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"(/vod/play/[^?#]+\.html)", raw)
        return matched.group(1).lstrip("/") if matched else raw.lstrip("/")

    def _decode_play_id(self, play_id):
        raw = str(play_id or "").strip().lstrip("/")
        return self._abs_url(raw)

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _get_html(self, url, headers=None):
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        response = self.fetch(url, headers=request_headers, timeout=15, verify=False)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for box in root.xpath("//*[contains(@class,'video-img-box')]"):
            href = self._clean_text((box.xpath(".//a[1]/@href") or [""])[0])
            title = self._clean_text("".join(box.xpath(".//*[contains(@class,'title')][1]//text()")))
            pic = self._clean_text(
                (box.xpath(".//img[1]/@data-src") or box.xpath(".//img[1]/@src") or [""])[0]
            )
            remarks = self._clean_text("".join(box.xpath(".//*[contains(@class,'label')][1]//text()")))
            vod_id = self._encode_vod_id(href)
            if not vod_id or not title or vod_id in seen:
                continue
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._abs_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def homeVideoContent(self):
        return {"list": self._parse_cards(self._get_html(self.host + "/"))[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        extend = extend or {}
        path = f"/vod/show/id/{tid}"
        path += str(extend.get("年代", "") or "")
        path += str(extend.get("排序", "") or "")
        path += f"/page/{page}.html"
        items = self._parse_cards(self._get_html(self.host + path))
        return {"page": page, "total": len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        url = f"{self.host}/vod/search/page/{page}/wd/{quote(keyword)}.html"
        items = self._parse_cards(self._get_html(url))
        return {"page": page, "total": len(items), "list": items[:10] if quick else items}

    def _parse_play_groups(self, root):
        groups = []
        tabs = root.xpath("//*[contains(@class,'module-tab-item') and contains(@class,'tab-item')]")
        for index, tab in enumerate(tabs):
            name = self._clean_text("".join(tab.xpath(".//text()")))
            target = self._clean_text((tab.xpath("./@href") or [""])[0])
            if not name:
                continue
            playlist = []
            if target.startswith("#"):
                playlist = root.xpath(f"//*[@id='{target[1:]}']")
            if not playlist:
                playlist = root.xpath(f"(//*[contains(@class,'module-player-list')])[{index + 1}]")
            if not playlist:
                continue
            episodes = []
            for anchor in playlist[0].xpath(".//a[@href]"):
                ep_name = self._clean_text("".join(anchor.xpath(".//text()")))
                ep_id = self._encode_play_id((anchor.xpath("./@href") or [""])[0])
                if ep_name and ep_id:
                    episodes.append(f"{ep_name}${ep_id}")
            if episodes:
                groups.append((name, "#".join(episodes)))
        if groups:
            return groups

        fallback = []
        for anchor in root.xpath("//*[contains(@class,'module-player-list')]//a[@href]"):
            ep_name = self._clean_text("".join(anchor.xpath(".//text()")))
            ep_id = self._encode_play_id((anchor.xpath("./@href") or [""])[0])
            if ep_name and ep_id:
                fallback.append(f"{ep_name}${ep_id}")
        if fallback:
            return [("播放列表", "#".join(fallback))]
        return []

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, list) else ids
        html = self._get_html(self._decode_vod_id(raw_id))
        root = self.html(html)
        if root is None:
            return {"list": []}
        groups = self._parse_play_groups(root)
        remarks = [
            self._clean_text("".join(node.xpath(".//text()")))
            for node in root.xpath("//*[contains(@class,'video-info-items')]")
        ]
        pic = (
            root.xpath("//*[contains(@class,'module-item-pic')]//img[1]/@data-src")
            or root.xpath("//*[contains(@class,'module-item-pic')]//img[1]/@src")
            or [""]
        )[0]
        vod = {
            "vod_id": str(raw_id),
            "vod_name": self._clean_text("".join(root.xpath("//*[contains(@class,'page-title')][1]//text()"))),
            "vod_pic": self._abs_url(pic),
            "vod_content": self._clean_text("".join(root.xpath("//*[contains(@class,'video-info-content')][1]//text()"))),
            "vod_remarks": " / ".join([value for value in remarks if value]),
            "vod_play_from": "$$$".join(name for name, _ in groups),
            "vod_play_url": "$$$".join(urls for _, urls in groups),
        }
        return {"list": [vod]}

    def _decode_player_url(self, raw_url, encrypt):
        value = str(raw_url or "").strip()
        mode = str(encrypt or "0").strip()
        if mode == "1":
            return unquote(value)
        if mode == "2":
            try:
                return unquote(base64.b64decode(value).decode("utf-8"))
            except Exception:
                return ""
        return value

    def _extract_player_data(self, html):
        matched = re.search(r"player_[a-z0-9_]+\s*=\s*(\{[\s\S]*?\})\s*;?", str(html or ""), re.I)
        if not matched:
            return {}
        try:
            return json.loads(matched.group(1))
        except Exception:
            return {}

    def _decrypt_token(self, token):
        try:
            payload = base64.b64decode(str(token or ""))
            cipher = AES.new(b"ejjooopppqqqrwww", AES.MODE_CBC, b"1348987635684651")
            value = unpad(cipher.decrypt(payload), AES.block_size)
            return value.decode("utf-8")
        except Exception:
            return ""

    def _is_media_url(self, url):
        return bool(re.search(r"\.(m3u8|mp4|flv|avi|mkv|ts)(?:[?#]|$)", str(url or ""), re.I))

    def _build_player_headers(self, referer):
        return {
            "User-Agent": self.mobile_ua,
            "Referer": referer,
            "Origin": self.host,
        }

    def _resolve_player_url(self, player, play_page_url):
        media = self._decode_player_url(player.get("url", ""), player.get("encrypt", "0"))
        if self._is_media_url(media):
            return media.split("&", 1)[0]
        return ""

    def playerContent(self, flag, id, vipFlags):
        play_page_url = self._decode_play_id(id)
        if self._is_media_url(play_page_url):
            return {"parse": 0, "url": play_page_url, "header": self._build_player_headers(self.host + "/")}
        body = self._get_html(play_page_url, headers={"Referer": self.host + "/"})
        player = self._extract_player_data(body)
        real_url = self._resolve_player_url(player, play_page_url)
        if real_url:
            return {"parse": 0, "url": real_url, "header": self._build_player_headers(play_page_url)}
        return {"parse": 1, "url": play_page_url, "header": self._build_player_headers(self.host + "/")}
