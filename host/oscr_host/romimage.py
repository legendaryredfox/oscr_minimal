# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara um arquivo para o WRITE_ROM: tira o cabeçalho iNES e acha chip, PRG e CHR.

No OSCR original isso era feito pelo firmware lendo o arquivo do SD (NES.cpp: `A29040B_writeFlash` lê o cabeçalho de 16 bytes e
`writeFlash` do NES Maker usa o arquivo cru); aqui é o PC que faz, e o firmware recebe só o chip, os tamanhos e os dados."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Valor do campo "chip" do WRITE_ROM (firmware/oscr/include/dumper/NesFlash.h) e o mapper do cartucho de cada chip.
CHIPS = {"nesmaker": 1, "a29040b": 2}
CHIP_MAPPER = {"nesmaker": 30, "a29040b": 0}
CHIP_LABEL = {"nesmaker": "NES Maker (SST 39SF040, mapper 30)", "a29040b": "A29040B (mapper 0)"}


@dataclass
class RomImage:
    body: bytes                 # PRG e depois CHR, sem cabeçalho
    prg_kb: int
    chr_kb: int
    mapper: Optional[int]       # do cabeçalho iNES; None se o arquivo era cru


def split_image(data: bytes, chip: str) -> RomImage:
    """Levanta ValueError (texto para o usuário) se o arquivo não serve para o chip."""
    if data[:4] == b"NES\x1a":
        if len(data) < 16:
            raise ValueError("cabeçalho iNES incompleto")
        if data[6] & 4:
            raise ValueError("o arquivo tem trainer de 512 bytes; remova o trainer antes de gravar")
        prg, chr_ = data[4] * 16, data[5] * 8
        mapper = (data[6] >> 4) | (data[7] & 0xF0)
        body = data[16:]
        if len(body) != (prg + chr_) * 1024:
            raise ValueError(f"o arquivo tem {len(body)} bytes depois do cabeçalho, mas o cabeçalho diz PRG {prg} KB e CHR {chr_} KB")
        return RomImage(body, prg, chr_, mapper)
    if chip == "a29040b":
        raise ValueError("o A29040B precisa de um arquivo .nes com cabeçalho iNES (PRG e CHR vêm do cabeçalho)")
    if len(data) == 0 or len(data) % 16384:
        raise ValueError("arquivo cru: o tamanho precisa ser múltiplo de 16 KB (use um .nes com cabeçalho, ou o PRG cru)")
    return RomImage(data, len(data) // 1024, 0, None)


def infer_chip(img: RomImage) -> Optional[str]:
    for name, m in CHIP_MAPPER.items():
        if img.mapper == m:
            return name
    return None
