#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v1.2 sem os 12 TVS das linhas de controle (D3 a D14; pedido do usuário, 2026-11-08, D130). A v1.3 continua com eles.
Tira os diodos do esquemático (com a poda de fios e símbolos de alimentação órfãos, como em sem_chave.py) e do PCB
(com as trilhas e vias que ficariam soltas) e refaz o preenchimento das zonas. Os resistores série R3 a R14 ficam.
Uso: python3 tools/16_bits/sem_tvs.py sch boards/16_bits/hardware-v1.2/dumper.kicad_sch
     <python do venv do KiCad MCP> tools/16_bits/sem_tvs.py pcb boards/16_bits/hardware-v1.2/dumper.kicad_pcb"""
import sys
from pathlib import Path
SAIR = tuple(f"D{n}" for n in range(3, 15))

if sys.argv[1] == "sch":
    import math
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sch"))
    from sexp import parse, dump, val, find, S
    p = Path(sys.argv[2]); tree = parse(p.read_text())
    libs = find(tree, "lib_symbols")[0]

    def lib_pins(sym):
        out = {}
        def walk(n):
            for k in n:
                if isinstance(k, list) and k:
                    if val(k[0]) == "pin":
                        at = find(k, "at")[0]; out[val(find(k, "number")[0][1])] = (float(at[1]), float(at[2]))
                    elif val(k[0]) == "symbol": walk(k)
        walk(sym); return out
    LP = {val(c[1]): lib_pins(c) for c in libs[1:] if isinstance(c, list) and c and val(c[0]) == "symbol"}
    K = lambda x, y: (round(float(x), 2), round(float(y), 2))

    def pin_xy(c):
        lib = val(find(c, "lib_id")[0][1]); at = find(c, "at")[0]
        x, y, rot = float(at[1]), float(at[2]), int(float(at[3]))
        mir = [val(m[1]) for m in find(c, "mirror")]; mir = mir[0] if mir else None
        r = math.radians(rot); cs, sn = round(math.cos(r), 6), round(math.sin(r), 6)
        out = []
        for px, py in LP[lib].values():
            if mir == "x": py = -py
            if mir == "y": px = -px
            out.append(K(x + px * cs - py * sn, y - (px * sn + py * cs)))
        return out

    kept = []; tira = 0
    for c in tree[1:]:
        if isinstance(c, list) and c and val(c[0]) == "symbol":
            ref = [val(q[2]) for q in find(c, "property") if val(q[1]) == "Reference"][0]
            if ref in SAIR:
                tira += 1; continue
            for q in find(c, "property"):
                pass
        kept.append(c)
    # poda: fios soltos, símbolos de alimentação órfãos e junções sem fio
    def is_sym(c): return isinstance(c, list) and c and val(c[0]) == "symbol"
    def refof(c): return [val(q[2]) for q in find(c, "property") if val(q[1]) == "Reference"][0]
    while True:
        wires = [c for c in kept if isinstance(c, list) and c and val(c[0]) == "wire"]
        ends = {}
        for w in wires:
            pts = find(find(w, "pts")[0], "xy"); a, b = K(pts[0][1], pts[0][2]), K(pts[1][1], pts[1][2])
            ends.setdefault(a, []).append(id(w)); ends.setdefault(b, []).append(id(w))
        real = set(); power = {}
        for c in kept:
            if is_sym(c):
                if refof(c).startswith("#PWR"):
                    for xy in pin_xy(c): power.setdefault(xy, []).append(id(c))
                else:
                    real.update(pin_xy(c))
            elif isinstance(c, list) and c and val(c[0]) in ("label", "no_connect", "junction"):
                at = find(c, "at")[0]; real.add(K(at[1], at[2]))
        def touches(pt, me):
            return pt in real or any(i != me for i in ends.get(pt, [])) or (pt in power)
        drop = set()
        for w in wires:
            pts = find(find(w, "pts")[0], "xy"); a, b = K(pts[0][1], pts[0][2]), K(pts[1][1], pts[1][2])
            if not touches(a, id(w)) or not touches(b, id(w)): drop.add(id(w))
        for xy, ids in power.items():
            if xy not in real and not ends.get(xy): drop.update(ids)
        # símbolo de alimentação só com fio que leva a nada: o fio cai na próxima volta
        if not drop: break
        kept = [c for c in kept if id(c) not in drop]
    tree = [tree[0]] + kept
    p.write_text(dump(tree) + "\n")
    print("símbolos removidos:", tira)
else:
    import pcbnew
    p = sys.argv[2]; b = pcbnew.LoadBoard(p)
    for r in SAIR:
        f = b.FindFootprintByReference(r)
        assert f is not None, r
        b.RemoveNative(f)
    # trilhas e vias que ficaram com uma ponta solta (sem pad, sem outra trilha, sem via, sem zona do mesmo net) saem, até não sobrar nenhuma
    def pts(t): return [(t.GetStart().x, t.GetStart().y)] if t.GetClass() == "PCB_VIA" else [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
    removidas = 0
    while True:
        tr = list(b.GetTracks()); pads = {}
        for f in b.GetFootprints():
            for pd in f.Pads(): pads.setdefault(pd.GetNetname(), []).append(pd)
        zonas = {}
        for z in b.Zones(): zonas.setdefault(z.GetNetname(), []).append(z)
        ends = {}
        for t in tr:
            for q in pts(t): ends.setdefault((t.GetNetname(), q), []).append(t)
        solto = []
        for t in tr:
            if t.GetClass() == "PCB_VIA":
                continue
            net = t.GetNetname()
            for q in pts(t):
                tocaPad = any(pd.HitTest(pcbnew.VECTOR2I(*q)) for pd in pads.get(net, []))
                outras = [o for o in ends.get((net, q), []) if o is not t]
                if not tocaPad and not outras:
                    solto.append(t); break
        # via sem trilha de nenhum lado e sem pad: solta (a que costura o GND numa zona fica, pois toca zona nas duas camadas)
        for t in tr:
            if t.GetClass() != "PCB_VIA": continue
            net = t.GetNetname(); q = pts(t)[0]
            if net in zonas and net == "GND": continue
            if not ends.get((net, q)) or all(o.GetClass() == "PCB_VIA" for o in ends.get((net, q), [])):
                if not any(pd.HitTest(pcbnew.VECTOR2I(*q)) for pd in pads.get(net, [])) and net not in zonas:
                    solto.append(t)
        if not solto: break
        for t in solto: b.RemoveNative(t)
        removidas += len(solto)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(p, b)
    print("ok; trilhas e vias soltas removidas:", removidas)
