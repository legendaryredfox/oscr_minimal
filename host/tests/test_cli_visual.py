"""Camada visual da CLI (cores, arte ASCII, barra): só em terminal ou com --color always; --json e saída redirecionada continuam texto puro."""
import json
import re

import pytest

from oscr_host.cli import main, ui

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


@pytest.fixture(autouse=True)
def _reset_mode():
    yield
    ui.set_mode("auto")


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_saida_redirecionada_nao_tem_enfeite(capsys, monkeypatch):
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    code, out, _ = run(capsys, "--simulate", "detect", "-s", "mock")
    assert code == 0 and not ANSI.search(out) and "mock: cartucho detectado" in out


def test_color_always_desenha_o_cartucho(capsys):
    code, out, _ = run(capsys, "--color", "always", "--simulate", "detect", "-s", "mock")
    assert code == 0 and ANSI.search(out)
    plain = ANSI.sub("", out)
    assert "S N E S" in plain and "cartucho detectado" in plain and "32768 bytes" in plain


def test_json_nunca_tem_enfeite(capsys):
    code, out, _ = run(capsys, "--color", "always", "--simulate", "--json", "detect", "-s", "mock")
    assert code == 0 and not ANSI.search(out) and json.loads(out)["ok"] is True


def test_no_color_vence_no_auto(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert ui.color_on() is False
    ui.set_mode("always")
    assert ui.color_on() is True            # --color always é explícito


def test_color_never(capsys):
    code, out, _ = run(capsys, "--color", "never", "--simulate", "detect", "-s", "mock")
    assert not ANSI.search(out)


@pytest.mark.parametrize("kind", range(1, 7))
def test_arte_alinhada(kind):
    ui.set_mode("never")
    rows = ui.cartridge(kind)
    assert len({len(r) for r in rows}) == 1 and len(rows) >= 6


def test_logo_tem_cinco_linhas_do_mesmo_tamanho():
    rows = ui.logo()
    assert len(rows) == 5 and len({len(r) for r in rows}) == 1


def test_barra_e_fallback_ascii():
    ui.set_mode("never")
    assert ui.bar(0.5, 10) in ("[█████░░░░░]", "[#####-----]")
    assert ui.bar(0, 4).count("[") == 1 and ui.bar(2.0, 4) == ui.bar(1.0, 4)


def test_decorate_realca_sem_mudar_o_texto():
    ui.set_mode("always")
    line = "ROM gravada: NES Maker  CRC32 DEADBEEF  OK"
    assert ANSI.sub("", ui.decorate(line)).endswith(line)
    ui.set_mode("never")
    assert ui.decorate(line) == line


def test_erro_colorido_em_stderr(capsys):
    ui.set_mode("always")
    code, _, err = run(capsys, "--color", "always", "--simulate", "save-write", "-s", "mock", "-i", "/nao/existe", "--yes")
    assert code == 1 and "erro:" in ANSI.sub("", err)
