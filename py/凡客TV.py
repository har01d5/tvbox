# coding=utf-8
import json
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "凡客TV"
        self.host = "https://fktv.me"
        self.cookie = "_did=57nTmEknMZ146xw4KXGHDCHk1MjshRyY"
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
        )
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "剧集"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "8", "type_name": "短剧"},
            {"type_id": "6", "type_name": "纪录片"},
            {"type_id": "7", "type_name": "解说"},
            {"type_id": "5", "type_name": "音乐"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes}

    def homeVideoContent(self):
        return {"list": []}

    def _clean_text(self, value):
        return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()

    def _abs_url(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return urljoin(self.host + "/", raw)

    def _page_headers(self, referer=""):
        headers = {"User-Agent": self.user_agent, "Referer": referer or self.host + "/"}
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def _request_html(self, url, headers=None):
        response = self.fetch(url, headers=headers or self._page_headers(), timeout=10, verify=False)
        if response.status_code != 200:
            return ""
        return str(response.text or "")

    def _ajax_headers(self, referer):
        headers = {
            "User-Agent": self.user_agent,
            "Referer": referer,
            "Origin": self.host,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def _request_json(self, url, data=None, headers=None):
        response = self.post(
            url,
            data=data,
            headers=headers or self._ajax_headers(self.host + "/"),
            timeout=10,
            verify=False,
        )
        if response.status_code != 200:
            return {}
        try:
            return json.loads(str(response.text or ""))
        except Exception:
            return {}

    def _extract_cards(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        items = []
        seen = set()
        nodes = root.xpath("//*[contains(@class,'meta-wrap')]/.. | //*[contains(@class,'hover-wrap')]")
        for node in nodes:
            href = self._clean_text(
                "".join(
                    node.xpath(
                        ".//a[contains(@class,'normal-title') or contains(@class,'hover-title')][1]/@href"
                    )
                )
            )
            matched = re.search(r"/movie/detail/([0-9A-Za-z]+)", href)
            if not matched:
                continue
            vod_id = matched.group(1)
            if vod_id in seen:
                continue
            seen.add(vod_id)
            title = self._clean_text(
                "".join(
                    node.xpath(
                        ".//a[contains(@class,'normal-title') or contains(@class,'hover-title')][1]/@title"
                    )
                )
            ) or self._clean_text(
                "".join(
                    node.xpath(
                        ".//a[contains(@class,'normal-title') or contains(@class,'hover-title')][1]//text()"
                    )
                )
            )
            pic = self._clean_text("".join(node.xpath(".//*[contains(@class,'lazy-load')][1]/@data-src")))
            tags = [
                self._clean_text("".join(tag.xpath(".//text()")))
                for tag in node.xpath(".//*[contains(@class,'tag')]")
            ]
            tags = [tag for tag in tags if tag]
            if not title:
                continue
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._abs_url(pic),
                    "vod_remarks": " | ".join(tags),
                    "type_name": tags[0] if tags else "",
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = max(1, int(pg))
        url = self.host + f"/channel?page={page}&cat_id={tid}&page_size=32&order=new"
        items = self._extract_cards(self._request_html(url))
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = max(1, int(pg))
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        url = self.host + "/search?keyword=" + quote(keyword)
        items = self._extract_cards(self._request_html(url))
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def _safe_json_loads(self, value, fallback=None):
        try:
            data = json.loads(str(value or ""))
        except Exception:
            data = fallback
        return data if data is not None else fallback

    def _extract_page_state(self, html):
        body = str(html or "")
        state = {"movieId": "", "linkId": "", "links": [], "play_links": [], "play_error_type": ""}
        movie = re.search(r"let\s+movieId\s*=\s*['\"]([^'\"]+)['\"]", body)
        link = re.search(r"let\s+linkId\s*=\s*['\"]([^'\"]+)['\"]", body)
        links = re.search(r"var\s+links\s*=\s*(\[[\s\S]*?\]);", body)
        play_links = re.search(r"var\s+play_links\s*=\s*(\[[\s\S]*?\]);", body)
        error_type = re.search(r"var\s+play_error_type\s*=\s*['\"]([^'\"]*)['\"]", body)
        if movie:
            state["movieId"] = movie.group(1)
        if link:
            state["linkId"] = link.group(1)
        if links:
            state["links"] = self._safe_json_loads(links.group(1), []) or []
        if play_links:
            state["play_links"] = self._safe_json_loads(play_links.group(1), []) or []
        if error_type:
            state["play_error_type"] = error_type.group(1)
        return state

    def _extract_line_tabs(self, html):
        root = self.html(html or "")
        if root is None:
            return []
        lines = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'item-wrap')][@data-line]"):
            line_id = self._clean_text("".join(node.xpath("./@data-line")))
            name = self._clean_text("".join(node.xpath(".//text()")))
            if not line_id or line_id in seen:
                continue
            seen.add(line_id)
            lines.append({"id": line_id, "name": name or line_id})
        return lines

    def _pick_episode_name(self, item):
        for key in ("name", "title", "id"):
            value = self._clean_text((item or {}).get(key))
            if value:
                return value
        return "正片"

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip()
        if not vod_id:
            return {"list": []}
        page_url = self.host + "/movie/detail/" + vod_id
        html = self._request_html(page_url, self._page_headers(self.host + "/"))
        root = self.html(html or "")
        state = self._extract_page_state(html)
        title = ""
        pic = ""
        content = ""
        if root is not None:
            title = self._clean_text("".join(root.xpath("//h1[1]//text()")))
            if not title:
                title = self._clean_text("".join(root.xpath("//title[1]//text()")))
            title = title.replace("-免费在线观看-凡客影视", "").strip()
            pic = self._clean_text("".join(root.xpath("//meta[@property='og:image'][1]/@content")))
            if not pic:
                pic = self._clean_text("".join(root.xpath("//video[1]/@poster")))
            content = self._clean_text("".join(root.xpath("//meta[@name='description'][1]/@content")))

        lines = self._extract_line_tabs(html)
        if not lines:
            lines = []
            for item in state["play_links"]:
                line_id = str((item or {}).get("id") or "").strip()
                if not line_id:
                    continue
                lines.append(
                    {
                        "id": line_id,
                        "name": self._clean_text((item or {}).get("name")) or line_id,
                    }
                )

        groups = []
        for line in lines:
            entries = []
            for episode in state["links"]:
                link_id = str((episode or {}).get("id") or "").strip()
                if not link_id:
                    continue
                meta = {
                    "movie_id": state["movieId"] or vod_id,
                    "link_id": link_id,
                    "line_id": line["id"],
                    "line_name": line["name"],
                    "episode_name": self._pick_episode_name(episode),
                    "type": "switch",
                    "page": page_url,
                }
                entries.append(meta["episode_name"] + "$" + self._encode_play_id(meta))
            if entries:
                groups.append((line["name"], "#".join(entries)))

        remarks = []
        if state["play_error_type"] == "captcha":
            remarks.append("站点当前需要验证码")
        if state["play_error_type"] == "need_vip":
            remarks.append("站点当前存在 VIP 限制")

        return {
            "list": [
                {
                    "vod_id": state["movieId"] or vod_id,
                    "vod_name": title or vod_id,
                    "vod_pic": self._abs_url(pic),
                    "vod_content": content,
                    "vod_remarks": " | ".join(remarks),
                    "vod_play_from": "$$$".join(name for name, _ in groups),
                    "vod_play_url": "$$$".join(urls for _, urls in groups),
                }
            ]
        }

    def _normalize_play_links(self, items):
        results = []
        for item in items or []:
            raw_url = str((item or {}).get("m3u8_url") or (item or {}).get("preview_m3u8_url") or "").strip()
            if not raw_url:
                continue
            results.append(
                {
                    "line_id": str((item or {}).get("id") or "").strip(),
                    "name": self._clean_text((item or {}).get("name")) or str((item or {}).get("id") or "线路"),
                    "url": urljoin(self.host + "/", raw_url),
                }
            )
        return results

    def _build_player_headers(self, referer, with_origin=False):
        headers = {"User-Agent": self.user_agent, "Referer": referer}
        if with_origin:
            headers["Origin"] = self.host
        return headers

    def _build_direct_result(self, entries, referer):
        return {
            "parse": 0,
            "playUrl": "",
            "url": entries[0]["url"] if entries else "",
            "urls": [{"name": item["name"], "url": item["url"]} for item in entries],
            "header": self._build_player_headers(referer, with_origin=True),
        }

    def _build_parse_result(self, url):
        return {
            "parse": 1,
            "playUrl": "",
            "url": url,
            "header": self._build_player_headers(url),
        }

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if not raw:
            return {"parse": 0, "playUrl": "", "url": "", "header": {}}
        if re.search(r"\.(m3u8|mp4|flv)(?:\?|#|$)", raw, re.I):
            return {
                "parse": 0,
                "playUrl": "",
                "url": raw,
                "header": self._build_player_headers(self.host + "/", with_origin=True),
            }

        meta = self._decode_play_id(raw)
        page_url = str(meta.get("page") or "").strip()
        if not page_url:
            movie_id = str(meta.get("movie_id") or "").strip()
            page_url = self.host + "/movie/detail/" + movie_id if movie_id else self.host + "/"

        html = self._request_html(page_url, self._page_headers(self.host + "/"))
        state = self._extract_page_state(html)
        movie_id = str(meta.get("movie_id") or state.get("movieId") or "").strip()
        link_id = str(meta.get("link_id") or state.get("linkId") or "").strip()
        line_id = str(meta.get("line_id") or "").strip()

        if movie_id and link_id:
            payload = self._request_json(
                self.host + "/movie/detail/" + movie_id,
                data={"link_id": link_id, "is_switch": 1},
                headers=self._ajax_headers(page_url),
            )
            data = (payload or {}).get("data") or {}
            urls = self._normalize_play_links(data.get("play_links") or [])
            if line_id:
                urls = [item for item in urls if item["line_id"] == line_id]
            if urls:
                return self._build_direct_result(urls, page_url)

        return self._build_parse_result(page_url)

    def _encode_play_id(self, payload):
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    def _decode_play_id(self, value):
        try:
            decoded = json.loads(str(value or "").strip())
        except Exception:
            decoded = {}
        return decoded if isinstance(decoded, dict) else {}
