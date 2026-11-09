#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Acabamento (D138; nasceu no bloco de troca de cartucho, D126) depois do roteamento: avisos de silkscreen, rótulos dos LEDs, data, pads de GND sólidos
onde o DRC aponta starved_thermal e novo preenchimento das zonas.
Uso (Python do venv do KiCad MCP): python finish.py boards/<placa>/hardware [--move "TEXTO=x,y"]... [--date 2026-11-07]"""
import argparse, re, subprocess, sys, tempfile
from pathlib import Path
import pcbnew

ap = argparse.ArgumentParser()
ap.add_argument("hw"); ap.add_argument("--move", action="append", default=[]); ap.add_argument("--date", default="2026-11-07")
ap.add_argument("--led-side", default="up")
ap.add_argument("--hide", action="append", default=[], help="oculta o texto de referência dessa peça")
ap.add_argument("--relabel", action="store_true", help="apaga e refaz os rótulos dos LEDs")
ap.add_argument("--fusivel", action="store_true", help="versão só com o F1: não troca os avisos do silkscreen")
a = ap.parse_args()
HW = Path(a.hw); PCB = str(HW / "dumper.kicad_pcb")
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(PCB)

def silk_text(txt, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(layer); t.SetPosition(V(x, y)); t.SetTextSize(V(size, size)); t.SetTextThickness(mm(0.15))
    b.Add(t); return t

# rótulos dos LEDs: primeiro lugar livre (sem tocar pads, silkscreen e outros textos) ao redor do LED
if a.relabel:
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_TEXT" and d.GetText() in ("5V LIGADO", "SEGURO TROCAR"):
            b.RemoveNative(d)
_bb = b.GetBoardEdgesBoundingBox(); bb_in = (_bb.GetLeft() + mm(1.5), _bb.GetTop() + mm(1.5), _bb.GetRight() - mm(1.5), _bb.GetBottom() - mm(1.5))
def _add_shape(boxes, g):
    """caixa de um item gráfico; item grande (retângulo ou contorno de peça) vale só pelas bordas, não pelo interior"""
    r = g.GetBoundingBox()
    l, t, rr, bt = r.GetLeft(), r.GetTop(), r.GetRight(), r.GetBottom()
    if (rr - l) * (bt - t) > mm(12) * mm(12) and g.GetClass() == "PCB_SHAPE":
        e = mm(0.3)
        boxes += [(l, t, rr, t + e), (l, bt - e, rr, bt), (l, t, l + e, bt), (rr - e, t, rr, bt)]
    else:
        boxes.append((l, t, rr, bt))
def occupied():
    boxes = []
    for f in b.GetFootprints():
        for p in f.Pads():
            r = p.GetBoundingBox(); boxes.append((r.GetLeft(), r.GetTop(), r.GetRight(), r.GetBottom()))
        for g in f.GraphicalItems():
            if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.F_CrtYd) and g.GetClass() != "PCB_TEXT":
                _add_shape(boxes, g)
        for t in (f.Reference(), f.Value()):
            if t.IsVisible() and t.GetLayer() == pcbnew.F_SilkS:
                r = t.GetBoundingBox(); boxes.append((r.GetLeft(), r.GetTop(), r.GetRight(), r.GetBottom()))
    for d in b.GetDrawings():
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.Edge_Cuts) and d.GetClass() in ("PCB_TEXT", "PCB_SHAPE"):
            _add_shape(boxes, d)
    return boxes
def label_near(txt, f, size=0.9):
    """texto de silkscreen no primeiro lugar livre ao redor da peça `f` (sem tocar pads, silkscreen e outros textos)"""
    c = f.GetPosition(); cx, cy = tomm(c.x), tomm(c.y)
    t = silk_text(txt, cx, cy - 3.6, size)
    obs = occupied()
    m = mm(0.35)
    done = False
    cands = sorted(((dx * 1.0, dy * 1.0) for dx in range(-30, 31) for dy in range(-20, 21)), key=lambda p: (p[0] ** 2 + (1.6 * p[1]) ** 2))
    for dx, dy in cands:
        if abs(dx) < 2 and abs(dy) < 3.2:
            continue
        t.SetPosition(V(cx + dx, cy + dy))
        r = t.GetBoundingBox()
        if r.GetLeft() < bb_in[0] or r.GetTop() < bb_in[1] or r.GetRight() > bb_in[2] or r.GetBottom() > bb_in[3]:
            continue
        if not any(r.GetLeft() - m < o[2] and r.GetRight() + m > o[0] and r.GetTop() - m < o[3] and r.GetBottom() + m > o[1] for o in obs):
            done = True; break
    if not done:
        print("AVISO: sem lugar livre para", txt)
        t.SetPosition(V(cx, cy - 3.6))
for f in b.GetFootprints():
    v = f.GetValue()
    if v.startswith("LED") and f.GetReference() != "D1":
        f.Reference().SetVisible(False)
    elif v == "TRAVA 3,3 V" and not any(d.GetClass() == "PCB_TEXT" and d.GetText() == "TRAVA 3,3 V" for d in b.GetDrawings()):
        label_near("TRAVA 3,3 V", f, 0.8)          # J1 (D138): jumper que impede o 5 V
tb = b.GetTitleBlock()
for r_ in a.hide:
    b.FindFootprintByReference(r_).Reference().SetVisible(False)
moves = {m.split("=")[0]: tuple(float(v) for v in m.split("=")[1].split(",")) for m in a.move}
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT":
        continue
    t = d.GetText()
    if a.fusivel:
        pass
    elif t == "NÃO COLOQUE NEM RETIRE":
        d.SetText("TROQUE O CARTUCHO COM")
    elif t == "O CARTUCHO COM USB LIGADO":
        d.SetText("O USB DESLIGADO")
    m = re.search(r"v\.? ?\d+\.\d+\s+\d{4}-\d{2}-\d{2}", t)
    if m:
        d.SetText(re.sub(r"\d{4}-\d{2}-\d{2}", a.date, t))
    for key, (x, y) in moves.items():
        if t.startswith(key):
            d.SetPosition(V(x, y))
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
