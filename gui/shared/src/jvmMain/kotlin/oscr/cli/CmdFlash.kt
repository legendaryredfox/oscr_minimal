// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comandos flash-* (programador de flash genérico, sistema 7). */
internal fun fpError(e: RomImageException, a: Args): CliError = CliError(if (e.problem in setOf(RomImageProblem.FP_BUS, RomImageProblem.FP_KB, RomImageProblem.FP_NEEDS_TYPE, RomImageProblem.FP_DETECT_ONLY, RomImageProblem.FP_MD_OPTIONS)) "usage" else "bad_rom",
    imageMessage(e, a), EXIT_USAGE)

internal fun fpInt(a: Args, k: String): Int? = a.opts[k]?.let { it.toIntOrNull() ?: throw CliError("usage", Msg.t("args.needs_number", "name" to k), EXIT_USAGE) }
internal fun fpBus(a: Args): String = a.opts["bus"] ?: throw CliError("usage", "give --bus (${FlashProg.BUS.keys.joinToString(", ")})", EXIT_USAGE)
internal fun fpSys(a: Args) = if (a.opts["system"] == "mock") CartSystem.MOCK else CartSystem.FLASH      // o simulador só entende o sistema MOCK

internal fun fpJob(a: Args, needType: Boolean = false, detect: Boolean = false): FlashJob =
    try { FlashProg.params(fpBus(a), fpInt(a, "flash-kb"), a.opts["flash-type"], fpInt(a, "sector-kb"), fpInt(a, "buffer"), needType, detect) } catch (e: RomImageException) { throw fpError(e, a) }

internal fun fpNeed(c: Conn) {
    if (!c.info.flashProg) throw CliError("unsupported_firmware", Msg.t("flash.no_prog"), EXIT_ERROR, Msg.t("fw.unsupported.hint"))
}

internal fun fpRead(io: CliIo, a: Args, c: Conn, job: FlashJob): DumpResult = c.client.dumpRom(fpSys(a), a.int("block"), job.chip, job.prgKb, job.chrWord, progress(io, a, "flash-read"))

internal fun cmdFlashId(io: CliIo, a: Args): Int {
    val job = fpJob(a, detect = true); val bus = fpBus(a)
    val c = connect(io, a)
    val r = try { fpNeed(c); c.client.detect(fpSys(a), job.chip, job.prgKb, job.chrWord) } finally { c.transport.close() }
    if (bus == "md") {                                    // flash do cartucho de Mega Drive: nome e capacidade pela tabela do firmware
        val known = r.status == 0
        val cfi = !known && r.name.startsWith("CFI ")
        emit(io, a, Json.obj("ok" to known, "known" to known, "ids" to r.name, "chip" to (if (known) r.name.substringBeforeLast(' ') else null), "size" to (if (known || cfi) r.romSize else 0L), "cfi" to cfi, "status" to r.status),
            listOf(if (known) "${FlashProg.LABEL.getValue(bus)}: ${r.name}  (${r.romSize / 1024} KB)"
                else "${FlashProg.LABEL.getValue(bus)}: chip not in the table or no answer (${r.name}): mask ROM (no flash), cartridge not seated, or a chip the firmware does not know yet. " +
                    (if (cfi) "The chip answered the CFI query and says it has ${r.romSize / 1024} KB, but only chips in the table are written. " else "") + "Nothing was written."))
        return if (known) EXIT_OK else EXIT_ERROR
    }
    val ok = r.status == 0
    val legend = if ('=' in r.name) " (I = Intel 28F, A = AMD 29F032, B = AMD 29F1610, S = SST 39SF040; ID 0000 or FFFF = the chip did not answer that routine)" else ""
    emit(io, a, Json.obj("ok" to ok, "ids" to r.name, "size" to r.romSize, "status" to r.status),
        listOf(if (ok) "${FlashProg.LABEL.getValue(bus)}: ${r.name}$legend" else "${FlashProg.LABEL.getValue(bus)}: no chip answered (ID 0000 or FFFF)"))
    return if (ok) EXIT_OK else EXIT_NO_CART
}

internal fun cmdFlashRead(io: CliIo, a: Args): Int {
    val job = fpJob(a)
    val c = connect(io, a)
    val res = try { fpNeed(c); fpRead(io, a, c, job) } finally { c.transport.close() }
    saveResult(io, a, res, ".bin", "flash.bin")
    return EXIT_OK
}

internal fun cmdFlashBlank(io: CliIo, a: Args): Int {
    val job = fpJob(a)
    val c = connect(io, a)
    val res = try { fpNeed(c); fpRead(io, a, c, job) } finally { c.transport.close() }
    val first = res.data.indexOfFirst { it != 0xFF.toByte() }
    emit(io, a, Json.obj("ok" to (first < 0), "blank" to (first < 0), "bytes" to res.data.size, "first_non_blank" to (if (first < 0) null else first)),
        listOf(if (first < 0) Msg.t("flash.blank_yes") else Msg.t("flash.blank_no", "first" to first)))
    return if (first < 0) EXIT_OK else EXIT_ERROR
}

internal fun cmdFlashErase(io: CliIo, a: Args): Int {
    val bus = fpBus(a)
    if (bus == "eprom") throw CliError("usage", Msg.t("flash.eprom_no_erase"), EXIT_USAGE)
    val job = fpJob(a, needType = bus == "8" || bus == "plcc32")
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", Msg.t("refused.erase"), EXIT_REFUSED, Msg.t("refused.repeat"))
        io.err(Msg.t("flash.erase_ask", "chip" to FlashProg.LABEL.getValue(bus), "kb" to job.prgKb))
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) { io.out(Msg.t("cancelled")); return EXIT_ERROR }
    }
    val c = connect(io, a)
    try { fpNeed(c); c.client.erase(fpSys(a), job.chip, job.prgKb, job.chrWord, ((a.opts["begin-timeout"]?.toDoubleOrNull() ?: 90.0) * 1000).toLong()) } finally { c.transport.close() }
    emit(io, a, Json.obj("erased" to true, "bus" to bus, "flash_kb" to job.prgKb), listOf(Msg.t("flash.erased")))
    return EXIT_OK
}

internal fun cmdFlashWrite(io: CliIo, a: Args): Int {
    val input = a.opts["input"] ?: throw CliError("usage", Msg.t("args.needs_input", "cmd" to "flash-write"), EXIT_USAGE)
    val bus = fpBus(a)
    val job = try { FlashProg.split(File(input).readBytes(), bus, fpInt(a, "flash-kb"), a.opts["flash-type"], fpInt(a, "sector-kb"), fpInt(a, "buffer")) } catch (e: RomImageException) { throw fpError(e, a) }
    val what = Msg.t("flash.write_what", "chip" to FlashProg.LABEL.getValue(bus), "n" to job.rom.size, "kb" to job.prgKb)
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", Msg.t("refused.write"), EXIT_REFUSED, Msg.t("refused.repeat"))
        io.err(Msg.t("flash.write_ask", "what" to what))
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) { io.out(Msg.t("cancelled")); return EXIT_ERROR }
    }
    val c = connect(io, a)
    val crc: Int
    try {
        fpNeed(c)
        crc = c.client.writeRom(fpSys(a), job.body, job.chip, job.prgKb, job.chrWord, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, progress(io, a, "flash-write"),
            ((a.opts["begin-timeout"]?.toDoubleOrNull() ?: 90.0) * 1000).toLong())
    } finally { c.transport.close() }
    val hex = hex8(crc)
    val out = linkedMapOf<String, Any?>("bus" to bus, "flash_kb" to job.prgKb, "bytes" to job.body.size, "crc32" to hex)
    val lines = mutableListOf(Msg.t("flash.written", "what" to what, "crc" to hex))
    if ("no-verify" in a.flags || a.opts["system"] == "mock") {
        out["verify"] = "skipped"; lines += Msg.t("verify.skipped")
    } else {
        val c2 = connect(io, a)
        val back = try { fpRead(io, a, c2, job).data } finally { c2.transport.close() }
        val n = job.rom.size
        val diff = (0 until minOf(back.size, n)).firstOrNull { back[it] != job.rom[it] } ?: (if (back.size >= n) null else back.size)
        out["verify"] = Json.obj("ok" to (diff == null), "read_bytes" to back.size, "first_diff" to diff)
        if (diff != null) throw CliError("verify_failed", Msg.t("flash.verify_failed", "first" to diff), EXIT_ERROR, Msg.t("flash.verify_failed.hint"), mapOf("written" to out, "first_diff" to diff))
        lines += Msg.t("verify.ok_chip", "n" to back.size)
    }
    emit(io, a, out, lines)
    return EXIT_OK
}
