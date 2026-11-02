# SPDX-License-Identifier: GPL-3.0-or-later
"""Cliente x simulador (modo MOCK): leitura, recuperação de falhas e gravação."""
import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.client import Client, TimeoutError_


@pytest.fixture
def env():
    t, dev, stop, th = sim.start()
    c = Client(t, timeout=0.3, long_timeout=3.0)
    yield c, dev
    stop.set()
    th.join(1)


def test_info(env):
    c, _ = env
    info = c.info()
    assert info["proto"] == 1 and info["mock"] is True


def test_detect_mock_e_sem_cartucho(env):
    c, _ = env
    r = c.detect(255)
    assert r["status"] == 0 and r["name"] == "MOCK" and r["rom_size"] == 32768
    assert c.detect(1)["status"] == 1


def test_dump_rom_reconstroi_o_arquivo(env):
    c, _ = env
    seen = []
    res = c.dump_rom(255, 0, lambda d, t: seen.append(d))
    assert res.data == P.mock_data() and res.crc32 == P.crc32(P.mock_data())
    assert seen[-1] == 32768 and seen == sorted(seen)


@pytest.mark.parametrize("block", [64, 512, 1020])
def test_blocos_de_tamanhos_diferentes(env, block):
    c, _ = env
    assert c.dump_rom(255, block).data == P.mock_data()


def test_bloco_corrompido_e_reenviado(env):
    c, dev = env
    dev.corrupt_data = 3
    assert c.dump_rom(255, 512).data == P.mock_data()


def test_acks_perdidos_nao_duplicam_dados(env):
    c, dev = env
    dev.drop_next_acks = 2          # abaixo do limite de 3 reenvios
    assert c.dump_rom(255, 512).data == P.mock_data()


def test_muitos_acks_perdidos_dao_erro_5(env):
    c, dev = env
    dev.drop_next_acks = 50
    with pytest.raises(P.DeviceError) as e:
        c.dump_rom(255, 512)
    assert e.value.code == 5


def test_read_save(env):
    c, dev = env
    res = c.read_save(255)
    assert res.kind == P.KIND_SAVE and res.data == dev.save


def test_write_save_confere_crc_e_grava(env):
    c, dev = env
    data = bytes(range(256)) * 20
    crc = c.write_save(255, data, 512)
    assert crc == P.crc32(data) and dev.written_save == data


def test_write_save_sistema_invalido(env):
    c, _ = env
    with pytest.raises(P.DeviceError) as e:
        c.write_save(1, b"\x00" * 16)
    assert e.value.code == 2


def test_dump_sem_cartucho_da_erro_3(env):
    c, _ = env
    with pytest.raises(P.DeviceError) as e:
        c.dump_rom(2)
    assert e.value.code == 3


def test_sem_dispositivo_estoura_o_tempo():
    from oscr_host.transport import pair

    a, _b = pair()
    c = Client(a, timeout=0.05, long_timeout=0.1, retries=1)
    with pytest.raises(TimeoutError_):
        c.info()


def test_cli_dump_simulado(tmp_path, capsys):
    from oscr_host.cli import main

    out = tmp_path / "x"
    assert main(["--simulate", "dump", "-s", "mock", "-o", str(out)]) == 0
    f = tmp_path / "x.bin"
    assert f.read_bytes() == P.mock_data()
    assert f"{P.crc32(P.mock_data()):08X}" in capsys.readouterr().out


def test_cli_save_roundtrip(tmp_path, capsys):
    from oscr_host.cli import main

    src = tmp_path / "in.sav"
    src.write_bytes(bytes(range(200)))
    assert main(["--simulate", "save-write", "-s", "mock", "-i", str(src)]) == 0
    assert main(["--simulate", "save-read", "-s", "mock", "-o", str(tmp_path / "s")]) == 0
    assert (tmp_path / "s.sav").stat().st_size == 8192
