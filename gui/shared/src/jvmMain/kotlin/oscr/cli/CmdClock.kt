// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando clock-cal: relógio do Si5351 (F-3, P-03). Mostra o fator de correção, liga as saídas de teste para medir com frequencímetro e grava o fator na EEPROM
 *  do firmware (vale já e nos próximos boots). Sem opção só consulta. A calibração em si é da bancada. Igual a host/oscr_host/cli/cmd_clock.py. */
internal fun cmdClock(io: CliIo, a: Args): Int {
    fun num(name: String): Double? = a.opts[name]?.let { it.toDoubleOrNull() ?: throw CliError("usage", Msg.t("args.bad_value", "name" to name, "value" to it), EXIT_USAGE) }
    val factorArg = a.opts["factor"]?.let { it.toIntOrNull() ?: throw CliError("usage", Msg.t("args.bad_value", "name" to "factor", "value" to it), EXIT_USAGE) }
    val measured = num("measured")
    val target = num("target") ?: 4_000_000.0
    val test = a.opts["test"]?.also { if (it != "on" && it != "off") throw CliError("usage", Msg.t("args.bad_value", "name" to "test", "value" to it), EXIT_USAGE) }
    if (factorArg != null && measured != null) throw CliError("usage", Msg.t("clock.both"), EXIT_USAGE)
    if (factorArg != null && Math.abs(factorArg) > Clock.MAX_PPB) throw CliError("usage", Msg.t("clock.range", "max" to Clock.MAX_PPB), EXIT_USAGE)
    if (measured != null && measured <= 0) throw CliError("usage", Msg.t("clock.measured_positive"), EXIT_USAGE)
    val c = connect(io, a, needCart = false)                  // não mexe na tensão: só fala com o Si5351
    var applied = false
    val st = try {
        fun call(action: Int, ppb: Int = 0): ClockState = try { c.client.clock(action, ppb) } catch (e: DeviceError) {
            when (e.code) {
                1 -> throw CliError("no_clock", Msg.t("clock.unsupported"), EXIT_ERROR)
                7 -> throw CliError("no_clockgen", Msg.t("clock.no_module"), EXIT_ERROR)
                else -> throw e
            }
        }
        var s = call(Clock.STATUS)
        var factor = factorArg
        if (measured != null) {
            val f = clockFactorFromMeasure(measured, target, s.ppb)
            if (Math.abs(f) > Clock.MAX_PPB) throw CliError("usage", Msg.t("clock.range", "max" to Clock.MAX_PPB), EXIT_USAGE, Msg.t("clock.range_hint"))
            factor = f.toInt()
        }
        if (factor != null) { s = call(Clock.SET, factor); applied = true }
        if (test != null) s = call(if (test == "on") Clock.TEST_ON else Clock.TEST_OFF)
        s
    } finally { c.transport.close() }
    val targets = Clock.TARGETS.map { Triple(it.output, it.hz, Msg.t(it.whereKey)) }
    val lines = mutableListOf(Msg.t(if (st.present) "clock.state" else "clock.state_absent", "ppb" to st.ppb, "saved" to Msg.t(if (st.stored) "clock.saved" else "clock.not_saved")))
    if (applied) lines += Msg.t("clock.applied", "ppb" to st.ppb)
    lines += Msg.t(if (st.test) "clock.test_on" else "clock.test_off")
    lines += Msg.t("clock.targets")
    targets.forEach { lines += Msg.t("clock.target", "hz" to it.second, "output" to it.first, "where" to it.third) }
    if (!applied && measured == null) lines += Msg.t("clock.how")
    emit(io, a, Json.obj("present" to st.present, "stored" to st.stored, "factor_ppb" to st.ppb, "test" to st.test, "applied" to applied,
        "targets" to targets.map { Json.obj("output" to it.first, "hz" to it.second, "where" to it.third) }), lines)
    return EXIT_OK
}
