# git auth — IA

Helper global `git-credential-vault` déjà installé et configuré.
Tu ne fais rien. Push/fetch HTTPS marchent partout.

## Mapping host → secret vault

| host | namespace | secret | user |
|---|---|---|---|
| gitea.c0re.me | claude | gitea-claude-write | claude |
| 127.0.0.1 / localhost | claude | forgejo-claude-write | claude |

## Si push échoue

1. Token rhorizon : `~/dev/tools/rhorizon_local/.rhorizon-creds/token`
2. Vault local prioritaire `http://127.0.0.1:8200` ; fallback distant via `$VAULT_REMOTE` si défini
3. Ajouter un host : éditer `~/.local/bin/git-credential-vault` (`case "$host" in`)

Aucun SSH, aucun token statique sur disque.
