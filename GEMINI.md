# Alexandria MCP Full-Stack: Paper Intelligence (Paper2Agents)

Ce projet est une architecture multi-services basée sur le **Model Context Protocol (MCP)**, spécialisée dans la transformation de documents scientifiques en agents autonomes fonctionnels.

## Architecture & Services (Paper Intelligence)

L'écosystème se concentre sur trois piliers :

*   **Paper2Agents (Backend) :** Service d'extraction de connaissances et de génération d'agents (Spawning ADK).
*   **Paper2Web (Frontend) :** Interface de monitoring et d'interaction avec le swarm d'agents académiques.
*   **Paper2all :** Utilitaires transverses, protocoles A2A et connecteurs MCP universels.

## Système "Pioneer" (Implémentation de Référence)

Les fichiers `pioneer_*` à la racine sont les exemples concrets de l'automatisation du cycle :
1.  **Ingestion** (MCP Filesystem)
2.  **Analyse/Évaluation** (LLM-Incentive)
3.  **Persistance** (MCP Supabase)
4.  **Récompense** (Sealing Energon/Ethereum)

## Structure du Workspace

*   **backend/** : Coeur Paper2Agents.
*   **frontend/** : Interface Paper2Web.

---
*Note : Référez-vous à PAPER-INTELLIGENCE-GUIDE.md pour les détails techniques profonds.*

## Commandes Rapides (Prévisionnel)

*   **Installation :** `bun install` (frontend)
*   **Configuration :** Copier `.env.example` vers `.env` et renseigner les clés API.
*   **Lancement :** (À définir selon l'implémentation du backend)

---
*Note : Ce fichier sert de mémoire contextuelle pour éviter les répétitions lors des prochaines sessions.*
