# SPDX-License-Identifier: GPL-3.0-or-later
"""GB Smart Card 32M (F-20, D249): a lista de jogos do "Game Menu" do OSCR, montada com um DETECT por índice.
O firmware acha o jogo N com o `getGames` do OSCR e responde título, ROM e save dele; `status` 5 = o cartucho tem menos jogos (firmware/oscr/include/dumper/GbSmartCore.h)."""
from __future__ import annotations

from typing import Callable, Optional

SID = 33
WHOLE = 0xFF            # --mapper 255: a flash inteira (4 MB, "Flash Menu > Read" do OSCR)
MAX_GAMES = 127         # 4 MB em blocos de 32 KB, menos o menu
ST_OK, ST_NO_CART, ST_BAD_HEADER, ST_PAST_END = 0, 1, 4, 5


def list_games(detect: Callable[[int, int], dict]) -> Optional[list[dict]]:
    """`detect(sistema, índice)` devolve o DETECT_RESP. None = nenhum cartucho; senão a lista (pode ser vazia), parando no primeiro índice sem jogo."""
    games: list[dict] = []
    for n in range(MAX_GAMES):
        r = detect(SID, n)
        st = r.get("status")
        if st in (ST_OK, ST_BAD_HEADER):
            games.append({"index": n, "title": r.get("name", ""), "rom_size": r.get("rom_size", 0), "save_size": r.get("save_size", 0),
                          "header_ok": st == ST_OK})
            continue
        if st == ST_NO_CART and n == 0:
            return None
        break
    return games
