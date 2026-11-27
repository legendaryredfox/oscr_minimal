#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Vectrex (docs/planos/adaptadores.md#adaptador-vectrex, D205) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/Vectrex.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa (A0-A7 PF, A8-A15 PK, D0-D7 PC, /CART PH3, PB6 PH5, R/W PH6);
4. que o pino 57 do slot SNES NÃO é o PH1 (o /OE do Vectrex): o documento prende o /OE ao GND por isso.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("vectrex")
CORE = ROOT / "firmware/oscr/src/cores/Vectrex.cpp"


def core_pinout() -> dict[int, str]:
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s.*?(\S+)\s+-\|\s*(\d+)\s+(\d+)\s*\|-\s+(\S+)", line)
        if m and "---" not in line:
            out[int(m.group(2))] = m.group(1)
            out[int(m.group(3))] = m.group(4)
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PF{n}" if n < 8 else f"PK{n - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return {"/CART": "PH3", "PB6": "PH5", "R/W": "PH6"}.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 36:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 36)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z0-9/]+) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 27:
        errs.append(f"tabela com {len(rows)} linhas (esperado 27)")
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
    fixed = {2: "+5V", 4: "+5V", 25: "GND", 27: "GND", 28: "GND", 12: "/OE", 1: "/HALT", 34: "/NMI", 36: "/IRQ"}
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 37)):
        errs.append("os 36 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    if pins.get(57, ("?", "?"))[1] == "PH1":
        errs.append("o pino 57 do slot SNES agora é PH1: o /OE pode ir a ele; atualize o documento")
    if not re.search(r"/OE\(PH1\)", CORE.read_text(encoding="utf-8")):
        errs.append("o núcleo não declara mais /OE(PH1)")
    for e in errs:
        print("ERRO", e)
    print("adaptador Vectrex:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
