// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File

/**
 * Comando firmware-flash: grava o firmware do fork (`firmware/oscr`) no Arduino Mega pela USB, com o avrdude (D131).
 * Mesmo contrato da CLI Python (docs/referencia/cli.md). O `.hex` vem de --hex, de OSCR_FIRMWARE_HEX ou da compilação do projeto
 * (`firmware/oscr/.pio/build/<--env>/firmware.hex`, procurada a partir da pasta atual para cima); o avrdude, de --avrdude, de AVRDUDE, do PATH ou do PlatformIO.
 */
private fun <T> prep(block: () -> T): T = try { block() } catch (e: FirmwareException) { throw CliError(e.kind, Msg.t(e.key, *e.args.toList().toTypedArray()), EXIT_USAGE, Msg.t(e.key + ".hint", *e.args.toList().toTypedArray())) }
internal fun findHex(a: Args): java.io.File = prep { FirmwareFlash.findHex(a.opts["hex"], a.opts["env"] ?: FirmwareFlash.DEFAULT_ENV) }
internal fun findAvrdude(a: Args): String = prep { FirmwareFlash.findAvrdude(a.opts["avrdude"]) }
internal fun avrdudeCmd(exe: String, port: String, hex: File, verify: Boolean): List<String> = FirmwareFlash.command(exe, port, hex, verify)

private fun runAvrdude(cmd: List<String>, progressFor: (String) -> Progress): Pair<Int, String> {
    val cbs = HashMap<String, Progress>()
    return FirmwareFlash.run(cmd) { label, pct -> cbs.getOrPut(label) { progressFor(label) }(pct.toLong(), 100L) }
}

private fun infoAfter(io: CliIo, a: Args, waitS: Double): DeviceInfo? {
    val end = System.currentTimeMillis() + (waitS * 1000).toLong()
    while (System.currentTimeMillis() < end) {
        try { val c = connect(io, a, needCart = false); c.transport.close(); return c.info } catch (e: Throwable) { Thread.sleep(1000) }
    }
    return null
}

internal fun cmdFirmwareFlash(io: CliIo, a: Args): Int {
    val hex = findHex(a)
    val simulate = "simulate" in a.flags
    val exe = if (simulate) Msg.t("fw.simulated_exe") else findAvrdude(a)
    val port = a.opts["port"] ?: if (simulate) Msg.t("fw.simulator") else (io.listPorts().firstOrNull { p -> listOf("ttyUSB", "ttyACM", "cu.usb", "COM").any { it in p } }
        ?: throw CliError("no_port", Msg.t("err.no_port"), EXIT_NO_DEVICE, Msg.t("err.no_port.hint")))
    val before = try { connect(io, a, needCart = false).also { it.transport.close() }.info } catch (e: Throwable) { null }       // placa nova não responde: sem versão de antes
    val verify = "no-verify" !in a.flags
    val what = Msg.t("fw.what", "hex" to hex.name, "size" to hex.length(), "port" to port)
    if ("dry-run" in a.flags) {
        val cmd = avrdudeCmd(exe, port, hex, verify)
        emit(io, a, Json.obj("dry_run" to true, "port" to port, "hex" to hex.path, "avrdude" to exe, "command" to cmd, "firmware_before" to before?.firmware), listOf(Msg.t("fw.dry_run", "cmd" to cmd.joinToString(" "))))
        return EXIT_OK
    }
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", Msg.t("refused.firmware"), EXIT_REFUSED, Msg.t("refused.repeat"))
        io.err(Msg.t("fw.ask", "what" to what.replaceFirstChar { it.uppercase() }))
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) { io.out(Msg.t("cancelled")); return EXIT_ERROR }
    }
    if (simulate) {
        emit(io, a, Json.obj("simulated" to true, "port" to port, "hex" to hex.path, "firmware_before" to before?.firmware, "firmware_after" to before?.firmware), listOf(Msg.t("fw.simulated", "what" to what)))
        return EXIT_OK
    }
    val (code, err) = runAvrdude(avrdudeCmd(exe, port, hex, verify)) { label -> progress(io, a, if (label == "writing") "gravando" else "conferindo") }
    if (code != 0) throw CliError("avrdude", Msg.t("fw.failed", "code" to code, "detail" to err.ifEmpty { Msg.t("fw.failed.no_message") }), if (code == 1 || code == 127) EXIT_NO_DEVICE else EXIT_ERROR,
        Msg.t("fw.failed.hint"))
    val after = infoAfter(io, a, a.opts["wait"]?.toDoubleOrNull() ?: 12.0)
    val lines = mutableListOf(Msg.t("fw.done", "port" to port) + if (verify) Msg.t("fw.done_verified") else "")
    if (after != null) lines += Msg.t("fw.answered", "fw" to after.firmware, "proto" to after.proto) + (before?.let { Msg.t("fw.before", "fw" to it.firmware) } ?: "")
    else lines += Msg.t("fw.no_answer")
    emit(io, a, Json.obj("port" to port, "hex" to hex.path, "verified" to verify, "firmware_before" to before?.firmware, "firmware_after" to after?.firmware, "responds" to (after != null)), lines)
    return EXIT_OK
}
