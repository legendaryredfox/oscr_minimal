#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Bally Astrocade (docs/planos/adaptador-astrocade.md, D223) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/BallyAstrocade.cpp (pino do conector -> sinal; uma coluna só);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa (A0-A7 em PF, A8-A12 em PK0-PK4, D0-D7 em PC, /ENABLE em PH3).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = ROOT / "docs/planos/adaptador-astrocade.md"
CORE = ROOT / "firmware/oscr/src/cores/BallyAstrocade.cpp"


def core_pinout() -> dict[int, str]:
    """Pino do conector -> sinal. O rótulo pode ter parênteses (`VCC(+5V)`): vale a primeira palavra."""
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*([^\s(]+)(?:\([^)]*\))?\s+-\|\s*(\d+)\s*\|", line)
        if m:
            out[int(m.group(2))] = m.group(1)
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        bit = int(m.group(1))
        return f"PF{bit}" if bit < 8 else f"PK{bit - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return {"/ENABLE": "PH3"}.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 26:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 26)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 22:
        errs.append(f"tabela com {len(rows)} linhas (esperado 22: A0-A12, D0-D7 e /ENABLE)")
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
    fixed = {25: "VCC", 1: "GND", 13: "GND", 26: "GND"}
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 27)):
        errs.append("os 26 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Bally Astrocade:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
