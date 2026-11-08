"""firmware-flash: grava o firmware do fork no Mega com o avrdude (D131). O avrdude aqui é um programa falso que registra os argumentos."""
import json
import os
import stat
import sys
from pathlib import Path

import pytest

from oscr_host.cli import main

FAKE = """#!{py}
import os, sys, json
open(os.environ["FAKE_AVRDUDE_LOG"], "w").write(json.dumps(sys.argv[1:]))
for pct in (0, 50, 100):
    sys.stderr.write("Writing | " + "#" * (pct // 10) + " | %d%% 0.5s\\r" % pct)
sys.stderr.write("\\navrdude: erro de teste\\n" if os.environ.get("FAKE_FAIL") else "\\navrdude done.  Thank you.\\n")
sys.exit(int(os.environ.get("FAKE_FAIL", "0")))
"""


@pytest.fixture
def fake(tmp_path, monkeypatch):
    exe = tmp_path / "avrdude"
    exe.write_text(FAKE.format(py=sys.executable))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    hexf = tmp_path / "firmware.hex"
    hexf.write_text(":00000001FF\n")
    log = tmp_path / "args.json"
    monkeypatch.setenv("FAKE_AVRDUDE_LOG", str(log))
    monkeypatch.delenv("FAKE_FAIL", raising=False)
    return exe, hexf, log


def _run(capsys, *argv):
    code = main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_dry_run_mostra_o_comando_e_nao_grava(fake, capsys):
    exe, hexf, log = fake
    code, out, _ = _run(capsys, "--json", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", str(hexf), "--avrdude", str(exe), "--dry-run")
    r = json.loads(out)
    assert code == 0 and r["ok"] and r["dry_run"] and not log.exists()
    assert r["command"] == [str(exe), "-p", "atmega2560", "-c", "wiring", "-P", "/dev/ttyOSCRteste", "-b", "115200", "-D", "-U", f"flash:w:{hexf}:i"]
    assert r["firmware_before"] is None


def test_grava_com_yes_e_traduz_o_progresso(fake, capsys):
    exe, hexf, log = fake
    code, out, err = _run(capsys, "--json", "--progress", "jsonl", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", str(hexf),
                          "--avrdude", str(exe), "--yes", "--wait", "0")
    r = json.loads(out)
    assert code == 0 and r["ok"] and r["verified"] is True and r["responds"] is False
    assert json.loads(log.read_text())[-2:] == ["-U", f"flash:w:{hexf}:i"] and "-V" not in json.loads(log.read_text())
    ev = [json.loads(l) for l in err.splitlines() if l.startswith("{")]
    assert ev and ev[-1]["label"] == "writing" and ev[-1]["percent"] == 100


def test_no_verify_passa_o_V(fake, capsys):
    exe, hexf, log = fake
    code, out, _ = _run(capsys, "--json", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", str(hexf), "--avrdude", str(exe), "--yes", "--wait", "0", "--no-verify")
    assert code == 0 and "-V" in json.loads(log.read_text()) and json.loads(out)["verified"] is False


def test_avrdude_que_falha_vira_erro_estruturado(fake, capsys, monkeypatch):
    exe, hexf, log = fake
    monkeypatch.setenv("FAKE_FAIL", "1")
    code, out, _ = _run(capsys, "--json", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", str(hexf), "--avrdude", str(exe), "--yes", "--wait", "0")
    e = json.loads(out)["error"]
    assert code == 3 and e["kind"] == "avrdude" and "erro de teste" in e["message"] and "dialout" in e["hint"]


def test_recusa_sem_yes_fora_de_terminal(fake, capsys):
    exe, hexf, log = fake
    code, out, _ = _run(capsys, "--json", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", str(hexf), "--avrdude", str(exe))
    assert code == 4 and json.loads(out)["error"]["kind"] == "refused" and not log.exists()


def test_sem_hex(tmp_path, capsys):
    code, out, _ = _run(capsys, "--json", "-p", "/dev/x", "firmware-flash", "--hex", str(tmp_path / "nao-existe.hex"), "--yes")
    e = json.loads(out)["error"]
    assert code == 64 and e["kind"] == "no_hex" and "pio run" in e["hint"]


def test_sem_avrdude(fake, capsys, monkeypatch, tmp_path):
    _, hexf, _ = fake
    monkeypatch.setenv("PATH", str(tmp_path / "vazio")); monkeypatch.setenv("HOME", str(tmp_path)); monkeypatch.delenv("AVRDUDE", raising=False)
    code, out, _ = _run(capsys, "--json", "-p", "/dev/x", "firmware-flash", "--hex", str(hexf), "--yes")
    e = json.loads(out)["error"]
    assert code == 64 and e["kind"] == "no_avrdude" and "apt install avrdude" in e["hint"]


def test_hex_pela_variavel_e_pelo_env(fake, capsys, monkeypatch):
    exe, hexf, log = fake
    monkeypatch.setenv("OSCR_FIRMWARE_HEX", str(hexf))
    code, out, _ = _run(capsys, "--json", "-p", "/dev/x", "firmware-flash", "--avrdude", str(exe), "--dry-run")
    assert code == 0 and json.loads(out)["hex"] == str(hexf)
    monkeypatch.delenv("OSCR_FIRMWARE_HEX")
    code, out, _ = _run(capsys, "--json", "-p", "/dev/x", "firmware-flash", "--env", "EnvQueNaoExiste", "--avrdude", str(exe), "--dry-run")
    assert code == 64 and "EnvQueNaoExiste" in json.loads(out)["error"]["hint"]


def test_simulador_nao_chama_o_avrdude(fake, capsys):
    _, hexf, log = fake
    code, out, _ = _run(capsys, "--json", "--simulate", "firmware-flash", "--hex", str(hexf), "--yes")
    r = json.loads(out)
    assert code == 0 and r["simulated"] is True and not log.exists() and r["firmware_after"] == r["firmware_before"] != None
