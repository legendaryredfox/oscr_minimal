# SPDX-License-Identifier: GPL-3.0-or-later
"""GBA 369-in-1, leitura (F-18, D174): regras iguais às do firmware e o `dump --block369` com um cliente falso."""
import json
import re
import zlib
from pathlib import Path

import pytest

from oscr_host import gba369 as G
from oscr_host import protocol as P

HEADER = Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "include" / "dumper" / "Gba369.h"


def test_constantes_batem_com_o_firmware():
    h = HEADER.read_text()
    assert int(re.search(r"kFlag = (0x[0-9A-Fa-f]+)", h).group(1), 16) == G.FLAG
    assert int(re.search(r"kBankMb = (\d+)", h).group(1)) == G.BANK_MB
    assert int(re.search(r"kTotalMb = (\d+)", h).group(1)) == G.TOTAL_MB


def test_codigo_e_regras():
    assert G.code(0) == 0x8000 and G.code(63) == 0xBF00
    ok = [(0, 0), (0, 32), (8, 32), (7, 4), (63, 4), (2, 1), (2, 3), (0, 8)]
    ruim = [(1, 0), (1, 32), (7, 8), (63, 8), (2, 5), (2, 6), (0, 33), (64, 4), (-1, 4)]
    assert all(G.error(b, m) is None for b, m in ok)
    assert all(G.error(b, m) for b, m in ruim)
    assert G.nbytes(0) == 256 << 20 and G.nbytes(32) == 32 << 20


def test_o_cliente_aceita_256_mb():
    assert P.MAX_STREAM_BYTES >= 256 << 20


class _Res:
    def __init__(self, data):
        self.data, self.crc32 = data, zlib.crc32(data)


class _Fake:
    def __init__(self):
        self.calls = []

    def detect(self, system, *a):
        return {"system": system, "status": 0, "rom_size": 0, "save_size": 0, "save_type": 0, "name": "369IN1"}

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.calls.append((system, mapper, prg))
        return _Res(bytes(range(256)) * 16)


class _T:
    def close(self):
        pass


def _cli(monkeypatch, capsys, *argv):
    from oscr_host import cli
    f = _Fake()
    monkeypatch.setattr(cli.common, "connect", lambda a: (f, _T(), {"write_rom": False, "flash_prog": False}))
    code = cli.main(["--json", *argv])
    return code, json.loads(capsys.readouterr().out.strip().splitlines()[-1]), f


def test_dump_envia_o_codigo_e_o_tamanho_em_mb(monkeypatch, capsys, tmp_path):
    code, o, f = _cli(monkeypatch, capsys, "dump", "-s", "gba", "--block369", "3", "--prg", "4", "-o", str(tmp_path / "j"))
    assert code == 0 and f.calls == [(5, 0x8300, 4)] and o["file"].endswith(".gba")
    assert "gba_save_type" not in o                       # sem dica de save: vários jogos
    code, o, f = _cli(monkeypatch, capsys, "dump", "-s", "gba", "--block369", "0", "-o", str(tmp_path / "k"))
    assert code == 0 and f.calls == [(5, 0x8000, 0)]


def test_dump_recusa_pedido_invalido_sem_falar_com_o_cartucho(monkeypatch, capsys, tmp_path):
    for argv in (("--block369", "1"), ("--block369", "7", "--prg", "8"), ("--block369", "64", "--prg", "4"), ("--block369", "2", "--prg", "6")):
        code, o, f = _cli(monkeypatch, capsys, "dump", "-s", "gba", *argv, "-o", str(tmp_path / "x"))
        assert code == 64 and not f.calls, argv
    code, o, f = _cli(monkeypatch, capsys, "dump", "-s", "snes", "--block369", "0", "-o", str(tmp_path / "x"))
    assert code == 64 and not f.calls


def test_dump_gba_comum_nao_muda(monkeypatch, capsys, tmp_path):
    code, o, f = _cli(monkeypatch, capsys, "dump", "-s", "gba", "-o", str(tmp_path / "j"))
    assert code == 0 and f.calls == [(5, 0, 0)]
