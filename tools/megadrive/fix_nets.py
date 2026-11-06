#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinos do Mega sem uso na placa só-Mega-Drive: a net do PCB passa a ser a 'unconnected-(A1-PadX)' do esquemático.
Uso (Python do venv do KiCad MCP): fix_nets.py placa.kicad_pcb PAD [PAD...]"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
a = b.FindFootprintByReference("A1")
for name in sys.argv[2:]:
    nn = "unconnected-(A1-Pad%s)" % name
    ni = b.FindNet(nn)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, nn); b.Add(ni)
    for p in a.Pads():
        if p.GetNumber() == name: p.SetNet(ni)
b.Save(sys.argv[1])
