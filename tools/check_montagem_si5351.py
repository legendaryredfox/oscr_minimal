#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere que o aviso do módulo Si5351 (P-13, D-6) é idêntico em todo montagem.md de placa que tem o header U1.

Placa com o header = o montagem.md fala do "Header fêmea do Si5351 (U1)". O aviso fica num bloco que começa em `<!-- si5351-aviso -->`.
Sai com 1 se faltar em alguma placa ou se o texto divergir entre elas."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HAS_HEADER = re.compile(r"^\d+\.\s+\*\*Header fêmea do Si5351 \(U1\)\*\*", re.M)
BLOCK = re.compile(r"^> <!-- si5351-aviso -->\n((?:> .*\n?)+)", re.M)


def check() -> list[str]:
    errors: list[str] = []
    texts: dict[str, str] = {}
    for f in sorted((ROOT / "boards").glob("*/docs/montagem.md")):
        s = f.read_text()
        board = f.parent.parent.name
        if not HAS_HEADER.search(s):
            if "si5351-aviso" in s:
                errors.append(f"{board}: tem o aviso do Si5351 mas não tem o header U1")
            continue
        m = BLOCK.search(s)
        if not m:
            errors.append(f"{board}: falta o aviso do módulo Si5351 (<!-- si5351-aviso -->)")
        else:
            texts[board] = m.group(1)
    if len(set(texts.values())) > 1:
        ref = next(iter(texts.values()))
        errors += [f"{b}: o aviso do Si5351 difere do das outras placas" for b, t in texts.items() if t != ref]
    return errors


if __name__ == "__main__":
    errs = check()
    for e in errs:
        print("ERRO:", e)
    print("ok" if not errs else f"{len(errs)} problema(s)")
    sys.exit(1 if errs else 0)
