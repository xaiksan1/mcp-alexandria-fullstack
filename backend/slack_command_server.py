"""
slack_command_server.py — Slack Slash Command Server
=====================================================
Implémente /update-manual (boucle yin-yang sens inverse : Slack → système).

Syntaxe de la commande :
  /update-manual add <emoji> <node_id> <label> <action_type> <target> [description]
  /update-manual disable <emoji>
  /update-manual enable  <emoji>
  /update-manual remove  <emoji>
  /update-manual status
  /update-manual regenerate
  /update-manual help

Setup (une seule fois) :
  1. Créer une Slack App → Slash Commands → /update-manual
  2. Request URL = https://<url-publique>/slack/command
  3. Copier le Signing Secret → SLACK_SIGNING_SECRET dans slack.env
  4. Lancer ce serveur   : python3 slack_command_server.py
  5. Exposer publiquement : ssh -R 80:localhost:8003 localhost.run
     → Coller l'URL dans Slack App settings

Config : ~/.config/alexandria/slack.env
  SLACK_SIGNING_SECRET=...   # obligatoire pour vérifier les requêtes Slack
  SLACK_XOXC=xoxc-...        # pour publish_to_slack (post du manuel)
  SLACK_COOKIE_D=...
  SLACK_CHANNEL_ID=C...
"""
import hashlib
import hmac
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

# ── Paths ─────────────────────────────────────────────────────────────────────

BACKEND     = Path(__file__).resolve().parent
SLACK_CFG   = Path.home() / ".config/alexandria/slack.env"
PORT        = int(os.environ.get("SLACK_CMD_PORT", 8003))

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path.home() / "alexandria/ADAM/CORPUS/SESHAT"))

from emoji_registry import get_registry, EmojiMapping

try:
    from manual_generator import generate as _generate, hook_registry as _hook
    _hook(auto_slack=False)
    HAS_MANUAL = True
except ImportError:
    HAS_MANUAL = False

# ── Config ────────────────────────────────────────────────────────────────────

def _load_cfg() -> dict:
    cfg = {}
    if SLACK_CFG.exists():
        for line in SLACK_CFG.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg

CFG = _load_cfg()
SIGNING_SECRET = CFG.get("SLACK_SIGNING_SECRET", os.environ.get("SLACK_SIGNING_SECRET", ""))

# ── Signature verification ────────────────────────────────────────────────────

def _verify_slack(raw_body: bytes, headers) -> None:
    """
    Vérifie la signature HMAC-SHA256 de Slack sur le body brut.
    Si SLACK_SIGNING_SECRET absent → mode dev (avertissement uniquement).
    """
    if not SIGNING_SECRET:
        print("[slack-cmd] ⚠️  SIGNING_SECRET absent — vérification désactivée (mode dev)")
        return

    ts        = headers.get("x-slack-request-timestamp", "")
    signature = headers.get("x-slack-signature", "")

    if abs(time.time() - int(ts or 0)) > 300:
        raise HTTPException(status_code=401, detail="Timestamp trop ancien")

    expected = "v0=" + hmac.new(
        SIGNING_SECRET.encode(),
        f"v0:{ts}:{raw_body.decode()}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Signature invalide")


# ── Parser commande ───────────────────────────────────────────────────────────

ACTION_TYPES = {
    "agent2web", "agent2cli", "agent2agents", "agent2tui",
    "mcp2cli", "mcp2agents", "paper2agent", "paper2mcp",
    "node2window", "node2slack",
}

def _parse(text: str) -> dict:
    """
    Parse le texte de la slash command.

    Syntaxes reconnues :
      add <emoji> <node_id> <label> <action_type> <target> [description...]
      disable <emoji>
      enable  <emoji>
      remove  <emoji>
      status
      regenerate
      help
    """
    text = text.strip()
    if not text or text in ("help", "--help", "-h"):
        return {"op": "help"}

    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()

    op = parts[0].lower()

    if op == "status":
        return {"op": "status"}

    if op == "regenerate":
        return {"op": "regenerate"}

    if op in ("disable", "enable", "remove"):
        if len(parts) < 2:
            return {"op": "error", "msg": f"`{op}` requiert un emoji. Ex: `{op} 🛡️`"}
        return {"op": op, "emoji": parts[1]}

    if op == "add":
        # add <emoji> <node_id> <label> <action_type> <target> [description...]
        if len(parts) < 6:
            return {
                "op":  "error",
                "msg": (
                    "Usage : `add <emoji> <node_id> <label> <action_type> <target> [description]`\n"
                    f"Action types valides : {', '.join(sorted(ACTION_TYPES))}"
                ),
            }
        emoji, node_id, label, action_type, target = parts[1], parts[2], parts[3], parts[4], parts[5]
        description = " ".join(parts[6:]) if len(parts) > 6 else ""

        if action_type not in ACTION_TYPES:
            return {
                "op":  "error",
                "msg": (
                    f"`{action_type}` n'est pas un action_type valide.\n"
                    f"Valides : {', '.join(sorted(ACTION_TYPES))}"
                ),
            }
        return {
            "op":          "add",
            "emoji":       emoji,
            "node_id":     node_id,
            "label":       label,
            "action_type": action_type,
            "target":      target,
            "description": description,
        }

    return {"op": "error", "msg": f"Opération inconnue : `{op}`. Tape `/update-manual help`."}


# ── Handlers ──────────────────────────────────────────────────────────────────

def _handle(cmd: dict, user: str) -> tuple[str, bool]:
    """
    Exécute l'opération parsée.
    Retourne (message_slack, in_channel).
    in_channel=True → visible par tout le monde, False → éphémère.
    """
    registry = get_registry()
    op       = cmd["op"]

    # ── help ──
    if op == "help":
        return (
            "*Commandes /update-manual* :\n"
            "```\n"
            "add <emoji> <node_id> <label> <action_type> <target> [description]\n"
            "disable <emoji>\n"
            "enable  <emoji>\n"
            "remove  <emoji>\n"
            "status\n"
            "regenerate\n"
            "```\n"
            f"*Action types* : {', '.join(sorted(ACTION_TYPES))}\n"
            "*Exemple* : `add 🛡️ aegis AEGIS agent2cli aegis.py Crypto defense`",
            False,
        )

    # ── error ──
    if op == "error":
        return f"❌ {cmd['msg']}", False

    # ── status ──
    if op == "status":
        mappings = registry.all()
        active   = [m for m in mappings if m.active]
        lines    = [f"*Alexandria Registry Status* — _{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"]
        lines.append(f"  {len(mappings)} mappings · {len(active)} actifs")
        lines.append("")
        by_type: dict[str, list] = {}
        for m in active:
            by_type.setdefault(m.action_type, []).append(m)
        for atype in sorted(by_type):
            emojis = " ".join(m.emoji for m in by_type[atype])
            lines.append(f"  *{atype}* : {emojis}")
        return "\n".join(lines), False

    # ── regenerate ──
    if op == "regenerate":
        if not HAS_MANUAL:
            return "❌ manual_generator non disponible", False
        full_md, slack_md = _generate()
        return (
            f"✅ Manuel régénéré par *{user}*\n"
            f"  `MANUAL.md` : {len(full_md):,} chars\n"
            f"  `MANUAL_SLACK.md` : {len(slack_md):,} chars",
            True,
        )

    # ── add ──
    if op == "add":
        emoji = cmd["emoji"]
        existing = registry.get(emoji)
        m = EmojiMapping(
            emoji       = emoji,
            node_id     = cmd["node_id"],
            label       = cmd["label"],
            action_type = cmd["action_type"],
            target      = cmd["target"],
            description = cmd["description"],
        )
        registry.register(m)  # déclenche le hook → régénère MANUAL.md
        verb = "mis à jour" if existing else "ajouté"
        return (
            f"✅ *{user}* a {verb} `{emoji}` dans le registre\n"
            f"  *{m.label}* · `{m.action_type}` → `{m.target}`\n"
            f"  Manuel régénéré automatiquement.",
            True,
        )

    # ── disable / enable ──
    if op in ("disable", "enable"):
        emoji   = cmd["emoji"]
        mapping = registry.get(emoji)
        if not mapping:
            return f"❌ Emoji `{emoji}` non trouvé dans le registre.", False

        # EmojiMapping est un dataclass — on crée une copie modifiée
        updated = EmojiMapping(
            emoji       = mapping.emoji,
            node_id     = mapping.node_id,
            label       = mapping.label,
            action_type = mapping.action_type,
            target      = mapping.target,
            description = mapping.description,
            active      = (op == "enable"),
            created_at  = mapping.created_at,
            meta        = mapping.meta,
        )
        registry.register(updated)
        state = "activé" if op == "enable" else "désactivé"
        return (
            f"✅ *{user}* a {state} `{emoji}` ({mapping.label})\n"
            f"  Manuel régénéré automatiquement.",
            True,
        )

    # ── remove ──
    if op == "remove":
        emoji = cmd["emoji"]
        ok    = registry.remove(emoji)
        if not ok:
            return f"❌ Emoji `{emoji}` non trouvé dans le registre.", False
        if HAS_MANUAL:
            _generate()
        return f"✅ *{user}* a supprimé `{emoji}` du registre. Manuel régénéré.", True

    return "❌ Opération non reconnue.", False


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Alexandria Slack Commands", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "alexandria-slack-cmd", "port": PORT}


@app.post("/slack/command")
async def slack_command(request: Request):
    # Lire le body brut UNE SEULE FOIS — évite le conflit Form + body stream
    raw_body = await request.body()

    # Vérification signature HMAC (non-bloquante si secret absent)
    _verify_slack(raw_body, request.headers)

    # Parser application/x-www-form-urlencoded manuellement
    params       = {k: v[0] for k, v in parse_qs(raw_body.decode()).items()}
    command      = params.get("command", "")
    text         = params.get("text", "")
    user_name    = params.get("user_name", "unknown")

    if command != "/update-manual":
        return JSONResponse({"text": f"Commande inconnue : {command}"})

    print(f"[slack-cmd] {user_name}: /update-manual {text!r}")

    parsed        = _parse(text)
    message, pub  = _handle(parsed, user_name)

    return JSONResponse({
        "response_type": "in_channel" if pub else "ephemeral",
        "text":          message,
        "mrkdwn":        True,
    })


# ── Tunnel helper ─────────────────────────────────────────────────────────────

def print_setup_instructions(public_url: str = "<URL-PUBLIQUE>"):
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     SETUP SLACK SLASH COMMAND /update-manual                 ║
╠══════════════════════════════════════════════════════════════╣
║  1. Va sur https://api.slack.com/apps                        ║
║  2. Crée ou sélectionne ton app Alexandria                   ║
║  3. Slash Commands → Create New Command                      ║
║     Command   : /update-manual                              ║
║     Request URL: {public_url}/slack/command
║     Short desc: Modifie le registre emoji Alexandria         ║
║  4. Signing Secret → Settings → Basic Information            ║
║     Copie dans ~/.config/alexandria/slack.env :              ║
║     SLACK_SIGNING_SECRET=<ton-secret>                        ║
║  5. Réinstalle l'app dans ton workspace                      ║
╚══════════════════════════════════════════════════════════════╝

Pour exposer ce serveur :
  ssh -R 80:localhost:{PORT} localhost.run
  └→ copier l'URL https://... dans Slack Request URL
""")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Alexandria Slack Command Server")
    parser.add_argument("--port",   type=int, default=PORT, help=f"Port (défaut: {PORT})")
    parser.add_argument("--host",   default="0.0.0.0",      help="Host (défaut: 0.0.0.0)")
    parser.add_argument("--setup",  action="store_true",     help="Afficher les instructions de setup")
    parser.add_argument("--test",   metavar="CMD",           help="Tester un parsing local (ex: 'add 🛡️ aegis AEGIS agent2cli aegis.py')")
    args = parser.parse_args()

    if args.setup:
        print_setup_instructions()
        sys.exit(0)

    if args.test:
        parsed = _parse(args.test)
        print("Parsed:", json.dumps(parsed, ensure_ascii=False, indent=2))
        msg, pub = _handle(parsed, "test-user")
        print(f"in_channel={pub}")
        print(msg)
        sys.exit(0)

    print_setup_instructions(f"http://localhost:{args.port}")
    print(f"[slack-cmd] Démarrage sur http://{args.host}:{args.port}")
    print(f"[slack-cmd] SIGNING_SECRET: {'configuré ✓' if SIGNING_SECRET else 'absent ⚠️  (mode dev)'}")
    print(f"[slack-cmd] Hook manuel: {'actif ✓' if HAS_MANUAL else 'absent'}")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
