# SPDX-License-Identifier: GPL-3.0-or-later
"""Fotos do Game Boy Camera (cartucho "Pocket Camera") a partir de um save de 128 KB para PNG (D160, P9; o formato vem de FlashGBX/PocketCamera.py, GPL-3.0).

Save de 128 KB: 30 fotos de 128 x 112 pixels em 2 bits por pixel (16 x 14 tiles de 16 bytes, os primeiros 0xE00 bytes de cada bloco de 0x1000), a foto n no bloco
0x2000 + n * 0x1000; a "cara do jogo" em 0x11FC; a última imagem vista (128 x 123) em 0x0000; a ordem do álbum em 0x11D7 (30 bytes: o número da foto em cada posição,
0xFF ou repetido = apagada). Só biblioteca padrão (o PNG é escrito aqui com zlib). Espelho de gui/shared/.../GbCamera.kt."""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

SAVE_BYTES = 128 * 1024
W, H, H_LAST = 128, 112, 123
PALETTES = {                                   # índice 0 = mais claro; 4 cores RGB
    "gray": [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)],
    "green": [(155, 188, 15), (139, 172, 15), (48, 98, 48), (15, 56, 15)],
    "gbc": [(240, 240, 240), (218, 196, 106), (112, 88, 52), (30, 30, 30)],
}


@dataclass(frozen=True)
class Photo:
    name: str               # "photo_01", "game_face", "last_seen"
    pixels: bytes           # largura x altura valores de 0 a 3
    width: int
    height: int
    deleted: bool = False
    empty: bool = False


def album_order(data: bytes) -> tuple[list[int], set[int]]:
    """(blocos na ordem do álbum, blocos apagados): a posição i do álbum é o bloco order[i]; apagados vão para o fim (como no FlashGBX)."""
    raw = data[0x11D7:0x11F5]
    order: list = [None] * 30
    deleted: list[int] = []
    seen: list[int] = []
    for i in range(30):
        v = raw[i]
        if v == 0xFF or v in seen or v >= 30:
            deleted.append(i)
        else:
            order[v] = i
        seen.append(v)
    return [x for x in order if x is not None] + deleted, set(deleted)


def decode(buf: bytes, tiles_high: int = 14) -> bytes:
    """Tiles 2bpp (16 de largura) para um valor de 0 a 3 por pixel, linha a linha (128 pixels de largura)."""
    out = bytearray(W * tiles_high * 8)
    for th in range(tiles_high):
        for tw in range(16):
            pos = 16 * (th * 16 + tw)
            tile = buf[pos:pos + 16]
            if len(tile) < 16:
                continue
            for i in range(8):
                lo_row, hi_row = tile[i * 2], tile[i * 2 + 1]
                for j in range(8):
                    out[(th * 8 + i) * W + tw * 8 + j] = (((hi_row >> (7 - j)) & 1) << 1) | ((lo_row >> (7 - j)) & 1)
    return bytes(out)


def extract(data: bytes) -> list[Photo]:
    """Todas as imagens do save: as 30 fotos (na ordem do álbum; apagadas e vazias marcadas), a cara do jogo e a última imagem vista."""
    if len(data) != SAVE_BYTES:
        raise ValueError(f"o save do Game Boy Camera tem {SAVE_BYTES} bytes, este tem {len(data)}")
    order, deleted = album_order(data)
    out: list[Photo] = []
    for pos in range(30):
        block = order[pos]
        raw = data[0x2000 + block * 0x1000:0x2000 + (block + 1) * 0x1000]
        out.append(Photo(f"photo_{pos + 1:02d}", decode(raw), W, H, deleted=block in deleted, empty=len(set(raw)) == 1))
    out.append(Photo("game_face", decode(data[0x11FC:0x11FC + 0x1000]), W, H))
    last = decode(data[0:0x1000], 16)[:W * H_LAST]
    out.append(Photo("last_seen", last, W, H_LAST))
    return out


def png(pixels: bytes, width: int, height: int, palette: str = "gray", scale: int = 1) -> bytes:
    """PNG indexado (4 cores) com a ampliação inteira `scale`."""
    pal = PALETTES[palette]
    sw, sh = width * scale, height * scale
    rows = bytearray()
    for y in range(height):
        row = bytes(b for p in pixels[y * width:(y + 1) * width] for b in (p,) * scale)
        rows += (b"\x00" + row) * scale

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", sw, sh, 8, 3, 0, 0, 0))
            + chunk(b"PLTE", bytes(c for rgb in pal for c in rgb)) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))
