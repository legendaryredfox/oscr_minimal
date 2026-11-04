# SPDX-License-Identifier: GPL-3.0-or-later
import sys, itertools; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from pcbops import *
src, dst, schp = sys.argv[2], sys.argv[3], sys.argv[4]
YS = [float(v) for v in sys.argv[5].split(",")]
X0, X1, PITCH = float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8])
sch = open(schp).read()
b = pcbnew.LoadBoard(src)
TPS = [("TP1", "/+5V", "5V"), ("TP2", "/GND", "GND"), ("TP3", "/D6", "/CE"), ("TP4", "/D9", "/OE"), ("TP5", "/D8", "/WE"), ("TP6", "/D7", "/UWR")]
R = 1.0 + CLR + 0.07
g = Grid(b)
def snap(v, o): return o + round((v-o)/RES)*RES
XS = [snap(X0+PITCH*k, g.x0) for k in range(int((X1-X0)/PITCH)+1)]
def crt_hit(x0, y0, x1, y1):
    for f in b.GetFootprints():
        if f.GetReference() == "A1": continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        if not (x1 < bb.GetLeft()/MM or x0 > bb.GetRight()/MM or y1 < bb.GetTop()/MM or y0 > bb.GetBottom()/MM): return True
    return False
rects = []
for f in b.GetFootprints():
    for p in f.Pads():
        bb = p.GetBoundingBox(); rects.append((p.GetNetname(), bb.GetLeft()/MM, bb.GetTop()/MM, bb.GetRight()/MM, bb.GetBottom()/MM))
cost = {}      # (ref, y, k) -> custo
for ref, net, label in TPS:
    trk, via, dist, both = g.free_maps(net)
    if net != "/GND":
        D, par = dijkstra_from(g, net_mask(g, net), trk, via, via_cost=12.0, maxd=150)
        C = np.minimum(D[0], D[1])
    for y in YS:
        for k, x in enumerate(XS):
            i, j = g.cell(x, y)
            ok = both[j, i] >= R and not crt_hit(x-1.3, y-1.3, x+1.3, y+1.3) and not any(r[0] != net and not (x+3.6 < r[1] or x+1.2 > r[3] or y+0.7 < r[2] or y-0.7 > r[4]) for r in rects)
            cost[(ref, y, k)] = (C[j, i] if net != "/GND" else 0.0) if ok else 1e9
    print(ref, net, "ok", sum(1 for y in YS for k in range(len(XS)) if cost[(ref, y, k)] < 1e8), "de", len(YS)*len(XS), flush=True)
best = []
refs = [t[0] for t in TPS]
for y in YS:
    for w in range(len(XS)-5):
        for perm in itertools.permutations(range(6)):
            tot = 0.0
            for r, pos in zip(refs, perm):
                c = cost[(r, y, w+pos)]
                if c >= 1e8: tot = 1e9; break
                tot += c
            if tot < 1e8: best.append((tot, y, w, perm))
best.sort()
print("combinacoes", len(best), best[:3])
def build(y, w, perm):
    bb = pcbnew.LoadBoard(src)
    for (ref, net, label), pos in zip(TPS, perm):
        x = XS[w+pos]
        fp = add_fp(bb, "/usr/share/kicad/footprints/TestPoint.pretty", "TestPoint", "TestPoint_THTPad_D2.0mm_Drill1.0mm", ref, label, x, y, 0, {"1": net}, sch_uuid(sch, ref))
        fp.Reference().SetVisible(False)
        v = fp.Value(); v.SetVisible(True); v.SetLayer(pcbnew.F_SilkS); v.SetTextSize(pcbnew.VECTOR2I(int(1.0*MM), int(1.0*MM))); v.SetTextThickness(int(0.16*MM))
        v.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); v.SetPosition(pcbnew.VECTOR2I(int(x*MM), int((y+2.0)*MM)))
    # rotear em ordem de menor custo
    order = sorted(range(6), key=lambda t: cost[(refs[t], y, w+perm[t])])
    for t in order:
        ref, net, label = TPS[t]
        if net == "/GND": continue
        x = XS[w+perm[t]]
        gg = Grid(bb)
        trk, via, _, _ = gg.free_maps(net)
        goal = net_mask(gg, net)
        i, j = gg.cell(x, y)
        for L in range(2): goal[L][j-12:j+13, i-12:i+13] = False
        bp = None
        for l0 in (0, 1):
            p = route_mask(gg, (x, y, l0), goal, trk, via, via_cost=12.0)
            if p and (bp is None or len(p) < len(bp)): bp = p
        if bp is None: return None
        add_path(bb, gg, net, bp, p_start=(x, y))
    return bb
for tot, y, w, perm in best[:12]:
    bb = build(y, w, perm)
    if bb is not None:
        print("escolhido: y=%.2f janela=%d total=%.1f mm  %s" % (y, w, tot, {TPS[t][0]: round(XS[w+perm[t]], 2) for t in range(6)}))
        pcbnew.SaveBoard(dst, bb); break
else:
    sys.exit("nenhuma combinacao roteou")
