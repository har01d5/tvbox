# coding=utf-8
import hashlib
import json
import sys
import uuid

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "橘子TV"
        self.config_url = "https://gapi0725.5p8jcjc.com/config.json"
        self.api_host = ""
        self.headers = {
            "User-Agent": "Dart/3.1 (dart:io)",
            "Accept-Encoding": "gzip",
            "content-type": "application/json; charset=utf-8",
        }
        self.app_id = "fea23e11fc1241409682880e15fb2851"
        self.app_key = "f384b87cc9ef41e4842dda977bae2c7f"
        self.udid = "bfc18c00-c866-46cb-8d7b-121c39b942d4"
        self.bundler_id = "com.voraguzzee.ts"
        self.source = "1003_default"
        self.version = "1.0.1"
        self.version_code = 1000
        self.inited = False
        self.next = ["", ""]

    def init(self, extend=""):
        if self.inited:
            return None

        response = self.fetch(self.config_url, headers=self.headers, timeout=10, verify=False)
        raw = response.text or ""

        try:
            hosts = json.loads(raw)
        except Exception:
            hosts = [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]

        for host in hosts:
            if str(host).startswith("http"):
                self.api_host = str(host).rstrip("/")
                break

        if not self.api_host:
            raise ValueError("未能获取到有效的API地址")

        self.inited = True
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def _dict_to_query(self, data):
        parts = []
        for key, value in data.items():
            if value != "":
                parts.append(f"{key}={value}")
        return "&".join(parts)

    def _sign_data(self, data):
        sorted_data = {key: data[key] for key in sorted(data)}
        query = self._dict_to_query(sorted_data)
        sign_source = f"{query}&appKey={self.app_key}" if query else f"appKey={self.app_key}"
        signed = dict(data)
        signed["sign"] = hashlib.md5(sign_source.encode("utf-8")).hexdigest()
        return signed

    def _build_payload(self, extra=None):
        payload = {
            "appId": self.app_id,
            "bundlerId": self.bundler_id,
            "cus1tom": "cus3tom",
            "deviceInfo": "xiaomi",
            "osInfo": "15",
            "otherParam": "1",
            "patchNumber": 0,
            "requestId": str(uuid.uuid4()),
            "source": self.source,
            "udid": self.udid,
            "version": self.version,
            "versionCode": self.version_code,
        }
        if extra:
            payload.update(extra)
        return self._sign_data(payload)

    def _post_api(self, path, payload):
        response = self.post(
            f"{self.api_host}{path}",
            json=payload,
            headers=self.headers,
            timeout=15,
            verify=False,
        )
        if response.status_code != 200:
            return {}
        try:
            return json.loads(response.text or "{}")
        except Exception:
            return {}

    def _parse_year(self, flags):
        text = str(flags or "")
        if not text:
            return ""
        return text.split(" / ")[0].strip()

    def homeContent(self, filter):
        response = self._post_api("/v2/api/home/header", self._build_payload())
        classes = []
        for item in response.get("data", {}).get("channeList", []):
            if item.get("channelId"):
                classes.append(
                    {
                        "type_id": str(item.get("channelId")),
                        "type_name": item.get("channelName", ""),
                    }
                )
        return {"class": classes}

    def homeVideoContent(self):
        response = self._post_api("/v2/api/home/body", self._build_payload())
        videos = []
        for topic in response.get("data", {}).get("vodTopicList", []):
            for item in topic.get("vodList", []):
                videos.append(
                    {
                        "vod_id": str(item.get("vodId", "")),
                        "vod_name": item.get("vodName", ""),
                        "vod_pic": item.get("coverImg", ""),
                        "vod_remarks": item.get("remark") or f"评分：{item.get('score', '')}",
                        "vod_year": self._parse_year(item.get("flags")),
                    }
                )
        return {"list": videos}

    def _map_video_item(self, item):
        return {
            "vod_id": str(item.get("vodId", "")),
            "vod_name": item.get("vodName", ""),
            "vod_pic": item.get("coverImg", ""),
            "vod_remarks": item.get("remark") or f"评分：{item.get('score', '')}",
            "vod_year": self._parse_year(item.get("flags")),
            "vod_content": item.get("intro", ""),
        }

    def _page_result(self, items, pg, has_next):
        page = int(pg)
        return {
            "list": items,
            "page": page,
            "limit": len(items),
            "total": page * 30 + len(items),
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        payload = self._build_payload(
            {
                "nextCount": 18,
                "nextVal": self.next[page] if page < len(self.next) else "",
                "queryValueJson": json.dumps(
                    [{"filerName": "channelId", "filerValue": str(tid)}],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "sortType": "",
            }
        )
        response = self._post_api("/v1/api/search/queryNow", payload)
        data = response.get("data", {})
        nextVal = data.get("nextVal", '')
        while len(self.next) <= page + 1:
            self.next.append("")
        self.next[page + 1] = nextVal
        items = [self._map_video_item(item) for item in data.get("items", []) if isinstance(item, dict)]
        return self._page_result(items, pg, data.get("hasNext") == 1)

    def searchContent(self, key, quick, pg="1"):
        payload = self._build_payload({"keyword": key, "nextVal": ""})
        response = self._post_api("/v1/api/search/search", payload)
        data = response.get("data", {})
        items = [self._map_video_item(item) for item in data.get("items", []) if isinstance(item, dict)]
        return self._page_result(items, pg, data.get("hasNext") == 1)

    def _parse_people(self, people):
        names = []
        for item in people or []:
            if isinstance(item, dict) and item.get("vodWorkerName"):
                names.append(item.get("vodWorkerName"))
        return ",".join(names)

    def _quality_score(self, show_name, resolution):
        text = "{0} {1}".format(str(show_name or "").lower(), str(resolution or "").lower())
        digits = "".join(ch for ch in text if ch.isdigit())
        if digits:
            try:
                return int(digits)
            except Exception:
                pass

        named_scores = {
            "原画": 5000,
            "蓝光": 4500,
            "4k": 4000,
            "2160": 4000,
            "超清": 3000,
            "uhd": 3000,
            "1080": 2800,
            "fhd": 2800,
            "高清": 2000,
            "hd": 2000,
            "720": 1800,
            "标清": 1000,
            "sd": 1000,
            "流畅": 500,
            "ld": 500,
        }
        for key, score in named_scores.items():
            if key in text:
                return score
        return 0

    def detailContent(self, ids):
        vod_id = ids[0]
        response = self._post_api("/v2/api/vodInfo/index", self._build_payload({"vodId": vod_id}))
        data = response.get("data", {})

        play_from = []
        play_urls = []
        for player in data.get("playerList", []):
            play_from.append(player.get("playerName", ""))
            episodes = []
            for episode in player.get("epList", []):
                episodes.append(f"{episode.get('epName', '')}${episode.get('epId', '')}")
            play_urls.append("#".join(episodes))

        return {
            "list": [
                {
                    "vod_id": str(data.get("vodId", "")),
                    "vod_name": data.get("vodName", ""),
                    "vod_pic": data.get("coverImg", ""),
                    "vod_remarks": data.get("updateRemark", ""),
                    "vod_year": data.get("year", ""),
                    "vod_area": data.get("areaName", ""),
                    "vod_actor": self._parse_people(data.get("actorList")),
                    "vod_director": self._parse_people(data.get("directorList")),
                    "vod_content": data.get("intro", ""),
                    "vod_play_from": "$$$".join(play_from),
                    "vod_play_url": "$$$".join(play_urls),
                }
            ]
        }

    def playerContent(self, flag, id, vipFlags):
        response = self._post_api("/v2/api/vodInfo/epDetail", self._build_payload({"vodEpId": id}))
        candidates = []

        for item in response.get("data", []):
            show_name = item.get("showName")
            resolution = item.get("vodResolution")
            if not show_name or not resolution:
                continue

            play_response = self._post_api(
                "/v2/api/vodInfo/playUrl",
                self._build_payload({"epId": id, "vodResolution": resolution}),
            )
            play_url = play_response.get("data", {}).get("playUrl", "")
            if str(play_url).startswith("http"):
                candidates.append(
                    {
                        "showName": show_name,
                        "vodResolution": resolution,
                        "playUrl": play_url,
                        "score": self._quality_score(show_name, resolution),
                    }
                )

        if not candidates:
            return {"parse": 0, "playUrl": "", "url": ""}

        best = sorted(candidates, key=lambda item: item["score"], reverse=True)[0]

        return {
            "parse": 0,
            "playUrl": "",
            "url": best["playUrl"],
            "header": {
                "User-Agent": "ExoPlayer",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
            },
        }
