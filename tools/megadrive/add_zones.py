#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recria as duas zonas de GND (F.Cu e B.Cu) no retângulo do contorno, com os parâmetros das placas do projeto
(largura mínima 0,2 mm, folga 0,3 mm, alívio térmico 0,3 mm / raio 0,5 mm, ilhas removidas) e preenche.
Uso (Python do venv do KiCad MCP): add_zones.py placa.kicad_pcb"""
import sys, pcbnew
mm = pcbnew.FromMM
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
bb = b.GetBoardEdgesBoundingBox()
pts = [(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())]
net = (b.FindNet("GND") or b.FindNet("/GND"))
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net)
    z.SetMinThickness(mm(0.2)); z.SetLocalClearance(mm(0.3))
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(x, y)
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path, b); print("zonas", len(list(b.Zones())))
