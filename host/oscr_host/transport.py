# SPDX-License-Identifier: GPL-3.0-or-later
"""Transportes: porta serial (pyserial) e par em memória (testes/simulador)."""
from __future__ import annotations

import queue
import threading
import time


class Transport:
    def write(self, data: bytes) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def read(self, size: int, timeout: float) -> bytes:  # pragma: no cover - interface
        """Devolve de 1 a `size` bytes, ou b'' se `timeout` esgotar."""
        raise NotImplementedError

    def close(self) -> None:
        pass


class SerialTransport(Transport):
    def __init__(self, port: str, baud: int = 1_000_000):
        import serial  # import tardio: os testes não precisam de pyserial

        self.ser = serial.Serial(port, baud, timeout=0.05, write_timeout=2.0)
        self.baud = baud
        self._wlock = threading.Lock()       # o Cancelar pode vir de outra thread: dois quadros não podem se intercalar

    def write(self, data: bytes) -> None:
        with self._wlock:
            n = self.ser.write(data)
            self.ser.flush()
        if n is not None and n != len(data):
            raise OSError(f"escrita parcial na porta serial: {n} de {len(data)} bytes")

    def read(self, size: int, timeout: float) -> bytes:
        end = time.monotonic() + timeout
        while True:
            chunk = self.ser.read(max(1, min(size, self.ser.in_waiting or 1)))
            if chunk:
                return chunk
            if time.monotonic() >= end:
                return b""

    def reset_input(self) -> None:
        self.ser.reset_input_buffer()

    def close(self) -> None:
        self.ser.close()


class _End(Transport):
    def __init__(self, rx: "queue.Queue[bytes]", tx: "queue.Queue[bytes]"):
        self._rx, self._tx, self._pending = rx, tx, bytearray()

    def write(self, data: bytes) -> None:
        self._tx.put(bytes(data))

    def read(self, size: int, timeout: float) -> bytes:
        if not self._pending:
            try:
                self._pending += self._rx.get(timeout=timeout)
            except queue.Empty:
                return b""
        out = bytes(self._pending[:size])
        del self._pending[:size]
        return out


def pair() -> tuple[Transport, Transport]:
    """Dois transportes ligados um ao outro (como um cabo serial)."""
    a, b = queue.Queue(), queue.Queue()
    return _End(a, b), _End(b, a)


class ProcessTransport(Transport):
    """Fala com um processo filho por stdin/stdout (usado para testar o firmware compilado no PC)."""

    def __init__(self, argv: list[str]):
        import os
        import subprocess

        self._wlock = threading.Lock()
        self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        self._fd = self.proc.stdout.fileno()
        self._os = os

    def write(self, data: bytes) -> None:
        with self._wlock:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()

    def read(self, size: int, timeout: float) -> bytes:
        import select

        r, _, _ = select.select([self._fd], [], [], timeout)
        return self._os.read(self._fd, size) if r else b""

    def close(self) -> None:
        try:
            self.proc.stdin.close()
        finally:
            self.proc.terminate()
            self.proc.wait(2)
