#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinos do Mega sem uso na placa só-Mega-Drive: a net do PCB passa a ser a 'unconnected-(A1-PadX)' do esquemático.
Uso (Python do venv do KiCad MCP): fix_nets.py placa.kicad_pcb PAD. Um pad por chamada: com vários, só o primeiro pegava (rode num laço)"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
a = b.FindFootprintByReference("A1")
for name in sys.argv[2:]:
    nn = "unconnected-(A1-Pad%s)" % name
    ni = b.FindNet(nn)
    if ni is None:
        b.Add(pcbnew.NETINFO_ITEM(b, nn)); ni = b.FindNet(nn)   # achar de novo: o objeto Python não é o dono
    for p in a.Pads():
        if p.GetNumber() == name: p.SetNet(ni)
pcbnew.SaveBoard(sys.argv[1], b)
