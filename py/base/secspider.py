from __future__ import annotations

import base64
import secrets
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import HKDF
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa


def _derive_wrap_material(master_secret: bytes, kid: str, name: str, version: str) -> tuple[bytes, bytes]:
    wrap_key = HKDF(
        master=master_secret,
        key_len=32,
        salt=kid.encode("utf-8"),
        hashmod=SHA256,
        num_keys=1,
        context=f"secspider:{name}:{version}:wrap-key".encode("utf-8"),
    )
    wrap_nonce = HKDF(
        master=master_secret,
        key_len=12,
        salt=kid.encode("utf-8"),
        hashmod=SHA256,
        num_keys=1,
        context=f"secspider:{name}:{version}:wrap-nonce".encode("utf-8"),
    )
    return wrap_key, wrap_nonce


def _signing_bytes(headers: dict[str, str], payload_b64: str) -> bytes:
    return "\n".join(
        [
            f"//@name:{headers['name']}",
            f"//@version:{headers['version']}",
            f"//@remark:{headers['remark']}",
            f"//@format:{headers['format']}",
            f"//@alg:{headers['alg']}",
            f"//@wrap:{headers['wrap']}",
            f"//@sign:{headers['sign']}",
            f"//@kid:{headers['kid']}",
            f"//@nonce:{headers['nonce']}",
            f"//@ek:{headers['ek']}",
            f"//@hash:{headers['hash']}",
            f"payload.base64:{payload_b64}",
        ]
    ).encode("utf-8")


def build_secspider_package(
    *,
    source_text: str,
    name: str,
    version: str,
    remark: str,
    kid: str,
    signing_private_key,
    master_secret: bytes,
) -> str:
    source_bytes = source_text.encode("utf-8")
    source_hash = SHA256.new(source_bytes).hexdigest()
    content_key = secrets.token_bytes(32)
    payload_nonce = secrets.token_bytes(12)
    wrap_key, wrap_nonce = _derive_wrap_material(master_secret, kid, name, version)

    wrap_cipher = AES.new(wrap_key, AES.MODE_GCM, nonce=wrap_nonce)
    wrapped_key, wrapped_tag = wrap_cipher.encrypt_and_digest(content_key)

    payload_cipher = AES.new(content_key, AES.MODE_GCM, nonce=payload_nonce)
    payload_ciphertext, payload_tag = payload_cipher.encrypt_and_digest(source_bytes)
    payload_b64 = base64.b64encode(payload_ciphertext + payload_tag).decode("ascii")

    headers = {
        "name": name,
        "version": version,
        "remark": remark,
        "format": "secspider/1",
        "alg": "aes-256-gcm",
        "wrap": "hkdf-aes-keywrap",
        "sign": "ed25519",
        "kid": kid,
        "nonce": "base64:" + base64.b64encode(payload_nonce).decode("ascii"),
        "ek": "base64:" + base64.b64encode(wrapped_key + wrapped_tag).decode("ascii"),
        "hash": f"sha256:{source_hash}",
    }

    signer = eddsa.new(signing_private_key, "rfc8032")
    headers["sig"] = "base64:" + base64.b64encode(signer.sign(_signing_bytes(headers, payload_b64))).decode("ascii")

    return "\n".join(
        [
            f"//@name:{headers['name']}",
            f"//@version:{headers['version']}",
            f"//@remark:{headers['remark']}",
            f"//@format:{headers['format']}",
            f"//@alg:{headers['alg']}",
            f"//@wrap:{headers['wrap']}",
            f"//@sign:{headers['sign']}",
            f"//@kid:{headers['kid']}",
            f"//@nonce:{headers['nonce']}",
            f"//@ek:{headers['ek']}",
            f"//@hash:{headers['hash']}",
            f"//@sig:{headers['sig']}",
            "",
            f"payload.base64:{payload_b64}",
        ]
    )


def generate_signing_keypair() -> tuple[str, str]:
    private_key = ECC.generate(curve="Ed25519")
    public_key = private_key.public_key()
    return private_key.export_key(format="PEM"), public_key.export_key(format="PEM")


def load_signing_private_key(path: str | Path):
    return ECC.import_key(Path(path).read_text(encoding="utf-8"))


def load_master_secret(path: str | Path) -> bytes:
    return Path(path).read_text(encoding="utf-8").strip().encode("utf-8")
