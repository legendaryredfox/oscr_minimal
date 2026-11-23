# SPDX-License-Identifier: GPL-3.0-or-later
"""Neo Geo Pocket (F-20, D202): sistema 13 no protocolo, na CLI e na lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_ngp.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["ngp"] == (13, ".ngp")
    assert P.SYSTEM_BY_ID[13] == "ngp"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "ngp" not in {k for k, _ in PLANNED}


def test_opcao_so_prg():
    assert cmd_info.SYSTEM_OPTIONS["ngp"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "ngp", "--prg", "2048"])
    assert a.system == "ngp" and a.prg == 2048


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_NGP = 13\b", h)
