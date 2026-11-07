#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compara a conectividade (quais pinos estão juntos) de dois esquemáticos, ignorando nomes de net e símbolos de alimentação.
Uso: verify.py antes.kicad_sch depois.kicad_sch   (sai com código 1 se diferirem)"""
import subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
def part(path):
    with tempfile.TemporaryDirectory() as t:
        o = Path(t) / "n.xml"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(o), str(path)], capture_output=True)
        r = ET.parse(o).getroot()
    sets = set()
    for n in r.find("nets"):
        pins = frozenset((x.get("ref"), x.get("pin")) for x in n.findall("node") if not x.get("ref").startswith("#"))
        if pins: sets.add(pins)
    return sets
a, b = part(sys.argv[1]), part(sys.argv[2])
only_a, only_b = a - b, b - a
# nets de um pino só não importam (sem ligação)
only_a = {s for s in only_a if len(s) > 1}; only_b = {s for s in only_b if len(s) > 1}
if only_a or only_b:
    print("DIFERENTE")
    for s in sorted(only_a, key=sorted)[:15]: print("  só antes:", sorted(s))
    for s in sorted(only_b, key=sorted)[:15]: print("  só depois:", sorted(s))
    sys.exit(1)
print(f"conectividade idêntica ({len(a)} grupos)")
