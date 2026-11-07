#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Renomeia as nets do PCB para os nomes da netlist do esquemático, casando pelas listas de pads (a geometria não muda).
Serve depois de tools/sch/regen.py, que troca rótulos por símbolos de alimentação ('/GND' vira 'GND') e dá nomes automáticos às nets locais.
Uso (Python do venv do KiCad MCP): sync_names.py placa.kicad_sch placa.kicad_pcb"""
import pcbnew, subprocess, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path
sch, pcb = sys.argv[1], sys.argv[2]
with tempfile.TemporaryDirectory() as t:
    x = Path(t) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(x), sch], check=True, capture_output=True)
    root = ET.parse(x).getroot()
b = pcbnew.LoadBoard(pcb)
refs = {f.GetReference() for f in b.GetFootprints()}
by_pads = {}
for n in root.find("nets"):
    pads = frozenset((nd.get("ref"), nd.get("pin")) for nd in n.findall("node") if nd.get("ref") in refs)
    if pads: by_pads[pads] = n.get("name")
cur = {}
for f in b.GetFootprints():
    for p in f.Pads():
        nm = str(p.GetNetname())
        if nm: cur.setdefault(nm, set()).add((f.GetReference(), p.GetNumber()))
plan = {}
for nm, pads in cur.items():
    new = by_pads.get(frozenset(pads))
    if new is None: print("sem correspondência:", nm, sorted(pads)[:3]); continue
    if new != nm: plan[nm] = new
ni = b.GetNetInfo()
items = {str(i.GetNetname()): i for i in ni.NetsByName().values()}
for nm, new in plan.items(): items[nm].SetNetname("\x01" + new)          # nomes provisórios: evita choque entre troca de nomes
for nm, new in plan.items(): items[nm].SetNetname(new)
pcbnew.SaveBoard(pcb, b)
print(f"nets renomeadas: {len(plan)}")
