#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bloco de troca de cartucho (D123/D126), esquemático. Acrescenta a uma placa o que falta para ligar e desligar o 5V dos slots por software,
descarregar o rail e acender o LED de "seguro trocar":
  Q1 (P-MOSFET, só nas placas que ainda não têm), R3 100k (gate ao +5V), R4 100R (D19 ao gate), R5 1k + LED verde (+5V_CART presente),
  Q2 2N7000 + R6 330R (descarga do +5V_CART; mais um 330R do +3V3 nas placas com regulador de 3,3 V),
  Q3 2N7000 + R7 100k + R8 1k + R9 1k + LED amarelo (sensor do rail: aceso = seguro trocar; SENSE_MCU vai ao D53).
Os pinos de 5V dos slots, Si5351, PIC, pull-ups e capacitores passam a +5V_CART (o 5V do Mega fica no C1, no LED de status, nos pontos de teste e no Q1).
As referências novas seguem a última de cada tipo da placa (D109). Uso: python3 tools/troca/sch_block.py boards/<placa>/hardware/dumper.kicad_sch [versão]
Variáveis de ambiente (D138):
  TROCA_MODO=bloco|fusivel   "fusivel": só o F1 (v1.0, 16_bits v1.2, SNES); sem Q1, Q2, Q3, LEDs nem D19/D53.
  TROCA_FUSE=1|0             F1 (PTC de furo passante, 0,5 A de retenção) em série na trilha de potência (padrão 1).
  TROCA_SELETOR=1            seletor 3,3 V/5 V (LDO, Q4, Q5), J1 "TRAVA 3,3 V" e resistores em série (precisa do modo bloco).
  TROCA_SLOTS=MD1,SMS1       slots que ficam no VCC_CART (seletor) e têm resistores em série; TROCA_SEL_CAPS=C3 os capacitores desses slots.
Não roda duas vezes. Desenho final com tools/sch/regen.py não é necessário: o bloco já sai com fios nas cadeias e rótulos nos nós compartilhados."""
import math, os, re, subprocess, sys, tempfile, uuid
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "sch"))
from sexp import parse, dump, val, find, S

PATH = Path(sys.argv[1]).resolve()
MODO = os.environ.get("TROCA_MODO", "bloco")
FUSE = os.environ.get("TROCA_FUSE", "1") == "1"
SELETOR = os.environ.get("TROCA_SELETOR") == "1"
SEL_SLOTS = [x for x in os.environ.get("TROCA_SLOTS", "MD1,SMS1").split(",") if x]
SEL_CAPS = [x for x in os.environ.get("TROCA_SEL_CAPS", "").split(",") if x]
SEL_REFS = set(SEL_SLOTS) | set(SEL_CAPS)
assert MODO in ("bloco", "fusivel") and not (SELETOR and MODO != "bloco"), "o seletor precisa do modo bloco"
SLOT_RE = re.compile(r"^(SNES|MD|NES|FC|N64|GBA|GB|SMS)\d+$")
text = PATH.read_text()
tree = parse(text)
g = lambda: str(uuid.uuid4())
f2 = lambda v: ("%.4f" % v).rstrip("0").rstrip(".")
KEEP_REFS = ("A1", "C1", "D1", "FLG", "TP", "#")

libs = find(tree, "lib_symbols")[0]
def lib_pins(sym):
    out = {}
    def walk(n):
        for k in n:
            if isinstance(k, list) and k:
                if val(k[0]) == "pin":
                    at = find(k, "at")[0]
                    out[val(find(k, "number")[0][1])] = (val(find(k, "name")[0][1]), float(at[1]), float(at[2]), float(at[3]))
                elif val(k[0]) == "symbol": walk(k)
    walk(sym); return out
LIBPINS = {val(c[1]): lib_pins(c) for c in libs[1:] if isinstance(c, list) and c and val(c[0]) == "symbol"}

def tr(px, py, rot, mir):
    if mir == "x": py = -py
    if mir == "y": px = -px
    r = math.radians(rot); c, s = round(math.cos(r), 6), round(math.sin(r), 6)
    return (px * c - py * s, -(px * s + py * c))

class Part:
    def __init__(self, lib, ref, x, y, rot=0, mir=None):
        self.lib, self.ref, self.x, self.y, self.rot, self.mir = lib, ref, x, y, rot, mir
        self.pins = LIBPINS[lib]
    def pos(self, n, rot=None, mir="__"):
        rot = self.rot if rot is None else rot; mir = self.mir if mir == "__" else mir
        ox, oy = tr(self.pins[n][1], self.pins[n][2], rot, mir)
        return (round(self.x + ox, 4), round(self.y + oy, 4))
    def out(self, n, rot=None, mir="__"):
        rot = self.rot if rot is None else rot; mir = self.mir if mir == "__" else mir
        a = math.radians(self.pins[n][3] + 180)
        dx, dy = tr(math.cos(a), math.sin(a), rot, mir)
        return (round(dx), round(dy))

# ------------------------------------------------------------------ leitura da placa
parts = {}
syms = [c for c in tree[1:] if isinstance(c, list) and c and val(c[0]) == "symbol"]
inst0 = find(syms[0], "instances")[0]
SHEET = val(find(inst0[1], "path")[0][1])
for c in syms:
    lib = val(find(c, "lib_id")[0][1])
    ref = [val(p[2]) for p in find(c, "property") if val(p[1]) == "Reference"][0]
    at = find(c, "at")[0]
    mir = [val(m[1]) for m in find(c, "mirror")]
    parts[ref] = (c, Part(lib, ref, float(at[1]), float(at[2]), int(float(at[3])), mir[0] if mir else None))
if "R3" in parts and "Q2" in parts:
    sys.exit("bloco já aplicado")

def netlist(path):
    with tempfile.TemporaryDirectory() as t:
        o = Path(t) / "n.xml"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(o), str(path)], capture_output=True, text=True)
        r = ET.parse(o).getroot()
    return {n.get("name").lstrip("/"): [(x.get("ref"), x.get("pin")) for x in n.findall("node")] for n in r.find("nets")}, \
           {c.get("ref"): c.findtext("value") for c in r.iter("comp")}
NETS, VALUES = netlist(PATH)
HAS_Q1 = any(p.lib == "dumper:Q_PMOS_GDS" for _, p in parts.values())
HAS_3V3 = "+3V3" in NETS and any(r not in ("A1",) for r, _ in NETS["+3V3"])
switched = {rp for rp in NETS.get("+5V", []) if not rp[0].startswith(KEEP_REFS)}

# ------------------------------------------------------------------ +5V -> +5V_CART nos símbolos de alimentação
UF = {}
def fu(a):
    while UF.setdefault(a, a) != a:
        UF[a] = UF[UF[a]]; a = UF[a]
    return a
def un(a, b): UF[fu(a)] = fu(b)
K = lambda x, y: (round(float(x), 2), round(float(y), 2))
for c in tree[1:]:
    if isinstance(c, list) and c and val(c[0]) == "wire":
        pts = find(find(c, "pts")[0], "xy")
        a, b = K(pts[0][1], pts[0][2]), K(pts[1][1], pts[1][2]); un(a, b)
pin_at = {}
for ref, (c, p) in parts.items():
    if p.lib.startswith("power:"):
        continue
    for n in p.pins:
        pin_at[K(*p.pos(n))] = (ref, n)
        fu(K(*p.pos(n)))
pw5 = []
for ref, (c, p) in parts.items():
    if p.lib == "power:+5V":
        v = [pr for pr in find(c, "property") if val(pr[1]) == "Value"][0]
        pw5.append((c, v, K(p.x, p.y)))
comp_pins = {}
for xy, rp in pin_at.items():
    comp_pins.setdefault(fu(xy), []).append(rp)
renamed = 0
for c, v, xy in pw5:
    if val(v[2]) != "+5V":
        continue
    pins = comp_pins.get(fu(xy), [])
    sw = [rp for rp in pins if rp in switched]
    if sw and len(sw) == len(pins):
        v[2] = S("VCC_CART" if SELETOR and all(rp[0] in SEL_REFS for rp in sw) else "+5V_CART"); renamed += 1
    elif sw:
        sys.exit("símbolo +5V em %s liga pinos %s: parte chaveada e parte não" % (xy, pins))
print("símbolos +5V renomeados:", renamed, "pinos chaveados:", sorted(switched))
labeled = {rp for xy, rps in comp_pins.items() for rp in rps if any(fu(xy) == fu(k) for c, v, k in pw5 if val(v[2]) in ("+5V_CART", "VCC_CART"))}
falta = switched - labeled
assert not falta, ("pinos de 5V sem símbolo próprio:", falta)

# ------------------------------------------------------------------ peças novas
OUT = []
def embed_lib(libfile, name, as_name):
    if as_name in LIBPINS:
        return
    t = parse(Path(libfile).read_text())
    blk = [c for c in t[1:] if isinstance(c, list) and c and val(c[0]) == "symbol" and val(c[1]) == name][0]
    s2 = parse(dump(blk).replace('(symbol "%s"' % name, '(symbol "%s"' % as_name, 1))
    libs.append(s2); LIBPINS[as_name] = lib_pins(s2)
embed_lib("/usr/share/kicad/symbols/Transistor_FET.kicad_sym", "2N7000", "Transistor_FET:2N7000")
embed_lib("/usr/share/kicad/symbols/Device.kicad_sym", "R", "Device:R")
embed_lib("/usr/share/kicad/symbols/Device.kicad_sym", "LED", "Device:LED")
embed_lib("/usr/share/kicad/symbols/power.kicad_sym", "PWR_FLAG", "power:PWR_FLAG")
embed_lib("/usr/share/kicad/symbols/power.kicad_sym", "+5V", "power:+5V")
embed_lib("/usr/share/kicad/symbols/power.kicad_sym", "+3V3", "power:+3V3")
embed_lib("/usr/share/kicad/symbols/power.kicad_sym", "GND", "power:GND")
if "dumper:Q_PMOS_GDS" not in LIBPINS:
    t = parse((ROOT / "boards/_lib/dumper.kicad_sym").read_text())
    blk = [c for c in t[1:] if isinstance(c, list) and c and val(c[0]) == "symbol" and val(c[1]) == "Q_PMOS_GDS"][0]
    s2 = parse(dump(blk).replace('(symbol "Q_PMOS_GDS"', '(symbol "dumper:Q_PMOS_GDS"', 1))
    libs.append(s2); LIBPINS["dumper:Q_PMOS_GDS"] = lib_pins(s2)

def last_ref(prefix):
    nums = [int(re.sub(r"\D", "", r)) for r in parts if re.fullmatch(prefix + r"\d+", r)]
    return max(nums) if nums else 0
NEXT = {"R": last_ref("R"), "D": last_ref("D"), "Q": last_ref("Q"), "FLG": last_ref("FLG"), "U": last_ref("U"), "C": last_ref("C"), "RN": last_ref("RN"), "F": last_ref("F"), "J": last_ref("J")}
D138 = {"novos": [], "fusivel": [], "rn": [], "bypass": []}      # peças do D138 (F1, J1, seletor, resistores em série): lidas por tools/check_netlist.py (d138.json)
PHASE = [False]
def newref(prefix):
    NEXT[prefix] += 1
    ref = "%s%d" % (prefix, NEXT[prefix])
    if PHASE[0]:
        D138["novos"].append(ref)
    return ref

def prop(n, v, x, y, hide=False, rot=0, just=None):
    j = '\t\t\t\t(justify %s)\n' % just if just else ''
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)\n%s\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n%s\t\t\t)\n\t\t)\n'
            % (n, v, f2(x), f2(y), rot, '\t\t\t(hide yes)\n' if hide else '', j))

def orient(lib, want):
    p = Part(lib, "?", 0, 0)
    for mir in (None, "x", "y"):
        for rot in (0, 90, 180, 270):
            if all(p.out(n, rot, mir) == d for n, d in want.items()):
                return rot, mir
    raise SystemExit("sem orientação %s %s" % (lib, want))

def add(lib, ref, value, fp, pin, at, want, desc="", dnp=False):
    """põe a peça com o pino `pin` em `at` e as saídas `want` {pino: (dx, dy)}"""
    rot, mir = orient(lib, want)
    p = Part(lib, ref, 0, 0, rot, mir)
    ox, oy = p.pos(pin)
    p.x, p.y = round(at[0] - ox, 4), round(at[1] - oy, 4)
    t = ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s %d)\n' % (lib, f2(p.x), f2(p.y), rot))
    if mir: t += '\t\t(mirror %s)\n' % mir
    t += ('\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp %s)\n\t\t(uuid "%s")\n' % ("yes" if dnp else "no", g()))
    xs = [p.pos(n)[0] for n in p.pins]; ys = [p.pos(n)[1] for n in p.pins]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    big = len(p.pins) > 2
    t += prop("Reference", ref, max(xs) + 1.5 if big else cx + 2.2, (min(ys) + 1.0) if big else cy - 1.0, just="left")
    t += prop("Value", value, max(xs) + 1.5 if big else cx + 2.2, (min(ys) + 3.5) if big else cy + 1.0, just="left")
    t += prop("Footprint", fp, p.x, p.y, True) + prop("Datasheet", "", p.x, p.y, True) + prop("Description", desc, p.x, p.y, True)
    for n in p.pins:
        t += '\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)\n' % (n, g())
    t += '\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (SHEET, ref)
    OUT.append(t)
    return p

def wire(a, b):
    if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
        return
    OUT.append('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (f2(a[0]), f2(a[1]), f2(b[0]), f2(b[1]), g()))
def junction(a):
    OUT.append('\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' % (f2(a[0]), f2(a[1]), g()))
def label(txt, a, out):
    ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[tuple(out)]
    j = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[ang]
    OUT.append('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (txt, f2(a[0]), f2(a[1]), ang, j, g()))
def note(txt, x, y, size=2.54):
    OUT.append('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %s %s)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (txt, f2(x), f2(y), size, size, g()))
PW = [0]
def power(net, a, out):
    """símbolo de alimentação com o pino em `a` e o corpo para `out`"""
    base = {"+5V_CART": "+5V", "VCC_CART": "+5V", "+5V_F": "+5V"}.get(net, net)
    default = (0, 1) if base == "GND" else (0, -1)
    rot = 0
    for r_ in (0, 90, 180, 270):
        r = math.radians(r_)
        d = (round(default[0] * math.cos(r) + default[1] * math.sin(r)), round(-default[0] * math.sin(r) + default[1] * math.cos(r)))
        if d == tuple(out):
            rot = r_; break
    PW[0] += 1; ref = "#PWR9%02d" % PW[0]
    x, y = a
    tx, ty, tj = {(-1, 0): (x - 3.5, y, "right"), (1, 0): (x + 3.5, y, "left"), (0, -1): (x, y - 3.8, None), (0, 1): (x, y + 4.2, None)}[tuple(out)]
    t = ('\t(symbol\n\t\t(lib_id "power:%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "%s")\n' % (base, f2(x), f2(y), rot, g()))
    t += prop("Reference", ref, x, y, True) + prop("Value", net, tx, ty, False, 0, tj)
    t += prop("Footprint", "", x, y, True) + prop("Datasheet", "", x, y, True) + prop("Description", "", x, y, True)
    t += '\t\t(pin "1"\n\t\t\t(uuid "%s")\n\t\t)\n\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (g(), SHEET, ref)
    OUT.append(t)
def pwrflag(a):
    ref = newref("FLG")
    flg = Part("power:PWR_FLAG", ref, 0, 0, 0, None)
    rot, mir = orient("power:PWR_FLAG", {"1": (0, 1)})
    flg.rot, flg.mir = rot, mir
    ox, oy = flg.pos("1"); flg.x, flg.y = round(a[0] - ox, 4), round(a[1] - oy, 4)
    t = ('\t(symbol\n\t\t(lib_id "power:PWR_FLAG")\n\t\t(at %s %s %d)\n' % (f2(flg.x), f2(flg.y), rot))
    t += ('\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "%s")\n' % g())
    t += prop("Reference", ref, a[0], a[1] + 6, True) + prop("Value", "PWR_FLAG", a[0] + 2, a[1] + 4, False, 0, "left")
    t += prop("Footprint", "", a[0], a[1], True) + prop("Datasheet", "~", a[0], a[1], True) + prop("Description", "", a[0], a[1], True)
    t += '\t\t(pin "1"\n\t\t\t(uuid "%s")\n\t\t)\n\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (g(), SHEET, ref)
    OUT.append(t)

FP_R = "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical"
FP_LED = "LED_THT:LED_D3.0mm"
FP_TO92 = "Package_TO_SOT_THT:TO-92_Inline"
FP_TO220 = "Package_TO_SOT_THT:TO-220-3_Vertical"
UP, DN, LF, RT = (0, -1), (0, 1), (-1, 0), (1, 0)
U = lambda v: round(v / 1.27) * 1.27

# origem: abaixo de tudo o que existe
ally = [float(m[1]) for m in re.findall(r"\(at ([-0-9.]+) ([-0-9.]+)", text)]     # tudo o que existe no desenho (peças, fios, textos)
OX, OY = U(30.0), U(max(ally) + 45.0)
STEP = 22.86
note("Bloco de troca de cartucho (D126)", OX, OY - 22.86, 2)

def R(value, at_pin1, up_net, down_net, desc=""):
    """resistor vertical com o pino 1 em `at_pin1`; `up_net`/`down_net` são ('pwr', nome), ('lab', nome) ou None (ligado por quem chamou)"""
    ref = newref("R")
    p = add("Device:R", ref, value, FP_R, "1", at_pin1, {"1": UP, "2": DN}, desc)
    for pin, net in (("1", up_net), ("2", down_net)):
        if net is None:
            continue
        a = p.pos(pin); d = p.out(pin); e = (a[0] + d[0] * 5.08, a[1] + d[1] * 5.08)
        wire(a, e)
        (power(net[1], e, d) if net[0] == "pwr" else label(net[1], e, d))
    return p

x = OX
# --- F1: PTC de furo passante em série na trilha de potência (D138). Modo bloco: +5V -> F1 -> +5V_F -> Q1; modo fusível: +5V -> F1 -> +5V_CART
FP_F1 = "Fuse:Fuse_Bourns_MF-RHT050"
SRC_NET = "+5V"
PEND_FLAG = None
if FUSE:
    PHASE[0] = True
    embed_lib("/usr/share/kicad/symbols/Device.kicad_sym", "Polyfuse", "Device:Polyfuse")
    SRC_NET = "+5V_F" if MODO == "bloco" else "+5V_CART"
    f1 = add("Device:Polyfuse", newref("F"), "PTC 0,5 A", FP_F1, "1", (x, OY), {"1": UP, "2": DN},
             "Fusivel rearmavel (PTC) de furo passante: 0,5 A de retencao, em serie com o 5 V da placa. Queda de 0,1 a 0,2 V a 200 mA")
    a1 = f1.pos("1"); a2 = f1.pos("2")
    wire(a1, (a1[0], a1[1] - 5.08)); power("+5V", (a1[0], a1[1] - 5.08), UP)
    wire(a2, (a2[0], a2[1] + 5.08)); power(SRC_NET, (a2[0], a2[1] + 5.08), DN)
    D138["fusivel"].append(f1.ref)
    wire((a2[0], a2[1] + 5.08), (a2[0] + 5.08, a2[1] + 5.08)); PEND_FLAG = (a2[0] + 5.08, a2[1] + 5.08)      # o PTC é passivo: a rede a jusante precisa do marcador de alimentação (criado depois do bloco, para não mudar a numeração dos FLG dele)
    x += STEP
PHASE[0] = False

if MODO == "bloco":
    # --- Q1 (se a placa não tem)
    if not HAS_Q1:
        q = add("dumper:Q_PMOS_GDS", newref("Q"), "IRF9540N", FP_TO220, "2", (x, OY), {"1": LF, "2": UP, "3": DN}, "P-MOSFET: chave de alta do 5V dos slots")
        g_, d_, s_ = q.pos("1"), q.pos("2"), q.pos("3")
        wire(g_, (g_[0] - 5.08, g_[1])); label("PWR_G", (g_[0] - 5.08, g_[1]), LF)
        wire(d_, (d_[0], d_[1] - 5.08))
        # dreno em cima, fonte embaixo: +5V_CART em cima (corpo para cima) e +5V embaixo (corpo para baixo)
        power("+5V_CART", (d_[0], d_[1] - 5.08), UP)
        wire(s_, (s_[0], s_[1] + 5.08)); power(SRC_NET, (s_[0], s_[1] + 5.08), DN)
        pwrflag((d_[0] + 5.08, d_[1] - 5.08)); wire((d_[0], d_[1] - 5.08), (d_[0] + 5.08, d_[1] - 5.08))
        x += STEP
        r3 = R("100k", (x, OY), ("pwr", "+5V"), ("lab", "PWR_G"), "Mantém o gate no 5V (chave desligada) com o Mega em reset")
        x += STEP
        r4 = R("100R", (x, OY), ("lab", "PWR_EN"), ("lab", "PWR_G"), "Série do comando D19 da chave")
        x += STEP
        # R5 + LED verde: +5V_CART -> R5 -> LED -> GND
        r5 = R("1k", (x, OY), ("pwr", "+5V_CART"), None, "Limita o LED verde do 5V dos slots")
        a = r5.pos("2"); d = (0, 1)
        led = add("Device:LED", newref("D"), "LED verde 3mm", FP_LED, "2", (a[0], a[1] + 7.62), {"2": UP, "1": DN}, "LED verde: 5V dos slots ligado")
        wire(a, led.pos("2"))
        k_ = led.pos("1"); wire(k_, (k_[0], k_[1] + 5.08)); power("GND", (k_[0], k_[1] + 5.08), DN)
        x += STEP
    else:
        # a placa já tem Q1, R3 a R14.. (16_bits): só o PWR_G existente é usado
        pass

    # --- Q2 + R6 (+ R6b): descarga
    q2 = add("Transistor_FET:2N7000", newref("Q"), "2N7000", FP_TO92, "3", (x, OY), {"2": LF, "3": UP, "1": DN}, "Descarga do rail dos slots quando a chave abre")
    gp, dp, sp = q2.pos("2"), q2.pos("3"), q2.pos("1")
    wire(gp, (gp[0] - 5.08, gp[1])); label("PWR_G", (gp[0] - 5.08, gp[1]), LF)
    wire(sp, (sp[0], sp[1] + 5.08)); power("GND", (sp[0], sp[1] + 5.08), DN)
    nd = (dp[0], dp[1] - 5.08); wire(dp, nd)
    # R6: pino 2 (baixo) no nó nd, pino 1 (cima) no +5V_CART
    ref6 = newref("R")
    r6 = add("Device:R", ref6, "330R", FP_R, "2", nd, {"2": DN, "1": UP}, "Descarga do +5V_CART pelo Q2")
    t6 = r6.pos("1"); wire(t6, (t6[0], t6[1] - 5.08)); power("+5V_CART", (t6[0], t6[1] - 5.08), UP)
    if HAS_3V3:
        r6b = add("Device:R", newref("R"), "330R", FP_R, "2", (nd[0] + 10.16, nd[1]), {"2": DN, "1": UP}, "Descarga do +3V3 pelo Q2")
        wire(nd, (nd[0] + 10.16, nd[1])); junction(nd)
        t = r6b.pos("1"); wire(t, (t[0], t[1] - 5.08)); power("+3V3", (t[0], t[1] - 5.08), UP)
    x += 2 * STEP + (10.16 if HAS_3V3 else 0)

    # --- Q3 + R7 + R8 + R9 + LED amarelo: sensor do rail
    q3 = add("Transistor_FET:2N7000", newref("Q"), "2N7000", FP_TO92, "3", (x, OY), {"2": LF, "3": UP, "1": DN}, "Detector de rail baixo (limiar de 1 a 2,5 V)")
    gp, dp, sp = q3.pos("2"), q3.pos("3"), q3.pos("1")
    ng = (gp[0] - 5.08, gp[1]); wire(gp, ng)
    wire(sp, (sp[0], sp[1] + 5.08)); power("GND", (sp[0], sp[1] + 5.08), DN)
    wire(dp, (dp[0], dp[1] - 5.08)); label("SENSE", (dp[0], dp[1] - 5.08), UP)
    r7 = add("Device:R", newref("R"), "100k", FP_R, "1", (ng[0] - 7.62, ng[1] + 5.08), {"1": UP, "2": DN}, "Garante rail baixo com o rail flutuando")
    t = r7.pos("1"); wire(t, (t[0], ng[1])); wire((t[0], ng[1]), ng); junction(ng)
    e_ = (ng[0], ng[1] - 5.08); wire(ng, e_); power("+5V_CART", e_, UP)
    t2 = r7.pos("2"); wire(t2, (t2[0], t2[1] + 5.08)); power("GND", (t2[0], t2[1] + 5.08), DN)
    x += STEP + 7.62
    r8 = R("1k", (x, OY), ("pwr", "+5V"), ("lab", "SENSE"), "Pull-up do nó SENSE")
    x += STEP
    r9 = R("1k", (x, OY), ("lab", "SENSE"), ("lab", "SENSE_MCU"), "Série do sensor ao D53")
    x += STEP
    led3 = add("Device:LED", newref("D"), "LED amarelo 3mm", FP_LED, "2", (x, OY), {"2": UP, "1": DN}, "Aceso = rail dos slots abaixo de ~2 V: seguro trocar o cartucho")
    a = led3.pos("2"); wire(a, (a[0], a[1] - 5.08)); label("SENSE", (a[0], a[1] - 5.08), UP)
    k_ = led3.pos("1"); wire(k_, (k_[0], k_[1] + 5.08)); power("GND", (k_[0], k_[1] + 5.08), DN)


if PEND_FLAG:
    PHASE[0] = True; pwrflag(PEND_FLAG); PHASE[0] = False

# ------------------------------------------------------------------ seletor 3,3 V / 5 V e resistores em série (TROCA_SELETOR=1, megadrive_sms v1.1, D138)
FP_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_CP = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
FP_DIP16 = "Package_DIP:DIP-16_W7.62mm"
if SELETOR:
    PHASE[0] = True
    embed_lib("/usr/share/kicad/symbols/Regulator_Linear.kicad_sym", "AP1117-15", "Regulator_Linear:AP1117-15")
    embed_lib("/usr/share/kicad/symbols/Device.kicad_sym", "R_Pack08", "Device:R_Pack08")
    embed_lib("/usr/share/kicad/symbols/Device.kicad_sym", "C", "Device:C")
    embed_lib("/usr/share/kicad/symbols/Device.kicad_sym", "C_Polarized", "Device:C_Polarized")
    x += 2 * STEP
    note("Seletor de tensao do cartucho: 3,3 V (LDO) ou 5 V (derivacao do LDO pelo Q4); D18 em nivel baixo = 5 V, solto = 3,3 V (D138)", x, OY - 22.86, 2)
    def C(lib, value, fp, at_pin1, up_net, down_net, desc=""):
        ref = newref("C")
        p_ = add(lib, ref, value, fp, "1", at_pin1, {"1": UP, "2": DN}, desc)
        for pin, net in (("1", up_net), ("2", down_net)):
            a_ = p_.pos(pin); d_ = p_.out(pin); e2 = (a_[0] + d_[0] * 5.08, a_[1] + d_[1] * 5.08)
            wire(a_, e2); power(net, e2, d_)
        return p_
    # LDO 3,3 V (LD1117V33, TO-220): VI no +5V_CART (saída do Q1), VO no VCC_CART (trilho do cartucho)
    print("pinos do LDO:", LIBPINS["Regulator_Linear:AP1117-15"])
    u2 = add("Regulator_Linear:AP1117-15", newref("U"), "LD1117V33", FP_TO220, "3", (x, OY), {"3": LF, "2": RT, "1": DN}, "LDO de 3,3 V (TO-220) para o VCC dos cartuchos de 3,3 V")
    vi, vo, gn = u2.pos("3"), u2.pos("2"), u2.pos("1")
    wire(vi, (vi[0] - 5.08, vi[1])); power("+5V_CART", (vi[0] - 5.08, vi[1]), LF)
    wire(vo, (vo[0] + 5.08, vo[1])); power("VCC_CART", (vo[0] + 5.08, vo[1]), RT)
    wire(gn, (gn[0], gn[1] + 5.08)); power("GND", (gn[0], gn[1] + 5.08), DN)
    x += STEP + 7.62
    C("Device:C", "100n", FP_C, (x, OY), "+5V_CART", "GND", "Desacoplamento da entrada do LDO")
    x += STEP
    C("Device:C_Polarized", "10u/16V", FP_CP, (x, OY), "VCC_CART", "GND", "Capacitor de saida do LDO (o LD1117 pede 10 uF ou mais)")
    x += STEP
    # Q4: P-MOSFET que liga o +5V_CART direto ao VCC_CART (deriva o LDO): conduz = 5 V; aberto = 3,3 V do LDO
    q4 = add("dumper:Q_PMOS_GDS", newref("Q"), "IRF9540N", FP_TO220, "2", (x, OY), {"1": LF, "2": UP, "3": DN}, "P-MOSFET: 5 V nos slots (deriva o LDO); aberto = 3,3 V")
    D138["bypass"].append(q4.ref)
    g4, d4, s4 = q4.pos("1"), q4.pos("2"), q4.pos("3")
    wire(g4, (g4[0] - 5.08, g4[1])); label("VSEL_G", (g4[0] - 5.08, g4[1]), LF)
    wire(d4, (d4[0], d4[1] - 5.08)); power("VCC_CART", (d4[0], d4[1] - 5.08), UP)
    wire(s4, (s4[0], s4[1] + 5.08)); power("+5V_CART", (s4[0], s4[1] + 5.08), DN)
    x += STEP
    R("100k", (x, OY), ("pwr", "+5V_CART"), ("lab", "VSEL_G"), "Mantem o gate do Q4 na fonte dele (Q4 aberto = 3,3 V) com o Mega em reset")
    x += STEP
    R("1k", (x, OY), ("lab", "VSEL_EN"), ("lab", "VSEL_G"), "Serie do comando D18 do seletor; com J1 fechado limita a corrente do pino a 5 mA")
    x += STEP
    # J1: jumper de 2 pinos "TRAVA 3,3 V": fechado prende o gate do Q4 na fonte dele (+5V_CART), Q4 nunca conduz e o 5 V fica impossivel, mesmo com erro de software
    embed_lib("/usr/share/kicad/symbols/Connector_Generic.kicad_sym", "Conn_01x02", "Connector_Generic:Conn_01x02")
    j1 = add("Connector_Generic:Conn_01x02", newref("J"), "TRAVA 3,3 V", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "1", (x, OY), {"1": LF, "2": LF},
             "Jumper opcional TRAVA 3,3 V: fechado, o gate do Q4 fica preso no 5 V e o slot nunca passa de 3,3 V")
    ja, jb = j1.pos("1"), j1.pos("2")
    wire(ja, (ja[0] - 5.08, ja[1])); label("VSEL_G", (ja[0] - 5.08, ja[1]), LF)
    wire(jb, (jb[0] - 5.08, jb[1])); power("+5V_CART", (jb[0] - 5.08, jb[1]), LF)
    x += STEP
    # Q5 + R 220: carga de 15 mA no VCC_CART so no modo 3,3 V (gate no VSEL_G: alto = 3,3 V), para absorver a corrente que os sinais de 5 V injetam
    q5 = add("Transistor_FET:2N7000", newref("Q"), "2N7000", FP_TO92, "3", (x, OY), {"2": LF, "3": UP, "1": DN}, "Carga que segura o VCC_CART em 3,3 V quando os sinais de 5 V injetam corrente")
    g5, d5, s5 = q5.pos("2"), q5.pos("3"), q5.pos("1")
    wire(g5, (g5[0] - 5.08, g5[1])); label("VSEL_G", (g5[0] - 5.08, g5[1]), LF)
    wire(s5, (s5[0], s5[1] + 5.08)); power("GND", (s5[0], s5[1] + 5.08), DN)
    nd5 = (d5[0], d5[1] - 5.08); wire(d5, nd5)
    r10 = add("Device:R", newref("R"), "220R", FP_R, "2", nd5, {"2": DN, "1": UP}, "Carga do VCC_CART no modo 3,3 V")
    t10 = r10.pos("1"); wire(t10, (t10[0], t10[1] - 5.08)); power("VCC_CART", (t10[0], t10[1] - 5.08), UP)
    x += 2 * STEP

    # ---- resistores de 470 ohms em série entre o Mega e os slots (opção B): redes isoladas de 8 resistores (DIP-16)
    slot_pin_end = {}
    for sref in SEL_SLOTS:
        sp_ = parts[sref][1]
        for n_ in sp_.pins:
            slot_pin_end[K(*sp_.pos(n_))] = (sref, n_)
    split, skipped = [], []
    for n, nodes in NETS.items():
        if n.startswith(("+", "GND", "unconnected")) or not any(r == "A1" for r, _ in nodes) or not any(r in SEL_SLOTS for r, _ in nodes):
            continue
        outros = sorted({r for r, _ in nodes if r != "A1" and not SLOT_RE.match(r) and not r.startswith("TP")})
        (skipped if outros else split).append((n, outros))        # rede que liga outra peça (Si5351, PIC, pull-up, TVS): sem resistor em série
    for n, outros in skipped:
        print("  SEM resistor em série:", n, "(liga também", ", ".join(outros) + ")")
    D138["sem_serie"] = [n for n, _ in skipped]
    D138["slots_sel"] = list(SEL_SLOTS)
    split = sorted((n for n, _ in split), key=lambda n: (n[0], int(re.sub(r"\D", "", n) or 0), n))
    nlab = 0
    for c in tree[1:]:
        if isinstance(c, list) and c and val(c[0]) == "label":
            nm = val(c[1])
            at = find(c, "at")[0]
            if K(at[1], at[2]) in slot_pin_end and nm in split:
                c[1] = S(nm + "_S"); nlab += 1
    expected = sum(1 for n in split for r, _ in NETS[n] if r in SEL_SLOTS)
    print("resistores em série:", len(split), "nets;", nlab, "rótulos de slot renomeados de", expected, "pinos de slot")
    assert nlab == expected, ("rótulos de slot não achados", nlab, expected)
    RN_PINS = LIBPINS["Device:R_Pack08"]
    print("pinos da R_Pack08:", RN_PINS)
    OY2 = OY + 60.96
    xr = OX
    for k in range(0, len(split), 8):
        grp = split[k:k + 8]
        rn = add("Device:R_Pack08", newref("RN"), "470R", FP_DIP16, "1", (xr, OY2), {"1": LF, "16": RT}, "Resistores em serie de 470 ohms: protegem cartuchos de 3,3 V das saidas de 5 V do Mega")
        for i, nm in enumerate(grp, start=1):
            for pin, suf in ((str(i), ""), (str(17 - i), "_S")):
                a_ = rn.pos(pin); d_ = rn.out(pin); e2 = (a_[0] + d_[0] * 5.08, a_[1] + d_[1] * 5.08)
                wire(a_, e2); label(nm + suf, e2, d_)
        for i in range(len(grp) + 1, 9):         # pinos livres da última rede: marca de não conexão
            for pin in (str(i), str(17 - i)):
                a_ = rn.pos(pin)
                OUT.append('\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)\n' % (f2(a_[0]), f2(a_[1]), g()))
        D138["rn"].append(rn.ref)
        xr += 6 * STEP
    PHASE[0] = False

# --- rótulos nos pinos D19 e D53 do Mega (no lugar dos símbolos de "sem ligação")
A1 = parts["A1"][1]
nc_names = {}
for n, nodes in NETS.items():
    for r, pn in nodes:
        if r == "A1" and n.startswith("unconnected-"):
            nc_names[pn] = n
alvo = {"D19": "PWR_EN", "D53": "SENSE_MCU"}
if SELETOR:
    alvo["D18"] = "VSEL_EN"
if MODO != "bloco":
    alvo = {}
if HAS_Q1:
    alvo.pop("D19")            # a placa já liga o D19 ao PWR_EN
for pin, net in alvo.items():
    assert pin in nc_names, ("pino do Mega ocupado:", pin)
body = [c for c in tree[1:] if not (isinstance(c, list) and c and val(c[0]) == "no_connect")]
ncs = [c for c in tree[1:] if isinstance(c, list) and c and val(c[0]) == "no_connect"]
keep_nc = []
for c in ncs:
    at = find(c, "at")[0]; xy = K(at[1], at[2])
    hit = [pin for pin in alvo if K(*A1.pos(pin)) == xy]
    if hit:
        label(alvo[hit[0]], A1.pos(hit[0]), A1.out(hit[0]))
    else:
        keep_nc.append(c)
assert len(ncs) - len(keep_nc) == len(alvo), "no_connect do Mega não achado"

# ------------------------------------------------------------------ saída
head = [c for c in tree[1:] if not (isinstance(c, list) and c and val(c[0]) == "no_connect")]
idx = next(i for i, c in enumerate(head) if isinstance(c, list) and c and val(c[0]) == "sheet_instances")
final = "(kicad_sch\n"
for c in head[:idx]: final += "\t" + dump(c, 1) + "\n"
for c in keep_nc: final += "\t" + dump(c, 1) + "\n"
final += "".join(OUT)
for c in head[idx:]: final += "\t" + dump(c, 1) + "\n"
final += ")\n"
if len(sys.argv) > 2:
    final = re.sub(r'\(rev "[^"]*"\)', '(rev "%s")' % sys.argv[2], final, count=1)      # versão no carimbo
PATH.write_text(final)
import json as _json
(PATH.parent / "d138.json").write_text(_json.dumps(D138, indent=1))
print("ok", PATH, "símbolos novos:", sum(1 for t in OUT if t.startswith("\t(symbol")))
