# coding=utf-8
import base64
import json
import re
import sys
from urllib.parse import quote, urljoin

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

from base.spider import Spider as BaseSpider

sys.path.append("..")


class Spider(BaseSpider):
    def __init__(self):
        self.name = "厂长资源"
        self.hosts = [
            "https://www.czzy89.com",
            "https://www.cz01.org",
        ]
        self.current_host = self.hosts[0]
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.categories = [
            {"type_name": "电影", "type_id": "movie"},
            {"type_name": "电视剧", "type_id": "tv"},
            {"type_name": "动漫", "type_id": "anime"},
            {"type_name": "华语电影", "type_id": "cn_movie"},
            {"type_name": "印度电影", "type_id": "in_movie"},
            {"type_name": "俄罗斯电影", "type_id": "ru_movie"},
            {"type_name": "加拿大电影", "type_id": "ca_movie"},
            {"type_name": "日本电影", "type_id": "jp_movie"},
            {"type_name": "韩国电影", "type_id": "kr_movie"},
            {"type_name": "欧美电影", "type_id": "western_movie"},
            {"type_name": "国产剧", "type_id": "cn_drama"},
            {"type_name": "日剧", "type_id": "jp_drama"},
            {"type_name": "美剧", "type_id": "us_drama"},
            {"type_name": "韩剧", "type_id": "kr_drama"},
            {"type_name": "海外剧", "type_id": "intl_drama"},
        ]
        self.category_paths = {
            "movie": "/movie_bt/movie_bt_series/dyy/page/{pg}",
            "tv": "/movie_bt/movie_bt_series/dianshiju/page/{pg}",
            "anime": "/movie_bt/movie_bt_series/dohua/page/{pg}",
            "cn_movie": "/movie_bt/movie_bt_series/huayudianying/page/{pg}",
            "in_movie": "/movie_bt/movie_bt_series/yindudianying/page/{pg}",
            "ru_movie": "/movie_bt/movie_bt_series/eluosidianying/page/{pg}",
            "ca_movie": "/movie_bt/movie_bt_series/jianadadianying/page/{pg}",
            "jp_movie": "/movie_bt/movie_bt_series/ribendianying/page/{pg}",
            "kr_movie": "/movie_bt/movie_bt_series/hanguodianying/page/{pg}",
            "western_movie": "/movie_bt/movie_bt_series/meiguodianying/page/{pg}",
            "cn_drama": "/movie_bt/movie_bt_series/guochanju/page/{pg}",
            "jp_drama": "/movie_bt/movie_bt_series/rj/page/{pg}",
            "us_drama": "/movie_bt/movie_bt_series/mj/page/{pg}",
            "kr_drama": "/movie_bt/movie_bt_series/hj/page/{pg}",
            "intl_drama": "/movie_bt/movie_bt_series/hwj/page/{pg}",
        }

    def init(self, extend=""):
        return None

    def getName(self):
        return self.name

    def homeContent(self, filter):
        return {"class": self.categories}

    def homeVideoContent(self):
        return {"list": []}

    def _request_html(self, path_or_url, expect_xpath=None, referer=None):
        candidates = [self.current_host] + [host for host in self.hosts if host != self.current_host]
        last_error = None

        for host in candidates:
            target = path_or_url if path_or_url.startswith("http") else urljoin(host, path_or_url)
            headers = dict(self.headers)
            if referer:
                headers["Referer"] = referer
            try:
                response = self.fetch(target, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                html = response.text or ""
                if expect_xpath:
                    root = self.html(html)
                    if root is None or not root.xpath(expect_xpath):
                        continue
                self.current_host = host
                return html, host
            except Exception as exc:
                last_error = exc

        if last_error:
            raise last_error
        return "", self.current_host

    def _normalize_url(self, value, host):
        value = (value or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        return urljoin(host, value)

    def _extract_meta_value(self, root, labels):
        for text in root.xpath("//li/text()"):
            clean = text.strip()
            for label in labels:
                if clean.startswith(label):
                    return clean.split("：", 1)[-1].strip()
        return ""

    def _page_result(self, items, pg):
        page = int(pg)
        pagecount = page + 1 if items else page
        return {
            "list": items,
            "page": page,
            "pagecount": pagecount,
            "limit": len(items),
            "total": pagecount * max(len(items), 1),
        }

    def _parse_media_cards(self, html, host):
        root = self.html(html)
        results = []
        if root is None:
            return results

        for item in root.xpath("//li[.//a[@href]]"):
            href = (item.xpath(".//a[@href][1]/@href") or [""])[0].strip()
            if not href:
                continue

            title = (
                (item.xpath(".//img[@alt][1]/@alt") or [""])[0].strip()
                or (item.xpath(".//a[@title][1]/@title") or [""])[0].strip()
                or "".join(item.xpath(".//a[1]//text()")).strip()
            )

            pic = ""
            for expr in [
                ".//img[@data-original][1]/@data-original",
                ".//img[@data-src][1]/@data-src",
                ".//img[@src][1]/@src",
            ]:
                pic = (item.xpath(expr) or [""])[0].strip()
                if pic:
                    break

            remarks = (
                (item.xpath(".//*[contains(@class,'jidi')][1]/text()") or [""])[0].strip()
                or (item.xpath(".//*[contains(@class,'hdinfo')][1]/text()") or [""])[0].strip()
            )

            results.append(
                {
                    "vod_id": href,
                    "vod_name": title or "未命名",
                    "vod_pic": urljoin(host, pic) if pic.startswith("/") else pic,
                    "vod_remarks": remarks,
                }
            )

        return results

    def _parse_detail_page(self, html, host, vod_id):
        root = self.html(html)
        title = ((root.xpath("//h1/text()") or [""])[0]).strip()
        pic = ((root.xpath("//img[@src][1]/@src") or [""])[0]).strip()
        content = "".join(root.xpath("//*[contains(@class,'yp_context')][1]//text()")).strip()

        direct = []
        for anchor in root.xpath("//*[contains(@class,'paly_list_btn')]//a[@href]"):
            name = "".join(anchor.xpath(".//text()")).strip() or "播放"
            href = self._normalize_url((anchor.xpath("./@href") or [""])[0], host)
            if href:
                direct.append(f"{name}${href}")

        pan = []
        for anchor in root.xpath("//*[contains(@class,'ypbt_down_list')]//a[@href]"):
            name = "".join(anchor.xpath(".//text()")).strip() or "网盘资源"
            href = self._normalize_url((anchor.xpath("./@href") or [""])[0], host)
            if href:
                pan.append(f"{name}${href}")

        play_from = []
        play_url = []
        if direct:
            play_from.append("厂长资源")
            play_url.append("#".join(dict.fromkeys(direct)))
        if pan:
            play_from.append("网盘资源")
            play_url.append("#".join(dict.fromkeys(pan)))

        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": self._normalize_url(pic, host),
            "vod_year": self._extract_meta_value(root, ["年份："]),
            "vod_area": self._extract_meta_value(root, ["地区："]),
            "vod_actor": self._extract_meta_value(root, ["主演："]),
            "vod_director": self._extract_meta_value(root, ["导演："]),
            "vod_content": content,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }
        return {"list": [vod]}

    def _extract_iframe_src(self, html, host):
        match = re.search(r"<iframe[^>]+src=['\"]([^'\"]+)['\"]", html, re.I)
        if not match:
            return ""
        return self._normalize_url(match.group(1), host)

    def _decode_data_url(self, value):
        try:
            encrypted = value[::-1]
            temp = ""
            for idx in range(0, len(encrypted), 2):
                pair = encrypted[idx:idx + 2]
                if len(pair) == 2:
                    temp += chr(int(pair, 16))
            middle = (len(temp) - 7) // 2
            return temp[:middle] + temp[middle + 7:]
        except Exception:
            return ""

    def _decrypt_player_payload(self, cipher_text, iv):
        try:
            cipher = AES.new(b"VFBTzdujpR9FWBhe", AES.MODE_CBC, iv.encode("utf-8"))
            raw = base64.b64decode(cipher_text)
            value = unpad(cipher.decrypt(raw), AES.block_size).decode("utf-8")
            return json.loads(value).get("url", "")
        except Exception:
            return ""

    def _extract_player_url_from_iframe(self, html):
        match = re.search(
            r"var\s+player\s*=\s*[\"']([^\"']+)[\"'].*?var\s+rand\s*=\s*[\"']([^\"']+)[\"']",
            html,
            re.S,
        )
        if match:
            value = self._decrypt_player_payload(match.group(1), match.group(2))
            if value:
                return value

        match = re.search(r"[\"']data[\"']\s*:\s*[\"']([^\"']+)[\"']", html)
        if match:
            value = self._decode_data_url(match.group(1))
            if value:
                return value

        match = re.search(r"\bmysvg\b\s*=\s*[\"']([^\"']+)[\"']", html, re.I)
        if match:
            return match.group(1)

        match = re.search(r"art\.url\s*=\s*[\"']([^\"']+)[\"']", html, re.I)
        if match:
            return match.group(1)

        if "window.wp_nonce" in html:
            match = re.search(r"url\s*:\s*[\"']([^\"']+)[\"']", html, re.I)
            if match:
                return match.group(1)

        return ""

    def categoryContent(self, tid, pg, filter, extend):
        path = self.category_paths.get(tid, self.category_paths["movie"]).format(pg=pg)
        html, host = self._request_html(path, expect_xpath="//a[@href]")
        items = self._parse_media_cards(html, host)
        return self._page_result(items, pg)

    def detailContent(self, ids):
        vod_id = ids[0]
        html, host = self._request_html(vod_id, expect_xpath="//h1|//*[contains(@class,'paly_list_btn')]")
        return self._parse_detail_page(html, host, vod_id)

    def searchContent(self, key, quick, pg="1"):
        path = "/boss1O1?q={keyword}".format(keyword=quote(key))
        html, host = self._request_html(path, expect_xpath="//a[@href]")
        items = self._parse_media_cards(html, host)
        return self._page_result(items, pg)
