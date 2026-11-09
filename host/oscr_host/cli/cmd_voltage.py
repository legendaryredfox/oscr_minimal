# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando voltage: consulta ou escolhe a tensão dos slots (seletor 3,3 V/5 V, D138). O 5V dos slots fica sempre ligado (D139)."""
from __future__ import annotations

from .. import protocol as P
from . import common
from .messages import tr
from .output import emit
from .errors import EXIT_OK


def cmd_voltage(args) -> int:
    c, t, info = common.connect(args, need_cart=False)         # o comando decide a tensão: nunca muda sozinho
    try:
        st = c.voltage(P.VOLT_STATUS)
        if args.action != "status":
            args.voltage = args.action
            st = common.set_voltage(args, c, st)
    finally:
        t.close()
    key = {"3v3": "volt.state_3v3", "5v": "volt.state_5v"}.get(st["voltage"], "volt.state_fixed")
    emit(args, {"voltage": st["voltage"], "voltage_select": st["voltage_select"], "chosen": st["chosen"]}, [tr(key)])
    return EXIT_OK
