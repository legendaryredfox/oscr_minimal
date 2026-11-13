# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando gbcamera: extrai as fotos de um save do Game Boy Camera para PNG (P9, D160). Não abre o dispositivo."""
from __future__ import annotations

from pathlib import Path

from .. import gbcamera as GBC
from .errors import CliError, EXIT_ERROR, EXIT_USAGE
from .messages import tr
from .output import emit


def cmd_gbcamera(args) -> int:
    src = Path(args.input)
    data = src.read_bytes()
    try:
        photos = GBC.extract(data)
    except ValueError as e:
        raise CliError("bad_save", tr("gbcamera.bad_size", size=len(data), need=GBC.SAVE_BYTES), EXIT_ERROR) from e
    if not 1 <= args.scale <= 8:
        raise CliError("usage", tr("gbcamera.scale"), EXIT_USAGE)
    out = Path(args.output) if args.output else src.with_suffix("")
    out.mkdir(parents=True, exist_ok=True)
    files, skipped = [], []
    for p in photos:
        if (p.deleted or p.empty) and not args.all:
            skipped.append(p.name)
            continue
        f = out / (p.name + ("_apagada" if p.deleted else "") + ".png")
        f.write_bytes(GBC.png(p.pixels, p.width, p.height, args.palette, args.scale))
        files.append(str(f))
    emit(args, {"folder": str(out), "files": files, "skipped": skipped, "palette": args.palette, "scale": args.scale},
         [tr("gbcamera.done", n=len(files), folder=out)] + ([tr("gbcamera.skipped", n=len(skipped))] if skipped else []))
    return 0
