# coding=utf-8
import json
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "在线之家"
        self.host = "https://www.zxzjhd.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "美剧"},
            {"type_id": "3", "type_name": "韩剧"},
            {"type_id": "4", "type_name": "日剧"},
            {"type_id": "5", "type_name": "泰剧"},
            {"type_id": "6", "type_name": "动漫"},
        ]
        sort_values = [
            {"n": "时间", "v": "time"},
            {"n": "人气", "v": "hits"},
            {"n": "评分", "v": "score"},
        ]
        common_years = [
            {"n": "全部", "v": ""},
            {"n": "2026", "v": "2026"},
            {"n": "2025", "v": "2025"},
            {"n": "2024", "v": "2024"},
            {"n": "2023", "v": "2023"},
            {"n": "2022", "v": "2022"},
            {"n": "2021", "v": "2021"},
            {"n": "2020", "v": "2020"},
            {"n": "2019", "v": "2019"},
            {"n": "2018", "v": "2018"},
            {"n": "2017", "v": "2017"},
            {"n": "2016", "v": "2016"},
            {"n": "2015", "v": "2015"},
            {"n": "2014", "v": "2014"},
            {"n": "2013", "v": "2013"},
            {"n": "2012", "v": "2012"},
            {"n": "2011", "v": "2011"},
        ]
        drama_classes = [
            {"n": "全部", "v": ""},
            {"n": "剧情", "v": "剧情"},
            {"n": "喜剧", "v": "喜剧"},
            {"n": "爱情", "v": "爱情"},
            {"n": "动作", "v": "动作"},
            {"n": "悬疑", "v": "悬疑"},
            {"n": "恐怖", "v": "恐怖"},
            {"n": "奇幻", "v": "奇幻"},
            {"n": "惊悚", "v": "惊悚"},
            {"n": "犯罪", "v": "犯罪"},
            {"n": "科幻", "v": "科幻"},
            {"n": "音乐", "v": "音乐"},
            {"n": "其他", "v": "其他"},
        ]
        self.filter_def = {key: {"cateId": key} for key in ["1", "2", "3", "4", "5", "6"]}
        self.filters = {
            "1": [
                {
                    "key": "class",
                    "name": "剧情",
                    "init": "",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "喜剧", "v": "喜剧"},
                        {"n": "爱情", "v": "爱情"},
                        {"n": "恐怖", "v": "恐怖"},
                        {"n": "动作", "v": "动作"},
                        {"n": "科幻", "v": "科幻"},
                        {"n": "剧情", "v": "剧情"},
                        {"n": "战争", "v": "战争"},
                        {"n": "警匪", "v": "警匪"},
                        {"n": "犯罪", "v": "犯罪"},
                        {"n": "动画", "v": "动画"},
                        {"n": "奇幻", "v": "奇幻"},
                        {"n": "冒险", "v": "冒险"},
                    ],
                },
                {
                    "key": "area",
                    "name": "地区",
                    "init": "",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "香港", "v": "香港"},
                        {"n": "台湾", "v": "台湾"},
                        {"n": "欧美", "v": "欧美"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "日本", "v": "日本"},
                        {"n": "泰国", "v": "泰国"},
                        {"n": "印度", "v": "印度"},
                        {"n": "俄罗斯", "v": "俄罗斯"},
                        {"n": "其他", "v": "其他"},
                    ],
                },
                {"key": "year", "name": "年份", "init": "", "value": list(common_years)},
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
            "2": [
                {"key": "class", "name": "剧情", "init": "", "value": list(drama_classes)},
                {"key": "year", "name": "年份", "init": "", "value": list(common_years)},
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
            "3": [
                {"key": "class", "name": "剧情", "init": "", "value": list(drama_classes)},
                {"key": "year", "name": "年份", "init": "", "value": list(common_years)},
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
            "4": [
                {"key": "class", "name": "剧情", "init": "", "value": list(drama_classes)},
                {"key": "year", "name": "年份", "init": "", "value": list(common_years)},
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
            "5": [
                {"key": "year", "name": "年份", "init": "", "value": list(common_years)},
                {"key": "by", "name": "排序", "init": "time", "value": list(sort_values)},
            ],
            "6": [
                {
                    "key": "class",
                    "name": "剧情",
                    "init": "",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "情感", "v": "情感"},
                        {"n": "科幻", "v": "科幻"},
                        {"n": "热血", "v": "热血"},
                        {"n": "推理", "v": "推理"},
                        {"n": "搞笑", "v": "搞笑"},
                        {"n": "冒险", "v": "冒险"},
                        {"n": "萝莉", "v": "萝莉"},
                        {"n": "校园", "v": "校园"},
                        {"n": "动作", "v": "动作"},
                        {"n": "机战", "v": "机战"},
                        {"n": "运动", "v": "运动"},
                        {"n": "战争", "v": "战争"},
                        {"n": "少年", "v": "少年"},
                    ],
                },
                {
                    "key": "area",
                    "name": "地区",
                    "init": "",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "国产", "v": "国产"},
                        {"n": "日本", "v": "日本"},
                        {"n": "欧美", "v": "欧美"},
                        {"n": "其他", "v": "其他"},
                    ],
                },
                {"key": "year", "name": "年份", "init": "", "value": list(common_years)},
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

    def homeVideoContent(self):
        return {"list": []}

    def _normalize_ext(self, extend):
        if isinstance(extend, dict):
            return extend
        if not extend:
            return {}
        try:
            return json.loads(str(extend))
        except Exception:
            return {}

    def _build_url(self, value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _build_category_url(self, tid, pg, extend):
        values = dict(self.filter_def.get(str(tid), {"cateId": str(tid)}))
        values.update(self._normalize_ext(extend))
        path = (
            f"{values.get('cateId', tid)}-"
            f"{values.get('area', '')}-"
            f"{values.get('by', '')}-"
            f"{values.get('class', '')}"
            f"-----{int(pg)}---"
            f"{values.get('year', '')}"
        )
        return self._build_url(f"/vodshow/{path}.html")

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _fix_json_wrapped_html(self, html):
        value = str(html or "").strip()
        if value.startswith("<"):
            return value
        if value.startswith('"') and value.endswith('"'):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, str) and parsed.startswith("<"):
                    return parsed.strip()
            except Exception:
                return value
        return value

    def _request_html(self, path_or_url, referer=None, extra_headers=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.headers["Referer"]
        if isinstance(extra_headers, dict):
            headers.update(extra_headers)
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return self._fix_json_wrapped_html(response.text or "")

    def _build_player_v2_headers(self):
        return {
            "Origin": self.host,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

    def _extract_vod_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/?(voddetail/\d+\.html)", raw)
        return matched.group(1) if matched else ""

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for node in root.xpath("//ul[contains(@class,'stui-vodlist')]//li"):
            href = ((node.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            vod_id = self._extract_vod_id(href)
            title = ((node.xpath(".//a[@title][1]/@title") or [""])[0]).strip()
            pic = (
                ((node.xpath(".//a[@data-original][1]/@data-original") or [""])[0]).strip()
                or ((node.xpath(".//img[@data-original][1]/@data-original") or [""])[0]).strip()
                or ((node.xpath(".//img[@src][1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(node.xpath(".//*[contains(@class,'pic-text')][1]//text()")))
            if not vod_id or not title or vod_id in seen:
                continue
            seen.add(vod_id)
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_cards(self._request_html(self._build_category_url(tid, pg, extend)))
        return {"list": items, "page": page, "limit": 24, "total": page * 30 + len(items)}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        url = self._build_url("/vodsearch/{0}-------------.html".format(quote(str(key or "").strip())))
        items = self._parse_cards(self._request_html(url))
        return {"list": items, "page": page, "limit": len(items), "total": len(items)}

    def _extract_actor_like_field(self, html, label):
        matched = re.search(rf"{label}：</span>([\s\S]*?)</p>", str(html or ""))
        if not matched:
            return ""
        texts = re.findall(r">([^<>]+)<", matched.group(1))
        clean = [self._clean_text(text) for text in texts if self._clean_text(text)]
        return ",".join(clean)

    def _parse_detail_meta(self, html):
        root = self.html(html)
        if root is None:
            return {}
        title_line = self._clean_text(
            "".join(root.xpath("//*[contains(@class,'stui-content__detail')]//*[contains(@class,'title')][1]//text()"))
        )
        title_match = re.match(r"^(.*?)(?:\s+(19\d{2}|20\d{2}))?(?:\s+([^\s]+))?(?:\s+([^\s]+))?$", title_line)
        vod_name = self._clean_text(title_match.group(1) if title_match else title_line)
        vod_year = self._clean_text(title_match.group(2) if title_match else "")
        vod_area = self._clean_text(title_match.group(3) if title_match else "")
        vod_class = self._clean_text(title_match.group(4) if title_match else "")
        return {
            "vod_name": vod_name,
            "vod_year": vod_year,
            "vod_area": vod_area,
            "vod_class": vod_class,
            "vod_pic": self._build_url(
                ((root.xpath("//*[contains(@class,'stui-content__thumb')]//img/@data-original") or [""])[0]).strip()
            ),
            "vod_content": self._clean_text(
                "".join(
                    root.xpath(
                        "//*[contains(concat(' ', normalize-space(@class), ' '), ' detail ')][1]//text()"
                    )
                )
            ),
            "vod_director": self._extract_actor_like_field(html, "导演"),
            "vod_actor": self._extract_actor_like_field(html, "主演"),
        }

    def _extract_playlists(self, html):
        root = self.html(html)
        if root is None:
            return {"normal": [], "pan": []}
        tabs = [self._clean_text("".join(node.xpath(".//text()"))) for node in root.xpath("//*[contains(@class,'stui-vodlist__head')]//h3")]
        playlists = root.xpath("//*[contains(@class,'stui-content__playlist')]")
        normal = []
        pan = []
        for index, playlist in enumerate(playlists):
            tab_name = tabs[index] if index < len(tabs) else ""
            items = []
            for anchor in playlist.xpath(".//a[@href]"):
                href = ((anchor.xpath("./@href") or [""])[0]).strip()
                name = self._clean_text("".join(anchor.xpath(".//text()"))) or "正片"
                play_id = re.sub(r"^/+", "", href)
                if not play_id:
                    continue
                items.append(
                    {
                        "name": name,
                        "url": self._build_url(play_id),
                        "play_id": play_id,
                        "tab_name": tab_name,
                    }
                )
            if any(keyword in tab_name for keyword in ["网盘", "百度", "夸克", "UC", "阿里", "迅雷"]):
                pan.extend(items)
            elif items:
                normal.extend([f"{item['name']}${item['play_id']}" for item in items])
        return {"normal": normal, "pan": pan}

    def _extract_pan_url_from_play_page(self, html):
        matched = re.search(r"player_[a-z0-9_]+\s*=\s*(\{[\s\S]*?\})\s*;?", str(html or ""), re.I)
        if not matched:
            return ""
        try:
            payload = json.loads(matched.group(1))
        except Exception:
            return ""
        return str(payload.get("url") or "").strip()

    def _detect_pan_type(self, tab_name, share_url):
        text = str(share_url or "")
        if "pan.baidu.com" in text:
            return "baidu"
        if "pan.quark.cn" in text:
            return "quark"
        if "drive.uc.cn" in text:
            return "uc"
        if "alipan.com" in text or "aliyundrive.com" in text:
            return "aliyun"
        if "pan.xunlei.com" in text:
            return "xunlei"
        name = str(tab_name or "").lower()
        if "百度" in str(tab_name or ""):
            return "baidu"
        if "夸克" in str(tab_name or ""):
            return "quark"
        if "uc" in name:
            return "uc"
        if "阿里" in str(tab_name or "") or "aliyun" in name:
            return "aliyun"
        if "迅雷" in str(tab_name or ""):
            return "xunlei"
        return ""

    def _extract_pan_groups(self, items):
        grouped = {}
        seen = set()
        order = ["quark", "baidu", "uc", "aliyun", "xunlei"]
        for item in items:
            play_html = self._request_html(item["url"], referer=self.headers["Referer"])
            share_url = self._extract_pan_url_from_play_page(play_html)
            pan_type = self._detect_pan_type(item.get("tab_name", ""), share_url)
            if not share_url or not pan_type:
                continue
            key = (pan_type, share_url)
            if key in seen:
                continue
            seen.add(key)
            grouped.setdefault(pan_type, []).append(f"{item['name']}${share_url}")
        return [{"from": key, "urls": "#".join(grouped[key])} for key in order if grouped.get(key)]

    def detailContent(self, ids):
        raw_id = str(ids[0]).strip()
        url = raw_id if raw_id.startswith("http") else self._build_url("/" + raw_id.lstrip("/"))
        html = self._request_html(url)
        meta = self._parse_detail_meta(html)
        playlists = self._extract_playlists(html)
        pan_groups = self._extract_pan_groups(playlists["pan"])
        play_from = []
        play_url = []
        if playlists["normal"]:
            play_from.append("zxzj")
            play_url.append("#".join(playlists["normal"]))
        for group in pan_groups:
            play_from.append(group["from"])
            play_url.append(group["urls"])
        vod = {
            "vod_id": raw_id,
            "vod_name": meta.get("vod_name", ""),
            "vod_pic": meta.get("vod_pic", ""),
            "vod_content": meta.get("vod_content", ""),
            "vod_remarks": "",
            "vod_year": meta.get("vod_year", ""),
            "vod_area": meta.get("vod_area", ""),
            "vod_class": meta.get("vod_class", ""),
            "vod_lang": "",
            "vod_director": meta.get("vod_director", ""),
            "vod_actor": meta.get("vod_actor", ""),
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }
        return {"list": [vod]}

    def _decrypt_url(self, encrypted_data):
        raw = str(encrypted_data or "").strip()
        if not raw or len(raw) % 2 != 0:
            return ""
        try:
            reversed_hex = raw[::-1]
            decoded = []
            for index in range(0, len(reversed_hex), 2):
                decoded.append(chr(int(reversed_hex[index : index + 2], 16)))
            text = "".join(decoded)
            split_len = max((len(text) - 7) // 2, 0)
            candidate = text[:split_len] + text[split_len + 7 :]
            return candidate if candidate.startswith("http") else ""
        except Exception:
            return ""

    def _extract_iframe_url(self, html):
        matched = re.search(r'"url"\s*:\s*"(https:[^"]*?)"', str(html or ""))
        if matched:
            value = matched.group(1).replace("\\/", "/")
            if any(token in value for token in ["jx.zxzj", "player-v2", "/player", "/embed"]):
                return value
        matched = re.search(r"player_[a-z0-9_]+\s*=\s*(\{[\s\S]*?\})\s*;?", str(html or ""), re.I)
        if not matched:
            return ""
        try:
            payload = json.loads(matched.group(1))
        except Exception:
            return ""
        value = str(payload.get("url") or "").replace("\\/", "/")
        return value if any(token in value for token in ["jx.zxzj", "player-v2", "/player", "/embed"]) else ""

    def _extract_result_v2_data(self, html):
        matched = re.search(r"result_v2\s*=\s*(\{[\s\S]*?\})\s*;", str(html or ""))
        if not matched:
            return ""
        try:
            payload = json.loads(matched.group(1))
        except Exception:
            return ""
        return str(payload.get("data") or payload.get("url") or "").strip()

    def playerContent(self, flag, id, vipFlags):
        raw_flag = str(flag or "").lower()
        raw_id = str(id or "").strip()
        if raw_flag in ("baidu", "quark", "uc", "aliyun", "xunlei"):
            return {"parse": 0, "jx": 0, "playUrl": "", "url": raw_id, "header": {}}

        play_url = raw_id if raw_id.startswith("http") else self._build_url("/" + raw_id.lstrip("/"))
        play_html = self._request_html(play_url, referer=self.headers["Referer"])
        iframe_url = self._extract_iframe_url(play_html)
        if not iframe_url:
            return {"parse": 1, "jx": 1, "playUrl": "", "url": play_url, "header": self.headers}

        iframe_headers = self._build_player_v2_headers() if "player-v2" in iframe_url else None
        iframe_html = self._request_html(iframe_url, referer=play_url, extra_headers=iframe_headers)
        encrypted = self._extract_result_v2_data(iframe_html)
        final_url = self._decrypt_url(encrypted)
        if not final_url:
            fallback_url = iframe_url if "player-v2" in iframe_url else play_url
            fallback_header = (
                {"Referer": play_url, "User-Agent": self.headers["User-Agent"]}
                if fallback_url == iframe_url
                else self.headers
            )
            return {
                "parse": 1,
                "jx": 1,
                "playUrl": "",
                "url": fallback_url,
                "header": fallback_header,
            }
        return {
            "parse": 0,
            "jx": 0,
            "playUrl": "",
            "url": final_url,
            "header": {"Referer": iframe_url, "User-Agent": self.headers["User-Agent"]},
        }
