#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera boards/_lib/ (símbolos e footprints próprios).

- Slots SNES/NES/Famicom/Mega Drive: copiados do OSCR (CC BY 4.0),
  vendor/oscr/legacy/hardware/{symbols,footprints}. O footprint original só tem
  pads; aqui são acrescentados courtyard, contorno Fab, rótulo e marca do pino 1.
- Mega 2560 R3 shield: gerado a partir das cotas oficiais do Arduino
  (furos e headers em mm; origem no canto inferior esquerdo da placa, Y negativo = para cima, vista de cima, USB à esquerda).
- Si5351: símbolo do módulo de 7 pinos (VIN GND SDA SCL CLK2 CLK1 CLK0).

Uso: python3 tools/build_lib.py && kicad-cli fp upgrade boards/_lib/dumper.pretty
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "vendor/oscr/legacy/hardware"
LIB = ROOT / "boards/_lib"
PRETTY = LIB / "dumper.pretty"
LIBNAME = "dumper"

SLOTS = {  # símbolo OSCR, footprint OSCR, nome novo, rótulo de silkscreen
    "SNES_Slot": ("SNES Slot.kicad_mod", "SNES_Slot", "SNES 62p"),
    "NES_Slot": ("NES_Slot.kicad_mod", "NES_Slot", "NES 72p"),
    "FC_Slot": ("FC_Slot.kicad_mod", "FC_Slot", "FAMICOM 60p"),
    "MD_Slot": ("MD_Slot.kicad_mod", "MD_Slot", "MEGA DRIVE 64p"),
    "N64_Slot": ("N64 Slot.kicad_mod", "N64_Slot", "N64 50p"),   # footprint próprio (build_n64_footprint): duas fileiras ao longo de x
}

# ----------------------------------------------------------------- símbolos
def top_level_symbols(text):
    """Devolve {nome: texto} dos símbolos de nível 1 de um .kicad_sym."""
    out = {}
    i = text.index("(symbol ")
    while i != -1:
        depth = 0
        j = i
        while True:
            c = text[j]
            if c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0: break
            j += 1
        block = text[i:j + 1]
        out[re.match(r'\(symbol "([^"]+)"', block).group(1)] = block
        i = text.find("\n  (symbol ", j)
        if i != -1: i += 3
    return out


GBA_PINS = ["VCC", "CLK", "WR", "RD", "CS1"] + [f"AD{i}" for i in range(16)] + \
           [f"D{i}_A{16+i}" for i in range(8)] + ["RST_CS2", "AUD_IRQ", "GND"]   # pinos 1..32


def gba_symbol():
    n = len(GBA_PINS)
    top = n * 2.54 / 2
    s = ['  (symbol "GBA_Slot" (in_bom yes) (on_board yes)',
         f'    (property "Reference" "J" (at 0 {top + 3:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Value" "GBA_Slot" (at 0 {-top - 3:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Footprint" "{LIBNAME}:GBA_Slot" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (property "ki_description" "Slot de cartucho GBA 32 pinos (3,3 V!). Pinos 33/34 = blindagem. Footprint SMD do OSCR." (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (symbol "GBA_Slot_0_1"',
         f'      (rectangle (start -10.16 {top:.2f}) (end 10.16 {-top:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))',
         "    )",
         '    (symbol "GBA_Slot_1_1"']
    for k, name in enumerate(GBA_PINS):
        t = "power_in" if name in ("VCC", "GND") else "bidirectional"
        y = top - 1.27 - k * 2.54
        s.append(f'      (pin {t} line (at -15.24 {y:.2f} 0) (length 5.08) (name "{name}" (effects (font (size 1.016 1.016)))) (number "{k+1}" (effects (font (size 1.016 1.016)))))')
    for j, nm in enumerate(("SHIELD_3", "SHIELD_4")):
        s.append(f'      (pin power_in line (at 15.24 {top - 1.27 - j * 2.54:.2f} 180) (length 5.08) (name "GND" (effects (font (size 1.016 1.016)))) (number "{nm}" (effects (font (size 1.016 1.016)))))')
    s += ["    )", "  )"]
    return "\n".join(s)


def build_gba_footprint():
    s = (SRC / "footprints/!OSCR.pretty/GBA_Slot.kicad_mod").read_text().rstrip()
    assert s.endswith(")")
    s = s[:-1].rstrip()
    s = re.sub(r'\(fp_text reference "[^"]*"', '(fp_text reference "REF**"', s, count=1)
    s = s.replace('(fp_text value "GBA_Slot" (at 0 0) (layer "F.SilkS") hide', '(fp_text value "GBA_Slot" (at 0 0) (layer "F.Fab") hide')
    extra = [rect(-8.0, -29.5, 19.5, 29.5, "F.CrtYd", 0.05),
             rect(-0.9, -28.6, 13.9, 28.6, "F.SilkS", 0.15),
             text("GBA 3V3", 6.2, 0, "F.SilkS", 1.5, 90),
             text("SOMENTE GBA - 3,3 V", 11.5, 0, "F.SilkS", 1.0, 90)]
    (PRETTY / "GBA_Slot.kicad_mod").write_text(s + "\n" + "\n".join(extra) + "\n)\n")


def mega_pins():
    """(número/nome, tipo, lado) dos pinos dos headers do Mega R3."""
    left, right = [], []
    for n in ("5V1", "VIN", "3V3", "RST1", "IORF", "GND2", "GND3"):
        left.append((n, "power_in" if n.startswith(("5V", "GND", "VIN")) else "passive"))
    left += [(f"A{i}", "passive") for i in range(16)]
    right += [(f"D{i}", "passive") for i in range(14)]
    right += [("AREF", "passive"), ("GND1", "power_in"), ("SDA", "passive"), ("SCL", "passive")]
    right += [(f"D{i}", "passive") for i in range(14, 22)]
    right += [(f"D{i}", "passive") for i in range(22, 54)]
    right += [("5V3", "power_in"), ("5V4", "power_in"), ("GND5", "power_in"), ("GND6", "power_in")]
    return left, right


def mega_symbol():
    left, right = mega_pins()
    rows = max(len(left), len(right))
    h = rows * 2.54
    w = 25.4
    top = h / 2
    s = []
    s.append(f'  (symbol "Mega2560_R3_Shield" (in_bom yes) (on_board yes)')
    s.append(f'    (property "Reference" "A" (at 0 {top + 3:.2f} 0) (effects (font (size 1.27 1.27))))')
    s.append(f'    (property "Value" "Mega2560_R3_Shield" (at 0 {-top - 3:.2f} 0) (effects (font (size 1.27 1.27))))')
    s.append(f'    (property "Footprint" "{LIBNAME}:Mega2560_R3_Shield" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    s.append('    (property "Datasheet" "https://docs.arduino.cc/hardware/mega-2560" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    s.append('    (symbol "Mega2560_R3_Shield_0_1"')
    s.append(f'      (rectangle (start {-w/2:.2f} {top:.2f}) (end {w/2:.2f} {-top:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))')
    s.append("    )")
    s.append('    (symbol "Mega2560_R3_Shield_1_1"')
    for side, pins, x, ang in (("L", left, -w / 2 - 5.08, 0), ("R", right, w / 2 + 5.08, 180)):
        for k, (n, t) in enumerate(pins):
            y = top - 1.27 - k * 2.54
            s.append(f'      (pin {t} line (at {x:.2f} {y:.2f} {ang}) (length 5.08) '
                     f'(name "{n}" (effects (font (size 1.016 1.016)))) '
                     f'(number "{n}" (effects (font (size 1.016 1.016)))))')
    s.append("    )")
    s.append("  )")
    return "\n".join(s)


def si5351_symbol():
    pins = [("1", "VIN", "power_in"), ("2", "GND", "power_in"), ("3", "SDA", "bidirectional"),
            ("4", "SCL", "input"), ("5", "CLK2", "output"), ("6", "CLK1", "output"), ("7", "CLK0", "output")]
    s = ['  (symbol "Si5351_Module" (in_bom yes) (on_board yes)',
         '    (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))',
         '    (property "Value" "Si5351_Module" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))',
         '    (property "Footprint" "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (property "ki_description" "Modulo Si5351 breakout (25MHz), header 1x7: VIN GND SDA SCL 2 1 0" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (symbol "Si5351_Module_0_1"',
         '      (rectangle (start -6.35 8.89) (end 6.35 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))',
         "    )",
         '    (symbol "Si5351_Module_1_1"']
    for k, (num, name, t) in enumerate(pins):
        y = 7.62 - k * 2.54
        s.append(f'      (pin {t} line (at -11.43 {y:.2f} 0) (length 5.08) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    s += ["    )", "  )"]
    return "\n".join(s)


def q_pmos_symbol():
    """P-MOSFET com os pinos numerados 1, 2, 3 (G, D, S) como no TO-220 (o Device:Q_PMOS do KiCad usa D, G, S como numero)."""
    t = Path("/usr/share/kicad/symbols/Device.kicad_sym").read_text()
    i = t.index('(symbol "Q_PMOS"')
    d = 0
    for j in range(i, len(t)):
        d += (t[j] == "(") - (t[j] == ")")
        if d == 0:
            break
    b = t[i:j + 1]
    b = b.replace('(symbol "Q_PMOS"', '(symbol "Q_PMOS_GDS"', 1).replace('(symbol "Q_PMOS_', '(symbol "Q_PMOS_GDS_')
    b = b.replace('(symbol "Q_PMOS_GDS_GDS"', '(symbol "Q_PMOS_GDS"')
    for a, c in (("G", "1"), ("D", "2"), ("S", "3")):
        b = b.replace('(number "%s"' % a, '(number "%s"' % c)
    b = re.sub(r'(\(property "Footprint" ")[^"]*"', r'\g<1>Package_TO_SOT_THT:TO-220-3_Vertical"', b, count=1)
    return "  " + b


def build_symbols():
    oscr = (SRC / "symbols/!OSCR.kicad_sym").read_text()
    syms = top_level_symbols(oscr)
    out = ['(kicad_symbol_lib (version 20220914) (generator build_lib.py)']
    for name in SLOTS:
        blk = syms[name]
        blk = re.sub(r'(\(property "Footprint" ")[^"]*"', rf'\g<1>{LIBNAME}:{name}"', blk, count=1)
        out.append("  " + blk)
    out.append(mega_symbol())
    out.append(gba_symbol())
    out.append(si5351_symbol())
    out.append(q_pmos_symbol())
    out.append(")")
    (LIB / f"{LIBNAME}.kicad_sym").write_text("\n".join(out) + "\n")

# --------------------------------------------------------------- footprints
PAD_RE = re.compile(r'\(pad "?([^"\s]*)"? (thru_hole|np_thru_hole) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)[^)]*\)\s*\(size ([\d.]+) ([\d.]+)\)')

def line(x1, y1, x2, y2, layer, w=0.12):
    return f'  (fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (layer "{layer}") (width {w}))'

def rect(x1, y1, x2, y2, layer, w=0.12):
    return "\n".join([line(x1, y1, x2, y1, layer, w), line(x2, y1, x2, y2, layer, w),
                      line(x2, y2, x1, y2, layer, w), line(x1, y2, x1, y1, layer, w)])

def text(t, x, y, layer, size=1.2, rot=0):
    return (f'  (fp_text user "{t}" (at {x:.3f} {y:.3f} {rot}) (layer "{layer}")\n'
            f'    (effects (font (size {size} {size}) (thickness {size*0.15:.2f}))))')

def build_slot(fname, newname, label):
    s = (SRC / "footprints/!OSCR.pretty" / fname).read_text()
    pads = PAD_RE.findall(s)
    xs = [float(p[3]) for p in pads]; ys = [float(p[4]) for p in pads]
    pad1 = next(p for p in pads if p[0] in ("1", "A1"))
    x1, y1 = float(pad1[3]), float(pad1[4])
    cx = (min(xs) + max(xs)) / 2
    BODY_W, BODY_END = 12.0, 4.0
    # Corpo do slot: ESTIMATIVA (ver docs/decisoes.md D17), a confirmar com paquímetro.
    # Largura (eixo das fileiras) = 12 mm centrada nas fileiras; comprimento = vão dos pads + 8 mm.
    bx0, bx1 = cx - BODY_W / 2, cx + BODY_W / 2
    by0, by1 = min(ys) - BODY_END, max(ys) + BODY_END
    s = s.rstrip()
    assert s.endswith(")")
    s = s[:-1].rstrip()
    s = re.sub(r'\(footprint "[^"]*"', f'(footprint "{newname}"', s, count=1)
    s = re.sub(r'\(fp_text value "[^"]*"', f'(fp_text value "{newname}"', s)
    # marca do pino 1: seta para o lado de fora da fileira
    out_dir = -1 if x1 <= cx else 1
    extra = [
        rect(bx0, by0, bx1, by1, "F.CrtYd", 0.05),
        rect(bx0, by0, bx1, by1, "F.Fab", 0.1),
        rect(bx0, by0, bx1, by1, "F.SilkS", 0.15),
        text("1" if pad1[0] == "1" else "A1", x1 + out_dir * 2.4, y1, "F.SilkS", 1.0),
        text(label, cx, (min(ys) + max(ys)) / 2, "F.SilkS", 1.5, 90),
    ]
    (PRETTY / f"{newname}.kicad_mod").write_text(s + "\n" + "\n".join(extra) + "\n)\n")
    return dict(pads=len(pads), bbox=(bx0, by0, bx1, by1))


def build_n64_footprint():
    """Slot N64 (50 pinos, 2,5 mm, duas fileiras ao longo de x, pino 1 em (0, 0)). Pads do OSCR;
    contorno e courtyard são ESTIMATIVA (D17/D120): conferir com o slot comprado."""
    s = (SRC / "footprints/!OSCR.pretty/N64 Slot.kicad_mod").read_text()
    pads = PAD_RE.findall(s)
    xs = [float(p[3]) for p in pads]; ys = [float(p[4]) for p in pads]
    s = s.rstrip()
    assert s.endswith(")")
    s = s[:-1].rstrip()
    s = re.sub(r'\(footprint "[^"]*"', '(footprint "N64_Slot"', s, count=1)
    s = re.sub(r'\(fp_text value "[^"]*"', '(fp_text value "N64_Slot"', s)
    x0, x1 = min(xs) - 4.0, max(xs) + 4.0
    y0, y1 = min(ys) - 4.0, max(ys) + 4.0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    extra = [rect(x0, y0, x1, y1, "F.CrtYd", 0.05), rect(x0, y0, x1, y1, "F.Fab", 0.1), rect(x0, y0, x1, y1, "F.SilkS", 0.15),
             text("1", -2.4, 0, "F.SilkS", 1.0),
             text("N64 3,3 V", cx, cy, "F.SilkS", 1.5)]
    (PRETTY / "N64_Slot.kicad_mod").write_text(s + "\n" + "\n".join(extra) + "\n)\n")
    return len(pads), (x0, y0, x1, y1)


def mega_pads():
    """Cotas oficiais do Arduino Mega 2560 R3 (docs.arduino.cc/hardware/mega-2560), mm."""
    P = []
    P += [(n, 30.48 + 2.54 * i, -2.54) for i, n in enumerate(("IORF", "RST1", "3V3", "5V1", "GND2", "GND3", "VIN"))]
    P += [(f"A{i}", 50.8 + 2.54 * i, -2.54) for i in range(8)]
    P += [(f"A{8+i}", 73.66 + 2.54 * i, -2.54) for i in range(8)]
    P += [("SCL", 18.796, -50.8), ("SDA", 21.336, -50.8), ("AREF", 23.876, -50.8), ("GND1", 26.416, -50.8)]
    P += [(f"D{13-i}", 28.956 + 2.54 * i, -50.8) for i in range(6)]          # D13..D8
    P += [(f"D{7-i}", 45.72 + 2.54 * i, -50.8) for i in range(8)]            # D7..D0
    P += [(f"D{14+i}", 68.58 + 2.54 * i, -50.8) for i in range(8)]           # D14..D21
    P += [("5V3", 93.98, -50.8), ("5V4", 96.52, -50.8)]
    for n in range(22, 54):
        P.append((f"D{n}", 93.98 if n % 2 == 0 else 96.52, -48.26 + 2.54 * ((n - 22) // 2)))
    P += [("GND5", 93.98, -7.62), ("GND6", 96.52, -7.62)]
    return P

MEGA_HOLES = [(13.97, -2.54), (66.04, -7.62), (15.24, -50.8), (96.52, -2.54), (66.04, -35.56), (90.17, -50.8)]
MEGA_W, MEGA_H = 101.6, 53.34   # contorno oficial

def build_mega_footprint():
    name = "Mega2560_R3_Shield"
    o = [f'(footprint "{name}" (version 20211014) (generator build_lib.py)',
         '  (layer "F.Cu")',
         '  (descr "Shield para Arduino Mega 2560 R3; cotas oficiais Arduino, origem no canto inferior esquerdo")',
         "  (attr through_hole)",
         f'  (fp_text reference "REF**" (at {MEGA_W/2:.2f} 2) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         f'  (fp_text value "{name}" (at {MEGA_W/2:.2f} {-MEGA_H-2:.2f}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    for i, (n, x, y) in enumerate(mega_pads()):
        o.append(f'  (pad "{n}" thru_hole circle (at {x:.3f} {y:.3f}) (size 1.7272 1.7272) (drill 1.016) (layers *.Cu *.Mask))')
    for x, y in MEGA_HOLES:
        o.append(f'  (pad "" np_thru_hole circle (at {x:.3f} {y:.3f}) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))')
    o.append(rect(0, 0, MEGA_W, -MEGA_H, "F.Fab", 0.1))
    # sem courtyard: o shield cobre a área dos slots; só contorno em F.Fab
    o.append(text("MEGA 2560 R3", MEGA_W / 2, -MEGA_H / 2, "F.Fab", 2))
    o.append(")")
    (PRETTY / f"{name}.kicad_mod").write_text("\n".join(o) + "\n")
    return len(mega_pads())


def main():
    PRETTY.mkdir(parents=True, exist_ok=True)
    build_symbols()
    for sym, (fname, newname, label) in SLOTS.items():
        if newname == "N64_Slot":
            n, bb = build_n64_footprint()
            print(f"N64_Slot: {n} pads, courtyard {bb[2]-bb[0]:.2f} x {bb[3]-bb[1]:.2f} mm")
            continue
        r = build_slot(fname, newname, label)
        print(f"{newname}: {r['pads']} pads, courtyard {r['bbox'][2]-r['bbox'][0]:.2f} x {r['bbox'][3]-r['bbox'][1]:.2f} mm")
    build_gba_footprint()
    print("GBA_Slot: 32 pads SMD + 2 blindagem + 2 furos (OSCR)")
    print("Mega2560_R3_Shield:", build_mega_footprint(), "pads +", len(MEGA_HOLES), "furos")
    (ROOT / "boards/16_and_8_bits/hardware-v1.1/fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n'
        f'  (lib (name "{LIBNAME}")(type "KiCad")(uri "${{KIPRJMOD}}/../../_lib/dumper.pretty")(options "")(descr "Footprints do dumper (slots OSCR CC BY 4.0, Mega R3)"))\n)\n')
    (ROOT / "boards/16_and_8_bits/hardware-v1.1/sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n'
        f'  (lib (name "{LIBNAME}")(type "KiCad")(uri "${{KIPRJMOD}}/../../_lib/dumper.kicad_sym")(options "")(descr "Simbolos do dumper (slots OSCR CC BY 4.0, Mega R3, Si5351)"))\n)\n')


main()
