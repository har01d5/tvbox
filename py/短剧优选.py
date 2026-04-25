# coding=utf-8
import hashlib
import json
import re
import sys
import time
from urllib.parse import quote, urlencode

from base.spider import Spider as BaseSpider

sys.path.append("..")


CHAR_MAP = {
    "+": "P", "/": "X", "0": "M", "1": "U", "2": "l", "3": "E", "4": "r", "5": "Y",
    "6": "W", "7": "b", "8": "d", "9": "J", "A": "9", "B": "s", "C": "a", "D": "I",
    "E": "0", "F": "o", "G": "y", "H": "_", "I": "H", "J": "G", "K": "i", "L": "t",
    "M": "g", "N": "N", "O": "A", "P": "8", "Q": "F", "R": "k", "S": "3", "T": "h",
    "U": "f", "V": "R", "W": "q", "X": "C", "Y": "4", "Z": "p", "a": "m", "b": "B",
    "c": "O", "d": "u", "e": "c", "f": "6", "g": "K", "h": "x", "i": "5", "j": "T",
    "k": "-", "l": "2", "m": "z", "n": "S", "o": "Z", "p": "1", "q": "V", "r": "v",
    "s": "j", "t": "Q", "u": "7", "v": "D", "w": "w", "x": "n", "y": "L", "z": "e",
}

QM_KEYS = "d3dGiJc651gSQ8w1"

XIFAN_SESSION = (
    "eyJpbmZvIjp7InVpZCI6IiIsInJ0IjoiMTc0MDY1ODI5NCIsInVuIjoiT1BHXzFlZGQ5OTZhNjQ3"
    "ZTQ1MjU4Nzc1MTE2YzFkNzViN2QwIiwiZnQiOiIxNzQwNjU4Mjk0In19"
)

XIFAN_FEEDS = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
    "eyJ1dHlwIjowLCJidWlkIjoxNjMzOTY4MTI2MTQ4NjQxNTM2LCJhdWQiOiJkcmFtYSIsInZlciI6MiwicmF0IjoxNzQwNjU4Mjk0LC"
    "J1bm0iOiJPUEdfMWVkZDk5NmE2NDdlNDUyNTg3NzUxMTY2YzFkNzViN2QwIiwiZXhwIjoxNzQxMjYzMDk0LCJkYyI6Imd6cXkifQ."
    "JS3QY6ER0P2cQSxAE_OGKSMIWNAMsYUZ3mJTnEpf-Rc"
)

XINGXING_HOST = "http://read.api.duodutek.com"
XINGXING_UA = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/50.0.2661.87 Safari/537.36"
)
XINGXING_COMMON_PARAMS = {
    "productId": "2a8c14d1-72e7-498b-af23-381028eb47c0",
    "vestId": "2be070e0-c824-4d0e-a67a-8f688890cadb",
    "channel": "oppo19",
    "osType": "android",
    "version": "20",
    "token": "202509271001001446030204698626",
}


class Spider(BaseSpider):
    def __init__(self):
        self.name = "短剧优选"
        self.xingya_headers = {}
        self.default_headers = {
            "User-Agent": "okhttp/3.12.11",
            "Content-Type": "application/json; charset=utf-8",
        }
        self.platforms = {
            "七猫": {
                "host": "https://api-store.qmplaylet.com",
                "url1": "/api/v1/playlet/index",
                "url2": "https://api-read.qmplaylet.com/player/api/v1/playlet/info",
                "search": "/api/v1/playlet/search",
            },
            "星芽": {
                "host": "https://app.whjzjx.cn",
                "url1": "/cloud/v2/theater/home_page?theater_class_id",
                "url2": "/v2/theater_parent/detail",
                "search": "/v3/search",
                "login": "https://u.shytkjgs.com/user/v1/account/login",
            },
            "星星": {
                "host": XINGXING_HOST,
                "url1": "/novel-api/app/pageModel/getResourceById",
                "url2": "/novel-api/basedata/book/getChapterList",
            },
            "西饭": {
                "host": "https://xifan-api-cn.youlishipin.com",
                "url1": "/xifan/drama/portalPage",
                "url2": "/xifan/drama/getDuanjuInfo",
                "search": "/xifan/search/getSearchList",
            },
            # "锦鲤": {
            #     "host": "https://api.jinlidj.com",
            #     "search": "/api/search",
            #     "url2": "/api/detail",
            # },
            "红果": {
                "host": "https://api-v2.cenguigui.cn",
                "url1": "/api/duanju/api.php?classname",
                "url2": "/api/duanju/api.php?book_id",
                "search": "/api/duanju/api.php?name",
            },
            "短剧网": {
                "host": "https://sm3.cc",
            },
        }
        self.classes = [
            {"type_id": "七猫", "type_name": "七猫短剧"},
            {"type_id": "星芽", "type_name": "星芽短剧"},
            {"type_id": "星星", "type_name": "星星短剧"},
            {"type_id": "西饭", "type_name": "西饭短剧"},
            {"type_id": "锦鲤", "type_name": "锦鲤短剧"},
            {"type_id": "红果", "type_name": "红果短剧"},
            {"type_id": "短剧网", "type_name": "短剧网"},
        ]
        self.filters = {
            "七猫": [self._filter_area("分类", [
                ("全部", "0"), ("新剧", "-1"), ("都市情感", "1273"), ("古装", "1272"),
                ("都市", "571"), ("玄幻仙侠", "1286"), ("青春校园", "1288"), ("年代", "572"),
                ("武侠", "371"), ("乡村", "590"), ("科幻", "594"), ("民国", "573"),
                ("奇幻", "570"), ("末世", "556"), ("二次元", "1289"), ("逆袭", "400"),
                ("复仇", "795"), ("重生", "784"), ("穿越", "373"), ("女性成长", "1294"),
                ("家庭", "670"), ("闪婚", "480"), ("强者回归", "402"), ("打脸虐渣", "716"),
                ("追妻火葬场", "715"), ("马甲", "558"), ("职场", "724"), ("高手下山", "1299"),
                ("穿书", "338"), ("系统", "787"), ("娱乐明星", "1295"), ("异能", "727"),
                ("致富", "492"), ("种田经商", "1291"), ("伦理", "1293"), ("社会话题", "1290"),
                ("脑洞", "526"), ("豪门总裁", "624"), ("萌宝", "356"), ("真假千金", "812"),
                ("战神", "527"), ("赘婿", "36"), ("神豪", "37"), ("小人物", "1296"),
                ("神医", "1269"), ("权谋", "790"), ("女帝", "617"), ("团宠", "545"),
                ("欢喜冤家", "464"), ("替身", "712"), ("银发", "1297"), ("兵王", "28"),
                ("虐恋", "16"), ("甜宠", "21"), ("搞笑", "793"), ("宅斗", "342"),
                ("宫斗", "343"), ("悬疑", "27"), ("商战", "723"), ("灵异", "1287"),
            ])],
            "星芽": [self._filter_area("分类", [
                ("剧场", "1"), ("热播", "2"), ("新剧", "3"),
                ("阳光剧场", "5"), ("星选好剧", "7"), ("会员专享", "8"),
            ])],
            "星星": [self._filter_area("分类", [
                ("甜宠", "1287"), ("逆袭", "1288"), ("热血", "1289"),
                ("现代", "1290"), ("古代", "1291"),
            ])],
            "西饭": [self._filter_area("分类", [
                ("全部", ""), ("都市", "68@都市"), ("青春", "68@青春"),
                ("现代言情", "81@现代言情"), ("豪门", "81@豪门"),
                ("大女主", "80@大女主"), ("逆袭", "79@逆袭"),
                ("打脸虐渣", "79@打脸虐渣"), ("穿越", "81@穿越"),
            ])],
            "锦鲤": [self._filter_area("分类", [
                ("全部", ""), ("推荐", "1"), ("霸总", "2"), ("战神", "3"),
                ("神医", "4"), ("虐恋", "5"), ("萌宝", "6"), ("逆袭", "7"),
                ("穿越", "8"), ("古装", "9"), ("重生", "10"),
            ])],
            "红果": [self._filter_area("分类", [
                ("逆袭", "逆袭"), ("霸总", "霸总"), ("现代言情", "现代言情"),
                ("打脸虐渣", "打脸虐渣"), ("豪门恩怨", "豪门恩怨"),
                ("神豪", "神豪"), ("马甲", "马甲"), ("都市日常", "都市日常"),
                ("战神归来", "战神归来"), ("小人物", "小人物"),
                ("女性成长", "女性成长"), ("大女主", "大女主"),
                ("穿越", "穿越"), ("都市修仙", "都市修仙"),
                ("强者回归", "强者回归"), ("亲情", "亲情"), ("古装", "古装"),
                ("重生", "重生"), ("闪婚", "闪婚"), ("赘婿逆袭", "赘婿逆袭"),
                ("虐恋", "虐恋"), ("追妻", "追妻"), ("天下无敌", "天下无敌"),
                ("家庭伦理", "家庭伦理"), ("萌宝", "萌宝"), ("古风权谋", "古风权谋"),
                ("职场", "职场"), ("奇幻脑洞", "奇幻脑洞"), ("异能", "异能"),
                ("无敌神医", "无敌神医"), ("古风言情", "古风言情"),
                ("传承觉醒", "传承觉醒"), ("现言甜宠", "现言甜宠"),
                ("奇幻爱情", "奇幻爱情"), ("乡村", "乡村"),
                ("历史古代", "历史古代"), ("王妃", "王妃"),
                ("高手下山", "高手下山"), ("娱乐圈", "娱乐圈"),
                ("强强联合", "强强联合"), ("破镜重圆", "破镜重圆"),
                ("暗恋成真", "暗恋成真"), ("民国", "民国"),
                ("欢喜冤家", "欢喜冤家"), ("系统", "系统"),
                ("真假千金", "真假千金"), ("龙王", "龙王"), ("校园", "校园"),
                ("穿书", "穿书"), ("女帝", "女帝"), ("团宠", "团宠"),
                ("年代爱情", "年代爱情"), ("玄幻仙侠", "玄幻仙侠"),
                ("青梅竹马", "青梅竹马"), ("悬疑推理", "悬疑推理"),
                ("皇后", "皇后"), ("替身", "替身"), ("大叔", "大叔"),
                ("喜剧", "喜剧"), ("剧情", "剧情"),
            ])],
            "短剧网": [self._filter_area("分类", [
                ("短剧大全", "1"), ("更新短剧", "2"),
            ])],
        }
        self.filter_defaults = {
            "七猫": {"area": "0"}, "星芽": {"area": "1"}, "星星": {"area": "1287"},
            "西饭": {"area": ""}, "锦鲤": {"area": ""}, "红果": {"area": "逆袭"},
            "短剧网": {"area": "1"},
        }

    def init(self, extend=""):
        self._init_xingya_token()
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        ext = extend or {}
        area = ext.get("area") or self.filter_defaults.get(tid, {}).get("area", "")
        try:
            items = self._fetch_category(tid, page, area)
        except Exception as e:
            self.log(f"categoryContent failed ({tid}): {e}")
            items = []
        pagecount = page + 1 if items else page
        return {
            "list": items,
            "page": page,
            "total": pagecount * 30 + len(items) if items else 0,
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            parts = raw_id.split("@", 1)
            platform = parts[0]
            detail_id = parts[1] if len(parts) > 1 else ""
            try:
                vod = self._fetch_detail(platform, detail_id, raw_id)
            except Exception as e:
                self.log(f"detailContent failed ({platform}): {e}")
                vod = {
                    "vod_id": raw_id,
                    "vod_name": f"{platform}：详情加载失败",
                    "vod_remarks": str(e),
                }
            result["list"].append(vod)
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = key.strip()
        if not keyword:
            return {"list": [], "page": page, "pagecount": 0, "total": 0}
        results = self._aggregate_search(keyword, page)
        filtered = [
            r for r in results
            if keyword.lower() in (r.get("vod_name") or "").lower()
        ]
        limit = 30
        offset = (page - 1) * limit
        sliced = filtered[offset:offset + limit]
        total_pages = max(1, (len(filtered) + limit - 1) // limit) if filtered else 0
        return {
            "list": sliced,
            "page": page,
            "pagecount": total_pages,
            "total": len(filtered),
        }

    def playerContent(self, flag, id, vipFlags):
        if "红果" in flag:
            res = self._get_json("https://api-v2.cenguigui.cn/api/duanju/api.php?video_id=" + id)
            return {"parse": 0, "jx": 0, "url": res.get("url")}
        if "锦鲤" in flag:
            return self._play_jinli(id)
        if "星芽" in flag or "星星" in flag or "七猫" in flag or "西饭" in flag:
            return {"parse": 0, "jx": 0, "url": id}
        if "短剧网" in flag:
            return {"parse": 0, "jx": 0, "url": id}
        return {"parse": 0, "jx": 0, "url": id}

    # --- helpers ---

    @staticmethod
    def _filter_area(name, values):
        return {"key": "area", "name": name, "value": [{"n": n, "v": v} for n, v in values]}

    def _s(self, val):
        return "" if val is None else str(val)

    def _clean(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _get_json(self, url, headers=None, params=None, timeout=6):
        h = dict(self.default_headers)
        if headers:
            h.update(headers)
        rsp = self.fetch(url, headers=h, params=params, timeout=timeout, verify=False)
        if rsp.status_code != 200:
            return {}
        return rsp.json()

    def _post_json(self, url, body=None, headers=None, timeout=6):
        h = dict(self.default_headers)
        if headers:
            h.update(headers)
        rsp = self.post(url, json=body, headers=h, timeout=timeout, verify=False)
        if rsp.status_code != 200:
            return {}
        return rsp.json()

    def _get_text(self, url, headers=None, timeout=6):
        h = dict(self.default_headers)
        if headers:
            h.update(headers)
        rsp = self.fetch(url, headers=h, timeout=timeout, verify=False)
        if rsp.status_code != 200:
            return ""
        return rsp.text or ""

    # --- 七猫 signing ---

    @staticmethod
    def _md5(text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _qm_params_and_sign(self):
        session_id = str(int(time.time() * 1000))
        data = {
            "static_score": "0.8", "uuid": "00000000-7fc7-08dc-0000-000000000000",
            "device-id": "20250220125449b9b8cac84c2dd3d035c9052a2572f7dd0122edde3cc42a70",
            "mac": "", "sourceuid": "aa7de295aad621a6", "refresh-type": "0",
            "model": "22021211RC", "wlb-imei": "", "client-id": "aa7de295aad621a6",
            "brand": "Redmi", "oaid": "", "oaid-no-cache": "", "sys-ver": "12",
            "trusted-id": "", "phone-level": "H", "imei": "",
            "wlb-uid": "aa7de295aad621a6", "session-id": session_id,
        }
        import base64
        b64 = base64.b64encode(json.dumps(data, separators=(",", ":")).encode("utf-8")).decode("utf-8")
        qm_params = "".join(CHAR_MAP.get(c, c) for c in b64)
        sign_str = (
            f"AUTHORIZATION=app-version=10001application-id=com.duoduo.read"
            f"channel=unknownis-white=net-env=5platform=android"
            f"qm-params={qm_params}reg={QM_KEYS}"
        )
        return qm_params, self._md5(sign_str)

    def _qm_headers(self):
        qm_params, sign = self._qm_params_and_sign()
        return {
            "net-env": "5", "reg": "", "channel": "unknown", "is-white": "",
            "platform": "android", "application-id": "com.duoduo.read",
            "authorization": "", "app-version": "10001",
            "user-agent": "webviewversion/0", "qm-params": qm_params, "sign": sign,
        }

    # --- 星芽/七星 token ---

    def _init_xingya_token(self):
        if self.xingya_headers:
            return
        try:
            plat = self.platforms["星芽"]
            body = {"device": "24250683a3bdb3f118dff25ba4b1cba1a"}
            h = {"User-Agent": "okhttp/4.10.0", "platform": "1", "Content-Type": "application/json"}
            res = self._post_json(plat["login"], body=body, headers=h)
            token = ""
            data = res.get("data") or {}
            if isinstance(data, dict):
                token = data.get("token") or (data.get("data") or {}).get("token") or ""
            if token:
                self.xingya_headers = dict(self.default_headers)
                self.xingya_headers["authorization"] = token
        except Exception:
            pass

    # --- 西饭 URL builder ---

    def _xifan_params(self, extra=None):
        ts = int(time.time())
        p = {
            "quickEngineVersion": -1, "scene": "", "categoryVersion": 1,
            "density": 1.5, "pageID": "page_theater", "version": 2001001,
            "androidVersionCode": 28,
            "requestId": f"{ts}aa498144140ef297",
            "appId": "drama", "teenMode": False, "userBaseMode": False,
            "session": XIFAN_SESSION, "feedssession": XIFAN_FEEDS,
        }
        if extra:
            p.update(extra)
        return p

    def _xingxing_headers(self):
        return {"User-Agent": XINGXING_UA}

    def _xingxing_url(self, path, params=None):
        query = urlencode(dict(XINGXING_COMMON_PARAMS, **(params or {})))
        return f"{XINGXING_HOST}{path}?{query}"

    def _normalize_xingxing_play_url(self, value):
        play_url = self._s(value).strip()
        if play_url.startswith("http://img.novel.wsljf.xyz/"):
            return "https://" + play_url[len("http://"):]
        return play_url

    # --- category per platform ---

    def _fetch_category(self, tid, page, area):
        plat = self.platforms.get(tid)
        if not plat:
            return []
        handler = {
            "七猫": self._cat_qimao,
            "星芽": self._cat_xingya,
            "星星": self._cat_xingxing,
            "西饭": self._cat_xifan,
            "锦鲤": self._cat_jinli,
            "红果": self._cat_tianquan,
            "短剧网": self._cat_duanjuwang,
        }.get(tid)
        if handler:
            return handler(plat, page, area)
        return []

    def _cat_qimao(self, plat, page, area):
        sign_str = f"operation=1playlet_privacy=1tag_id={area}{QM_KEYS}"
        sign = self._md5(sign_str)
        url = f"{plat['host']}{plat['url1']}?tag_id={area}&playlet_privacy=1&operation=1&sign={sign}"
        res = self._get_json(url, headers=self._qm_headers())
        items = []
        for it in (res.get("data") or {}).get("list") or []:
            items.append({
                "vod_id": f"七猫@{quote(str(it.get('playlet_id', '')))}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("image_link")),
                "vod_remarks": f"{it.get('total_episode_num', 0)}集",
            })
        return items

    def _cat_xingya(self, plat, page, area):
        url = f"{plat['host']}{plat['url1']}={area}&type=1&class2_ids=0&page_num={page}&page_size=24"
        res = self._get_json(url, headers=self.xingya_headers)
        items = []
        for it in (res.get("data") or {}).get("list") or []:
            tid = it.get("theater", {}).get("id", "")
            detail_url = f"{plat['host']}{plat['url2']}?theater_parent_id={tid}"
            items.append({
                "vod_id": f"星芽@{detail_url}",
                "vod_name": self._s(it.get("theater", {}).get("title")),
                "vod_pic": self._s(it.get("theater", {}).get("cover_url")),
                "vod_remarks": f"{it.get('theater', {}).get('total', 0)}集",
            })
        return items

    def _cat_xingxing(self, plat, page, area):
        url = self._xingxing_url(
            plat["url1"],
            {"resourceId": area, "pageNum": str(page), "pageSize": "10"},
        )
        res = self._get_json(url, headers=self._xingxing_headers())
        items = []
        for it in (res.get("data") or {}).get("datalist") or []:
            book_id = self._s(it.get("id")).strip()
            name = self._s(it.get("name")).strip()
            intro = self._s(it.get("introduction")).strip()
            items.append({
                "vod_id": f"星星@{book_id}@@{name}@@{intro}",
                "vod_name": name,
                "vod_pic": self._s(it.get("icon")).strip(),
                "vod_remarks": f"{self._s(it.get('heat')).strip()}万播放" if self._s(it.get("heat")).strip() else "",
            })
        return items

    def _cat_xifan(self, plat, page, area):
        type_id, type_name = (area.split("@", 1) + [""])[:2]
        params = self._xifan_params({
            "reqType": "aggregationPage",
            "offset": (page - 1) * 24,
            "categoryId": type_id,
            "categoryNames": type_name,
        })
        url = f"{plat['host']}{plat['url1']}?{urlencode(params)}"
        res = self._get_json(url)
        items = []
        for soup in (res.get("result") or {}).get("elements") or []:
            for vod in soup.get("contents") or []:
                dj = vod.get("duanjuVo") or {}
                items.append({
                    "vod_id": f"西饭@{dj.get('duanjuId', '')}#{dj.get('source', '')}",
                    "vod_name": self._s(dj.get("title")),
                    "vod_pic": self._s(dj.get("coverImageUrl")),
                    "vod_remarks": f"{dj.get('total', 0)}集",
                })
        return items

    def _cat_jinli(self, plat, page, area):
        body = {"page": page, "limit": 24, "type_id": area, "year": "", "keyword": ""}
        res = self._post_json(f"{plat['host']}{plat['search']}", body=body)
        items = []
        for it in (res.get("data") or {}).get("list") or []:
            items.append({
                "vod_id": f"锦鲤@{it.get('vod_id', '')}",
                "vod_name": self._s(it.get("vod_name")),
                "vod_pic": self._s(it.get("vod_pic")),
                "vod_remarks": f"{it.get('vod_total', 0)}集",
            })
        return items

    def _cat_weiguan(self, plat, page, area):
        body = {
            "audience": "全部受众", "page": page, "pageSize": 30,
            "searchWord": "", "subject": area or "全部主题",
        }
        res = self._post_json(f"{plat['host']}{plat['search']}", body=body)
        items = []
        for it in res.get("data") or []:
            items.append({
                "vod_id": f"围观@{it.get('oneId', '')}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("vertPoster")),
                "vod_remarks": f"集数:{it.get('episodeCount', 0)}",
            })
        return items

    def _cat_juwang(self, plat, page, area):
        category = area or "/all/"
        if page == 1:
            url = f"{plat['host']}{category}"
        else:
            url = f"{plat['host']}{category}page/{page}/"
        html = self._get_text(url)
        root = self.html(html)
        if root is None:
            return []
        items = []
        for li in root.xpath("//section[contains(@class,'container')]//li"):
            name_el = li.xpath(".//img/@alt")
            href_el = li.xpath(".//a[contains(@class,'image-line')]/@href")
            src_el = li.xpath(".//img/@src")
            remark_el = li.xpath(".//*[contains(@class,'remarks')]/text()")
            name = self._s(name_el[0]) if name_el else ""
            href = self._s(href_el[0]) if href_el else ""
            pic = self._s(src_el[0]) if src_el else ""
            remark = self._s(remark_el[0]).strip() if remark_el else ""
            if href:
                items.append({
                    "vod_id": f"剧王@{href}",
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remark,
                })
        return items

    def _cat_qixing(self, plat, page, area):
        url = f"{plat['host']}{plat['url1']}={area}&page_num={page}&page_size=24"
        res = self._get_json(url, headers=self.xingya_headers)
        items = []
        for it in (res.get("data") or {}).get("list") or []:
            theater = it.get("theater") or {}
            detail_url = f"{plat['host']}{plat['url2']}?theater_parent_id={theater.get('id', '')}"
            items.append({
                "vod_id": f"七星@{detail_url}",
                "vod_name": self._s(theater.get("title")),
                "vod_pic": self._s(theater.get("cover_url")),
                "vod_remarks": f"{theater.get('total', 0)}集",
            })
        return items

    def _cat_tianquan(self, plat, page, area):
        url = f"{plat['host']}{plat['url1']}={area}&offset={page}"
        res = self._get_json(url)
        items = []
        for it in res.get("data") or []:
            items.append({
                "vod_id": f"红果@{it.get('book_id', '')}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("cover")),
                "vod_remarks": self._s(it.get("sub_title")),
            })
        return items

    def _cat_duanjuwang(self, plat, page, area):
        host = plat["host"]
        url = f"{host}/?cate={area or '1'}&page={page}"
        html = self._get_text(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
            "Referer": host + "/",
        })
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//li[contains(@class,'col-6')]"):
            anchors = card.xpath(".//h3[contains(@class,'f-14')]//a[@href]")
            if not anchors:
                continue
            anchor = anchors[0]
            name = self._clean("".join(anchor.xpath(".//text()")))
            href = self._s((anchor.xpath("./@href") or [""])[0]).strip()
            if not name or not href:
                continue
            full_url = href if href.startswith("http") else host + href
            if full_url in seen:
                continue
            seen.add(full_url)
            pic = self._s((card.xpath(".//img[contains(@class,'lazy')]/@data-original") or [""])[0])
            if pic and not pic.startswith(("http://", "https://", "//")):
                pic = host + pic
            elif pic.startswith("//"):
                pic = "https:" + pic
            items.append({
                "vod_id": f"短剧网@{full_url}",
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": "",
            })
        return items

    # --- detail per platform ---

    def _fetch_detail(self, platform, detail_id, raw_id):
        plat = self.platforms.get(platform)
        if not plat:
            return {"vod_id": raw_id, "vod_name": "未知平台"}
        handler = {
            "七猫": self._detail_qimao,
            "星芽": self._detail_xingya,
            "星星": self._detail_xingxing,
            "西饭": self._detail_xifan,
            "锦鲤": self._detail_jinli,
            "红果": self._detail_tianquan,
            "短剧网": self._detail_duanjuwang,
        }.get(platform)
        if handler:
            return handler(plat, detail_id, raw_id)
        return {"vod_id": raw_id, "vod_name": "未实现"}

    def _detail_qimao(self, plat, detail_id, raw_id):
        did = __import__("urllib.parse", fromlist=["unquote"]).unquote(detail_id)
        sign = self._md5(f"playlet_id={did}{QM_KEYS}")
        url = f"{plat['url2']}?playlet_id={did}&sign={sign}"
        res = self._get_json(url, headers=self._qm_headers())
        data = res.get("data") or {}
        play_list = data.get("play_list") or []
        play_urls = "#".join(
            f"{it.get('sort', '')}${it.get('video_url', '')}" for it in play_list
        )
        return {
            "vod_id": raw_id,
            "vod_name": self._s(data.get("title")),
            "vod_pic": self._s(data.get("image_link")),
            "vod_remarks": f"{self._s(data.get('tags'))} {data.get('total_episode_num', 0)}集",
            "vod_content": self._s(data.get("intro")),
            "vod_play_from": "七猫短剧",
            "vod_play_url": play_urls,
        }

    def _detail_xingya(self, plat, detail_id, raw_id):
        url = detail_id
        res = self._get_json(url, headers=self.xingya_headers)
        data = res.get("data") or {}
        theaters = data.get("theaters") or []
        play_urls = "#".join(
            f"{it.get('num', '')}${it.get('son_video_url', '')}" for it in theaters
        )
        return {
            "vod_id": raw_id,
            "vod_name": self._s(data.get("title")),
            "vod_pic": self._s(data.get("cover_url")),
            "vod_content": self._s(data.get("introduction")),
            "vod_remarks": self._s(data.get("desc_tags")),
            "vod_play_from": "星芽短剧",
            "vod_play_url": play_urls,
        }

    def _detail_xingxing(self, plat, detail_id, raw_id):
        book_id, name, intro = (detail_id.split("@@", 2) + ["", ""])[:3]
        url = self._xingxing_url(plat["url2"], {"bookId": book_id})
        res = self._get_json(url, headers=self._xingxing_headers())
        episodes = []
        for index, chapter in enumerate(res.get("data") or [], start=1):
            chapter_name = self._s(chapter.get("chapterName")).strip() or f"第{index}集"
            play_url = ""
            for play_group in chapter.get("shortPlayList") or []:
                for play in play_group.get("chapterShortPlayVoList") or []:
                    play_url = self._normalize_xingxing_play_url(play.get("shortPlayUrl"))
                    if play_url:
                        break
                if play_url:
                    break
            if play_url:
                episodes.append(f"{chapter_name}${play_url}")
        return {
            "vod_id": raw_id,
            "vod_name": name,
            "vod_content": intro,
            "vod_remarks": f"共{len(episodes)}集" if episodes else "",
            "vod_play_from": "星星短剧",
            "vod_play_url": "#".join(episodes),
        }

    def _detail_xifan(self, plat, detail_id, raw_id):
        duanju_id, source = detail_id.split("#", 1) if "#" in detail_id else (detail_id, "")
        params = self._xifan_params({
            "duanjuId": duanju_id, "source": source, "openFrom": "homescreen",
            "pageID": "page_inner_flow",
        })
        url = f"{plat['host']}{plat['url2']}?{urlencode(params)}"
        res = self._get_json(url)
        data = res.get("result") or {}
        episodes = data.get("episodeList") or []
        play_urls = "#".join(
            f"{ep.get('index', '')}${ep.get('playUrl', '')}" for ep in episodes
        )
        total = data.get("total", 0)
        status = data.get("updateStatus", "")
        remark = f"{total}集 已完结" if status == "over" else f"更新{total}集"
        return {
            "vod_id": raw_id,
            "vod_name": self._s(data.get("title")),
            "vod_pic": self._s(data.get("coverImageUrl")),
            "vod_content": self._s(data.get("desc")),
            "vod_remarks": remark,
            "vod_play_from": "西饭短剧",
            "vod_play_url": play_urls or "暂无播放地址$0",
        }

    def _detail_jinli(self, plat, detail_id, raw_id):
        url = f"{plat['host']}{plat['url2']}/{detail_id}"
        res = self._get_json(url)
        data = res.get("data") or {}
        player = data.get("player") or {}
        play_urls = "#".join(f"{name}${url}" for name, url in player.items())
        return {
            "vod_id": raw_id,
            "vod_name": self._s(data.get("vod_name")),
            "vod_pic": self._s(data.get("vod_pic")),
            "vod_remarks": self._s(data.get("vod_remarks")),
            "vod_content": self._s(data.get("vod_blurb")),
            "type_name": self._s(data.get("vod_class")),
            "vod_play_from": "锦鲤短剧",
            "vod_play_url": play_urls,
        }

    def _detail_weiguan(self, plat, detail_id, raw_id):
        url = f"{plat['host']}{plat['url2']}?oneId={detail_id}&page=1&pageSize=1000"
        res = self._get_json(url)
        data = res.get("data") or []
        if not data:
            return {"vod_id": raw_id, "vod_name": "无数据"}
        first = data[0]
        play_urls = "#".join(
            f"{ep.get('title', '')}第{ep.get('playOrder', '')}集${json.dumps(ep.get('playSetting', {}), ensure_ascii=False)}"
            for ep in data
        )
        return {
            "vod_id": raw_id,
            "vod_name": self._s(first.get("title")),
            "vod_pic": self._s(first.get("vertPoster")),
            "vod_remarks": f"共{len(data)}集",
            "vod_content": f"播放:{first.get('collectionCount', 0)}",
            "vod_play_from": "围观短剧",
            "vod_play_url": play_urls,
        }

    def _detail_juwang(self, plat, detail_id, raw_id):
        url = detail_id if detail_id.startswith("http") else plat["host"] + detail_id
        html_text = self._get_text(url)
        root = self.html(html_text)
        if root is None:
            return {"vod_id": raw_id, "vod_name": "加载失败"}
        title = self._s(root.xpath("string(//h1)")).strip()
        pic = self._s((root.xpath("//img/@src") or [""])[0])
        content = self._s(root.xpath("string(//*[contains(@class,'info-detail')])")).strip()
        remarks = self._s(root.xpath("string(//*[contains(@class,'info-mark')])")).strip()
        episodes = []
        for a in root.xpath("//*[contains(@class,'ep-list')]//a[@href]"):
            ep_name = self._s(a.xpath("string(.)")).strip()
            ep_url = self._s((a.xpath("./@href") or [""])[0])
            if ep_name and ep_url:
                episodes.append(f"{ep_name}${ep_url}")
        return {
            "vod_id": raw_id,
            "vod_name": title or "未知标题",
            "vod_pic": pic,
            "vod_content": content,
            "vod_remarks": remarks,
            "vod_play_from": "剧王短剧",
            "vod_play_url": "#".join(episodes) or "暂无播放地址$0",
        }

    def _detail_qixing(self, plat, detail_id, raw_id):
        res = self._get_json(detail_id, headers=self.xingya_headers)
        data = res.get("data") or {}
        theaters = data.get("theaters") or []
        if theaters:
            play_urls = "#".join(
                f"{it.get('num', '')}${it.get('son_video_url', '')}" for it in theaters
            )
        elif data.get("video_url"):
            play_urls = f"1${data['video_url']}"
        else:
            play_urls = "暂无播放地址$0"
        tags = data.get("desc_tags") or []
        return {
            "vod_id": raw_id,
            "vod_name": self._s(data.get("title")),
            "vod_pic": self._s(data.get("cover_url")),
            "vod_content": self._s(data.get("introduction")),
            "vod_remarks": self._s(data.get("filing")),
            "vod_area": ",".join(tags) if isinstance(tags, list) else self._s(tags),
            "vod_play_from": "七星短剧",
            "vod_play_url": play_urls,
        }

    def _detail_tianquan(self, plat, detail_id, raw_id):
        url = f"{plat['host']}{plat['url2']}={detail_id}"
        res = self._get_json(url)
        episodes = res.get("data") or []
        play_urls = "#".join(
            f"{it.get('title', '')}${it.get('video_id', '')}" for it in episodes
        )
        return {
            "vod_id": raw_id,
            "vod_name": self._s(res.get("book_name")),
            "vod_pic": self._s(res.get("book_pic")),
            "vod_content": self._s(res.get("desc")),
            "vod_remarks": self._s(res.get("duration")),
            "vod_year": f"更新时间:{res.get('time', '')}",
            "vod_actor": self._s(res.get("author")),
            "vod_play_from": "红果短剧",
            "vod_play_url": play_urls,
        }

    _DISK_TOKENS = [
        "drive.uc.cn", "pan.quark.cn", "pan.baidu.com",
        "pan.xunlei.com", "alipan.com", "aliyundrive.com",
    ]
    _DISK_MAP = {
        "pan.baidu.com": "baidu", "pan.quark.cn": "quark",
        "drive.uc.cn": "uc", "alipan.com": "aliyun",
        "aliyundrive.com": "aliyun", "pan.xunlei.com": "xunlei",
    }
    _DISK_PRIORITY = {"baidu": 1, "quark": 2, "uc": 3, "aliyun": 4, "xunlei": 5}

    def _detail_duanjuwang(self, plat, detail_id, raw_id):
        host = plat["host"]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
            "Referer": host + "/",
        }
        html_text = self._get_text(detail_id, headers=headers)
        root = self.html(html_text)
        if root is None:
            return {"vod_id": raw_id, "vod_name": "加载失败"}
        title = self._clean(root.xpath("string(//h1[1])"))
        pic = self._s((root.xpath("(//img[contains(@class,'lazy')]/@data-original)[1]") or [""])[0])
        if not pic:
            pic = self._s((root.xpath("(//img/@src)[1]") or [""])[0])
        if pic and not pic.startswith(("http://", "https://", "//")):
            pic = host + pic
        elif pic.startswith("//"):
            pic = "https:" + pic
        links = []
        seen = set()
        for a in root.xpath("//*[contains(@class,'content')]//a[@href]"):
            href = self._s((a.xpath("./@href") or [""])[0])
            if not href or href in seen:
                continue
            seen.add(href)
            links.append(href)
        play_data = self._build_disk_play(links)
        return {
            "vod_id": raw_id,
            "vod_name": title or "短剧",
            "vod_pic": pic,
            "vod_content": "此为推送网盘规则",
            "vod_play_from": play_data["vod_play_from"],
            "vod_play_url": play_data["vod_play_url"],
        }

    def _build_disk_play(self, links):
        if not links:
            return {"vod_play_from": "短剧网", "vod_play_url": ""}
        grouped = {}
        order = []
        for link in links:
            disk = self._identify_disk(link)
            if not disk:
                continue
            if disk not in grouped:
                grouped[disk] = []
                order.append(disk)
            urls_in_group = {item.split("$", 1)[1] for item in grouped[disk]}
            if link not in urls_in_group:
                grouped[disk].append(f"{disk}${link}")
        if not grouped:
            fallback = "#".join(f"{i + 1}$push://{url}" for i, url in enumerate(links))
            return {"vod_play_from": "短剧网", "vod_play_url": fallback}
        names = sorted(order, key=lambda n: self._DISK_PRIORITY.get(n, 999))
        return {
            "vod_play_from": "$$$".join(names),
            "vod_play_url": "$$$".join("#".join(grouped[n]) for n in names),
        }

    @classmethod
    def _identify_disk(cls, url):
        low = url.lower()
        for token in cls._DISK_TOKENS:
            if token in low:
                return cls._DISK_MAP.get(token, "")
        return ""

    # --- search ---

    def _aggregate_search(self, keyword, page):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        results = []
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self._search_platform, pid, keyword, page): pid
                for pid in self.platforms
            }
            for future in as_completed(futures, timeout=8):
                try:
                    items = future.result()
                    results.extend(items)
                except Exception:
                    pass
        return results

    def _search_platform(self, platform_id, keyword, page):
        plat = self.platforms[platform_id]
        handler = {
            "七猫": self._search_qimao,
            "星芽": self._search_xingya,
            "星星": self._search_xingxing,
            "西饭": self._search_xifan,
            "锦鲤": self._search_jinli,
            "红果": self._search_tianquan,
            "短剧网": self._search_duanjuwang,
        }.get(platform_id)
        if handler:
            return handler(plat, keyword, page)
        return []

    def _search_qimao(self, plat, keyword, page):
        sign_str = f"operation=2playlet_privacy=1search_word={keyword}{QM_KEYS}"
        sign = self._md5(sign_str)
        url = f"{plat['host']}{plat['search']}?search_word={quote(keyword)}&playlet_privacy=1&operation=2&sign={sign}"
        res = self._get_json(url, headers=self._qm_headers())
        items = []
        for it in (res.get("data") or {}).get("list") or []:
            items.append({
                "vod_id": f"七猫@{quote(str(it.get('playlet_id', '')))}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("image_link")),
                "vod_remarks": f"七猫短剧 | {it.get('total_episode_num', 0)}集",
            })
        return items

    def _search_xingya(self, plat, keyword, page):
        url = f"{plat['host']}{plat['search']}"
        res = self._post_json(url, body={"text": keyword}, headers=self.xingya_headers)
        items = []
        for it in (res.get("data") or {}).get("theater", {}).get("search_data") or []:
            detail_url = f"{plat['host']}{plat['url2']}?theater_parent_id={it.get('id', '')}"
            items.append({
                "vod_id": f"星芽@{detail_url}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("cover_url")),
                "vod_remarks": f"星芽短剧 | {it.get('total', 0)}集",
            })
        return items

    def _search_xingxing(self, plat, keyword, page):
        return []

    def _search_xifan(self, plat, keyword, page):
        params = self._xifan_params({
            "reqType": "search",
            "offset": (page - 1) * 30,
            "keyword": keyword,
        })
        url = f"{plat['host']}{plat['search']}?{urlencode(params)}"
        res = self._get_json(url)
        items = []
        for vod in (res.get("result") or {}).get("elements") or []:
            dj = vod.get("duanjuVo") or {}
            items.append({
                "vod_id": f"西饭@{dj.get('duanjuId', '')}#{dj.get('source', '')}",
                "vod_name": self._s(dj.get("title")),
                "vod_pic": self._s(dj.get("coverImageUrl")),
                "vod_remarks": f"西饭短剧 | {dj.get('total', 0)}集",
            })
        return items

    def _search_jinli(self, plat, keyword, page):
        body = {"page": page, "limit": 30, "type_id": "", "year": "", "keyword": keyword}
        res = self._post_json(f"{plat['host']}{plat['search']}", body=body)
        items = []
        for it in (res.get("data") or {}).get("list") or []:
            items.append({
                "vod_id": f"锦鲤@{it.get('vod_id', '')}",
                "vod_name": self._s(it.get("vod_name")),
                "vod_pic": self._s(it.get("vod_pic")),
                "vod_remarks": f"锦鲤短剧 | {it.get('vod_total', 0)}集",
            })
        return items

    def _search_weiguan(self, plat, keyword, page):
        body = {
            "audience": "", "page": page, "pageSize": 30,
            "searchWord": keyword, "subject": "",
        }
        res = self._post_json(f"{plat['host']}{plat['search']}", body=body)
        items = []
        for it in res.get("data") or []:
            items.append({
                "vod_id": f"围观@{it.get('oneId', '')}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("vertPoster")),
                "vod_remarks": f"围观短剧 | 集数:{it.get('episodeCount', 0)}",
            })
        return items

    def _search_juwang(self, plat, keyword, page):
        url = f"{plat['host']}{plat['search']}/{quote(keyword)}/page/{page}/"
        html_text = self._get_text(url)
        root = self.html(html_text)
        if root is None:
            return []
        items = []
        for li in root.xpath("//section[contains(@class,'container')]//li"):
            name_el = li.xpath(".//img/@alt")
            href_el = li.xpath(".//a[contains(@class,'image-line')]/@href")
            src_el = li.xpath(".//img/@src")
            remark_el = li.xpath(".//*[contains(@class,'remarks')]/text()")
            name = self._s(name_el[0]) if name_el else ""
            href = self._s(href_el[0]) if href_el else ""
            pic = self._s(src_el[0]) if src_el else ""
            remark = self._s(remark_el[0]).strip() if remark_el else ""
            if href:
                items.append({
                    "vod_id": f"剧王@{href}",
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": f"剧王短剧 | {remark}",
                })
        return items

    def _search_qixing(self, plat, keyword, page):
        url = f"{plat['host']}{plat['search']}"
        res = self._post_json(url, body={"text": keyword}, headers=self.xingya_headers)
        items = []
        for it in (res.get("data") or {}).get("theater", {}).get("search_data") or []:
            detail_url = f"{plat['host']}{plat['url2']}?theater_parent_id={it.get('id', '')}"
            items.append({
                "vod_id": f"七星@{detail_url}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("cover_url")),
                "vod_remarks": f"七星短剧 | {it.get('total', 0)}集",
            })
        return items

    def _search_tianquan(self, plat, keyword, page):
        url = f"{plat['host']}{plat['search']}={quote(keyword)}&offset={page}"
        res = self._get_json(url)
        items = []
        for it in res.get("data") or []:
            items.append({
                "vod_id": f"红果@{it.get('book_id', '')}",
                "vod_name": self._s(it.get("title")),
                "vod_pic": self._s(it.get("cover")),
                "vod_remarks": f"红果短剧 | {self._s(it.get('sub_title'))}",
            })
        return items

    def _search_duanjuwang(self, plat, keyword, page):
        host = plat["host"]
        url = f"{host}/search.php?q={quote(keyword)}&page={page}"
        html = self._get_text(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
            "Referer": host + "/",
        })
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//li[contains(@class,'col-6')]"):
            anchors = card.xpath(".//h3[contains(@class,'f-14')]//a[@href]")
            if not anchors:
                continue
            anchor = anchors[0]
            name = self._clean("".join(anchor.xpath(".//text()")))
            href = self._s((anchor.xpath("./@href") or [""])[0]).strip()
            if not name or not href:
                continue
            full_url = href if href.startswith("http") else host + href
            if full_url in seen:
                continue
            seen.add(full_url)
            pic = self._s((card.xpath(".//img[contains(@class,'lazy')]/@data-original") or [""])[0])
            if pic and not pic.startswith(("http://", "https://", "//")):
                pic = host + pic
            elif pic.startswith("//"):
                pic = "https:" + pic
            items.append({
                "vod_id": f"短剧网@{full_url}",
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": "短剧网",
            })
        return items

    # --- play per platform ---

    def _play_weiguan(self, play_id):
        try:
            data = json.loads(play_id) if isinstance(play_id, str) else play_id
        except (json.JSONDecodeError, TypeError):
            return {"parse": 0, "jx": 0, "url": play_id}
        url = data.get("super") or data.get("high") or data.get("normal") or ""
        return {"parse": 0, "jx": 0, "url": url}

    def _play_juwang(self, play_id):
        url = play_id if play_id.startswith("http") else self.platforms["剧王"]["host"] + play_id
        html_text = self._get_text(url)
        m = re.search(r'"wwm3u8"\s*:\s*"([^"]+)"', html_text)
        video_url = ""
        if m:
            video_url = m.group(1).replace(r"\/", "/").replace(r'\"', '"')
        return {
            "parse": 0, "jx": 0, "url": video_url,
            "header": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36"
                ),
            },
        }

    def _play_jinli(self, play_id):
        html_text = self._get_text(play_id, headers={"referer": "https://www.jinlidj.com/"})
        trimmed = html_text.strip()
        if trimmed[:1] in ("{", "["):
            try:
                data = json.loads(trimmed)
                video_url = data.get("url") or (data.get("data") or {}).get("url") or ""
                if video_url:
                    return {"parse": 0, "jx": 0, "url": video_url}
            except (TypeError, ValueError):
                pass
        match = re.search(r'https?://[^\'"\\s]+\\.(?:m3u8|mp4)(?:\\?[^\'"\\s]*)?', html_text, re.I)
        if match:
            return {"parse": 0, "jx": 0, "url": match.group(0)}
        match = re.search(r'url\\s*:\\s*[\'"]([^\'"]+)[\'"]', html_text)
        video_url = match.group(1) if match else play_id
        return {"parse": 0, "jx": 0, "url": video_url}
