#!/usr/bin/env python3
"""Ajoute une tâche orgmode dans projets/<projet>/user/tasks.org."""

from __future__ import annotations

from datetime import date as date_cls
from pathlib import Path

import typer
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_YAML = REPO_ROOT / "catalog" / "projects.yaml"

WEEKDAYS_FR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _known_project_ids() -> set[str]:
    if not PROJECTS_YAML.exists():
        return set()
    data = yaml.safe_load(PROJECTS_YAML.read_text(encoding="utf-8")) or []
    return {p["id"] for p in data if "id" in p}


def _format_deadline(deadline: date_cls) -> str:
    return f"<{deadline.isoformat()} {WEEKDAYS_FR[deadline.weekday()]}>"


def _entry(title: str, priority: str | None, deadline: date_cls | None) -> str:
    parts = ["* TODO"]
    if priority:
        parts.append(f"[#{priority}]")
    parts.append(title)
    line = " ".join(parts) + "\n"
    if deadline:
        line += f"  DEADLINE: {_format_deadline(deadline)}\n"
    return line


app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main(
    project_id: str = typer.Argument(..., help="ID du projet (cf. catalog/projects.yaml)"),
    title: str = typer.Argument(..., help="Titre de la tâche"),
    priority: str | None = typer.Option(None, "--priority", help="A, B ou C"),
    deadline: str | None = typer.Option(None, "--deadline", help="YYYY-MM-DD"),
    strict: bool = typer.Option(
        True, "--strict/--no-strict", help="Refuse si project_id inconnu"
    ),
) -> None:
    known = _known_project_ids()
    if strict and known and project_id not in known:
        typer.echo(
            f"projet {project_id!r} inconnu dans projects.yaml. "
            f"Utilise --no-strict pour forcer.",
            err=True,
        )
        raise typer.Exit(code=2)

    if priority and priority not in {"A", "B", "C"}:
        typer.echo("priority doit être A, B ou C", err=True)
        raise typer.Exit(code=2)

    parsed_deadline: date_cls | None = None
    if deadline:
        try:
            parsed_deadline = date_cls.fromisoformat(deadline)
        except ValueError as exc:
            typer.echo(f"deadline invalide: {deadline!r} (attendu YYYY-MM-DD)", err=True)
            raise typer.Exit(code=2) from exc

    target = REPO_ROOT / project_id / "user" / "tasks.org"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(f"#+TITLE: {project_id} — tâches\n\n", encoding="utf-8")

    with target.open("a", encoding="utf-8") as f:
        f.write(_entry(title, priority, parsed_deadline))

    typer.echo(f"ajouté: {target}")


if __name__ == "__main__":
    app()
