#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera a seção Master System do pinmap da placa megadrive_sms cruzando:
  sch = vendor/oscr/legacy/hardware/mastersystem_adapter (net de cada pino do slot SMS)
  ods = vendor/oscr/legacy/pinout.ods, coluna "Master System"
  fw  = vendor/oscr/firmware/src/cores/SMS.cpp (porta/bit usados)
Uso: python3 tools/boards/megadrive_sms/gen_pinmap_sms.py  (precisa de kicad-cli)
Escreve a tabela em stdout."""
import re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEG = ROOT / "vendor/oscr/legacy"
SCH = LEG / "hardware/mastersystem_adapter/mastersystem_adapter.kicad_sch"

ARD2AVR = {}
def reg(port, names):
    for bit, n in enumerate(names):
        if n: ARD2AVR[n] = f"P{port}{bit}"
reg("A", [f"D{22+i}" for i in range(8)]); reg("C", [f"D{37-i}" for i in range(8)])
reg("F", [f"A{i}" for i in range(8)]);    reg("K", [f"A{8+i}" for i in range(8)])
reg("L", [f"D{49-i}" for i in range(8)]); reg("H", ["D17","D16",None,"D6","D7","D8","D9",None])

def ods_sms():
    ns = {"t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0", "x": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    T = "{%s}" % ns["t"]
    root = ET.fromstring(zipfile.ZipFile(LEG / "pinout.ods").read("content.xml"))
    tb = next(root.iter(T + "table"))
    rows = []
    for row in tb.iter(T + "table-row"):
        cells = []
        for c in row:
            txt = "".join("".join(p.itertext()) for p in c.findall("x:p", ns))
            cells += [txt] * min(int(c.get(T + "number-columns-repeated", "1")), 40)
        rows.append(cells)
    col = rows[0].index("Master System")
    return {r[0]: r[col] for r in rows[1:] if r and r[0] and len(r) > col and r[col]}

def main():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "n.xml"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(out), str(SCH)],
                       check=True, capture_output=True)
        root = ET.parse(out).getroot()
    names = {}
    for lib in root.iter("libpart"):
        if lib.get("part") == "SMS_Slot":
            for p in lib.iter("pin"):
                names[p.get("num")] = p.get("name")
    pins = {}
    for n in root.find("nets"):
        for x in n:
            if x.get("ref") == "U1":
                pins[int(x.get("pin"))] = n.get("name")
    ods = ods_sms()
    ods_by_name = {}
    for ard, sig in ods.items():
        ods_by_name.setdefault(sig.upper(), []).append(ard)
    print("| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |")
    print("|---|---|---|---|---|")
    for p in range(1, 51):
        net = pins.get(p, "?")
        sig = names.get(str(p), "?")
        if net.startswith("unconnected"):
            print(f"| {p} | {sig} | NC (sem ligação) | - | sch |"); continue
        if net == "+5V":   print(f"| {p} | {sig} | 5V (fixo) | - | sch |"); continue
        if net == "GND":   print(f"| {p} | {sig} | GND | - | sch |"); continue
        avr = ARD2AVR.get(net, "-")
        mark = "sch"
        o = ods.get(net, "")
        mark += " ods" if o else " -ods"
        print(f"| {p} | {sig} | {net} | {avr} | {mark} |")
if __name__ == "__main__":
    main()
