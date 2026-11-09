#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: troca o PTC soldado (F1, Bourns MF-RHT050) por um fusível de vidro 5x20 mm de 500 mA em suporte de clipes (Littelfuse série 100): o usuário
troca o fusível sem soldar (pedido do usuário). Esquemático: símbolo Device:Fuse, valor e footprint. PCB: o F1 antigo sai (e as trilhas que ficaram soltas nos
pads dele), o contorno cresce 10 mm para baixo e o suporte vai para a faixa nova; depois rode `route.py --incremental` para ligar os pads novos.
Uso (python do venv do KiCad MCP): python tools/troca/fusivel138.py boards/<placa>/hardware-<versão>"""
import math, re, sys
from pathlib import Path
import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sch"))
HW = Path(sys.argv[1])
EXT = 10.0                      # mm a mais na borda de baixo
LIB, NAME = "/usr/share/kicad/footprints/Fuse.pretty", "Fuseholder_Littelfuse_100_series_5x20mm"
VALOR = "Fusivel 5x20 500mA"
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))

# ------------------------------------------------------------------ esquemático
sp = HW / "dumper.kicad_sch"
s = sp.read_text()
if "Fuse:Fuse_Bourns_MF-RHT050" in s:
    from sexp import parse, dump, val, find
    s = s.replace("Fuse:Fuse_Bourns_MF-RHT050", "Fuse:" + NAME)
    s = s.replace('(property "Value" "PTC 0,5 A"', '(property "Value" "%s"' % VALOR)
    s = re.sub(r'Fusivel rearmavel \(PTC\)[^"]*', "Fusivel de vidro 5x20 mm de 500 mA (rapido) em suporte de clipes: troca sem solda. Queda de 0,1 a 0,2 V a 200 mA", s)
    # símbolo: Device:Fuse no lugar do Polyfuse (mesmos pinos 1 e 2)
    t = parse(Path("/usr/share/kicad/symbols/Device.kicad_sym").read_text())
    blk = [c for c in t[1:] if isinstance(c, list) and c and val(c[0]) == "symbol" and val(c[1]) == "Fuse"][0]
    s = s.replace('(lib_id "Device:Polyfuse")', '(lib_id "Device:Fuse")')
    tree = parse(s)
    libs = find(tree, "lib_symbols")[0]
    if not any(isinstance(c, list) and c and val(c[0]) == "symbol" and val(c[1]) == "Device:Fuse" for c in libs[1:]):
        libs.append(parse(dump(blk).replace('(symbol "Fuse"', '(symbol "Device:Fuse"', 1)))
    out = "(kicad_sch\n"
    for c in tree[1:]:
        out += "\t" + dump(c, 1) + "\n"
    out += ")\n"
    sp.write_text(out)
    print("esquemático:", HW, "F1 agora", NAME)

# ------------------------------------------------------------------ PCB
pp = str(HW / "dumper.kicad_pcb")
b = pcbnew.LoadBoard(pp)
old = b.FindFootprintByReference("F1")
if old is None:
    sys.exit("sem F1")
def liga_clipes(board, f):
    """As duas pernas de cada clipe do suporte (pads de mesmo número) são o mesmo nó: liga com uma trilha de 0,8 mm na face de baixo, se ainda não houver."""
    n = 0
    for num in ("1", "2"):
        ps = [p for p in f.Pads() if p.GetNumber() == num]
        if len(ps) != 2:
            continue
        a, b_ = ps[0].GetPosition(), ps[1].GetPosition()
        if any(t.GetClass() != "PCB_VIA" and t.GetLayer() == pcbnew.B_Cu and {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)} == {(a.x, a.y), (b_.x, b_.y)} for t in board.GetTracks()):
            continue
        t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(b_); t.SetLayer(pcbnew.B_Cu); t.SetWidth(mm(0.8)); t.SetNet(ps[0].GetNet())
        board.Add(t); n += 1
    return n


if str(old.GetFPID().GetLibItemName()) == NAME:
    n = liga_clipes(b, old)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(pp, b)
    print("já é o suporte de fusível; ligações entre as pernas dos clipes acrescentadas:", n); sys.exit(0)
nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
path = old.GetPath()
pads_old = [(p.GetPosition().x, p.GetPosition().y, p.GetNetname()) for p in old.Pads()]
b.RemoveNative(old)

# trilhas que ficaram com a ponta solta no pad do F1 antigo
sys.path.insert(0, str(Path(__file__).resolve().parent))
from poda138 import poda
print("trilhas soltas podadas:", poda(b))

# borda de baixo +EXT mm e furos de canto
bb = b.GetBoardEdgesBoundingBox(); y1 = bb.GetBottom(); x0, x1 = bb.GetLeft(), bb.GetRight()
for d in b.GetDrawings():
    if d.GetLayer() != pcbnew.Edge_Cuts:
        continue
    for get, setp in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
        p = get()
        if abs(p.y - y1) < mm(0.2):
            setp(pcbnew.VECTOR2I(p.x, p.y + mm(EXT)))
for f in b.GetFootprints():
    if f.GetReference().startswith("MH") and abs(f.GetPosition().y - y1) < mm(8):
        p = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(p.x, p.y + mm(EXT)))

# suporte novo na faixa: encostado à esquerda (depois do furo de canto), centrado na altura da faixa
fp = pcbnew.FootprintLoad(LIB, NAME)
fp.SetFPID(pcbnew.LIB_ID("Fuse", NAME)); fp.SetReference("F1"); fp.SetValue(VALOR); fp.SetPath(path)
fp.Reference().SetVisible(True)
fp.Value().SetVisible(False)
b.Add(fp)
cx = tomm(x0) + 30.0
cy = tomm(y1) + EXT / 2
fp.SetPosition(V(cx, cy))
r = fp.GetBoundingBox(False)
# o corpo fica centrado na altura da faixa; o pino 1 mais à esquerda a 18 mm da borda esquerda (longe do furo de canto)
dy = (r.GetTop() + r.GetBottom()) / 2 - fp.GetPosition().y
padx = min(p.GetPosition().x for p in fp.Pads())
fp.SetPosition(pcbnew.VECTOR2I(int(fp.GetPosition().x + (x0 + mm(18.0) - padx)), int(mm(cy) - dy)))
for p in fp.Pads():
    n = nets.get(p.GetNumber())
    if n is not None:
        p.SetNet(n)
# texto de silkscreen
t = pcbnew.PCB_TEXT(b); t.SetText("FUSIVEL 5x20 500 mA"); t.SetLayer(pcbnew.F_SilkS)
t.SetPosition(V(tomm(fp.GetPosition().x) + 10.0, tomm(y1) + EXT / 2 - 4.2)); t.SetTextSize(V(1.0, 1.0)); t.SetTextThickness(mm(0.15)); b.Add(t)
liga_clipes(b, fp)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(pp, b)
print("pcb:", HW, "suporte do fusível em (%.1f, %.1f); borda de baixo +%.0f mm" % (cx, cy, EXT))
