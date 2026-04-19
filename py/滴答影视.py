# coding=utf-8
import json
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "滴答影视"
        self.host = "https://www.didahd.pro"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "5", "type_name": "综艺"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "纪录片"},
        ]
        self.filter_def = {
            "1": {"cateId": "1", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "2": {"cateId": "2", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "3": {"cateId": "3", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "4": {"cateId": "4", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
            "5": {"cateId": "5", "area": "", "sort": "time", "class": "", "lang": "", "letter": "", "year": ""},
        }
        self.filters = json.loads(
            """
            {
              "1": [
                {"key":"class","name":"按剧情","init":"","value":[{"n":"全部","v":""},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"警匪","v":"警匪"},{"n":"犯罪","v":"犯罪"},{"n":"动画","v":"动画"},{"n":"奇幻","v":"奇幻"},{"n":"武侠","v":"武侠"},{"n":"冒险","v":"冒险"},{"n":"枪战","v":"枪战"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"经典","v":"经典"},{"n":"青春","v":"青春"},{"n":"文艺","v":"文艺"},{"n":"微电影","v":"微电影"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"运动","v":"运动"},{"n":"农村","v":"农村"},{"n":"儿童","v":"儿童"},{"n":"网络电影","v":"网络电影"}]},
                {"key":"area","name":"按地区","init":"","value":[{"n":"全部","v":""},{"n":"大陆","v":"大陆"},{"n":"香港","v":"香港"},{"n":"台湾","v":"台湾"},{"n":"美国","v":"美国"},{"n":"法国","v":"法国"},{"n":"英国","v":"英国"},{"n":"日本","v":"日本"},{"n":"韩国","v":"韩国"},{"n":"德国","v":"德国"},{"n":"泰国","v":"泰国"},{"n":"印度","v":"印度"},{"n":"意大利","v":"意大利"},{"n":"西班牙","v":"西班牙"},{"n":"加拿大","v":"加拿大"},{"n":"其他","v":"其他"}]},
                {"key":"year","name":"按年份","init":"","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"}]},
                {"key":"lang","name":"按语言","init":"","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"法语","v":"法语"},{"n":"德语","v":"德语"},{"n":"其它","v":"其它"}]},
                {"key":"sort","name":"按排序","init":"time","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}
              ],
              "2": [
                {"key":"class","name":"按剧情","init":"","value":[{"n":"全部","v":""},{"n":"古装","v":"古装"},{"n":"战争","v":"战争"},{"n":"青春偶像","v":"青春偶像"},{"n":"喜剧","v":"喜剧"},{"n":"家庭","v":"家庭"},{"n":"犯罪","v":"犯罪"},{"n":"动作","v":"动作"},{"n":"奇幻","v":"奇幻"},{"n":"剧情","v":"剧情"},{"n":"历史","v":"历史"},{"n":"经典","v":"经典"},{"n":"乡村","v":"乡村"},{"n":"情景","v":"情景"},{"n":"商战","v":"商战"},{"n":"网剧","v":"网剧"},{"n":"其他","v":"其他"}]},
                {"key":"area","name":"按地区","init":"","value":[{"n":"全部","v":""},{"n":"内地","v":"内地"},{"n":"韩国","v":"韩国"},{"n":"香港","v":"香港"},{"n":"台湾","v":"台湾"},{"n":"日本","v":"日本"},{"n":"美国","v":"美国"},{"n":"泰国","v":"泰国"},{"n":"英国","v":"英国"},{"n":"新加坡","v":"新加坡"},{"n":"其他","v":"其他"}]},
                {"key":"year","name":"按年份","init":"","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"}]},
                {"key":"lang","name":"按语言","init":"","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},
                {"key":"sort","name":"按排序","init":"time","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}
              ],
              "5": [
                {"key":"class","name":"按剧情","init":"","value":[{"n":"全部","v":""},{"n":"真人秀","v":"真人秀"},{"n":"综艺","v":"综艺"},{"n":"脱口秀","v":"脱口秀"},{"n":"欧美综艺","v":"欧美综艺"},{"n":"日韩综艺","v":"日韩综艺"}]},
                {"key":"year","name":"按年份","init":"","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"}]},
                {"key":"lang","name":"按语言","init":"","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},
                {"key":"sort","name":"按排序","init":"time","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}
              ],
              "4": [
                {"key":"year","name":"按年份","init":"","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"}]},
                {"key":"lang","name":"按语言","init":"","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},
                {"key":"sort","name":"按排序","init":"time","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}
              ],
              "3": [
                {"key":"year","name":"按年份","init":"","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"}]},
                {"key":"lang","name":"按语言","init":"","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},
                {"key":"sort","name":"按排序","init":"time","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}
              ]
            }
            """
        )

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes, "filters": self.filters}

    def homeVideoContent(self):
        return {"list": []}

    def _stringify(self, value):
        return "" if value is None else str(value)

    def _normalize_ext(self, extend):
        if isinstance(extend, dict):
            return extend
        if not extend:
            return {}
        try:
            return json.loads(str(extend))
        except Exception:
            return {}

    def _build_url(self, path):
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

    def _build_category_url(self, tid, pg, extend):
        values = dict(self.filter_def.get(str(tid), {"cateId": str(tid), "sort": "time"}))
        values.update(self._normalize_ext(extend))
        path = (
            f"show/{values.get('cateId', tid)}-{values.get('area', '')}-{values.get('sort', 'time')}-"
            f"{values.get('class', '')}-{values.get('lang', '')}-{values.get('letter', '')}---{int(pg)}---"
            f"{values.get('year', '')}"
        )
        return self._build_url(path)

    def _request_html(self, path_or_url, referer=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.headers["Referer"]
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _parse_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for card in root.xpath("//*[contains(@class,'myui-vodlist__box')]"):
            href = ((card.xpath(".//*[contains(@class,'title')]//a[@href][1]/@href") or [""])[0]).strip()
            title = (
                ((card.xpath(".//*[contains(@class,'title')]//a[@title][1]/@title") or [""])[0]).strip()
                or self._clean_text("".join(card.xpath(".//*[contains(@class,'title')]//a[1]//text()")))
            )
            pic = (
                ((card.xpath(".//*[contains(@class,'lazyload')][1]/@data-original") or [""])[0]).strip()
                or ((card.xpath(".//*[contains(@class,'lazyload')][1]/@src") or [""])[0]).strip()
                or ((card.xpath(".//img[1]/@data-original") or [""])[0]).strip()
                or ((card.xpath(".//img[1]/@src") or [""])[0]).strip()
            )
            remarks = self._clean_text("".join(card.xpath(".//*[contains(@class,'pic-text')][1]//text()")))
            vod_id = self._build_url(href)
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
        return {
            "list": items,
            "page": page,
            "pagecount": page + 1 if items else page,
            "limit": 12,
            "total": page * 12 + len(items),
        }

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._stringify(key).strip()
        if not keyword:
            return {"page": page, "pagecount": 0, "total": 0, "list": []}
        url = f"{self.host}/search/-------------.html?wd={quote(keyword)}"
        items = self._parse_cards(self._request_html(url))
        return {"page": page, "pagecount": page + 1 if items else page, "total": len(items), "list": items}

    def _extract_detail_field(self, root, label, joiner=""):
        if root is None:
            return ""
        nodes = root.xpath(f'.//*[contains(@class,"data")][.//*[contains(normalize-space(.), "{label}：")]]')
        if not nodes:
            return ""
        anchor_values = [self._clean_text(text) for text in nodes[0].xpath(".//a//text()") if self._clean_text(text)]
        if anchor_values:
            return joiner.join(anchor_values) if joiner else "".join(anchor_values)
        text = self._clean_text("".join(nodes[0].xpath(".//text()")))
        return text.split("：", 1)[-1].strip() if "：" in text else text

    def _normalize_disk_name(self, text):
        value = self._clean_text(text).lower()
        if "百度" in value:
            return "baidu"
        if "夸克" in value:
            return "quark"
        if value.startswith("uc") or "uc网盘" in value or "uc 网盘" in value:
            return "uc"
        if "阿里" in value or "aliyun" in value:
            return "aliyun"
        if "迅雷" in value:
            return "xunlei"
        return value or "netdisk"

    def _disk_priority(self, name):
        order = {"baidu": 1, "quark": 2, "uc": 3, "aliyun": 4, "xunlei": 5}
        return order.get(name, 999)

    def _extract_netdisk_groups(self, html):
        root = self.html(html)
        if root is None:
            return []
        grouped = {}
        order_seen = []
        for row in root.xpath("//*[contains(@class,'text-muted') and contains(@class,'col-pd')]"):
            raw_name = self._clean_text("".join(row.xpath(".//b[1]//text()"))).replace("：", "")
            disk_name = self._normalize_disk_name(raw_name)
            href = ((row.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            title = self._clean_text("".join(row.xpath(".//a[1]//text()"))) or disk_name
            if not href:
                continue
            if disk_name not in grouped:
                grouped[disk_name] = []
                order_seen.append(disk_name)
            links = {item.split("$", 1)[1] for item in grouped[disk_name]}
            if href not in links:
                grouped[disk_name].append(f"{title}${href}")
        names = sorted(order_seen, key=self._disk_priority)
        return [{"from": name, "urls": "#".join(grouped[name])} for name in names if grouped[name]]

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        if root is None:
            return {"vod_id": vod_id, "vod_name": "", "vod_play_from": "", "vod_play_url": ""}
        detail_root = (root.xpath("//*[contains(@class,'myui-content__detail')][1]") or [root])[0]
        title = self._clean_text("".join(detail_root.xpath(".//*[contains(@class,'title')][1]//text()")))
        pic = (
            ((root.xpath("//*[contains(@class,'lazyload')][1]/@data-original") or [""])[0]).strip()
            or ((root.xpath("//*[contains(@class,'myui-vodlist__thumb')]//img[1]/@src") or [""])[0]).strip()
        )
        content = ""
        for node in root.xpath("//*[contains(@class,'text-muted')]"):
            text = self._clean_text("".join(node.xpath(".//text()")))
            if "剧情简介" in text:
                content = text.replace("剧情简介：", "").strip()
                break
        groups = self._extract_netdisk_groups(html)
        return {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_content": content,
            "vod_remarks": "",
            "vod_year": self._extract_detail_field(detail_root, "年份"),
            "vod_area": self._extract_detail_field(detail_root, "地区"),
            "vod_class": self._extract_detail_field(detail_root, "分类"),
            "vod_director": self._extract_detail_field(detail_root, "导演"),
            "vod_actor": self._extract_detail_field(detail_root, "主演", joiner=","),
            "vod_play_from": "$$$".join([item["from"] for item in groups]),
            "vod_play_url": "$$$".join([item["urls"] for item in groups]),
        }

    def detailContent(self, ids):
        result = {"list": []}
        for raw in ids:
            vod_id = self._stringify(raw).strip()
            if not vod_id:
                continue
            result["list"].append(self._parse_detail_page(self._request_html(vod_id), vod_id))
        return result

    def _is_netdisk_url(self, value):
        text = self._stringify(value).strip().lower()
        return any(
            token in text
            for token in [
                "drive.uc.cn",
                "pan.quark.cn",
                "pan.baidu.com",
                "pan.xunlei.com",
                "alipan.com",
                "aliyundrive.com",
            ]
        )

    def playerContent(self, flag, id, vipFlags):
        raw = self._stringify(id).strip()
        if self._is_netdisk_url(raw):
            return {"parse": 0, "playUrl": "", "url": raw}
        return {"parse": 0, "playUrl": "", "url": ""}
