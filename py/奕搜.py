# coding=utf-8
import re
import sys
from urllib.parse import quote, urljoin

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "奕搜"
        self.host = "https://ysso.cc"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Referer": self.host + "/",
        }
        self.classes = [
            {"type_id": "dy", "type_name": "电影"},
            {"type_id": "dsj", "type_name": "电视剧"},
            {"type_id": "zy", "type_name": "综艺"},
            {"type_id": "dm", "type_name": "动漫"},
            {"type_id": "jlp", "type_name": "纪录片"},
            {"type_id": "dj", "type_name": "短剧"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes}

    def homeVideoContent(self):
        return {"list": []}

    def _build_url(self, path):
        return urljoin(self.host + "/", str(path or "").strip())

    def _extract_remark_from_title(self, title_text):
        parts = re.findall(r"\[(.*?)\]", str(title_text or ""))
        for part in parts:
            text = part.strip()
            if text.startswith("更"):
                match = re.search(r"更\s*([0-9]+)", text)
                return f"更新至{match.group(1)}集" if match else text
        for part in parts:
            text = part.strip()
            if text.endswith("分"):
                return f"评分:{text[:-1].strip()}"
        for part in parts:
            text = part.strip()
            if re.match(r"^\d{4}$", text):
                return f"首播:{text}"
        return ""

    def _clean_title_text(self, title):
        return re.sub(r"\s*\[.*?\]", "", str(title or "")).strip()

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _request_html(self, path_or_url):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        response = self.fetch(target, headers=dict(self.headers), timeout=10, verify=False)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _parse_list_boxes(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        seen = set()
        for node in root.xpath("//*[contains(@class,'list-boxes')]"):
            title_href = "".join(node.xpath(".//a[contains(@class,'text_title_p')][1]/@href")).strip()
            fallback_href = "".join(node.xpath(".//*[contains(@class,'left_ly')]//a[1]/@href")).strip()
            vod_id = title_href or fallback_href
            title = self._clean_text("".join(node.xpath(".//a[contains(@class,'text_title_p')][1]//text()")))
            if not vod_id or not title or vod_id in seen:
                continue
            seen.add(vod_id)
            pic = self._build_url("".join(node.xpath(".//img[contains(@class,'image_left')][1]/@src")).strip())
            remark = self._extract_remark_from_title(title) or self._clean_text(
                "".join(node.xpath(".//*[contains(@class,'list-actions')]//span[1]//text()"))
            )
            items.append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_title_text(title),
                    "vod_pic": pic,
                    "vod_remarks": remark,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        items = self._parse_list_boxes(self._request_html(self._build_url(f"/{tid}.html?page={page}")))
        return {"page": page, "limit": len(items) or 20, "total": page * (len(items) or 20), "list": items}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = self._clean_text(key)
        if not keyword:
            return {"page": page, "total": 0, "list": []}
        url = self._build_url(f"/search.html?keyword={quote(keyword)}&page={page}")
        items = self._parse_list_boxes(self._request_html(url))
        return {"page": page, "limit": len(items) or 20, "total": len(items), "list": items}

    def _identify_disk(self, value):
        text = str(value or "").strip().lower()
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
        return ""

    def _disk_priority(self, name):
        order = {"baidu": 1, "quark": 2, "uc": 3, "aliyun": 4, "xunlei": 5}
        return order.get(name, 999)

    def _extract_share_links(self, root):
        links = []
        seen = set()
        for href in root.xpath("//a[@target='_blank']/@href"):
            url = str(href or "").strip()
            if not url.startswith(("http://", "https://")) or url in seen:
                continue
            seen.add(url)
            links.append(url)
        return links

    def _build_play_data(self, share_links):
        unique_links = []
        seen = set()
        for link in share_links:
            if link and link not in seen:
                seen.add(link)
                unique_links.append(link)
        grouped = {}
        for link in unique_links:
            disk = self._identify_disk(link)
            if not disk:
                continue
            grouped.setdefault(disk, []).append(f"{disk}${link}")
        if grouped:
            names = sorted(grouped, key=self._disk_priority)
            return {
                "vod_play_from": "$$$".join(names),
                "vod_play_url": "$$$".join("#".join(grouped[name]) for name in names),
            }
        if unique_links:
            return {
                "vod_play_from": "奕搜",
                "vod_play_url": "#".join(
                    f"{index + 1}$push://{link}" for index, link in enumerate(unique_links)
                ),
            }
        return {"vod_play_from": "奕搜", "vod_play_url": ""}

    def detailContent(self, ids):
        result = {"list": []}
        for raw_id in ids:
            vod_id = str(raw_id or "").strip()
            if not vod_id:
                continue
            html = self._request_html(self._build_url(vod_id))
            root = self.html(html)
            if root is None:
                continue
            title = self._clean_text("".join(root.xpath("//h1[contains(@class,'articl_title')][1]//text()")))
            director_items = []
            actor_items = []
            for span in root.xpath("//*[@id='info']/span"):
                key = self._clean_text(
                    "".join(span.xpath(".//*[contains(@class,'pl')][1]//text()"))
                ).replace("：", "").replace(":", "")
                names = [self._clean_text(text) for text in span.xpath(".//*[contains(@class,'attrs')]//a/text()")]
                names = [name for name in names if name]
                if "导演" in key or "编剧" in key:
                    for name in names:
                        if name not in director_items:
                            director_items.append(name)
                if "主演" in key or "演员" in key:
                    for name in names:
                        if name not in actor_items:
                            actor_items.append(name)
            content = ""
            for text in root.xpath("//p/text()"):
                cleaned = self._clean_text(text)
                if len(cleaned) > 20:
                    content = cleaned
                    break
            remarks = self._extract_remark_from_title(title)
            body_text = self._clean_text("".join(root.xpath("//body//text()")))
            code_match = re.search(r"提取码[：:]\s*([a-zA-Z0-9]{4})", body_text)
            if code_match:
                remarks = f"{remarks} 提取码: {code_match.group(1)}".strip()
            play = self._build_play_data(self._extract_share_links(root))
            result["list"].append(
                {
                    "vod_id": vod_id,
                    "vod_name": self._clean_title_text(title),
                    "vod_pic": self._build_url(
                        "".join(
                            root.xpath(
                                "(//*[contains(@class,'tc-box') and contains(@class,'article-box')]//img)[1]/@src"
                            )
                        ).strip()
                    ),
                    "vod_remarks": remarks,
                    "vod_director": ", ".join(director_items),
                    "vod_actor": ", ".join(actor_items),
                    "vod_content": content,
                    "vod_play_from": play["vod_play_from"],
                    "vod_play_url": play["vod_play_url"],
                }
            )
        return result

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("push://"):
            return {"parse": 0, "url": raw[7:]}
        return {"parse": 0, "url": raw}
