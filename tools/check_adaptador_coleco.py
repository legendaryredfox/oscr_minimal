#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do ColecoVision (docs/planos/adaptadores.md#adaptador-coleco, D204) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/Colecovision.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa (A0-A7 PF, A8-A14 PK, D0-D7 PC, /8000 PH3, /A000 PH4, /C000 PH5, /E000 PH6).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("coleco")
CORE = ROOT / "firmware/oscr/src/cores/Colecovision.cpp"


def core_pinout() -> dict[int, str]:
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s+(\S+)\s+-\|\s*(\d+)\s+(\d+)\s*\|-\s+(\S+)", line)
        if m:
            out[int(m.group(2))] = m.group(1)
            out[int(m.group(3))] = m.group(4)
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PF{n}" if n < 8 else f"PK{n - 8}" if n < 15 else None
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return {"/8000": "PH3", "/A000": "PH4", "/C000": "PH5", "/E000": "PH6"}.get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 30:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 30)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z0-9]+) \| ([\d e]+) \| ([A-Z]{2}\d|-) \| ([\d e]+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 29:
        errs.append(f"tabela com {len(rows)} linhas (esperado 29)")
    used = []
    for sig, slot, port, conn in rows:
        if sig in ("GND", "VCC"):
            for p in map(int, slot.split(" e ")):
                want = "GND" if sig == "GND" else "5V (fixo)"
                got = pins.get(p, ("?", "?"))[0]
                if got != want:
                    errs.append(f"{sig}: pino {p} do slot é '{got}' (esperado '{want}')")
            for c in map(int, conn.split(" e ")):
                used.append(c)
                want = "VCC(+5V)" if sig == "VCC" else None
                got = cp.get(c, "?")
                if (sig == "VCC" and got != want) or (sig == "GND" and not got.startswith("GND")):
                    errs.append(f"{sig}: pino {c} do conector é '{got}' no quadro do núcleo")
            continue
        c = int(conn)
        used.append(c)
        if cp.get(c) != sig:
            errs.append(f"{sig}: pino {c} do conector é '{cp.get(c)}' no quadro do núcleo")
        if expected_port(sig) != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {expected_port(sig)}")
        if pins.get(int(slot), ("?", "?"))[1] != port:
            errs.append(f"{sig}: pino {slot} do slot SNES é {pins.get(int(slot), ('?', '?'))[1]} no pinmap (tabela diz {port})")
    if sorted(used) != list(range(1, 31)):
        errs.append("os 30 pinos do conector não aparecem todos uma vez")
    for e in errs:
        print("ERRO", e)
    print("adaptador ColecoVision:", "divergências" if errs else f"ok ({len(rows)} linhas conferidas)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
