# sextant

Catalogue minimaliste + helpers multi-audience pour solo opérateurs self-hosted.

Inspiration : un instrument de navigation qui donne ta position avec quelques mesures simples. Ici, on donne à une IA (Claude, OpenAI, ta plateforme locale) la position de ton écosystème — projets, forges, nodes, vaults, fichiers — en quelques centaines de tokens au lieu de plusieurs dizaines de milliers.

## Pour quoi faire

- Rassembler en un seul endroit la liste des projets, leurs repos, leurs forges, les nodes qui les hébergent.
- Séparer strictement par audience (`user/`, `claude/`, `openai/`, `shared/`) pour ne plus mélanger tâches humaines, notes IA et docs clients.
- Permettre à toute IA qui débarque de répondre depuis un point d'entrée unique (`MAP.md`) sans aspirer tout le contexte.

## Pour démarrer

- **Toi (humain)** : `make install && make serve` puis ouvre http://127.0.0.1:8001.
- **Une IA** : lit `MAP.md` puis grep le YAML pertinent dans `catalog/`.

## Arborescence

```
sextant/
├── MAP.md                # point d'entrée IA (≤60 lignes)
├── README.md             # ce fichier (point d'entrée humain)
├── catalog/              # sources de vérité YAML
│   ├── projects.yaml
│   ├── forges.yaml
│   ├── nodes.yaml
│   ├── vaults.yaml
│   └── files.yaml        # auto-généré
├── helpers/              # notes transverses par audience
│   ├── user/
│   ├── claude/
│   └── openai/
├── tools/                # outillage Python (serveur, lint, scan, scaffold)
└── <projet>/             # dossier par projet
    ├── user/             # tasks.org, notes.org, helpers user
    ├── claude/           # main.md, helpers Claude
    ├── openai/           # main.md, helpers OpenAI
    ├── shared/           # doc client/générale
    └── last/             # état de la dernière session (cf. MAP.md)
```

## Outils

Chaque outil est un CLI typer single-file. Activer le venv puis :

```bash
source .venv/bin/activate

python tools/catalog_lint.py            # valide les YAML
python tools/catalog_scan.py            # régénère catalog/files.yaml
python tools/task_emit.py my-app "Faire la revue sprint 5" --priority A
```

## Conventions

- IDs : kebab-case court (`gitea-main`, `srv-ci`, `my-app`).
- Secrets : jamais en clair. Le YAML stocke un `secret_ref: <namespace>/<key>` qui pointe vers ton vault.
- `.org` dans `user/`, `.md` ailleurs.
- Pas de duplication entre `catalog/` et `helpers/`.
- **Reprise de session** : chaque projet a un `last/session.md` que l'IA doit lire au début de session, valider, écraser avec la tâche du jour. Détails dans `MAP.md`.

Détails dans `MAP.md`.

## Installation

```bash
git clone <forge>:<user>/sextant.git
cd sextant
make install   # ou: python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
```

Puis peuple les YAML de `catalog/` selon ton infra (les fichiers livrés sont des squelettes vides avec exemples commentés).

## Licence

MIT. Cf. `LICENSE`.
