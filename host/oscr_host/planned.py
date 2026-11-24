# SPDX-License-Identifier: GPL-3.0-or-later
"""Outros cartuchos que o OSCR lê e que este projeto ainda não suporta (marcadores de lugar).

Sem id no protocolo, sem hardware, sem firmware. A mesma lista está em gui/shared/.../PlannedSystems.kt
(host/tests/test_planned.py confere). Nomes próprios: não são traduzidos."""
from __future__ import annotations

PLANNED: tuple[tuple[str, str], ...] = (
    ("astrocade", "Bally Astrocade"),
    ("loopy", "Casio Loopy"), ("pv1000", "Casio PV-1000"), ("channelf", "Fairchild Channel F"),
    ("c64", "Commodore 64"), ("vic20", "Commodore VIC-20"),
    ("cps3", "Capcom CPS3"), ("intellivision", "Intellivision"), ("leapster", "Leapster"),
    ("jammer", "Little Jammer"), ("jammerpro", "Little Jammer Pro"),
    ("vb", "Virtual Boy"), ("pokemini", "Pokémon Mini"),
    ("odyssey2", "Odyssey 2"), ("pce", "PC Engine / TurboGrafx-16"), ("pcw", "Pocket Challenge W"),
    ("satellaview", "Satellaview (BS-X)"), ("sfm", "SF Memory"),
    ("supercan", "Super A'can"),
    ("ti99", "TI-99/4A"), ("trs80", "TRS-80"),
    ("vsmile", "V.Smile"), ("ws", "WonderSwan"), ("msx", "MSX"),
    ("gbsmart", "Game Boy Smart Card"), ("gbmem", "Game Boy Memory"),
)

# Adaptadores de 3,3 V da comunidade (P-16, H-4): não podem ir num slot de 5 V. Conferido contra a tabela de docs/historico/pesquisa-comunidade.md por tools/check_adaptadores.py.
NEEDS_3V3: frozenset[str] = frozenset({"leapster", "jammerpro", "pokemini", "vsmile"})
