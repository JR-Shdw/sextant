#!/usr/bin/env python3
"""Scan le repo a la recherche d'IP RFC1918 qui ne sont ni loopback,
ni des ranges documentes, ni dans l'allowlist .leakscan-allow.

Sort 0 si OK, 1 si un leak est detecte. Pense pour la CI.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST_FILE = REPO_ROOT / ".leakscan-allow"

IP_RE = re.compile(
    r"\b(?:"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r")\b"
)

ALWAYS_ALLOWED = {
    "10.0.0.0/8",
    "192.168.0.0/16",
    "172.16.0.0/12",
}


def tracked_files() -> list[Path]:
    res = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [REPO_ROOT / p for p in res.stdout.splitlines() if p]


def load_allowlist() -> set[str]:
    if not ALLOWLIST_FILE.exists():
        return set()
    allow: set[str] = set()
    for line in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            allow.add(line)
    return allow


def is_documented_range(line: str, match: str) -> bool:
    for r in ALWAYS_ALLOWED:
        if r in line and match in r:
            return True
    return False


def scan() -> list[tuple[Path, int, str, str]]:
    allow = load_allowlist()
    leaks: list[tuple[Path, int, str, str]] = []
    for f in tracked_files():
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in IP_RE.finditer(line):
                ip = m.group(0)
                if ip in allow:
                    continue
                if is_documented_range(line, ip):
                    continue
                leaks.append((f.relative_to(REPO_ROOT), lineno, ip, line.strip()))
    return leaks


def main() -> int:
    leaks = scan()
    if not leaks:
        print("leak-scan: OK (0 leak)")
        return 0
    print(f"leak-scan: {len(leaks)} IP(s) RFC1918 detectee(s) hors allowlist :", file=sys.stderr)
    for path, lineno, ip, snippet in leaks:
        print(f"  {path}:{lineno}: {ip}  -- {snippet}", file=sys.stderr)
    print(
        f"\nSi ces IP sont des exemples documentes, ajoute-les a {ALLOWLIST_FILE.name} "
        "(une IP par ligne, # pour commenter).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
