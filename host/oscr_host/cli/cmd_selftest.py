# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando selftest: autoteste da placa sem cartucho (curtos entre os pinos, pull-up do D7, Si5351; P-12). Usa o SelfTest do OSCR no firmware."""
from __future__ import annotations

import sys

from . import common
from .errors import CliError, EXIT_ERROR, EXIT_OK
from .messages import tr
from .output import emit


def selftest_lines(res: dict) -> list[str]:
    """Texto de cada achado, no idioma escolhido."""
    keys = {"gnd": "selftest.gnd", "pair": "selftest.pair", "pullup": "selftest.pullup", "clockgen": "selftest.clockgen"}
    lines = [tr(keys.get(f["kind"], "selftest.unknown"), pin=(f["pins"] or [""])[0], a=(f["pins"] or [""])[0], b=(f["pins"] + [""])[1], kind=f["kind"])
             for f in res["findings"]]
    if res["truncated"]:
        lines.append(tr("selftest.truncated"))
    return lines


def cmd_selftest(args) -> int:
    c, t, info = common.connect(args, need_cart=False)         # não mexe na tensão: o teste roda sem cartucho
    try:
        if not info.get("selftest"):
            raise CliError("no_selftest", tr("selftest.unsupported"), EXIT_ERROR)
        if not getattr(args, "json", False):
            print(tr("selftest.start"), file=sys.stderr, flush=True)
        res = c.selftest()
    finally:
        t.close()
    lines = selftest_lines(res)
    lines.append(tr("selftest.ok") if res["ok"] else tr("selftest.found", n=len(res["findings"])))
    emit(args, {"ok": res["ok"], "truncated": res["truncated"], "findings": res["findings"]}, lines)
    return EXIT_OK if res["ok"] else EXIT_ERROR
