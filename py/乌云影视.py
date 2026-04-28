# coding=utf-8
import base64
import json
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "乌云影视"
        self.host = "https://wooyun.tv"
        self.page_size = 24
        self.home_limit = 12
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": self.host,
            "Referer": self.host + "/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        self.sort_options = [
            {"n": "默认", "v": "default"},
            {"n": "最新", "v": "latest"},
            {"n": "最热", "v": "hot"},
            {"n": "评分", "v": "score"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _ensure_list(self, value):
        return value if isinstance(value, list) else []

    def _normalize_ext(self, extend):
        if isinstance(extend, dict):
            return extend
        if not extend:
            return {}
        try:
            return json.loads(str(extend))
        except Exception:
            return {}

    def _full_url(self, path):
        raw = self._stringify(path).strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _request_json(self, path, method="GET", data=None, headers=None):
        url = path if str(path).startswith("http") else self.host + path
        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)

        if method == "POST":
            response = self.post(url, json=data, headers=merged_headers, timeout=15)
        else:
            response = self.fetch(url, headers=merged_headers, timeout=15)

        if response.status_code < 200 or response.status_code >= 300:
            raise ValueError(f"{method} {path} => HTTP {response.status_code}")

        payload = response.json()
        if payload.get("code") not in (None, 200) and payload.get("isSuccess") is False:
            raise ValueError(payload.get("resultMsg") or str(payload.get("code")))
        return payload.get("data")

    def _build_classes(self, menu):
        classes = []
        for code, fallback in [
            ("movie", "电影"),
            ("tv_series", "电视剧"),
            ("animation", "动画"),
            ("variety", "综艺"),
            ("short_drama", "短剧"),
        ]:
            found = next((item for item in self._ensure_list(menu) if item.get("code") == code), None)
            classes.append(
                {"type_id": code, "type_name": self._stringify((found or {}).get("name") or fallback)}
            )

        year_group = next((item for item in self._ensure_list(menu) if item.get("nameEn") == "year"), {})
        year_children = self._ensure_list(year_group.get("children"))
        this_year = next((item for item in year_children if item.get("code") == "THIS_YEAR"), {})
        last_year = next((item for item in year_children if item.get("code") == "LAST_YEAR"), {})
        classes.append({"type_id": "THIS_YEAR", "type_name": self._stringify(this_year.get("name") or "今年")})
        classes.append({"type_id": "LAST_YEAR", "type_name": self._stringify(last_year.get("name") or "去年")})
        return classes

    def _build_filters(self, menu, classes):
        option_map = {"genre": [], "region": [], "year": [], "language": []}
        for group in self._ensure_list(menu):
            values = []
            for item in self._ensure_list(group.get("children")):
                code = self._stringify(item.get("code"))
                name = self._stringify(item.get("name") or item.get("nameEn") or code)
                if code and name and code not in ("THIS_YEAR", "LAST_YEAR"):
                    values.append({"n": name, "v": code})
            if group.get("nameEn") in option_map:
                option_map[group.get("nameEn")] = values

        filters = {}
        for cls in classes:
            items = []
            if option_map["year"]:
                items.append(
                    {
                        "key": "year",
                        "name": "年份",
                        "init": "",
                        "value": [{"n": "全部", "v": ""}] + option_map["year"],
                    }
                )
            if option_map["region"]:
                items.append(
                    {
                        "key": "region",
                        "name": "地区",
                        "init": "",
                        "value": [{"n": "全部", "v": ""}] + option_map["region"],
                    }
                )
            if option_map["genre"] and cls["type_id"] in (
                "movie",
                "tv_series",
                "animation",
                "variety",
                "short_drama",
            ):
                items.append(
                    {
                        "key": "genre",
                        "name": "类型",
                        "init": "",
                        "value": [{"n": "全部", "v": ""}] + option_map["genre"],
                    }
                )
            if option_map["language"]:
                items.append(
                    {
                        "key": "lang",
                        "name": "语言",
                        "init": "",
                        "value": [{"n": "全部", "v": ""}] + option_map["language"],
                    }
                )
            items.append({"key": "sort", "name": "排序", "init": "default", "value": self.sort_options})
            filters[cls["type_id"]] = items
        return filters

    def _map_top_code(self, category_id):
        mapping = {
            "movie": "movie",
            "tv_series": "tv_series",
            "animation": "animation",
            "variety": "variety",
            "short_drama": "short_drama",
            "THIS_YEAR": "movie",
            "LAST_YEAR": "movie",
        }
        return mapping.get(category_id, "movie")

    def _build_category_body(self, category_id, page, extend):
        filters = self._normalize_ext(extend)
        menu_code_list = []
        if category_id not in ("movie", "tv_series", "animation", "variety", "short_drama"):
            menu_code_list.append(category_id)
        for key in ("genre", "region", "year", "lang", "other"):
            value = self._stringify(filters.get(key))
            if value and value not in menu_code_list:
                menu_code_list.append(value)
        return {
            "menuCodeList": menu_code_list,
            "pageIndex": self._stringify(page or 1),
            "pageSize": self.page_size,
            "searchKey": "",
            "sortCode": "" if filters.get("sort") in (None, "", "default") else self._stringify(filters.get("sort")),
            "topCode": self._map_top_code(category_id),
        }

    def _join_text(self, value):
        return "/".join([self._stringify(item) for item in self._ensure_list(value) if self._stringify(item)])

    def _pick_poster(self, item):
        return self._stringify(
            item.get("posterUrlS3") or item.get("posterUrl") or item.get("thumbUrlS3") or item.get("thumbUrl")
        )

    def _extract_home_list(self, home_blocks):
        if isinstance(home_blocks, dict):
            blocks = self._ensure_list(home_blocks.get("records"))
        else:
            blocks = self._ensure_list(home_blocks)
        seen = set()
        items = []
        for block in blocks:
            for item in self._ensure_list(block.get("mediaResources")):
                vod_id = self._stringify(item.get("id"))
                if not vod_id or vod_id in seen:
                    continue
                seen.add(vod_id)
                copied = dict(item)
                copied["id"] = vod_id
                items.append(copied)
        return items

    def _map_vod(self, item):
        media_type = item.get("mediaType") or {}
        return {
            "vod_id": self._stringify(item.get("id")),
            "vod_name": self._stringify(item.get("title")),
            "vod_pic": self._pick_poster(item),
            "type_id": self._stringify(media_type.get("code")),
            "type_name": self._stringify(media_type.get("name")),
            "vod_remarks": self._stringify(item.get("episodeStatus") or item.get("remark")),
            "vod_year": self._stringify(item.get("releaseYear")),
            "vod_douban_score": self._stringify(item.get("rating")),
            "vod_actor": self._join_text(item.get("actors")),
            "vod_director": self._join_text(item.get("directors")),
        }

    def homeContent(self, filter):
        menu = self._request_json("/movie/category/menu")
        classes = self._build_classes(menu)
        return {"class": classes, "filters": self._build_filters(menu, classes)}

    def homeVideoContent(self):
        data = self._request_json(f"/movie/media/home/custom/classify/1/3?limit={self.home_limit}")
        items = self._extract_home_list(data)[: self.home_limit]
        return {"list": [self._map_vod(item) for item in items]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        data = self._request_json(
            "/movie/media/search",
            method="POST",
            data=self._build_category_body(self._stringify(tid or "movie"), page, extend),
            headers={"Content-Type": "application/json"},
        ) or {}
        records = [self._map_vod(item) for item in self._ensure_list(data.get("records"))]
        total = int(data.get("total") or 0)
        return {"page": page, "limit": self.page_size, "total": total, "list": records}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._stringify(key).strip()
        if not keyword:
            return {"page": page, "total": 0, "list": []}

        data = self._request_json(
            "/movie/media/search",
            method="POST",
            data={
                "menuCodeList": [],
                "pageIndex": self._stringify(page),
                "pageSize": self.page_size,
                "searchKey": keyword,
                "sortCode": "",
                "topCode": "",
            },
            headers={"Content-Type": "application/json"},
        ) or {}
        records = [self._map_vod(item) for item in self._ensure_list(data.get("records"))]
        total = int(data.get("total") or 0)
        return {"page": page, "total": total, "list": records}

    def _encode_play_payload(self, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    def _decode_play_id(self, play_id):
        raw = self._stringify(play_id).strip()
        padding = "=" * (-len(raw) % 4)
        try:
            return json.loads(base64.urlsafe_b64decode((raw + padding).encode("utf-8")).decode("utf-8"))
        except Exception:
            return {"mediaId": "", "playUrl": ""}

    def _build_play_sources(self, seasons, media_id):
        season_list = self._ensure_list(seasons)
        multiple = len(season_list) > 1
        from_list = []
        url_list = []
        for index, season in enumerate(season_list, start=1):
            season_no = season.get("seasonNo") or index
            episode_entries = []
            for video_index, video in enumerate(self._ensure_list(season.get("videoList")), start=1):
                ep_no = int(video.get("epNo") or video_index)
                remark = self._stringify(video.get("remark")).strip()
                if ep_no > 0:
                    name = f"第{ep_no}集" if not remark else f"第{ep_no}集 {remark}"
                else:
                    name = remark or "正片"
                payload = self._encode_play_payload(
                    {
                        "mediaId": self._stringify(media_id),
                        "seasonNo": season_no,
                        "epNo": ep_no,
                        "videoId": video.get("id"),
                        "playUrl": video.get("playUrl"),
                        "name": name,
                    }
                )
                episode_entries.append(f"{name}${payload}")
            if episode_entries:
                from_list.append(
                    f"第{season_no}季"
                    if multiple
                    else self._stringify(season.get("lineName") or season.get("title") or self.name)
                )
                url_list.append("#".join(episode_entries))
        return {"vod_play_from": "$$$".join(from_list), "vod_play_url": "$$$".join(url_list)}

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            media_id = self._stringify(raw_id).strip()
            if not media_id:
                continue
            base_detail = self._request_json(f"/movie/media/base/detail?mediaId={media_id}") or {}
            detail = self._request_json(f"/movie/media/detail?mediaId={media_id}") or {}
            seasons = self._request_json(
                f"/movie/media/video/list?mediaId={media_id}&lineName=&resolutionCode="
            ) or []
            merged = detail or base_detail
            play_data = self._build_play_sources(seasons, media_id)
            result["list"].append(
                {
                    "vod_id": self._stringify(merged.get("id") or media_id),
                    "vod_name": self._stringify(merged.get("title") or base_detail.get("title")),
                    "vod_pic": self._pick_poster(merged or base_detail),
                    "type_id": self._stringify((merged.get("mediaType") or {}).get("code")),
                    "type_name": self._stringify((merged.get("mediaType") or {}).get("name")),
                    "vod_remarks": self._stringify(merged.get("episodeStatus")),
                    "vod_year": self._stringify(merged.get("releaseYear")),
                    "vod_area": self._stringify(merged.get("region")),
                    "vod_actor": self._join_text(merged.get("actors")),
                    "vod_director": self._join_text(merged.get("directors")),
                    "vod_content": self._stringify(merged.get("overview") or merged.get("description")),
                    "vod_douban_score": self._stringify(merged.get("rating")),
                    **play_data,
                }
            )
        return result

    def _find_play_url(self, seasons, target):
        for season in self._ensure_list(seasons):
            if target.get("seasonNo") is not None and int(season.get("seasonNo") or 0) != int(target.get("seasonNo")):
                continue
            for video in self._ensure_list(season.get("videoList")):
                if target.get("videoId") is not None and int(video.get("id") or 0) == int(target.get("videoId")):
                    return self._stringify(video.get("playUrl"))
                if target.get("epNo") is not None and int(video.get("epNo") or 0) == int(target.get("epNo")):
                    return self._stringify(video.get("playUrl"))

        first_season = self._ensure_list(seasons)[0] if self._ensure_list(seasons) else {}
        first_video = (
            self._ensure_list(first_season.get("videoList"))[0]
            if self._ensure_list(first_season.get("videoList"))
            else {}
        )
        return self._stringify(first_video.get("playUrl"))

    def playerContent(self, flag, id, vipFlags):
        payload = self._decode_play_id(self._stringify(id).strip())
        final_url = self._stringify(payload.get("playUrl"))
        if not final_url and payload.get("mediaId"):
            seasons = self._request_json(
                f"/movie/media/video/list?mediaId={payload['mediaId']}&lineName=&resolutionCode="
            ) or []
            final_url = self._find_play_url(seasons, payload)

        if not final_url:
            return {"parse": 1, "jx": 1, "url": self._stringify(id), "header": dict(self.headers)}

        return {
            "parse": 0,
            "jx": 0,
            "url": self._full_url(final_url),
            "header": {
                "Referer": self.host + "/",
                "Origin": self.host,
                "User-Agent": self.headers["User-Agent"],
            },
        }
