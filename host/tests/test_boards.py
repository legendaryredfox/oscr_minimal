# SPDX-License-Identifier: GPL-3.0-or-later
"""Perfis das placas e a decisão de gravar o firmware (D162)."""
import hashlib
import json
from pathlib import Path

import pytest

from oscr_host import boards as B
from oscr_host import protocol as P

ALL = frozenset(range(1, 12))


def info(systems=ALL, firmware="0.2.0", board=True, volt=False):
    return {"system_ids": sorted(systems), "firmware": firmware, "board_profile": board, "voltage_select": volt}


def img(systems=ALL, fw=(0, 2, 0), id="completa"):
    return B.Image(id, Path("/x.hex"), fw, frozenset(systems), "0" * 64)


def test_cada_placa_resolve_na_versao_atual_e_numa_versao_dada():
    for name in B.board_names():
        p = B.resolve(name)
        assert p.systems and p.slots and p.version == B.load_profiles()[name]["atual"]
    assert B.resolve("16_bits@v1.2").voltage_select is False
    assert B.resolve("16_bits@1.3").voltage_select is True            # o "v" é opcional
    assert B.resolve("completa").systems == ALL


def test_placa_ou_versao_desconhecida():
    with pytest.raises(B.BoardError, match="placa desconhecida"):
        B.resolve("zx_spectrum")
    with pytest.raises(B.BoardError, match="versão desconhecida"):
        B.resolve("snes@v9.9")


def test_seletor_so_nas_versoes_com_o_jumper_j1():
    assert B.resolve("snes").voltage_select is False                 # SA-1 precisa de 5 V: sem seletor
    assert B.resolve("n64").voltage_select is False                  # placa de 3,3 V
    assert B.resolve("nes@v1.0").voltage_select is False and B.resolve("nes@v1.1").voltage_select is True


def test_tudo_certo_nao_faz_nada():
    p = B.resolve("snes")
    assert B.plan(p, info(volt=False), {"stored": True, "voltage_select": False}, [img()]).action == "none"


def test_perfil_ainda_nao_guardado_so_grava_o_perfil():
    p = B.resolve("nes@v1.1")                                         # tem seletor
    pl = B.plan(p, info(volt=False), {"stored": False, "voltage_select": False}, [img()])
    assert pl.action == "set_profile" and pl.profile_flags == P.BOARD_VOLT_SELECT


def test_seletor_diferente_com_board_so_grava_o_perfil_sem_gravar_firmware():
    p = B.resolve("nes@v1.0")                                         # sem seletor, firmware com seletor
    pl = B.plan(p, info(volt=True), {"stored": True, "voltage_select": True}, [img()])
    assert pl.action == "set_profile" and pl.profile_flags == 0


def test_sistema_que_falta_pede_a_gravacao_da_imagem():
    p = B.resolve("n64")
    pl = B.plan(p, info(systems=ALL - {11}), {"stored": True}, [img()])
    assert pl.action == "flash" and pl.image is not None and any("n64" in r for r in pl.reasons)


def test_firmware_sem_board_e_seletor_errado_pede_gravacao():
    p = B.resolve("nes@v1.1")
    pl = B.plan(p, info(board=False, volt=False), None, [img()])
    assert pl.action == "flash" and any("BOARD" in r for r in pl.reasons)


def test_firmware_sem_board_mas_que_serve_nao_regrava():
    p = B.resolve("nes@v1.0")                                         # sem seletor e o firmware velho também não tem: funciona como está
    assert B.plan(p, info(board=False, volt=False), None, [img()]).action == "none"


def test_sem_resposta_do_arduino_grava_a_imagem():
    pl = B.plan(B.resolve("snes"), None, None, [img()])
    assert pl.action == "flash" and "não respondeu" in pl.reasons[0]


def test_sem_imagem_conhecida_e_sem_resposta_e_nao_suportado():
    assert B.plan(B.resolve("snes"), None, None, []).action == "unsupported"
    assert B.plan(B.resolve("n64"), info(systems=ALL - {11}), {"stored": True}, []).action == "unsupported"


def test_imagem_que_nao_cobre_a_placa_nao_serve():
    pl = B.plan(B.resolve("n64"), info(systems=ALL - {11}), {"stored": True}, [img(systems=ALL - {11})])
    assert pl.action == "unsupported"


def test_nao_grava_uma_imagem_que_nao_e_mais_nova_quando_so_faltava_o_perfil_do_board():
    # firmware 0.2.0 já tem BOARD e todos os sistemas; um motivo só pode vir do seletor, que o perfil resolve: nunca chega a pedir gravação
    p = B.resolve("nes@v1.1")
    assert B.plan(p, info(volt=False), {"stored": True}, [img()]).action == "set_profile"


def test_escolhe_a_menor_imagem_que_cobre_e_a_mais_nova_no_empate():
    pequena, grande, nova = img({1, 4, 7}, id="pequena"), img(ALL, id="grande"), img({1, 4, 7}, fw=(0, 3, 0), id="nova")
    assert B.best_image([grande, pequena], frozenset({1, 4})).id == "pequena"
    assert B.best_image([pequena, nova], frozenset({1})).id == "nova"
    assert B.best_image([pequena], frozenset({11})) is None


def test_manifesto_ignora_hex_ausente_e_sha_errado(tmp_path):
    hexp = tmp_path / "a.hex"; hexp.write_text(":00000001FF\n")
    ok = {"id": "completa", "hex": "a.hex", "firmware": "0.2.0", "sistemas": [1, 7], "sha256": hashlib.sha256(hexp.read_bytes()).hexdigest()}
    ruim = dict(ok, id="ruim", sha256="0" * 64)
    falta = dict(ok, id="falta", hex="nao_existe.hex")
    (tmp_path / "manifest.json").write_text(json.dumps({"images": [ok, ruim, falta]}))
    imgs = B.load_images(str(tmp_path))
    assert [i.id for i in imgs] == ["completa"] and imgs[0].firmware == (0, 2, 0) and imgs[0].systems == {1, 7}


def test_perfis_do_pacote_e_o_tsv_do_kotlin_estao_em_dia():
    import subprocess, sys
    r = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "gen_perfis.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
