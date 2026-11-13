# SPDX-License-Identifier: GPL-3.0-or-later
"""Melhorias vindas da análise dos repositórios de referência (D160, docs/historico/pesquisa-repos-referencia-2026-11-13.md)."""


def test_sound_um_bel_se_deu_certo_e_tres_se_falhou(capsys):
    from oscr_host import cli
    assert cli.main(["--simulate", "--json", "--sound", "detect", "-s", "mock"]) == 0
    assert capsys.readouterr().err.count("\a") == 1
    assert cli.main(["--simulate", "--json", "--sound", "detect", "-s", "snes"]) != 0       # o simulador só tem cartucho MOCK
    assert capsys.readouterr().err.count("\a") == 3
    assert cli.main(["--simulate", "--json", "detect", "-s", "mock"]) == 0
    assert "\a" not in capsys.readouterr().err                                              # sem --sound, silêncio


# ---------------------------------------------------------------- P2: save do GBA pela base do FlashGBX
import hashlib
from pathlib import Path

import pytest
import json
import zlib

from oscr_host import gba_db as G


def _rom(code=b"ABCD", title=b"TESTE", n=0x400):
    r = bytearray(n)
    r[0xA0:0xA0 + len(title)] = title
    r[0xAC:0xB0] = code
    return bytes(r)


def test_base_do_flashgbx_carrega():
    jogos = G.load()
    assert len(jogos) > 2900
    assert all(len(k) == 40 for k in jogos) and all(j.save_type in G.SAVE_LABEL for j in jogos.values())
    assert any(j.save_type == 3 and j.save_size == 32768 for j in jogos.values())


def test_sha1_do_cabecalho_como_no_flashgbx():
    r = _rom()
    assert G.header_sha1(r) == hashlib.sha1(r[:0x180]).hexdigest().upper()
    m = _rom(code=b"MXYZ")
    assert G.header_sha1(m) == hashlib.sha1(m[:0x100]).hexdigest().upper()           # códigos "M...": só 0x100 bytes
    y = _rom(title=b"YJencrypted")
    assert G.header_sha1(y) == hashlib.sha1(y[0x0A:0x180]).hexdigest().upper()
    assert G.header_sha1(b"curto") is None


def test_lookup_com_tsv_proprio(tmp_path):
    r = _rom()
    tsv = tmp_path / "gba.tsv"
    tsv.write_text(f"# cabecalho\n{G.header_sha1(r)}\tDEADBEEF\t8388608\t5\t131072\tJogo de Teste (USA)\n", encoding="utf-8")
    g = G.lookup(r, tsv)
    assert g and g.save_type == 5 and g.save_size == 131072 and g.name.startswith("Jogo")
    assert G.lookup(_rom(code=b"WXYZ"), tsv) is None


class _Res:
    def __init__(self, data):
        self.data, self.crc32 = data, zlib.crc32(data)


class _FakeGba:
    def __init__(self, rom):
        self.rom = rom

    def detect(self, system, *a):
        return {"system": system, "status": 0, "rom_size": len(self.rom), "save_size": 0, "save_type": 0, "name": "TESTE"}

    def dump_rom(self, *a, **k):
        return _Res(self.rom)


class _T:
    def close(self):
        pass


def test_dump_gba_sugere_o_save_da_base(monkeypatch, capsys, tmp_path):
    from oscr_host import cli
    r = _rom()
    tsv = tmp_path / "gba.tsv"
    tsv.write_text(f"{G.header_sha1(r)}\tDEADBEEF\t1024\t3\t32768\tJogo de Teste (USA)\n", encoding="utf-8")
    monkeypatch.setattr(G, "TSV", tsv)
    G._cache.clear()
    monkeypatch.setattr(cli.common, "connect", lambda a: (_FakeGba(r), _T(), {}))
    code = cli.main(["--json", "dump", "-s", "gba", "-o", str(tmp_path / "jogo")])
    o = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 0 and o["gba_save_type"] == 3 and o["gba_save_db"]["save_label"] == "SRAM 32 KB"
    G._cache.clear()


# ---------------------------------------------------------------- P9: fotos do Game Boy Camera
import struct

from oscr_host import gbcamera as C


def _tile(rows):
    """Tile 8x8 de 2 bits: rows = 8 listas de 8 valores (0 a 3) -> 16 bytes (plano baixo e alto por linha)."""
    b = bytearray()
    for r in rows:
        lo = sum(((v & 1) << (7 - j)) for j, v in enumerate(r))
        hi = sum((((v >> 1) & 1) << (7 - j)) for j, v in enumerate(r))
        b += bytes([lo, hi])
    return bytes(b)


def _save_com_uma_foto():
    d = bytearray(C.SAVE_BYTES)
    tile = _tile([[(i + j) % 4 for j in range(8)] for i in range(8)])
    foto = tile * (16 * 14) + bytes(0x1000 - 0xE00)
    d[0x2000:0x2000 + 0x1000] = foto                       # bloco 0
    d[0x11D7:0x11D7 + 30] = bytes([0]) + bytes([0xFF] * 29)   # o álbum tem só a foto do bloco 0
    return bytes(d), tile


def test_decode_do_tile():
    tile = _tile([[(i + j) % 4 for j in range(8)] for i in range(8)])
    px = C.decode(tile * (16 * 14))
    assert len(px) == 128 * 112
    assert [px[i * 128 + j] for i in range(8) for j in range(8)] == [(i + j) % 4 for i in range(8) for j in range(8)]
    assert px[8 * 128 + 8] == (0 + 0) % 4                    # o tile seguinte repete o desenho


def test_extract_ordem_apagadas_e_vazias():
    d, _ = _save_com_uma_foto()
    fotos = C.extract(d)
    assert [f.name for f in fotos][:2] == ["photo_01", "photo_02"] and fotos[-2].name == "game_face" and fotos[-1].name == "last_seen"
    assert not fotos[0].deleted and not fotos[0].empty
    assert fotos[1].deleted and fotos[1].empty                # o resto do álbum está apagado e em branco
    assert (fotos[-1].width, fotos[-1].height) == (128, 123)
    try:
        C.extract(b"curto")
        assert False
    except ValueError:
        pass


def test_png_valido():
    px = bytes((i % 4) for i in range(128 * 112))
    for scale in (1, 3):
        b = C.png(px, 128, 112, "green", scale)
        assert b[:8] == b"\x89PNG\r\n\x1a\n"
        w, h, depth, ctype = struct.unpack(">IIBB", b[16:26])
        assert (w, h, depth, ctype) == (128 * scale, 112 * scale, 8, 3)
        assert b.rstrip().endswith(b"IEND\xaeB`\x82")


def test_comando_gbcamera(tmp_path, capsys):
    from oscr_host import cli
    d, _ = _save_com_uma_foto()
    sav = tmp_path / "camera.sav"
    sav.write_bytes(d)
    code = cli.main(["--json", "gbcamera", "-i", str(sav), "-o", str(tmp_path / "fotos"), "--scale", "2", "--palette", "gbc"])
    o = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    nomes = sorted(Path(f).name for f in o["files"])
    assert code == 0 and nomes == ["game_face.png", "last_seen.png", "photo_01.png"] and len(o["skipped"]) == 29
    code = cli.main(["--json", "gbcamera", "-i", str(sav), "-o", str(tmp_path / "todas"), "--all"])
    o = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 0 and len(o["files"]) == 32 and any(f.endswith("photo_02_apagada.png") for f in o["files"])
    (tmp_path / "pequeno.sav").write_bytes(b"x" * 100)
    assert cli.main(["--json", "gbcamera", "-i", str(tmp_path / "pequeno.sav")]) == 1
    assert cli.main(["--json", "gbcamera", "-i", str(sav), "--scale", "9"]) == 64


# ---------------------------------------------------------------- P5: detecção automática do sistema
class _FakeAuto:
    """DETECT por sistema: só `presente` responde detectado (0); os outros dizem que não há cartucho (1)."""
    def __init__(self, presente, nes_pega_tudo=False):
        self.presente, self.nes_pega_tudo, self.chamadas = presente, nes_pega_tudo, []

    def detect(self, system, *a):
        nome = P.SYSTEM_BY_ID[system]
        self.chamadas.append(nome)
        ok = nome == self.presente or (nome == "nes" and self.nes_pega_tudo)
        return {"system": system, "status": 0 if ok else 1, "rom_size": 32768 if ok else 0, "save_size": 0, "save_type": 0, "name": "JOGO" if ok else ""}

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.chamadas.append(("dump", P.SYSTEM_BY_ID[system]))
        return _Res(bytes(range(256)) * 4)

    def read_save(self, system, block, progress, mapper, ram):
        self.chamadas.append(("save-read", P.SYSTEM_BY_ID[system]))
        return _Res(bytes(8192))


from oscr_host import protocol as P


def _cli_auto(monkeypatch, capsys, fake, *argv, systems=("n64", "gba", "gb", "md", "snes", "sms", "nes", "famicom")):
    from oscr_host import cli
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _T(), {"systems": list(systems)}))
    code = cli.main(["--json", *argv])
    return code, json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_auto_acha_o_sistema_e_para_no_primeiro(monkeypatch, capsys):
    f = _FakeAuto("md")
    code, o = _cli_auto(monkeypatch, capsys, f, "detect", "-s", "auto")
    assert code == 0 and o["ok"] and o["system"] == 4 and f.chamadas[:4] == ["n64", "gba", "gb", "md"] and "snes" not in f.chamadas     # não sonda o resto


def test_auto_deixa_o_nes_por_ultimo_e_ele_nao_rouba_os_outros(monkeypatch, capsys):
    f = _FakeAuto("snes", nes_pega_tudo=True)
    code, o = _cli_auto(monkeypatch, capsys, f, "detect", "-s", "auto")
    assert o["system"] == 1 and "nes" not in f.chamadas                                              # o SNES vem antes: o NES nem foi sondado
    f = _FakeAuto(None, nes_pega_tudo=True)
    code, o = _cli_auto(monkeypatch, capsys, f, "detect", "-s", "auto")
    assert o["system"] == 2 and f.chamadas[-1] == "nes"


def test_auto_sem_cartucho_sai_com_2_e_so_usa_sistemas_do_firmware(monkeypatch, capsys):
    f = _FakeAuto(None)
    code, o = _cli_auto(monkeypatch, capsys, f, "detect", "-s", "auto", systems=("md", "snes"))
    assert code == 2 and not o["ok"] and f.chamadas == ["md", "snes"]


def test_auto_em_dump_e_save_read_mas_nao_em_gravacao(monkeypatch, capsys, tmp_path):
    from oscr_host import cli
    f = _FakeAuto("gba")
    code, o = _cli_auto(monkeypatch, capsys, f, "dump", "-s", "auto", "-o", str(tmp_path / "j"))
    assert code == 0 and ("dump", "gba") in f.chamadas and o["file"].endswith(".gba")
    f = _FakeAuto("gba")
    code, o = _cli_auto(monkeypatch, capsys, f, "save-read", "-s", "auto", "--mapper", "3", "-o", str(tmp_path / "s"))
    assert code == 0 and ("save-read", "gba") in f.chamadas
    for cmd in (["save-write", "-s", "auto", "-i", str(tmp_path / "s.sav"), "--yes"], ["rom-write", "-s", "auto", "-i", "x", "--yes"]):
        with pytest.raises(SystemExit) as e:
            cli.main(["--json", *cmd])
        assert e.value.code in (2, 64)                                                                 # o argparse recusa "auto" na gravação
    capsys.readouterr()
