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
# No SNES o campo é (disposição << 8) | fiação (SNES_WIRING); `chip_code()` monta o valor final.
CHIPS = {"nesmaker": 1, "a29040b": 2, "snes-lorom": 1, "snes-hirom": 2, "md-flash": 1,
         "snes-lorom-p0": 1, "snes-hirom-p0": 2, "snes-exlorom-p1": 3, "snes-exhirom-p1": 4, "gba-flash": 1}
CHIP_MAPPER = {"nesmaker": 30, "a29040b": 0, "snes-lorom": 0, "snes-hirom": 0, "md-flash": 0,
               "snes-lorom-p0": 0, "snes-hirom-p0": 0, "snes-exlorom-p1": 0, "snes-exhirom-p1": 0, "gba-flash": 0}
CHIP_LABEL = {"nesmaker": "NES Maker (SST 39SF040, mapper 30)", "a29040b": "A29040B (mapper 0)",
              "snes-lorom": "SNES flash CFI (fiação LoROM)", "snes-hirom": "SNES flash CFI (fiação HiROM)",
              "md-flash": "Mega Drive flash (MX29F1610 2 MB ou S29GL064N 4 MB)",
              "gba-flash": "GBA flash (Intel 4000/4400, MX29GL128E, MSP55LV128, PC28F256M29, M29W128GH, 369-in-1)",
              "snes-lorom-p0": "SNES flash de 8 bits, LoROM (P0)", "snes-hirom-p0": "SNES flash de 8 bits, HiROM (P0)",
              "snes-exlorom-p1": "SNES flash de 8 bits, ExLoROM (P1)", "snes-exhirom-p1": "SNES flash de 8 bits, ExHiROM (P1)"}
SNES_CFI_CHIPS = ("snes-lorom", "snes-hirom")                     # menus "CFI LoROM / CFI HiROM": flash CFI de 1, 2 ou 4 chips (--layout)
SNES_GENERIC_CHIPS = ("snes-lorom-p0", "snes-hirom-p0", "snes-exlorom-p1", "snes-exhirom-p1")   # menus P0 e P1: tipo do flash informado (--flash-type)
SNES_CHIPS = SNES_CFI_CHIPS + SNES_GENERIC_CHIPS
# Disposição do flash CFI (parte alta do campo chip; firmware/oscr/include/dumper/SnesPlan.h).
SNES_LAYOUTS = {"1x": 0, "2x2mb": 1, "2x4mb": 2, "4x2mb": 3, "1x8mb": 4}
SNES_GENERIC = 0x10
# FlashType do OSCR (Flash.h) e o que cada tipo exige. Tipos com setor/buffer: o OSCR achava no banco CRDB; aqui o usuário informa.
FLASH_TYPES = {"29f032": 1, "29f1610": 2, "lh28f0xx": 3, "29f1601": 4, "29lv640": 5, "29f800": 6, "29gl": 7, "e28fxxxj3a": 8}
FLASH_TYPES_NEED_SECTOR = ("29gl", "lh28f0xx", "e28fxxxj3a")
MD_MAX_BYTES = 4 * 1024 * 1024
GBA_MAX_BYTES = 32 * 1024 * 1024               # flash de 1 chip; o 369-in-1 vai até 256 MB (bloco 0) ou até o fim da memória (bloco N, de 4 MB)
GBA_369_MAX_BYTES = 256 * 1024 * 1024
GBA_VERIFY_MAX_BYTES = 64 * 1024 * 1024 - 1024   # prg_kb do DUMP_ROM é u16 (KB)
SNES_CAPACITIES_KB = (2048, 4096)     # as opções "1x 2MB" e "1x 4MB" do OSCR


@dataclass
class RomImage:
    body: bytes                 # PRG e depois CHR, sem cabeçalho
    prg_kb: int
    chr_kb: int
    mapper: Optional[int]       # do cabeçalho iNES; None se o arquivo era cru
    flash_kb: int = 0           # só no SNES: capacidade do chip de flash em KB (vai no campo prg_kb do WRITE_ROM); prg_kb é o tamanho da ROM
    layout: int = 0             # só no SNES: disposição (SNES_LAYOUTS) ou SNES_GENERIC
    wire_chr: int = 0           # só no SNES genérico: campo chr_kb do WRITE_ROM (tipo | setor << 4 | buffer << 9)
    rom: Optional[bytes] = None  # SNES: a ROM original, que a conferência compara com o que a leitura devolve (body vem reordenado e completado)
    block: int = 0              # só no GBA 369-in-1: bloco de 4 MB (0 a 63) onde a gravação começa


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


MB = 1 << 20


def snes_plan(layout: int, size: int, cap_bytes: int = 0) -> list[tuple[int, int, int, int]]:
    """Espelho de `plan()` em firmware/oscr/include/dumper/SnesPlan.h: lista de (chip 1..4, endereço no chip, bytes, deslocamento no arquivo).
    É a regra do `adjustFileSizeOffset` e do `writeCFI` do OSCR. A ordem é a dos trechos no fluxo. Lista vazia = tamanho ou disposição inválidos."""
    if size == 0 or size % 512:
        return []
    if layout == 0:
        return [(1, 0, size, 0)] if cap_bytes in (2 * MB, 4 * MB) and size <= cap_bytes else []
    if layout == 1:
        return [(1, 0, min(size, 2 * MB), 0), (2, 0, max(size - 2 * MB, 0), 2 * MB)] if size <= 4 * MB else []
    if layout == 2:
        return [(1, 0, size - 4 * MB, 4 * MB), (2, 0, 4 * MB, 0)] if 6 * MB <= size <= 8 * MB else []
    if layout == 3:
        return [(1, 0, 2 * MB, 4 * MB), (2, 0, 2 * MB if size > 6 * MB else 0, 6 * MB), (3, 0, 2 * MB, 0), (4, 0, 2 * MB, 2 * MB)] if 6 * MB <= size <= 8 * MB else []
    if layout == 4:
        return [(1, 0, size - 4 * MB, 4 * MB), (1, 4 * MB, 4 * MB, 0)] if size in (6 * MB, 8 * MB) else []
    return []


SNES_LAYOUT_TOTAL_KB = {1: 4096, 2: 8192, 3: 8192, 4: 8192}      # capacidade total de cada disposição (prg_kb do WRITE_ROM); a de 1 chip é 2048 ou 4096


def _snes_strip_header(data: bytes) -> bytes:
    """Tira o cabeçalho de copiadora (512 bytes, quando o tamanho é múltiplo de 1024 mais 512)."""
    if len(data) % 1024 == 512:
        data = data[512:]
    if len(data) == 0 or len(data) % 1024:
        raise ValueError("a ROM de SNES precisa ter tamanho múltiplo de 1 KB (com ou sem o cabeçalho de 512 bytes de copiadora)")
    return data


def split_snes(data: bytes, capacity_kb: Optional[int] = None, layout: str = "1x") -> RomImage:
    """ROM de SNES para o flash CFI (menus "CFI LoROM / CFI HiROM" do OSCR). `layout`: 1x (1 chip de 2 ou 4 MB; `capacity_kb` força a capacidade,
    senão a menor em que a ROM cabe), 2x2mb, 2x4mb, 4x2mb ou 1x8mb. O corpo devolvido é a ROM já reordenada nos trechos de cada chip, na ordem
    em que o firmware os grava. Levanta ValueError (texto para o usuário)."""
    if layout not in SNES_LAYOUTS:
        raise ValueError(f"disposição desconhecida: {layout} (use {', '.join(SNES_LAYOUTS)})")
    rom = _snes_strip_header(data)
    kb = len(rom) // 1024
    lay = SNES_LAYOUTS[layout]
    if lay == 0:
        if capacity_kb is None:
            capacity_kb = next((c for c in SNES_CAPACITIES_KB if kb <= c), None)
            if capacity_kb is None:
                raise ValueError(f"a ROM tem {kb} KB; para mais de 4 MB use --layout 2x4mb, 4x2mb ou 1x8mb (ROM de 6 a 8 MB)")
        elif capacity_kb not in SNES_CAPACITIES_KB:
            raise ValueError("capacidade do flash: 2048 ou 4096 (KB)")
        elif kb > capacity_kb:
            raise ValueError(f"a ROM tem {kb} KB e não cabe em um flash de {capacity_kb} KB")
    else:
        if capacity_kb is not None:
            raise ValueError("--capacity só vale na disposição de 1 chip (1x); as outras têm capacidade fixa")
        capacity_kb = SNES_LAYOUT_TOTAL_KB[lay]
    segs = snes_plan(lay, len(rom), capacity_kb * 1024 if lay == 0 else 0)
    if not segs:
        raise ValueError(f"a ROM de {kb} KB não serve para a disposição {layout} (o OSCR exige 6 a 8 MB nas de 8 MB, no máximo 4 MB em 2x2mb, e 1x8mb só aceita 6 ou 8 MB)")
    body = b"".join(rom[off:off + n] for _c, _a, n, off in segs if n)
    return RomImage(body, kb, 0, None, capacity_kb, lay, 0, rom)


def split_snes_generic(data: bytes, flash_mb: int, flash_type: str, sector_kb: Optional[int] = None, buffer: Optional[int] = None) -> RomImage:
    """ROM de SNES para os menus "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)" do OSCR: flash de 8 bits de tipo informado (no OSCR vinha do banco CRDB).
    Os tipos 29gl, lh28f0xx e e28fxxxj3a precisam de setor (KB) e buffer (bytes), potências de 2; e28fxxxj3a assume 128 KB e 32 bytes se faltarem.
    No 29gl o arquivo é completado com 0xFF até um múltiplo do setor (o OSCR grava setores inteiros). Levanta ValueError."""
    if flash_type not in FLASH_TYPES:
        raise ValueError(f"tipo de flash desconhecido: {flash_type} (use {', '.join(FLASH_TYPES)})")
    if not 1 <= flash_mb <= 8:
        raise ValueError("tamanho do flash: 1 a 8 (MB)")
    rom = _snes_strip_header(data)
    if len(rom) > flash_mb * MB:
        raise ValueError(f"a ROM tem {len(rom) // 1024} KB e não cabe em um flash de {flash_mb} MB")
    if flash_type == "e28fxxxj3a":
        sector_kb = sector_kb or 128
        buffer = buffer or 32
    sec_exp = buf_exp = 0
    if flash_type in FLASH_TYPES_NEED_SECTOR:
        if not sector_kb or not buffer:
            raise ValueError(f"o tipo {flash_type} precisa de --sector-kb (tamanho do setor) e --buffer (bytes do buffer de escrita); veja a folha de dados do chip")
        if sector_kb & (sector_kb - 1) or not 1 <= sector_kb <= 16384:
            raise ValueError("--sector-kb precisa ser potência de 2 (1 a 16384)")
        if buffer & (buffer - 1) or not 2 <= buffer <= 128:
            raise ValueError("--buffer precisa ser potência de 2 (2 a 128)")
        sec_exp, buf_exp = (sector_kb * 1024).bit_length() - 1, buffer.bit_length() - 1
    body = rom
    if flash_type == "29gl":
        sector = sector_kb * 1024
        body = rom + b"\xff" * (-len(rom) % sector)
        if len(body) > flash_mb * MB:
            raise ValueError(f"a ROM completada até um múltiplo do setor ({len(body) // 1024} KB) não cabe em {flash_mb} MB")
    word = FLASH_TYPES[flash_type] | (sec_exp << 4) | (buf_exp << 9)
    return RomImage(body, len(rom) // 1024, 0, None, flash_mb * 1024, SNES_GENERIC, word, rom)


def split_gba(data: bytes, block: int = 0) -> RomImage:
    """ROM de GBA para o flash repro (o firmware identifica o chip pelo ID). Tamanho múltiplo de 1 KB, até 32 MB (no 369-in-1, até 256 MB no bloco 0
    ou até o fim da memória a partir do bloco N). `block` (0 a 63, de 4 MB) só vale no 369-in-1. `prg_kb` é o tamanho em KB (limitado a 65535).
    Levanta ValueError."""
    if not 0 <= block <= 63:
        raise ValueError("o bloco do 369-in-1 vai de 0 a 63")
    if len(data) == 0 or len(data) % 1024:
        raise ValueError("a ROM de GBA precisa ter tamanho múltiplo de 1 KB")
    limit = GBA_369_MAX_BYTES if block == 0 else 4 * 1024 * 1024 * (64 - block)
    if len(data) > limit:
        raise ValueError(f"a ROM tem {len(data) // 1024} KB e passa do que cabe a partir do bloco {block}")
    return RomImage(data, min(len(data) // 1024, 65535), 0, None, block=block)


def chip_code(chip: str, img: "RomImage") -> int:
    """Valor do campo `chip` do WRITE_ROM. No SNES: (disposição << 8) | fiação; no GBA: (bloco << 8) | 1; nos demais, o número do chip."""
    if chip == "gba-flash":
        return (img.block << 8) | 1
    return (img.layout << 8) | CHIPS[chip] if chip in SNES_CHIPS else CHIPS[chip]


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
    exp = img.rom if img.rom is not None else img.body
    diff = None
    if data != exp:
        diff = next((i for i in range(min(len(data), len(exp))) if data[i] != exp[i]), min(len(data), len(exp)))
    return VerifyResult(diff is None, zlib.crc32(data), zlib.crc32(exp), diff, len(data))

