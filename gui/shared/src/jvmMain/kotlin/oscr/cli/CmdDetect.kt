// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comando detect e a identificação do chip de flash do Mega Drive. */
internal fun cmdDetect(io: CliIo, a0: Args): Int {
    val wantChip = "flash-id" in a0.flags
    if (wantChip && a0.opts["system"] != "md") throw CliError("usage", Msg.t("detect.flash_id_md_only"), EXIT_USAGE)
    val c = connect(io, a0)
    val a = if (a0.opts["system"] == "auto") resolveAuto(io, c, a0) else a0
    var chip: MdFlashChip? = null
    val adapter = if (a.opts["system"] in setOf("sms", "gg", "sg1000")) (a.opts["mapper"]?.toIntOrNull() ?: 0) else 0     // o adaptador (campo mapper) muda a fiação dos barramentos
    val r = try {
        c.client.detect(system(a), adapter).also { if (wantChip) chip = identifyMdFlash(c.client, c.info) }
    } finally { c.transport.close() }
    val n64 = if (a.opts["system"] == "n64" && r.status == 0) N64.info(r, N64Games.byCrc1) else null
    val text = statusText(r.status)
    val lines = mutableListOf("${CartSystem.entries.firstOrNull { it.id == r.system }?.name?.lowercase() ?: r.system}: $text")
    if (n64 != null) {
        val g = n64.game
        lines += Msg.t("detect.title_line", "name" to (g?.name ?: n64.header.title).ifEmpty { Msg.t("detect.unknown_title") }, "rom" to (g?.let { it.sizeMb.toLong() shl 20 } ?: 0L), "save" to (g?.saveBytes ?: 0L))
        lines += if (g != null) Msg.t("n64.game_line", "crc1" to n64.crc1Hex, "gid" to n64.header.gameId) else Msg.t("n64.unknown_game", "crc1" to n64.crc1Hex, "gid" to n64.header.gameId)
        if (g != null && n64.ambiguous) lines += Msg.t("n64.ambiguous", "n" to (n64.others + 1))
    } else if (r.status == 0) lines += Msg.t("detect.title_line", "name" to r.name.ifEmpty { Msg.t("detect.unknown_title") }, "rom" to r.romSize, "save" to r.saveSize)
    if (wantChip) lines += "  " + mdChipLine(chip)
    val json = linkedMapOf<String, Any?>("ok" to (r.status == 0), "system" to r.system, "status" to r.status, "rom_size" to r.romSize, "save_size" to r.saveSize,
        "save_type" to r.saveType, "name" to r.name, "status_text" to text)
    if (wantChip) json["flash_chip"] = mdChipJson(chip)
    if (n64 != null) {
        val g = n64.game
        json["name"] = g?.name ?: n64.header.title
        if (g != null) { json["rom_size"] = g.sizeMb.toLong() shl 20; json["save_size"] = g.saveBytes; json["save_type"] = g.saveType }
        json["n64"] = Json.obj("crc1" to n64.crc1Hex, "game_id" to n64.header.gameId, "title" to n64.header.title, "found" to (g != null), "rom_mb" to g?.sizeMb, "save_type" to g?.saveType,
            "save_label" to g?.let { N64.SAVE_LABEL[it.saveType] }, "others" to n64.others, "ambiguous" to n64.ambiguous)
    }
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
