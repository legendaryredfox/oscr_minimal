// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando detect e a identificação do chip de flash do Mega Drive. */
internal fun cmdDetect(io: CliIo, a: Args): Int {
    val wantChip = "flash-id" in a.flags
    if (wantChip && a.opts["system"] != "md") throw CliError("usage", Msg.t("detect.flash_id_md_only"), EXIT_USAGE)
    val c = connect(io, a)
    var chip: MdFlashChip? = null
    val adapter = if (a.opts["system"] in setOf("sms", "gg", "sg1000")) (a.opts["mapper"]?.toIntOrNull() ?: 0) else 0     // o adaptador (campo mapper) muda a fiação dos barramentos
    val r = try {
        c.client.detect(system(a), adapter).also { if (wantChip) chip = identifyMdFlash(c.client, c.info) }
    } finally { c.transport.close() }
    val text = statusText(r.status)
    val lines = mutableListOf("${CartSystem.entries.firstOrNull { it.id == r.system }?.name?.lowercase() ?: r.system}: $text")
    if (r.status == 0) lines += Msg.t("detect.title_line", "name" to r.name.ifEmpty { Msg.t("detect.unknown_title") }, "rom" to r.romSize, "save" to r.saveSize)
    if (wantChip) lines += "  " + mdChipLine(chip)
    val json = linkedMapOf<String, Any?>("ok" to (r.status == 0), "system" to r.system, "status" to r.status, "rom_size" to r.romSize, "save_size" to r.saveSize,
        "save_type" to r.saveType, "name" to r.name, "status_text" to text)
    if (wantChip) json["flash_chip"] = mdChipJson(chip)
    if (!a.json && colorOn(io, a)) {                      // terminal: o cartucho desenhado ao lado dos dados
        val fields = mutableListOf<Pair<String, String>>()
        if (r.status == 0) { fields += Msg.t("detect.field_title") to r.name.ifEmpty { Msg.t("detect.unknown_title") }; fields += "ROM" to "${r.romSize} bytes"; fields += Msg.t("detect.field_save") to "${r.saveSize} bytes" }
        if (wantChip) fields += Msg.t("detect.field_chip") to mdChipLine(chip).substringAfter(": ")
        val name = CartSystem.entries.firstOrNull { it.id == r.system }?.name?.lowercase() ?: r.system.toString()
        val art = mapOf("snes" to 1, "nes" to 2, "famicom" to 3, "md" to 4, "gba" to 5, "gb" to 6)[name] ?: 1
        Ui.detectCard(true, art, "$name: ${text.substringBefore(" (")}", r.status == 0, fields).forEach(io.out)
    } else emit(io, a, json, lines)
    return if (r.status == 0) EXIT_OK else EXIT_NO_CART
}

internal fun mdChipLine(c: MdFlashChip?): String = when {
    c == null -> Msg.t("chip.no_id")
    c.known -> Msg.t("chip.known", "chip" to c.chip, "kb" to c.sizeBytes / 1024, "codes" to c.codes)
    else -> Msg.t("chip.unknown", "ids" to c.ids) + (if (c.sizeBytes > 0) Msg.t("chip.cfi_size", "kb" to c.sizeBytes / 1024) else "")
}

internal fun mdChipJson(c: MdFlashChip?): Any? = c?.let { Json.obj("known" to it.known, "ids" to it.ids, "chip" to it.chip, "codes" to it.codes, "size" to it.sizeBytes) }
