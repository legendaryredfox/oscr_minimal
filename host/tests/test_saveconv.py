# SPDX-License-Identifier: GPL-3.0-or-later
"""save-convert (H-1, D163): operações de ordem de bytes com vetores fixos e o comando da CLI."""
import json

import pytest

from oscr_host import cli
from oscr_host import saveconv as SC


def test_swap16_e_swap32_vetores():
    assert SC.convert(bytes([1, 2, 3, 4, 5, 6]), "swap16") == bytes([2, 1, 4, 3, 6, 5])
    assert SC.convert(bytes(range(8)), "swap32") == bytes([3, 2, 1, 0, 7, 6, 5, 4])
    assert SC.convert(b"", "swap32") == b""


def test_swap_e_involucao():
    d = bytes(range(256))
    for op in ("swap16", "swap32"):
        assert SC.convert(SC.convert(d, op), op) == d


def test_swap_tamanho_invalido():
    with pytest.raises(ValueError):
        SC.convert(b"abc", "swap16")
    with pytest.raises(ValueError):
        SC.convert(b"abcdef", "swap32")


def test_md_expand_odd_even_e_fill():
    assert SC.convert(b"\x11\x22", "md-expand-odd") == bytes([0xFF, 0x11, 0xFF, 0x22])
    assert SC.convert(b"\x11\x22", "md-expand-even") == bytes([0x11, 0xFF, 0x22, 0xFF])
    assert SC.convert(b"\x11", "md-expand-odd", fill=0) == bytes([0, 0x11])


def test_md_compact_inverso_do_expand():
    d = bytes(range(1, 65))
    for op_e, op_c in (("md-expand-odd", "md-compact-odd"), ("md-expand-even", "md-compact-even")):
        assert SC.convert(SC.convert(d, op_e), op_c) == d
    assert SC.convert(bytes([1, 2, 3, 4]), "md-compact-odd") == bytes([2, 4])
    assert SC.convert(bytes([1, 2, 3, 4]), "md-compact-even") == bytes([1, 3])
    with pytest.raises(ValueError):
        SC.convert(b"abc", "md-compact-odd")


def test_op_desconhecida():
    with pytest.raises(ValueError):
        SC.convert(b"ab", "xyz")


def test_comando(tmp_path, capsys):
    src = tmp_path / "jogo.sav"
    src.write_bytes(bytes([1, 2, 3, 4]))
    assert cli.main(["--json", "save-convert", "-i", str(src), "--op", "swap16"]) == 0
    o = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert o["output"] == str(tmp_path / "jogo_swap16.sav") and o["out_bytes"] == 4
    assert (tmp_path / "jogo_swap16.sav").read_bytes() == bytes([2, 1, 4, 3])
    dst = tmp_path / "x.srm"
    assert cli.main(["--json", "save-convert", "-i", str(src), "-o", str(dst), "--op", "md-expand-odd", "--fill", "0x00"]) == 0
    assert dst.read_bytes() == bytes([0, 1, 0, 2, 0, 3, 0, 4])
    src.write_bytes(b"abc")
    assert cli.main(["--json", "save-convert", "-i", str(src), "--op", "swap16"]) == 1
    assert cli.main(["--json", "save-convert", "-i", str(src), "--op", "md-expand-odd", "--fill", "300"]) == 64
