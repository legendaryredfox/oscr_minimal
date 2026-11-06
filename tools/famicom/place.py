#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da placa só-Famicom a partir da cópia da 16_and_8_bits: limpa trilhas e zonas, remove os outros slots,
Si5351, PIC, R2, U3 e os capacitores que não são do Famicom (o Famicom não usa clock nem CIC), move o slot FC1 para o
centro do Mega (como o Mega Drive na placa megadrive), refaz contorno e reposiciona peças e textos.
Uso (Python do venv do KiCad MCP): python place.py boards/famicom/hardware/dumper.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
for ref in ("SNES1", "NES1", "MD1", "GBA1", "U1", "U2", "R2", "U3", "C2", "C3", "C5", "C6", "C7", "C8", "C9", "MH5", "MH6"):
    b.RemoveNative(b.FindFootprintByReference(ref))
X0, Y0, X1, Y1 = 16.0, 52.0, 123.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
def mv(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
mv("FC1", 64.0, 84.3)
mv("MH1", 19, 55); mv("MH2", 120, 55); mv("MH3", 19, 114); mv("MH4", 120, 114)
mv("C1", 26, 61); mv("R1", 24, 69, 0); mv("D1", 42, 69, 0)
mv("C4", 104.8, 74.5)
keep = {"FAMICOM: v v ETIQUETA v v": (64.0, 92.5), "UM CARTUCHO POR VEZ": (60.0, 99.0),
        "SNES / NES / FAMICOM / MEGA DRIVE   v1.0   2026-11-02": (60.0, 104.5),
        "Projeto original: github.com/sanni/cartreader": (75.0, 65.0),
        "Adaptado por: github.com/legendaryredfox/oscr_minimal": (75.0, 67.5),
        "Baseado no Open Source Cartridge Reader de sanni — CC BY 4.0": (75.0, 70.0)}
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t in keep:
        if t.startswith("SNES /"): d.SetText("FAMICOM   v1.0   2026-11-06")
        d.SetPosition(V(*keep[t]))
        if t.startswith(("Projeto", "Adaptado", "Baseado")): d.SetLayer(pcbnew.B_SilkS); d.SetMirrored(True)   # créditos na face de baixo, como nas outras placas
    else: b.RemoveNative(d)
b.Save(path); print("ok")
