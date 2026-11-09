#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: poda trilhas com ponta solta (sem pad, via ou outra trilha na ponta), que sobram quando o F1 antigo sai da placa (fusivel138.py).
Uso (python do venv do KiCad MCP): python tools/troca/poda138.py <pasta hardware>..."""
import sys
from pathlib import Path
import pcbnew


def poda(b):
    total = 0
    for _ in range(500):
        pads = {}
        for f in b.GetFootprints():
            for q in f.Pads():
                pads.setdefault(q.GetNetCode(), set()).add((q.GetPosition().x, q.GetPosition().y))
        pts = {}
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA":
                for ly in (pcbnew.F_Cu, pcbnew.B_Cu):       # a via liga as duas faces
                    pts.setdefault((t.GetPosition().x, t.GetPosition().y, t.GetNetCode(), ly), []).append(t.m_Uuid.AsString())
            else:
                for q in (t.GetStart(), t.GetEnd()):
                    pts.setdefault((q.x, q.y, t.GetNetCode(), t.GetLayer()), []).append(t.m_Uuid.AsString())
        mortos = []
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA":
                continue
            u = t.m_Uuid.AsString(); nc = t.GetNetCode()
            for q in (t.GetStart(), t.GetEnd()):
                k = (q.x, q.y, nc, t.GetLayer())
                if (q.x, q.y) in pads.get(nc, set()):
                    continue
                if not [o for o in pts[k] if o != u]:
                    mortos.append(t); break
        if not mortos:
            break
        for t in mortos:
            b.RemoveNative(t); total += 1
    return total


if __name__ == "__main__":
    for hw in sys.argv[1:]:
        p = str(Path(hw) / "dumper.kicad_pcb"); b = pcbnew.LoadBoard(p)
        n = poda(b)
        if n:
            pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(p, b)
        print(hw, "trilhas soltas podadas:", n)
