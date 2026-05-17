# sextant

Catalogue minimaliste et helpers multi-audience pour solo opérateurs self-hosted.

Inspiration : un instrument de navigation qui donne ta position avec quelques mesures simples. Ici, on donne à une IA (Claude, OpenAI, ta plateforme locale) la position de ton écosystème — projets, forges, nodes, vaults, fichiers — en quelques centaines de tokens au lieu de plusieurs dizaines de milliers.

## À quoi ça sert

- Rassembler en un seul endroit la liste des projets, leurs repos, leurs forges, les nodes qui les hébergent.
- Séparer strictement par audience (`user/`, `claude/`, `openai/`, `shared/`) pour ne plus mélanger tâches humaines, notes IA et docs clients.
- Permettre à toute IA qui débarque de répondre depuis un point d'entrée unique (`MAP.md`) sans aspirer tout le contexte.

Pour la motivation détaillée et les chiffres d'économie de tokens : `philosophie.md`.

## Démarrer

```bash
git clone <forge>:<user>/sextant.git
cd sextant
make install
```

Puis suivre `QUICKSTART.md` (cinq minutes, premier projet bout en bout).

Une fois en place : `make serve` ouvre l'UI CRUD locale sur `http://127.0.0.1:8001` ; une IA se borne à lire `MAP.md` puis à grep le YAML pertinent.

## Arborescence

```
sextant/
├── MAP.md                # point d'entrée IA (≤80 lignes)
├── QUICKSTART.md         # walkthrough humain, premier projet
├── philosophie.md        # pourquoi sextant existe, économies mesurées
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
└── <projet>/             # un dossier par projet déclaré dans catalog/
    ├── user/             # tasks.org, notes.org, helpers user
    ├── claude/           # main.md, helpers Claude
    ├── openai/           # main.md, helpers OpenAI
    ├── shared/           # doc client/générale
    └── last/             # état de la dernière session
```

## Conventions

- IDs : kebab-case court (`gitea-main`, `srv-ci`, `my-app`).
- Secrets : jamais en clair. Le YAML stocke un `secret_ref: <namespace>/<key>` qui pointe vers ton vault.
- `.org` dans `user/`, `.md` ailleurs.
- Pas de duplication entre `catalog/` et `helpers/`.
- **Reprise de session** : chaque projet a un `last/session.md` que l'IA doit lire au début, valider, écraser avec la tâche du jour. Détails dans `MAP.md`.

## Outils

| Cible | Rôle |
|---|---|
| `make install` | crée `.venv` et installe les dépendances |
| `make lint` | valide les YAML du `catalog/` (schéma + FKs) |
| `make scan` | régénère `catalog/files.yaml` (index des fichiers) |
| `make leak-scan` | échoue sur toute IP RFC1918 hors `.leakscan-allow` |
| `make serve` | sert l'UI CRUD sur `127.0.0.1:8001` |
| `tools/project_init.py <id>` | scaffold un dossier projet (cinq audiences) |
| `tools/user-task <projet> "<titre>"` | crée une tâche humaine canonique |

## Repo public, contenu privé

Tous les défauts d'outils pointent sur `127.0.0.1` ou exigent une variable d'environnement. Aucune IP de réseau privé n'est commitée. Le garde-fou `tools/leak_scan.py` (intégré à la CI Woodpecker) refait le tour à chaque push : si une IP RFC1918 apparaît hors allowlist, le build casse.

Pour publier un fork avec ton propre catalog peuplé : ajoute les chemins sensibles à `.gitignore` (les lignes commentées sont déjà prêtes) ou tiens deux working trees séparés, l'un public, l'autre privé.

## Licence

MIT. Cf. `LICENSE`.
