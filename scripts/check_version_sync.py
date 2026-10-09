"""Falha se a versao declarada divergir das constantes publicadas no pacote."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "src" / "coffeemail" / "__init__.py"
HTTP = ROOT / "src" / "coffeemail" / "core" / "http.py"

VERSION_PATTERNS = {
    INIT: re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE),
    HTTP: re.compile(r'^SDK_VERSION\s*=\s*"([^"]+)"', re.MULTILINE),
}


def read_declared_version() -> str:
    with PYPROJECT.open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def read_constant(path: Path) -> str | None:
    match = VERSION_PATTERNS[path].search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def main() -> int:
    declared = read_declared_version()
    mismatches: list[str] = []

    for path in VERSION_PATTERNS:
        found = read_constant(path)
        if found is None:
            mismatches.append(f"{path.relative_to(ROOT)}: constante de versao nao encontrada")
            continue
        if found != declared:
            mismatches.append(f"{path.relative_to(ROOT)}: {found} != {declared} (pyproject.toml)")

    if not mismatches:
        print(f"[check-version-sync] todas as versoes em {declared}")
        return 0

    for mismatch in mismatches:
        print(f"[check-version-sync] DIVERGENCIA {mismatch}", file=sys.stderr)
    print(
        "[check-version-sync] o User-Agent publicado mente sobre a versao do SDK.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
