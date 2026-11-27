#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Neo Geo Pocket (docs/planos/adaptadores.md#adaptador-ngp, D203) contra o pinmap do slot SNES
(boards/16_and_8_bits/docs/pinmap.md) e contra as portas que o núcleo NeoGeoPocket.cpp usa.

1. cada sinal da tabela cai no pino do slot SNES cuja porta AVR é a que a tabela diz (pinmap);
2. essa porta é a que o núcleo usa (A0-A7 PF, A8-A15 PK, A16-A20 PL0-4, D0-D7 PC, /CE0 PH3, /CE1 PH0, /OE PH6, /WE PH5, PWR PH4);
3. os pinos do conector do NGP não se repetem e vão de 1 a 36;
4. GND e VCC do slot são GND e 5 V (fixo) no pinmap (o que motiva o regulador de 3,3 V do adaptador).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
DOC = secao_doc("ngp")
PINMAP = ROOT / "boards/16_and_8_bits/docs/pinmap.md"
CORE = ROOT / "firmware/oscr/src/cores/NeoGeoPocket.cpp"


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PF{n}" if n < 8 else f"PK{n - 8}" if n < 16 else f"PL{n - 16}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return {"/CE0": "PH3", "/CE1": "PH0", "/OE": "PH6", "/WE": "PH5", "PWR": "PH4"}.get(sig)


def snes_pins() -> dict[int, tuple[str, str]]:
    out: dict[int, tuple[str, str]] = {}
    on = False
    for line in PINMAP.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            on = line.startswith("## SNES")
            continue
        m = re.match(r"^\| (\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", line)
        if on and m:
            out[int(m.group(1))] = (m.group(3).strip(), m.group(4).strip())
    return out


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| ([A-Z/][A-Za-z0-9/]*) \| ([\d e]+) \| ([A-Z]{2}\d|-) \| (\d+) \|$", line)
        if m:
            rows.append((m.group(1), m.group(2), m.group(3), int(m.group(4))))
    if len(rows) != 36:
        errs.append(f"tabela com {len(rows)} linhas (esperado 36)")
    ngp_pins = [r[3] for r in rows if r[0] not in ("GND", "VCC")]
    if len(ngp_pins) != len(set(ngp_pins)) or not all(1 <= p <= 36 for p in ngp_pins):
        errs.append("pinos do conector repetidos ou fora de 1..36")
    core = CORE.read_text(encoding="utf-8")
    for sig, ctl in (("/CE0", "PH3"), ("/CE1", "PH0"), ("/OE", "PH6"), ("/WE", "PH5"), ("PWR", "PH4")):
        if not re.search(rf"//\s*{re.escape(sig)}:\s*{ctl}\b", core):
            errs.append(f"o núcleo não declara {sig}: {ctl}")
    for sig, slot, port, ngp in rows:
        if sig in ("GND", "VCC"):
            for p in map(int, slot.split(" e ")):
                want = "GND" if sig == "GND" else "5V (fixo)"
                got = pins.get(p, ("?", "?"))[0]
                if got != want:
                    errs.append(f"{sig}: pino {p} do slot é '{got}' no pinmap (esperado '{want}')")
            continue
        exp = expected_port(sig)
        if exp != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {exp}")
        p = int(slot)
        got = pins.get(p, ("?", "?"))[1]
        if got != port:
            errs.append(f"{sig}: pino {p} do slot SNES é {got} no pinmap (tabela diz {port})")
    for e in errs:
        print("ERRO", e)
    print("adaptador NGP:", "divergências" if errs else f"ok ({len(rows)} linhas conferidas)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
