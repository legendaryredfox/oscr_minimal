#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Costura GND: vias de 0,6/0,3 numa grade (passo dado, mm) onde há folga de 0,5 mm de qualquer cobre de outra net
e que caiam dentro do preenchimento de GND das duas camadas. Evita legendas do silkscreen. Remove antes as vias de GND soltas que este script pôs
. Antes de rodar, apague as vias de GND da rodada anterior. Uso (Python do venv do KiCad MCP): stitch.py placa.kicad_pcb [passo]"""
import sys, pcbnew
mm = pcbnew.FromMM
path = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
b = pcbnew.LoadBoard(path); gnd = b.FindNet("/GND").GetNetCode()
items = list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = [v / 1e6 for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
zones = [z for z in b.Zones() if z.GetNetCode() == gnd]
def free(pt):
    for it in items:
        same = it.GetNetCode() == gnd
        if same and it.GetClass() != "PCB_VIA" and not (it.GetClass() == "PAD" and it.GetDrillSize().x > 0): continue
        if it.HitTest(pt, mm(0.3 + (1.0 if same else 0.5))): return False
    for f in b.GetFootprints():          # nada de via sob o corpo de peça com furo próximo: só pads contam
        pass
    return True
silk = []        # nada de via sob textos e campos do silkscreen (aviso silk_over_copper)
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS): silk.append(d.GetBoundingBox())
for f in b.GetFootprints():
    for fld in f.GetFields():
        if fld.IsVisible() and fld.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS): silk.append(fld.GetBoundingBox())
for k in silk: k.Inflate(mm(0.8))
def in_zone(pt):
    return all(z.HitTestFilledArea(z.GetLayer(), pt, mm(0.31)) for z in zones)
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd: b.RemoveNative(t)
items = list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]
n = 0
y = y0 + 3
while y < y1 - 3:
    x = x0 + 3
    while x < x1 - 3:
        pt = pcbnew.VECTOR2I(mm(x), mm(y))
        if free(pt) and in_zone(pt) and not any(k.Contains(pt) for k in silk):
            v = pcbnew.PCB_VIA(b); v.SetPosition(pt); v.SetNet(b.FindNet("/GND"))
            v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); b.Add(v); n += 1
        x += step
    y += step
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path, b)
print("vias de costura", n)
