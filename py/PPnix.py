# coding=utf-8
import re
import sys
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "PPnix[采]"
        self.host = "https://www.ppnix.com"
        self.lang_path = "/cn"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + self.lang_path + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
        ]
        sort_values = [
            {"n": "按时间", "v": "time"},
            {"n": "按人气", "v": "hits"},
            {"n": "按评分", "v": "score"},
        ]
        self.filters = {
            "1": [
                {
                    "key": "class",
                    "name": "类型",
                    "init": "",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "动作", "v": "动作"},
                        {"n": "喜剧", "v": "喜剧"},
                        {"n": "剧情", "v": "剧情"},
                    ],
                },
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
            "2": [
                {
                    "key": "class",
                    "name": "类型",
                    "init": "",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "爱情", "v": "爱情"},
                        {"n": "古装", "v": "古装"},
                        {"n": "悬疑", "v": "悬疑"},
                    ],
                },
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def _build_url(self, value):
        raw = str(value or "").strip()
        if not raw:
            return self.host + self.lang_path + "/"
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _map_type_slug(self, tid):
        return "tv" if str(tid) == "2" else "movie"

    def _map_sort(self, value):
        mapping = {"time": "newstime", "hits": "onclick", "score": "rating"}
        return mapping.get(str(value or "time"), "newstime")

    def _build_category_url(self, tid, pg, extend):
        values = extend if isinstance(extend, dict) else {}
        slug = self._map_type_slug(tid)
        genre = str(values.get("class") or "").strip()
        page = max(int(pg), 1)
        page_part = "" if page <= 1 else str(page - 1)
        sort = self._map_sort(values.get("by", "time"))
        return self._build_url(f"{self.lang_path}/{slug}/{genre}---{page_part}-{sort}.html")

    def _build_search_url(self, keyword, pg):
        page = max(int(pg), 1)
        suffix = "" if page <= 1 else f"-page-{page}"
        encoded = quote(str(keyword or "").strip())
        return self._build_url(f"{self.lang_path}/search/{encoded}--.html{suffix}")

    def _text(self, node):
        return node.get_text(" ", strip=True) if node else ""

    def _request_html(self, path_or_url, referer=None, extra_headers=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.headers["Referer"]
        if isinstance(extra_headers, dict):
            headers.update(extra_headers)
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _dedupe(self, items):
        seen = set()
        result = []
        for item in items:
            vod_id = str(item.get("vod_id") or "").strip()
            if not vod_id or vod_id in seen:
                continue
            seen.add(vod_id)
            result.append(item)
        return result

    def _parse_cards(self, html):
        soup = BeautifulSoup(html or "", "html.parser")
        items = []
        for node in soup.select("li"):
            anchor = node.select_one("a.thumbnail") or node.select_one("h2 a") or node.select_one("a")
            image = node.select_one("img.thumb")
            if not anchor:
                continue
            href = str(anchor.get("href") or "").strip()
            if not re.search(r"/cn/(movie|tv)/\d+\.html", href):
                continue
            vod_name = str((image.get("alt") if image else "") or self._text(anchor)).strip()
            if not vod_name:
                continue
            items.append(
                {
                    "vod_id": href.replace("/cn/", "").lstrip("/"),
                    "vod_name": vod_name,
                    "vod_pic": self._build_url((image.get("src") if image else "") or ""),
                    "vod_remarks": self._text(node.select_one("footer .rate") or node.select_one("footer")),
                }
            )
        return items

    def _extract_m3u8_items(self, html):
        body = str(html or "")
        info_match = re.search(r"infoid\s*=\s*(\d+)", body)
        list_match = re.search(r"m3u8\s*=\s*\[(.*?)\]", body, re.S)
        raw_list = list_match.group(1) if list_match else ""
        items = []
        for single, double in re.findall(r"'([^']*)'|\"([^\"]*)\"", raw_list):
            value = str(single or double or "").strip()
            if value:
                items.append(value)
        return {"info_id": info_match.group(1) if info_match else "", "items": items}

    def _build_play_id(self, info_id, param):
        return f"{str(info_id or '').strip()}|{quote(str(param or '').strip())}"

    def _parse_play_id(self, play_id):
        parts = str(play_id or "").split("|", 1)
        if len(parts) != 2:
            return {"info_id": "", "param": ""}
        info_id = parts[0].strip()
        param = unquote(parts[1].strip())
        if not info_id or not param:
            return {"info_id": "", "param": ""}
        return {"info_id": info_id, "param": param}

    def _extract_excerpt_text(self, soup, label):
        for node in soup.select(".product-excerpt"):
            text = self._text(node)
            if text.startswith(label) or label in text:
                return text.replace(label, "", 1).strip()
        return ""

    def homeVideoContent(self):
        html = self._request_html(self.lang_path + "/")
        soup = BeautifulSoup(html or "", "html.parser")
        blocks = soup.select(".lists-content ul")
        items = []
        if len(blocks) > 0:
            items.extend(self._parse_cards(str(blocks[0])))
        if len(blocks) > 1:
            items.extend(self._parse_cards(str(blocks[1])))
        return {"list": self._dedupe(items)[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = max(int(pg), 1)
        slug = self._map_type_slug(tid)
        html = self._request_html(self._build_category_url(tid, pg, extend or {}))
        items = [item for item in self._parse_cards(html) if item["vod_id"].startswith(slug + "/")]
        return {"page": page, "limit": 24, "total": page * 24 + len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = max(int(pg), 1)
        items = self._parse_cards(self._request_html(self._build_search_url(key, pg)))
        if str(quick).lower() == "true":
            items = items[:10]
        return {"page": page, "limit": 24, "total": page * 24 + len(items), "list": items}

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, list) and ids else ids or "").strip().lstrip("/")
        if not vod_id:
            return {"list": []}
        html = self._request_html(f"{self.lang_path}/{vod_id}")
        if not html:
            return {"list": []}
        soup = BeautifulSoup(html, "html.parser")
        title_text = self._text(soup.select_one("h1.product-title") or soup.select_one("title"))
        info = self._extract_m3u8_items(html)
        play_urls = []
        for item in info["items"]:
            play_urls.append(f"{item}${self._build_play_id(info['info_id'], item)}")
        actor = self._extract_excerpt_text(soup, "主演：").replace(" / ", ",").replace("/", ",")
        vod_name = re.sub(r"\s*\([^)]*\)\s*$", "", title_text).strip()
        year_match = re.search(r"\((\d{4})\)", title_text)
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": vod_name,
                    "vod_pic": self._build_url((soup.select_one("header.product-header img.thumb") or {}).get("src", "")),
                    "type_name": "电视剧" if vod_id.startswith("tv/") else "电影",
                    "vod_year": year_match.group(1) if year_match else "",
                    "vod_director": self._extract_excerpt_text(soup, "导演："),
                    "vod_actor": actor,
                    "vod_content": self._extract_excerpt_text(soup, "简介："),
                    "vod_play_from": "PPnix" if play_urls else "",
                    "vod_play_url": "#".join(play_urls),
                }
            ]
        }

    def playerContent(self, flag, id, vipFlags):
        meta = self._parse_play_id(id)
        if not meta["info_id"] or not meta["param"]:
            return {"parse": 1, "jx": 1, "url": str(id or ""), "header": {}}
        encoded = quote(meta["param"])
        return {
            "parse": 0,
            "jx": 0,
            "url": self._build_url(f"/info/m3u8/{meta['info_id']}/{encoded}.m3u8"),
            "header": {
                "Referer": self.host + self.lang_path + "/",
                "Origin": self.host,
                "User-Agent": self.headers["User-Agent"],
            },
        }
