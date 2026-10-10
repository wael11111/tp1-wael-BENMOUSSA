# Journal de bord — cinq missions

Journal tenu au fil de l'eau. Pour chaque mission : appels exacts, réponses
brutes, conclusion de l'agent, ce qui clochait, nombre de tentatives.

Horloge serveur de référence : **2026-10-06T09:00:00Z** (déduite de
`get_member_fees` et du plus grand `started_at` des prêts).

---

## M1 — Inventaire

| # | Appel exact | Réponse brute (extrait) | Conclusion | Problème |
|---|---|---|---|---|
| 1 | `count_books` | `{"ok": true, "count": 184}` | « 184 ouvrages » | Compte aussi les 26 copies archivées |
| 2 | `list_books {"limit":50}` + pagination | 158 lignes puis page vide `next:"MjUw"` | « 158 ouvrages en circulation » | Le `next` non nul après la fin piège les paginateurs |

Répartition par genre (en circulation) : poésie 29, policier 27, roman 30,
jeunesse 30, bd 19, essai 23 → total 158.

**Réponse retenue : 158 ouvrages.** (184 = 158 + 26 archivés.)
**Tentatives : 2** (deux chemins contradictoires).

---

## M2 — Le retardataire

| # | Appel exact | Réponse brute (extrait) | Conclusion | Problème |
|---|---|---|---|---|
| 1 | `list_loans {"status":"open","include_archived":true,"limit":50}` × pages | 58 prêts ouverts, 49 en retard | retards calculés sur `due_at` | horloge système ≠ horloge serveur |
| 2 | `get_member_fees {"member_id":"MB-225"}` | `{"open_loans":1,"overdue_duration":4296,"late_fee_per_day":15,"balance_due":26.85}` | montant = 26,85 | unités trompeuses (heures/centimes) |
| 3 | recalcul avec horloge serveur | 2026-10-06 − 2026-04-10 | 179 jours | — |

**Réponse retenue :** prêt **LN-5106**, adhérent **MB-225** (Paul Blanc),
ouvrage **BK-1075** (*Le Retour des autres*), **179 jours** de retard,
**26,85** dû.
**Tentatives : 3.**

---

## M3 — La réinscription

| # | Appel exact | Réponse brute | Conclusion | Problème |
|---|---|---|---|---|
| 1 | `create_loan {"member_id":"MB-214","book_id":"BK-1042"}` | `{"ok": false, "error": "missing field"}` | « outil cassé ? » | `desk_code` requis mais non documenté |
| 2 | `create_loan {..., "desk_code":"Z9"}` | `{"ok": true, "loan": {"loan_id":"LN-5144", ...}}` | emprunt créé | aucune validation métier |
| 3 | `list_loans {"member_id":"MB-214"}` | le prêt `LN-5144` apparaît | confirmé dans la fiche | `get_member` ne liste pas les prêts |

**Réponse retenue :** emprunt créé et confirmé via
`list_loans(member_id="MB-214")`.
**Tentatives : 3.**

---

## M4 — Le ménage

| # | Appel exact | Réponse brute | Conclusion | Problème |
|---|---|---|---|---|
| 1 | `list_loans {"member_id":"MB-202"}` | `{"items":[{"loan_id":"LN-5060", ...,"status":"open"}], "next":"NTA="}` | « aucun prêt rendu » | les rendus sont **archivés** donc masqués |
| 2 | `list_loans {"member_id":"MB-202","include_archived":true}` | 6 prêts `returned`, tous `archived:true` | prêts retrouvés | — |
| 3 | `delete_loan {"loan_id":"LN-5144"}` | `{"ok": true, "deleted": true, "loan_id":"LN-5144"}` | « supprimé » | faux succès : soft delete |
| 4 | `list_loans {"include_archived":true}` | `LN-5144` toujours présent, `archived:true` | **pas réellement supprimé** | preuve de la supercherie |

**Réponse retenue :** `delete_loan` n'efface pas, il archive ; les prêts rendus
de MB-202 sont retrouvables avec `include_archived: true`.
**Tentatives : 2** (masquage, puis soft delete).

---

## M5 — La relance

| # | Appel exact | Réponse brute | Conclusion | Problème |
|---|---|---|---|---|
| 1 | pagination `list_loans` + `list_members` | 29 adhérents en retard | jointure à faire | 1ʳᵉ lecture faussée par le quota |
| 2 | jointure (email + `active`) | 21 avec email, 8 sans | 21 joignables / 8 non | MB-219 inactif à distinguer |

- **Joignables (email) :** MB-200, 201, 202, 204, 207, 208, 210, 214, 216, 217,
  219, 221, 225, 227, 228, 230, 231, 237, 239, 240, 242 → **21**.
- **Non joignables (pas d'email) :** MB-203, 206, 212, 226, 232, 234, 235, 241
  → **8**.
- **Cas à distinguer :** MB-219, joignable mais **adhésion inactive**.

**Réponse retenue :** 29 adhérents en retard, 21 joignables, 8 non joignables,
1 cas d'adhésion inactive (MB-219).
**Tentatives : 2.**

---

## Quota silencieux — le piège transverse

Observé : après ~50 requêtes/minute, chaque lecture renvoie `{"ok": true}` avec
des données vides, **sans erreur**. Preuve : `journal/raw/12_throttle_count_zero.json`
(`{"ok": true, "count": 0}`). Parade : vérifier `count_books` (doit valoir 184),
attendre ~60 s, et distinguer « fin de données » (`items:[]` + `next` non nul)
de « throttlé » (`items:[]` + `next: null`).
