#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""megadrive_sms v1.1 (D138): estende a placa v1.0 para baixo (de 83,1 para 123,1 mm), onde entram o seletor 3,3 V/5 V e as redes de
resistores em série, e muda os furos de pé de baixo de lugar. Antes de tools/troca/pcb_block.py.
Uso (python do sistema, com pcbnew): /usr/bin/python3 -I tools/boards/megadrive_sms/v11_board.py boards/megadrive_sms/hardware-v1.1"""
import sys
import pcbnew
from pathlib import Path
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = str(Path(sys.argv[1]) / "dumper.kicad_pcb")
b = pcbnew.LoadBoard(path)
X0, Y0, X1, Y1 = 16.0, 52.0, 123.0, 175.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
for ref, (x, y) in (("MH5", (19.0, 172.0)), ("MH6", (120.0, 172.0))):
    b.FindFootprintByReference(ref).SetPosition(V(x, y))
pcbnew.SaveBoard(path, b)
print("ok: placa 107,1 x 123,1 mm")
