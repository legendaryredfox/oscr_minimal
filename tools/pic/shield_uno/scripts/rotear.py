#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Roteia hardware/shield_uno.kicad_pcb com o Freerouting (DSN -> SES), cria as zonas de GND e preenche.
Uso (Python do venv do KiCad MCP): gerar_pcb.py e depois rotear.py   (precisa de java e ~/.kicad-mcp/freerouting.jar)"""
import json
import subprocess
import sys
from pathlib import Path

import pcbnew

HW = Path(__file__).resolve().parent.parent / "hardware"
PCB = str(HW / "shield_uno.kicad_pcb")
JAR = Path.home() / ".kicad-mcp" / "freerouting.jar"
mm = pcbnew.FromMM


def regras():
    p = HW / "shield_uno.kicad_pro"
    d = json.loads(p.read_text())
    ns = d["net_settings"]
    for c in ns["classes"]:
        if c["name"] == "Default":
            c.update(track_width=0.4, clearance=0.25, via_diameter=0.8, via_drill=0.4)
        if c["name"] == "Power":
            c.update(track_width=0.6, clearance=0.25, via_diameter=0.8, via_drill=0.4)
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in ("/V13", "/VIN13", "/VDD", "/MCLR", "/GND")]
    p.write_text(json.dumps(d, indent=2))


def main():
    regras()
    b = pcbnew.LoadBoard(PCB)
    if list(b.GetTracks()) or list(b.Zones()):
        sys.exit("a placa ja tem trilhas ou zonas: rode gerar_pcb.py antes (ele recria a placa limpa)")
    dsn, ses = "/tmp/shield_uno.dsn", "/tmp/shield_uno.ses"
    Path(dsn).unlink(missing_ok=True)
    Path(ses).unlink(missing_ok=True)
    pcbnew.ExportSpecctraDSN(b, dsn)
    for tentativa in range(3):
        r = subprocess.run(["java", "-jar", str(JAR), "-de", dsn, "-do", ses, "-mp", "30", "-mt", "1"], capture_output=True, text=True, timeout=600)
        print(r.stdout[-300:])
        if Path(ses).exists() and Path(ses).stat().st_size > 0:
            break
    else:
        sys.exit("freerouting nao gerou o .ses")
    pcbnew.ImportSpecctraSES(b, ses)
    bb = b.GetBoardEdgesBoundingBox()
    net = b.FindNet("/GND")
    d = mm(0.3)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b)
        z.SetLayer(layer)
        z.SetNet(net)
        z.SetMinThickness(mm(0.25))
        z.SetLocalClearance(mm(0.3))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((bb.GetLeft() + d, bb.GetTop() + d), (bb.GetRight() - d, bb.GetTop() + d),
                     (bb.GetRight() - d, bb.GetBottom() - d), (bb.GetLeft() + d, bb.GetBottom() - d)):
            o.Append(x, y)
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("trilhas:", len(list(b.GetTracks())), "zonas:", len(list(b.Zones())))


if __name__ == "__main__":
    main()
