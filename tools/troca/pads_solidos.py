#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D140: onde o DRC aponta starved_thermal (alívio térmico de um pad de GND ligado a uma ilha da zona), o pad passa a ligar sólido à zona; refaz o preenchimento.
Uso (python do sistema, com pcbnew): /usr/bin/python3 -I tools/troca/pads_solidos.py <pasta hardware-vX.Y>"""
import json, subprocess, sys, tempfile
from pathlib import Path
import pcbnew
PCB = Path(sys.argv[1]).resolve() / "dumper.kicad_pcb"
tmp = Path(tempfile.mkdtemp())
for volta in range(3):
    js = tmp / "d.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "-o", str(js), str(PCB)], capture_output=True)
    ids = {i["uuid"] for v in json.loads(js.read_text())["violations"] if v["type"] == "starved_thermal" for i in v["items"]}
    if not ids:
        break
    b = pcbnew.LoadBoard(str(PCB))
    n = 0
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.m_Uuid.AsString() in ids:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); n += 1
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(PCB), b)
    print("pads com ligação sólida:", n)
print("ok")
