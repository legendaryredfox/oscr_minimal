# SPDX-License-Identifier: GPL-3.0-or-later
"""Outros cartuchos que o OSCR lê e que este projeto ainda não suporta (marcadores de lugar).

Sem id no protocolo, sem hardware, sem firmware. A mesma lista está em gui/shared/.../PlannedSystems.kt
(host/tests/test_planned.py confere). Nomes próprios: não são traduzidos."""
from __future__ import annotations

PLANNED: tuple[tuple[str, str], ...] = (
    ("a2600", "Atari 2600"), ("a5200", "Atari 5200"), ("a7800", "Atari 7800"), ("a8bit", "Atari 8-bit"),
    ("jaguar", "Atari Jaguar"), ("lynx", "Atari Lynx"), ("astrocade", "Bally Astrocade"),
    ("loopy", "Casio Loopy"), ("pv1000", "Casio PV-1000"), ("channelf", "Fairchild Channel F"),
    ("coleco", "ColecoVision"), ("c64", "Commodore 64"), ("vic20", "Commodore VIC-20"),
    ("cps3", "Capcom CPS3"), ("intellivision", "Intellivision"), ("leapster", "Leapster"),
    ("jammer", "Little Jammer"), ("jammerpro", "Little Jammer Pro"),
    ("vb", "Virtual Boy"), ("pokemini", "Pokémon Mini"), ("ngp", "Neo Geo Pocket"),
    ("odyssey2", "Odyssey 2"), ("pce", "PC Engine / TurboGrafx-16"), ("pcw", "Pocket Challenge W"),
    ("rca2", "RCA Studio II"), ("satellaview", "Satellaview (BS-X)"), ("sfm", "SF Memory"),
    ("supercan", "Super A'can"), ("supervision", "Watara Supervision"),
    ("ti99", "TI-99/4A"), ("pyuuta", "Tomy Pyuuta"), ("trs80", "TRS-80"), ("vectrex", "Vectrex"),
    ("vsmile", "V.Smile"), ("ws", "WonderSwan"), ("msx", "MSX"), ("arcadia", "Arcadia 2001"),
    ("gbsmart", "Game Boy Smart Card"), ("gbmem", "Game Boy Memory"),
)
