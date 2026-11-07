#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bloco de troca de cartucho (D126), PCB. Depois de tools/troca/sch_block.py: cria as peças novas e as nets, liga os pads pela netlist,
acha para cada peça nova um lugar livre (busca em espiral a partir de uma âncora, sem tocar pads, furos nem a área do slot),
apaga trilhas, vias e zonas (o roteamento é refeito por tools/troca/route.py) e atualiza versão e avisos do silkscreen.
Uso (Python do venv do KiCad MCP): python pcb_block.py boards/<placa>/hardware <versão> <x_ancora> <y_ancora> [x0 y0 x1 y1 da região permitida]"""
import math, re, subprocess, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1]); VERSAO = sys.argv[2]
AX, AY = float(sys.argv[3]), float(sys.argv[4])
REGION = [float(v) for v in sys.argv[5:9]] if len(sys.argv) >= 9 else None
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "revisao"))
from schlib import placed
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
FPDIR = "/usr/share/kicad/footprints"

b = pcbnew.LoadBoard(str(HW / "dumper.kicad_pcb"))
sch = (HW / "dumper.kicad_sch").read_text()
SHEET = re.search(r'\(path "/([0-9a-f-]+)"', sch).group(1)
uu = {p['ref']: p['uuid'] for p in placed(sch)}
with tempfile.TemporaryDirectory() as t:
    xml = str(Path(t) / "n.xml")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, str(HW / "dumper.kicad_sch")], check=True, capture_output=True)
    root = ET.parse(xml).getroot()
comps = {c.get("ref"): (c.findtext("value"), c.findtext("footprint") or "") for c in root.iter("comp")}
nets = {n.get("name"): [(x.get("ref"), x.get("pin")) for x in n.iter("node")] for n in root.iter("net")}
novos = [r for r in comps if b.FindFootprintByReference(r) is None and not comps[r][1] == ""]
if not novos:
    sys.exit("nada a acrescentar (já aplicado?)")
print("peças novas:", novos)

# ------------------------------------------------------------ peças novas
for ref in novos:
    val, fpid = comps[ref]
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad("%s/%s.pretty" % (FPDIR, lib), name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name)); fp.SetReference(ref); fp.SetValue(val)
    fp.SetPath(pcbnew.KIID_PATH("/%s/%s" % (SHEET, uu[ref])))
    fp.Reference().SetVisible(not ref.startswith("R"))
    fp.Value().SetVisible(False)
    for g in fp.GraphicalItems():
        pass
    b.Add(fp)

# ------------------------------------------------------------ nets
for name in nets:
    if b.FindNet(name) is None:
        b.Add(pcbnew.NETINFO_ITEM(b, name))
n_pads = 0
for name, nodes in nets.items():
    ni = b.FindNet(name)
    for ref, pin in nodes:
        f = b.FindFootprintByReference(ref)
        if f is None:
            continue
        for p in f.Pads():
            if p.GetNumber() == pin:
                if name.startswith("unconnected-") and p.GetNetname().startswith("unconnected-"):
                    continue
                p.SetNet(ni); n_pads += 1
print("pads ligados:", n_pads)
# pads de peças novas e antigas que ficaram em nets que deixaram de existir
for t in list(b.GetTracks()):
    b.RemoveNative(t)
for z in list(b.Zones()):
    b.RemoveNative(z)

# ------------------------------------------------------------ posição das peças novas
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = (tomm(bb.GetLeft()) + 2.5, tomm(bb.GetTop()) + 2.5, tomm(bb.GetRight()) - 2.5, tomm(bb.GetBottom()) - 2.5)
if REGION:
    x0, y0, x1, y1 = REGION
OBST = []     # (x0, y0, x1, y1) em mm, com folga
def pad_boxes(f, margin):
    """caixa dos pads de uma peça existente; para peças novas, o retângulo da peça inteira (corpo e pads) com folga"""
    out = []
    if f.GetReference() in novos:
        r = f.GetBoundingBox(False)
        return [(tomm(r.GetLeft()) - margin, tomm(r.GetTop()) - margin, tomm(r.GetRight()) + margin, tomm(r.GetBottom()) + margin)]
    for p in f.Pads():
        r = p.GetBoundingBox()
        out.append((tomm(r.GetLeft()) - margin, tomm(r.GetTop()) - margin, tomm(r.GetRight()) + margin, tomm(r.GetBottom()) + margin))
    return out
for f in b.GetFootprints():
    ref = f.GetReference()
    if ref in novos:
        continue
    if ref.startswith("MH"):
        c = f.GetPosition(); cx, cy = tomm(c.x), tomm(c.y)
        OBST.append((cx - 4.2, cy - 4.2, cx + 4.2, cy + 4.2))
    elif ref.startswith(("SNES", "MD", "NES", "FC", "N64", "GBA", "GB", "SMS")) and str(f.GetFPID().GetLibItemName()).endswith("Slot"):
        r = f.GetBoundingBox(False)
        OBST.append((tomm(r.GetLeft()) - 1.5, tomm(r.GetTop()) - 1.5, tomm(r.GetRight()) + 1.5, tomm(r.GetBottom()) + 1.5))
    else:
        OBST += pad_boxes(f, 1.0)
        if ref == "A1":
            pass
def hit(box):
    for o in OBST:
        if box[0] < o[2] and box[2] > o[0] and box[1] < o[3] and box[3] > o[1]:
            return True
    return False
def boxes_at(f, x, y):
    c = f.GetPosition(); dx, dy = x - tomm(c.x), y - tomm(c.y)
    return [(bx0 + dx, by0 + dy, bx1 + dx, by1 + dy) for bx0, by0, bx1, by1 in pad_boxes(f, 0.6)]
ORDER = [r for r in novos if r.startswith("Q")] + [r for r in novos if r.startswith("D")] + [r for r in novos if r.startswith("R")]
# peças ligadas pelas mesmas nets pequenas ficam juntas: a âncora de cada peça é a média das já postas que dividem uma net com até 6 nós
small = [set(r for r, _ in nodes) for n, nodes in nets.items() if 2 <= len(nodes) <= 6 and not n.startswith(("GND", "+"))]
placed_pos = {}
for ref in ORDER:
    mates = [placed_pos[o] for sset in small if ref in sset for o in sset if o in placed_pos]
    ax_, ay_ = (sum(p[0] for p in mates) / len(mates), sum(p[1] for p in mates) / len(mates)) if mates else (AX, AY)
    f = b.FindFootprintByReference(ref)
    f.SetPosition(V(0, 0))
    ok = False
    for rot in (0, 90):
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(0, 0))
        # candidatos em espiral (passo 1,27 mm) ordenados pela distância à âncora
        cand = sorted(((ax_ + i * 1.27, ay_ + j * 1.27) for i in range(-60, 61) for j in range(-40, 41)), key=lambda p: math.hypot(p[0] - ax_, p[1] - ay_))
        for x, y in cand:
            bx = boxes_at(f, x, y)
            if any(b_[0] < x0 or b_[1] < y0 or b_[2] > x1 or b_[3] > y1 for b_ in bx):
                continue
            if any(hit(bb_) for bb_ in bx):
                continue
            f.SetPosition(V(x, y)); OBST.extend(bx); ok = True; placed_pos[ref] = (x, y); break
        if ok:
            break
    if not ok:
        sys.exit("sem lugar para %s" % ref)
    c = f.GetPosition(); print("  %s em (%.2f, %.2f) rot %d" % (ref, tomm(c.x), tomm(c.y), f.GetOrientationDegrees()))

# ------------------------------------------------------------ versão e avisos do silkscreen
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT":
        t = d.GetText()
        m = re.search(r"v\d+\.\d+", t)
        if m and "   " in t:
            d.SetText(t[:m.start()] + VERSAO + t[m.end():])
tb = b.GetTitleBlock(); tb.SetRevision(VERSAO); b.SetTitleBlock(tb)
pcbnew.SaveBoard(str(HW / "dumper.kicad_pcb"), b)
print("ok")
