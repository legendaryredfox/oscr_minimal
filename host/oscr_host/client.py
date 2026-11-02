# SPDX-License-Identifier: GPL-3.0-or-later
"""Cliente do protocolo v1 (lado do PC)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from . import protocol as P
from .transport import Transport

Progress = Callable[[int, int], None]


class TimeoutError_(Exception):
    pass


@dataclass
class DumpResult:
    data: bytes
    crc32: int
    kind: int


class Client:
    def __init__(self, transport: Transport, timeout: float = 1.0, long_timeout: float = 10.0,
                 retries: int = 3):
        self.t = transport
        self.dec = P.FrameDecoder()
        self.timeout, self.long_timeout, self.retries = timeout, long_timeout, retries
        self._seq = 0
        self._queue: list[P.Frame] = []

    # ---------------------------------------------------------------- baixo nível
    def _next_seq(self) -> int:
        self._seq = (self._seq + 1) & 0xFF
        return self._seq

    def _send(self, type_: int, payload: bytes, seq: int) -> None:
        self.t.write(P.encode_frame(type_, seq, payload))

    def _recv(self, timeout: float, seq: Optional[int] = None) -> Optional[P.Frame]:
        end = time.monotonic() + timeout
        while True:
            for i, f in enumerate(self._queue):
                if seq is None or f.seq == seq:
                    return self._queue.pop(i)
            left = end - time.monotonic()
            if left <= 0:
                return None
            data = self.t.read(1100, min(left, 0.2))
            if data:
                self._queue += self.dec.feed(data)

    def _request(self, type_: int, payload: bytes, seq: int, expect: set[int], timeout: float,
                 accept: Optional[Callable[[P.Frame], bool]] = None) -> P.Frame:
        """Envia e espera uma resposta de tipo esperado (ERRO vira exceção). Reenvia em timeout."""
        for _ in range(self.retries + 1):
            self._send(type_, payload, seq)
            end = time.monotonic() + timeout
            while True:
                f = self._recv(max(0.0, end - time.monotonic()), seq)
                if f is None:
                    break
                if f.type == P.T_ERRO:
                    raise P.parse_error(f.payload)
                if f.type in expect and (accept is None or accept(f)):
                    return f
        raise TimeoutError_(f"sem resposta ao comando 0x{type_:02X}")

    # ---------------------------------------------------------------- comandos
    def info(self) -> dict:
        f = self._request(P.T_INFO, b"", self._next_seq(), {P.T_INFO_RESP}, self.timeout)
        return P.parse_info_resp(f.payload)

    def detect(self, system: int) -> dict:
        f = self._request(P.T_DETECT, P.build_detect(system), self._next_seq(), {P.T_DETECT_RESP},
                          self.long_timeout)
        return P.parse_detect_resp(f.payload)

    def abort(self) -> None:
        self._send(P.T_ABORT, b"", self._next_seq())

    def _stream_in(self, cmd: int, payload: bytes, progress: Optional[Progress]) -> DumpResult:
        seq = self._next_seq()
        begin = self._request(cmd, payload, seq, {P.T_BEGIN}, self.long_timeout)
        kind, size, block = P.parse_begin(begin.payload)
        self._send(P.T_ACK, P.build_offset(0), seq)
        buf = bytearray(size)
        expected, idle = 0, 0
        while True:
            f = self._recv(self.long_timeout if expected == 0 else self.timeout * 3, seq)
            if f is None:
                idle += 1
                if idle > self.retries:
                    raise TimeoutError_("o dispositivo parou de enviar dados")
                self._send(P.T_NAK, P.build_offset(expected), seq)
                continue
            idle = 0
            if f.type == P.T_DATA:
                off, data = P.parse_data(f.payload)
                if off == expected and off + len(data) <= size:
                    buf[off:off + len(data)] = data
                    expected += len(data)
                    self._send(P.T_ACK, P.build_offset(off), seq)
                    if progress:
                        progress(expected, size)
                elif off < expected:
                    self._send(P.T_ACK, P.build_offset(off), seq)  # duplicado: confirma de novo
                else:
                    self._send(P.T_NAK, P.build_offset(expected), seq)
            elif f.type == P.T_END:
                total, crc = P.parse_end(f.payload)
                if total != size or expected != size:
                    self.abort()
                    raise P.ProtocolError(f"END com total {total}, recebido {expected}, esperado {size}")
                mine = P.crc32(bytes(buf))
                if mine != crc:
                    self.abort()
                    raise P.DeviceError(6, f"calculado {mine:08X}, dispositivo {crc:08X}")
                self._send(P.T_ACK, P.build_offset(total), seq)
                return DumpResult(bytes(buf), mine, kind)
            elif f.type == P.T_ERRO:
                raise P.parse_error(f.payload)
            elif f.type == P.T_BEGIN:
                self._send(P.T_ACK, P.build_offset(0), seq)
            # T_PROGRESSO e outros: ignorados

    def dump_rom(self, system: int, block: int = 0, progress: Optional[Progress] = None) -> DumpResult:
        return self._stream_in(P.T_DUMP_ROM, P.build_dump(system, block), progress)

    def read_save(self, system: int, block: int = 0, progress: Optional[Progress] = None) -> DumpResult:
        return self._stream_in(P.T_READ_SAVE, P.build_dump(system, block), progress)

    def write_save(self, system: int, data: bytes, block: int = 512, progress: Optional[Progress] = None) -> int:
        seq = self._next_seq()
        block = block or P.DEFAULT_BLOCK
        f = self._request(P.T_WRITE_SAVE, P.build_write_save(system, len(data), block), seq,
                          {P.T_D_ACK}, self.long_timeout)
        if P.parse_offset(f.payload) != 0:
            raise P.ProtocolError("ACK inicial com offset diferente de 0")
        for off in range(0, len(data), block):
            chunk = data[off:off + block]
            self._request(P.T_H_DATA, P.build_data(off, chunk), seq, {P.T_D_ACK}, self.timeout,
                          accept=lambda fr, o=off: P.parse_offset(fr.payload) == o)
            if progress:
                progress(off + len(chunk), len(data))
        crc = P.crc32(data)
        self._request(P.T_H_END, P.build_end(len(data), crc), seq, {P.T_D_ACK}, self.long_timeout,
                      accept=lambda fr: P.parse_offset(fr.payload) == len(data))
        return crc
