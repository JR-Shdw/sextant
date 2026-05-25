# MAP — sextant

Toute IA : lis ce fichier d'abord, puis charge UNIQUEMENT ce dont tu as besoin.

## Où chercher quoi

| Question | Fichier |
|---|---|
| Liste projets, leurs repos, forge, nodes | catalog/projects.yaml |
| Endpoints des forges | catalog/forges.yaml |
| IPs/rôles des serveurs | catalog/nodes.yaml |
| Endpoints vault + namespaces | catalog/vaults.yaml |
| Trouver un .md/.org dans le repo | catalog/files.yaml (généré) |
| Notes spécifiques Claude transverses | helpers/claude/*.md (peut être vide) |
| Notes spécifiques OpenAI transverses | helpers/openai/*.md (peut être vide) |
| Tout sur un projet (tâches, notes, helpers) | &lt;projet&gt;/&lt;audience&gt;/*.md\|.org |

## Conventions YAML

- IDs : kebab-case court (`gitea-main`, `srv-ci`, `my-app`)
- FKs : `forge_id`, `node_ids[]`, `vault_namespace`
- Jamais de secret en clair — utiliser `secret_ref: <namespace>/<key>` qui pointe vers vault
- Tout chemin de fichier est relatif à la racine du repo

## Audiences (dossiers)

- `user/` : pour l'humain (orgmode, tâches, notes perso)
- `claude/` : pour Claude (notes idiosyncrasiques, pas duplication catalog)
- `openai/` : pour OpenAI (idem)
- `shared/` : doc client/projet générale
- `last/` : état de la dernière session (cf. ci-dessous)

Un dossier audience peut contenir N fichiers (`main.md`, `tasks.org`, `<topic>.md`...).

## CONSIGNE IA (importante)

Quand tu (IA) crées un helper que TU vas consommer plus tard, il va dans
`helpers/<ton-nom>/` (`claude/`, `openai/`, ...), JAMAIS dans `helpers/user/`.
L'humain connaît déjà son infra ; ses helpers sont rares et différents des
tiens. Idem au niveau projet : un helper que tu vas relire va dans
`<projet>/<ton-nom>/`, pas dans `<projet>/user/`.

Règle de décision : si tu hésites → `claude/`. L'humain peut toujours lire
un .md dans `claude/` au besoin ; le coût d'un classement raté en `user/`
c'est des tokens gaspillés à recharger un contenu mal placé.

## Reprise de session — `<projet>/last/` (OBLIGATOIRE pour toute IA)

Au DÉBUT de chaque session de travail sur un projet :
1. **Lire** `<projet>/last/session.md` (s'il existe).
2. **Valider** avec l'humain que la tâche précédente est bien terminée comme prévu.
3. **Nettoyer** `last/session.md` (le vider ou l'écraser).
4. **Remplir** immédiatement `last/session.md` avec la tâche du jour, AVANT d'attaquer le travail. Comme ça, en cas d'arrêt impromptu, l'état est déjà capturé.

Mettre à jour `last/session.md` au fil de l'eau quand le focus change.

Gabarit minimal de `last/session.md` :

```markdown
# session <YYYY-MM-DD>
objectif: <une ligne>
fichiers: <liste courte>
état: en cours | bloqué | en attente d'input
next: <prochaine étape>
```

## Helpers spécifiques projet

Vivent dans `<projet>/<audience>/`, PAS dans `helpers/<projet>/`.
`helpers/` au top-level = transverses uniquement (pas attachés à un projet).

## Règle d'or token-efficiency

- Si une info est dans `catalog/`, ne pas la recopier dans `helpers/<ia>/`. Pointer.
- Si un helper `<ia>/X.md` est vide, ne pas le créer.
- `MAP.md` : viser ≤80 lignes. Catalog YAML ≤ 200 lignes (split sinon).
- Pas de prose dans les YAML — commentaires `#` minimaux uniquement.

## Accès aux forges

Exclusivement HTTPS via `git-credential-vault` (helper global). Cf. `helpers/claude/credentials.md`.

## Tâche pour l'humain (arbre de décision)

Si tu trouves quelque chose à faire :
1. As-tu besoin de son autorisation ? Non → fais-le. Oui → demande.
2. Action **humaine** réellement requise ? Non → fais-le toi. Oui → `tools/user-task <projet> "<titre>"`.

Détails et flags : `helpers/claude/user-task.md`. **Ne JAMAIS diluer une tâche humaine** dans un CLAUDE.md / README / notes — uniquement `<projet>/user/tasks.org`.

## Outils

- `tools/catalog_scan.py` : régénère `catalog/files.yaml`
- `tools/catalog_lint.py` : valide FKs et existence des fichiers
- `tools/server.py` : sert le CRUD web (`make serve`)
- `tools/task_emit.py <projet> "<titre>"` : ajoute tâche dans `<projet>/user/tasks.org`

Venv local : `.venv/` (racine). `make install` pour le créer.

## Commandes Claude Code

- `/sextant-wrap <projet>` : diff `<projet>/last/session.md`, écrit sur OK (`.claude/commands/sextant-wrap.md`).
