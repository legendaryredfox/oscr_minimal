#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: ajustes de silkscreen e furos numa placa: tira o texto "PIC EM SOQUETE", mostra a referência de todos os resistores (R e RN) e remove os furos de fixação que não são dos cantos (pedido do usuário).
Uso (python do KiCad MCP, com pcbnew): python tools/troca/silk138.py boards/<placa>/hardware-<versão> [...]"""
import sys
from pathlib import Path
import pcbnew
mm = pcbnew.FromMM
for hw in sys.argv[1:]:
    p = Path(hw) / "dumper.kicad_pcb"
    b = pcbnew.LoadBoard(str(p))
    tirados = 0
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_TEXT" and d.GetText().strip().upper() == "PIC EM SOQUETE":
            b.RemoveNative(d); tirados += 1
    mostrados = 0
    for f in b.GetFootprints():
        r = f.GetReference()
        if r.startswith("R") and r[1:].replace("N", "").isdigit():
            t = f.Reference()
            if not t.IsVisible():
                t.SetVisible(True); mostrados += 1
            t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); t.SetTextThickness(mm(0.12))
    bb = b.GetBoardEdgesBoundingBox()
    L, R, T, B = (pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetRight(), bb.GetTop(), bb.GetBottom()))
    furos = []
    for f in list(b.GetFootprints()):
        if f.GetReference().startswith("MH"):
            x, y = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
            if not (min(x - L, R - x) < 10 and min(y - T, B - y) < 10):      # canto = a menos de 10 mm de duas bordas perpendiculares
                furos.append(f.GetReference()); b.RemoveNative(f)
    pcbnew.SaveBoard(str(p), b)
    print(hw, "texto PIC removido:", tirados, "| rótulos de resistor mostrados:", mostrados, "| furos fora dos cantos removidos:", furos or "-")
