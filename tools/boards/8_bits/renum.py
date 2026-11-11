#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Renumera referências (esquemático, PCB e d138.json) de uma vez, para que cada prefixo fique em sequência (D109, D150).
Também troca a referência dentro dos nomes de net automáticos (Net-(Q4-G) -> Net-(Q1-G); unconnected-(Q4-...)).
Uso: python3 tools/boards/8_bits/renum.py boards/8_bits/hardware-v1.1 C4=C5 C5=C6 C6=C4 R9=R2 ...  (troca simultânea)"""
import json, re, sys
from pathlib import Path
hw = Path(sys.argv[1]); mp = dict(a.split("=") for a in sys.argv[2:])
def sub_ref(m): return m.group(1) + mp.get(m.group(2), m.group(2)) + m.group(3)
for name in ("dumper.kicad_sch", "dumper.kicad_pcb"):
    p = hw / name; s = p.read_text()
    s = re.sub(r'(\(reference ")([A-Z]+\d+)(")', sub_ref, s)
    s = re.sub(r'(\(property "Reference" ")([A-Z]+\d+)(")', sub_ref, s)
    s = re.sub(r'((?:Net-|unconnected-)\()([A-Z]+\d+)(-)', sub_ref, s)
    p.write_text(s)
j = hw / "d138.json"
if j.exists():
    d = json.loads(j.read_text())
    d = {k: [mp.get(x, x) for x in v] for k, v in d.items()}
    j.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print("renumerado:", mp)
