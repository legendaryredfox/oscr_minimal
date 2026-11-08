# SPDX-License-Identifier: GPL-3.0-or-later
"""Tabela de chips de flash do OSCR (flash.json do oscr-databases): do ID que o chip responde ao nome, tipo, tamanho, setor e buffer.
No OSCR isso era o banco CRDB `flash` do cartão SD; aqui o PC lê o JSON (database/oscr/chips/flash.json) e **só sugere**: nada é
escolhido sozinho, quem manda é o `--flash-type`/`--flash-kb` do usuário. Vale para o flash de 8 e de 16 bits do programador genérico."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .romimage import FLASH_TYPES

FILE = Path(__file__).resolve().parents[2] / "database" / "oscr" / "chips" / "flash.json"
_TYPE_NAME = {v: k for k, v in FLASH_TYPES.items()}
_HEX = re.compile(r"\b([IABS])=([0-9A-Fa-f]{4})\b|\bID ([0-9A-Fa-f]{4})\b")


@lru_cache(maxsize=1)
def records() -> tuple[dict, ...]:
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    return tuple(r for r in data.get("records", []) if isinstance(r, dict) and r.get("type") in _TYPE_NAME)   # tipo 0 = chips de GBA, fora daqui


def ids_from_text(text: str) -> list[tuple[str, str]]:
    """O texto que o firmware devolve ("I=XXXX A=XXXX B=XXXX S=XXXX" ou "ID XXXX") -> [(rotina, ID)], sem 0000 nem FFFF."""
    out = []
    for m in _HEX.finditer(text):
        label, ident = (m.group(1), m.group(2)) if m.group(1) else ("", m.group(3))
        if ident.upper() not in ("0000", "FFFF"):
            out.append((label, ident.upper()))
    return out


def candidates(text: str, bus: str) -> list[dict]:
    """Chips da tabela que têm algum dos IDs de `text` e o barramento (8/plcc32 = 8 bits; 16 = 16 bits). Cada item traz o que usar na CLI."""
    want = 16 if bus == "16" else 8
    found, seen = [], set()
    for label, ident in ids_from_text(text):
        for r in records():
            if r["id"].upper() != ident or r.get("bits", 8) != want:
                continue
            key = (ident, r["name"], r.get("variant"))
            if key in seen:
                continue
            seen.add(key)
            found.append({"routine": label, "id": ident, "name": r["name"], "type": r["typeName"], "flash_type": _TYPE_NAME[r["type"]],
                          "size": r["size"], "sector_kb": r["sector"] // 1024 if r.get("sector") else None, "buffer": r.get("buffer"),
                          "voltage": r.get("voltage")})
    return found


def command_hint(c: dict, bus: str) -> str:
    """Opções da CLI para esse chip. No flash de 16 bits só o tamanho; no de 8 bits também o tipo e, se a tabela tiver, setor e buffer."""
    s = f"--flash-kb {c['size'] // 1024}"
    if bus != "16":
        s = f"--flash-type {c['flash_type']} " + s
        if c["sector_kb"] and c["buffer"]:
            s += f" --sector-kb {c['sector_kb']} --buffer {c['buffer']}"
    return s
