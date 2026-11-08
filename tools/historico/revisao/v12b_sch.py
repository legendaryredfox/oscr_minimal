#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v. 1.2 final (D108): esquematico. Move para a v. 1.2 o que estava planejado para a v. 1.3 (menos o RP2040):
 - 12 resistores serie (R3..R14, 0R de fabrica) nas linhas de controle D2 a D9 e D14 a D17, mais 12 TVS 5V (D3..D14, DNP) no lado do slot;
 - pull-up de /VRES (R15, DNP);
 - botao de reset (SW1) no RST1 do Mega;
 - chave de alimentacao dos slots: Q1 (P-MOSFET) liga o 5V (Mega) ao +5V_CART (slots, Si5351, PIC), comando no D19 (nivel baixo = liga),
   R16 mantem desligado, R17 em serie, LED verde D2 (R18) acende com o cartucho energizado.
Uso: python3 tools/historico/revisao/v12b_sch.py boards/16_bits/hardware-v1.3/dumper.kicad_sch   (nao roda duas vezes)"""
import sys, re, uuid
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from schlib import *

path = sys.argv[1]
s = open(path).read()
assert '"R3"' not in s, "ja aplicado"
SHEET = "7a60289e-82cc-4290-bd86-3bc08aff2373"
libs = lib_symbols(s)
P = placed(s)
byref = {p['ref']: p for p in P}
A1 = byref["A1"]

# ---------------------------------------------------------------- 1. renomear labels existentes
CTRL = ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D14", "D15", "D16", "D17"]
SWITCHED = {("SNES1", "27"), ("SNES1", "58"), ("MD1", "A2"), ("MD1", "A31"), ("U1", "1"), ("U2", "1"), ("R2", "1"),
            ("C2", "1"), ("C3", "1"), ("C4", "1"), ("C5", "1"), ("C6", "1")}
ends = {}
for sym in P:
    for pin in pins_of(libs[sym['lib']]):
        ends[pin_xy(sym, pin, libs)] = (sym['ref'], pin)
a1pin = {n: pin_xy(A1, n, libs) for n in CTRL + ["D19", "RST1"]}
ren = []   # (inicio, fim, novo_texto)
for t, x, y, ang, i, e in labels(s):
    who = ends[(round(x, 3), round(y, 3))]
    new = None
    if who[0] == "A1" and who[1] in CTRL:
        new = who[1] + "_M"
    elif t == "+5V" and who in SWITCHED:
        new = "+5V_CART"
    if new:
        ren.append((i, e, s[i:e].replace('(label "%s"' % t, '(label "%s"' % new, 1)))
for i, e, txt in sorted(ren, reverse=True):
    s = s[:i] + txt + s[e:]
assert len(ren) == len(CTRL) + len(SWITCHED), len(ren)

# ---------------------------------------------------------------- 2. no_connect de D19 e RST1 saem (viram PWR_EN e RESET)
for n in ("D19", "RST1"):
    x, y = a1pin[n]
    achou = None
    for m in re.finditer(r'\n\t\(no_connect\n\t\t\(at ([-0-9.]+) ([-0-9.]+)\)\n\t\t\(uuid "[^"]*"\)\n\t\)', s):
        if abs(float(m.group(1)) - x) < 0.01 and abs(float(m.group(2)) - y) < 0.01:
            achou = m
    assert achou, ("no_connect de", n, x, y)
    s = s[:achou.start()] + s[achou.end():]

# ---------------------------------------------------------------- 3. simbolos de biblioteca que faltam
def embed(lib_file, name, newname, renum=None):
    t = open("/usr/share/kicad/symbols/%s.kicad_sym" % lib_file).read()
    i = t.index('(symbol "%s"' % name)
    b, _ = block_at(t, i)
    b = b.replace('(symbol "%s"' % name, '(symbol "%s"' % newname, 1)
    b = b.replace('(symbol "%s_' % name, '(symbol "%s_' % newname.split(':')[1])
    if renum:
        for a, c in renum.items():
            b = b.replace('(number "%s"' % a, '(number "%s"' % c)
    return '\t\t' + b + '\n'


def embed_dumper(name):
    """copia do simbolo de boards/_lib/dumper.kicad_sym (a ERC compara a copia embutida com a da biblioteca)."""
    t = open(__import__("os").path.dirname(__import__("os").path.abspath(__file__)) + "/../../../boards/_lib/dumper.kicad_sym").read()
    i = t.index('(symbol "%s"' % name)
    b, _ = block_at(t, i)
    b = b.replace('(symbol "%s"' % name, '(symbol "dumper:%s"' % name, 1)
    return '\t\t' + b + '\n'


novos = [embed("Device", "D_TVS", "Device:D_TVS"),
         embed_dumper("Q_PMOS_GDS"),
         embed("Switch", "SW_Push", "Switch:SW_Push")]
li = s.index('\t(lib_symbols')
lb, lend = block_at(s, li + 1)
close = lend - 1
s = s[:close].rstrip('\t') + ''.join(novos) + '\t)' + s[lend:]
libs = lib_symbols(s)
# no simbolo do MOSFET os pinos passam a ser 1, 2, 3 (G, D, S) como no TO-220
assert pins_of(libs["dumper:Q_PMOS_GDS"]) == {'1': (-5.08, 0.0), '2': (2.54, 5.08), '3': (2.54, -5.08)}, pins_of(libs["dumper:Q_PMOS_GDS"])

# ---------------------------------------------------------------- 4. pecas novas
out = ''
labs = ''


def prop(name, v, x, y, hide=False):
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n%s\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
            % (name, v, x, y, '\t\t\t(hide yes)\n' if hide else ''))


def inst(lib, ref, value, fp, x, y, pins, dnp=False, desc=''):
    u = uuid.uuid4()
    t = ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp %s)\n\t\t(uuid "%s")\n'
         % (lib, x, y, 'yes' if dnp else 'no', u))
    t += prop('Reference', ref, x + 2.54, y - 1.27) + prop('Value', value, x + 2.54, y + 1.27)
    t += prop('Footprint', fp, x, y, True) + prop('Datasheet', '', x, y, True) + prop('Description', desc, x, y, True)
    for n in pins:
        t += '\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)\n' % (n, uuid.uuid4())
    t += ('\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (SHEET, ref))
    return t


def lab(name, xy, ang):
    just = {0: 'left bottom', 90: 'left bottom', 180: 'right bottom', 270: 'right bottom'}[ang]
    return label_text(name, xy[0], xy[1], ang, just)


def g(v):
    return round(round(v / 1.27) * 1.27, 3)


FP_R = "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical"
FP_D = "Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_CathodeUp"


def res(ref, val, x, y, top, bot, dnp=False, desc='Resistor'):
    global out, labs
    out += inst("Device:R", ref, val, FP_R, x, y, ("1", "2"), dnp, desc)
    labs += lab(top, (x, y - 3.81), 90) + lab(bot, (x, y + 3.81), 270)


def nxt(ref):
    return ref


for k, n in enumerate(CTRL):
    x = g(160 + 22 * k)
    res("R%d" % (3 + k), "0R", x, g(620), n + "_M", n, desc='Resistor serie (protecao de porta; 0R de fabrica, trocavel por 47 a 100R)')
    out += inst("Device:D_TVS", "D%d" % (3 + k), "TVS ou zener 5V (DNP)", FP_D, x, g(660), ("1", "2"), True, 'TVS 5V unidirecional, nao montado')
    labs += lab(n, (x - 3.81, g(660)), 180) + lab("GND", (x + 3.81, g(660)), 0)

Y1 = g(720)
XR15, XQ, XR16, XR17, XR18, XD2, XSW, XF = (g(v) for v in (160, 270, 320, 345, 370, 405, 460, 520))
res("R15", "10k (DNP)", XR15, Y1, "+5V_CART", "D17", True, 'Pull-up de /VRES para o Open EverDrive, nao montado')
out += inst("dumper:Q_PMOS_GDS", "Q1", "IRF9540N", "Package_TO_SOT_THT:TO-220-3_Vertical", XQ, Y1, ("1", "2", "3"), False, 'P-MOSFET: chave de alta do 5V dos slots')
labs += lab("PWR_G", (XQ - 5.08, Y1), 180) + lab("+5V_CART", (XQ + 2.54, Y1 - 5.08), 90) + lab("+5V", (XQ + 2.54, Y1 + 5.08), 270)
res("R16", "100k", XR16, Y1, "+5V", "PWR_G", desc='Mantem a chave desligada (gate no 5V) com o Mega em reset')
res("R17", "100R", XR17, Y1, "PWR_G", "PWR_EN", desc='Serie do comando D19 da chave')
res("R18", "1k", XR18, Y1, "+5V_CART", "LED_CART", desc='Limita o LED verde do 5V dos slots')
out += inst("Device:LED", "D2", "LED verde 3mm", "LED_THT:LED_D3.0mm", XD2, Y1, ("1", "2"), False, 'LED verde: 5V dos slots ligado')
labs += lab("GND", (XD2 - 3.81, Y1), 180) + lab("LED_CART", (XD2 + 3.81, Y1), 0)
out += inst("Switch:SW_Push", "SW1", "Reset", "Button_Switch_THT:SW_PUSH_6mm", XSW, Y1, ("1", "2"), False, 'Botao de reset do Mega')
labs += lab("RESET", (XSW - 5.08, Y1), 180) + lab("GND", (XSW + 5.08, Y1), 0)
# PWR_FLAG do +5V_CART (a ponta do Q1 e passiva): copia do FLG1
flg = [p for p in P if p['ref'] == 'FLG1'][0]['blk']
f3 = flg.replace('949.96', '%g' % XF).replace('539.75', '%g' % Y1).replace('537.21', '%g' % (Y1 - 2.54)).replace('542.29', '%g' % (Y1 + 2.54)).replace('"FLG1"', '"FLG3"')
f3 = re.sub(r'\(uuid "[^"]*"\)', lambda m: '(uuid "%s")' % uuid.uuid4(), f3)
f3 = re.sub(r'(\(pin "1"\n\t\t\t)\(uuid "[^"]*"\)', lambda m: m.group(1) + '(uuid "%s")' % uuid.uuid4(), f3)
out += '\t' + f3.lstrip('\t') + '\n'
labs += lab("+5V_CART", (XF, Y1), 0)
# labels do Mega: PWR_EN no D19 e RESET no RST1
labs += lab("PWR_EN", a1pin["D19"], 0) + lab("RESET", a1pin["RST1"], 0)

# inserir antes do (sheet_instances ou do ultimo ')'
end = s.rindex('\n)')
if '(sheet_instances' in s:
    end = s.index('\t(sheet_instances')
s = s[:end] + out + labs + s[end:]
open(path, 'w').write(s)
print("ok:", len(CTRL), "series,", len(CTRL), "TVS, 5V_CART em", len(SWITCHED), "pinos")
