---
description: Clore la session courante et proposer un diff de <projet>/last/session.md (validation explicite avant écriture)
argument-hint: <projet>
allowed-tools: Bash, Read, Write, Edit
---

# /sextant-wrap $1

## Racine sextant

`$SEXTANT_ROOT` si défini, sinon `git rev-parse --show-toplevel`, sinon erreur.

## Procédure

1. **Résoudre le projet.**
   ```bash
   grep -P "^$1\t" "$SEXTANT_ROOT/catalog/_index.tsv" | cut -f2
   ```
   Vide → lister les ids (`cut -f1 "$SEXTANT_ROOT/catalog/_index.tsv" | tail -n +2`) et stop.

2. **Lire** `$SEXTANT_ROOT/$1/last/session.md`.

3. **Synthétiser la session courante** en cinq champs :
   - **objectif** : ce qu'on visait au démarrage (ou la dérive si différente).
   - **état** : `complete | en cours | bloqué | en attente d'input`.
   - **changements effectifs** : commits, fichiers modifiés, décisions actées. Factuels. Zéro commit/edit → le dire.
   - **next** : 1-2 lignes ou `-` si fini.
   - **notes** : contexte ou décision à ne pas perdre.

   Si rien de substantiel (Q&R, exploration sans suite), ne rien proposer et stop.

4. **Construire le contenu proposé** :

   ```
   # session <YYYY-MM-DD> — <résumé une ligne>

   derniere_mise_a_jour: <YYYY-MM-DD>

   ## Objectif

   <1 ligne>

   ## État

   <statut>

   ## Changements

   - <commit hash + message | fichier + nature | décision>

   ## Next

   <1-2 lignes ou tiret>

   ## Notes

   - <contexte à préserver>
   ```

   Date : `currentDate` du contexte session.

   `last/session.md` est un journal : conserver les sections antérieures encore vivantes, retirer uniquement les sessions closes obsolètes. En cas de doute, garder.

5. **Présenter le diff** (patch unifié si long) et terminer par : « OK pour écraser, ou ajustements ? ».

6. **Attendre validation explicite.** OK → `Write`. Ajustement → itérer à 4.

## Garde-fous

- Jamais d'écriture sans OK explicite.
- Aucune invention : commit/fichier/décision absent de la session → absent du résumé.
- Dérive de sujet → l'expliciter, pas la masquer.
- ASCII pur, pas d'emoji.
- `derniere_mise_a_jour` > 7 j avec contenu en cours → le signaler avant d'écraser.
