# SPDX-License-Identifier: GPL-3.0-or-later
"""Atari 2600 (F-20, D206): sistema 15, mappers (a mesma tabela no firmware, no Python e no Kotlin), --mapper em hexadecimal."""
from __future__ import annotations

import pathlib
import re

import pytest

from oscr_host import a2600 as A
from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED

ROOT = pathlib.Path(__file__).parents[2]


def test_id_e_extensao():
    assert P.SYSTEMS["a2600"] == (15, ".a26")
    assert P.SYSTEM_BY_ID[15] == "a2600"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "a2600" not in {k for k, _ in PLANNED}


def test_opcao_so_mapper():
    assert cmd_info.SYSTEM_OPTIONS["a2600"] == ["mapper"]


def test_mapper_em_hexadecimal_e_decimal():
    p = build_parser()
    assert p.parse_args(["dump", "-s", "a2600", "--mapper", "0xF8"]).mapper == 0xF8
    assert p.parse_args(["dump", "-s", "a2600", "--mapper", "248"]).mapper == 248
    assert p.parse_args(["dump", "-s", "snes", "--mapper", "07"]).mapper == 7          # zero à esquerda continua decimal
    with pytest.raises(SystemExit):
        p.parse_args(["dump", "-s", "a2600", "--mapper", "0xZZ"])


def test_tamanhos():
    assert A.rom_kb(0x40) == 4 and A.rom_kb(0xF8) == 8 and A.rom_kb(0xBB) == 256
    assert A.rom_kb(0xE7) == A.VARIABLE
    assert A.rom_kb(0x41) is None


def test_tabela_igual_no_firmware_e_no_kotlin():
    h = (ROOT / "firmware/oscr/include/dumper/AtariCore.h").read_text()
    fw = {int(i, 16): (0 if k == "kVariable" else int(k)) for i, k in re.findall(r"\{ (0x[0-9A-Fa-f]{2}), (\w+) \}", h)}
    assert fw == {i: kb for i, (_, kb) in A.MAPPERS.items()}
    kt = (ROOT / "gui/shared/src/commonMain/kotlin/oscr/A2600.kt").read_text()
    kot = {int(i, 16): (n, int(k)) for i, n, k in re.findall(r'Mapper\((0x[0-9A-Fa-f]{2}), "([^"]+)", (\d+)\)', kt)}
    assert kot == {i: (n, kb) for i, (n, kb) in A.MAPPERS.items()}


def test_id_igual_ao_do_firmware():
    h = (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_A26 = 15\b", h)
