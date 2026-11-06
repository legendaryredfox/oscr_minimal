#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da placa só-SNES a partir da cópia da 16_bits: limpa trilhas e vias, remove MD1, C3, C5, C6 e TP3,
refaz contorno e zonas (107 x 65 mm) e reposiciona peças e textos. O slot SNES não sai do lugar.
Uso (Python do venv do KiCad MCP): python place.py boards/snes/hardware/dumper.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)          # o GND é roteado como trilha e as zonas voltam depois (add_zones.py, D93)
for ref in ("MD1", "C3", "C5", "C6", "TP3"):
    f = b.FindFootprintByReference(ref)
    if f is not None: b.RemoveNative(f)                 # pode rodar de novo sobre a própria placa
X0, Y0, X1, Y1 = 16.0, 52.0, 123.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
def mv(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
mv("MH1", 19, 55); mv("MH2", 120, 55); mv("MH3", 19, 114); mv("MH4", 120, 114)
mv("C1", 26, 61); mv("R1", 24, 68); mv("R2", 24, 73); mv("D1", 42, 66)
mv("U1", 50, 74); mv("U2", 84, 64); mv("C4", 97, 68); mv("C2", 92.5, 98)
tps = sorted([b.FindFootprintByReference("TP%d" % i) for i in (1, 2, 4, 5, 6)], key=lambda f: f.GetPosition().x)
for k, f in enumerate(tps): f.SetPosition(V(24.0 + 2.54 * k, 113))   # 2,54 mm: tira de pinos 1x5 padrão; rótulos e áreas de proteção em tools/megadrive/tp_header.py
keep = {"SNES: v v ETIQUETA v v": (73.0, 97.0), "UM CARTUCHO POR VEZ": (46.0, 102.0),
        "SNES / MEGA DRIVE   v. 1.2   2026-11-04": (42.0, 106.0), "SNES   v1.0   2026-11-06": (42.0, 106.0),
        "Si5351  pino 1 = VIN": (60.0, 77.5), "PIC EM SOQUETE": (84.0, 76.0)}
back = {"Adaptado por": 96, "Baseado no": 99, "Projeto original": 102}
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t in keep:
        if t.startswith("SNES /"): d.SetText("SNES   v1.0   2026-11-06")
        d.SetPosition(V(*keep[t]))
    elif d.GetLayer() == pcbnew.B_SilkS:
        for k, y in back.items():
            if t.startswith(k): d.SetPosition(V(60.0, y))
    else: b.RemoveNative(d)
b.Save(path); print("ok")
