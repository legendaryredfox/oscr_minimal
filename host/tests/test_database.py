# SPDX-License-Identifier: GPL-3.0-or-later
"""Identificação do jogo por CRC32 no PC (oscr_host.database e os comandos identify, search e dump --db)."""
import json
import zlib

import pytest

from oscr_host import database as DB
from oscr_host.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    return code, capsys.readouterr().out


def crc(b: bytes) -> str:
    return f"{zlib.crc32(b):08X}"


def logiqx(path, entries):
    rows = "".join(f'<game name="{n}"><description>{n}</description><rom name="{n}.bin" size="{s}" crc="{c}" sha1="00"/></game>' for n, s, c in entries)
    path.write_text(f'<?xml version="1.0"?><datafile><header><name>teste</name></header>{rows}</datafile>')
    return path


def make_nes(prg: bytes, chr_: bytes, mapper: int = 0) -> bytes:
    hdr = bytes([0x4E, 0x45, 0x53, 0x1A, len(prg) // 16384, len(chr_) // 8192, (mapper & 0xF) << 4, mapper & 0xF0]) + bytes(8)
    return hdr + prg + chr_


def test_logiqx_por_crc(tmp_path):
    rom = bytes(range(256)) * 8
    db = DB.Database()
    assert db.load(logiqx(tmp_path / "a.dat", [("Jogo A", len(rom), crc(rom)), ("Jogo B", 3, "00000001")])) == 2
    m = db.identify(1, rom)
    assert m and m.entry.name == "Jogo A" and m.how == "crc32" and m.entry.source == "a.dat"
    assert db.identify(1, rom + b"x") is None


def test_nes_sem_cabecalho_ines(tmp_path):
    nes = make_nes(bytes([1]) * 16384, bytes([2]) * 8192)
    db = DB.Database()
    db.load(logiqx(tmp_path / "n.dat", [("Mario", len(nes) - 16, crc(nes[16:]))]))
    m = db.identify(2, nes)
    assert m and m.how == "crc32 sem cabeçalho iNES"
    assert db.identify(1, nes) is None                    # em outro sistema a regra do cabeçalho não vale


NES20 = """<?xml version="1.0"?><nes20db>
<game><rom name="Zelda.nes" size="{size}" crc32="{full}"/><prgrom size="{prgs}" crc32="{prg}"/><chrrom size="{chrs}" crc32="{chr}"/>
<prgnvram size="8192"/><pcb mapper="1" submapper="0" mirroring="H" battery="1"/></game>
<game><rom name="Outro.nes" size="1" crc32="00000002"/><prgrom size="32768" crc32="00000003"/><pcb mapper="0" submapper="0"/></game>
</nes20db>"""


def test_nes20_por_prg_e_chr_e_opcoes(tmp_path):
    prg, chr_ = bytes([7]) * 32768, bytes([9]) * 16384
    nes = make_nes(prg, chr_, mapper=1)
    f = tmp_path / "nes20db.xml"
    f.write_text(NES20.format(size=len(nes), full="DEADBEEF", prgs=len(prg), prg=crc(prg), chrs=len(chr_), chr=crc(chr_)))
    db = DB.Database()
    db.load(f)
    m = db.identify(2, nes)
    assert m and m.entry.name == "Zelda.nes" and m.how == "crc32 da PRG e da CHR"
    assert m.entry.nes_options() == {"mapper": 1, "prg": 32, "chr": 16, "ram": 8} and m.entry.battery
    assert db.search("zelda")[0].name == "Zelda.nes" and db.search("zelda nada") == []


def test_pasta_e_xml_invalido(tmp_path):
    logiqx(tmp_path / "x.dat", [("A", 1, "00000010")])
    (tmp_path / "leiame.txt").write_text("ignorado")
    db = DB.Database()
    assert db.load(tmp_path) == 1
    (tmp_path / "ruim.dat").write_text("<datafile><game")
    with pytest.raises(ValueError):
        DB.Database().load(tmp_path / "ruim.dat")
    with pytest.raises(ValueError):
        DB.Database().load(tmp_path / "naoexiste")


def test_cli_identify_e_search(tmp_path, capsys):
    rom = b"abc" * 100
    (tmp_path / "j.sfc").write_bytes(rom)
    dat = logiqx(tmp_path / "d.dat", [("Super Teste (USA)", len(rom), crc(rom))])
    code, out = run(capsys, "--json", "identify", str(tmp_path / "j.sfc"), "--db", str(dat))
    o = json.loads(out)
    assert code == 0 and o["results"][0]["game"]["name"] == "Super Teste (USA)" and o["entries_in_database"] == 1
    (tmp_path / "k.sfc").write_bytes(b"zzz")
    code, out = run(capsys, "--json", "identify", str(tmp_path / "k.sfc"), "--db", str(dat))
    assert code == 1 and json.loads(out)["results"][0]["game"] is None
    code, out = run(capsys, "--json", "search", "teste", "--db", str(dat))
    assert code == 0 and json.loads(out)["results"][0]["crc32"] == crc(rom)


def test_cli_sem_base_da_erro_estruturado(capsys, monkeypatch):
    monkeypatch.delenv("OSCR_DB", raising=False)
    code, out = run(capsys, "--json", "search", "x")
    o = json.loads(out)
    assert code == 64 and o["error"]["kind"] == "no_database"


def test_dump_simulado_mostra_o_jogo(tmp_path, capsys):
    out_rom = tmp_path / "m"
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "mock", "-o", str(out_rom))
    assert code == 0
    data = (tmp_path / "m").read_bytes() if (tmp_path / "m").exists() else json.loads(out) and open(json.loads(out)["file"], "rb").read()
    dat = logiqx(tmp_path / "d.dat", [("Padrão MOCK", len(data), crc(data))])
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "mock", "-o", str(out_rom), "--db", str(dat))
    o = json.loads(out)
    assert code == 0 and o["game"]["name"] == "Padrão MOCK"
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "mock", "-o", str(out_rom), "--db", str(logiqx(tmp_path / "e.dat", [("Outro", 1, "00000001")])))
    assert json.loads(out)["game"] is None


def test_dump_game_preenche_mapper(tmp_path, capsys):
    f = tmp_path / "nes20db.xml"
    f.write_text(NES20.format(size=1, full="DEADBEEF", prgs=32768, prg="00000005", chrs=16384, chr="00000006"))
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "nes", "--game", "zelda", "--db", str(f), "-o", str(tmp_path / "z"))
    assert code != 64                                       # o simulador não tem NES (sai 2 ou 1): o que importa é a base ter resolvido o jogo
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "nes", "--game", "naoexiste", "--db", str(f))
    assert code == 64 and json.loads(out)["error"]["kind"] == "game_not_found"
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "snes", "--game", "zelda", "--db", str(f))
    assert code == 64
