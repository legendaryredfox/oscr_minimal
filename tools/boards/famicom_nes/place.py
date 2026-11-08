#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da placa Famicom + NES a partir da cópia da 16_and_8_bits: limpa trilhas e zonas, remove SNES, Mega Drive, GBA,
PIC, R2, U3 e os capacitores deles, deixa o slot NES no centro do Mega (como na placa nes) e põe o slot Famicom acima do
cabeçalho do Mega (a placa cresce para cima), refaz o contorno e reposiciona peças e textos.
Uso (Python do venv do KiCad MCP): python place.py boards/famicom_nes/hardware-v1.1/dumper.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
for ref in ("SNES1", "MD1", "GBA1", "U2", "R2", "U3", "C2", "C5", "C6", "C7", "C8", "C9", "MH5", "MH6"):
    f = b.FindFootprintByReference(ref)
    if f is not None: b.RemoveNative(f)
X0, Y0, X1, Y1 = 11.0, 38.0, 123.0, 117.0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(d)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
def mv(ref, x, y, rot=None):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y))
    if rot is not None: f.SetOrientationDegrees(rot)
mv("NES1", 52.0, 84.3)        # entre as fileiras de pinos do Mega, 12 mm à esquerda do centro: sobra espaço à direita para o Si5351
mv("FC1", 60.0, 46.0)         # acima do cabeçalho do Mega
mv("MH1", 19, 41); mv("MH2", 120, 41); mv("MH3", 19, 114); mv("MH4", 120, 114)
mv("C1", 26, 61); mv("R1", 24, 69, 0); mv("D1", 42, 69, 0)
mv("C3", 18.0, 96.5)          # VCC do NES (pino 36)
mv("C4", 100.8, 56.6)         # VCC do Famicom (pinos 30 e 31)
mv("U1", 111.0, 76.7, 0)      # soquete do Si5351 na vertical, ao lado do header 2x18 do Mega (o módulo fica em pé, com folga até o slot NES e até o header do Mega)
keep = {"FAMICOM: v v ETIQUETA v v": (60.0, 56.5), "NES: v v ETIQUETA v v": (64.0, 94.5),
        "UM CARTUCHO POR VEZ": (60.0, 99.0),
        "SNES / NES / FAMICOM / MEGA DRIVE   v1.0   2026-11-02": (52.0, 104.5),
        "Si5351  pino 1 = VIN": (111.5, 72.0),
        "Projeto original: github.com/sanni/cartreader": (52.0, 73.0),
        "Adaptado por: github.com/legendaryredfox/oscr_minimal": (52.0, 75.0),
        "Baseado no Open Source Cartridge Reader de sanni — CC BY 4.0": (52.0, 77.0)}
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t = d.GetText()
    if t in keep:
        if t.startswith("SNES /"): d.SetText("FAMICOM + NES   v1.0   2026-11-06")
        d.SetPosition(V(*keep[t]))
        if t.startswith("Si5351"): d.SetText("Si5351"); d.SetTextAngle(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
    else: b.RemoveNative(d)
b.FindFootprintByReference("U1").Reference().SetPosition(V(108.0, 76.0))
b.FindFootprintByReference("C4").Reference().SetPosition(V(100.8, 54.3))
pcbnew.SaveBoard(path, b); print("ok")
