#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Acrescenta ao PCB da completa v1.1 as peças do seletor de tensão (U4, Q1, Q2, R3, R4, R5, C12, C13, J1), copiadas do PCB da 8_bits v1.1
(U2, Q1, Q2, R2, R3, R4, C5, C6, J1), numa fileira abaixo do slot SMS, e liga os pads às nets do esquemático; troca para VCC_CART os pads de
VCC dos slots NES, Famicom, Mega Drive e SMS e dos capacitores C3, C4, C5 e C10. Roda depois de place_sms.py.
Uso (python com pcbnew): python tools/boards/completa/place_seletor.py boards/completa/hardware-v1.1"""
import re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1]).resolve()
ROOT = HW.parents[2]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(str(HW / "dumper.kicad_pcb"))
if b.FindFootprintByReference("U4") is not None:
    print("seletor já existe"); sys.exit(0)
don = pcbnew.LoadBoard(str(ROOT / "boards/8_bits/hardware-v1.1/dumper.kicad_pcb"))
with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(HW / "dumper.kicad_sch")], check=True, capture_output=True)
    nl = ET.parse(out).getroot()
padnet = {}
for n in nl.find("nets"):
    for x in n:
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
# nova ref -> (ref no doador, x, y)
Y = 177.5
PARTS = {"U4": ("U2", 40.0, Y), "Q1": ("Q1", 58.0, Y), "Q2": ("Q2", 74.0, Y), "C12": ("C5", 88.0, Y), "C13": ("C6", 100.0, Y),
         "R3": ("R2", 112.0, Y), "R4": ("R3", 122.0, Y), "R5": ("R4", 132.0, Y), "J1": ("J1", 148.0, Y)}
for new, (old, x, y) in PARTS.items():
    f = pcbnew.Cast_to_FOOTPRINT(don.FindFootprintByReference(old).Duplicate(False))
    f.SetReference(new)
    f.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid(new)}"))
    b.Add(f); f.SetPosition(V(x, y)); f.SetOrientationDegrees(0)
    for p in f.Pads():
        nm = padnet.get((new, p.GetNumber()))
        if nm and not nm.startswith("unconnected"): p.SetNet(net(nm))
# pads que passam de +5V_CART para VCC_CART (slots e capacitores)
for f in b.GetFootprints():
    for p in f.Pads():
        nm = padnet.get((f.GetReference(), p.GetNumber()))
        if nm and nm != p.GetNetname().lstrip("/") and nm != p.GetNetname() and "VCC_CART" in nm:
            p.SetNet(net(nm))
# Mega D18 = VSEL_EN
m = b.FindFootprintByReference("A1"); m.FindPadByNumber("D18").SetNet(net(padnet[("A1", "D18")]))
t = pcbnew.PCB_TEXT(b); t.SetText("TRAVA 3,3 V"); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(148.0, Y - 5.0))
t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0))); t.SetTextThickness(mm(0.15)); b.Add(t)
pcbnew.SaveBoard(str(HW / "dumper.kicad_pcb"), b)
print("ok:", ", ".join(PARTS))
