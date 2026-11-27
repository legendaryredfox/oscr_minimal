# SPDX-License-Identifier: GPL-3.0-or-later
"""V.Smile (F-20, D228): sistema 30 no protocolo, na CLI e fora da lista de planejados (e da de 3,3 V dos planejados).
As regras puras do firmware estão em firmware/oscr/pc-tests/test_vsm.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import NEEDS_3V3, PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["vsmile"] == (30, ".bin")
    assert P.SYSTEM_BY_ID[30] == "vsmile"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "vsmile" not in {k for k, _ in PLANNED}
    assert "vsmile" not in NEEDS_3V3


def test_opcao_de_tamanho():
    assert cmd_info.SYSTEM_OPTIONS["vsmile"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "vsmile", "--prg", "8192"])
    assert a.system == "vsmile" and a.prg == 8192


def test_id_igual_ao_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_VSMILE = 30\b", h)


def test_tamanhos_iguais_aos_do_firmware():
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/include/dumper/VsmCore.h").read_text()
    assert "{ 4096, 6144, 8192, 16384 }" in h
