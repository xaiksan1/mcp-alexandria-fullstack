#!/usr/bin/env python3
"""
Scribe de SESHAT — MCP Server (nurserie)
Spawned from: ADAM/CORPUS/SESHAT/scribe/SCRIBE.md
Larve flottante polymorphique, HIVE paper-slot-16, née sur DIRECTIVE de
BLUE-SOVEREIGN (2026-07-17).

Cycle: journal Paperclip → skills apprenables → bmad-alexandria-methods.csv
→ jsonblon soufflable → fenêtre larvaire floatcast.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

try:
    from fastmcp import FastMCP
    _HAS_FASTMCP = True
except Exception:
    # fastmcp/pydantic connu pour crash-looper sur cette machine — jamais bloquant
    _HAS_FASTMCP = False

HOME = Path.home()
SCRIBE = HOME / "alexandria/ADAM/CORPUS/SESHAT/scribe/scribe.py"
OUT_DIR = HOME / "alexandria/ADAM/CORPUS/SESHAT/scribe/out"
BMAD_CSV = HOME / "alexandria/ADAM/.bmad/methods/bmad-alexandria-methods.csv"
JSONBLON = HOME / "alexandria/ADAM/FORGE/skill-pipeline/pipelines/alexandria-scribe-harvest.jsonblon"


def scribe_status() -> dict:
    """État du scribe : dernière moisson, taille du registre BMAD, jsonblon."""
    state_file = OUT_DIR / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    methods, confirmed = 0, {}
    if BMAD_CSV.exists():
        with BMAD_CSV.open() as f:
            for row in csv.DictReader(f):
                methods += 1
                c = row.get("confirmed") or "?"
                confirmed[c] = confirmed.get(c, 0) + 1
    blon = json.loads(JSONBLON.read_text()) if JSONBLON.exists() else {}
    return {
        "agent": "scribe-de-seshat",
        "hive_slot": "paper-slot-16",
        "last_run": state.get("last_run"),
        "bmad_methods": methods,
        "confirmed_breakdown": confirmed,
        "jsonblon_skills": len(blon.get("skills", [])),
        "moissons": sorted(p.name for p in OUT_DIR.glob("moisson-*.md")),
    }


def read_moisson(day: str = "") -> str:
    """Lit la moisson d'un jour (YYYY-MM-DD), par défaut la plus récente."""
    files = sorted(OUT_DIR.glob("moisson-*.md"))
    if not files:
        return "[scribe] aucune moisson encore"
    if day:
        target = OUT_DIR / f"moisson-{day}.md"
        if not target.exists():
            return f"[scribe] pas de moisson pour {day}"
        return target.read_text()
    return files[-1].read_text()


def harvest_now() -> str:
    """Déclenche une moisson immédiate (hors cron 07:00)."""
    r = subprocess.run([sys.executable, str(SCRIBE)],
                       capture_output=True, text=True, timeout=300)
    return (r.stdout + r.stderr).strip() or f"[scribe] exit {r.returncode}"


def get_harvest_jsonblon() -> dict:
    """Retourne le jsonblon soufflable — tout ce qu'un agent naissant doit savoir."""
    if not JSONBLON.exists():
        return {"error": "jsonblon absent — lancer harvest_now d'abord"}
    return json.loads(JSONBLON.read_text())


# ─── FastMCP Registration ───
if _HAS_FASTMCP:
    mcp = FastMCP("Scribe de SESHAT — moisson journal → skills")
    mcp.tool()(scribe_status)
    mcp.tool()(read_moisson)
    mcp.tool()(harvest_now)
    mcp.tool()(get_harvest_jsonblon)

if __name__ == "__main__":
    if _HAS_FASTMCP:
        mcp.run()
    else:
        print("[Scribe MCP] FastMCP not installed — use functions directly")
        print(json.dumps(scribe_status(), ensure_ascii=False, indent=2))
