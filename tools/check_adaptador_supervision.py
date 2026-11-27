#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Watara Supervision (docs/planos/adaptadores.md#adaptador-supervision, D218) contra
1. o quadro "Cartridge Pinout" (duas colunas) no começo de firmware/oscr/src/cores/Supervision.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa: A0-A7 em PF, A8-A15 em PK, A16 em PL0, D0-D7 em PC, /RD em PH6 e /WR em PH5.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("supervision")
CORE = ROOT / "firmware/oscr/src/cores/Supervision.cpp"


def core_pinout() -> dict[int, str]:
    """Pino do conector -> sinal. O quadro tem dois pinos por linha (esquerda 1-20, direita 40-21)."""
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(\S+)\s+-\|\s*(\d+)\s+(\d+)\s*\|-\s*(.+?)\s*$", line)
        if m:
            out[int(m.group(2))] = m.group(1)
            out[int(m.group(3))] = m.group(4)
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        bit = int(m.group(1))
        return f"PF{bit}" if bit < 8 else f"PK{bit - 8}" if bit < 16 else f"PL{bit - 16}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return {"/RD": "PH6", "/WR": "PH5"}.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 40:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 40)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 27:
        errs.append(f"tabela com {len(rows)} linhas (esperado 27: A0-A16, D0-D7, /RD e /WR)")
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
    fixed = {40: "+5V", 22: "GND", 21: "PWR GND"}
    unused = {19: "L3", 20: "L0", 23: "L2", 24: "L1", 25: "nc", 26: "nc", 36: "nc", 37: "nc", 38: "nc", 39: "nc"}   # o núcleo não conduz (ver o plano)
    for c, want in {**fixed, **unused}.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 41)):
        errs.append("os 40 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos e não conduzidos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Watara Supervision:", "divergências" if errs else f"ok ({len(rows)} linhas, {len(fixed)} fixos e {len(unused)} não conduzidos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
