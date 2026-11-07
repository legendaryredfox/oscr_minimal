#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Alarga as trilhas de alimentação (+5V, +3V3) de uma placa já roteada até onde cabe (CLAUDE.md, seção 5: 0,8 a 1,0 mm).
O padrão de net class 'Power' do projeto dizia '+5V', mas a net se chama '/+5V', então o Freerouting roteou tudo com 0,3 mm.
Para cada segmento tenta 0,8, 0,6, 0,5 e 0,4 mm e fica com o maior que mantém 0,2 mm de folga de cobre de outra net
(trilhas, vias e pads na mesma camada). Depois: preencher as zonas e rodar o DRC.
Uso (Python do venv do KiCad MCP): widen_power.py placa.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
NETS = {"/+5V", "/+3V3", "+5V", "+3V3", "+5V_CART"}
CLR = mm(0.2)
others = [t for t in b.GetTracks()] + [p for f in b.GetFootprints() for p in f.Pads()]
hist = {}
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK" or t.GetNetname() not in NETS: continue
    ly = t.GetLayer(); old = t.GetWidth(); best = old
    for w in (0.8, 0.6, 0.5, 0.4):
        if mm(w) <= old: break
        t.SetWidth(mm(w)); sh = t.GetEffectiveShape()
        bad = False
        for o in others:
            if o is t or o.GetNetCode() == t.GetNetCode(): continue
            if o.GetClass() == "PAD":
                if not o.IsOnLayer(ly): continue
            elif o.GetClass() == "PCB_VIA":
                pass
            elif o.GetLayer() != ly: continue
            if sh.Collide(o.GetEffectiveShape(ly), CLR): bad = True; break
        if not bad: best = mm(w); break
    t.SetWidth(best); hist[round(pcbnew.ToMM(best), 2)] = hist.get(round(pcbnew.ToMM(best), 2), 0) + 1
pcbnew.SaveBoard(path, b)
print("larguras:", dict(sorted(hist.items())))
