#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: fecha à mão as últimas ligações que o Freerouting deixou abertas. Para cada par "x1,y1,x2,y2" (mm, pontos de pad ou de ponta de trilha da mesma rede)
tenta caminhos em L e em Z, nas duas faces, e fica com o primeiro que não cria erro de DRC novo.
Uso (python do venv do KiCad MCP): python tools/troca/liga_manual.py <pasta hardware> <largura mm> x1,y1,x2,y2 [...]"""
import itertools, subprocess, sys, tempfile
from pathlib import Path
import pcbnew
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
HW = Path(sys.argv[1]); LARG = float(sys.argv[2]); PARES = [tuple(float(v) for v in a.split(",")) for a in sys.argv[3:]]
PCB = str(HW / "dumper.kicad_pcb")
ERROS = ("clearance", "shorting_items", "tracks_crossing", "copper_edge_clearance", "hole_clearance", "via_dangling", "courtyards_overlap")


def erros(b):
    d = tempfile.mkdtemp()
    pcbnew.SaveBoard(d + "/t.kicad_pcb", b)
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "-o", d + "/r.txt", d + "/t.kicad_pcb"], capture_output=True)
    t = Path(d + "/r.txt").read_text()
    return sum(t.count("[%s]" % e) for e in ERROS), t.count("[unconnected_items]")


def ponto_mais_proximo(b, x, y):
    """rede e posição exata do pad ou da ponta de trilha mais perto de (x, y)"""
    melhor = None
    P = pcbnew.VECTOR2I(mm(x), mm(y))
    cand = []
    for f in b.GetFootprints():
        for p in f.Pads():
            cand.append((p.GetPosition(), p.GetNetCode()))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            cand.append((t.GetPosition(), t.GetNetCode()))
        else:
            cand += [(t.GetStart(), t.GetNetCode()), (t.GetEnd(), t.GetNetCode())]
    return min(cand, key=lambda c: (c[0].x - P.x) ** 2 + (c[0].y - P.y) ** 2)


def caminho(a, b_, modo, lane):
    (x1, y1), (x2, y2) = a, b_
    if modo == "hv": return [(x1, y1), (x2, y1), (x2, y2)]
    if modo == "vh": return [(x1, y1), (x1, y2), (x2, y2)]
    if modo == "zh": return [(x1, y1), (lane, y1), (lane, y2), (x2, y2)]       # sai na horizontal, sobe na faixa x = lane
    return [(x1, y1), (x1, lane), (x2, lane), (x2, y2)]                         # sai na vertical, anda na faixa y = lane


b = pcbnew.LoadBoard(PCB)
base_err, base_aberto = erros(b)
print("base: erros", base_err, "abertas", base_aberto)
for (x1, y1, x2, y2) in PARES:
    pa, na = ponto_mais_proximo(b, x1, y1); pb, nb = ponto_mais_proximo(b, x2, y2)
    if na != nb:
        print("redes diferentes nos pontos", (x1, y1), (x2, y2), na, nb); continue
    A = (tomm(pa.x), tomm(pa.y)); B_ = (tomm(pb.x), tomm(pb.y))
    cands = [("hv", 0), ("vh", 0)]
    for k in range(-30, 31):
        cands.append(("zh", min(A[0], B_[0]) + (max(A[0], B_[0]) - min(A[0], B_[0])) / 2 + k * 1.27))
        cands.append(("zv", min(A[1], B_[1]) + (max(A[1], B_[1]) - min(A[1], B_[1])) / 2 + k * 1.27))
    feito = False
    for (modo, lane), layer in itertools.product(cands, (pcbnew.F_Cu, pcbnew.B_Cu)):
        pts = caminho(A, B_, modo, lane)
        novos = []
        for p, q in zip(pts, pts[1:]):
            if p == q: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
            t.SetLayer(layer); t.SetWidth(mm(LARG)); t.SetNetCode(na); b.Add(t); novos.append(t)
        e, ab = erros(b)
        if e <= base_err and ab < base_aberto:
            print("ligado", (round(A[0], 2), round(A[1], 2)), "->", (round(B_[0], 2), round(B_[1], 2)), modo, round(lane, 2), b.GetLayerName(layer)); base_aberto = ab; feito = True; break
        for t in novos:
            b.RemoveNative(t)
    if not feito:
        print("sem caminho para", (x1, y1, x2, y2))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("final: abertas", base_aberto)
