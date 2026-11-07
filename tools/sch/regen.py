#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Refaz o desenho de um esquemático do projeto para leitura humana, sem mudar a netlist:
fios diretos nos circuitos locais (LED, resistores e capacitores em série, Si5351, PIC, regulador, pull-ups),
símbolos de alimentação (+5V, +3V3, GND) nos pinos de alimentação e rótulos de net só nos barramentos longos
entre o Mega e os slots. Preserva símbolos, referências, valores e UUIDs; só muda posição, rotação e as ligações desenhadas.
Uso: python3 tools/sch/regen.py boards/<placa>/hardware/dumper.kicad_sch   (reescreve o arquivo; precisa de kicad-cli)"""
import math, re, subprocess, sys, tempfile, uuid
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sexp import parse, dump, val, find, S

PATH = Path(sys.argv[1]).resolve()
RAILS = {"+5V", "+3V3", "GND", "+5V_CART"}
PWR_LIB = {"GND": "GND", "+5V": "+5V", "+3V3": "+3V3", "+5V_CART": "+5V"}   # nome da net -> símbolo de base (o Value do símbolo é a net)
g = lambda: str(uuid.uuid4())
U = lambda x: round(x / 1.27) * 1.27
f2 = lambda v: ("%.4f" % v).rstrip("0").rstrip(".")

# ------------------------------------------------------------------ leitura
text = PATH.read_text()
tree = parse(text)
libs = find(tree, "lib_symbols")[0]
SHEET = None
for c in tree:
    if isinstance(c, list) and c and val(c[0]) == "symbol":
        inst = find(c, "instances")[0]
        SHEET = val(find(find(inst[1], "path")[0], "reference")[0][1]) if False else val(find(inst[1], "path")[0][1])
        break

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
def lib_box(sym):
    xs, ys = [], []
    def walk(n):
        for k in n:
            if isinstance(k, list) and k:
                if val(k[0]) == "rectangle":
                    a, b = find(k, "start")[0], find(k, "end")[0]
                    xs.extend([float(a[1]), float(b[1])]); ys.extend([float(a[2]), float(b[2])])
                elif val(k[0]) == "symbol": walk(k)
    walk(sym); return (min(xs), min(ys), max(xs), max(ys)) if xs else None
LIBBOX = {val(c[1]): lib_box(c) for c in libs[1:] if isinstance(c, list) and c and val(c[0]) == "symbol"}

# símbolos de alimentação (do KiCad) para o lib_symbols
pw = parse(Path("/usr/share/kicad/symbols/power.kicad_sym").read_text())
for nm in ("GND", "+5V", "+3V3"):
    lid = "power:" + nm
    if lid in LIBPINS: continue
    blk = [c for c in pw[1:] if isinstance(c, list) and c and val(c[0]) == "symbol" and val(c[1]) == nm][0]
    s2 = parse(dump(blk).replace('(symbol "%s"' % nm, '(symbol "%s"' % lid, 1).replace('"%s_0_1"' % nm, '"%s_0_1"' % nm))
    libs.append(s2); LIBPINS[lid] = lib_pins(s2)

# netlist do arquivo atual (nets -> pinos)
def netlist(path):
    with tempfile.TemporaryDirectory() as t:
        o = Path(t) / "n.xml"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(o), str(path)], capture_output=True, text=True)
        r = ET.parse(o).getroot()
    return {n.get("name"): [(x.get("ref"), x.get("pin")) for x in n.findall("node")] for n in r.find("nets")}
NETS0 = netlist(PATH)
NETOF = {}
for n, nodes in NETS0.items():
    for rp in nodes: NETOF[rp] = n.lstrip("/")
NODES = {n.lstrip("/"): v for n, v in NETS0.items()}
def kind(netname):
    if netname in RAILS: return "rail"
    if netname.startswith("unconnected-") or len(NODES.get(netname, [])) <= 1: return "nc"
    return "sig"

# ------------------------------------------------------------------ peças
class Part:
    def __init__(self, node):
        self.node = node
        self.lib = val(find(node, "lib_id")[0][1])
        self.ref = [val(p[2]) for p in find(node, "property") if val(p[1]) == "Reference"][0]
        self.value = [val(p[2]) for p in find(node, "property") if val(p[1]) == "Value"][0]
        self.pins = LIBPINS[self.lib]
        self.x = self.y = 0.0; self.rot = 0; self.mir = None; self.placed = False
    def off(self, num, rot=None, mir="__", lx=None):
        """posição do pino relativa à origem, para a transformação dada"""
        rot = self.rot if rot is None else rot; mir = self.mir if mir == "__" else mir
        _, px, py, _a = self.pins[num]
        return tr(px, py, rot, mir)
    def pos(self, num):
        ox, oy = self.off(num); return (self.x + ox, self.y + oy)
    def out(self, num, rot=None, mir="__"):
        rot = self.rot if rot is None else rot; mir = self.mir if mir == "__" else mir
        a = math.radians(self.pins[num][3] + 180)             # direção para fora do corpo (em coordenadas da biblioteca)
        dx, dy = tr(math.cos(a), math.sin(a), rot, mir)
        return (round(dx), round(dy))

def tr(px, py, rot, mir):
    if mir == "x": py = -py
    if mir == "y": px = -px
    r = math.radians(rot); c, s = round(math.cos(r), 6), round(math.sin(r), 6)
    return (px * c - py * s, -(px * s + py * c))          # já em coordenadas de tela (y para baixo)

PARTS = {}
for c in tree:
    if isinstance(c, list) and c and val(c[0]) == "symbol":
        p = Part(c); PARTS[p.ref] = p
MEGA = PARTS["A1"]
SLOTS = [p for p in PARTS.values() if p.lib.endswith("_Slot")]
OUTP = []          # itens novos: textos prontos
JUNC = []
UF = {}            # união de pinos ligados por fio/símbolo
def find_uf(a):
    while UF.setdefault(a, a) != a:
        UF[a] = UF[UF[a]]; a = UF[a]
    return a
def union(a, b): UF[find_uf(a)] = find_uf(b)
ATTACH = set()     # pinos que já têm algo ligado (fio ou símbolo de alimentação)
OCC = []           # retângulos ocupados (x0, y0, x1, y1) para evitar sobreposição grosseira

def wire(x1, y1, x2, y2):
    if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6: return
    OUTP.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f2(x1)} {f2(y1)}) (xy {f2(x2)} {f2(y2)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{g()}")\n\t)\n')
def junction(x, y):
    OUTP.append(f'\t(junction\n\t\t(at {f2(x)} {f2(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{g()}")\n\t)\n')
def noconn(x, y):
    OUTP.append(f'\t(no_connect\n\t\t(at {f2(x)} {f2(y)})\n\t\t(uuid "{g()}")\n\t)\n')
def label(txt, x, y, out):
    ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[out]
    j = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[ang]
    OUTP.append(f'\t(label "{txt}"\n\t\t(at {f2(x)} {f2(y)} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {j})\n\t\t)\n\t\t(uuid "{g()}")\n\t)\n')
def note(txt, x, y, size=2.54):
    OUTP.append(f'\t(text "{txt}"\n\t\t(exclude_from_sim no)\n\t\t(at {f2(x)} {f2(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{g()}")\n\t)\n')

PWRN = [0]
def power(netname, x, y, out):
    """símbolo de alimentação com o pino em (x, y) e o corpo apontando para `out`"""
    base = PWR_LIB[netname]
    default = (0, 1) if base == "GND" else (0, -1)           # direção do corpo na tela com rot 0
    for rot in (0, 90, 180, 270):
        r = math.radians(rot)
        d = (round(default[0] * math.cos(r) + default[1] * math.sin(r)), round(-default[0] * math.sin(r) + default[1] * math.cos(r)))
        if d == tuple(out): break
    PWRN[0] += 1; ref = f"#PWR{PWRN[0]:03d}"
    tx, ty, tj = {(-1, 0): (x - 3.5, y, "right"), (1, 0): (x + 3.5, y, "left"), (0, -1): (x, y - 3.8, "center"), (0, 1): (x, y + 4.2, "center")}[tuple(out)]
    def pr(n, v, hide):
        px, py = (tx, ty) if n == "Value" else (x, y)
        j = f"\t\t\t\t(justify {tj})\n" if n == "Value" and tj != "center" else ""
        return (f'\t\t(property "{n}" "{v}"\n\t\t\t(at {f2(px)} {f2(py)} {(360 - rot) % 360})\n' + ('\t\t\t(hide yes)\n' if hide else '') +
                '\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n' + j + '\t\t\t)\n\t\t)\n')
    OUTP.append('\t(symbol\n\t\t(lib_id "power:%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom no)\n\t\t(on_board no)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(uuid "%s")\n'
                % (base, f2(x), f2(y), rot, g()) + pr("Reference", ref, True) + pr("Value", netname, False) + pr("Footprint", "", True) + pr("Datasheet", "", True) + pr("Description", "", True)
                + f'\t\t(pin "1"\n\t\t\t(uuid "{g()}")\n\t\t)\n\t\t(instances\n\t\t\t(project "dumper"\n\t\t\t\t(path "{SHEET}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')

def setprops(p, label_xy=None):
    """posição dos textos Reference/Value perto da peça"""
    pts = [p.pos(n) for n in p.pins]
    bx = LIBBOX.get(p.lib)
    if bx and len(p.pins) > 2:
        pts += [tr(bx[0], bx[1], p.rot, p.mir), tr(bx[2], bx[3], p.rot, p.mir)]
        pts = [pt if i < len(p.pins) else (p.x + pt[0], p.y + pt[1]) for i, pt in enumerate(pts)]
    xs = [a for a, _ in pts]; ys = [b for _, b in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    horiz = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    for pr in find(p.node, "property"):
        n = val(pr[1])
        at = find(pr, "at")[0]
        big = len(p.pins) > 2
        if big:
            if n == "Reference": pos = (max(xs) + 1.5, min(ys) + 1.0)
            elif n == "Value": pos = (max(xs) + 1.5, min(ys) + 3.5)
            else: pos = (cx, cy)
        elif n == "Reference": pos = (cx, cy - 3.0) if horiz else (cx + 2.2, cy - 1.0)
        elif n == "Value": pos = (cx, cy + 3.0) if horiz else (cx + 2.2, cy + 1.0)
        else: pos = (cx, cy)
        at[1], at[2], at[3] = f2(pos[0]), f2(pos[1]), str((360 - p.rot) % 360)
        if n in ("Reference", "Value") and (len(p.pins) > 2 or not horiz):
            eff = find(pr, "effects")[0]
            for j in find(eff, "justify"): eff.remove(j)
            eff.append(["justify", "left"])

def put(p, x, y, rot=0, mir=None):
    p.x, p.y, p.rot, p.mir, p.placed = x, y, rot, mir, True
    at = find(p.node, "at")[0]; at[1], at[2], at[3] = f2(x), f2(y), str(rot)
    for m in find(p.node, "mirror"): p.node.remove(m)
    if mir:
        p.node.insert(p.node.index(at) + 1, ["mirror", mir])
    setprops(p)
    for n in p.pins: OCC.append(p.pos(n))

def orient(p, want):
    """acha (rot, mir) tal que out(pino) == direção, para cada par {pino: (dx, dy)}"""
    for mir in (None, "x", "y"):
        for rot in (0, 90, 180, 270):
            if all(p.out(n, rot, mir) == d for n, d in want.items()): return rot, mir
    raise SystemExit(f"{p.ref}: sem orientação para {want}")

def place_at_pin(p, num, x, y, want):
    """põe a peça `p` com o pino `num` exatamente em (x, y) e as direções `want`"""
    rot, mir = orient(p, want)
    ox, oy = p.off(num, rot, mir)
    put(p, round(x - ox, 4), round(y - oy, 4), rot, mir)
    return p.pos(num)

def connect_rail(p, num, x=None, y=None):
    """símbolo de alimentação no pino (se a net do pino é um trilho)"""
    n = NETOF[(p.ref, num)]
    x, y = p.pos(num) if x is None else (x, y)
    power(n, x, y, p.out(num)); ATTACH.add((p.ref, num)); OCC.append((x, y))

def two_pins(p):
    ks = sorted(p.pins, key=lambda k: int(k) if k.isdigit() else 99)
    return ks

def net_other(p, num):
    """pino do outro lado de um componente de 2 pinos"""
    ks = [k for k in p.pins if k != num]
    return ks[0] if len(ks) == 1 else None

def label_pin(p, num):
    n = NETOF[(p.ref, num)]
    x, y = p.pos(num); label(n, x, y, p.out(num)); ATTACH.add((p.ref, num))

def is_two_term(p):
    return len(p.pins) == 2 and not p.lib.startswith("power:")

# ------------------------------------------------------------------ layout
# Mega
mega_pins = {v[0]: k for k, v in MEGA.pins.items()}     # nome -> número (no Mega o nome é igual ao número)
ys = sorted({v[2] for v in MEGA.pins.values()})
top_y = max(ys)
XM = 114.3
YM = 76.2 + top_y                        # o topo do símbolo fica em y = 76.2 (pino mais alto = YM - top)
put(MEGA, XM, YM, 0, None)
def mpin(name):
    return MEGA.pos(mega_pins[name]), MEGA.out(mega_pins[name])

done_nets_local = set()

# --- cadeias de 2 terminais a partir de um pino (Mega ou slot) --------------------------------
def chain(start_p, start_num, parts_spec, gap=5.08, stagger=0.0, rail_end=True):
    """parts_spec: [(Part, entry_pin)]; cada peça entra pelo `entry_pin` e sai pelo outro; o pino final liga ao trilho se for trilho"""
    (x, y), d = start_p.pos(start_num), start_p.out(start_num)
    cx, cy = x + d[0] * (gap + stagger), y + d[1] * (gap + stagger)
    wire(x, y, cx, cy); ATTACH.add((start_p.ref, start_num))
    prev = (start_p, start_num)
    for part, ent in parts_spec:
        ex = net_other(part, ent)
        px, py = place_at_pin(part, ent, cx, cy, {ent: (-d[0], -d[1]), ex: d})
        union((prev[0].ref, prev[1]), (part.ref, ent)); ATTACH.add((part.ref, ent))
        ex_xy = part.pos(ex); ATTACH.add((part.ref, ex))
        prev = (part, ex)
        cx, cy = ex_xy[0] + d[0] * gap, ex_xy[1] + d[1] * gap
        last_end = ex_xy
        nxt = parts_spec[parts_spec.index((part, ent)) + 1] if parts_spec.index((part, ent)) + 1 < len(parts_spec) else None
        if nxt is not None: wire(ex_xy[0], ex_xy[1], cx, cy)
    return prev

def end_rail(prev):
    part, num = prev
    n = NETOF[(part.ref, num)]
    if kind(n) == "rail":
        connect_rail(part, num)
        return True
    return False

# ---- regra: LED/resistor/chave em cadeia a partir de um pino do Mega cuja net só tem ele e uma peça de 2 terminais
def auto_chain(owner, num):
    key = (owner.ref, num)
    spec = []; cur = key
    seen = {owner.ref}
    while True:
        n = NETOF[cur]
        others = [rp for rp in NODES[n] if rp != cur]
        if len(others) != 1: break
        r, pn = others[0]
        q = PARTS.get(r)
        if q is None or not is_two_term(q) or r in seen or q.placed: break
        seen.add(r); spec.append((q, pn)); cur = (r, net_other(q, pn))
        if kind(NETOF[cur]) == "rail": break
    return spec

placed_chain_pins = set()
def do_chain_at(owner, num, spec, gap=5.08, stagger=0.0):
    prev = chain(owner, num, spec, gap, stagger)
    if not end_rail(prev):
        # fim da cadeia numa net com outros pinos: rótulo na saída
        pt, pn = prev
        n = NETOF[(pt.ref, pn)]
        if kind(n) == "sig" and len({rp for rp in NODES[n]}) > 1 and len(NODES[n]) > 1:
            pass
    return prev

# Mega: lado direito, linhas com cadeia automática
mega_names = sorted(MEGA.pins, key=lambda k: -MEGA.pos(k)[1])
right_pins = [k for k in MEGA.pins if MEGA.out(k) == (1, 0)]
left_pins = [k for k in MEGA.pins if MEGA.out(k) == (-1, 0)]
def satellite(owner_ref, num, stagger=0.0):
    """resistor/TVS de 2 terminais ligado à net deste pino e a um trilho, ainda sem posição: vira uma cadeia a partir do pino"""
    n = NETOF[(owner_ref, num)]
    for r, pn in sorted(NODES[n]):
        q = PARTS.get(r)
        if q is None or q.placed or not is_two_term(q) or q.lib.startswith("Connector") or q.lib.startswith("Switch"): continue
        other = net_other(q, pn)
        if kind(NETOF[(r, other)]) != "rail": continue
        prev = chain(PARTS[owner_ref], num, [(q, pn)], 7.62, stagger)
        end_rail(prev)
        return True
    return False

prev_y = [None, 0]
done_pin = set()
for k in sorted(right_pins + left_pins, key=lambda k: MEGA.pos(k)[1]):
    n = NETOF[(MEGA.ref, k)]
    if kind(n) != "sig": continue
    spec = auto_chain(MEGA, k)
    if spec and not any(q.lib.startswith("dumper:") for q, _ in spec):
        y = MEGA.pos(k)[1]
        # linhas vizinhas: desloca em três colunas para os textos das peças não se sobreporem
        prev_y[1] = prev_y[1] + 1 if prev_y[0] is not None and abs(y - prev_y[0] - 2.54) < 0.01 else 0
        prev_y[0] = y
        prev = do_chain_at(MEGA, k, spec, 7.62, (prev_y[1] % 3) * 20.32)
        done_pin.add(k)
        pt, pn = prev
        if kind(NETOF[(pt.ref, pn)]) == "sig":
            label_pin(pt, pn)
            satellite(pt.ref, pn, 7.62)

# satélites diretamente nos pinos do Mega (por exemplo o pull-up do D7)
for k in sorted(right_pins + left_pins, key=lambda k: MEGA.pos(k)[1]):
    if k in done_pin or kind(NETOF[(MEGA.ref, k)]) != "sig": continue
    if satellite(MEGA.ref, k, 0.0): label_pin(MEGA, k)

# --- Si5351 ao lado de D20/D21 ---------------------------------------------------------------
SI = PARTS.get("U1") if PARTS.get("U1") and PARTS["U1"].lib == "dumper:Si5351_Module" else None
PIC = next((p for p in PARTS.values() if "PIC12F629" in p.lib), None)
def mega_row(name): return mpin(name)[0]
XR = XM + 17.78            # x dos pinos da direita do Mega
if SI:
    (ex, ey), _ = mpin("D20")
    sx = XR + 50.8
    put(SI, round(sx + 11.43, 4), round(ey + 2.54, 4), 0, None)      # pino 3 (SDA) na altura do D20
    for mn, pn in (("D20", "3"), ("D21", "4")):
        a = mpin(mn)[0]; b = SI.pos(pn)
        wire(a[0], a[1], b[0], b[1]); union((MEGA.ref, mega_pins[mn]), (SI.ref, pn)); ATTACH |= {(MEGA.ref, mega_pins[mn]), (SI.ref, pn)}
    connect_rail(SI, "1"); connect_rail(SI, "2")
if PIC:
    (ex, ey), _ = mpin("D40")
    # espelhado: pinos 2, 3, 4 (CLK2, D41, D40) na esquerda; pino 4 na altura do D40
    ref_pin = PIC.pins
    px = XR + 50.8
    rot, mir = 0, "y"
    ox, oy = PIC.off("4", rot, mir)
    put(PIC, round(px - ox, 4), round(ey - oy, 4), rot, mir)
    for mn, pn in (("D40", "4"), ("D41", "3")):
        a = mpin(mn)[0]; b = PIC.pos(pn)
        wire(a[0], a[1], b[0], b[1]); union((MEGA.ref, mega_pins[mn]), (PIC.ref, pn)); ATTACH |= {(MEGA.ref, mega_pins[mn]), (PIC.ref, pn)}
    connect_rail(PIC, "1"); connect_rail(PIC, "8")
    # CLK2: Si5351 -> PIC direto
    if SI:
        a = SI.pos("5"); b = PIC.pos("2")
        xv = a[0] - 6.35
        wire(a[0], a[1], xv, a[1]); wire(xv, a[1], xv, b[1]); wire(xv, b[1], b[0], b[1])
        union((SI.ref, "5"), (PIC.ref, "2")); ATTACH |= {(SI.ref, "5"), (PIC.ref, "2")}

# --- slots ---------------------------------------------------------------------------------
XS = XR + 50.8 + 40
slot_w = {}
for s in SLOTS:
    xs = [v[1] for v in s.pins.values()]; slot_w[s.ref] = (max(xs) - min(xs))
cur_x = XS + 60
for s in sorted(SLOTS, key=lambda p: p.ref):
    top = max(v[2] for v in s.pins.values())
    put(s, round(cur_x / 1.27) * 1.27, round(76.2 + top, 4), 0, None)
    cur_x += slot_w[s.ref] + 60

# --- retorno: pinos restantes do Mega e dos slots (rótulos, alimentação, sem ligação) -------------
def finish_pins(p):
    for num in p.pins:
        if (p.ref, num) in ATTACH: continue
        n = NETOF[(p.ref, num)]
        k = kind(n)
        if k == "rail": connect_rail(p, num)
        elif k == "nc": x, y = p.pos(num); noconn(x, y); ATTACH.add((p.ref, num))
        else: pass   # sinais: rótulo decidido depois
finish_pins(MEGA)
for s in SLOTS: finish_pins(s)

for _p in list(PARTS.values()):
    if _p.placed and _p is not MEGA and _p not in SLOTS: finish_pins(_p)
# --- peças restantes: blocos de alimentação e solitárias ---------------------------------------------
rest = [p for p in PARTS.values() if not p.placed]
YP = U(76.2 + 2 * top_y + 30)        # abaixo do Mega
cx = U(40.0)
def next_slot(w):
    global cx
    r = cx; cx += w; return r
regs = [p for p in rest if p.lib.startswith("Regulator_Linear")]
caps = [p for p in rest if p.lib in ("Device:C", "Device:C_Polarized")]
for p in regs:
    # regulador: IN à esquerda, OUT à direita, GND embaixo
    pin_in = next(k for k, v in p.pins.items() if v[0] in ("VI", "VIN", "IN"))
    pin_out = next(k for k, v in p.pins.items() if v[0] in ("VO", "VOUT", "OUT"))
    pin_gnd = next(k for k, v in p.pins.items() if v[0] == "GND")
    x0 = next_slot(80)
    place_at_pin(p, pin_in, U(x0 + 25.4), U(YP + 30), {pin_in: (-1, 0), pin_out: (1, 0), pin_gnd: (0, 1)})
    for num in (pin_in, pin_out, pin_gnd): pass
    # nós: entrada e saída com capacitores de 1u em paralelo
    cin = next((c for c in caps if NETOF[(c.ref, "1")] == "+5V" and c.value.lower().startswith("1u")), None)
    cout = [c for c in caps if NETOF[(c.ref, "1")] == "+3V3"]
    pi = p.pos(pin_in); po = p.pos(pin_out); pg = p.pos(pin_gnd)
    nx = pi[0] - 7.62
    wire(pi[0], pi[1], nx, pi[1]); ATTACH.add((p.ref, pin_in)); ATTACH.add((p.ref, pin_out)); ATTACH.add((p.ref, pin_gnd))
    power("+5V", nx, pi[1], (0, -1)); junction(nx, pi[1])
    connect_ref = []
    if cin:
        cp = place_at_pin(cin, "1", nx, pi[1], {"1": (0, -1), "2": (0, 1)}); connect_rail(cin, "2"); ATTACH.add((cin.ref, "1")); caps.remove(cin)
    mx = po[0] + 7.62
    wire(po[0], po[1], mx, po[1]); power("+3V3", mx, po[1], (0, -1)); junction(mx, po[1])
    first = True
    for i, c in enumerate(sorted(cout, key=lambda q: q.ref)):
        xx = mx + i * 10.16
        if i: wire(xx - 10.16, po[1], xx, po[1])
        place_at_pin(c, "1", xx, po[1], {"1": (0, -1), "2": (0, 1)}); connect_rail(c, "2"); ATTACH.add((c.ref, "1")); caps.remove(c)
        if i < len(cout) - 1 or i > 0: junction(xx, po[1])
    # GND do regulador
    power("GND", pg[0], pg[1], (0, 1))
    note("Regulador 3,3 V", x0, YP - 2.54)

def stack_two_term(p, rail_top, rail_bot, x):
    pass

# TestPoint de uma net de trilho / sinal, 1 pino
for p in list(rest):
    pass

# capacitores restantes entre trilhos: pilha vertical
cx2 = 40.0
rest_caps = [c for c in caps if not c.placed]
YC = U(YP + 70)
for i, c in enumerate(sorted(rest_caps, key=lambda q: q.ref)):
    n1, n2 = NETOF[(c.ref, "1")], NETOF[(c.ref, "2")]
    x = U(40.0 + i * 15.24)
    place_at_pin(c, "1", x, YC, {"1": (0, -1), "2": (0, 1)})
    connect_rail(c, "1"); connect_rail(c, "2")
note("Capacitores", U(40.0), YC - 8.0)

# demais peças soltas: cada pino com símbolo de alimentação, rótulo ou sem ligação
rest = [p for p in PARTS.values() if not p.placed]
yy = U(YC + 40)
xx = U(40.0)
for p in rest:
    if len(p.pins) == 1:
        num = next(iter(p.pins)); n = NETOF[(p.ref, num)]
        if kind(n) == "rail":
            put(p, xx, yy, 0, None)
            # cadeia: símbolo de alimentação ligado por fio
            a = p.pos(num); b = (a[0], a[1] + 5.08)
            put(p, xx, yy, 180 if n != "GND" else 0, None) if False else None
        else: put(p, xx, yy, 0, None)
    else:
        put(p, xx, yy, 0, None)
    for num in p.pins:
        if (p.ref, num) in ATTACH: continue
        n = NETOF[(p.ref, num)]
        if kind(n) == "rail": connect_rail(p, num)
        elif kind(n) == "nc": x, y = p.pos(num); noconn(x, y)
    xx += 25.4

# --- rótulos das nets de sinal ainda separadas ---------------------------------------------------------
groups = defaultdict(lambda: defaultdict(list))
for (ref, num), n in NETOF.items():
    if ref not in PARTS or kind(n) != "sig": continue
    groups[n][find_uf((ref, num))].append((ref, num))
for n, comps in groups.items():
    if len(comps) < 2:
        continue
    for root, pinsl in comps.items():
        # um rótulo por grupo, de preferência num slot ou no Mega
        pick = sorted(pinsl, key=lambda rp: (0 if PARTS[rp[0]].lib.endswith("_Slot") else 1 if rp[0] == "A1" else 2))[0]
        label_pin(PARTS[pick[0]], pick[1])
for n, comps in groups.items():
    pass

# ------------------------------------------------------------------ saída
drop = ("label", "no_connect", "wire", "junction", "text")
head = [c for c in tree[1:] if not (isinstance(c, list) and c and val(c[0]) in drop + ("symbol",))]
syms = [c for c in tree[1:] if isinstance(c, list) and c and val(c[0]) == "symbol"]
idx = next(i for i, c in enumerate(head) if isinstance(c, list) and c and val(c[0]) == "sheet_instances")
final = "(kicad_sch\n"
for c in head[:idx]: final += "\t" + dump(c, 1) + "\n"
for c in syms: final += "\t" + dump(c, 1) + "\n"
final += "".join(OUTP)
for c in head[idx:]: final += "\t" + dump(c, 1) + "\n"
final += ")\n"
PATH.write_text(final)
print("ok", PATH, "fios:", sum(1 for t in OUTP if t.startswith("\t(wire")), "rótulos:", sum(1 for t in OUTP if t.startswith("\t(label")))
