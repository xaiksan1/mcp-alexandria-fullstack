# Alexandria MCP Full-Stack: Paper Intelligence (Paper2Agents)

Ce répertoire constitue l'ossature du système d'intelligence distribuée d'Alexandria, spécialisé dans la transformation de la connaissance académique et scientifique en agents opérationnels.

## 🧬 Concept Core

L'objectif est d'automatiser le cycle **"Papier Scientifique → Agent IA"**. Le système ingère des documents (PDF, LaTeX, Arxiv), en extrait les modèles théoriques, les paramètres et les logiques de décision, puis génère des agents spécialisés capables d'appliquer ces connaissances.

## 🏗️ Architecture du Projet

### 1. Paper2Agents (Backend)
Situé dans le dossier `backend/`.
- **Rôle** : Coeur logique du système.
- **Fonctionnalités** : 
    - Parsing de documents via MCP-Filesystem et outils d'extraction.
    - Analyse sémantique et structuration des connaissances.
    - Spawning d'agents ADK basés sur les modèles extraits.
    - Gestion des cycles d'incitation (LMM-Incentive).

### 2. Paper2Web (Frontend)
Situé dans le dossier `frontend/`.
- **Rôle** : Interface utilisateur d'interaction.
- **Fonctionnalités** :
    - Tableau de bord de monitoring des agents.
    - Visualisation des graphes de connaissances (Paper2all).
    - Interface de chat avec les agents "papiers".

### 3. Paper2all
- **Rôle** : Socle commun et utilitaires universels.
- **Fonctionnalités** :
    - Schémas de données partagés.
    - Connecteurs MCP génériques.
    - Protocoles de communication A2A (Agent-to-Agent).

## 🚀 Les Exemples "Pioneer"

Les fichiers à la racine (`pioneer_master.py`, `pioneer_daemon.py`, `pioneer_cron.sh`) sont les implémentations historiques et fonctionnelles de ce concept :

- **pioneer_master.py** : L'orchestrateur de cycle complet (Ingestion → Évaluation → Récompense). Il démontre comment un agent peut évaluer du contenu scientifique et déclencher des scellages de récompenses via Ethereum/Energon.
- **pioneer_daemon.py** : Le service de surveillance continue qui maintient la boucle d'intelligence active.
- **pioneer_cron.sh** : Planification système pour l'exécution périodique du cycle Pioneer.

## 🛡️ Mandat de Développement
Toute modification dans ce répertoire doit suivre les standards de production d'ADAM : **Zéro placeholder, code cryptographiquement validé, et persistance hybride.**
