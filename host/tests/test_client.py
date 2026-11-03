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
    bdir = tmp_path / "bk"
    assert main(["--simulate", "save-write", "-s", "mock", "-i", str(src), "--yes", "--backup-dir", str(bdir)]) == 0
    assert len(list(bdir.glob("mock_*.sav"))) == 1                       # backup do save anterior, antes de gravar
    assert main(["--simulate", "save-read", "-s", "mock", "-o", str(tmp_path / "s")]) == 0
    assert (tmp_path / "s.sav").stat().st_size == 8192


def test_cli_save_write_recusa_sem_confirmacao(tmp_path):
    import pytest
    from oscr_host.cli import main

    src = tmp_path / "in.sav"
    src.write_bytes(b"\x00" * 16)
    with pytest.raises(SystemExit) as e:                                  # pytest não tem terminal: sem --yes recusa
        main(["--simulate", "save-write", "-s", "mock", "-i", str(src), "--backup-dir", str(tmp_path / "bk")])
    assert "--yes" in str(e.value)
    assert not (tmp_path / "bk").exists()                                 # nada foi lido nem gravado


def test_cli_saida_json(tmp_path, capsys):
    import json
    from oscr_host.cli import main

    assert main(["--simulate", "--json", "detect", "-s", "mock"]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["status"] == 0
    assert main(["--simulate", "--json", "dump", "-s", "mock", "-o", str(tmp_path / "j")]) == 0
    o = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert o["bytes"] == P.MOCK_SIZE and o["crc32"] == f"{P.crc32(P.mock_data()):08X}"


def test_dump_sem_o_usa_o_titulo_como_nome(tmp_path, monkeypatch, capsys):
    from oscr_host.cli import main

    monkeypatch.chdir(tmp_path)
    assert main(["--simulate", "dump", "-s", "mock"]) == 0
    assert (tmp_path / "MOCK.bin").exists()                               # título do DETECT do simulador


def test_erro_do_dispositivo_traz_dica():
    e = P.DeviceError(4, "args")
    assert "argumento inválido" in str(e) and "Dica:" in str(e) and "PRG" in str(e)
    assert "Dica" not in str(P.DeviceError(99))


def test_cliente_recusa_tipo_e_tamanho_errados(env):
    import pytest
    c, _dev = env
    with pytest.raises(P.ProtocolError, match="tipo de dados"):
        c._stream_in(P.T_DUMP_ROM, P.build_dump(255), None, P.KIND_SAVE)   # o simulador responde ROM
    old = P.MAX_STREAM_BYTES
    try:
        P.MAX_STREAM_BYTES = 100
        with pytest.raises(P.ProtocolError, match="absurdo"):
            c.dump_rom(255)
    finally:
        P.MAX_STREAM_BYTES = old


def test_opcoes_de_mapper_chegam_ao_dispositivo(env):
    c, dev = env
    c.dump_rom(255, 512, mapper=4, prg_kb=128, chr_kb=128)
    assert dev.last_options == (4, 128, 128)
    c.dump_rom(255)
    assert dev.last_options == (4, 128, 128)       # sem opções: o payload não as inclui


def test_build_dump_so_inclui_opcoes_quando_pedidas():
    assert len(P.build_dump(2, 512)) == 3
    assert P.build_dump(2, 512, 4, 128, 64) == bytes([2, 0, 2]) + (4).to_bytes(2, "little") + (128).to_bytes(2, "little") + (64).to_bytes(2, "little")


def test_cli_aceita_mapper(tmp_path):
    from oscr_host.cli import main

    assert main(["--simulate", "dump", "-s", "mock", "--mapper", "1", "--prg", "128", "--chr", "64", "-o", str(tmp_path / "m")]) == 0


def test_mapper_chega_no_save_read_e_write(env):
    c, dev = env
    c.read_save(255, 0, None, 4)
    assert dev.last_options == (4, 0, 0)
    c.write_save(255, bytes(range(64)), 512, None, 1)
    assert dev.last_write_mapper == 1
    c.write_save(255, bytes(range(64)))
    assert dev.last_write_mapper == 0


def test_ram_do_save_chega_no_read_e_write(env):
    c, dev = env[0], env[1]
    c.read_save(255, 0, None, 1, 32)
    assert dev.last_options == (1, 32, 0)
    c.write_save(255, bytes(range(64)), 512, None, 1, 16)
    assert (dev.last_write_mapper, dev.last_write_ram_kb) == (1, 16)
    c.write_save(255, bytes(range(64)))
    assert dev.last_write_ram_kb == 0


def test_build_write_save_opcional():
    assert len(P.build_write_save(2, 8192, 512)) == 7
    assert len(P.build_write_save(2, 8192, 512, 4)) == 13
    assert P.build_write_save(2, 32768, 512, 1, 32)[7:] == bytes([1, 0, 32, 0, 0, 0])
