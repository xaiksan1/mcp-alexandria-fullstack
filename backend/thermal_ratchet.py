#!/usr/bin/env python3
"""
Thermal Ratchet — Dynamic Slot Expansion Engine
Alexandria Anima Mundi — Physics-Inspired Architecture

Like a real thermal ratchet in thermodynamics:
  - Energy (load) flows in ONE direction
  - Slots ONLY expand, never contract
  - Each "click" locks in a new capability
  - Brownian motion (chaotic requests) is rectified into directed growth

"Pressure builds. Slots click. The system grows."
"""

import time
import json
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path


class ThermalRatchet:
    """
    One-directional slot expansion engine.
    Monitors pressure (active/total ratio) and spawns
    new slots when the system needs to grow.
    """

    # Pressure thresholds
    COOL = 0.5       # < 50% slots active → system is relaxed
    WARM = 0.7       # 50-70% → warming up
    HOT = 0.85       # 70-85% → heavy load
    CRITICAL = 0.95  # > 95% → must expand NOW

    def __init__(self, initial_slots: Optional[List[dict]] = None):
        self._boot_time = time.time()
        self._ratchet_count = 0  # Total expansions performed
        self._expansion_log: List[dict] = []

        # Import current slots or start empty
        if initial_slots:
            self._slots = list(initial_slots)
        else:
            self._slots = self._load_default_slots()

    def _load_default_slots(self) -> list:
        """Load the default Claude×Zangetsu + MDVI slot configuration."""
        return [
            {"id": 0, "name": "reasoning_engine",   "agent": "claude",    "status": "active",  "desc": "Primary analytical reasoning"},
            {"id": 1, "name": "guardian_perimeter",  "agent": "zangetsu",  "status": "stealth", "desc": "Perimeter watch & threat detection"},
            {"id": 2, "name": "code_synthesis",      "agent": "claude",    "status": "active",  "desc": "Code generation & architecture"},
            {"id": 3, "name": "ethical_compass",     "agent": "zangetsu",  "status": "standby", "desc": "Ethical constraint verification"},
            {"id": 4, "name": "rl_adaptation",       "agent": "claude",    "status": "active",  "desc": "Reinforcement learning from feedback"},
            {"id": 5, "name": "true_intelligence",   "agent": "zangetsu",  "status": "stealth", "desc": "Beyond mimicry — genuine understanding"},
            {"id": 6, "name": "role_coherence",      "agent": "claude",    "status": "active",  "desc": "Cognitive consistency across sessions"},
            {"id": 7, "name": "autonomous_defense",  "agent": "zangetsu",  "status": "armed",   "desc": "Self-directed threat neutralization"},
            {"id": 8, "name": "tui_renderer",        "agent": "mdvi",      "status": "active",  "desc": "Terminal markdown rendering engine"},
            {"id": 9, "name": "cortex_terminal",     "agent": "cortex",    "status": "armed",   "desc": "Self-injecting terminal controller"},
            {"id": 10, "name": "thermal_monitor",    "agent": "ratchet",   "status": "stealth", "desc": "Slot pressure monitoring & expansion"},
            {"id": 11, "name": "changelog_oracle",   "agent": "mdvi",      "status": "standby", "desc": "Version intelligence & perf tracking"},
        ]

    # ─── Pressure Monitoring ───

    def check_pressure(self) -> dict:
        """
        Calculate current slot pressure.
        Pressure = active_slots / total_slots
        """
        active_statuses = {"active", "stealth", "armed"}
        active = sum(1 for s in self._slots if s["status"] in active_statuses)
        total = len(self._slots)
        pressure = active / total if total > 0 else 0

        return {
            "active": active,
            "total": total,
            "pressure": round(pressure, 3),
            "state": self._pressure_to_state(pressure),
        }

    def _pressure_to_state(self, pressure: float) -> str:
        """Convert pressure ratio to thermal state."""
        if pressure >= self.CRITICAL:
            return "CRITICAL"
        elif pressure >= self.HOT:
            return "HOT"
        elif pressure >= self.WARM:
            return "WARM"
        else:
            return "COOL"

    def ratchet_status(self) -> dict:
        """Full thermal ratchet status report."""
        pressure = self.check_pressure()
        return {
            "agent": "thermal_ratchet",
            "uptime_s": round(time.time() - self._boot_time, 2),
            "total_slots": len(self._slots),
            "pressure": pressure,
            "total_expansions": self._ratchet_count,
            "physics": "one_directional",  # Slots only grow
            "expansion_log": self._expansion_log[-5:],  # Last 5 expansions
        }

    # ─── Ratchet Expansion ───

    def ratchet_expand(self, agent_name: str, desc: str, status: str = "active") -> dict:
        """
        Click! Spawn a new slot. One-directional — it never contracts.
        This is the fundamental thermal ratchet operation.
        """
        new_id = max(s["id"] for s in self._slots) + 1
        slot_name = f"{agent_name}_ratchet_{new_id}"

        new_slot = {
            "id": new_id,
            "name": slot_name,
            "agent": agent_name,
            "status": status,
            "desc": desc,
            "spawned_by": "thermal_ratchet",
            "spawned_at": datetime.now(timezone.utc).isoformat(),
        }

        self._slots.append(new_slot)
        self._ratchet_count += 1

        expansion = {
            "event": "RATCHET_CLICK",
            "slot": new_slot,
            "new_total": len(self._slots),
            "pressure_after": self.check_pressure(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._expansion_log.append(expansion)

        return expansion

    def auto_ratchet(self, agent_name: str = "overflow", desc: str = "Auto-expanded under pressure") -> Optional[dict]:
        """
        Automatic expansion — check pressure and expand if needed.
        Only fires at HOT or CRITICAL state.
        Returns the new slot if expanded, None if pressure is fine.
        """
        pressure = self.check_pressure()
        state = pressure["state"]

        if state in ("HOT", "CRITICAL"):
            return self.ratchet_expand(
                agent_name=agent_name,
                desc=f"{desc} [state={state}, pressure={pressure['pressure']}]",
                status="active" if state == "CRITICAL" else "standby",
            )

        return None

    # ─── Slot Management ───

    def get_slots(self) -> list:
        """Return all current slots."""
        return self._slots

    def get_slot(self, slot_id: int) -> Optional[dict]:
        """Get a specific slot by ID."""
        for s in self._slots:
            if s["id"] == slot_id:
                return s
        return None

    def update_slot_status(self, slot_id: int, status: str) -> dict:
        """Update a slot's status. Cannot delete — only change state."""
        for s in self._slots:
            if s["id"] == slot_id:
                old = s["status"]
                s["status"] = status
                return {"id": slot_id, "old_status": old, "new_status": status}
        return {"error": f"Slot {slot_id} not found"}


# ─── CLI Mode ───
if __name__ == "__main__":
    ratchet = ThermalRatchet()

    if len(sys.argv) < 2:
        print(json.dumps(ratchet.ratchet_status(), indent=2, default=str))
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "pressure":
        print(json.dumps(ratchet.check_pressure(), indent=2))
    elif cmd == "expand":
        name = sys.argv[2] if len(sys.argv) > 2 else "emergency"
        desc = sys.argv[3] if len(sys.argv) > 3 else "Manual ratchet expansion"
        print(json.dumps(ratchet.ratchet_expand(name, desc), indent=2, default=str))
    elif cmd == "auto":
        result = ratchet.auto_ratchet()
        if result:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("Pressure is fine — no expansion needed")
    elif cmd == "slots":
        print(json.dumps(ratchet.get_slots(), indent=2, default=str))
    else:
        print(f"Usage: python3 thermal_ratchet.py [pressure|expand|auto|slots]")
