#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Seletor 3,3 V/5 V (D138): estende o contorno da placa para baixo em `delta` mm (onde entram o LDO, o Q4, o Q5 e as redes de resistores em série)
e desce os furos de fixação da borda de baixo. Uso (python do sistema, com pcbnew): /usr/bin/python3 -I tools/troca/estende.py <pasta hardware> <delta mm>
Escreve na saída padrão "y_antigo y_novo x0 x1" (mm) da borda de baixo."""
import sys
import pcbnew
from pathlib import Path
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
path = str(Path(sys.argv[1]) / "dumper.kicad_pcb"); delta = float(sys.argv[2])
b = pcbnew.LoadBoard(path)
bb = b.GetBoardEdgesBoundingBox()
y1 = bb.GetBottom()
n = 0
for d in b.GetDrawings():
    if d.GetLayer() != pcbnew.Edge_Cuts:
        continue
    for get, setp in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
        p = get()
        if abs(p.y - y1) < mm(0.2):
            setp(pcbnew.VECTOR2I(p.x, p.y + mm(delta))); n += 1
assert n >= 1, "borda de baixo não achada"
for f in b.GetFootprints():
    if f.GetReference().startswith("MH") and abs(f.GetPosition().y - y1) < mm(8):
        p = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(p.x, p.y + mm(delta)))
pcbnew.SaveBoard(path, b)
print("%.2f %.2f %.2f %.2f" % (tomm(y1), tomm(y1) + delta, tomm(bb.GetLeft()), tomm(bb.GetRight())))
