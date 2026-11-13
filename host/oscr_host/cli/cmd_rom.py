# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando rom-write (gravação de ROM em cartucho de flash)."""
from __future__ import annotations

import sys
from pathlib import Path

from .. import protocol as P
from .. import romimage as RI
from . import common
from .common import system_id
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_REFUSED, EXIT_USAGE
from .md_chip import BOARD_LIMIT_BYTES, board_limit_bytes, md_chip_line, md_flash_chip
from .output import emit, progress


def _layout_name(img) -> str:
    if img.layout == RI.SNES_GENERIC:
        return "flash de 8 bits de tipo informado"
    return next((k for k, v in RI.SNES_LAYOUTS.items() if v == img.layout), "?")


def cmd_rom_write(args) -> int:
    """Grava uma ROM em cartucho de flash (WRITE_ROM). Apaga o chip: sempre confirma."""
    if args.system not in ("nes", "famicom", "snes", "md", "gba", "gb", "mock"):
        raise CliError("usage", tr("rom.usage.system"), EXIT_USAGE)
    try:
        data = Path(args.input).read_bytes()
        chip = args.chip
        snes_chip = chip in RI.SNES_CHIPS
        if args.system == "snes" or (args.system == "mock" and snes_chip):       # no simulador (mock) o chip decide
            if chip is None:
                raise CliError("usage", tr("rom.usage.snes_chip"), EXIT_USAGE)
            if not snes_chip:
                raise CliError("usage", tr("rom.usage.not_snes", chip=chip), EXIT_USAGE)
            if chip in RI.SNES_GENERIC_CHIPS:
                if not args.flash_type or not args.flash_mb:
                    raise CliError("usage", tr("rom.usage.generic_needs", chip=chip), EXIT_USAGE)
                img = RI.split_snes_generic(data, args.flash_mb, args.flash_type, args.sector_kb, args.buffer)
            else:
                img = RI.split_snes(data, args.capacity, args.layout)
        elif args.system == "md" or (args.system == "mock" and chip == "md-flash"):
            if chip not in (None, "md-flash"):
                raise CliError("usage", tr("rom.usage.not_md", chip=chip), EXIT_USAGE)
            chip = "md-flash"
            img = RI.split_md(data)
        elif args.system == "gba" or (args.system == "mock" and chip == "gba-flash"):
            if chip not in (None, "gba-flash"):
                raise CliError("usage", tr("rom.usage.not_gba", chip=chip), EXIT_USAGE)
            chip = "gba-flash"
            img = RI.split_gba(data, args.block369)
        elif args.system == "gb" or (args.system == "mock" and chip in RI.GB_CHIPS):
            if chip not in RI.GB_CHIPS:
                raise CliError("usage", tr("rom.usage.gb_chip", chips=", ".join(RI.GB_CHIPS)), EXIT_USAGE)
            img = RI.split_gb(data, chip)
        elif snes_chip or chip in ("md-flash", "gba-flash") or chip in RI.GB_CHIPS:
            raise CliError("usage", tr("rom.usage.chip_other_system", chip=chip), EXIT_USAGE)
        else:
            img = RI.split_image(data, chip or "nesmaker")
            if chip is None:
                chip = RI.infer_chip(img)
                if chip is None:
                    raise CliError("usage", tr("rom.usage.infer"), EXIT_USAGE)
                img = RI.split_image(data, chip)
    except ValueError as e:
        raise CliError("bad_rom", str(e), EXIT_USAGE) from e
    if img.mapper is not None and img.mapper != RI.CHIP_MAPPER[chip] and not args.json:
        print(tr("rom.mapper_warn", file=img.mapper, chip=chip, chipmapper=RI.CHIP_MAPPER[chip]), file=sys.stderr)
    if img.flash_kb:
        what = tr("rom.what_flash", label=RI.CHIP_LABEL[chip], prg=img.prg_kb, flash=img.flash_kb, layout=_layout_name(img), n=len(img.body))
    elif chip in ("md-flash", "gba-flash") or chip in RI.GB_CHIPS:
        what = tr("rom.what_block" if img.block else "rom.what_plain", label=RI.CHIP_LABEL[chip], n=len(img.body), block=img.block)
    else:
        what = tr("rom.what_prgchr", label=RI.CHIP_LABEL[chip], prg=img.prg_kb, chr=img.chr_kb, n=len(img.body))
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", tr("refused.rom"), EXIT_REFUSED,
                           tr("refused.repeat"))
        ans = input(tr("rom.ask", what=what))
        if ans.strip().lower() not in ("s", "sim", "y", "yes", "да", "д", "是", "是的"):
            print(tr("cancelled"))
            return 1
    c, t, info = common.connect(args)
    try:
        if not info.get("write_rom"):
            raise CliError("unsupported_firmware", tr("fw.unsupported_write_rom"), EXIT_ERROR, tr("fw.unsupported.hint"))
        md_chip = md_flash_chip(c, info) if args.system == "md" else None          # mostra o chip que vai ser gravado antes de apagar
        if args.system == "md" and not args.json:
            print(md_chip_line(md_chip))
        limit = board_limit_bytes(md_chip)
        if limit is not None and len(img.body) > limit and not getattr(args, "ignore_cart_limit", False):
            raise CliError("refused", tr("rom.md_limit", size=len(img.body) // (1 << 20) if len(img.body) % (1 << 20) == 0 else f"{len(img.body) / (1 << 20):.2f}",
                                         chip=md_chip["chip"], codes=md_chip.get("codes", ""), limit=BOARD_LIMIT_BYTES >> 20), EXIT_REFUSED, tr("rom.md_limit_hint"))
        crc = c.write_rom(system_id(args.system), img.body, RI.chip_code(chip, img), img.flash_kb or img.prg_kb, img.wire_chr or img.chr_kb, args.block or P.DEFAULT_BLOCK,
                          progress("write-rom", args.progress), args.begin_timeout)
    finally:
        t.close()
    out = {"chip": chip, "prg_kb": img.prg_kb, "chr_kb": img.chr_kb, "bytes": len(img.body), "crc32": f"{crc:08X}"}
    if img.flash_kb:
        out["flash_kb"] = img.flash_kb
        out["layout"] = _layout_name(img)
    if md_chip is not None:
        out["flash_chip"] = md_chip
    lines = [tr("rom.written", what=what, crc=f"{crc:08X}")]
    gba_skip = chip == "gba-flash" and (img.block != 0 or len(img.body) > RI.GBA_VERIFY_MAX_BYTES)   # 369-in-1 em bloco N ou ROM > 64 MB: a leitura comum não alcança
    gb_skip = chip == "gb-cam-second"           # o 2º jogo do GB Camera fica em outra metade do flash; a leitura comum vê o 1º
    gba_skip = gba_skip or gb_skip
    if args.no_verify or args.system == "mock" or gba_skip:      # o simulador não guarda a ROM gravada para ler de volta
        out["verify"] = "skipped"
        lines.append(tr("verify.skipped") + ((" " + tr("rom.skip_gbcam" if gb_skip else "rom.skip_gba")) if gba_skip else ""))
    else:
        c2, t2, _ = common.connect(args)
        try:
            v = RI.verify_written(c2, system_id(args.system), chip, img, progress("verify", args.progress))
        finally:
            t2.close()
        out["verify"] = v.to_dict()
        if not v.ok:
            raise CliError("verify_failed", tr("rom.verify_failed", first=v.first_diff, read=f"{v.read_crc32:08X}", exp=f"{v.expected_crc32:08X}"),
                           EXIT_ERROR, tr("rom.verify_failed.hint"),
                           written=out, first_diff=v.first_diff)
        lines.append(tr("verify.ok", n=v.read_bytes, crc=f"{v.read_crc32:08X}"))
    emit(args, out, lines)
    return 0


