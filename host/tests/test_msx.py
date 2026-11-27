# SPDX-License-Identifier: GPL-3.0-or-later
"""MSX (F-20, D230): sistema 31 no protocolo, na CLI e fora da lista de planejados.
As regras puras do firmware (faixa de cada mapper, tamanhos de ROM e de SRAM) estão em firmware/oscr/pc-tests/test_msx.cpp."""
from __future__ import annotations

import pathlib
import re

import pytest

from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import NEEDS_3V3, PLANNED

ROOT = pathlib.Path(__file__).parents[2]


def test_id_e_extensao():
    assert P.SYSTEMS["msx"] == (31, ".rom")
    assert P.SYSTEM_BY_ID[31] == "msx"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_cabe_na_mascara_de_32_bits():
    assert max(v[0] for k, v in P.SYSTEMS.items() if k != "mock") <= 31


def test_saiu_dos_planejados():
    assert "msx" not in {k for k, _ in PLANNED}
    assert "msx" not in NEEDS_3V3


def test_opcoes():
    assert cmd_info.SYSTEM_OPTIONS["msx"] == ["mapper", "prg", "ram"]


def test_cli_aceita_mapper_rom_e_save():
    a = build_parser().parse_args(["dump", "-s", "msx", "--mapper", "2", "--prg", "256"])
    assert a.system == "msx" and a.mapper == 2 and a.prg == 256
    b = build_parser().parse_args(["save-read", "-s", "msx", "--mapper", "1", "--ram", "8"])
    assert b.system == "msx" and b.mapper == 1 and b.ram == 8


def test_id_igual_ao_do_firmware():
    h = (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_MSX = 31\b", h)


def test_tabela_igual_a_do_oscr_legado():
    """A faixa de cada mapper em MsxCore.h é a `msxmapsize[]` do OSCR legado (o firmware novo a lê do cartão SD)."""
    src = ROOT / "vendor/oscr/legacy/Cart_Reader/MSX.ino"
    if not src.exists():
        pytest.skip("vendor/oscr fora do git: clone o upstream para conferir")
    ino = src.read_text(errors="replace")
    bloco = ino[ino.index("msxmapsize[] = {"):]
    bloco = bloco[:bloco.index("};")]
    legado = [tuple(int(x) for x in m.groups()) for m in re.finditer(r"^\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),", bloco, re.M)]
    h = (ROOT / "firmware/oscr/include/dumper/MsxCore.h").read_text()
    fork = [(int(m.group(5)), int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
            for m in re.finditer(r"\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\},\s*//\s*(\d+)", h)]
    assert len(legado) == 15 and fork == legado
