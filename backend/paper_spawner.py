import os
import json
import sys
import re
from typing import Dict, Any

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
        
        new_agent = {
            "id": f"paper-slot-{len(data['name'])}",
            "name": data['name'],
            "type": "PAPER_BORN",
            "status": "SLOT_READY",
            "capabilities": data['capabilities'],
            "source": data['source']
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
        print("Usage: python3 paper_spawner.py <markdown_file> <mode: mcp|slot>")
        sys.exit(1)
    
    spawner = PaperSpawner()
    info = spawner.parse_markdown(sys.argv[1])
    
    if sys.argv[2] == "mcp":
        spawner.spawn_mcp_server(info)
    elif sys.argv[2] == "slot":
        spawner.spawn_slot_agent(info)
