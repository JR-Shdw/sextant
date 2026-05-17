# tâches humaines — arbre de décision IA

Quand tu rencontres quelque chose qui ressemble à du travail à faire,
applique CES 2 questions dans l'ordre. Pas de troisième chemin.

## Q1. As-tu besoin de l'autorisation du user pour faire cette action ?

- **Non** → fais-le. Pas de tâche.
- **Oui** → demande à l'utilisateur, puis Q2 selon sa réponse.

## Q2. Est-ce que ça nécessite RÉELLEMENT une action humaine ?

(physique, décisionnelle, accès qu'il est seul à avoir, validation client…)

- **Non** → tu peux le faire toi-même → fais-le.
- **Oui** → crée une tâche, **une seule** commande :

```bash
~/dev/sextant/tools/user-task <projet_id> "<titre>" [--priority A|B|C] [--deadline YYYY-MM-DD]
```

Ça fait, en un coup :
1. append dans `<projet>/user/tasks.org` (format chronolion-importable)
2. push dans chronolion (`POST /api/me/tasks/import-org` sur `$CHRONOLION_URL`, défaut `http://127.0.0.1:8000`)
3. notification Matrix au user

Flags : `--no-push`, `--no-notify` si besoin d'éviter une étape.

## Interdiction

Ne JAMAIS diluer une tâche humaine dans un CLAUDE.md, un README, des notes
diverses. C'est le seul endroit canonique : `<projet>/user/tasks.org`.
