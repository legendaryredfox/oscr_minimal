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
    for bad in (b"", md_rom(1001), md_rom(8 * 1024 * 1024 + 2)):
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


# ---------------------------------------------------------------- GBA (Intel, MX29GL128E, MSP55LV128, 369-in-1)
def gba_rom(kb: int) -> bytes:
    return bytes((i * 13 + 7) & 0xFF for i in range(kb * 1024))


def test_split_gba_e_codigo():
    img = RI.split_gba(gba_rom(4096))
    assert (img.prg_kb, img.block, len(img.body)) == (4096, 0, 4 * 1024 * 1024)
    assert RI.chip_code("gba-flash", img) == 0x0001
    assert RI.chip_code("gba-flash", RI.split_gba(gba_rom(1024), 5)) == 0x0501
    assert RI.split_gba(gba_rom(1024), 63).block == 63


def test_split_gba_erros():
    for kw in ({"data": b""}, {"data": bytes(1000)}, {"data": gba_rom(1), "block": 64}, {"data": gba_rom(1), "block": -1},
               {"data": gba_rom(8192), "block": 63}):            # 8 MB a partir do bloco 63 (último de 4 MB) passa do fim
        with pytest.raises(ValueError):
            RI.split_gba(**kw)


def test_rom_write_gba_simulado(tmp_path, capsys):
    f = tmp_path / "jogo.gba"
    f.write_bytes(gba_rom(1024))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "gba-flash", "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["chip"] == "gba-flash" and (o["prg_kb"], o["bytes"]) == (1024, 1024 * 1024)
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "gba-flash", "--block369", "3", "--yes")
    assert code == 0
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "gba", "-i", str(f), "--chip", "nesmaker", "--yes")
    assert code == 64


# ---------------------------------------------------------------- Game Boy (29F, 39SF, CFI)
def gb_rom(kb: int) -> bytes:
    return bytes((i * 17 + 9) & 0xFF for i in range(kb * 1024))


def test_split_gb_e_codigos():
    img = RI.split_gb(gb_rom(512), "gb-cfi")
    assert (img.prg_kb, len(img.body)) == (512, 512 * 1024)
    assert [RI.chip_code(c, img) for c in RI.GB_CHIPS] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert RI.split_gb(gb_rom(32), "gb-orange-fm").prg_kb == 32


def test_split_gb_erros():
    for data, chip in ((b"", "gb-cfi"), (bytes(16384), "gb-cfi"), (bytes(32768 + 100), "gb-cfi"), (gb_rom(8192), "gb-cfi"), (gb_rom(64), "gb-orange-fm")):
        with pytest.raises(ValueError):
            RI.split_gb(data, chip)


def test_rom_write_gb_simulado(tmp_path, capsys):
    f = tmp_path / "jogo.gb"
    f.write_bytes(gb_rom(256))
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "mock", "-i", str(f), "--chip", "gb-diy-mbc5", "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["chip"] == "gb-diy-mbc5" and (o["prg_kb"], o["bytes"]) == (256, 256 * 1024)
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "gb", "-i", str(f), "--yes")
    assert code == 64 and "gb-cfi" in json.loads(out)["error"]["message"]
    code, out = run(capsys, "--simulate", "--json", "rom-write", "-s", "gb", "-i", str(f), "--chip", "md-flash", "--yes")
    assert code == 64


# ---------------------------------------------------------------- programador de flash genérico (sistema 7)
def test_flashprog_params():
    j = RI.flashprog_params("16", 4096)
    assert (j.chip, j.prg_kb, j.chr_word) == (3, 4096, 0)
    assert RI.flashprog_params("eprom", None).prg_kb == 4096 and RI.flashprog_params("eprom", None).chip == 4
    j = RI.flashprog_params("8", 512, "29f032")
    assert (j.chip, j.prg_kb, j.chr_word) == (1, 512, 1)
    assert RI.flashprog_params("plcc32", 512, "29gl", 128, 32).chr_word == 7 | (17 << 4) | (5 << 9)
    assert RI.flashprog_params("8", 512).chr_word == 0                       # sem tipo: serve para ler e identificar
    for kw in ({"bus": "8", "flash_kb": 512, "need_type": True}, {"bus": "8", "flash_kb": None}, {"bus": "8", "flash_kb": 9000}, {"bus": "usb", "flash_kb": 1},
               {"bus": "8", "flash_kb": 512, "flash_type": "29gl"}):
        with pytest.raises(ValueError):
            RI.flashprog_params(**kw)


def test_split_flashprog():
    j = RI.split_flashprog(bytes(1024), "16", 1024)
    assert (j.chip, j.prg_kb, len(j.body)) == (3, 1024, 1024) and j.rom == bytes(1024)
    g = RI.split_flashprog(bytes(1536), "8", 1024, "29gl", 128, 32)
    assert len(g.body) == 128 * 1024 and g.body[:1536] == bytes(1536) and set(g.body[1536:]) == {0xFF} and len(g.rom) == 1536
    for args in ((b"", "16", 1024), (bytes(100), "16", 1024), (bytes(2048), "16", 1), (bytes(512), "8", 1024), (bytes(2 * 1024 * 1024), "eprom", None)[:3] + ()):
        if args[0] == bytes(2 * 1024 * 1024):
            continue
        with pytest.raises(ValueError):
            RI.split_flashprog(*args)
    assert RI.split_flashprog(bytes(4096 * 1024), "eprom", None).prg_kb == 4096
    with pytest.raises(ValueError):
        RI.split_flashprog(bytes(4096 * 1024 + 512), "eprom", None)


def test_flash_comandos_simulados(tmp_path, capsys):
    f = tmp_path / "chip.bin"
    f.write_bytes(bytes(1024))
    code, out = run(capsys, "--simulate", "--json", "flash-write", "-s", "mock", "--bus", "16", "--flash-kb", "1024", "-i", str(f), "--yes")
    o = json.loads(out)
    assert code == 0 and o["ok"] and o["bus"] == "16" and o["bytes"] == 1024 and o["verify"] == "skipped"
    code, out = run(capsys, "--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "8", "--flash-kb", "512", "--flash-type", "29f032", "--yes")
    assert code == 0 and json.loads(out)["erased"] is True
    code, out = run(capsys, "--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "8", "--flash-kb", "512", "--yes")
    assert code == 64 and "--flash-type" in json.loads(out)["error"]["message"]
    code, out = run(capsys, "--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "eprom", "--yes")
    assert code == 64
    code, out = run(capsys, "--simulate", "--json", "flash-blank", "-s", "mock", "--bus", "16", "--flash-kb", "32")
    assert code == 1 and json.loads(out)["blank"] is False                 # o padrão do simulador não é 0xFF
    o = tmp_path / "lido.bin"
    code, out = run(capsys, "--simulate", "--json", "flash-read", "-s", "mock", "--bus", "16", "--flash-kb", "32", "-o", str(o))
    assert code == 0 and o.exists() and len(o.read_bytes()) == 32768


def test_flash_erase_recusa_sem_yes(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    code, out = run(capsys, "--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "16", "--flash-kb", "512")
    assert code == 4 and json.loads(out)["error"]["kind"] == "refused"


# ---------------------------------------------------------------- flash-id --bus md (detecção do chip do cartucho de Mega Drive)

def test_flashprog_md_so_identifica():
    j = RI.flashprog_params("md", None, detect=True)
    assert (j.chip, j.prg_kb, j.chr_word) == (5, 0, 0)
    for kw in ({}, {"need_type": True}):
        with pytest.raises(ValueError, match="rom-write"):
            RI.flashprog_params("md", None, **kw)
    with pytest.raises(ValueError, match="não usa"):
        RI.flashprog_params("md", 4096, detect=True)
    with pytest.raises(ValueError, match="não usa"):
        RI.flashprog_params("md", None, "29gl", detect=True)
    assert RI.flashprog_params("16", 4096).chip == 3                 # os outros barramentos não mudaram


class _FakeFlash:
    def __init__(self, resp):
        self.resp, self.calls = resp, []

    def detect(self, system, chip=0, prg_kb=0, chr_kb=0):
        self.calls.append((system, chip, prg_kb, chr_kb))
        return self.resp


class _FakeT:
    def close(self):
        pass


def _flash_id(monkeypatch, capsys, resp, *argv):
    from oscr_host import cli
    fake = _FakeFlash(resp)
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _FakeT(), {"flash_prog": True}))
    code = cli.main(["--json", "flash-id", *argv])
    return code, json.loads(capsys.readouterr().out), fake


def test_flash_id_md_chip_conhecido(monkeypatch, capsys):
    code, o, fake = _flash_id(monkeypatch, capsys, {"system": 7, "status": 0, "rom_size": 8 << 20, "save_size": 0, "save_type": 0, "name": "S29GL064N 017E"},
                              "--bus", "md")
    assert code == 0 and o["ok"] and o["known"] and o["chip"] == "S29GL064N" and o["size"] == 8 << 20
    assert fake.calls == [(7, 5, 0, 0)]


def test_flash_id_md_chip_desconhecido(monkeypatch, capsys):
    code, o, _ = _flash_id(monkeypatch, capsys, {"system": 7, "status": 1, "rom_size": 0, "save_size": 0, "save_type": 0, "name": "? FFFF"}, "--bus", "md")
    assert code == 1 and not o["ok"] and o["known"] is False and o["ids"] == "? FFFF" and o["chip"] is None


def test_flash_id_md_cfi_so_informa(monkeypatch, capsys):
    code, o, _ = _flash_id(monkeypatch, capsys, {"system": 7, "status": 1, "rom_size": 4 << 20, "save_size": 0, "save_type": 0, "name": "CFI 32Mbit 00AB22CD"},
                           "--bus", "md")
    assert code == 1 and not o["ok"] and o["known"] is False and o["cfi"] and o["size"] == 4 << 20 and o["chip"] is None


def test_flash_id_md_recusa_tamanho_e_outros_comandos(monkeypatch, capsys):
    code, o, fake = _flash_id(monkeypatch, capsys, {}, "--bus", "md", "--flash-kb", "4096")
    assert code == 64 and fake.calls == []
    from oscr_host import cli
    code = cli.main(["--json", "flash-read", "--bus", "md"])
    assert code == 64 and "rom-write" in json.loads(capsys.readouterr().out)["error"]["message"]
    code = cli.main(["--json", "flash-erase", "--bus", "md", "--yes"])
    assert code == 64


# ---------------------------------------------------------------- nome do chip no detect -s md --flash-id e no rom-write -s md
class _FakeMd(_FakeFlash):
    def __init__(self, resp):
        super().__init__(resp)
        self.writes = []

    def detect(self, system, chip=0, prg_kb=0, chr_kb=0):
        if system == 7:
            return super().detect(system, chip, prg_kb, chr_kb)
        return {"system": 3, "status": 0, "rom_size": 524288, "save_size": 0, "save_type": 0, "name": "SONIC"}

    def write_rom(self, *a, **k):
        self.writes.append(a)
        return 0x1234

    def dump_rom(self, *a, **k):
        raise AssertionError("conferência deve ser pulada")


def _md(monkeypatch, capsys, info, *argv, resp=None):
    from oscr_host import cli
    fake = _FakeMd(resp or {"system": 7, "status": 0, "rom_size": 2 << 20, "save_size": 0, "save_type": 0, "name": "MX29F1610 C2F1"})
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _FakeT(), info))
    code = cli.main(["--json", *argv])
    return code, json.loads(capsys.readouterr().out), fake


def test_detect_md_com_flash_id(monkeypatch, capsys):
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True}, "detect", "-s", "md", "--flash-id")
    assert code == 0 and o["flash_chip"]["chip"] == "MX29F1610" and o["flash_chip"]["size"] == 2 << 20
    assert fake.calls == [(7, 5, 0, 0)]
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True}, "detect", "-s", "md")
    assert "flash_chip" not in o and fake.calls == []                  # sem a flag, nada é escrito no cartucho
    code, o, _ = _md(monkeypatch, capsys, {"flash_prog": False}, "detect", "-s", "md", "--flash-id")
    assert o["flash_chip"] is None
    code, o, _ = _md(monkeypatch, capsys, {"flash_prog": True}, "detect", "-s", "snes", "--flash-id")
    assert code == 64


def test_rom_write_md_mostra_o_chip(monkeypatch, capsys, tmp_path):
    f = tmp_path / "jogo.md"
    f.write_bytes(md_rom(524288))
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True, "write_rom": True}, "rom-write", "-s", "md", "-i", str(f), "--chip", "md-flash", "--yes", "--no-verify")
    assert code == 0 and o["flash_chip"]["chip"] == "MX29F1610" and len(fake.writes) == 1


_GL = {"system": 7, "status": 0, "rom_size": 8 << 20, "save_size": 0, "save_type": 0, "name": "S29GL064N 017E1000"}


def test_chip_mostra_os_codigos_do_autoselect(monkeypatch, capsys):
    code, o, _ = _md(monkeypatch, capsys, {"flash_prog": True}, "detect", "-s", "md", "--flash-id", resp=_GL)
    assert o["flash_chip"]["codes"] == "017E1000" and o["flash_chip"]["chip"] == "S29GL064N"
    from oscr_host.cli.md_chip import md_chip_line
    assert "017E1000" in md_chip_line(o["flash_chip"])


def test_rom_write_md_acima_de_2mib_recusa_no_s29gl(monkeypatch, capsys, tmp_path):
    """Cartuchos KY / FlashKit com S29GL só têm 2 MiB de flash (bancada do md_rewriter): recusa antes de apagar, a menos que --ignore-cart-limit."""
    f = tmp_path / "jogo.md"
    f.write_bytes(md_rom(4 << 20))
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True, "write_rom": True}, "rom-write", "-s", "md", "-i", str(f), "--chip", "md-flash", "--yes", "--no-verify", resp=_GL)
    assert code == 4 and fake.writes == []
    assert "2 MiB" in json.dumps(o) and "--ignore-cart-limit" in json.dumps(o)
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True, "write_rom": True}, "rom-write", "-s", "md", "-i", str(f), "--chip", "md-flash", "--yes", "--no-verify",
                        "--ignore-cart-limit", resp=_GL)
    assert code == 0 and len(fake.writes) == 1


def test_rom_write_md_limite_so_acima_de_2mib_e_so_no_s29gl(monkeypatch, capsys, tmp_path):
    f = tmp_path / "jogo.md"
    f.write_bytes(md_rom(2 << 20))
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True, "write_rom": True}, "rom-write", "-s", "md", "-i", str(f), "--chip", "md-flash", "--yes", "--no-verify", resp=_GL)
    assert code == 0 and len(fake.writes) == 1                                          # exatamente 2 MiB passa
    g = tmp_path / "grande.md"
    g.write_bytes(md_rom(4 << 20))
    other = {"system": 7, "status": 0, "rom_size": 4 << 20, "save_size": 0, "save_type": 0, "name": "M29W320EB 0020"}
    code, o, fake = _md(monkeypatch, capsys, {"flash_prog": True, "write_rom": True}, "rom-write", "-s", "md", "-i", str(g), "--chip", "md-flash", "--yes", "--no-verify", resp=other)
    assert code == 0 and len(fake.writes) == 1                                          # outro chip: sem limite


# ---------------------------------------------------------------- dump --raw (NES: PRG e CHR em arquivos separados)
class _FakeNes:
    def __init__(self, prg_kb, chr_kb):
        self.prg = bytes((i * 5) & 0xFF for i in range(prg_kb * 1024))
        self.chr = bytes((i * 11) & 0xFF for i in range(chr_kb * 1024))
        hdr = b"NES\x1a" + bytes([prg_kb // 16, chr_kb // 8, 0x10, 0]) + bytes(8)
        self.ines = hdr + self.prg + self.chr

    def detect(self, system, *a):
        return {"name": "JOGO TESTE"}

    def dump_rom(self, *a, **k):
        import zlib
        return type("R", (), {"data": self.ines, "crc32": zlib.crc32(self.ines)})()


def _nes_raw(monkeypatch, capsys, tmp_path, prg, chr_, *extra):
    from oscr_host import cli
    fake = _FakeNes(prg, chr_)
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _FakeT(), {}))
    code = cli.main(["--json", "dump", "-s", "nes", "--raw", "-o", str(tmp_path / "jogo"), "--mapper", "1", "--prg", str(prg), "--chr", str(chr_), *extra])
    return code, json.loads(capsys.readouterr().out), fake


def test_dump_raw_separa_prg_e_chr(monkeypatch, capsys, tmp_path):
    code, o, fake = _nes_raw(monkeypatch, capsys, tmp_path, 32, 8)
    assert code == 0
    assert (tmp_path / "jogo.prg").read_bytes() == fake.prg and (tmp_path / "jogo.chr").read_bytes() == fake.chr
    assert not (tmp_path / "jogo.nes").exists() and o["prg_bytes"] == 32768 and o["chr_bytes"] == 8192


def test_dump_raw_sem_chr_rom(monkeypatch, capsys, tmp_path):
    code, o, fake = _nes_raw(monkeypatch, capsys, tmp_path, 16, 0)
    assert code == 0 and (tmp_path / "jogo.prg").read_bytes() == fake.prg and not (tmp_path / "jogo.chr").exists() and "chr_bytes" not in o


def test_dump_raw_so_nes(tmp_path, capsys):
    from oscr_host import cli
    assert cli.main(["--simulate", "--json", "dump", "-s", "snes", "--raw", "-o", str(tmp_path / "x")]) == 64


# ---------------------------------------------------------------- dump --twice (lê duas vezes e compara)
class _FakeTwice:
    def __init__(self, reads):
        self.reads, self.calls = list(reads), 0

    def detect(self, system, *a):
        return {"name": "JOGO TESTE"}

    def dump_rom(self, *a, **k):
        import zlib
        d = self.reads[self.calls]
        self.calls += 1
        return type("R", (), {"data": d, "crc32": zlib.crc32(d)})()


def _twice(monkeypatch, capsys, tmp_path, reads):
    from oscr_host import cli
    fake = _FakeTwice(reads)
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _FakeT(), {}))
    code = cli.main(["--json", "dump", "-s", "snes", "--twice", "-o", str(tmp_path / "jogo.sfc")])
    return code, json.loads(capsys.readouterr().out.strip().splitlines()[-1]), fake


def test_dump_twice_iguais_grava_um_arquivo(monkeypatch, capsys, tmp_path):
    d = bytes(range(256)) * 16
    code, o, fake = _twice(monkeypatch, capsys, tmp_path, [d, d])
    assert code == 0 and o["ok"] and o["twice"] is True and fake.calls == 2
    assert (tmp_path / "jogo.sfc").read_bytes() == d and not (tmp_path / "jogo.leitura1.sfc").exists()


def test_dump_twice_diferentes_grava_as_duas_e_falha(monkeypatch, capsys, tmp_path):
    a = bytes(range(256)) * 16
    b = bytearray(a)
    b[100] ^= 1
    b[3000] ^= 0x80
    code, o, _ = _twice(monkeypatch, capsys, tmp_path, [a, bytes(b)])
    assert code == 1 and o["ok"] is False and o["error"]["kind"] == "mismatch"
    assert o["error"]["diff_bytes"] == 2 and o["error"]["first_diff"] == 100
    assert (tmp_path / "jogo.leitura1.sfc").read_bytes() == a and (tmp_path / "jogo.leitura2.sfc").read_bytes() == bytes(b)
    assert not (tmp_path / "jogo.sfc").exists()


def test_diff_summary_tamanhos_diferentes():
    from oscr_host.cli.output import diff_summary
    assert diff_summary(b"abc", b"abc") == (0, -1)
    assert diff_summary(b"abcd", b"abc") == (1, 3)
    assert diff_summary(b"abxd", b"abcd") == (1, 2)


def test_flash_id_8_bits_sugere_o_chip_da_tabela(monkeypatch, capsys):
    resp = {"system": 7, "status": 0, "rom_size": 2 << 20, "save_size": 0, "save_type": 0, "name": "I=FFFF A=01AD B=0000 S=FFFF"}
    code, o, _ = _flash_id(monkeypatch, capsys, resp, "--bus", "8", "--flash-kb", "2048")
    assert code == 0 and o["ok"] and [c["name"] for c in o["candidates"]] == ["AM29F016B"] and o["candidates"][0]["flash_type"] == "29f032"


def test_flash_id_8_bits_texto_e_aviso_de_tamanho(monkeypatch, capsys):
    from oscr_host import cli
    fake = _FakeFlash({"system": 7, "status": 0, "rom_size": 1 << 20, "save_size": 0, "save_type": 0, "name": "I=FFFF A=01AD B=0000 S=FFFF"})
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _FakeT(), {"flash_prog": True}))
    assert cli.main(["--lang", "en", "flash-id", "--bus", "8", "--flash-kb", "1024"]) == 0
    out = capsys.readouterr().out
    assert "candidate: AM29F016B (29F032, 2048 KB, 5 V), answered routine A  ->  --flash-type 29f032 --flash-kb 2048" in out
    assert "the given size (1024 KB) differs from the table's (2048 KB)" in out and "not a confirmation" in out


def test_flash_id_id_fora_da_tabela(monkeypatch, capsys):
    resp = {"system": 7, "status": 0, "rom_size": 2 << 20, "save_size": 0, "save_type": 0, "name": "ID 1234"}
    code, o, _ = _flash_id(monkeypatch, capsys, resp, "--bus", "16", "--flash-kb", "2048")
    assert code == 0 and o["candidates"] == []
