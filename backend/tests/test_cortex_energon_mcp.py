"""cortex-energon MCP : les outils qui AGISSENT (shell, énergie) sont désactivés par défaut ; les chemins visent ADAM."""

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "spawned_agents"))
import cortex_energon_mcp as cem  # noqa: E402
import cortex_injector  # noqa: E402

FLAG = "CORTEX_MCP_ECRITURE"


def outil(nom):
    o = getattr(cem, nom)
    return getattr(o, "fn", o)


@pytest.fixture(autouse=True)
def sans_flag(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)


class Interdit:
    def __init__(self):
        self.appels = 0

    def __call__(self, *a, **k):
        self.appels += 1
        raise AssertionError("ne devait jamais être appelé")


# ── chemins ─────────────────────────────────────────────────────────────────
def test_chemins_visent_adam():
    assert cem.ADAM_ROOT.name == "ADAM" and cem.ADAM_ROOT.is_dir()
    assert cem.LEDGER_PATH.exists() and cem.HANDS_STATUS.exists()
    assert cortex_injector.CortexInjector().adam_root == cem.ADAM_ROOT


def test_hands_status_se_lit():
    assert "error" not in outil("hands_status")()


# ── inject_command ──────────────────────────────────────────────────────────
def test_inject_command_desactive_par_defaut_et_n_execute_rien(tmp_path, monkeypatch):
    marque = tmp_path / "MARQUE"
    interdit = Interdit()
    monkeypatch.setattr(cem.injector, "inject_command", interdit)
    r = outil("inject_command")(f"touch {marque}")
    assert interdit.appels == 0 and not marque.exists()
    assert r["returncode"] == -1 and "désactiv" in r["error"] and FLAG in r["error"]


@pytest.mark.parametrize("valeur", ["", "0", "true", "yes", "oui", "01", " 1", "1 ", "2"])
def test_seul_un_1_exact_active(valeur, monkeypatch):
    monkeypatch.setenv(FLAG, valeur)
    interdit = Interdit()
    monkeypatch.setattr(cem.injector, "inject_command", interdit)
    r = outil("inject_command")("echo salut")
    assert interdit.appels == 0 and "error" in r


def test_inject_command_actif_avec_le_flag(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    r = outil("inject_command")("echo salut")
    assert r["stdout"].strip() == "salut" and r["returncode"] == 0 and "error" not in r


# ── send_energy ─────────────────────────────────────────────────────────────
def test_send_energy_desactive_par_defaut(monkeypatch):
    interdit = Interdit()
    monkeypatch.setattr(cem, "_post", interdit)
    r = outil("send_energy")(50.0)
    assert interdit.appels == 0 and r["sent"] is False and FLAG in r["error"]


def test_send_energy_actif_avec_le_flag(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    vus = []
    monkeypatch.setattr(cem, "_post", lambda url, payload, timeout=5: vus.append((url, payload)) or {"ok": True, "data": {"x": 1}})
    r = outil("send_energy")(12.5, "w1")
    assert r["sent"] is True and vus[0][1]["egn_generated"] == 12.5 and vus[0][1]["worker_id"] == "w1"
