# SPDX-License-Identifier: GPL-3.0-or-later
"""Comandos identify e search (base de dados de jogos)."""
from __future__ import annotations

import zlib
from pathlib import Path

from .. import protocol as P
from .common import load_db
from .messages import tr
from .errors import EXIT_ERROR, EXIT_OK
from .output import emit


_EXT_SYSTEM = {".sfc": 1, ".smc": 1, ".nes": 2, ".md": 4, ".gen": 4, ".smd": 4, ".gba": 5, ".gb": 6, ".gbc": 6}


def cmd_identify(args) -> int:
    db = load_db(args, required=True)
    results = []
    for f in args.files:
        data = Path(f).read_bytes()
        sid = P.SYSTEMS[args.system][0] if args.system != "mock" else _EXT_SYSTEM.get(Path(f).suffix.lower(), 0)
        m = db.identify(sid, data)
        results.append({"file": f, "bytes": len(data), "crc32": f"{zlib.crc32(data):08X}", "game": m.to_dict() if m else None})
    lines = [f"{r['file']}  CRC32 {r['crc32']}  " + (f"{r['game']['name']} ({r['game']['source']}, {r['game']['match']})" if r["game"] else tr("db.not_found"))
             for r in results]
    emit(args, {"entries_in_database": len(db), "results": results}, lines)
    return EXIT_OK if all(r["game"] for r in results) else EXIT_ERROR


def cmd_search(args) -> int:
    db = load_db(args, required=True)
    found = db.search(args.query, args.limit)
    emit(args, {"entries_in_database": len(db), "results": [e.to_dict() for e in found]},
         [f"{e.crc:08X}  {e.name}" + (f"  [mapper {e.mapper}, PRG {e.prg_kb} KB, CHR {e.chr_kb} KB, RAM {e.ram_kb} KB]" if e.nes_options() else "") for e in found]
         or [tr("search.none")])
    return EXIT_OK if found else EXIT_ERROR

