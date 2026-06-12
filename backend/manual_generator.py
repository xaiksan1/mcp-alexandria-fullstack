"""
manual_generator.py — Alexandria Living Manual Generator
=========================================================
Lit emoji_registry + SESHAT graph → génère un manuel Markdown en 3 couches.

Couche 1 : Glossaire emoji (une ligne par mapping, groupé par action_type)
Couche 2 : Blocs système (nœuds SESHAT groupés par type)
Couche 3 : Recettes concrètes (comment déclencher quoi)

Outputs :
  backend/MANUAL.md         — version complète (toutes couches)
  backend/MANUAL_SLACK.md   — version courte mrkdwn (Slack-friendly)

Hook yin-yang :
  hook_registry()  — patch EmojiRegistry._save() → régénère à chaque changement
  post_to_slack()  — publie sur Slack (credentials dans ~/.config/alexandria/slack.env)
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

BACKEND = Path(__file__).resolve().parent
SESHAT_PATH = Path.home() / "alexandria/ADAM/CORPUS/SESHAT"
MANUAL_FULL_PATH  = BACKEND / "MANUAL.md"
MANUAL_SLACK_PATH = BACKEND / "MANUAL_SLACK.md"
SLACK_CONFIG      = Path.home() / ".config/alexandria/slack.env"

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(SESHAT_PATH))

from emoji_registry import get_registry, EmojiMapping

try:
    from graph_store import get_graph
    HAS_SESHAT = True
except ImportError:
    HAS_SESHAT = False
    print("[manual] SESHAT graph non disponible — Couche 2 désactivée")


# ── Métadonnées ────────────────────────────────────────────────────────────────

ACTION_LABELS = {
    "agent2web":    "Ouvre un agent web (interface navigateur)",
    "agent2cli":    "Lance un agent en ligne de commande",
    "agent2agents": "Orchestre un essaim d'agents",
    "agent2tui":    "Lance un agent en interface texte (TUI)",
    "mcp2cli":      "Expose un serveur MCP comme commande CLI",
    "mcp2agents":   "Connecte un serveur MCP à un essaim d'agents",
    "paper2agent":  "Transforme un PDF/paper en agent autonome",
    "paper2mcp":    "Transforme un PDF/paper en serveur MCP",
    "node2window":  "Ouvre un nœud SESHAT comme fenêtre UI",
    "node2slack":   "Poste l'état d'un nœud sur Slack",
}

NODE_ICONS = {
    "HUB":          "🌐",
    "AGENT":        "🤖",
    "FOLDER":       "📁",
    "FILE":         "📄",
    "PROJECT":      "🏗️",
    "MEMORY":       "🧠",
    "GATEWAY":      "🚪",
    "ORCHESTRATOR": "🎯",
    "SYSTEM":       "⚙️",
    "TEST":         "🧪",
}

RECIPES = [
    {
        "title": "Spawner un agent depuis un paper ou un PDF",
        "emoji": "📄",
        "steps": [
            "Dépose ton fichier dans `alexandria/ADAM/pdf/` ou n'importe où",
            "Déclenche `📄` avec `{\"source\": \"/chemin/vers/paper.md\"}`",
            "L'agent est généré dans `backend/spawned_agents/` et prêt à tourner",
            "Même chose avec `🖥️` pour un serveur MCP au lieu d'un agent CLI",
        ],
        "example": 'dispatch_emoji("📄", {"source": "pdf/mon_paper.md"})',
    },
    {
        "title": "Enregistrer un nouvel emoji dans le système",
        "emoji": "✨",
        "steps": [
            "Choisis un emoji libre, un node_id SESHAT, et un action_type",
            "Via MCP : outil `register_emoji`",
            "Via CLI : `python3 trunk_dispatcher.py` (liste les mappings)",
            "Le manuel se met à jour automatiquement après l'enregistrement",
        ],
        "example": 'register_emoji("🛡️", "aegis", "AEGIS", "agent2cli", "aegis.py")',
    },
    {
        "title": "Lancer un agent en interface texte (TUI)",
        "emoji": "🌡️",
        "steps": [
            "Déclenche un emoji `agent2tui` : `🌡️` (Thermal Ratchet) ou `🕸️` (SERENA)",
            "Un terminal s'ouvre avec l'agent en mode interactif",
            "Ctrl+C pour fermer",
        ],
        "example": 'dispatch_emoji("🌡️")',
    },
    {
        "title": "Poster un état sur Slack",
        "emoji": "🤖",
        "steps": [
            "`👤` → #alexandria-human (pour les humains)",
            "`🤖` → #alexandria-llm (pour les agents IA)",
            "Ajoute `text` dans les args pour personnaliser le message",
            "Ajoute `webhook_url` dans le meta du mapping pour activer l'envoi",
        ],
        "example": 'dispatch_emoji("🤖", {"text": "ADAM : opérationnel, 67 nœuds actifs"})',
    },
    {
        "title": "Voir le mind-map SESHAT en direct",
        "emoji": "⬡",
        "steps": [
            "Déclenche `⬡` pour ouvrir Alexandria Core",
            "`📜` → dossier Memory, `🌸` → carte Stigmergy",
            "Chaque nœud est cliquable et affiche ses pheromone trails",
        ],
        "example": 'dispatch_emoji("⬡")',
    },
    {
        "title": "Régénérer ce manuel manuellement",
        "emoji": "📖",
        "steps": [
            "Via MCP : outil `regenerate_manual`",
            "Via CLI : `python3 manual_generator.py`",
            "Via CLI avec preview : `python3 manual_generator.py --preview`",
            "Poste sur Slack : `python3 manual_generator.py --slack #alexandria-human`",
        ],
        "example": "python3 manual_generator.py --preview",
    },
]


# ── Couche 1 : Glossaire Emoji (Markdown) ────────────────────────────────────

def layer1_md(registry) -> str:
    lines = [
        "## 🗺️ COUCHE 1 — GLOSSAIRE EMOJI",
        "",
        "> **Chaque emoji = un déclencheur.** Tape l'emoji pour activer l'action correspondante.",
        "> La liste complète est dans `emoji_registry.json`. Elle évolue en temps réel.",
        "",
    ]

    by_type: dict[str, list] = {}
    for m in registry.all():
        by_type.setdefault(m.action_type, []).append(m)

    for atype in sorted(by_type):
        label = ACTION_LABELS.get(atype, atype)
        lines.append(f"### `{atype}` — {label}")
        lines.append("")
        lines.append("| Emoji | Nom | Cible | Description |")
        lines.append("|:-----:|-----|-------|-------------|")
        for m in sorted(by_type[atype], key=lambda x: x.label):
            status = "" if m.active else " *(désactivé)*"
            lines.append(
                f"| {m.emoji} | **{m.label}**{status} | `{m.target}` | {m.description or '—'} |"
            )
        lines.append("")

    return "\n".join(lines)


# ── Couche 1 : Glossaire Emoji (Slack mrkdwn) ────────────────────────────────

def layer1_slack(registry) -> str:
    lines = [
        "*🗺️ GLOSSAIRE EMOJI — Alexandria*",
        "_Chaque emoji = un déclencheur. Tape l'emoji pour activer l'action._",
        "",
    ]

    by_type: dict[str, list] = {}
    for m in registry.all():
        by_type.setdefault(m.action_type, []).append(m)

    for atype in sorted(by_type):
        label = ACTION_LABELS.get(atype, atype)
        lines.append(f"*{atype}* — {label}")
        for m in sorted(by_type[atype], key=lambda x: x.label):
            status = " ~désactivé~" if not m.active else ""
            lines.append(f"  {m.emoji}  *{m.label}*{status}  →  `{m.target}`")
            if m.description:
                lines.append(f"       _{m.description}_")
        lines.append("")

    return "\n".join(lines)


# ── Couche 2 : Blocs Système (SESHAT) ────────────────────────────────────────

def layer2_md() -> str:
    if not HAS_SESHAT:
        return "## 🧩 COUCHE 2 — BLOCS SYSTÈME\n\n_SESHAT non disponible._\n"

    graph   = get_graph()
    nodes   = graph.all_nodes()
    hot     = {t.from_id for t in graph.hot_trails(20)} | {t.to_id for t in graph.hot_trails(20)}

    lines = [
        "## 🧩 COUCHE 2 — BLOCS SYSTÈME",
        "",
        "> Les nœuds du Mind-Map SESHAT. Chaque bloc = une capacité du système.",
        "> 🔥 = nœud chaud (beaucoup traversé récemment).",
        "",
    ]

    by_type: dict[str, list] = {}
    for n in nodes:
        by_type.setdefault(n.type, []).append(n)

    for ntype in sorted(by_type):
        icon = NODE_ICONS.get(ntype, "▪️")
        nlist = sorted(by_type[ntype], key=lambda n: n.label)
        lines.append(f"### {icon} {ntype} ({len(nlist)})")
        lines.append("")
        for n in nlist:
            heat = " 🔥" if n.id in hot else ""
            children_str = f" → `{', '.join(n.children[:4])}`" if n.children else ""
            lines.append(f"- **{n.label}**{heat} `{n.id}`{children_str}")
            if n.desc:
                lines.append(f"  _{n.desc}_")
        lines.append("")

    return "\n".join(lines)


# ── Couche 3 : Recettes ───────────────────────────────────────────────────────

def layer3_md() -> str:
    lines = [
        "## 📖 COUCHE 3 — RECETTES",
        "",
        "> Comment faire des choses concrètes. Copie-colle et adapte.",
        "",
    ]

    for recipe in RECIPES:
        lines.append(f"### {recipe['emoji']} {recipe['title']}")
        lines.append("")
        for i, step in enumerate(recipe["steps"], 1):
            lines.append(f"{i}. {step}")
        lines.append("")
        lines.append(f"**Exemple :** `{recipe['example']}`")
        lines.append("")

    return "\n".join(lines)


# ── Génération complète ───────────────────────────────────────────────────────

def generate(registry=None, save: bool = True) -> tuple[str, str]:
    """
    Génère MANUAL.md (complet) et MANUAL_SLACK.md (court, mrkdwn).
    Retourne (full_md, slack_md).
    """
    if registry is None:
        registry = get_registry()

    ts          = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    emoji_count = len(registry.all())
    node_count  = len(get_graph().all_nodes()) if HAS_SESHAT else "?"

    header_md = (
        f"# MANUEL ALEXANDRIA — Anima Mundi\n"
        f"*Généré automatiquement · {ts}*  \n"
        f"*{emoji_count} emojis · {node_count} nœuds SESHAT*\n\n"
        f"> Ce manuel est vivant. Il se met à jour quand le système change.  \n"
        f"> Le système se met à jour quand vous modifiez ce manuel.  \n"
        f"> ☯ Yin-Yang.\n\n"
        f"---\n\n"
    )

    full_md = (
        header_md
        + layer1_md(registry)
        + "\n---\n\n"
        + layer2_md()
        + "\n---\n\n"
        + layer3_md()
    )

    slack_header = (
        f"*MANUEL ALEXANDRIA — Anima Mundi*  |  _{ts}_\n"
        f"_{emoji_count} emojis · {node_count} nœuds SESHAT_\n\n"
    )
    slack_md = slack_header + layer1_slack(registry)

    if save:
        MANUAL_FULL_PATH.write_text(full_md, encoding="utf-8")
        MANUAL_SLACK_PATH.write_text(slack_md, encoding="utf-8")
        print(f"[manual] MANUAL.md        → {len(full_md):,} chars")
        print(f"[manual] MANUAL_SLACK.md  → {len(slack_md):,} chars")

    return full_md, slack_md


# ── Slack post ────────────────────────────────────────────────────────────────

def _load_slack_cfg() -> dict:
    cfg = {}
    if SLACK_CONFIG.exists():
        for line in SLACK_CONFIG.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def post_to_slack(channel: str = "#alexandria-human", text: Optional[str] = None) -> dict:
    """
    Poste la version Slack du manuel dans un channel.
    Nécessite ~/.config/alexandria/slack.env :
      SLACK_XOXC=xoxc-...
      SLACK_COOKIE_D=...
      SLACK_CHANNEL_ID=C...  (ou le nom du channel)
    """
    import urllib.request

    cfg      = _load_slack_cfg()
    token    = cfg.get("SLACK_XOXC", "")
    cookie_d = cfg.get("SLACK_COOKIE_D", "")
    chan     = cfg.get("SLACK_CHANNEL_ID", channel)

    if not token:
        return {
            "status": "NO_TOKEN",
            "hint":   "Ajoute SLACK_XOXC et SLACK_COOKIE_D dans ~/.config/alexandria/slack.env",
        }

    if text is None:
        _, text = generate(save=True)

    # Slack limite les messages à ~40k caractères
    if len(text) > 39_000:
        text = text[:39_000] + "\n\n_[... tronqué — voir MANUAL.md pour la version complète]_"

    payload = json.dumps({"channel": chan, "text": text, "mrkdwn": True}).encode()

    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {token}",
            "Cookie":        f"d={cookie_d}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        status = "OK" if result.get("ok") else f"SLACK_ERROR:{result.get('error')}"
        print(f"[manual] Slack post → {chan} : {status}")
        return result
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


# ── Hook yin-yang ─────────────────────────────────────────────────────────────

def hook_registry(auto_slack: bool = False, slack_channel: str = "#alexandria-human"):
    """
    Patch EmojiRegistry._save() pour régénérer le manuel à chaque changement.
    Appelle une fois au démarrage du dispatcher.

    auto_slack=True → poste aussi sur Slack à chaque changement (peut être verbeux).
    """
    registry = get_registry()
    _orig    = registry._save

    def _patched():
        _orig()
        full_md, slack_md = generate(registry=registry, save=True)
        if auto_slack:
            post_to_slack(channel=slack_channel, text=slack_md)

    registry._save = _patched
    print(f"[manual] Hook yin-yang installé (auto_slack={auto_slack})")
    return registry


# ── FastMCP tools ─────────────────────────────────────────────────────────────

try:
    from fastmcp import FastMCP as _FastMCP
    _mcp     = _FastMCP("alexandria-manual")
    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False

if _HAS_MCP:
    @_mcp.tool()
    def regenerate_manual() -> dict:
        """Régénère MANUAL.md et MANUAL_SLACK.md depuis l'état courant du registre + SESHAT."""
        full_md, slack_md = generate()
        return {
            "status":       "OK",
            "full_chars":   len(full_md),
            "slack_chars":  len(slack_md),
            "full_path":    str(MANUAL_FULL_PATH),
            "slack_path":   str(MANUAL_SLACK_PATH),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }

    @_mcp.tool()
    def get_manual(layer: str = "full") -> str:
        """
        Retourne le contenu du manuel.
        layer : 'full' | 'slack' | 'layer1' | 'layer2' | 'layer3'
        """
        reg = get_registry()
        if layer == "slack":
            return layer1_slack(reg)
        elif layer == "layer1":
            return layer1_md(reg)
        elif layer == "layer2":
            return layer2_md()
        elif layer == "layer3":
            return layer3_md()
        full_md, _ = generate(registry=reg, save=False)
        return full_md

    @_mcp.tool()
    def publish_to_slack(channel: str = "#alexandria-human") -> dict:
        """Poste la version Slack du manuel dans le channel indiqué."""
        return post_to_slack(channel=channel)

    @_mcp.tool()
    def manual_status() -> dict:
        """Retourne l'état actuel du générateur (chemins, compteurs, hook actif)."""
        reg = get_registry()
        return {
            "emoji_count":       len(reg.all()),
            "seshat_available":  HAS_SESHAT,
            "node_count":        len(get_graph().all_nodes()) if HAS_SESHAT else 0,
            "full_path":         str(MANUAL_FULL_PATH),
            "slack_path":        str(MANUAL_SLACK_PATH),
            "full_exists":       MANUAL_FULL_PATH.exists(),
            "slack_exists":      MANUAL_SLACK_PATH.exists(),
            "slack_config":      SLACK_CONFIG.exists(),
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--mcp" in sys.argv:
        if _HAS_MCP:
            _mcp.run()
        else:
            print("[manual] FastMCP non disponible")

    elif "--slack" in sys.argv:
        idx = sys.argv.index("--slack")
        chan = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "#alexandria-human"
        result = post_to_slack(channel=chan)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        full_md, slack_md = generate()
        if "--preview" in sys.argv:
            print("─" * 60)
            print("APERÇU SLACK (2000 premiers caractères) :")
            print("─" * 60)
            print(slack_md[:2000])
            print("─" * 60)
        else:
            print(f"Fichiers générés :")
            print(f"  {MANUAL_FULL_PATH}")
            print(f"  {MANUAL_SLACK_PATH}")
