# SPDX-License-Identifier: GPL-3.0-or-later
import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from pcbops import *
g = Grid(sys.argv[2])
tgt = tuple(float(v) for v in sys.argv[3:5]); rmax = float(sys.argv[5]); skip = sys.argv[6:] 
trk, via, dist, both = g.free_maps("/+5V")
src = net_mask(g, "/+5V")
D, par = dijkstra_from(g, src, trk, via, maxd=60)
fmG = [g.foreign("/GND", l) for l in g.layers]
bothG = ndimage.distance_transform_edt(~(fmG[0] | fmG[1]))*RES
R = 0.8 + CLR + 0.06
# patios de TODOS os footprints exceto A1 (contorno do Mega)
def crt_hit(x0, y0, x1, y1):
    for f in g.b.GetFootprints():
        if f.GetReference() in ("A1",) + tuple(skip): continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        if not (x1 < bb.GetLeft()/MM or x0 > bb.GetRight()/MM or y1 < bb.GetTop()/MM or y0 > bb.GetBottom()/MM): return True
    return False
# pinos e textos de silk que o corpo da peca nao pode cobrir
others = []
for f in g.b.FindFootprintByReference("A1"), :
    pass
pads = []
for f in g.b.GetFootprints():
    for p in f.Pads():
        pos = p.GetPosition(); bb = p.GetBoundingBox()
        pads.append((bb.GetLeft()/MM-0.3, bb.GetTop()/MM-0.3, bb.GetRight()/MM+0.3, bb.GetBottom()/MM+0.3))
texts = []
for d in g.b.GetDrawings():
    if d.Type() == pcbnew.PCB_TEXT_T and d.GetLayer() in (pcbnew.F_SilkS,):
        bb = d.GetBoundingBox(); texts.append((bb.GetLeft()/MM-0.3, bb.GetTop()/MM-0.3, bb.GetRight()/MM+0.3, bb.GetBottom()/MM+0.3))
for f in g.b.GetFootprints():
    for t in (f.Reference(), f.Value()):
        if t.IsVisible() and t.GetLayer() == pcbnew.F_SilkS:
            bb = t.GetBoundingBox(); texts.append((bb.GetLeft()/MM-0.3, bb.GetTop()/MM-0.3, bb.GetRight()/MM+0.3, bb.GetBottom()/MM+0.3))
def hit_rects(rects, x0, y0, x1, y1, own=()):
    for (a, b, c2, d) in rects:
        if not (x1 < a or x0 > c2 or y1 < b or y0 > d): return True
    return False
c = []
snap = lambda v, o: o + round((v-o)/RES)*RES
for dx in np.arange(-rmax, rmax+0.01, 0.1):
    for dy in np.arange(-rmax, rmax+0.01, 0.1):
        x, y = snap(tgt[0]+dx, g.x0), snap(tgt[1]+dy, g.y0)
        if math.hypot(x-tgt[0], y-tgt[1]) > rmax: continue
        i, j = g.cell(x, y)
        if not (0 <= i < g.nx and 0 <= j < g.ny) or x < g.x0+2 or x > g.x1-2 or y < g.y0+2 or y > g.y1-2: continue
        if both[j, i] < R: continue
        d1 = min(D[0][j, i], D[1][j, i])
        if d1 > 6: continue
        for (ex, ey) in ((5, 0), (-5, 0), (0, 5), (0, -5)):
            x2, y2 = x+ex, y+ey
            i2, j2 = g.cell(x2, y2)
            if not (0 <= i2 < g.nx and 0 <= j2 < g.ny) or bothG[j2, i2] < R: continue
            xa, xb = min(x, x2)-1.3, max(x, x2)+1.3
            ya, yb = min(y, y2)-1.9, max(y, y2)+1.9
            if ey != 0: xa, xb, ya, yb = min(x, x2)-1.9, max(x, x2)+1.9, min(y, y2)-1.3, max(y, y2)+1.3
            if crt_hit(xa, ya, xb, yb): continue
            # corpo: entre as pads, sem pino de outra peca; so as proprias pads do capacitor (nos centros) ficam de fora
            bx0, bx1 = min(x, x2)-0.9, max(x, x2)+0.9
            by0, by1 = min(y, y2)-0.9, max(y, y2)+0.9
            own = [(x-0.9, y-0.9, x+0.9, y+0.9), (x2-0.9, y2-0.9, x2+0.9, y2+0.9)]
            if any(hit_rects([r], bx0, by0, bx1, by1) and not any(abs(r[0]+0.3-(o[0]+0.9)) < 1.0 and abs(r[1]+0.3-(o[1]+0.9)) < 1.0 for o in own) for r in pads): continue
            if hit_rects(texts, xa, ya, xb, yb): continue
            c.append((d1, math.hypot(x-tgt[0], y-tgt[1]), round(x, 2), round(y, 2), round(x2, 2), round(y2, 2)))
c.sort(key=lambda k: (k[1] + 0.3*k[0]))
for k in c[:6]: print("rota5V=%.1f dist_alvo=%.1f +5V(%.2f,%.2f) GND(%.2f,%.2f)" % k)
print(len(c))
