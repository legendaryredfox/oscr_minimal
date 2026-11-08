#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v. 1.2 (D107): move o C4 (100 nF do PIC) para junto do PIC. Estava a 21,7 mm do VDD (pino 1) e 20 mm do GND (pino 8);
vai para (92; 43,5)-(97; 43,5), a 2,5 mm do pino 1, com o GND pela zona de cobre que passa junto ao pino 8.
O pad antigo do C4 era também a passagem do 5V e do GND entre as camadas: no lugar dele entram duas vias.
Uso (Python com pcbnew): PYTHONPATH=/usr/lib/python3/dist-packages python3 tools/historico/revisao/v12_c4.py"""
import pcbnew
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
path = __file__.rsplit("/tools/", 1)[0] + "/boards/16_bits/hardware-v1.3/dumper.kicad_pcb"
b = pcbnew.LoadBoard(path)
c4 = b.FindFootprintByReference("C4")
p1 = [p for p in c4.Pads() if p.GetNumber() == "1"][0]
p2 = [p for p in c4.Pads() if p.GetNumber() == "2"][0]
if abs(pcbnew.ToMM(c4.GetY()) - 43.5) < 0.01:
    raise SystemExit("C4 ja esta na posicao nova")
net5, netg = p1.GetNet(), p2.GetNet()
antigo5 = (pcbnew.ToMM(p1.GetX()), pcbnew.ToMM(p1.GetY()))
antigog = (pcbnew.ToMM(p2.GetX()), pcbnew.ToMM(p2.GetY()))
c4.SetPosition(V(92.0, 43.5))
# o rotulo do U2 ia para cima do pad 2 do C4: desce para a direita do soquete
b.FindFootprintByReference('U2').Reference().SetPosition(V(103.0, 52.0))

# o desenho do C4 (silk e patio) fica so acima do soquete: o corpo de 2,5 mm encosta no soquete por 0,2 mm e o DRC reclamaria
for g in list(c4.GraphicalItems()):
    if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.F_CrtYd):
        g.SetLayer(pcbnew.Dwgs_User)   # (Remove() derruba o pcbnew)
def seg(layer, a, c, w):
    s_ = pcbnew.PCB_SHAPE(c4); s_.SetShape(pcbnew.SHAPE_T_SEGMENT); s_.SetLayer(layer)
    s_.SetStart(V(*a)); s_.SetEnd(V(*c)); s_.SetWidth(mm(w)); c4.Add(s_)
for a, c in (((91.9, 44.2), (91.9, 42.5)), ((91.9, 42.5), (97.1, 42.5)), ((97.1, 42.5), (97.1, 44.2))):
    seg(pcbnew.F_SilkS, a, c, 0.12)
for a, c in (((91.5, 44.4), (91.5, 42.2)), ((91.5, 42.2), (97.5, 42.2)), ((97.5, 42.2), (97.5, 44.4)), ((97.5, 44.4), (91.5, 44.4))):
    seg(pcbnew.F_CrtYd, a, c, 0.05)
# vias no lugar dos pads antigos (passagem entre camadas)
for (x, y), net in ((antigo5, net5), (antigog, netg)):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)
# trilha do pad 1 (5V) ao pino 1 do PIC, na camada de cima
t = pcbnew.PCB_TRACK(b)
t.SetStart(V(92.0, 43.5)); t.SetEnd(V(92.0, 46.0)); t.SetLayer(pcbnew.F_Cu); t.SetWidth(mm(0.5)); t.SetNet(net5)
b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(path, b)
print("ok: C4 em (92; 43,5); vias em", antigo5, antigog)
