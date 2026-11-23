# SPDX-License-Identifier: GPL-3.0-or-later
"""Vectrex (F-20, D205): sistema 14 no protocolo, na CLI e na lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_vec.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["vectrex"] == (14, ".vec")
    assert P.SYSTEM_BY_ID[14] == "vectrex"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "vectrex" not in {k for k, _ in PLANNED}


def test_opcao_so_prg():
    assert cmd_info.SYSTEM_OPTIONS["vectrex"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "vectrex", "--prg", "8"])
    assert a.system == "vectrex" and a.prg == 8


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_VEC = 14\b", h)
