#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bloco de troca de cartucho (D126), acabamento depois do roteamento: avisos de silkscreen, rótulos dos LEDs, data, pads de GND sólidos
onde o DRC aponta starved_thermal e novo preenchimento das zonas.
Uso (Python do venv do KiCad MCP): python finish.py boards/<placa>/hardware [--move "TEXTO=x,y"]... [--date 2026-11-07]"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path
import pcbnew

ap = argparse.ArgumentParser()
ap.add_argument("hw"); ap.add_argument("--move", action="append", default=[]); ap.add_argument("--date", default="2026-11-07")
ap.add_argument("--led-side", default="up")
a = ap.parse_args()
HW = Path(a.hw); PCB = str(HW / "dumper.kicad_pcb")
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(PCB)

def silk_text(txt, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(layer); t.SetPosition(V(x, y)); t.SetTextSize(V(size, size)); t.SetTextThickness(mm(0.15))
    b.Add(t); return t

# rótulos dos LEDs (o verde só existe aqui se o gerador o criou)
for f in b.GetFootprints():
    v = f.GetValue()
    if v.startswith("LED") and f.GetReference() != "D1":
        txt = {"LED verde 3mm": "5V LIGADO", "LED amarelo 3mm": "SEGURO TROCAR"}.get(v)
        f.Reference().SetVisible(False)
        if txt and not any(d.GetClass() == "PCB_TEXT" and d.GetText() == txt for d in b.GetDrawings()):
            c = f.GetPosition(); dy = -3.6 if a.led_side == "up" else 3.6
            silk_text(txt, tomm(c.x), tomm(c.y) + dy, 0.9)
moves = {m.split("=")[0]: tuple(float(v) for v in m.split("=")[1].split(",")) for m in a.move}
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT":
        continue
    t = d.GetText()
    if t == "NÃO COLOQUE NEM RETIRE":
        d.SetText("SÓ TROQUE O CARTUCHO COM")
    elif t == "O CARTUCHO COM USB LIGADO":
        d.SetText("O LED AMARELO ACESO")
    m = re.search(r"v\d+\.\d+\s+\d{4}-\d{2}-\d{2}", t)
    if m:
        d.SetText(re.sub(r"\d{4}-\d{2}-\d{2}", a.date, t))
    for key, (x, y) in moves.items():
        if t.startswith(key):
            d.SetPosition(V(x, y))
tb = b.GetTitleBlock()
pcbnew.SaveBoard(PCB, b)

# pads de GND com alívio térmico incompleto: sólidos (iterativo)
for _ in range(3):
    with tempfile.TemporaryDirectory() as t:
        rpt = Path(t) / "drc.txt"
        subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "-o", str(rpt), PCB], capture_output=True)
        txt = rpt.read_text()
    pads = re.findall(r"\[starved_thermal\].*?\n.*?\n.*?\n\s+@\([^)]*\): PTH pad (\S+) \[[^\]]*\] of (\S+)", txt)
    if not pads:
        break
    b = pcbnew.LoadBoard(PCB)
    for pad, ref in pads:
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNumber() == pad:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); print(ref, pad, "sólido")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
b = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("ok")
