# SPDX-License-Identifier: GPL-3.0-or-later
"""Magnavox Odyssey 2 / Videopac (F-20, D226): sistema 28 no protocolo, na CLI e na lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_ody.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["odyssey2"] == (28, ".bin")
    assert P.SYSTEM_BY_ID[28] == "odyssey2"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "odyssey2" not in {k for k, _ in PLANNED}


def test_opcoes_modo_e_tamanho():
    assert cmd_info.SYSTEM_OPTIONS["odyssey2"] == ["mapper", "prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "odyssey2", "--mapper", "1", "--prg", "4"])
    assert a.system == "odyssey2" and a.prg == 4 and int(str(a.mapper), 0) == 1


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_ODY2 = 28\b", h)
