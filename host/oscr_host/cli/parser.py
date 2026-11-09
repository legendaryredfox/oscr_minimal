# SPDX-License-Identifier: GPL-3.0-or-later
"""Definição dos argumentos (argparse)."""
from __future__ import annotations

import argparse
import json
import sys

from .. import protocol as P
from .. import romimage as RI
from .. import __version__
from . import messages
from .cmd_db import cmd_identify, cmd_search
from .cmd_detect import cmd_detect
from .cmd_dump import cmd_dump
from .cmd_firmware import DEFAULT_ENV, cmd_firmware_flash
from .cmd_flash import cmd_flash_blank, cmd_flash_erase, cmd_flash_id, cmd_flash_read, cmd_flash_write
from .cmd_info import cmd_errors, cmd_info, cmd_ports, cmd_systems
from .cmd_voltage import cmd_voltage
from .cmd_rom import cmd_rom_write
from .cmd_save import cmd_save_read, cmd_save_write
from .errors import EXIT_USAGE
from .messages import tr


def H(slug: str, **kw) -> str:
    """Texto de ajuda no idioma atual (catálogo `help.<slug>`, D133)."""
    return tr("help." + slug, **kw)


def _lang_arg(v: str) -> str:
    n = messages.normalize(v)
    if n is None:
        raise argparse.ArgumentTypeError(tr("args.unknown_lang_cli", tag=v, langs=", ".join(messages.LANGS)))
    return n


class _Parser(argparse.ArgumentParser):
    """Erro de uso vira saída 64 (e JSON com --json), não o 2 do argparse, que é 'nenhum cartucho'."""

    json_mode = False

    def error(self, message):
        if _Parser.json_mode:
            print(json.dumps({"ok": False, "error": {"kind": "usage", "message": message}}, ensure_ascii=False))
        else:
            self.print_usage(sys.stderr)
            print(f"{self.prog}: {tr('err.prefix')}: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def _add_common(p: argparse.ArgumentParser, top: bool) -> None:
    """Opções globais. Valem antes e depois do subcomando (nos subcomandos o padrão é SUPPRESS para não sobrescrever)."""
    d = (lambda v: v) if top else (lambda v: argparse.SUPPRESS)
    p.add_argument("-p", "--port", default=d(None), help=H("port"))
    p.add_argument("-b", "--baud", type=int, default=d(None), help=H("baud"))
    p.add_argument("--db", action="append", default=d(None), metavar="PATH",
                   help=H("db"))
    p.add_argument("--no-builtin-db", action="store_true", default=d(False),
                   help=H("no_builtin_db"))
    p.add_argument("--simulate", action="store_true", default=d(False), help=H("simulate"))
    p.add_argument("--json", action="store_true", default=d(False),
                   help=H("json"))
    p.add_argument("--color", choices=("auto", "always", "never"), default=d("auto"),
                   help=H("color"))
    p.add_argument("--voltage", choices=("auto", "3v3", "5v"), default=d("auto"), help=H("voltage"))
    p.add_argument("--allow-5v", action="store_true", default=d(False), help=H("allow_5v"))
    p.add_argument("--lang", default=d(None), type=_lang_arg, metavar="LANG",
                   help=H("lang"))
    p.add_argument("--progress", choices=("auto", "none", "jsonl"), default=d("auto"),
                   help=H("progress"))


def _epilog() -> str:
    return (H("epilog") + """
  dumper --json detect -s snes
  dumper dump -s snes -o jogo --json --progress jsonl
  dumper save-write -s snes -i jogo.sav --yes --json
  dumper voltage 3v3          """ + H("epilog_volt") + """
  dumper --simulate --json systems
""" + H("epilog_guide"))


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(prog="dumper", description=H("description"), epilog=_epilog(),
                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=H("version", v=__version__, p=P.PROTO_VERSION))
    _add_common(ap, True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, system=True, out=False, inp=False):
        sp = sub.add_parser(name, help=help_, description=help_, epilog=_epilog(), formatter_class=argparse.RawDescriptionHelpFormatter)
        sp.set_defaults(fn=fn)
        _add_common(sp, False)
        if system:
            sp.add_argument("-s", "--system", default="mock", choices=sorted(P.SYSTEMS), help=H("system"))
        if out:
            sp.add_argument("-o", "--output", help=H("output"))
        if inp:
            sp.add_argument("-i", "--input", required=True, help=H("input"))
        if out or inp:
            sp.add_argument("--block", type=int, default=0, help=H("block"))
        return sp

    add("ports", cmd_ports, H("cmd_ports"), system=False)
    add("systems", cmd_systems, H("cmd_systems"), system=False)
    add("errors", cmd_errors, H("cmd_errors"), system=False)
    add("info", cmd_info, H("cmd_info"), system=False)
    vlp = add("voltage", cmd_voltage, H("cmd_voltage"), system=False)
    vlp.add_argument("action", choices=("status", "3v3", "5v"), help=H("volt_action"))
    fw = add("firmware-flash", cmd_firmware_flash, H("cmd_firmware_flash"), system=False)
    fw.add_argument("--hex", help=H("fw_hex"))
    fw.add_argument("--env", default=DEFAULT_ENV, help=H("fw_env", envs=H("fw_env_list")))
    fw.add_argument("--avrdude", help=H("fw_avrdude"))
    fw.add_argument("--yes", action="store_true", help=H("yes_write"))
    fw.add_argument("--no-verify", action="store_true", help=H("fw_no_verify"))
    fw.add_argument("--wait", type=float, default=12.0, help=H("fw_wait"))
    fw.add_argument("--dry-run", action="store_true", help=H("fw_dry_run"))
    dtp = add("detect", cmd_detect, H("cmd_detect"))
    dtp.add_argument("--flash-id", action="store_true", help=H("detect_flash_id"))
    dtp.add_argument("--mapper", type=int, default=0, help=H("detect_mapper"))
    ip = add("identify", cmd_identify, H("cmd_identify"))
    ip.add_argument("files", nargs="+", help=H("identify_files"))
    sp_ = add("search", cmd_search, H("cmd_search"), system=False)
    sp_.add_argument("query", help=H("search_query"))
    sp_.add_argument("--limit", type=int, default=20, help=H("search_limit"))
    dp = add("dump", cmd_dump, H("cmd_dump"), out=True)
    dp.add_argument("--mapper", type=int, default=0, help=H("dump_mapper"))
    dp.add_argument("--prg", type=int, default=0, help=H("dump_prg"))
    dp.add_argument("--chr", type=int, default=0, help=H("dump_chr"))
    dp.add_argument("--raw", action="store_true", help=H("dump_raw"))
    dp.add_argument("--twice", action="store_true", help=H("dump_twice"))
    dp.add_argument("--game", help=H("dump_game"))
    for sp in (add("save-read", cmd_save_read, H("cmd_save_read"), out=True), add("save-write", cmd_save_write, H("cmd_save_write"), inp=True)):
        sp.add_argument("--mapper", type=int, default=0, help=H("save_mapper"))
        sp.add_argument("--ram", type=int, default=0, help=H("save_ram"))
        if sp.prog.endswith("save-write"):
            sp.add_argument("--yes", action="store_true", help=H("yes_write"))
            sp.add_argument("--no-backup", action="store_true", help=H("save_no_backup"))
            sp.add_argument("--no-verify", action="store_true", help=H("save_no_verify"))
            sp.add_argument("--backup-dir", default="~/oscr_backups", help=H("save_backup_dir"))
    rp = add("rom-write", cmd_rom_write, H("cmd_rom_write"), inp=True)
    rp.set_defaults(system="nes")
    rp.add_argument("--chip", choices=sorted(RI.CHIPS), help=H("rom_chip"))
    rp.add_argument("--capacity", type=int, choices=RI.SNES_CAPACITIES_KB, help=H("rom_capacity"))
    rp.add_argument("--layout", choices=list(RI.SNES_LAYOUTS), default="1x",
                    help=H("rom_layout"))
    rp.add_argument("--block369", type=int, default=0, help=H("rom_block369"))
    rp.add_argument("--flash-type", choices=list(RI.FLASH_TYPES), help=H("rom_flash_type"))
    rp.add_argument("--flash-mb", type=int, help=H("rom_flash_mb"))
    rp.add_argument("--sector-kb", type=int, help=H("rom_sector_kb"))
    rp.add_argument("--buffer", type=int, help=H("rom_buffer"))
    rp.add_argument("--yes", action="store_true", help=H("yes_write"))
    rp.add_argument("--no-verify", action="store_true", help=H("rom_no_verify"))
    rp.add_argument("--begin-timeout", type=float, default=90.0, help=H("begin_timeout_rom"))
    # programador de flash genérico (sistema 7)
    def flash_cmd(name, fn, help_, out=False, inp=False, write=False):
        sp = add(name, fn, help_, system=False, out=out, inp=inp)
        sp.add_argument("-s", "--system", default="flash", choices=["flash", "mock"], help=H("fp_system"))
        sp.add_argument("--bus", required=True, choices=list(RI.FLASHPROG_BUS), help=H("fp_bus"))
        sp.add_argument("--flash-kb", type=int, help=H("fp_flash_kb"))
        sp.add_argument("--flash-type", choices=list(RI.FLASH_TYPES), help=H("fp_flash_type"))
        sp.add_argument("--sector-kb", type=int, help=H("fp_sector_kb"))
        sp.add_argument("--buffer", type=int, help=H("fp_buffer"))
        if write or fn is cmd_flash_erase:
            sp.add_argument("--yes", action="store_true", help=H("fp_yes"))
            sp.add_argument("--begin-timeout", type=float, default=90.0, help=H("begin_timeout_erase"))
        if write:
            sp.add_argument("--no-verify", action="store_true", help=H("fp_no_verify"))
        return sp

    flash_cmd("flash-id", cmd_flash_id, H("cmd_flash_id"))
    flash_cmd("flash-read", cmd_flash_read, H("cmd_flash_read"), out=True)
    flash_cmd("flash-blank", cmd_flash_blank, H("cmd_flash_blank"))
    flash_cmd("flash-erase", cmd_flash_erase, H("cmd_flash_erase"))
    flash_cmd("flash-write", cmd_flash_write, H("cmd_flash_write"), inp=True, write=True)
    return ap

