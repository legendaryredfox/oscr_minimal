#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Atualiza o índice no topo de docs/decisoes.md (entre os marcadores <!-- indice --> e <!-- /indice -->). Rode depois de acrescentar uma decisão."""
import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "docs" / "decisoes.md"
s = p.read_text()
rows = []
for m in re.finditer(r"^### (D\d+) — (.+)$", s, re.M):
    rows.append(f"- **{m.group(1)}** {m.group(2)}")
block = "<!-- indice -->\n" + "\n".join(rows) + "\n<!-- /indice -->"
if "<!-- indice -->" in s:
    s = re.sub(r"<!-- indice -->.*?<!-- /indice -->", lambda _: block, s, flags=re.S)
else:
    first = s.index("\n") + 1
    s = s[:first] + "\n## Índice\n\n" + block + "\n" + s[first:]
p.write_text(s)
print(f"{len(rows)} decisões no índice")
