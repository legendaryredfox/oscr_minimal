# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando power: liga, desliga ou consulta o 5V dos slots (D115)."""
from __future__ import annotations

from .. import protocol as P
from . import common
from .messages import tr
from .errors import EXIT_ERROR, EXIT_OK
from .output import emit

_ACTION = {"on": P.POWER_ON, "off": P.POWER_OFF, "status": P.POWER_STATUS}


def cmd_power(args) -> int:
    c, t, info = common.connect(args, need_cart=False)         # o comando decide o estado: nunca liga sozinho
    try:
        if args.action == "on" and info.get("power_switch"):         # --voltage 3v3|5v: liga na tensão escolhida (seletor, D138); 3,3 V -> 5 V pede confirmação
            r = common.set_voltage(args, c, c.power(P.POWER_STATUS))
        else:
            r = c.power(_ACTION[args.action])
    finally:
        t.close()
    r["power_switch"] = bool(info.get("power_switch"))
    lines = [tr("power.state_on" if r["on"] else "power.state_off")]
    if not r["power_switch"]:
        lines.append(tr("power.no_switch"))
    if r["power_switch"] and r["on"]:
        lines.append(tr({"3v3": "power.volt_3v3", "5v": "power.volt_5v"}.get(r["voltage"], "power.volt_fixed")) if r["voltage_select"] else tr("power.volt_fixed"))
    if r["rail_low"] is not None:
        lines.append(tr("power.rail_low" if r["rail_low"] else "power.rail_high"))
    if r["power_switch"] and args.action == "off":
        lines.append(tr("power.can_swap") + ("" if r["rail_sensor"] else tr("power.no_sensor")) + tr("power.then_on"))
    emit(args, {"state": "on" if r["on"] else "off", **r}, lines)
    return EXIT_OK if r["power_switch"] or args.action != "off" else EXIT_ERROR
