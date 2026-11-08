# SPDX-License-Identifier: GPL-3.0-or-later
"""Comandos ports, systems, errors e info."""
from __future__ import annotations

from .. import __version__
from .. import protocol as P
from ..planned import PLANNED
from . import common, ui
from .errors import CLI_EXIT_CODES
from .messages import tr
from .output import emit


def cmd_ports(args) -> int:
    ports = common.list_ports()
    emit(args, {"ports": ports}, ports)
    return 0


# Opções específicas de cada sistema (as de --mapper, --prg, --chr e --ram; o sentido de cada uma está em --help)
SYSTEM_OPTIONS = {"snes": ["prg"], "nes": ["mapper", "prg", "chr", "ram"], "famicom": ["mapper", "prg", "chr", "ram"],
                  "md": ["prg"], "gba": ["mapper"], "gb": [], "mock": []}


def cmd_systems(args) -> int:
    rows = [{"name": n, "id": v[0], "extension": v[1], "options": SYSTEM_OPTIONS.get(n, []), "needs_cartridge": n != "mock"}
            for n, v in P.SYSTEMS.items()]
    planned = [{"name": k, "label": l, "supported": False} for k, l in PLANNED]
    emit(args, {"systems": rows, "planned": planned},
         [f"{r['name']:8} id {r['id']:3}  {r['extension']:5} {tr('systems.options')}: {', '.join(r['options']) or '-'}" for r in rows]
         + ["", tr("systems.planned")] + [f"  {p['name']:13} {p['label']}" for p in planned])
    return 0


def cmd_errors(args) -> int:
    dev = [{"code": c, "text": tr(f"dev.{c}.msg"), "hint": tr(f"dev.{c}.hint")} for c in P.ERRORS]
    cli = [{"exit_code": c, "meaning": tr(f"exit.{c}")} for c in CLI_EXIT_CODES]
    emit(args, {"device_errors": dev, "exit_codes": cli},
         [tr("errors.exit_line", code=c["exit_code"], text=c["meaning"]) for c in cli] + [tr("errors.dev_line", code=d["code"], text=d["text"]) for d in dev])
    return 0



def cmd_info(args) -> int:
    _c, t, info = common.connect(args, need_cart=False)
    if args.json:
        emit(args, info, [])
        t.close()
        return 0
    if ui.fancy():
        print(ui.banner(__version__) + "\n")
    print(tr("info.line", proto=info["proto"], fw=info["firmware"], mock=tr("yes" if info["mock"] else "no"), si=tr("yes" if info["si5351"] else "no"),
             systems=", ".join(info["systems"]) or "-", maxp=info["max_payload"]))
    t.close()
    return 0

