#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Renumera os símbolos de alimentação (#PWR) do esquemático em sequência (#PWR001, #PWR002...), na ordem em que aparecem no arquivo.
Só a referência muda (esses símbolos não existem no PCB). Uso: python3 tools/boards/8_bits/renum_pwr.py boards/8_bits/hardware-vX/dumper.kicad_sch"""
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
order = []
for m in re.finditer(r'#PWR\d+', s):
    if m.group(0) not in order: order.append(m.group(0))
mp = {old: f"#PWR{i + 1:03d}" for i, old in enumerate(order)}
s = re.sub(r'#PWR\d+', lambda m: mp[m.group(0)], s)
p.write_text(s)
print(len(order), "símbolos #PWR renumerados")
