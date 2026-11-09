#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bloco de troca (D126), roteamento: roteia com o Freerouting (DSN -> SES), cria as zonas de GND e preenche. Se sobrar ligação aberta
(o Freerouting às vezes deixa uma rede de fora sem avisar) ou o .ses não aparecer, tenta de novo com mais passadas (até 3 vezes).
Uso (Python do venv do KiCad MCP): python route.py boards/<placa>/hardware [passes]   (precisa de java e ~/.kicad-mcp/freerouting.jar)"""
import subprocess, sys, tempfile, time
from pathlib import Path
import pcbnew

SES_PRONTO = sys.argv[sys.argv.index("--ses") + 1] if "--ses" in sys.argv else None      # usa um .ses já gerado (Freerouting rodado à mão) na 1ª tentativa
if SES_PRONTO:
    i_ = sys.argv.index("--ses"); del sys.argv[i_:i_ + 2]
INCREMENTAL = "--incremental" in sys.argv       # continua de onde parou: mantém as trilhas existentes e só roteia o que falta
sys.argv = [a for a in sys.argv if a != "--incremental"]
HW = Path(sys.argv[1])
PASSES = int(sys.argv[2]) if len(sys.argv) > 2 else 40
PCB = str(HW / "dumper.kicad_pcb")
JAR = Path.home() / ".kicad-mcp" / "freerouting.jar"
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)


def limpa(tudo=True):
    if tudo:
        for t in list(b.GetTracks()):
            b.RemoveNative(t)
    for z in list(b.Zones()):
        b.RemoveNative(z)


def abertas_drc():
    """Ligações abertas segundo o DRC do KiCad (o contador de ratsnest da API não é confiável depois de importar o .ses)."""
    d = tempfile.mkdtemp()
    pcbnew.SaveBoard(d + "/t.kicad_pcb", b)
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-all", "-o", d + "/drc.txt", d + "/t.kicad_pcb"], capture_output=True)
    return Path(d + "/drc.txt").read_text().count("[unconnected_items]")


def tentar(passes):
    global SES_PRONTO
    if SES_PRONTO:
        ses_, SES_PRONTO = SES_PRONTO, None
        return ses_
    d = tempfile.mkdtemp()
    dsn, ses = d + "/r.dsn", d + "/r.ses"
    pcbnew.ExportSpecctraDSN(b, dsn)
    r = subprocess.run(["java", "-jar", str(JAR), "-de", dsn, "-do", ses, "-mp", str(passes), "-mt", "1"], capture_output=True, text=True, timeout=10800)
    print(r.stdout[-300:])
    for _ in range(180):         # o .ses às vezes aparece muito depois de o Java sair (máquina carregada)
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
for n_try in (1, 2, 3, 4):
    limpa(tudo=not (INCREMENTAL or n_try > 1))      # da 2ª tentativa em diante, continua sobre as trilhas já feitas
    ses = tentar(PASSES + 10 * (n_try - 1))
    if not ses:
        print("tentativa", n_try, ": o freerouting não gerou o .ses")
        continue
    pcbnew.ImportSpecctraSES(b, ses)
    zonas()
    abertas = abertas_drc()
    print("tentativa", n_try, ": ligações abertas (DRC):", abertas)
    if abertas == 0:
        break
if abertas is None:
    sys.exit("freerouting nao gerou o .ses")
pcbnew.SaveBoard(PCB, b)
print("trilhas:", len(list(b.GetTracks())), "zonas:", len(list(b.Zones())), "ligações abertas:", abertas)
if abertas:
    sys.exit("FALTAM %d ligações depois de 3 tentativas" % abertas)
