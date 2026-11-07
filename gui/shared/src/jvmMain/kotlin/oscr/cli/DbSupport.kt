// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Base de dados de jogos: carregar, buscar e transformar em JSON. */
internal val DbMatch.How.text get() = when (this) { DbMatch.How.CRC32 -> "crc32"; DbMatch.How.CRC32_NO_HEADER -> "crc32 without iNES header"; DbMatch.How.CRC32_PRG_CHR -> "crc32 of PRG and CHR" }

internal fun entryJson(e: DbEntry): MutableMap<String, Any?> {
    val d = LinkedHashMap(Json.obj("name" to e.name, "crc32" to hex8(e.crc), "size" to e.size, "source" to e.source, "kind" to e.kind))
    e.nesOptions()?.let { o -> d["mapper"] = o.mapper; d["submapper"] = e.submapper; d["prg_kb"] = o.prgKb; d["chr_kb"] = o.chrKb; d["ram_kb"] = o.ramKb; d["battery"] = e.battery }
    return d
}

internal fun matchJson(m: DbMatch): Map<String, Any?> = entryJson(m.entry).also { it["match"] = m.how.text; it["others"] = m.others }

internal fun loadDb(a: Args, required: Boolean): Database? {
    val paths = a.opts["db"]?.split("\n").orEmpty().ifEmpty { DatabaseLoader.pathsFromEnv() }
    val builtin = "no-builtin-db" !in a.flags && DatabaseLoader::class.java.classLoader.getResource("oscr/INDEX.txt") != null
    if (paths.isEmpty() && !builtin) {
        if (required) throw CliError("no_database", "no database: use --db FILE_OR_FOLDER (No-Intro .dat or NES 2.0 XML) or the OSCR_DB environment variable", EXIT_USAGE)
        return null
    }
    try { return DatabaseLoader.loadAll(paths, builtin) }
    catch (e: DatabaseError) { throw CliError("database", e.message ?: "database error", EXIT_ERROR, "check the path and that the file is a Logiqx .dat or nes20db.xml") }
}

internal fun gameOptions(db: Database, query: String): DbEntry {
    var found = db.searchNes(query, 200)
    val exact = found.filter { it.name.equals(query, true) }
    if (exact.isNotEmpty()) found = exact
    val uniq = LinkedHashMap<List<Int?>, DbEntry>()
    for (e in found) uniq[listOf(e.mapper, e.prgKb, e.chrKb, e.ramKb)] = e
    if (uniq.isEmpty()) throw CliError("game_not_found", "no game with mapper and sizes in the database for: $query", EXIT_USAGE,
        "the database must be the NES 2.0 XML (nes20db.xml); No-Intro has no mapper. Use 'search' to look up names")
    if (uniq.size > 1) throw CliError("game_ambiguous", "${found.size} games match '$query' with different configurations", EXIT_USAGE,
        "be more specific. Examples: " + uniq.values.take(5).joinToString("; ") { "${it.name} (mapper ${it.mapper}, PRG ${it.prgKb} KB, CHR ${it.chrKb} KB)" })
    return uniq.values.first()
}
