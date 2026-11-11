#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Acrescenta o slot SMS1 (dumper:SMS_Slot) ao esquemático da 8_bits (cópia da famicom_nes v1.0), em paralelo a NES1 e FC1.
Rótulos de net nos pinos de sinal (nomes de net do Arduino, como o MD1), símbolos +5V e GND, marcas de não
conexão nos pinos livres. As nets vêm do mastersystem_adapter do OSCR (netlist por kicad-cli). Os pinos do Mega que só o SMS usa (D6, D8, D9, D17, D30 a D34, D36, D37)
perdem a marca de não conexão e ganham o rótulo. O 5V do slot e do C4 é +5V_CART (atrás do F1).
Uso: python3 tools/boards/8_bits/add_sms_sch.py boards/8_bits/hardware-v1.0/dumper.kicad_sch
Idempotente: não faz nada se SMS1 já existe."""
import re, subprocess, sys, tempfile, uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import os
ROOT = Path(__file__).resolve().parents[3]
VCC = os.environ.get("SMS_VCC", "+5V_CART")      # v1.0: +5V_CART (atrás do F1); v1.1: VCC_CART (saída do seletor 3,3 V/5 V)
CAP_NEW = os.environ.get("SMS_CAP", "C4")         # referência do capacitor novo do slot SMS
CAP_SRC = os.environ.get("SMS_CAP_SRC", "C3")     # capacitor do Famicom, clonado (com seus símbolos de alimentação)
LEG = ROOT / "vendor/oscr/legacy/hardware/mastersystem_adapter/mastersystem_adapter.kicad_sch"
LIB = (ROOT / "boards/_lib/dumper.kicad_sym").read_text()
path = Path(sys.argv[1])
sch = path.read_text()
if '(reference "SMS1")' in sch:
    print("SMS1 já existe"); sys.exit(0)

def block(text, start):
    d, j = 0, start
    while True:
        c = text[j]
        if c == "(": d += 1
        elif c == ")":
            d -= 1
            if d == 0: return text[start:j + 1]
        j += 1

# --- nets do OSCR --------------------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(LEG)],
                   check=True, capture_output=True)
    root = ET.parse(out).getroot()
net = {}
for n in root.find("nets"):
    for x in n:
        if x.get("ref") == "U1":
            net[x.get("pin")] = n.get("name")
net["47"] = "unconnected-clock"   # decisão D136: Clock do SMS sem ligação (o CLK0 do Si5351 vai só ao pino 37 do NES)

# --- símbolo na lib_symbols ----------------------------------------------------
sym = block(LIB, LIB.index('\t(symbol "SMS_Slot"'))
sym_pins = {}
for m in re.finditer(r'\(pin (\w+) line\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\(length [\d.]+\)\s*\(name "([^"]*)".*?\(number "([^"]*)"', sym, re.S):
    sym_pins[m.group(6)] = (float(m.group(2)), float(m.group(3)), int(m.group(4)), m.group(5))
assert len(sym_pins) == 50
lib_sym = "\t" + sym.replace('(symbol "SMS_Slot"', '(symbol "dumper:SMS_Slot"', 1).replace("\n", "\n\t")
i = sch.index("\t(lib_symbols\n") + len("\t(lib_symbols\n")
sch = sch[:i] + "\t" + lib_sym + "\n" + sch[i:]

# --- instância ----------------------------------------------------------------
X, Y = 480.06, 118.11
u = lambda: str(uuid.uuid4())
root_uuid = re.search(r"\(uuid ([0-9a-f-]{36})\)", sch).group(1)
pins_xml = "".join(f'\t\t(pin "{n}"\n\t\t\t(uuid "{u()}")\n\t\t)\n' for n in sorted(sym_pins, key=int))
inst = f'''\t(symbol
\t\t(lib_id "dumper:SMS_Slot")
\t\t(at {X} {Y} 0)
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "{u()}")
\t\t(property "Reference" "SMS1"
\t\t\t(at {X+24.5} {Y-19.3} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Value" "SMS_Slot"
\t\t\t(at {X+24.5} {Y-16.8} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" "dumper:SMS_Slot"
\t\t\t(at {X+6.35} {Y+22} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {X+6.35} {Y+22} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
{pins_xml}\t\t(instances
\t\t\t(project "dumper"
\t\t\t\t(path "/{root_uuid}"
\t\t\t\t\t(reference "SMS1")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

def power(kind, x, y, rot, ref):
    val = "+5V" if kind == "+5V" else "GND"
    shown = VCC if kind == "+5V" else "GND"
    return f'''\t(symbol
\t\t(lib_id "power:{val}")
\t\t(at {x:.2f} {y:.2f} {rot})
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom no)
\t\t(on_board no)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "{u()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {x:.2f} {y:.2f} 90)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "{shown}"
\t\t\t(at {x:.2f} {y:.2f} 90)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pin "1"
\t\t\t(uuid "{u()}")
\t\t)
\t\t(instances
\t\t\t(project "dumper"
\t\t\t\t(path "/{root_uuid}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

def label(name, x, y, side):
    ang, just = (0, "left bottom") if side == "R" else (180, "right bottom")
    return f'''\t(label "{name}"
\t\t(at {x:.2f} {y:.2f} {ang})
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify {just})
\t\t)
\t\t(uuid "{u()}")
\t)
'''

parts = [inst]
pwr = 100
for n in sorted(sym_pins, key=int):
    px, py, ori, name = sym_pins[n]
    x, y = X + px, Y - py           # y do símbolo cresce para cima
    side = "R" if ori == 180 else "L"   # pino na borda direita aponta para dentro (180)
    nm = net[n]
    if nm.startswith("unconnected"):
        parts.append(f'\t(no_connect\n\t\t(at {x:.2f} {y:.2f})\n\t\t(uuid "{u()}")\n\t)\n')
    elif nm in ("+5V", "GND"):
        pwr += 1
        parts.append(power(nm, x, y, 270 if side == "R" else 90, f"#PWR{pwr:03d}"))
    else:
        parts.append(label(nm, x, y, side))

# --- capacitor de desacoplamento do slot SMS: clona o grupo C3 (Famicom) + +5V_CART + GND --------
def clone_cap(sch, new_ref, pwr_refs):
    """Clona o capacitor CAP_SRC e os dois símbolos de alimentação ligados a ele, 15,24 mm à direita."""
    found = []
    i = 0
    cap = None
    syms = []
    while True:
        k = sch.find("\n\t(symbol\n\t\t(lib_id", i)
        if k < 0: break
        k += 1
        s0 = sch.index("(symbol", k); e = s0 + len(block(sch, s0))
        b = sch[s0:e]
        m = re.search(r'\(lib_id "([^"]+)"\)\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)', b)
        r = re.search(r'\(property "Reference" "([^"]+)"', b)
        if m and r:
            syms.append((r.group(1), float(m.group(2)), float(m.group(3)), b))
            if r.group(1) == CAP_SRC: cap = (float(m.group(2)), float(m.group(3)))
        i = e
    assert cap, CAP_SRC
    near = [(r, x, y, b) for r, x, y, b in syms if abs(x - cap[0]) < 0.01 and abs(y - cap[1]) < 6.0]
    assert len(near) == 3, [n[0] for n in near]
    pw = iter(pwr_refs)
    res = []
    for r, x, y, b in sorted(near, key=lambda t: t[2]):
        new = new_ref if r == CAP_SRC else next(pw)
        nb = re.sub(r'\(uuid "[0-9a-f-]{36}"\)', lambda _m: f'(uuid "{u()}")', b)
        nb = nb.replace(f'"{r}"', f'"{new}"')
        for fx in (f"{x:g}", f"{x:.2f}"):
            nb = re.sub(r'(\(at )' + re.escape(fx) + r'( )', lambda mm: mm.group(1) + f"{x + 15.24:g}" + mm.group(2), nb)
        res.append("\t" + nb + "\n")
    return "".join(res)

parts.append(clone_cap(sch, CAP_NEW, ("#PWR201", "#PWR202")))
# --- pinos do Mega usados só pelo SMS: tira a marca de não conexão e põe o rótulo no pino ---------------------
mega_i = sch.index('(lib_id "dumper:Mega2560_R3_Shield")')
mx, my = [float(v) for v in re.search(r"\(at ([-\d.]+) ([-\d.]+) 0\)", sch[mega_i:mega_i + 200]).groups()]
mm = sch.index('(symbol "dumper:Mega2560_R3_Shield"')
mega_sym = block(sch, mm)
mpins = {}
for m in re.finditer(r'\(pin (\w+) line\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\(length [\d.]+\)\s*\(name "([^"]*)".*?\(number "([^"]*)"', mega_sym, re.S):
    mpins[m.group(6)] = (float(m.group(2)), float(m.group(3)), int(m.group(4)))
mega_nets = sorted({v for v in net.values() if re.fullmatch(r"[AD]\d+", v)})
nlab = 0
for nm in mega_nets:
    px, py, ori = mpins[nm]
    x, y = mx + px, my - py
    pat = re.compile(r"\t\(no_connect\n\t\t\(at %s %s\)\n\t\t\(uuid \"[0-9a-f-]{36}\"\)\n\t\)\n" % (re.escape(f"{x:g}"), re.escape(f"{y:g}")))
    if pat.search(sch):
        sch = pat.sub("", sch, count=1)
        parts.append(label(nm, x, y, "R" if ori == 180 else "L"))
        nlab += 1
print("rótulos novos nos pinos do Mega:", nlab)
end = sch.index("\t(sheet_instances")
sch = sch[:end] + "".join(parts) + sch[end:]
path.write_text(sch)
print("SMS1 acrescentado:", sum(1 for n in net.values() if n.startswith("D") or n.startswith("A")), "pinos com rótulo")
