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
 * Aplica `--voltage`. A placa sobe em 3,3 V (estado seguro: abrir a porta reinicia o Mega); o padrão é 5 V; `3v3` usa 3,3 V (cartucho marcado como 3,3 V);
 * passar de 3,3 V (escolhido) para 5 V pede confirmação. Falha de leitura nunca muda a tensão sozinha. Devolve o estado depois.
 */
internal fun setVoltage(io: CliIo, a: Args, c: Conn, st: VoltState): VoltState {
    val mode = a.opts["voltage"] ?: "auto"
    if (mode == "3v3" && !st.voltageSelect) throw CliError("no_selector", Msg.t("volt.no_selector"), EXIT_USAGE)
    if (!st.voltageSelect) return st
    if (mode == "3v3") return if (st.voltage == "3v3" && st.chosen) st else c.client.voltage(Volt.V3V3)
    if (st.voltage == "3v3" && (mode == "5v" || !st.chosen)) {            // padrão: 5 V. Só a escolha de 3,3 V do usuário pede confirmação
        if (st.chosen) confirm5v(io, a)
        return c.client.voltage(Volt.V5V)
    }
    return st
}
