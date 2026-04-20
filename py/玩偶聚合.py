# coding=utf-8
import base64
import json
import os
import re
import sys
from urllib.parse import quote

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "玩偶聚合"
        self.filter_root = os.path.join(os.path.dirname(__file__), "../筛选")
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            )
        }
        self.site_priority = [
            "wanou",
            "muou",
            "labi",
            "zhizhen",
            "erxiao",
            "huban",
            "kuaiying",
            "shandian",
            "ouge",
        ]
        self.pan_priority = {
            "baidu": 1,
            "a139": 2,
            "a189": 3,
            "a123": 4,
            "a115": 5,
            "quark": 6,
            "xunlei": 7,
            "aliyun": 8,
            "uc": 9,
        }
        self.sites = [
            {
                "id": "wanou",
                "name": "玩偶",
                "domains": ["https://www.wogg.net"],
                "filter_files": ["wogg.json"],
                "list_xpath": "//*[contains(@class,'module-item')]",
                "search_xpath": "//*[contains(@class,'module-search-item')]",
                "detail_pan_xpath": "//*[contains(@class,'module-row-info')]//p",
                "category_url": "/vodshow/{categoryId}--------{page}---.html",
                "category_url_with_filters": "/vodshow/{categoryId}-{area}-{by}-{class}-----{page}---{year}.html",
                "search_url": "/vodsearch/-------------.html?wd={keyword}&page={page}",
                "default_categories": [("1", "电影"), ("2", "电视剧"), ("3", "动漫"), ("4", "综艺")],
            },
            {
                "id": "muou",
                "name": "木偶",
                "domains": ["https://www.muou.site"],
                "filter_files": ["mogg.json"],
                "list_xpath": "//*[contains(@class,'module-item')]",
                "search_xpath": "//*[contains(@class,'module-search-item')]",
                "detail_pan_xpath": "//*[contains(@class,'module-row-info')]//p",
                "category_url": "/vodshow/{categoryId}--------{page}---.html",
                "search_url": "/vodsearch/-------------.html?wd={keyword}&page={page}",
                "default_categories": [("1", "电影"), ("2", "电视剧"), ("3", "动漫"), ("29", "综艺")],
            },
            {
                "id": "labi",
                "name": "蜡笔",
                "domains": ["http://xiaocge.fun"],
                "filter_files": ["labi.json"],
                "list_xpath": "//*[contains(@class,'module-item')]",
                "search_xpath": "//*[contains(@class,'module-search-item')]",
                "detail_pan_xpath": "//*[contains(@class,'module-row-info')]//p",
                "category_url": "/vodshow/{categoryId}--------{page}---.html",
                "search_url": "/vodsearch/-------------.html?wd={keyword}&page={page}",
                "default_categories": [("1", "电影"), ("2", "电视剧"), ("3", "动漫"), ("4", "综艺")],
            },
        ]

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeVideoContent(self):
        return {"list": []}

    def _load_local_filter_groups(self, site):
        return []

    def _build_site_filters(self, site):
        groups = [
            {
                "key": "categoryId",
                "name": "分类",
                "init": site["default_categories"][0][0],
                "value": [{"n": "全部", "v": ""}]
                + [{"n": name, "v": cid} for cid, name in site["default_categories"]],
            }
        ]
        groups.extend(self._load_local_filter_groups(site))
        return groups

    def homeContent(self, filter):
        classes = [{"type_id": f"site_{site['id']}", "type_name": site["name"]} for site in self.sites]
        filters = {f"site_{site['id']}": self._build_site_filters(site) for site in self.sites}
        return {"class": classes, "filters": filters}

    def _encode_site_vod_id(self, site_id, path):
        return f"site:{site_id}:{path}"

    def _decode_site_vod_id(self, value):
        prefix, site_id, path = str(value).split(":", 2)
        if prefix != "site":
            raise ValueError("not site vod id")
        return {"site": site_id, "path": path}

    def _encode_aggregate_vod_id(self, payload):
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return "agg:" + base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    def _decode_aggregate_vod_id(self, value):
        encoded = str(value)[4:]
        padded = encoded + "=" * (-len(encoded) % 4)
        return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))

    def _normalize_title(self, value):
        text = str(value or "").lower()
        text = re.sub(r"(4k|hdr|2160p|1080p|720p|玩偶|木偶|蜡笔)", "", text, flags=re.I)
        text = re.sub(r"[\s\-_.·,，。!！?:：()（）\[\]]+", "", text)
        return text

    def _is_same_title(self, left, right):
        left_year = str(left.get("vod_year") or "").strip()
        right_year = str(right.get("vod_year") or "").strip()
        if left_year and right_year and left_year != right_year:
            return False
        return self._normalize_title(left.get("vod_name")) == self._normalize_title(right.get("vod_name"))

    def _get_site(self, site_id):
        for site in self.sites:
            if site["id"] == site_id:
                return site
        return None

    def _build_absolute_url(self, base, path):
        raw = str(path or "").strip()
        if not raw:
            return ""
        if raw.startswith(("http://", "https://")):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return str(base).rstrip("/") + "/" + raw.lstrip("/")

    def _build_category_url(self, site, category_id, pg, extend):
        values = dict(extend or {})
        values.setdefault("categoryId", category_id)
        values.setdefault("area", "")
        values.setdefault("by", values.get("sort", ""))
        values.setdefault("class", "")
        values.setdefault("year", "")
        if site.get("category_url_with_filters") and any(values.get(key) for key in ("area", "by", "class", "year")):
            path = site["category_url_with_filters"].format(
                **{
                    "categoryId": values["categoryId"],
                    "area": quote(str(values["area"])),
                    "by": quote(str(values["by"])),
                    "class": quote(str(values["class"])),
                    "page": int(pg),
                    "year": quote(str(values["year"])),
                }
            )
        else:
            path = site["category_url"].format(categoryId=values["categoryId"], page=int(pg))
        return self._build_absolute_url(site["domains"][0], path)

    def _request_with_failover(self, site, path_or_url, referer=None):
        last_error = None
        for index, domain in enumerate(list(site["domains"])):
            target = path_or_url if str(path_or_url).startswith("http") else self._build_absolute_url(domain, path_or_url)
            try:
                headers = dict(self.headers)
                headers["Referer"] = referer or self._build_absolute_url(domain, "/")
                response = self.fetch(target, headers=headers, timeout=10)
                if response.status_code == 200 and response.text:
                    if index > 0:
                        site["domains"].insert(0, site["domains"].pop(index))
                    return response.text
            except Exception as exc:
                last_error = exc
        raise RuntimeError(str(last_error or "all domains failed"))

    def _parse_cards(self, site, html):
        root = self.html(html)
        if root is None:
            return []

        items = []
        seen = set()
        for card in root.xpath(site["list_xpath"]):
            href = ((card.xpath(".//a[@href][1]/@href") or [""])[0]).strip()
            title = (
                ((card.xpath(".//img[@alt][1]/@alt") or [""])[0]).strip()
                or ((card.xpath(".//a[@title][1]/@title") or [""])[0]).strip()
            )
            pic = (
                ((card.xpath(".//img[@data-src][1]/@data-src") or [""])[0]).strip()
                or ((card.xpath(".//img[@src][1]/@src") or [""])[0]).strip()
            )
            remarks = "".join(card.xpath(".//*[contains(@class,'module-item-text')][1]//text()")).strip()
            if not href or not title or href in seen:
                continue
            seen.add(href)
            items.append(
                {
                    "vod_id": self._encode_site_vod_id(site["id"], href),
                    "vod_name": title,
                    "vod_pic": self._build_absolute_url(site["domains"][0], pic),
                    "vod_remarks": remarks,
                    "vod_year": "",
                    "_site": site["id"],
                    "_detail_path": href,
                }
            )
        return items

    def categoryContent(self, tid, pg, filter, extend):
        site_id = str(tid).replace("site_", "", 1)
        site = self._get_site(site_id)
        values = extend if isinstance(extend, dict) else {}
        category_id = values.get("categoryId") or site["default_categories"][0][0]
        html = self._request_with_failover(site, self._build_category_url(site, category_id, pg, values))
        items = self._parse_cards(site, html)
        return {"list": items, "page": int(pg), "limit": len(items), "total": int(pg) * 20 + len(items)}

    def _site_rank(self, site_id):
        try:
            return self.site_priority.index(site_id)
        except ValueError:
            return 999

    def _parse_search_cards(self, site, html):
        root = self.html(html)
        if root is None:
            return []

        items = []
        seen = set()
        xpath = site.get("search_xpath") or site["list_xpath"]
        for card in root.xpath(xpath):
            href = (
                ((card.xpath(".//*[contains(@class,'video-serial')][1]/@href") or [""])[0]).strip()
                or ((card.xpath(".//*[@href][1]/@href") or [""])[0]).strip()
            )
            title = (
                ((card.xpath(".//*[contains(@class,'video-serial')][1]/@title") or [""])[0]).strip()
                or ((card.xpath(".//img[@alt][1]/@alt") or [""])[0]).strip()
                or ((card.xpath(".//*[@title][1]/@title") or [""])[0]).strip()
            )
            pic = (
                ((card.xpath(".//img[@data-src][1]/@data-src") or [""])[0]).strip()
                or ((card.xpath(".//img[@src][1]/@src") or [""])[0]).strip()
            )
            remarks = "".join(card.xpath(".//*[contains(@class,'module-item-text')][1]//text()")).strip()
            if not href or not title or href in seen:
                continue
            seen.add(href)
            items.append(
                {
                    "vod_id": self._encode_site_vod_id(site["id"], href),
                    "vod_name": title,
                    "vod_pic": self._build_absolute_url(site["domains"][0], pic),
                    "vod_remarks": remarks,
                    "vod_year": "",
                    "_site": site["id"],
                    "_detail_path": href,
                }
            )
        return items

    def _fetch_site_search(self, site, keyword, pg):
        search_path = site["search_url"].format(keyword=quote(str(keyword)), page=int(pg))
        html = self._request_with_failover(site, search_path)
        return self._parse_search_cards(site, html)

    def _aggregate_search_results(self, items):
        groups = []
        for item in items:
            matched_group = None
            for group in groups:
                if self._is_same_title(group[0], item):
                    matched_group = group
                    break
            if matched_group is None:
                groups.append([item])
            else:
                matched_group.append(item)

        result = []
        for group in groups:
            group.sort(key=lambda item: self._site_rank(item["_site"]))
            primary = group[0]
            payload = [
                {
                    "site": item["_site"],
                    "path": item["_detail_path"],
                    "name": item.get("vod_name", ""),
                    "year": item.get("vod_year", ""),
                }
                for item in group
            ]
            result.append(
                {
                    "vod_id": self._encode_aggregate_vod_id(payload),
                    "vod_name": primary["vod_name"],
                    "vod_pic": primary.get("vod_pic", ""),
                    "vod_remarks": primary.get("vod_remarks", ""),
                    "vod_year": primary.get("vod_year", ""),
                }
            )
        return result

    def searchContent(self, key, quick, pg="1"):
        page = int(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return {"page": page, "total": 0, "list": []}

        all_items = []
        for site in self.sites:
            try:
                all_items.extend(self._fetch_site_search(site, keyword, page))
            except Exception:
                continue

        merged = self._aggregate_search_results(all_items)
        return {"page": page, "total": len(merged), "list": merged}

    def _detect_pan_type(self, url):
        value = str(url or "").lower()
        if "pan.baidu.com" in value:
            return "baidu", "百度资源"
        if "pan.quark.cn" in value:
            return "quark", "夸克资源"
        if "drive.uc.cn" in value:
            return "uc", "UC资源"
        if "alipan.com" in value or "aliyundrive.com" in value:
            return "aliyun", "阿里资源"
        if "pan.xunlei.com" in value:
            return "xunlei", "迅雷资源"
        if "123pan.com" in value:
            return "a123", "123资源"
        if "115.com" in value:
            return "a115", "115资源"
        if "189.cn" in value:
            return "a189", "天翼资源"
        if "139.com" in value:
            return "a139", "移动云资源"
        return "", ""

    def _join_next_sibling_links(self, root, label):
        values = []
        labels = root.xpath(f"//*[contains(@class,'video-info-itemtitle') and contains(normalize-space(.), '{label}')]")
        for node in labels:
            sibling = node.getnext()
            if sibling is None:
                continue
            for text in sibling.xpath(".//a/text()"):
                clean = str(text).strip()
                if clean:
                    values.append(clean)
        unique = []
        for value in values:
            if value not in unique:
                unique.append(value)
        return ",".join(unique)

    def _join_next_sibling_text(self, root, label):
        labels = root.xpath(f"//*[contains(@class,'video-info-itemtitle') and contains(normalize-space(.), '{label}')]")
        for node in labels:
            sibling = node.getnext()
            if sibling is None:
                continue
            text = "".join(sibling.xpath(".//text()")).strip()
            if text:
                return text
        return ""

    def _parse_detail_page(self, site, detail_path, html):
        root = self.html(html)
        if root is None:
            return {
                "vod_name": "",
                "vod_pic": "",
                "vod_year": "",
                "vod_director": "",
                "vod_actor": "",
                "vod_content": "",
                "pan_urls": [],
                "_site_name": site["name"],
            }

        title = "".join(root.xpath("//*[contains(@class,'page-title')][1]//text()")).strip()
        pic = ((root.xpath("//*[contains(@class,'mobile-play')]//img[1]/@data-src") or [""])[0]).strip()
        pan_urls = []
        for node in root.xpath(site["detail_pan_xpath"]):
            text = "".join(node.xpath(".//text()")).strip()
            if text.startswith("http"):
                pan_urls.append(text)

        return {
            "vod_name": title,
            "vod_pic": self._build_absolute_url(site["domains"][0], pic),
            "vod_year": "",
            "vod_director": self._join_next_sibling_links(root, "导演"),
            "vod_actor": self._join_next_sibling_links(root, "主演"),
            "vod_content": self._join_next_sibling_text(root, "剧情"),
            "pan_urls": pan_urls,
            "_site_name": site["name"],
        }

    def _fetch_site_detail(self, site, detail_path):
        html = self._request_with_failover(site, detail_path)
        return self._parse_detail_page(site, detail_path, html)

    def _build_pan_lines(self, detail):
        lines = []
        seen = set()
        for url in detail.get("pan_urls", []):
            pan_type, title = self._detect_pan_type(url)
            if not pan_type or url in seen:
                continue
            seen.add(url)
            lines.append(
                (
                    self.pan_priority.get(pan_type, 999),
                    f"{pan_type}#{detail['_site_name']}",
                    f"{title}${url}",
                )
            )
        lines.sort(key=lambda item: item[0])
        return lines

    def detailContent(self, ids):
        vod_id = ids[0]
        if str(vod_id).startswith("agg:"):
            payload = self._decode_aggregate_vod_id(vod_id)
            details = []
            for item in payload:
                site = self._get_site(item["site"])
                try:
                    details.append(self._fetch_site_detail(site, item["path"]))
                except Exception:
                    continue

            primary = details[0]
            all_lines = []
            seen_urls = set()
            for detail in details:
                for _, line_from, line_url in self._build_pan_lines(detail):
                    share_url = line_url.split("$", 1)[1]
                    if share_url in seen_urls:
                        continue
                    seen_urls.add(share_url)
                    all_lines.append((line_from, line_url))

            return {
                "list": [
                    {
                        "vod_id": vod_id,
                        "vod_name": primary["vod_name"],
                        "vod_pic": primary["vod_pic"],
                        "vod_year": primary["vod_year"],
                        "vod_director": primary["vod_director"],
                        "vod_actor": primary["vod_actor"],
                        "vod_content": primary["vod_content"],
                        "vod_play_from": "$$$".join([item[0] for item in all_lines]),
                        "vod_play_url": "$$$".join([item[1] for item in all_lines]),
                    }
                ]
            }

        info = self._decode_site_vod_id(vod_id)
        site = self._get_site(info["site"])
        detail = self._fetch_site_detail(site, info["path"])
        lines = self._build_pan_lines(detail)
        return {
            "list": [
                {
                    "vod_id": vod_id,
                    "vod_name": detail["vod_name"],
                    "vod_pic": detail["vod_pic"],
                    "vod_year": detail["vod_year"],
                    "vod_director": detail["vod_director"],
                    "vod_actor": detail["vod_actor"],
                    "vod_content": detail["vod_content"],
                    "vod_play_from": "$$$".join([item[1] for item in lines]),
                    "vod_play_url": "$$$".join([item[2] for item in lines]),
                }
            ]
        }
