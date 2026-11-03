# SPDX-License-Identifier: GPL-3.0-or-later
"""WRITE_ROM no host: preparo do arquivo (iNES, chip), comando rom-write com o simulador, erros estruturados."""
import json

import pytest

from oscr_host import protocol as P
from oscr_host import romimage as RI
from oscr_host.cli import main


def ines(prg_kb: int, chr_kb: int, mapper: int, trainer: bool = False) -> bytes:
    hdr = bytes([0x4E, 0x45, 0x53, 0x1A, prg_kb // 16, chr_kb // 8, ((mapper & 0xF) << 4) | (4 if trainer else 0), mapper & 0xF0]) + bytes(8)
    return hdr + bytes((i * 7) & 0xFF for i in range((prg_kb + chr_kb) * 1024))


def run(capsys, *argv):
    code = main(list(argv))
    return code, capsys.readouterr().out


def test_split_image_ines():
    img = RI.split_image(ines(32, 8, 0), "a29040b")
    assert (img.prg_kb, img.chr_kb, img.mapper, len(img.body)) == (32, 8, 0, 40 * 1024)
    assert RI.infer_chip(img) == "a29040b" and RI.infer_chip(RI.split_image(ines(512, 0, 30), "nesmaker")) == "nesmaker"
    assert RI.infer_chip(RI.split_image(ines(32, 8, 4), "nesmaker")) is None


def test_split_image_erros():
    with pytest.raises(ValueError):
        RI.split_image(ines(32, 0, 30, trainer=True), "nesmaker")
    with pytest.raises(ValueError):
        RI.split_image(ines(32, 0, 30)[:-1], "nesmaker")            # cabeçalho diz 32 KB, falta um byte
    with pytest.raises(ValueError):
        RI.split_image(bytes(16384), "a29040b")                      # A29040B exige cabeçalho
    with pytest.raises(ValueError):
        RI.split_image(bytes(1000), "nesmaker")                      # cru: múltiplo de 16 KB
    assert RI.split_image(bytes(32768), "nesmaker").prg_kb == 32


def test_build_write_rom():
    assert P.build_write_rom(2, 40960, 512, 2, 32, 8) == bytes([2]) + (40960).to_bytes(4, "little") + (512).to_bytes(2, "little") + bytes([2, 0, 32, 0, 8, 0])


def test_rom_write_simulado(tmp_path, capsys):
    f = tmp_path / "jogo.nes"
    f.write_bytes(ines(32, 8, 0))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["chip"] == "a29040b" and (o["prg_kb"], o["chr_kb"], o["bytes"]) == (32, 8, 40 * 1024)


def test_rom_write_recusa_sem_yes(tmp_path, capsys, monkeypatch):
    f = tmp_path / "jogo.nes"
    f.write_bytes(ines(32, 8, 0))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f))
    assert code == 4 and json.loads(out)["error"]["kind"] == "refused"


def test_rom_write_erros_de_uso(tmp_path, capsys):
    f = tmp_path / "x.nes"
    f.write_bytes(ines(32, 8, 4))                                    # mapper 4: não dá para saber o chip
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--yes")
    assert code == 64 and json.loads(out)["error"]["kind"] == "usage"
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "snes", "-i", str(f), "--yes")
    assert code == 64
    g = tmp_path / "ruim.nes"
    g.write_bytes(ines(32, 0, 30)[:-5])
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(g), "--yes")
    assert code == 64 and json.loads(out)["error"]["kind"] == "bad_rom"


def test_chip_nao_reconhecido_vira_erro_do_dispositivo(capsys, tmp_path):
    from oscr_host import sim
    from oscr_host.client import Client

    t, _dev, _stop, _th = sim.start()
    c = Client(t, timeout=0.5)
    with pytest.raises(P.DeviceError) as e:
        c.write_rom(255, bytes(16384), chip=9, prg_kb=16, chr_kb=0)
    assert e.value.code == 11 and "flash" in str(e.value)
    t.close()


def test_info_do_simulador_anuncia_write_rom():
    from oscr_host import sim
    from oscr_host.client import Client

    t, _dev, _stop, _th = sim.start()
    assert Client(t, timeout=0.5).info()["write_rom"] is True
    t.close()
