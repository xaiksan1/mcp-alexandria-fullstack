#!/bin/bash
# pioneer_cron.sh - Le battement de coeur de l'Incentive Engine
export PROJECT_ROOT="/home/ichigo/alexandria/ADAM"
cd $PROJECT_ROOT

echo "[$(date)] --- Lancement du cycle d'Incentive Pioneer 3.0 ---" >> pioneer_execution.log

# Exécution de l'orchestrateur maître
# On passe le dernier fragment de code modifié en entrée (simulation)
python3 pioneer_master.py >> pioneer_execution.log 2>&1

echo "[$(date)] --- Cycle complété avec succès ---" >> pioneer_execution.log
