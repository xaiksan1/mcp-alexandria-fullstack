#!/usr/bin/env python3
"""
MDVI Changelog MCP Server — Version Intelligence Oracle
Spawned from: mdvi/CHANGELOG.md

This agent tracks the evolution of the TUI system:
  v0.1.0 → v0.6.3, from basic Vim nav to a fully cached,
  lazy-loading, background-threaded rendering engine.

The changelog IS the DNA history of the agent.
"""

import re
from pathlib import Path
from typing import Optional

try:
    from fastmcp import FastMCP
    _HAS_FASTMCP = True
except ImportError:
    _HAS_FASTMCP = False

# ─── Changelog DNA (parsed from CHANGELOG.md) ───
VERSIONS = [
    {
        "version": "0.6.3", "date": "2026-02-13",
        "changes": [
            {"type": "perf", "desc": "Cached search-highlighted lines — no redundant regex on redraws"},
        ]
    },
    {
        "version": "0.6.2", "date": "2026-02-13",
        "changes": [
            {"type": "perf", "desc": "Local image dimension probing moved off UI thread"},
            {"type": "perf", "desc": "Zero per-frame document line cloning — ownership transfer to Text"},
            {"type": "perf", "desc": "Throttled image-load results per UI tick for responsive scrolling"},
            {"type": "perf", "desc": "Dedicated background resize worker for image encode"},
        ]
    },
    {
        "version": "0.6.1", "date": "2026-02-13",
        "changes": [
            {"type": "perf", "desc": "Cached virtual-row counts in max_scroll keyed by content width"},
        ]
    },
    {
        "version": "0.6.0", "date": "2026-02-11",
        "changes": [
            {"type": "feature", "desc": "Less-style half-page nav aliases: d (down) and u (up)"},
        ]
    },
    {
        "version": "0.5.0", "date": "2026-02-10",
        "changes": [
            {"type": "feature", "desc": "Lazy image loading with non-blocking background fetch/decode"},
            {"type": "fix", "desc": "Image layout reserves space using HTML width/height hints"},
            {"type": "fix", "desc": "Fixed partial-viewport draw artifacts while scrolling past images"},
        ]
    },
    {
        "version": "0.4.0", "date": "2026-02-10",
        "changes": [
            {"type": "feature", "desc": "Visible in-document cursor with line:column in status bar"},
        ]
    },
    {
        "version": "0.3.0", "date": "2026-02-10",
        "changes": [
            {"type": "feature", "desc": "Syntax highlighting for fenced code blocks with language tags"},
        ]
    },
    {
        "version": "0.2.0", "date": "2026-02-10",
        "changes": [
            {"type": "feature", "desc": "Inline terminal image rendering (markdown + HTML img tags)"},
            {"type": "feature", "desc": "Remote image loading (http/https)"},
            {"type": "feature", "desc": "--image-protocol CLI option (auto/halfblocks/sixel/kitty/iterm2)"},
            {"type": "fix", "desc": "TUI redraw on input/resize instead of fixed idle cadence"},
        ]
    },
    {
        "version": "0.1.0", "date": "2026-02-10",
        "changes": [
            {"type": "feature", "desc": "Vim-style full-page navigation (Ctrl-f/Ctrl-b)"},
            {"type": "feature", "desc": "Visual search match highlighting with active match emphasis"},
            {"type": "change", "desc": "Renamed from mdview to mdvi"},
        ]
    },
]


def get_versions() -> list:
    """List all versions with dates — the DNA timeline."""
    return [{"version": v["version"], "date": v["date"], "changes": len(v["changes"])} for v in VERSIONS]


def get_changes(version: str) -> dict:
    """Get detailed changes for a specific version."""
    for v in VERSIONS:
        if v["version"] == version:
            return v
    return {"error": f"Version {version} not found", "available": [v["version"] for v in VERSIONS]}


def get_latest() -> dict:
    """What's new in the current version."""
    return VERSIONS[0]


def get_perf_improvements() -> list:
    """Aggregate all performance work — thermal ratchet intelligence."""
    perfs = []
    for v in VERSIONS:
        for c in v["changes"]:
            if c["type"] == "perf":
                perfs.append({"version": v["version"], "date": v["date"], **c})
    return perfs


def get_evolution_summary() -> dict:
    """The full evolution arc from v0.1.0 to current — for context injection."""
    total_changes = sum(len(v["changes"]) for v in VERSIONS)
    features = sum(1 for v in VERSIONS for c in v["changes"] if c["type"] == "feature")
    perf = sum(1 for v in VERSIONS for c in v["changes"] if c["type"] == "perf")
    fixes = sum(1 for v in VERSIONS for c in v["changes"] if c["type"] == "fix")

    return {
        "agent": "mdvi_changelog",
        "first_version": VERSIONS[-1]["version"],
        "current_version": VERSIONS[0]["version"],
        "total_releases": len(VERSIONS),
        "total_changes": total_changes,
        "breakdown": {"features": features, "performance": perf, "fixes": fixes},
        "arc": "Basic Vim nav → syntax highlighting → images → lazy loading → full caching engine",
    }


# ─── FastMCP Registration ───
if _HAS_FASTMCP:
    mcp = FastMCP("MDVI Changelog — Version Oracle")
    mcp.tool()(get_versions)
    mcp.tool()(get_changes)
    mcp.tool()(get_latest)
    mcp.tool()(get_perf_improvements)
    mcp.tool()(get_evolution_summary)

if __name__ == "__main__":
    if _HAS_FASTMCP:
        mcp.run()
    else:
        print("[Changelog MCP] FastMCP not installed — use functions directly")
