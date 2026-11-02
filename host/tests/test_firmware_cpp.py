# SPDX-License-Identifier: GPL-3.0-or-later
"""Teste cruzado: o cliente Python fala com o código REAL do firmware (compilado no PC).

Compila firmware/oscr_serial (g++) e roda `sim_stdio`. Pula se não houver g++/make.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from oscr_host import protocol as P
from oscr_host.client import Client
from oscr_host.transport import ProcessTransport

FW = Path(__file__).resolve().parents[2] / "firmware" / "oscr_serial"


@pytest.fixture(scope="module")
def sim_bin():
    if not (shutil.which("g++") and shutil.which("make")):
        pytest.skip("sem g++/make")
    r = subprocess.run(["make", "-C", str(FW), "build/sim_stdio"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return FW / "build" / "sim_stdio"


@pytest.fixture
def client(sim_bin):
    t = ProcessTransport([str(sim_bin)])
    yield Client(t, timeout=0.5, long_timeout=5.0)
    t.close()


def test_info_do_firmware(client):
    info = client.info()
    assert info["proto"] == 1 and info["mock"] and info["firmware"] == "0.1.0"


def test_detect(client):
    r = client.detect(255)
    assert r["status"] == 0 and r["name"] == "MOCK" and r["rom_size"] == 32768 and r["save_size"] == 8192


def test_dump_rom_bate_com_o_padrao_e_o_crc(client):
    res = client.dump_rom(255)
    assert res.data == P.mock_data()
    assert res.crc32 == P.crc32(P.mock_data())


@pytest.mark.parametrize("block", [64, 200, 1020])
def test_blocos_variados(client, block):
    assert client.dump_rom(255, block).data == P.mock_data()


def test_read_save(client):
    res = client.read_save(255)
    assert res.data == bytes((i * 3 + 1) & 0xFF for i in range(8192))


def test_write_save_valida_crc_no_firmware(client):
    data = bytes((i * 5) & 0xFF for i in range(3000))
    assert client.write_save(255, data, 512) == P.crc32(data)


def test_sistema_sem_suporte_e_erro_2(client):
    with pytest.raises(P.DeviceError) as e:
        client.dump_rom(1)
    assert e.value.code == 2


def test_dois_dumps_seguidos_no_mesmo_firmware(client):
    assert client.dump_rom(255).data == client.dump_rom(255).data == P.mock_data()
