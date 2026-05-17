#!/usr/bin/env python3
"""Scanne les .md/.org du repo et écrit catalog/files.yaml.

Par défaut (--scope repo) : ne scanne que le repo sextant lui-même.
Avec --scope dev : scanne aussi ~/dev/ (utile pour la migration initiale).
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_ROOT = Path.home() / "dev"
CATALOG_FILE = REPO_ROOT / "catalog" / "files.yaml"

EXCLUDED_PARTS = {".git", "node_modules", "target", ".venv", "__pycache__", "dist", "build"}
AUDIENCES = {"user", "claude", "openai", "shared"}
REPO_SYSTEM_DIRS = {"catalog", "helpers", "tools", "web"}


def detect_audience(path: Path) -> str:
    parts = path.parts
    for audience in AUDIENCES:
        if audience in parts:
            return audience
    return "unknown"


def detect_project_id(path: Path) -> str | None:
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2:
        return None
    head = parts[0]
    if head in REPO_SYSTEM_DIRS:
        return None
    return head


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def scan(scope: str = "repo") -> list[dict]:
    if scope == "repo":
        root = REPO_ROOT
    elif scope == "dev":
        root = DEV_ROOT
    else:
        raise ValueError(f"scope inconnu: {scope!r}")

    entries: list[dict] = []
    for pattern in ("*.md", "*.org"):
        for path in root.rglob(pattern):
            if is_excluded(path):
                continue
            if not path.is_file():
                continue
            entries.append(
                {
                    "path": str(path.relative_to(root)),
                    "audience": detect_audience(path),
                    "project_id": detect_project_id(path),
                    "mtime": int(path.stat().st_mtime),
                }
            )
    entries.sort(key=lambda e: e["path"])
    return entries


app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main(
    output: Path = typer.Option(CATALOG_FILE, help="Fichier de sortie"),
    scope: str = typer.Option("repo", help="repo (défaut) ou dev"),
    dry_run: bool = typer.Option(False, "--dry-run", help="N'écrit pas le fichier"),
) -> None:
    entries = scan(scope=scope)
    payload = yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)
    if dry_run:
        sys.stdout.write(payload)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload, encoding="utf-8")
    typer.echo(f"{len(entries)} fichier(s) écrits dans {output} (scope={scope})")


if __name__ == "__main__":
    app()
