import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("siwan_spider", str(ROOT / "四万影视.py")).load_module()
Spider = MODULE.Spider


class TestSiWanSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()
        self.spider.init()

    def _response(self, status_code=200, payload=None, text=None):
        body = text if text is not None else json.dumps(payload or {}, ensure_ascii=False)
        return SimpleNamespace(status_code=status_code, text=body)

    def test_home_content_exposes_expected_classes_and_filters(self):
        content = self.spider.homeContent(False)
        self.assertEqual(
            [item["type_id"] for item in content["class"]],
            ["20", "30", "39", "45", "32"],
        )
        self.assertEqual(
            [item["key"] for item in content["filters"]["20"]],
            ["subType", "year", "sort"],
        )
        self.assertEqual(content["filters"]["20"][0]["init"], "20")
        self.assertEqual(content["filters"]["20"][1]["value"][0], {"n": "全部", "v": ""})
        self.assertEqual(content["filters"]["20"][2]["value"][0], {"n": "时间", "v": "time"})

    def test_home_video_content_returns_empty_list(self):
        self.assertEqual(self.spider.homeVideoContent(), {"list": []})

    @patch.object(Spider, "fetch")
    def test_api_get_requests_maccms_endpoint_with_browser_headers(self, mock_fetch):
        mock_fetch.return_value = self._response(payload={"list": []})
        data = self.spider._api_get({"ac": "detail", "pg": 1})
        self.assertEqual(data, {"list": []})
        self.assertEqual(mock_fetch.call_args.args[0], "https://40000.me/api/maccms")
        self.assertEqual(mock_fetch.call_args.kwargs["params"], {"ac": "detail", "pg": 1})
        self.assertEqual(mock_fetch.call_args.kwargs["headers"]["Referer"], "https://40000.me/")

    @patch.object(Spider, "fetch")
    def test_api_get_rejects_non_200_and_non_object_body(self, mock_fetch):
        mock_fetch.return_value = self._response(status_code=500, payload={"msg": "bad"})
        with self.assertRaises(ValueError):
            self.spider._api_get({"ac": "detail"})

        mock_fetch.return_value = self._response(text="[]")
        with self.assertRaises(ValueError):
            self.spider._api_get({"ac": "detail"})
