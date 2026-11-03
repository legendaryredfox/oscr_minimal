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


# ---- conferência depois de gravar

class FakeClient:
    def __init__(self, data: bytes):
        self.data, self.calls = data, []

    def dump_rom(self, system, block, progress, mapper, prg_kb, chr_kb):
        self.calls.append((system, mapper, prg_kb, chr_kb))
        from types import SimpleNamespace
        return SimpleNamespace(data=self.data)


def test_verify_ok_tira_o_cabecalho_sintetico():
    raw = ines(32, 8, 0)
    img = RI.split_image(raw, "a29040b")
    c = FakeClient(raw)                                   # o firmware devolve cabeçalho iNES + PRG + CHR
    v = RI.verify_written(c, 2, "a29040b", img)
    assert v.ok and v.first_diff is None and c.calls == [(2, 0, 32, 8)]


def test_verify_acha_o_primeiro_byte_diferente():
    raw = ines(512, 0, 30)
    img = RI.split_image(raw, "nesmaker")
    bad = bytearray(raw)
    bad[16 + 1234] ^= 0xFF
    c = FakeClient(bytes(bad))
    v = RI.verify_written(c, 2, "nesmaker", img)
    assert not v.ok and v.first_diff == 1234 and c.calls == [(2, 30, 512, 0)]
    short = RI.verify_written(FakeClient(raw[:-100]), 2, "nesmaker", img)
    assert not short.ok and short.first_diff == len(img.body) - 100


def test_rom_write_no_simulador_pula_a_conferencia(tmp_path, capsys):
    f = tmp_path / "jogo.nes"
    f.write_bytes(ines(32, 8, 0))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--yes")
    assert code == 0 and json.loads(out)["verify"] == "skipped"


# ---------------------------------------------------------------- SNES (flash CFI)
def snes_rom(kb: int, copier: bool = False) -> bytes:
    body = bytes((i * 5 + 3) & 0xFF for i in range(kb * 1024))
    return (bytes(512) if copier else b"") + body


def test_split_snes():
    img = RI.split_snes(snes_rom(1024))
    assert (img.prg_kb, img.flash_kb, img.chr_kb, len(img.body)) == (1024, 2048, 0, 1024 * 1024)
    assert RI.split_snes(snes_rom(3072)).flash_kb == 4096
    assert RI.split_snes(snes_rom(1024), 4096).flash_kb == 4096


def test_split_snes_tira_cabecalho_de_copiadora():
    img = RI.split_snes(snes_rom(512, copier=True))
    assert len(img.body) == 512 * 1024 and img.body == snes_rom(512)


def test_snes_plan_vetores():
    """Os mesmos vetores de firmware/oscr/pc-tests/test_snes_plan.cpp e de RomWriteTest.kt."""
    M = 1 << 20
    assert RI.snes_plan(0, 1 * M, 2 * M) == [(1, 0, M, 0)]
    assert RI.snes_plan(0, 3 * M, 2 * M) == [] and RI.snes_plan(0, M, 3 * M) == [] and RI.snes_plan(0, 1000, 2 * M) == []
    assert RI.snes_plan(1, 1 * M, 0) == [(1, 0, M, 0), (2, 0, 0, 2 * M)]
    assert RI.snes_plan(1, 3 * M, 0) == [(1, 0, 2 * M, 0), (2, 0, M, 2 * M)]
    assert RI.snes_plan(1, 5 * M, 0) == []
    assert RI.snes_plan(2, 8 * M, 0) == [(1, 0, 4 * M, 4 * M), (2, 0, 4 * M, 0)]
    assert RI.snes_plan(2, 6 * M, 0) == [(1, 0, 2 * M, 4 * M), (2, 0, 4 * M, 0)]
    assert RI.snes_plan(2, 4 * M, 0) == []
    assert RI.snes_plan(3, 8 * M, 0) == [(1, 0, 2 * M, 4 * M), (2, 0, 2 * M, 6 * M), (3, 0, 2 * M, 0), (4, 0, 2 * M, 2 * M)]
    assert RI.snes_plan(3, 6 * M, 0) == [(1, 0, 2 * M, 4 * M), (2, 0, 0, 6 * M), (3, 0, 2 * M, 0), (4, 0, 2 * M, 2 * M)]
    assert RI.snes_plan(3, 2 * M, 0) == []
    assert RI.snes_plan(4, 8 * M, 0) == [(1, 0, 4 * M, 4 * M), (1, 4 * M, 4 * M, 0)]
    assert RI.snes_plan(4, 6 * M, 0) == [(1, 0, 2 * M, 4 * M), (1, 4 * M, 4 * M, 0)]
    assert RI.snes_plan(4, 7 * M, 0) == [] and RI.snes_plan(9, M, 0) == []


def test_split_snes_reordena_como_o_oscr():
    M = 1 << 20
    rom = bytes((i // 4096) & 0xFF for i in range(8 * M))            # cada 4 KB tem o número do trecho: dá para ver a troca
    img = RI.split_snes(rom, layout="1x8mb")
    assert (img.layout, img.flash_kb, img.prg_kb) == (4, 8192, 8192) and img.rom == rom
    assert img.body == rom[4 * M:] + rom[:4 * M]                      # metades trocadas
    img = RI.split_snes(rom, layout="4x2mb")
    assert img.body == rom[4 * M:6 * M] + rom[6 * M:] + rom[:2 * M] + rom[2 * M:4 * M]
    img = RI.split_snes(rom[:6 * M], layout="4x2mb")                 # 6 MB: o chip 2 só é apagado
    assert img.body == rom[4 * M:6 * M] + rom[:2 * M] + rom[2 * M:4 * M]
    img = RI.split_snes(rom[:3 * M], layout="2x2mb")
    assert img.body == rom[:3 * M] and img.flash_kb == 4096
    img = RI.split_snes(rom, layout="2x4mb")
    assert img.body == rom[4 * M:] + rom[:4 * M]


def test_chip_code_snes():
    img = RI.split_snes(snes_rom(512), layout="1x")
    assert RI.chip_code("snes-lorom", img) == 0x0001 and RI.chip_code("snes-hirom", img) == 0x0002
    img = RI.split_snes(snes_rom(6144), layout="1x8mb")
    assert RI.chip_code("snes-hirom", img) == 0x0402
    g = RI.split_snes_generic(snes_rom(1024), 4, "29f032")
    assert RI.chip_code("snes-exhirom-p1", g) == 0x1004 and g.flash_kb == 4096 and g.wire_chr == 1
    assert RI.chip_code("nesmaker", img) == 1


def test_split_snes_generic():
    g = RI.split_snes_generic(snes_rom(1000), 4, "29gl", sector_kb=128, buffer=32)
    assert len(g.body) % (128 * 1024) == 0 and g.body[:1000 * 1024] == snes_rom(1000) and set(g.body[1000 * 1024:]) == {0xFF}
    assert g.wire_chr == 7 | (17 << 4) | (5 << 9) and g.rom == snes_rom(1000) and g.layout == 0x10
    assert RI.split_snes_generic(snes_rom(512), 1, "e28fxxxj3a").wire_chr == 8 | (17 << 4) | (5 << 9)      # padrão: 128 KB e 32 bytes
    for kw in ({"flash_type": "29gl"}, {"flash_type": "xx"}, {"flash_type": "29gl", "sector_kb": 100, "buffer": 32},
               {"flash_type": "29gl", "sector_kb": 128, "buffer": 256}, {"flash_type": "29f032", "flash_mb": 9}):
        with pytest.raises(ValueError):
            RI.split_snes_generic(snes_rom(512), **{"flash_mb": 4, **kw})
    with pytest.raises(ValueError):
        RI.split_snes_generic(snes_rom(5120), 4, "29f032")           # 5 MB em flash de 4 MB


def test_split_snes_erros():
    with pytest.raises(ValueError):
        RI.split_snes(bytes(1000))                    # não é múltiplo de 1 KB
    with pytest.raises(ValueError):
        RI.split_snes(snes_rom(6144))                 # 6 MB: precisa de 2 chips, ainda não existe
    with pytest.raises(ValueError):
        RI.split_snes(snes_rom(3072), 2048)           # não cabe
    with pytest.raises(ValueError):
        RI.split_snes(snes_rom(1024), 1024)           # capacidade que o firmware não aceita
    with pytest.raises(ValueError):
        RI.split_snes(b"")


def test_rom_write_snes_simulado(tmp_path, capsys):
    f = tmp_path / "jogo.sfc"
    f.write_bytes(snes_rom(1024, copier=True))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "snes-lorom", "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["chip"] == "snes-lorom" and (o["prg_kb"], o["flash_kb"], o["bytes"]) == (1024, 2048, 1024 * 1024)


def test_rom_write_snes_exige_chip(tmp_path, capsys):
    f = tmp_path / "jogo.sfc"
    f.write_bytes(snes_rom(512))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "snes", "-i", str(f), "--yes")
    assert code == 64 and "snes-lorom" in json.loads(out)["error"]["message"]


def test_rom_write_chip_de_nes_no_snes(tmp_path, capsys):
    f = tmp_path / "jogo.sfc"
    f.write_bytes(snes_rom(512))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "snes", "-i", str(f), "--chip", "nesmaker", "--yes")
    assert code == 64 and json.loads(out)["error"]["kind"] == "usage"


# ---------------------------------------------------------------- Mega Drive (MX29F1610 / S29GL064N)
def md_rom(n: int) -> bytes:
    return bytes((i * 11 + 5) & 0xFF for i in range(n))


def test_split_md():
    img = RI.split_md(md_rom(524288))
    assert (img.prg_kb, img.chr_kb, img.flash_kb, len(img.body)) == (512, 0, 0, 524288)
    assert RI.split_md(md_rom(1000)).prg_kb == 1            # arredonda para cima; o firmware recebe o tamanho exato
    assert RI.split_md(md_rom(4 * 1024 * 1024)).prg_kb == 4096


def test_split_md_erros():
    for bad in (b"", md_rom(1001), md_rom(4 * 1024 * 1024 + 2)):
        with pytest.raises(ValueError):
            RI.split_md(bad)
    smd = bytearray(md_rom(512 + 2048))
    smd[512 + 0x100:512 + 0x104] = b"SEGA"
    with pytest.raises(ValueError):
        RI.split_md(bytes(smd))


def test_rom_write_md_simulado(tmp_path, capsys):
    f = tmp_path / "jogo.md"
    f.write_bytes(md_rom(524288))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "md-flash", "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["chip"] == "md-flash" and (o["prg_kb"], o["bytes"]) == (512, 524288)


def test_rom_write_md_chip_errado(tmp_path, capsys):
    f = tmp_path / "jogo.md"
    f.write_bytes(md_rom(1024))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "md", "-i", str(f), "--chip", "nesmaker", "--yes")
    assert code == 64 and json.loads(out)["error"]["kind"] == "usage"
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "nes", "-i", str(f), "--chip", "md-flash", "--yes")
    assert code == 64


def test_rom_write_snes_generico_simulado(tmp_path, capsys):
    f = tmp_path / "jogo.sfc"
    f.write_bytes(snes_rom(512))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "snes-exlorom-p1", "--flash-type", "29f032", "--flash-mb", "2", "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["chip"] == "snes-exlorom-p1" and o["flash_kb"] == 2048 and o["bytes"] == 512 * 1024
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "snes-exlorom-p1", "--yes")
    assert code == 64 and "--flash-type" in json.loads(out)["error"]["message"]


def test_rom_write_snes_layout_invalido(tmp_path, capsys):
    f = tmp_path / "jogo.sfc"
    f.write_bytes(snes_rom(512))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "snes-lorom", "--layout", "4x2mb", "--yes")
    assert code == 64 and json.loads(out)["error"]["kind"] == "bad_rom"
