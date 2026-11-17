# SPDX-License-Identifier: GPL-3.0-or-later
"""Acessórios do SNES (F-10, D178): Sufami Turbo (dump e detect), Game Processor RAM Cassette (save-read e save-write) e ram-test."""
import json
import re
import types
import zlib
from pathlib import Path

import pytest

from oscr_host import protocol as P

HEADER = Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "include" / "dumper" / "SnesAcc.h"


def test_codigos_batem_com_o_firmware():
    h = HEADER.read_text()
    for name, key in (("kSufamiA", "sufami-a"), ("kSufamiB", "sufami-b"), ("kGpc", "gpc")):
        assert int(re.search(rf"{name} = (0x[0-9A-Fa-f]+)", h).group(1), 16) == P.SNES_ACCESSORIES[key]
    assert int(re.search(r"kGpcBytes = (0x[0-9A-Fa-f]+)", h).group(1), 16) == P.GPC_BYTES
    for name, key in (("kBsxPack", "bsx-pack"), ("kBsxSram", "bsx-sram"), ("kSfmFlash", "sfm-flash"), ("kSfmMap", "sfm-map")):      # F-11 (D187)
        assert int(re.search(rf"{name} = (0x[0-9A-Fa-f]+)", h).group(1), 16) == P.SNES_ACCESSORIES[key]
    assert int(re.search(r"kSfmGame = (0x[0-9A-Fa-f]+)", h).group(1), 16) == P.SNES_ACCESSORIES["sfm-game-0"] and P.SNES_ACCESSORIES["sfm-game-6"] == 0x8016
    assert int(re.search(r"kBsxSramBytes = (0x[0-9A-Fa-f]+)", h).group(1), 16) == P.SNES_SAVE_ACCESSORIES["bsx-sram"]
    assert all(v >= 0x8000 for v in P.SNES_ACCESSORIES.values()) and not set(P.SNES_ACCESSORIES.values()) & set(P.SNES_TYPES.values())


class _Res:
    def __init__(self, data):
        self.data, self.crc32 = data, zlib.crc32(data)


class _T:
    def close(self):
        pass


class Fake:
    """Cliente falso: guarda as chamadas; o 'save' é o que o ram-test deve restaurar."""
    def __init__(self, save=b"\x5a" * 8192, rom=b"\x01" * 4096, fail_erase_at=None):
        self.save, self.rom, self.calls, self.fail_erase_at, self.erases = save, rom, [], fail_erase_at, 0

    def detect(self, system, chip=0, prg=0, chr_=0):
        self.calls.append(("detect", system, chr_))
        return {"system": system, "status": 0, "rom_size": 524288, "save_size": 0, "save_type": 0, "name": "SUFAMI MINI"}

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.calls.append(("dump", system, chr_))
        return _Res(self.rom)

    def read_save(self, system, block, progress, mapper=0, ram=0, snes_type=0):
        self.calls.append(("read_save", system, snes_type))
        return _Res(self.save)

    def write_save(self, system, data, block, progress, mapper=0, ram=0, snes_type=0):
        self.calls.append(("write_save", system, snes_type, len(data)))
        self.save = data
        return zlib.crc32(data)

    def erase(self, system, chip, prg, chr_, timeout=90.0):
        self.calls.append(("erase", system, chip))
        self.erases += 1
        self.save = bytes([chip]) * len(self.save)
        if self.fail_erase_at == self.erases:
            raise P.DeviceError(7, "falha") if hasattr(P, "DeviceError") else RuntimeError("falha")


def _cli(monkeypatch, capsys, fake, *argv):
    from oscr_host import cli
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _T(), {"write_rom": False, "flash_prog": True}))
    code = cli.main(["--json", *argv])
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1])


def test_dump_sufami_manda_o_codigo_e_grava_st(monkeypatch, capsys, tmp_path):
    f = Fake()
    code, o = _cli(monkeypatch, capsys, f, "dump", "-s", "snes", "--accessory", "sufami-b", "-o", str(tmp_path / "jogo"))
    assert code == 0 and o["file"].endswith(".st") and ("dump", 1, 0x8002) in f.calls and o["checksum"] == "na"
    code, o = _cli(monkeypatch, capsys, Fake(), "detect", "-s", "snes", "--accessory", "sufami-a")
    assert code == 0 and o["name"] == "SUFAMI MINI"


def test_save_gpc_le_e_grava_512_kb(monkeypatch, capsys, tmp_path):
    gpc = bytes(range(256)) * 2048
    f = Fake(save=gpc)
    code, o = _cli(monkeypatch, capsys, f, "save-read", "-s", "snes", "--accessory", "gpc", "-o", str(tmp_path / "ram"))
    assert code == 0 and o["file"].endswith(".bin") and o["bytes"] == 512 * 1024 and ("read_save", 1, 0x8003) in f.calls
    src = tmp_path / "gpc.bin"
    src.write_bytes(gpc)
    f = Fake(save=bytes(512 * 1024))
    code, o = _cli(monkeypatch, capsys, f, "save-write", "-s", "snes", "--accessory", "gpc", "-i", str(src), "--backup-dir", str(tmp_path / "bk"), "--yes")
    assert code == 0 and o["verify"]["ok"] and ("write_save", 1, 0x8003, 512 * 1024) in f.calls and len(list((tmp_path / "bk").glob("snes_*.sav"))) == 1


def test_acessorio_recusas(monkeypatch, capsys, tmp_path):
    f = Fake()
    bad = tmp_path / "x.bin"
    bad.write_bytes(bytes(1000))
    cases = [("dump", "-s", "snes", "--accessory", "gpc"), ("detect", "-s", "snes", "--accessory", "gpc"), ("save-read", "-s", "snes", "--accessory", "sufami-a"),
             ("dump", "-s", "md", "--accessory", "sufami-a"), ("dump", "-s", "snes", "--accessory", "sufami-a", "--type", "lorom"),
             ("save-write", "-s", "snes", "--accessory", "gpc", "-i", str(bad), "--yes")]
    for argv in cases:
        code, o = _cli(monkeypatch, capsys, f, *argv, *(["-o", str(tmp_path / "o")] if argv[0] in ("dump", "save-read") else []))
        assert code == 64, argv
    assert not f.calls


def test_ram_test_faz_backup_preenche_e_restaura(monkeypatch, capsys, tmp_path):
    orig = bytes((i * 3) & 0xFF for i in range(8192))
    f = Fake(save=orig)
    code, o = _cli(monkeypatch, capsys, f, "ram-test", "--backup-dir", str(tmp_path / "bk"), "--yes")
    assert code == 0 and o["ok"] and o["patterns"] == [0x0F, 0xF0] and o["verify"]["ok"]
    assert [c[0] for c in f.calls] == ["read_save", "erase", "erase", "write_save", "read_save"]
    assert [c[2] for c in f.calls if c[0] == "erase"] == [0x0F, 0xF0] and f.save == orig
    assert Path(o["backup"]).read_bytes() == orig


def test_ram_test_restaura_mesmo_se_o_preenchimento_falha(monkeypatch, capsys, tmp_path):
    orig = bytes(range(256)) * 32
    f = Fake(save=orig, fail_erase_at=2)
    code, o = _cli(monkeypatch, capsys, f, "ram-test", "--backup-dir", str(tmp_path / "bk"), "--yes")
    assert code != 0 and f.save == orig and "write_save" in [c[0] for c in f.calls]       # a SRAM voltou ao que era, e o erro apareceu


def test_ram_test_recusas(monkeypatch, capsys, tmp_path):
    f = Fake()
    code, o = _cli(monkeypatch, capsys, f, "ram-test", "-s", "md", "--yes")
    assert code == 64 and not f.calls
    code, o = _cli(monkeypatch, capsys, f, "ram-test")                  # sem --yes e sem terminal: recusa sem tocar no cartucho
    assert code != 0 and not f.calls


def test_bsx_e_sfm_f11(monkeypatch, capsys, tmp_path):
    f = Fake(rom=b"\x02" * 4096)
    code, o = _cli(monkeypatch, capsys, f, "dump", "-s", "snes", "--accessory", "bsx-pack", "-o", str(tmp_path / "pack"))
    assert code == 0 and o["file"].endswith(".bs") and ("dump", 1, 0x8004) in f.calls
    code, o = _cli(monkeypatch, capsys, f, "dump", "-s", "snes", "--accessory", "sfm-game-3", "-o", str(tmp_path / "g"))
    assert code == 0 and o["file"].endswith(".sfc") and ("dump", 1, 0x8013) in f.calls
    code, o = _cli(monkeypatch, capsys, f, "dump", "-s", "snes", "--accessory", "sfm-flash", "-o", str(tmp_path / "fl"))
    assert code == 0 and o["file"].endswith(".bin") and ("dump", 1, 0x8006) in f.calls
    sram = bytes(range(256)) * 128
    f = Fake(save=sram)
    code, o = _cli(monkeypatch, capsys, f, "save-read", "-s", "snes", "--accessory", "bsx-sram", "-o", str(tmp_path / "bsx"))
    assert code == 0 and o["bytes"] == 32768 and ("read_save", 1, 0x8005) in f.calls
    src = tmp_path / "bsx.bin"
    src.write_bytes(sram)
    f = Fake(save=bytes(32768))
    code, o = _cli(monkeypatch, capsys, f, "save-write", "-s", "snes", "--accessory", "bsx-sram", "-i", str(src), "--backup-dir", str(tmp_path / "bk"), "--yes")
    assert code == 0 and ("write_save", 1, 0x8005, 32768) in f.calls
    bad = tmp_path / "g512.bin"
    bad.write_bytes(bytes(512 * 1024))
    g = Fake()
    for argv in (("save-write", "-s", "snes", "--accessory", "bsx-sram", "-i", str(bad), "--yes"), ("save-read", "-s", "snes", "--accessory", "bsx-pack"),
                 ("dump", "-s", "snes", "--accessory", "bsx-sram"), ("save-write", "-s", "snes", "--accessory", "sfm-flash", "-i", str(src), "--yes")):
        code, o = _cli(monkeypatch, capsys, g, *argv)
        assert code == 64, argv
    assert not g.calls
