#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v. 1.2 final (D108), parte 4: acabamento depois do Freerouting: textos e rotulos, pads de GND sem alivio termico onde o DRC
reclama (starved_thermal), novo preenchimento (sem costura: o stitch.py removia vias de GND do Freerouting e as duas camadas ficavam sem ligacao). Uso (Python do venv do KiCad MCP): python v12b_finish.py boards/16_bits/hardware"""
import subprocess, sys
from pathlib import Path
import pcbnew
HW = Path(sys.argv[1]); PCB = str(HW / "dumper.kicad_pcb")
HERE = Path(__file__).resolve().parent
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(PCB)
for r in ("R16", "R17", "R18"):
    b.FindFootprintByReference(r).Reference().SetVisible(False)
b.FindFootprintByReference("U2").Reference().SetPosition(V(105.8, 56.6))
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT":
        continue
    t = d.GetText()
    if t == "PIC EM SOQUETE":
        d.SetPosition(V(99.6, 52.2)); d.SetTextAngleDegrees(90)
    elif t.startswith("SÉRIE"):
        d.SetPosition(V(62.0, 45.4))
    elif t.startswith("TVS 5V"):
        d.SetPosition(V(62.0, 43.6))
pcbnew.SaveBoard(PCB, b)
subprocess.run([sys.executable, str(HERE / "solid_pad.py"), PCB, "A1:GND6", "C2:2", "D6:2"], check=True)
b = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("ok")
