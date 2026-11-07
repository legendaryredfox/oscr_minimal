// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando power: liga, desliga ou consulta o 5V dos slots (D115). */
internal fun cmdPower(io: CliIo, a: Args): Int {
    val action = when (a.positional.singleOrNull()) {
        "on" -> Power.ON; "off" -> Power.OFF; "status" -> Power.STATUS
        else -> throw CliError("usage", "power needs one action: on, off or status", EXIT_USAGE)
    }
    val c = connect(io, a, needCart = false)                  // o comando decide o estado: nunca liga sozinho
    val r = try { c.client.power(action) } finally { c.transport.close() }
    val sw = c.info.powerSwitch
    val lines = mutableListOf("slots 5V: ${if (r.on) "on" else "off"}")
    if (!sw) lines += "this board/firmware has no 5V switch: the 5V is always on"
    r.railLow?.let { lines += "rail sensor: " + (if (it) "low (safe to swap the cartridge)" else "high (voltage still present: do not swap the cartridge)") }
    if (sw && action == Power.OFF) lines += "you can swap the cartridge" + (if (r.railSensor) "" else " (no voltage sensor: the firmware already waited for the discharge; check with a multimeter)") + "; then run `dumper power on`"
    emit(io, a, Json.obj("state" to (if (r.on) "on" else "off"), "on" to r.on, "rail_sensor" to r.railSensor,
        "forced_discharge" to r.forcedDischarge, "rail_low" to r.railLow, "power_switch" to sw), lines)
    return EXIT_OK
}
