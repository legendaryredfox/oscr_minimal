#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Roteia uma net que o Freerouting deixou de fora, com o roteador A* de tools/pcb_v12 (grade de 0,1 mm, duas camadas, vias).
Uso (Python do venv do KiCad MCP): route_net.py entrada.kicad_pcb saida.kicad_pcb NET REF_A PAD_A REF_B PAD_B
Ex.: route_net.py b.kicad_pcb b.kicad_pcb /D9 A1 D9 GBA1 4"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pcb_v12"))
from pcbops import *
src, dst, net, ra, pa_, rb, pb_ = sys.argv[1:8]
g = Grid(src); b = g.b
pa = [p for p in b.FindFootprintByReference(ra).Pads() if p.GetNumber() == pa_][0]
pb = [p for p in b.FindFootprintByReference(rb).Pads() if p.GetNumber() == pb_][0]
sx, sy = pa.GetPosition().x / MM, pa.GetPosition().y / MM
gx, gy = pb.GetPosition().x / MM, pb.GetPosition().y / MM
trk, via, _, _ = g.free_maps(net)
goal = net_mask(g, net)
i, j = g.cell(sx, sy)
for L in range(2): goal[L][j - 12:j + 13, i - 12:i + 13] = False
best = None
for l0 in (0, 1):
    p = route_mask(g, (sx, sy, l0), goal, trk, via, via_cost=12.0)
    print("camada", l0, None if p is None else round(len(p) * RES, 1))
    if p and (best is None or len(p) < len(best)): best = p
if best is None: sys.exit("sem caminho")
print("trilhas/vias", add_path(b, g, net, best, p_start=(sx, sy), p_end=(gx, gy)))
pcbnew.SaveBoard(dst, b)
