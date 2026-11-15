#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a lista de adaptadores da comunidade (H-4, P-16) contra o que o programa diz.

Fonte: a tabela da seção 3 de docs/historico/pesquisa-comunidade.md (id, console, tensão, link). Confere que
1. todo marcador de lugar (host/oscr_host/planned.py) tem linha na tabela;
2. os ids de 3,3 V da tabela são exatamente host/oscr_host/planned.py:NEEDS_3V3;
3. a GUI (PlannedSystems.kt, `needs3v3`) marca os mesmos;
4. nenhum adaptador de 3,3 V tem como destino um slot de 5 V nas placas: a tabela só diz o adaptador, então isto só lista os ids para a pessoa conferir.
Sai com 1 se 1 a 3 falharem. Não baixa nada: a tabela não traz pinos, então a conferência pino a pino com `boards/*/docs/pinmap.md` continua manual (P-16)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "host"))
from oscr_host.planned import NEEDS_3V3, PLANNED  # noqa: E402

DOC = ROOT / "docs/historico/pesquisa-comunidade.md"
KT = ROOT / "gui/shared/src/commonMain/kotlin/oscr/PlannedSystems.kt"
ROW = re.compile(r"^\| `([a-z0-9]+)` \| ([^|]+) \| ([^|]+) \| (.*) \|$")


def table() -> dict[str, tuple[str, str]]:
    rows = {}
    in3 = False
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 3."):
            in3 = True
        elif line.startswith("## 4."):
            break
        if in3 and (m := ROW.match(line)):
            rows[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return rows


def check() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    rows = table()
    for key, _ in PLANNED:
        if key not in rows:
            errors.append(f"{key}: sem linha na tabela de adaptadores")
    doc3v3 = {k for k, (_, volt) in rows.items() if "3,3" in volt}
    py3v3 = set(NEEDS_3V3)
    if doc3v3 & {k for k, _ in PLANNED} != py3v3:
        errors.append(f"3,3 V: tabela {sorted(doc3v3 & {k for k, _ in PLANNED})} x planned.py {sorted(py3v3)}")
    kt3v3 = set(re.findall(r'PlannedSystem\("([^"]+)", "[^"]+", true\)', KT.read_text(encoding="utf-8")))
    if kt3v3 != py3v3:
        errors.append(f"3,3 V: PlannedSystems.kt {sorted(kt3v3)} x planned.py {sorted(py3v3)}")
    notes = [f"{k} ({rows[k][0]}): adaptador de 3,3 V, conferir o slot pino a pino" for k in sorted(doc3v3)]
    return errors, notes


if __name__ == "__main__":
    errs, notes = check()
    for n in notes:
        print("aviso:", n)
    for e in errs:
        print("ERRO:", e)
    print("ok" if not errs else f"{len(errs)} problema(s)")
    sys.exit(1 if errs else 0)
