#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pontos de teste TP1 a TP6 a 2,54 mm (tira de pinos 1x6 padrão): rótulo (valor do footprint) na vertical, acima de cada pino,
e sem a área de proteção do footprint TestPoint (maior que 2,54 mm; os pads ficam a 0,54 mm um do outro).
Rode num processo novo, depois de place.py (os campos só funcionam numa placa recém-carregada).
Uso (Python do venv do KiCad MCP): tp_header.py placa.kicad_pcb [y_rotulo_mm=108.6]"""
import sys, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); y = float(sys.argv[2]) if len(sys.argv) > 2 else 108.6
for i in range(1, 7):
    f = b.FindFootprintByReference("TP%d" % i)
    if f is None: continue
    x = f.GetX()
    for fld in f.GetFields():
        if fld.GetName() == "Value":
            fld.SetTextAngle(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T)); fld.SetPosition(pcbnew.VECTOR2I(x, mm(y)))
    for g in list(f.GraphicalItems()):
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd): f.RemoveNative(g)
pcbnew.SaveBoard(sys.argv[1], b); print("ok")
