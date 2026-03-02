#!/usr/bin/env python3
"""
Cortex Energon MCP Server — ADAM Stack as Claude Code Tools
============================================================
Expose le stack ADAM complet comme outils natifs Claude Code via FastMCP stdio.

Outils:
  cortex_stats        → Phase 3 Hashgraph stats (port 3003)
  send_energy         → Envoyer un batch kWh au Cortex
  bmad_systems        → 20 systèmes BMAD (port 5001)
  energon_ledger      → Ledger total kWh scellés
  services_health     → Santé de tous les services
  hands_status        → État du Cortex Hands autonome
  inject_command      → Exécuter une commande shell (via CortexInjector)
"""

import json
import sys
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastmcp import FastMCP
from cortex_injector import CortexInjector

# ─── Config ───
CORTEX_URL = "http://localhost:3003"
DASHBOARD_URL = "http://localhost:5001"
ADAM_ROOT = Path(__file__).resolve().parent.parent.parent
LEDGER_PATH = ADAM_ROOT / "digital-twin-data" / "energon_ledger.json"
HANDS_STATUS = ADAM_ROOT / "cortex_hands_status.json"

mcp = FastMCP(
    name="cortex-energon",
    instructions=(
        "ADAM Cortex & Energon stack tools. "
        "Use these to monitor and control the Alexandria energy sealing system, "
        "BMAD services, and execute commands via CortexInjector."
    ),
)

injector = CortexInjector()


def _get(url: str, timeout: int = 3) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _post(url: str, payload: dict, timeout: int = 5) -> dict:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── Tools ───

@mcp.tool()
def cortex_stats() -> dict:
    """
    Retourne les statistiques complètes du Cortex V3 (port 3003).
    Inclut: active_engine, phase3 batches/kWh, pending_kwh, router stats.
    """
    res = _get(f"{CORTEX_URL}/api/sealing/stats")
    if not res["ok"]:
        return {"error": res["error"], "cortex_alive": False}
    d = res["data"]
    p3 = d.get("phase3", {})
    return {
        "cortex_alive": True,
        "active_engine": d.get("active_engine"),
        "pending_kwh": d.get("pending_kwh", 0),
        "phase3_batches": p3.get("batches_sealed", 0),
        "phase3_kwh": p3.get("total_kwh_sealed", 0),
        "phase3_dag_events": p3.get("dag_events_count", 0),
        "validators": p3.get("validators", []),
        "router_selections": d.get("router", {}).get("selections_phase3", 0),
    }


@mcp.tool()
def send_energy(kwh: float, worker_id: str = "mcp_claude") -> dict:
    """
    Envoie un batch d'énergie au Cortex V3.
    Args:
        kwh: Quantité en kWh à sceller (≥10 pour activer Phase 3)
        worker_id: Identifiant du worker source
    """
    res = _post(f"{CORTEX_URL}/api/energon/collect", {
        "worker_id": worker_id,
        "egn_generated": kwh,
        "status": "mcp_injection"
    })
    if not res["ok"]:
        return {"error": res["error"], "sent": False}
    return {"sent": True, "kwh": kwh, "worker_id": worker_id, **res["data"]}


@mcp.tool()
def bmad_systems() -> list:
    """
    Retourne les 20 systèmes BMAD Alexandria (ports 5000-5019).
    Source: dashboard API port 5001 + bmad-alexandria-methods.csv
    """
    res = _get(f"{DASHBOARD_URL}/api/bmad")
    if not res["ok"]:
        # Fallback: lire directement le CSV
        csv_path = ADAM_ROOT / "CLAUDE" / "bmad-alexandria-methods.csv"
        if csv_path.exists():
            import csv
            with open(csv_path) as f:
                return list(csv.DictReader(f))
        return [{"error": res["error"]}]
    return res["data"]


@mcp.tool()
def energon_ledger() -> dict:
    """
    Lit le ledger Energon local.
    Retourne: total kWh scellés, nombre de batches, timestamp dernier batch.
    """
    if not LEDGER_PATH.exists():
        return {"error": "Ledger file not found", "path": str(LEDGER_PATH)}
    data = json.loads(LEDGER_PATH.read_text())
    batches = data.get("batches", [])
    last_batch = batches[-1] if batches else None
    return {
        "sealed_kwh": data.get("sealed_kwh", 0),
        "total_batches": len(batches),
        "last_batch_time": last_batch.get("timestamp") if last_batch else None,
        "last_batch_kwh": last_batch.get("kwh") if last_batch else None,
        "version": data.get("version"),
    }


@mcp.tool()
def services_health() -> dict:
    """
    Vérifie la santé de tous les services du stack Alexandria.
    Retourne le statut de: Cortex V3, Dashboard, guacd, tomcat, nginx.
    """
    import socket

    def port_alive(port: int) -> bool:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            return False

    cortex = _get(f"{CORTEX_URL}/health")
    dashboard = _get(f"{DASHBOARD_URL}/api/health")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cortex_v3":   {"alive": cortex["ok"],    "port": 3003},
        "dashboard":   {"alive": dashboard["ok"], "port": 5001},
        "redis":       {"alive": port_alive(6379), "port": 6379},
        "guacd":       {"alive": port_alive(4822), "port": 4822},
        "tomcat":      {"alive": port_alive(8088), "port": 8088},
        "nginx":       {"alive": port_alive(443),  "port": 443},
        "zangetsu":    {"alive": port_alive(3042), "port": 3042},
    }


@mcp.tool()
def hands_status() -> dict:
    """
    Lit le fichier de statut du Cortex Hands (exécuteur autonome).
    Retourne: cycle courant, services vivants/morts, phase active.
    """
    if not HANDS_STATUS.exists():
        return {"error": "Status file not found — cortex-hands not running?"}
    return json.loads(HANDS_STATUS.read_text())


@mcp.tool()
def inject_command(cmd: str, timeout: int = 15) -> dict:
    """
    Exécute une commande shell via CortexInjector (bypass D-Bus, direct subprocess).
    Args:
        cmd: Commande shell à exécuter
        timeout: Timeout en secondes (max 60)
    Returns: stdout, stderr, returncode, elapsed_ms
    """
    if timeout > 60:
        timeout = 60
    result = injector.inject_command(cmd, timeout=timeout)
    return {
        "cmd": cmd,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "returncode": result.get("returncode", -1),
        "elapsed_ms": round(result.get("elapsed", 0) * 1000),
    }


# ─── Entry Point ───

if __name__ == "__main__":
    mcp.run(transport="stdio")
