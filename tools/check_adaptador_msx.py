#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do MSX (docs/planos/adaptadores.md#adaptador-msx, D230) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/MSX.cpp (linhas `SINAL -| 2   1 |- SINAL`);
2. a lista "CONTROL PINS" do mesmo arquivo (`/SLTSL(PH3) - SNES /CS`: sinal -> porta AVR);
3. o pinmap do slot SNES (pino do slot -> porta AVR);
4. as portas que o `readData` e o `writeData` do núcleo usam: A0-A7 em PF, A8-A15 em PK e D0-D7 em PC.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("msx")
CORE = ROOT / "firmware/oscr/src/cores/MSX.cpp"


def core_pinout() -> dict[int, str]:
    """Pino do conector (1 a 50) -> sinal, do quadro de duas colunas (`/CS2 -| 2   1 |- /CS1`)."""
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(\S+?)\s*-\|\s*(\d+)\s+(\d+)\s*\|-\s*(\S+)\s*$", line)
        if m:
            out[int(m.group(2))] = m.group(1)
            out[int(m.group(3))] = m.group(4)
    return out


def core_control() -> dict[str, str]:
    """`// /SLTSL(PH3) - SNES /CS` -> {'/SLTSL': 'PH3'}."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(/?[A-Z0-9]+)\((P[A-Z]\d)\)\s+-\s+SNES\b", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def expected_port(sig: str, control: dict[str, str]) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PF{n}" if n < 8 else f"PK{n - 8}" if n < 16 else None
    m = re.fullmatch(r"D(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PC{n}" if n < 8 else None
    return control.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    control = core_control()
    if sorted(cp) != list(range(1, 51)):
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 50: 1 a 50)")
    want_ctrl = {"/RESET": "PH0", "CLOCK": "PH1", "/SLTSL": "PH3", "/MERQ": "PH4", "/WR": "PH5", "/RD": "PH6", "/CS1": "PL0", "/CS2": "PL1", "/CS12": "PL2"}
    if control != want_ctrl:
        errs.append(f"lista de controle do núcleo inesperada: {control}")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 32:
        errs.append(f"tabela com {len(rows)} linhas (esperado 32: A0-A15, D0-D7 e 8 sinais de controle)")
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
    fixed = {45: "+5V", 47: "+5V", 41: "GND", 43: "GND",
             5: "RSV(NC)", 16: "RSV(NC)", 7: "/WAIT", 8: "/INT", 10: "/BUSDIR", 44: "SW1", 46: "SW2", 48: "+12V", 49: "SOUNDIN", 50: "-12V",
             42: "CLOCK", 11: "/IORQ", 9: "/M1", 6: "/RFSH"}   # CLOCK no pino 57 (CLK1 do Si5351, D230); /IORQ, /M1 e /RFSH: PENDENTE no plano
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 51)):
        errs.append("os 50 pinos do conector não aparecem todos uma vez (tabela, pinos fixos, sem ligação e pendentes)")
    if "PH1" in {v[1] for v in pins.values()}:
        errs.append("PH1 apareceu no slot SNES: rever a ligação do CLOCK no plano")
    if "CLK1" not in pins.get(57, ("?", "?"))[0]:
        errs.append(f"pino 57 do slot SNES não é o CLK1 do Si5351 no pinmap ({pins.get(57)})")
    if "**CLOCK (42) no pino 57 do slot SNES**" not in DOC.read_text(encoding="utf-8"):
        errs.append("o plano não liga o CLOCK (42) ao pino 57 do slot SNES")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador MSX:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos, sem ligação ou pendentes conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
