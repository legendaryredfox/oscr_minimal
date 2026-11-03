#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verifica a netlist do esquemático contra boards/16_bits/docs/pinmap.md (CLAUDE.md, seção 8).

1. exporta a netlist com `kicad-cli sch export netlist`;
2. lê boards/16_bits/docs/pinmap.md;
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
SCH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "boards/16_bits/hardware/dumper.kicad_sch"
PINMAP = ROOT / "boards/16_bits/docs/pinmap.md"

SLOT_REF = {"SNES": "SNES1", "NES": "NES1", "Famicom": "FC1", "Mega Drive": "MD1", "GBA": "GBA1"}
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


def read_pinmap():
    """-> (net -> {(ref, pin)}, lista de (ref, pin) que devem ficar sem ligação)"""
    nets = defaultdict(set)
    nc = []
    sec = None
    for ln in PINMAP.read_text().splitlines():
        m = re.match(r"## (SNES|NES|Famicom|Mega Drive|GBA) \(", ln)
        if m:
            sec = SLOT_REF[m.group(1)]
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
    for net, pin in SI_CLK.items():
        exp.setdefault(net, set()).add((SI, pin))
    for net, pin in PIC_NET.items():
        exp.setdefault(net, set()).add((PIC, pin))
    exp["CLK2"].add((PIC, "2"))
    # I2C, CIC reset in/out e periféricos
    exp.setdefault("D20", set()).update({(MEGA, "D20"), (SI, "3")})
    exp.setdefault("D21", set()).update({(MEGA, "D21"), (SI, "4")})
    exp.setdefault("D41", set()).update({(MEGA, "D41"), (PIC, "3")})
    exp.setdefault("D40", set()).update({(MEGA, "D40"), (PIC, "4")})
    exp.setdefault("D38", set()).update({(MEGA, "D38"), ("R1", "2")})
    exp.setdefault("LED_K", set()).update({("R1", "1"), ("D1", "1")})
    exp.setdefault("D7", set()).update({(MEGA, "D7"), ("R2", "2")})
    exp["+5V"].update({(MEGA, p) for p in MEGA_5V})
    exp["+5V"].update({(SI, "1"), (PIC, "1"), ("D1", "2"), ("R2", "1"), ("C1", "1"), ("FLG1", "1")})
    exp["+5V"].update({(f"C{i}", "1") for i in range(2, 7)})
    exp["+5V"].update({("U3", "2"), ("C7", "1")})
    exp.setdefault("+3V3", set()).update({("U3", "3"), ("C8", "1"), ("C9", "1")})
    exp["GND"].update({("U3", "1"), ("C7", "2"), ("C8", "2"), ("C9", "2")})
    exp.setdefault("GND", set()).update({(MEGA, p) for p in MEGA_GND})
    exp["GND"].update({(SI, "2"), (PIC, "8"), ("C1", "2"), ("FLG2", "1")})
    exp["GND"].update({(f"C{i}", "2") for i in range(2, 7)})
    return exp


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
        for pin in pins:
            net = next((k for k, v in act.items() if (ref, pin) in v), None)
            if net is None or (MEGA, "5V1") not in act[net]:
                errors.append(f"{ref}.{pin} (VCC) não está na net do 5V do Mega")
    for pin in ("1",):
        net = next((k for k, v in act.items() if ("GBA1", pin) in v), None)
        if net is None or ("U3", "3") not in act[net] or (MEGA, "5V1") in act[net]:
            errors.append("GBA1.1 (VCC) deve estar só na saída de 3,3 V do U3, nunca no 5V")
    for ref, pins in (("SNES1", ("5", "36")), ("NES1", ("1", "72")), ("FC1", ("1", "16")),
                      ("MD1", ("A1", "A18", "A32")), ("GBA1", ("32", "SHIELD_3", "SHIELD_4"))):
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
        if net and any(r in ("SNES1", "NES1", "FC1", "MD1", "GBA1") for r, _ in act[net]):
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
    print(f"OK: {len(exp)} nets e {n_pins} ligações conferem com boards/16_bits/docs/pinmap.md; "
          f"{len(pm_nc)} pinos de slot sem ligação conferidos.")


main()
