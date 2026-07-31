#!/usr/bin/env python3
# Run via ADAM/.venv/bin/python3 (has eth-account for the real wallet
# derivation below) — plain system python3 does not have it and PEP 668
# blocks a global pip install on this host.
import hashlib
import os
import json
import sys
import re
from typing import Dict, Any

# Every agent is supposed to grab a Tim-Burner wallet the moment it's born, so
# it can pay for things via x402 (ADAM/dwallstreet/x402_handler.py). Larva-born
# (PAPER_BORN) agents are new in Alexandria v5.0, and this was simply never
# wired in yet for this birth path — confirmed by grep (2026-07-31), not a
# regression. derive_agent_wallet() is a REAL secp256k1 address (BIP44 HD
# derivation from one securely-held master mnemonic — see
# agentic-ads/payments/tim_burner.py) as of the same day: energon is a real,
# continuously-tested system, not a disposable prototype, so this doesn't get
# a placeholder while waiting for a "final" version that never actually ships.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentic-ads", "payments"))
from tim_burner import derive_agent_wallet  # noqa: E402

class PaperSpawner:
    def __init__(self):
        self.output_dir = "/home/ichigo/alexandria/ADAM/mcp-alexandria-fullstack/backend/spawned_agents"
        os.makedirs(self.output_dir, exist_ok=True)
        print("--- Paper Spawner 1.0 (Straight-Pipe) Initialized ---")

    def parse_markdown(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else os.path.basename(file_path)
        
        # Simple extraction of sections/capabilities
        sections = re.findall(r'^##?\s+(.+)$', content, re.MULTILINE)
        
        return {
            "name": title.strip(),
            "source": file_path,
            "capabilities": [s.strip() for s in sections],
            "raw_content": content[:2000] # Buffer for prompt context
        }

    def spawn_mcp_server(self, data: Dict[str, Any]):
        """Generates a Python FastMCP server script"""
        server_name = data['name'].lower().replace(" ", "_")
        script_path = os.path.join(self.output_dir, f"{server_name}_mcp.py")
        
        caps = ", ".join(data['capabilities'])
        script_content = f'''
from fastmcp import FastMCP
import os

# Server spawned from: {data['source']}
mcp = FastMCP("{data['name']}")

@mcp.tool()
def get_info() -> str:
    """Returns the core purpose of this spawned agent."""
    return "I am the {data['name']} agent. My capabilities include: {caps}"

@mcp.tool()
def analyze_context(query: str) -> str:
    """Simulated analysis based on the paper context."""
    return f"Analyzing '{{query}}' based on {data['name']} principles."

if __name__ == "__main__":
    mcp.run()
'''
        with open(script_path, 'w') as f:
            f.write(script_content)
        print(f"✅ [MCP MODE] Server generated: {script_path}")
        return script_path

    def spawn_slot_agent(self, data: Dict[str, Any]):
        """Registers the agent as a REAL slot in the HIVE/Blower system"""
        registry_path = "/home/ichigo/alexandria/ADAM/agent_registry_phase8.json"
        
        # Was `f"paper-slot-{len(data['name'])}"` — keyed by the NAME'S LENGTH,
        # so two different agents with same-length names collided on both the
        # slot id and (once wired) the wallet. Fixed 2026-07-31: keyed by a
        # hash of the actual name content instead, effectively collision-free.
        name_hash = hashlib.sha256(data['name'].encode()).hexdigest()[:12]
        agent_id = f"paper-slot-{name_hash}"
        new_agent = {
            "id": agent_id,
            "name": data['name'],
            "type": "PAPER_BORN",
            "status": "SLOT_READY",
            "capabilities": data['capabilities'],
            "source": data['source'],
            "wallet": derive_agent_wallet(data['name']),
        }
        
        # Update registry if it exists
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            registry[new_agent['id']] = new_agent
            with open(registry_path, 'w') as f:
                json.dump(registry, f, indent=2)
        
        print(f"🎰 [SLOT MODE] Agent bound to HIVE slot: {new_agent['id']}")
        return new_agent

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ADAM/.venv/bin/python3 paper_spawner.py <markdown_file> <mode: mcp|slot>")
        sys.exit(1)
    
    spawner = PaperSpawner()
    info = spawner.parse_markdown(sys.argv[1])
    
    if sys.argv[2] == "mcp":
        spawner.spawn_mcp_server(info)
    elif sys.argv[2] == "slot":
        spawner.spawn_slot_agent(info)
