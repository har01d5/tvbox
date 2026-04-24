# coding=utf-8
import json
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "酷我听书"
        self.api_host = "http://tingshu.kuwo.cn"
        self.search_host = "http://search.kuwo.cn"
        self.play_host = "http://mobi.kuwo.cn"
        self.parse_api = "https://music-api.gdstudio.xyz/api.php"
        self.ua = "kwplayer_ar_9.1.8.1_tvivo.apk"
        self.headers = {
            "User-Agent": self.ua,
            "Referer": self.api_host,
        }
        self.classes = [
            {"type_id": "2", "type_name": "有声小说"},
            {"type_id": "37", "type_name": "音乐金曲"},
            {"type_id": "5", "type_name": "相声评书"},
            {"type_id": "62", "type_name": "影视原声"},
        ]
        self.class_filters = {
            "2": [
                {"n": "都市传说", "v": "42"},
                {"n": "玄幻奇幻", "v": "44"},
                {"n": "武侠仙侠", "v": "48"},
                {"n": "穿越架空", "v": "52"},
                {"n": "科幻竞技", "v": "57"},
                {"n": "幻想言情", "v": "169"},
                {"n": "独家定制", "v": "170"},
                {"n": "古代言情", "v": "207"},
                {"n": "影视原著", "v": "213"},
                {"n": "悬疑推理", "v": "45"},
                {"n": "历史军事", "v": "56"},
                {"n": "现代言情", "v": "41"},
                {"n": "青春校园", "v": "55"},
                {"n": "文学名著", "v": "61"},
            ],
            "5": [
                {"n": "评书大全", "v": "220"},
                {"n": "小品合辑", "v": "221"},
                {"n": "单口相声", "v": "219"},
                {"n": "热门相声", "v": "218"},
                {"n": "相声名家", "v": "290"},
                {"n": "粤语评书", "v": "320"},
                {"n": "相声新人", "v": "222"},
                {"n": "张少佐", "v": "313"},
                {"n": "刘立福", "v": "314"},
                {"n": "刘兰芳", "v": "309"},
                {"n": "连丽如", "v": "311"},
                {"n": "田占义", "v": "317"},
                {"n": "袁阔成", "v": "310"},
                {"n": "孙一", "v": "315"},
                {"n": "王玥波", "v": "316"},
                {"n": "单田芳", "v": "217"},
                {"n": "关永超", "v": "325"},
                {"n": "马长辉", "v": "326"},
                {"n": "赵维莉", "v": "327"},
                {"n": "潮剧", "v": "1718"},
                {"n": "沪剧", "v": "1719"},
                {"n": "晋剧", "v": "1720"},
            ],
            "37": [
                {"n": "抖音神曲", "v": "253"},
                {"n": "怀旧老歌", "v": "252"},
                {"n": "创作翻唱", "v": "248"},
                {"n": "催眠", "v": "254"},
                {"n": "古风", "v": "255"},
                {"n": "博客周刊", "v": "1423"},
                {"n": "民谣", "v": "1409"},
                {"n": "纯音乐", "v": "1408"},
                {"n": "3D电音", "v": "1407"},
                {"n": "音乐课程", "v": "1380"},
                {"n": "音乐推荐", "v": "250"},
                {"n": "音乐故事", "v": "247"},
                {"n": "情感推荐", "v": "246"},
                {"n": "儿童音乐", "v": "249"},
            ],
            "62": [
                {"n": "影视广播", "v": "1485"},
                {"n": "影视解读", "v": "1483"},
                {"n": "影视原著", "v": "1486"},
                {"n": "陪你追剧", "v": "1398"},
                {"n": "经典原声", "v": "1482"},
            ],
        }
        self.default_class = {"2": "42", "37": "253", "5": "220", "62": "1485"}
        self.vip_filter = {
            "key": "vip",
            "name": "权限",
            "init": "",
            "value": [
                {"n": "全部权限", "v": ""},
                {"n": "免费权限", "v": "0"},
                {"n": "会员权限", "v": "1"},
            ],
        }
        self.sort_filter = {
            "key": "sort",
            "name": "排序",
            "init": "tsScore",
            "value": [
                {"n": "综合排序", "v": "tsScore"},
                {"n": "最新上架", "v": "pubDate"},
                {"n": "按总播放", "v": "playCnt"},
            ],
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def _format_play_count(self, count):
        value = int(count or 0)
        if value >= 100000000:
            return f"{value / 100000000:.1f}亿"
        if value >= 10000:
            return f"{value / 10000:.1f}万"
        return str(value)

    def _is_paid_track(self, track):
        pay_info = (track or {}).get("payInfo") or {}
        fee_type = pay_info.get("feeType") or {}
        return str(fee_type.get("bookvip", "0")) == "1"

    def _parse_search_payload(self, text):
        raw = str(text or "").strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                return json.loads(raw.replace("'", '"'))
            except json.JSONDecodeError:
                return {}

    def _api_get(self, path, params=None, host=None, headers=None):
        target_host = str(host or self.api_host).rstrip("/")
        target = path if str(path or "").startswith("http") else f"{target_host}/{str(path or '').lstrip('/')}"
        request_headers = dict(self.headers)
        request_headers["Referer"] = target_host
        if headers:
            request_headers.update(headers)
        try:
            response = self.fetch(target, params=params, headers=request_headers, timeout=10, verify=False)
        except Exception:
            return {}
        if response.status_code != 200:
            return {}
        body = response.text or ""
        if not body.strip():
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body

    def _search_get(self, path, params=None):
        payload = self._api_get(path, params=params, host=self.search_host)
        if isinstance(payload, str):
            return self._parse_search_payload(payload)
        return payload or {}

    def _normalize_vod(self, item, category_name=""):
        data = item or {}
        vip_tag = "会员" if str(data.get("vip", "0")) == "1" else "免费"
        play_count = self._format_play_count(data.get("playCnt"))
        suffix = category_name or str(data.get("artist") or "")
        return {
            "vod_id": str(data.get("albumId", "")),
            "vod_name": str(data.get("albumName", "")),
            "vod_pic": str(data.get("coverImg", "")),
            "vod_remarks": f"{vip_tag} | {play_count}次播放 | {suffix}".strip(),
        }

    def _build_filters(self):
        filters = {}
        for item in self.classes:
            filters[item["type_id"]] = [
                {
                    "key": "class",
                    "name": "类型",
                    "init": self.default_class[item["type_id"]],
                    "value": list(self.class_filters[item["type_id"]]),
                },
                self.vip_filter,
                self.sort_filter,
            ]
        return filters

    def homeContent(self, filter):
        return {
            "class": self.classes,
            "filters": self._build_filters(),
            "list": self.homeVideoContent()["list"],
        }

    def homeVideoContent(self):
        videos = []
        for item in self.classes:
            payload = self._api_get(
                "/v2/api/search/filter/albums",
                {
                    "classifyId": self.default_class[item["type_id"]],
                    "notrace": 0,
                    "source": self.ua,
                    "platform": 1,
                    "uid": 2511482006,
                    "sortType": "tsScore",
                    "loginUid": 540339516,
                    "bksource": "kwbook_ar_9.1.8.1_tvivo.apk",
                    "rn": 12,
                    "categoryId": item["type_id"],
                    "pn": 1,
                },
            ) or {}
            for row in ((payload.get("data") or {}).get("data") or []):
                videos.append(self._normalize_vod(row, item["type_name"]))
        return {"list": videos}

    def _fetch_category_page(self, tid, page, classify_id, sort_type):
        payload = self._api_get(
            "/v2/api/search/filter/albums",
            {
                "classifyId": classify_id,
                "notrace": 0,
                "source": self.ua,
                "platform": 1,
                "uid": 2511482006,
                "sortType": sort_type,
                "loginUid": 540339516,
                "bksource": "kwbook_ar_9.1.8.1_tvivo.apk",
                "rn": 21,
                "categoryId": tid,
                "pn": page,
            },
        ) or {}
        return ((payload.get("data") or {}).get("data") or [])

    def _force_page_fetch(self, tid, page, classify_id, sort_type, vip_value):
        current_page = page
        attempts = 0
        while attempts < 10:
            items = self._fetch_category_page(tid, current_page, classify_id, sort_type)
            if not items:
                attempts += 1
                current_page += 1
                continue
            if vip_value in ("0", "1"):
                items = [item for item in items if str(item.get("vip", "")) == vip_value]
            if items or vip_value == "":
                return items, current_page, len(items) >= 21
            attempts += 1
            current_page += 1
        return [], current_page, False

    def categoryContent(self, tid, pg, filter, extend):
        tid = str(tid)
        page = int(pg)
        type_ids = {item["type_id"] for item in self.classes}
        if tid not in type_ids:
            return {"page": page, "limit": 21, "total": 0, "list": []}

        options = dict(extend or {})
        classify_id = str(options.get("class") or self.default_class[tid])
        vip_value = str(options.get("vip", self.vip_filter["init"]))
        sort_type = str(options.get("sort") or self.sort_filter["init"])
        items, actual_page, has_more = self._force_page_fetch(tid, page, classify_id, sort_type, vip_value)
        del actual_page
        category_name = next((item["type_name"] for item in self.classes if item["type_id"] == tid), "")
        return {
            "page": page,
            "limit": 21,
            "total": 999999 if has_more else len(items),
            "list": [self._normalize_vod(item, category_name) for item in items],
        }

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = int(pg)
        if not keyword:
            return {"page": page, "limit": 0, "total": 0, "list": []}

        payload = self._search_get(
            "/r.s",
            {
                "client": "kt",
                "all": keyword,
                "ft": "album",
                "newsearch": 1,
                "itemset": "web_2013",
                "cluster": 0,
                "pn": page - 1,
                "rn": 21,
                "rformat": "json",
                "encoding": "utf8",
                "show_copyright_off": 1,
                "vipver": "MUSIC_8.0.3.0_BCS75",
                "show_series_listen": 1,
                "version": "9.1.8.1",
            },
        )
        items = []
        for item in payload.get("albumlist") or []:
            vip_tag = "会员" if str(item.get("vip", "0")) == "1" else "免费"
            items.append(
                {
                    "vod_id": str(item.get("DC_TARGETID", "")),
                    "vod_name": str(item.get("name", "")),
                    "vod_pic": str(item.get("img", "")),
                    "vod_remarks": f"{vip_tag} | {str(item.get('artist', '')).strip()}".strip(),
                }
            )
        return {
            "page": page,
            "limit": 21,
            "total": int(payload.get("TOTAL") or len(items)),
            "list": items,
        }

    def _build_play_id(self, rid, is_vip):
        return f"{'vip' if is_vip else 'free'}|{rid}"

    def _build_cover(self, image):
        image = str(image or "")
        if image and not image.startswith("http"):
            return f"http://img3.sycdn.kuwo.cn/star/albumcover/240/{image}"
        return image

    def _fetch_album_detail_page(self, album_id, page, page_size=2000):
        return self._search_get(
            "/r.s",
            {
                "stype": "albuminfo",
                "user": "8d378d72qw28f5f4",
                "uid": 2511552006,
                "loginUid": 540129516,
                "loginSid": 958467960,
                "prod": "kwplayer_ar_9.1.8.1",
                "bkprod": "kwbook_ar_9.1.8.1",
                "source": self.ua,
                "bksource": "kwbook_ar_9.1.8.1_tvivo.apk",
                "corp": "kuwo",
                "albumid": album_id,
                "pn": page,
                "rn": page_size,
                "show_copyright_off": 1,
                "vipver": "MUSIC_8.2.0.0_BCS17",
                "mobi": 1,
                "iskwbook": 1,
            },
        ) or {}

    def _fetch_album_detail(self, album_id, page_size=2000, max_pages=20):
        merged_payload = {}
        tracks = []
        seen_track_ids = set()
        total_expected = 0

        for page in range(max_pages):
            payload = self._fetch_album_detail_page(album_id, page, page_size)
            page_tracks = payload.get("musiclist") or []
            if not payload and page == 0:
                return {}
            if not merged_payload and payload:
                merged_payload = dict(payload)
            elif payload:
                for key, value in payload.items():
                    if key == "musiclist":
                        continue
                    if merged_payload.get(key) in ("", None, [], {}) and value not in ("", None, [], {}):
                        merged_payload[key] = value

            songnum = payload.get("songnum") or merged_payload.get("songnum")
            try:
                total_expected = int(songnum or 0)
            except (TypeError, ValueError):
                total_expected = 0

            added = 0
            for track in page_tracks:
                track_id = str(track.get("musicrid") or "")
                dedupe_key = track_id or f"{track.get('name', '')}|{len(tracks)}"
                if dedupe_key in seen_track_ids:
                    continue
                seen_track_ids.add(dedupe_key)
                tracks.append(track)
                added += 1

            if not page_tracks or added == 0:
                break
            if total_expected and len(tracks) >= total_expected:
                break
            if len(page_tracks) < page_size:
                break

        if not tracks:
            return {}
        merged_payload["musiclist"] = tracks
        if total_expected:
            merged_payload["songnum"] = str(total_expected)
        return merged_payload

    def detailContent(self, ids):
        album_id = str(ids[0] if isinstance(ids, list) and ids else ids).strip()
        if not album_id:
            return {"list": []}

        payload = self._fetch_album_detail(album_id)
        tracks = payload.get("musiclist") or []
        if not tracks:
            return {"list": []}

        play_items = []
        total_play = 0
        for index, track in enumerate(tracks, start=1):
            total_play += int(track.get("playcnt") or 0)
            is_vip = self._is_paid_track(track)
            name = str(track.get("name") or f"第{index}集")
            display_name = f"💎{name}" if is_vip else name
            play_items.append(f"{index}.{display_name}${self._build_play_id(track.get('musicrid'), is_vip)}")

        is_finished = str(payload.get("finished", "0")) == "1"
        vip_tag = "会员" if str(payload.get("vip", "0")) == "1" else "免费"
        pub = str(payload.get("pub") or "")
        return {
            "list": [
                {
                    "vod_id": album_id,
                    "vod_name": str(payload.get("name") or ""),
                    "vod_pic": self._build_cover(payload.get("img")),
                    "vod_remarks": (
                        f"{vip_tag} | {'已完结' if is_finished else '连载中'} | "
                        f"共{payload.get('songnum') or len(tracks)}集 | {self._format_play_count(total_play)}播放"
                    ),
                    "vod_content": str(payload.get("info") or payload.get("title") or ""),
                    "vod_actor": str(payload.get("artist") or ""),
                    "vod_director": str(payload.get("company") or ""),
                    "vod_year": f"{pub.split('-')[0]}年" if pub else "",
                    "vod_area": str(payload.get("lang") or ""),
                    "vod_lang": str(payload.get("lang") or ""),
                    "vod_time": pub,
                    "vod_tag": "完结" if is_finished else "连载",
                    "vod_play_from": "酷我听书",
                    "vod_play_url": "#".join(play_items),
                }
            ]
        }

    def _resolve_free_play(self, rid):
        params = {
            "f": "web",
            "source": "kwplayerhd_ar_4.3.0.8_tianbao_T1A_qirui.apk",
            "type": "convert_url_with_sign",
            "rid": rid,
            "br": "320kmp3",
        }
        payload = self._api_get("/mobi.s", params=params, host=self.play_host) or {}
        url = ((payload.get("data") or {}).get("url") or "")
        if not url:
            url = (
                f"{self.play_host}/mobi.s?f=web&source=kwplayerhd_ar_4.3.0.8_tianbao_T1A_qirui.apk"
                f"&type=convert_url_with_sign&rid={rid}&br=320kmp3"
            )
        return {
            "parse": 0,
            "url": url,
            "header": {"User-Agent": self.ua, "Referer": self.api_host},
        }

    def _resolve_vip_play(self, rid):
        params = {
            "use_xbridge3": "true",
            "loader_name": "forest",
            "need_sec_link": "1",
            "sec_link_scene": "im",
            "theme": "light",
            "types": "url",
            "source": "kuwo",
            "id": rid,
            "br": "1",
        }
        payload = self._api_get("", params=params, host=self.parse_api, headers={"User-Agent": "LX-Music-Mobile"}) or {}
        url = str(payload.get("url") or "")
        if not url:
            url = (
                f"{self.parse_api}?use_xbridge3=true&loader_name=forest&need_sec_link=1"
                f"&sec_link_scene=im&theme=light&types=url&source=kuwo&id={rid}&br=1"
            )
        return {
            "parse": 0,
            "url": url,
            "header": {"User-Agent": "LX-Music-Mobile", "Referer": "https://music-api.gdstudio.xyz"},
        }

    def playerContent(self, flag, id, vipFlags):
        play_id = str(id or "")
        if play_id.startswith("free|"):
            return self._resolve_free_play(play_id.split("|", 1)[1])
        if play_id.startswith("vip|"):
            return self._resolve_vip_play(play_id.split("|", 1)[1])
        return {"parse": 0, "url": play_id, "header": {"User-Agent": self.ua}}
