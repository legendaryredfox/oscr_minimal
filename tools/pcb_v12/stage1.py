# SPDX-License-Identifier: GPL-3.0-or-later
import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from pcbops import *
src, dst, schp = sys.argv[2], sys.argv[3], sys.argv[4]
sch = open(schp).read()
g = Grid(src); b = g.b
CAPS = (("C5", 101.35, 111.05), ("C6", 33.45, 111.05))
CAPLIB = "/usr/share/kicad/footprints/Capacitor_THT.pretty"; NAME = "C_Disc_D5.0mm_W2.5mm_P5.00mm"
for ref, x, y in CAPS:
    add_fp(b, CAPLIB, "Capacitor_THT", NAME, ref, "100n", x, y, 0, {"1": "/+5V", "2": "/GND"}, sch_uuid(sch, ref), like="C3")
# 5V de cada capacitor ate o cobre de 5V mais proximo
for ref, x, y in CAPS:
    g2 = Grid.__new__(Grid); g2.__dict__.update(g.__dict__)
    trk, via, _, _ = g.free_maps("/+5V")
    goal = net_mask(g, "/+5V")
    # nao terminar dentro da propria pad do capacitor: apagar a regiao da pad da mascara de destino
    i, j = g.cell(x, y)
    for L in range(2): goal[L][j-10:j+11, i-10:i+11] = False
    best = None
    for l0 in (0, 1):
        p = route_mask(g, (x, y, l0), goal, trk, via)
        if p and (best is None or len(p) < len(best)): best = p
    print(ref, "caminho", None if best is None else len(best)*RES)
    if best: print(ref, "trilhas/vias", add_path(b, g, "/+5V", best))
for ref, x, y in CAPS:
    f = b.FindFootprintByReference(ref)
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    print(ref, [(p.GetNumber(), round(p.GetPosition().x/MM,2), round(p.GetPosition().y/MM,2), p.GetNetname()) for p in f.Pads()])
pcbnew.SaveBoard(dst, b)
