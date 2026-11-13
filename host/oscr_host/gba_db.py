# SPDX-License-Identifier: GPL-3.0-or-later
"""Tipo e tamanho do save de um jogo de GBA pelo cabeçalho da ROM (D160, P2).

Base `database/flashgbx/gba.tsv` (do FlashGBX, Lesserkuma, GPL-3.0; `tools/importar_flashgbx.py`): a chave é o SHA-1 dos primeiros 0x180 bytes do cabeçalho.
O tipo de save segue a numeração do OSCR (`--mapper` de save-read e save-write): 0 nenhum, 1 EEPROM 512 B, 2 EEPROM 8 KB, 3 SRAM 32 KB, 4 Flash 64 KB, 5 Flash 128 KB,
6 Flash 1 MB. Só **sugere**: nada é escolhido sozinho. Espelho de gui/shared/.../GbaSaveDb.kt."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

TSV = Path(__file__).resolve().parents[2] / "database" / "flashgbx" / "gba.tsv"

SAVE_LABEL = {0: "none", 1: "EEPROM 512 B", 2: "EEPROM 8 KB", 3: "SRAM 32 KB", 4: "Flash 64 KB", 5: "Flash 128 KB", 6: "Flash 1 MB"}


@dataclass(frozen=True)
class GbaGame:
    name: str
    crc32: int
    rom_size: int
    save_type: int
    save_size: int

    def to_dict(self) -> dict:
        return {"name": self.name, "crc32": f"{self.crc32:08X}", "rom_size": self.rom_size, "save_type": self.save_type,
                "save_label": SAVE_LABEL.get(self.save_type, "?"), "save_size": self.save_size}


_cache: dict[str, dict[str, GbaGame]] = {}


def header_sha1(rom: bytes) -> Optional[str]:
    """SHA-1 do cabeçalho como o FlashGBX calcula: 0x0A a 0x180 se o título é "YJencrypted"; 0x00 a 0x100 se o código do jogo começa com "M"; senão 0x00 a 0x180."""
    if len(rom) < 0x180:
        return None
    title = rom[0xA0:0xAC].rstrip(b"\x00 ")
    code = rom[0xAC:0xB0]
    if title == b"YJencrypted":
        return hashlib.sha1(rom[0x0A:0x180]).hexdigest().upper()
    if len(code) == 4 and code[:1] == b"M":
        return hashlib.sha1(rom[0x00:0x100]).hexdigest().upper()
    return hashlib.sha1(rom[0x00:0x180]).hexdigest().upper()


def load(path: Optional[Path] = None) -> dict[str, GbaGame]:
    p = Path(path) if path else TSV
    key = str(p)
    if key in _cache:
        return _cache[key]
    out: dict[str, GbaGame] = {}
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) >= 6:
                out[f[0].upper()] = GbaGame(f[5], int(f[1], 16), int(f[2]), int(f[3]), int(f[4]))
    except (OSError, ValueError):
        out = {}
    _cache[key] = out
    return out


def lookup(rom: bytes, path: Optional[Path] = None) -> Optional[GbaGame]:
    h = header_sha1(rom)
    return load(path).get(h) if h else None
