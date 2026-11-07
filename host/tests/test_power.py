"""POWER: chave de 5V dos slots (D115). Cliente, simulador, CLI e o Session real do firmware (compilado no PC)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import main
from oscr_host.client import Client


def _client(power_switch):
    t, dev, stop, th = sim.start(sim.MockDevice(power_switch=power_switch))
    return Client(t, timeout=0.5, long_timeout=5.0), dev, t, stop


def test_placa_com_chave_comeca_desligada_e_recusa_cartucho():
    c, dev, t, stop = _client(True)
    try:
        assert c.info()["power_switch"] is True
        assert c.power(P.POWER_STATUS)["on"] is False
        with pytest.raises(P.DeviceError) as e:
            c.detect(1)                                       # SNES com o 5V desligado
        assert e.value.code == 12 and "desligado" in P.ERRORS[12]
        assert c.detect(255)["name"] == "MOCK"                # o MOCK não precisa de cartucho
        r = c.power(P.POWER_ON)
        assert r["on"] and "switch" not in r and r["rail_low"] is None
        assert c.detect(1)["status"] == 1                     # ligado: o simulador responde "nenhum cartucho"
        assert c.power(P.POWER_OFF)["on"] is False and dev.power_calls == [1, 0]
    finally:
        stop.set(); t.close()


def test_placa_sem_chave_nao_muda_nada():
    c, dev, t, stop = _client(False)
    try:
        assert c.info()["power_switch"] is False
        assert c.power(P.POWER_STATUS)["on"] is True and c.power(P.POWER_ON)["on"] is True
        with pytest.raises(P.DeviceError) as e:
            c.power(P.POWER_OFF)                              # não dá para cortar um 5V que não tem chave
        assert e.value.code == 1
        with pytest.raises(P.DeviceError) as e:
            c.power(7)
        assert e.value.code == 4
        assert dev.power_calls == []
    finally:
        stop.set(); t.close()


def run(capsys, *argv):
    code = main(list(argv))
    return code, capsys.readouterr().out


def test_cli_power_status_on_off_json(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_POWER", "1")
    code, out = run(capsys, "--simulate", "--json", "power", "status")
    o = json.loads(out)
    assert code == 0 and o["state"] == "off" and o["power_switch"] is True
    code, out = run(capsys, "--simulate", "--json", "power", "on")
    assert code == 0 and json.loads(out)["state"] == "on"
    code, out = run(capsys, "--simulate", "--json", "power", "off")      # cada comando abre um simulador novo; off a partir de off
    assert code == 0 and json.loads(out)["state"] == "off"


def test_cli_liga_sozinha_ou_respeita_keep(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_POWER", "1")
    code, out = run(capsys, "--simulate", "--json", "detect", "-s", "snes")
    assert code == 2 and json.loads(out)["status"] == 1                  # ligou sozinha, o simulador diz "nenhum cartucho"
    code, out = run(capsys, "--simulate", "--json", "--power", "keep", "detect", "-s", "snes")
    err = json.loads(out)
    assert code == 1 and err["error"]["kind"] == "device_error" and err["error"]["device_code"] == 12
    assert "dumper power on" in err["error"]["hint"]
    code, out = run(capsys, "--simulate", "--json", "info")              # info nunca liga o 5V
    assert code == 0 and json.loads(out)["power_switch"] is True


def test_cli_sem_chave(capsys, monkeypatch):
    monkeypatch.delenv("OSCR_SIM_POWER", raising=False)
    code, out = run(capsys, "--simulate", "--json", "power", "status")
    o = json.loads(out)
    assert code == 0 and o["state"] == "on" and o["power_switch"] is False
    code, out = run(capsys, "--simulate", "--json", "power", "off")
    assert code == 1 and json.loads(out)["error"]["device_code"] == 1


FW = Path(__file__).resolve().parents[2] / "firmware" / "oscr" / "pc-tests"


def test_firmware_real_com_a_chave():
    if not (shutil.which("g++") and shutil.which("make")):
        pytest.skip("sem g++/make")
    r = subprocess.run(["make", "-C", str(FW), "build/sim_stdio"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    from oscr_host.transport import ProcessTransport

    t = ProcessTransport([str(FW / "build" / "sim_stdio"), "power"])
    try:
        c = Client(t, timeout=0.5, long_timeout=5.0)
        assert c.info()["power_switch"] is True
        assert c.power(P.POWER_STATUS)["on"] is False
        with pytest.raises(P.DeviceError) as e:
            c.detect(1)
        assert e.value.code == 12
        assert c.power(P.POWER_ON)["on"] is True and c.detect(1)["status"] == 0
        assert c.power(P.POWER_OFF)["on"] is False
    finally:
        t.close()


# ---------------------------------------------------------------- sensor do rail e tentativas do SA-1 (D119, D123: sem chave física)
def _hw(**kw):
    t, dev, stop, th = sim.start(sim.MockDevice(rail_sensor=True, **kw))
    return Client(t, timeout=0.5, long_timeout=5.0), dev, t, stop


def test_sensor_do_rail_acompanha_o_5v():
    c, dev, t, stop = _hw()
    try:
        assert c.info()["power_switch"] is True                        # o sensor implica a chave de 5V em software
        r = c.power(P.POWER_STATUS)
        assert r["rail_sensor"] and r["on"] is False and r["rail_low"] is True and "switch" not in r      # desligado: o rail caiu, seguro trocar
        with pytest.raises(P.DeviceError) as e:
            c.detect(1)                                                # 5V desligado: recusa
        assert e.value.code == 12
        r = c.power(P.POWER_ON)
        assert r["on"] and r["rail_low"] is False                      # ligado: o rail está alto
        r = c.power(P.POWER_OFF)
        assert r["on"] is False and r["rail_low"] is True
    finally:
        stop.set(); t.close()


def test_detect_informa_as_tentativas_do_sa1():
    c, dev, t, stop = _hw(detect_attempts=3)
    try:
        c.power(P.POWER_ON)
        assert c.detect(1)["attempts"] == 3
        assert c.detect(255)["attempts"] == 1                              # o MOCK não usa ciclo de energia
    finally:
        stop.set(); t.close()


def test_parse_detect_sem_o_byte_extra_vale_uma_tentativa():
    p = bytes([1, 0]) + (1).to_bytes(4, "little") + (2).to_bytes(4, "little") + bytes([0, 4]) + b"ABCD"
    assert P.parse_detect_resp(p)["attempts"] == 1
    assert P.parse_detect_resp(p + bytes([2]))["attempts"] == 2


def test_cli_sensor_do_rail(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_SENSE", "1")
    code, out = run(capsys, "--simulate", "--json", "power", "status")
    o = json.loads(out)
    assert code == 0 and o["rail_sensor"] is True and o["rail_low"] is True and "switch" not in o
    code, out = run(capsys, "--simulate", "--json", "detect", "-s", "snes")
    assert code == 2 and json.loads(out)["attempts"] == 3                   # ligou sozinha; o simulador informa 3 tentativas
