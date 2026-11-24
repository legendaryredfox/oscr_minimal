# SPDX-License-Identifier: GPL-3.0-or-later
"""Mappers do Atari 5200 e do Atari 7800 (F-20, D209): os ids dos `readROM` dos núcleos Atari5200.cpp e Atari7800.cpp do OSCR e os tamanhos que cada um lê.
A mesma tabela está em firmware/oscr/include/dumper/AtariCore.h e em gui/shared/.../Atari.kt (host/tests/test_atari.py confere as três).
Os nomes são nomes próprios (não são traduzidos)."""
from __future__ import annotations

# id -> nome (os ids do `a5200-mappers` e do `a7800-mappers` do OSCR). Os tamanhos saem de `a5200_kb` e `a7800_kb`.
A5200: dict[int, str] = {0: "Standard 4K/8K/16K/32K", 1: "Two Chip 16K", 2: "Bounty Bob Strikes Back 40K"}
A7800: dict[int, str] = {
    0: "Standard 16K/32K/48K", 1: "SuperGame 128K", 2: "SuperGame 144K [78S9]", 3: "F-18 Hornet 64K [78AB]", 4: "Double Dragon/Rampage 128K [78AC]",
    5: "Realsports Baseball etc. 64K [78S4]", 6: "Karateka (PAL) 64K [78S4]", 7: "Bankset 32K/48K/64K/128K", 8: "Crystal Quest/Bounty Bob 144K",
}
# Mappers que pedem `--prg` (os outros têm tamanho fixo e ignoram o campo)
A5200_SIZED = {0: (4, 8, 16, 32)}
A7800_SIZED = {0: (16, 32, 48), 7: (32, 48, 64, 128)}


def a5200_kb(mapper: int, kb: int) -> int:
    """KB que o `readROM` lê; 0 se mapper ou tamanho inválido. Nos mappers de tamanho fixo o `kb` é ignorado."""
    if mapper == 0:
        return kb if kb in (4, 8, 16, 32) else 0
    return {1: 16, 2: 40}.get(mapper, 0)


def _a7800_std(kb: int) -> int:
    return 48 if kb > 32 else (32 if kb > 16 else 16)


def a7800_kb(mapper: int, kb: int) -> int:
    """KB que o `readROM` lê; 0 se mapper ou tamanho inválido. O bankset (7) lê duas vezes: acima de 64 KB o SuperGame de 128 KB, senão o padrão."""
    if mapper == 0:
        return kb if kb in (16, 32, 48) else 0
    if mapper == 7:
        return (256 if kb > 64 else 2 * _a7800_std(kb)) if kb in (32, 48, 64, 128) else 0
    return {1: 128, 2: 144, 3: 64, 4: 128, 5: 64, 6: 64, 8: 144}.get(mapper, 0)


# Atari 8 bits (D210): tamanhos do slot esquerdo (a tabela `romSizes` do núcleo Atari8.cpp); o slot direito é sempre 8 KB.
A8_SIZES = (8, 16, 32, 40, 64, 128)


def a8_kb(slot: int, kb: int) -> int:
    """KB que o `readROM` do 8 bits lê; 0 se inválido. Slot 1 (direito) ignora o tamanho."""
    if slot == 1:
        return 8
    return kb if slot == 0 and kb in A8_SIZES else 0


def lynx_bytes(block: int) -> int:
    """Bytes que o `readROM` do Lynx entrega para o bloco achado por `detectCart` (cabeçalho .lnx de 64 bytes e 256 blocos); 0 se o bloco não é 512, 1024 ou 2048."""
    return 64 + 256 * block if block in (512, 1024, 2048) else 0
