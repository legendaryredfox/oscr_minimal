// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comando rom-write (gravação de ROM em cartucho de flash). */
internal fun cmdRomWrite(io: CliIo, a: Args): Int {
    val input = a.opts["input"] ?: throw CliError("usage", "rom-write needs -i/--input FILE", EXIT_USAGE)
    val sys = if (a.opts["system"] != null) system(a) else CartSystem.NES
    if (sys != CartSystem.NES && sys != CartSystem.FAMICOM && sys != CartSystem.SNES && sys != CartSystem.MD && sys != CartSystem.GBA && sys != CartSystem.GB && sys != CartSystem.MOCK)
        throw CliError("usage", "rom-write exists for NES and Famicom (NES Maker and A29040B flash), SNES (flash CFI and 8-bit), Mega Drive (flash chips identified by ID: see docs/melhorias-megadrive.md) GBA (Intel, MX29GL128E, MSP55LV128, 369-in-1) and Game Boy (29F, 39SF, CFI); see docs/funcoes-oscr.md", EXIT_USAGE)
    val chipOpt0 = a.opts["chip"]?.let { FlashChip.byKey(it) ?: throw CliError("usage", "unknown --chip: $it. Use: ${FlashChip.entries.joinToString(", ") { c -> c.key }}", EXIT_USAGE) }
    val chipOpt = if (sys == CartSystem.MD && chipOpt0 == null) FlashChip.MD_FLASH else if (sys == CartSystem.GBA && chipOpt0 == null) FlashChip.GBA_FLASH else chipOpt0
    if (chipOpt != null && sys != CartSystem.MOCK && chipOpt !in FlashChip.forSystem(sys)) throw CliError("usage", "chip ${chipOpt.key} does not belong to system ${a.opts["system"] ?: "nes"}", EXIT_USAGE)
    if (sys == CartSystem.SNES && chipOpt == null) throw CliError("usage", "on the SNES choose the flash wiring with --chip snes-lorom or --chip snes-hirom (the ROM alone does not say how the cartridge was built)", EXIT_USAGE)
    if (sys == CartSystem.GB && chipOpt == null) throw CliError("usage", "on the Game Boy choose the cartridge with --chip: ${FlashChip.forSystem(CartSystem.GB).joinToString(", ") { it.key }} (the ROM alone does not say how the cartridge was built)", EXIT_USAGE)
    val capacityOpt = a.opts["capacity"]?.let { it.toIntOrNull() ?: throw CliError("usage", "--capacity needs a number of KB (2048 or 4096)", EXIT_USAGE) }
    fun optInt(k: String) = a.opts[k]?.let { it.toIntOrNull() ?: throw CliError("usage", "--$k needs a number", EXIT_USAGE) }
    val (chip, img) = try {
        RomImages.prepare(File(input).readBytes(), chipOpt, capacityOpt, a.opts["layout"] ?: "1x", optInt("flash-mb"), a.opts["flash-type"], optInt("sector-kb"), optInt("buffer"), optInt("block369") ?: 0)
    }
    catch (e: RomImageException) {
        val msg = when (e.problem) {
            RomImageProblem.TRUNCATED_HEADER -> "incomplete iNES header"
            RomImageProblem.TRAINER -> "the file has a 512-byte trainer; remove it before writing"
            RomImageProblem.SIZE_MISMATCH -> "the file has ${e.a} bytes after the header, but the header says PRG ${e.b} KB and CHR ${e.c} KB"
            RomImageProblem.NEEDS_HEADER -> "the A29040B needs a .nes file with an iNES header (PRG and CHR come from the header)"
            RomImageProblem.RAW_SIZE -> "raw file: the size must be a multiple of 16 KB (use a .nes with header, or raw PRG)"
            RomImageProblem.CHIP_UNKNOWN -> "cannot tell the chip: use --chip nesmaker (mapper 30) or --chip a29040b (mapper 0)"
            RomImageProblem.SNES_SIZE -> "the SNES ROM size must be a multiple of 1 KB (with or without the 512-byte copier header)"
            RomImageProblem.SNES_TOO_BIG -> "the ROM has ${e.a} KB; the SNES writer covers a single 2 MB or 4 MB flash chip (the 2 and 4 chip options of the OSCR do not exist here yet)"
            RomImageProblem.SNES_NO_FIT -> "the ROM has ${e.a} KB and does not fit a ${e.b} KB flash"
            RomImageProblem.SNES_CAPACITY -> "flash capacity: 2048 or 4096 (KB)"
            RomImageProblem.SNES_NEEDS_CHIP -> "on the SNES choose --chip snes-lorom or --chip snes-hirom"
            RomImageProblem.SNES_LAYOUT -> "unknown --layout (use ${SnesLayouts.NAMES.keys.joinToString(", ")})"
            RomImageProblem.SNES_BAD_LAYOUT -> "the ${e.a} KB ROM does not fit this layout (the OSCR requires 6 to 8 MB in the 8 MB ones, at most 4 MB in 2x2mb, and 1x8mb takes only 6 or 8 MB)"
            RomImageProblem.SNES_CAPACITY_FIXED -> "--capacity only applies to the one-chip layout (1x); the others have a fixed capacity"
            RomImageProblem.GEN_TYPE -> "this chip needs --flash-type (${SnesLayouts.FLASH_TYPES.keys.joinToString(", ")}); the OSCR found it in the SD card database, check the chip's datasheet"
            RomImageProblem.GEN_MB -> "this chip needs --flash-mb (1 to 8)"
            RomImageProblem.GEN_NO_FIT -> "the ROM has ${e.a} KB and does not fit a ${e.b} MB flash"
            RomImageProblem.GEN_NEEDS_SECTOR -> "this flash type needs --sector-kb (sector size) and --buffer (write buffer bytes); see the chip's datasheet"
            RomImageProblem.GEN_SECTOR -> "--sector-kb must be a power of 2 (1 to 16384)"
            RomImageProblem.GEN_BUFFER -> "--buffer must be a power of 2 (2 to 128)"
            RomImageProblem.GEN_PADDED_NO_FIT -> "the ROM padded to a whole number of sectors (${e.a} KB) does not fit ${e.b} MB"
            RomImageProblem.GB_SIZE -> "the Game Boy ROM size must be a multiple of 16 KB (one bank), 32 KB or more"
            RomImageProblem.GB_TOO_BIG -> "the ROM has ${e.a} KB; the Game Boy writer goes up to 4 MB (256 banks)"
            RomImageProblem.GB_ORANGE -> "the flash without MBC (Orange FM) writes only 32 KB, as in the OSCR"
            RomImageProblem.GB_NEEDS_CHIP -> "on the Game Boy choose --chip"
            RomImageProblem.FP_BUS, RomImageProblem.FP_KB, RomImageProblem.FP_NEEDS_TYPE, RomImageProblem.FP_SIZE, RomImageProblem.FP_NO_FIT, RomImageProblem.FP_PADDED_NO_FIT, RomImageProblem.FP_DETECT_ONLY, RomImageProblem.FP_MD_OPTIONS -> e.problem.name
            RomImageProblem.GBA_BLOCK -> "--block369 goes from 0 to 63"
            RomImageProblem.GBA_SIZE -> "the GBA ROM size must be a multiple of 1 KB"
            RomImageProblem.GBA_TOO_BIG -> "the ROM has ${e.a} KB and goes past what fits from block ${e.b}"
            RomImageProblem.MD_SIZE -> "the Mega Drive ROM size must be even (binary .md/.bin/.gen file)"
            RomImageProblem.MD_TOO_BIG -> "the ROM has ${e.a} KB; the Mega Drive flash repro holds at most 8 MB (the firmware refuses a ROM larger than the cartridge's chip)"
            RomImageProblem.MD_SMD -> "the file seems to have the 512-byte copier header (.smd); use the plain binary ROM without a header"
        }
        throw CliError(if (e.problem in setOf(RomImageProblem.CHIP_UNKNOWN, RomImageProblem.GEN_TYPE, RomImageProblem.GEN_MB)) "usage" else "bad_rom", msg, EXIT_USAGE)
    }
    if (img.mapper != null && img.mapper != chip.mapper && !a.json) io.err("warning: the file is mapper ${img.mapper}, but chip ${chip.key} belongs to mapper ${chip.mapper} cartridges")
    val layoutName = if (img.layout == SnesLayouts.GENERIC) "8-bit flash of chosen type" else SnesLayouts.NAMES.entries.firstOrNull { it.value == img.layout }?.key ?: "?"
    val what = if (img.flashKb > 0) "${chip.label}: ROM ${img.prgKb} KB in a ${img.flashKb} KB flash, $layoutName (${img.body.size} bytes sent)"
               else if (chip.md || chip.gba || chip.gb) "${chip.label}: ROM ${img.body.size} bytes" + (if (img.block != 0) ", block ${img.block}" else "")
               else "${chip.label}: PRG ${img.prgKb} KB, CHR ${img.chrKb} KB (${img.body.size} bytes)"
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", "refused: writing the ROM ERASES the cartridge's flash chip. Outside a terminal confirm with --yes.", EXIT_REFUSED, "repeat the command with --yes")
        io.err("Write $what? This ERASES the current ROM of the cartridge. Continue? [y/N] ")
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim")) { io.out("cancelled"); return EXIT_ERROR }
    }
    val c = connect(io, a)
    val crc: Int
    var mdChip: MdFlashChip? = null
    try {
        if (!c.info.writeRom) throw CliError("unsupported_firmware", "this firmware does not support WRITE_ROM", EXIT_ERROR, "update the firmware (docs/funcoes-oscr.md)")
        val timeout = ((a.opts["begin-timeout"]?.toDoubleOrNull() ?: 90.0) * 1000).toLong()
        if (sys == CartSystem.MD) {                       // mostra o chip que vai ser gravado antes de apagar
            mdChip = identifyMdFlash(c.client, c.info)
            if (!a.json) io.out(mdChipLine(mdChip))
        }
        crc = c.client.writeRom(sys, img.body, RomImages.chipCode(chip, img), if (img.flashKb > 0) img.flashKb else img.prgKb, if (img.wireChr != 0) img.wireChr else img.chrKb, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, progress(io, a, "write-rom"), timeout)
    } finally { c.transport.close() }
    val hex = (crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
    val out = linkedMapOf<String, Any?>("chip" to chip.key, "prg_kb" to img.prgKb, "chr_kb" to img.chrKb, "bytes" to img.body.size, "crc32" to hex)
    if (img.flashKb > 0) { out["flash_kb"] = img.flashKb; out["layout"] = layoutName }
    if (sys == CartSystem.MD) out["flash_chip"] = mdChipJson(mdChip)
    val lines = mutableListOf("ROM written: $what  CRC32 $hex")
    val gbaSkip = (chip.gba && (img.block != 0 || img.body.size > RomImages.GBA_VERIFY_MAX_BYTES)) || chip == FlashChip.GB_CAM_SECOND    // 369-in-1 em bloco N ou ROM > 64 MB: a leitura comum não alcança
    if ("no-verify" in a.flags || sys == CartSystem.MOCK || gbaSkip) {          // o simulador não guarda a ROM gravada para ler de volta
        out["verify"] = "skipped"; lines += "verification after writing: skipped" + (if (!gbaSkip) "" else if (chip == FlashChip.GB_CAM_SECOND) " (the plain read does not see the 2nd GB Camera game)" else " (the GBA read does not reach 369-in-1 block N, nor more than 64 MB)")
    } else {
        val c2 = connect(io, a)
        val v = try { verifyWritten(c2.client, sys, chip, img, progress(io, a, "verify")) } finally { c2.transport.close() }
        val vj = Json.obj("ok" to v.ok, "read_crc32" to hex8(v.readCrc), "expected_crc32" to hex8(v.expectedCrc), "first_diff" to v.firstDiff, "read_bytes" to v.readBytes)
        out["verify"] = vj
        if (!v.ok) throw CliError("verify_failed", "the ROM read back does NOT match what was written (first differing byte at offset ${v.firstDiff}; read ${hex8(v.readCrc)}, expected ${hex8(v.expectedCrc)})",
            EXIT_ERROR, "clean the contacts, check that the chip is the one chosen and write again; the chip may be erased or half written", mapOf("written" to out, "first_diff" to v.firstDiff))
        lines += "verification after writing: OK (read ${v.readBytes} bytes, CRC32 ${hex8(v.readCrc)})"
    }
    emit(io, a, out, lines)
    return EXIT_OK
}
