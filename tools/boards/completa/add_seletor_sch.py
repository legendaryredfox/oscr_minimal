#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Transplanta o seletor de tensão 3,3 V/5 V (D138, D147: LDO LD1117V33, P-MOSFET de bypass, 2N7000, J1 e resistores) do esquemático da 8_bits v1.1
para o esquemático da completa v1.1 e passa os slots NES, Famicom, Mega Drive e SMS (e seus capacitores) de +5V_CART para VCC_CART. SNES, GBA, PIC e Si5351 ficam
em +5V_CART (o SA-1 precisa de 5 V). Refs novas: U4, C12, C13, R3, R4, R5, Q1, Q2, J1 (C11 é o do N64) (as da 8_bits são U2, C5, C6, R2, R3, R4).
Uso: python3 tools/boards/completa/add_seletor_sch.py boards/completa/hardware-v1.1/dumper.kicad_sch   (depois de add_sms_sch.py com SMS_VCC=VCC_CART)
Idempotente: não faz nada se U4 já existe."""
import re, sys, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
DONOR = (ROOT / "boards/8_bits/hardware-v1.1/dumper.kicad_sch").read_text()
path = Path(sys.argv[1]); sch = path.read_text()
if '(reference "U4")' in sch:
    print("seletor já existe"); sys.exit(0)
u = lambda: str(uuid.uuid4())
MAP = {"U2": "U4", "C5": "C12", "C6": "C13", "R2": "R3", "R3": "R4", "R4": "R5"}

def top(t):
    d, els, st = 0, [], None
    for k, ch in enumerate(t):
        if ch == "(":
            d += 1
            if d == 2: st = k
        elif ch == ")":
            if d == 2: els.append((st, k + 1))
            d -= 1
    return els

def block(t, i):
    d, j = 0, i
    while True:
        c = t[j]
        if c == "(": d += 1
        elif c == ")":
            d -= 1
            if d == 0: return t[i:j + 1]
        j += 1

def xy(e):
    m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", e) or re.search(r"\(pts\s*\(xy ([-\d.]+) ([-\d.]+)", e)
    return (float(m.group(1)), float(m.group(2))) if m else None

droot = re.search(r"\(uuid ([0-9a-f-]{36})\)", DONOR).group(1)
troot = re.search(r"\(uuid ([0-9a-f-]{36})\)", sch).group(1)
els = [DONOR[a:b] for a, b in top(DONOR)]
reg = [e for e in els if xy(e) and 300 <= xy(e)[0] <= 500 and 395 <= xy(e)[1] <= 450 and e.split("\n")[0].split(" ")[0] in ("(symbol", "(wire", "(label", "(text", "(junction")]
# o rótulo VSEL_EN do pino D18 do Mega (fora da região)
d18 = [e for e in els if e.startswith('(label "VSEL_EN"') and xy(e) == (132.08, 132.08)]
assert len(reg) >= 40 and len(d18) == 1, (len(reg), len(d18))

# símbolos da biblioteca que faltam
lib_ids = sorted({m.group(1) for e in reg if e.startswith("(symbol") for m in [re.search(r'\(lib_id "([^"]+)"\)', e)] if m})
add = ""
for lid in lib_ids:
    if f'(symbol "{lid}"' not in sch.split("(lib_symbols")[1].split("\n\t(symbol\n")[0] and f'\t\t(symbol "{lid}"' not in sch:
        i = DONOR.index(f'\t\t(symbol "{lid}"')
        add += block(DONOR, i + 2).join(["\t\t", "\n"]) if False else "\t\t" + block(DONOR, i + 2) + "\n"
if add:
    k = sch.index("\t(lib_symbols\n") + len("\t(lib_symbols\n")
    sch = sch[:k] + add + sch[k:]

pw = 1000
out = []
for e in reg:
    n = re.sub(r'\(uuid "[0-9a-f-]{36}"\)', lambda _m: f'(uuid "{u()}")', e)
    n = n.replace(droot, troot)
    if n.startswith("(symbol"):
        ref = re.search(r'\(property "Reference" "([^"]+)"', n).group(1)
        if ref.startswith("#PWR"):
            pw += 1; new = f"#PWR{pw}"
        else:
            new = MAP.get(ref, ref)
        n = n.replace(f'"{ref}"', f'"{new}"')
    out.append("\t" + n.replace("\n", "\n\t") + "\n")
# rótulo VSEL_EN no pino D18 do Mega (tira a marca de não conexão que estava ali)
nc = re.compile(r"\t\(no_connect\n\t\t\(at 132\.08 132\.08\)\n\t\t\(uuid \"[0-9a-f-]{36}\"\)\n\t\)\n")
assert nc.search(sch), "D18 do Mega sem marca de não conexão"
sch = nc.sub("", sch, count=1)
n = re.sub(r'\(uuid "[0-9a-f-]{36}"\)', lambda _m: f'(uuid "{u()}")', d18[0])
out.append("\t" + n.replace("\n", "\n\t") + "\n")

# slots NES, Famicom, Mega Drive, SMS e seus capacitores (C3, C4, C5, C10): +5V_CART -> VCC_CART. Por referência dos símbolos de alimentação (16_and_8_bits v1.0 + add_sms_sch)
cart = ["#PWR019", "#PWR024", "#PWR025", "#PWR027", "#PWR029", "#PWR045", "#PWR047", "#PWR049", "#PWR201"]
sms_pw = [m.group(1) for m in re.finditer(r'\(reference "(#PWR1\d\d)"\)', sch)]
for ref in cart + sms_pw:
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "power:\+5V"\)', sch):
        s0 = m.start() + 1; b = block(sch, s0 + sch[s0:].index("(symbol"))
        if f'(property "Reference" "{ref}"' in b and '"+5V_CART"' in b:
            sch = sch.replace(b, b.replace('(property "Value" "+5V_CART"', '(property "Value" "VCC_CART"'), 1)
            break
end = sch.index("\t(sheet_instances")
sch = sch[:end] + "".join(out) + sch[end:]
path.write_text(sch)
print("seletor transplantado:", len(reg), "elementos; slots NES, Famicom, Mega Drive e SMS em VCC_CART")
