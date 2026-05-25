# Quickstart

Cinq minutes pour brancher sextant sur un premier projet et ouvrir une session IA propre.

## Prérequis

- Python 3.12 ou supérieur.
- Un repo git distant (Gitea, Forgejo, GitLab self-hosted, peu importe).
- Optionnel : un Vault accessible localement si tu veux passer les secrets par `tools/vault-get`.

## 1. Installer

```bash
git clone <forge>:<user>/sextant.git
cd sextant
make install
```

Le venv local atterrit dans `.venv/`. Activation optionnelle (`source .venv/bin/activate`), les cibles `make` n'en ont pas besoin.

## 2. Peupler le minimum vital du catalog

Les quatre YAML de `catalog/` arrivent vides avec un exemple commenté. Décommente et adapte. Au strict minimum, pour qu'une IA puisse t'aider :

`catalog/forges.yaml` — une entrée :

```yaml
- id: ma-forge
  name: Ma Forge Git
  url: https://git.example.com
  status: active
```

`catalog/nodes.yaml` — au moins la workstation où tu codes :

```yaml
- id: workstation
  hostname: workstation
  role: dev
  os: arch
  status: active
```

`catalog/projects.yaml` — un premier projet :

```yaml
- id: mon-projet
  name: Mon Projet
  path: mon-projet
  forge_id: ma-forge
  repo: mon-projet
  node_ids: [workstation]
  status: active
```

Valide :

```bash
make lint
# attendu : forges=1 nodes=1 vaults=0 projects=1 \n OK
```

## 3. Scaffold le dossier du projet

```bash
.venv/bin/python tools/project_init.py mon-projet
```

Cela crée `mon-projet/{user,claude,openai,shared,last}/` avec les fichiers vides attendus, dont `mon-projet/last/session.md` qui pilote la reprise de session IA.

## 4. Première session IA

Pointe ton IA sur `MAP.md`, puis sur l'entrée du projet :

```
Lis MAP.md, puis catalog/projects.yaml pour l'entrée id: mon-projet,
puis mon-projet/last/session.md. Demande-moi confirmation que la
dernière tâche est close avant d'agir.
```

À la fin de la session, demande à l'IA d'écraser `mon-projet/last/session.md` avec l'état final. Au prochain reload, ces ~1 000 tokens suffisent à reprendre.

## 5. Première tâche humaine

Quand l'IA croise quelque chose qui demande une action de toi (validation, accès physique, décision), elle ne le dilue pas dans une note. Elle fait :

```bash
tools/user-task mon-projet "Faire l'audit final du sprint" --priority A --deadline 2026-06-01
```

L'entrée atterrit dans `mon-projet/user/tasks.org` au format chronolion-importable. Les flags `--no-push` et `--no-notify` désactivent respectivement l'envoi à chronolion et la notification Matrix si tu n'as pas branché ces intégrations.

## 6. UI optionnelle

Pour éditer le catalog ou parcourir les fichiers d'un projet à la souris :

```bash
make serve   # bind 127.0.0.1:8001, filtre IP middleware
# arrêter : make stop
```

L'UI est en lecture-écriture sans auth, restreinte aux réseaux loopback / RFC1918 (cf. `tools/server.py:26`). Ne l'expose pas au-delà.

## 7. Avant de publier ton fork

Pour les nodes/vaults qui ne doivent jamais quitter ta machine, décommente les lignes correspondantes dans `.gitignore`. Tu peux aussi tenir deux working trees distincts, l'un public, l'autre privé.

## Pour aller plus loin

- `MAP.md` : la même doc côté IA, plus dense.
- `philosophie.md` : pourquoi sextant existe, économies de tokens mesurées.
- `helpers/claude/credentials.md` : modèle d'auth git via vault.
- `helpers/claude/user-task.md` : arbre de décision IA "faire / déléguer".
