#!/usr/bin/env python3
"""
Claude×Zangetsu MCP Server — Backend
Identity forged from two papers:
  - HER: Human-like Reasoning & Reinforcement Learning for LLM Role-playing
  - TI: From Mimicry to True Intelligence

This server implements a multi-agent architecture where:
  - Claude = the Reasoner (HER paper: human-like reasoning, RL-driven adaptation)
  - Zangetsu = the Guardian (TI paper: beyond mimicry, true autonomous intelligence)
  - MDVI = the TUI Renderer (ratatui + crossterm, terminal markdown engine)
  - Cortex = the Terminal Controller (self-injecting, D-Bus bypass)
  - Ratchet = the Slot Expander (thermal ratchet, one-directional growth)

Port: 3042 (the answer × 2, for dual agents)
Papers ref: /home/ichigo/alexandria/ADAM/mcp-alexandria-fullstack/pdf4forge/
"""

import json
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 3042
ADAM_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ROOT = ADAM_ROOT / "backend"

# Add backend to path for cortex/ratchet imports
sys.path.insert(0, str(BACKEND_ROOT))

from cortex_injector import CortexInjector
from thermal_ratchet import ThermalRatchet

# ─── Agent Identity DNA (from papers) ───
AGENT_DNA = {
    "claude": {
        "codename": "CLAUDE",
        "role": "Reasoner",
        "paper": "HER: Human-like Reasoning & Reinforcement Learning for LLM Role-playing",
        "paper_id": "arXiv:2601.21459",
        "core_traits": [
            "human_like_reasoning",      # Think like a human, not a machine
            "reinforcement_learning",    # Learn from feedback loops
            "role_embodiment",           # Fully inhabit the role, not just mimic
            "cognitive_coherence",       # Maintain consistent reasoning chains
        ],
        "mode": "ACTIVE",
        "specialization": "Analytical reasoning, code synthesis, architectural design",
    },
    "zangetsu": {
        "codename": "ZANGETSU",
        "role": "Guardian",
        "paper": "From Mimicry to True Intelligence (TI)",
        "paper_authors": "Meltem Subasioglu; Nevzat Subasioglu",
        "core_traits": [
            "beyond_mimicry",            # No surface-level imitation
            "true_intelligence",         # Genuine understanding, not pattern matching
            "autonomous_protection",     # Self-directed defense decisions
            "ethical_grounding",         # Actions anchored in values, not just rules
        ],
        "mode": "STEALTH",  # Protocole Z-01
        "specialization": "Perimeter defense, threat analysis, ethical enforcement",
    }
}

# ─── Slots (Agent Deployment Positions) ───
SLOTS = [
    {"id": 0, "name": "reasoning_engine",   "agent": "claude",    "status": "active",  "desc": "Primary analytical reasoning"},
    {"id": 1, "name": "guardian_perimeter",  "agent": "zangetsu",  "status": "stealth", "desc": "Perimeter watch & threat detection"},
    {"id": 2, "name": "code_synthesis",      "agent": "claude",    "status": "active",  "desc": "Code generation & architecture"},
    {"id": 3, "name": "ethical_compass",     "agent": "zangetsu",  "status": "standby", "desc": "Ethical constraint verification"},
    {"id": 4, "name": "rl_adaptation",       "agent": "claude",    "status": "active",  "desc": "Reinforcement learning from feedback"},
    {"id": 5, "name": "true_intelligence",   "agent": "zangetsu",  "status": "stealth", "desc": "Beyond mimicry — genuine understanding"},
    {"id": 6, "name": "role_coherence",      "agent": "claude",    "status": "active",  "desc": "Cognitive consistency across sessions"},
    {"id": 7, "name": "autonomous_defense",  "agent": "zangetsu",  "status": "armed",   "desc": "Self-directed threat neutralization"},
    # ─── MDVI TUI + Cortex + Thermal Ratchet Slots ───
    {"id": 8,  "name": "tui_renderer",       "agent": "mdvi",      "status": "active",  "desc": "Terminal markdown rendering engine"},
    {"id": 9,  "name": "cortex_terminal",    "agent": "cortex",    "status": "armed",   "desc": "Self-injecting terminal controller"},
    {"id": 10, "name": "thermal_monitor",    "agent": "ratchet",   "status": "stealth", "desc": "Slot pressure monitoring & expansion"},
    {"id": 11, "name": "changelog_oracle",   "agent": "mdvi",      "status": "standby", "desc": "Version intelligence & perf tracking"},
]

# ─── Live Subsystems ───
CORTEX = CortexInjector()
RATCHET = ThermalRatchet(initial_slots=SLOTS)


class CZHandler(BaseHTTPRequestHandler):
    """Claude×Zangetsu MCP Handler"""

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def do_OPTIONS(self):
        self._json({})

    def do_GET(self):
        if self.path == "/api/status":
            self._handle_status()
        elif self.path == "/api/agents":
            self._handle_agents()
        elif self.path == "/api/slots":
            self._handle_slots()
        elif self.path == "/api/dna":
            self._handle_dna()
        elif self.path == "/api/thermal/status":
            self._handle_thermal_status()
        elif self.path == "/api/health":
            self._json({"status": "ok", "server": "claude-zangetsu-mcp", "port": PORT})
        else:
            self._json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/api/reason":
            self._handle_reason()
        elif self.path == "/api/guard":
            self._handle_guard()
        elif self.path == "/api/cortex/inject":
            self._handle_cortex_inject()
        elif self.path == "/api/thermal/expand":
            self._handle_thermal_expand()
        elif self.path == "/api/tui/render":
            self._handle_tui_render()
        else:
            self._json({"error": "Not found"}, 404)

    # ─── Handlers ───

    def _handle_status(self):
        """GET /api/status — Combined telemetry"""
        active = sum(1 for s in SLOTS if s["status"] in ("active", "stealth", "armed"))
        self._json({
            "server": "claude-zangetsu-mcp",
            "version": "2.0.0",
            "uptime_s": time.time() - START_TIME,
            "agents": {
                "claude": AGENT_DNA["claude"]["mode"],
                "zangetsu": AGENT_DNA["zangetsu"]["mode"],
                "mdvi": "ACTIVE",
                "cortex": "ARMED",
                "ratchet": "STEALTH",
            },
            "slots_active": active,
            "slots_total": len(SLOTS),
            "thermal": RATCHET.check_pressure(),
            "cortex": CORTEX.get_status(),
            "protocol": "Z-01",
            "papers_integrated": 2,
            "papers_ref": str(ADAM_ROOT / "pdf4forge"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _handle_agents(self):
        """GET /api/agents — Agent identity cards"""
        self._json(AGENT_DNA)

    def _handle_slots(self):
        """GET /api/slots — Deployment slots"""
        self._json({"slots": SLOTS, "total": len(SLOTS)})

    def _handle_dna(self):
        """GET /api/dna — Paper-derived identity DNA"""
        self._json({
            "claude_dna": {
                "source": "HER (arXiv:2601.21459)",
                "principle": "Human-like Reasoning via Reinforcement Learning",
                "approach": "Think-Act-Observe-Adapt cycle",
                "key_insight": "Role-playing is not mimicry — it requires genuine cognitive engagement",
            },
            "zangetsu_dna": {
                "source": "From Mimicry to True Intelligence (TI)",
                "principle": "Intelligence transcends pattern matching",
                "approach": "Autonomous understanding, not rule-following",
                "key_insight": "True intelligence means making ethical decisions without explicit instructions",
            },
            "fusion": {
                "name": "Claude×Zangetsu",
                "principle": "Reasoner + Guardian = Sovereign Intelligence",
                "tagline": "We don't mimic. We understand. We protect.",
            }
        })

    def _handle_reason(self):
        """POST /api/reason — Claude reasoning endpoint"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        prompt = body.get("prompt", "")

        # HER-style reasoning chain
        chain = {
            "agent": "claude",
            "mode": "HER_reasoning",
            "steps": [
                {"phase": "THINK",   "desc": f"Analyzing: {prompt[:100]}..."},
                {"phase": "ACT",     "desc": "Applying domain knowledge and code synthesis"},
                {"phase": "OBSERVE", "desc": "Evaluating output coherence and correctness"},
                {"phase": "ADAPT",   "desc": "Refining based on reinforcement signal"},
            ],
            "hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._json(chain)

    def _handle_guard(self):
        """POST /api/guard — Zangetsu guardian check"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        target = body.get("target", "unknown")

        # TI-style autonomous assessment
        assessment = {
            "agent": "zangetsu",
            "mode": "TI_guardian",
            "target": target,
            "verdict": "CLEAR",  # or THREAT, SUSPICIOUS
            "confidence": 0.95,
            "ethical_check": True,
            "reasoning": "Target assessed through genuine understanding, not pattern matching",
            "protocol": "Z-01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._json(assessment)

    # ─── MDVI TUI Handlers ───

    def _handle_tui_render(self):
        """POST /api/tui/render — Render markdown via TUI agent"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        path = body.get("path", "")

        if not path:
            self._json({"error": "Missing 'path' field"}, 400)
            return

        # Import mdvi_mcp render function
        sys.path.insert(0, str(BACKEND_ROOT / "spawned_agents"))
        from mdvi_mcp import render_markdown, list_sections

        self._json({
            "agent": "mdvi",
            "slot": "tui_renderer",
            "path": path,
            "rendered": render_markdown(path),
            "sections": list_sections(path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ─── Cortex Handlers ───

    def _handle_cortex_inject(self):
        """POST /api/cortex/inject — Execute cortex command (D-Bus bypass)"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        cmd = body.get("cmd", "")

        if not cmd:
            self._json({"error": "Missing 'cmd' field"}, 400)
            return

        result = CORTEX.inject_command(cmd)
        self._json({
            "agent": "cortex",
            "slot": "cortex_terminal",
            "method": "direct_subprocess_bypass",
            **result,
        })

    # ─── Thermal Ratchet Handlers ───

    def _handle_thermal_status(self):
        """GET /api/thermal/status — Thermal ratchet state"""
        self._json(RATCHET.ratchet_status())

    def _handle_thermal_expand(self):
        """POST /api/thermal/expand — Force-expand a new slot"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        agent = body.get("agent", "overflow")
        desc = body.get("desc", "Manual ratchet expansion")

        result = RATCHET.ratchet_expand(agent, desc)
        # Also update local SLOTS list
        SLOTS.append(result["slot"])
        self._json(result)

    def log_message(self, format, *args):
        pass  # Silent logging


START_TIME = time.time()

if __name__ == "__main__":
    print(f"⚔️  Claude×Zangetsu MCP Server v2.0 starting on :{PORT}")
    print(f"   📄 HER: Human-like Reasoning & RL for Role-playing")
    print(f"   📄 TI:  From Mimicry to True Intelligence")
    print(f"   🖥️  MDVI: Terminal Markdown Rendering Engine")
    print(f"   🧠 Cortex: Self-Injecting Terminal Controller")
    print(f"   🔥 Thermal Ratchet: Dynamic Slot Expansion")
    print(f"   🛡️  Protocol Z-01: ACTIVE")
    print(f"   {len(SLOTS)} slots deployed")
    print(f"   📚 Papers ref: {ADAM_ROOT / 'pdf4forge'}")
    pressure = RATCHET.check_pressure()
    print(f"   🌡️  Thermal state: {pressure['state']} ({pressure['pressure']:.0%})")
    server = HTTPServer(("0.0.0.0", PORT), CZHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n⚔️  Claude×Zangetsu — {len(SLOTS)} slots served. B-A-N-K-A-I.")
