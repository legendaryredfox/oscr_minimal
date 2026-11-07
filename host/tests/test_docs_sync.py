# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere que a lista de mappers do firmware aparece na CLI, na GUI (4 idiomas) e na documentação.

A lista já ficou desatualizada em um lugar ou outro (a ajuda da GUI chegou a dizer que só o SNES tem save). A fonte da verdade é a linha
`known` de nesCheckRom (firmware/oscr/src/dumper/Dumper.cpp); qualquer mapper novo precisa entrar em todos os textos abaixo.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def firmware_mappers() -> set[int]:
    src = (ROOT / "firmware/oscr/src/dumper/Dumper.cpp").read_text()
    m = re.search(r"bool known = (.*?);", src, re.S)
    assert m, "linha 'known' não encontrada em Dumper.cpp (nesCheckRom)"
    return {int(n) for n in re.findall(r"m == (\d+)", m.group(1))}


def has_all(text: str, nums: set[int]) -> list[int]:
    return sorted(n for n in nums if not re.search(rf"(?<![0-9]){n}(?![0-9])", text))


def test_lista_do_firmware_nao_esta_vazia():
    assert {0, 1, 2, 3, 4, 7} <= firmware_mappers()


def test_cli_lista_todos_os_mappers():
    src = (ROOT / "host/oscr_host/cli/parser.py").read_text()
    line = next(l for l in src.splitlines() if "NES/Famicom: número do mapper" in l)
    assert has_all(line, firmware_mappers()) == []


def test_gui_lista_todos_os_mappers_nos_quatro_idiomas():
    src = (ROOT / "gui/shared/src/commonMain/kotlin/oscr/I18n.kt").read_text()
    for key in ("NES_HINT", "HELP_USE_6"):
        lines = [l for l in src.splitlines() if f"S.{key} to" in l]
        assert len(lines) == 4, key
        for l in lines:
            assert has_all(l, firmware_mappers() - {0}) == [], (key, l[:80])


def test_docs_listam_todos_os_mappers():
    nums = firmware_mappers()
    uso = (ROOT / "docs/uso.md").read_text()
    row = next(l for l in uso.splitlines() if l.startswith("| NES |"))
    assert has_all(row, nums) == []
    proto = (ROOT / "docs/protocolo.md").read_text()
    line = next(l for l in proto.splitlines() if "Mappers aceitos:" in l)
    assert has_all(line, nums) == []
