#!/usr/bin/env bash
# start-mcp-fullstack.sh recréé le 2026-07-25 (disparu au reformat, seul le commit
# "checkpoint avant reformat" existait, sans ce fichier). Le backend/ FastAPI complet
# (Vault, TimescaleDB, DeepCode) décrit dans backend/README.md est encore "Prévu",
# jamais construit. Le seul composant réellement fonctionnel du repo est le serveur
# Claude×Zangetsu (stdlib http.server, aucune dépendance externe) — protocole Z-01.
cd "$(dirname "$0")/claude-zangetsu/backend"
exec /home/ichigo/alexandria/ADAM/.venv/bin/python3 server.py
