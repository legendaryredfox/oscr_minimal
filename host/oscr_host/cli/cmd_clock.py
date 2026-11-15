# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando clock-cal: relógio do Si5351 (F-3, P-03). Mostra o fator de correção, liga as saídas de teste para medir com frequencímetro e grava o fator
na EEPROM do firmware (vale já e nos próximos boots). Sem opção só consulta: nada muda sem frequencímetro. A calibração em si é da bancada."""
from __future__ import annotations

from .. import protocol as P
from . import common
from .errors import CliError, EXIT_ERROR, EXIT_OK, EXIT_USAGE
from .messages import tr
from .output import emit

_WHERE = {"CLK0": "clock.where_ext", "CLK2": "clock.where_cic", "CLK1": "clock.where_cpu"}


def _targets() -> list[dict]:
    return [{"output": t["output"], "hz": t["hz"], "where": tr(_WHERE[t["output"]])} for t in P.CLOCK_TARGETS]


def _call(c, action: int, ppb: int = 0) -> dict:
    try:
        return c.clock(action, ppb)
    except P.DeviceError as e:
        if e.code == 1:                                        # E_COMANDO: firmware sem o comando
            raise CliError("no_clock", tr("clock.unsupported"), EXIT_ERROR) from e
        if e.code == 7:                                        # E_CARTUCHO_IO: o Si5351 não respondeu
            raise CliError("no_clockgen", tr("clock.no_module"), EXIT_ERROR) from e
        raise


def cmd_clock(args) -> int:
    factor, measured, test = getattr(args, "factor", None), getattr(args, "measured", None), getattr(args, "test", None)
    if factor is not None and measured is not None:
        raise CliError("usage", tr("clock.both"), EXIT_USAGE)
    if factor is not None and abs(factor) > P.CLOCK_MAX_PPB:
        raise CliError("usage", tr("clock.range", max=P.CLOCK_MAX_PPB), EXIT_USAGE)
    if measured is not None and measured <= 0:
        raise CliError("usage", tr("clock.measured_positive"), EXIT_USAGE)
    c, t, info = common.connect(args, need_cart=False)         # não mexe na tensão: só fala com o Si5351
    applied = False
    try:
        st = _call(c, P.CLOCK_STATUS)
        if measured is not None:
            factor = P.clock_factor_from_measure(measured, args.target, st["ppb"])
            if abs(factor) > P.CLOCK_MAX_PPB:
                raise CliError("usage", tr("clock.range", max=P.CLOCK_MAX_PPB), EXIT_USAGE, tr("clock.range_hint"))
        if factor is not None:
            st = _call(c, P.CLOCK_SET, factor)
            applied = True
        if test:
            st = _call(c, P.CLOCK_TEST_ON if test == "on" else P.CLOCK_TEST_OFF)
    finally:
        t.close()
    lines = [tr("clock.state" if st["present"] else "clock.state_absent", ppb=st["ppb"], saved=tr("clock.saved" if st["stored"] else "clock.not_saved"))]
    if applied:
        lines.append(tr("clock.applied", ppb=st["ppb"]))
    lines.append(tr("clock.test_on" if st["test"] else "clock.test_off"))
    lines.append(tr("clock.targets"))
    lines += [tr("clock.target", hz=x["hz"], output=x["output"], where=x["where"]) for x in _targets()]
    if not applied and measured is None:
        lines.append(tr("clock.how"))
    emit(args, {"present": st["present"], "stored": st["stored"], "factor_ppb": st["ppb"], "test": st["test"], "applied": applied, "targets": _targets()}, lines)
    return EXIT_OK
