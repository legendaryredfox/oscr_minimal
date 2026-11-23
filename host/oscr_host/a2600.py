# SPDX-License-Identifier: GPL-3.0-or-later
"""Mappers do Atari 2600 (F-20, D206): os ids do `readROM` do núcleo Atari2600.cpp do OSCR e o tamanho que cada um lê.
A mesma tabela está em firmware/oscr/include/dumper/AtariCore.h e em gui/shared/.../A2600.kt (host/tests/test_a2600.py confere as três).
Os nomes são nomes próprios (não são traduzidos)."""
from __future__ import annotations

VARIABLE = 0   # E7: 8, 12 ou 16 KB, o núcleo descobre pelo conteúdo

# id -> (nome, KB)
MAPPERS: dict[int, tuple[str, int]] = {
    0x20: ("2K standard", 2), 0xC0: ("CV 2K", 2), 0x40: ("4K standard", 4), 0x3F: ("3F (Tigervision) 8K", 8),
    0xE0: ("E0 8K", 8), 0xF8: ("F8 8K", 8), 0x08: ("F8SC 8K (RAM)", 8), 0xF9: ("F9 (Time Pilot) 8K", 8),
    0xFE: ("FE 8K", 8), 0x0A: ("UA 8K", 8), 0xD0: ("DPC 10K", 10), 0xFA: ("FA 12K", 12),
    0xE7: ("E7 8/12/16K", VARIABLE), 0xF6: ("F6 16K", 16), 0x06: ("F6SC 16K (RAM)", 16), 0x3E: ("3E 32K (RAM 32K)", 32),
    0xF4: ("F4 32K", 32), 0x04: ("F4SC 32K (RAM)", 32), 0xF0: ("F0 64K", 64), 0x07: ("X07 64K", 64),
    0xDF: ("DFSC 128K", 128), 0xBA: ("SUPERbank 128K", 128), 0xBB: ("SUPERbank 256K", 256),
}


def rom_kb(mapper: int) -> int | None:
    """KB que o mapper lê; `VARIABLE` (0) para o E7; None se o id não existe."""
    m = MAPPERS.get(mapper)
    return None if m is None else m[1]
