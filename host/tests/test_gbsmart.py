# SPDX-License-Identifier: GPL-3.0-or-later
"""GB Smart Card 32M (F-20, D249): sistema 33, lista de jogos por DETECT e a correção do fork no núcleo do OSCR.
As regras puras do firmware estão em firmware/oscr/pc-tests/test_gbs.cpp."""
from __future__ import annotations

import pathlib
import re

from oscr_host import gbsmart as GBS
from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.cli.messages import tr
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED

ROOT = pathlib.Path(__file__).parents[2]


def test_id_e_extensao():
    assert P.SYSTEMS["gbsmart"] == (33, ".gb")
    assert P.SYSTEM_BY_ID[33] == "gbsmart"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))


def test_saiu_dos_planejados():
    assert "gbsmart" not in {k for k, _ in PLANNED}
    assert "gbmem" in {k for k, _ in PLANNED}       # o GB Memory vem no incremento seguinte


def test_opcoes_e_cli():
    assert cmd_info.SYSTEM_OPTIONS["gbsmart"] == ["mapper"]
    a = build_parser().parse_args(["dump", "-s", "gbsmart", "--mapper", "3"])
    assert a.system == "gbsmart" and a.mapper == 3
    b = build_parser().parse_args(["save-write", "-s", "gbsmart", "--mapper", "1", "-i", "x.sav"])
    assert b.mapper == 1


def _fake(games: list[tuple[str, int, int, int]], cart: bool = True):
    calls = []

    def detect(sid, n):
        calls.append((sid, n))
        if not cart:
            return {"status": 1}
        if n < len(games):
            t, rom, save, st = games[n]
            return {"status": st, "name": t, "rom_size": rom, "save_size": save}
        return {"status": 5}
    return detect, calls


def test_lista_para_no_primeiro_indice_sem_jogo():
    det, calls = _fake([("TETRIS", 32768, 0, 0), ("POKEMON", 1048576, 32768, 0), ("ZELDA", 524288, 8192, 4)])
    g = GBS.list_games(det)
    assert [x["title"] for x in g] == ["TETRIS", "POKEMON", "ZELDA"]
    assert [x["index"] for x in g] == [0, 1, 2]
    assert g[1]["save_size"] == 32768 and g[2]["header_ok"] is False
    assert calls[-1] == (33, 3) and len(calls) == 4


def test_sem_cartucho_e_lista_vazia():
    det, _ = _fake([], cart=False)
    assert GBS.list_games(det) is None
    det, _ = _fake([])
    assert GBS.list_games(det) == []


def test_limite_de_indices():
    det, calls = _fake([("X", 32768, 0, 0)] * 200)
    assert len(GBS.list_games(det)) == GBS.MAX_GAMES == 127
    assert len(calls) == 127


def test_constantes_iguais_ao_firmware():
    h = (ROOT / "firmware/oscr/include/dumper/GbSmartCore.h").read_text()
    assert re.search(r"kWhole = 0xFF\b", h) and re.search(r"kMaxGames = 127\b", h) and re.search(r"kPastEnd = 5\b", h)
    assert re.search(r"SYS_GBSMART = 33\b", (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text())


def test_correcao_do_fork_no_nucleo():
    """D249: o `cartOn` do GB Smart não volta mais a lista ao banco 2 (o `getGames` o chama a cada página); o `gameMenu` faz isso uma vez."""
    src = (ROOT / "firmware/oscr/src/cores/GameBoySmart.cpp").read_text()
    on = src[src.index("void cartOn()"):src.index("void cartOff()")]
    assert "gameMenuStartBank = 0x02;" not in on
    menu = src[src.index("void gameMenu()"):src.index("void flashMenu()")]
    assert menu.index("gameMenuStartBank = 0x02;") < menu.index("do")


def test_textos_nos_quatro_idiomas():
    for lang in ("pt-BR", "en", "ru", "zh-CN"):
        from oscr_host.cli import messages
        messages.set_lang(lang)
        assert "255" in tr("gbs.hint") and "{" not in tr("gbs.header", n=2)
        assert tr("detect.status.5")
    messages.set_lang("pt-BR")
