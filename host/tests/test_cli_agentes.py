# SPDX-License-Identifier: GPL-3.0-or-later
"""Contrato da CLI para agentes de IA (docs/cli.md): JSON, erros estruturados, códigos de saída."""
import json

from oscr_host import protocol as P
from oscr_host.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_json_depois_do_subcomando(capsys):
    code, out, _ = run(capsys, "detect", "-s", "mock", "--simulate", "--json")
    o = json.loads(out)
    assert code == 0 and o["ok"] is True and o["status"] == 0 and o["status_text"]


def test_todo_json_tem_ok(tmp_path, capsys):
    for argv in (["info"], ["systems"], ["errors"], ["dump", "-s", "mock", "-o", str(tmp_path / "a")]):
        code, out, _ = run(capsys, "--simulate", "--json", *argv)
        o = json.loads(out)
        assert code == 0 and o["ok"] is True, argv


def test_systems_e_errors_nao_abrem_a_porta(capsys):
    code, out, _ = run(capsys, "systems", "--json")          # sem --simulate nem hardware
    assert code == 0
    names = {s["name"] for s in json.loads(out)["systems"]}
    assert names == set(P.SYSTEMS)
    code, out, _ = run(capsys, "errors", "--json")
    o = json.loads(out)
    assert {e["code"] for e in o["device_errors"]} == set(P.ERRORS)
    assert {e["exit_code"] for e in o["exit_codes"]} >= {0, 1, 2, 3, 4, 64}


def test_sem_porta_da_saida_3_com_json(capsys, monkeypatch):
    monkeypatch.setattr("oscr_host.cli.list_ports", lambda: [])
    code, out, _ = run(capsys, "--json", "detect")
    o = json.loads(out)
    assert code == 3 and o["ok"] is False and o["error"]["kind"] == "no_port" and o["error"]["hint"]


def test_uso_invalido_da_saida_64(capsys):
    import pytest

    with pytest.raises(SystemExit) as e:
        main(["--json", "detect", "-s", "naoexiste"])
    assert e.value.code == 64
    o = json.loads(capsys.readouterr().out)
    assert o["ok"] is False and o["error"]["kind"] == "usage"


def test_recusa_sem_yes_em_json(tmp_path, capsys):
    src = tmp_path / "in.sav"
    src.write_bytes(b"\x00" * 16)
    code, out, _ = run(capsys, "--simulate", "--json", "save-write", "-s", "mock", "-i", str(src), "--backup-dir", str(tmp_path / "bk"))
    o = json.loads(out)
    assert code == 4 and o["error"]["kind"] == "refused" and "--yes" in o["error"]["hint"]


def test_arquivo_inexistente_vira_erro_io(tmp_path, capsys):
    code, out, _ = run(capsys, "--simulate", "--json", "save-write", "-s", "mock", "-i", str(tmp_path / "nao"), "--yes")
    assert code == 1 and json.loads(out)["error"]["kind"] == "io"


def test_progresso_jsonl_em_stderr(tmp_path, capsys):
    code, out, err = run(capsys, "--simulate", "--json", "--progress", "jsonl", "dump", "-s", "mock", "-o", str(tmp_path / "p"))
    assert code == 0 and json.loads(out)["ok"]
    ev = [json.loads(l) for l in err.splitlines() if l.startswith("{")]
    assert ev and ev[-1]["event"] == "progress" and ev[-1]["percent"] == 100 and ev[-1]["done"] == ev[-1]["total"]
