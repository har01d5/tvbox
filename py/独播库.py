# coding=utf-8
import base64
import json
import re
import sys
from urllib.parse import quote, unquote

from lxml import etree

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "独播库"
        self.host = "https://www.dbku.tv"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.categories = [
            {"type_name": "连续剧", "type_id": "index"},
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "综艺", "type_id": "variety"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "港剧", "type_id": "hk"},
            {"type_name": "陆剧", "type_id": "luju"},
        ]
        self.category_paths = {
            "index": "/vodtype/2--------{pg}---.html",
            "movie": "/vodtype/1--------{pg}---.html",
            "variety": "/vodtype/3--------{pg}---.html",
            "anime": "/vodtype/4--------{pg}---.html",
            "hk": "/vodtype/20--------{pg}---.html",
            "luju": "/vodtype/13--------{pg}---.html",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeContent(self, filter):
        return {"class": self.categories}

    def homeVideoContent(self):
        return {"list": []}

    def _build_url(self, href):
        raw = str(href or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        if raw.startswith("/"):
            return self.host + raw
        return self.host + "/" + raw

    def _extract_play_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/vodplay/(\d+-\d+-\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"\d+-\d+-\d+", raw):
            return raw
        return ""

    def _extract_vod_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/voddetail/(\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"\d+", raw):
            return raw
        return ""

    def _build_detail_request_url(self, id_or_url):
        raw = str(id_or_url or "").strip()
        if not raw:
            return ""
        vod_id = self._extract_vod_id(raw)
        if vod_id:
            return f"{self.host}/voddetail/{vod_id}.html"
        return self._build_url(raw)

    def _build_play_request_url(self, id_or_url):
        raw = str(id_or_url or "").strip()
        if not raw:
            return ""
        play_id = self._extract_play_id(raw)
        if play_id:
            return f"{self.host}/vodplay/{play_id}.html"
        return self._build_url(raw)

    def _parse_list_cards(self, html):
        root = self.html(html)
        results = []
        if root is None:
            return results

        cards = root.xpath("//*[contains(@class,'myui-vodlist__box')]")
        seen = set()
        for card in cards:
            href = ""
            title = ""
            pic = ""
            for anchor in card.xpath(".//a[@href]"):
                raw_href = (anchor.xpath("./@href") or [""])[0].strip()
                if "/voddetail/" in raw_href:
                    href = self._extract_vod_id(raw_href)
                    title = (
                        (anchor.xpath("./@title") or [""])[0].strip()
                        or "".join(anchor.xpath(".//text()")).strip()
                    )
                    pic = (
                        (anchor.xpath("./@data-original") or [""])[0].strip()
                        or (anchor.xpath("./@src") or [""])[0].strip()
                    )
                    break
            if not href or href in seen or not title:
                continue

            remarks = "".join(card.xpath(".//*[contains(@class,'pic-text')][1]//text()")).strip()
            seen.add(href)
            results.append(
                {
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return results

    def _request_html(self, path_or_url, expect_xpath=None, referer=None):
        target = path_or_url if path_or_url.startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or self.host
        headers["Origin"] = self.host
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        html = response.text or ""
        if expect_xpath:
            root = self.html(html)
            if root is None or not root.xpath(expect_xpath):
                return ""
        return html

    def _parse_cards_from_nodes(self, nodes):
        results = []
        seen = set()
        for card in nodes:
            snippet = self._parse_list_cards(etree.tostring(card, encoding="unicode"))
            for item in snippet:
                if item["vod_id"] in seen:
                    continue
                seen.add(item["vod_id"])
                results.append(item)
        return results

    def _parse_search_cards(self, html):
        root = self.html(html)
        if root is None:
            return []
        search_list = root.xpath("//*[@id='searchList']")
        if search_list:
            cards = search_list[0].xpath(".//*[contains(@class,'myui-vodlist__box')]")
            parsed = self._parse_cards_from_nodes(cards)
            if parsed:
                return parsed
        return self._parse_list_cards(html)

    def _page_result(self, items, pg):
        page = int(pg)
        return {
            "list": items,
            "page": page,
            "limit": len(items),
            "total": page * 30 + len(items),
        }

    def categoryContent(self, tid, pg, filter, extend):
        path = self.category_paths.get(tid, self.category_paths["index"]).format(pg=pg)
        html = self._request_html(path, expect_xpath="//*[contains(@class,'myui-vodlist__box')]")
        return self._page_result(self._parse_list_cards(html), pg)

    def searchContent(self, key, quick, pg="1"):
        path = "/vodsearch/-------------.html?wd={0}&submit=".format(quote(key))
        html = self._request_html(path, expect_xpath="//*[@id='searchList']|//*[contains(@class,'myui-vodlist__box')]")
        return self._page_result(self._parse_search_cards(html), pg)

    def _extract_text_by_prefix(self, html, prefixes):
        texts = re.findall(r">([^<>]+)<", html)
        for text in texts:
            clean = text.strip()
            for prefix in prefixes:
                if clean.startswith(prefix):
                    return clean.split("：", 1)[-1].strip()
        return ""

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _extract_detail_text(self, detail_root, html, label, joiner=""):
        value = self._extract_detail_field(detail_root, label, joiner=joiner)
        if value:
            return value
        return self._extract_text_by_prefix(html, [f"{label}："])

    def _extract_detail_field(self, detail_root, label, joiner=""):
        if detail_root is None:
            return ""
        nodes = detail_root.xpath(f'.//span[contains(normalize-space(.), "{label}：")]')
        if not nodes:
            return ""
        label_node = nodes[0]
        values = []
        if self._clean_text(label_node.tail):
            values.append(self._clean_text(label_node.tail))
        for sibling in label_node.itersiblings():
            classes = " ".join(sibling.xpath("./@class"))
            if sibling.tag == "span" and "text-muted" in classes:
                break
            if sibling.tag == "span" and "split-line" in classes:
                continue
            if sibling.tag == "a" and (sibling.xpath("./@href") or [""])[0].startswith("#"):
                break
            text = self._clean_text("".join(sibling.xpath(".//text()")))
            if text:
                values.append(text)
            tail = self._clean_text(sibling.tail)
            if tail:
                values.append(tail)

        cleaned = []
        for value in values:
            if value and value not in cleaned:
                cleaned.append(value)
        if joiner:
            return joiner.join(cleaned)
        return self._clean_text("".join(cleaned))

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        detail_root = (
            root.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' myui-content__detail ')][1]")
            or [root]
        )[0]
        title = ((detail_root.xpath(".//*[contains(@class,'title')][1]//text()") or [""])[0]).strip()
        pic = (
            (root.xpath("//*[contains(@class,'myui-content__thumb')]//img/@data-original") or [""])[0].strip()
            or (root.xpath("//*[contains(@class,'myui-content__thumb')]//img/@src") or [""])[0].strip()
        )
        content = self._extract_detail_field(detail_root, "简介") or "".join(
            root.xpath("//*[contains(@class,'data')][1]//text()")
        ).strip()

        episodes = []
        seen = set()
        for href, label in re.findall(
            r'<a[^>]+href=["\']([^"\']*/vodplay/\d+-\d+-\d+\.html[^"\']*)["\'][^>]*>([\s\S]*?)</a>',
            html,
            re.I,
        ):
            play_id = self._extract_play_id(href)
            name = re.sub(r"<[^>]*>", "", label).strip()
            if not play_id or not name or "立即播放" in name or play_id in seen:
                continue
            seen.add(play_id)
            episodes.append(f"{name}${play_id}")

        vod = {
            "vod_id": vod_id,
            "path": self._build_detail_request_url(vod_id),
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_tag": "",
            "vod_time": self._extract_detail_text(detail_root, html, "更新"),
            "vod_remarks": self._clean_text(
                ((detail_root.xpath('.//*[@id="rating"]//*[contains(@class,"branch")][1]//text()') or [""])[0]).strip()
                or ((detail_root.xpath('.//*[@id="ratewords"][1]//text()') or [""])[0]).strip()
            ),
            "vod_play_from": "独播库",
            "vod_play_url": "#".join(episodes),
            "type_name": self._extract_detail_text(detail_root, html, "分类"),
            "vod_content": content,
            "vod_year": self._extract_detail_text(detail_root, html, "年份"),
            "vod_area": self._extract_detail_text(detail_root, html, "地区"),
            "vod_lang": "",
            "vod_director": self._extract_detail_text(detail_root, html, "导演", joiner=","),
            "vod_actor": self._extract_detail_text(detail_root, html, "主演", joiner=","),
        }
        return {"list": [vod]}

    def detailContent(self, ids):
        vod_id = ids[0]
        html = self._request_html(
            self._build_detail_request_url(vod_id),
            expect_xpath="//*[contains(@class,'title')]|//a[contains(@href,'/vodplay/')]",
        )
        return self._parse_detail_page(html, vod_id)

    def _parse_player_data(self, html):
        matched = re.search(r"var\s+player_data\s*=\s*(\{[\s\S]*?\})\s*;?\s*</script>", html, re.I)
        if not matched:
            matched = re.search(r"var\s+player_[^=]*\s*=\s*(\{[\s\S]*?\})\s*;?\s*</script>", html, re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _decode_play_url_by_encrypt(self, value, encrypt):
        raw = str(value or "")
        mode = int(encrypt or 0)
        if not raw:
            return ""
        try:
            if mode == 1:
                return unquote(raw)
            if mode == 2:
                decoded = base64.b64decode(raw).decode("utf-8")
                return unquote(decoded)
            if mode == 3:
                text = raw[8:] if len(raw) > 16 else raw
                text = base64.b64decode(text).decode("utf-8")
                if len(text) > 16:
                    text = text[8:-8]
                return text
            return raw
        except Exception:
            return raw

    def _build_player_headers(self, referer):
        return {
            "User-Agent": self.headers["User-Agent"],
            "Referer": referer,
        }

    def playerContent(self, flag, id, vipFlags):
        current = id
        for _ in range(3):
            request_url = self._build_play_request_url(current)
            html = self._request_html(request_url, referer=self.host)
            data = self._parse_player_data(html)
            if not data:
                return {"parse": 0, "playUrl": "", "url": ""}
            decoded = self._decode_play_url_by_encrypt(data.get("url", ""), data.get("encrypt", 0))
            play_url = self._build_url(decoded)
            if not play_url:
                return {"parse": 0, "playUrl": "", "url": ""}
            if self.host in play_url and "/vodplay/" in play_url and play_url != current:
                current = play_url
                continue
            return {
                "parse": 0,
                "playUrl": "",
                "url": play_url,
                "header": self._build_player_headers(request_url),
            }
        return {"parse": 0, "playUrl": "", "url": ""}
