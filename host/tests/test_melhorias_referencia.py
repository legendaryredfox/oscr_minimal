# SPDX-License-Identifier: GPL-3.0-or-later
"""Melhorias vindas da análise dos repositórios de referência (D160, docs/historico/pesquisa-repos-referencia-2026-11-13.md)."""


def test_sound_um_bel_se_deu_certo_e_tres_se_falhou(capsys):
    from oscr_host import cli
    assert cli.main(["--simulate", "--json", "--sound", "detect", "-s", "mock"]) == 0
    assert capsys.readouterr().err.count("\a") == 1
    assert cli.main(["--simulate", "--json", "--sound", "detect", "-s", "snes"]) != 0       # o simulador só tem cartucho MOCK
    assert capsys.readouterr().err.count("\a") == 3
    assert cli.main(["--simulate", "--json", "detect", "-s", "mock"]) == 0
    assert "\a" not in capsys.readouterr().err                                              # sem --sound, silêncio
