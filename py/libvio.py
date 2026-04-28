# coding=utf-8
import json
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "LibVIO"
        self.host = "https://www.libvio.la"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.categories = [
            {"type_name": "最近更新", "type_id": "index"},
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "电视剧", "type_id": "series"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "日韩剧", "type_id": "jpandkr"},
            {"type_name": "欧美剧", "type_id": "euandus"},
        ]
        self.category_paths = {
            "index": "/",
            "movie": "/type/1-{pg}.html",
            "series": "/type/2-{pg}.html",
            "anime": "/type/4-{pg}.html",
            "jpandkr": "/type/15-{pg}.html",
            "euandus": "/type/16-{pg}.html",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def danmaku(self):
        return True

    def homeContent(self, filter):
        return {"class": self.categories}

    def _build_url(self, href):
        raw = str(href or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return self.host + "/" + raw.lstrip("/")

    def _extract_vod_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/detail/(\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"\d+", raw):
            return raw
        return ""

    def _extract_play_id(self, href):
        raw = str(href or "").strip()
        matched = re.search(r"/play/([^./]+-\d+-\d+)\.html", raw)
        if matched:
            return matched.group(1)
        if re.fullmatch(r"[^./]+-\d+-\d+", raw):
            return raw
        return ""

    def _build_detail_request_url(self, vod_id):
        return f"{self.host}/detail/{self._extract_vod_id(vod_id)}.html"

    def _build_play_request_url(self, play_id):
        return f"{self.host}/play/{self._extract_play_id(play_id)}.html"

    def _parse_list_cards(self, html):
        root = self.html(html)
        results = []
        if root is None:
            return results

        seen = set()
        for card in root.xpath("//*[contains(@class,'stui-vodlist__box')]"):
            href = ((card.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            vod_id = self._extract_vod_id(href)
            title = ((card.xpath(".//a[@title][1]/@title") or [""])[0]).strip()
            pic = (
                (card.xpath(".//a[@data-original][1]/@data-original") or [""])[0].strip()
                or (card.xpath(".//img[@data-original][1]/@data-original") or [""])[0].strip()
                or (card.xpath(".//img[@src][1]/@src") or [""])[0].strip()
            )
            remarks = "".join(card.xpath(".//*[contains(@class,'pic-text')][1]//text()")).strip()
            if not vod_id or vod_id in seen or not title:
                continue
            seen.add(vod_id)
            results.append(
                {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._build_url(pic),
                    "vod_remarks": remarks,
                }
            )
        return results

    def _request_html(self, path_or_url, expect_xpath=None, referer=None):
        target = path_or_url if str(path_or_url).startswith("http") else self._build_url(path_or_url)
        headers = dict(self.headers)
        headers["Referer"] = referer or (self.host + "/")
        response = self.fetch(target, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        return response.text or ""

    def _page_result(self, items, pg):
        page = int(pg)
        return {
            "list": items,
            "page": page,
            "limit": len(items),
            "total": page * 30 + len(items),
        }

    def _clean_text(self, text):
        return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()

    def _extract_detail_field(self, root, label, joiner=""):
        if root is None:
            return ""
        nodes = root.xpath(f'.//span[contains(normalize-space(.), "{label}：")]')
        if not nodes:
            return ""
        values = []
        label_node = nodes[0]
        if self._clean_text(label_node.tail):
            values.append(self._clean_text(label_node.tail))
        for sibling in label_node.itersiblings():
            if sibling.tag == "span" and "text-muted" in " ".join(sibling.xpath("./@class")):
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
        return joiner.join(cleaned) if joiner else "".join(cleaned)

    def _parse_detail_page(self, html, vod_id):
        root = self.html(html)
        detail_root = (root.xpath("//*[contains(@class,'stui-content__detail')][1]") or [root])[0]
        title = ((detail_root.xpath(".//*[contains(@class,'title')][1]//text()") or [""])[0]).strip()
        pic = (
            (root.xpath("//*[contains(@class,'stui-content__thumb')]//img/@data-original") or [""])[0].strip()
            or (root.xpath("//*[contains(@class,'stui-content__thumb')]//img/@src") or [""])[0].strip()
        )

        episodes = []
        seen = set()
        for playlist in root.xpath("//*[contains(@class,'stui-content__playlist')]"):
            heading = self._clean_text("".join(playlist.xpath("./preceding-sibling::*[1]//text()")))
            if any(keyword in heading for keyword in ("夸克", "UC", "网盘")):
                continue
            for anchor in playlist.xpath(".//a[@href]"):
                play_id = self._extract_play_id((anchor.xpath("./@href") or [""])[0])
                name = self._clean_text("".join(anchor.xpath(".//text()")))
                if not play_id or not name or play_id in seen:
                    continue
                seen.add(play_id)
                episodes.append(f"{name}${play_id}")

        netdisk_groups = self._extract_netdisk_sources(html)
        play_from = ["LibVIO"] if episodes else []
        play_url = ["#".join(episodes)] if episodes else []
        for group in netdisk_groups:
            play_from.append(group["from"])
            play_url.append(group["urls"])

        vod = {
            "vod_id": vod_id,
            "path": self._build_detail_request_url(vod_id),
            "vod_name": title,
            "vod_pic": self._build_url(pic),
            "vod_tag": "",
            "vod_time": "",
            "vod_remarks": "",
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
            "type_name": self._extract_detail_field(detail_root, "类型"),
            "vod_content": self._extract_detail_field(detail_root, "简介"),
            "vod_year": self._extract_detail_field(detail_root, "年份"),
            "vod_area": self._extract_detail_field(detail_root, "地区"),
            "vod_lang": "",
            "vod_director": self._extract_detail_field(detail_root, "导演", joiner=","),
            "vod_actor": self._extract_detail_field(detail_root, "主演", joiner=","),
        }
        return {"list": [vod]}

    def _extract_netdisk_sources(self, html):
        root = self.html(html)
        if root is None:
            return []

        groups = []
        for panel in root.xpath("//*[contains(@class,'netdisk-panel')]"):
            heading = self._clean_text("".join(panel.xpath(".//h3[1]//text()")))
            matched = re.search(r"\(([^()]+)\)", heading)
            line_name = self._clean_text(matched.group(1) if matched else heading.replace("视频下载", "")) or "网盘资源"

            entries = []
            seen_links = set()
            for anchor in panel.xpath(".//a[contains(@class,'netdisk-item')]"):
                href = ((anchor.xpath("./@href") or [""])[0]).strip()
                url_text = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'netdisk-url')][1]//text()")))
                link = url_text or href
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                title = self._clean_text("".join(anchor.xpath(".//*[contains(@class,'netdisk-name')][1]//text()"))) or line_name
                entries.append(f"{title}${link}")

            if entries:
                groups.append({"from": line_name, "urls": "#".join(entries)})
        return groups

    def homeVideoContent(self):
        html = self._request_html("/", expect_xpath="//*[contains(@class,'stui-vodlist__box')]")
        return {"list": self._parse_list_cards(html)}

    def categoryContent(self, tid, pg, filter, extend):
        path = self.category_paths.get(tid, self.category_paths["movie"]).format(pg=pg)
        html = self._request_html(path, expect_xpath="//*[contains(@class,'stui-vodlist__box')]")
        return self._page_result(self._parse_list_cards(html), pg)

    def searchContent(self, key, quick, pg="1"):
        path = "/search/-------------.html?wd={0}".format(quote(key))
        html = self._request_html(path, expect_xpath="//*[contains(@class,'stui-vodlist__box')]")
        return self._page_result(self._parse_list_cards(html), pg)

    def detailContent(self, ids):
        vod_id = ids[0]
        html = self._request_html(
            self._build_detail_request_url(vod_id),
            expect_xpath="//*[contains(@class,'stui-content__playlist')]",
        )
        return self._parse_detail_page(html, vod_id)

    def _parse_player_config(self, html):
        matched = re.search(r"player_[a-z0-9_]+\s*=\s*(\{[\s\S]*?\})\s*;?", html, re.I)
        if not matched:
            return None
        try:
            return json.loads(matched.group(1))
        except Exception:
            return None

    def _extract_play_api_base(self, body):
        matched = re.search(r'src\s*=\s*["\']([^"\']+)["\']', body, re.I)
        if not matched:
            return ""
        return self._build_url(matched.group(1))

    def _extract_playable_url(self, body):
        patterns = [
            r'["\']?urls?["\']?\s*:\s*["\']([^"\']+)["\']',
            r'(?:var|let|const)\s+urls?\s*=\s*["\']([^"\']+)["\']',
            r'["\']url["\']\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'url\s*=\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
        ]
        text = str(body or "")
        for pattern in patterns:
            matched = re.search(pattern, text, re.I)
            if matched:
                return self._build_url(matched.group(1).replace("\\/", "/").replace("&amp;", "&").strip())
        return ""

    def _request_player_js(self, source):
        return self._request_html(f"/static/player/{source}.js", referer=self.host + "/")

    def playerContent(self, flag, id, vipFlags):
        raw_id = str(id or "").strip()
        if raw_id.startswith(("https://", "http://")) and any(
            token in raw_id for token in ("drive.uc.cn", "pan.quark.cn", "pan.baidu.com", "alipan.com", "aliyundrive.com")
        ):
            return {"parse": 0, "playUrl": "", "url": raw_id}

        play_page_url = self._build_play_request_url(id)
        detail_html = self._request_html(play_page_url, referer=self.host + "/")
        config = self._parse_player_config(detail_html)
        if not config or config.get("from") in ("kuake", "uc"):
            return {"parse": 0, "playUrl": "", "url": ""}

        if config.get("from") == "ty_new1":
            api_body = self._request_html(f"/vid/ty4.php?url={config.get('url', '')}", referer=self.host + "/")
            final_url = self._extract_playable_url(api_body)
        else:
            player_js = self._request_player_js(config.get("from", ""))
            api_base = self._extract_play_api_base(player_js)
            api_url = "{base}{url}&next={next}&id={id}&nid={nid}".format(
                base=api_base,
                url=config.get("url", ""),
                next=config.get("link_next", ""),
                id=config.get("id", ""),
                nid=config.get("nid", ""),
            )
            api_body = self._request_html(api_url, referer=self.host + "/")
            final_url = self._extract_playable_url(api_body)

        if not final_url:
            return {"parse": 0, "playUrl": "", "url": ""}

        return {
            "parse": 0,
            "playUrl": "",
            "url": final_url,
            "header": {
                "User-Agent": self.headers["User-Agent"],
                "Referer": self.host + "/",
            },
        }
