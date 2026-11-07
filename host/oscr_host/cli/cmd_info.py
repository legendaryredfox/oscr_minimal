# SPDX-License-Identifier: GPL-3.0-or-later
"""Comandos ports, systems, errors e info."""
from __future__ import annotations

from .. import __version__
from .. import protocol as P
from ..planned import PLANNED
from . import common, ui
from .errors import CLI_EXIT_CODES
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
         [f"{r['name']:8} id {r['id']:3}  {r['extension']:5} opções: {', '.join(r['options']) or '-'}" for r in rows]
         + ["", "em breve (outros cartuchos do OSCR, ainda sem hardware, firmware nem id no protocolo):"] + [f"  {p['name']:13} {p['label']}" for p in planned])
    return 0


def cmd_errors(args) -> int:
    dev = [{"code": c, "text": t, "hint": P.ERROR_HINTS.get(c)} for c, t in P.ERRORS.items()]
    cli = [{"exit_code": c, "meaning": m} for c, m in CLI_EXIT_CODES.items()]
    emit(args, {"device_errors": dev, "exit_codes": cli},
         [f"saída {c}: {m}" for c, m in CLI_EXIT_CODES.items()] + [f"erro 0x{d['code']:04X}: {d['text']}" for d in dev])
    return 0



def cmd_info(args) -> int:
    _c, t, info = common.connect(args)
    if args.json:
        emit(args, info, [])
        t.close()
        return 0
    if ui.fancy():
        print(ui.banner(__version__) + "\n")
    print(f"protocolo {info['proto']}  firmware {info['firmware']}  MOCK={'sim' if info['mock'] else 'não'}"
          f"  Si5351={'sim' if info['si5351'] else 'não'}  sistemas: {', '.join(info['systems']) or '-'}  payload máx. {info['max_payload']}")
    t.close()
    return 0

