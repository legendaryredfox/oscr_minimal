// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando power: liga, desliga ou consulta o 5V dos slots (D115). */
internal fun cmdPower(io: CliIo, a: Args): Int {
    val action = when (a.positional.singleOrNull()) {
        "on" -> Power.ON; "off" -> Power.OFF; "status" -> Power.STATUS
        else -> throw CliError("usage", Msg.t("args.power_action"), EXIT_USAGE)
    }
    val c = connect(io, a, needCart = false)                  // o comando decide o estado: nunca liga sozinho
    val r = try { c.client.power(action) } finally { c.transport.close() }
    val sw = c.info.powerSwitch
    val lines = mutableListOf(Msg.t(if (r.on) "power.state_on" else "power.state_off"))
    if (!sw) lines += Msg.t("power.no_switch")
    r.railLow?.let { lines += Msg.t(if (it) "power.rail_low" else "power.rail_high") }
    if (sw && action == Power.OFF) lines += Msg.t("power.can_swap") + (if (r.railSensor) "" else Msg.t("power.no_sensor")) + Msg.t("power.then_on")
    emit(io, a, Json.obj("state" to (if (r.on) "on" else "off"), "on" to r.on, "rail_sensor" to r.railSensor,
        "forced_discharge" to r.forcedDischarge, "rail_low" to r.railLow, "power_switch" to sw), lines)
    return EXIT_OK
}
