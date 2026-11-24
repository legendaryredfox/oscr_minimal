#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere docs/planos/adaptador-jaguar.md (D211) contra o pinmap do slot SNES e do Mega Drive: os pinos que a tabela lista batem com as portas, e o conflito
documentado continua verdadeiro (PE3 só no Mega Drive, PL7 só fora dele). Sai com 1 se algo divergir; se o pinmap mudar e o conflito sumir, avisa para revisar o documento."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINMAP = ROOT / "boards/16_and_8_bits/docs/pinmap.md"
DOC = ROOT / "docs/planos/adaptador-jaguar.md"


def section(prefix: str) -> dict[str, str]:
    out: dict[str, str] = {}
    on = False
    for line in PINMAP.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            on = line.startswith("## " + prefix)
            continue
        m = re.match(r"^\| (\S+) \| [^|]+ \| [^|]+ \| ([^|]+) \|", line)
        if on and m:
            out[m.group(1)] = m.group(2).strip()
    return out


def main() -> int:
    errs: list[str] = []
    snes, md = section("SNES"), section("Mega Drive")
    by_port_snes = {p: k for k, p in snes.items()}
    by_port_md = {p: k for k, p in md.items()}
    doc = DOC.read_text(encoding="utf-8")
    groups = {"PF": range(8), "PK": range(8), "PL": range(8), "PC": range(8)}
    rows = re.findall(r"^\| ([^|]+) \| (P[A-Z]\d(?: a P[A-Z]\d)?) \| ([\d, ]+) \|$", doc, re.M)
    if len(rows) != 14:
        errs.append(f"tabela com {len(rows)} linhas (esperado 14)")
    for sig, ports, pins in rows:
        plist = [int(x) for x in pins.replace(" ", "").split(",")]
        if " a " in ports:
            a, b = ports.split(" a ")
            names = [f"{a[:2]}{i}" for i in range(int(a[2]), int(b[2]) + 1)]
        else:
            names = [ports]
        if len(names) != len(plist):
            errs.append(f"{sig}: {len(names)} portas e {len(plist)} pinos")
            continue
        for n, pin in zip(names, plist):
            if snes.get(str(pin)) != n:
                errs.append(f"{sig}: pino {pin} do slot SNES é {snes.get(str(pin))} no pinmap (tabela diz {n})")
    # o conflito documentado
    if "PE3" in by_port_snes:
        errs.append("PE3 chegou ao slot SNES: o conflito do adaptador do Jaguar acabou, revisar docs/planos/adaptador-jaguar.md")
    if by_port_md.get("PE3") != "B15":
        errs.append("PE3 deveria estar no pino B15 do slot Mega Drive")
    if "PL7" in by_port_md:
        errs.append("PL7 chegou ao slot Mega Drive: revisar o conflito do adaptador do Jaguar")
    if "PL7" not in by_port_snes:
        errs.append("PL7 deveria estar no slot SNES")
    if "PENDENTE" not in doc:
        errs.append("o documento tem que se declarar PENDENTE")
    for e in errs:
        print("ERRO", e)
    print("adaptador Atari Jaguar:", "divergências" if errs else "ok (14 linhas e o conflito PE3 x PL7 conferidos)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
