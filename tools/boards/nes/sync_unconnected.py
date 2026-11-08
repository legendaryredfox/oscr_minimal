#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Passa para o PCB as nets 'unconnected-(...)' do esquemático (pinos sem ligação): o equivalente de rodar fix_nets.py
em laço, mas lendo a netlist (kicad-cli sch export netlist --format kicadsexpr) e tratando qualquer referência.
Uso (Python do venv do KiCad MCP): sync_unconnected.py placa.kicad_pcb netlist.net"""
import re, sys, pcbnew
path, net = sys.argv[1], sys.argv[2]
s = open(net).read()
todo = []
for m in re.finditer(r'\(net\s+\(code "\d+"\)\s+\(name "(unconnected-[^"]*)"\)(.*?)\n\t\t\)', s, re.S):
    for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m.group(2)):
        todo.append((m.group(1), ref, pin))
for nn, ref, pin in todo:      # uma net por vez: o objeto da net só vale depois de achado de novo
    b = pcbnew.LoadBoard(path)
    if b.FindNet(nn) is None: b.Add(pcbnew.NETINFO_ITEM(b, nn))
    ni = b.FindNet(nn)
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == pin: p.SetNet(ni)
    pcbnew.SaveBoard(path, b)
print(len(todo), "pinos")
