# SPDX-License-Identifier: GPL-3.0-or-later
"""TRS-80 Color Computer (F-20, D248): sistema 32 no protocolo, na CLI e fora da lista de planejados.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_trs.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import NEEDS_3V3, PLANNED

ROOT = pathlib.Path(__file__).parents[2]


def test_id_e_extensao():
    assert P.SYSTEMS["trs80"] == (32, ".ccc")
    assert P.SYSTEM_BY_ID[32] == "trs80"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "trs80" not in {k for k, _ in PLANNED}
    assert "trs80" not in NEEDS_3V3


def test_opcao_de_tamanho():
    assert cmd_info.SYSTEM_OPTIONS["trs80"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "trs80", "--prg", "16"])
    assert a.system == "trs80" and a.prg == 16


def test_id_igual_ao_do_firmware():
    h = (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_TRS80 = 32\b", h)


def test_tamanhos_iguais_aos_do_nucleo():
    """A tabela de TrsCore.h é a `romSizes` do núcleo TRS80.cpp do OSCR, na mesma ordem (o índice vai para `romSize`)."""
    core = (ROOT / "firmware/oscr/src/cores/TRS80.cpp").read_text()
    bloco = core[core.index("romSizes[] = {"):]
    nucleo = [int(x) for x in re.findall(r"\d+", bloco[:bloco.index("};")])]
    h = (ROOT / "firmware/oscr/include/dumper/TrsCore.h").read_text()
    assert nucleo == [2, 4, 8, 10, 16, 32, 64, 128]
    assert "{ 2, 4, 8, 10, 16, 32, 64, 128 }" in h
