# SPDX-License-Identifier: GPL-3.0-or-later
"""Leitura do GBA 369-in-1 (F-18, D174): as mesmas regras de firmware/oscr/include/dumper/Gba369.h (o teste de paridade confere os números).
`mapper` do DUMP_ROM = 0x8000 | (bloco << 8); `prg_kb` = tamanho em MB (0 só no bloco 0: lê os 256 MB, "Read 256MB" do OSCR)."""
from __future__ import annotations

FLAG = 0x8000
BANK_MB = 32
TOTAL_MB = 256
MAX_BLOCK = 63


def code(block: int) -> int:
    return FLAG | (block << 8)


def error(block: int, mb: int) -> str | None:
    """None se o pedido vale; senão a chave da mensagem (cli/messages.py)."""
    if not 0 <= block <= MAX_BLOCK:
        return "gba369.block"
    if mb == 0:
        return None if block == 0 else "gba369.size0"
    if not 0 < mb <= BANK_MB or (mb >= 4 and mb % 4):
        return "gba369.size"
    if (block * 4) % BANK_MB + mb > BANK_MB:
        return "gba369.bank"
    return None


def nbytes(mb: int) -> int:
    return (mb or TOTAL_MB) << 20
