#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Junta os pontos de teste TP1 a TP6 de uma placa já roteada a 2,54 mm (tira de pinos 1x6 padrão): apaga o trecho de trilha que
liga cada TP ao resto da net (até o primeiro cruzamento ou pad), move os TPs e reroteia cada um com o A* de tools/historico/pcb_v12.
O GND (TP sem trilha) só muda de lugar: a zona o alcança. Depois rodar tools/boards/megadrive/tp_header.py e preencher as zonas.
Uso (Python do venv do KiCad MCP): move_tps.py placa.kicad_pcb x_centro_mm y_mm ORDEM...   ex.: ... 47.7 56.5 TP6 TP3 TP1 TP2 TP4 TP5"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pcb_v12"))
from pcbops import *
path, xc, y = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); order = sys.argv[4:]
PITCH = 2.54
b = pcbnew.LoadBoard(path)
key = lambda p: (round(p.x / 1000), round(p.y / 1000))        # tolerância de 1 µm
def stub(net, start):
    """trilhas da net ligadas ao ponto `start` por nós de grau 2 (só trilhas e vias), parando em pad ou cruzamento"""
    items = [t for t in b.GetTracks() if t.GetNetname() == net]
    pads = {key(p.GetPosition()) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net}
    out, front, seen = [], [key(start)], set()
    while front:
        pt = front.pop()
        if pt in seen: continue
        seen.add(pt)
        here = [t for t in items if t not in out and (key(t.GetStart()) == pt or key(t.GetEnd()) == pt or (t.GetClass() == "PCB_VIA" and key(t.GetPosition()) == pt))]
        if pt != key(start) and (len(here) != 1 or pt in pads): continue    # cruzamento ou pad: fica
        for t in here:
            out.append(t)
            if t.GetClass() == "PCB_VIA": front.append(key(t.GetPosition())); continue
            front.append(key(t.GetEnd()) if key(t.GetStart()) == pt else key(t.GetStart()))
    return out
nets = {}
for ref in order:
    f = b.FindFootprintByReference(ref); p = f.Pads()[0]; nets[ref] = p.GetNetname()
    for t in stub(p.GetNetname(), p.GetPosition()): b.RemoveNative(t)
for k, ref in enumerate(order):
    f = b.FindFootprintByReference(ref); dx = pcbnew.FromMM(xc + PITCH * (k - (len(order) - 1) / 2)) - f.GetX()
    f.SetPosition(pcbnew.VECTOR2I(f.GetX() + dx, pcbnew.FromMM(y)))
pcbnew.SaveBoard(path, b); del b
for ref in order:
    net = nets[ref]
    if net == "/GND": continue
    g = Grid(path); b = g.b
    pa = b.FindFootprintByReference(ref).Pads()[0]
    sx, sy = pa.GetPosition().x / MM, pa.GetPosition().y / MM
    trk, via, _, _ = g.free_maps(net)
    goal = net_mask(g, net)
    i, j = g.cell(sx, sy)
    for L in range(2): goal[L][j - 12:j + 13, i - 12:i + 13] = False
    best = None
    for l0 in (0, 1):
        p = route_mask(g, (sx, sy, l0), goal, trk, via, via_cost=12.0)
        if p and (best is None or len(p) < len(best)): best = p
    if best is None: sys.exit("sem caminho para " + ref)
    print(ref, net, "trilhas/vias", add_path(b, g, net, best, p_start=(sx, sy)))
    pcbnew.SaveBoard(path, b); del g, b
