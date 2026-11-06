#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Liga pads de GND ao plano sem alívio térmico (conexão sólida), para resolver avisos starved_thermal do DRC.
Uso (Python do venv do KiCad MCP): solid_pad.py placa.kicad_pcb REF:PAD [REF:PAD ...]   (depois preencher as zonas)"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for a in sys.argv[2:]:
    ref, pad = a.split(":")
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == pad: p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); print(ref, pad, "sólido")
pcbnew.SaveBoard(sys.argv[1], b)
