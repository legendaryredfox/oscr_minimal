#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera o catálogo de mensagens da CLI Kotlin a partir do da CLI Python (D133): uma só fonte, `host/oscr_host/cli/messages.py`.
Saída: gui/shared/src/jvmMain/resources/oscr/cli-messages.tsv (uma linha por chave: chave, pt-BR, en, ru, zh-CN, separados por TAB).
Uso, da raiz do repositório:  python3 tools/gen_cli_messages.py [--check]"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))
from oscr_host.cli.messages import CATALOG, LANGS  # noqa: E402

OUT = ROOT / "gui" / "shared" / "src" / "jvmMain" / "resources" / "oscr" / "cli-messages.tsv"


def render() -> str:
    lines = ["# Gerado por tools/gen_cli_messages.py a partir de host/oscr_host/cli/messages.py. Não edite à mão.",
             "# chave\t" + "\t".join(LANGS)]
    for key, row in CATALOG.items():
        if key.startswith("help."):
            continue                      # o --help da Python não vai para a Kotlin (tem o HELP dela)
        cells = [row[l] for l in LANGS]
        assert not any("\t" in c or "\n" in c for c in cells), key
        lines.append(key + "\t" + "\t".join(cells))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = render()
    if "--check" in sys.argv:
        sys.exit(0 if OUT.is_file() and OUT.read_text(encoding="utf-8") == text else 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print("escrito", OUT.relative_to(ROOT), len(CATALOG), "mensagens")
