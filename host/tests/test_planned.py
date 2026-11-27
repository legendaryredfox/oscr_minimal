# SPDX-License-Identifier: GPL-3.0-or-later
"""Os marcadores de lugar dos outros cartuchos do OSCR: mesma lista no host e na GUI, e nenhum conflita com um sistema real."""
import json
import re
from pathlib import Path

from oscr_host import protocol as P
from oscr_host.cli import main
from oscr_host.planned import PLANNED

KT = Path(__file__).resolve().parents[2] / "gui/shared/src/commonMain/kotlin/oscr/PlannedSystems.kt"


def test_mesma_lista_na_gui():
    kt = re.findall(r'PlannedSystem\("([^"]+)", "([^"]+)"(?:, true)?\)', KT.read_text(encoding="utf-8"))
    assert kt == [tuple(p) for p in PLANNED]


def test_sem_conflito_e_sem_duplicata():
    keys = [k for k, _ in PLANNED]
    assert len(keys) == len(set(keys)) and not set(keys) & set(P.SYSTEMS)


def test_systems_lista_os_planejados(capsys):
    assert main(["--json", "systems"]) == 0
    o = json.loads(capsys.readouterr().out)
    assert {r["name"] for r in o["systems"]} == set(P.SYSTEMS)
    assert [p["name"] for p in o["planned"]] == [k for k, _ in PLANNED] and not any(p["supported"] for p in o["planned"])


def test_adaptadores_de_3v3_marcados(capsys):
    """H-4 (P-16): os adaptadores de 3,3 V da comunidade aparecem marcados no `systems`, na tabela, no host e na GUI (tools/check_adaptadores.py)."""
    import subprocess
    import sys

    from oscr_host.planned import NEEDS_3V3
    r = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "check_adaptadores.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert main(["--json", "systems"]) == 0
    o = json.loads(capsys.readouterr().out)
    assert {p["name"] for p in o["planned"] if p["voltage"] == "3v3"} == set(NEEDS_3V3) == {"leapster", "jammerpro", "vsmile"}
    assert main(["--lang", "pt-BR", "systems"]) == 0
    out = capsys.readouterr().out
    assert "leapster" in out and "[3,3 V]" in out and "não pode ir num slot de 5 V" in out
