#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Casio PV-1000 (docs/planos/adaptador-pv1000.md, D219) contra
1. o quadro "Cartridge Pinout" (fileiras B e A) no começo de firmware/oscr/src/cores/CasioPV1000.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa: A(n) = bit n do endereço (PF para os bits 0-7, PK para 8-15), D(n) = PC(n) (ordem normal);
   /CS1 = PH4, /CS2 = PH3, /WR = PH5, /RD = PH6.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = ROOT / "docs/planos/adaptador-pv1000.md"
CORE = ROOT / "firmware/oscr/src/cores/CasioPV1000.cpp"


def core_pinout() -> dict[str, str]:
    """Pino do conector (B01..B18, A01..A18) -> sinal. Cada linha do quadro tem o pino B à esquerda e o A à direita."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(\S+)\s+-\|\s*([AB]\d\d)\s+([AB]\d\d)\s*\|-\s*(\S+)\s*$", line)
        if m:
            out[m.group(2)] = m.group(1)
            out[m.group(3)] = m.group(4)
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        bit = int(m.group(1))
        return f"PF{bit}" if bit < 8 else f"PK{bit - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return {"/CS1": "PH4", "/CS2": "PH3", "/WR": "PH5", "/RD": "PH6"}.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 36:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 36)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| ([AB]\d\d) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 28:
        errs.append(f"tabela com {len(rows)} linhas (esperado 28: A0-A15, D0-D7, /CS1, /CS2, /RD e /WR)")
    used: list[str] = []
    for sig, slot, port, conn in rows:
        used.append(conn)
        if cp.get(conn) != sig:
            errs.append(f"{sig}: pino {conn} do conector é '{cp.get(conn)}' no quadro do núcleo")
        if expected_port(sig) != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {expected_port(sig)}")
        got = pins.get(int(slot), ("?", "?"))[1]
        if got != port:
            errs.append(f"{sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")
    fixed = {"B01": "VCC", "B18": "VCC", "A01": "GND", "A18": "GND"}
    unused = {"B02": "NC", "A02": "NC", "B17": "CON", "A17": "/IORQ"}   # o núcleo não conduz (ver o plano)
    for c, want in {**fixed, **unused}.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != sorted(cp):
        errs.append("os 36 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos e não conduzidos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Casio PV-1000:", "divergências" if errs else f"ok ({len(rows)} linhas, {len(fixed)} fixos e {len(unused)} não conduzidos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
