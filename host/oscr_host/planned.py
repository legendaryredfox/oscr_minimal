# SPDX-License-Identifier: GPL-3.0-or-later
"""Outros cartuchos que o OSCR lê e que este projeto ainda não suporta (marcadores de lugar).

Sem id no protocolo, sem hardware, sem firmware. A mesma lista está em gui/shared/.../PlannedSystems.kt
(host/tests/test_planned.py confere). Nomes próprios: não são traduzidos."""
from __future__ import annotations

PLANNED: tuple[tuple[str, str], ...] = (
    ("loopy", "Casio Loopy"), 
    ("c64", "Commodore 64"), ("vic20", "Commodore VIC-20"),
    ("cps3", "Capcom CPS3"), ("intellivision", "Intellivision"), ("leapster", "Leapster"),
    ("jammer", "Little Jammer"), ("jammerpro", "Little Jammer Pro"),
    ("vb", "Virtual Boy"),
    ("pce", "PC Engine / TurboGrafx-16"), ("pcw", "Pocket Challenge W"),
    ("satellaview", "Satellaview (BS-X)"), ("sfm", "SF Memory"),
    ("supercan", "Super A'can"),
    ("ti99", "TI-99/4A"),
    ("ws", "WonderSwan"),
    ("gbmem", "Game Boy Memory"),
)

# Adaptadores de 3,3 V da comunidade (P-16, H-4): não podem ir num slot de 5 V. Conferido contra a tabela de docs/historico/pesquisa-comunidade.md por tools/check_adaptadores.py.
NEEDS_3V3: frozenset[str] = frozenset({"leapster", "jammerpro"})
