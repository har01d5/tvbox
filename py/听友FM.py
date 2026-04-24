# coding=utf-8
import json
import re
import sys
import time
from hashlib import sha256
from urllib.parse import quote

from Crypto.Cipher import AES
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
from lxml import html as lxml_html

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "听友FM"
        self.host = "https://tingyou.fm"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
            "Origin": self.host,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.payload_key_hex = "ea9d9d4f9a983fe6f6382f29c7b46b8d6dc47abc6da36662e6ddff8c78902f65"
        self.payload_version = 1
        self.classes = [
            {"type_id": "46", "type_name": "有声小说"},
            {"type_id": "11", "type_name": "武侠小说"},
            {"type_id": "19", "type_name": "言情通俗"},
            {"type_id": "21", "type_name": "相声小品"},
            {"type_id": "14", "type_name": "恐怖惊悚"},
            {"type_id": "17", "type_name": "官场商战"},
            {"type_id": "15", "type_name": "历史军事"},
            {"type_id": "9", "type_name": "百家讲坛"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _get_headers(self, extra=None):
        headers = dict(self.headers)
        if extra:
            headers.update(extra)
        return headers

    def _normalize_url(self, url):
        value = str(url or "").strip()
        if not value:
            return ""
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if value.startswith("//"):
            return "https:" + value
        if value.startswith("/"):
            return self.host + value
        return value

    def _safe_text(self, node):
        if node is None:
            return ""
        if isinstance(node, str):
            return re.sub(r"\s+", " ", node).strip()
        return re.sub(r"\s+", " ", "".join(node.itertext())).strip()

    def _load_html(self, content):
        text = str(content or "").strip() or "<html></html>"
        return lxml_html.fromstring(text)

    def _get_html(self, path):
        url = path if str(path).startswith("http") else self.host + (path if str(path).startswith("/") else "/" + str(path))
        try:
            response = self.fetch(url, headers=self._get_headers(), timeout=10, verify=False)
        except Exception:
            return ""
        return response.text if getattr(response, "status_code", 0) == 200 else ""

    def _hex_to_bytes(self, hex_text):
        return bytes.fromhex(str(hex_text or "").strip())

    def _bytes_to_hex(self, data):
        return bytes(data or b"").hex()

    def _encrypt_payload(self, plain_text):
        key = self._hex_to_bytes(self.payload_key_hex)
        iv = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        encrypted, tag = cipher.encrypt_and_digest(str(plain_text or "").encode("utf-8"))
        return self._bytes_to_hex(bytes([self.payload_version]) + iv + encrypted + tag)

    def _decrypt_xchacha_body(self, key, nonce, body):
        cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
        return cipher.decrypt_and_verify(body[:-16], body[-16:])

    def _decrypt_aes_gcm_payload(self, raw, attempts):
        key = self._hex_to_bytes(self.payload_key_hex)
        last_error = None
        for iv_start, cipher_start in attempts:
            try:
                iv = raw[iv_start:iv_start + 12]
                body = raw[cipher_start:]
                encrypted = body[:-16]
                tag = body[-16:]
                cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
                return cipher.decrypt_and_verify(encrypted, tag).decode("utf-8")
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error
        raise ValueError("aes decrypt failed")

    def _decrypt_payload(self, hex_text):
        raw = self._hex_to_bytes(hex_text)
        if len(raw) < 2:
            raise ValueError("payload too short")
        version = raw[0]
        key = self._hex_to_bytes(self.payload_key_hex)
        if version == 1:
            if len(raw) >= 41:
                try:
                    plain = self._decrypt_xchacha_body(key, raw[1:25], raw[25:])
                    return plain.decode("utf-8")
                except Exception:
                    pass
            return self._decrypt_aes_gcm_payload(raw, [(1, 13), (0, 12), (2, 14)])
        if version == 2:
            nonce = raw[1:25]
            body = raw[25:][::-1]
            plain = self._decrypt_xchacha_body(key, nonce, body)
            return bytes(plain).decode("utf-8")
        raise ValueError("unsupported payload version")

    def _make_dfp_cookie(self):
        today_hex = format(int(time.strftime("%Y%m%d")), "x")
        seed = f"{time.time()}|tingyou|{get_random_bytes(8).hex()}".encode("utf-8")
        return f"dfp=f-{today_hex}:f-{sha256(seed).hexdigest()}"

    def _decode_nuxt_value(self, table, node, seen=None):
        seen = seen or {}
        markers = {
            "ShallowReactive",
            "Reactive",
            "Ref",
            "EmptyRef",
            "Set",
            "Map",
            "Date",
            "RegExp",
            "BigInt",
            "null",
            "undefined",
            "NaN",
            "-0",
            "Infinity",
            "-Infinity",
        }
        if isinstance(node, int) and 0 <= node < len(table):
            if node in seen:
                return seen[node]
            raw = table[node]
            if isinstance(raw, list) and raw and isinstance(raw[0], str) and raw[0] in markers:
                marker = raw[0]
                if marker in ("ShallowReactive", "Reactive", "Ref"):
                    value = self._decode_nuxt_value(table, raw[1] if len(raw) > 1 else None, seen)
                    seen[node] = value
                    return value
                if marker in ("EmptyRef", "null", "undefined", "NaN"):
                    seen[node] = None
                    return None
            if isinstance(raw, dict):
                seen[node] = {}
                for key, value in raw.items():
                    seen[node][key] = self._decode_nuxt_value(table, value, seen)
                return seen[node]
            if isinstance(raw, list):
                seen[node] = []
                for item in raw:
                    seen[node].append(self._decode_nuxt_value(table, item, seen))
                return seen[node]
            return raw
        if isinstance(node, list):
            return [self._decode_nuxt_value(table, item, seen) for item in node]
        if isinstance(node, dict):
            return {key: self._decode_nuxt_value(table, value, seen) for key, value in node.items()}
        return node

    def _load_nuxt_root(self, html):
        match = re.search(r'<script[^>]*id=["\']__NUXT_DATA__["\'][^>]*>([\s\S]*?)</script>', str(html or ""), re.I)
        if not match:
            return {}
        try:
            payload = json.loads(match.group(1))
        except Exception:
            return {}
        if isinstance(payload, list) and len(payload) > 1:
            return self._decode_nuxt_value(payload, 1)
        return payload if isinstance(payload, dict) else {}

    def _pick_image(self, node):
        if node is None:
            return ""
        for name in ("src", "data-src", "data-lazy-src", "data-original", "data-url"):
            value = node.get(name, "")
            if value and not value.startswith("data:image"):
                return self._normalize_url(value)
        return ""

    def _parse_album_anchor(self, anchor, fallback_type_id="", fallback_type_name=""):
        href = anchor.get("href", "")
        match = re.search(r"/albums/(\d+)", href)
        if not match:
            return None
        album_id = match.group(1)
        images = anchor.xpath(".//img")
        image = images[0] if images else None
        title = ""
        if image is not None:
            title = image.get("alt", "").strip()
        if not title:
            first_p = anchor.xpath(".//p")
            title = self._safe_text(first_p[0]) if first_p else self._safe_text(anchor)
        text = self._safe_text(anchor)
        periods = re.search(r"(\d+)\s*期", text)
        status = re.search(r"(连载中|已完结)", text)
        person = re.search(r"播音[：:]\s*([^\s·|]+)", text) or re.search(r"作者[：:]\s*([^\s·|]+)", text)
        remarks = " · ".join(
            [value for value in [periods.group(1) + "期" if periods else "", status.group(1) if status else "", person.group(1) if person else ""] if value]
        )
        return {
            "vod_id": album_id,
            "vod_name": title or ("专辑" + album_id),
            "vod_pic": self._pick_image(image),
            "vod_remarks": remarks,
            "type_id": str(fallback_type_id or ""),
            "type_name": fallback_type_name or "",
        }

    def _unique_by_id(self, items):
        seen = set()
        result = []
        for item in items or []:
            vod_id = str((item or {}).get("vod_id", "")).strip()
            if not vod_id or vod_id in seen:
                continue
            seen.add(vod_id)
            result.append(item)
        return result

    def _category_name(self, tid):
        for item in self.classes:
            if item["type_id"] == str(tid):
                return item["type_name"]
        return ""

    def _parse_home_list(self, html, fallback_type_id="", fallback_type_name=""):
        document = self._load_html(html)
        items = []
        for anchor in document.xpath("//a[contains(@href, '/albums/')]"):
            if not anchor.xpath(".//img"):
                continue
            item = self._parse_album_anchor(anchor, fallback_type_id, fallback_type_name)
            if item:
                items.append(item)
        return self._unique_by_id(items)

    def _parse_home_nuxt(self, html):
        root = self._load_nuxt_root(html)
        tabs = ((root.get("data") or {}).get("index-home-tabs") or {})
        items = []
        for bucket in tabs.values():
            tab_items = bucket.get("items") if isinstance(bucket, dict) else None
            if not isinstance(tab_items, list):
                continue
            for item in tab_items:
                album_id = str((item or {}).get("id") or "").strip()
                if not album_id:
                    continue
                status = "连载中" if str(item.get("status")) == "1" else "已完结" if str(item.get("status")) == "0" else ""
                remarks = " · ".join(
                    [
                        value
                        for value in [
                            f"{item.get('chapterTotal')}期" if item.get("chapterTotal") else "",
                            status,
                            str(item.get("teller") or item.get("author") or "").strip(),
                        ]
                        if value
                    ]
                )
                items.append(
                    {
                        "vod_id": album_id,
                        "vod_name": str(item.get("title") or ("专辑" + album_id)),
                        "vod_pic": self._normalize_url(item.get("cover") or item.get("cover_url") or ""),
                        "vod_remarks": remarks,
                        "type_id": "",
                        "type_name": str(item.get("categoryName") or "").strip(),
                    }
                )
        return self._unique_by_id(items)

    def _map_nuxt_album_item(self, item, tid, type_name):
        data = item or {}
        album_id = str(data.get("id") or "")
        if not album_id:
            return None
        status = "连载中" if str(data.get("status")) == "1" else "已完结" if str(data.get("status")) == "0" else ""
        remarks = " · ".join(
            [
                value
                for value in [
                    f"{data.get('count')}期" if data.get("count") else "",
                    status,
                    str(data.get("teller") or data.get("author") or "").strip(),
                ]
                if value
            ]
        )
        return {
            "vod_id": album_id,
            "vod_name": str(data.get("title") or ("专辑" + album_id)),
            "vod_pic": self._normalize_url(data.get("cover_url") or ""),
            "vod_remarks": remarks,
            "type_id": str(tid or ""),
            "type_name": type_name or "",
        }

    def _parse_category_nuxt(self, html, tid):
        root = self._load_nuxt_root(html)
        data = (root.get("data") or {}).get(f"categoryAlbums-{tid}") or {}
        items = [self._map_nuxt_album_item(item, tid, self._category_name(tid)) for item in data.get("data", [])]
        return {
            "page": int(data.get("page") or 1),
            "pages": int(data.get("pages") or 1),
            "list": [item for item in items if item],
        } if items else None

    def _parse_search_nuxt(self, html):
        root = self._load_nuxt_root(html)
        data = root.get("data") or {}
        search_value = None
        for key, value in data.items():
            if "search" in str(key).lower():
                search_value = value
                break
        results = []

        def walk(node):
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return
            if not isinstance(node, dict):
                return
            if node.get("id") and (node.get("title") or node.get("name")):
                pic = node.get("cover") or node.get("cover_url") or node.get("pic") or node.get("pic_url")
                if pic:
                    results.append(
                        {
                            "vod_id": str(node.get("id")),
                            "vod_name": str(node.get("title") or node.get("name") or ""),
                            "vod_pic": self._normalize_url(pic),
                            "vod_remarks": str(node.get("desc") or node.get("subtitle") or node.get("author") or node.get("teller") or "").strip(),
                        }
                    )
            for value in node.values():
                walk(value)

        walk(search_value)
        return self._unique_by_id(results)

    def _parse_detail_page(self, html, album_id):
        document = self._load_html(html)
        name = self._safe_text(next(iter(document.xpath("//section[contains(@class, 'album-pannel')]//*[contains(@class, 'album-intro')]//h1")), None))
        if not name:
            name = document.xpath("string(//meta[@property='og:title']/@content)").strip()
        pic = ""
        images = document.xpath("//section[contains(@class, 'album-pannel')]//img")
        if images:
            pic = self._pick_image(images[0])
        if not pic:
            pic = self._normalize_url(document.xpath("string(//meta[@property='og:image']/@content)").strip())
        content = (
            document.xpath("string(//meta[@name='description']/@content)").strip()
            or document.xpath("string(//meta[@property='og:description']/@content)").strip()
            or self._safe_text(next(iter(document.xpath("//*[contains(@class, 'album-desc') or contains(@class, 'desc') or contains(@class, 'intro')]")), None))
        )
        type_name = ""
        for node in document.xpath("//section[contains(@class, 'album-pannel')]//*[contains(@class, 'pods')]//span"):
            text = self._safe_text(node)
            if text.startswith("分类:"):
                type_name = text.split(":", 1)[1].strip()
                break
        root = self._load_nuxt_root(html)
        nuxt_data = root.get("data") or {}
        album_detail = nuxt_data.get(f"album-detail-{album_id}") or {}
        album_chapters = nuxt_data.get(f"album-chapters-{album_id}") or {}
        if not name:
            name = str(album_detail.get("title") or "").strip()
        if not pic:
            pic = self._normalize_url(album_detail.get("cover_url") or "")
        if not content:
            content = str(album_detail.get("synopsis") or "").strip()
        play_items = []
        chapters = album_chapters.get("chapters") or []
        if isinstance(chapters, list) and chapters:
            for index, item in enumerate(chapters, start=1):
                raw_index = item.get("index")
                chapter_idx = int(raw_index) if isinstance(raw_index, (int, str)) and str(raw_index).isdigit() else index
                title = str(item.get("title") or f"第{chapter_idx}集").strip()
                play_items.append(f"{title}${album_id}|{chapter_idx}")
        else:
            for index, item in enumerate(document.xpath("//ul[contains(@class, 'chapter-list')]/li[contains(@class, 'chapter-item')]"), start=1):
                num_text = self._safe_text(next(iter(item.xpath("./p")), None))
                title = self._safe_text(next(iter(item.xpath(".//*[contains(@class, 'title')]")), None)) or f"第{index}集"
                chapter_idx = int(num_text) if str(num_text).isdigit() else index
                play_items.append(f"{title}${album_id}|{chapter_idx}")
        return {
            "vod_id": str(album_id),
            "vod_name": name or ("专辑" + str(album_id)),
            "vod_pic": pic,
            "vod_content": content,
            "type_name": type_name,
            "vod_play_from": "听友FM",
            "vod_play_url": "#".join(play_items),
        }

    def _normalize_api_result(self, data):
        value = data
        if isinstance(value, dict) and isinstance(value.get("payload"), str):
            plain = self._decrypt_payload(value["payload"])
            try:
                return json.loads(plain)
            except Exception:
                return plain
        if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]+", value or ""):
            plain = self._decrypt_payload(value)
            try:
                return json.loads(plain)
            except Exception:
                return plain
        return value

    def _api_post(self, path, body=None, extra_headers=None):
        url = path if str(path).startswith("http") else self.host + (path if str(path).startswith("/") else "/" + str(path))
        payload = None
        if body is not None:
            payload = self._encrypt_payload(json.dumps(body, ensure_ascii=False, separators=(",", ":")))
        headers = self._get_headers({"X-Payload-Version": str(self.payload_version)})
        if payload is not None:
            headers["Content-Type"] = "text/plain"
        if extra_headers:
            headers.update(extra_headers)
        response = self.post(url, data=payload, headers=headers, timeout=10, verify=False)
        if getattr(response, "status_code", 0) >= 400:
            raise ValueError("api request failed")
        text = getattr(response, "text", "") or ""
        try:
            data = json.loads(text)
        except Exception:
            data = text
        return self._normalize_api_result(data)

    def _extract_play_url(self, value):
        candidates = []

        def walk(node):
            if isinstance(node, str):
                if node.startswith("http://") or node.startswith("https://"):
                    candidates.append(node)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return
            if not isinstance(node, dict):
                return
            for key, item in node.items():
                if isinstance(item, str) and (key.lower() in ("url", "src", "play", "audio", "file", "link") or item.startswith("http")):
                    candidates.append(item)
                walk(item)

        walk(value)
        for candidate in candidates:
            if candidate.startswith("http://") or candidate.startswith("https://"):
                return candidate
        return ""

    def _anonymous_auth(self):
        cookie = self._make_dfp_cookie()
        data = self._api_post("/api/me", None, extra_headers={"Accept": "application/json", "Cookie": cookie})
        auth_token = str((data or {}).get("auth_token") or "").strip()
        return {
            "auth_token": auth_token,
            "cookie": cookie,
            "data": data or {},
        }

    def homeContent(self, filter):
        html = self._get_html("/")
        document = self._load_html(html)
        classes = []
        seen = set()
        for anchor in document.xpath("//a[contains(@href, '/categories/')]"):
            href = anchor.get("href", "")
            match = re.search(r"/categories/(\d+)", href)
            if not match:
                continue
            type_id = match.group(1)
            if type_id in seen:
                continue
            seen.add(type_id)
            classes.append({"type_id": type_id, "type_name": self._safe_text(anchor) or self._category_name(type_id)})
        items = self._parse_home_nuxt(html) or self._parse_home_list(html)
        return {"class": classes or list(self.classes), "list": items[:20]}

    def homeVideoContent(self):
        return {"list": self.homeContent(False).get("list", [])}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg or 1)
        html = self._get_html(f"/categories/{tid}?sort=comprehensive&page={page}")
        nuxt = self._parse_category_nuxt(html, tid)
        items = (nuxt or {}).get("list") or self._parse_home_list(html, tid, self._category_name(tid))
        return {"page": (nuxt or {}).get("page", page), "limit": len(items), "total": len(items), "list": items}

    def detailContent(self, ids):
        result = {"list": []}
        for album_id in ids or []:
            html = self._get_html(f"/albums/{album_id}")
            vod = self._parse_detail_page(html, str(album_id))
            if vod:
                result["list"].append(vod)
        return result

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        if not keyword:
            return {"page": 1, "limit": 0, "total": 0, "list": []}
        html = self._get_html(f"/search?q={quote(keyword)}")
        items = self._parse_search_nuxt(html)
        if not items:
            items = self._parse_home_list(html)
        lowered = keyword.lower()
        filtered = [
            item for item in self._unique_by_id(items)
            if lowered in f"{item.get('vod_name', '')} {item.get('vod_remarks', '')}".lower()
        ]
        return {"page": int(pg or 1), "limit": len(filtered), "total": len(filtered), "list": filtered}

    def playerContent(self, flag, id, vipFlags):
        album_id, chapter_idx = str(id or "").split("|", 1)
        fallback = f"{self.host}/audios/{album_id}/{chapter_idx}"
        try:
            auth = self._anonymous_auth()
            extra_headers = {
                "Accept": "application/json",
                "Cookie": auth.get("cookie", ""),
            }
            if auth.get("auth_token"):
                extra_headers["Authorization"] = f"Bearer {auth['auth_token']}"
            payload = self._api_post(
                "/api/play_token",
                {"album_id": int(album_id), "chapter_idx": int(chapter_idx)},
                extra_headers=extra_headers,
            )
            data = self._normalize_api_result(payload)
            url = self._extract_play_url(data)
            if url:
                return {"parse": 0, "url": url, "header": self._get_headers(extra_headers)}
        except Exception:
            pass
        return {"parse": 1, "url": fallback, "header": self._get_headers()}
