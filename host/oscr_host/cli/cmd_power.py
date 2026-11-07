# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando power: liga, desliga ou consulta o 5V dos slots (D115)."""
from __future__ import annotations

from .. import protocol as P
from . import common
from .errors import EXIT_ERROR, EXIT_OK
from .output import emit

_ACTION = {"on": P.POWER_ON, "off": P.POWER_OFF, "status": P.POWER_STATUS}


def cmd_power(args) -> int:
    c, t, info = common.connect(args, need_cart=False)         # o comando decide o estado: nunca liga sozinho
    try:
        r = c.power(_ACTION[args.action])
    finally:
        t.close()
    r["power_switch"] = bool(info.get("power_switch"))
    state = "ligado" if r["on"] else "desligado"
    lines = [f"5V dos slots: {state}"]
    if not r["power_switch"]:
        lines.append("esta placa/firmware não tem a chave de 5V: o 5V fica sempre ligado")
    if r["switch"] is not None:
        lines.append("chave física: " + ("fechada (ligado permitido)" if r["switch"] else "ABERTA (o 5V fica desligado; feche a chave para ligar)"))
    if r["rail_low"] is not None:
        lines.append("sensor do rail: " + ("baixo (seguro trocar o cartucho)" if r["rail_low"] else "alto (ainda há tensão: não troque o cartucho)"))
    if r["power_switch"] and args.action == "off":
        lines.append("pode trocar o cartucho" + ("" if r["rail_sensor"] else " (sem sensor de tensão: o firmware já esperou a descarga; confira com o multímetro)")
                     + "; depois rode `dumper power on`")
    emit(args, {"state": "on" if r["on"] else "off", **r}, lines)
    return EXIT_OK if r["power_switch"] or args.action != "off" else EXIT_ERROR
