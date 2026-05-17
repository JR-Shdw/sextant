#!/usr/bin/env python3
"""Scaffold un nouveau projet : <projet>/{user,claude,openai,shared,last}/."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_YAML = REPO_ROOT / "catalog" / "projects.yaml"
TEMPLATE_LAST = REPO_ROOT / "templates" / "last_session.md"

AUDIENCES = ["user", "claude", "openai", "shared", "last"]


def _project_exists_in_catalog(project_id: str) -> bool:
    if not PROJECTS_YAML.exists():
        return False
    data = yaml.safe_load(PROJECTS_YAML.read_text(encoding="utf-8")) or []
    return any(p.get("id") == project_id for p in data)


def _write_if_absent(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def scaffold(project_id: str) -> list[str]:
    base = REPO_ROOT / project_id
    created: list[str] = []

    for audience in AUDIENCES:
        (base / audience).mkdir(parents=True, exist_ok=True)

    files = {
        base / "user" / "tasks.org": f"#+TITLE: {project_id} — tâches\n\n",
        base / "user" / "notes.org": f"#+TITLE: {project_id} — notes\n\n",
        base / "claude" / "main.md": f"# {project_id} — notes Claude\n\n",
        base / "openai" / "main.md": f"# {project_id} — notes OpenAI\n\n",
        base / "shared" / "README.md": f"# {project_id}\n\n",
        base / "last" / "session.md": TEMPLATE_LAST.read_text(encoding="utf-8")
        if TEMPLATE_LAST.exists()
        else "# session\n",
    }
    for path, content in files.items():
        if _write_if_absent(path, content):
            created.append(str(path.relative_to(REPO_ROOT)))

    return created


app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main(
    project_id: str = typer.Argument(..., help="ID du projet (kebab-case)"),
    strict: bool = typer.Option(
        True,
        "--strict/--no-strict",
        help="Refuse si project_id absent de catalog/projects.yaml",
    ),
) -> None:
    if strict and not _project_exists_in_catalog(project_id):
        typer.echo(
            f"projet {project_id!r} absent de catalog/projects.yaml. "
            f"Ajoute-le ou utilise --no-strict.",
            err=True,
        )
        raise typer.Exit(code=2)

    created = scaffold(project_id)
    if not created:
        typer.echo(f"{project_id}: déjà scaffold, rien à faire")
        return
    typer.echo(f"{project_id}: {len(created)} fichier(s) créé(s)")
    for path in created:
        typer.echo(f"  + {path}")


if __name__ == "__main__":
    app()
