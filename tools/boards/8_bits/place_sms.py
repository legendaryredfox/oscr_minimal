#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da 8_bits v1.0 a partir da cópia do PCB da famicom_nes v1.0: tira trilhas e zonas, estende a placa para baixo
(y de 127 para 135 mm), põe SMS1 (dumper:SMS_Slot) e C4, dá aos pads do Mega que só o SMS usa as nets novas (o PCB da famicom_nes
as tinha sem ligação) e ajusta os textos. Depois: Freerouting, add_zones.py etc. (tools/boards/8_bits/reroute.sh).
Uso (python com pcbnew): python tools/boards/8_bits/place_sms.py boards/8_bits/hardware-v1.0
Precisa de dumper.kicad_sch já com SMS1 e C4 (add_sms_sch.py). Roda uma vez sobre a cópia da famicom_nes."""
import os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1]).resolve()
V11 = HW.name.endswith("v1.1")     # v1.1: a placa da famicom_nes v1.1 já é alta (147 mm, seletor e F1 embaixo): só entra o SMS; capacitor novo = C6 (renumerado depois)
CAP = "C6" if V11 else "C4"
ROOT = HW.parents[2]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(str(HW / "dumper.kicad_pcb"))
if b.FindFootprintByReference("SMS1") is not None:
    print("SMS1 já existe"); sys.exit(0)

with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(HW / "dumper.kicad_sch")],
                   check=True, capture_output=True)
    nl = ET.parse(out).getroot()
padnet = {}
for n in nl.find("nets"):
    for x in n:
        if x.get("ref") in ("SMS1", CAP, "A1"):
            padnet[(x.get("ref"), x.get("pin"))] = n.get("name")
sch = (HW / "dumper.kicad_sch").read_text()
root_uuid = re.search(r"\(uuid ([0-9a-f-]{36})\)", sch).group(1)
def sym_uuid(ref):
    i = sch.index(f'(reference "{ref}")'); j = sch.rfind("\n\t(symbol\n", 0, i)
    return re.search(r'\(uuid "([0-9a-f-]{36})"\)', sch[j:i]).group(1)

for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

def net(nm):
    ni = b.FindNet(nm)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
    return ni

# contorno: 117,1 x 97,1 mm (a famicom_nes tinha 89,1 de altura)
X0, Y0, X1, Y1 = 6.0, 38.0, 123.0, 135.0
for dr in ([] if V11 else list(b.GetDrawings())):
    if dr.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(dr)
for a, c in (() if V11 else (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0)))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)

def setnets(f, ref):
    for p in f.Pads():
        nm = padnet.get((ref, p.GetNumber()))
        if nm and not nm.startswith("unconnected"):
            p.SetNet(net(nm))

# pads do Mega que só o SMS usa
mega = b.FindFootprintByReference("A1")
for (ref, pin), nm in padnet.items():
    if ref == "A1" and not nm.startswith("unconnected"):
        p = mega.FindPadByNumber(pin)
        if p.GetNetname() != nm: p.SetNet(net(nm))

# SMS1 (mesma posição relativa da megadrive_sms: de lado, abaixo da fileira de baixo do Mega)
SX, SY = (82.0, 138.0) if V11 else (83.0, 125.0)
f = pcbnew.FootprintLoad(str(ROOT / "boards/_lib/dumper.pretty"), "SMS_Slot")
f.SetReference("SMS1"); f.SetValue("SMS_Slot"); f.SetFPID(pcbnew.LIB_ID("dumper", "SMS_Slot"))
f.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid('SMS1')}"))
b.Add(f); setnets(f, "SMS1")
f.SetOrientationDegrees(90); f.SetPosition(V(SX, SY))
pads = [p.GetPosition() for p in f.Pads()]
cx = sum(p.x for p in pads) / len(pads); cy = sum(p.y for p in pads) / len(pads)
f.Move(pcbnew.VECTOR2I(mm(SX) - int(cx), mm(SY) - int(cy)))
p1 = f.FindPadByNumber("1").GetPosition()
print("SMS1 pino 1 em", pcbnew.ToMM(p1.x), pcbnew.ToMM(p1.y))

# C4: cópia do C3 (capacitor do 5V do Famicom), junto ao 5V do slot SMS
c3 = b.FindFootprintByReference("C3")
c4 = pcbnew.Cast_to_FOOTPRINT(c3.Duplicate(False)); c4.SetReference(CAP); c4.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid(CAP)}"))
b.Add(c4); setnets(c4, CAP)
c4.SetPosition(V(112.0, 128.5) if V11 else V(112.0, 115.3))

# furos de pé dos cantos de baixo descem para a borda nova
for ref, (x, y) in (() if V11 else (("MH3", (14.0, 132.0)), ("MH4", (120.0, 132.0)))):
    b.FindFootprintByReference(ref).SetPosition(V(x, y))

for dr in list(b.GetDrawings()):
    if dr.GetClass() != "PCB_TEXT": continue
    t = dr.GetText()
    if t.startswith("FAMICOM + NES   v"):
        dr.SetText("NES + FAMICOM + MASTER SYSTEM   " + ("v1.1" if V11 else "v1.0") + "   2026-11-11"); dr.SetPosition(V(64.0, 104.5))
pcbnew.SaveBoard(str(HW / "dumper.kicad_pcb"), b)
print("ok")
