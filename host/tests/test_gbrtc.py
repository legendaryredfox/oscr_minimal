# SPDX-License-Identifier: GPL-3.0-or-later
"""RTC do MBC3 do Game Boy (F-17, D192): bytes, rodapé de 48 bytes, código do firmware e o comando gb-rtc com um cliente falso."""
import json
import re
import zlib
from pathlib import Path

import pytest

from oscr_host import gbrtc as R
from oscr_host import protocol as P
from oscr_host.cli import main
from oscr_host.cli import common

FW = Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "include" / "dumper"


def test_codigo_do_firmware_bate():
    assert int(re.search(r"kRtc = (\d+)", (FW / "GbAcc.h").read_text()).group(1)) == 7
    assert int(re.search(r"kRegs = (\d+)", (FW / "GbRtc.h").read_text()).group(1)) == R.REGS


def test_codifica_e_decodifica():
    raw = R.encode(5, 4, 3, 300, True, True)
    assert raw == bytes([5, 4, 3, 300 & 0xFF, 0x01 | 0x40 | 0x80])
    assert R.decode(raw) == {"seconds": 5, "minutes": 4, "hours": 3, "days": 300, "halted": True, "carry": True}
    assert R.decode(bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFE]))["days"] == 255                   # bits que o MBC3 não usa são ignorados
    for bad in ((60, 0, 0, 0), (0, 60, 0, 0), (0, 0, 24, 0), (0, 0, 0, 512)):
        with pytest.raises(R.RtcError):
            R.encode(*bad)
    with pytest.raises(R.RtcError):
        R.decode(b"\x00" * 4)


def test_hora_e_rodape():
    assert R.parse_time("07:05") == (7, 5, 0) and R.parse_time("23:59:58") == (23, 59, 58)
    for bad in ("24:00", "12:60", "12", "ab:cd", "1:2:3:4"):
        with pytest.raises(R.RtcError):
            R.parse_time(bad)
    raw = R.encode(1, 2, 3, 4)
    f = R.footer(raw, 1_700_000_000)
    assert len(f) == 48 and f[:20] == f[20:40] and f[:4] == b"\x01\x00\x00\x00" and int.from_bytes(f[40:], "little") == 1_700_000_000
    assert R.from_footer(f) == raw and R.from_footer(raw) == raw
    with pytest.raises(R.RtcError):
        R.from_footer(b"\x00" * 7)


class _Res:
    def __init__(self, data):
        self.data, self.crc32 = data, zlib.crc32(data)


class _T:
    def close(self):
        pass


class Fake:
    """Relógio falso: dump_rom (mapper 7) devolve os 5 bytes; write_save (mapper 7) guarda."""
    def __init__(self, raw=bytes([10, 20, 5, 7, 0]), no_rtc=False, drift=0):
        self.raw, self.no_rtc, self.drift, self.calls = raw, no_rtc, drift, []

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.calls.append(("dump", system, mapper))
        if self.no_rtc:
            raise P.DeviceError(10)
        return _Res(self.raw)

    def write_save(self, system, data, block, progress, mapper=0, ram=0, snes_type=0):
        self.calls.append(("write", system, mapper, bytes(data)))
        d = R.decode(data)
        self.raw = R.encode(min(59, d["seconds"] + self.drift), d["minutes"], d["hours"], d["days"], d["halted"], d["carry"])
        return zlib.crc32(data)


def _run(monkeypatch, capsys, fake, *argv):
    monkeypatch.setattr(common, "connect", lambda a, need_cart=True: (fake, _T(), {}))
    code = main(["--json", "gb-rtc", *argv])
    return code, json.loads(capsys.readouterr().out)


def test_so_le(monkeypatch, capsys, tmp_path):
    f = Fake()
    out = tmp_path / "rtc.bin"
    code, j = _run(monkeypatch, capsys, f, "-o", str(out))
    assert code == 0 and j["written"] is None and j["before"]["days"] == 7 and j["before"]["raw"] == "0a14050700"
    assert [c[0] for c in f.calls] == ["dump"] and f.calls[0][1:] == (P.SYSTEMS["gb"][0], 7)
    assert len(out.read_bytes()) == 48


def test_grava_hora_e_dia_e_confere(monkeypatch, capsys):
    f = Fake()
    code, j = _run(monkeypatch, capsys, f, "--set", "12:34:56", "--day", "100", "--halt")
    assert code == 0 and j["verified"] is True
    assert f.calls[1] == ("write", P.SYSTEMS["gb"][0], 7, bytes([56, 34, 12, 100, 0x40]))
    assert j["written"]["raw"] == "38220c6440"


def test_mantem_o_que_nao_foi_pedido(monkeypatch, capsys):
    f = Fake(raw=bytes([1, 2, 3, 4, 0x80 | 0x01]))                 # dia 260, estouro, andando
    code, j = _run(monkeypatch, capsys, f, "--day", "5")
    assert code == 0 and f.calls[1][3] == bytes([1, 2, 3, 5, 0x80])
    f2 = Fake(raw=bytes([1, 2, 3, 4, 0x80]))
    _run(monkeypatch, capsys, f2, "--clear-carry")
    assert f2.calls[1][3] == bytes([1, 2, 3, 4, 0])


def test_acerta_com_a_hora_do_pc(monkeypatch, capsys):
    f = Fake()
    code, j = _run(monkeypatch, capsys, f, "--now")
    w = f.calls[1][3]
    assert code == 0 and R.decode(w)["days"] == 7 and not R.decode(w)["halted"]


def test_conferencia_falha_se_o_cartucho_devolve_outro_valor(monkeypatch, capsys):
    f = Fake(drift=9)
    code, j = _run(monkeypatch, capsys, f, "--set", "01:00:00")
    assert code == 1 and j["verified"] is False


def test_sem_rtc_e_erros_de_uso(monkeypatch, capsys):
    code, out = _run(monkeypatch, capsys, Fake(no_rtc=True))
    assert code == 1 and out["error"]["kind"] == "no_rtc"
    for argv in (["--now", "--set", "10:00"], ["--set", "99:00"], ["--day", "512"], ["--halt", "--run"]):
        code, out = _run(monkeypatch, capsys, Fake(), *argv)
        assert code == 64 and out["error"]["kind"] == "usage"
