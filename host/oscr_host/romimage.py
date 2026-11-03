# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara um arquivo para o WRITE_ROM: tira o cabeçalho iNES e acha chip, PRG e CHR.

No OSCR original isso era feito pelo firmware lendo o arquivo do SD (NES.cpp: `A29040B_writeFlash` lê o cabeçalho de 16 bytes e
`writeFlash` do NES Maker usa o arquivo cru); aqui é o PC que faz, e o firmware recebe só o chip, os tamanhos e os dados."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Valor do campo "chip" do WRITE_ROM (firmware/oscr/include/dumper/NesFlash.h) e o mapper do cartucho de cada chip.
# SNES (firmware/oscr/include/dumper/SnesFlash.h): flash CFI de um chip só, com a fiação de LoROM ou de HiROM (menu "CFI LoROM / CFI HiROM" do OSCR).
# Mega Drive (firmware/oscr/include/dumper/MdFlash.h): o firmware identifica o chip (MX29F1610 de 2 MB ou S29GL064N de 4 MB) pelo ID.
CHIPS = {"nesmaker": 1, "a29040b": 2, "snes-lorom": 1, "snes-hirom": 2, "md-flash": 1}
CHIP_MAPPER = {"nesmaker": 30, "a29040b": 0, "snes-lorom": 0, "snes-hirom": 0, "md-flash": 0}
CHIP_LABEL = {"nesmaker": "NES Maker (SST 39SF040, mapper 30)", "a29040b": "A29040B (mapper 0)",
              "snes-lorom": "SNES flash CFI (fiação LoROM)", "snes-hirom": "SNES flash CFI (fiação HiROM)",
              "md-flash": "Mega Drive flash (MX29F1610 2 MB ou S29GL064N 4 MB)"}
MD_MAX_BYTES = 4 * 1024 * 1024
SNES_CAPACITIES_KB = (2048, 4096)     # as opções "1x 2MB" e "1x 4MB" do OSCR


@dataclass
class RomImage:
    body: bytes                 # PRG e depois CHR, sem cabeçalho
    prg_kb: int
    chr_kb: int
    mapper: Optional[int]       # do cabeçalho iNES; None se o arquivo era cru
    flash_kb: int = 0           # só no SNES: capacidade do chip de flash em KB (vai no campo prg_kb do WRITE_ROM); prg_kb é o tamanho da ROM


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


def split_snes(data: bytes, capacity_kb: Optional[int] = None) -> RomImage:
    """ROM de SNES para o flash CFI: tira o cabeçalho de copiadora (512 bytes, quando o tamanho é múltiplo de 1024 mais 512) e acha a capacidade
    do chip (a menor de 2 MB ou 4 MB em que a ROM cabe, ou a pedida). Levanta ValueError (texto para o usuário)."""
    if len(data) % 1024 == 512:
        data = data[512:]
    if len(data) == 0 or len(data) % 1024:
        raise ValueError("a ROM de SNES precisa ter tamanho múltiplo de 1 KB (com ou sem o cabeçalho de 512 bytes de copiadora)")
    kb = len(data) // 1024
    if capacity_kb is None:
        capacity_kb = next((c for c in SNES_CAPACITIES_KB if kb <= c), None)
        if capacity_kb is None:
            raise ValueError(f"a ROM tem {kb} KB; o gravador de SNES cobre flash de 1 chip de 2 MB ou 4 MB (as opções com 2 ou 4 chips do OSCR ainda não existem aqui)")
    elif capacity_kb not in SNES_CAPACITIES_KB:
        raise ValueError("capacidade do flash: 2048 ou 4096 (KB)")
    elif kb > capacity_kb:
        raise ValueError(f"a ROM tem {kb} KB e não cabe em um flash de {capacity_kb} KB")
    return RomImage(data, kb, 0, None, capacity_kb)


def split_md(data: bytes) -> RomImage:
    """ROM de Mega Drive para o flash repro: arquivo binário (.md/.bin/.gen) de tamanho par, até 4 MB. ROM entrelaçada (.smd) não é aceita.
    `prg_kb` é o tamanho arredondado para cima (o firmware recebe o tamanho exato em bytes). Levanta ValueError."""
    if len(data) == 0 or len(data) % 2:
        raise ValueError("a ROM de Mega Drive precisa ter tamanho par (arquivo binário .md/.bin/.gen)")
    if len(data) > MD_MAX_BYTES:
        raise ValueError(f"a ROM tem {len(data) // 1024} KB; o flash repro do Mega Drive tem no máximo 4 MB (MX29F1610 2 MB ou S29GL064N 4 MB)")
    if len(data) % 1024 == 512 and data[0x100:0x104] != b"SEGA" and data[512 + 0x100:512 + 0x104] == b"SEGA":
        raise ValueError("o arquivo parece ter o cabeçalho de copiadora de 512 bytes (.smd); use a ROM binária sem cabeçalho")
    return RomImage(data, (len(data) + 1023) // 1024, 0, None)


def infer_chip(img: RomImage) -> Optional[str]:
    for name, m in CHIP_MAPPER.items():
        if img.mapper == m:
            return name
    return None


@dataclass
class VerifyResult:
    ok: bool
    read_crc32: int
    expected_crc32: int
    first_diff: Optional[int]       # offset (dentro de PRG+CHR) do primeiro byte diferente; None se iguais
    read_bytes: int

    def to_dict(self) -> dict:
        return {"ok": self.ok, "read_crc32": f"{self.read_crc32:08X}", "expected_crc32": f"{self.expected_crc32:08X}",
                "first_diff": self.first_diff, "read_bytes": self.read_bytes}


def verify_written(client, system: int, chip: str, img: RomImage, progress=None) -> VerifyResult:
    """Confere a gravação: lê o cartucho de volta (DUMP_ROM com o mapper do chip e os tamanhos gravados) e compara com o que foi enviado.

    O OSCR original só confere cada byte durante a gravação (leituras logo depois de programar); esta leitura completa pega também
    o que mudou depois (um setor apagado por engano, um banco que não responde)."""
    import zlib

    res = client.dump_rom(system, 0, progress, CHIP_MAPPER[chip], img.prg_kb, img.chr_kb)     # SNES: prg_kb = tamanho da ROM; sem cabeçalho iNES
    data = res.data[16:] if res.data[:4] == b"NES\x1a" else res.data      # o firmware acrescenta um cabeçalho iNES sintético
    exp = img.body
    diff = None
    if data != exp:
        diff = next((i for i in range(min(len(data), len(exp))) if data[i] != exp[i]), min(len(data), len(exp)))
    return VerifyResult(diff is None, zlib.crc32(data), zlib.crc32(exp), diff, len(data))

