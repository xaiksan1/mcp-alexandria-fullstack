"""paper_spawner.spawn_mcp_server : un titre de papier est une DONNÉE, jamais du code. Un papier normal donne le même agent qu'avant."""

import ast
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paper_spawner import PaperSpawner  # noqa: E402


class FauxMCP:
    def __init__(self, nom):
        self.nom = nom

    def tool(self):
        return lambda f: f


def generer(tmp_path, nom, capacites=("Intro", "Methode"), source="/papiers/p.md"):
    sp = PaperSpawner.__new__(PaperSpawner)        # sans __init__ : il crée un dossier à un chemin codé en dur
    sp.output_dir = str(tmp_path / "spawned_agents")
    Path(sp.output_dir).mkdir()
    chemin = Path(sp.spawn_mcp_server({"name": nom, "source": source, "capabilities": list(capacites)}))
    return sp, chemin


def executer(chemin: Path):
    """Charge le script généré avec un faux fastmcp ; retourne son espace de noms (jamais lancé comme programme)."""
    faux = types.ModuleType("fastmcp"); faux.FastMCP = FauxMCP
    avant = sys.modules.get("fastmcp"); sys.modules["fastmcp"] = faux
    try:
        ns = {"__name__": "agent_genere"}
        exec(compile(chemin.read_text(), str(chemin), "exec"), ns)
        return ns
    finally:
        if avant is None:
            sys.modules.pop("fastmcp", None)
        else:
            sys.modules["fastmcp"] = avant


# ── un papier normal : même résultat qu'avant ───────────────────────────────
def test_papier_normal_meme_comportement_qu_avant(tmp_path):
    sp, chemin = generer(tmp_path, "Mon Agent")
    assert chemin.name == "mon_agent_mcp.py" and chemin.parent == Path(sp.output_dir)
    ns = executer(chemin)
    assert ns["mcp"].nom == "Mon Agent"
    assert ns["get_info"]() == "I am the Mon Agent agent. My capabilities include: Intro, Methode"
    assert ns["analyze_context"]("q") == "Analyzing 'q' based on Mon Agent principles."


def test_titre_avec_accents_et_emoji(tmp_path):
    _, chemin = generer(tmp_path, "Grimoire opérationnel 🌌")
    ns = executer(chemin)
    assert ns["mcp"].nom == "Grimoire opérationnel 🌌"
    assert "Grimoire opérationnel 🌌" in chemin.read_text()          # lisible dans le script, pas en \uXXXX


# ── un titre hostile : aucune exécution, le texte reste du texte ────────────
HOSTILES = [
    'X" + __import__("os").system("touch {marque}") + "',
    "X') or __import__('os').system('touch {marque}') or ('",
    'X"""\n__import__("os").system("touch {marque}")\n"""',
    "{__import__('os').system('touch {marque}')}",
    "X\\\" + __import__(\\\"os\\\").system(\\\"touch {marque}\\\") + \\\"",
    "X\r__import__('os').system('touch {marque}')",
]


@pytest.mark.parametrize("modele", HOSTILES)
def test_titre_hostile_n_execute_rien(tmp_path, modele):
    marque = tmp_path / "INJECTE"
    nom = modele.replace("{marque}", str(marque)) if "{marque}" in modele and not modele.startswith("{") else modele.replace("{marque}", str(marque))
    _, chemin = generer(tmp_path, nom)
    ast.parse(chemin.read_text())                                   # toujours un script valide
    ns = executer(chemin)
    assert not marque.exists()
    assert ns["mcp"].nom == nom                                      # le titre reste tel quel, comme texte
    assert ns["get_info"]().startswith("I am the " + nom + " agent.")
    assert nom in ns["analyze_context"]("q")


def test_accolades_du_titre_ne_sont_pas_evaluees(tmp_path):
    _, chemin = generer(tmp_path, "Calcul {1+1} {nom}")
    ns = executer(chemin)
    assert ns["analyze_context"]("q") == "Analyzing 'q' based on Calcul {1+1} {nom} principles."


def test_capacites_et_source_hostiles(tmp_path):
    marque = tmp_path / "INJECTE2"
    cap = f'Cap" + __import__("os").system("touch {marque}") + "'
    src = f"/papiers/p.md\n__import__('os').system('touch {marque}')\n#"
    _, chemin = generer(tmp_path, "Sain", capacites=(cap, "B"), source=src)
    ast.parse(chemin.read_text())
    ns = executer(chemin)
    assert not marque.exists() and cap in ns["get_info"]()


# ── le nom du fichier reste dans le dossier de sortie ───────────────────────
@pytest.mark.parametrize("nom", ["../../evil", "..\\..\\evil", "/etc/cron.d/x", "a/b/c", ".caché", "...", "x\x00y", " "])
def test_nom_de_fichier_reste_dans_le_dossier(tmp_path, nom):
    sp, chemin = generer(tmp_path, nom)
    assert chemin.parent == Path(sp.output_dir)
    assert chemin.resolve().parent == Path(sp.output_dir).resolve()
    assert chemin.name.endswith("_mcp.py") and "/" not in chemin.name and "\x00" not in chemin.name and not chemin.name.startswith(".")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["spawned_agents"]      # rien d'écrit ailleurs
