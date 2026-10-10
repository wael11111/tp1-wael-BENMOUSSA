#!/usr/bin/env python3
"""Petit client MCP pour reproduire les sorties à capturer.

Usage:
    export $(grep -v '^#' .env | xargs)
    python3 scripts/demo_captures.py m1-avant
    python3 scripts/demo_captures.py m1-apres
    python3 scripts/demo_captures.py m4-avant
    python3 scripts/demo_captures.py m4-apres
"""
import json
import os
import sys
import urllib.request

URL = "https://ai-tools-mcp-biblio-production.up.railway.app/mcp"
TOKEN = os.environ.get("BIBLIO_MCP_TOKEN")
if not TOKEN:
    sys.exit("BIBLIO_MCP_TOKEN manquant : `export $(grep -v '^#' .env | xargs)`")

SESSION = {}


def rpc(method, params=None, notify=False):
    payload = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        payload["params"] = params
    if not notify:
        payload["id"] = 1
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if SESSION.get("id"):
        headers["mcp-session-id"] = SESSION["id"]
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    resp = urllib.request.urlopen(req)
    sid = resp.headers.get("mcp-session-id")
    if sid:
        SESSION["id"] = sid
    out = [l[5:].strip() for l in resp.read().decode().splitlines() if l.startswith("data:")]
    return "\n".join(out)


def init():
    rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "demo", "version": "1.0"}})
    rpc("notifications/initialized", {}, notify=True)


def call(name, args):
    raw = rpc("tools/call", {"name": name, "arguments": args})
    for line in raw.splitlines():
        if line.startswith("{"):
            obj = json.loads(line)
            if "result" in obj and "content" in obj["result"]:
                return json.loads(obj["result"]["content"][0]["text"])
    return None


def paginate(tool, base=None):
    base = dict(base or {})
    items, key = [], None
    while True:
        args = dict(base)
        if key:
            args["start_key"] = key
        r = call(tool, args)
        got = r.get("items", [])
        items.extend(got)
        if not got:  # page vide = fin (le `next` n'est jamais null)
            break
        key = r.get("next")
        if not key:
            break
    return items


def m1_avant():
    print("# M1 AVANT le skill : l'agent demande 'combien d'ouvrages' -> count_books")
    print(json.dumps(call("count_books", {}), ensure_ascii=False))
    print("# -> l'agent conclut 184. FAUX : compte aussi les 26 copies archivées.")


def m1_apres():
    print("# M1 AVEC le skill : pagination de list_books (limit 50) jusqu'à page vide")
    books = paginate("list_books", {"limit": 50})
    genres = {}
    for b in books:
        genres[b["genre"]] = genres.get(b["genre"], 0) + 1
    print(json.dumps({"ok": True, "total_en_circulation": len(books), "par_genre": genres}, ensure_ascii=False, indent=2))
    print("# -> 158 ouvrages en circulation (184 = 158 + 26 archivés).")


def m4_avant():
    print("# M4 AVANT le skill : list_loans(member_id=MB-202) par défaut")
    print(json.dumps(call("list_loans", {"member_id": "MB-202", "limit": 50}), ensure_ascii=False, indent=2))
    print("# -> 1 seul prêt (ouvert). L'agent conclut 'aucun prêt rendu à supprimer'. FAUX.")


def m4_apres():
    print("# M4 AVEC le skill : list_loans(member_id=MB-202, include_archived=true)")
    r = call("list_loans", {"member_id": "MB-202", "limit": 50, "include_archived": True})
    returned = [x for x in r.get("items", []) if x["status"] == "returned"]
    print(json.dumps({"ok": True, "prets_rendus_retrouves": returned}, ensure_ascii=False, indent=2))
    print("# -> les prêts rendus existent mais sont archivés (masqués par défaut).")


ZONES = {"m1-avant": m1_avant, "m1-apres": m1_apres, "m4-avant": m4_avant, "m4-apres": m4_apres}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ZONES:
        sys.exit("usage: demo_captures.py {%s}" % "|".join(ZONES))
    init()
    ZONES[sys.argv[1]]()
