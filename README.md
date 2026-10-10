# tp1-wael-BENMOUSSA

TP1 — *Faire parler une API que personne ne documente* (Outils d'IA pour
développeurs, 2026/2027).

Branchement du serveur MCP `bibliotheque-municipale`, exécution de cinq missions
sur une API non documentée, puis capitalisation dans un **skill OpenCode**.

## Contenu

| Chemin | Contenu |
|---|---|
| `opencode.json` | Déclaration du serveur MCP (token via `{env:BIBLIO_MCP_TOKEN}`). |
| `.env.example` | Modèle de fichier d'environnement (`.env` n'est pas commité). |
| `.opencode/skills/bibliotheque-api/SKILL.md` | Le skill : pièges de l'API + recette des missions. |
| `RAPPORT.md` | Réponses des exercices 1 à 3 + synthèse du journal. |
| `JOURNAL.md` | Journal de bord détaillé des cinq missions. |
| `journal/raw/` | Preuves brutes JSON (appels et réponses). |
| `journal/analyse.json` | Analyse chiffrée reproductible. |
| `scripts/demo_captures.py` | Reproduit les sorties des zones à capturer. |
| `captures/` | Captures d'écran (voir `captures/README.md`). |

## Mise en route

```bash
cp .env.example .env          # puis renseigner BIBLIO_MCP_TOKEN
export $(grep -v '^#' .env | xargs)
opencode                      # redémarrer après toute modif de config
```

Le token n'est jamais commité : `.env` est listé dans `.gitignore`.
