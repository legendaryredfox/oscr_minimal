# SPDX-License-Identifier: GPL-3.0-or-later
"""WRITE_ROM no host: preparo do arquivo (iNES, chip), comando rom-write com o simulador, erros estruturados."""
import json
import types
import zlib

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


# ---------------------------------------------------------------- N64 (flash repro, F-19, D176)
def n64_z64(kb: int) -> bytes:
    return b"\x80\x37\x12\x40" + bytes((i * 11 + 3) & 0xFF for i in range(kb * 1024 - 4))


def _n64_swap_v64(z: bytes) -> bytes:
    b = bytearray(z)
    b[0::2], b[1::2] = z[1::2], z[0::2]
    return bytes(b)


def _n64_swap_n64(z: bytes) -> bytes:
    b = bytearray(z)
    b[0::4], b[1::4], b[2::4], b[3::4] = z[3::4], z[2::4], z[1::4], z[0::4]
    return bytes(b)


def test_split_n64_converte_a_ordem_e_completa_o_setor():
    z = n64_z64(1024)
    assert RI.split_n64(z).body == z
    assert RI.split_n64(_n64_swap_v64(z)).body == z and RI.split_n64(_n64_swap_n64(z)).body == z
    img = RI.split_n64(z[:1024 * 1024 - 100])                     # 100 bytes a menos: completa com $FF até o setor de 128 KB
    assert len(img.body) == 1024 * 1024 and img.body[-100:] == b"\xff" * 100 and img.prg_kb == 1024 and img.mapper is None
    assert RI.chip_code("n64-flash", img) == 1


def test_split_n64_erros():
    for data in (b"", bytes(100), bytes(8192), b"\x00\x01\x02\x03" + bytes(8192), n64_z64(65 * 1024)):     # vazio, pequena, sem cabeçalho, 65 MB
        with pytest.raises(ValueError):
            RI.split_n64(data)
    assert len(RI.split_n64(n64_z64(64 * 1024)).body) == 64 * 1024 * 1024


class _FakeN64:
    """Cliente falso do rom-write do N64: guarda o WRITE_ROM e devolve a ROM gravada no DUMP_ROM (uma leitura de MB inteiros, como o firmware)."""
    def __init__(self, readback=None):
        self.written, self.dumps, self.readback = None, [], readback

    def write_rom(self, system, data, chip, prg_kb, chr_kb, block, progress, begin_timeout):
        self.written = (system, len(data), chip, prg_kb, chr_kb, begin_timeout)
        self.data = data
        return zlib.crc32(data)

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.dumps.append((system, mapper, prg))
        data = self.readback if self.readback is not None else self.data
        mb = prg << 20
        return types.SimpleNamespace(data=data + b"\xff" * (mb - len(data)) if len(data) < mb else data[:mb], crc32=0)


def _n64_cli(monkeypatch, capsys, fake, *argv):
    from oscr_host import cli
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _FakeT(), {"write_rom": True, "flash_prog": False}))
    code = cli.main(["--json", *argv])
    return code, json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_rom_write_n64_envia_o_codigo_e_confere_pelo_prefixo(monkeypatch, capsys, tmp_path):
    f = tmp_path / "jogo.v64"
    z = n64_z64(1024 + 128)                                       # 1,125 MB: a conferência lê 2 MB e compara só o que foi gravado
    f.write_bytes(_n64_swap_v64(z))
    fake = _FakeN64()
    code, o = _n64_cli(monkeypatch, capsys, fake, "rom-write", "-s", "n64", "-i", str(f), "--yes")
    assert code == 0 and o["chip"] == "n64-flash" and o["bytes"] == len(z) and o["verify"]["ok"]
    assert fake.written[:5] == (11, len(z), 1, len(z) // 1024, 0) and fake.dumps == [(11, 0, 2)] and fake.data == z


def test_rom_write_n64_conferencia_acusa_diferenca(monkeypatch, capsys, tmp_path):
    f = tmp_path / "jogo.z64"
    z = n64_z64(1024)
    f.write_bytes(z)
    bad = bytearray(z); bad[5000] ^= 0xFF
    code, o = _n64_cli(monkeypatch, capsys, _FakeN64(bytes(bad)), "rom-write", "-s", "n64", "-i", str(f), "--yes")
    assert code == 1 and o["error"]["kind"] == "verify_failed" and o["error"]["first_diff"] == 5000


def test_rom_write_n64_recusas(monkeypatch, capsys, tmp_path):
    f = tmp_path / "x.z64"
    f.write_bytes(n64_z64(1024))
    code, o = _n64_cli(monkeypatch, capsys, _FakeN64(), "rom-write", "-s", "n64", "-i", str(f), "--chip", "gba-flash", "--yes")
    assert code == 64
    f.write_bytes(bytes(8192))
    code, o = _n64_cli(monkeypatch, capsys, _FakeN64(), "rom-write", "-s", "n64", "-i", str(f), "--yes")
    assert code == 64 and o["error"]["kind"] == "bad_rom"


# ---------------------------------------------------------------- N64: Gameshark e Xplorer 64 (F-19, D177)
def _gs_image(kb: int) -> bytes:
    return bytes((i * 7 + 1) & 0xFF for i in range(kb * 1024))


def test_xplorer_unscramble_e_uma_permutacao_dentro_de_blocos_de_4096_meias_palavras():
    for block in (0, 1, 31):
        base = block * 4096
        got = {RI.xplorer_unscramble(base + k) for k in range(4096)}
        assert got == set(range(base, base + 4096))


def test_xplorer_unscramble_igual_ao_do_oscr():
    """Lê a expressão de `unscramble` direto do N64.cpp do firmware e compara com a do host em todos os endereços de 17 bits."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "src" / "cores" / "N64.cpp").read_text()
    expr = re.search(r"uint32_t unscramble\(uint32_t addr\)\s*\{\s*uint32_t result = (.*?);", src, re.S).group(1)
    expr = expr.replace("~addr", "(~addr & 0xFFFFFFFF)")
    for a in range(1 << 17):
        assert eval(expr, {"addr": a}) & 0xFFFFFFFF == RI.xplorer_unscramble(a), a


def test_split_xplorer_entrega_na_ordem_que_o_writeXplorer_consome():
    img = _gs_image(256)
    out = RI.split_xplorer(img)
    assert out.rom == img and len(out.body) == 256 * 1024 and out.prg_kb == 256
    # simula o laço do OSCR: palavra j do buffer = palavra unscramble(j) do arquivo (seekSet + read de 2 bytes); o fluxo entrega na ordem do corpo
    for j in (0, 1, 127, 128, 4095, 4096, 70000, 131071):
        u = RI.xplorer_unscramble(j) * 2
        assert out.body[2 * j:2 * j + 2] == img[u:u + 2]
    assert sorted(out.body) == sorted(img)                         # é só uma reordenação


def test_split_xplorer_e_gameshark_erros():
    for n in (0, 128 * 1024, 256 * 1024 + 2):
        with pytest.raises(ValueError):
            RI.split_xplorer(bytes(n))
    for n in (0, 8 * 1024, 16 * 1024 + 256, 1024 * 1024 + 16 * 1024):
        with pytest.raises(ValueError):
            RI.split_gameshark(bytes(n))
    assert RI.split_gameshark(_gs_image(256)).body == _gs_image(256) and len(RI.split_gameshark(_gs_image(1024)).body) == 1 << 20
    assert RI.chip_code("gameshark", RI.split_gameshark(_gs_image(256))) == 2 and RI.chip_code("xplorer64", RI.split_xplorer(_gs_image(256))) == 3
    assert RI.n64_backup_code("gameshark") == 0x8002 and RI.n64_backup_code("xplorer64") == 0x8003


class _FakeAcc:
    """Cliente falso do Gameshark/Xplorer 64: DUMP_ROM com o bit 15 devolve a flash (de início um conteúdo antigo; depois da gravação, a imagem gravada)."""
    def __init__(self, old, size):
        self.flash, self.size, self.calls, self.written = old, size, [], None

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.calls.append(("dump", system, mapper, prg))
        return types.SimpleNamespace(data=self.flash, crc32=zlib.crc32(self.flash))

    def write_rom(self, system, data, chip, prg_kb, chr_kb, block, progress, begin_timeout):
        self.calls.append(("write", system, chip, len(data), begin_timeout))
        self.written = data
        return zlib.crc32(data)


def test_rom_write_gameshark_faz_backup_antes_e_confere_pela_imagem(monkeypatch, capsys, tmp_path):
    img = _gs_image(256)
    f = tmp_path / "gs.bin"
    f.write_bytes(img)
    class Fake2(_FakeAcc):
        def write_rom(self, *a, **k):
            r = super().write_rom(*a, **k)
            self.flash = img                      # depois de gravar, a flash tem a imagem
            return r
    fake = Fake2(b"\x11" * (256 * 1024), 0)
    code, o = _n64_cli(monkeypatch, capsys, fake, "rom-write", "-s", "n64", "--chip", "gameshark", "-i", str(f), "--backup-dir", str(tmp_path / "bk"), "--yes")
    assert code == 0 and o["chip"] == "gameshark" and o["verify"]["ok"]
    assert [c[0] for c in fake.calls] == ["dump", "write", "dump"]            # backup, gravação, leitura de volta
    assert fake.calls[0][2] == 0x8002 and fake.calls[2][2] == 0x8002 and fake.calls[1][2] == 2 and fake.calls[1][4] == 600.0
    bk = list((tmp_path / "bk").glob("gameshark_*.bin"))
    assert len(bk) == 1 and bk[0].read_bytes() == b"\x11" * (256 * 1024) and o["backup"] == str(bk[0])


def test_rom_write_xplorer_manda_o_fluxo_reordenado_e_confere_a_imagem_original(monkeypatch, capsys, tmp_path):
    img = _gs_image(256)
    f = tmp_path / "xp.bin"
    f.write_bytes(img)
    class Fake3(_FakeAcc):
        def write_rom(self, *a, **k):
            r = super().write_rom(*a, **k)
            self.flash = img
            return r
    fake = Fake3(b"\xff" * (256 * 1024), 0)
    code, o = _n64_cli(monkeypatch, capsys, fake, "rom-write", "-s", "n64", "--chip", "xplorer64", "-i", str(f), "--no-backup", "--yes")
    assert code == 0 and o["verify"]["ok"] and "backup" not in o
    assert [c[0] for c in fake.calls] == ["write", "dump"] and fake.calls[1][2] == 0x8003
    assert fake.written == RI.split_xplorer(img).body and fake.written != img


def test_rom_write_acessorio_recusas(monkeypatch, capsys, tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(bytes(1000))
    code, o = _n64_cli(monkeypatch, capsys, _FakeAcc(b"", 0), "rom-write", "-s", "n64", "--chip", "xplorer64", "-i", str(f), "--yes")
    assert code == 64 and o["error"]["kind"] == "bad_rom"
    code, o = _n64_cli(monkeypatch, capsys, _FakeAcc(b"", 0), "rom-write", "-s", "gba", "--chip", "gameshark", "-i", str(f), "--yes")
    assert code == 64


# ---------------------------------------------------------------- Game Boy (29F, 39SF, CFI)
def gb_rom(kb: int) -> bytes:
    return bytes((i * 17 + 9) & 0xFF for i in range(kb * 1024))


def test_split_gb_e_codigos():
    img = RI.split_gb(gb_rom(512), "gb-cfi")
    assert (img.prg_kb, len(img.body)) == (512, 512 * 1024)
    assert [RI.chip_code(c, img) for c in RI.GB_CHIPS] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    assert RI.split_gb(gb_rom(32), "gb-orange-fm").prg_kb == 32


def test_gb_acessorios_f17():
    """Pelican, Mega Memory e GameShark GBC (D188): tamanhos exatos, backup e conferência pela leitura do acessório (D186)."""
    assert RI.split_gb(bytes(262144), "gb-pelican").prg_kb == 256 and RI.split_gb(bytes(524288), "gb-pelican").prg_kb == 512
    assert RI.split_gb(bytes(524288), "gb-megamem").prg_kb == 512 and RI.split_gb(bytes(131072), "gb-gameshark").prg_kb == 128
    for data, chip in ((bytes(131072), "gb-pelican"), (bytes(262144), "gb-megamem"), (bytes(524288), "gb-gameshark"), (b"", "gb-gameshark")):
        with pytest.raises(ValueError):
            RI.split_gb(data, chip)
    assert [RI.backup_code(c) for c in ("gb-pelican", "gb-megamem", "gb-gameshark")] == [1, 2, 3] and RI.backup_code("gameshark") == 0x8002
    assert set(RI.BACKUP_CHIPS) == {"gameshark", "xplorer64", "gb-pelican", "gb-megamem", "gb-gameshark", "gb-memory", "gb-memory-map", "gb-smart", "bsx-pack", "sfm-flash", "sfm-map"}

    class Client:
        def __init__(self, data): self.data, self.calls = data, []
        def dump_rom(self, system, block, progress, mapper, prg, chr_):
            self.calls.append((system, mapper))
            class R: pass
            r = R(); r.data = self.data; return r
    body = bytes((i * 7) & 0xFF for i in range(524288))
    img = RI.split_gb(body, "gb-megamem")
    c = Client(bytes(16384) + body)                       # a leitura traz a ROM de 16 KB antes dos dados
    assert RI.verify_written(c, 6, "gb-megamem", img).ok and c.calls == [(6, 2)]
    bad = bytearray(bytes(16384) + body); bad[16384 + 100] ^= 1
    v = RI.verify_written(Client(bytes(bad)), 6, "gb-megamem", img)
    assert not v.ok and v.first_diff == 100
    p = RI.split_gb(bytes(262144), "gb-pelican")
    assert RI.verify_written(Client(bytes(262144)), 6, "gb-pelican", p).ok


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


def test_gb_modulos_nintendo_d189():
    """GB Memory Module (ROM de 1 MB e mapeamento de 128 bytes) e GB Smart (4 MB): tamanho exato, códigos do chip e do backup (D189)."""
    assert RI.split_gb(bytes(1048576), "gb-memory").prg_kb == 1024 and RI.split_gb(bytes(4194304), "gb-smart").prg_kb == 4096
    assert RI.split_gb(bytes(128), "gb-memory-map").body == bytes(128)
    for data, chip in ((bytes(524288), "gb-memory"), (bytes(127), "gb-memory-map"), (bytes(1048576), "gb-smart"), (bytes(4194304), "gb-memory")):
        with pytest.raises(ValueError):
            RI.split_gb(data, chip)
    assert [RI.CHIPS[c] for c in ("gb-memory", "gb-memory-map", "gb-smart")] == [12, 13, 14]
    assert [RI.backup_code(c) for c in ("gb-memory", "gb-memory-map", "gb-smart")] == [4, 5, 6]
    class Client:
        def __init__(self, data): self.data, self.calls = data, []
        def dump_rom(self, system, block, progress, mapper, prg, chr_):
            self.calls.append((system, mapper))
            class R: pass
            r = R(); r.data = self.data; return r
    m = bytes((i * 5) & 0xFF for i in range(128))
    c = Client(m)
    assert RI.verify_written(c, 6, "gb-memory-map", RI.split_gb(m, "gb-memory-map")).ok and c.calls == [(6, 5)]


def test_snes_memory_pack_e_sfm_d190():
    """Memory Pack do BS-X, flash e mapeamento do SFM: tamanho exato, campo chip inteiro (0x2001 a 0x2003) e leitura do acessório no backup e na conferência (D190)."""
    assert RI.split_snes_accessory(bytes(1048576), "bsx-pack").prg_kb == 1024 and RI.split_snes_accessory(bytes(4194304), "sfm-flash").prg_kb == 4096
    assert RI.split_snes_accessory(bytes(512), "sfm-map").body == bytes(512)
    for data, chip in ((bytes(524288), "bsx-pack"), (bytes(511), "sfm-map"), (bytes(2097152), "sfm-flash"), (bytes(1048576), "sfm-flash")):
        with pytest.raises(ValueError):
            RI.split_snes_accessory(data, chip)
    assert [RI.chip_code(c, RI.split_snes_accessory(bytes(RI.SNES_ACCESSORY_SIZES[c]), c)) for c in ("bsx-pack", "sfm-flash", "sfm-map")] == [0x2001, 0x2002, 0x2003]
    assert [RI.backup_params(c) for c in ("bsx-pack", "sfm-flash", "sfm-map")] == [(0, 0, 0x8004), (0, 0, 0x8006), (0, 0, 0x8007)]
    assert all(RI.SNES_ACCESSORY_CHIPS[c] == P.SNES_ACCESSORIES[c] for c in RI.SNES_ACCESSORY_CHIPS)       # o mesmo código da leitura do D187
    assert all(c in RI.BACKUP_CHIPS for c in RI.SNES_ACCESSORY_CHIPS) and not any(c in RI.SNES_CHIPS for c in RI.SNES_ACCESSORY_CHIPS)
    class Client:
        def __init__(self, data): self.data, self.calls = data, []
        def dump_rom(self, system, block, progress, mapper, prg, chr_):
            self.calls.append((system, mapper, chr_))
            class R: pass
            r = R(); r.data = self.data; return r
    m = bytes((i * 7) & 0xFF for i in range(512))
    c = Client(m)
    assert RI.verify_written(c, 1, "sfm-map", RI.split_snes_accessory(m, "sfm-map")).ok and c.calls == [(1, 0, 0x8007)]
    bad = bytearray(m); bad[300] ^= 1
    v = RI.verify_written(Client(bytes(bad)), 1, "sfm-map", RI.split_snes_accessory(m, "sfm-map"))
    assert not v.ok and v.first_diff == 300

