# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando dump (ROM), com a leitura raw do NES."""
from __future__ import annotations

import sys
import zlib

from .. import database as DB
from .. import protocol as P
from ..client import TimeoutError_
from ..verify import gba_save_hint, verify_rom
from . import common
from .common import game_options, load_db, system_id
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_USAGE
from .output import diff_summary, emit, out_path, progress, safe_name, save_result


def cmd_dump(args) -> int:
    sid = system_id(args.system)
    db = load_db(args, required=bool(args.game))
    if args.game:
        if sid not in DB.NES_SYSTEMS:
            raise CliError("usage", tr("dump.game_only_nes"), EXIT_USAGE)
        g = game_options(db, args.game)
        o = g.nes_options()
        args.mapper = args.mapper or o["mapper"]
        args.prg = args.prg or o["prg"]
        args.chr = args.chr or o["chr"]
        if not args.json:
            print(f"jogo da base: {g.name}  mapper {o['mapper']}  PRG {o['prg']} KB  CHR {o['chr']} KB  ({g.source})", file=sys.stderr)
    c, t, _ = common.connect(args)
    title = ""
    if not args.output:                                   # sem -o: nome do arquivo pelo título do cartucho
        try:
            title = c.detect(sid).get("name", "")
        except (P.DeviceError, P.ProtocolError, TimeoutError_):
            title = ""
    if getattr(args, "raw", False) and sid not in DB.NES_SYSTEMS:
        t.close()
        raise CliError("usage", tr("dump.raw_only_nes"), EXIT_USAGE)
    try:
        res = c.dump_rom(sid, args.block, progress("rom", args.progress), args.mapper, args.prg, args.chr)
        res2 = c.dump_rom(sid, args.block, progress("rom 2", args.progress), args.mapper, args.prg, args.chr) if getattr(args, "twice", False) else None
    finally:
        t.close()
    ext = P.SYSTEMS[args.system][1]
    if sid == 6 and len(res.data) > 0x143 and res.data[0x143] & 0x80:
        ext = ".gbc"                                      # cabeçalho com a flag de Game Boy Color
    if res2 is not None and res2.data != res.data:
        _twice_mismatch(args, res, res2, ext, safe_name(title, f"rom_{args.system}"))
    chk = verify_rom(sid, res.data)
    notes = []
    extra: dict = {"checksum": chk.status}
    if res2 is not None:
        extra["twice"] = True
        notes.append(tr("dump.twice_ok", crc=f"{res.crc32:08X}"))
    if chk.status != "na":
        notes.append((tr("dump.warning") if chk.status == "mismatch" else "") + str(chk))
    if db is not None:
        m = db.identify(sid, res.data)
        extra["game"] = m.to_dict() if m else None
        if m:
            title = m.entry.name
            notes.append(tr("dump.game_more" if m.others else "dump.game", name=m.entry.name, source=m.entry.source, how=m.how, others=m.others))
        else:
            notes.append(tr("dump.game_missing", n=len(db)))
    if sid == 5:
        hint = gba_save_hint(res.data)
        if hint:
            code, label, tag = hint
            extra["gba_save_type"] = code
            more = " (se o save sair repetido a cada 512 bytes, use --mapper 1)" if code == 2 else ""
            notes.append(f"save do GBA: {tag}, {label}: use --mapper {code} em save-read{more}")
        else:
            notes.append("save do GBA: nenhuma cadeia de biblioteca de save na ROM (sem save, ou tipo desconhecido)")
    if getattr(args, "raw", False):
        return _save_nes_raw(args, res, safe_name(title, f"rom_{args.system}"), extra, notes)
    return save_result(args, res, ext, safe_name(title, f"rom_{args.system}"), extra, notes)


def _save_nes_raw(args, res, default: str, extra: dict, notes: list[str]) -> int:
    """NES/Famicom com --raw: grava PRG e CHR em arquivos separados (.prg e .chr), sem o cabeçalho iNES — a leitura "raw" do OSCR.
    O firmware já devolve o iNES; o PC só corta (o cabeçalho sintético tem 16 bytes, sem trainer)."""
    d = res.data
    if len(d) < 16 or d[:4] != b"NES\x1a":
        raise CliError("usage", tr("dump.raw_no_header"), EXIT_ERROR)
    prg_n, chr_n = d[4] * 16384, d[5] * 8192
    if len(d) < 16 + prg_n + chr_n:
        raise CliError("protocol", tr("dump.raw_header_big"), EXIT_ERROR)
    prg, chr_ = d[16:16 + prg_n], d[16 + prg_n:16 + prg_n + chr_n]
    base = out_path(args, ".prg", default)
    base = base.with_suffix("")
    files = {"prg": base.with_suffix(".prg")}
    files["prg"].write_bytes(prg)
    lines = [f"{files['prg']}  PRG {len(prg)} bytes  CRC32 {zlib.crc32(prg):08X}"]
    obj = {"files": {"prg": str(files["prg"])}, "prg_bytes": len(prg), "prg_crc32": f"{zlib.crc32(prg):08X}", "crc32": f"{res.crc32:08X}"}
    if chr_:
        files["chr"] = base.with_suffix(".chr")
        files["chr"].write_bytes(chr_)
        obj["files"]["chr"] = str(files["chr"])
        obj["chr_bytes"], obj["chr_crc32"] = len(chr_), f"{zlib.crc32(chr_):08X}"
        lines.append(f"{files['chr']}  CHR {len(chr_)} bytes  CRC32 {zlib.crc32(chr_):08X}")
    else:
        lines.append(tr("dump.no_chr"))
    lines.append(tr("dump.ines_full", crc=f"{res.crc32:08X}"))
    obj.update(extra)
    emit(args, obj, lines + notes)
    return 0



def _twice_mismatch(args, res, res2, ext: str, default: str) -> None:
    """--twice: as duas leituras diferem. Grava as duas (NOME.leitura1 e NOME.leitura2) para comparar e sai com erro."""
    diff, first = diff_summary(res.data, res2.data)
    base = out_path(args, ext, default)
    f1, f2 = base.with_suffix(f".leitura1{base.suffix}"), base.with_suffix(f".leitura2{base.suffix}")
    f1.write_bytes(res.data)
    f2.write_bytes(res2.data)
    raise CliError("mismatch", tr("dump.mismatch", diff=diff, first=f"{first:#x}", crc1=f"{res.crc32:08X}", crc2=f"{res2.crc32:08X}"), EXIT_ERROR,
                   hint=tr("dump.mismatch.hint"),
                   files=[str(f1), str(f2)], diff_bytes=diff, first_diff=first)
