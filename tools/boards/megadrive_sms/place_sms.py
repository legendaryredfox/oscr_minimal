#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepara o PCB da megadrive_sms a partir da cópia do PCB da megadrive v1.0: tira trilhas e zonas, estende a placa para
baixo, põe SMS1 (dumper:SMS_Slot) e C5, ajusta os textos. Depois: autoroute (Freerouting), add_zones.py etc.
Uso (python do sistema, com pcbnew): /usr/bin/python3 -I tools/boards/megadrive_sms/place_sms.py boards/megadrive_sms/hardware-v1.0
Precisa de dumper.kicad_sch já com SMS1 e C5 (add_sms_sch.py). Roda uma vez sobre a cópia da megadrive."""
import re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1]).resolve()
ROOT = HW.parents[2]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.LoadBoard(str(HW / "dumper.kicad_pcb"))
if b.FindFootprintByReference("SMS1") is not None:
    print("SMS1 já existe"); sys.exit(0)

# netlist do esquemático = fonte dos nomes de net dos pads novos
with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(HW / "dumper.kicad_sch")],
                   check=True, capture_output=True)
    nl = ET.parse(out).getroot()
padnet = {}
for n in nl.find("nets"):
    for x in n:
        if x.get("ref") in ("SMS1", "C5"):
            padnet[(x.get("ref"), x.get("pin"))] = n.get("name")
sch = (HW / "dumper.kicad_sch").read_text()
root_uuid = re.search(r"\(uuid ([0-9a-f-]{36})\)", sch).group(1)
def sym_uuid(ref):
    i = sch.index(f'(reference "{ref}")'); j = sch.rfind("\n\t(symbol\n", 0, i)
    return re.search(r'\(uuid "([0-9a-f-]{36})"\)', sch[j:i]).group(1)

for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

# contorno: 107,1 x 85,1 mm (a megadrive tinha 65,1)
X0, Y0, X1, Y1 = 16.0, 52.0, 123.0, 135.0
for dr in list(b.GetDrawings()):
    if dr.GetLayer() == pcbnew.Edge_Cuts: b.RemoveNative(dr)
for a, c in (((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)

def setnets(f, ref):
    for p in f.Pads():
        nm = padnet.get((ref, p.GetNumber()))
        if nm and not nm.startswith("unconnected"):
            ni = b.FindNet(nm); assert ni is not None, nm
            p.SetNet(ni)

# SMS1
f = pcbnew.FootprintLoad(str(ROOT / "boards/_lib/dumper.pretty"), "SMS_Slot")
f.SetReference("SMS1"); f.SetValue("SMS_Slot"); f.SetFPID(pcbnew.LIB_ID("dumper", "SMS_Slot"))
f.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid('SMS1')}"))
b.Add(f); setnets(f, "SMS1")
f.SetOrientationDegrees(90); f.SetPosition(V(64, 125))
pads = [p.GetPosition() for p in f.Pads()]
cx = sum(p.x for p in pads) / len(pads); cy = sum(p.y for p in pads) / len(pads)
f.Move(pcbnew.VECTOR2I(mm(64) - int(cx), mm(125) - int(cy)))
p1 = f.FindPadByNumber("1").GetPosition()
print("SMS1 pino 1 em", pcbnew.ToMM(p1.x), pcbnew.ToMM(p1.y))

# C5: cópia do C2
c2 = b.FindFootprintByReference("C2")
c5 = pcbnew.Cast_to_FOOTPRINT(c2.Duplicate(False)); c5.SetReference("C5"); c5.SetPath(pcbnew.KIID_PATH(f"/{root_uuid}/{sym_uuid('C5')}"))
b.Add(c5); setnets(c5, "C5")
c5.SetPosition(V(106.0, 122.0))

# furos de pé M3 nos cantos de baixo
for ref, (x, y) in (("MH5", (19.0, 132.0)), ("MH6", (120.0, 132.0))):
    h = pcbnew.Cast_to_FOOTPRINT(b.FindFootprintByReference("MH3").Duplicate(False)); h.SetReference(ref); b.Add(h); h.SetPosition(V(x, y))

# textos
for dr in list(b.GetDrawings()):
    if dr.GetClass() != "PCB_TEXT": continue
    t = dr.GetText()
    if t.startswith("MEGA DRIVE   v"):
        dr.SetText("MEGA DRIVE + MASTER SYSTEM   v1.0   2026-11-08"); dr.SetPosition(V(64.0, 103.0))
def addtext(txt, x, y, h):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(h * 0.15)); b.Add(t)
addtext("UM CARTUCHO POR VEZ", 64.0, 105.8, 1.25)
pcbnew.SaveBoard(str(HW / "dumper.kicad_pcb"), b)
print("ok")
