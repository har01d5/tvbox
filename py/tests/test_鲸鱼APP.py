import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = SourceFileLoader("jingyu_spider", str(ROOT / "鲸鱼APP.py")).load_module()
Spider = MODULE.Spider


class TestJingyuSpider(unittest.TestCase):
    def setUp(self):
        Spider._instance = None
        self.spider = Spider()

    def test_aes_encrypt_decrypt_roundtrip(self):
        plaintext = '{"key":"value"}'
        encrypted = self.spider._aes_encrypt(plaintext)
        decrypted = self.spider._aes_decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)

    def test_aes_encrypt_produces_base64(self):
        import re
        encrypted = self.spider._aes_encrypt("hello")
        self.assertTrue(re.match(r'^[A-Za-z0-9+/=]+$', encrypted))
