#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""16_bits v. 1.2 final (D108), parte 3: roteia com o Freerouting (DSN -> SES), cria as zonas de GND e preenche.
Uso (Python do venv do KiCad MCP): python v12b_route.py boards/16_bits/hardware-v1.3 [passes]   (precisa de java e ~/.kicad-mcp/freerouting.jar)"""
import subprocess, sys
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1])
PASSES = sys.argv[2] if len(sys.argv) > 2 else "40"
PCB = str(HW / "dumper.kicad_pcb")
JAR = Path.home() / ".kicad-mcp" / "freerouting.jar"
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()):
    b.RemoveNative(t)
for z in list(b.Zones()):
    b.RemoveNative(z)
dsn, ses = "/tmp/v12b.dsn", "/tmp/v12b.ses"
Path(dsn).unlink(missing_ok=True); Path(ses).unlink(missing_ok=True)
pcbnew.ExportSpecctraDSN(b, dsn)
r = subprocess.run(["java", "-jar", str(JAR), "-de", dsn, "-do", ses, "-mp", PASSES, "-mt", "1"], capture_output=True, text=True, timeout=3000)
print(r.stdout[-600:])
if not (Path(ses).exists() and Path(ses).stat().st_size > 0):
    sys.exit("freerouting nao gerou o .ses")
pcbnew.ImportSpecctraSES(b, ses)
bb = b.GetBoardEdgesBoundingBox()
net = b.FindNet("/GND")
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net)
    z.SetMinThickness(mm(0.2)); z.SetLocalClearance(mm(0.3))
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
        o.Append(x, y)
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("trilhas:", len(list(b.GetTracks())), "zonas:", len(list(b.Zones())))
