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
