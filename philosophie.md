# Philosophie — charger, sprinter, clear

## D'où vient sextant

Un seul problème, vu sous deux angles.

**Côté humain — la lassitude.** À chaque session, l'IA repose les mêmes questions de plomberie :

- Où est le code de ce projet ?
- Quelle forge l'héberge ?
- Comment on commit, comment on push ?
- Où est le token, comment on s'authentifie ?
- Qui déploie quoi sur quel serveur ?
- C'était quoi déjà ce projet, et où on en était hier ?

On répète, on copie-colle des chemins, on cite des endpoints. Au bout de dix sessions on est usé d'expliquer.

**Côté machine — le contexte qui explose.** Cette redécouverte se paie en tokens. Un bootstrap exploratoire (lire `CLAUDE.md`, deviner les conventions, scanner `env.example`, retrouver le remote git, reconstruire la topologie ansible) coûte facilement 10–30k tokens, davantage sur un gros repo. Et chaque tour suivant repaie l'historique en input. La session devient lente, dérive, finit en confusion entre projets.

**Côté doc — la dérive.** Le `CLAUDE.md` qu'on relit pour s'orienter a lui-même grossi par accrétion. Sections obsolètes côtoient sections vivantes, conventions abandonnées traînent à côté des actuelles, contradictions enfouies remontent au mauvais moment. Même après relecture intégrale, tu n'es pas sûr de ce qui tient encore. Le scan ne te donne pas une réponse, il te donne un brouillard de réponses possibles.

Les trois faces se renforcent : la lassitude vient de ce que c'est coûteux à chaque fois, le coût vient de ce qu'il n'y a pas de raccourci stable, la dérive vient de ce que la doc unique accumule sans jamais purger. Sextant est ce raccourci stable, et sa structure est conçue contre les trois faces à la fois :

- **`catalog/`** — source de vérité unique pour la plomberie (forges, nodes, vaults, services, projets). YAML liné, pas de prose, règle d'or "si c'est ici, on ne le duplique pas ailleurs". La dérive ne peut pas s'y installer parce que la duplication est interdite.
- **`helpers/<audience>/`** — notes transverses courtes (credentials, git, woodpecker, servers), chargées à la demande sur trigger, jamais en bloc. Si un helper est vide, il n'existe pas.
- **`<projet>/<audience>/`** — notes par projet séparées strictement : `claude/` pour l'IA, `user/` pour l'humain, `openai/` pour une autre IA, `shared/` pour la doc générale. Pas de mélange, donc pas d'érosion d'un dossier par les concerns d'un autre.
- **`<projet>/last/session.md`** — état point-in-time, réécrit à chaque sprint plutôt qu'enrichi. C'est la seule pièce volontairement périssable.

Pas un seul fichier qui accumule tout. Plusieurs petits, chacun avec un scope clair, une règle de mise à jour, et un linter qui chasse la duplication. La fatigue humaine, l'explosion de contexte et la dérive documentaire se résolvent ensemble parce qu'elles avaient la même cause : pas de structure qui force la révision.

## La boucle

```
charger un projet   →   sprint focalisé   →   /clear   →   charger le suivant
     ~1k tokens             borné                0                ~1k tokens
```

Trois invariants :

1. **Bootstrap stable** — `MAP.md` route vers `catalog/` (où vit la plomberie : forges, nodes, vaults, services, projets) et vers `<projet>/last/session.md` (où on en était). Pas de scan, pas de redécouverte.
2. **Sprint borné** — une tâche, un état tenu à jour dans `last/session.md`. Quand la tâche est livrée, on clear sans regret.
3. **Clear gratuit** — grâce à (1), le clear ne coûte que ~1k au tour suivant. On peut clear à la fin de chaque sprint, ou dès qu'on sent une dérive de contexte.

## Économie au bootstrap

Mesures réelles sur un repo CMDB de 3 177 fichiers, ~20 MB hors `.git`. "Reprise" signifie : l'IA sait où est le code, comment commit/push, ce que fait le projet, et où en était la dernière session.

| Méthode de reprise | Tokens | Ratio | Couvre la plomberie ? |
|---|---:|---:|---|
| Sextant (`MAP` → `catalog` → `<projet>/last` + `claude`) | ~1 035 | 1× | oui (forge, push, vault, état) |
| `CLAUDE.md` du repo seul | ~10 500 | 10× | non — pas d'infra topology |
| `CLAUDE.md` + README + API + SECURITY + compose + env | ~29 800 | 29× | partiellement (compose/env donnent des indices) |
| Scan complet doc + schéma SQL | ~92 000 | 89× | oui mais coûteux |
| Repo intégral | ~5 100 000 | infaisable | — |

Le point n'est pas que sextant lit moins que `CLAUDE.md`. Le point est que sextant **répond directement** à "où, comment, avec quoi" — alors que `CLAUDE.md` répond à "quelles conventions" et laisse le reste à reconstituer.

## Économie cumulée sur session longue

Le bootstrap n'est qu'une partie. Le vrai effet est compound : sur 20 tours d'une session active, sans clear, chaque tour repaie l'historique entier en input.

| Régime | Contexte par tour | Coût input cumulé (~20 tours) |
|---|---:|---:|
| Sans sextant, pas de clear | 50k → 250k tokens (croissant) | ~3 000 000 tokens |
| Avec sextant, clear toutes les 4–5 tours | borné ~30k tokens | ~600 000 tokens |

Facteur 5× à 10× sur le débit d'une session, et une qualité d'attention nettement meilleure : contexte court = moins de bruit, moins de confusion entre projets, moins de hallucination sur des artefacts vus 80 tours plus tôt.

## Ce que sextant n'est pas

- **Pas une base de connaissance.** Le code reste source de vérité ; sextant pointe vers le code, ne le duplique pas.
- **Pas un PKM.** Pas de prose dans les YAML, pas d'historique narratif. Juste : où trouver quoi, et où en était la dernière session.
- **Pas un orchestrateur.** Aucun process tourne, aucune IA n'est appelée. C'est un index plat, multi-audience, en fichiers texte.
- **Pas un remplaçant de `CLAUDE.md`.** Les deux coexistent : `CLAUDE.md` dans le repo donne les conventions du code ; sextant donne la position du projet dans l'écosystème.

## La discipline qui rend la promesse vraie

Le système ne tient que si `last/session.md` est écrit à la fin de chaque sprint. C'est l'unique point de défaillance — et la seule discipline demandée, humaine ou IA. En contrepartie de cette ligne tenue à jour, on gagne le droit de clear sans coût.
