# coding=utf-8
import sys
from urllib.parse import quote, urljoin

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

    def categoryContent(self, tid, pg, filter, extend):
        path = self.category_paths.get(tid, self.category_paths["movie"]).format(pg=pg)
        html, host = self._request_html(path, expect_xpath="//a[@href]")
        items = self._parse_media_cards(html, host)
        return self._page_result(items, pg)

    def searchContent(self, key, quick, pg="1"):
        path = "/boss1O1?q={keyword}".format(keyword=quote(key))
        html, host = self._request_html(path, expect_xpath="//a[@href]")
        items = self._parse_media_cards(html, host)
        return self._page_result(items, pg)
