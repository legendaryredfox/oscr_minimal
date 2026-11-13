// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comando rom-write (gravação de ROM em cartucho de flash). */
internal fun cmdRomWrite(io: CliIo, a: Args): Int {
    val input = a.opts["input"] ?: throw CliError("usage", Msg.t("args.needs_input", "cmd" to "rom-write"), EXIT_USAGE)
    val sys = if (a.opts["system"] != null) system(a) else CartSystem.NES
    if (sys != CartSystem.NES && sys != CartSystem.FAMICOM && sys != CartSystem.SNES && sys != CartSystem.MD && sys != CartSystem.GBA && sys != CartSystem.GB && sys != CartSystem.MOCK)
        throw CliError("usage", Msg.t("rom.usage.system"), EXIT_USAGE)
    val chipOpt0 = a.opts["chip"]?.let { FlashChip.byKey(it) ?: throw CliError("usage", Msg.t("args.chip_unknown", "chip" to it, "chips" to FlashChip.entries.joinToString(", ") { c -> c.key }), EXIT_USAGE) }
    val chipOpt = if (sys == CartSystem.MD && chipOpt0 == null) FlashChip.MD_FLASH else if (sys == CartSystem.GBA && chipOpt0 == null) FlashChip.GBA_FLASH else chipOpt0
    if (chipOpt != null && sys != CartSystem.MOCK && chipOpt !in FlashChip.forSystem(sys)) throw CliError("usage", Msg.t("rom.usage.chip_not_system", "chip" to chipOpt.key, "system" to (a.opts["system"] ?: "nes")), EXIT_USAGE)
    if (sys == CartSystem.SNES && chipOpt == null) throw CliError("usage", Msg.t("rom.usage.snes_wiring"), EXIT_USAGE)
    if (sys == CartSystem.GB && chipOpt == null) throw CliError("usage", Msg.t("rom.usage.gb_chip", "chips" to FlashChip.forSystem(CartSystem.GB).joinToString(", ") { it.key }), EXIT_USAGE)
    val capacityOpt = a.opts["capacity"]?.let { it.toIntOrNull() ?: throw CliError("usage", Msg.t("args.capacity"), EXIT_USAGE) }
    fun optInt(k: String) = a.opts[k]?.let { it.toIntOrNull() ?: throw CliError("usage", Msg.t("args.needs_number", "name" to k), EXIT_USAGE) }
    val (chip, img) = try {
        RomImages.prepare(File(input).readBytes(), chipOpt, capacityOpt, a.opts["layout"] ?: "1x", optInt("flash-mb"), a.opts["flash-type"], optInt("sector-kb"), optInt("buffer"), optInt("block369") ?: 0)
    }
    catch (e: RomImageException) {
        val msg = imageMessage(e, a)
        throw CliError(if (e.problem in setOf(RomImageProblem.CHIP_UNKNOWN, RomImageProblem.GEN_TYPE, RomImageProblem.GEN_MB)) "usage" else "bad_rom", msg, EXIT_USAGE)
    }
    if (img.mapper != null && img.mapper != chip.mapper && !a.json) io.err(Msg.t("rom.mapper_warn", "file" to img.mapper, "chip" to chip.key, "chipmapper" to chip.mapper))
    val layoutName = if (img.layout == SnesLayouts.GENERIC) "8-bit flash of chosen type" else SnesLayouts.NAMES.entries.firstOrNull { it.value == img.layout }?.key ?: "?"
    val what = if (img.flashKb > 0) Msg.t("rom.what_flash", "label" to chip.label, "prg" to img.prgKb, "flash" to img.flashKb, "layout" to layoutName, "n" to img.body.size)
               else if (chip.md || chip.gba || chip.gb) (if (img.block != 0) Msg.t("rom.what_block", "label" to chip.label, "n" to img.body.size, "block" to img.block) else Msg.t("rom.what_plain", "label" to chip.label, "n" to img.body.size))
               else Msg.t("rom.what_prgchr", "label" to chip.label, "prg" to img.prgKb, "chr" to img.chrKb, "n" to img.body.size)
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", Msg.t("refused.rom"), EXIT_REFUSED, Msg.t("refused.repeat"))
        io.err(Msg.t("rom.ask", "what" to what))
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) { io.out(Msg.t("cancelled")); return EXIT_ERROR }
    }
    val c = connect(io, a)
    val crc: Int
    var mdChip: MdFlashChip? = null
    try {
        if (!c.info.writeRom) throw CliError("unsupported_firmware", Msg.t("fw.unsupported_write_rom"), EXIT_ERROR, Msg.t("fw.unsupported.hint"))
        val timeout = ((a.opts["begin-timeout"]?.toDoubleOrNull() ?: 90.0) * 1000).toLong()
        if (sys == CartSystem.MD) {                       // mostra o chip que vai ser gravado antes de apagar
            mdChip = identifyMdFlash(c.client, c.info)
            if (!a.json) io.out(mdChipLine(mdChip))
            val limit = mdChip?.boardLimitBytes
            if (limit != null && img.body.size > limit && "ignore-cart-limit" !in a.flags) {         // KY / FlashKit: só 2 MiB de flash; recusa antes de apagar
                val mib = img.body.size / (1024.0 * 1024.0)
                throw CliError("refused", Msg.t("rom.md_limit", "size" to (if (img.body.size % (1 shl 20) == 0) (img.body.size shr 20).toString() else String.format(java.util.Locale.ROOT, "%.2f", mib)),
                    "chip" to (mdChip?.chip ?: ""), "codes" to (mdChip?.codes ?: ""), "limit" to (MdFlashChip.BOARD_LIMIT_BYTES shr 20)), EXIT_REFUSED, Msg.t("rom.md_limit_hint"))
            }
        }
        crc = c.client.writeRom(sys, img.body, RomImages.chipCode(chip, img), if (img.flashKb > 0) img.flashKb else img.prgKb, if (img.wireChr != 0) img.wireChr else img.chrKb, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, progress(io, a, "write-rom"), timeout)
    } finally { c.transport.close() }
    val hex = (crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
    val out = linkedMapOf<String, Any?>("chip" to chip.key, "prg_kb" to img.prgKb, "chr_kb" to img.chrKb, "bytes" to img.body.size, "crc32" to hex)
    if (img.flashKb > 0) { out["flash_kb"] = img.flashKb; out["layout"] = layoutName }
    if (sys == CartSystem.MD) out["flash_chip"] = mdChipJson(mdChip)
    val lines = mutableListOf(Msg.t("rom.written", "what" to what, "crc" to hex))
    val gbaSkip = (chip.gba && (img.block != 0 || img.body.size > RomImages.GBA_VERIFY_MAX_BYTES)) || chip == FlashChip.GB_CAM_SECOND    // 369-in-1 em bloco N ou ROM > 64 MB: a leitura comum não alcança
    if ("no-verify" in a.flags || sys == CartSystem.MOCK || gbaSkip) {          // o simulador não guarda a ROM gravada para ler de volta
        out["verify"] = "skipped"; lines += Msg.t("verify.skipped") + (if (!gbaSkip) "" else " " + Msg.t(if (chip == FlashChip.GB_CAM_SECOND) "rom.skip_gbcam" else "rom.skip_gba"))
    } else {
        val c2 = connect(io, a)
        val v = try { verifyWritten(c2.client, sys, chip, img, progress(io, a, "verify")) } finally { c2.transport.close() }
        val vj = Json.obj("ok" to v.ok, "read_crc32" to hex8(v.readCrc), "expected_crc32" to hex8(v.expectedCrc), "first_diff" to v.firstDiff, "read_bytes" to v.readBytes)
        out["verify"] = vj
        if (!v.ok) throw CliError("verify_failed", Msg.t("rom.verify_failed", "first" to v.firstDiff, "read" to hex8(v.readCrc), "exp" to hex8(v.expectedCrc)),
            EXIT_ERROR, Msg.t("rom.verify_failed.hint"), mapOf("written" to out, "first_diff" to v.firstDiff))
        lines += Msg.t("verify.ok", "n" to v.readBytes, "crc" to hex8(v.readCrc))
    }
    emit(io, a, out, lines)
    return EXIT_OK
}
