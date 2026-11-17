# SPDX-License-Identifier: GPL-3.0-or-later
"""Comandos save-read e save-write."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from .. import autodetect as AUTO
from .. import n64 as N64
from .. import protocol as P
from .. import romimage as RI
from ..verify import eeprom_is_4k
from . import common
from .common import system_id
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_REFUSED, EXIT_USAGE
from .output import emit, progress, save_result


def _n64_save_type(c, args) -> int:
    """Tipo de save do N64 (campo mapper): --mapper vale sempre; senão o CRC1 do cabeçalho na base do projeto (D158)."""
    if args.mapper:
        if not N64.save_type_valid(args.mapper):
            raise CliError("usage", tr("n64.save_type_bad", types=", ".join(f"{k} = {v}" for k, v in N64.SAVE_LABEL.items() if k)), EXIT_USAGE)
        return args.mapper
    info = N64.enrich_detect(c.detect(11)).get("n64") or {}
    if not info.get("found"):
        raise CliError("usage", tr("n64.need_save", crc1=info.get("crc1") or "?", types=", ".join(f"{k} = {v}" for k, v in N64.SAVE_LABEL.items() if k)), EXIT_USAGE)
    if not info["save_type"]:
        raise CliError("no_save", tr("n64.no_save"), EXIT_ERROR)
    return info["save_type"]


def _stype_kw(args) -> dict:
    t = common.snes_type_code(args)
    return {"snes_type": t} if t else {}


def cmd_save_read(args) -> int:
    c, t, info = common.connect(args)
    if args.system == "auto":                             # P5 (D160): descobre o sistema só com leituras (só na leitura; gravar exige o sistema explícito)
        found = AUTO.autodetect(c, info.get("systems"))
        if not found:
            t.close()
            raise CliError("no_cartridge", tr("auto.none"), 2)
        args.system = found[0]
        if not args.json:
            print(tr("auto.found", system=args.system), file=sys.stderr)
    if args.system == "n64":
        try:
            args.mapper = _n64_save_type(c, args)
        except CliError:
            t.close()
            raise
    res = c.read_save(system_id(args.system), args.block, progress("save", args.progress), args.mapper, args.ram, **_stype_kw(args))
    t.close()
    notes = []
    if system_id(args.system) == 5 and args.mapper == 2 and eeprom_is_4k(res.data):
        notes.append(tr("save.eeprom_warn"))
    acc = getattr(args, "accessory", None)
    return save_result(args, res, ".bin" if acc else ".sav", f"save_snes_{acc.replace('-', '_')}" if acc else f"save_{args.system}", None, notes)


def cmd_save_write(args) -> int:
    data = Path(args.input).read_bytes()
    sid = system_id(args.system)
    if getattr(args, "accessory", None):
        common.snes_type_code(args)                       # valida o acessório antes de qualquer coisa
        want = P.SNES_SAVE_ACCESSORIES[args.accessory]
        if len(data) != want:
            raise CliError("bad_rom", tr("gpc.size", n=len(data), want=want), EXIT_USAGE)
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
        if sid == 11:
            args.mapper = _n64_save_type(c, args)
        kw = _stype_kw(args)                              # SNES: tipo forçado (F-2); sem --type nada muda na chamada
        extra: dict = {}
        if not args.no_backup:                            # backup do save atual antes de gravar
            cur = c.read_save(sid, args.block, progress("backup", args.progress), args.mapper, args.ram, **kw)
            bdir = Path(args.backup_dir).expanduser()
            bdir.mkdir(parents=True, exist_ok=True)
            bpath = bdir / f"{args.system}_{time.strftime('%Y%m%d-%H%M%S')}.sav"
            bpath.write_bytes(cur.data)
            extra["backup"] = str(bpath)
            if not args.json:
                print(tr("save.backup", path=bpath, crc=f"{cur.crc32:08X}"))
        crc = c.write_save(sid, data, args.block or P.DEFAULT_BLOCK, progress("write", args.progress), args.mapper, args.ram, **kw)
        v = None
        if not args.no_verify:                            # o WRITE_SAVE não relê: o PC lê o save de volta e compara
            v = RI.verify_save_written(c, sid, data, progress("verify", args.progress), args.mapper, args.ram, **kw)
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

