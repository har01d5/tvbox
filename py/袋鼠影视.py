# coding=utf-8
import re
import subprocess
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "袋鼠影视"
        self.host = "https://daishuys.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
        ]
        self.filters = {
            "1": [
                {
                    "key": "tid",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": "1"},
                        {"n": "动作片", "v": "5"},
                        {"n": "喜剧片", "v": "10"},
                        {"n": "爱情片", "v": "6"},
                        {"n": "科幻片", "v": "7"},
                        {"n": "恐怖片", "v": "8"},
                        {"n": "战争片", "v": "9"},
                        {"n": "剧情片", "v": "12"},
                        {"n": "动画片", "v": "41"},
                        {"n": "纪录片", "v": "11"},
                    ],
                },
                {
                    "key": "area",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "香港", "v": "香港"},
                        {"n": "台湾", "v": "台湾"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "美国", "v": "美国"},
                        {"n": "英国", "v": "英国"},
                        {"n": "印度", "v": "印度"},
                        {"n": "法国", "v": "法国"},
                        {"n": "泰国", "v": "泰国"},
                    ],
                },
                {
                    "key": "year",
                    "name": "年份",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "2026", "v": "2026"},
                        {"n": "2025", "v": "2025"},
                        {"n": "2024", "v": "2024"},
                        {"n": "2023", "v": "2023"},
                        {"n": "2022", "v": "2022"},
                        {"n": "2021", "v": "2021"},
                        {"n": "2020", "v": "2020"},
                    ],
                },
            ],
            "2": [
                {
                    "key": "tid",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": "2"},
                        {"n": "国产剧", "v": "13"},
                        {"n": "港台剧", "v": "14"},
                        {"n": "欧美剧", "v": "15"},
                        {"n": "日韩剧", "v": "16"},
                    ],
                },
                {
                    "key": "area",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "香港", "v": "香港"},
                        {"n": "台湾", "v": "台湾"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "美国", "v": "美国"},
                        {"n": "英国", "v": "英国"},
                    ],
                },
                {
                    "key": "year",
                    "name": "年份",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "2026", "v": "2026"},
                        {"n": "2025", "v": "2025"},
                        {"n": "2024", "v": "2024"},
                        {"n": "2023", "v": "2023"},
                        {"n": "2022", "v": "2022"},
                    ],
                },
            ],
            "3": [
                {
                    "key": "area",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "美国", "v": "美国"},
                    ],
                },
                {
                    "key": "year",
                    "name": "年份",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "2026", "v": "2026"},
                        {"n": "2025", "v": "2025"},
                        {"n": "2024", "v": "2024"},
                    ],
                },
            ],
            "4": [
                {
                    "key": "area",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "美国", "v": "美国"},
                    ],
                },
                {
                    "key": "year",
                    "name": "年份",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "2026", "v": "2026"},
                        {"n": "2025", "v": "2025"},
                        {"n": "2024", "v": "2024"},
                    ],
                },
            ],
        }
        self.filter_defaults = {
            "1": {"tid": "1", "area": "", "year": ""},
            "2": {"tid": "2", "area": "", "year": ""},
            "3": {"tid": "3", "area": "", "year": ""},
            "4": {"tid": "4", "area": "", "year": ""},
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeContent(self, filter):
        result = {"class": self.classes}
        if filter:
            result["filters"] = self.filters
        return result

    def homeVideoContent(self):
        html = self._request_html(self.host + "/")
        root = self.html(html)
        if root is None:
            return {"list": []}
        items = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'swiper-container') and contains(@class,'hy-slide')]//a[contains(@class,'videopic')][@href]"):
            card = self._parse_card(root, node)
            if card and card["vod_id"] not in seen:
                seen.add(card["vod_id"])
                items.append(card)
        for node in root.xpath("//*[contains(@class,'hy-video-list')]//*[contains(@class,'item')]//a[contains(@class,'videopic')][@href]"):
            card = self._parse_card(root, node)
            if card and card["vod_id"] not in seen:
                seen.add(card["vod_id"])
                items.append(card)
        return {"list": items}

    def _build_url(self, path):
        raw = str(path or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return urljoin(self.host + "/", raw)

    def _encode_vod_id(self, href):
        matched = re.search(r"/movie/([^/?#]+)\.html", self._build_url(href))
        return f"movie/{matched.group(1)}" if matched else ""

    def _decode_vod_id(self, vod_id):
        matched = re.search(r"^movie/([^/?#]+)$", str(vod_id or "").strip())
        return self._build_url(f"/movie/{matched.group(1)}.html") if matched else ""

    def _encode_play_id(self, href):
        matched = re.search(r"/play/([^/?#]+)\.html", self._build_url(href))
        return f"play/{matched.group(1)}" if matched else ""

    def _decode_play_id(self, play_id):
        matched = re.search(r"^play/([^/?#]+)$", str(play_id or "").strip())
        return self._build_url(f"/play/{matched.group(1)}.html") if matched else ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=dict(self.headers), timeout=15, verify=False)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _normalize_media_url(self, value):
        raw = str(value or "").strip().strip("'\"")
        if not raw:
            return ""
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("/"):
            return self._build_url(raw)
        return ""

    def _first_text(self, node, expr):
        for value in node.xpath(expr):
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def _parse_card(self, root, anchor):
        href = self._first_text(anchor, "./@href")
        vod_id = self._encode_vod_id(href)
        if not vod_id:
            return None
        title = (
            self._first_text(anchor, "./@title")
            or self._first_text(anchor, ".//img[1]/@alt")
        )
        pic = (
            self._first_text(anchor, "./@data-original")
            or self._first_text(anchor, ".//img[1]/@data-original")
            or self._first_text(anchor, ".//img[1]/@src")
        )
        remarks = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'note')][1]//text()")))
        return {
            "vod_id": vod_id,
            "vod_name": self._clean_text(title),
            "vod_pic": self._build_url(pic),
            "vod_remarks": remarks,
        }

    def _parse_page_count(self, root):
        max_page = 1
        for node in root.xpath("//*[contains(@class,'hy-page')]//a[@href]"):
            href = self._first_text(node, "./@href")
            match = re.search(r"[?&]page=(\d+)", href)
            if match:
                max_page = max(max_page, int(match.group(1)))
        return max_page

    def _parse_category_cards(self, html):
        root = self.html(html)
        if root is None:
            return [], 1
        items = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'hy-video-list')]//*[contains(@class,'item')]//a[contains(@class,'videopic')][@href]"):
            card = self._parse_card(root, node)
            if card and card["vod_id"] not in seen and card["vod_name"]:
                seen.add(card["vod_id"])
                items.append(card)
        for node in root.xpath("//*[contains(@class,'hy-video-details')]//*[contains(@class,'item')]//dl[contains(@class,'content')]"):
            anchor = node.xpath(".//dt//a[contains(@class,'videopic')][@href]")
            if not anchor:
                continue
            anchor = anchor[0]
            href = self._first_text(anchor, "./@href")
            vod_id = self._encode_vod_id(href)
            if not vod_id or vod_id in seen:
                continue
            title = self._clean_text(
                self._first_text(node, ".//dd//*[contains(@class,'head')]//a[1]//text()")
                or self._first_text(node, ".//dd//*[contains(@class,'head')]//h3[1]//text()")
                or self._first_text(node, ".//dd//*[contains(@class,'head')]//h5[1]//text()")
            )
            pic = (
                self._first_text(anchor, "./@data-original")
                or self._first_text(anchor, ".//img[1]/@src")
                or ""
            )
            style_match = re.search(r"url\(([^)]+)\)", self._first_text(anchor, "./@style"))
            if not pic and style_match:
                pic = style_match.group(1).strip("'\"")
            remarks = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'note')][1]//text()")))
            card = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": self._build_url(pic),
                "vod_remarks": remarks,
            }
            for li in node.xpath(".//li"):
                li_text = self._clean_text("".join(li.xpath(".//text()")))
                if li_text.startswith("主演："):
                    card["vod_actor"] = li_text[3:]
                elif li_text.startswith("导演："):
                    card["vod_director"] = li_text[3:]
                elif li_text.startswith("地区："):
                    card["vod_area"] = li_text[3:]
                elif li_text.startswith("年份："):
                    card["vod_year"] = li_text[3:]
            if card["vod_id"] not in seen and card["vod_name"]:
                seen.add(card["vod_id"])
                items.append(card)
        pagecount = self._parse_page_count(root)
        return items, pagecount

    def _build_category_url(self, tid, pg, extend):
        defaults = self.filter_defaults.get(str(tid), {"tid": str(tid)})
        merged = {**defaults, **(extend or {})}
        tid_val = str(merged.get("tid", tid))
        params = f"searchtype=5&tid={tid_val}&page={int(pg)}"
        area = str(merged.get("area", ""))
        if area:
            params += f"&area={quote(area)}"
        year = str(merged.get("year", ""))
        if year:
            params += f"&year={quote(year)}"
        return f"{self.host}/search.php?{params}"

    def categoryContent(self, tid, pg, filter, extend):
        url = self._build_category_url(tid, pg, extend)
        html = self._request_html(url)
        items, pagecount = self._parse_category_cards(html)
        page = int(pg)
        return {
            "page": page,
            "pagecount": pagecount,
            "limit": len(items) or 20,
            "total": pagecount * (len(items) or 20),
            "list": items,
        }

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "pagecount": 0, "total": 0, "list": []}
        search_headers = dict(self.headers)
        search_headers["Content-Type"] = "application/x-www-form-urlencoded"
        search_headers["Referer"] = f"{self.host}/search.php"
        response = self.post(
            f"{self.host}/search.php?page={page}",
            data=f"searchword={quote(keyword)}",
            headers=search_headers,
            timeout=15,
            verify=False,
        )
        if response.status_code != 200:
            return {"page": page, "pagecount": 0, "total": 0, "list": []}
        html = response.text or ""
        items, pagecount = self._parse_category_cards(html)
        total_match = re.search(r"相关的.?“(\d+)”.?条结果", html)
        total = int(total_match.group(1)) if total_match else len(items)
        return {
            "page": page,
            "pagecount": pagecount or page,
            "total": total,
            "list": items,
        }

    def _parse_detail(self, html, vod_id):
        root = self.html(html)
        if root is None:
            return {"vod_id": vod_id, "vod_name": "", "vod_pic": "", "vod_play_from": "", "vod_play_url": ""}
        title = self._clean_text("".join(root.xpath("//h1[contains(@class,'h4')][1]//text() | //h1[1]//text()")))
        pic = ""
        detail_anchor = root.xpath("//*[contains(@class,'hy-video-details')]//*[contains(@class,'content')]//dt//a[contains(@class,'videopic')][1]")
        if detail_anchor:
            pic = (
                self._first_text(detail_anchor[0], ".//img[1]/@src")
                or self._first_text(detail_anchor[0], "./@data-original")
            )
            remarks = self._clean_text("".join(detail_anchor[0].xpath(".//*[contains(@class,'note')][1]//text()")))
        else:
            remarks = ""
        info = {}
        for li in root.xpath("//*[contains(@class,'hy-video-details')]//li"):
            li_text = self._clean_text("".join(li.xpath(".//text()")))
            if li_text.startswith("主演："):
                info["vod_actor"] = li_text[3:]
            elif li_text.startswith("导演："):
                info["vod_director"] = li_text[3:]
            elif li_text.startswith("年份："):
                info["vod_year"] = li_text[3:]
            elif li_text.startswith("地区："):
                info["vod_area"] = li_text[3:]
            elif li_text.startswith("类型："):
                info["type_name"] = li_text[3:]
            elif li_text.startswith("语言："):
                info["vod_lang"] = li_text[3:]
            elif li_text.startswith("又名："):
                info["other"] = li_text[3:]
            elif li_text.startswith("豆瓣："):
                info["vod_douban_score"] = li_text[3:]
        content = self._clean_text(
            "".join(root.xpath("//*[@id='list3']//*[contains(@class,'plot')][1]//text()"))
            or "".join(root.xpath("//*[contains(@class,'plot')][1]//text()"))
        )
        play_from = []
        play_urls = []
        for index, panel in enumerate(root.xpath("//*[@id='playlist']//*[contains(@class,'panel')]")):
            source_name = (
                self._clean_text(self._first_text(panel, ".//a[contains(@class,'option')][1]/@title"))
                or self._clean_text(
                    "".join(
                        panel.xpath(
                            ".//a[contains(@class,'option')][1]//text()"
                            " | .//a[contains(@class,'option')][1]/text()"
                        )
                    )
                )
                or f"线路{index + 1}"
            )
            episodes = []
            for anchor in panel.xpath(".//*[contains(@class,'playlist')]//a[@href]"):
                href = self._first_text(anchor, "./@href")
                ep_name = self._clean_text(self._first_text(anchor, "./@title") or "".join(anchor.xpath(".//text()")))
                if not href or not ep_name:
                    continue
                play_id = self._encode_play_id(href)
                if not play_id:
                    continue
                episodes.append(f"{ep_name}${play_id}")
            if episodes:
                play_from.append(source_name)
                play_urls.append("#".join(episodes))
        return {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_remarks": remarks,
            "vod_content": content,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_urls),
            **info,
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            if not vod_id:
                continue
            url = self._decode_vod_id(vod_id)
            if not url:
                url = vod_id if vod_id.startswith(("http://", "https://")) else self._build_url(vod_id)
            html = self._request_html(url)
            detail = self._parse_detail(html, vod_id)
            result["list"].append(detail)
        return result

    def _curl_request(self, url, headers=None):
        command = ["curl", "-L", "--silent", "--show-error", url]
        for key, value in (headers or {}).items():
            command.extend(["-H", f"{key}: {value}"])
        completed = subprocess.run(command, capture_output=True, text=True, check=True, timeout=20)
        return {"body": completed.stdout or "", "status_code": 200}

    def _extract_play_url(self, html):
        patterns = [
            r'var\s+now\s*=\s*"([^"]+)"',
            r"var\s+now\s*=\s*'([^']+)'",
            r'var\s+now\s*=\s*((?:https?:)?//[^\s;"\']+)',
        ]
        for p in patterns:
            match = re.search(p, html)
            if match:
                url = self._normalize_media_url(match.group(1))
                if url:
                    return url
        match = re.search(r'((?:https?:)?//[^\s"\'<>\)]+\.m3u8[^\s"\'<>\)]*)', html)
        if match:
            return self._normalize_media_url(match.group(1))
        return ""

    def playerContent(self, flag, id, vipFlags):
        play_url = str(id or "").strip()
        if not play_url:
            return {"parse": 1, "jx": 1, "playUrl": "", "url": "", "header": {}}
        url = self._decode_play_id(play_url)
        if not url:
            url = self._build_url(play_url)
        headers = dict(self.headers)
        headers["Referer"] = url
        try:
            response = self.fetch(url, headers=headers, timeout=15, verify=False)
            html = response.text if response.status_code == 200 else ""
        except Exception:
            try:
                html = self._curl_request(url, headers=headers).get("body", "")
            except Exception:
                html = ""
        direct_url = self._extract_play_url(html)
        if direct_url:
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": direct_url,
                "header": {
                    "User-Agent": self.headers["User-Agent"],
                    "Referer": url,
                },
            }
        return {
            "parse": 1,
            "jx": 1,
            "playUrl": "",
            "url": url,
            "header": {
                "User-Agent": self.headers["User-Agent"],
                "Referer": url,
            },
        }
