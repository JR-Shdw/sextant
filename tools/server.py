#!/usr/bin/env python3
"""Mini-serveur sextant : CRUD catalog + édition fichiers.

Pas d'auth — filtré par IP source via middleware.
À lancer :  python tools/server.py --host 127.0.0.1
ou:         make serve
"""

from __future__ import annotations

import ipaddress
from pathlib import Path

import typer
import uvicorn
import yaml
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.middleware.base import BaseHTTPMiddleware

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "catalog"
TEMPLATES = Path(__file__).resolve().parent / "templates"

ALLOWED_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("10.0.0.0/8"),
]

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "target",
                 ".ruff_cache", ".pytest_cache", ".mypy_cache", "dist", "build"}

# Schémas d'entités du catalog. Les champs sont (nom, type, optionnel, hint).
# type ∈ {str, int, bool, list_str}
ENTITY_FIELDS: dict[str, list[tuple[str, str, bool, str]]] = {
    "projects": [
        ("id", "str", False, "kebab-case court, ex: my-app"),
        ("name", "str", False, "nom lisible"),
        ("path", "str", True, "chemin du code source relatif à ~/dev/ (ou vide)"),
        ("forge_id", "str", False, "FK vers forges.yaml"),
        ("repo", "str", False, "nom du repo dans la forge"),
        ("node_ids", "list_str", True, "FKs vers nodes.yaml, séparés par virgules"),
        ("vault_namespace", "str", True, "namespace dans vaults.yaml (ou vide)"),
        ("status", "str", False, "active | planned | production | archived | unknown"),
        ("notes", "str", True, "optionnel, une ligne"),
    ],
    "forges": [
        ("id", "str", False, "kebab-case, ex: gitea-main"),
        ("name", "str", False, "nom lisible"),
        ("url", "str", False, "https://..."),
        ("node_id", "str", True, "FK vers nodes.yaml (ou vide)"),
        ("secret_ref", "str", True, "<namespace>/<key> dans le vault (ou vide)"),
        ("status", "str", False, "active | planned | archived"),
    ],
    "nodes": [
        ("id", "str", False, "kebab-case"),
        ("hostname", "str", False, "nom DNS court"),
        ("public_ip", "str", True, "IP publique (ou vide)"),
        ("private_ip", "str", True, "IP réseau privé / VPN (ou vide)"),
        ("role", "str", False, "rôle fonctionnel"),
        ("os", "str", False, "ex: debian-12, arch, manjaro"),
        ("services", "list_str", True, "services, séparés par virgules"),
        ("status", "str", False, "active | maintenance | retired"),
    ],
    "vaults": [
        ("id", "str", False, "kebab-case"),
        ("endpoint", "str", False, "URL"),
        ("public_dns", "str", True, "DNS public (ou vide)"),
        ("node_id", "str", True, "FK vers nodes.yaml (ou vide)"),
        ("namespaces", "list_str", True, "namespaces, séparés par virgules"),
        ("token_secret_ref", "str", False, "pointeur vers token ou 'external'"),
        ("status", "str", False, "active | planned | archived"),
    ],
}


class IPFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "0.0.0.0"
        try:
            addr = ipaddress.ip_address(client_host)
        except ValueError:
            return Response("Forbidden", status_code=403)
        if not any(addr in net for net in ALLOWED_NETS):
            return Response(f"Forbidden ({client_host})", status_code=403)
        return await call_next(request)


app = FastAPI()
app.add_middleware(IPFilterMiddleware)

env = Environment(
    loader=FileSystemLoader(TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


def render(template_name: str, **ctx) -> HTMLResponse:
    return HTMLResponse(env.get_template(template_name).render(**ctx))


def safe_path(rel: str) -> Path:
    target = (REPO_ROOT / rel).resolve()
    try:
        target.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="path traversal") from exc
    return target


def _load_yaml(name: str) -> list[dict]:
    path = CATALOG / f"{name}.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return data if isinstance(data, list) else []


def _save_yaml(name: str, items: list[dict]) -> None:
    path = CATALOG / f"{name}.yaml"
    header = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        header_lines = []
        for line in existing.splitlines():
            if line.startswith("#") or line.strip() == "":
                header_lines.append(line)
            else:
                break
        header = "\n".join(header_lines).rstrip() + "\n\n" if header_lines else ""
    body = yaml.safe_dump(items, sort_keys=False, allow_unicode=True) if items else "[]\n"
    path.write_text(header + body, encoding="utf-8")


def _parse_form(entity: str, form: dict) -> dict:
    item: dict = {}
    for name, typ, optional, _hint in ENTITY_FIELDS[entity]:
        raw = form.get(name, "").strip()
        if not raw:
            if optional:
                item[name] = None if typ != "list_str" else []
                continue
            raise HTTPException(status_code=400, detail=f"champ requis: {name}")
        if typ == "str":
            item[name] = raw
        elif typ == "int":
            try:
                item[name] = int(raw)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"{name}: entier invalide") from exc
        elif typ == "bool":
            item[name] = raw.lower() in {"1", "true", "yes", "on"}
        elif typ == "list_str":
            item[name] = [s.strip() for s in raw.split(",") if s.strip()]
    return item


REPO_SYSTEM_DIRS = {"catalog", "helpers", "tools", "web", "templates"}


def _project_id_of(rel: Path) -> str | None:
    parts = rel.parts
    if len(parts) < 2:
        return None
    head = parts[0]
    if head in REPO_SYSTEM_DIRS:
        return None
    return head


def _list_files() -> list[dict]:
    entries: list[dict] = []
    for path in REPO_ROOT.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT)
        is_text = _is_text(path)
        words = tokens = None
        if is_text:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                words = len(content.split())
                # Heuristique tokens: chars/3.5 (cl100k_base, FR-leaning).
                tokens = round(len(content) / 3.5)
            except OSError:
                pass
        entries.append(
            {
                "path": str(rel),
                "words": words,
                "tokens": tokens,
                "is_text": is_text,
                "project_id": _project_id_of(rel),
            }
        )
    entries.sort(key=lambda e: e["path"])
    return entries


TEXT_EXTS = {".md", ".org", ".yaml", ".yml", ".py", ".toml", ".txt", ".j2",
             ".css", ".html", ".js", ".sh", ""}


def _is_text(path: Path) -> bool:
    return path.suffix in TEXT_EXTS


@app.get("/", response_class=HTMLResponse)
def home():
    counts = {
        entity: len(_load_yaml(entity)) for entity in ENTITY_FIELDS
    }
    files = _list_files()
    return render("home.html.j2", counts=counts, file_count=len(files))


@app.get("/catalog/{entity}", response_class=HTMLResponse)
def list_entity(entity: str):
    if entity not in ENTITY_FIELDS:
        raise HTTPException(status_code=404)
    items = _load_yaml(entity)
    return render(
        "catalog_list.html.j2",
        entity=entity,
        items=items,
        fields=ENTITY_FIELDS[entity],
    )


@app.get("/catalog/{entity}/new", response_class=HTMLResponse)
def new_entity(entity: str):
    if entity not in ENTITY_FIELDS:
        raise HTTPException(status_code=404)
    return render(
        "catalog_form.html.j2",
        entity=entity,
        item={},
        fields=ENTITY_FIELDS[entity],
        is_new=True,
    )


@app.get("/catalog/{entity}/{item_id}", response_class=HTMLResponse)
def edit_entity(entity: str, item_id: str):
    if entity not in ENTITY_FIELDS:
        raise HTTPException(status_code=404)
    items = _load_yaml(entity)
    match = next((it for it in items if it.get("id") == item_id), None)
    if not match:
        raise HTTPException(status_code=404)
    return render(
        "catalog_form.html.j2",
        entity=entity,
        item=match,
        fields=ENTITY_FIELDS[entity],
        is_new=False,
    )


@app.post("/catalog/{entity}")
async def save_entity(entity: str, request: Request):
    if entity not in ENTITY_FIELDS:
        raise HTTPException(status_code=404)
    form = dict(await request.form())
    new_item = _parse_form(entity, form)
    items = _load_yaml(entity)
    original_id = form.get("__original_id", "").strip()
    if original_id:
        items = [it if it.get("id") != original_id else new_item for it in items]
    else:
        if any(it.get("id") == new_item.get("id") for it in items):
            raise HTTPException(status_code=400, detail=f"id {new_item.get('id')!r} déjà utilisé")
        items.append(new_item)
    _save_yaml(entity, items)
    return RedirectResponse(f"/catalog/{entity}", status_code=303)


@app.post("/catalog/{entity}/{item_id}/delete")
def delete_entity(entity: str, item_id: str):
    if entity not in ENTITY_FIELDS:
        raise HTTPException(status_code=404)
    items = _load_yaml(entity)
    items = [it for it in items if it.get("id") != item_id]
    _save_yaml(entity, items)
    return RedirectResponse(f"/catalog/{entity}", status_code=303)


@app.get("/files", response_class=HTMLResponse)
def files_list(project: str | None = None):
    files = _list_files()
    available_projects = sorted({f["project_id"] for f in files if f["project_id"]})
    system_count = sum(1 for f in files if f["project_id"] is None)
    if project == "_system":
        files = [f for f in files if f["project_id"] is None]
    elif project:
        files = [f for f in files if f["project_id"] == project]
    return render(
        "files.html.j2",
        files=files,
        current_project=project,
        available_projects=available_projects,
        system_count=system_count,
    )


@app.get("/edit", response_class=HTMLResponse)
def edit_file(path: str):
    target = safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404)
    content = target.read_text(encoding="utf-8")
    return render("file_edit.html.j2", path=path, content=content)


@app.post("/edit")
def save_file(path: str = Form(...), content: str = Form(...)):
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return RedirectResponse(f"/edit?path={path}", status_code=303)


@app.get("/download")
def download_file(path: str):
    target = safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(target, filename=target.name)


@app.get("/view", response_class=Response)
def view_file(path: str):
    target = safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404)
    return Response(target.read_text(encoding="utf-8"), media_type="text/plain; charset=utf-8")


cli = typer.Typer(add_completion=False, help=__doc__)


@cli.command()
def main(
    host: str = typer.Option("127.0.0.1", help="Bind IP"),
    port: int = typer.Option(8001, help="Port"),
    reload: bool = typer.Option(False, "--reload", help="Hot reload (dev only)"),
) -> None:
    uvicorn.run("server:app" if reload else app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    cli()
