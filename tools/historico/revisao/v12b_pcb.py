#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v. 1.2 final (D108), parte 2: leva o esquematico novo (v12b_sch.py) para o PCB.
Cria as nets, liga os pads pela netlist, adiciona as pecas novas (resistores serie, TVS, pull-up, chave de 5V, LED, reset, 3 furos M3
alinhados com o Mega), desloca U2/C4/C6/TPs, apaga trilhas e zonas (o roteamento e refeito por v12b_route.py).
Uso (Python do venv do KiCad MCP): python v12b_pcb.py boards/16_bits/hardware"""
import re, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1])
sys.path.insert(0, str(Path(__file__).resolve().parent))
from schlib import placed, lib_symbols
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
SHEET = "7a60289e-82cc-4290-bd86-3bc08aff2373"
FPDIR = "/usr/share/kicad/footprints"

b = pcbnew.LoadBoard(str(HW / "dumper.kicad_pcb"))
if b.FindFootprintByReference("R3") is not None:
    sys.exit("ja aplicado")
sch = (HW / "dumper.kicad_sch").read_text()
uu = {p['ref']: p['uuid'] for p in placed(sch)}

# ------------------------------------------------------------ netlist
xml = "/tmp/v12b.xml"
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, str(HW / "dumper.kicad_sch")], check=True, capture_output=True)
root = ET.parse(xml).getroot()
comps = {c.get("ref"): (c.findtext("value"), (c.findtext("footprint") or "")) for c in root.iter("comp")}
nets = {}
for n in root.iter("net"):
    nets[n.get("name")] = [(x.get("ref"), x.get("pin")) for x in n.iter("node")]

# ------------------------------------------------------------ pecas novas
CTRL = ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D14", "D15", "D16", "D17"]
XCOL = {"D9": 59.1, "D8": 61.7, "D7": 65.7, "D6": 68.3, "D5": 70.8, "D4": 73.3, "D3": 75.9, "D2": 78.4,
        "D14": 88.6, "D15": 91.1, "D16": 93.7, "D17": 96.2}
Y_R1, Y_D1 = 56.9, 51.82      # pad 1 do resistor (lado do Mega) e pad 1 (K) do TVS; os pads 2 ficam 2,54 mm acima


def add_fp(ref, x, y, rot, show_ref=True):
    val, fpid = comps[ref]
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad("%s/%s.pretty" % (FPDIR, lib), name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.SetPosition(V(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.Reference().SetVisible(show_ref)
    fp.SetPath(pcbnew.KIID_PATH("/%s/%s" % (SHEET, uu[ref])))
    if ref in ["D%d" % k for k in range(3, 15)] + ["R15"]:
        fp.SetDNP(True)
    if ref in ["D%d" % k for k in range(3, 15)] + ["R%d" % k for k in range(3, 15)]:
        for g in fp.GraphicalItems():            # nas colunas de 2,54 mm o silk de uma peca encosta nos pads da vizinha
            if g.GetLayer() == pcbnew.F_SilkS:
                g.SetLayer(pcbnew.F_Fab)
    b.Add(fp)
    return fp


for k, n in enumerate(CTRL):
    x = XCOL[n]
    add_fp("R%d" % (3 + k), x, Y_R1, 90, False)
    add_fp("D%d" % (3 + k), x, Y_D1, 90, False)
# R15 (pull-up de /VRES, DNP), na coluna do D17 mais a esquerda do bloco: logo abaixo do PIC antigo
add_fp("R15", 85.5, 56.9, 90)
# bloco da chave de 5V no canto de cima a direita
add_fp("Q1", 119.5, 53.0, 270)
add_fp("R16", 112.2, 56.5, 90)
add_fp("R17", 114.74, 56.5, 90)
add_fp("R18", 112.2, 51.0, 90)
add_fp("D2", 115.5, 46.2, 90)
add_fp("SW1", 22.75, 99.25, 0)
for i, (x, y) in enumerate(((35.24, 60.2), (110.17, 60.2), (33.97, 108.46))):
    fp = pcbnew.FootprintLoad("%s/MountingHole.pretty" % FPDIR, "MountingHole_3.2mm_M3")
    fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
    fp.SetReference("MH%d" % (5 + i)); fp.SetValue("MountingHole_3.2mm")
    fp.SetPosition(V(x, y)); fp.Reference().SetVisible(False)
    b.Add(fp)

# ------------------------------------------------------------ deslocamentos
b.FindFootprintByReference("U2").SetPosition(V(102.0, 46.0))
b.FindFootprintByReference("C4").SetPosition(V(102.0, 43.5))
c6 = b.FindFootprintByReference("C6")
c6.SetPosition(V(36.9, 111.05))
tps = ["TP6", "TP3", "TP1", "TP2", "TP4", "TP5"]       # ordem atual da fileira (x crescente)
tp0 = b.FindFootprintByReference("TP6").GetPosition()
dx, dy = mm(40.1) - tp0.x, mm(56.6) - tp0.y
for r in tps:
    f = b.FindFootprintByReference(r)
    f.SetPosition(pcbnew.VECTOR2I(f.GetX() + dx, f.GetY() + dy))
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetText() in ("/UWR", "/CE", "5V", "GND", "/OE", "/WE") and d.GetLayer() == pcbnew.F_SilkS:
        d.SetPosition(pcbnew.VECTOR2I(d.GetX() + dx, d.GetY() + dy))

# creditos do verso (espelhados) para uma faixa sem pads; rotulo do PIC; textos de aviso
for d in b.GetDrawings():
    if d.GetClass() != "PCB_TEXT":
        continue
    t = d.GetText()
    if d.GetLayer() == pcbnew.B_SilkS:
        y = {"Adaptado": 79.5, "Baseado": 81.7, "Projeto": 83.9}
        for k, v in y.items():
            if t.startswith(k):
                d.SetPosition(V(60.5, v))
    elif t == "PIC EM SOQUETE":
        d.SetPosition(V(105.5, 58.2))
    elif t in ("UM CARTUCHO POR VEZ", "NÃO COLOQUE NEM RETIRE", "O CARTUCHO COM USB LIGADO"):
        d.SetPosition(V(58.0, d.GetY() / 1e6))
    elif t.startswith("SNES / MEGA DRIVE"):
        d.SetPosition(V(60.0, d.GetY() / 1e6))
for txt, x, y in (("SÉRIE 0R (R3-R14)", 70.0, 58.9), ("TVS 5V: NÃO MONTAR (D3-D14)", 70.0, 43.4)):
    t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(x, y)); t.SetTextSize(V(1, 1)); t.SetTextThickness(mm(0.15))
    b.Add(t)

# ------------------------------------------------------------ nets e pads pela netlist
have = {n for n in b.GetNetsByName()}
for name in nets:
    nm = name
    if b.FindNet(nm) is None:
        b.Add(pcbnew.NETINFO_ITEM(b, nm))
for p in b.GetPads():
    p.SetNet(b.FindNet("")) if False else None
nrp = 0
for name, nodes in nets.items():
    ni = b.FindNet(name)
    for ref, pin in nodes:
        f = b.FindFootprintByReference(ref)
        if f is None:
            continue
        for p in f.Pads():
            if p.GetNumber() == pin:
                if name.startswith('unconnected-') and p.GetNetname().startswith('unconnected-'):
                    continue
                p.SetNet(ni)
                nrp += 1
print("pads ligados:", nrp)

# ------------------------------------------------------------ limpa trilhas e zonas
for t in list(b.GetTracks()):
    b.RemoveNative(t)
for z in list(b.Zones()):
    b.RemoveNative(z)
pcbnew.SaveBoard(str(HW / "dumper.kicad_pcb"), b)
print("ok")
