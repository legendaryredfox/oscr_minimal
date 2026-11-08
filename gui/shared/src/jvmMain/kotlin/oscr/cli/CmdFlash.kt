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
            listOf(if (known) Msg.t("fid.md_known", "label" to FlashProg.LABEL.getValue(bus), "name" to r.name, "kb" to r.romSize / 1024)
                else Msg.t("fid.md_unknown", "label" to FlashProg.LABEL.getValue(bus), "ids" to r.name) +
                    (if (cfi) Msg.t("fid.md_cfi", "kb" to r.romSize / 1024) else "") + Msg.t("fid.nothing_written")))
        return if (known) EXIT_OK else EXIT_ERROR
    }
    val ok = r.status == 0
    val legend = if ('=' in r.name) Msg.t("fid.legend") else ""
    val cands = if (ok && bus != "eprom") FlashChips.candidates(r.name, bus) else emptyList()
    val lines = ArrayList<String>()
    lines += if (ok) Msg.t("fid.line", "label" to FlashProg.LABEL.getValue(bus), "ids" to r.name, "legend" to legend) else Msg.t("fid.none", "label" to FlashProg.LABEL.getValue(bus))
    if (ok && bus != "eprom") {
        val given = fpInt(a, "flash-kb")
        for (cd in cands) {
            lines += Msg.t("fid.cand", "name" to cd.name, "type" to cd.type, "kb" to cd.size / 1024, "volt" to cd.voltage,
                "routine" to (if (cd.routine.isNotEmpty()) Msg.t("fid.cand_routine", "r" to cd.routine) else ""), "opts" to FlashChips.commandHint(cd, bus))
            if (given != null && given.toLong() != cd.size / 1024) lines += Msg.t("fid.cand_size", "given" to given, "table" to cd.size / 1024, "name" to cd.name)
        }
        lines += if (cands.isNotEmpty()) Msg.t("fid.cand_note") else Msg.t("fid.cand_none")
    }
    val candJson = cands.map { Json.obj("routine" to it.routine, "id" to it.id, "name" to it.name, "type" to it.type, "flash_type" to it.flashType, "size" to it.size,
        "sector_kb" to it.sectorKb, "buffer" to it.buffer, "voltage" to it.voltage) }
    emit(io, a, Json.obj("ok" to ok, "ids" to r.name, "size" to r.romSize, "status" to r.status, "candidates" to candJson), lines)
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
