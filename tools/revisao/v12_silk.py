#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v. 1.2 (D107): aviso do USB no silk (como nas placas de um cartucho, D104), mantendo "UM CARTUCHO POR VEZ" menor,
e data da versão 2026-11-06. Idempotente. Uso: PYTHONPATH=/usr/lib/python3/dist-packages python3 tools/revisao/v12_silk.py"""
import pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = __file__.rsplit("/tools/", 1)[0] + "/boards/16_bits/hardware/dumper.kicad_pcb"
b = pcbnew.LoadBoard(path)
X = 45.0
AVISO = ("NÃO COLOQUE NEM RETIRE", "O CARTUCHO COM USB LIGADO")
existentes = {d.GetText(): d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT"}
for d in existentes.values():
    t = d.GetText()
    if t == "UM CARTUCHO POR VEZ":
        d.SetPosition(V(X, 99.0)); d.SetTextSize(V(2.0, 2.0)); d.SetTextThickness(mm(0.3))
    elif t.startswith("SNES / MEGA DRIVE"):
        d.SetText("SNES / MEGA DRIVE   v. 1.2   2026-11-06"); d.SetPosition(V(53.0, 106.2))
for k, linha in enumerate(AVISO):
    t = existentes.get(linha)
    if t is None:
        t = pcbnew.PCB_TEXT(b); t.SetText(linha); t.SetLayer(pcbnew.F_SilkS); b.Add(t)
    t.SetPosition(V(X, 101.6 + 2.3 * k))
    t.SetTextSize(V(1.7, 1.7)); t.SetTextThickness(mm(0.26))
# rotulo do C4 (a v12_c4.py o levou para fora da placa) e silk dele fora dos pads
c4 = b.FindFootprintByReference("C4")
c4.Reference().SetPosition(V(88.5, 43.5))
for g in c4.GraphicalItems():
    if g.GetLayer() == pcbnew.F_SilkS:
        for getp, setp in ((g.GetStart, g.SetStart), (g.GetEnd, g.SetEnd)):
            q = getp()
            if abs(pcbnew.ToMM(q.x) - 91.9) < 0.01: setp(V(90.9, pcbnew.ToMM(q.y)))
            if abs(pcbnew.ToMM(q.x) - 97.1) < 0.01: setp(V(98.1, pcbnew.ToMM(q.y)))
pcbnew.SaveBoard(path, b)
print("ok")
