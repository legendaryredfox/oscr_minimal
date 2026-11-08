"""Seletor de tensão do cartucho (D138): padrão 5 V, 3,3 V opcional, alerta e confirmação ao passar de 3,3 V para 5 V."""
import json
from types import SimpleNamespace

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import common, main
from oscr_host.cli.errors import CliError, EXIT_REFUSED, EXIT_USAGE
from oscr_host.client import Client


def _client(**kw):
    t, dev, stop, th = sim.start(sim.MockDevice(power_switch=True, volt_select=True, **kw))
    return Client(t, timeout=0.5, long_timeout=5.0), dev, t


def _args(**kw):
    d = dict(voltage="auto", allow_5v=False, json=True)
    d.update(kw)
    return SimpleNamespace(**d)


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_simulador_liga_em_5v_e_volta_a_5v_depois_de_desligar():
    c, dev, t = _client()
    try:
        assert c.power(P.POWER_STATUS)["voltage"] == "5v"
        r = c.power(P.POWER_ON)
        assert r["on"] and r["voltage"] == "5v" and r["voltage_select"]
        assert c.power(P.POWER_ON_3V3)["voltage"] == "3v3"
        assert c.power(P.POWER_OFF)["voltage"] == "5v"            # desligado, volta ao padrão
    finally:
        t.close()


def test_padrao_liga_a_5v_sem_alerta(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_POWER", "1")
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    code, out, err = run(capsys, "--simulate", "--json", "power", "on")
    assert code == 0 and json.loads(out)["voltage"] == "5v" and err == ""
    code, out, err = run(capsys, "--simulate", "--json", "power", "on", "--voltage", "5v")
    assert code == 0 and json.loads(out)["voltage"] == "5v" and err == ""      # 5 V com o slot desligado: nada a avisar


def test_voltage_3v3_liga_a_3v3(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_POWER", "1")
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    code, out, err = run(capsys, "--simulate", "--json", "power", "on", "--voltage", "3v3")
    assert code == 0 and json.loads(out)["voltage"] == "3v3"


def test_voltage_3v3_em_placa_sem_seletor_recusa(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_POWER", "1")
    monkeypatch.delenv("OSCR_SIM_VOLT", raising=False)
    code, out, err = run(capsys, "--simulate", "--json", "detect", "-s", "md", "--voltage", "3v3")
    assert code == EXIT_USAGE and json.loads(out)["error"]["kind"] == "no_selector"


def test_falha_de_leitura_a_3v3_nao_sobe_para_5v(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("OSCR_SIM_POWER", "1")
    monkeypatch.setenv("OSCR_SIM_VOLT", "1")
    monkeypatch.setenv("OSCR_SIM_5V_CART", "1")                            # cartucho simulado que só lê a 5 V
    code, out, err = run(capsys, "--simulate", "--json", "dump", "-s", "md", "--voltage", "3v3", "--allow-5v", "-o", str(tmp_path / "x.md"))
    assert code != 0                                                       # não leu a 3,3 V
    assert "ATENÇÃO" not in err and "WARNING" not in err                   # e não alertou nem subiu sozinho para 5 V
    assert not (tmp_path / "x.md").exists()


def test_3v3_para_5v_pede_confirmacao_e_recusa_em_script():
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3"), c, c.power(P.POWER_STATUS))
        assert c.power(P.POWER_STATUS)["voltage"] == "3v3"
        with pytest.raises(CliError) as e:                                 # --json: sem terminal para perguntar e sem --allow-5v
            common.set_voltage(_args(voltage="5v"), c, c.power(P.POWER_STATUS))
        assert e.value.exit_code == EXIT_REFUSED and e.value.kind == "refused"
        assert c.power(P.POWER_STATUS)["voltage"] == "3v3"                 # continua em 3,3 V
    finally:
        t.close()


def test_3v3_para_5v_com_allow_5v_mostra_o_alerta(capsys):
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3"), c, c.power(P.POWER_STATUS))
        capsys.readouterr()
        r = common.set_voltage(_args(voltage="5v", allow_5v=True), c, c.power(P.POWER_STATUS))
        err = capsys.readouterr().err
        assert r["voltage"] == "5v" and dev.volt == 2
        assert "#" * 78 in err and "RISCO DE DANIFICAR" in err          # o alerta aparece antes de subir
    finally:
        t.close()


def test_3v3_para_5v_interativo(monkeypatch, capsys):
    c, dev, t = _client()
    try:
        common.set_voltage(_args(voltage="3v3", json=False), c, c.power(P.POWER_STATUS))
        monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)
        monkeypatch.setattr("builtins.input", lambda prompt="": "nao")
        with pytest.raises(CliError):
            common.set_voltage(_args(voltage="5v", json=False), c, c.power(P.POWER_STATUS))
        assert dev.volt == 1
        monkeypatch.setattr("builtins.input", lambda prompt="": "5V")
        r = common.set_voltage(_args(voltage="5v", json=False), c, c.power(P.POWER_STATUS))
        assert r["voltage"] == "5v" and dev.volt == 2
    finally:
        t.close()
