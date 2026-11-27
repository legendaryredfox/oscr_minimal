#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do Fairchild Channel F (docs/planos/adaptadores.md#adaptador-channelf, D224) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/ChannelF.cpp (pino do conector -> sinal; o sinal fica à direita do número);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa: ROMC0-ROMC4 em PF0-PF4, D0-D7 em PC, PHI em PH3, /INTREQ em PH4 e WRITE em PH5 (lista "CONTROL PINS" do núcleo).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("channelf")
CORE = ROOT / "firmware/oscr/src/cores/ChannelF.cpp"


def core_pinout() -> dict[int, str]:
    """Pino do conector -> sinal. O rótulo pode ter parênteses (`VDD(+5V)`): vale a primeira palavra."""
    out: dict[int, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*\|\s*(\d+)\s*\|-\s*([^\s(]+)", line)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


def core_control() -> dict[str, str]:
    """Lista "CONTROL PINS" do núcleo: sinal -> porta (`PHI(PH3) - SNES /CS`)."""
    out: dict[str, str] = {}
    for line in CORE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*(/?[A-Z]+\d?)\((P[A-Z]\d)\)\s+-\s+SNES", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def expected_port(sig: str) -> str | None:
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return core_control().get(sig)


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout()
    if len(cp) != 22:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 22)")
    ctl = core_control()
    if len(ctl) != 8:
        errs.append(f"lista CONTROL PINS do núcleo com {len(ctl)} sinais (esperado 8: PHI, /INTREQ, WRITE e ROMC0-ROMC4)")
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d?) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 16:
        errs.append(f"tabela com {len(rows)} linhas (esperado 16: ROMC0-ROMC4, D0-D7, PHI, /INTREQ e WRITE)")
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
    fixed = {1: "GND", 2: "GND", 19: "VDD", 20: "VDD", 21: "NC", 22: "VGG"}   # VGG é +12 V: o slot não tem (ver o plano)
    for c, want in fixed.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 23)):
        errs.append("os 22 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos)")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador Fairchild Channel F:", "divergências" if errs else f"ok ({len(rows)} linhas e {len(fixed)} pinos fixos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
