"""
emoji_registry.py — Alexandria Emoji Dispatch Registry
=======================================================
Maps emojis → SESHAT nodes → action types.
Persisted in TiDB via graph_store (same interface).

Action types:
  agent2web     → spawn web-facing agent
  agent2cli     → spawn CLI agent
  agent2agents  → spawn agent that orchestrates other agents
  agent2tui     → spawn TUI agent (mdvi-style)
  mcp2cli       → expose MCP server as CLI commands
  mcp2agents    → MCP server feeding an agent swarm
  paper2agent   → spawn agent from a PDF/paper
  paper2mcp     → spawn MCP server from a PDF/paper
  node2window   → open SESHAT node as UI window
  node2slack    → post node state to Slack channel
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional

REGISTRY_PATH = Path(__file__).parent / "emoji_registry.json"


@dataclass
class EmojiMapping:
    emoji: str
    node_id: str           # SESHAT node ID
    label: str             # Human-readable label
    action_type: str       # agent2web | agent2cli | agent2tui | mcp2cli | paper2agent | node2window | ...
    target: str            # path, URL, port, slack channel, etc.
    description: str = ""
    active: bool = True
    created_at: float = field(default_factory=time.time)
    meta: dict = field(default_factory=dict)


# ── DEFAULT REGISTRY (seed) ─────────────────────────────────────────────────

DEFAULT_MAPPINGS = [
    # ─ Core Alexandria ─
    EmojiMapping("⬡",  "root",          "Alexandria Core",     "node2window",   "root",              "Open Alexandria Core window"),
    EmojiMapping("📜", "f-mem",          "Memory/",            "node2window",   "f-mem",             "Open Memory folder"),
    EmojiMapping("🧬", "a-adam",         "ADAM",               "agent2agents",  "port:5000",         "ADAM Core orchestrator"),
    EmojiMapping("⚔️", "a-zangetsu",     "Zangetsu",           "agent2cli",     "port:3042",         "Zangetsu threat scanner"),
    EmojiMapping("🌸", "m-stigmergy",    "Stigmergy Map",      "node2window",   "m-stigmergy",       "Open stigmergy map"),
    EmojiMapping("🔥", "swarm-hub",      "Swarm Gen15",        "agent2agents",  "agents_exponential","Swarm dispatch hub"),

    # ─ Projects ─
    EmojiMapping("⚡", "p-mcp",          "MCP Servers",        "mcp2agents",    "port:8000",         "MCP fullstack dispatcher"),
    EmojiMapping("🔬", "p-rag",          "RAG Engine",         "mcp2cli",       "rag_engine.py",     "BMAD RAG via CLI"),
    EmojiMapping("🏗️", "p-forge",        "Sovereign Forge",   "agent2web",     "port:3000",         "Sovereign Forge UI"),
    EmojiMapping("🧛", "nosferatu",       "Nosferatu NFT",     "agent2web",     "nosferatu-nexus-pwa","Nosferatu PWA"),

    # ─ Infrastructure ─
    EmojiMapping("🌐", "a-aker",         "AKER Gateway",       "agent2cli",     "port:6G",           "AI-RAN 6G gateway"),
    EmojiMapping("♻️", "a-kheper",       "KHEPER:Nexus",       "agent2agents",  "kheper",            "Resource redistributor"),
    EmojiMapping("🕸️", "a-serena",       "SERENA",            "agent2tui",     "serena_tui",        "9-vector IMUX interface"),
    EmojiMapping("💙", "blue-core",       "BLUE",              "agent2agents",  "blue-daemon.py",    "Soul of Alexandria"),

    # ─ Channels Slack ─
    EmojiMapping("👤", "slack-human",    "Slack Human",        "node2slack",    "#alexandria-humans","Human channel"),
    EmojiMapping("🤖", "slack-llm",      "Slack LLM",         "node2slack",    "#alexandria-llm",   "LLM channel"),
    EmojiMapping("🔗", "slack-bridge",   "Slack Bridge",       "node2slack",    "#alexandria-bridge","Human-LLM channel"),

    # ─ Paper2Agent shortcuts ─
    EmojiMapping("📄", "paper-spawn",    "Paper→Agent",        "paper2agent",   "pdf/",              "Spawn agent from paper"),
    EmojiMapping("🖥️", "paper-mcp",     "Paper→MCP",          "paper2mcp",     "pdf/",              "Spawn MCP from paper"),

    # ─ GhostDesk sections ─
    EmojiMapping("👁️", "ghostdesk-main", "GhostDesk Main",    "node2window",   "ghostdesk:main",    "Main GhostDesk view"),
    EmojiMapping("📊", "floatilla",      "Floatilla",          "node2window",   "port:5006",         "Floatilla observatory"),
    EmojiMapping("🌡️", "thermal",        "Thermal Ratchet",   "agent2tui",     "thermal_ratchet.py","Thermal slot monitor"),
]


class EmojiRegistry:
    def __init__(self):
        self._map: dict[str, EmojiMapping] = {}
        self._load()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def register(self, mapping: EmojiMapping) -> EmojiMapping:
        self._map[mapping.emoji] = mapping
        self._save()
        return mapping

    def get(self, emoji: str) -> Optional[EmojiMapping]:
        return self._map.get(emoji)

    def get_by_node(self, node_id: str) -> list[EmojiMapping]:
        return [m for m in self._map.values() if m.node_id == node_id]

    def get_by_action(self, action_type: str) -> list[EmojiMapping]:
        return [m for m in self._map.values() if m.action_type == action_type]

    def all(self) -> list[EmojiMapping]:
        return list(self._map.values())

    def remove(self, emoji: str) -> bool:
        if emoji in self._map:
            del self._map[emoji]
            self._save()
            return True
        return False

    def to_llm_txt(self) -> str:
        """Generate LLM-readable emoji map for system prompt injection."""
        lines = ["## EMOJI DISPATCH MAP", ""]
        by_type: dict[str, list] = {}
        for m in sorted(self._map.values(), key=lambda x: x.action_type):
            by_type.setdefault(m.action_type, []).append(m)

        for atype, mappings in sorted(by_type.items()):
            lines.append(f"### {atype.upper()}")
            for m in mappings:
                lines.append(f"  {m.emoji}  →  [{m.node_id}] {m.label} · {m.target}")
                if m.description:
                    lines.append(f"       {m.description}")
            lines.append("")
        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self):
        data = {e: asdict(m) for e, m in self._map.items()}
        REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _load(self):
        if REGISTRY_PATH.exists():
            try:
                data = json.loads(REGISTRY_PATH.read_text())
                for e, d in data.items():
                    self._map[e] = EmojiMapping(**d)
                return
            except Exception as ex:
                print(f"[emoji_registry] Load error: {ex} — seeding defaults")
        self._seed()

    def _seed(self):
        for m in DEFAULT_MAPPINGS:
            self._map[m.emoji] = m
        self._save()
        print(f"[emoji_registry] Seeded {len(self._map)} mappings")


# Singleton
_registry = None
def get_registry() -> EmojiRegistry:
    global _registry
    if _registry is None:
        _registry = EmojiRegistry()
    return _registry
