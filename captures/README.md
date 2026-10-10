# Captures d'écran

Strict minimum demandé par le sujet. Chaque capture doit montrer **la commande /
l'appel et la réponse brute** (pas le résumé de l'agent).

| Fichier | Zone à capturer | Rattachement |
|---|---|---|
| `01-tools-list.png` | La liste des 12 outils renvoyée par `tools/list` (nom + description), dans la session OpenCode. | Ex. 1.a |
| `02-reponse-brute.png` | Un appel de lecture et sa réponse **brute** JSON, par ex. `count_books` → `{"ok": true, "count": 184}` ou la 1ʳᵉ page de `list_books` (avec `BK-1000`, `Le Voyage du fleuve (tome 2)`…). | Ex. 1.b |
| `03-cinq-missions.png` | L'énoncé exact des 5 missions (sortie de `list_missions` + `get_mission` M1→M5). | Ex. 1.c |
| `04-faux-succes.png` | Le faux succès : `delete_loan` → `{"ok": true, "deleted": true}` **puis** la relecture `list_loans(include_archived:true)` qui montre le prêt toujours présent (`archived:true`). | Ex. 2.b |
| `05a-avant-m1.png` | M1 **sans** le skill : `count_books` → 184. | Ex. 3.3.a |
| `05b-apres-m1.png` | M1 **avec** le skill : pagination `list_books` → 158 + répartition par genre. | Ex. 3.3.a |
| `06a-avant-m4.png` | M4 **sans** le skill : `list_loans(member_id="MB-202")` → « rien à supprimer ». | Ex. 3.3.a |
| `06b-apres-m4.png` | M4 **avec** le skill : `list_loans(member_id="MB-202", include_archived:true)` → prêts rendus retrouvés. | Ex. 3.3.a |
| `07-chargement-skill.png` | Le moment où OpenCode **charge** le skill : la liste des skills disponibles (nom + description) puis l'appel `skill({ name: "bibliotheque-api" })`. | Ex. 3.3.b |

## Optionnel (si une capture de plus est tolérée)

- `08-quota-silencieux.png` : `count_books` → `{"ok": true, "count": 0}` après
  une rafale de requêtes (preuve du quota silencieux).

## Reproduire une capture en ligne de commande

```bash
export $(grep -v '^#' .env | xargs)
# outils
python3 -c "import sys;sys.path.insert(0,'journal');print(open('journal/raw/00_tools_list.json').read())"
# missions
for m in M1 M2 M3 M4 M5; do echo "== $m =="; cat journal/raw/04_mission_$m.json; done
# faux succès
cat journal/raw/10_delete_loan.json journal/raw/11_deleted_loan_still_present.json
```

> Les fichiers `journal/raw/*.json` fournissent le contenu exact à reproduire à
> l'écran pour chaque capture.
