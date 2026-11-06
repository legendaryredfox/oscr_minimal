#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Gera hardware/shield_uno.kicad_pcb a partir do esquematico (netlist do kicad-cli).

Faz: footprint do Uno, pecas posicionadas, nets, contorno, textos, furos. Nao roteia (ver rotear.py).
Uso (Python do venv do KiCad MCP, que tem o pcbnew), da raiz do repositorio:
  ~/development/llms/KiCAD-MCP-Server/.venv/bin/python tools/pic/shield_uno/scripts/gerar_pcb.py
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

AQUI = Path(__file__).resolve().parent.parent
HW = AQUI / "hardware"
FPLIB = Path("/usr/share/kicad/footprints")
mm = pcbnew.FromMM
X0, Y0 = 100.0, 80.0     # canto inferior esquerdo do Uno (coordenadas do PCB, y para baixo)
LARG, ALT = 68.58, 53.34
ESQ = 16.0               # a placa comeca aqui (x do Uno): deixa livres o USB-B e o jack do Uno

# ------------------------------------------------------------------ footprint do Uno
TOPO10 = [("SCL", 18.796), ("SDA", 21.336), ("AREF", 23.876), ("GND1", 26.416), ("D13", 28.956), ("D12", 31.496),
          ("D11", 34.036), ("D10", 36.576), ("D9", 39.116), ("D8", 41.656)]
TOPO8 = [("D7", 45.72), ("D6", 48.26), ("D5", 50.8), ("D4", 53.34), ("D3", 55.88), ("D2", 58.42), ("D1", 60.96), ("D0", 63.5)]
BASE_PWR = [("NC", 27.94), ("IORF", 30.48), ("RST1", 33.02), ("3V3", 35.56), ("5V1", 38.1), ("GND2", 40.64), ("GND3", 43.18), ("VIN", 45.72)]
BASE_AN = [("A0", 50.8), ("A1", 53.34), ("A2", 55.88), ("A3", 58.42), ("A4", 60.96), ("A5", 63.5)]
FUROS = [(66.04, 7.62), (66.04, 35.56)]


def escrever_footprint():
    L = ['(footprint "Uno_R3_Shield"', '\t(version 20260101)', '\t(generator "gerar_pcb.py")', '\t(generator_version "10.0")',
         '\t(layer "F.Cu")', '\t(descr "Headers do Arduino Uno R3 (cotas do Mega 2560 R3, parte compativel com o Uno). Origem: canto inferior esquerdo da placa do Uno.")',
         '\t(tags "arduino uno shield")', '\t(attr through_hole)']

    def txt(kind, s, x, y, layer, size=1.0, hide=False):
        return (f'\t(property "{kind}" "{s}"\n\t\t(at {x} {y} 0)\n\t\t(layer "{layer}")\n' + ("\t\t(hide yes)\n" if hide else "")
                + f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n')
    L.append(txt("Reference", "REF**", 40, 3, "F.SilkS").rstrip("\n"))
    L.append(txt("Value", "Uno_R3_Shield", 40, -3, "F.Fab").rstrip("\n"))
    L.append('\t(property "Datasheet" ""\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(hide yes)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)\n\t)')
    L.append('\t(property "Description" ""\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(hide yes)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t)\n\t)')
    # contorno da placa do Uno (so referencia, na camada Fab) e dos headers (serigrafia)
    L.append(f'\t(fp_rect\n\t\t(start 0 0)\n\t\t(end {LARG} {-ALT})\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type dash)\n\t\t)\n\t\t(fill no)\n\t\t(layer "F.Fab")\n\t)')
    for grupo, y in ((TOPO10, ALT - 2.54), (TOPO8, ALT - 2.54), (BASE_PWR, 2.54), (BASE_AN, 2.54)):
        x1, x2 = grupo[0][1] - 1.27, grupo[-1][1] + 1.27
        L.append(f'\t(fp_rect\n\t\t(start {x1:.3f} {-y - 1.27:.3f})\n\t\t(end {x2:.3f} {-y + 1.27:.3f})\n\t\t(stroke\n\t\t\t(width 0.12)\n\t\t\t(type default)\n\t\t)\n\t\t(fill no)\n\t\t(layer "F.SilkS")\n\t)')
    for grupo, y in ((TOPO10, ALT - 2.54), (TOPO8, ALT - 2.54), (BASE_PWR, 2.54), (BASE_AN, 2.54)):
        for nome, x in grupo:
            L.append(f'\t(pad "{nome}" thru_hole circle\n\t\t(at {x} {-y})\n\t\t(size 1.7272 1.7272)\n\t\t(drill 1.016)\n\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t)')
    for x, y in FUROS:
        L.append(f'\t(pad "" np_thru_hole circle\n\t\t(at {x} {-y})\n\t\t(size 3.2 3.2)\n\t\t(drill 3.2)\n\t\t(layers "*.Cu" "*.Mask")\n\t)')
    L.append(")")
    (HW / "uno_shield.pretty").mkdir(exist_ok=True)
    (HW / "uno_shield.pretty" / "Uno_R3_Shield.kicad_mod").write_text("\n".join(L) + "\n")


# ------------------------------------------------------------------ posicoes (xu, yu em mm no sistema do Uno, rotacao)
POS = {
    "A1": None,
    "J1": (19.5, 9.0, 0),
    "D1": (20.0, 21.0, 0),
    "R1": (20.0, 27.0, 0),
    "R4": (20.0, 33.0, 0),
    "D2": (34.5, 33.0, 0),
    "Q1": (35.0, 16.0, 0),
    "R2": (36.0, 11.0, 0),
    "C1": (40.0, 27.0, 90),
    "U2": (46.0, 22.0, 90),
    "J2": (60.0, 36.0, 0),
    "R3": (50.0, 8.0, 0),
    "D3": (62.0, 14.0, 0),
    "TP1": (24.0, 43.0, 0),
    "TP2": (28.0, 43.0, 0),
    "TP3": (32.0, 43.0, 0),
}


def netlist():
    xml = Path("/tmp/shield_uno_net.xml")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), str(HW / "shield_uno.kicad_sch")],
                   check=True, capture_output=True)
    r = ET.parse(xml).getroot()
    comps = {c.get("ref"): (c.findtext("footprint"), c.findtext("value")) for c in r.find("components")}
    nets = {n.get("name"): [(nd.get("ref"), nd.get("pin")) for nd in n.findall("node")] for n in r.find("nets")}
    return comps, nets


def vec(xu, yu):
    return pcbnew.VECTOR2I(mm(X0 + xu), mm(Y0 + ALT - yu))


def carregar(fpid):
    lib, nome = fpid.split(":")
    d = HW / (lib + ".pretty") if lib == "uno_shield" else FPLIB / (lib + ".pretty")
    fp = pcbnew.FootprintLoad(str(d), nome)
    if fp is not None:
        fp.SetFPID(pcbnew.LIB_ID(lib, nome))
    if fp is None:
        sys.exit("footprint nao encontrado: " + fpid)
    return fp


def linha(b, x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    b.Add(s)


def texto(b, s, xu, yu, tam=1.0, layer=pcbnew.F_SilkS, rot=0, espessura=0.15):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetPosition(vec(xu, yu))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(tam), mm(tam)))
    t.SetTextThickness(mm(espessura))
    t.SetTextAngleDegrees(rot)
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    b.Add(t)


def main():
    escrever_footprint()
    comps, nets = netlist()
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    b.GetTitleBlock().SetTitle("Programador de PIC12F629 - shield para Arduino Uno")
    b.GetTitleBlock().SetDate("2026-11-06")
    b.GetTitleBlock().SetRevision("v1.0")
    b.GetTitleBlock().SetComment(0, "Circuito: ardpicprog (R. Weatherley), CC BY-SA 2.5")
    for nome in nets:
        if nome:
            b.Add(pcbnew.NETINFO_ITEM(b, nome))
    for ref, (fpid, valor) in sorted(comps.items()):
        if ref.startswith("#") or not fpid:
            continue
        fp = carregar(fpid)
        fp.SetReference(ref)
        fp.SetValue(valor)
        if ref == "A1":
            fp.SetPosition(pcbnew.VECTOR2I(mm(X0), mm(Y0 + ALT)))
        else:
            xu, yu, rot = POS[ref]
            fp.SetPosition(vec(xu, yu))
            fp.SetOrientationDegrees(rot)
        b.Add(fp)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        fp.Reference().SetTextThickness(mm(0.15))
        fp.Value().SetLayer(pcbnew.F_Fab)
    for nome, nos in nets.items():
        net = b.FindNet(nome)
        for ref, pino in nos:
            if ref.startswith("#"):
                continue
            fp = b.FindFootprintByReference(ref)
            pad = fp.FindPadByNumber(pino)
            if pad is None:
                sys.exit(f"{ref} sem pad {pino}")
            pad.SetNet(net)
    # contorno: retangulo com cantos chanfrados de 2 mm
    xa, xb = X0 + ESQ, X0 + LARG
    ya, yb = Y0, Y0 + ALT
    c = 2.0
    pts = [(xa + c, ya), (xb - c, ya), (xb, ya + c), (xb, yb - c), (xb - c, yb), (xa + c, yb), (xa, yb - c), (xa, ya + c)]
    for i in range(len(pts)):
        linha(b, *pts[i], *pts[(i + 1) % len(pts)])
    # textos (portugues)
    texto(b, "PROGRAMADOR PIC12F629", 18.0, 37.6, 1.1, espessura=0.2)
    texto(b, "UNO SHIELD v1.0 - 2026-11-06", 18.0, 46.4, 0.8)
    texto(b, "Circuito do ardpicprog (CC BY-SA 2.5)", 18.0, 47.9, 0.8)
    texto(b, "+13V", 18.6, 16.5, 0.9)
    texto(b, "GND", 23.8, 16.5, 0.9)
    texto(b, "BC547 (CBE)", 26.2, 18.4, 0.8)
    texto(b, "LED 13V", 30.4, 30.4, 0.8)
    texto(b, "ATIVO", 56.0, 14.4, 0.8)
    texto(b, "ICSP", 59.2, 20.6, 0.8)
    texto(b, "MCLR", 22.6, 40.6, 0.8)
    texto(b, "VDD", 27.0, 40.6, 0.8)
    texto(b, "GND", 31.0, 40.6, 0.8)
    pcbnew.SaveBoard(str(HW / "shield_uno.kicad_pcb"), b)
    print("pcb ok:", len(b.GetFootprints()), "footprints,", b.GetNetCount(), "nets")


if __name__ == "__main__":
    main()
