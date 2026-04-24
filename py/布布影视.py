# coding=utf-8
import hashlib
import random
import re
import sys
import time

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "布布影视"
        self.host = "https://bbys.app"
        self.pkg = "com.sunshine.tv"
        self.ver = "4"
        self.finger = "SF-C3B2B41F6EFFFF9869176CF68F6790E8F07506FC88632C94B4F5F0430D5498CA"
        self.sk = "SK-thanks"
        self.web_sign = "f65f3a83d6d9ad6f"
        self.x_client = "8f3d2a1c7b6e5d4c9a0b1f2e3d4c5b6a"
        self.current_year = time.localtime().tm_year
        self.headers = {
            "User-Agent": "okhttp/4.12.0",
            "Accept": "application/json",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "剧集"},
            {"type_id": "3", "type_name": "动漫"},
            {"type_id": "4", "type_name": "综艺"},
        ]
        self.filters = {
            "1": [
                {
                    "key": "class",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "动作", "v": "动作"},
                        {"n": "喜剧", "v": "喜剧"},
                        {"n": "爱情", "v": "爱情"},
                        {"n": "科幻", "v": "科幻"},
                        {"n": "恐怖", "v": "恐怖"},
                        {"n": "悬疑", "v": "悬疑"},
                        {"n": "犯罪", "v": "犯罪"},
                        {"n": "战争", "v": "战争"},
                        {"n": "动画", "v": "动画"},
                        {"n": "冒险", "v": "冒险"},
                        {"n": "历史", "v": "历史"},
                        {"n": "灾难", "v": "灾难"},
                        {"n": "纪录", "v": "纪录"},
                        {"n": "剧情", "v": "剧情"},
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
                        {"n": "美国", "v": "美国"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "泰国", "v": "泰国"},
                        {"n": "印度", "v": "印度"},
                        {"n": "英国", "v": "英国"},
                        {"n": "法国", "v": "法国"},
                        {"n": "德国", "v": "德国"},
                        {"n": "加拿大", "v": "加拿大"},
                        {"n": "西班牙", "v": "西班牙"},
                        {"n": "意大利", "v": "意大利"},
                        {"n": "澳大利亚", "v": "澳大利亚"},
                    ],
                },
                {"key": "year", "name": "年份", "value": self._generate_years("电影")},
                {
                    "key": "by",
                    "name": "排序",
                    "value": [
                        {"n": "最热", "v": "hits"},
                        {"n": "最新", "v": "time"},
                        {"n": "评分", "v": "score"},
                    ],
                },
            ],
            "2": [
                {
                    "key": "class",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "爱情", "v": "爱情"},
                        {"n": "古装", "v": "古装"},
                        {"n": "武侠", "v": "武侠"},
                        {"n": "历史", "v": "历史"},
                        {"n": "家庭", "v": "家庭"},
                        {"n": "喜剧", "v": "喜剧"},
                        {"n": "悬疑", "v": "悬疑"},
                        {"n": "犯罪", "v": "犯罪"},
                        {"n": "战争", "v": "战争"},
                        {"n": "奇幻", "v": "奇幻"},
                        {"n": "科幻", "v": "科幻"},
                        {"n": "恐怖", "v": "恐怖"},
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
                        {"n": "美国", "v": "美国"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "泰国", "v": "泰国"},
                        {"n": "英国", "v": "英国"},
                    ],
                },
                {"key": "year", "name": "年份", "value": self._generate_years("剧集")},
                {
                    "key": "by",
                    "name": "排序",
                    "value": [
                        {"n": "最热", "v": "hits"},
                        {"n": "最新", "v": "time"},
                        {"n": "评分", "v": "score"},
                    ],
                },
            ],
            "3": [
                {
                    "key": "class",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "冒险", "v": "冒险"},
                        {"n": "奇幻", "v": "奇幻"},
                        {"n": "科幻", "v": "科幻"},
                        {"n": "武侠", "v": "武侠"},
                        {"n": "悬疑", "v": "悬疑"},
                    ],
                },
                {
                    "key": "area",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "日本", "v": "日本"},
                        {"n": "欧美", "v": "欧美"},
                    ],
                },
                {"key": "year", "name": "年份", "value": self._generate_years("动漫")},
                {
                    "key": "by",
                    "name": "排序",
                    "value": [
                        {"n": "最热", "v": "hits"},
                        {"n": "最新", "v": "time"},
                        {"n": "评分", "v": "score"},
                    ],
                },
            ],
            "4": [
                {
                    "key": "class",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "真人秀", "v": "真人秀"},
                        {"n": "音乐", "v": "音乐"},
                        {"n": "脱口秀", "v": "脱口秀"},
                        {"n": "歌舞", "v": "歌舞"},
                        {"n": "爱情", "v": "爱情"},
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
                        {"n": "美国", "v": "美国"},
                        {"n": "日本", "v": "日本"},
                        {"n": "韩国", "v": "韩国"},
                    ],
                },
                {"key": "year", "name": "年份", "value": self._generate_years("综艺")},
                {
                    "key": "by",
                    "name": "排序",
                    "value": [
                        {"n": "最热", "v": "hits"},
                        {"n": "最新", "v": "time"},
                        {"n": "评分", "v": "score"},
                    ],
                },
            ],
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        payload = self._request_json("/api.php/web/index/home", headers=self._get_web_headers())
        categories = ((payload.get("data") or {}).get("categories") or [])
        videos = []
        for category in categories:
            videos.extend(self._convert_json_to_vods(category.get("videos") or []))
        if not videos:
            for type_name in ("电影", "剧集", "综艺", "动漫"):
                videos.extend(self._get_class_list(type_name, 1, {"by": "hits"}).get("list", []))
        return {"list": videos}

    def categoryContent(self, tid, pg, filter, extend):
        type_name = self._map_type_name(tid)
        if type_name not in ("电影", "剧集", "动漫", "综艺"):
            videos = []
            for name in ("电影", "剧集", "综艺", "动漫"):
                videos.extend(self._get_class_list(name, 1, {"by": "hits"}).get("list", []))
            return {"page": 1, "limit": len(videos), "total": int(pg) * 30 + len(videos), "list": videos}
        return self._get_class_list(type_name, int(pg), extend or {})

    def detailContent(self, ids):
        vod_id = self._stringify(ids[0] if isinstance(ids, list) and ids else ids).strip()
        if not vod_id:
            return {"list": []}
        payload = self._request_json(
            "/api.php/web/vod/get_detail",
            headers=self._get_web_headers(),
            params={"vod_id": vod_id},
        )
        detail = payload.get("data")
        if isinstance(detail, list):
            detail = detail[0] if detail else None
        if not detail:
            return {"list": []}
        play_data = self._build_play_data(
            detail.get("vod_play_from", ""),
            detail.get("vod_play_url", ""),
            payload.get("vodplayer") or [],
        )
        return {
            "list": [
                {
                    "vod_id": self._stringify(detail.get("vod_id") or vod_id),
                    "vod_name": self._stringify(detail.get("vod_name")),
                    "vod_pic": self._stringify(detail.get("vod_pic")),
                    "vod_remarks": self._stringify(detail.get("vod_remarks") or detail.get("vod_duration")),
                    "vod_year": self._stringify(detail.get("vod_year")),
                    "vod_area": self._stringify(detail.get("vod_area")),
                    "vod_actor": self._stringify(detail.get("vod_actor")),
                    "vod_director": self._stringify(detail.get("vod_director")),
                    "vod_content": self._clean_html_content(detail.get("vod_content")),
                    "type_name": self._stringify(detail.get("vod_class") or detail.get("type_name")),
                    "vod_play_from": play_data["vod_play_from"],
                    "vod_play_url": play_data["vod_play_url"],
                }
            ]
        }

    def searchContent(self, key, quick, pg="1"):
        keyword = self._stringify(key).strip()
        page = int(pg)
        if not keyword:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        payload = self._request_json(
            "/api.php/app/search/index",
            headers=self._get_app_headers(),
            params={"wd": keyword, "page": page, "limit": 15},
        )
        items = self._convert_json_to_vods(payload.get("data") or [])
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def playerContent(self, flag, id, vipFlags):
        raw = self._stringify(id).strip()
        if not raw:
            return {"parse": 0, "playUrl": "", "url": "", "jx": 0}

        play_from = ""
        play_url = raw
        need_decode = False
        matched = re.match(r"^([^@]+)@([^@]+)@([\s\S]+)$", raw)
        if matched:
            play_from = matched.group(1)
            need_decode = matched.group(2).strip() not in ("", "0")
            play_url = matched.group(3)
        elif not raw.startswith(("http://", "https://")):
            need_decode = True

        final_url = play_url
        if need_decode:
            payload = self._request_json(
                "/api.php/app/decode/url/",
                headers=self._get_app_headers(),
                params={"url": play_url, "vodFrom": play_from},
            )
            decoded = self._extract_decode_url(payload)
            if self._is_disabled_decode_result(payload, play_url, decoded):
                return {
                    "parse": 1,
                    "playUrl": "",
                    "url": "",
                    "jx": 0,
                    "header": {"User-Agent": "okhttp/4.12.0"},
                }
            if decoded:
                final_url = decoded

        need_jx = 1 if re.search(r"(iqiyi\.com|v\.qq\.com|youku\.com|mgtv\.com|bilibili\.com)", final_url, re.I) else 0
        return {
            "parse": 0,
            "playUrl": "",
            "url": final_url,
            "jx": need_jx,
            "header": {"User-Agent": "okhttp/4.12.0"},
        }

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _join_text(self, value):
        if isinstance(value, list):
            return "/".join([self._stringify(item) for item in value if self._stringify(item)])
        return self._stringify(value)

    def _clean_html_content(self, content):
        if not content:
            return ""
        text = str(content).replace("<p>", "").replace("</p>", "\n")
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()

    def _safe_split(self, value, sep):
        if value or value == "":
            return str(value).split(sep)
        return []

    def _build_play_data(self, vod_play_from, vod_play_url, vodplayer=None):
        from_list = self._safe_split(vod_play_from, "$$$")
        url_groups = self._safe_split(vod_play_url, "$$$")
        player_meta = self._build_player_meta(vodplayer)
        final_from = []
        final_url = []
        for index in range(max(len(from_list), len(url_groups))):
            raw_from = (from_list[index] if index < len(from_list) else f"line{index + 1}").strip() or f"line{index + 1}"
            group = (url_groups[index] if index < len(url_groups) else "").strip()
            if not group:
                continue
            meta = player_meta.get(raw_from) or {}
            display_from = self._stringify(meta.get("show")).strip() or raw_from
            episodes = []
            for item in [part.strip() for part in group.split("#") if part.strip()]:
                if "$" in item:
                    title, raw_url = item.split("$", 1)
                else:
                    title, raw_url = "播放", item
                title = title.strip() or "播放"
                raw_url = raw_url.strip()
                if raw_url:
                    decode_status = self._stringify(meta.get("decode_status")).strip()
                    if not decode_status:
                        decode_status = "0" if raw_url.startswith(("http://", "https://")) else "1"
                    episodes.append(f"{title}${raw_from}@{decode_status}@{raw_url}")
            if episodes:
                final_from.append(f"{display_from}({len(episodes)})")
                final_url.append("#".join(episodes))
        return {"vod_play_from": "$$$".join(final_from), "vod_play_url": "$$$".join(final_url)}

    def _build_player_meta(self, vodplayer):
        meta = {}
        for item in vodplayer or []:
            if not isinstance(item, dict):
                continue
            source_from = self._stringify(item.get("from")).strip()
            if not source_from:
                continue
            meta[source_from] = {
                "show": self._stringify(item.get("show")).strip(),
                "decode_status": self._stringify(item.get("decode_status")).strip(),
            }
        return meta

    def _is_disabled_decode_result(self, payload, play_url, decoded):
        if not isinstance(payload, dict):
            return False
        message = self._stringify(payload.get("msg")).strip()
        if "停用" in message or "稍后再试" in message:
            return True
        if "解码失败" not in message:
            return False
        return bool(decoded) and decoded == play_url and not decoded.startswith(("http://", "https://", "/"))

    def _generate_years(self, type_name):
        years = [{"n": "全部", "v": ""}]
        if type_name == "电影":
            for year in range(self.current_year, 2015, -1):
                years.append({"n": str(year), "v": str(year)})
            years.extend(
                [
                    {"n": "2015-2011", "v": "2015-2011"},
                    {"n": "2010-2000", "v": "2010-2000"},
                    {"n": "90年代", "v": "90年代"},
                    {"n": "80年代", "v": "80年代"},
                    {"n": "更早", "v": "更早"},
                ]
            )
            return years

        floor = 2021 if type_name == "剧集" else 2011
        for year in range(self.current_year, floor - 1, -1):
            years.append({"n": str(year), "v": str(year)})
        years.append({"n": "更早", "v": "更早"})
        return years

    def _create_sign_data(self):
        timestamp = str(int(time.time()))
        nonce = f"{random.randint(0, 9)}{random.randint(10, 99)}"
        sign_source = (
            f"finger={self.finger}&id={self.pkg}&nonce={nonce}"
            f"&sk={self.sk}&time={timestamp}&v={self.ver}"
        )
        sign = hashlib.sha256(sign_source.encode("utf-8")).hexdigest().upper()
        return {"timestamp": timestamp, "nonce": nonce, "sign": sign}

    def _get_app_headers(self):
        sign_data = self._create_sign_data()
        headers = dict(self.headers)
        headers.update(
            {
                "x-aid": self.pkg,
                "x-time": sign_data["timestamp"],
                "x-sign": sign_data["sign"],
                "x-nonc": sign_data["nonce"],
                "x-ave": self.ver,
            }
        )
        return headers

    def _get_web_headers(self):
        headers = self._get_app_headers()
        headers.update(
            {
                "web-sign": self.web_sign,
                "X-Client": self.x_client,
            }
        )
        return headers

    def _request_json(self, path, headers=None, params=None):
        url = path if str(path).startswith("http") else self.host + path
        response = self.fetch(url, headers=headers, params=params, timeout=15, verify=False)
        if response.status_code != 200:
            return {}
        return response.json()

    def _convert_json_to_vods(self, video_list):
        items = []
        for item in video_list or []:
            items.append(
                {
                    "vod_id": self._stringify(item.get("vod_id") or item.get("id")),
                    "vod_name": self._stringify(item.get("vod_name") or item.get("name")),
                    "vod_pic": self._stringify(item.get("vod_pic") or item.get("pic")),
                    "vod_remarks": self._stringify(
                        item.get("vod_remarks") or item.get("vod_duration") or item.get("remark")
                    ),
                    "type_name": self._join_text(item.get("vod_class") or item.get("type_name") or item.get("class")),
                    "vod_year": self._join_text(item.get("vod_year") or item.get("year")),
                    "vod_area": self._join_text(item.get("vod_area") or item.get("area")),
                }
            )
        return items

    def _map_type_name(self, value):
        mapping = {
            "1": "电影",
            "2": "剧集",
            "3": "动漫",
            "4": "综艺",
            "电影": "电影",
            "剧集": "剧集",
            "动漫": "动漫",
            "综艺": "综艺",
        }
        return mapping.get(self._stringify(value), self._stringify(value))

    def _get_class_list(self, tid, page=1, extend=None):
        type_name = self._map_type_name(tid)
        ext = extend or {}
        payload = self._request_json(
            "/api.php/web/filter/vod",
            headers=self._get_web_headers(),
            params={
                "type_name": type_name,
                "page": int(page),
                "sort": ext.get("by", "hits"),
                "class": ext.get("class", ""),
                "area": ext.get("area", ""),
                "year": ext.get("year", ""),
            },
        )
        items = self._convert_json_to_vods(payload.get("data") or [])
        return {"page": int(page), "limit": len(items), "total": page * 30 + len(items), "list": items}

    def _extract_decode_url(self, payload):
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, str) and data:
                return data
            if isinstance(data, dict) and isinstance(data.get("url"), str) and data.get("url"):
                return data.get("url")
            if isinstance(payload.get("url"), str) and payload.get("url"):
                return payload.get("url")
        return ""
