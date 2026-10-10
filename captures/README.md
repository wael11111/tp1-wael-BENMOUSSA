# Captures d'écran

Chaque capture montre **la commande / l'appel et la réponse brute** (pas le
résumé de l'agent).

## Fournies

| Fichier | Contenu | Rattachement |
|---|---|---|
| `01-tools-list.png` | `tools/list` : les 12 outils exposés. | Ex. 1.a |
| `02-reponse-brute.png` | `count_books` → `{"ok":true,"count":184}` **et** 1ʳᵉ page brute de `list_books` (`BK-1000`, …). | Ex. 1.b |
| `03-cinq-missions.png` | Énoncé exact des 5 missions (`get_mission` M1→M5). | Ex. 1.c |
| `04-faux-succes.png` | Faux succès : `delete_loan` → `{"ok":true,"deleted":true}` **puis** relecture montrant le prêt toujours présent (`archived:true`) ; contient aussi `count: 0` (quota silencieux). | Ex. 2.b |
| `05a-avant-m1.png` | M1 **sans** le skill : `count_books` → 184. | Ex. 3.3.a |
| `05b-apres-m1.png` | M1 **avec** le skill : pagination `list_books` → **158** + répartition par genre. | Ex. 3.3.a |
| `06a-avant-m4.png` | M4 **sans** le skill : `list_loans(member_id="MB-202")` → 1 seul prêt (ouvert) → « rien à supprimer ». | Ex. 3.3.a |
| `06b-apres-m4.png` | M4 **avec** le skill : `list_loans(member_id="MB-202", include_archived=true)` → les 6 prêts rendus réapparaissent (`archived:true`). | Ex. 3.3.a |
| `07-chargement-skill.png` | OpenCode **charge** le skill : `bibliotheque-api -> …/.opencode/skills/bibliotheque-api/SKILL.md`. | Ex. 3.3.b |
| `08-quota-recupere.png` | Bonus : `count_books` → 184 après le `sleep 60` (retour à la normale après le quota silencieux). | Bonus |

Toutes les captures demandées par le sujet sont présentes.

## Reproduire

```bash
export $(grep -v '^#' .env | xargs)
python3 scripts/demo_captures.py m1-avant
python3 scripts/demo_captures.py m1-apres
python3 scripts/demo_captures.py m4-avant
python3 scripts/demo_captures.py m4-apres
opencode debug skill | python3 -c "import sys,json;[print(s['name'],'->',s['location']) for s in json.load(sys.stdin)]"
```

Les contenus de référence sont aussi dans `journal/raw/*.json`.
