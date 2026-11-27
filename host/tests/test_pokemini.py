# SPDX-License-Identifier: GPL-3.0-or-later
"""Pokémon Mini (F-20, D227): sistema 29 no protocolo, na CLI e fora da lista de planejados (e da de 3,3 V dos planejados).
As regras puras do firmware estão em firmware/oscr/pc-tests/test_pkm.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import NEEDS_3V3, PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["pokemini"] == (29, ".min")
    assert P.SYSTEM_BY_ID[29] == "pokemini"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "pokemini" not in {k for k, _ in PLANNED}
    assert "pokemini" not in NEEDS_3V3


def test_sem_opcoes():
    assert cmd_info.SYSTEM_OPTIONS["pokemini"] == []


def test_cli_aceita_sistema():
    a = build_parser().parse_args(["dump", "-s", "pokemini"])
    assert a.system == "pokemini"


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_POKE = 29\b", h)
