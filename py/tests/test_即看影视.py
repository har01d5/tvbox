import base64
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
except ModuleNotFoundError:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("jikanyingshi_spider", str(ROOT / "即看影视.py")).load_module()
Spider = MODULE.Spider


def build_sk_payload(value, key, iv):
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    encrypted = cipher.encrypt(pad(value.encode("utf-8"), AES.block_size)).hex()
    return "FROMSKZZJM" + encrypted


class TestJiKanYingShiSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    @patch.object(Spider, "fetch")
    def test_resolve_api_host_reads_appipr_txt(self, mock_fetch):
        mock_fetch.return_value = SimpleNamespace(text="https://appsky2025999.ideasz.net\n")
        self.assertEqual(self.spider._resolve_api_host(), "https://appsky2025999.ideasz.net")

    def test_sk_decrypt_returns_plain_text_without_prefix(self):
        self.assertEqual(self.spider._sk_decrypt("plain-text"), "plain-text")

    def test_sk_decrypt_decodes_prefixed_ciphertext(self):
        encrypted = build_sk_payload('{"msg":"ok"}', self.spider.aes_key, self.spider.aes_iv)
        self.assertEqual(self.spider._sk_decrypt(encrypted), '{"msg":"ok"}')

    def test_ck_encrypt_returns_base64_ascii(self):
        result = self.spider._ck_encrypt("https://host##5483##1700000000000##ckzmbc")
        decoded = base64.b64decode(result.encode("utf-8")).decode("utf-8")
        self.assertTrue(decoded)

    @patch.object(Spider, "fetch")
    @patch.object(Spider, "post")
    def test_ensure_ready_fetches_host_token_and_config_once(self, mock_post, mock_fetch):
        mock_fetch.side_effect = [
            SimpleNamespace(text="https://appsky2025999.ideasz.net\n"),
            SimpleNamespace(text=build_sk_payload('{"direct_link":[]}', self.spider.aes_key, self.spider.aes_iv)),
        ]
        mock_post.return_value = SimpleNamespace(
            text=build_sk_payload("token-123", self.spider.aes_key, self.spider.aes_iv)
        )

        self.spider._ensure_ready()
        self.spider._ensure_ready()

        self.assertEqual(self.spider.api_host, "https://appsky2025999.ideasz.net")
        self.assertEqual(self.spider.auth_token, "token-123")
        self.assertEqual(self.spider.config_data, {"direct_link": []})
        self.assertEqual(mock_post.call_count, 1)

    @patch.object(Spider, "_fetch_filters")
    @patch.object(Spider, "_fetch_api")
    def test_home_content_returns_classes_filters_and_home_list(self, mock_fetch_api, mock_fetch_filters):
        mock_fetch_api.side_effect = [
            {"data": [{"type_id": "1", "type_name": "电影"}, {"type_id": "2", "type_name": "剧集"}]},
            {"data": [{"vod_id": "v1", "vod_name": "首页推荐"}]},
        ]
        mock_fetch_filters.return_value = {
            "1": [{"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}]}]
        }

        content = self.spider.homeContent(False)

        self.assertEqual(
            content["class"],
            [{"type_id": "1", "type_name": "电影"}, {"type_id": "2", "type_name": "剧集"}],
        )
        self.assertEqual(content["filters"]["1"][0]["key"], "year")
        self.assertEqual(content["list"], [{"vod_id": "v1", "vod_name": "首页推荐"}])

    @patch.object(Spider, "_fetch_api")
    def test_home_video_content_requests_randomlikeindex(self, mock_fetch_api):
        mock_fetch_api.return_value = {"data": [{"vod_id": "x1", "vod_name": "推荐片"}]}

        result = self.spider.homeVideoContent()

        self.assertEqual(
            mock_fetch_api.call_args.args,
            ("/sk-api/vod/list", {"page": 1, "limit": 12, "type": "randomlikeindex"}),
        )
        self.assertEqual(result["list"][0]["vod_id"], "x1")

    @patch.object(Spider, "_fetch_api")
    def test_fetch_filters_maps_extend_fields_and_adds_sort(self, mock_fetch_api):
        mock_fetch_api.return_value = {
            "code": 200,
            "data": {"extendtype": "动作,喜剧", "area": "大陆,香港", "lang": "国语", "year": "2025,2024"},
        }

        filters = self.spider._fetch_filters([{"type_id": "1", "type_name": "电影"}])

        self.assertEqual(filters["1"][0]["key"], "class")
        self.assertEqual(filters["1"][0]["value"][1], {"n": "动作", "v": "动作"})
        self.assertEqual(filters["1"][-1]["value"][-1], {"n": "评分", "v": "score"})

    @patch.object(Spider, "_fetch_api")
    def test_category_content_maps_extend_to_sk_api_params(self, mock_fetch_api):
        mock_fetch_api.return_value = {"data": [{"vod_id": "c1", "vod_name": "分类片"}]}

        result = self.spider.categoryContent(
            "2",
            "3",
            False,
            {"sort": "hot", "area": "香港", "lang": "粤语", "year": "2025", "class": "动作"},
        )

        self.assertEqual(
            mock_fetch_api.call_args.args,
            (
                "/sk-api/vod/list",
                {
                    "typeId": "2",
                    "page": 3,
                    "limit": 18,
                    "type": "hot",
                    "area": "香港",
                    "lang": "粤语",
                    "year": "2025",
                    "mtype": "",
                    "extendtype": "动作",
                },
            ),
        )
        self.assertEqual(result["page"], 3)
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_fetch_api")
    def test_search_content_returns_standard_page_payload(self, mock_fetch_api):
        mock_fetch_api.return_value = {"data": [{"vod_id": "s1", "vod_name": "繁花"}]}

        result = self.spider.searchContent("繁花", False, "4")

        self.assertEqual(
            mock_fetch_api.call_args.args,
            ("/sk-api/search/pages", {"keyword": "繁花", "page": 4, "limit": 10, "typeId": -1}),
        )
        self.assertEqual(result["page"], 4)
        self.assertEqual(result["list"][0]["vod_id"], "s1")
        self.assertNotIn("pagecount", result)

    @patch.object(Spider, "_fetch_api")
    def test_category_content_returns_empty_list_on_api_error(self, mock_fetch_api):
        mock_fetch_api.side_effect = RuntimeError("boom")

        result = self.spider.categoryContent("1", "1", False, {})

        self.assertEqual(result["list"], [])
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main()
