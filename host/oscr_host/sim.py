# SPDX-License-Identifier: GPL-3.0-or-later
"""Simulador do dispositivo (lado do firmware) para testes e para `dumper --simulate`.

Implementa o protocolo v1 com dados sintéticos (modo MOCK). Aceita injeção de falhas
(`corrupt_data`, `drop_acks`) para testar a recuperação do host.

Limite conhecido: só entende os sistemas 0 e 255 (MOCK) e não reproduz a lógica de nenhum cartucho real. O comportamento por sistema (cabeçalhos,
mappers, saves) é testado contra o firmware em C++ compilado no PC (`tests/test_firmware_cpp.py`, `firmware/arquivo/oscr_serial/tests`, arquivado; o protocolo do fork é testado em `firmware/oscr/pc-tests`).
"""
from __future__ import annotations

import threading
import time
from typing import Optional

from . import protocol as P
from .transport import Transport


class _Aborted(Exception):
    pass


class MockDevice:
    def __init__(self, rom: Optional[bytes] = None, save: Optional[bytes] = None):
        self.rom = rom if rom is not None else P.mock_data()
        self.save = save if save is not None else bytes((i * 3 + 1) & 0xFF for i in range(8192))
        self.written_save: Optional[bytes] = None
        self.written_rom: Optional[bytes] = None
        self.last_rom_options = None   # (chip, prg_kb, chr_kb) do último WRITE_ROM
        self.corrupt_data = 0      # quantos DATA enviados terão 1 byte alterado (CRC ruim)
        self.drop_next_acks = 0    # quantos ACK do host serão ignorados
        self.log: list[str] = []
        self.last_options = None   # (mapper, prg_kb, chr_kb) do último DUMP_ROM/READ_SAVE
        self.last_write_mapper = None
        self.last_write_ram_kb = None
        self._dec = P.FrameDecoder()
        self._q: list[P.Frame] = []

    # ------------------------------------------------------------------ E/S
    def _send(self, t: Transport, type_: int, seq: int, payload: bytes = b"", corrupt: bool = False) -> None:
        raw = bytearray(P.encode_frame(type_, seq, payload))
        if corrupt:
            raw[8] ^= 0xFF
        t.write(bytes(raw))

    def _next(self, t: Transport, timeout: float) -> Optional[P.Frame]:
        end = time.monotonic() + timeout
        while True:
            if self._q:
                return self._q.pop(0)
            left = end - time.monotonic()
            if left <= 0:
                return None
            d = t.read(1100, min(left, 0.05))
            if d:
                self._q += self._dec.feed(d)

    def _wait_ack(self, t: Transport, seq: int, offset: int, timeout: float = 0.4) -> str:
        """'ack', 'nak' ou 'timeout' para o bloco `offset`. ABORT levanta _Aborted."""
        end = time.monotonic() + timeout
        while True:
            f = self._next(t, max(0.0, end - time.monotonic()))
            if f is None:
                return "timeout"
            if f.type == P.T_ABORT:
                raise _Aborted()
            if f.seq != seq:
                continue
            if f.type == P.T_ACK and P.parse_offset(f.payload) == offset:
                if self.drop_next_acks > 0:
                    self.drop_next_acks -= 1
                    continue
                return "ack"
            if f.type == P.T_NAK and P.parse_offset(f.payload) == offset:
                return "nak"

    # ------------------------------------------------------------------ comandos
    def serve(self, t: Transport, stop: threading.Event) -> None:
        while not stop.is_set():
            f = self._next(t, 0.05)
            if f is None:
                continue
            try:
                self._handle(t, f)
            except _Aborted:
                self.log.append("abort")
                self._send(t, P.T_D_ACK, f.seq, P.build_offset(0))

    def _handle(self, t: Transport, f: P.Frame) -> None:
        if f.type == P.T_INFO:
            # proto, firmware 0.1.0, flags (bit0 = MOCK), máscara de sistemas (0: só o modo MOCK)
            self._send(t, P.T_INFO_RESP, f.seq, bytes([P.PROTO_VERSION, 0, 1, 0, 0b1001]) + (0).to_bytes(2, "little") + P.MAX_PAYLOAD.to_bytes(2, "little"))
        elif f.type == P.T_DETECT:
            sysid = f.payload[0] if f.payload else 0
            if sysid in (0, 255):
                name = b"MOCK"
                self._send(t, P.T_DETECT_RESP, f.seq,
                           bytes([255, 0]) + len(self.rom).to_bytes(4, "little") + len(self.save).to_bytes(4, "little")
                           + bytes([1, len(name)]) + name)
            else:
                self._send(t, P.T_DETECT_RESP, f.seq, bytes([sysid, 1]) + bytes(8) + bytes([0, 0]))
        elif f.type in (P.T_DUMP_ROM, P.T_READ_SAVE):
            sysid = f.payload[0] if f.payload else 0
            block = int.from_bytes(f.payload[1:3], "little") if len(f.payload) >= 3 else 0
            if sysid not in (0, 255):
                self._error(t, f.seq, 3, "sem cartucho")
                return
            if len(f.payload) >= 9:
                self.last_options = tuple(int.from_bytes(f.payload[3 + 2 * i:5 + 2 * i], "little") for i in range(3))
            block = block or P.DEFAULT_BLOCK
            if block > P.MAX_PAYLOAD - 4:
                self._error(t, f.seq, 4, "bloco grande")
                return
            kind, data = (P.KIND_ROM, self.rom) if f.type == P.T_DUMP_ROM else (P.KIND_SAVE, self.save)
            self._stream_out(t, f.seq, kind, data, block)
        elif f.type == P.T_WRITE_SAVE:
            self._write_save(t, f)
        elif f.type == P.T_WRITE_ROM:
            self._write_save(t, f, rom=True)
        elif f.type == P.T_ABORT:
            self._send(t, P.T_D_ACK, f.seq, P.build_offset(0))
        else:
            self._error(t, f.seq, 1, "comando")

    def _error(self, t: Transport, seq: int, code: int, text: str = "") -> None:
        tb = text.encode()
        self._send(t, P.T_ERRO, seq, code.to_bytes(2, "little") + bytes([len(tb)]) + tb)

    def _stream_out(self, t: Transport, seq: int, kind: int, data: bytes, block: int) -> None:
        begin = bytes([kind]) + len(data).to_bytes(4, "little") + block.to_bytes(2, "little")
        for _ in range(4):
            self._send(t, P.T_BEGIN, seq, begin)
            if self._wait_ack(t, seq, 0, 0.5) == "ack":
                break
        else:
            return self._error(t, seq, 5, "begin")
        for off in range(0, len(data), block):
            chunk = data[off:off + block]
            for attempt in range(4):
                corrupt = self.corrupt_data > 0
                if corrupt:
                    self.corrupt_data -= 1
                self._send(t, P.T_DATA, seq, P.build_data(off, chunk), corrupt)
                r = self._wait_ack(t, seq, off)
                if r == "ack":
                    break
            else:
                return self._error(t, seq, 5, "reenvios")
        end = P.build_end(len(data), P.crc32(data))
        for _ in range(4):
            self._send(t, P.T_END, seq, end)
            if self._wait_ack(t, seq, len(data), 0.5) == "ack":
                return
        self._error(t, seq, 5, "end")

    def _write_save(self, t: Transport, f: P.Frame, rom: bool = False) -> None:
        if len(f.payload) < 7:
            return self._error(t, f.seq, 4, "args")
        sysid = f.payload[0]
        size = int.from_bytes(f.payload[1:5], "little")
        self.last_write_mapper = int.from_bytes(f.payload[7:9], "little") if len(f.payload) >= 9 else 0
        self.last_write_ram_kb = int.from_bytes(f.payload[9:11], "little") if len(f.payload) >= 11 else 0
        if rom:                                        # WRITE_ROM: chip, PRG e CHR em KB; no simulador o chip 9 "não é reconhecido"
            chip, prg, chr_ = (int.from_bytes(f.payload[7 + 2 * i:9 + 2 * i], "little") for i in range(3))
            self.last_rom_options = (chip, prg, chr_)
            if chip == 9:
                return self._error(t, f.seq, 11, "id")
            if chip < 0x100 and size != (prg + chr_) * 1024 and not (chr_ == 0 and 0 < size <= prg * 1024 and size % 2 == 0):    # NES: PRG+CHR; SNES e MD: ROM dentro do flash
                return self._error(t, f.seq, 4, "tamanho")
        if sysid not in (0, 255) or size > 1 << 20:
            return self._error(t, f.seq, 2 if sysid not in (0, 255) else 4)
        self._send(t, P.T_D_ACK, f.seq, P.build_offset(0))
        buf, expected = bytearray(size), 0
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            g = self._next(t, 0.2)
            if g is None:
                continue
            if g.type == P.T_ABORT:
                raise _Aborted()
            if g.seq != f.seq:
                continue
            if g.type == P.T_H_DATA:
                off, data = P.parse_data(g.payload)
                if off == expected and off + len(data) <= size:
                    buf[off:off + len(data)] = data
                    expected += len(data)
                    self._send(t, P.T_D_ACK, f.seq, P.build_offset(off))
                elif off < expected:
                    self._send(t, P.T_D_ACK, f.seq, P.build_offset(off))
                deadline = time.monotonic() + 5.0
            elif g.type == P.T_H_END:
                total, crc = P.parse_end(g.payload)
                if total != size or expected != size or P.crc32(bytes(buf)) != crc:
                    return self._error(t, f.seq, 6, "crc")
                if rom:
                    self.written_rom = bytes(buf)
                else:
                    self.written_save = bytes(buf)
                self._send(t, P.T_D_ACK, f.seq, P.build_offset(total))
                return
        self._error(t, f.seq, 5, "timeout")


def start(device: Optional[MockDevice] = None) -> tuple[Transport, MockDevice, threading.Event, threading.Thread]:
    """Cria o par de transportes e inicia o simulador numa thread. Devolve o lado do host."""
    from .transport import pair

    host_t, dev_t = pair()
    dev = device or MockDevice()
    stop = threading.Event()
    th = threading.Thread(target=dev.serve, args=(dev_t, stop), daemon=True)
    th.start()
    return host_t, dev, stop, th
