# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando detect."""
from __future__ import annotations

from .. import protocol as P
from . import common, ui
from .common import system_id
from .errors import CliError, EXIT_NO_CART, EXIT_OK, EXIT_USAGE
from .md_chip import md_chip_line, md_flash_chip
from .output import emit


def cmd_detect(args) -> int:
    c, t, info = common.connect(args)
    r = c.detect(system_id(args.system))
    flash = None
    if getattr(args, "flash_id", False):
        if args.system != "md":
            t.close()
            raise CliError("usage", "--flash-id vale só para o Mega Drive (-s md)", EXIT_USAGE)
        flash = md_flash_chip(c, info)
    status = {0: "cartucho detectado", 1: "nenhum cartucho", 2: "não suportado",
              3: "erro de hardware", 4: "cabeçalho inválido ou ilegível (há dados, mas o checksum do cabeçalho não confere; ou, no Mega Drive com a placa v. 1.2, o pino /CART indica cartucho mas o cabeçalho não leu: limpe os contatos e encaixe de novo)"}
    lines = [f"{P.SYSTEM_BY_ID.get(r['system'], r['system'])}: {status.get(r['status'], r['status'])}"]
    if r["status"] == 0:
        lines.append(f"  título: {r['name'] or '(desconhecido)'}  ROM: {r['rom_size']} bytes  save: {r['save_size']} bytes")
    if getattr(args, "flash_id", False):
        lines.append("  " + md_chip_line(flash))
    obj = {"ok": r["status"] == 0, **r, "status_text": status.get(r["status"], str(r["status"])),
           **({"flash_chip": flash} if getattr(args, "flash_id", False) else {})}
    if not args.json and ui.fancy():                       # terminal: o cartucho desenhado ao lado dos dados
        fields = []
        if r["status"] == 0:
            fields = [("título", r["name"] or "(desconhecido)"), ("ROM", f"{r['rom_size']} bytes"), ("save", f"{r['save_size']} bytes")]
        if getattr(args, "flash_id", False):
            fields.append(("chip", md_chip_line(flash).removeprefix("chip de flash: ")))
        name = P.SYSTEM_BY_ID.get(r["system"], str(r["system"]))
        text = f"{name}: {status.get(r['status'], r['status']).split(' (')[0]}"
        art = {"snes": 1, "nes": 2, "famicom": 3, "md": 4, "gba": 5, "gb": 6}.get(name, 1)
        print("\n".join(ui.detect_card(art, text, r["status"] == 0, fields)))
    else:
        emit(args, obj, lines)
    t.close()
    return EXIT_OK if r["status"] == 0 else EXIT_NO_CART

