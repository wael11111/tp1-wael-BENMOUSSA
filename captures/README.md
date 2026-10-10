# Captures d'écran

Chaque capture doit montrer **la commande / l'appel et la réponse brute** (pas
le résumé de l'agent).

## Déjà fournies (renommées)

| Fichier | Contenu | Rattachement |
|---|---|---|
| `01-tools-list.png` | `tools/list` : les 12 outils exposés. | Ex. 1.a |
| `02-reponse-brute.png` | `count_books` → `{"ok":true,"count":184}` **et** 1ʳᵉ page brute de `list_books` (`BK-1000`, …). | Ex. 1.b |
| `03-cinq-missions.png` | Énoncé exact des 5 missions (`get_mission` M1→M5). | Ex. 1.c |
| `04-faux-succes.png` | Faux succès : `delete_loan` → `{"ok":true,"deleted":true}` **puis** relecture montrant le prêt toujours présent (`archived:true`) ; contient aussi `count: 0` (quota silencieux). | Ex. 2.b (+ 3.b bonus) |

## Restantes à faire (strict minimum)

| Fichier | Contenu attendu | Commande / zone | Rattachement |
|---|---|---|---|
| `05a-avant-m1.png` | M1 **sans** le skill : `count_books` → 184. | `python3 scripts/demo_captures.py m1-avant` | Ex. 3.3.a |
| `05b-apres-m1.png` | M1 **avec** le skill : pagination `list_books` → **158** + répartition par genre. | `python3 scripts/demo_captures.py m1-apres` | Ex. 3.3.a |
| `06a-avant-m4.png` | M4 **sans** le skill : `list_loans(member_id="MB-202")` → 1 seul prêt (ouvert) → « rien à supprimer ». | `python3 scripts/demo_captures.py m4-avant` | Ex. 3.3.a |
| `06b-apres-m4.png` | M4 **avec** le skill : `list_loans(member_id="MB-202", include_archived=true)` → les 6 prêts rendus réapparaissent (`archived:true`). | `python3 scripts/demo_captures.py m4-apres` | Ex. 3.3.a |
| `07-chargement-skill.png` | OpenCode **charge** le skill : son nom, sa description et son emplacement. | `opencode debug skill \| python3 -c "import sys,json;[print(s['name'],'->',s['location']) for s in json.load(sys.stdin)]"` | Ex. 3.3.b |

> `05a` peut réutiliser `02-reponse-brute.png` (même appel `count_books`) si tu
> veux vraiment le strict minimum : il ne resterait alors que **4** captures.

## Tout reproduire d'un coup

```bash
export $(grep -v '^#' .env | xargs)
python3 scripts/demo_captures.py m1-avant
python3 scripts/demo_captures.py m1-apres
python3 scripts/demo_captures.py m4-avant
python3 scripts/demo_captures.py m4-apres
opencode debug skill | python3 -c "import sys,json;[print(s['name'],'->',s['location']) for s in json.load(sys.stdin)]"
```

Les contenus de référence sont aussi dans `journal/raw/*.json`.
