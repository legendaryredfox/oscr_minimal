#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da placa gb_gba (slot GBA; GB e GBC por adaptador) a partir da cópia da 16_and_8_bits: limpa trilhas, vias e zonas,
remove os outros slots, Si5351, PIC, R2, C2 a C6 e os furos M2, move o slot GBA para a direita do Mega (boca para +x),
refaz contorno e reposiciona peças e textos. Uso (Python do venv do KiCad MCP): place.py boards/gb_gba/hardware-v1.1/dumper.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
for ref in ("SNES1", "NES1", "FC1", "MD1", "U1", "U2", "R2", "C2", "C3", "C4", "C5", "C6", "MH5", "MH6"):
    b.RemoveNative(b.FindFootprintByReference(ref))
X0, Y0, X1, Y1 = 16.0, 50.0, 154.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
def mv(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
mv("MH1", 19, 53); mv("MH2", 118.5, 53); mv("MH3", 19, 114); mv("MH4", 115, 114.5)  # MH4: afastado da trilha do A9 e da via de GND (feito à mão na placa, D94)
mv("GBA1", 134, 84.3, 0)
# NPTH do Mega em (86, 75,4) e (86, 103,4): nada por perto
mv("C1", 26, 64); mv("C7", 50, 80); mv("U3", 64, 80); mv("C8", 76, 80); mv("C9", 100, 80)
mv("R1", 60, 90, 0); mv("D1", 80, 90, 0)
keep = {"GBA: ETIQUETA P/ CIMA": (143.0, 51.6), "ENTRA PELA DIREITA": (143.0, 53.2),
        "UM CARTUCHO POR VEZ": (52.0, 96.0),
        "SNES / NES / FAMICOM / MEGA DRIVE   v1.0   2026-11-02": (52.0, 101.5),
        "Projeto original: github.com/sanni/cartreader": (62.0, 66.0),
        "Adaptado por: github.com/legendaryredfox/oscr_minimal": (62.0, 68.5),
        "Baseado no Open Source Cartridge Reader de sanni — CC BY 4.0": (62.0, 71.0)}
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t in keep:
        if t.startswith("SNES /"): d.SetText("GB / GBC / GBA   v1.0   2026-11-06")
        d.SetPosition(V(*keep[t]))
    else: b.RemoveNative(d)
b.Save(path); print("ok")
