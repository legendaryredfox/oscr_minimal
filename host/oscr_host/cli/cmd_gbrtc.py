# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando gb-rtc: relógio (RTC) do MBC3 do Game Boy (F-17, D192). Sem opção só lê. Com --now, --set, --day, --halt ou --clear-carry grava os 5 registradores
(o que não foi pedido fica como estava) e confere lendo de volta. `-o` guarda o rodapé de 48 bytes que BGB, VBA-M e mGBA põem depois do save."""
from __future__ import annotations

import time
from pathlib import Path

from .. import gbrtc as R
from .. import protocol as P
from . import common
from .errors import CliError, EXIT_ERROR, EXIT_OK, EXIT_USAGE
from .messages import tr
from .output import emit

GB = P.SYSTEMS["gb"][0]
RTC_MAPPER = 7                                                  # GbAcc::kRtc do firmware


def _read(c) -> bytes:
    try:
        return c.dump_rom(GB, 0, None, RTC_MAPPER, 0, 0).data
    except P.DeviceError as e:
        if e.code == 10:                                        # E_SEM_SAVE: o cartucho não é MBC3 com TIMER
            raise CliError("no_rtc", tr("gbrtc.no_rtc"), EXIT_ERROR) from e
        raise


def cmd_gbrtc(args) -> int:
    new_time = None
    if args.now and args.set:
        raise CliError("usage", tr("gbrtc.both"), EXIT_USAGE)
    if args.set:
        try:
            new_time = R.parse_time(args.set)
        except R.RtcError as e:
            raise CliError("usage", tr("gbrtc.bad_time", value=args.set), EXIT_USAGE) from e
    if args.now:
        lt = time.localtime()
        new_time = (lt.tm_hour, lt.tm_min, lt.tm_sec)
    if args.day is not None and not 0 <= args.day <= R.MAX_DAY:
        raise CliError("usage", tr("gbrtc.bad_day", max=R.MAX_DAY), EXIT_USAGE)
    if args.halt and args.run:
        raise CliError("usage", tr("gbrtc.halt_run"), EXIT_USAGE)
    write = new_time is not None or args.day is not None or args.halt or args.run or args.clear_carry
    c, t, info = common.connect(args)
    try:
        before = _read(c)
        raw, verified = before, None
        if write:
            old = R.decode(before)
            h, m, s = new_time or (old["hours"], old["minutes"], old["seconds"])
            halted = True if args.halt else False if args.run else old["halted"]
            raw = R.encode(s, m, h, old["days"] if args.day is None else args.day, halted, old["carry"] and not args.clear_carry)
            c.write_save(GB, raw, 512, None, RTC_MAPPER, 0)
            after = R.decode(_read(c))
            want = R.decode(raw)
            # o relógio anda: com ele rodando aceita até 2 s de diferença (e a virada de dia); parado tem que ser igual
            def secs(d): return ((d["days"] * 24 + d["hours"]) * 60 + d["minutes"]) * 60 + d["seconds"]
            verified = after["halted"] == want["halted"] and after["carry"] == want["carry"] and (secs(after) == secs(want) if want["halted"] else 0 <= secs(after) - secs(want) <= 2)
    finally:
        t.close()
    old_d = R.decode(before)
    lines = [tr("gbrtc.state", value=R.format_value(old_d), state=tr("gbrtc.halted" if old_d["halted"] else "gbrtc.running"), carry=tr("gbrtc.carry_yes" if old_d["carry"] else "gbrtc.carry_no"))]
    if write:
        new_d = R.decode(raw)
        lines.append(tr("gbrtc.written", value=R.format_value(new_d), state=tr("gbrtc.halted" if new_d["halted"] else "gbrtc.running")))
        lines.append(tr("gbrtc.verified" if verified else "gbrtc.not_verified"))
    saved = None
    if args.output:
        out = Path(args.output)
        out.write_bytes(R.footer(raw if write else before, int(time.time())))
        saved = str(out)
        lines.append(tr("gbrtc.saved", path=saved))
    emit(args, {"before": {**old_d, "raw": before.hex()}, "written": {**R.decode(raw), "raw": raw.hex()} if write else None, "verified": verified, "footer": saved}, lines)
    return EXIT_OK if verified in (None, True) else EXIT_ERROR
