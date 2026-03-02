#!/usr/bin/env python3
"""
Cortex Injector — The Terminal IS the Agent
Alexandria Anima Mundi — Defense Layer

The Cortex doesn't ask permission to use the terminal.
It BECOMES the terminal. Direct subprocess injection,
bypassing VmCicerone D-Bus delays entirely.

"We don't wait. We inject. We execute."
"""

import os
import sys
import subprocess
import signal
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List


class CortexInjector:
    """
    Self-injecting terminal controller.
    Spawns isolated TUI processes, executes commands,
    and tracks all active terminals.
    """

    def __init__(self):
        self._terminals: Dict[str, dict] = {}
        self._cmd_history: List[dict] = []
        self._boot_time = time.time()
        self.adam_root = Path(__file__).resolve().parent.parent

    # ─── Core Injection ───

    def inject_command(self, cmd: str, timeout: int = 30) -> dict:
        """
        Execute a shell command directly — no D-Bus, no VmCicerone delay.
        Returns stdout, stderr, return code, and execution time.
        """
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.adam_root),
            )
            elapsed = time.time() - start

            entry = {
                "cmd": cmd,
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-500:] if result.stderr else "",
                "returncode": result.returncode,
                "elapsed_ms": round(elapsed * 1000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": "direct_subprocess",  # NOT D-Bus
            }
            self._cmd_history.append(entry)
            return entry

        except subprocess.TimeoutExpired:
            return {"cmd": cmd, "error": "TIMEOUT", "timeout_s": timeout}
        except Exception as e:
            return {"cmd": cmd, "error": str(e)}

    # ─── TUI Terminal Spawning ───

    def spawn_tui_terminal(self, name: str, cmd: str) -> dict:
        """
        Launch an isolated terminal process for a TUI agent.
        Each TUI gets its own PID, its own stdout, its own life.
        """
        if name in self._terminals:
            info = self._terminals[name]
            # Check if still alive
            if info["process"].poll() is None:
                return {"name": name, "status": "ALREADY_RUNNING", "pid": info["pid"]}
            else:
                del self._terminals[name]

        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.adam_root),
                preexec_fn=os.setsid,  # New process group — isolated
            )

            entry = {
                "name": name,
                "cmd": cmd,
                "pid": proc.pid,
                "process": proc,
                "spawned_at": datetime.now(timezone.utc).isoformat(),
                "status": "RUNNING",
            }
            self._terminals[name] = entry
            return {k: v for k, v in entry.items() if k != "process"}

        except Exception as e:
            return {"name": name, "error": str(e)}

    def list_active_terminals(self) -> list:
        """List all spawned TUI terminals with their status."""
        result = []
        dead = []
        for name, info in self._terminals.items():
            alive = info["process"].poll() is None
            result.append({
                "name": name,
                "pid": info["pid"],
                "cmd": info["cmd"],
                "status": "RUNNING" if alive else "DEAD",
                "spawned_at": info["spawned_at"],
            })
            if not alive:
                dead.append(name)

        # Clean up dead terminals
        for name in dead:
            del self._terminals[name]

        return result

    def kill_terminal(self, name: str) -> dict:
        """Clean shutdown of a TUI terminal by name."""
        if name not in self._terminals:
            return {"name": name, "error": "NOT_FOUND"}

        info = self._terminals[name]
        try:
            os.killpg(os.getpgid(info["pid"]), signal.SIGTERM)
            info["process"].wait(timeout=5)
            del self._terminals[name]
            return {"name": name, "status": "TERMINATED", "pid": info["pid"]}
        except Exception as e:
            # Force kill
            try:
                os.killpg(os.getpgid(info["pid"]), signal.SIGKILL)
                del self._terminals[name]
                return {"name": name, "status": "FORCE_KILLED", "pid": info["pid"]}
            except:
                return {"name": name, "error": str(e)}

    # ─── Cortex Intelligence ───

    def inject_and_capture(self, cmd: str) -> str:
        """Quick injection — returns just the stdout for piping."""
        result = self.inject_command(cmd)
        return result.get("stdout", result.get("error", ""))

    def batch_inject(self, commands: List[str]) -> list:
        """Execute multiple commands sequentially, return all results."""
        return [self.inject_command(cmd) for cmd in commands]

    def get_status(self) -> dict:
        """Cortex status report."""
        return {
            "agent": "cortex_injector",
            "uptime_s": round(time.time() - self._boot_time, 2),
            "terminals_active": len([t for t in self._terminals.values()
                                     if t["process"].poll() is None]),
            "commands_executed": len(self._cmd_history),
            "method": "direct_subprocess_bypass",
            "dbus_dependency": False,  # We don't need VmCicerone
        }


# ─── CLI Mode ───
if __name__ == "__main__":
    cortex = CortexInjector()

    if len(sys.argv) < 2:
        print(json.dumps(cortex.get_status(), indent=2))
        sys.exit(0)

    cmd = " ".join(sys.argv[1:])
    result = cortex.inject_command(cmd)
    print(json.dumps(result, indent=2))
