#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Confere a PCB contra a tabela de ligacoes do ardpicprog (D91, tools/pic/uno/README.md), de forma independente do
esquematico: le os pads da placa e checa que cada grupo esta numa net so e que os grupos nao se misturam.
Uso (Python do venv do KiCad MCP): check_netlist.py   -> codigo 1 se algo diverge"""
import sys
from pathlib import Path

import pcbnew

PCB = str(Path(__file__).resolve().parent.parent / "hardware" / "shield_uno.kicad_pcb")
GRUPOS = {
    "VDD (D2 do Uno -> pino 1 do PIC)": [("A1", "D2"), ("U2", "1"), ("C1", "1"), ("J2", "2"), ("TP2", "1")],
    "clock (D4 -> pino 6)": [("A1", "D4"), ("U2", "6"), ("J2", "5")],
    "dados (D7 -> pino 7)": [("A1", "D7"), ("U2", "7"), ("J2", "4")],
    "MCLR (pino 4)": [("U2", "4"), ("R1", "2"), ("Q1", "1"), ("J2", "1"), ("TP1", "1")],
    "comando do MCLR (A1 -> R2)": [("A1", "A1"), ("R2", "1")],
    "base do transistor": [("R2", "2"), ("Q1", "2")],
    "GND": [("A1", "GND1"), ("A1", "GND2"), ("A1", "GND3"), ("U2", "8"), ("Q1", "3"), ("C1", "2"), ("J1", "2"), ("J2", "3"),
            ("D2", "1"), ("D3", "1"), ("TP3", "1")],
    "13 V depois do diodo": [("D1", "1"), ("R1", "1"), ("R4", "1")],
    "13 V na entrada": [("J1", "1"), ("D1", "2")],
    "LED de 13 V": [("R4", "2"), ("D2", "2")],
    "A5 -> LED de atividade": [("A1", "A5"), ("R3", "1")],
    "LED de atividade": [("R3", "2"), ("D3", "2")],
}
# pinos que devem ficar sem ligacao
LIVRES = [("U2", "2"), ("U2", "3"), ("U2", "5"), ("J2", "6")]


def main():
    b = pcbnew.LoadBoard(PCB)
    erros, nets = [], {}
    for nome, pads in GRUPOS.items():
        ns = set()
        for ref, pino in pads:
            fp = b.FindFootprintByReference(ref)
            pad = fp.FindPadByNumber(pino) if fp else None
            if pad is None:
                erros.append(f"{nome}: {ref}.{pino} nao existe")
                continue
            ns.add(pad.GetNetname())
        if len(ns) != 1:
            erros.append(f"{nome}: nets diferentes {sorted(ns)}")
        else:
            n = ns.pop()
            if n in nets:
                erros.append(f"{nome} e {nets[n]} estao na mesma net {n}")
            nets[n] = nome
    for ref, pino in LIVRES:
        n = b.FindFootprintByReference(ref).FindPadByNumber(pino).GetNetname()
        if not n.startswith("unconnected"):
            erros.append(f"{ref}.{pino} devia ficar livre e esta em {n}")
    # nenhum pad do Uno alem dos usados tem net
    usados = {p for r, p in sum(GRUPOS.values(), []) if r == "A1"}
    for pad in b.FindFootprintByReference("A1").Pads():
        if pad.GetNumber() not in usados and not pad.GetNetname().startswith("unconnected") and pad.GetNetname():
            erros.append(f"A1.{pad.GetNumber()} tem net {pad.GetNetname()}")
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    print(f"ok: {len(GRUPOS)} grupos, {len(LIVRES)} pinos livres")


if __name__ == "__main__":
    main()
