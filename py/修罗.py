# coding=utf-8
import gzip
import hashlib
import json
import os
import re
import sys
import time
from urllib.parse import quote, urljoin

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
if os.path.dirname(CURRENT_DIR) not in sys.path:
    sys.path.append(os.path.dirname(CURRENT_DIR))

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    BASE_SITE = "https://v.xlys.ltd.ua/"
    HOST = "v.xlys.ltd.ua"
    SEARCH_API = "https://www.ymck.pro/API/v2.php?q="
    SEARCH_SIZE = "&size=50"
    TARGET_WEBSITE = "哔滴"
    UA = (
        "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    )
    LOCAL_PROXY_BASE = "http://127.0.0.1:9978/proxy?do=py"

    def __init__(self):
        self.name = "修罗"
        self.host = "https://www.xlys02.com"
        self.origin = self.BASE_SITE
        self.url_re = re.compile(r"https?://[^/]+(?P<path>/.*?\.htm)", re.I)
        self.classes = [
            {"type_id": "movie", "type_name": "电影"},
            {"type_id": "tv", "type_name": "电视剧"},
            {"type_id": "zongyi", "type_name": "综艺"},
            {"type_id": "duanju", "type_name": "短剧"},
        ]
        common_genres = [
            {"n": "不限", "v": "all"},
            {"n": "动作", "v": "dongzuo"},
            {"n": "爱情", "v": "aiqing"},
            {"n": "喜剧", "v": "xiju"},
            {"n": "科幻", "v": "kehuan"},
            {"n": "恐怖", "v": "kongbu"},
            {"n": "战争", "v": "zhanzheng"},
            {"n": "武侠", "v": "wuxia"},
            {"n": "魔幻", "v": "mohuan"},
            {"n": "剧情", "v": "juqing"},
            {"n": "动画", "v": "donghua"},
            {"n": "惊悚", "v": "jingsong"},
            {"n": "灾难", "v": "zainan"},
            {"n": "悬疑", "v": "xuanyi"},
            {"n": "警匪", "v": "jingfei"},
            {"n": "文艺", "v": "wenyi"},
            {"n": "青春", "v": "qingchun"},
            {"n": "冒险", "v": "maoxian"},
            {"n": "犯罪", "v": "fanzui"},
            {"n": "记录", "v": "jilu"},
            {"n": "古装", "v": "guzhuang"},
            {"n": "奇幻", "v": "奇幻"},
        ]
        common_areas = [
            {"n": "不限", "v": ""},
            {"n": "中国大陆", "v": "中国大陆"},
            {"n": "中国香港", "v": "中国香港"},
            {"n": "美国", "v": "美国"},
            {"n": "日本", "v": "日本"},
            {"n": "韩国", "v": "韩国"},
            {"n": "法国", "v": "法国"},
            {"n": "印度", "v": "印度"},
            {"n": "德国", "v": "德国"},
            {"n": "西班牙", "v": "西班牙"},
            {"n": "意大利", "v": "意大利"},
            {"n": "澳大利亚", "v": "澳大利亚"},
            {"n": "比利时", "v": "比利时"},
            {"n": "瑞典", "v": "瑞典"},
            {"n": "荷兰", "v": "荷兰"},
            {"n": "丹麦", "v": "丹麦"},
            {"n": "加拿大", "v": "加拿大"},
            {"n": "俄罗斯", "v": "俄罗斯"},
        ]
        years = [{"n": "不限", "v": ""}] + [{"n": str(year), "v": str(year)} for year in range(2026, 2001, -1)]
        order_values = [{"n": "更新时间", "v": "0"}, {"n": "豆瓣评分", "v": "1"}]
        self.filters = {
            "movie": [
                {"key": "genre", "name": "类型", "init": "all", "value": list(common_genres)},
                {"key": "area", "name": "地区", "init": "", "value": list(common_areas)},
                {"key": "year", "name": "年份", "init": "", "value": list(years)},
                {"key": "order", "name": "排序", "init": "0", "value": list(order_values)},
            ],
            "tv": [
                {"key": "genre", "name": "类型", "init": "all", "value": list(common_genres)},
                {"key": "area", "name": "地区", "init": "", "value": list(common_areas)},
                {"key": "year", "name": "年份", "init": "", "value": list(years)},
                {"key": "order", "name": "排序", "init": "0", "value": list(order_values)},
            ],
            "zongyi": [
                {"key": "area", "name": "地区", "init": "", "value": list(common_areas)},
                {"key": "year", "name": "年份", "init": "", "value": list(years)},
                {"key": "order", "name": "排序", "init": "0", "value": list(order_values)},
            ],
            "duanju": [
                {"key": "year", "name": "年份", "init": "", "value": [{"n": "不限", "v": ""}] + [{"n": str(year), "v": str(year)} for year in range(2026, 2022, -1)]},
                {"key": "order", "name": "排序", "init": "0", "value": list(order_values)},
            ],
        }
        self._detail_title_blacklist = {"观看历史", "猜你喜欢", "相关推荐", "相关影视", "热门推荐", "为你推荐"}

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeContent(self, filter):
        return {"class": list(self.classes), "filters": self.filters, "list": []}

    def homeVideoContent(self):
        return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = max(int(str(pg or "1")), 1)
        type_id = self._stringify(tid).strip()
        if type_id not in self.filters:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        values = extend or {}
        if "genre" not in values:
            if type_id == "movie":
                values["genre"] = "all"
            if type_id == "tv":
                values["genre"] = "all"
        url = self._build_category_url(type_id, page, values)
        response = self.fetch(url, headers=self.build_headers(), timeout=15)
        if response.status_code != 200:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        items = self._parse_category_cards(response.text or "")
        return {"page": page, "limit": len(items), "total": page * 30 + len(items), "list": items}

    def build_headers(self, extra=None):
        headers = {
            "User-Agent": self.UA,
            "Origin": self.origin,
            "Referer": self.origin,
        }
        if isinstance(extra, dict):
            headers.update(extra)
        return headers

    def _site_headers(self, referer=None, extra=None):
        headers = {"User-Agent": self.UA, "Referer": referer or (self.host + "/")}
        if isinstance(extra, dict):
            headers.update(extra)
        return headers

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _build_url(self, value):
        raw = self._stringify(value).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return urljoin(self.host + "/", raw)

    def _extract_vod_path(self, value):
        raw = self._stringify(value).strip()
        if not raw:
            return ""
        if raw.startswith("/"):
            return "/" + raw.lstrip("/")
        matched = self.url_re.search(raw)
        if matched:
            return "/" + matched.group("path").lstrip("/")
        generic = re.search(r"(/[^?#\s]+?\.htm)", raw, re.I)
        if generic:
            return "/" + generic.group(1).lstrip("/")
        return ""

    def _extract_site_id(self, href):
        raw = self._stringify(href).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            matched = re.search(r"^https?://[^/]+/(.+?)(?:\.htm|[?#]|$)", raw, re.I)
            return matched.group(1).lstrip("/") if matched else ""
        cleaned = raw.split(".htm", 1)[0]
        return cleaned.lstrip("/")

    def _normalize_detail_id(self, value):
        raw = self._stringify(value).strip()
        if not raw:
            return ""
        path = self._extract_vod_path(raw)
        if path:
            return self._extract_site_id(path)
        return self._extract_site_id(raw)

    def _clean_text(self, value):
        return re.sub(r"\s+", " ", self._stringify(value).replace("\xa0", " ")).strip()

    def _extract_detail_title(self, root):
        if root is None:
            return ""
        candidate_xpaths = [
            "//*[contains(concat(' ', normalize-space(@class), ' '), ' detail ')]//*[self::h1 or self::h2][1]//text()",
            "//*[contains(concat(' ', normalize-space(@class), ' '), ' col ')]//*[self::h1 or self::h2][1]//text()",
            "//h1[1]//text()",
            "//h2//text()",
        ]
        for xpath in candidate_xpaths:
            nodes = root.xpath(xpath)
            if not nodes:
                continue
            texts = nodes if isinstance(nodes, list) else [nodes]
            for text in texts:
                title = self._clean_text(text)
                if title and title not in self._detail_title_blacklist:
                    return title
        return ""

    def _extract_labeled_meta(self, root):
        info = {}
        if root is None:
            return info
        for node in root.xpath("//p[strong[1]]|//li[strong[1]]|//div[strong[1]]"):
            label = self._clean_text("".join(node.xpath("./strong[1]//text()"))).rstrip(":：")
            if not label:
                continue

            link_texts = []
            for text in node.xpath(".//a//text()"):
                value = self._clean_text(text)
                if value and value not in link_texts:
                    link_texts.append(value)

            raw_text = self._clean_text("".join(node.xpath(".//text()")))
            raw_text = re.sub(r"^\s*%s\s*[:：]?\s*" % re.escape(label), "", raw_text).strip()

            value = ""
            if label in ("导演", "主演", "演员", "编剧", "类型"):
                value = " / ".join(link_texts) if link_texts else raw_text
            else:
                value = raw_text

            if label in ("制片国家/地区", "地区"):
                value = value.strip("[]")

            hrefs = [self._stringify(item).strip() for item in node.xpath(".//a/@href") if self._stringify(item).strip()]
            info[label] = {"value": value, "hrefs": hrefs, "links": link_texts}
        return info

    def _is_media_url(self, value):
        return re.search(r"^https?://.+\.(?:m3u8|mp4|flv|mkv|ts)(?:[?#].*)?$", self._stringify(value), re.I) is not None

    def _page_result(self, items, pg):
        page = max(int(str(pg or "1")), 1)
        return {"page": page, "limit": len(items), "total": (page - 1) * 50 + len(items), "list": items}

    def _build_category_url(self, tid, page, values):
        genre = self._stringify((values or {}).get("genre")).strip() or tid
        url = f"{self.host}/s/{genre}/{page}"
        params = []
        if tid not in ("zongyi", "duanju"):
            params.append("type=1" if tid == "tv" else "type=0")
        area = self._stringify((values or {}).get("area")).strip()
        year = self._stringify((values or {}).get("year")).strip()
        order = self._stringify((values or {}).get("order")).strip()
        if area:
            params.append(f"area={quote(area)}")
        if year:
            params.append(f"year={year}")
        if order:
            params.append(f"order={order}")
        return url + ("?" + "&".join(params) if params else "")

    def _parse_category_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        for card in root.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' card ') and contains(concat(' ', normalize-space(@class), ' '), ' card-link ')]"):
            href = self._stringify((card.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            vod_id = self._extract_site_id(href)
            if not vod_id:
                continue
            title = self._stringify("".join(card.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' card-title ')]//text()"))).strip()
            pic = self._stringify((card.xpath(".//img[1]/@src") or [""])[0]).strip()
            remarks = self._stringify("".join(card.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' text-muted ')]//text()"))).strip()
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def searchContent(self, key, quick, pg="1"):
        keyword = self._stringify(key).strip()
        if not keyword:
            return self._page_result([], pg)
        url = f"{self.SEARCH_API}{keyword}{self.SEARCH_SIZE}"
        response = self.fetch(url, headers=self.build_headers(), timeout=15)
        if response.status_code != 200:
            return self._page_result([], pg)
        try:
            payload = response.json()
        except Exception:
            return self._page_result([], pg)

        items = []
        for row in payload.get("data", []) or []:
            if self._stringify((row or {}).get("website")).strip() != self.TARGET_WEBSITE:
                continue
            vod_id = self._extract_vod_path((row or {}).get("url"))
            if not vod_id:
                continue
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._stringify((row or {}).get("text")).strip(),
                    "vod_pic": self._stringify((row or {}).get("icon")).strip(),
                    "vod_remarks": self._stringify((row or {}).get("website")).strip(),
                }
            )
        return self._page_result(items, pg)

    def detailContent(self, ids):
        vod_id = self._normalize_detail_id(ids[0] if ids else "")
        if not vod_id:
            return {"list": []}
        detail_url = f"{self.host}/{vod_id}.htm"
        response = self.fetch(detail_url, headers=self._site_headers(detail_url), timeout=15)
        if response.status_code != 200:
            return {"list": []}
        root = self.html(response.text or "")
        if root is None:
            return {"list": []}
        play_urls = []
        for anchor in root.xpath("//*[@id='play-list']//a[@href]"):
            name = self._stringify("".join(anchor.xpath(".//text()"))).strip()
            href = self._stringify((anchor.xpath("./@href") or [""])[0]).strip()
            play_id = self._extract_site_id(href)
            if name and play_id:
                play_urls.append(f"{name}${play_id}")
        meta = self._extract_labeled_meta(root)
        type_name = self._stringify((meta.get("类型") or {}).get("value")).strip()
        douban_meta = meta.get("豆瓣链接") or meta.get("豆瓣ID") or {}
        douban_text = self._stringify(douban_meta.get("value")).strip()
        douban_id = ""
        for href in douban_meta.get("hrefs") or []:
            matched = re.search(r"douban\.com/subject/(\d+)", href, re.I)
            if matched:
                douban_id = matched.group(1)
                break
        if not douban_id:
            matched = re.search(r"\b(\d{5,})\b", douban_text)
            if matched:
                douban_id = matched.group(1)
        score_meta = meta.get("豆瓣评分") or meta.get("豆瓣") or meta.get("评分") or {}
        score_text = self._stringify(score_meta.get("value")).strip()
        score_match = re.search(r"(\d+(?:\.\d+)?)", score_text)
        vod = {
            "vod_id": vod_id,
            "vod_name": self._extract_detail_title(root),
            "vod_pic": self._build_url((root.xpath("//img[contains(concat(' ', normalize-space(@class), ' '), ' cover ')]/@src") or [""])[0]),
            "type_name": type_name,
            "vod_class": type_name,
            "vod_year": self._stringify((meta.get("年代") or meta.get("年份") or {}).get("value")).strip(),
            "vod_area": self._stringify((meta.get("制片国家/地区") or meta.get("地区") or {}).get("value")).strip(),
            "vod_lang": self._stringify((meta.get("语言") or {}).get("value")).strip(),
            "vod_remarks": self._stringify((meta.get("摘要") or {}).get("value")).strip(),
            "vod_actor": self._stringify((meta.get("主演") or meta.get("演员") or {}).get("value")).strip(),
            "vod_director": self._stringify((meta.get("导演") or {}).get("value")).strip(),
            "vod_douban_score": score_match.group(1) if score_match else "",
            "vod_douban_id": douban_id,
            "vod_content": self._clean_text("".join(root.xpath("//*[@id='synopsis'][1]//text()"))),
            "vod_play_from": "修罗直连" if play_urls else "",
            "vod_play_url": "#".join(play_urls),
        }
        return {"list": [vod]}

    def _current_millis(self):
        return int(time.time() * 1000)

    def _load_json(self, response):
        if response is None:
            return {}
        try:
            return response.json()
        except Exception:
            try:
                return json.loads(self._stringify(getattr(response, "text", "")) or "{}")
            except Exception:
                return {}

    def _build_play_page_url(self, value):
        raw = self._stringify(value).strip()
        if not raw:
            return ""
        if self._is_media_url(raw):
            return raw
        if raw.startswith(("http://", "https://")):
            return raw
        return f"{self.host}/{self._extract_site_id(raw)}.htm"

    def _extract_pid(self, html):
        matched = re.search(r"var\s+pid\s*=\s*(\d+)\s*;", self._stringify(html))
        return self._stringify(matched.group(1) if matched else "").strip()

    def _build_lines_signature(self, pid, millis):
        payload = f"{pid}-{millis}"
        key = hashlib.md5(payload.encode("utf-8")).hexdigest()[:16]
        return self._aes_ecb_hex(key, payload).upper()

    def _pick_direct_urls(self, data):
        urls = []
        for item in self._stringify((data or {}).get("url3")).split(","):
            url = self._stringify(item).strip()
            if not url:
                continue
            lower = url.lower()
            if ".m3u8" in lower or "byteimg" in lower:
                continue
            urls.append(url)
        return urls

    def _request_tos_url(self, pid, millis, sg, play_page_url):
        target = f"{self.host}/god/{pid}?type=1"
        response = self.post(
            target,
            data=f"t={millis}&sg={sg}&verifyCode=888",
            headers=self._site_headers(play_page_url),
            timeout=15,
        )
        data = self._load_json(response)
        url = self._stringify((data or {}).get("url")).strip()
        if not url:
            return ""
        lower = url.lower()
        if ".m3u8" in lower or "byteimg" in lower:
            return ""
        return url

    def _range_probe(self, url):
        return self.fetch(
            url,
            headers=self.build_headers({"Range": "bytes=0-0"}),
            timeout=20,
            stream=True,
        )

    def _make_proxy_url(self, real_url):
        return f"{self.LOCAL_PROXY_BASE}&type=m3u8&url={quote(self._stringify(real_url).strip(), safe='')}"

    def _aes_ecb_hex(self, key, data):
        cipher = AES.new(str(key).encode("utf-8"), AES.MODE_ECB)
        return cipher.encrypt(pad(self._stringify(data).encode("utf-8"), 16)).hex()

    def _decode_m3u8_payload(self, payload):
        return gzip.decompress(payload[3354:]).decode("utf-8")

    def _rewrite_m3u8(self, text, real_url):
        lines = []
        for raw_line in self._stringify(text).splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                lines.append(raw_line)
                continue
            target = line if line.startswith(("http://", "https://")) else urljoin(real_url, line)
            lines.append(self._make_proxy_url(target))
        return "\n".join(lines)

    def playerContent(self, flag, id, vipFlags):
        raw = self._stringify(id).strip()
        if not raw:
            return {"parse": 1, "jx": 1, "playUrl": "", "url": "", "header": self.build_headers()}

        if not self._is_media_url(raw):
            play_page_url = self._build_play_page_url(raw)
            response = self.fetch(play_page_url, headers=self._site_headers(play_page_url), timeout=15)
            html = response.text if response.status_code == 200 else ""
            pid = self._extract_pid(html)
            if not pid:
                return {"parse": 1, "jx": 1, "playUrl": "", "url": play_page_url, "header": self._site_headers(play_page_url)}

            millis = self._current_millis()
            sg = self._build_lines_signature(pid, millis)
            lines_url = f"{self.host}/lines?t={millis}&sg={sg}&pid={pid}"
            lines_response = self.fetch(
                lines_url,
                headers=self._site_headers(play_page_url, {"X-Requested-With": "XMLHttpRequest"}),
                timeout=15,
            )
            payload = self._load_json(lines_response)
            data = (payload or {}).get("data") or {}
            if int((payload or {}).get("code", 0)) == 0:
                direct_urls = self._pick_direct_urls(data)
                if direct_urls:
                    return {
                        "parse": 0,
                        "jx": 0,
                        "playUrl": "",
                        "url": direct_urls[0],
                        "header": {"User-Agent": self.UA, "Referer": self.host},
                    }
                if data.get("tos"):
                    tos_url = self._request_tos_url(pid, millis, sg, play_page_url)
                    if tos_url:
                        return {
                            "parse": 0,
                            "jx": 0,
                            "playUrl": "",
                            "url": tos_url,
                            "header": {"User-Agent": self.UA, "Referer": self.host},
                        }
            return {"parse": 1, "jx": 1, "playUrl": "", "url": play_page_url, "header": self._site_headers(play_page_url)}

        if re.search(r"\.mp4(?:[?#]|$)", raw, re.I):
            try:
                response = self._range_probe(raw)
                if "video/mp4" in self._stringify(response.headers.get("Content-Type")).lower():
                    return {"parse": 0, "jx": 0, "playUrl": "", "url": raw, "header": self.build_headers()}
            except Exception:
                return {"parse": 0, "jx": 0, "playUrl": "", "url": raw, "header": self.build_headers()}

        return {"parse": 0, "jx": 0, "playUrl": "", "url": self._make_proxy_url(raw), "header": self.build_headers()}

    def localProxy(self, params):
        if not isinstance(params, dict):
            return None
        if self._stringify(params.get("type")).strip().lower() != "m3u8":
            return None
        real_url = self._stringify(params.get("url")).strip()
        if not real_url:
            return None

        response = self.fetch(real_url, headers=self.build_headers(), timeout=20)
        if response.status_code != 200:
            return [response.status_code, "text/plain", b""]
        rewritten = self._rewrite_m3u8(self._decode_m3u8_payload(response.content), real_url)
        return [200, "application/vnd.apple.mpegurl", rewritten.encode("utf-8")]

    def isVideoFormat(self, url):
        return self._is_media_url(url)

    def manualVideoCheck(self):
        return False
