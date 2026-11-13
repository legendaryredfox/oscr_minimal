# SPDX-License-Identifier: GPL-3.0-or-later
"""Nintendo 64 (D158): o que o PC faz no lugar do cartão SD do OSCR.

O OSCR identifica o jogo pelo CRC1 do cabeçalho numa base de dados do cartão SD (tamanho da ROM e tipo de save). O firmware daqui não tem SD:
o `DETECT` devolve `CCCCCCCC IIII TÍTULO` (CRC1, código do jogo e nome do cabeçalho) e o PC consulta a base do projeto (`database/oscr/json/n64.json`,
do oscr-databases) ou usa o que o usuário informar (`--prg` em MB, `--mapper` = tipo de save). Espelho de gui/shared/.../N64Games.kt e de firmware/oscr/include/dumper/N64Core.h."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import database as DB

MIN_MB, MAX_MB = 1, 64                      # o protocolo leva o tamanho em MB no campo prg_kb; o menu do OSCR vai a 128 MB, o maior jogo conhecido tem 64
COMMON_MB = (4, 8, 12, 16, 24, 32, 40, 48, 64)

# Tipos de save do OSCR (campo `mapper` do protocolo)
SAVE_BYTES = {0: 0, 1: 32768, 2: 98304, 4: 131072, 5: 512, 6: 2048}
SAVE_LABEL = {0: "none", 1: "SRAM 32 KB", 2: "SRAM 96 KB", 4: "FlashRAM 128 KB", 5: "EEPROM 4 Kbit", 6: "EEPROM 16 Kbit"}


@dataclass(frozen=True)
class Header:
    crc1: Optional[int]
    game_id: str
    title: str


@dataclass(frozen=True)
class Game:
    name: str
    crc1: int
    crc32: int
    size_mb: int
    save_type: int

    @property
    def save_bytes(self) -> int:
        return SAVE_BYTES.get(self.save_type, 0)

    def to_dict(self) -> dict:
        return {"name": self.name, "crc1": f"{self.crc1:08X}", "crc32": f"{self.crc32:08X}", "rom_mb": self.size_mb,
                "save_type": self.save_type, "save_label": SAVE_LABEL.get(self.save_type, "?")}


_HEADER = re.compile(r"^([0-9A-Fa-f]{8}) (.{4}) ?(.*)$")


def parse_detect_name(name: str) -> Header:
    """`CCCCCCCC IIII TÍTULO` do DETECT do N64 (firmware/oscr/include/dumper/N64Core.h, formatName). Fora do formato: sem CRC1."""
    m = _HEADER.match(name or "")
    if not m:
        return Header(None, "", (name or "").strip())
    return Header(int(m.group(1), 16), m.group(2), m.group(3).strip().replace("_", " "))


_cache: dict[str, dict[int, list[Game]]] = {}


def load_games(path: Optional[Path] = None) -> dict[int, list[Game]]:
    """Registros de `database/oscr/json/n64.json` por CRC1 (o mesmo CRC1 pode ter mais de um jogo: variantes iguais no cabeçalho)."""
    p = Path(path) if path else DB.BUILTIN_DIR / "json" / "n64.json"
    key = str(p)
    if key in _cache:
        return _cache[key]
    out: dict[int, list[Game]] = {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for r in data.get("records", []):
            g = Game(str(r["name"]), int(str(r["crc1"]), 16), int(str(r["crc32"]), 16), int(r["size"]), int(r.get("saveType", 0)))
            out.setdefault(g.crc1, []).append(g)
    except (OSError, ValueError, KeyError):
        out = {}
    _cache[key] = out
    return out


def lookup(crc1: Optional[int], path: Optional[Path] = None) -> list[Game]:
    return [] if crc1 is None else list(load_games(path).get(crc1, []))


def distinct_options(games: list[Game]) -> bool:
    """True se as entradas do mesmo CRC1 pedem tamanho ou save diferentes (a escolha é do usuário)."""
    return len({(g.size_mb, g.save_type) for g in games}) > 1


def size_valid(mb: int) -> bool:
    return MIN_MB <= mb <= MAX_MB


def save_type_valid(t: int) -> bool:
    return t in SAVE_BYTES


def enrich_detect(r: dict, path: Optional[Path] = None) -> dict:
    """Troca nome, tamanhos e tipo de save do DETECT pelos da base (se achou o CRC1) e acrescenta `n64` ao resultado. Devolve uma cópia."""
    h = parse_detect_name(r.get("name", ""))
    games = lookup(h.crc1, path)
    out = dict(r)
    info = {"crc1": f"{h.crc1:08X}" if h.crc1 is not None else None, "game_id": h.game_id, "title": h.title, "found": bool(games)}
    out["name"] = h.title
    if games:
        g = games[0]
        out["name"] = g.name
        out["rom_size"] = g.size_mb << 20
        out["save_size"] = g.save_bytes
        out["save_type"] = g.save_type
        info.update(g.to_dict())
        info["others"] = len(games) - 1
        info["ambiguous"] = distinct_options(games)
    out["n64"] = info
    return out
