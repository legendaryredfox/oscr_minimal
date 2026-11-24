# SPDX-License-Identifier: GPL-3.0-or-later
"""Emerson Arcadia 2001 (F-20, D215): sistema 21 no protocolo, na CLI e na lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_arc.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["arcadia"] == (21, ".bin")
    assert P.SYSTEM_BY_ID[21] == "arcadia"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "arcadia" not in {k for k, _ in PLANNED}


def test_opcao_so_prg():
    assert cmd_info.SYSTEM_OPTIONS["arcadia"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "arcadia", "--prg", "4"])
    assert a.system == "arcadia" and a.prg == 4


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_ARC = 21\b", h)
