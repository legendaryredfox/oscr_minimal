#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere a tabela do adaptador do TRS-80 Color Computer (docs/planos/adaptadores.md#adaptador-trs80, D248) contra
1. o quadro "Cartridge Pinout" (duas colunas) no começo de firmware/oscr/src/cores/TRS80.cpp (pino do conector -> sinal);
2. a lista "CONTROL PINS" do mesmo arquivo (sinal de controle -> bit de PORTH) e o `readData` (A0-A7 em PORTF, A8-A15 em PORTK, dados em PINC);
3. o pinmap do slot SNES (pino do slot -> porta AVR).
Também confere que o E (PH1 no núcleo) não está no slot SNES e que a seção manda prendê-lo em nível alto.
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

DOC = secao_doc("trs80")
CORE = ROOT / "firmware/oscr/src/cores/TRS80.cpp"


def core_pinout(text: str) -> dict[int, str]:
    """Pino do conector -> sinal. O quadro tem dois pinos por linha (ímpar à esquerda, par à direita)."""
    out: dict[int, str] = {}
    for line in text.splitlines():
        m = re.match(r"^\s*//\s*(\S+)\s+-\|\s*(\d+)\s+(\d+)\s*\|-\s*(\S+)\s*$", line)
        if m:
            out[int(m.group(2))] = m.group(1)
            out[int(m.group(3))] = m.group(4)
    return out


def core_controls(text: str) -> dict[str, str]:
    """`// /RESET(PH0)    - SNES RESET` -> {'/RESET': 'PH0'}, só dentro do bloco CONTROL PINS."""
    out: dict[str, str] = {}
    on = False
    for line in text.splitlines():
        if "CONTROL PINS" in line:
            on = True
            continue
        if on:
            m = re.match(r"^\s*//\s*(\S+)\((P[A-Z]\d)\)\s*-", line)
            if not m:
                break
            out[m.group(1)] = m.group(2)
    return out


def expected_port(sig: str, ctl: dict[str, str]) -> str | None:
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PF{n}" if n < 8 else f"PK{n - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    if m:
        return f"PC{m.group(1)}"
    return ctl.get(sig)


def main() -> int:
    errs: list[str] = []
    text = CORE.read_text(encoding="utf-8")
    pins = snes_pins()
    by_port = {port: p for p, (_, port) in pins.items()}
    cp = core_pinout(text)
    if len(cp) != 40:
        errs.append(f"quadro do núcleo com {len(cp)} pinos (esperado 40)")
    ctl = core_controls(text)
    if ctl != {"/RESET": "PH0", "E": "PH1", "/CTS": "PH3", "/SCS": "PH4", "R/W": "PH5"}:
        errs.append(f"lista CONTROL PINS do núcleo mudou: {ctl}")
    body = text[text.index("uint8_t readData(uint16_t addr)"):]
    body = body[:body.index("return ret;")]
    for want in ("PORTF = addr & 0xFF", "PORTK = (addr >> 8) & 0xFF", "PORTH &= ~(1 << 3)", "PINC"):
        if want not in body:
            errs.append(f"readData do núcleo não tem '{want}'")

    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (/?[A-Z]+\d*|R/W) \| (\d+) \| (P[A-Z]\d) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    if len(rows) != 28:
        errs.append(f"tabela com {len(rows)} linhas (esperado 28: A0-A15, D0-D7, /RESET, /CTS, /SCS e R/W)")
    used = []
    for sig, slot, port, conn in rows:
        c = int(conn)
        used.append(c)
        if cp.get(c) != sig:
            errs.append(f"{sig}: pino {c} do conector é '{cp.get(c)}' no quadro do núcleo")
        if expected_port(sig, ctl) != port:
            errs.append(f"{sig}: tabela diz {port}, o núcleo usa {expected_port(sig, ctl)}")
        got = pins.get(int(slot), ("?", "?"))[1]
        if got != port:
            errs.append(f"{sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")

    fixed = {9: "+5V", 33: "GND", 34: "GND", 6: "E"}            # E preso em nível alto no adaptador (D248)
    unused = {1: "NC", 2: "NC", 3: "/HALT", 4: "/NMI", 7: "Q", 8: "/CART", 35: "SND", 40: "/SLENB"}   # o núcleo não conduz (ver o plano)
    for c, want in {**fixed, **unused}.items():
        used.append(c)
        if cp.get(c) != want:
            errs.append(f"pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, 41)):
        errs.append("os 40 pinos do conector não aparecem todos uma vez (tabela mais pinos fixos e não conduzidos)")
    if "PH1" in by_port:
        errs.append(f"PH1 apareceu no slot SNES (pino {by_port['PH1']}): o E pode ir ao Mega em vez de ficar preso em nível alto")
    doc = DOC.read_text(encoding="utf-8")
    if "**E (6): preso ao +5V no adaptador" not in doc:
        errs.append("a seção não diz que o E (pino 6) vai preso ao +5V")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptador TRS-80:", "divergências" if errs else f"ok ({len(rows)} linhas, {len(fixed)} fixos e {len(unused)} não conduzidos conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
