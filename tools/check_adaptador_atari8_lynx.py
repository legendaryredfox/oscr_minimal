#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere as tabelas dos adaptadores do Atari 8 bits e do Atari Lynx (docs/planos/adaptador-a8bit.md e adaptador-lynx.md, D210) contra
1. o quadro de pinos no começo de firmware/oscr/src/cores/Atari8.cpp e AtariLynx.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa. No Lynx só os sinais confirmados pelo código entram na tabela; A12 a A19 e AUDIN estão PENDENTES (o teste exige que o documento diga isso).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adaptador_ngp import snes_pins  # noqa: E402


def a8_pinout() -> dict[str, str]:
    """Quadro `NOME -| L nn |- NOME`: pino `L` (letra, esquerda) e `nn` (número, direita)."""
    out: dict[str, str] = {}
    for line in (ROOT / "firmware/oscr/src/cores/Atari8.cpp").read_text(encoding="utf-8").splitlines()[:40]:
        m = re.match(r"^\s*//(.*?)-\|\s*([A-Z])\s+(\d+)\s*\|-\s*(\S+)", line)
        if m:
            left, letter, num, right = m.groups()
            out[letter] = left.split()[-1]
            out[num] = right
    return out


def lynx_pinout() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (ROOT / "firmware/oscr/src/cores/AtariLynx.cpp").read_text(encoding="utf-8").splitlines()[:50]:
        m = re.match(r"^\s*//\s*\|\s*(\d+)\s*\|-\s*(\S+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def port_of(sig: str, a_hi: int) -> str | None:
    if sig == "/OE":
        return "PH6"
    if sig == "/WE":
        return "PH5"
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        if n <= a_hi:
            return f"PF{n}" if n < 8 else f"PK{n - 8}"
        return None
    m = re.fullmatch(r"D(\d)", sig)
    return f"PC{m.group(1)}" if m else None


def rows_of(doc: Path) -> list[tuple[str, str, str, str]]:
    rows = []
    for line in doc.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| ([AD]\d+|/S4|/S5|R/W|/CCTL|/OE|/WE|PHI2) \| (\d+) \| (P[A-Z]\d|-) \| (\w+) \|$", line)
        if m:
            rows.append(m.groups())
    return rows


def check(tag: str, doc: Path, pinout: dict[str, str], want_rows: int, a_hi: int, controls: dict[str, str], fixed: dict[str, str], free: dict[str, str], n_pins: int) -> list[str]:
    errs: list[str] = []
    pins = snes_pins()
    if len(pinout) != n_pins:
        errs.append(f"{tag}: quadro do núcleo com {len(pinout)} pinos (esperado {n_pins})")
    rows = rows_of(doc)
    if len(rows) != want_rows:
        errs.append(f"{tag}: tabela com {len(rows)} linhas (esperado {want_rows})")
    used: list[str] = []
    for sig, slot, port, conn in rows:
        used.append(conn)
        if pinout.get(conn) != sig:
            errs.append(f"{tag} {sig}: pino {conn} do conector é '{pinout.get(conn)}' no quadro do núcleo")
        want = controls.get(sig) or port_of(sig, a_hi)
        if want != port:
            errs.append(f"{tag} {sig}: tabela diz {port}, o núcleo usa {want}")
        if port == "-":
            if int(slot) != 57:
                errs.append(f"{tag} {sig}: a saída CLK1 do Si5351 é o pino 57 do slot SNES (tabela diz {slot})")
            continue
        got = pins.get(int(slot), ("?", "?"))[1]
        if got != port:
            errs.append(f"{tag} {sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")
    for c, want in {**fixed, **free}.items():
        used.append(c)
        if pinout.get(c) != want and not (want == "+5V" and pinout.get(c) in ("+5V", "5V")):
            errs.append(f"{tag}: pino {c} do conector é '{pinout.get(c)}' no quadro (esperado '{want}')")
    return errs, used  # type: ignore[return-value]


def main() -> int:
    errs: list[str] = []
    pins = snes_pins()
    # --- Atari 8 bits
    po = a8_pinout()
    e, used = check("a8bit", ROOT / "docs/planos/adaptador-a8bit.md", po, 26, 12, {"/S4": "PH6", "/S5": "PH3", "R/W": "PH5", "/CCTL": "PL0", "PHI2": "-"},
                    {"13": "+5V", "B": "GND"}, {"A": "RD4", "14": "RD5"}, 30)  # type: ignore[misc]
    errs += e
    if sorted(used) != sorted(po):
        errs.append(f"a8bit: pinos do conector que faltam ou sobram: {sorted(set(po) ^ set(used))}")
    doc8 = (ROOT / "docs/planos/adaptador-a8bit.md").read_text(encoding="utf-8")
    if "PENDENTE" in doc8:
        errs.append("a8bit: o documento não deveria ter mais PENDENTE (o PHI2 vai ao pino 57, D213)")
    if any(v[1] == "PH1" for v in pins.values()):
        errs.append("a8bit: o pinmap SNES passou a ter PH1; revisar a nota do PHI2")
    # --- Lynx
    pl = lynx_pinout()
    e, used = check("lynx", ROOT / "docs/planos/adaptador-lynx.md", pl, 21, 10, {}, {"1": "GND"}, {"31": "VCC", "33": "VCC", "34": "SWVCC"}, 34)  # type: ignore[misc]
    errs += e
    pend = {"26", "25", "24", "23", "19", "20", "21", "22", "32"}   # A12 a A19 e AUDIN
    if (set(pl) - set(used)) != pend:
        errs.append(f"lynx: os pinos fora da tabela deveriam ser os PENDENTES {sorted(pend)}, são {sorted(set(pl) - set(used))}")
    for k in sorted(pend, key=int):
        if not re.fullmatch(r"A1[2-9]|AUDIN", pl.get(k, "")):
            errs.append(f"lynx: pino {k} do quadro deveria ser A12-A19 ou AUDIN, é '{pl.get(k)}'")
    doc_l = (ROOT / "docs/planos/adaptador-lynx.md").read_text(encoding="utf-8")
    if "PENDENTES" not in doc_l:
        errs.append("lynx: o documento tem que listar A12 a A19 e AUDIN como PENDENTES")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"pino {p} do slot SNES não é '{want}' no pinmap")
    for e in errs:
        print("ERRO", e)
    print("adaptadores Atari 8 bits e Lynx:", "divergências" if errs else "ok (8 bits 26 linhas, Lynx 21 linhas; PENDENTES conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
