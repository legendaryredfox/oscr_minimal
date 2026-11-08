# SPDX-License-Identifier: GPL-3.0-or-later
"""Verificação do checksum do cabeçalho depois do dump (Mega Drive, SNES, GBA, Game Boy).

Serve para pegar tamanho errado, contato ruim ou ROM corrompida. Não substitui o CRC32 do No-Intro:
alguns jogos têm checksum errado de fábrica ("mismatch" pode ser normal em ROMs modificadas ou antigas).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import protocol as P


@dataclass
class Check:
    status: str                 # "ok", "mismatch" ou "na" (não se aplica / sem cabeçalho)
    name: str = ""              # qual checksum
    expected: Optional[int] = None
    computed: Optional[int] = None

    def __str__(self) -> str:
        from .cli.messages import tr          # import tardio: o pacote cli importa este módulo
        if self.status == "ok":
            return tr("check.ok", name=self.name, value=self.expected)
        if self.status == "mismatch":
            return tr("check.mismatch", name=self.name, expected=self.expected, computed=self.computed)
        return ""


def _md(data: bytes) -> Check:
    if len(data) < 0x200 or data[0x100:0x104] != b"SEGA":
        return Check("na")
    exp = int.from_bytes(data[0x18E:0x190], "big")
    body = data[0x200:]
    if len(body) % 2:
        body += b"\x00"
    total = sum(int.from_bytes(body[i:i + 2], "big") for i in range(0, len(body), 2)) & 0xFFFF
    return Check("ok" if total == exp else "mismatch", "Mega Drive", exp, total)


def _gba(data: bytes) -> Check:
    if len(data) < 0xC0 or data[4:8] != bytes([0x24, 0xFF, 0xAE, 0x51]):
        return Check("na")
    comp = (-(sum(data[0xA0:0xBD]) + 0x19)) & 0xFF
    return Check("ok" if comp == data[0xBD] else "mismatch", "GBA", data[0xBD], comp)


def _snes(data: bytes) -> Check:
    for pos in (0x7FC0, 0xFFC0):
        if len(data) < pos + 0x20:
            continue
        comp = int.from_bytes(data[pos + 0x1C:pos + 0x1E], "little")
        chk = int.from_bytes(data[pos + 0x1E:pos + 0x20], "little")
        if comp ^ chk != 0xFFFF or data[pos + 0x1C:pos + 0x20] == bytes(4):
            continue
        n = len(data)
        p = 1 << (n.bit_length() - 1)               # maior potência de 2 <= n
        if p == n:
            total = sum(data) & 0xFFFF
        else:
            rest = n - p
            if p % rest:
                return Check("na")
            total = (sum(data[:p]) + sum(data[p:]) * (p // rest)) & 0xFFFF
        return Check("ok" if total == chk else "mismatch", "SNES", chk, total)
    return Check("na")


def _gb(data: bytes) -> Check:
    if len(data) < 0x150 or data[0x104:0x108] != bytes([0xCE, 0xED, 0x66, 0x66]):     # começo do logo da Nintendo
        return Check("na")
    x = 0
    for b in data[0x134:0x14D]:
        x = (x - b - 1) & 0xFF
    return Check("ok" if x == data[0x14D] else "mismatch", "Game Boy", data[0x14D], x)


def verify_rom(system: int, data: bytes) -> Check:
    if system == 6:
        return _gb(data)
    if system == 4:
        return _md(data)
    if system == 5:
        return _gba(data)
    if system == 1:
        return _snes(data)
    return Check("na")


# Tipo de save do GBA, pelas cadeias que o SDK da Nintendo grava na ROM (mesma numeração do OSCR e do --mapper).
_GBA_SAVE_IDS = (
    (b"FLASH1M_V", 5, "Flash 128 KB"),
    (b"FLASH512_V", 4, "Flash 64 KB"),
    (b"FLASH_V", 4, "Flash 64 KB"),
    (b"EEPROM_V", 2, "EEPROM (512 bytes ou 8 KB)"),
    (b"SRAM_F_V", 3, "FRAM 32 KB"),
    (b"SRAM_V", 3, "SRAM 32 KB"),
)


def gba_save_hint(rom: bytes) -> Optional[tuple[int, str, str]]:
    """Procura a cadeia de biblioteca de save na ROM do GBA. -> (tipo, descrição, cadeia) ou None."""
    for needle, code, label in _GBA_SAVE_IDS:
        i = rom.find(needle)
        if i >= 0:
            end = i + len(needle)
            while end < len(rom) and end - i < 20 and 0x30 <= rom[end] <= 0x39:
                end += 1
            return code, label, rom[i:end].decode("ascii", "replace")
    return None


def eeprom_is_4k(save: bytes) -> bool:
    """Ler uma EEPROM de 512 bytes como se fosse de 8 KB repete os mesmos 512 bytes 16 vezes."""
    return len(save) == 8192 and save == save[:512] * 16
