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
        if (required) throw CliError("no_database", Msg.t("db.none"), EXIT_USAGE)
        return null
    }
    try { return DatabaseLoader.loadAll(paths, builtin) }
    catch (e: DatabaseError) { throw CliError("database", e.message ?: "database error", EXIT_ERROR, Msg.t("db.load_hint")) }
}

internal fun gameOptions(db: Database, query: String): DbEntry {
    var found = db.searchNes(query, 200)
    val exact = found.filter { it.name.equals(query, true) }
    if (exact.isNotEmpty()) found = exact
    val uniq = LinkedHashMap<List<Int?>, DbEntry>()
    for (e in found) uniq[listOf(e.mapper, e.prgKb, e.chrKb, e.ramKb)] = e
    if (uniq.isEmpty()) throw CliError("game_not_found", Msg.t("game.not_found", "query" to query), EXIT_USAGE, Msg.t("game.not_found.hint"))
    if (uniq.size > 1) throw CliError("game_ambiguous", Msg.t("game.ambiguous", "n" to found.size, "query" to query), EXIT_USAGE,
        Msg.t("game.ambiguous.hint", "examples" to uniq.values.take(5).joinToString("; ") { Msg.t("game.example", "name" to it.name, "mapper" to it.mapper, "prg" to it.prgKb, "chr" to it.chrKb) }))
    return uniq.values.first()
}
