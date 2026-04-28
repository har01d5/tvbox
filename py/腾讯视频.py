# coding=utf-8
import json
import re
import sys

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "腾讯视频"
        self.base_host = "https://v.qq.com"
        self.header = {"User-Agent": "PC_UA"}
        self.classes = [
            {"type_id": "choice", "type_name": "精选"},
            {"type_id": "movie", "type_name": "电影"},
            {"type_id": "tv", "type_name": "电视剧"},
            {"type_id": "variety", "type_name": "综艺"},
            {"type_id": "cartoon", "type_name": "动漫"},
            {"type_id": "child", "type_name": "少儿"},
            {"type_id": "doco", "type_name": "纪录片"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def _headers(self):
        return dict(self.header)

    def _parse_list_items(self, html, with_channel=False, channel_id=""):
        videos = []
        list_items = re.findall(
            r'<div[^>]*class=["\']?list_item["\']?[^>]*>([\s\S]*?)</div>',
            str(html or ""),
            re.I,
        )
        for item in list_items:
            title_match = re.search(r'<img[^>]*alt=["\']?([^"\']*)["\']?', item, re.I)
            pic_match = re.search(r'<img[^>]*src=["\']?([^"\'\s>]+)["\']?', item, re.I)
            desc_values = [
                re.sub(r"<[^>]*>", "", value).strip()
                for value in re.findall(r'<a[^>]*>([\s\S]*?)</a>', item, re.I)
            ]
            url_match = re.search(r'<a[^>]*data-float=["\']?([^"\'\s>]+)["\']?', item, re.I)
            if not title_match or not pic_match:
                continue
            source_id = url_match.group(1) if url_match else ""
            vod_id = f"{channel_id}${source_id}" if with_channel else source_id
            videos.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title_match.group(1) or "",
                    "vod_pic": pic_match.group(1) or "",
                    "vod_remarks": next((value for value in reversed(desc_values) if value), ""),
                }
            )
        return videos

    def homeContent(self, filter):
        url = (
            f"{self.base_host}/x/bu/pagesheet/list?_all=1&append=1&channel=cartoon"
            "&listpage=1&offset=0&pagesize=21&iarea=-1&sort=18"
        )
        response = self.fetch(url, headers=self._headers())
        videos = self._parse_list_items(getattr(response, "text", ""), with_channel=False)
        return {"class": self.classes, "list": videos[:20]}

    def homeVideoContent(self):
        return {"list": self.homeContent(False).get("list", [])}

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 1, "jx": 1, "url": id, "header": self._headers()}

    def _safe_json(self, text, strip_prefix="", strip_suffix=""):
        raw = str(text or "")
        if strip_prefix and raw.startswith(strip_prefix):
            raw = raw[len(strip_prefix):]
        if strip_suffix and raw.endswith(strip_suffix):
            raw = raw[: -len(strip_suffix)]
        return json.loads(raw) if raw else {}

    def _join_text_list(self, values):
        parts = []
        for item in values or []:
            if isinstance(item, (list, tuple)):
                text = next((str(value).strip() for value in item if str(value).strip()), "")
            else:
                text = str(item).strip()
            if text:
                parts.append(text)
        return ",".join(parts)

    def _get_batch_video_info(self, vids):
        results = []
        for start in range(0, len(vids or []), 30):
            batch = vids[start:start + 30]
            if not batch:
                continue
            url = (
                "https://union.video.qq.com/fcgi-bin/data?otype=json&tid=1804&appid=20001238"
                "&appkey=6c03bbe9658448a4&union_platform=1&idlist=" + ",".join(batch)
            )
            response = self.fetch(url, headers=self._headers())
            payload = self._safe_json(getattr(response, "text", ""), strip_prefix="QZOutputJson=", strip_suffix=";")
            for item in payload.get("results", []):
                fields = item.get("fields", {})
                category_map = fields.get("category_map", [])
                results.append(
                    {
                        "vid": fields.get("vid", ""),
                        "title": fields.get("title", ""),
                        "type": category_map[1] if len(category_map) > 1 else "",
                    }
                )
        return results

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        offset = (page - 1) * 21
        params = [
            "_all=1",
            "append=1",
            f"channel={tid}",
            "listpage=1",
            f"offset={offset}",
            "pagesize=21",
            "iarea=-1",
        ]
        options = dict(extend or {})
        if options.get("sort"):
            params.append(f"sort={options['sort']}")
        if options.get("iyear"):
            params.append(f"iyear={options['iyear']}")
        if options.get("year"):
            params.append(f"year={options['year']}")
        if options.get("type"):
            params.append(f"itype={options['type']}")
        if options.get("feature"):
            params.append(f"ifeature={options['feature']}")
        if options.get("area"):
            params.append(f"iarea={options['area']}")
        if options.get("itrailer"):
            params.append(f"itrailer={options['itrailer']}")
        if options.get("sex"):
            params.append(f"gender={options['sex']}")
        url = f"{self.base_host}/x/bu/pagesheet/list?" + "&".join(params)
        response = self.fetch(url, headers=self._headers())
        return {
            "list": self._parse_list_items(getattr(response, "text", ""), with_channel=True, channel_id=str(tid)),
            "page": page,
            "pagecount": 9999,
            "limit": 21,
            "total": 999999,
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids or []:
            parts = str(raw_id).split("$", 1)
            target_cid = parts[1] if len(parts) > 1 else parts[0]
            url = f"https://node.video.qq.com/x/api/float_vinfo2?cid={target_cid}"
            try:
                payload = self.fetch(url, headers=self._headers()).json()
            except Exception:
                continue
            cover = ((payload.get("c") or {}).get("pic") or "")
            vod = {
                "vod_id": raw_id,
                "vod_name": ((payload.get("c") or {}).get("title") or ""),
                "type_name": self._join_text_list(payload.get("typ", []) or []),
                "vod_actor": self._join_text_list(payload.get("nam", []) or []),
                "vod_year": ((payload.get("c") or {}).get("year") or ""),
                "vod_content": ((payload.get("c") or {}).get("description") or ""),
                "vod_remarks": payload.get("rec", "") or "",
                "vod_pic": cover if cover.startswith("http") else self.base_host + cover,
                "vod_play_from": "",
                "vod_play_url": "",
            }
            video_ids = ((payload.get("c") or {}).get("video_ids") or [])
            if video_ids:
                detail_map = {item.get("vid"): item for item in self._get_batch_video_info(video_ids)}
                play_items = []
                for vid in video_ids:
                    item = detail_map.get(vid, {"title": "", "type": ""})
                    display_title = (item.get("title") or "选集").strip()
                    if re.fullmatch(r"\d+", display_title):
                        display_title = f"第{display_title}集"
                    play_items.append(f"{display_title}${self.base_host}/x/cover/{target_cid}/{vid}.html")
                vod["vod_play_from"] = "腾讯视频"
                vod["vod_play_url"] = "#".join(play_items)
            result["list"].append(vod)
        return result

    def searchContent(self, key, quick, pg="1"):
        url = (
            "https://pbaccess.video.qq.com/trpc.videosearch.mobile_search."
            "MultiTerminalSearch/MbSearch?vplatform=2"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/98.0.4758.139 Safari/537.36"
            ),
            "Content-Type": "application/json",
            "Origin": "https://v.qq.com",
            "Referer": "https://v.qq.com/",
        }
        payload = {
            "version": "25042201",
            "clientType": 1,
            "query": key,
            "pagenum": int(pg) - 1,
            "pagesize": 30,
            "extraInfo": {
                "isNewMarkLabel": "1",
                "multi_terminal_pc": "1",
                "themeType": "1",
            },
        }
        try:
            response = self.post(url, headers=headers, json=payload)
            data = response.json()
        except Exception:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 30, "total": 0}

        videos = []

        def process_item(item):
            if not item or not item.get("doc") or not item["doc"].get("id") or not item.get("videoInfo"):
                return
            if len(item["doc"]["id"]) <= 11:
                return
            info = item["videoInfo"]
            videos.append(
                {
                    "vod_id": item["doc"]["id"],
                    "vod_name": re.sub(r"</?em>", "", info.get("title", "")),
                    "vod_pic": info.get("imgUrl", ""),
                    "vod_remarks": info.get("firstLine") or info.get("secondLine") or "",
                }
            )

        for item in (((data.get("data") or {}).get("normalList") or {}).get("itemList") or []):
            process_item(item)
        for area in ((data.get("data") or {}).get("areaBoxList") or []):
            for item in (area.get("itemList") or []):
                process_item(item)

        page = int(pg)
        return {
            "list": videos,
            "page": page,
            "pagecount": page + 1 if len(videos) >= 20 else page,
            "limit": 30,
            "total": 999 if videos else 0,
        }
