# SPDX-License-Identifier: GPL-3.0-or-later
import random

from oscr_host import protocol as P
from oscr_host.verify import verify_rom


def _rom(n, seed=1):
    random.seed(seed)
    return bytearray(random.randrange(256) for _ in range(n))


def test_mega_drive_ok_e_mismatch():
    d = _rom(0x40000)
    d[0x100:0x104] = b"SEGA"
    total = sum(int.from_bytes(d[i:i + 2], "big") for i in range(0x200, len(d), 2)) & 0xFFFF
    d[0x18E:0x190] = total.to_bytes(2, "big")
    assert verify_rom(4, bytes(d)).status == "ok"
    d[0x300] ^= 0x01
    c = verify_rom(4, bytes(d))
    assert c.status == "mismatch" and "NÃO confere" in str(c)


def test_gba_complemento_do_cabecalho():
    d = _rom(0x1000, 2)
    d[4:8] = bytes([0x24, 0xFF, 0xAE, 0x51])
    d[0xBD] = (-(sum(d[0xA0:0xBD]) + 0x19)) & 0xFF
    assert verify_rom(5, bytes(d)).status == "ok"
    d[0xA2] ^= 0xFF
    assert verify_rom(5, bytes(d)).status == "mismatch"


def _snes(n, pos):
    d = _rom(n, 3)
    d[pos + 0x1C:pos + 0x20] = bytes([0xFF, 0xFF, 0x00, 0x00])
    total = sum(d) & 0xFFFF
    d[pos + 0x1E:pos + 0x20] = total.to_bytes(2, "little")
    d[pos + 0x1C:pos + 0x1E] = (total ^ 0xFFFF).to_bytes(2, "little")
    return d


def test_snes_lorom_e_hirom_potencia_de_2():
    assert verify_rom(1, bytes(_snes(0x80000, 0x7FC0))).status == "ok"
    assert verify_rom(1, bytes(_snes(0x100000, 0xFFC0))).status == "ok"
    d = _snes(0x80000, 0x7FC0); d[0x1000] ^= 1
    assert verify_rom(1, bytes(d)).status == "mismatch"


def test_snes_tamanho_nao_potencia_de_2():
    # 1,5 MB: 1 MB + 512 KB espelhado até 2 MB
    n = 0x180000
    d = _rom(n, 4); pos = 0xFFC0
    d[pos + 0x1C:pos + 0x20] = bytes([0xFF, 0xFF, 0, 0])
    total = (sum(d[:0x100000]) + sum(d[0x100000:]) * 2) & 0xFFFF
    d[pos + 0x1E:pos + 0x20] = total.to_bytes(2, "little"); d[pos + 0x1C:pos + 0x1E] = (total ^ 0xFFFF).to_bytes(2, "little")
    assert verify_rom(1, bytes(d)).status == "ok"


def test_sem_cabecalho_ou_sistema_sem_checksum():
    assert verify_rom(1, bytes(_rom(0x80000, 5))).status == "na"
    assert verify_rom(2, bytes(_rom(0x8000, 6))).status == "na"
    assert verify_rom(4, b"\x00" * 100).status == "na"
    assert verify_rom(255, P.mock_data()).status == "na"
