# SPDX-License-Identifier: GPL-3.0-or-later
"""Nintendo 64 (D158): nome do DETECT, base de jogos por CRC1 e os comandos detect, dump e save-read/save-write com um cliente falso."""
import json
import zlib

import pytest

from oscr_host import n64 as N64
from oscr_host import protocol as P

# jogos reais de database/oscr/json/n64.json
WORLD_IS_NOT_ENOUGH = "033F4C13"          # 007 - The World Is Not Enough (USA): 32 MB, sem save
SNOWBOARD = "58FD3F25"                    # 1080 Snowboarding (Europe): 16 MB, SRAM (tipo 1)
CRUISN = None                             # preenchido abaixo com um jogo de EEPROM


def test_nome_do_detect():
    h = N64.parse_detect_name("3B941695 NSME SUPER_MARIO_64")
    assert h.crc1 == 0x3B941695 and h.game_id == "NSME" and h.title == "SUPER MARIO 64"
    assert N64.parse_detect_name("sem formato").crc1 is None
    assert N64.parse_detect_name("").crc1 is None


def test_base_do_projeto_carrega_e_acha_por_crc1():
    games = N64.load_games()
    assert len(games) > 900
    g = N64.lookup(int(WORLD_IS_NOT_ENOUGH, 16))[0]
    assert g.size_mb == 32 and g.save_type == 0 and "World Is Not Enough" in g.name and g.save_bytes == 0
    s = N64.lookup(int(SNOWBOARD, 16))[0]
    assert s.size_mb == 16 and s.save_type == 1 and s.save_bytes == 32768
    assert N64.lookup(0xDEADBEEF) == [] and N64.lookup(None) == []


def test_tamanhos_de_save_batem_com_o_firmware():
    # firmware/oscr/include/dumper/N64Core.h (saveBytes)
    assert N64.SAVE_BYTES == {0: 0, 1: 32768, 2: 98304, 4: 131072, 5: 512, 6: 2048}
    assert all(N64.save_type_valid(t) for t in (0, 1, 2, 4, 5, 6)) and not N64.save_type_valid(3)
    assert N64.size_valid(1) and N64.size_valid(64) and not N64.size_valid(0) and not N64.size_valid(65)
    tipos = {g.save_type for gs in N64.load_games().values() for g in gs}
    assert tipos <= set(N64.SAVE_BYTES)                       # a base só usa tipos que o firmware conhece


def test_enrich_detect_troca_nome_e_tamanhos():
    r = {"system": 11, "status": 0, "rom_size": 0, "save_size": 0, "save_type": 0, "name": f"{SNOWBOARD} NNSE 1080_SNOWBOARDING"}
    o = N64.enrich_detect(r)
    assert o["rom_size"] == 16 << 20 and o["save_size"] == 32768 and o["save_type"] == 1 and "1080" in o["name"]
    assert o["n64"]["found"] and o["n64"]["crc1"] == SNOWBOARD and o["n64"]["rom_mb"] == 16
    u = N64.enrich_detect({"system": 11, "status": 0, "rom_size": 0, "save_size": 0, "save_type": 0, "name": "AAAAAAAA XXXX FOO_BAR"})
    assert not u["n64"]["found"] and u["name"] == "FOO BAR" and u["rom_size"] == 0


class _Res:
    def __init__(self, data):
        self.data, self.crc32 = data, zlib.crc32(data)


class _Fake:
    """Cliente falso: DETECT do N64 e as leituras; guarda o que a CLI pediu."""
    def __init__(self, name):
        self.name, self.calls, self.save = name, [], bytes(range(256)) * 128

    def detect(self, system, *a):
        self.calls.append(("detect", system))
        return {"system": system, "status": 0, "rom_size": 0, "save_size": 0, "save_type": 0, "name": self.name}

    def dump_rom(self, system, block, progress, mapper, prg, chr_):
        self.calls.append(("dump", system, mapper, prg))
        return _Res(bytes((i * 3) & 0xFF for i in range(1024)))

    def read_save(self, system, block, progress, mapper, ram):
        self.calls.append(("save-read", system, mapper))
        return _Res(self.save[:N64.SAVE_BYTES[mapper]])

    def write_save(self, system, data, block, progress, mapper, ram):
        self.calls.append(("save-write", system, mapper, len(data)))
        return zlib.crc32(data)


class _T:
    def close(self):
        pass


def _cli(monkeypatch, capsys, fake, *argv):
    from oscr_host import cli
    monkeypatch.setattr(cli.common, "connect", lambda a: (fake, _T(), {"write_rom": False, "flash_prog": False}))
    code = cli.main(["--json", *argv])
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1]), fake


def test_detect_mostra_jogo_da_base(monkeypatch, capsys):
    code, o, _ = _cli(monkeypatch, capsys, _Fake(f"{SNOWBOARD} NNSE 1080_SNOWBOARDING"), "detect", "-s", "n64")
    assert code == 0 and o["ok"] and o["n64"]["found"] and o["rom_size"] == 16 << 20 and o["save_size"] == 32768 and o["save_type"] == 1


def test_dump_pega_o_tamanho_da_base_e_a_extensao_z64(monkeypatch, capsys, tmp_path):
    f = _Fake(f"{SNOWBOARD} NNSE 1080_SNOWBOARDING")
    code, o, _ = _cli(monkeypatch, capsys, f, "dump", "-s", "n64", "-o", str(tmp_path / "jogo"))
    assert code == 0 and ("dump", 11, 0, 16) in f.calls and o["file"].endswith(".z64")


def test_dump_com_prg_ignora_a_base(monkeypatch, capsys, tmp_path):
    f = _Fake(f"{SNOWBOARD} NNSE 1080_SNOWBOARDING")
    code, o, _ = _cli(monkeypatch, capsys, f, "dump", "-s", "n64", "--prg", "8", "-o", str(tmp_path / "jogo"))
    assert code == 0 and ("dump", 11, 0, 8) in f.calls


def test_dump_sem_base_pede_o_tamanho(monkeypatch, capsys, tmp_path):
    code, o, f = _cli(monkeypatch, capsys, _Fake("AAAAAAAA XXXX DESCONHECIDO"), "dump", "-s", "n64", "-o", str(tmp_path / "jogo"))
    assert code == 64 and not [c for c in f.calls if c[0] == "dump"]
    assert "--prg" in json.dumps(o)
    code, o, f = _cli(monkeypatch, capsys, _Fake("AAAAAAAA XXXX DESCONHECIDO"), "dump", "-s", "n64", "--prg", "99", "-o", str(tmp_path / "jogo"))
    assert code == 64 and not [c for c in f.calls if c[0] == "dump"]


def test_save_read_usa_o_tipo_da_base(monkeypatch, capsys, tmp_path):
    f = _Fake(f"{SNOWBOARD} NNSE 1080_SNOWBOARDING")
    code, o, _ = _cli(monkeypatch, capsys, f, "save-read", "-s", "n64", "-o", str(tmp_path / "s"))
    assert code == 0 and ("save-read", 11, 1) in f.calls and o["bytes"] == 32768


def test_save_read_jogo_sem_save_e_tipo_invalido(monkeypatch, capsys, tmp_path):
    code, o, f = _cli(monkeypatch, capsys, _Fake(f"{WORLD_IS_NOT_ENOUGH} NWTE 007"), "save-read", "-s", "n64", "-o", str(tmp_path / "s"))
    assert code == 1 and "no_save" in json.dumps(o) and not [c for c in f.calls if c[0] == "save-read"]
    code, o, f = _cli(monkeypatch, capsys, _Fake(f"{SNOWBOARD} NNSE X"), "save-read", "-s", "n64", "--mapper", "3", "-o", str(tmp_path / "s"))
    assert code == 64
    code, o, f = _cli(monkeypatch, capsys, _Fake("AAAAAAAA XXXX DESCONHECIDO"), "save-read", "-s", "n64", "-o", str(tmp_path / "s"))
    assert code == 64
    code, o, f = _cli(monkeypatch, capsys, _Fake("AAAAAAAA XXXX DESCONHECIDO"), "save-read", "-s", "n64", "--mapper", "5", "-o", str(tmp_path / "s"))
    assert code == 0 and ("save-read", 11, 5) in f.calls and o["bytes"] == 512


def test_save_write_com_tipo_informado(monkeypatch, capsys, tmp_path):
    arq = tmp_path / "s.sav"
    arq.write_bytes(bytes(2048))
    f = _Fake("AAAAAAAA XXXX DESCONHECIDO")
    code, o, _ = _cli(monkeypatch, capsys, f, "save-write", "-s", "n64", "--mapper", "6", "-i", str(arq), "--yes", "--no-backup", "--no-verify")
    assert code == 0 and ("save-write", 11, 6, 2048) in f.calls


def test_n64_sai_da_lista_de_planejados_e_entra_nos_sistemas():
    from oscr_host.planned import PLANNED
    assert "n64" not in [k for k, _ in PLANNED]
    assert P.SYSTEMS["n64"] == (11, ".z64") and P.SYSTEM_BY_ID[11] == "n64"


def test_dump_traz_md5_e_sha1(monkeypatch, capsys, tmp_path):
    """P1 (D160): o resultado de dump e save-read traz MD5 e SHA-1 além do CRC32."""
    import hashlib
    f = _Fake(f"{SNOWBOARD} NNSE 1080_SNOWBOARDING")
    code, o, _ = _cli(monkeypatch, capsys, f, "dump", "-s", "n64", "-o", str(tmp_path / "jogo"))
    data = (tmp_path / "jogo.z64").read_bytes()
    assert code == 0 and o["md5"] == hashlib.md5(data).hexdigest().upper() and o["sha1"] == hashlib.sha1(data).hexdigest().upper()
