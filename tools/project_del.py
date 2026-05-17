#!/usr/bin/env python3
"""Supprime un projet (dossier <project_id>/ entier). Action destructive."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_YAML = REPO_ROOT / "catalog" / "projects.yaml"

REPO_SYSTEM_DIRS = {"catalog", "helpers", "tools", "web", "templates"}


def _in_catalog(project_id: str) -> bool:
    if not PROJECTS_YAML.exists():
        return False
    data = yaml.safe_load(PROJECTS_YAML.read_text(encoding="utf-8")) or []
    return any(p.get("id") == project_id for p in data)


def _count_files(path: Path) -> int:
    return sum(1 for _ in path.rglob("*") if _.is_file())


app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main(
    project_id: str = typer.Argument(..., help="ID du projet à supprimer"),
    force: bool = typer.Option(
        False, "--force", help="Supprime même si encore listé dans catalog/projects.yaml"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Confirme sans demander (usage script uniquement)"
    ),
) -> None:
    if project_id in REPO_SYSTEM_DIRS:
        typer.echo(f"{project_id!r} est un répertoire système, suppression refusée", err=True)
        raise typer.Exit(code=2)

    target = REPO_ROOT / project_id
    if not target.exists():
        typer.echo(f"{target} n'existe pas, rien à supprimer")
        return
    if not target.is_dir():
        typer.echo(f"{target} n'est pas un dossier, refus", err=True)
        raise typer.Exit(code=2)

    if _in_catalog(project_id) and not force:
        typer.echo(
            f"{project_id!r} est encore listé dans catalog/projects.yaml. "
            f"Retire-le d'abord, ou utilise --force.",
            err=True,
        )
        raise typer.Exit(code=2)

    nb = _count_files(target)
    typer.echo(f"À supprimer : {target} ({nb} fichier(s))")

    if not yes:
        confirm = typer.prompt("Confirmer ? (tape le nom du projet pour valider)")
        if confirm != project_id:
            typer.echo("Annulé", err=True)
            raise typer.Exit(code=1)

    shutil.rmtree(target)
    typer.echo(f"supprimé: {target}")


if __name__ == "__main__":
    app()
