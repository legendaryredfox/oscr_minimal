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
    kt = re.findall(r'PlannedSystem\("([^"]+)", "([^"]+)"\)', KT.read_text(encoding="utf-8"))
    assert kt == [tuple(p) for p in PLANNED]


def test_sem_conflito_e_sem_duplicata():
    keys = [k for k, _ in PLANNED]
    assert len(keys) == len(set(keys)) and not set(keys) & set(P.SYSTEMS)


def test_systems_lista_os_planejados(capsys):
    assert main(["--json", "systems"]) == 0
    o = json.loads(capsys.readouterr().out)
    assert {r["name"] for r in o["systems"]} == set(P.SYSTEMS)
    assert [p["name"] for p in o["planned"]] == [k for k, _ in PLANNED] and not any(p["supported"] for p in o["planned"])
