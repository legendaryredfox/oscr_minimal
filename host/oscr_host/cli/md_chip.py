# SPDX-License-Identifier: GPL-3.0-or-later
"""Identificação do chip de flash de um cartucho de Mega Drive (usada por detect e rom-write)."""
from __future__ import annotations

from .messages import tr
from .. import romimage as RI


BOARD_LIMITED_CHIPS = ("S29GL064N", "S29GL-7E")
BOARD_LIMIT_BYTES = 2 << 20


def md_flash_chip(c, info: dict) -> dict | None:
    """Identifica o chip de flash do cartucho de Mega Drive (DETECT do sistema 7, chip 5). None se o firmware não tem o programador de flash.
    ATENÇÃO: a sondagem escreve comandos de ID no cartucho (ROM de máscara os ignora), por isso só roda quando o usuário pede ou antes de gravar."""
    if not info.get("flash_prog"):
        return None
    r = c.detect(7, RI.FLASHPROG_BUS["md"], 0, 0)
    known = r["status"] == 0
    return {"known": known, "ids": r["name"], "chip": r["name"].rsplit(" ", 1)[0] if known else None,
            "codes": r["name"].rsplit(" ", 1)[-1] if " " in r["name"] else "",
            "size": r["rom_size"] if known or r["name"].startswith("CFI ") else 0}


def board_limit_bytes(chip: dict | None) -> int | None:
    """Limite de ROM da placa do cartucho, quando o chip identificado é o S29GL (ID 017E): os cartuchos KY / FlashKit selecionam a flash só nos 2 MiB de baixo
    (74HC139 sem registrador) e o resto é a SRAM de save (bancada do md_rewriter, 2026-11-13). None = sem limite conhecido. Só um aviso: outra placa com o mesmo chip pode ter 8 MiB."""
    if chip and chip.get("known") and chip.get("chip") in BOARD_LIMITED_CHIPS:
        return BOARD_LIMIT_BYTES
    return None


def md_chip_line(chip: dict | None) -> str:
    if chip is None:
        return tr("chip.no_id")
    if chip["known"]:
        return tr("chip.known", chip=chip["chip"], kb=chip["size"] // 1024, codes=chip.get("codes", ""))
    return tr("chip.unknown", ids=chip["ids"]) + (tr("chip.cfi_size", kb=chip["size"] // 1024) if chip["size"] else "")

