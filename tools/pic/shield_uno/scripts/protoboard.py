#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Verifica a montagem na protoboard descrita no README (furos por tira: a-e e f-j de cada linha; trilhos + e -).
O "+" e o trilho de 13 V (a fonte entra direto: D1 e DNP); o "-" e o GND. Uso: python3 protoboard.py -> codigo 1 se algo diverge."""
import sys

def tira(h):
    """h = 'e10' -> tira; 'rail+' / 'rail-' ; 'UNO.D2' etc. ficam como estao (pontos soltos)"""
    if h.startswith(("rail", "UNO.", "FONTE.")):
        return h
    col, lin = h[0], int(h[1:])
    return ("E" if col in "abcde" else "D", lin)

# peca: {pino: furo}
PECAS = {
    "U2": {"1": "e10", "2": "e11", "3": "e12", "4": "e13", "8": "f10", "7": "f11", "6": "f12", "5": "f13"},
    "C1": {"1": "b10", "2": "rail-"},
    "Q1": {"C": "a13", "B": "a14", "E": "a15"},
    "R1": {"1": "c13", "2": "c17"},
    "R2": {"1": "b18", "2": "b14"},
    "R4": {"1": "a17", "2": "a21"},
    "D2": {"A": "b21", "K": "b22"},
    "R3": {"1": "g18", "2": "g22"},
    "D3": {"A": "h22", "K": "h23"},
}
JUMPERS = [("a10", "UNO.D2"), ("j11", "UNO.D7"), ("j12", "UNO.D4"), ("j10", "rail-"), ("b15", "rail-"),
           ("a18", "UNO.A1"), ("d17", "rail+"), ("c22", "rail-"), ("j18", "UNO.A5"), ("i23", "rail-"),
           ("FONTE.+", "rail+"), ("UNO.GND", "rail-"), ("FONTE.-", "rail-")]
ESPERADO = [
    {"UNO.D2", "U2.1", "C1.1"}, {"UNO.D4", "U2.6"}, {"UNO.D7", "U2.7"},
    {"U2.4", "Q1.C", "R1.1"}, {"UNO.A1", "R2.1"}, {"R2.2", "Q1.B"},
    {"UNO.GND", "FONTE.-", "U2.8", "Q1.E", "C1.2", "D2.K", "D3.K"},
    {"R1.2", "R4.1", "FONTE.+"}, {"R4.2", "D2.A"}, {"UNO.A5", "R3.1"}, {"R3.2", "D3.A"},
]

def main():
    pai = {}
    def f(a):
        pai.setdefault(a, a)
        while pai[a] != a:
            pai[a] = pai[pai[a]]; a = pai[a]
        return a
    pads = {}
    for ref, pinos in PECAS.items():
        for pino, h in pinos.items():
            pads[f"{ref}.{pino}"] = tira(h)
    # dois pads no mesmo furo
    furos = {}
    for k, h in {f"{r}.{p}": h for r, ps in PECAS.items() for p, h in ps.items()}.items():
        if not h.startswith("rail") and h in furos:
            print("dois pads no mesmo furo", h, k, furos[h]); sys.exit(1)
        furos[h] = k
    for a, b in JUMPERS:
        pai[f(tira(a))] = f(tira(b))
    for uno in ("UNO.D2", "UNO.D4", "UNO.D7", "UNO.A1", "UNO.A5", "UNO.GND", "FONTE.+", "FONTE.-"):
        pads[uno] = uno
    g = {}
    for nome, t in pads.items():
        g.setdefault(f(t), set()).add(nome)
    achados = [s for s in g.values() if len(s) > 1]
    erros = [f"falta: {sorted(e)}" for e in ESPERADO if e not in achados]
    erros += [f"a mais: {sorted(s)}" for s in achados if s not in ESPERADO]
    for p in ("U2.2", "U2.3", "U2.5"):
        if any(p in s for s in achados):
            erros.append(p + " devia ficar livre")
    if erros:
        print("\n".join(erros)); sys.exit(1)
    print(f"ok: {len(ESPERADO)} nets conferidas na protoboard")

if __name__ == "__main__":
    main()
