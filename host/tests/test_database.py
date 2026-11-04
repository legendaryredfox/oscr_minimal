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
    code, out = run(capsys, "--json", "--no-builtin-db", "identify", str(tmp_path / "j.sfc"), "--db", str(dat))
    o = json.loads(out)
    assert code == 0 and o["results"][0]["game"]["name"] == "Super Teste (USA)" and o["entries_in_database"] == 1
    (tmp_path / "k.sfc").write_bytes(b"zzz")
    code, out = run(capsys, "--json", "--no-builtin-db", "identify", str(tmp_path / "k.sfc"), "--db", str(dat))
    assert code == 1 and json.loads(out)["results"][0]["game"] is None
    code, out = run(capsys, "--json", "--no-builtin-db", "search", "teste", "--db", str(dat))
    assert code == 0 and json.loads(out)["results"][0]["crc32"] == crc(rom)


def test_cli_sem_base_da_erro_estruturado(capsys, monkeypatch):
    monkeypatch.delenv("OSCR_DB", raising=False)
    code, out = run(capsys, "--json", "--no-builtin-db", "search", "x")
    o = json.loads(out)
    assert code == 64 and o["error"]["kind"] == "no_database"


def test_dump_simulado_mostra_o_jogo(tmp_path, capsys):
    out_rom = tmp_path / "m"
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "mock", "-o", str(out_rom))
    assert code == 0
    data = (tmp_path / "m").read_bytes() if (tmp_path / "m").exists() else json.loads(out) and open(json.loads(out)["file"], "rb").read()
    dat = logiqx(tmp_path / "d.dat", [("Padrão MOCK", len(data), crc(data))])
    code, out = run(capsys, "--simulate", "--json", "--no-builtin-db", "dump", "-s", "mock", "-o", str(out_rom), "--db", str(dat))
    o = json.loads(out)
    assert code == 0 and o["game"]["name"] == "Padrão MOCK"
    code, out = run(capsys, "--simulate", "--json", "--no-builtin-db", "dump", "-s", "mock", "-o", str(out_rom), "--db", str(logiqx(tmp_path / "e.dat", [("Outro", 1, "00000001")])))
    assert json.loads(out)["game"] is None


def test_dump_game_preenche_mapper(tmp_path, capsys):
    f = tmp_path / "nes20db.xml"
    f.write_text(NES20.format(size=1, full="DEADBEEF", prgs=32768, prg="00000005", chrs=16384, chr="00000006"))
    code, out = run(capsys, "--simulate", "--json", "--no-builtin-db", "dump", "-s", "nes", "--game", "zelda", "--db", str(f), "-o", str(tmp_path / "z"))
    assert code != 64                                       # o simulador não tem NES (sai 2 ou 1): o que importa é a base ter resolvido o jogo
    code, out = run(capsys, "--simulate", "--json", "--no-builtin-db", "dump", "-s", "nes", "--game", "naoexiste", "--db", str(f))
    assert code == 64 and json.loads(out)["error"]["kind"] == "game_not_found"
    code, out = run(capsys, "--simulate", "--json", "--no-builtin-db", "dump", "-s", "snes", "--game", "zelda", "--db", str(f))
    assert code == 64


# ---- base que vem no projeto (database/oscr/, do OSCR legado) ----

OSCR_NES = (
    "Jogo Um (USA).nes\r\nA2C2C172,D1628A60,4E45531A10001008000007070000000\r\n\r\n"          # cabeçalho truncado (31 dígitos): ignorado sem quebrar a leitura
    "Zelda Teste (USA).nes\r\n{crc},00000000,4E45531A02011208000007070000000{x}\r\n\r\n"
    "Sem Dados\r\n\r\n"
    "Outro (Japan).nes\r\n00000007,00000000,4E45531A010001080000000700000001\r\n"
)


def test_leitor_oscr_txt(tmp_path):
    nes = make_nes(bytes([5]) * 32768, bytes([6]) * 8192, mapper=4)
    f = tmp_path / "nes.txt"
    f.write_bytes(OSCR_NES.format(crc=crc(nes[16:]), x="1").encode())
    es = DB.parse_file(f)
    assert [e.name for e in es] == ["Jogo Um (USA)", "Zelda Teste (USA)", "Outro (Japan)"]   # extensão do arquivo sai do nome
    assert es[0].mapper is None                                                              # cabeçalho inválido: sem mapper, mas o CRC32 vale
    z = es[1]
    assert (z.kind, z.source, z.mapper, z.prg_kb, z.chr_kb, z.ram_kb, z.size) == ("oscr", "nes.txt", 1, 32, 8, 8, 40960)
    assert z.battery is True and z.nes_options() == {"mapper": 1, "prg": 32, "chr": 8, "ram": 8}
    db = DB.Database()
    db.load(f)
    m = db.identify(2, nes)                                   # arquivo com cabeçalho: o CRC32 da base é o do conteúdo sem cabeçalho
    assert m and m.entry.name == "Zelda Teste (USA)" and m.how == "crc32 sem cabeçalho iNES"


def test_ines_cabecalhos():
    h = bytes.fromhex("4E45531A100010080000070700000001")       # exemplo do OSCR: NES 2.0, mapper 1, PRG 256 KB, CHR RAM
    assert DB._ines(h) == {"mapper": 1, "submapper": 0, "prg_kb": 256, "chr_kb": 0, "ram_kb": 8, "battery": False}
    h1 = bytes([0x4E, 0x45, 0x53, 0x1A, 2, 1, 0x12, 0x00, 0, 0, 0, 0, 0, 0, 0, 0])     # iNES 1: mapper 1, bateria, byte 8 = 0 (8 KB)
    assert DB._ines(h1) == {"mapper": 1, "submapper": 0, "prg_kb": 32, "chr_kb": 8, "ram_kb": 8, "battery": True}
    big = bytes([0x4E, 0x45, 0x53, 0x1A, 0, 0, 0xF0, 0x08, 0x31, 0x11, 0, 0, 0, 0, 0, 0])   # NES 2.0: mapper F (byte 6) + 1 (byte 8, bits 0-3) = 0x10F, submapper 3
    assert DB._ines(big)["mapper"] == 0x10F and DB._ines(big)["submapper"] == 3
    assert DB._ines(big[:15]) is None and DB._ines(b"XXXX" + bytes(12)) is None
    assert DB._ines(bytes([0x4E, 0x45, 0x53, 0x1A, 0, 0, 0, 0x08, 0, 0x0F, 0, 0, 0, 0, 0, 0])) is None   # tamanho exponencial


def test_base_do_projeto_esta_completa():
    d = DB.BUILTIN_DIR
    assert d.is_dir(), "database/oscr/ deve vir no repositório"
    index = (d / "INDEX.txt").read_text().split()
    assert {"nes.txt", "snes.txt", "md.txt", "gba.txt", "gb.txt"} <= set(index)
    assert all((d / n).is_file() for n in index)
    assert not (d / "config.txt").exists()                      # config.txt do OSCR é configuração, não base
    assert "sanni/cartreader" in (d / "ORIGEM.txt").read_text() and "GPL" in (d / "ORIGEM.txt").read_text()
    on_disk = {p.name for p in d.glob("*.txt")} - {"INDEX.txt", "ORIGEM.txt"}
    assert on_disk == set(index)


def test_base_do_projeto_carrega_sozinha():
    db = DB.load_databases([])
    by_src = {}
    for e in db.entries:
        by_src[e.source] = by_src.get(e.source, 0) + 1
    assert len(db) > 23000 and by_src["md.txt"] > 2500 and by_src["nes.txt"] > 7000 and by_src["snes.txt"] > 3800
    assert DB.load_databases([], builtin=False).entries == []
    assert any("sonic" in e.name.lower() for e in db.search("sonic", 5))
    nes = [e for e in db.entries if e.source == "nes.txt"]
    assert sum(1 for e in nes if e.nes_options()) > len(nes) * 0.99          # quase todos têm mapper e tamanhos pelo cabeçalho
    assert all(e.name == e.name.strip() and not e.name.lower().endswith(".nes") for e in nes)
    assert all(0 <= e.crc <= 0xFFFFFFFF for e in db.entries)


def test_base_do_projeto_e_base_do_usuario_somam(tmp_path):
    rom = b"\x01\x02" * 400
    dat = logiqx(tmp_path / "u.dat", [("Meu Jogo", len(rom), crc(rom))])
    db = DB.load_databases([dat])
    assert db.identify(1, rom).entry.name == "Meu Jogo"
    assert len(db) > 23000


def test_cli_search_usa_a_base_do_projeto(capsys, monkeypatch):
    monkeypatch.delenv("OSCR_DB", raising=False)
    code, out = run(capsys, "--json", "search", "sonic", "--limit", "3")
    o = json.loads(out)
    assert code == 0 and o["entries_in_database"] > 23000 and len(o["results"]) == 3
    code, out = run(capsys, "--json", "search", "zzzznaoexiste")
    assert code == 1


def test_dump_simulado_com_a_base_do_projeto_nao_acha_o_padrao_mock(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OSCR_DB", raising=False)
    code, out = run(capsys, "--simulate", "--json", "dump", "-s", "mock", "-o", str(tmp_path / "m"))
    o = json.loads(out)
    assert code == 0 and o["game"] is None                      # a base foi carregada (a chave "game" existe), mas o padrão do simulador não é um jogo
