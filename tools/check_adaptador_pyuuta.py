#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Tomy Pyuuta (docs/planos/adaptador-pyuuta.md, D217) contra
1. o quadro "Cartridge Pinout" (duas colunas) no começo de firmware/oscr/src/cores/TomyPyuuta.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa, na ordem invertida do TMS9995: A(n) = bit 15-n do endereço (PF para os bits 0-7, PK para 8-15), D(n) = PC(7-n);
   /CS0 = PH3, /CS1 = PH6, /DBIN = PH4, /RESET = PH0.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = ROOT / "docs/planos/adaptador-pyuuta.md"
CORE = ROOT / "firmware/oscr/src/cores/TomyPyuuta.cpp"


def core_pinout() -> dict[int, str]:
    """Pino do conector -> sinal. O quadro tem dois pinos por linha (par e ímpar); `A15/CRUOUT` vale `A15`."""
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(.+?)\s+-\|\s*(\d+)\s+(\d+)\s*\|-\s*(.+?)\s*$", line)
        if m:
            for pin, name in ((m.group(2), m.group(1)), (m.group(3), m.group(4))):
                a = re.match(r"A\d+", name)
                out[int(pin)] = a.group(0) if a else name
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        bit = 15 - int(m.group(1))
        return f"PF{bit}" if bit < 8 else f"PK{bit - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{7 - int(m.group(1))}"
    return {"/CS0": "PH3", "/CS1": "PH6", "/DBIN": "PH4", "/RESET": "PH0"}.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 36:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 36)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 28:
        errs.append(f"tabela com {len(rows)} linhas (esperado 28: A0-A15, D0-D7, /CS0, /CS1, /DBIN e /RESET)")
    used = []
    for sig, slot, port, conn in rows:
        c = int(conn)
        used.append(c)
        if cp.get(c) != sig:
            errs.append(f"{sig}: pino {c} do conector é '{cp.get(c)}' no quadro do núcleo")
        if expected_port(sig) != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {expected_port(sig)}")
        got = pins.get(int(slot), ("?", "?"))[1]
        if got != port:
            errs.append(f"{sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")
    fixed = {19: "VCC", 1: "GND", 2: "GND"}
    unused = {6: "J1-6", 32: "/WE/CPUCLK", 33: "SOUND", 34: "/INT4 /EC", 36: "CRUIN"}   # o núcleo não conduz (ver o plano)
    for c, want in {**fixed, **unused}.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 37)):
        errs.append("os 36 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos e não conduzidos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Tomy Pyuuta:", "divergências" if errs else f"ok ({len(rows)} linhas, {len(fixed)} fixos e {len(unused)} não conduzidos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
