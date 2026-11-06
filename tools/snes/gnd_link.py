#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Liga o GND2 do Mega (cluster isolado entre a fileira de baixo e o slot) ao ponto de teste GND (TP2) por uma trilha
em L na camada dada, passando entre a fileira de pinos e a fileira de pontos de teste.
Uso (Python do venv do KiCad MCP): gnd_link.py placa.kicad_pcb [F.Cu|B.Cu] [y_mm]"""
import sys, pcbnew
mm = pcbnew.FromMM
path = sys.argv[1]; layer = pcbnew.B_Cu if len(sys.argv) > 2 and sys.argv[2] == "B.Cu" else pcbnew.F_Cu
y = float(sys.argv[3]) if len(sys.argv) > 3 else 110.9
b = pcbnew.LoadBoard(path); g = b.FindNet("/GND")
pad = [p for p in b.FindFootprintByReference("A1").Pads() if p.GetNumber() == "GND2"][0]
tp = b.FindFootprintByReference("TP2").Pads()[0]
a = pad.GetPosition(); t = tp.GetPosition()
pts = [(a.x, a.y), (a.x, mm(y)), (t.x, mm(y)), (t.x, t.y)]
for p, q in zip(pts, pts[1:]):
    tr = pcbnew.PCB_TRACK(b); tr.SetStart(pcbnew.VECTOR2I(*p)); tr.SetEnd(pcbnew.VECTOR2I(*q))
    tr.SetLayer(layer); tr.SetWidth(mm(0.3)); tr.SetNet(g); b.Add(tr)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path, b); print("ok")
