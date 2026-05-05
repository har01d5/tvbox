from __future__ import annotations

import argparse
from pathlib import Path

from base.secspider import (
    build_secspider_package,
    generate_signing_keypair,
    load_master_secret,
    load_signing_private_key,
)


def _resolve_package_version(output_path: Path, requested_version: str) -> str:
    if output_path.suffix.lower() != ".txt" or not output_path.is_file():
        return requested_version

    for line in output_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("//@version:"):
            continue
        current_version = line.removeprefix("//@version:").strip()
        try:
            return str(int(current_version) + 1)
        except ValueError:
            return requested_version

    return requested_version


def _cmd_genkeys(args) -> int:
    private_pem, public_pem = generate_signing_keypair()
    Path(args.private_key).write_text(private_pem, encoding="utf-8")
    Path(args.public_key).write_text(public_pem, encoding="utf-8")
    print(f"wrote {args.private_key}")
    print(f"wrote {args.public_key}")
    return 0


def _cmd_pack(args) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else Path(f"{(args.name or input_path.stem)}.txt")
    version = _resolve_package_version(output_path, args.version)
    package_text = build_secspider_package(
        source_text=input_path.read_text(encoding="utf-8"),
        name=args.name or input_path.stem,
        version=version,
        remark=args.remark,
        kid=args.kid,
        signing_private_key=load_signing_private_key(args.private_key),
        master_secret=load_master_secret(args.master_secret_file),
    )
    output_path.write_text(package_text, encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secspider_tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    genkeys = subparsers.add_parser("genkeys")
    genkeys.add_argument("--private-key", required=True)
    genkeys.add_argument("--public-key", required=True)
    genkeys.set_defaults(func=_cmd_genkeys)

    pack = subparsers.add_parser("pack")
    pack.add_argument("--input", required=True)
    pack.add_argument("--output", default="")
    pack.add_argument("--name", default="")
    pack.add_argument("--version", default="1")
    pack.add_argument("--remark", default="")
    pack.add_argument("--kid", default="k2026_04")
    pack.add_argument("--private-key", default="signing-private.pem")
    pack.add_argument("--master-secret-file", default="master-secret.txt")
    pack.set_defaults(func=_cmd_pack)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
