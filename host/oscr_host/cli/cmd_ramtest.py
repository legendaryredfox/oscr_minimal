# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando ram-test: o "Test RAM" do SNES do OSCR (F-10, D178)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

from .. import protocol as P
from .. import romimage as RI
from . import common
from .common import system_id
from .errors import CliError, EXIT_ERROR, EXIT_REFUSED, EXIT_USAGE
from .messages import tr
from .output import emit, progress

PATTERNS = (0x0F, 0xF0)        # as duas passadas do OSCR (`eraseSRAM(0x0F)` e `eraseSRAM(0xF0)`)


def cmd_ram_test(args) -> int:
    """Teste da SRAM do SNES: lê o save (e o guarda), sobrescreve a SRAM inteira com 0x0F e 0xF0, grava o save de volta e confere lendo.

    No OSCR o save ia para um arquivo do cartão SD no firmware; aqui o PC faz o backup e a restauração (a SRAM tem até 128 KB e não cabe na RAM do Arduino),
    e o firmware só preenche (`ERASE` do SNES). Se qualquer passo falha depois do backup, o PC ainda tenta restaurar o save."""
    if args.system != "snes":
        raise CliError("usage", tr("ramtest.only_snes"), EXIT_USAGE)
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", tr("refused.ramtest"), EXIT_REFUSED, tr("refused.repeat"))
        ans = input(tr("ramtest.ask"))
        if ans.strip().lower() not in ("s", "sim", "y", "yes", "да", "д", "是", "是的"):
            print(tr("cancelled"))
            return 1
    sid = system_id(args.system)
    c, t, info = common.connect(args)
    try:
        if not info.get("flash_prog"):                    # o ERASE do SNES existe junto com o do programador de flash (INFO bit 4)
            raise CliError("unsupported_firmware", tr("fw.unsupported_erase"), EXIT_ERROR, tr("fw.unsupported.hint"))
        saved = c.read_save(sid, args.block, progress("backup", args.progress), 0, 0)
        bdir = Path(args.backup_dir).expanduser()
        bdir.mkdir(parents=True, exist_ok=True)
        bpath = bdir / f"snes_ramtest_{time.strftime('%Y%m%d-%H%M%S')}.sav"
        bpath.write_bytes(saved.data)
        if not args.json:
            print(tr("save.backup", path=bpath, crc=f"{saved.crc32:08X}"))
        failure = None
        try:
            for p in PATTERNS:
                c.erase(sid, p, 0, 0, args.begin_timeout)
        except Exception as e:                            # a SRAM pode ter ficado pela metade: restaura de qualquer jeito, depois repassa o erro
            failure = e
        c.write_save(sid, saved.data, args.block or P.DEFAULT_BLOCK, progress("restore", args.progress), 0, 0)
        v = RI.verify_save_written(c, sid, saved.data, progress("verify", args.progress), 0, 0)
    finally:
        t.close()
    if failure is not None:
        raise failure
    out = {"ok": v.ok, "bytes": len(saved.data), "crc32": f"{saved.crc32:08X}", "patterns": list(PATTERNS), "backup": str(bpath), "verify": v.to_dict()}
    if not v.ok:
        raise CliError("verify_failed", tr("ramtest.verify_failed", first=v.first_diff, read=f"{v.read_crc32:08X}", exp=f"{v.expected_crc32:08X}"),
                       EXIT_ERROR, tr("ramtest.verify_failed.hint"), written=out, first_diff=v.first_diff)
    emit(args, out, [tr("ramtest.ok", n=len(saved.data), crc=f"{saved.crc32:08X}")])
    return 0
