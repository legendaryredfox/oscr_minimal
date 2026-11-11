"""Autoteste da placa sem cartucho (P-12): quadro SELFTEST, texto dos achados e código de saída da CLI."""
import json

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import main
from oscr_host.client import Client, TimeoutError_


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_nome_dos_pinos():
    assert P.pin_name(22) == "D22" and P.pin_name(53) == "D53" and P.pin_name(54) == "A0" and P.pin_name(69) == "A15"


def test_parse_resposta():
    r = P.parse_selftest_resp(bytes([0, 0]))
    assert r == {"ok": True, "truncated": False, "findings": []}
    r = P.parse_selftest_resp(bytes([0, 3, P.ST_GND, 30, 0, P.ST_PAIR, 22, 57, P.ST_NO_PULLUP, 7, 0]))
    assert not r["ok"]
    assert r["findings"] == [{"kind": "gnd", "pins": ["D30"]}, {"kind": "pair", "pins": ["D22", "A3"]}, {"kind": "pullup", "pins": ["D7"]}]
    r = P.parse_selftest_resp(bytes([1, 1, P.ST_NO_CLOCKGEN, 0, 0]))
    assert r["truncated"] and r["findings"] == [{"kind": "clockgen", "pins": []}]
    assert P.parse_selftest_resp(bytes([0, 1, 99, 5, 6]))["findings"][0]["kind"] == "unknown99"     # tipo novo de um firmware mais novo
    with pytest.raises(P.ProtocolError):
        P.parse_selftest_resp(bytes([0, 2, 1, 2]))
    with pytest.raises(P.ProtocolError):
        P.parse_selftest_resp(b"")


def test_info_anuncia_o_autoteste():
    t, dev, stop, th = sim.start(sim.MockDevice())
    try:
        c = Client(t, timeout=0.5, long_timeout=5.0)
        assert c.info()["selftest"] is True
        assert c.selftest() == {"ok": True, "truncated": False, "findings": []}
        assert dev.selftest_calls == 1
    finally:
        t.close()


def test_simulador_corta_em_24_achados():
    t, dev, stop, th = sim.start(sim.MockDevice(selftest_report=[(P.ST_GND, 22 + i % 10, 0) for i in range(30)]))
    try:
        r = Client(t, timeout=0.5, long_timeout=5.0).selftest()
        assert r["truncated"] and len(r["findings"]) == 24 and not r["ok"]
    finally:
        t.close()


def test_cli_sem_problema(capsys):
    code, out, err = run(capsys, "--simulate", "--json", "selftest")
    assert code == 0 and json.loads(out) == {"ok": True, "truncated": False, "findings": []}


def test_cli_com_problemas_sai_com_1(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_SELFTEST", "1")
    code, out, err = run(capsys, "--simulate", "--json", "selftest")
    d = json.loads(out)
    assert code == 1 and not d["ok"] and d["findings"][0] == {"kind": "gnd", "pins": ["D30"]} and d["findings"][1] == {"kind": "pair", "pins": ["D22", "A3"]}
    code, out, err = run(capsys, "--simulate", "--lang", "pt-BR", "selftest")
    assert code == 1 and "pino D30 em curto com GND" in out and "pinos D22 e A3 em curto entre si" in out and "2 problema(s)" in out
    assert "Demora" in err or "demora" in err                                          # o aviso de espera vai para o stderr
    code, out, err = run(capsys, "--simulate", "--lang", "en", "selftest")
    assert "pin D30 is shorted to GND" in out and "pins D22 and A3 are shorted together" in out


def test_cli_firmware_sem_autoteste(capsys, monkeypatch):
    orig = sim.MockDevice._handle
    def sem_bit6(self, t, f):                                                          # firmware antigo: INFO sem o bit6
        if f.type == P.T_INFO:
            return self._send(t, P.T_INFO_RESP, f.seq, bytes([P.PROTO_VERSION, 0, 1, 0, 0b11001]) + (0).to_bytes(2, "little") + P.MAX_PAYLOAD.to_bytes(2, "little"))
        return orig(self, t, f)
    monkeypatch.setattr(sim.MockDevice, "_handle", sem_bit6)
    code, out, err = run(capsys, "--simulate", "--json", "selftest")
    assert code == 1 and json.loads(out)["error"]["kind"] == "no_selftest"
