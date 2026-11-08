# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando detect."""
from __future__ import annotations

from .. import protocol as P
from . import common, ui
from .common import system_id
from .messages import tr
from .errors import CliError, EXIT_NO_CART, EXIT_OK, EXIT_USAGE
from .md_chip import md_chip_line, md_flash_chip
from .output import emit


def cmd_detect(args) -> int:
    c, t, info = common.connect(args)
    sega = args.system in ("sms", "gg", "sg1000")          # o adaptador (campo mapper) muda a fiação dos barramentos; os outros sistemas ignoram as opções no DETECT
    r = c.detect(system_id(args.system), args.mapper if sega else 0)
    flash = None
    if getattr(args, "flash_id", False):
        if args.system != "md":
            t.close()
            raise CliError("usage", tr("detect.flash_id_md_only"), EXIT_USAGE)
        flash = md_flash_chip(c, info)
    status = {k: tr(f"detect.status.{k}") for k in range(5)}
    lines = [f"{P.SYSTEM_BY_ID.get(r['system'], r['system'])}: {status.get(r['status'], r['status'])}"]
    if r["status"] == 0:
        lines.append(tr("detect.title_line", name=r["name"] or tr("detect.unknown_title"), rom=r["rom_size"], save=r["save_size"]))
    if getattr(args, "flash_id", False):
        lines.append("  " + md_chip_line(flash))
    if r.get("attempts", 1) > 1:
        lines.append(tr("detect.attempts", n=r["attempts"]))
    obj = {"ok": r["status"] == 0, **r, "status_text": status.get(r["status"], str(r["status"])),
           **({"flash_chip": flash} if getattr(args, "flash_id", False) else {})}
    if not args.json and ui.fancy():                       # terminal: o cartucho desenhado ao lado dos dados
        fields = []
        if r["status"] == 0:
            fields = [(tr("detect.field_title"), r["name"] or tr("detect.unknown_title")), ("ROM", f"{r['rom_size']} bytes"), (tr("detect.field_save"), f"{r['save_size']} bytes")]
        if getattr(args, "flash_id", False):
            fields.append((tr("detect.field_chip"), md_chip_line(flash).split(": ", 1)[-1]))
        if r.get("attempts", 1) > 1:
            fields.append((tr("detect.field_tries"), tr("detect.field_tries_val", n=r["attempts"])))
        name = P.SYSTEM_BY_ID.get(r["system"], str(r["system"]))
        text = f"{name}: {status.get(r['status'], r['status']).split(' (')[0]}"
        art = {"snes": 1, "nes": 2, "famicom": 3, "md": 4, "gba": 5, "gb": 6}.get(name, 1)
        print("\n".join(ui.detect_card(art, text, r["status"] == 0, fields)))
    else:
        emit(args, obj, lines)
    t.close()
    return EXIT_OK if r["status"] == 0 else EXIT_NO_CART

