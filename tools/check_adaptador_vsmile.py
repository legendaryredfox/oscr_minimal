#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do V.Smile (docs/planos/adaptador-vsmile.md, D228) contra
1. o quadro "Cartridge pinout" no começo de firmware/oscr/src/cores/VSmile.cpp (linhas `SINAL -| 25    1 |- SINAL`);
2. os `#define VSMILE_*_HIGH` de firmware/oscr/include/cores/VSmile.h (sinal de controle -> bit de PORTH);
3. o pinmap do slot SNES (pino do slot -> porta AVR);
4. as portas que o `read_rom_word` do núcleo usa: A1-A8 em PF, A9-A16 em PK, A17-A22 em PL0-PL5, D0-D7 em PC e D8-D15 em PA.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = ROOT / "docs/planos/adaptador-vsmile.md"
CORE = ROOT / "firmware/oscr/src/cores/VSmile.cpp"
HEADER = ROOT / "firmware/oscr/include/cores/VSmile.h"


def core_pinout() -> dict[int, str]:
    """Pino do conector (1 a 48) -> sinal, do quadro de duas colunas (`VCC -| 25    1 |- WE`)."""
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(\S+)\s+-\|\s*(\d+)\s+(\d+)\s*\|-\s*(\S+)\s*$", line)
        if m:
            out[int(m.group(2))] = m.group(1)
            out[int(m.group(3))] = m.group(4)
    return out


def core_control() -> dict[str, str]:
    """`#define VSMILE_OE_HIGH PORTH |= (1<<3)` -> {'OE': 'PH3'}."""
    out: dict[str, str] = {}
    for line in HEADER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*#\s*define\s+VSMILE_([A-Z0-9]+)_HIGH\s+PORTH\s*\|=\s*\(1\s*<<\s*(\d)\)", line)
        if m:
            out[m.group(1)] = f"PH{m.group(2)}"
    return out


def expected_port(sig: str, control: dict[str, str]) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 8:
            return f"PF{n - 1}"
        if 9 <= n <= 16:
            return f"PK{n - 9}"
        if 17 <= n <= 22:
            return f"PL{n - 17}"
        return None
    m = re.fullmatch(r"D(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PC{n}" if n < 8 else f"PA{n - 8}" if n < 16 else None
    return control.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    control = core_control()
    if sorted(cp) != list(range(1, 49)):
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 48: 1 a 48)")
    if control != {"OE": "PH3", "CSB1": "PH6", "CSB2": "PH4"}:
        errs.append(f"#define de controle do núcleo inesperados: {control}")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| ([A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 41:
        errs.append(f"tabela com {len(rows)} linhas (esperado 41: A1-A22, D0-D15, OE, CSB1 e CSB2)")
    used: list[int] = []
    for sig, slot, port, conn in rows:
        used.append(int(conn))
        if cp.get(int(conn)) != sig:
            errs.append(f"{sig}: pino {conn} do conector é '{cp.get(int(conn))}' no quadro do núcleo")
        if expected_port(sig, control) != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {expected_port(sig, control)}")
        got = pins.get(int(slot), ("?", "?"))[1]
        if got != port:
            errs.append(f"{sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")
    fixed = {24: "VCC", 25: "VCC", 27: "VCC", 3: "GND", 23: "GND", 1: "WE", 26: "RAMCS"}   # WE e RAMCS: PENDENTE no plano
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 49)):
        errs.append("os 48 pinos do conector não aparecem todos uma vez (tabela, pinos fixos e pendentes)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador V.Smile:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos ou pendentes conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
