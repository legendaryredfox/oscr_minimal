#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Magnavox Odyssey 2 (docs/planos/adaptadores.md#adaptador-odyssey2, D226) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/Odyssey2.cpp (duas colunas: pino numerado na frente, letra atrás);
2. a lista CONTROL PINS do mesmo quadro (sinal -> porta AVR);
3. o pinmap do slot SNES (pino do slot -> porta AVR);
4. as portas que o núcleo usa (A0-A7 em PF, A8-A11 em PK0-PK3, D0-D7 em PC; P10 e P11 nos bits 12 e 13, PK4 e PK5, por dedução: ver o plano).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("odyssey2")
CORE = ROOT / "firmware/oscr/src/cores/Odyssey2.cpp"
LETTERS = "ABCDEFGHJKLMNPR"     # fileira de trás: 15 letras, sem I, O e Q


def core_pinout() -> dict[str, str]:
    """Pino do conector ('1'..'15' e 'A'..'R') -> sinal. Vale a primeira palavra do rótulo (`A10 (P22)` -> `A10`)."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(\S+)(?:\s+\([^)]*\))?\s+-\|\s*(\d+)\s+([A-Z])\s*\|-\s*(\S+)", line)
        if m:
            out[m.group(2)] = m.group(1)
            out[m.group(3)] = m.group(4)
    return out


def core_control() -> dict[str, str]:
    """Lista CONTROL PINS: sinal -> porta (`T0(PH0)    - SNES RESET`)."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(/?[A-Z]+\d*)\((P[A-Z]\d)\)\s+-\s+SNES", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def expected_port(sig: str, control: dict[str, str]) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        bit = int(m.group(1))
        return f"PF{bit}" if bit < 8 else f"PK{bit - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    if sig in ("P10", "P11"):
        return {"P10": "PK4", "P11": "PK5"}[sig]
    return control.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    control = core_control()
    want_keys = [str(n) for n in range(1, 16)] + list(LETTERS)
    if sorted(cp) != sorted(want_keys):
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 30: 1 a 15 e {LETTERS})")
    if sorted(control) != sorted(["T0", "CS3", "/CS1", "/WR", "/PSEN"]):
        errs.append(f"lista CONTROL PINS do núcleo inesperada: {sorted(control)}")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| (\d+|[A-Z]) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 27:
        errs.append(f"tabela com {len(rows)} linhas (esperado 27: A0-A11, P10, P11, D0-D7 e 5 de controle)")
    used = []
    for sig, slot, port, conn in rows:
        used.append(conn)
        if cp.get(conn) != sig:
            errs.append(f"{sig}: pino {conn} do conector é '{cp.get(conn)}' no quadro do núcleo")
        if expected_port(sig, control) != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {expected_port(sig, control)}")
        got = pins.get(int(slot), ("?", "?"))[1]
        if got != port:
            errs.append(f"{sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")
    fixed = {"D": "VCC", "B": "GND", "C": "GND"}
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != sorted(want_keys):
        errs.append("os 30 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Odyssey 2:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
