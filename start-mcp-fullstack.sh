#!/usr/bin/env bash
cd /home/ichigo/alexandria/mcp-alexandria-fullstack
set -a; source .env; set +a
cd backend
exec /home/ichigo/alexandria/ADAM/.venv/bin/python3 slack_command_server.py --host 127.0.0.1 --port 8003
