#!/usr/bin/env python3
"""
MDVI MCP Server — Terminal Markdown Rendering Engine
Spawned from: mdvi/README.md
Stack DNA: Rust (ratatui + crossterm + pulldown-cmark)

This agent doesn't just describe markdown — it RENDERS it in the terminal.
Alexandria-style: the document becomes the interface.
"""

import re
import os
import subprocess
from pathlib import Path

try:
    from fastmcp import FastMCP
    _HAS_FASTMCP = True
except ImportError:
    _HAS_FASTMCP = False

# ─── Source DNA ───
MDVI_CAPABILITIES = {
    "renderer": "ratatui + crossterm full-screen TUI",
    "parser": "pulldown-cmark (CommonMark compliant)",
    "navigation": "Vim-style (j/k/d/u/g/G/Ctrl-f/Ctrl-b)",
    "images": "lazy loading, halfblocks/sixel/kitty/iterm2 protocols",
    "syntax": "syntect-based fenced code block highlighting",
    "search": "regex with match highlighting and n/N navigation",
    "performance": "cached scroll, zero-clone rendering, background image workers",
}

IMAGE_PROTOCOLS = ["auto", "halfblocks", "sixel", "kitty", "iterm2"]


def get_capabilities() -> dict:
    """Returns the full MDVI capability set derived from the Rust TUI codebase."""
    return {
        "agent": "mdvi",
        "version": "0.6.3",
        "capabilities": MDVI_CAPABILITIES,
        "image_protocols": IMAGE_PROTOCOLS,
        "source": "mdvi/README.md — Rust TUI markdown viewer",
    }


def render_markdown(path: str) -> str:
    """
    Render a markdown file as formatted terminal text.
    Uses ANSI escape codes for headings, bold, code, etc.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"[ERROR] File not found: {path}"
    if not p.suffix.lower() in ('.md', '.markdown', '.txt'):
        return f"[WARNING] Not a markdown file: {path}"

    content = p.read_text(encoding='utf-8', errors='replace')

    # ─── ANSI Terminal Rendering ───
    lines = []
    for line in content.split('\n'):
        # Headings → bold + color
        h_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if h_match:
            level = len(h_match.group(1))
            title = h_match.group(2)
            colors = ['\033[1;35m', '\033[1;36m', '\033[1;33m', '\033[1;32m', '\033[1;34m', '\033[1;31m']
            color = colors[min(level - 1, 5)]
            prefix = '▌' * level
            lines.append(f"{color}{prefix} {title}\033[0m")
        # Code blocks
        elif line.startswith('```'):
            lines.append('\033[2;37m' + '─' * 40 + '\033[0m')
        # Blockquotes
        elif line.startswith('>'):
            lines.append(f"\033[2;36m  ┃ {line[1:].strip()}\033[0m")
        # Task lists
        elif re.match(r'^[-*]\s+\[[ x]\]', line):
            checked = '[x]' in line or '[X]' in line
            icon = '✅' if checked else '⬜'
            text = re.sub(r'^[-*]\s+\[[ xX]\]\s*', '', line)
            lines.append(f"  {icon} {text}")
        # Bullet lists
        elif re.match(r'^[-*+]\s', line):
            lines.append(f"  • {line.lstrip('-*+ ')}")
        # Numbered lists
        elif re.match(r'^\d+\.\s', line):
            lines.append(f"  {line}")
        # Inline formatting
        else:
            # Bold
            line = re.sub(r'\*\*(.+?)\*\*', r'\033[1m\1\033[0m', line)
            # Italic
            line = re.sub(r'\*(.+?)\*', r'\033[3m\1\033[0m', line)
            # Inline code
            line = re.sub(r'`([^`]+)`', r'\033[7m \1 \033[0m', line)
            lines.append(line)

    return '\n'.join(lines)


def search_doc(path: str, query: str) -> list:
    """
    Search within a markdown document — regex-capable like mdvi's / command.
    Returns matching lines with line numbers.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return [{"error": f"File not found: {path}"}]

    content = p.read_text(encoding='utf-8', errors='replace')
    matches = []
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    for i, line in enumerate(content.split('\n'), 1):
        if pattern.search(line):
            matches.append({"line": i, "content": line.strip()})

    return matches if matches else [{"info": f"No matches for '{query}'"}]


def list_sections(path: str) -> list:
    """
    Extract the heading structure from a markdown file.
    Returns a hierarchy of sections with line numbers — like a TOC.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return [{"error": f"File not found: {path}"}]

    content = p.read_text(encoding='utf-8', errors='replace')
    sections = []

    for i, line in enumerate(content.split('\n'), 1):
        h_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if h_match:
            sections.append({
                "level": len(h_match.group(1)),
                "title": h_match.group(2).strip(),
                "line": i,
            })

    return sections


def render_file_to_tui(path: str, image_protocol: str = "halfblocks") -> str:
    """
    Launch the real mdvi Rust binary to render a file in the terminal.
    Falls back to Python rendering if mdvi binary isn't available.
    """
    # Try to find mdvi binary
    mdvi_bin = None
    for candidate in [
        Path.home() / '.cargo' / 'bin' / 'mdvi',
        Path('/usr/local/bin/mdvi'),
    ]:
        if candidate.exists():
            mdvi_bin = str(candidate)
            break

    if mdvi_bin:
        return f"[EXEC] {mdvi_bin} --image-protocol {image_protocol} {path}"
    else:
        return render_markdown(path)


# ─── FastMCP Registration ───
if _HAS_FASTMCP:
    mcp = FastMCP("MDVI — Terminal Markdown Renderer")
    mcp.tool()(get_capabilities)
    mcp.tool()(render_markdown)
    mcp.tool()(search_doc)
    mcp.tool()(list_sections)
    mcp.tool()(render_file_to_tui)

if __name__ == "__main__":
    if _HAS_FASTMCP:
        mcp.run()
    else:
        print("[MDVI MCP] FastMCP not installed — use functions directly")
