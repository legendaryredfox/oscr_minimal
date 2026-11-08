// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File

/**
 * Comando firmware-flash: grava o firmware do fork (`firmware/oscr`) no Arduino Mega pela USB, com o avrdude (D131).
 * Mesmo contrato da CLI Python (docs/referencia/cli.md). O `.hex` vem de --hex, de OSCR_FIRMWARE_HEX ou da compilação do projeto
 * (`firmware/oscr/.pio/build/<--env>/firmware.hex`, procurada a partir da pasta atual para cima); o avrdude, de --avrdude, de AVRDUDE, do PATH ou do PlatformIO.
 */
private fun <T> prep(block: () -> T): T = try { block() } catch (e: FirmwareException) { throw CliError(e.kind, e.message ?: e.kind, EXIT_USAGE, e.hint) }
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
    val exe = if (simulate) "avrdude (simulated)" else findAvrdude(a)
    val port = a.opts["port"] ?: if (simulate) "simulator" else (io.listPorts().firstOrNull { p -> listOf("ttyUSB", "ttyACM", "cu.usb", "COM").any { it in p } }
        ?: throw CliError("no_port", "no serial port found", EXIT_NO_DEVICE, "connect the device, use --port, or --simulate without hardware (Linux: dialout group)"))
    val before = try { connect(io, a, needCart = false).also { it.transport.close() }.info } catch (e: Throwable) { null }       // placa nova não responde: sem versão de antes
    val verify = "no-verify" !in a.flags
    val what = "write ${hex.name} (${hex.length()} bytes of HEX) to $port with avrdude"
    if ("dry-run" in a.flags) {
        val cmd = avrdudeCmd(exe, port, hex, verify)
        emit(io, a, Json.obj("dry_run" to true, "port" to port, "hex" to hex.path, "avrdude" to exe, "command" to cmd, "firmware_before" to before?.firmware), listOf("nothing was written (--dry-run). Command: " + cmd.joinToString(" ")))
        return EXIT_OK
    }
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", "refused: flashing the firmware replaces the Arduino's program. Outside a terminal confirm with --yes.", EXIT_REFUSED, "repeat the command with --yes")
        io.err("${what.replaceFirstChar { it.uppercase() }}. The current firmware will be replaced. Continue? [y/N] ")
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim")) { io.out("cancelled"); return EXIT_ERROR }
    }
    if (simulate) {
        emit(io, a, Json.obj("simulated" to true, "port" to port, "hex" to hex.path, "firmware_before" to before?.firmware, "firmware_after" to before?.firmware), listOf("simulated: $what"))
        return EXIT_OK
    }
    val (code, err) = runAvrdude(avrdudeCmd(exe, port, hex, verify)) { label -> progress(io, a, if (label == "writing") "gravando" else "conferindo") }
    if (code != 0) throw CliError("avrdude", "avrdude failed (code $code): ${err.ifEmpty { "no message" }}", if (code == 1 || code == 127) EXIT_NO_DEVICE else EXIT_ERROR,
        "check the port and the cable, close other programs using the port (serial monitor, GUI) and retry; on Linux, dialout group")
    val after = infoAfter(io, a, a.opts["wait"]?.toDoubleOrNull() ?: 12.0)
    val lines = mutableListOf("firmware written to $port" + if (verify) " and verified by avrdude" else "")
    if (after != null) lines += "the device answered INFO: firmware ${after.firmware}, protocol ${after.proto}" + (before?.let { " (before: ${it.firmware})" } ?: "")
    else lines += "the device has not answered INFO yet (the port may have changed name): run `dumper info` in a few seconds"
    emit(io, a, Json.obj("port" to port, "hex" to hex.path, "verified" to verify, "firmware_before" to before?.firmware, "firmware_after" to after?.firmware, "responds" to (after != null)), lines)
    return EXIT_OK
}
