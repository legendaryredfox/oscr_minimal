#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Põe uma via de GND ao lado de cada pad GND dado (X,Y em mm), no primeiro ponto livre de um anel de 0,9 a 1,5 mm.
Uso (Python do venv do KiCad MCP): gnd_vias.py placa.kicad_pcb X,Y [X,Y ...]"""
import sys, math, pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); gnd = b.FindNet("/GND")
def free(pt, r, net):
    for it in list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]:
        if it.GetNetCode() == net and it.GetNetCode() != 0: continue
        if it.HitTest(pt, mm(r + 0.3)): return False
    return True
for arg in sys.argv[2:]:
    x, y = map(float, arg.split(","))
    done = False
    for d in (0.9, 1.0, 1.2, 1.5, 2.0, 2.5):
        for k in range(24):
            a = 2 * math.pi * k / 24
            pt = pcbnew.VECTOR2I(mm(x + d * math.cos(a)), mm(y + d * math.sin(a)))
            if free(pt, 0.3, gnd.GetNetCode()):
                v = pcbnew.PCB_VIA(b); v.SetPosition(pt); v.SetNet(gnd)
                v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); b.Add(v); done = True; print("via", arg, d); break
        if done: break
    if not done: print("sem lugar", arg)
b.Save(sys.argv[1])
