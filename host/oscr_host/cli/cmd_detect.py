# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando detect."""
from __future__ import annotations

from .. import protocol as P
from . import common, ui
from .common import system_id
from .. import autodetect as AUTO
from .. import n64 as N64
from .messages import tr
from .errors import CliError, EXIT_NO_CART, EXIT_OK, EXIT_USAGE
from .md_chip import md_chip_line, md_flash_chip
from .output import emit


def cmd_detect(args) -> int:
    c, t, info = common.connect(args)
    if args.system == "auto":                              # P5 (D160): descobre o sistema só com leituras e segue como se tivesse sido pedido
        found = AUTO.autodetect(c, info.get("systems"))
        if not found:
            t.close()
            raise CliError("no_cartridge", tr("auto.none"), EXIT_NO_CART)
        args.system = found[0]
        if not args.json:
            print(tr("auto.found", system=args.system), file=sys.stderr)
    sega = args.system in ("sms", "gg", "sg1000")          # o adaptador (campo mapper) muda a fiação dos barramentos; os outros sistemas ignoram as opções no DETECT
    r = c.detect(system_id(args.system), args.mapper if sega else 0)
    if args.system == "n64" and r["status"] == 0:
        r = N64.enrich_detect(r)                                # tamanho e save vêm da base pelo CRC1 do cabeçalho (D158)
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
    if r.get("n64"):
        n = r["n64"]
        lines.append(tr("n64.game_line", crc1=n["crc1"], gid=n["game_id"]) if n["found"] else tr("n64.unknown_game", crc1=n["crc1"], gid=n["game_id"]))
        if n["found"] and n.get("ambiguous"):
            lines.append(tr("n64.ambiguous", n=n["others"] + 1))
    if getattr(args, "flash_id", False):
        lines.append("  " + md_chip_line(flash))
    obj = {"ok": r["status"] == 0, **r, "status_text": status.get(r["status"], str(r["status"])),
           **({"flash_chip": flash} if getattr(args, "flash_id", False) else {})}
    if not args.json and ui.fancy():                       # terminal: o cartucho desenhado ao lado dos dados
        fields = []
        if r["status"] == 0:
            fields = [(tr("detect.field_title"), r["name"] or tr("detect.unknown_title")), ("ROM", f"{r['rom_size']} bytes"), (tr("detect.field_save"), f"{r['save_size']} bytes")]
        if getattr(args, "flash_id", False):
            fields.append((tr("detect.field_chip"), md_chip_line(flash).split(": ", 1)[-1]))
        name = P.SYSTEM_BY_ID.get(r["system"], str(r["system"]))
        text = f"{name}: {status.get(r['status'], r['status']).split(' (')[0]}"
        art = {"snes": 1, "nes": 2, "famicom": 3, "md": 4, "gba": 5, "gb": 6}.get(name, 1)
        print("\n".join(ui.detect_card(art, text, r["status"] == 0, fields)))
    else:
        emit(args, obj, lines)
    t.close()
    return EXIT_OK if r["status"] == 0 else EXIT_NO_CART

