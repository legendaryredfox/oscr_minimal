#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da placa n64 (slot N64, 3,3 V) a partir da cópia da 16_and_8_bits: limpa trilhas, vias e zonas,
remove os outros slots, o PIC, C2 a C6 e os furos M2, acrescenta o N64_Slot (nets pelo pinmap.md), liga o R2 ao 3,3 V,
renumera U3->U2, C7->C2, C8->C3, C9->C4 (como no esquemático), refaz contorno e reposiciona peças e textos.
Uso (Python do venv do KiCad MCP): place.py boards/n64/hardware/dumper.kicad_pcb"""
import re, sys, pcbnew
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
for ref in ("SNES1", "NES1", "FC1", "MD1", "GBA1", "U2", "C2", "C3", "C4", "C5", "C6", "MH5", "MH6"):
    f = b.FindFootprintByReference(ref)
    if f is not None: b.RemoveNative(f)
for old, new in (("U3", "U2"), ("C7", "C2"), ("C8", "C3"), ("C9", "C4")):
    f = b.FindFootprintByReference(old)
    if f is not None: f.SetReference(new)

# slot N64
if b.FindFootprintByReference("N64_1") is None:
    s = pcbnew.FootprintLoad(str(ROOT / "boards/_lib/dumper.pretty"), "N64_Slot")
    s.SetReference("N64_1"); s.SetValue("N64_Slot"); b.Add(s)
slot = b.FindFootprintByReference("N64_1")
net_of = {}
for ln in (ROOT / "boards/n64/docs/pinmap.md").read_text().splitlines():
    if ln.startswith("| ") and not ln.startswith("| pino") and not ln.startswith("|---"):
        c = [x.strip() for x in ln.strip("|").split("|")]
        if c[0].isdigit() and len(c) == 5: net_of[c[0]] = c[2]
for p in slot.Pads():
    n = net_of[p.GetNumber()]
    if n.startswith("NC"): continue
    n = "+3V3" if n.startswith("3V3") else n.split()[0]
    net = b.FindNet("/" + n)
    assert net is not None, n
    p.SetNet(net)
r2 = b.FindFootprintByReference("R2")
for p in r2.Pads():
    if p.GetNumber() == "1": p.SetNet(b.FindNet("/+3V3"))

X0, Y0, X1, Y1 = 13.0, 52.0, 123.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
def mv(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
mv("N64_1", 31.0, 87.5, 0)            # pad 1 em (31; 87,5), pads até x = 91; fila de cima em y = 82,5
mv("MH1", 19, 55); mv("MH2", 120, 55); mv("MH3", 19, 114); mv("MH4", 120, 114)
mv("C1", 26, 61); mv("R1", 24, 69, 0); mv("D1", 42, 69, 0)
mv("U1", 53, 69, 90)
mv("C4", 51, 98.5, 90)                  # junto aos VCC (pads 9 e 34) do slot
mv("R2", 100, 88, 90)                 # pull-up do EEPROM_DATA (D7)
mv("C2", 88, 100, 0); mv("U2", 97, 100, 0); mv("C3", 105, 100, 0)   # a origem do C é o pad 1 (o pad 2 fica 5 mm à direita)
keep = {"Si5351  pino 1 = VIN": (71.0, 65.5),
        "UM CARTUCHO POR VEZ": None,
        "SNES / NES / FAMICOM / MEGA DRIVE   v1.0   2026-11-02": (52.0, 113.5),
        "Projeto original: github.com/sanni/cartreader": (52.0, 73.0),
        "Adaptado por: github.com/legendaryredfox/oscr_minimal": (52.0, 75.0),
        "Baseado no Open Source Cartridge Reader de sanni — CC BY 4.0": (52.0, 77.0)}
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t in keep and keep[t] is not None:
        if t.startswith("SNES /"): d.SetText("N64 (3,3 V)   v1.0   2026-11-07")
        d.SetPosition(V(*keep[t]))
    else: b.RemoveNative(d)
def add_text(txt, x, y, h):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(V(x, y)); t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(h * 0.15)); b.Add(t)
add_text("N64: ETIQUETA A CONFIRMAR", 78.0, 94.5, 1.0)
add_text("SOMENTE N64 - 3,3 V", 78.0, 96.0, 1.0)
add_text("NÃO COLOQUE NEM RETIRE", 58.0, 102.4, 1.6)
add_text("O CARTUCHO COM USB LIGADO", 58.0, 104.8, 1.6)
b.FindFootprintByReference("N64_1").Reference().SetPosition(V(38.0, 93.8))
b.FindFootprintByReference("U1").Reference().SetPosition(V(56.8, 66.6))
b.Save(path); print("ok")
