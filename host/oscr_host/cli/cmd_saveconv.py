# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando save-convert: troca a ordem dos bytes de um save para emulador (H-1, D163). Não abre o dispositivo."""
from __future__ import annotations

from pathlib import Path

from .. import saveconv as SC
from .errors import CliError, EXIT_ERROR, EXIT_USAGE
from .messages import tr
from .output import emit


def _fill(text: str) -> int:
    try:
        v = int(text, 0)
    except ValueError:
        v = -1
    if not 0 <= v <= 255:
        raise CliError("usage", tr("saveconv.fill"), EXIT_USAGE)
    return v


def cmd_saveconv(args) -> int:
    src = Path(args.input)
    data = src.read_bytes()
    fill = _fill(args.fill)
    try:
        out_data = SC.convert(data, args.op, fill)
    except ValueError as e:
        raise CliError("bad_save", tr("saveconv.bad_size", size=len(data), op=args.op), EXIT_ERROR) from e
    out = Path(args.output) if args.output else src.with_name(f"{src.stem}_{args.op}{src.suffix}")
    out.write_bytes(out_data)
    emit(args, {"input": str(src), "output": str(out), "op": args.op, "in_bytes": len(data), "out_bytes": len(out_data)},
         [tr("saveconv.done", op=args.op, n=len(out_data), out=out)])
    return 0
