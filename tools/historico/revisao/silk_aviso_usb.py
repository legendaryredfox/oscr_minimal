#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Revisão do silkscreen (D104). Idempotente.
1. Placas de um cartucho só (snes, megadrive, nes, famicom, gb_gba): troca "UM CARTUCHO POR VEZ" por um aviso de duas
   linhas: não colocar nem retirar o cartucho com a placa ligada ao computador.
2. Ajustes de rótulos: C5 e C6 da 16_bits visíveis (C5 abaixo, C6 acima do capacitor, fora dos pads do Mega); "PIC EM SOQUETE"
   da snes abaixo do rótulo U2; rótulo D1 da 16_and_8_bits fora do pad do R1.
Uso (Python com pcbnew): PYTHONPATH=/usr/lib/python3/dist-packages python3 tools/historico/revisao/silk_aviso_usb.py"""
import pcbnew
mm = pcbnew.FromMM
ROOT = __file__.rsplit("/tools/", 1)[0]
OLD = "UM CARTUCHO POR VEZ"
AVISO = ("NÃO COLOQUE NEM RETIRE", "O CARTUCHO COM USB LIGADO")
for brd in ("snes", "megadrive", "nes", "famicom", "gb_gba"):
    path = f"{ROOT}/boards/{brd}/hardware/dumper.kicad_pcb"
    b = pcbnew.LoadBoard(path)
    old = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetText() == OLD]
    for d in old:
        x, y = d.GetX(), d.GetY()
        b.RemoveNative(d)
        for k, linha in enumerate(AVISO):
            t = pcbnew.PCB_TEXT(b)
            t.SetText(linha); t.SetLayer(pcbnew.F_SilkS)
            t.SetPosition(pcbnew.VECTOR2I(x, y + mm(-1.5 + 3.0 * k)))
            t.SetTextSize(pcbnew.VECTOR2I(mm(2), mm(2))); t.SetTextThickness(mm(0.3))
            b.Add(t)
    if brd == "snes":
        for d in b.GetDrawings():
            if d.GetClass() == "PCB_TEXT" and d.GetText() == "PIC EM SOQUETE":
                d.SetPosition(pcbnew.VECTOR2I(mm(84.0), mm(77.8)))
    b.Save(path); print(brd, "aviso" if old else "sem texto antigo")
V = pcbnew.VECTOR2I
path = f"{ROOT}/boards/16_bits/hardware-v1.3/dumper.kicad_pcb"
b = pcbnew.LoadBoard(path)
for ref, dy in (("C5", 3.6), ("C6", -2.6)):
    f = b.FindFootprintByReference(ref); r = f.Reference()
    r.SetVisible(True); r.SetPosition(V(f.GetX() + mm(2.5), f.GetY() + mm(dy)))
b.Save(path); print("16_bits C5, C6 visíveis")
path = f"{ROOT}/boards/16_and_8_bits/hardware-v1.1/dumper.kicad_pcb"
b = pcbnew.LoadBoard(path)
b.FindFootprintByReference("D1").Reference().SetPosition(V(mm(121.2), mm(102.0)))
b.Save(path); print("16_and_8_bits D1 movido")
