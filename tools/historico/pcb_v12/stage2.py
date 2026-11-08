# SPDX-License-Identifier: GPL-3.0-or-later
import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from pcbops import *
src, dst = sys.argv[2], sys.argv[3]
g = Grid(src); b = g.b
ni = pcbnew.NETINFO_ITEM(b, "/CART"); b.Add(ni)
a = b.FindFootprintByReference("MD1"); m = b.FindFootprintByReference("A1")
pa = [p for p in a.Pads() if p.GetNumber() == "B32"][0]; pm = [p for p in m.Pads() if p.GetNumber() == "D50"][0]
pa.SetNet(ni); pm.SetNet(ni)
sx, sy = pa.GetPosition().x/MM, pa.GetPosition().y/MM
gx, gy = pm.GetPosition().x/MM, pm.GetPosition().y/MM
print("de", sx, sy, "para", gx, gy)
trk, via, _, _ = g.free_maps("/CART")
goal = net_mask(g, "/CART")
i, j = g.cell(sx, sy)
for L in range(2): goal[L][j-12:j+13, i-12:i+13] = False
best = None
for l0 in (0, 1):
    p = route_mask(g, (sx, sy, l0), goal, trk, via, via_cost=12.0)
    print("camada", l0, None if p is None else round(len(p)*RES, 1))
    if p and (best is None or len(p) < len(best)): best = p
if best is None: sys.exit("sem caminho")
print("trilhas/vias", add_path(b, g, "/CART", best, p_start=(sx, sy), p_end=(gx, gy)))
pcbnew.SaveBoard(dst, b)
