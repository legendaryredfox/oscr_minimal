// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando detect e a identificação do chip de flash do Mega Drive. */
internal fun cmdDetect(io: CliIo, a: Args): Int {
    val wantChip = "flash-id" in a.flags
    if (wantChip && a.opts["system"] != "md") throw CliError("usage", Msg.t("detect.flash_id_md_only"), EXIT_USAGE)
    val c = connect(io, a)
    var chip: MdFlashChip? = null
    val r = try { c.client.detect(system(a)).also { if (wantChip) chip = identifyMdFlash(c.client, c.info) } } finally { c.transport.close() }
    val text = STATUS[r.status] ?: r.status.toString()
    val lines = mutableListOf("${CartSystem.entries.firstOrNull { it.id == r.system }?.name?.lowercase() ?: r.system}: $text")
    if (r.status == 0) lines += "  title: ${r.name.ifEmpty { "(unknown)" }}  ROM: ${r.romSize} bytes  save: ${r.saveSize} bytes"
    if (wantChip) lines += "  " + mdChipLine(chip)
    if (r.attempts > 1) lines += "  ${r.attempts} header read attempts (SA-1 power cycle)"
    val json = linkedMapOf<String, Any?>("ok" to (r.status == 0), "system" to r.system, "status" to r.status, "rom_size" to r.romSize, "save_size" to r.saveSize,
        "save_type" to r.saveType, "name" to r.name, "attempts" to r.attempts, "status_text" to text)
    if (wantChip) json["flash_chip"] = mdChipJson(chip)
    if (!a.json && colorOn(io, a)) {                      // terminal: o cartucho desenhado ao lado dos dados
        val fields = mutableListOf<Pair<String, String>>()
        if (r.status == 0) { fields += "title" to r.name.ifEmpty { "(unknown)" }; fields += "ROM" to "${r.romSize} bytes"; fields += "save" to "${r.saveSize} bytes" }
        if (wantChip) fields += "chip" to mdChipLine(chip).removePrefix("flash chip: ")
        if (r.attempts > 1) fields += "attempts" to "${r.attempts} (SA-1 power cycle)"
        val name = CartSystem.entries.firstOrNull { it.id == r.system }?.name?.lowercase() ?: r.system.toString()
        val art = mapOf("snes" to 1, "nes" to 2, "famicom" to 3, "md" to 4, "gba" to 5, "gb" to 6)[name] ?: 1
        Ui.detectCard(true, art, "$name: ${text.substringBefore(" (")}", r.status == 0, fields).forEach(io.out)
    } else emit(io, a, json, lines)
    return if (r.status == 0) EXIT_OK else EXIT_NO_CART
}

internal fun mdChipLine(c: MdFlashChip?): String = when {
    c == null -> "flash chip: this firmware does not identify the chip"
    c.known -> "flash chip: ${c.chip}  (${c.sizeBytes / 1024} KB)"
    else -> "flash chip: not in the table or no answer (${c.ids})" + (if (c.sizeBytes > 0) "; the CFI query says ${c.sizeBytes / 1024} KB" else "")
}

internal fun mdChipJson(c: MdFlashChip?): Any? = c?.let { Json.obj("known" to it.known, "ids" to it.ids, "chip" to it.chip, "size" to it.sizeBytes) }
