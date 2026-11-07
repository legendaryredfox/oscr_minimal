# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando rom-write (gravação de ROM em cartucho de flash)."""
from __future__ import annotations

import sys
from pathlib import Path

from .. import protocol as P
from .. import romimage as RI
from . import common
from .common import system_id
from .errors import CliError, EXIT_ERROR, EXIT_REFUSED, EXIT_USAGE
from .md_chip import md_chip_line, md_flash_chip
from .output import emit, progress


def _layout_name(img) -> str:
    if img.layout == RI.SNES_GENERIC:
        return "flash de 8 bits de tipo informado"
    return next((k for k, v in RI.SNES_LAYOUTS.items() if v == img.layout), "?")


def cmd_rom_write(args) -> int:
    """Grava uma ROM em cartucho de flash (WRITE_ROM). Apaga o chip: sempre confirma."""
    if args.system not in ("nes", "famicom", "snes", "md", "gba", "gb", "mock"):
        raise CliError("usage", "rom-write existe para NES e Famicom (flash NES Maker e A29040B), SNES (flash CFI de 2 ou 4 MB), Mega Drive (chips de flash identificados pelo ID: veja docs/melhorias-megadrive.md) GBA (Intel, MX29GL128E, MSP55LV128, 369-in-1) e Game Boy (29F, 39SF, CFI); veja docs/funcoes-oscr.md", EXIT_USAGE)
    try:
        data = Path(args.input).read_bytes()
        chip = args.chip
        snes_chip = chip in RI.SNES_CHIPS
        if args.system == "snes" or (args.system == "mock" and snes_chip):       # no simulador (mock) o chip decide
            if chip is None:
                raise CliError("usage", "no SNES escolha o cartucho com --chip: snes-lorom ou snes-hirom (flash CFI, veja --layout), ou snes-lorom-p0, snes-hirom-p0, "
                               "snes-exlorom-p1, snes-exhirom-p1 (flash de 8 bits, veja --flash-type); a ROM sozinha não diz como o cartucho foi montado", EXIT_USAGE)
            if not snes_chip:
                raise CliError("usage", f"o chip {chip} não é de SNES", EXIT_USAGE)
            if chip in RI.SNES_GENERIC_CHIPS:
                if not args.flash_type or not args.flash_mb:
                    raise CliError("usage", f"o chip {chip} precisa de --flash-type e --flash-mb (o OSCR achava isso no banco do cartão SD; confira a folha de dados do chip)", EXIT_USAGE)
                img = RI.split_snes_generic(data, args.flash_mb, args.flash_type, args.sector_kb, args.buffer)
            else:
                img = RI.split_snes(data, args.capacity, args.layout)
        elif args.system == "md" or (args.system == "mock" and chip == "md-flash"):
            if chip not in (None, "md-flash"):
                raise CliError("usage", f"o chip {chip} não é de Mega Drive (use --chip md-flash, ou nada)", EXIT_USAGE)
            chip = "md-flash"
            img = RI.split_md(data)
        elif args.system == "gba" or (args.system == "mock" and chip == "gba-flash"):
            if chip not in (None, "gba-flash"):
                raise CliError("usage", f"o chip {chip} não é de GBA (use --chip gba-flash, ou nada)", EXIT_USAGE)
            chip = "gba-flash"
            img = RI.split_gba(data, args.block369)
        elif args.system == "gb" or (args.system == "mock" and chip in RI.GB_CHIPS):
            if chip not in RI.GB_CHIPS:
                raise CliError("usage", "no Game Boy escolha o cartucho com --chip: " + ", ".join(RI.GB_CHIPS) + " (a ROM sozinha não diz como o cartucho foi montado)", EXIT_USAGE)
            img = RI.split_gb(data, chip)
        elif snes_chip or chip in ("md-flash", "gba-flash") or chip in RI.GB_CHIPS:
            raise CliError("usage", f"o chip {chip} é só para o sistema dele (snes, md, gba ou gb)", EXIT_USAGE)
        else:
            img = RI.split_image(data, chip or "nesmaker")
            if chip is None:
                chip = RI.infer_chip(img)
                if chip is None:
                    raise CliError("usage", "não deu para saber o chip: use --chip nesmaker (mapper 30) ou --chip a29040b (mapper 0)", EXIT_USAGE)
                img = RI.split_image(data, chip)
    except ValueError as e:
        raise CliError("bad_rom", str(e), EXIT_USAGE) from e
    if img.mapper is not None and img.mapper != RI.CHIP_MAPPER[chip] and not args.json:
        print(f"aviso: o arquivo é do mapper {img.mapper}, mas o chip {chip} é de cartucho de mapper {RI.CHIP_MAPPER[chip]}", file=sys.stderr)
    if img.flash_kb:
        what = f"{RI.CHIP_LABEL[chip]}: ROM {img.prg_kb} KB em flash de {img.flash_kb} KB, {_layout_name(img)} ({len(img.body)} bytes enviados)"
    elif chip in ("md-flash", "gba-flash") or chip in RI.GB_CHIPS:
        what = f"{RI.CHIP_LABEL[chip]}: ROM {len(img.body)} bytes" + (f", bloco {img.block}" if img.block else "")
    else:
        what = f"{RI.CHIP_LABEL[chip]}: PRG {img.prg_kb} KB, CHR {img.chr_kb} KB ({len(img.body)} bytes)"
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", "recusado: gravar a ROM APAGA o chip de flash do cartucho. Em modo não interativo confirme com --yes.", EXIT_REFUSED,
                           "repita o comando com --yes")
        ans = input(f"Gravar {what}? Isso APAGA a ROM atual do cartucho. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes"):
            print("cancelado")
            return 1
    c, t, info = common.connect(args)
    try:
        if not info.get("write_rom"):
            raise CliError("unsupported_firmware", "este firmware não aceita WRITE_ROM", EXIT_ERROR, "atualize o firmware (docs/funcoes-oscr.md)")
        md_chip = md_flash_chip(c, info) if args.system == "md" else None          # mostra o chip que vai ser gravado antes de apagar
        if args.system == "md" and not args.json:
            print(md_chip_line(md_chip))
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
    lines = [f"ROM gravada: {what}  CRC32 {crc:08X}"]
    gba_skip = chip == "gba-flash" and (img.block != 0 or len(img.body) > RI.GBA_VERIFY_MAX_BYTES)   # 369-in-1 em bloco N ou ROM > 64 MB: a leitura comum não alcança
    gb_skip = chip == "gb-cam-second"           # o 2º jogo do GB Camera fica em outra metade do flash; a leitura comum vê o 1º
    gba_skip = gba_skip or gb_skip
    if args.no_verify or args.system == "mock" or gba_skip:      # o simulador não guarda a ROM gravada para ler de volta
        out["verify"] = "skipped"
        lines.append("conferência depois de gravar: pulada" + ((" (o 2º jogo do GB Camera não é visto pela leitura comum)" if gb_skip else " (a leitura do GBA não alcança o bloco N do 369-in-1, nem mais de 64 MB)") if gba_skip else ""))
    else:
        c2, t2, _ = common.connect(args)
        try:
            v = RI.verify_written(c2, system_id(args.system), chip, img, progress("verify", args.progress))
        finally:
            t2.close()
        out["verify"] = v.to_dict()
        if not v.ok:
            raise CliError("verify_failed", f"a ROM lida de volta NÃO confere com a gravada (primeiro byte diferente no offset {v.first_diff}; lido {v.read_crc32:08X}, esperado {v.expected_crc32:08X})",
                           EXIT_ERROR, "limpe os contatos, confira se o chip é o escolhido e grave de novo; o chip pode estar apagado ou pela metade",
                           written=out, first_diff=v.first_diff)
        lines.append(f"conferência depois de gravar: OK (leu {v.read_bytes} bytes, CRC32 {v.read_crc32:08X})")
    emit(args, out, lines)
    return 0


