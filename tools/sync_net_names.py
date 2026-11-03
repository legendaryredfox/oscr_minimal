#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Alinha os nomes de net da PCB com os da netlist do esquemático (equivale ao que o
"Atualizar PCB a partir do esquemático" do KiCad faz com os nomes). Roda fora do MCP.
Uso: python tools/sync_net_names.py boards/16_and_8_bits/hardware/dumper.kicad_sch boards/16_and_8_bits/hardware/dumper.kicad_pcb
(use o python do venv do MCP, que enxerga o pcbnew)"""
import pcbnew, subprocess, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path
sch, pcb = sys.argv[1], sys.argv[2]
with tempfile.TemporaryDirectory() as t:
    x = Path(t) / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(x), sch], check=True, capture_output=True)
    root = ET.parse(x).getroot()
want = {}      # (ref, pin) -> nome da net
names = set()
for n in root.find("nets"):
    names.add(n.get("name"))
    for nd in n.findall("node"):
        want[(nd.get("ref"), nd.get("pin"))] = n.get("name")
b = pcbnew.LoadBoard(pcb)
ni = b.GetNetInfo()
renamed = 0
for item in list(ni.NetsByName().values()):
    nm = item.GetNetname()
    if nm and nm not in names and ("/" + nm) in names:
        item.SetNetname("/" + nm); renamed += 1
created = assigned = 0
for fp in b.GetFootprints():
    for pad in fp.Pads():
        nm = want.get((fp.GetReference(), pad.GetNumber()))
        if nm and nm.startswith("unconnected-"):
            nm = nm.replace("/", "{slash}")        # o KiCad escapa "/" nos nomes das nets sem ligação
        if not nm or pad.GetNetname() == nm: continue
        it = ni.GetNetItem(nm)
        if it is None:
            it = pcbnew.NETINFO_ITEM(b, nm); b.Add(it); created += 1
        pad.SetNet(it); assigned += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(pcb, b)
print(f"nets renomeadas: {renamed}; criadas: {created}; pads reatribuídos: {assigned}")
