#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v1.3 (D128): acabamento do silkscreen depois de tools/troca/finish.py: versão "v. 1.3", textos do aviso menores
(não encostam em "UM CARTUCHO POR VEZ").  Uso (python do venv do KiCad MCP): python retoque_v13.py boards/16_bits/hardware-v1.3"""
import re, sys
from pathlib import Path
import pcbnew
mm = pcbnew.FromMM
p = str(Path(sys.argv[1]) / "dumper.kicad_pcb"); b = pcbnew.LoadBoard(p)
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t.startswith("SNES / MEGA DRIVE"):
        d.SetText(re.sub(r"v\. \d+\.\d+", "v. 1.3", t))
    if t in ("SÓ TROQUE O CARTUCHO COM", "O LED AMARELO ACESO"):
        d.SetTextSize(pcbnew.VECTOR2I(mm(1.8), mm(1.8))); d.SetTextThickness(mm(0.2))
    if t == "SÓ TROQUE O CARTUCHO COM":
        d.SetPosition(pcbnew.VECTOR2I(d.GetPosition().x, mm(101.8)))
    if t == "O LED AMARELO ACESO":
        d.SetPosition(pcbnew.VECTOR2I(d.GetPosition().x, mm(104.0)))
pcbnew.SaveBoard(p, b)
print("ok")
