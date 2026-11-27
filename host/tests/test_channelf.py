# SPDX-License-Identifier: GPL-3.0-or-later
"""Fairchild Channel F (F-20, D224): sistema 27 no protocolo, na CLI e na lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_chf.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["channelf"] == (27, ".bin")
    assert P.SYSTEM_BY_ID[27] == "channelf"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "channelf" not in {k for k, _ in PLANNED}


def test_opcoes_modo_e_tamanho():
    assert cmd_info.SYSTEM_OPTIONS["channelf"] == ["mapper", "prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "channelf", "--mapper", "1", "--prg", "3"])
    assert a.system == "channelf" and a.prg == 3 and int(str(a.mapper), 0) == 1


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_CHF = 27\b", h)
