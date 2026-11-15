# SPDX-License-Identifier: GPL-3.0-or-later
"""BOARD: perfil da placa guardado na EEPROM do firmware (D162). Cliente Python contra o simulador Python e contra o código real do firmware (C++)."""
import shutil
import subprocess
from pathlib import Path

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.client import Client
from oscr_host.protocol import DeviceError
from oscr_host.transport import ProcessTransport

FW = Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "pc-tests"


def _py(**kw):
    t, dev, stop, th = sim.start(sim.MockDevice(**kw))
    return Client(t, timeout=0.5, long_timeout=5.0), dev


def test_info_diz_que_o_firmware_tem_board():
    c, _ = _py()
    assert c.info()["board_profile"] is True


def test_firmware_sem_board_nao_anuncia_e_recusa():
    c, _ = _py(board_profile=False)
    assert c.info()["board_profile"] is False
    with pytest.raises(DeviceError):
        c.board()


def test_consulta_sem_perfil_guardado():
    c, dev = _py()
    r = c.board()
    assert r == {"stored": False, "voltage_select": False} and dev.board_calls == []


def test_gravar_perfil_com_seletor_liga_o_bit5_do_info():
    c, dev = _py()
    assert c.info()["voltage_select"] is False
    r = c.board(P.BOARD_SET, P.BOARD_VOLT_SELECT)
    assert r == {"stored": True, "voltage_select": True} and dev.board_calls == [1]
    assert c.info()["voltage_select"] is True
    assert c.voltage()["voltage_select"] is True


def test_gravar_perfil_sem_seletor_desliga():
    c, dev = _py(volt_select=True)
    r = c.board(P.BOARD_SET, 0)
    assert r == {"stored": True, "voltage_select": False}
    assert c.info()["voltage_select"] is False
    assert c.voltage()["voltage"] == "5v-fixed"


def test_bits_desconhecidos_e_acao_invalida_sao_recusados():
    c, dev = _py()
    with pytest.raises(DeviceError):
        c.board(P.BOARD_SET, 2)
    with pytest.raises(DeviceError):
        c.board(5)
    assert dev.board_calls == []


@pytest.fixture(scope="module")
def sim_bin():
    if not (shutil.which("g++") and shutil.which("make")):
        pytest.skip("sem g++/make")
    r = subprocess.run(["make", "-C", str(FW), "build/sim_stdio"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return FW / "build" / "sim_stdio"


def test_contra_o_codigo_real_do_firmware(sim_bin):
    t = ProcessTransport([str(sim_bin), "board"])
    try:
        c = Client(t, timeout=0.5, long_timeout=5.0)
        i = c.info()
        assert i["board_profile"] and not i["voltage_select"] and i["firmware"] == "0.2.0"
        assert c.board() == {"stored": False, "voltage_select": False}
        assert c.board(P.BOARD_SET, P.BOARD_VOLT_SELECT) == {"stored": True, "voltage_select": True}
        assert c.info()["voltage_select"] is True
        assert c.board(P.BOARD_SET, 0) == {"stored": True, "voltage_select": False}
        with pytest.raises(DeviceError):
            c.board(P.BOARD_SET, 4)
    finally:
        t.close()
