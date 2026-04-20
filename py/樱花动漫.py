# coding=utf-8
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "樱花动漫"
        self.host = "https://www.dmvvv.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.dmvvv.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.classes = [
            {"type_id": "guoman", "type_name": "国产动漫"},
            {"type_id": "riman", "type_name": "日本动漫"},
            {"type_id": "oman", "type_name": "欧美动漫"},
            {"type_id": "dmfilm", "type_name": "动漫电影"},
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.classes}

    def homeVideoContent(self):
        html = self._get_html(self.host + "/")
        items = self._parse_list(html)
        seen = set()
        unique = []
        for item in items:
            if item["vod_id"] not in seen:
                seen.add(item["vod_id"])
                unique.append(item)
        return {"list": unique[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg)
        url = f"{self.host}/type/{tid}/" if page <= 1 else f"{self.host}/type/{tid}/{page}/"
        html = self._get_html(url)
        items = self._parse_list(html)
        pagecount = self._parse_page_count(html, tid)
        if pagecount <= page and len(items) >= 36:
            pagecount = page + 1
        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "total": pagecount * len(items) if items else 0,
        }

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, list) else ids
        url = raw_id if raw_id.startswith("http") else self.host + raw_id
        html = self._get_html(url)
        vod = self._parse_detail(html, raw_id)
        return {"list": [vod] if vod else []}

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = key.strip()
        if not keyword:
            return {"list": [], "page": page, "pagecount": 0, "total": 0}
        encoded = quote(keyword)
        url = (
            f"{self.host}/search/?wd={encoded}"
            if page <= 1
            else f"{self.host}/search/?wd={encoded}&pageno={page}"
        )
        html = self._get_html(url)
        items = self._parse_search_list(html)
        pagecount = self._parse_search_page_count(html, page, len(items))
        return {
            "list": items[:10] if quick else items,
            "page": page,
            "pagecount": pagecount,
            "total": len(items),
        }

    def playerContent(self, flag, id, vipFlags):
        url = id if id.startswith("http") else self.host + id
        html = self._get_html(url)
        play_url = self._extract_play_url(html, url)
        return {
            "parse": 0,
            "url": play_url,
            "header": {
                "User-Agent": self.headers["User-Agent"],
                "Referer": self.host + "/",
            },
        }

    # --- helpers ---

    def _s(self, val):
        return "" if val is None else str(val).strip()

    def _get_html(self, url):
        rsp = self.fetch(url, headers=self.headers, timeout=15, verify=False)
        if rsp.status_code != 200:
            return ""
        return rsp.text or ""

    def _parse_list(self, html):
        root = self.html(html)
        if root is None:
            return []
        items = []
        for li in root.xpath("//li"):
            link = li.xpath(".//a[@href]")
            if not link:
                continue
            href = self._s(link[0].get("href", ""))
            title = self._s(link[0].get("title", ""))
            if not href or "/detail/" not in href or not title:
                continue
            pic = self._s((li.xpath(".//img/@data-original") or li.xpath(".//img/@src") or [""])[0])
            remarks = self._s((li.xpath(".//p//text()") or [""])[0])
            items.append({
                "vod_id": href,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": remarks,
            })
        return items

    def _parse_search_list(self, html):
        items = []
        pattern = re.compile(r'<a class="cover" href="(/detail/\d+/)"', re.S)
        for block in re.finditer(r"<li>\s*<a class=\"cover\".*?</li>", html, re.S):
            chunk = block.group(0)
            href_m = pattern.search(chunk)
            if not href_m:
                continue
            title_m = re.search(r'title="([^"]+)"', chunk)
            cover_m = re.search(r'data-original="([^"]+)"', chunk)
            remark_m = re.search(r'<div class="item"><span>状态:</span>([^<]*)', chunk)
            if not title_m:
                continue
            items.append({
                "vod_id": href_m.group(1),
                "vod_name": title_m.group(1).strip(),
                "vod_pic": cover_m.group(1).strip() if cover_m else "",
                "vod_remarks": remark_m.group(1).strip() if remark_m else "",
            })
        return items

    def _parse_page_count(self, html, tid):
        max_page = 1
        for m in re.finditer(r"/type/[^/]+/(\d+)/", html):
            max_page = max(max_page, int(m.group(1)))
        for m in re.finditer(r"[?&]page(?:no)?=(\d+)", html):
            max_page = max(max_page, int(m.group(1)))
        return max_page

    def _parse_search_page_count(self, html, current_page, result_count):
        total_m = re.search(r"找到\s*<em>(\d+)</em>", html)
        if total_m:
            return max(1, -(-int(total_m.group(1)) // 12))
        max_page = current_page
        for m in re.finditer(r"pageno=(\d+)", html):
            max_page = max(max_page, int(m.group(1)))
        if max_page == current_page and result_count >= 12:
            return current_page + 1
        return max(max_page, 1)

    def _parse_detail(self, html, raw_id):
        root = self.html(html)
        if root is None:
            return None
        title = ""
        title_m = re.search(r'<div class="detail">.*?<h2>([^<]+)</h2>', html, re.S)
        if title_m:
            title = title_m.group(1).strip()
        if not title:
            title_m2 = re.search(r"<title>([^<]+)", html)
            if title_m2:
                title = title_m2.group(1).split("-")[0].strip()

        cover = ""
        cover_m = re.search(r'<div class="cover">\s*<img[^>]+data-original="([^"]+)"', html, re.S)
        if cover_m:
            cover = cover_m.group(1)

        def get_info(label, use_em=True):
            pat = rf'<span>{label}:</span><em>([^<]+)</em>' if use_em else rf'<span>{label}:</span>([^<]+)'
            m = re.search(pat, html)
            return m.group(1).strip() if m else ""

        vod_remarks = get_info("状态", True)
        vod_year = get_info("年份", False)
        vod_area = get_info("地区", False)
        vod_type = get_info("类型", False)
        vod_actor = get_info("主演", False)

        vod_content = ""
        desc_m = re.search(r'class="blurb"[^>]*>.*?<span>[^<]+</span>(.*?)</li>', html, re.S)
        if desc_m:
            vod_content = re.sub(r"<[^>]+>", "", desc_m.group(1)).strip()

        play_data = self._parse_play_sources(html, raw_id)

        return {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": cover,
            "vod_year": vod_year,
            "vod_area": vod_area,
            "vod_type": vod_type,
            "vod_actor": vod_actor,
            "vod_remarks": vod_remarks,
            "vod_content": vod_content,
            "vod_play_from": play_data["vod_play_from"],
            "vod_play_url": play_data["vod_play_url"],
        }

    def _parse_play_sources(self, html, raw_id):
        root = self.html(html)
        if root is None:
            return {"vod_play_from": "default", "vod_play_url": ""}
        source_names = ["高清", "ikun", "非凡", "量子"]
        # collect tab names in order
        tabs = []
        for idx, tab in enumerate(root.xpath("//*[contains(@class,'module-tab-item') or contains(@class,'tab-item')]")):
            name = self._s(tab.xpath("string(.)")).strip()
            if not name:
                name = source_names[idx] if idx < len(source_names) else f"线路{idx+1}"
            tabs.append(name)
        # group episodes by source index from URL: /play/{vid}-{sourceIdx}-{epIdx}/
        grouped = {}
        all_links = root.xpath("//*[contains(@class,'module-play-list')]//a[@href] | //*[contains(@class,'playlist')]//a[@href]")
        # fallback: try all links under .scroll-content or .module-list
        if not all_links:
            all_links = root.xpath("//*[contains(@class,'scroll-content') or contains(@class,'module-list')]//a[@href]")
        for a in all_links:
            ep_name = self._s(a.xpath("string(.)")).strip()
            ep_url = self._s(a.get("href", ""))
            if not ep_name or not ep_url or ep_url.startswith(("javascript:", "#")):
                continue
            m = re.search(r"/play/\d+-(\d+)-\d+/", ep_url)
            if m:
                src_idx = int(m.group(1)) - 1
            else:
                src_idx = 0
            if src_idx not in grouped:
                grouped[src_idx] = []
            grouped[src_idx].append(f"{ep_name}${ep_url}")
        if not grouped:
            return {"vod_play_from": "default", "vod_play_url": ""}
        # build output ordered by source index
        play_from = []
        play_url = []
        for src_idx in sorted(grouped.keys()):
            name = tabs[src_idx] if src_idx < len(tabs) else (source_names[src_idx] if src_idx < len(source_names) else f"线路{src_idx+1}")
            play_from.append(name)
            play_url.append("#".join(grouped[src_idx]))
        return {
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }

    def _extract_play_url(self, html, fallback_url):
        m = re.search(r"url:\s*'(https?://[^']+)'", html)
        if m:
            return m.group(1)
        m = re.search(r"(https?://[^\s'\"<>]+\.m3u8(?:\?[^\s'\"<>]*)?)", html)
        if m:
            return m.group(1)
        return fallback_url
