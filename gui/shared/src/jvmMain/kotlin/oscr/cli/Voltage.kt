// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Alerta bem visível (stderr) antes de passar o slot de 3,3 V para 5 V (D138). */
private fun warn5v(io: CliIo) {
    val bar = "#".repeat(78)
    val lines = listOf(Msg.t("volt.warn_title"), "", Msg.t("volt.warn_1"), "", Msg.t("volt.warn_2"), "", Msg.t("volt.warn_3"))
    val color = io.stderrTty && io.env("NO_COLOR") == null
    fun red(s: String) = if (color) "\u001B[1;31m$s\u001B[0m" else s
    fun yellow(s: String) = if (color) "\u001B[1;33m$s\u001B[0m" else s
    io.err(red(bar)); io.err(red(lines[0])); lines.drop(1).forEach { io.err(if (it.isEmpty()) "" else yellow(it)) }; io.err(red(bar))
}

/** Escolheu 5 V num cartucho marcado como 3,3 V (D138): mostra o alerta de risco e só segue se o usuário digitar 5V ou se `--allow-5v` foi dado. Recusa se não confirmar. */
internal fun confirm5v(io: CliIo, a: Args) {
    warn5v(io)
    if ("allow-5v" in a.flags) { io.err(Msg.t("volt.now_5v")); return }
    if (a.json || !io.interactive) throw CliError("refused", Msg.t("volt.need_flag"), EXIT_REFUSED)
    io.err(Msg.t("volt.prompt"))
    if (io.readLine()?.trim()?.lowercase() != "5v") throw CliError("refused", Msg.t("volt.cancelled"), EXIT_REFUSED)
    io.err(Msg.t("volt.now_5v"))
}

/**
 * Aplica `--voltage` e liga o 5V dos slots (se `turnOn`). Placa com seletor: padrão 5 V; `3v3` liga a 3,3 V (cartucho marcado como 3,3 V);
 * passar de 3,3 V para 5 V pede confirmação. Falha de leitura nunca muda a tensão sozinha. Devolve o estado depois.
 */
internal fun setVoltage(io: CliIo, a: Args, c: Conn, st: PowerState, turnOn: Boolean = true): PowerState {
    val mode = a.opts["voltage"] ?: "auto"
    val sel = st.voltageSelect
    if (mode == "3v3" && !sel) throw CliError("no_selector", Msg.t("volt.no_selector"), EXIT_USAGE)
    if (sel && mode == "5v" && st.on && st.voltage == "3v3") { confirm5v(io, a); return c.client.power(Power.ON_5V) }
    if (sel && mode == "3v3" && (!st.on || st.voltage != "3v3")) return c.client.power(Power.ON_3V3)
    if (sel && mode == "5v" && !st.on) return c.client.power(Power.ON_5V)
    if (turnOn && !st.on) return c.client.power(Power.ON)
    return st
}
