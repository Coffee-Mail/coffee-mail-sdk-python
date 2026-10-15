"""Sincroniza (ou verifica, com --check) o snapshot spec/product.json.

A fonte é COFFEEMAIL_OPENAPI_SPEC (caminho local ou URL http/https); o padrão é o spec
público da API de produto.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "spec" / "product.json"
DEFAULT_SOURCE = "https://api.coffeemail.com.br/v1/product/docs/json"
TIMEOUT_SECONDS = 30
USER_AGENT = "coffeemail-python-sync-openapi"
INDENT = 2


def read_source(source: str) -> str:
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(source, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return str(response.read().decode("utf-8"))
    return Path(source).read_text(encoding="utf-8")


def normalize(raw: str) -> str:
    return json.dumps(json.loads(raw), indent=INDENT, ensure_ascii=False) + "\n"


def main() -> int:
    source = os.environ.get("COFFEEMAIL_OPENAPI_SPEC") or DEFAULT_SOURCE
    normalized = normalize(read_source(source))
    if "--check" not in sys.argv:
        SNAPSHOT.write_text(normalized, encoding="utf-8")
        print(f"[sync-openapi] {SNAPSHOT.relative_to(ROOT)} atualizado a partir de {source}")
        return 0
    if SNAPSHOT.read_text(encoding="utf-8") != normalized:
        print("[sync-openapi] spec/product.json diverge da fonte", file=sys.stderr)
        return 1
    print("[sync-openapi] snapshot em dia")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
