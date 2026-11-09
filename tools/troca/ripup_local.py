#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D140: apaga as trilhas de todas as redes de sinal que passam perto de cada ligação aberta (as que o DRC aponta como unconnected_items entre dois pontos),
para o Freerouting refazer essas redes (e a ligação aberta) com mais liberdade; o resto da placa fica como está.
Uso: /usr/bin/python3 -I tools/troca/ripup_local.py <pasta hardware-vX.Y> [margem_mm=5] [--seco]
  --seco: só lista as redes que seriam apagadas.
Depois: roteie de forma incremental (tools/troca/route.py <pasta> 30 --incremental, ou a ferramenta autoroute do MCP do KiCad)."""
import json, subprocess, sys, tempfile
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1]).resolve()
MARG = float(next((a for a in sys.argv[2:] if not a.startswith("--")), 5))
SECO = "--seco" in sys.argv
PCB = HW / "dumper.kicad_pcb"
tmp = Path(tempfile.mkdtemp())
js = tmp / "drc.json"
subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "-o", str(js), str(PCB)], capture_output=True)
d = json.loads(js.read_text())
abertas = d.get("unconnected_items", []) + [v for v in d.get("violations", []) if v["type"] == "unconnected_items"]
print("ligações abertas:", len(abertas))
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(str(PCB))
POT = {"GND", "+5V", "+5V_CART", "VCC_CART", "+3V3", "+5V_F"}
rip = set()
for v in abertas:
    pts = [(i["pos"]["x"], i["pos"]["y"]) for i in v["items"]]
    x0, x1 = min(p[0] for p in pts) - MARG, max(p[0] for p in pts) + MARG
    y0, y1 = min(p[1] for p in pts) - MARG, max(p[1] for p in pts) + MARG
    box = pcbnew.BOX2I(pcbnew.VECTOR2I(mm(x0), mm(y0)), pcbnew.VECTOR2I(mm(x1 - x0), mm(y1 - y0)))
    for t in b.GetTracks():
        if t.GetNetname() in POT or t.GetNetname().startswith("unconnected"):
            continue
        if t.GetBoundingBox().Intersects(box):
            rip.add(t.GetNetCode())
    print("  ", v["description"][:60], [round(c, 1) for p in pts for c in p], "->", len(rip), "redes até aqui")
nomes = sorted(b.FindNet(c).GetNetname() for c in rip)
print("redes a refazer (%d):" % len(nomes), ", ".join(nomes))
if SECO:
    sys.exit(0)
n = 0
for t in list(b.GetTracks()):
    if t.GetNetCode() in rip:
        b.RemoveNative(t); n += 1
pcbnew.SaveBoard(str(PCB), b)
print("trilhas e vias apagadas:", n)
