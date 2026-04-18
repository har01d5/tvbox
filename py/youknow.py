# coding=utf-8
import base64
import ast
import json
import re
import sys
from urllib.parse import quote, unquote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "YouKnowTV"
        self.host = "https://www.youknow.tv"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.categories = [
            {"type_name": "今日更新", "type_id": "index"},
            {"type_name": "剧集", "type_id": "drama"},
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "综艺", "type_id": "variety"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "短剧", "type_id": "short"},
            {"type_name": "纪录片", "type_id": "doc"},
        ]
        self.category_paths = {
            "index": "/label/new/",
            "drama": "/show/1--------{pg}---/",
            "movie": "/show/2--------{pg}---/",
            "variety": "/show/3--------{pg}---/",
            "anime": "/show/4--------{pg}---/",
            "short": "/show/55--------{pg}---/",
            "doc": "/show/5--------{pg}---/",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def _build_url(self, href):
        raw = str(href or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return self.host + "/" + raw.lstrip("/")

    def _extract_vod_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/d/(\d+)/?$", raw) or re.search(r"/v/(\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"\d+", raw):
            return raw
        return ""

    def _extract_play_meta(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/p/(\d+)-(\d+)-(\d+)/?$", raw)
        if not matched:
            return None
        return {
            "vod_id": matched.group(1),
            "source_id": matched.group(2),
            "episode_index": int(matched.group(3)),
        }

    def _build_detail_request_url(self, vod_id):
        return f"{self.host}/d/{self._extract_vod_id(vod_id)}/"

    def _encode_episode_payload(self, payload):
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    def _decode_episode_payload(self, value):
        text = str(value or "")
        padded = text + "=" * (-len(text) % 4)
        return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))

    def _parse_list_cards(self, html):
        root = self.html(html)
        if root is None:
            return []

        results = []
        seen = set()
        for card in root.xpath("//*[contains(@class,'module-poster-item') or contains(@class,'module-card-item-poster')]"):
            href = ((card.xpath("./@href") or [""])[0]).strip()
            vod_id = self._extract_vod_id(href)
            title = ((card.xpath("./@title") or [""])[0]).strip() or ((card.xpath(".//@alt") or [""])[0]).strip()
            pic = (
                (card.xpath("./@data-original") or [""])[0].strip()
                or (card.xpath("./@data-src") or [""])[0].strip()
                or (card.xpath(".//img/@data-original") or [""])[0].strip()
                or (card.xpath(".//img/@data-src") or [""])[0].strip()
                or (card.xpath(".//@data-original") or [""])[0].strip()
                or (card.xpath(".//@data-src") or [""])[0].strip()
                or (card.xpath(".//@src") or [""])[0].strip()
            )
            remarks = "".join(
                card.xpath(".//*[contains(@class,'module-item-note') or contains(@class,'module-item-text')][1]//text()")
            ).strip()
            if not vod_id or vod_id in seen or not title:
                continue
            seen.add(vod_id)
            results.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return results

    def _request_html(self, path_or_url, expect_xpath=None, referer=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or (self.host + "/")
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _page_result(self, items, pg):
        page = int(pg)
        pagecount = page + 1 if items else page
        self.log(items[0])
        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": len(items),
            "total": pagecount * max(len(items), 1),
        }

    def _build_category_path(self, tid, pg):
        page = int(pg)
        if tid == "index":
            return self.category_paths["index"]
        type_map = {
            "drama": "1",
            "movie": "2",
            "variety": "3",
            "anime": "4",
            "short": "55",
            "doc": "5",
        }
        type_id = type_map.get(tid, "2")
        if page <= 1:
            return f"/show/{type_id}-----------/"
        return f"/show/{type_id}--------{page}---/"

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _extract_detail_field(self, root, label, joiner=""):
        if root is None:
            return ""
        nodes = root.xpath(f'.//span[normalize-space(.)="{label}："]')
        if not nodes:
            return ""
        label_node = nodes[0]
        parent = label_node.getparent()
        values = []

        if self._clean_text(label_node.tail):
            values.append(self._clean_text(label_node.tail))

        if parent is not None:
            started = False
            for child in parent.iterchildren():
                if child is label_node:
                    started = True
                    continue
                if not started:
                    continue
                text = self._clean_text("".join(child.xpath(".//text()")))
                if text:
                    values.append(text)
                tail = self._clean_text(child.tail)
                if tail:
                    values.append(tail)

        cleaned = []
        for value in values:
            if value and value not in cleaned:
                cleaned.append(value)
        return joiner.join(cleaned) if joiner else "".join(cleaned)

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        title = ((root.xpath("//*[contains(@class,'module-info-heading')]//h1[1]//text()") or [""])[0]).strip() or (
            (root.xpath("//h1[1]//text()") or [""])[0]
        ).strip()
        pic = (
            (root.xpath("//*[contains(@class,'module-info-poster')]//img/@data-original") or [""])[0].strip()
            or (root.xpath("//*[contains(@class,'module-info-poster')]//img/@src") or [""])[0].strip()
        )
        source_names = [self._clean_text(value) for value in root.xpath("//*[@data-dropdown-value]/@data-dropdown-value")]
        play_groups = root.xpath("//*[contains(@class,'module-play-list')]")
        aligned = {}

        for group_index, group in enumerate(play_groups):
            source_name = source_names[group_index] if group_index < len(source_names) else f"线路{group_index + 1}"
            for anchor in group.xpath(".//a[@href]"):
                href = (anchor.xpath("./@href") or [""])[0]
                meta = self._extract_play_meta(href)
                if not meta:
                    continue
                key = meta["episode_index"]
                if key not in aligned:
                    aligned[key] = {
                        "vod_id": meta["vod_id"],
                        "episode_index": key,
                        "title": self._clean_text("".join(anchor.xpath(".//text()"))),
                        "candidates": [],
                    }
                aligned[key]["candidates"].append(
                    {
                        "source": source_name,
                        "source_id": meta["source_id"],
                        "episode_url": self._build_url(href),
                    }
                )

        play_urls = []
        for episode_index in sorted(aligned):
            record = aligned[episode_index]
            payload = self._encode_episode_payload(record)
            title_text = record["title"] or f"第{episode_index}集"
            play_urls.append(f"{title_text}${payload}")

        vod = {
            "vod_id": vod_id,
            "path": self._build_detail_request_url(vod_id),
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_tag": "",
            "vod_time": "",
            "vod_remarks": self._extract_detail_field(root, "备注"),
            "vod_play_from": "YouKnowTV",
            "vod_play_url": "#".join(play_urls),
            "type_name": self._extract_detail_field(root, "类型"),
            "vod_content": self._extract_detail_field(root, "简介"),
            "vod_year": self._extract_detail_field(root, "年份"),
            "vod_area": self._extract_detail_field(root, "地区"),
            "vod_lang": self._extract_detail_field(root, "语言"),
            "vod_director": self._extract_detail_field(root, "导演", joiner=","),
            "vod_actor": self._extract_detail_field(root, "主演", joiner=","),
        }
        return {"list": [vod]}

    def homeVideoContent(self):
        html = self._request_html("/label/new/", expect_xpath="//*[contains(@class,'module-poster-item')]")
        return {"list": self._parse_list_cards(html)}

    def categoryContent(self, tid, pg, filter, extend):
        path = self._build_category_path(tid, pg)
        html = self._request_html(
            path,
            expect_xpath="//*[contains(@class,'module-poster-item') or contains(@class,'module-card-item-poster')]",
        )
        return self._page_result(self._parse_list_cards(html), pg)

    def searchContent(self, key, quick, pg="1"):
        path = "/search/-------------.html?wd={0}".format(quote(key))
        html = self._request_html(
            path,
            expect_xpath="//*[contains(@class,'module-poster-item') or contains(@class,'module-card-item-poster')]",
        )
        return self._page_result(self._parse_list_cards(html), pg)

    def detailContent(self, ids):
        vod_id = ids[0]
        html = self._request_html(
            self._build_detail_request_url(vod_id),
            expect_xpath="//*[contains(@class,'module-play-list')]",
        )
        return self._parse_detail_page(html, vod_id)

    def _safe_unquote(self, value):
        try:
            return unquote(str(value or ""))
        except Exception:
            return str(value or "")

    def _base64_decode(self, value):
        text = str(value or "").replace("-", "+").replace("_", "/")
        text += "=" * (-len(text) % 4)
        try:
            return base64.b64decode(text.encode("utf-8")).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _normalize_play_url(self, value):
        text = str(value or "").strip().replace("\\/", "/").replace("\\u0026", "&")
        if text.startswith("//"):
            return "https:" + text
        if text.startswith("/"):
            return self.host + text
        return text

    def _is_direct_play_url(self, value):
        text = str(value or "").strip().lower()
        if not text:
            return False
        return (
            text.startswith("http://")
            or text.startswith("https://")
            or text.startswith("//")
            or (text.startswith("/") and any(ext in text for ext in (".m3u8", ".mp4", ".flv")))
        ) and any(ext in text for ext in (".m3u8", ".mp4", ".flv"))

    def _parse_player_config(self, html):
        text = str(html or "")
        matched = re.search(r"player_aaaa\s*=", text, re.I)
        if not matched:
            return None
        object_start = text.find("{", matched.end())
        if object_start < 0:
            return None
        raw_object = self._extract_balanced_object(text, object_start)
        if not raw_object:
            return None
        return self._parse_object_literal(raw_object)

    def _extract_balanced_object(self, text, start_index):
        raw = str(text or "")
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

    def _parse_object_literal(self, raw):
        text = str(raw or "").strip()
        if not text:
            return None
        sanitized = re.sub(r",\s*}", "}", text)
        try:
            return json.loads(sanitized)
        except Exception:
            try:
                return ast.literal_eval(sanitized)
            except Exception:
                return None

    def _collect_direct_media_urls(self, html):
        text = str(html or "").replace("\\/", "/")
        urls = re.findall(r'https?:\/\/[^"\'\s]+?\.(?:m3u8|mp4|flv)(?:\?[^"\'\s]*)?', text, re.I)
        proto_less = [
            "https:" + item
            for item in re.findall(r'\/\/[^"\'\s]+?\.(?:m3u8|mp4|flv)(?:\?[^"\'\s]*)?', text, re.I)
        ]
        out = []
        for value in urls + proto_less:
            normalized = self._normalize_play_url(value)
            if normalized and normalized not in out:
                out.append(normalized)
        return out

    def _decode_player_url(self, raw_url, encrypt):
        mode = str(encrypt or "0")
        if mode == "1":
            return self._normalize_play_url(self._safe_unquote(raw_url))
        if mode == "2":
            seeds = [str(raw_url or ""), self._safe_unquote(raw_url), self._safe_unquote(self._safe_unquote(raw_url))]
            candidates = []
            for seed in seeds:
                for value in [seed, self._base64_decode(seed)]:
                    if not value:
                        continue
                    candidates.append(value)
                    candidates.append(self._safe_unquote(value))
                    candidates.append(self._safe_unquote(self._safe_unquote(value)))
            for value in candidates:
                for candidate in [value, self._safe_unquote(value), self._safe_unquote(self._safe_unquote(value))]:
                    normalized = self._normalize_play_url(candidate)
                    if self._is_direct_play_url(normalized):
                        return normalized
        return self._normalize_play_url(raw_url)

    def _collect_playable_urls_from_html(self, html):
        urls = []
        config = self._parse_player_config(html)
        if config and config.get("url"):
            decoded = self._decode_player_url(config.get("url", ""), config.get("encrypt", "0"))
            if decoded:
                urls.append(decoded)
        for value in self._collect_direct_media_urls(html):
            if value not in urls:
                urls.append(value)
        root = self.html(html)
        iframe = ""
        if root is not None:
            iframe = ((root.xpath("//*[contains(@class,'embed-responsive-item')][1]/@src")) or [""])[0]
        return urls, self._build_url(iframe) if iframe else ""

    def playerContent(self, flag, id, vipFlags):
        payload = self._decode_episode_payload(id)
        candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
        for candidate in candidates:
            episode_url = str(candidate.get("episode_url", "")).strip()
            if not episode_url:
                continue
            page_html = self._request_html(episode_url, referer=self.host + "/")
            page_urls, iframe_url = self._collect_playable_urls_from_html(page_html)
            if iframe_url:
                iframe_html = self._request_html(iframe_url, referer=episode_url)
                iframe_urls, _ = self._collect_playable_urls_from_html(iframe_html)
                for value in iframe_urls:
                    if value not in page_urls:
                        page_urls.append(value)
            if page_urls:
                return {
                    "parse": 0,
                    "playUrl": "",
                    "url": page_urls[0],
                    "header": {"User-Agent": self.headers["User-Agent"], "Referer": self.host + "/"},
                }
        return {"parse": 0, "playUrl": "", "url": ""}
