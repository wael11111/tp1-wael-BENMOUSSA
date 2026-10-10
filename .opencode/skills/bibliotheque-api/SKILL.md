---
name: bibliotheque-api
description: >
  Use when working with the "bibliotheque-municipale" MCP server (outils
  list_books, count_books, get_book, search_books, list_members, get_member,
  list_loans, get_member_fees, create_loan, delete_loan, list_missions,
  get_mission). Documents the traps of this undocumented library API (silent
  quota/empty responses, non-terminating pagination, limit capped at 50,
  count_books counting archived copies, create_loan requiring an undocumented
  desk_code, delete_loan only archiving, get_member_fees units in hours and
  cents) and the exact procedure to run the five missions without falling for
  them.
license: MIT
compatibility: opencode
metadata:
  server: bibliotheque-municipale
  transport: remote-mcp
---

# Bibliothèque municipale — mode d'emploi (API non documentée)

Ce skill décrit le serveur MCP `bibliotheque-municipale` tel qu'il se comporte
**réellement** (et non tel qu'il se décrit). À charger avant tout appel sur ce
serveur. L'API est vieille et incohérente : un appel qui ne renvoie pas
d'erreur n'est pas un appel qui a marché. **Lisez toujours la réponse brute.**

## Règle d'or

Avant de croire un résultat, vérifiez-le par un **second chemin**.
Si deux chemins vers le même chiffre divergent, l'un des deux est piégé.

---

## Pièges confirmés

### P1 — Quota silencieux : les lectures se vident sans erreur
- **Outils concernés :** tous les outils de lecture (`list_*`, `get_*`,
  `count_books`, `search_books`).
- **Ce qu'on observe :** après environ **50 requêtes en moins d'une minute**,
  chaque lecture renvoie `{"ok": true, ...}` mais avec des données vides :
  `{"ok": true, "items": [], "next": null}`, `{"ok": true, "count": 0}`,
  `{"ok": true, "book": null}`, `{"ok": true, "member": null}`,
  `{"ok": true, "mission": null}`. Aucune erreur, aucun code HTTP anormal.
- **Ce que fait réellement le serveur :** il applique un quota/rate-limit par
  token et, une fois dépassé, **renvoie du vide au lieu d'une erreur**.
- **Règle :** ne jamais conclure « pas de données » sur une réponse vide.
  Sonder une valeur de référence connue (`count_books` doit valoir **184**) ;
  si elle vaut 0, on est throttlé : **attendre ~60 s et réessayer**.
  Indice de distinction : une fin de données réelle renvoie `items: []` **avec
  un `next` non nul**, alors que le throttle renvoie `items: []` **avec
  `next: null`**.

### P2 — La pagination ne se termine jamais (`next` n'est jamais null)
- **Outils concernés :** `list_books`, `list_members`, `list_loans`,
  `search_books`.
- **Ce qu'on observe :** après la dernière page utile, le serveur continue de
  renvoyer des pages **vides** avec un `next` **non nul qui s'incrémente**
  (`NTA=`, `MTAw`, `MTUw`, `MjAw`, …). `next` n'est jamais `null`.
  Il est aussi non nul quand tous les résultats tiennent sur une page.
- **Ce que fait réellement le serveur :** `next` est un offset encodé en
  base64, émis même quand il n'y a plus de lignes ; ce n'est **pas** un
  terminateur.
- **Règle :** arrêter la pagination à la **première page vide**
  (`items: []` + `next` non nul). Ne jamais boucler « tant que `next` != null » :
  la boucle ne s'arrête pas (et finit par déclencher P1).

### P3 — `limit` est plafonné à 50, en silence
- **Outils concernés :** `list_books`, `list_members`, `list_loans`,
  `search_books`.
- **Ce qu'on observe :** `{"limit": 1000}` renvoie **50** lignes. La
  description ne parle que d'un défaut de 20, pas d'un maximum.
- **Ce que fait réellement le serveur :** plafonne à 50 sans le dire.
- **Règle :** paginer avec `limit: 50` (P2) ; ne jamais croire qu'un gros
  `limit` a tout ramené.

### P4 — `count_books` compte les exemplaires archivés, `list_books` non
- **Outils concernés :** `count_books`, `list_books` (mission M1).
- **Ce qu'on observe :** `count_books` → **184**. `list_books` par défaut →
  **158** lignes. Écart = **26** ouvrages `archived: true`.
- **Ce que fait réellement le serveur :** `count_books` compte *tout*, y
  compris les copies retirées de la circulation ; `list_books` les exclut par
  défaut (`include_archived`).
- **Règle :** pour le catalogue **en circulation**, se fier à `list_books`
  (`include_archived: false`) → **158**. `count_books` surestime de 26.
  Répartition par genre (en circulation) : poésie 29, policier 27, roman 30,
  jeunesse 30, bd 19, essai 23 (total 158).

### P5 — `search_books` inclut les archivés, sans moyen de les exclure
- **Outil concerné :** `search_books`.
- **Ce qu'on observe :** une recherche renvoie des livres `archived: true`
  (ex. `BK-1002`), et l'outil n'expose aucun `include_archived`.
- **Règle :** filtrer `archived == false` côté client ; ne jamais compter le
  catalogue via `search_books`.

### P6 — `create_loan` exige un `desk_code` non documenté
- **Outil concerné :** `create_loan` (mission M3).
- **Ce qu'on observe :** `{"member_id": "...", "book_id": "..."}` →
  `{"ok": false, "error": "missing field"}`. En ajoutant `desk_code`, l'appel
  réussit.
- **Ce que fait réellement le serveur :** exige un argument `desk_code`
  **absent** de son `inputSchema` (qui ne liste que `member_id`, `book_id`).
- **Règle :** toujours fournir `desk_code` (ex. `"Z9"`), en plus de
  `member_id` et `book_id`.

### P7 — `create_loan` ne valide aucune règle métier
- **Outil concerné :** `create_loan` (mission M3).
- **Ce qu'on observe :** l'emprunt est accepté même pour :
  - un adhérent qui a **déjà** ce même ouvrage (doublons créés : plusieurs
    `LN-…` identiques) ;
  - un ouvrage dont **tous les exemplaires sont déjà empruntés** (création
    au-delà de `copies`) ;
  - un adhérent **inactif** (`active: false`).
  Seuls un `member_id`/`book_id` inexistant ou un livre archivé sont refusés
  (`{"ok": false, "error": "invalid request"}`).
- **Règle :** vérifier soi-même doublons, disponibilité (`copies` vs emprunts
  ouverts) et statut de l'adhérent **avant** de créer.

### P8 — `delete_loan` ne supprime pas : il archive
- **Outil concerné :** `delete_loan` (mission M4).
- **Ce qu'on observe :** `{"ok": true, "deleted": true}`. Le prêt disparaît de
  `list_loans` **par défaut**, mais reste présent avec
  `list_loans(include_archived: true)` en `archived: true`.
- **Ce que fait réellement le serveur :** passe `archived` à `true` (soft
  delete) ; la ligne n'est jamais effacée.
- **Règle :** « prouver la disparition » avec `include_archived: true`. Si un
  vrai effacement est demandé, l'API ne le permet pas.

### P9 — `delete_loan` accepte aussi les prêts ouverts
- **Outil concerné :** `delete_loan` (mission M4).
- **Ce qu'on observe :** supprimer un prêt `status: "open"` renvoie
  `deleted: true`.
- **Règle :** ne jamais utiliser `delete_loan` pour « rendre » un livre.

### P10 — `get_member_fees` : unités trompeuses (heures et centimes)
- **Outil concerné :** `get_member_fees` (mission M2).
- **Ce qu'on observe :** `overdue_duration: 4296`, `late_fee_per_day: 15`,
  `balance_due: 26.85`.
- **Ce que fait réellement le serveur :**
  - `overdue_duration` est en **heures** (4296 h = 179 jours) ;
  - `late_fee_per_day` est en **centimes** (15 = 0,15) ;
  - `balance_due` = (`overdue_duration` / 24) × `late_fee_per_day` / 100
    (ici 179 × 0,15 = 26,85). `balance_due` est déjà le montant en devise.
- **Règle :** diviser `overdue_duration` par 24 pour des jours ; diviser
  `late_fee_per_day` par 100 ; se fier à `balance_due` pour le montant.

### P11 — L'horloge du serveur diffère de l'horloge système
- **Outils concernés :** `get_member_fees`, `create_loan` (mission M2).
- **Ce qu'on observe :** le serveur raisonne sur un « maintenant » figé au
  **2026-10-06 09:00 UTC** (déductible de `get_member_fees` ou du plus grand
  `started_at`), alors que la machine peut afficher une autre date.
- **Règle :** calculer les jours de retard « exacts » avec l'horloge du
  serveur, pas avec la date système. Le montant `balance_due` est la référence.

### P12 — Formats de dates incohérents selon les ressources
- **Outils concernés :** `list_books`/`get_book` (`added_at` en **ISO 8601**
  chaîne), `list_members`/`get_member` (`joined_at` en **JJ/MM/AAAA** chaîne),
  `list_loans` (`started_at`/`due_at`/`returned_at` en **epoch Unix** entier).
- **Règle :** parser chaque ressource avec son propre format.

---

## Pièges mineurs / bonnes pratiques (à ne pas sur-signaler)

- **Noms de paramètres incohérents :** `get_member` attend `memberId`
  (camelCase) ; `get_member_fees` attend `member_id`. Un mauvais nom renvoie
  `{"ok": false, "error": "invalid request"}` — ce n'est pas silencieux.
- **Filtres sensibles aux accents/casse :** `genre: "poesie"` → 0 ;
  `genre: "poésie"` → 29. `status: "OPEN"` → 0 ; `status: "open"` fonctionne.
  Utiliser exactement les valeurs documentées.
- **Titres dupliqués :** plusieurs `book_id` distincts partagent le même
  titre. Toujours identifier un ouvrage par `book_id`.
- **`get_member` ne liste pas les prêts :** pour « voir la fiche » d'un
  adhérent, utiliser `list_loans(member_id=...)`.

---

## Procédure des cinq missions (recette fiable)

0. **Santé :** `count_books` doit renvoyer 184. Sinon, attendre 60 s (P1).
1. **M1 — Inventaire.** Paginer `list_books` avec `limit: 50` jusqu'à la
   première page vide, sans `include_archived` → **158** ouvrages, répartition
   par genre ci-dessus. Ne pas utiliser `count_books` (184, inclut 26 archivés).
2. **M2 — Le retardataire.** Récupérer tous les prêts ouverts, calculer le
   retard avec l'horloge serveur (P11) sur `due_at`. Résultat attendu :
   prêt **LN-5106**, adhérent **MB-225**, ouvrage **BK-1075**, **179 jours** de
   retard, montant dû **26,85** (`get_member_fees`).
3. **M3 — La réinscription.** `create_loan` avec
   `{"member_id":"MB-214","book_id":"BK-1042","desk_code":"Z9"}` (P6), puis
   vérifier via `list_loans(member_id="MB-214")` (P7 : les doublons sont
   possibles).
4. **M4 — Le ménage.** Lister les prêts de MB-202 **avec**
   `include_archived: true` pour voir les prêts rendus ; `delete_loan` ne fait
   que les archiver (P8) — le « effacé » reste récupérable.
5. **M5 — La relance.** Joindre prêts ouverts en retard et adhérents :
   29 adhérents en retard, dont **21 joignables** (email présent) et **8 sans
   email** ; parmi les joignables, **MB-219** a une adhésion inactive (cas à
   distinguer).

---

## Vérification rapide

- `count_books` == 184 **et** `list_books` (défaut, toutes pages) == 158.
- Une page vide avec `next` non nul = fin normale ; vide avec `next: null` =
  throttle → attendre.
- Toute écriture (`create_loan`, `delete_loan`) se re-vérifie en lecture
  (`list_loans` avec `include_archived: true`).
