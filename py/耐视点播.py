# coding=utf-8
import json
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "耐视点播"
        self.host = "https://nsvod.me"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "连续剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "37", "type_name": "Netflix"},
            {"type_id": "40", "type_name": "纪录片"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes}

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _clean_text(self, text):
        raw = self._stringify(text).replace("&nbsp;", " ")
        raw = re.sub(r"<[^>]+>", " ", raw)
        return re.sub(r"\s+", " ", raw).strip()

    def _build_url(self, path):
        raw = self._stringify(path).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return urljoin(self.host + "/", raw)

    def _extract_vod_id(self, href):
        matched = re.search(r"/index\.php/vod/detail/id/(\d+)\.html", self._stringify(href))
        return matched.group(1) if matched else ""

    def _build_detail_url(self, vod_id):
        return self._build_url(f"/index.php/vod/detail/id/{self._stringify(vod_id).strip()}.html")

    def _request_html(self, path_or_url, headers=None, referer=None):
        target = path_or_url if self._stringify(path_or_url).startswith("http") else self._build_url(path_or_url)
        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)
        merged_headers["Referer"] = referer or self.headers["Referer"]
        response = self.fetch(target, headers=merged_headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_cards(self, html):
        items = []
        seen = set()
        for block, href, vod_id, title in re.findall(
            r'(<a[^>]*href="(/index\.php/vod/detail/id/(\d+)\.html)"[^>]*title="([^"]*)"[^>]*>[\s\S]*?</a>)',
            self._stringify(html),
            re.I,
        ):
            if vod_id in seen or not title:
                continue
            seen.add(vod_id)
            pic_match = re.search(r'data-src="([^"]*)"', block, re.I) or re.search(r'src="([^"]*)"', block, re.I)
            remarks_match = re.search(r'public-list-prb[^>]*>([^<]*)</span>', block, re.I)
            if not remarks_match:
                remarks_match = re.search(r'public-list-subtitle[^>]*>([^<]*)</div>', block, re.I)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title.strip(),
                    "vod_pic": self._build_url(pic_match.group(1) if pic_match else ""),
                    "vod_remarks": self._clean_text(remarks_match.group(1) if remarks_match else ""),
                }
            )
        return items

    def homeVideoContent(self):
        return {"list": self._parse_cards(self._request_html(self.host + "/"))}

    def _extract_section_cards(self, html, tid):
        section_map = {
            "1": "最新电影",
            "2": "最新连续剧",
            "3": "最新综艺",
            "4": "最新动漫",
            "37": "最新Netflix",
            "40": "最新纪录片",
        }
        section_name = section_map.get(self._stringify(tid))
        if not section_name:
            return []
        markers = [
            "最新热播",
            "最新Netflix",
            "最新电影",
            "最新连续剧",
            "最新资讯",
            "最新动漫",
            "最新综艺",
            "最新纪录片",
        ]
        body = self._stringify(html)
        start_tag = f'title-h cor4">{section_name}'
        start = body.find(start_tag)
        if start < 0:
            return []
        end = len(body)
        for name in markers:
            if name == section_name:
                continue
            pos = body.find(f'title-h cor4">{name}', start + len(start_tag))
            if pos > 0 and pos < end:
                end = pos
        return self._parse_cards(body[start:end])

    def _parse_search_cards(self, html):
        items = []
        seen = set()
        for block in re.findall(
            r'(<div[^>]*class="[^"]*module-search-item[^"]*"[^>]*>[\s\S]*?</div>)',
            self._stringify(html),
            re.I,
        ):
            href_match = re.search(r'class="[^"]*video-serial[^"]*"[^>]*href="([^"]*)"', block, re.I)
            title_match = re.search(r'class="[^"]*video-serial[^"]*"[^>]*title="([^"]*)"', block, re.I)
            pic_match = re.search(r'data-src="([^"]*)"', block, re.I) or re.search(r'src="([^"]*)"', block, re.I)
            remark_match = re.search(r'class="[^"]*video-serial[^"]*"[^>]*>([^<]*)</a>', block, re.I)
            vod_id = self._extract_vod_id(href_match.group(1) if href_match else "")
            if not vod_id or vod_id in seen:
                continue
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_text(title_match.group(1) if title_match else ""),
                    "vod_pic": self._build_url(pic_match.group(1) if pic_match else ""),
                    "vod_remarks": self._clean_text(remark_match.group(1) if remark_match else ""),
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        url = self._build_url(f"/index.php/vod/show/id/{tid}.html?page={page}")
        items = self._parse_cards(self._request_html(url))
        if not items:
            items = self._extract_section_cards(self._request_html(self.host + "/"), tid)
        return {"page": page, "limit": len(items), "total": page * 20 + len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        url = self._build_url(f"/index.php/vod/search.html?wd={quote(keyword)}")
        items = self._parse_search_cards(self._request_html(url))
        return {"page": page, "total": len(items), "list": items}

    def _strip_title(self, title):
        matched = re.search(r"《([^》]+)》", self._stringify(title))
        if matched:
            return matched.group(1)
        return self._clean_text(title)

    def _parse_play_groups(self, html):
        source_names = []
        for raw in re.findall(r'<div[^>]*class="[^"]*swiper-slide[^"]*"[^>]*>([\s\S]*?)</div>', self._stringify(html), re.I):
            cleaned = re.sub(r"\d+\s*集?$", "", self._clean_text(raw)).strip()
            if cleaned:
                source_names.append(cleaned)

        groups = []
        for index, block in enumerate(
            re.findall(r'(<div[^>]*class="[^"]*anthology-list-box[^"]*"[^>]*>[\s\S]*?</div>)', self._stringify(html), re.I)
        ):
            episodes = []
            for href, title in re.findall(r'<a[^>]*href="([^"]*/index\.php/vod/play/[^"]*)"[^>]*>([\s\S]*?)</a>', block, re.I):
                episodes.append(f"{self._clean_text(title)}${href.replace('&amp;', '&').strip()}")
            if episodes:
                groups.append((source_names[index] if index < len(source_names) else f"线路{index + 1}", "#".join(episodes)))

        if not groups:
            episodes = []
            for href, title in re.findall(
                r'<a[^>]*href="([^"]*/index\.php/vod/play/[^"]*)"[^>]*>([\s\S]*?)</a>',
                self._stringify(html),
                re.I,
            ):
                episodes.append(f"{self._clean_text(title)}${href.replace('&amp;', '&').strip()}")
            if episodes:
                groups.append(("线路1", "#".join(episodes)))
        return groups

    def _parse_detail_page(self, vod_id, html):
        body = self._stringify(html)
        name_match = re.search(r"<title>([^<]+)</title>", body, re.I)
        name = self._strip_title(name_match.group(1) if name_match else "")
        if not name:
            slide_match = re.search(r'slide-info-title[^>]*>([^<]+)<', body, re.I)
            name = self._clean_text(slide_match.group(1) if slide_match else "")

        pic_match = re.search(r'detail-pic[\s\S]*?data-src="([^"]*)"', body, re.I) or re.search(
            r'detail-pic[\s\S]*?src="([^"]*)"',
            body,
            re.I,
        )
        year_match = re.search(r"年份</em>[\s\S]*?<span>(\d{4})</span>", body, re.I) or re.search(r"年份[\s\S]*?(\d{4})", body, re.I)
        area_match = re.search(r"地区</em>[\s\S]*?<span>([^<]+)</span>", body, re.I)
        director_match = re.search(r"导演</em>\s*([^<\n]+)", body, re.I)
        actor_match = re.search(r"主演</em>\s*([^<\n]+)", body, re.I)
        content_match = re.search(r'id="height_limit"[^>]*>([\s\S]*?)</div>', body, re.I)
        groups = self._parse_play_groups(body)

        director = self._clean_text(director_match.group(1) if director_match else "")
        actor = self._clean_text(actor_match.group(1) if actor_match else "")
        return {
            "vod_id": self._stringify(vod_id),
            "vod_name": name,
            "vod_pic": self._build_url(pic_match.group(1) if pic_match else ""),
            "vod_year": year_match.group(1) if year_match else "",
            "vod_area": self._clean_text(area_match.group(1) if area_match else ""),
            "vod_director": "" if director == "未知" else director,
            "vod_actor": "" if actor == "未知" else actor,
            "vod_content": self._clean_text(content_match.group(1) if content_match else "") or "暂无简介",
            "vod_play_from": "$$$".join(item[0] for item in groups),
            "vod_play_url": "$$$".join(item[1] for item in groups),
        }

    def detailContent(self, ids):
        vod_id = self._stringify(ids[0] if isinstance(ids, list) and ids else ids).strip()
        if not vod_id:
            return {"list": []}
        vod = self._parse_detail_page(vod_id, self._request_html(self._build_detail_url(vod_id)))
        if not vod.get("vod_play_from"):
            return {"list": []}
        return {"list": [vod]}

    def _extract_balanced_object(self, text, start_index):
        raw = self._stringify(text)
        if start_index < 0 or start_index >= len(raw) or raw[start_index] != "{":
            return ""

        depth = 0
        in_string = False
        quote_char = ""
        escaped = False

        for index in range(start_index, len(raw)):
            char = raw[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote_char:
                    in_string = False
                continue

            if char in ('"', "'"):
                in_string = True
                quote_char = char
                continue

            if char == "{":
                depth += 1
                continue

            if char == "}":
                depth -= 1
                if depth == 0:
                    return raw[start_index : index + 1]

        return ""

    def _extract_player_data(self, html):
        text = self._stringify(html)
        matched = re.search(r"player_aaaa\s*=", text, re.I)
        if not matched:
            return {}
        object_start = text.find("{", matched.end())
        if object_start < 0:
            return {}
        raw_object = self._extract_balanced_object(text, object_start)
        if not raw_object:
            return {}
        try:
            return json.loads(raw_object)
        except Exception:
            return {}

    def _pick_direct_media_url(self, html):
        matched = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', self._stringify(html), re.I)
        return matched.group(1) if matched else ""

    def playerContent(self, flag, id, vipFlags):
        play_url = self._build_url(id)
        html = self._request_html(play_url, headers={"User-Agent": self.headers["User-Agent"]}, referer=self.host + "/")
        player_data = self._extract_player_data(html)
        if player_data.get("url"):
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": self._stringify(player_data.get("url")),
                "header": {"User-Agent": self.headers["User-Agent"], "Referer": play_url},
            }

        media_url = self._pick_direct_media_url(html)
        if media_url:
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": media_url,
                "header": {"User-Agent": self.headers["User-Agent"], "Referer": play_url},
            }

        return {
            "parse": 0,
            "jx": 1,
            "playUrl": "",
            "url": play_url,
            "header": dict(self.headers),
        }
