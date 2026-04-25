# coding=utf-8
import json
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


CLASS_LIST = [
    {"type_id": "热播", "type_name": "🎬热播"},
    {"type_id": "新剧", "type_name": "🎬新剧"},
    {"type_id": "都市", "type_name": "🎬都市"},
    {"type_id": "穿越", "type_name": "🎬穿越"},
    {"type_id": "重生", "type_name": "🎬重生"},
    {"type_id": "赘婿", "type_name": "🎬赘婿"},
    {"type_id": "逆袭", "type_name": "🎬逆袭"},
    {"type_id": "霸总", "type_name": "🎬霸总"},
    {"type_id": "职场", "type_name": "🎬职场"},
    {"type_id": "异能", "type_name": "🎬异能"},
    {"type_id": "神医", "type_name": "🎬神医"},
    {"type_id": "系统", "type_name": "🎬系统"},
    {"type_id": "总裁", "type_name": "🎬总裁"},
    {"type_id": "豪门", "type_name": "🎬豪门"},
    {"type_id": "神豪", "type_name": "🎬神豪"},
    {"type_id": "校园", "type_name": "🎬校园"},
    {"type_id": "青春", "type_name": "🎬青春"},
    {"type_id": "马甲", "type_name": "🎬马甲"},
    {"type_id": "年代", "type_name": "🎬年代"},
    {"type_id": "闪婚", "type_name": "🎬闪婚"},
    {"type_id": "战神", "type_name": "🎬战神"},
    {"type_id": "女主", "type_name": "🎬女主"},
    {"type_id": "修仙", "type_name": "🎬修仙"},
    {"type_id": "亲情", "type_name": "🎬亲情"},
    {"type_id": "虐恋", "type_name": "🎬虐恋"},
    {"type_id": "追妻", "type_name": "🎬追妻"},
    {"type_id": "萌宝", "type_name": "🎬萌宝"},
    {"type_id": "古风", "type_name": "🎬古风"},
    {"type_id": "传承", "type_name": "🎬传承"},
    {"type_id": "甜宠", "type_name": "🎬甜宠"},
    {"type_id": "奇幻", "type_name": "🎬奇幻"},
    {"type_id": "爱情", "type_name": "🎬爱情"},
    {"type_id": "乡村", "type_name": "🎬乡村"},
    {"type_id": "历史", "type_name": "🎬历史"},
    {"type_id": "王妃", "type_name": "🎬王妃"},
    {"type_id": "高手", "type_name": "🎬高手"},
    {"type_id": "娱乐", "type_name": "🎬娱乐"},
    {"type_id": "联合", "type_name": "🎬联合"},
    {"type_id": "破镜", "type_name": "🎬破镜"},
    {"type_id": "暗恋", "type_name": "🎬暗恋"},
    {"type_id": "民国", "type_name": "🎬民国"},
    {"type_id": "冤家", "type_name": "🎬冤家"},
    {"type_id": "真假", "type_name": "🎬真假"},
    {"type_id": "龙王", "type_name": "🎬龙王"},
    {"type_id": "穿书", "type_name": "🎬穿书"},
    {"type_id": "女帝", "type_name": "🎬女帝"},
    {"type_id": "团宠", "type_name": "🎬团宠"},
    {"type_id": "玄幻", "type_name": "🎬玄幻"},
    {"type_id": "仙侠", "type_name": "🎬仙侠"},
    {"type_id": "青梅", "type_name": "🎬青梅"},
    {"type_id": "悬疑", "type_name": "🎬悬疑"},
    {"type_id": "推理", "type_name": "🎬推理"},
    {"type_id": "皇后", "type_name": "🎬皇后"},
    {"type_id": "替身", "type_name": "🎬替身"},
    {"type_id": "大叔", "type_name": "🎬大叔"},
    {"type_id": "喜剧", "type_name": "🎬喜剧"},
    {"type_id": "剧情", "type_name": "🎬剧情"},
]


class Spider(BaseSpider):
    def __init__(self):
        self.name = "红果短剧"
        self.host = "https://api-v2.cenguigui.cn"
        self.api = self.host + "/api/duanju.html"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        self.classes = CLASS_LIST
        self.filters = {
            "分类": [
                {
                    "key": "area",
                    "name": "分类",
                    "value": CLASS_LIST,
                }
            ]
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        return {"list": self._list_items("热播", 1)}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._list_items(tid, page)
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return {"page": page, "limit": 0, "total": 0, "list": []}
        items = self._list_items(keyword, page)
        return {"page": page, "limit": len(items), "total": len(items), "list": items}

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            if not vod_id:
                continue
            payload = self._get_json(f"{self.api}?id={quote(vod_id)}")
            data = payload.get("data", []) if isinstance(payload, dict) else []
            if not data:
                continue
            first = data[0]
            base_name = self._clean_title(re.sub(r"\s+\d+\s*$", "", str(first.get("title", ""))))
            episodes = []
            for index, item in enumerate(data, start=1):
                play_id = str(item.get("video_id", "")).strip()
                if not play_id:
                    continue
                episode_name = self._clean_title(str(item.get("title", f"第{index}集")))
                episodes.append(f"{episode_name}${play_id}")
            result["list"].append(
                {
                    "vod_id": vod_id,
                    "vod_name": base_name,
                    "vod_pic": str(first.get("cover", "")),
                    "vod_area": "中国",
                    "vod_remarks": f"更新至{len(episodes)}集",
                    "vod_content": f"{base_name} 短剧，共 {len(episodes)} 集",
                    "vod_play_from": "红果短剧",
                    "vod_play_url": "#".join(episodes),
                }
            )
        return result

    def playerContent(self, flag, id, vipFlags):
        try:
            payload = self._get_json(f"{self.api}?video_id={quote(str(id or '').strip())}")
            data = payload.get("data", {}) if isinstance(payload, dict) else {}
            qualities = self._sort_qualities(data.get("qualities", []))
            best = next(
                (item for item in qualities if str(item.get("download_url", "")).strip()),
                {},
            )
            return {
                "parse": 0,
                "jx": 0,
                "url": str(best.get("download_url", "")).strip(),
                "header": {},
            }
        except Exception:
            return {"parse": 0, "jx": 0, "url": "", "header": {}}

    def _list_items(self, name, page):
        payload = self._get_json(f"{self.api}?name={quote(str(name))}&page={int(page)}")
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return [self._map_vod(item) for item in data]

    def _map_vod(self, item):
        total = item.get("totalChapterNum")
        return {
            "vod_id": str(item.get("id", "")),
            "vod_name": self._clean_title(item.get("title", "")),
            "vod_pic": str(item.get("cover", "")),
            "vod_remarks": f"更新至{total}集" if total else "",
        }

    def _clean_title(self, text):
        value = str(text or "")
        value = re.sub(r"[【\[]热播(?:好剧|短剧)?[】\]]", "", value)
        value = re.sub(r"[【\[]新剧(?:热播)?[】\]]", "", value)
        return re.sub(r"\s+", " ", value).strip()

    def _sort_qualities(self, items):
        priority = {"1080p": 3, "sc": 2, "sd": 1}
        return sorted(
            items or [],
            key=lambda item: priority.get(str(item.get("quality", "")), 0),
            reverse=True,
        )

    def _get_json(self, url):
        response = self.fetch(url, headers=dict(self.headers), timeout=10, verify=False)
        if response.status_code != 200:
            return {}
        return json.loads(response.text or "{}")
