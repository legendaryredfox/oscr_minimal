#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v1.2 sem o desligamento por software (D128): tira Q1, R16, R17, R18, D2 (LED verde) e SW1 (reset) do esquemático e do PCB.
O que era +5V_CART volta a ser +5V; um trilho de 0,8 mm no lugar do Q1 liga os dois pedaços de cobre.
Uso: python3 tools/boards/16_bits/sem_chave.py sch boards/16_bits/hardware-v1.2/dumper.kicad_sch     (depois: tools/sch/regen.py no mesmo arquivo)
     <python do venv do KiCad MCP> tools/boards/16_bits/sem_chave.py pcb boards/16_bits/hardware-v1.2/dumper.kicad_pcb"""
import sys
from pathlib import Path
SAIR = ("Q1", "R16", "R17", "R18", "D2", "SW1", "FLG3")

if sys.argv[1] == "sch":
    import math
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sch"))
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
                if val(q[1]) == "Value" and val(q[2]) == "+5V_CART": q[2] = S("+5V")
        if isinstance(c, list) and c and val(c[0]) == "label" and val(c[1]) in ("PWR_G", "LED_CART", "PWR_EN", "SENSE"):
            continue
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
    import uuid
    for x, y in ((96.52, 83.82), (132.08, 134.62)):       # pinos RST1 e D19 do Mega, agora sem ligação
        kept.append(parse('(no_connect (at %s %s) (uuid "%s"))' % (x, y, uuid.uuid4())))
    tree = [tree[0]] + kept
    p.write_text(dump(tree) + "\n")
    print("símbolos removidos:", tira)
else:
    import pcbnew
    mm = pcbnew.FromMM
    p = sys.argv[2]; b = pcbnew.LoadBoard(p)
    for r in SAIR:
        f = b.FindFootprintByReference(r)
        if f is not None: b.RemoveNative(f)
    mortas = {"/PWR_G", "/LED_CART", "Net-(A1-PadD19)", "Net-(A1-PadRST1)"}
    for t in list(b.GetTracks()):
        if t.GetNetname() in mortas: b.RemoveNative(t)
    cart = b.FindNet("+5V_CART"); v5 = b.FindNet("+5V")
    for t in b.GetTracks():
        if t.GetNetname() == "+5V_CART": t.SetNet(v5)
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetNetname() == "+5V_CART": pd.SetNet(v5)
    for z in b.Zones():
        if z.GetNetname() == "+5V_CART": z.SetNet(v5)
    # trilhos que levavam só ao R18 (LED) saem; o resto do que era +5V_CART fica
    T = lambda t: (round(pcbnew.ToMM(t.GetStart().x), 2), round(pcbnew.ToMM(t.GetStart().y), 2), round(pcbnew.ToMM(t.GetEnd().x), 2), round(pcbnew.ToMM(t.GetEnd().y), 2))
    LED = {(120.3, 51.0, 112.2, 51.0), (121.1, 51.8, 120.3, 51.0), (121.1, 55.54, 121.1, 51.8), (119.5, 55.54, 121.1, 55.54)}
    for t in list(b.GetTracks()):
        if t.GetNetname() == "+5V" and T(t) in LED: b.RemoveNative(t)
    # liga os dois pedaços de cobre onde era o Q1 (pads 2 e 3 em x=119,5; y=55,54 e 58,08)
    tr = pcbnew.PCB_TRACK(b); tr.SetLayer(pcbnew.F_Cu); tr.SetWidth(mm(0.8)); tr.SetNet(v5)
    tr.SetStart(pcbnew.VECTOR2I(mm(119.5), mm(55.54))); tr.SetEnd(pcbnew.VECTOR2I(mm(119.5), mm(58.08))); b.Add(tr)
    # o pad 1 do R16 (112,2; 56,5) trocava de camada: vira via
    via0 = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"][0]
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(112.2), mm(56.5))); v.SetNet(v5)
    v.SetWidth(via0.GetWidth()); v.SetDrill(via0.GetDrill()); b.Add(v)
    for n, ref, pad in (("unconnected-(A1-PadD19)", "A1", "D19"), ("unconnected-(A1-PadRST1)", "A1", "RST1")):
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni)
        for pd in b.FindFootprintByReference(ref).Pads():
            if pd.GetName() == pad: pd.SetNet(ni)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(p, b)
    print("ok")
