// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Conexão com o dispositivo (porta serial ou simulador) e leitura do sistema escolhido. */
internal class Conn(val client: OscrClient, val transport: Transport, val info: DeviceInfo, val boardResult: Map<String, Any?>? = null)

/**
 * Abre a porta (ou o simulador), faz INFO e, antes de um comando de cartucho, ajusta a tensão do seletor 3,3 V/5 V (D138; placa sem seletor: só recusa `--voltage 3v3`).
 * O 5V dos slots fica sempre ligado (D139). `needCart = false` (info, voltage) nunca mexe na tensão.
 */
internal fun connect(io: CliIo, a: Args, needCart: Boolean = true): Conn {
    var c = if (a.opts["board"] != null) {                              // D162: a placa escolhida decide se o firmware serve ou se precisa gravar
        val opened = try { open(io, a) } catch (e: CliError) { if (e.kind == "no_response") null else throw e }
        ensureBoard(io, a, opened)
    } else open(io, a)
    if (needCart) {
        try {
            setVoltage(io, a, c, c.client.voltage(Volt.STATUS))
        } catch (e: Throwable) { c.transport.close(); throw e }
    }
    return c
}

internal fun open(io: CliIo, a: Args): Conn {
    val conn = openRaw(io, a)
    conn.client.onStage = stageNotifier(io, a)                  // F-1: etapa avisada pelo firmware (apagando, gravando...)
    return conn
}

private fun openRaw(io: CliIo, a: Args): Conn {
    if ("simulate" in a.flags) {
        val old = io.simOldFw && !io.simFlashed
        val t = SimDevice(voltSelect = io.simVolt, cartNeeds5v = io.simCart5v, selftestReport = if (io.simSelftest) listOf(Triple(1, 30, 0), Triple(2, 22, 57)) else emptyList(),
            boardProfile = !old, firmware = if (old) Triple(0, 1, 0) else Triple(0, 2, 0), systemsMask = if (old) 0L else (1..11).sumOf { 1L shl it }, stages = !old, clockSupported = !old)
        val c = OscrClient(t, 500, 5000)
        return Conn(c, t, c.info())
    }
    val port = a.opts["port"] ?: io.listPorts().firstOrNull { p -> listOf("ttyUSB", "ttyACM", "cu.usb", "COM").any { it in p } }
        ?: throw CliError("no_port", Msg.t("err.no_port"), EXIT_NO_DEVICE, Msg.t("err.no_port.hint"))
    val bauds = a.opts["baud"]?.let { listOf(a.int("baud")) } ?: Proto.BAUDS
    var last: Exception? = null
    for (b in bauds) {
        val t = io.openPort(port, b)
        val c = OscrClient(t, 500, 10_000)
        try { return Conn(c, t, infoAfterBoot(t, c)) } catch (e: TimeoutError) { last = e; t.close() }
    }
    throw CliError("no_response", Msg.t("err.no_response", "port" to port, "bauds" to bauds.joinToString(", "), "error" to last?.message), EXIT_NO_DEVICE, Msg.t("err.no_response.hint"))
}

/** `--type` do SNES (F-2, D164) como código do protocolo; 0 = pelo cabeçalho. Em outro sistema, ou com valor desconhecido, é erro de uso. */
internal fun snesTypeCode(a: Args): Int {
    val acc = a.opts["accessory"]
    if (acc != null) {                                                // F-10: Sufami Turbo (ROM) e GPC (save), no mesmo 3º campo
        if (a.opts["system"] != "snes") throw CliError("usage", Msg.t("snes_acc.only_snes"), EXIT_USAGE)
        if (a.opts["type"] != null) throw CliError("usage", Msg.t("snes_acc.with_type"), EXIT_USAGE)
        val code = Proto.SNES_ACCESSORIES[acc] ?: throw CliError("usage", Msg.t("args.chip_unknown", "chip" to acc, "chips" to Proto.SNES_ACCESSORIES.keys.joinToString(", ")), EXIT_USAGE)
        val isSave = acc in Proto.SNES_SAVE_ACCESSORIES                  // GPC e SRAM do BS-X são RAM; os outros, ROM
        if ((isSave && a.cmd in setOf("dump", "detect")) || (!isSave && a.cmd in setOf("save-read", "save-write"))) throw CliError("usage", Msg.t(if (isSave) "snes_acc.gpc_is_save" else "snes_acc.sufami_is_rom"), EXIT_USAGE)
        return code
    }
    val t = a.opts["type"] ?: return 0
    if (a.opts["system"] != "snes") throw CliError("usage", Msg.t("snes_type.only_snes"), EXIT_USAGE)
    return SnesType.CODES[t] ?: throw CliError("usage", Msg.t("snes_type.bad"), EXIT_USAGE)
}

internal fun system(a: Args): CartSystem {
    val n = (a.opts["system"] ?: "mock").lowercase()
    return CartSystem.entries.firstOrNull { it.name.lowercase() == n }
        ?: throw CliError("usage", Msg.t("sys.unknown", "name" to n, "systems" to CartSystem.entries.joinToString(", ") { it.name.lowercase() }), EXIT_USAGE)
}
