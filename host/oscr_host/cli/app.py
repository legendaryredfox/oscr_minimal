# SPDX-License-Identifier: GPL-3.0-or-later
"""Ponto de entrada: interpreta os argumentos, chama o comando e traduz os erros em códigos de saída."""
from __future__ import annotations

import sys

from .. import __version__
from . import messages, ui
from .messages import tr

from .. import protocol as P
from ..client import TimeoutError_
from .errors import CliError, EXIT_ERROR, EXIT_INTERRUPTED, EXIT_NO_CART, fail
from .parser import _Parser, build_parser


def main(argv: list[str] | None = None) -> int:
    _Parser.json_mode = "--json" in (sys.argv[1:] if argv is None else argv)
    raw = sys.argv[1:] if argv is None else argv
    messages.set_lang(messages.detect(raw))
    ui.set_mode(next((raw[i + 1] for i, a in enumerate(raw[:-1]) if a == "--color"), next((a.split("=", 1)[1] for a in raw if a.startswith("--color=")), "auto")))
    if ("--json" not in raw and ui.fancy()) and (not raw or "-h" in raw[:3] or "--help" in raw[:3]):
        print(ui.banner(__version__) + "\n")             # logo só no terminal e só na ajuda
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except CliError as e:
        return fail(args.json, e)
    except P.DeviceError as e:
        kind, code = {3: ("no_cartridge", EXIT_NO_CART), 10: ("no_save", EXIT_ERROR)}.get(e.code, ("device_error", EXIT_ERROR))
        known = f"dev.{e.code}.msg" in messages.CATALOG
        msg = (tr(f"dev.{e.code}.msg") if known else tr("dev.unknown")) + (f" ({e.text})" if e.text else "")
        return fail(args.json, CliError(kind, msg, code, tr(f"dev.{e.code}.hint") if known else None, device_code=e.code))
    except P.ProtocolError as e:
        return fail(args.json, CliError("protocol", str(e)))
    except TimeoutError_ as e:
        return fail(args.json, CliError("timeout", str(e), EXIT_ERROR, tr("err.timeout")))
    except OSError as e:                                  # porta que não abre, arquivo inexistente, disco cheio
        return fail(args.json, CliError("io", str(e)))
    except KeyboardInterrupt:
        return fail(args.json, CliError("interrupted", tr("err.interrupted"), EXIT_INTERRUPTED))
