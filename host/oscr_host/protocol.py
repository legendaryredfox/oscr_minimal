# SPDX-License-Identifier: GPL-3.0-or-later
"""Quadros, tipos e (de)serialização do protocolo v1. Sem dependência de serial."""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

PROTO_VERSION = 1
MAGIC = b"\xA5\x5A"
MAX_PAYLOAD = 1024
DEFAULT_BLOCK = 512
HEADER_LEN = 6
CRC_LEN = 4

# host -> dispositivo
T_INFO, T_DETECT, T_DUMP_ROM, T_READ_SAVE, T_WRITE_SAVE = 0x01, 0x02, 0x03, 0x04, 0x05
T_ACK, T_NAK, T_ABORT, T_H_DATA, T_H_END = 0x06, 0x07, 0x08, 0x09, 0x0A
# dispositivo -> host
T_INFO_RESP, T_DETECT_RESP, T_BEGIN, T_DATA, T_END = 0x81, 0x82, 0x83, 0x84, 0x85
T_D_ACK, T_ERRO, T_PROGRESSO = 0x86, 0x87, 0x88

KIND_ROM, KIND_SAVE = 1, 2

SYSTEMS = {  # nome -> (id, extensão)
    "snes": (1, ".sfc"), "nes": (2, ".nes"), "famicom": (3, ".nes"),
    "md": (4, ".md"), "gba": (5, ".gba"), "gb": (6, ".gb"), "mock": (255, ".bin"),
}
SYSTEM_BY_ID = {v[0]: k for k, v in SYSTEMS.items()}

ERRORS = {
    1: "comando desconhecido ou não suportado", 2: "sistema desconhecido ou não suportado",
    3: "nenhum cartucho detectado", 4: "argumento inválido", 5: "reenvios excedidos",
    6: "CRC32 do arquivo não confere", 7: "erro de leitura/gravação no cartucho",
    8: "dispositivo ocupado", 9: "abortado", 10: "cartucho não tem save",
}


class ProtocolError(Exception):
    pass


class DeviceError(Exception):
    """Dispositivo respondeu ERRO."""

    def __init__(self, code: int, text: str = ""):
        self.code, self.text = code, text
        super().__init__(f"erro 0x{code:04X}: {ERRORS.get(code, 'desconhecido')}" + (f" ({text})" if text else ""))


def crc32(data: bytes, start: int = 0) -> int:
    return zlib.crc32(data, start) & 0xFFFFFFFF


@dataclass
class Frame:
    type: int
    seq: int
    payload: bytes = b""


def encode_frame(type_: int, seq: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ProtocolError(f"payload de {len(payload)} bytes (máx. {MAX_PAYLOAD})")
    body = struct.pack("<BBH", type_, seq & 0xFF, len(payload)) + payload
    return MAGIC + body + struct.pack("<I", crc32(body))


class FrameDecoder:
    """Decodificador em fluxo: alimente com bytes, receba quadros válidos.

    Quadros com CRC ruim ou len inválido são descartados; o decodificador
    ressincroniza na próxima magia. `bad_frames` conta os descartes.
    """

    def __init__(self) -> None:
        self._buf = bytearray()
        self.bad_frames = 0

    def feed(self, data: bytes) -> list[Frame]:
        self._buf += data
        out: list[Frame] = []
        while True:
            i = self._buf.find(MAGIC)
            if i < 0:
                # mantém o último byte (pode ser metade da magia)
                if self._buf and self._buf[-1] == MAGIC[0]:
                    del self._buf[:-1]
                else:
                    self._buf.clear()
                break
            if i > 0:
                del self._buf[:i]
            if len(self._buf) < HEADER_LEN:
                break
            type_, seq, length = struct.unpack_from("<BBH", self._buf, 2)
            if length > MAX_PAYLOAD:
                self.bad_frames += 1
                del self._buf[:2]
                continue
            total = HEADER_LEN + length + CRC_LEN
            if len(self._buf) < total:
                break
            body = bytes(self._buf[2:HEADER_LEN + length])
            (got,) = struct.unpack_from("<I", self._buf, HEADER_LEN + length)
            if got != crc32(body):
                self.bad_frames += 1
                del self._buf[:2]
                continue
            out.append(Frame(type_, seq, bytes(self._buf[HEADER_LEN:HEADER_LEN + length])))
            del self._buf[:total]
        return out


# ---------------------------------------------------------------- builders / parsers
def build_info() -> bytes:
    return b""


def build_detect(system: int) -> bytes:
    return struct.pack("<B", system)


def build_dump(system: int, block: int = 0, mapper: int = 0, prg_kb: int = 0, chr_kb: int = 0) -> bytes:
    base = struct.pack("<BH", system, block)
    if mapper or prg_kb or chr_kb:      # opções do NES/Famicom (docs/protocolo.md)
        base += struct.pack("<HHH", mapper, prg_kb, chr_kb)
    return base


def build_write_save(system: int, size: int, block: int = 0, mapper: int = 0, ram_kb: int = 0) -> bytes:
    base = struct.pack("<BIH", system, size, block)
    if mapper or ram_kb:                # NES/Famicom: mapper (1, 4, 5 e 69 têm PRG-RAM com bateria) e RAM em KB (16/32 só nos mappers 1 e 5)
        base += struct.pack("<HHH", mapper, ram_kb, 0)
    return base


def build_offset(offset: int) -> bytes:  # ACK / NAK
    return struct.pack("<I", offset)


def build_data(offset: int, data: bytes) -> bytes:
    return struct.pack("<I", offset) + data


def build_end(total: int, crc: int) -> bytes:
    return struct.pack("<II", total, crc)


def parse_info_resp(p: bytes) -> dict:
    if len(p) < 7:
        raise ProtocolError("INFO_RESP curto")
    ver, ma, mi, pa, flags, systems = struct.unpack_from("<BBBBBH", p)
    max_payload = struct.unpack_from("<H", p, 7)[0] if len(p) >= 9 else MAX_PAYLOAD
    return {"proto": ver, "firmware": f"{ma}.{mi}.{pa}", "flags": flags, "max_payload": max_payload,
            "mock": bool(flags & 1), "si5351": bool(flags & 2), "pic": bool(flags & 4),
            "systems": [n for n, (i, _) in SYSTEMS.items() if i < 16 and systems & (1 << i)]}


def parse_detect_resp(p: bytes) -> dict:
    if len(p) < 12:
        raise ProtocolError("DETECT_RESP curto")
    system, status, rom, save, stype, n = struct.unpack_from("<BBIIBB", p)
    name = p[12:12 + n].decode("ascii", "replace")
    return {"system": system, "status": status, "rom_size": rom, "save_size": save,
            "save_type": stype, "name": name}


def parse_begin(p: bytes) -> tuple[int, int, int]:
    if len(p) < 7:
        raise ProtocolError("BEGIN curto")
    return struct.unpack_from("<BIH", p)  # tipo_dado, tamanho, bloco


def parse_data(p: bytes) -> tuple[int, bytes]:
    if len(p) < 4:
        raise ProtocolError("DATA curto")
    return struct.unpack_from("<I", p)[0], p[4:]


def parse_end(p: bytes) -> tuple[int, int]:
    if len(p) < 8:
        raise ProtocolError("END curto")
    return struct.unpack_from("<II", p)


def parse_offset(p: bytes) -> int:
    if len(p) < 4:
        raise ProtocolError("ACK/NAK curto")
    return struct.unpack_from("<I", p)[0]


def parse_error(p: bytes) -> DeviceError:
    code, n = struct.unpack_from("<HB", p) if len(p) >= 3 else (0, 0)
    return DeviceError(code, p[3:3 + n].decode("ascii", "replace"))


# padrão do modo MOCK (docs/protocolo.md, seção 9)
MOCK_SIZE = 32768


def mock_byte(i: int) -> int:
    return (i * 7 + (i >> 8)) & 0xFF


def mock_data(size: int = MOCK_SIZE) -> bytes:
    return bytes(mock_byte(i) for i in range(size))
