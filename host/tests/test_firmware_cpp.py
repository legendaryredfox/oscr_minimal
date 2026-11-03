# SPDX-License-Identifier: GPL-3.0-or-later
"""Teste cruzado: o cliente Python fala com o código REAL do firmware (compilado no PC).

Compila os arquivos do protocolo do fork (firmware/oscr/src/dumper, g++) e roda `sim_stdio`. Pula se não houver g++/make.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from oscr_host import protocol as P
from oscr_host.client import Client
from oscr_host.transport import ProcessTransport

FW = Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "pc-tests"


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


def test_firmware_aceita_opcoes_de_mapper_sem_quebrar(client):
    assert client.dump_rom(255, 0, mapper=4, prg_kb=128, chr_kb=128).data == P.mock_data()


# ---------------------------------------------------------------- modo fluxo (núcleos do OSCR): tamanho desconhecido no BEGIN
@pytest.fixture
def stream_client(sim_bin):
    t = ProcessTransport([str(sim_bin), "stream"])
    yield Client(t, timeout=0.5, long_timeout=5.0)
    t.close()


@pytest.mark.parametrize("block", [64, 200, 512, 1020])
def test_fluxo_rom_com_tamanho_desconhecido(stream_client, block):
    seen = []
    res = stream_client.dump_rom(255, block, progress=lambda done, total: seen.append((done, total)))
    assert res.data == bytes(((i * 7 + (i >> 8)) & 0xFF) for i in range(5000))
    assert res.crc32 == P.crc32(res.data)
    assert seen and all(t == 0 for _, t in seen) and seen[-1][0] == 5000      # total 0 = desconhecido


def test_fluxo_save(stream_client):
    res = stream_client.read_save(255)
    assert res.data == bytes(((i * 3 + 1) & 0xFF) for i in range(2000))


@pytest.mark.parametrize("size,block", [(3000, 512), (1, 512), (513, 100), (4096, 1020)])
def test_fluxo_write_save_so_confirma_depois_de_consumir(stream_client, size, block):
    data = bytes((i * 5) & 0xFF for i in range(size))
    assert stream_client.write_save(255, data, block) == P.crc32(data)


def test_fluxo_write_save_com_dado_errado_e_erro_7(stream_client):
    data = bytearray((i * 5) & 0xFF for i in range(1000)); data[700] ^= 0xFF
    with pytest.raises(P.DeviceError) as e:
        stream_client.write_save(255, bytes(data), 512)
    assert e.value.code == 7


# ---- WRITE_ROM contra a sessão REAL do firmware (modo fluxo): o apagamento acontece antes do primeiro ACK


@pytest.fixture
def stream_client(sim_bin):
    t = ProcessTransport([str(sim_bin), "stream"])
    yield Client(t, timeout=0.5, long_timeout=5.0)
    t.close()


def test_write_rom_fluxo(stream_client):
    data = bytes((i * 5) & 0xFF for i in range(32 * 1024))
    crc = stream_client.write_rom(255, data, chip=1, prg_kb=32, chr_kb=0, block=512)
    assert crc == P.crc32(data)


def test_write_rom_chip_nao_reconhecido(stream_client):
    with pytest.raises(P.DeviceError) as e:
        stream_client.write_rom(255, bytes(16384), chip=9, prg_kb=16, chr_kb=0)
    assert e.value.code == 11


def test_write_rom_tamanho_errado(stream_client):
    with pytest.raises(P.DeviceError) as e:
        stream_client.write_rom(255, bytes(16384), chip=1, prg_kb=32, chr_kb=0)
    assert e.value.code == 4


def test_write_rom_dado_errado_da_erro_de_cartucho(stream_client):
    with pytest.raises(P.DeviceError) as e:
        stream_client.write_rom(255, bytes(16384), chip=1, prg_kb=16, chr_kb=0)      # o simulador espera o padrão i*5
    assert e.value.code in (7, 6)
