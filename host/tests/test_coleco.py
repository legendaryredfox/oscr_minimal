# SPDX-License-Identifier: GPL-3.0-or-later
"""ColecoVision (F-20, D201): sistema 12 no protocolo, na CLI e na lista de planejados.
O firmware (núcleo Colecovision.cpp do OSCR) não roda no PC; as regras puras estão em firmware/oscr/pc-tests/test_colv.cpp."""
from __future__ import annotations

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_id_e_extensao():
    assert P.SYSTEMS["coleco"] == (12, ".col")
    assert P.SYSTEM_BY_ID[12] == "coleco"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "coleco" not in {k for k, _ in PLANNED}


def test_opcao_so_prg():
    assert cmd_info.SYSTEM_OPTIONS["coleco"] == ["prg"]


def test_cli_aceita_sistema_e_tamanho():
    a = build_parser().parse_args(["dump", "-s", "coleco", "--prg", "16"])
    assert a.system == "coleco" and a.prg == 16


def test_id_igual_ao_do_firmware():
    import re, pathlib
    h = (pathlib.Path(__file__).parents[2] / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_COLV = 12\b", h)
