// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Conexão com o dispositivo (porta serial ou simulador) e leitura do sistema escolhido. */
internal class Conn(val client: OscrClient, val transport: Transport, val info: DeviceInfo)

/**
 * Abre a porta (ou o simulador), faz INFO e, antes de um comando de cartucho, ajusta a tensão do seletor 3,3 V/5 V (D138; placa sem seletor: só recusa `--voltage 3v3`).
 * O 5V dos slots fica sempre ligado (D139). `needCart = false` (info, voltage) nunca mexe na tensão.
 */
internal fun connect(io: CliIo, a: Args, needCart: Boolean = true): Conn {
    val c = open(io, a)
    if (needCart) {
        try {
            setVoltage(io, a, c, c.client.voltage(Volt.STATUS))
        } catch (e: Throwable) { c.transport.close(); throw e }
    }
    return c
}

private fun open(io: CliIo, a: Args): Conn {
    if ("simulate" in a.flags) {
        val t = SimDevice(voltSelect = io.simVolt, cartNeeds5v = io.simCart5v, selftestReport = if (io.simSelftest) listOf(Triple(1, 30, 0), Triple(2, 22, 57)) else emptyList())
        val c = OscrClient(t, 500, 5000)
        return Conn(c, t, c.info())
    }
    val port = a.opts["port"] ?: io.listPorts().firstOrNull { p -> listOf("ttyUSB", "ttyACM", "cu.usb", "COM").any { it in p } }
        ?: throw CliError("no_port", Msg.t("err.no_port"), EXIT_NO_DEVICE, Msg.t("err.no_port.hint"))
    val bauds = a.opts["baud"]?.let { listOf(a.int("baud")) } ?: listOf(1_000_000, 115_200)
    var last: Exception? = null
    for (b in bauds) {
        val t = io.openPort(port, b)
        val c = OscrClient(t, 500, 10_000)
        try { return Conn(c, t, c.info()) } catch (e: TimeoutError) { last = e; t.close() }
    }
    throw CliError("no_response", Msg.t("err.no_response", "port" to port, "bauds" to bauds.joinToString(", "), "error" to last?.message), EXIT_NO_DEVICE, Msg.t("err.no_response.hint"))
}

internal fun system(a: Args): CartSystem {
    val n = (a.opts["system"] ?: "mock").lowercase()
    return CartSystem.entries.firstOrNull { it.name.lowercase() == n }
        ?: throw CliError("usage", Msg.t("sys.unknown", "name" to n, "systems" to CartSystem.entries.joinToString(", ") { it.name.lowercase() }), EXIT_USAGE)
}
