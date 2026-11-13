#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Acrescenta ao PCB da completa o slot N64_1 (dumper:N64_Slot) e o capacitor C11 (3,3 V), abaixo do slot SMS, e liga os pads às nets do esquemático
(os pinos do Mega que só o N64 usa já têm net pelos outros slots). Roda depois de place_sms.py e antes de place_seletor.py (D156).
Uso (python com pcbnew): python tools/boards/completa/place_n64.py boards/completa/hardware-v1.0"""
import re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1]).resolve()
ROOT = HW.parents[2]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(str(HW / "dumper.kicad_pcb"))
if b.FindFootprintByReference("N64_1") is not None:
    print("N64_1 já existe"); sys.exit(0)
with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(HW / "dumper.kicad_sch")], check=True, capture_output=True)
    nl = ET.parse(out).getroot()
padnet = {}
for n in nl.find("nets"):
    for x in n:
        if x.get("ref") in ("N64_1", "C11", "A1"):
            padnet[(x.get("ref"), x.get("pin"))] = n.get("name")
sch = (HW / "dumper.kicad_sch").read_text()
root_uuid = re.search(r"\(uuid ([0-9a-f-]{36})\)", sch).group(1)
def sym_uuid(ref):
    i = sch.index(f'(reference "{ref}")'); j = sch.rfind("\n\t(symbol\n", 0, i)
    return re.search(r'\(uuid "([0-9a-f-]{36})"\)', sch[j:i]).group(1)
def net(nm):
    ni = b.FindNet(nm)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
    return ni
def setnets(f, ref):
    for p in f.Pads():
        nm = padnet.get((ref, p.GetNumber()))
        if nm and not nm.startswith("unconnected"): p.SetNet(net(nm))
mega = b.FindFootprintByReference("A1")
for (ref, pin), nm in padnet.items():
    if ref == "A1" and not nm.startswith("unconnected"):
        p = mega.FindPadByNumber(pin)
        if p.GetNetname() != nm: p.SetNet(net(nm))
NX, NY = 104.0, 160.0
f = pcbnew.FootprintLoad(str(ROOT / "boards/_lib/dumper.pretty"), "N64_Slot")
f.SetReference("N64_1"); f.SetValue("N64_Slot"); f.SetFPID(pcbnew.LIB_ID("dumper", "N64_Slot"))
f.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid('N64_1')}"))
b.Add(f); setnets(f, "N64_1"); f.SetOrientationDegrees(0); f.SetPosition(V(NX, NY))
pads = [p.GetPosition() for p in f.Pads()]
cx = sum(p.x for p in pads) / len(pads); cy = sum(p.y for p in pads) / len(pads)
f.Move(pcbnew.VECTOR2I(mm(NX) - int(cx), mm(NY) - int(cy)))
c6 = b.FindFootprintByReference("C6")
c = pcbnew.Cast_to_FOOTPRINT(c6.Duplicate(False)); c.SetReference("C11"); c.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid('C11')}"))
b.Add(c); setnets(c, "C11"); c.SetPosition(V(147.0, 160.0))
for dr in b.GetDrawings():
    if dr.GetClass() == "PCB_TEXT" and dr.GetText().startswith("COMPLETA:"):
        dr.SetText("COMPLETA: SNES NES FAMICOM MEGA DRIVE MASTER SYSTEM N64 GBA   " + ("v1.1" if HW.name.endswith("v1.1") else "v1.0") + "   2026-11-11")
t = pcbnew.PCB_TEXT(b); t.SetText("N64: 3,3 V"); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(104.0, 155.4))
t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0))); t.SetTextThickness(mm(0.15)); b.Add(t)
bb = f.GetBoundingBox(False, False)
print("N64_1:", [round(pcbnew.ToMM(v), 1) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom())])
pcbnew.SaveBoard(str(HW / "dumper.kicad_pcb"), b)
print("ok")
