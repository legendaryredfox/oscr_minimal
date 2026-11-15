# SPDX-License-Identifier: GPL-3.0-or-later
"""Tipo de ROM do SNES forçado pelo PC (F-2, D164): o tipo vai no 3º campo opcional (`chr_kb`). Mesmos vetores de
firmware/oscr/pc-tests/test_snes_type.cpp e do SnesTypeTest.kt."""
import struct

import pytest

from oscr_host import cli
from oscr_host import protocol as P


def test_codigos():
    assert P.SNES_TYPES == {"lorom": 1, "hirom": 2, "sa1": 3, "exhirom": 4}


def test_bytes_no_fio():
    # DETECT: sistema + (chip, prg_kb, chr_kb); o tipo é o chr_kb
    assert P.build_detect(1, 0, 0, 2) == struct.pack("<BHHH", 1, 0, 0, 2)
    assert P.build_detect(1) == b"\x01"
    # DUMP_ROM: sistema, bloco, mapper, prg_kb, chr_kb
    assert P.build_dump(1, 0, 0, 3072, 4) == struct.pack("<BHHHH", 1, 0, 0, 3072, 4)
    # READ_SAVE usa o mesmo construtor: mapper 0, ram 0, tipo 1
    assert P.build_dump(1, 0, 0, 0, 1) == struct.pack("<BHHHH", 1, 0, 0, 0, 1)
    # WRITE_SAVE: o tipo vai no 3º campo; sem opções nada muda
    assert P.build_write_save(1, 8192, 512, 0, 0, 2) == struct.pack("<BIH", 1, 8192, 512) + struct.pack("<HHH", 0, 0, 2)
    assert P.build_write_save(1, 8192, 512) == struct.pack("<BIH", 1, 8192, 512)
    assert P.build_write_save(2, 8192, 512, 4, 16) == struct.pack("<BIH", 2, 8192, 512) + struct.pack("<HHH", 4, 16, 0)


def test_cli_aceita_tipo_no_snes(capsys):
    # o simulador só tem cartucho MOCK: sem cartucho (2) com ou sem --type; o que importa é a opção ser aceita e chegar ao comando
    for t in P.SNES_TYPES:
        assert cli.main(["--simulate", "--json", "detect", "-s", "snes", "--type", t]) == 2
    capsys.readouterr()


def test_cli_so_no_snes(capsys):
    assert cli.main(["--simulate", "--json", "detect", "-s", "md", "--type", "lorom"]) == 64
    with pytest.raises(SystemExit) as e:
        cli.main(["--simulate", "--json", "detect", "-s", "snes", "--type", "xyz"])
    assert e.value.code == 64
    capsys.readouterr()
