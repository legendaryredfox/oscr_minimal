#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Para cada fragmento pequeno do preenchimento de GND (menos de 500 mm2), põe uma via de GND dentro dele, num ponto livre
(0,5 mm de folga de outra net, 1 mm de furos) que também caia no preenchimento da outra camada. Depois preenche de novo.
Pula fragmentos que já têm via. Uso (Python do venv do KiCad MCP): frag_vias.py placa.kicad_pcb [folga_mm=0.5] [passo_mm=0.4]"""
import sys, pcbnew
mm = pcbnew.FromMM
path = sys.argv[1]
MARGIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5   # folga extra (mm) de cobre de outra net
STEP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4
b = pcbnew.LoadBoard(path); gnd = b.FindNet("/GND").GetNetCode()
zs = list(b.Zones())
def items(): return list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]
def free(pt, its):
    for it in its:
        same = it.GetNetCode() == gnd
        if same and it.GetClass() != "PCB_VIA" and not (it.GetClass() == "PAD" and it.GetDrillSize().x > 0): continue
        if it.HitTest(pt, mm(0.3 + (1.0 if same else MARGIN))): return False
    return True
n = 0
for z in zs:
    L = z.GetLayer(); ps = z.GetFilledPolysList(L)
    other = [q for q in zs if q is not z]
    for i in range(ps.OutlineCount()):
        o = ps.COutline(i)
        if abs(o.Area()) / 1e12 > 500: continue
        if any(t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd and o.PointInside(t.GetPosition()) for t in b.GetTracks()): continue
        bb = o.BBox(); best = None
        its = items()
        x = bb.GetX() / 1e6
        while x < (bb.GetX() + bb.GetWidth()) / 1e6:
            y = bb.GetY() / 1e6
            while y < (bb.GetY() + bb.GetHeight()) / 1e6:
                pt = pcbnew.VECTOR2I(mm(x), mm(y))
                if o.PointInside(pt) and z.HitTestFilledArea(L, pt, mm(0.31)) and all(q.HitTestFilledArea(q.GetLayer(), pt, mm(0.31)) for q in other) and free(pt, its):
                    best = pt; break
                y += STEP
            if best: break
            x += STEP
        if best:
            v = pcbnew.PCB_VIA(b); v.SetPosition(best); v.SetNet(b.FindNet("/GND")); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); b.Add(v); n += 1
            print("via", b.GetLayerName(L), round(best.x / 1e6, 2), round(best.y / 1e6, 2))
        else:
            print("sem ponto", b.GetLayerName(L), round(bb.GetX() / 1e6, 1), round(bb.GetY() / 1e6, 1))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path, b)
print("vias", n)
