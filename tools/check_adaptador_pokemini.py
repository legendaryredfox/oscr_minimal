#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Pokémon Mini (docs/planos/adaptador-pokemini.md, D227) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/PokemonMini.cpp (fileira B1 a B17 à esquerda, A1 a A15 à direita);
2. a lista CONTROL PINS do mesmo quadro (sinal -> porta AVR);
3. o pinmap do slot SNES (pino do slot -> porta AVR);
4. as portas que o `readData` do núcleo usa: fase LALE com A0-A7 em PF e A8-A9 em PK0-PK1; fase HALE com A10-A17 em PF e A18-A20 em PK0-PK2
   (o rótulo `Ax/Ay` precisa ter y = x + 10; o A20 vai em PK2); D0-D7 em PC.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = ROOT / "docs/planos/adaptador-pokemini.md"
CORE = ROOT / "firmware/oscr/src/cores/PokemonMini.cpp"
KEYS = [f"B{n}" for n in range(1, 18)] + [f"A{n}" for n in range(1, 16)]   # 32 pinos: B1-B17 e A1-A15


def core_pinout() -> dict[str, str]:
    """Pino do conector ('B1'..'B17', 'A1'..'A15') -> sinal, do quadro de duas colunas (`A20 -| B2 |` e `| A2 |- A9/A19`)."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(\S.*?)\s+-\|\s*(B\d+)\s*\|\s*$", line)
        if m:
            out[m.group(2)] = m.group(1)
        m = re.match(r"^\s*//\s*\|\s*(A\d+)\s*\|-\s*(\S.*?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def core_control() -> dict[str, str]:
    """Lista CONTROL PINS: sinal -> porta (`HALE(PH0) - SNES RESET`)."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*([A-Z]+)\((P[A-Z]\d)\)\s+-\s+SNES", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def expected_port(sig: str, control: dict[str, str]) -> str | None:
    m = re.fullmatch(r"A(\d+)/A(\d+)", sig)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if hi != lo + 10 or lo > 9:
            return None
        return f"PF{lo}" if lo < 8 else f"PK{lo - 8}"
    if sig == "A20":
        return "PK2"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return control.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    control = core_control()
    if sorted(cp) != sorted(KEYS):
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 32: B1 a B17 e A1 a A15)")
    if sorted(control) != sorted(["HALE", "CS", "LALE", "WE", "OE"]):
        errs.append(f"lista CONTROL PINS do núcleo inesperada: {sorted(control)}")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| ([A-Z]+\d*(?:/A\d+)?) \| (\d+) \| (P[A-Z]\d) \| ([AB]\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 24:
        errs.append(f"tabela com {len(rows)} linhas (esperado 24: 11 de endereço, D0-D7 e 5 de controle)")
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
    fixed = {"B1": "VCC (3.3V)", "A1": "VCC (3.3V)", "A7": "VCC (3.3V)", "A8": "GND", "A15": "GND", "B17": "GND", "A13": "IRQ", "B16": "CARD_N"}
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != sorted(KEYS):
        errs.append("os 32 pinos do conector não aparecem todos uma vez (tabela, pinos fixos e sem ligação)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Pokémon Mini:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos ou sem ligação conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
