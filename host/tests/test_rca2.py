# SPDX-License-Identifier: GPL-3.0-or-later
"""RCA Studio II (F-20, D216): sistema 22 no protocolo, na CLI e na lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_rca.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["rca2"] == (22, ".bin")
    assert P.SYSTEM_BY_ID[22] == "rca2"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "rca2" not in {k for k, _ in PLANNED}


def test_opcao_so_prg():
    assert cmd_info.SYSTEM_OPTIONS["rca2"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "rca2", "--prg", "1"])
    assert a.system == "rca2" and a.prg == 1


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_RCA2 = 22\b", h)
