#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Alonga a placa Famicom + NES em 5 mm para a esquerda e desloca o slot NES (e o que acompanha: capacitor do VCC, furos de canto
da esquerda, legenda) 5 mm para a esquerda, para dar folga ao soquete do Si5351 (U1) entre o slot e o header do Mega (D124).
Apaga trilhas, vias e zonas (a placa é roteada de novo depois: tools/boards/famicom_nes/reroute.sh).
Uso (Python do venv do KiCad MCP): widen.py boards/famicom_nes/hardware-v1.1/dumper.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
D = 5.0
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
def shift(ref):
    f = b.FindFootprintByReference(ref); p = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(p.x - mm(D), p.y))
for ref in ("NES1", "C3", "MH1", "MH3"): shift(ref)
X0, Y0, X1, Y1 = 6.0, 38.0, 123.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetText().startswith("NES: v v"):
        p = d.GetPosition(); d.SetPosition(pcbnew.VECTOR2I(p.x - mm(D), p.y))
pcbnew.SaveBoard(path, b); print("ok")
