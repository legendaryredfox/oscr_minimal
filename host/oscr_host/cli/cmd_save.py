# SPDX-License-Identifier: GPL-3.0-or-later
"""Comandos save-read e save-write."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from .. import protocol as P
from .. import romimage as RI
from ..verify import eeprom_is_4k
from . import common
from .common import system_id
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_REFUSED
from .output import emit, progress, save_result


def cmd_save_read(args) -> int:
    c, t, _ = common.connect(args)
    res = c.read_save(system_id(args.system), args.block, progress("save", args.progress), args.mapper, args.ram)
    t.close()
    notes = []
    if system_id(args.system) == 5 and args.mapper == 2 and eeprom_is_4k(res.data):
        notes.append(tr("save.eeprom_warn"))
    return save_result(args, res, ".sav", f"save_{args.system}", None, notes)


def cmd_save_write(args) -> int:
    data = Path(args.input).read_bytes()
    sid = system_id(args.system)
    if not args.yes:                                      # gravar sobrescreve (ou apaga) a memória do cartucho: sempre confirmar
        if not sys.stdin.isatty():
            raise CliError("refused", tr("refused.save"),
                           EXIT_REFUSED, tr("refused.save.hint"))
        ans = input(tr("save.ask", n=len(data), system=args.system))
        if ans.strip().lower() not in ("s", "sim", "y", "yes", "да", "д", "是", "是的"):
            print(tr("cancelled"))
            return 1
    c, t, _ = common.connect(args)
    try:
        extra: dict = {}
        if not args.no_backup:                            # backup do save atual antes de gravar
            cur = c.read_save(sid, args.block, progress("backup", args.progress), args.mapper, args.ram)
            bdir = Path(args.backup_dir).expanduser()
            bdir.mkdir(parents=True, exist_ok=True)
            bpath = bdir / f"{args.system}_{time.strftime('%Y%m%d-%H%M%S')}.sav"
            bpath.write_bytes(cur.data)
            extra["backup"] = str(bpath)
            if not args.json:
                print(f"backup do save atual: {bpath}  CRC32 {cur.crc32:08X}")
        crc = c.write_save(sid, data, args.block or P.DEFAULT_BLOCK, progress("write", args.progress), args.mapper, args.ram)
        v = None
        if not args.no_verify:                            # o WRITE_SAVE não relê: o PC lê o save de volta e compara
            v = RI.verify_save_written(c, sid, data, progress("verify", args.progress), args.mapper, args.ram)
    finally:
        t.close()
    extra.update({"bytes": len(data), "crc32": f"{crc:08X}"})
    lines = [tr("save.written", n=len(data), crc=f"{crc:08X}")]
    if v is None:
        extra["verify"] = "skipped"
        lines.append(tr("verify.skipped_flag"))
    else:
        extra["verify"] = v.to_dict()
        if not v.ok:
            raise CliError("verify_failed", tr("save.verify_failed", first=v.first_diff, read=f"{v.read_crc32:08X}", exp=f"{v.expected_crc32:08X}", n=v.read_bytes, total=len(data)),
                           EXIT_ERROR, tr("save.verify_failed.hint"),
                           written=extra, first_diff=v.first_diff)
        lines.append(tr("verify.ok", n=v.read_bytes, crc=f"{v.read_crc32:08X}"))
    emit(args, extra, lines)
    return 0

