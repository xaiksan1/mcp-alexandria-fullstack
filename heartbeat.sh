#!/bin/bash
# ADAM Heartbeat - Zangetsu Emergency Monitor
LEDGER="../digital-twin-data/energon_ledger.json"

echo "------------------------------------------"
echo "   ADAM CORE STATUS - PHASE 8 / v7.0"
echo "------------------------------------------"
echo "DATE ACTUELLE : $(date)"
echo ""

if [ -f "$LEDGER" ]; then
    BALANCE=$(jq -r '.balance' $LEDGER)
    SEALED=$(jq -r '.sealed_to_blockchain' $LEDGER)
    LAST_UPDATE=$(jq -r '.last_update' $LEDGER)
    PENDING=$(jq -r '.pending_seal' $LEDGER)

    echo "⚡ BALANCE TOTALE      : $BALANCE EGN"
    echo "🔒 SCELLÉ BLOCKCHAIN   : $SEALED kWh"
    echo "⏳ EN ATTENTE (PENDING): $PENDING EGN"
    echo "📅 DERNIÈRE MISE À JOUR: $LAST_UPDATE"
    echo ""
    echo "--- DERNIERS SCEAUX ---"
    jq -r '(.blockchain_seals[-3:] | .[] | "• Bloc: \(.block_hash[:12])... Amount: \(.sealed_egn)")' $LEDGER
else
    echo "❌ Erreur : Ledger introuvable."
fi
echo "------------------------------------------"
