"""toob_gate — le portail de naissance des larves.

Aucune larve ne naît sans avoir passé le TOOB (11 couches, status=complete).
Consigne de l'Architecte (2026-07-19) : une larve qui n'a pas passé le TOOB
ne doit PAS naître — le refus est le comportement correct, pas une erreur.

Autorité de diplôme (décision 2026-07-09, Flash and Jump) : une session TOOB
complète (11/11) EST le diplôme. Pas de nouveau système d'artefact — on lit
directement le store file-based du dashboard (straight-pipe, RAM_DOCTRINE :
fonctionne même si :5001 est down).
"""
import json
import os

TOOB_STORE = os.environ.get(
    "TOOB_STORE",
    "/home/ichigo/alexandria/ADAM/dashboard/.data/toob-sessions",
)
REQUIRED_LAYERS = 11


class ToobRefus(Exception):
    """La naissance est refusée — TOOB absent, incomplet ou introuvable."""


def verify(session_id: str) -> dict:
    """Retourne la session TOOB si elle vaut diplôme, sinon lève ToobRefus."""
    if not session_id or os.path.basename(session_id) != session_id:
        raise ToobRefus(f"identifiant de session TOOB invalide: {session_id!r}")
    path = os.path.join(TOOB_STORE, f"{session_id}.json")
    if not os.path.isfile(path):
        raise ToobRefus(
            f"session TOOB introuvable: {session_id} — pas de diplôme, pas de naissance"
        )
    with open(path) as f:
        session = json.load(f)
    done = sum(1 for l in session.get("layers", []) if l.get("status") == "done")
    if session.get("status") != "complete" or done < REQUIRED_LAYERS:
        raise ToobRefus(
            f"TOOB non passé ({done}/{REQUIRED_LAYERS} couches, "
            f"status={session.get('status')!r}) — la larve ne naît pas"
        )
    return session
