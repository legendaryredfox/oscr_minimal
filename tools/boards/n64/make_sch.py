#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera o esquemático da placa n64 a partir da cópia da 16_and_8_bits (boards/n64/hardware/dumper.kicad_sch):
acrescenta o slot N64 (símbolo dumper:N64_Slot, rótulos pelo pinmap.md), tira SNES1, NES1, FC1, MD1, GBA1, PIC (U2) e C2 a C6
(tools/boards/megadrive/strip_sch.py), liga o pull-up R2 ao 3,3 V (EEPROM_DATA do N64) e renumera as referências (D109):
  U3 -> U2 (regulador), C7 -> C2, C8 -> C3, C9 -> C4 (VCC do slot).
Depois, rode tools/sch/regen.py boards/n64/hardware/dumper.kicad_sch (fios diretos e símbolos de alimentação, D122).
Uso: make_sch.py   (da raiz do repositório; idempotência: rode sobre a cópia nova da 16_and_8_bits)"""
import re, subprocess, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCH = ROOT / "boards/n64/hardware/dumper.kicad_sch"
PINMAP = ROOT / "boards/n64/docs/pinmap.md"
LIBSYM = ROOT / "boards/_lib/dumper.kicad_sym"
X0, Y0 = 900.43, 299.72                     # onde ficava o GBA1
REF = "N64_1"
SHEET = "/7a60289e-82cc-4290-bd86-3bc08aff2373"

s = SCH.read_text()
u = lambda: str(uuid.uuid4())

# --- definição do símbolo
lib = LIBSYM.read_text()
i = lib.index('(symbol "N64_Slot"'); d = 0
for j in range(i, len(lib)):
    d += (lib[j] == "(") - (lib[j] == ")")
    if d == 0: break
block = lib[i:j + 1].replace('(symbol "N64_Slot"', '(symbol "dumper:N64_Slot"', 1)
pins = re.findall(r'\(pin (\w+) line\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\(length ([\d.]+)\)\s*\(name "([^"]*)".*?\(number "([^"]*)"', block, re.S)
assert len(pins) == 50, len(pins)
k = s.index('(symbol "dumper:GBA_Slot"')
s = s[:k] + block + "\n\t\t" + s[k:]

# --- pino -> net, pelo pinmap.md
net_of = {}
for ln in PINMAP.read_text().splitlines():
    if ln.startswith("| ") and not ln.startswith("| pino") and not ln.startswith("|---"):
        c = [x.strip() for x in ln.strip("|").split("|")]
        if c[0].isdigit() and len(c) == 5 and c[3] != "":
            net_of[c[0]] = c[2]
labels, ncs = [], []
for _t, px, py, _a, _l, name, num in pins:
    X, Y = X0 + float(px), Y0 - float(py)
    net = net_of[num]
    if net.startswith("NC"):
        ncs.append(f'\t(no_connect\n\t\t(at {X:.2f} {Y:.2f})\n\t\t(uuid "{u()}")\n\t)\n')
        continue
    if net.startswith("3V3"): net = "+3V3"
    elif net.startswith("CLK"): net = net.split()[0]
    labels.append(f'\t(label "{net}"\n\t\t(at {X:.2f} {Y:.2f} 180)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
                  f'\t\t\t(justify right bottom)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')
prop = lambda n, v, at, hide="": (f'\t\t(property "{n}" "{v}"\n\t\t\t(at {at} 0)\n{hide}\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
                                  f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')
inst = ('\t(symbol\n\t\t(lib_id "dumper:N64_Slot")\n' f'\t\t(at {X0} {Y0} 0)\n'
        '\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n'
        f'\t\t(uuid "{u()}")\n'
        + prop("Reference", REF, f"{X0 - 10.16} {Y0 - 35.56}")
        + prop("Value", "N64_Slot", f"{X0 - 6.35} {Y0 - 33.02}")
        + prop("Footprint", "dumper:N64_Slot", f"{X0} {Y0}", "\t\t\t(hide yes)\n")
        + prop("Datasheet", "", f"{X0} {Y0}", "\t\t\t(hide yes)\n")
        + prop("Description", "Slot de cartucho N64 50 pinos (3,3 V!). Footprint do OSCR.", f"{X0} {Y0}", "\t\t\t(hide yes)\n")
        + "".join(f'\t\t(pin "{n}"\n\t\t\t(uuid "{u()}")\n\t\t)\n' for n in sorted((p[6] for p in pins), key=int))
        + f'\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "{SHEET}"\n\t\t\t\t\t(reference "{REF}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
cut = s.index("\t(sheet_instances")
s = s[:cut] + inst + "".join(labels) + "".join(ncs) + s[cut:]
tmp = SCH.with_suffix(".pre")
tmp.write_text(s)

# --- tira o que a placa não usa
REMOVE = "SNES1,NES1,FC1,MD1,GBA1,U2,C2,C3,C4,C5,C6"
p = subprocess.run([sys.executable, str(ROOT / "tools/boards/megadrive/strip_sch.py"), str(tmp), str(SCH), REMOVE], capture_output=True, text=True)
sys.stderr.write(p.stderr)
tmp.unlink()
s = SCH.read_text()

# --- R2: pull-up do EEPROM_DATA vai ao 3,3 V (o rótulo +5V do pino 1 vira +3V3)
m = re.search(r'\(symbol\s*\(lib_id "Device:R"\)\s*\(at ([\d.]+) ([\d.]+) 0\).*?\(property "Reference" "R2"', s, re.S)
# o regex acima pega o primeiro Device:R; confere pela referência e usa a posição do R2
for m in re.finditer(r'\(symbol\s*\(lib_id "Device:R"\)\s*\(at ([\d.]+) ([\d.]+) [\d.]+\)(.*?)\n\t\)\n', s, re.S):
    if '(property "Reference" "R2"' in m.group(3):
        rx, ry = float(m.group(1)), float(m.group(2)); break
else:
    sys.exit("R2 não achado")
done = 0
def fix(mm):
    global done
    x, y = float(mm.group(2)), float(mm.group(3))
    if mm.group(1) == "+5V" and abs(x - rx) < 0.02 and abs(y - (ry - 3.81)) < 0.02:
        done += 1
        return mm.group(0).replace('"+5V"', '"+3V3"', 1)
    return mm.group(0)
s = re.sub(r'\(label "([^"]*)"\s*\(at ([\d.]+) ([\d.]+) \d+\)', fix, s)
assert done == 1, f"rótulo +5V do R2 pin 1: {done}"

# --- renumera referências: U3->U2, C7->C2, C8->C3, C9->C4 (os antigos U2, C2..C6 já saíram)
for old, new in (("U3", "U2"), ("C7", "C2"), ("C8", "C3"), ("C9", "C4")):
    s, n1 = re.subn(r'\(property "Reference" "%s"' % old, '(property "Reference" "%s"' % new, s)
    s, n2 = re.subn(r'\(reference "%s"\)' % old, '(reference "%s")' % new, s)
    assert n1 == 1 and n2 == 1, (old, n1, n2)
SCH.write_text(s)
print("esquemático n64 gerado:", SCH)
