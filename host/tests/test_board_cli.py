# SPDX-License-Identifier: GPL-3.0-or-later
"""`--board`: a CLI confere o firmware do Arduino para a placa escolhida e, se faltar suporte, grava o certo depois de pedir confirmação (D162).
Contra o simulador (OSCR_SIM_OLD_FW=1 finge um firmware 0.1.0 antigo) e, no caminho real, contra um avrdude falso."""
import hashlib
import json
import stat
import sys

import pytest

from oscr_host import boards as B
from oscr_host.cli import common, main

ALL = list(range(1, 12))


@pytest.fixture(autouse=True)
def _limpa(monkeypatch):
    monkeypatch.delenv("OSCR_SIM_OLD_FW", raising=False)
    monkeypatch.delenv("OSCR_SIM_SYSTEMS", raising=False)
    monkeypatch.setattr(common, "SIM_FLASHED", False)


@pytest.fixture
def images(tmp_path):
    """Uma pasta de imagens com manifest.json e um .hex qualquer."""
    d = tmp_path / "images"
    d.mkdir()
    hexp = d / "oscr-0.2.0-completa.hex"
    hexp.write_text(":00000001FF\n")
    (d / "manifest.json").write_text(json.dumps({"images": [{"id": "completa", "hex": hexp.name, "firmware": "0.2.0", "sistemas": ALL,
                                                             "sha256": hashlib.sha256(hexp.read_bytes()).hexdigest()}]}))
    return d


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_boards_lista_as_placas_sem_usar_o_arduino(capsys):
    code, out, _ = run(capsys, "--json", "boards")
    r = json.loads(out)
    assert code == 0 and {b["board"] for b in r["boards"]} == set(B.board_names())


def test_placa_desconhecida_e_erro_de_uso(capsys):
    code, out, _ = run(capsys, "--simulate", "--json", "--board", "zx_spectrum", "board")
    assert code == 64 and json.loads(out)["error"]["kind"] == "unknown_board"


def test_firmware_que_serve_so_grava_o_perfil(capsys, images):
    code, out, err = run(capsys, "--simulate", "--json", "--firmware-dir", str(images), "--board", "16_bits", "board")
    r = json.loads(out)
    assert code == 0 and r["action"] == "set_profile" and r["firmware"] == "0.2.0" and r["voltage_select"] is True
    assert "perfil" in err or "profile" in err


def test_firmware_antigo_sem_confirmacao_e_recusado_e_nao_grava(capsys, images, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    code, out, _ = run(capsys, "--simulate", "--json", "--firmware-dir", str(images), "--board", "16_bits", "board")
    assert code == 4 and json.loads(out)["error"]["kind"] == "refused" and common.SIM_FLASHED is False


def test_firmware_antigo_com_auto_flash_grava_e_depois_ajusta_o_perfil(capsys, images, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    code, out, err = run(capsys, "--simulate", "--json", "--auto-flash", "--firmware-dir", str(images), "--board", "16_bits", "board")
    r = json.loads(out)
    assert code == 0 and r["action"] == "flash" and r["firmware"] == "0.2.0" and r["voltage_select"] is True and common.SIM_FLASHED
    assert "0.2.0" in err


def test_pergunta_no_terminal_e_a_resposta_nao_cancela(capsys, images, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    code, out, err = run(capsys, "--simulate", "--firmware-dir", str(images), "--board", "16_bits", "board")
    assert code == 4 and common.SIM_FLASHED is False


def test_pergunta_no_terminal_e_a_resposta_sim_grava(capsys, images, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    asked = []
    monkeypatch.setattr("builtins.input", lambda prompt="": asked.append(prompt) or "s")
    code, out, err = run(capsys, "--simulate", "--lang", "pt-BR", "--firmware-dir", str(images), "--board", "16_bits", "board")
    assert code == 0 and common.SIM_FLASHED and len(asked) == 1 and "substituído" in asked[0]


def test_sem_imagem_conhecida_nao_grava_e_explica(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    code, out, _ = run(capsys, "--simulate", "--json", "--auto-flash", "--firmware-dir", str(tmp_path), "--board", "16_bits", "board")
    e = json.loads(out)["error"]
    assert code == 1 and e["kind"] == "board_unsupported" and common.SIM_FLASHED is False


def test_board_vale_para_qualquer_comando_de_cartucho(capsys, images):
    code, out, _ = run(capsys, "--simulate", "--json", "--firmware-dir", str(images), "--board", "snes", "detect", "-s", "mock")
    assert code == 0 and json.loads(out)["ok"]


def test_sem_resposta_do_arduino_grava_e_o_caminho_real_usa_o_avrdude(capsys, images, tmp_path, monkeypatch):
    """Sem simulador: a porta não responde (`no_response`), o plano manda gravar, o avrdude falso é chamado e o INFO depois responde."""
    from oscr_host.cli import cmd_firmware
    from oscr_host.cli.errors import CliError

    exe = tmp_path / "avrdude"
    exe.write_text(f"#!{sys.executable}\nimport sys\nsys.stderr.write('Writing | ### | 100%\\\\r\\\\navrdude done.\\\\n')\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    calls = {"open": 0}
    from oscr_host import sim
    from oscr_host.client import Client

    def fake_open(args):
        calls["open"] += 1
        if calls["open"] <= 1:                                    # antes da gravação: nada responde
            raise CliError("no_response", "sem resposta", 3)
        dev = sim.MockDevice(systems=sum(1 << i for i in ALL))     # depois: firmware novo
        t, _d, _s, _th = sim.start(dev)
        c = Client(t, timeout=0.5, long_timeout=5.0)
        return c, t, c.info()

    monkeypatch.setenv("AVRDUDE", str(exe))
    monkeypatch.setattr(common, "_open", fake_open)
    monkeypatch.setattr(cmd_firmware, "_info_after", lambda args, timeout=12.0: {"firmware": "0.2.0", "proto": 1})
    code, out, err = run(capsys, "--json", "-p", "/dev/ttyOSCRteste", "--auto-flash", "--firmware-dir", str(images), "--board", "snes", "board")
    r = json.loads(out)
    assert code == 0 and r["action"] == "flash" and calls["open"] == 2, (out, err)
