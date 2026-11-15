# SPDX-License-Identifier: GPL-3.0-or-later
"""clock-cal (F-3, P-03): quadro CLOCK, fator a partir da medida, comando da CLI com o simulador, firmware antigo e módulo ausente."""
import json

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import main
from oscr_host.client import Client


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_quadros():
    assert P.build_clock(P.CLOCK_STATUS) == b"\x00" and P.build_clock(P.CLOCK_TEST_ON) == b"\x02"
    assert P.build_clock(P.CLOCK_SET, -1234) == bytes([1]) + (-1234).to_bytes(4, "little", signed=True)
    with pytest.raises(ValueError):
        P.build_clock(P.CLOCK_SET, P.CLOCK_MAX_PPB + 1)
    r = P.parse_clock_resp(bytes([1, 1]) + (-5).to_bytes(4, "little", signed=True) + bytes([1]))
    assert r == {"present": True, "stored": True, "ppb": -5, "test": True}
    with pytest.raises(P.ProtocolError):
        P.parse_clock_resp(bytes(6))


def test_fator_a_partir_da_medida():
    f = P.clock_factor_from_measure
    assert f(4_000_400, 4_000_000) == 100_000                    # saída 100 ppm alta: fator positivo (biblioteca Si5351)
    assert f(3_999_600, 4_000_000) == -100_000
    assert f(4_000_000, 4_000_000) == 0
    assert f(1_000_100, 1_000_000) == 100_000                    # o mesmo erro em ppm dá o mesmo fator em qualquer saída
    # medida já com 100000 ppb em vigor: sobra 100 ppm de erro => o fator total é a composição, não a soma ingênua
    assert f(4_000_400, 4_000_000, 100_000) == round((1.0001 * 1.0001 - 1) * 1e9)
    with pytest.raises(ValueError):
        f(0, 4_000_000)


def test_cliente_e_simulador():
    t, dev, stop, th = sim.start(sim.MockDevice())
    try:
        c = Client(t, timeout=0.5, long_timeout=5.0)
        assert c.clock() == {"present": True, "stored": False, "ppb": 0, "test": False}
        assert c.clock(P.CLOCK_SET, -250)["ppb"] == -250
        assert c.clock(P.CLOCK_TEST_ON)["test"] is True
        assert c.clock(P.CLOCK_TEST_OFF)["test"] is False
        assert c.clock()["stored"] is True and dev.clock_calls == [(0, 0), (1, -250), (2, 0), (3, 0), (0, 0)]
    finally:
        stop.set()


def test_cli_consulta_nao_muda_nada(capsys):
    code, out, err = run(capsys, "--simulate", "--json", "clock-cal")
    r = json.loads(out)
    assert code == 0 and r["present"] and not r["stored"] and r["factor_ppb"] == 0 and not r["applied"]
    assert [x["hz"] for x in r["targets"]] == [4_000_000, 3_072_000, 1_000_000]


def test_cli_aplica_a_medida(capsys):
    code, out, err = run(capsys, "--simulate", "--json", "clock-cal", "--measured", "4000400")
    r = json.loads(out)
    assert code == 0 and r["applied"] and r["stored"] and r["factor_ppb"] == 100_000
    code, out, err = run(capsys, "--simulate", "--json", "clock-cal", "--measured", "1000100", "--target", "1000000")
    assert json.loads(out)["factor_ppb"] == 100_000
    code, out, err = run(capsys, "--simulate", "--json", "clock-cal", "--factor", "-42", "--test", "on")
    r = json.loads(out)
    assert r["factor_ppb"] == -42 and r["test"] is True


def test_cli_argumentos_invalidos(capsys):
    for argv in (["--factor", "1", "--measured", "4000000"], ["--factor", "2000000"], ["--measured", "0"], ["--measured", "5000000"]):
        code, out, err = run(capsys, "--simulate", "--json", "clock-cal", *argv)
        assert code == 64, argv


def test_cli_firmware_antigo(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    code, out, err = run(capsys, "--simulate", "--json", "clock-cal")
    assert code == 1 and json.loads(out)["error"]["kind"] == "no_clock"


def test_modulo_ausente(capsys):
    t, dev, stop, th = sim.start(sim.MockDevice(clock_present=False))
    try:
        c = Client(t, timeout=0.5, long_timeout=5.0)
        assert c.clock()["present"] is False
        with pytest.raises(P.DeviceError) as e:
            c.clock(P.CLOCK_SET, 10)
        assert e.value.code == 7
    finally:
        stop.set()
