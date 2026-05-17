#!/usr/bin/env python3
"""Valide les YAML du catalog (schéma + FKs)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
import yaml
from pydantic import BaseModel, ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "catalog"


class Forge(BaseModel):
    id: str
    name: str
    url: str
    node_id: str | None = None
    secret_ref: str | None = None
    status: Literal["active", "planned", "archived"]


class Node(BaseModel):
    id: str
    hostname: str
    wg_admin_ip: str | None = None
    wg_metrics_ip: str | None = None
    wg_uptime_ip: str | None = None
    public_ip: str | None = None
    role: str
    os: str
    services: list[str] = []
    status: Literal["active", "maintenance", "retired"]


class Vault(BaseModel):
    id: str
    endpoint: str
    public_dns: str | None = None
    node_id: str | None = None
    namespaces: list[str] = []
    token_secret_ref: str
    status: Literal["active", "planned", "archived"]


class Project(BaseModel):
    id: str
    name: str
    path: str | None = None
    forge_id: str
    repo: str
    node_ids: list[str] = []
    vault_namespace: str | None = None
    status: Literal["active", "planned", "production", "archived", "unknown"]
    notes: str | None = None


def _load(name: str) -> list[dict]:
    path = CATALOG / name
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or []


def lint() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    raw_forges = _load("forges.yaml")
    raw_nodes = _load("nodes.yaml")
    raw_vaults = _load("vaults.yaml")
    raw_projects = _load("projects.yaml")

    forges: list[Forge] = []
    for i, item in enumerate(raw_forges):
        try:
            forges.append(Forge(**item))
        except ValidationError as e:
            errors.append(f"forges.yaml[{i}]: {e}")

    nodes: list[Node] = []
    for i, item in enumerate(raw_nodes):
        try:
            nodes.append(Node(**item))
        except ValidationError as e:
            errors.append(f"nodes.yaml[{i}]: {e}")

    vaults: list[Vault] = []
    for i, item in enumerate(raw_vaults):
        try:
            vaults.append(Vault(**item))
        except ValidationError as e:
            errors.append(f"vaults.yaml[{i}]: {e}")

    projects: list[Project] = []
    for i, item in enumerate(raw_projects):
        try:
            projects.append(Project(**item))
        except ValidationError as e:
            errors.append(f"projects.yaml[{i}]: {e}")

    forge_ids = {f.id for f in forges}
    node_ids = {n.id for n in nodes}
    vault_namespaces = {ns for v in vaults for ns in v.namespaces}

    for f in forges:
        if f.node_id and f.node_id not in node_ids:
            errors.append(f"forges[{f.id}].node_id={f.node_id!r} introuvable dans nodes.yaml")

    for v in vaults:
        if v.node_id and v.node_id not in node_ids:
            errors.append(f"vaults[{v.id}].node_id={v.node_id!r} introuvable dans nodes.yaml")

    for p in projects:
        if p.forge_id not in forge_ids:
            errors.append(f"projects[{p.id}].forge_id={p.forge_id!r} introuvable dans forges.yaml")
        for nid in p.node_ids:
            if nid not in node_ids:
                errors.append(f"projects[{p.id}].node_ids contient {nid!r} introuvable dans nodes.yaml")
        if p.vault_namespace and p.vault_namespace not in vault_namespaces:
            errors.append(
                f"projects[{p.id}].vault_namespace={p.vault_namespace!r} non déclaré dans aucun vault"
            )

    counts = {
        "forges": len(forges),
        "nodes": len(nodes),
        "vaults": len(vaults),
        "projects": len(projects),
    }
    return errors, counts


app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main() -> None:
    errors, counts = lint()
    typer.echo(
        f"forges={counts['forges']} nodes={counts['nodes']} "
        f"vaults={counts['vaults']} projects={counts['projects']}"
    )
    if errors:
        for err in errors:
            typer.echo(f"  ERR {err}", err=True)
        raise typer.Exit(code=1)
    typer.echo("OK")


if __name__ == "__main__":
    app()
