# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara um arquivo para o WRITE_ROM: tira o cabeçalho iNES e acha chip, PRG e CHR.

No OSCR original isso era feito pelo firmware lendo o arquivo do SD (NES.cpp: `A29040B_writeFlash` lê o cabeçalho de 16 bytes e
`writeFlash` do NES Maker usa o arquivo cru); aqui é o PC que faz, e o firmware recebe só o chip, os tamanhos e os dados."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ImageError(ValueError):
    """Problema com o arquivo ou com as opções do chip. `str(e)` é o texto no idioma da CLI (catálogo `img.<key>`, D133); os testes e o código que captura ValueError continuam valendo."""

    def __init__(self, key: str, **kw):
        super().__init__(key)
        self.key, self.kw = key, kw

    def __str__(self) -> str:
        from .cli.messages import tr          # import tardio: o pacote cli importa este módulo
        return tr("img." + self.key, **self.kw)

# Valor do campo "chip" do WRITE_ROM (firmware/oscr/include/dumper/NesFlash.h) e o mapper do cartucho de cada chip.
# SNES (firmware/oscr/include/dumper/SnesFlash.h): flash CFI de um chip só, com a fiação de LoROM ou de HiROM (menu "CFI LoROM / CFI HiROM" do OSCR).
# Mega Drive (firmware/oscr/include/dumper/MdFlash.h): o firmware identifica o chip pelo ID (MX29F1610, S29GL064N, chips AMD de 32 e 64 Mbit, MX29L3211, PA28F400, SST39VF).
# No SNES o campo é (disposição << 8) | fiação (SNES_WIRING); `chip_code()` monta o valor final.
CHIPS = {"nesmaker": 1, "a29040b": 2, "snes-lorom": 1, "snes-hirom": 2, "md-flash": 1,
         "snes-lorom-p0": 1, "snes-hirom-p0": 2, "snes-exlorom-p1": 3, "snes-exhirom-p1": 4, "gba-flash": 1,
         "gb-diy-mbc3": 1, "gb-diy-mbc5": 2, "gb-hdr-mbc30": 3, "gb-cam-first": 4, "gb-cam-second": 5, "gb-orange-fm": 6, "gb-39sf-mbc5": 7, "gb-cfi": 8}
CHIP_MAPPER = {"nesmaker": 30, "a29040b": 0, "snes-lorom": 0, "snes-hirom": 0, "md-flash": 0,
               "snes-lorom-p0": 0, "snes-hirom-p0": 0, "snes-exlorom-p1": 0, "snes-exhirom-p1": 0, "gba-flash": 0,
               "gb-diy-mbc3": 0, "gb-diy-mbc5": 0, "gb-hdr-mbc30": 0, "gb-cam-first": 0, "gb-cam-second": 0, "gb-orange-fm": 0, "gb-39sf-mbc5": 0, "gb-cfi": 0}
CHIP_LABEL = {"nesmaker": "NES Maker (SST 39SF040, mapper 30)", "a29040b": "A29040B (mapper 0)",
              "snes-lorom": "SNES flash CFI (fiação LoROM)", "snes-hirom": "SNES flash CFI (fiação HiROM)",
              "md-flash": "Mega Drive flash (o firmware identifica o chip: MX29F1610, S29GL064N, M29W/MX29LV 32 e 64 Mbit, MX29L3211, PA28F400, SST39VF)",
              "gba-flash": "GBA flash (Intel 4000/4400, MX29GL128E, MSP55LV128, PC28F256M29, M29W128GH, 369-in-1)",
              "gb-diy-mbc3": "GB flash 29F, DIY MBC3 (WR)", "gb-diy-mbc5": "GB flash 29F, DIY MBC5 (WR)", "gb-hdr-mbc30": "GB flash 29F, HDR MBC30 (WE no pino de áudio)",
              "gb-cam-first": "GB flash 29F, HDR GameBoy Cam, 1º jogo (apaga)", "gb-cam-second": "GB flash 29F, HDR GameBoy Cam, 2º jogo (sem apagar)",
              "gb-orange-fm": "GB flash 39SF010 sem MBC, Orange FM (32 KB)", "gb-39sf-mbc5": "GB flash 39SF040, MBC5 (WE no pino de áudio)", "gb-cfi": "GB flash CFI",
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
MD_MAX_BYTES = 8 * 1024 * 1024               # o maior chip da tabela do firmware tem 64 Mbit; o firmware recusa ROM maior que o chip encontrado
GB_CHIPS = ("gb-diy-mbc3", "gb-diy-mbc5", "gb-hdr-mbc30", "gb-cam-first", "gb-cam-second", "gb-orange-fm", "gb-39sf-mbc5", "gb-cfi")
GB_MAX_BYTES = 4 * 1024 * 1024
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
            raise ImageError("truncated")
        if data[6] & 4:
            raise ImageError("trainer")
        prg, chr_ = data[4] * 16, data[5] * 8
        mapper = (data[6] >> 4) | (data[7] & 0xF0)
        body = data[16:]
        if len(body) != (prg + chr_) * 1024:
            raise ImageError("size_mismatch", n=len(body), prg=prg, chr=chr_)
        return RomImage(body, prg, chr_, mapper)
    if chip == "a29040b":
        raise ImageError("needs_header")
    if len(data) == 0 or len(data) % 16384:
        raise ImageError("raw_size")
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
        raise ImageError("snes_size")
    return data


def split_snes(data: bytes, capacity_kb: Optional[int] = None, layout: str = "1x") -> RomImage:
    """ROM de SNES para o flash CFI (menus "CFI LoROM / CFI HiROM" do OSCR). `layout`: 1x (1 chip de 2 ou 4 MB; `capacity_kb` força a capacidade,
    senão a menor em que a ROM cabe), 2x2mb, 2x4mb, 4x2mb ou 1x8mb. O corpo devolvido é a ROM já reordenada nos trechos de cada chip, na ordem
    em que o firmware os grava. Levanta ValueError (texto para o usuário)."""
    if layout not in SNES_LAYOUTS:
        raise ImageError("snes_layout", layout=layout, layouts=", ".join(SNES_LAYOUTS))
    rom = _snes_strip_header(data)
    kb = len(rom) // 1024
    lay = SNES_LAYOUTS[layout]
    if lay == 0:
        if capacity_kb is None:
            capacity_kb = next((c for c in SNES_CAPACITIES_KB if kb <= c), None)
            if capacity_kb is None:
                raise ImageError("snes_too_big", kb=kb)
        elif capacity_kb not in SNES_CAPACITIES_KB:
            raise ImageError("snes_capacity")
        elif kb > capacity_kb:
            raise ImageError("snes_no_fit", kb=kb, cap=capacity_kb)
    else:
        if capacity_kb is not None:
            raise ImageError("snes_capacity_fixed")
        capacity_kb = SNES_LAYOUT_TOTAL_KB[lay]
    segs = snes_plan(lay, len(rom), capacity_kb * 1024 if lay == 0 else 0)
    if not segs:
        raise ImageError("snes_bad_layout", kb=kb, layout=layout)
    body = b"".join(rom[off:off + n] for _c, _a, n, off in segs if n)
    return RomImage(body, kb, 0, None, capacity_kb, lay, 0, rom)


def _type_word(flash_type: str, sector_kb: Optional[int], buffer: Optional[int]) -> int:
    """Campo chr_kb do modo genérico de flash de 8 bits: tipo | (log2 do setor em bytes << 4) | (log2 do buffer << 9). Levanta ValueError."""
    if flash_type not in FLASH_TYPES:
        raise ImageError("gen_type", type=flash_type, types=", ".join(FLASH_TYPES))
    if flash_type == "e28fxxxj3a":
        sector_kb = sector_kb or 128
        buffer = buffer or 32
    sec_exp = buf_exp = 0
    if flash_type in FLASH_TYPES_NEED_SECTOR:
        if not sector_kb or not buffer:
            raise ImageError("gen_needs_sector", type=flash_type)
        if sector_kb & (sector_kb - 1) or not 1 <= sector_kb <= 16384:
            raise ImageError("gen_sector")
        if buffer & (buffer - 1) or not 2 <= buffer <= 128:
            raise ImageError("gen_buffer")
        sec_exp, buf_exp = (sector_kb * 1024).bit_length() - 1, buffer.bit_length() - 1
    return FLASH_TYPES[flash_type] | (sec_exp << 4) | (buf_exp << 9)


def split_snes_generic(data: bytes, flash_mb: int, flash_type: str, sector_kb: Optional[int] = None, buffer: Optional[int] = None) -> RomImage:
    """ROM de SNES para os menus "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)" do OSCR: flash de 8 bits de tipo informado (no OSCR vinha do banco CRDB).
    Os tipos 29gl, lh28f0xx e e28fxxxj3a precisam de setor (KB) e buffer (bytes), potências de 2; e28fxxxj3a assume 128 KB e 32 bytes se faltarem.
    No 29gl o arquivo é completado com 0xFF até um múltiplo do setor (o OSCR grava setores inteiros). Levanta ValueError."""
    if flash_type not in FLASH_TYPES:
        raise ImageError("gen_type", type=flash_type, types=", ".join(FLASH_TYPES))
    if not 1 <= flash_mb <= 8:
        raise ImageError("gen_mb")
    rom = _snes_strip_header(data)
    if len(rom) > flash_mb * MB:
        raise ImageError("gen_no_fit", kb=len(rom) // 1024, mb=flash_mb)
    word = _type_word(flash_type, sector_kb, buffer)
    body = rom
    if flash_type == "29gl":
        sector = sector_kb * 1024
        body = rom + b"\xff" * (-len(rom) % sector)
        if len(body) > flash_mb * MB:
            raise ImageError("gen_padded_no_fit", kb=len(body) // 1024, mb=flash_mb)
    return RomImage(body, len(rom) // 1024, 0, None, flash_mb * 1024, SNES_GENERIC, word, rom)


def split_gba(data: bytes, block: int = 0) -> RomImage:
    """ROM de GBA para o flash repro (o firmware identifica o chip pelo ID). Tamanho múltiplo de 1 KB, até 32 MB (no 369-in-1, até 256 MB no bloco 0
    ou até o fim da memória a partir do bloco N). `block` (0 a 63, de 4 MB) só vale no 369-in-1. `prg_kb` é o tamanho em KB (limitado a 65535).
    Levanta ValueError."""
    if not 0 <= block <= 63:
        raise ImageError("gba_block")
    if len(data) == 0 or len(data) % 1024:
        raise ImageError("gba_size")
    limit = GBA_369_MAX_BYTES if block == 0 else 4 * 1024 * 1024 * (64 - block)
    if len(data) > limit:
        raise ImageError("gba_too_big", kb=len(data) // 1024, block=block)
    return RomImage(data, min(len(data) // 1024, 65535), 0, None, block=block)


def split_gb(data: bytes, chip: str) -> RomImage:
    """ROM de Game Boy para o flash repro: tamanho múltiplo de 16 KB (um banco), de 32 KB a 4 MB; o Orange FM (sem MBC) grava só 32 KB.
    O número de bancos o firmware tira do tamanho. Levanta ValueError."""
    if len(data) < 32768 or len(data) % 16384:
        raise ImageError("gb_size")
    if len(data) > GB_MAX_BYTES:
        raise ImageError("gb_too_big", kb=len(data) // 1024)
    if chip == "gb-orange-fm" and len(data) != 32768:
        raise ImageError("gb_orange")
    return RomImage(data, len(data) // 1024, 0, None)


def chip_code(chip: str, img: "RomImage") -> int:
    """Valor do campo `chip` do WRITE_ROM. No SNES: (disposição << 8) | fiação; no GBA: (bloco << 8) | 1; nos demais, o número do chip."""
    if chip == "gba-flash":
        return (img.block << 8) | 1
    return (img.layout << 8) | CHIPS[chip] if chip in SNES_CHIPS else CHIPS[chip]


def split_md(data: bytes) -> RomImage:
    """ROM de Mega Drive para o flash repro: arquivo binário (.md/.bin/.gen) de tamanho par, até 8 MB. ROM entrelaçada (.smd) não é aceita.
    `prg_kb` é o tamanho arredondado para cima (o firmware recebe o tamanho exato em bytes). Levanta ValueError."""
    if len(data) == 0 or len(data) % 2:
        raise ImageError("md_size")
    if len(data) > MD_MAX_BYTES:
        raise ImageError("md_too_big", kb=len(data) // 1024)
    if len(data) % 1024 == 512 and data[0x100:0x104] != b"SEGA" and data[512 + 0x100:512 + 0x104] == b"SEGA":
        raise ImageError("md_smd")
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


def verify_save_written(client, system: int, data: bytes, progress=None, mapper: int = 0, ram_kb: int = 0) -> VerifyResult:
    """Confere a gravação do save: lê o save de volta (READ_SAVE com as mesmas opções) e compara byte a byte com o que foi enviado.

    O OSCR original relia o arquivo do cartão SD; o WRITE_SAVE do fork não relê, então a conferência fica no PC.
    Tamanho diferente conta como diferença (o primeiro byte além do menor)."""
    import zlib

    res = client.read_save(system, 0, progress, mapper, ram_kb)
    got = res.data
    diff = None
    if got != data:
        diff = next((i for i in range(min(len(got), len(data))) if got[i] != data[i]), min(len(got), len(data)))
    return VerifyResult(diff is None, zlib.crc32(got), zlib.crc32(data), diff, len(got))


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


# ---------------------------------------------------------------- programador de flash genérico (sistema 7)
FLASHPROG_BUS = {"8": 1, "plcc32": 2, "16": 3, "eprom": 4, "md": 5}      # parte baixa do campo chip (firmware/oscr/include/dumper/FlashProg.h); "md" só identifica
FLASHPROG_LABEL = {"8": "flash de 8 bits (adaptador de flash)", "plcc32": "flash de 8 bits PLCC32 (adaptador de SNES)",
                   "16": "flash de 16 bits", "eprom": "EPROM 27C322 (4 MB)", "md": "flash do cartucho de Mega Drive"}
DETECT_ONLY_BUS = ("md",)       # barramentos que só valem em flash-id; ler, apagar e gravar o cartucho de Mega Drive são `dump` e `rom-write`
EPROM_KB = 4096


@dataclass
class FlashJob:
    chip: int                   # campo chip do comando
    prg_kb: int                 # tamanho do chip em KB
    chr_word: int               # campo chr_kb: tipo | setor << 4 | buffer << 9 (só no flash de 8 bits)
    body: bytes = b""           # o que vai ao chip (no 29gl, completado com 0xFF até um múltiplo do setor)
    rom: bytes = b""            # o arquivo original, que a conferência compara com a leitura


def flashprog_params(bus: str, flash_kb: Optional[int], flash_type: Optional[str] = None, sector_kb: Optional[int] = None,
                     buffer: Optional[int] = None, need_type: bool = False, detect: bool = False) -> FlashJob:
    """Campos do comando para um chip. No flash de 8 bits o tipo é obrigatório para apagar e gravar (`need_type`), opcional para ler e identificar.
    `detect` = só identificar (flash-id): é o único caso em que o barramento "md" vale, e ele não leva tamanho nem tipo.
    Levanta ValueError (texto para o usuário)."""
    if bus not in FLASHPROG_BUS:
        raise ImageError("fp_bus", bus=bus, buses=", ".join(FLASHPROG_BUS))
    if bus in DETECT_ONLY_BUS:
        if not detect:
            raise ImageError("fp_detect_only")
        if flash_kb or flash_type or sector_kb or buffer:
            raise ImageError("fp_md_options")
        return FlashJob(FLASHPROG_BUS[bus], 0, 0)
    if bus == "eprom":
        return FlashJob(FLASHPROG_BUS[bus], EPROM_KB, 0)
    if not flash_kb or not 1 <= flash_kb <= 8192:
        raise ImageError("fp_kb")
    word = 0
    if bus in ("8", "plcc32"):
        if flash_type is None:
            if need_type:
                raise ImageError("needs_flash_type", types=", ".join(FLASH_TYPES))
        else:
            word = _type_word(flash_type, sector_kb, buffer)
    return FlashJob(FLASHPROG_BUS[bus], flash_kb, word)


def split_flashprog(data: bytes, bus: str, flash_kb: Optional[int], flash_type: Optional[str] = None, sector_kb: Optional[int] = None,
                    buffer: Optional[int] = None) -> FlashJob:
    """Arquivo cru (sem cabeçalho) para gravar no chip. Tamanho múltiplo de 512 e que cabe. No 29gl completa com 0xFF até um múltiplo do setor."""
    job = flashprog_params(bus, flash_kb, flash_type, sector_kb, buffer, need_type=bus in ("8", "plcc32"))
    if len(data) == 0 or len(data) % 512:
        raise ImageError("fp_size")
    if len(data) > job.prg_kb * 1024:
        raise ImageError("fp_no_fit", kb=len(data) // 1024, cap=job.prg_kb)
    body = data
    if flash_type == "29gl" and bus in ("8", "plcc32"):
        sector = sector_kb * 1024
        body = data + b"\xff" * (-len(data) % sector)
        if len(body) > job.prg_kb * 1024:
            raise ImageError("fp_padded_no_fit", kb=len(body) // 1024, cap=job.prg_kb)
    job.body, job.rom = body, data
    return job
