#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da placa só-Mega-Drive a partir da cópia da 16_bits.
Remove trilhas, vias e as peças de SNES/PIC/Si5351, move o slot MD para dentro da área do Mega,
redesenha o contorno e as zonas, reposiciona peças e textos. Uso (Python do venv do KiCad MCP):
  python place.py boards/megadrive/hardware/dumper.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = sys.argv[1]
b = pcbnew.LoadBoard(path)

for t in list(b.GetTracks()): b.RemoveNative(t)
for ref in ("SNES1", "U1", "U2", "R2", "C2", "C4"):
    b.RemoveNative(b.FindFootprintByReference(ref))

X0, Y0, X1, Y1 = 16.0, 52.0, 123.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
for z in b.Zones():
    o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
    for p in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)): o.Append(mm(p[0]), mm(p[1]))

def mv(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
mv("MD1", 64.0, 84.3)
mv("MH1", 19, 55); mv("MH2", 120, 55); mv("MH3", 19, 114); mv("MH4", 120, 114)
mv("C1", 26, 61); mv("R1", 24, 69); mv("D1", 42, 69)
mv("C6", 29.7, 75.5); mv("C3", 64, 75.5); mv("C5", 100.8, 75.5)
tps = sorted([b.FindFootprintByReference("TP%d" % i) for i in range(1, 7)], key=lambda f: f.GetPosition().x)
for k, f in enumerate(tps): f.SetPosition(V(26 + 5.5 * k, 113))

keep = {"MEGA DRIVE: v v ETIQUETA v v": (64.0, 91.9), "UM CARTUCHO POR VEZ": (64.0, 98.5),
        "SNES / MEGA DRIVE   v. 1.2   2026-11-04": (64.0, 103.5)}
back = {"Adaptado por": 69.0, "Baseado no": 72.0, "Projeto original": 75.0}
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t in keep:
        if t.startswith("SNES"): d.SetText("MEGA DRIVE   v1.0   2026-11-06")
        d.SetPosition(V(*keep[t]))
    elif d.GetLayer() == pcbnew.B_SilkS:
        for k, y in back.items():
            if t.startswith(k): d.SetPosition(V(70.0, y))
    else: b.RemoveNative(d)
b.Save(path)
print("ok")
