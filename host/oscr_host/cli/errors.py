# SPDX-License-Identifier: GPL-3.0-or-later
"""Códigos de saída e o erro estruturado da CLI."""
from __future__ import annotations

import json
import sys

from . import ui


# Códigos de saída (estáveis; docs/cli.md)
EXIT_OK, EXIT_ERROR, EXIT_NO_CART, EXIT_NO_DEVICE, EXIT_REFUSED, EXIT_USAGE, EXIT_INTERRUPTED = 0, 1, 2, 3, 4, 64, 130

CLI_EXIT_CODES = {
    EXIT_OK: "sucesso", EXIT_ERROR: "erro do dispositivo, do protocolo, de timeout ou de arquivo",
    EXIT_NO_CART: "nenhum cartucho (detect) ou o dispositivo respondeu 'nenhum cartucho'",
    EXIT_NO_DEVICE: "porta serial não encontrada ou dispositivo sem resposta",
    EXIT_REFUSED: "operação recusada: falta --yes fora de um terminal", EXIT_USAGE: "argumentos inválidos",
    EXIT_INTERRUPTED: "interrompido (Ctrl+C)",
}


class CliError(Exception):
    """Erro com tipo estável (`kind`) e código de saída; vira JSON com --json."""

    def __init__(self, kind: str, message: str, exit_code: int = EXIT_ERROR, hint: str | None = None, **extra):
        super().__init__(message)
        self.kind, self.message, self.exit_code, self.hint, self.extra = kind, message, exit_code, hint, extra



def fail(args_json: bool, e: CliError) -> int:
    if args_json:
        err = {"kind": e.kind, "message": e.message, **e.extra}
        if e.hint:
            err["hint"] = e.hint
        print(json.dumps({"ok": False, "error": err}, ensure_ascii=False))
    else:
        if ui.color_on(sys.stderr):
            print(ui.error_line(e.message, e.hint, sys.stderr), file=sys.stderr)
        else:
            print(f"erro: {e.message}" + (f". Dica: {e.hint}" if e.hint else ""), file=sys.stderr)
    return e.exit_code
