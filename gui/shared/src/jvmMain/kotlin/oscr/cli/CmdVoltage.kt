// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando voltage: consulta ou escolhe a tensão dos slots (seletor 3,3 V/5 V, D138). O 5V dos slots fica sempre ligado (D139). */
internal fun cmdVoltage(io: CliIo, a: Args): Int {
    val action = a.positional.singleOrNull()
    if (action !in setOf("status", "3v3", "5v")) throw CliError("usage", Msg.t("args.volt_action"), EXIT_USAGE)
    val c = connect(io, a, needCart = false)                  // o comando decide a tensão: nunca muda sozinha
    val r = try {
        val st = c.client.voltage(Volt.STATUS)
        if (action == "status") st else setVoltage(io, a.withOpt("voltage", action!!), c, st)
    } finally { c.transport.close() }
    val key = when (r.voltage) { "3v3" -> "volt.state_3v3"; "5v" -> "volt.state_5v"; else -> "volt.state_fixed" }
    emit(io, a, Json.obj("voltage" to r.voltage, "voltage_select" to r.voltageSelect, "chosen" to r.chosen), listOf(Msg.t(key)))
    return EXIT_OK
}
