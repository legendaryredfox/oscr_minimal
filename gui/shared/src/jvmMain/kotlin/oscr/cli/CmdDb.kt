// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comandos identify e search. */
internal val EXT_SYSTEM = mapOf("sfc" to CartSystem.SNES, "smc" to CartSystem.SNES, "nes" to CartSystem.NES, "md" to CartSystem.MD, "gen" to CartSystem.MD,
    "smd" to CartSystem.MD, "gba" to CartSystem.GBA, "gb" to CartSystem.GB, "gbc" to CartSystem.GB)

internal fun cmdIdentify(io: CliIo, a: Args): Int {
    val db = loadDb(a, required = true)!!
    if (a.positional.isEmpty()) throw CliError("usage", Msg.t("args.identify"), EXIT_USAGE)
    val results = a.positional.map { f ->
        val file = File(f); val data = file.readBytes()
        val sys = if (a.opts["system"] != null) system(a) else EXT_SYSTEM[file.extension.lowercase()] ?: CartSystem.MOCK
        val m = db.identify(sys, data)
        Json.obj("file" to f, "bytes" to data.size, "crc32" to hex8(crc32(data)), "game" to m?.let { matchJson(it) })
    }
    emit(io, a, Json.obj("entries_in_database" to db.size, "results" to results), results.map { r ->
        val g = r["game"] as? Map<*, *>
        "${r["file"]}  CRC32 ${r["crc32"]}  " + (g?.let { "${it["name"]} (${it["source"]}, ${it["match"]})" } ?: Msg.t("db.not_found"))
    })
    return if (results.all { it["game"] != null }) EXIT_OK else EXIT_ERROR
}

internal fun cmdSearch(io: CliIo, a: Args): Int {
    val db = loadDb(a, required = true)!!
    val q = a.positional.joinToString(" ").ifBlank { throw CliError("usage", Msg.t("args.search"), EXIT_USAGE) }
    val found = db.search(q, a.opts["limit"]?.let { a.int("limit") } ?: 20)
    emit(io, a, Json.obj("entries_in_database" to db.size, "results" to found.map { entryJson(it) }),
        found.map { e -> "${hex8(e.crc)}  ${e.name}" + (e.nesOptions()?.let { "  [mapper ${it.mapper}, PRG ${it.prgKb} KB, CHR ${it.chrKb} KB, RAM ${it.ramKb} KB]" } ?: "") }.ifEmpty { listOf(Msg.t("search.none")) })
    return if (found.isNotEmpty()) EXIT_OK else EXIT_ERROR
}
