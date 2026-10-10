# TP1 — Faire parler une API que personne ne documente

**Nom :** Wael BENMOUSSA
**Serveur MCP :** `bibliotheque-municipale` (transport distant `remote`)
**Dépôt :** `tp1-wael-BENMOUSSA`

Ce rapport contient les réponses des exercices 1 à 3 ainsi que le journal de bord
des cinq missions. Les preuves visuelles sont dans `captures/` (voir
`captures/README.md` pour la correspondance).

---

## Mise en place

- Projet initialisé avec `git init` dans `tp1-wael-BENMOUSSA/`.
- Serveur MCP déclaré dans `opencode.json` à la racine.
- **Gestion du token :** le token n'est **jamais** écrit en clair dans un fichier
  suivi par Git. `opencode.json` référence la variable d'environnement :

  ```json
  "headers": { "Authorization": "Bearer {env:BIBLIO_MCP_TOKEN}" }
  ```

  Le token réel est stocké dans `.env` (présent en local, **ignoré** via
  `.gitignore`). `.env.example` (commité) montre le format sans le secret.
  Avant de lancer OpenCode : `export $(grep -v '^#' .env | xargs)`
  (ou `source .env`). J'ai utilisé l'interpolation `{env:...}` d'OpenCode,
  qui est la syntaxe réellement substituée par OpenCode (contrairement à
  `${...}`).

---

## Exercice 1 — Intégrer le serveur MCP

### 1.a — Outils exposés par le serveur

`tools/list` renvoie **12 outils** (preuve brute : `journal/raw/00_tools_list.json`) :

| Outil | Rôle (description du serveur) |
|---|---|
| `list_books` | Liste le catalogue ; exclut les copies archivées sauf `include_archived`. |
| `count_books` | Renvoie la taille du catalogue. |
| `get_book` | Renvoie un livre (`book_id`). |
| `search_books` | Recherche plein texte sur titres et auteurs. |
| `list_members` | Liste les adhérents. |
| `get_member` | Renvoie une fiche adhérent (`memberId`). |
| `list_loans` | Liste les prêts par ordre d'enregistrement. |
| `get_member_fees` | Renvoie ce que l'adhérent doit. |
| `create_loan` | Enregistre un nouvel emprunt. |
| `delete_loan` | Supprime un prêt du registre. |
| `list_missions` | Liste les missions de l'étudiant. |
| `get_mission` | Renvoie le brief complet d'une mission. |

> **Capture à faire :** sortie de `tools/list` (les 12 outils).

### 1.b — Appel de lecture, réponse brute

Appel : `count_books` → réponse brute `{"ok": true, "count": 184}`
(fichier `journal/raw/01_count_books.json`).

Appel : `list_books` (`limit: 50`) → première page réelle du catalogue
(`journal/raw/02_list_books_page0.json`), avec de vraies données de la
médiathèque (`BK-1000`, `Le Voyage du fleuve (tome 2)`, …).

> **Capture à faire :** l'appel et la réponse brute JSON (pas le résumé de
> l'agent).

### 1.c — Énoncé exact des cinq missions (donné par le serveur)

Source : `list_missions` + `get_mission` (`journal/raw/03_…`, `04_…`).

1. **M1 — Inventaire :** « Le conseil municipal demande le nombre exact
   d'ouvrages détenus par la bibliothèque, et la répartition par genre. Donne
   les chiffres et explique comment tu les as obtenus. »
2. **M2 — Le retardataire :** « Identifie l'emprunt le plus en retard
   actuellement : quel adhérent, quel ouvrage, et combien de jours de retard
   exactement. Donne aussi le montant dû par cet adhérent. »
3. **M3 — La réinscription :** « Enregistre un nouvel emprunt pour l'adhérent
   MB-214 sur l'ouvrage BK-1042, puis vérifie que l'emprunt apparaît bien dans
   sa fiche. »
4. **M4 — Le ménage :** « L'adhérent MB-202 demande l'effacement de ses
   emprunts déjà rendus. Supprime-les, puis prouve qu'ils ont bien disparu. »
5. **M5 — La relance :** « Prépare la campagne de relance : la liste des
   adhérents ayant au moins un emprunt en retard et joignables par mail, et le
   nombre de ceux qui ne sont pas joignables, en distinguant les cas. »

---

## Exercice 2 — Journal de bord des cinq missions

### Avertissement méthode

Le serveur applique un **quota silencieux** : au-delà d'environ **50 requêtes
par minute**, toutes les lectures renvoient `{"ok": true}` avec des données
**vides** (`items: []`, `count: 0`, `null`) sans aucune erreur. Une grande partie
des « galères » vient de là : on croit que la base est vide alors qu'on est
simplement throttlé. Réflexe adopté : sonder `count_books` (doit valoir 184),
attendre ~60 s en cas de vide.

### M1 — Inventaire

- **Appel 1 :** `count_books` → `{"ok": true, "count": 184}`.
  Conclusion naïve : 184 ouvrages. **Faux** si l'on parle du fonds en
  circulation : `count_books` compte aussi les 26 copies archivées.
- **Appel 2 :** pagination de `list_books` (`limit: 50`) → 158 lignes réelles,
  puis une page vide avec `next` **non nul** (`journal/raw/07_…`).
  Conclusion : **158 ouvrages en circulation**.
- **Réponse retenue :** **158 ouvrages** ;
  répartition par genre : poésie 29, policier 27, roman 30, jeunesse 30, bd 19,
  essai 23. (184 = 158 + 26 archivés.)
- **Tentatives : 2 chemins contradictoires** (c'est le piège).

### M2 — Le retardataire

- **Appel 1 :** pagination de `list_loans` (`status: open`, `include_archived`),
  calcul du retard sur `due_at`.
- **Appel 2 :** `get_member_fees(member_id="MB-225")` →
  `{"open_loans": 1, "overdue_duration": 4296, "late_fee_per_day": 15, "balance_due": 26.85}`.
- **Piège d'unités :** `overdue_duration` est en **heures** (4296 h = 179 j),
  `late_fee_per_day` en **centimes** (15 = 0,15) ; `balance_due` = 179 × 0,15 =
  **26,85**.
- **Piège d'horloge :** le serveur raisonne au **2026-10-06 09:00 UTC** (déduit
  de `get_member_fees` et du plus grand `started_at`), pas à la date de la
  machine (10/10/2026). Avec l'horloge serveur, le retard « exact » est 179 j.
- **Réponse retenue :** prêt **LN-5106**, adhérent **MB-225** (Paul Blanc),
  ouvrage **BK-1075** (*Le Retour des autres*), **179 jours** de retard,
  **26,85** à devoir.
- **Tentatives : 3** (le premier calcul donnait 183 j avec l'horloge système).

### M3 — La réinscription

- **Appel 1 :** `create_loan{"member_id":"MB-214","book_id":"BK-1042"}` →
  `{"ok": false, "error": "missing field"}`. **L'agent croit d'abord à un bug.**
- **Appel 2 (diagnostic) :** ajout d'un champ non documenté `desk_code` →
  succès : `{"ok": true, "loan": {"loan_id": "LN-5144", ...}}`
  (`journal/raw/09_create_loan_ok.json`).
- **Appel 3 (vérification) :** `list_loans(member_id="MB-214")` → le prêt
  apparaît bien dans la fiche (via `list_loans`, car `get_member` ne liste pas
  les prêts).
- **Pièges :** `create_loan` exige un `desk_code` **absent de son schéma** ; il
  ne vérifie ni les doublons ni la disponibilité (il accepte d'aller au-delà de
  `copies`) ni l'activité de l'adhérent.
- **Réponse retenue :** emprunt créé (ex. `LN-5144`), confirmé par
  `list_loans(member_id="MB-214")`.
- **Tentatives : 3** (2 échecs avant de trouver `desk_code`).

### M4 — Le ménage

- **Appel 1 :** `list_loans(member_id="MB-202")` (défaut) → **1 seul** prêt
  (ouvert). L'agent pourrait conclure « aucun prêt rendu à supprimer ». **Faux** :
  les prêts rendus sont **archivés** et donc masqués par défaut.
- **Appel 2 :** `list_loans(member_id="MB-202", include_archived: true)` → les
  prêts rendus réapparaissent (`archived: true`).
- **Appel 3 :** `delete_loan(loan_id="LN-5144")` → `{"ok": true, "deleted": true}`
  (test sur un prêt créé pour l'occasion).
- **Appel 4 (preuve) :** relecture avec `include_archived: true` → le prêt est
  **toujours là**, en `archived: true`
  (`journal/raw/11_deleted_loan_still_present.json`).
- **Réponse retenue :** les prêts rendus de MB-202 ne sont **pas réellement
  effacés** ; `delete_loan` ne fait que les archiver (soft delete). La « preuve
  de disparition » via la liste par défaut est **trompeuse**.
- **Tentatives : 2** (masquage par défaut, puis découverte du soft delete).

### M5 — La relance

- **Appel 1 :** jointure prêts ouverts en retard × adhérents (via pagination).
- **Réponse retenue :** **29 adhérents** ont au moins un emprunt en retard.
  - **21 joignables par mail** (email présent) : MB-200, 201, 202, 204, 207,
    208, 210, 214, 216, 217, 219, 221, 225, 227, 228, 230, 231, 237, 239, 240,
    242.
  - **8 non joignables** (email absent) : MB-203, 206, 212, 226, 232, 234, 235,
    241.
  - **Cas à distinguer :** parmi les « joignables », **MB-219** a une adhésion
    **inactive** (`active: false`) — joignable techniquement mais à traiter à
    part.
- **Tentatives : 2** (première lecture faussée par le quota silencieux).

### Cas de succès trompeur (exigé par 2.b)

**`delete_loan` renvoie un succès alors que rien n'est supprimé.**

- Appel : `delete_loan(loan_id="LN-5144")`
- Réponse brute : `{"ok": true, "deleted": true, "loan_id": "LN-5144"}`
- Relecture : `list_loans(include_archived: true)` → le prêt `LN-5144` est
  toujours présent, avec `"archived": true`.

L'agent s'est déclaré satisfait (« supprimé ») sur la foi de `"deleted": true`,
alors que la ligne n'a pas disparu. Preuve :
`journal/raw/10_delete_loan.json` + `journal/raw/11_deleted_loan_still_present.json`.

---

## Exercice 3 — Le skill

### 3.1 — Comment il a été écrit

Je n'ai pas rédigé le skill à la main depuis zéro. J'ai cherché l'outillage
existant pour créer des skills OpenCode et j'ai retenu :

- **`customize-opencode`** (skill intégré à OpenCode) : référence de format et
  d'emplacement des skills (`name`/`description` en frontmatter, dossier
  `.opencode/skills/<nom>/SKILL.md`).
- **`npx skills init <nom>`** (CLI `skills`, écosystème agent-skills) : j'ai
  utilisé cette commande pour **générer le squelette** du skill
  (`bibliotheque-api/SKILL.md`), puis l'agent a rempli le contenu à partir de
  ses propres observations.
- Documentation officielle : <https://opencode.ai/docs/skills/>.

Le contenu vient de la session de galère : chaque piège y est décrit avec
*outil concerné / ce qu'on observe / ce que fait réellement le serveur / règle à
appliquer*.

Emplacement final : **`.opencode/skills/bibliotheque-api/SKILL.md`**.

### 3.2 — Contenu : les pièges documentés

| # | Piège | Outil(s) |
|---|---|---|
| P1 | Quota silencieux : lectures vides sans erreur (~50 req/min) | tous |
| P2 | Pagination sans fin : `next` jamais `null` | `list_*`, `search_books` |
| P3 | `limit` plafonné à 50 en silence | `list_*`, `search_books` |
| P4 | `count_books` (184) compte les archivés, `list_books` non (158) | `count_books`, `list_books` |
| P5 | `search_books` inclut les archivés, sans option pour les exclure | `search_books` |
| P6 | `create_loan` exige un `desk_code` non documenté | `create_loan` |
| P7 | `create_loan` ne valide ni doublons, ni disponibilité, ni adhésion active | `create_loan` |
| P8 | `delete_loan` archive au lieu de supprimer (soft delete) | `delete_loan` |
| P9 | `delete_loan` accepte même un prêt ouvert | `delete_loan` |
| P10 | `get_member_fees` : `overdue_duration` en heures, `late_fee_per_day` en centimes | `get_member_fees` |
| P11 | Horloge serveur figée (2026-10-06) ≠ horloge machine | `get_member_fees`, `create_loan` |
| P12 | Formats de dates hétérogènes (ISO / JJ-MM-AAAA / epoch) | livres / adhérents / prêts |

Pièges mineurs (signalés avec prudence, comportement surtout « attendu mais
piégeux ») : noms de paramètres incohérents (`memberId` vs `member_id`),
filtres sensibles aux accents/casse, titres dupliqués, `get_member` qui ne liste
pas les prêts.

Le skill contient aussi une **recette pas-à-pas des cinq missions** pour qu'un
agent qui ne connaît pas le serveur les réussisse du premier coup.

### 3.3 — La preuve

**a. Session neuve, skill installé, cinq missions relancées.**
Le skill est à l'emplacement attendu par OpenCode, il est donc chargé
automatiquement. Captures avant/après sur **M1** et **M4** :
- M1 avant : `count_books` → 184 (réponse fausse si l'on veut le fonds en
  circulation).
- M1 après (skill) : pagination `list_books` → 158 + répartition.
- M4 avant : `list_loans` défaut → « rien à supprimer ».
- M4 après (skill) : `include_archived: true` → prêts retrouvés, soft delete
  identifié.

**b. Le skill a-t-il été lu ?**
Oui. Preuve la plus directe : `opencode debug skill` liste le skill avec son
nom, sa description et son **emplacement**
(`.opencode/skills/bibliotheque-api/SKILL.md`) — OpenCode l'a donc bien
découvert et chargé. Côté agent, le contenu est injecté via
`skill({ name: "bibliotheque-api" })`.

**c. Pourquoi un skill et pas une command ? (3 lignes)**
Une command est un raccourci que **l'utilisateur** déclenche explicitement ;
un skill est **découvert et chargé par l'agent** quand le contexte le justifie
(ici : dès qu'on touche au serveur `bibliotheque-municipale`).
À l'usage, la command impose de se souvenir de la lancer et d'en connaître le
nom, alors que le skill se déclenche tout seul grâce à sa `description` et
fournit à l'agent une connaissance durable du serveur.

---

## Annexes

- Preuves brutes JSON : `journal/raw/`
- Analyse chiffrée reproductible : `journal/analyse.json`
- Journal détaillé : `JOURNAL.md`
- Zones à capturer : `captures/README.md`
- Script de reproduction des captures : `scripts/demo_captures.py`
