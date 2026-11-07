# SPDX-License-Identifier: GPL-3.0-or-later
"""Identificação do chip de flash de um cartucho de Mega Drive (usada por detect e rom-write)."""
from __future__ import annotations

from .. import romimage as RI


def md_flash_chip(c, info: dict) -> dict | None:
    """Identifica o chip de flash do cartucho de Mega Drive (DETECT do sistema 7, chip 5). None se o firmware não tem o programador de flash.
    ATENÇÃO: a sondagem escreve comandos de ID no cartucho (ROM de máscara os ignora), por isso só roda quando o usuário pede ou antes de gravar."""
    if not info.get("flash_prog"):
        return None
    r = c.detect(7, RI.FLASHPROG_BUS["md"], 0, 0)
    known = r["status"] == 0
    return {"known": known, "ids": r["name"], "chip": r["name"].rsplit(" ", 1)[0] if known else None,
            "size": r["rom_size"] if known or r["name"].startswith("CFI ") else 0}


def md_chip_line(chip: dict | None) -> str:
    if chip is None:
        return "chip de flash: este firmware não identifica o chip"
    if chip["known"]:
        return f"chip de flash: {chip['chip']}  ({chip['size'] // 1024} KB)"
    return f"chip de flash: fora da tabela ou sem resposta ({chip['ids']})" + (f"; a consulta CFI diz {chip['size'] // 1024} KB" if chip["size"] else "")

