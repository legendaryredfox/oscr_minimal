#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reaplica só os textos e o campo de referência do U1 do place.py numa placa já roteada (não mexe em peças nem trilhas).
Uso (Python do venv do KiCad MCP): retext.py placa.kicad_pcb (importa o dicionário 'keep' de place.py lendo o arquivo)"""
import re, sys, ast, pcbnew
src = open(__file__.replace("retext.py", "place.py")).read()
keep = ast.literal_eval(re.search(r"keep = (\{.*?\})\n", src, re.S).group(1))
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and (d.GetText() in keep or d.GetText().startswith("NES   v1.0")):
        k = d.GetText() if d.GetText() in keep else "SNES / NES / FAMICOM / MEGA DRIVE   v1.0   2026-11-02"
        d.SetPosition(pcbnew.VECTOR2I(mm(keep[k][0]), mm(keep[k][1])))
b.FindFootprintByReference("U1").Reference().SetPosition(pcbnew.VECTOR2I(mm(56.8), mm(66.6)))
pcbnew.SaveBoard(sys.argv[1], b)
