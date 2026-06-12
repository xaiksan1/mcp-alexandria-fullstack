"""
trunk_dispatcher.py — Alexandria Trunk Dispatcher
==================================================
Resolves emoji → EmojiMapping → spawns the right agent/MCP/window.
Drop this in mcp-alexandria-fullstack/backend/ — it sits on top of
paper_spawner.py, cortex_injector.py, and thermal_ratchet.py.

Expose as FastMCP tool or call directly.

Action routing table:
  agent2web     → cortex.inject_command("browser open {target}")
  agent2cli     → cortex.inject_command("python3 {target}")
  agent2agents  → paper_spawner.spawn_slot_agent()
  agent2tui     → cortex.spawn_tui_terminal(label, target)
  mcp2cli       → cortex.inject_command("python3 {target} --stdio")
  mcp2agents    → paper_spawner.spawn_mcp_server()
  paper2agent   → paper_spawner.parse_markdown() + spawn_slot_agent()
  paper2mcp     → paper_spawner.parse_markdown() + spawn_mcp_server()
  node2window   → post to SESHAT WebSocket (opens window in UI)
  node2slack    → post to Slack channel via webhook
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Path setup ──────────────────────────────────────────────────────────────
BACKEND = Path(__file__).resolve().parent
FULLSTACK = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from emoji_registry import get_registry, EmojiMapping

try:
    from cortex_injector import CortexInjector
    CORTEX = CortexInjector()
except ImportError:
    CORTEX = None
    print("[trunk] cortex_injector not available — CLI actions will be mocked")

try:
    from paper_spawner import PaperSpawner
    SPAWNER = PaperSpawner()
except ImportError:
    SPAWNER = None
    print("[trunk] paper_spawner not available — paper actions will be mocked")

try:
    from fastmcp import FastMCP
    mcp = FastMCP(
        "alexandria-trunk",
        instructions=(
            "Alexandria Trunk Dispatcher. "
            "Resolves emojis to actions in the Alexandria ecosystem. "
            "Use dispatch_emoji() to trigger any registered action. "
            "Use list_emojis() to see all available triggers."
        )
    )
    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False


# ── Dispatch Engine ──────────────────────────────────────────────────────────

class TrunkDispatcher:
    def __init__(self):
        self.registry = get_registry()
        self._dispatch_log: list[dict] = []

    def dispatch(self, emoji: str, args: dict = None) -> dict:
        """
        Main dispatch entry point. Resolves emoji → action → execute.
        Returns a result dict with status, action_type, and output.
        """
        args = args or {}
        mapping = self.registry.get(emoji)

        if not mapping:
            return self._result("NOT_FOUND", emoji, f"No mapping for emoji '{emoji}'")

        if not mapping.active:
            return self._result("INACTIVE", emoji, f"Mapping '{mapping.label}' is disabled")

        ts = datetime.now(timezone.utc).isoformat()
        print(f"[trunk] {ts} {emoji} → {mapping.action_type}:{mapping.target} [{mapping.label}]")

        result = self._route(mapping, args)
        entry = {
            "emoji": emoji,
            "label": mapping.label,
            "action_type": mapping.action_type,
            "target": mapping.target,
            "result": result,
            "timestamp": ts,
        }
        self._dispatch_log.append(entry)
        return entry

    def _route(self, m: EmojiMapping, args: dict) -> dict:
        at = m.action_type

        if at == "agent2web":
            return self._agent2web(m, args)
        elif at == "agent2cli":
            return self._agent2cli(m, args)
        elif at == "agent2agents":
            return self._agent2agents(m, args)
        elif at == "agent2tui":
            return self._agent2tui(m, args)
        elif at == "mcp2cli":
            return self._mcp2cli(m, args)
        elif at == "mcp2agents":
            return self._mcp2agents(m, args)
        elif at == "paper2agent":
            return self._paper2agent(m, args)
        elif at == "paper2mcp":
            return self._paper2mcp(m, args)
        elif at == "node2window":
            return self._node2window(m, args)
        elif at == "node2slack":
            return self._node2slack(m, args)
        else:
            return {"status": "UNKNOWN_ACTION", "action_type": at}

    # ── Action Handlers ──────────────────────────────────────────────────────

    def _agent2web(self, m: EmojiMapping, args: dict) -> dict:
        """Open a web-facing agent — chromium or curl."""
        target = args.get("url", m.target)
        if target.startswith("port:"):
            port = target.split(":")[1]
            url = f"http://localhost:{port}"
        else:
            url = target
        if CORTEX:
            result = CORTEX.inject_command(f"chromium --app={url} &")
            return {"status": "LAUNCHED", "url": url, **result}
        return {"status": "MOCKED", "url": url}

    def _agent2cli(self, m: EmojiMapping, args: dict) -> dict:
        """Spawn a CLI agent process."""
        cmd = args.get("cmd", f"python3 {m.target}")
        if CORTEX:
            result = CORTEX.inject_command(cmd, timeout=30)
            return {"status": "EXECUTED", "cmd": cmd, **result}
        return {"status": "MOCKED", "cmd": cmd}

    def _agent2agents(self, m: EmojiMapping, args: dict) -> dict:
        """Spawn an agent that orchestrates other agents (slot-based)."""
        if SPAWNER and args.get("source_md"):
            data = SPAWNER.parse_markdown(args["source_md"])
            slot = SPAWNER.spawn_slot_agent(data)
            return {"status": "SPAWNED", "slot": slot}
        target = m.target
        if CORTEX and target.startswith("port:"):
            port = target.split(":")[1]
            result = CORTEX.inject_command(f"curl -s http://localhost:{port}/api/status")
            return {"status": "QUERIED", "port": port, **result}
        return {"status": "ROUTED", "target": target, "node_id": m.node_id}

    def _agent2tui(self, m: EmojiMapping, args: dict) -> dict:
        """Spawn a TUI agent in a new terminal."""
        name = args.get("name", m.label.replace(" ", "_"))
        cmd = args.get("cmd", f"python3 {m.target}")
        if CORTEX:
            result = CORTEX.spawn_tui_terminal(name, cmd)
            return {"status": "TUI_SPAWNED", "name": name, **result}
        return {"status": "MOCKED_TUI", "name": name, "cmd": cmd}

    def _mcp2cli(self, m: EmojiMapping, args: dict) -> dict:
        """Expose MCP server as CLI — run in stdio mode."""
        cmd = args.get("cmd", f"python3 {m.target} --stdio")
        if CORTEX:
            result = CORTEX.inject_command(cmd)
            return {"status": "MCP_CLI", "cmd": cmd, **result}
        return {"status": "MOCKED", "cmd": cmd}

    def _mcp2agents(self, m: EmojiMapping, args: dict) -> dict:
        """Spawn MCP server feeding an agent swarm."""
        if SPAWNER and args.get("source_md"):
            data = SPAWNER.parse_markdown(args["source_md"])
            script = SPAWNER.spawn_mcp_server(data)
            if CORTEX:
                CORTEX.spawn_tui_terminal(m.label, f"python3 {script}")
            return {"status": "MCP_SPAWNED", "script": script}
        return {"status": "ROUTED", "target": m.target}

    def _paper2agent(self, m: EmojiMapping, args: dict) -> dict:
        """Spawn agent from a PDF/markdown paper."""
        source = args.get("source", m.target)
        if SPAWNER and Path(source).exists():
            data = SPAWNER.parse_markdown(source)
            slot = SPAWNER.spawn_slot_agent(data)
            return {"status": "PAPER_AGENT_SPAWNED", "name": data["name"], "slot": slot}
        return {"status": "NEEDS_SOURCE", "hint": "Pass 'source' in args pointing to the paper file"}

    def _paper2mcp(self, m: EmojiMapping, args: dict) -> dict:
        """Spawn MCP server from a PDF/markdown paper."""
        source = args.get("source", m.target)
        if SPAWNER and Path(source).exists():
            data = SPAWNER.parse_markdown(source)
            script = SPAWNER.spawn_mcp_server(data)
            return {"status": "PAPER_MCP_SPAWNED", "name": data["name"], "script": script}
        return {"status": "NEEDS_SOURCE", "hint": "Pass 'source' in args pointing to the paper file"}

    def _node2window(self, m: EmojiMapping, args: dict) -> dict:
        """Open SESHAT node as UI window (posts to WebSocket if available)."""
        # The SESHAT HTML UI listens for this via Slack or direct WebSocket
        node_id = args.get("node_id", m.node_id)
        payload = json.dumps({"action": "open_window", "node_id": node_id})
        # Try WebSocket endpoint if available
        if CORTEX:
            result = CORTEX.inject_command(
                f"curl -s -X POST http://localhost:8000/api/window/open "
                f"-H 'Content-Type: application/json' -d '{payload}'"
            )
            return {"status": "WINDOW_REQUESTED", "node_id": node_id, **result}
        return {"status": "WINDOW_SIGNAL", "node_id": node_id, "payload": payload}

    def _node2slack(self, m: EmojiMapping, args: dict) -> dict:
        """Post node state to Slack channel."""
        channel = m.target  # e.g. "#alexandria-llm"
        text = args.get("text", f"{m.emoji} [{m.node_id}] {m.label} triggered")
        # Uses Slack webhook or API — cortex injects the curl
        webhook = m.meta.get("webhook_url", "")
        if webhook and CORTEX:
            payload = json.dumps({"channel": channel, "text": text})
            result = CORTEX.inject_command(
                f"curl -s -X POST '{webhook}' "
                f"-H 'Content-Type: application/json' -d '{payload}'"
            )
            return {"status": "SLACK_POSTED", "channel": channel, **result}
        return {"status": "SLACK_PENDING", "channel": channel,
                "hint": "Add webhook_url to mapping meta"}

    # ── Utilities ────────────────────────────────────────────────────────────

    def list_mappings(self, action_type: str = None) -> list[dict]:
        mappings = self.registry.all()
        if action_type:
            mappings = [m for m in mappings if m.action_type == action_type]
        return [
            {"emoji": m.emoji, "label": m.label, "action_type": m.action_type,
             "target": m.target, "node_id": m.node_id, "active": m.active}
            for m in sorted(mappings, key=lambda x: x.action_type)
        ]

    def register(self, emoji: str, node_id: str, label: str,
                 action_type: str, target: str, description: str = "") -> dict:
        from emoji_registry import EmojiMapping
        m = EmojiMapping(emoji=emoji, node_id=node_id, label=label,
                         action_type=action_type, target=target,
                         description=description)
        self.registry.register(m)
        return {"status": "REGISTERED", "emoji": emoji, "label": label}

    def dispatch_log(self, last_n: int = 10) -> list:
        return self._dispatch_log[-last_n:]

    def _result(self, status: str, emoji: str, message: str) -> dict:
        return {"status": status, "emoji": emoji, "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Singleton ────────────────────────────────────────────────────────────────
_dispatcher = None
def get_dispatcher() -> TrunkDispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = TrunkDispatcher()
    return _dispatcher


# ── FastMCP Tools ────────────────────────────────────────────────────────────
if _HAS_MCP:
    D = get_dispatcher()

    @mcp.tool()
    def dispatch_emoji(emoji: str, args_json: str = "{}") -> dict:
        """
        Dispatch an emoji trigger in the Alexandria ecosystem.
        emoji: the emoji character (e.g. '⬡', '🧬', '⚔️')
        args_json: optional JSON string with extra args (e.g. '{"source": "/path/to/paper.md"}')
        """
        try:
            args = json.loads(args_json)
        except Exception:
            args = {}
        return D.dispatch(emoji, args)

    @mcp.tool()
    def list_emojis(action_type: str = "") -> list:
        """
        List all registered emoji mappings.
        action_type: optional filter (agent2web|agent2cli|paper2agent|node2window|...)
        """
        return D.list_mappings(action_type or None)

    @mcp.tool()
    def register_emoji(emoji: str, node_id: str, label: str,
                       action_type: str, target: str, description: str = "") -> dict:
        """
        Register a new emoji mapping.
        action_type: agent2web|agent2cli|agent2agents|agent2tui|
                     mcp2cli|mcp2agents|paper2agent|paper2mcp|
                     node2window|node2slack
        """
        return D.register(emoji, node_id, label, action_type, target, description)

    @mcp.tool()
    def emoji_llm_context() -> str:
        """
        Returns the full emoji dispatch map as LLM.txt context.
        Inject this into any agent's system prompt so it knows how to trigger actions.
        """
        return get_dispatcher().registry.to_llm_txt()

    @mcp.tool()
    def dispatch_log(last_n: int = 10) -> list:
        """Returns the last N dispatch events."""
        return D.dispatch_log(last_n)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        if _HAS_MCP:
            mcp.run()
        else:
            print("[trunk] FastMCP not installed")
    elif len(sys.argv) > 1:
        # Direct emoji dispatch from terminal
        emoji = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = get_dispatcher().dispatch(emoji, args)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        # List all mappings
        print(get_dispatcher().registry.to_llm_txt())
