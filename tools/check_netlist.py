#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verifica a netlist do esquemático contra boards/<placa>/docs/pinmap.md (`--board <placa>`, padrão 16_and_8_bits) (CLAUDE.md, seção 8).

1. exporta a netlist com `kicad-cli sch export netlist`;
2. lê boards/16_and_8_bits/docs/pinmap.md;
3. confirma que cada pino de cada slot está na mesma net do pino do Mega esperado
   (e que nenhuma net tem pino a mais ou a menos);
4. confirma VCC dos slots = 5V (net do pino 5V do Mega) e GND = GND;
5. sai com código != 0 e lista as divergências.

Uso: python3 tools/check_netlist.py [esquematico.kicad_sch]
"""
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_args = sys.argv[1:]
BOARD = "16_and_8_bits"          # --board <pasta em boards/>
if "--board" in _args:
    i = _args.index("--board")
    BOARD = _args[i + 1]
    del _args[i:i + 2]
SEM_TROCA = "--sem-troca" in _args      # versão sem o bloco de troca de cartucho (D128): v1.0 das placas, v1.2 da 16_bits
_args = [a for a in _args if a != "--sem-troca"]
SCH = Path(_args[0]) if _args else ROOT / f"boards/{BOARD}/hardware/dumper.kicad_sch"
PINMAP = ROOT / f"boards/{BOARD}/docs/pinmap.md"
# Capacitores de 100 nF (slots e PIC) e regulador de 3,3 V de cada placa.
# Referências sempre sequenciais por prefixo (C1, C2, ...): ao tirar peças de uma placa derivada, renumerar (D109)
BOARD_CFG = {
    "16_and_8_bits": dict(caps=range(2, 7), reg=True, tps={}),
    # C2 SNES, C3 Mega Drive, C4 PIC (renumerados em 7c38c77; C1 é o eletrolítico); v. 1.2: C5 junto ao A31 e C6 junto ao A2 do slot Mega Drive
    # tps: pontos de teste da v. 1.2 (referência, net)
    # v. 1.2 final (D108): resistores serie R3..R14 e TVS D3..D14 nas 12 linhas de controle (net do Mega = <nome>_M), pull-up R15 de /VRES,
    # chave de 5V dos slots (Q1, R16..R18, D2; comando no D19), reset (SW1)
    "16_bits": dict(caps=(2, 3, 4, 5, 6), reg=False, tps={"TP1": "+5V", "TP2": "GND", "TP3": "D6", "TP4": "D9", "TP5": "D8", "TP6": "D7"}, v12b=True),
    # só GBA (GB e GBC por adaptador): regulador de 3,3 V (U1, C2, C3, C4), sem Si5351, PIC e R2
    "gb_gba": dict(caps=(), reg=True, mdonly=True, tps={}, regref=("U1", "C2", "C3", "C4")),
    # só SNES: C2 do slot e C3 do PIC; Si5351, PIC e R2 ficam; sem /CART
    "snes": dict(caps=(2, 3), reg=False, tps={"TP1": "+5V", "TP2": "GND", "TP3": "D9", "TP4": "D8", "TP5": "D7"}),
    # só NES: Si5351 (só o CLK0 vai ao slot, pino 37) e C2 do slot; sem PIC, R2, regulador, pontos de teste nem /CART
    "nes": dict(caps=(2,), reg=False, nopic=True, tps={}),
    # Famicom + NES: Si5351 (só o CLK0, no pino 37 do NES), C2 (NES) e C3 (Famicom); sem PIC, R2, regulador nem pontos de teste
    "famicom_nes": dict(caps=(2, 3), reg=False, nopic=True, tps={}),
    # só Famicom: sem Si5351 (o slot não usa clock), PIC, R2 nem regulador; C2 do slot
    "famicom": dict(caps=(2,), reg=False, mdonly=True, tps={}),
    # só Mega Drive: sem SNES, Si5351, PIC nem R2; C2 do slot e C3/C4 extras
    # só N64 (3,3 V): Si5351 (só o CLK1, EEPROM_CLK no pino 19), regulador de 3,3 V (U2, C2, C3, C4), R2 de 1 kΩ do D7 ao 3,3 V; sem PIC
    "n64": dict(caps=(), reg=True, nopic=True, clks=("CLK1",), r2_3v3=True, tps={}, regref=("U2", "C2", "C3", "C4")),
    "megadrive": dict(caps=(2, 3, 4), reg=False, mdonly=True, tps={"TP1": "+5V", "TP2": "GND", "TP3": "D6", "TP4": "D9", "TP5": "D8", "TP6": "D7"}),
}
CFG = BOARD_CFG[BOARD]
V12B = CFG.get("v12b", False)
import json as _json
TROCA = None if SEM_TROCA else _json.loads((ROOT / "tools/troca/boards.json").read_text()).get(BOARD)      # bloco de troca de cartucho (D126): dict(q0, r0, d0, f0, q1) com a primeira referência nova de cada tipo; ver troca_ajusta()
CTRL = ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D14", "D15", "D16", "D17"]      # v12b: ordem de R3..R14 e D3..D14
MDONLY = CFG.get("mdonly", False)
NOPIC = CFG.get("nopic", False)      # tem Si5351 mas não tem PIC nem R2

R2_3V3 = CFG.get("r2_3v3", False)    # R2 puxa o D7 para o 3,3 V (EEPROM_DATA do N64)
SI_CLKS = CFG.get("clks", ("CLK0",))   # saídas do Si5351 usadas pela placa sem PIC
SLOT_REF = {"SNES": "SNES1", "NES": "NES1", "Famicom": "FC1", "Mega Drive": "MD1", "GBA": "GBA1", "N64": "N64_1"}
SLOTS = set()      # slots presentes no pinmap da placa
MEGA = "A1"          # shield
SI = "U1"            # Si5351: 1 VIN 2 GND 3 SDA 4 SCL 5 CLK2 6 CLK1 7 CLK0
PIC = "U2"           # PIC12F629: 1 VDD 2 CLK2 3 D41 4 D40 5 RESET 6 DATA1 7 DATA0 8 VSS
SI_CLK = {"CLK0": "7", "CLK1": "6", "CLK2": "5"}
PIC_NET = {"CIC_DATA_0": "7", "CIC_DATA_1": "6", "CIC_RESET": "5"}
MEGA_5V = ("5V1", "5V3", "5V4")
MEGA_GND = ("GND1", "GND2", "GND3", "GND5", "GND6")
# Pinos do Mega que existem no footprint mas ficam sem ligação por projeto.
# D0/D1 = serial USB; nunca podem ir a um slot.
MEGA_NC_OK = {"D0", "D1", "D10", "D11", "D12", "D13", "D18", "D19", "D39", "D50", "D51", "D52",
              "D53", "3V3", "VIN", "RST1", "IORF", "AREF", "SCL", "SDA"}
if TROCA:
    MEGA_NC_OK -= {"D19", "D53"}       # D19 = comando do Q1 (PWR_EN), D53 = sensor do rail (SENSE_MCU)
if BOARD in ("16_bits", "megadrive"):
    MEGA_NC_OK.discard("D50")          # v. 1.2: D50 = /CART (B32 do slot Mega Drive)


def read_pinmap():
    """-> (net -> {(ref, pin)}, lista de (ref, pin) que devem ficar sem ligação)"""
    nets = defaultdict(set)
    nc = []
    sec = None
    SLOTS.clear()
    for ln in PINMAP.read_text().splitlines():
        m = re.match(r"## (SNES|NES|Famicom|Mega Drive|GBA|N64) \(", ln)
        if m:
            sec = SLOT_REF[m.group(1)]
            SLOTS.add(sec)
            continue
        if ln.startswith("## "):
            sec = None
            continue
        if not sec or not ln.startswith("| ") or ln.startswith("| pino") or ln.startswith("|---"):
            continue
        c = [x.strip() for x in ln.strip("|").split("|")]
        pin, net = c[0], c[2]
        if net.startswith("NC"):
            nc.append((sec, pin))
            continue
        if net.startswith("5V"):
            net = "+5V"
        elif net.startswith("3V3"):
            net = "+3V3"
        elif net.startswith("CLK"):
            net = net.split()[0]
        elif net.startswith("CIC"):
            net = net.split(" →")[0].replace(" ", "_")
        nets[net].add((sec, pin))
    return nets, nc


def expected_nets(pm_nets):
    """Acrescenta ao pinmap o lado do Mega, Si5351, PIC e periféricos."""
    exp = {k: set(v) for k, v in pm_nets.items()}
    for net in list(exp):
        if re.fullmatch(r"[AD]\d+", net):
            exp[net].add((MEGA, net))                       # pad do Mega com o mesmo nome
    if not MDONLY:
        for net, pin in SI_CLK.items():
            if NOPIC and net not in SI_CLKS: continue
            exp.setdefault(net, set()).add((SI, pin))
        if not NOPIC:
            for net, pin in PIC_NET.items():
                exp.setdefault(net, set()).add((PIC, pin))
            exp["CLK2"].add((PIC, "2"))
        # I2C, CIC reset in/out e periféricos
        exp.setdefault("D20", set()).update({(MEGA, "D20"), (SI, "3")})
        exp.setdefault("D21", set()).update({(MEGA, "D21"), (SI, "4")})
        if not NOPIC:
            exp.setdefault("D41", set()).update({(MEGA, "D41"), (PIC, "3")})
            exp.setdefault("D40", set()).update({(MEGA, "D40"), (PIC, "4")})
    exp.setdefault("D38", set()).update({(MEGA, "D38"), ("R1", "2")})
    exp.setdefault("LED_K", set()).update({("R1", "1"), ("D1", "1")})
    if not MDONLY and (not NOPIC or R2_3V3):
        exp.setdefault("D7", set()).update({(MEGA, "D7"), ("R2", "2")})
    exp.setdefault("+5V", set()).update({(MEGA, p) for p in MEGA_5V})
    exp["+5V"].update({("D1", "2"), ("C1", "1"), ("FLG1", "1")})
    if not MDONLY:
        exp["+5V"].add((SI, "1"))
        if not NOPIC: exp["+5V"].update({(PIC, "1"), ("R2", "1")})
    exp["+5V"].update({(f"C{i}", "1") for i in CFG["caps"]})
    for tp, net in CFG["tps"].items():
        exp.setdefault(net, set()).add((tp, "1"))
    if CFG["reg"]:
        ru, ci, co, cv = CFG.get("regref", ("U3", "C7", "C8", "C9"))
        exp["+5V"].update({(ru, "2"), (ci, "1")})
        exp.setdefault("+3V3", set()).update({(ru, "3"), (co, "1"), (cv, "1")})
        if R2_3V3: exp["+3V3"].add(("R2", "1"))
        exp["GND"].update({(ru, "1"), (ci, "2"), (co, "2"), (cv, "2")})
    exp.setdefault("GND", set()).update({(MEGA, p) for p in MEGA_GND})
    exp["GND"].update({("C1", "2"), ("FLG2", "1")})
    if not MDONLY:
        exp["GND"].add((SI, "2"))
        if not NOPIC: exp["GND"].add((PIC, "8"))
    exp["GND"].update({(f"C{i}", "2") for i in CFG["caps"]})
    if V12B:
        v12b_ajusta(exp)
    if TROCA:
        troca_ajusta(exp)
    return exp


def troca_ajusta(exp):
    """Bloco de troca de cartucho (D126, tools/troca/sch_block.py): Q1 (chave de alta), Q2 (descarga), Q3 (sensor), LEDs verde e amarelo.
    Ordem das referências novas, como o gerador as numera: [Q1, R100k, R100R, R1k, LED verde se a placa não tinha Q1], Q2, R330, [R330 do 3,3 V], Q3, R100k, R1k, R1k, LED amarelo."""
    t = TROCA
    q, r, d = t["q0"], t["r0"], t["d0"]
    keep = {(MEGA, p) for p in MEGA_5V} | {("D1", "2"), ("C1", "1"), ("FLG1", "1")} | {(tp, "1") for tp, n in CFG["tps"].items() if n == "+5V"}
    cart = {rp for rp in exp["+5V"] if rp not in keep}
    exp["+5V"] -= cart
    q1, q2, q3 = f"Q{q}", f"Q{q + 1}", f"Q{q + 2}"
    r3, r4, r5 = f"R{r}", f"R{r + 1}", f"R{r + 2}"
    n = r + 3
    r6 = f"R{n}"; n += 1
    r6b = None
    if t.get("v3"):
        r6b = f"R{n}"; n += 1
    r7, r8, r9 = f"R{n}", f"R{n + 1}", f"R{n + 2}"
    dg, dy = f"D{d}", f"D{d + 1}"
    flg = f"FLG{t['f0']}"
    exp["+5V"].update({(q1, "3"), (r3, "1"), (r8, "1")})
    exp["+5V_CART"] = cart | {(q1, "2"), (r5, "1"), (r6, "1"), (q3, "2"), (r7, "1"), (flg, "1")}
    exp["PWR_G"] = {(q1, "1"), (q2, "2"), (r3, "2"), (r4, "2")}
    exp["PWR_EN"] = {(MEGA, "D19"), (r4, "1")}
    exp["LED_CART"] = {(r5, "2"), (dg, "2")}
    exp["DESCARGA"] = {(q2, "3"), (r6, "2")} | ({(r6b, "2")} if r6b else set())
    exp["SENSE"] = {(dy, "2"), (q3, "3"), (r8, "2"), (r9, "1")}
    exp["SENSE_MCU"] = {(MEGA, "D53"), (r9, "2")}
    exp["GND"].update({(q2, "1"), (q3, "1"), (r7, "2"), (dg, "1"), (dy, "1")})
    if r6b:
        exp["+3V3"].add((r6b, "1"))


def v12b_ajusta(exp):
    """Resistores serie, TVS e pull-up (so a 16_bits v. 1.2 em diante). Desde D128 a v. 1.2 não tem chave de 5V, LED D2 nem reset; a v. 1.3 leva o bloco de troca (TROCA)."""
    for k, n in enumerate(CTRL):
        r, d = f"R{3 + k}", f"D{3 + k}"
        exp[n].discard((MEGA, n))
        exp[n].update({(r, "2"), (d, "1")})
        exp[n + "_M"] = {(MEGA, n), (r, "1")}
        exp["GND"].add((d, "2"))
    exp["D17"].add(("R15", "2"))
    exp["+5V"].add(("R15", "1"))        # pull-up de /VRES (com o bloco de troca vai para o +5V_CART, em troca_ajusta)


def actual_nets():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "n.xml"
        p = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
                            "-o", str(out), str(SCH)], capture_output=True, text=True)
        if not out.exists():
            sys.exit(f"kicad-cli falhou: {p.stdout}{p.stderr}")
        root = ET.parse(out).getroot()
    nets = {}
    for n in root.find("nets"):
        nets[n.get("name")] = {(x.get("ref"), x.get("pin")) for x in n.findall("node")}
    return nets


def main():
    pm_nets, pm_nc = read_pinmap()
    exp = expected_nets(pm_nets)
    act = actual_nets()
    errors = []

    # 1. cada net esperada existe, com exatamente os mesmos nós
    act_by_nodes = {frozenset(v): k for k, v in act.items()}
    for net, nodes in sorted(exp.items()):
        key = frozenset(nodes)
        if key in act_by_nodes:
            continue
        # procura a net real que contém algum nó esperado
        found = [(k, v) for k, v in act.items() if v & nodes]
        if not found:
            errors.append(f"net {net}: nenhum dos nós esperados existe na netlist ({sorted(nodes)[:4]}...)")
            continue
        for k, v in found:
            miss, extra = sorted(nodes - v), sorted(v - nodes)
            errors.append(f"net {net} (real '{k}'): faltam {miss or '-'}; sobram {extra or '-'}")

    # 2. pinos que devem ficar sem ligação
    for ref, pin in pm_nc:
        net = next((k for k, v in act.items() if (ref, pin) in v), None)
        if net is not None and len(act[net]) > 1:
            errors.append(f"{ref}.{pin} deveria estar sem ligação, mas está em '{net}': {sorted(act[net])}")
    for pin in sorted(MEGA_NC_OK):
        net = next((k for k, v in act.items() if (MEGA, pin) in v), None)
        if net is not None and len(act[net]) > 1:
            errors.append(f"{MEGA}.{pin} deveria estar sem ligação, mas está em '{net}'")

    # 3. alimentação
    for ref, pins in (("SNES1", ("27", "58")), ("NES1", ("36",)), ("FC1", ("30", "31")), ("MD1", ("A2", "A31"))):
        if ref not in SLOTS:
            continue
        for pin in pins:
            net = next((k for k, v in act.items() if (ref, pin) in v), None)
            if TROCA:
                if net is None or ("Q1", "2") not in act[net] or (MEGA, "5V1") in act[net]:
                    errors.append(f"{ref}.{pin} (VCC) deve estar só no 5V chaveado (dreno do Q1), nunca direto no 5V do Mega")
            elif net is None or (MEGA, "5V1") not in act[net]:
                errors.append(f"{ref}.{pin} (VCC) não está na net do 5V do Mega")
    for ref, pins in (("GBA1", ("1",)), ("N64_1", ("9", "17", "34", "42"))):
        if ref not in SLOTS:
            continue
        for pin in pins:
            net = next((k for k, v in act.items() if (ref, pin) in v), None)
            REGU = CFG.get("regref", ("U3",))[0]
            if net is None or (REGU, "3") not in act[net] or (MEGA, "5V1") in act[net]:
                errors.append(f"{ref}.{pin} (VCC) deve estar só na saída de 3,3 V do {REGU}, nunca no 5V")
    for ref, pins in (("SNES1", ("5", "36")), ("NES1", ("1", "72")), ("FC1", ("1", "16")),
                      ("MD1", ("A1", "A18", "A32")), ("GBA1", ("32", "SHIELD_3", "SHIELD_4")),
                      ("N64_1", ("1", "2", "6", "22", "23", "25", "26", "27", "31", "47", "48", "50"))):
        if ref not in SLOTS:
            continue
        for pin in pins:
            net = next((k for k, v in act.items() if (ref, pin) in v), None)
            if net is None or (MEGA, "GND1") not in act[net]:
                errors.append(f"{ref}.{pin} (GND) não está na net do GND do Mega")

    # 4. curtos: 5V e GND não podem estar na mesma net; D0/D1 nunca em slot
    for k, v in act.items():
        if (MEGA, "5V1") in v and (MEGA, "GND1") in v:
            errors.append(f"CURTO 5V-GND na net '{k}'")
    for p in ("D0", "D1"):
        net = next((k for k, v in act.items() if (MEGA, p) in v), None)
        if net and any(r in SLOTS for r, _ in act[net]):
            errors.append(f"{p} (serial USB) ligado a um slot na net '{net}'")

    # 5. nets reais sem correspondência (ligações que não estão no pinmap)
    exp_sets = {frozenset(v) for v in exp.values()}
    for k, v in act.items():
        if len(v) > 1 and frozenset(v) not in exp_sets and not any(v & e for e in exp_sets):
            errors.append(f"net '{k}' não consta no pinmap: {sorted(v)}")

    n_pins = sum(len(v) for v in exp.values())
    if errors:
        print(f"FALHOU: {len(errors)} divergência(s):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"OK: {len(exp)} nets e {n_pins} ligações conferem com boards/{BOARD}/docs/pinmap.md; "
          f"{len(pm_nc)} pinos de slot sem ligação conferidos.")


main()
