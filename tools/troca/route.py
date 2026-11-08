#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bloco de troca (D126), roteamento: roteia com o Freerouting (DSN -> SES), cria as zonas de GND e preenche. Se sobrar ligação aberta
(o Freerouting às vezes deixa uma rede de fora sem avisar) ou o .ses não aparecer, tenta de novo com mais passadas (até 3 vezes).
Uso (Python do venv do KiCad MCP): python route.py boards/<placa>/hardware [passes]   (precisa de java e ~/.kicad-mcp/freerouting.jar)"""
import subprocess, sys, tempfile, time
from pathlib import Path
import pcbnew

HW = Path(sys.argv[1])
PASSES = int(sys.argv[2]) if len(sys.argv) > 2 else 40
PCB = str(HW / "dumper.kicad_pcb")
JAR = Path.home() / ".kicad-mcp" / "freerouting.jar"
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)


def limpa():
    for t in list(b.GetTracks()):
        b.RemoveNative(t)
    for z in list(b.Zones()):
        b.RemoveNative(z)


def tentar(passes):
    d = tempfile.mkdtemp()
    dsn, ses = d + "/r.dsn", d + "/r.ses"
    pcbnew.ExportSpecctraDSN(b, dsn)
    r = subprocess.run(["java", "-jar", str(JAR), "-de", dsn, "-do", ses, "-mp", str(passes), "-mt", "1"], capture_output=True, text=True, timeout=3000)
    print(r.stdout[-300:])
    for _ in range(15):          # o .ses às vezes aparece um instante depois de o Java sair
        if Path(ses).exists() and Path(ses).stat().st_size > 0:
            return ses
        time.sleep(1)
    return None


def zonas():
    bb = b.GetBoardEdgesBoundingBox()
    net = b.FindNet("GND") or b.FindNet("/GND")
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


abertas = None
for n_try in (1, 2, 3):
    limpa()
    ses = tentar(PASSES + 10 * (n_try - 1))
    if not ses:
        print("tentativa", n_try, ": o freerouting não gerou o .ses")
        continue
    pcbnew.ImportSpecctraSES(b, ses)
    zonas()
    conn = b.GetConnectivity(); conn.RecalculateRatsnest()
    abertas = conn.GetUnconnectedCount(True)
    print("tentativa", n_try, ": ligações abertas:", abertas)
    if abertas == 0:
        break
if abertas is None:
    sys.exit("freerouting nao gerou o .ses")
pcbnew.SaveBoard(PCB, b)
print("trilhas:", len(list(b.GetTracks())), "zonas:", len(list(b.Zones())), "ligações abertas:", abertas)
if abertas:
    sys.exit("FALTAM %d ligações depois de 3 tentativas" % abertas)
