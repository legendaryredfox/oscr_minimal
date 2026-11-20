# SPDX-License-Identifier: GPL-3.0-or-later
"""Relógio (RTC) do MBC3 do Game Boy (F-17, D192). O firmware manda e recebe 5 bytes, na ordem dos registradores 08h a 0Ch do MBC3: segundos, minutos, horas,
dias (byte baixo) e dias (byte alto: bit 0 = bit 8 dos dias, bit 6 = parado, bit 7 = estouro). Aqui ficam a leitura desses bytes e o rodapé de 48 bytes que
BGB, VBA-M e mGBA põem depois do save (5 registradores ao vivo e 5 travados, 4 bytes cada, mais a hora do PC em segundos Unix, 8 bytes)."""
from __future__ import annotations

import struct

REGS = 5
HALT, CARRY, DAY_HIGH = 0x40, 0x80, 0x01
FOOTER_BYTES = 48
MAX_DAY = 511


class RtcError(ValueError):
    pass


def decode(raw: bytes) -> dict:
    """Valores dos 5 registradores. Bits não usados (acima de 6 em segundos e minutos, de 5 nas horas) são ignorados."""
    if len(raw) != REGS:
        raise RtcError(f"o RTC tem {REGS} bytes, vieram {len(raw)}")
    return {"seconds": raw[0] & 0x3F, "minutes": raw[1] & 0x3F, "hours": raw[2] & 0x1F, "days": ((raw[4] & DAY_HIGH) << 8) | raw[3],
            "halted": bool(raw[4] & HALT), "carry": bool(raw[4] & CARRY)}


def encode(seconds: int, minutes: int, hours: int, days: int, halted: bool = False, carry: bool = False) -> bytes:
    if not (0 <= seconds < 60 and 0 <= minutes < 60 and 0 <= hours < 24 and 0 <= days <= MAX_DAY):
        raise RtcError("hora ou dia fora da faixa")
    return bytes([seconds, minutes, hours, days & 0xFF, (days >> 8) | (HALT if halted else 0) | (CARRY if carry else 0)])


def parse_time(text: str) -> tuple[int, int, int]:
    """`HH:MM:SS` ou `HH:MM` (segundos 0)."""
    parts = text.strip().split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError as e:
        raise RtcError(text) from e
    if len(nums) == 2:
        nums.append(0)
    if len(nums) != 3 or not (0 <= nums[0] < 24 and 0 <= nums[1] < 60 and 0 <= nums[2] < 60):
        raise RtcError(text)
    return nums[0], nums[1], nums[2]


def format_value(d: dict) -> str:
    return f"{d['days']} {d['hours']:02d}:{d['minutes']:02d}:{d['seconds']:02d}"


def footer(raw: bytes, now: int) -> bytes:
    """Rodapé de 48 bytes de save (BGB, VBA-M, mGBA): ao vivo, travado (iguais: o firmware trava antes de ler) e a hora do PC."""
    if len(raw) != REGS:
        raise RtcError(f"o RTC tem {REGS} bytes, vieram {len(raw)}")
    regs = struct.pack("<5I", *raw)
    return regs + regs + struct.pack("<Q", now)


def from_footer(data: bytes) -> bytes:
    """Os 5 registradores ao vivo de um rodapé de 48 bytes (ou de um arquivo de 5 bytes)."""
    if len(data) == REGS:
        return bytes(data)
    if len(data) != FOOTER_BYTES:
        raise RtcError(f"o rodapé do RTC tem {FOOTER_BYTES} bytes, vieram {len(data)}")
    return bytes(v & 0xFF for v in struct.unpack_from("<5I", data, 0))
