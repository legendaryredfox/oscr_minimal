# SPDX-License-Identifier: GPL-3.0-or-later
"""Conversão mecânica da ordem de bytes de um save, para abrir em emulador (H-1, P-08). Só PC; não abre o dispositivo.

Operações (nome do protocolo da CLI `save-convert --op`):
- `swap16`, `swap32`: troca a ordem dos bytes de cada palavra de 2 ou 4 bytes (N64: SRAM e FlashRAM de alguns emuladores usam a ordem trocada);
- `md-expand-odd`, `md-expand-even`: Mega Drive, SRAM de 8 bits. O save do OSCR traz só os bytes úteis; a expansão leva cada byte para o endereço ímpar
  (`odd`: byte baixo da palavra de 16 bits) ou par (`even`: byte alto) e preenche o outro com `fill` (0xFF por padrão);
- `md-compact-odd`, `md-compact-even`: o inverso (tira os bytes ímpares ou pares de um save de emulador de 16 bits).

Não diz qual emulador espera qual ordem: isso não foi conferido com emulador nenhum (D163). Espelho de gui/shared/.../SaveConv.kt."""
from __future__ import annotations

OPS = ("swap16", "swap32", "md-expand-odd", "md-expand-even", "md-compact-odd", "md-compact-even")


def swap(data: bytes, width: int) -> bytes:
    """Inverte a ordem dos bytes de cada palavra de `width` bytes (2 ou 4). O tamanho precisa ser múltiplo de `width`."""
    if width not in (2, 4):
        raise ValueError("width")
    if len(data) % width:
        raise ValueError("size")
    out = bytearray(len(data))
    for k in range(width):
        out[k::width] = data[width - 1 - k::width]
    return bytes(out)


def md_expand(data: bytes, odd: bool, fill: int = 0xFF) -> bytes:
    """Cada byte vira uma palavra de 16 bits: o byte útil no endereço ímpar (odd) ou par, `fill` no outro."""
    if not 0 <= fill <= 255:
        raise ValueError("fill")
    out = bytearray([fill]) * (2 * len(data))
    out[1 if odd else 0::2] = data
    return bytes(out)


def md_compact(data: bytes, odd: bool) -> bytes:
    """Fica só com os bytes dos endereços ímpares (odd) ou pares. O tamanho precisa ser par."""
    if len(data) % 2:
        raise ValueError("size")
    return bytes(data[1 if odd else 0::2])


def convert(data: bytes, op: str, fill: int = 0xFF) -> bytes:
    if op == "swap16":
        return swap(data, 2)
    if op == "swap32":
        return swap(data, 4)
    if op in ("md-expand-odd", "md-expand-even"):
        return md_expand(data, op.endswith("odd"), fill)
    if op in ("md-compact-odd", "md-compact-even"):
        return md_compact(data, op.endswith("odd"))
    raise ValueError("op")
