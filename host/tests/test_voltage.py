"""Seletor de tensão do cartucho (D138): a placa sobe em 3,3 V (estado seguro), o padrão do host é 5 V, 3,3 V opcional,
alerta e confirmação ao passar de 3,3 V (escolhido) para 5 V. O 5V dos slots fica sempre ligado (D139)."""
import json
from types import SimpleNamespace

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import common, main
from oscr_host.cli.errors import CliError, EXIT_REFUSED, EXIT_USAGE
from oscr_host.client import Client


def _client(**kw):
    t, dev, stop, th = sim.start(sim.MockDevice(volt_select=True, **kw))
    return Client(t, timeout=0.5, long_timeout=5.0), dev, t


def _args(**kw):
    d = dict(voltage="auto", allow_5v=False, json=True)
    d.update(kw)
    return SimpleNamespace(**d)


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_simulador_sobe_em_3v3_sem_escolha():
    c, dev, t = _client()
    try:
        r = c.voltage(P.VOLT_STATUS)
        assert r["voltage"] == "3v3" and r["voltage_select"] and not r["chosen"]      # estado seguro: ninguém escolheu
        assert c.voltage(P.VOLT_5V)["voltage"] == "5v"
        r = c.voltage(P.VOLT_3V3)
        assert r["voltage"] == "3v3" and r["chosen"]
    finally:
        t.close()


def test_padrao_sobe_a_5v_sem_alerta(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    code, out, err = run(capsys, "--simulate", "--json", "voltage", "5v")
    assert code == 0 and json.loads(out)["voltage"] == "5v" and err == ""             # a placa subiu em 3,3 V sem escolha: nada a avisar
    code, out, err = run(capsys, "--simulate", "--json", "detect", "-s", "md")        # comando de cartucho com --voltage auto: 5 V
    assert code in (0, 2) and err == ""


def test_comando_de_cartucho_sem_voltage_pede_5v(monkeypatch):
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    c, dev, t = _client()
    try:
        r = common.set_voltage(_args(), c, c.voltage(P.VOLT_STATUS))
        assert r["voltage"] == "5v" and dev.volt == 2 and dev.volt_calls == [2]
    finally:
        t.close()


def test_voltage_3v3_usa_3v3(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    code, out, err = run(capsys, "--simulate", "--json", "voltage", "3v3")
    assert code == 0 and json.loads(out)["voltage"] == "3v3" and json.loads(out)["chosen"]


def test_voltage_3v3_em_placa_sem_seletor_recusa(capsys, monkeypatch):
    monkeypatch.delenv("OSCR_SIM_VOLT", raising=False)
    code, out, err = run(capsys, "--simulate", "--json", "detect", "-s", "md", "--voltage", "3v3")
    assert code == EXIT_USAGE and json.loads(out)["error"]["kind"] == "no_selector"


def test_falha_de_leitura_a_3v3_nao_sobe_para_5v(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    monkeypatch.setenv("OSCR_SIM_5V_CART", "1")                            # cartucho simulado que só lê a 5 V
    code, out, err = run(capsys, "--simulate", "--json", "dump", "-s", "md", "--voltage", "3v3", "--allow-5v", "-o", str(tmp_path / "x.md"))
    assert code != 0                                                       # não leu a 3,3 V
    assert "ATENÇÃO" not in err and "WARNING" not in err                   # e não alertou nem subiu sozinho para 5 V
    assert not (tmp_path / "x.md").exists()


def test_3v3_para_5v_pede_confirmacao_e_recusa_em_script():
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3"), c, c.voltage(P.VOLT_STATUS))
        assert c.voltage(P.VOLT_STATUS)["voltage"] == "3v3"
        with pytest.raises(CliError) as e:                                 # --json: sem terminal para perguntar e sem --allow-5v
            common.set_voltage(_args(voltage="5v"), c, c.voltage(P.VOLT_STATUS))
        assert e.value.exit_code == EXIT_REFUSED and e.value.kind == "refused"
        assert c.voltage(P.VOLT_STATUS)["voltage"] == "3v3"                # continua em 3,3 V
    finally:
        t.close()


def test_auto_depois_de_escolher_3v3_mantem_3v3():
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3"), c, c.voltage(P.VOLT_STATUS))
        n = len(dev.volt_calls)
        common.set_voltage(_args(voltage="auto"), c, c.voltage(P.VOLT_STATUS))     # a escolha do usuário vale até ele mudar
        assert dev.volt == 1 and len(dev.volt_calls) == n
    finally:
        t.close()


def test_3v3_para_5v_com_allow_5v_mostra_o_alerta(capsys):
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3"), c, c.voltage(P.VOLT_STATUS))
        capsys.readouterr()
        r = common.set_voltage(_args(voltage="5v", allow_5v=True), c, c.voltage(P.VOLT_STATUS))
        err = capsys.readouterr().err
        assert r["voltage"] == "5v" and dev.volt == 2
        assert "#" * 78 in err and "RISCO DE DANIFICAR" in err          # o alerta aparece antes de subir
    finally:
        t.close()


def test_3v3_para_5v_interativo(monkeypatch, capsys):
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3", json=False), c, c.voltage(P.VOLT_STATUS))
        monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)
        monkeypatch.setattr("builtins.input", lambda prompt="": "nao")
        with pytest.raises(CliError):
            common.set_voltage(_args(voltage="5v", json=False), c, c.voltage(P.VOLT_STATUS))
        assert dev.volt == 1
        monkeypatch.setattr("builtins.input", lambda prompt="": "5V")
        r = common.set_voltage(_args(voltage="5v", json=False), c, c.voltage(P.VOLT_STATUS))
        assert r["voltage"] == "5v" and dev.volt == 2
    finally:
        t.close()


def test_protocolo_volt_resp():
    assert P.parse_volt_resp(bytes([1, 1, 1])) == {"voltage_select": True, "voltage": "3v3", "chosen": True}
    assert P.parse_volt_resp(bytes([0, 0, 0]))["voltage"] == "5v-fixed"
    with pytest.raises(P.ProtocolError):
        P.parse_volt_resp(bytes([1, 2]))
