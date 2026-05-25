---
description: Clore la session courante et proposer un diff de <projet>/last/session.md (validation explicite avant écriture)
argument-hint: <projet>
allowed-tools: Bash, Read, Write, Edit
---

# /sextant-wrap $1

Mission : synthétiser la session courante et faire valider une mise à jour de `<sextant>/$1/last/session.md` AVANT toute écriture.

## Résolution de la racine sextant

Déterminer `SEXTANT_ROOT` dans cet ordre :

1. Variable d'environnement `$SEXTANT_ROOT` si définie.
2. Sinon `git rev-parse --show-toplevel` exécuté depuis le cwd (le repo courant doit être un clone de sextant).
3. Sinon erreur explicite et stop.

## Procédure (stricte)

1. **Résoudre le projet.**
   ```bash
   grep -P "^$1\t" "$SEXTANT_ROOT/catalog/_index.tsv" | cut -f2
   ```
   Vide → erreur. Lister les ids valides au user via `cut -f1 "$SEXTANT_ROOT/catalog/_index.tsv" | tail -n +2` puis stop.

2. **Lire l'état courant** de `$SEXTANT_ROOT/$1/last/session.md` (peu importe si template vierge ou journal rempli).

3. **Synthétiser la session courante** depuis la conversation, en cinq champs :
   - **objectif** : 1 ligne, ce qu'on visait au démarrage (ou la dérive si différente).
   - **état** : `complete | en cours | bloqué | en attente d'input`.
   - **changements effectifs** : commits, fichiers modifiés, décisions actées. Factuels uniquement. Si zéro commit/edit, le dire.
   - **next** : 1-2 lignes si interruption, `-` si fini.
   - **notes** : contexte ou décision à ne pas perdre pour la prochaine session.

   Si la session n'a produit aucun changement substantiel (simple Q&R, exploration sans suite), NE PAS proposer d'écrasement. Signaler au user que rien ne justifie une mise à jour et s'arrêter.

4. **Construire le contenu proposé.** Format minimal :

   ```
   # session <date du jour> — <résumé une ligne>

   derniere_mise_a_jour: <date du jour>

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

   Date du jour : utiliser `currentDate` du contexte session, format `YYYY-MM-DD`.

   **Préservation du journal antérieur** : `last/session.md` est un journal, pas un écraseur bête. Conserver les sections antérieures encore pertinentes (side-quests non terminés, contexte vivant). Retirer uniquement ce qui n'a plus de valeur (sessions closes et obsolètes). En cas de doute, garder et demander.

5. **Présenter le diff au user.** Afficher l'ancien contenu et le proposé. Si le delta est long, un patch unifié suffit. Terminer par : « OK pour écraser, ou ajustements ? ».

6. **Attendre validation explicite.** Sur OK → écrire avec `Write`. Sur ajustement → itérer à l'étape 4. Jamais d'écriture sans le OK.

## Garde-fous

- Pas d'écriture sans validation explicite du user.
- Pas d'invention : un commit, un fichier ou une décision absents de la session restent absents du résumé.
- Si le sujet a dérivé en cours de session, l'expliciter dans la synthèse plutôt que la masquer.
- Registre soutenu, pas d'emoji, ASCII pur.
- Si `derniere_mise_a_jour` antérieur > 7 j et que le journal contient du contenu en cours, le mentionner avant d'écraser — le user voudra peut-être archiver d'abord.
