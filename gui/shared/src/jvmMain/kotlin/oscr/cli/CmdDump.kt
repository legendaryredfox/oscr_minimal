// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comando dump (ROM), com a leitura raw do NES. */
internal fun cmdDump(io: CliIo, a0: Args): Int {
    var a = a0
    var c0: Conn? = null
    if (a0.opts["system"] == "auto") {                  // P5 (D160): descobre o sistema só com leituras
        if (a0.opts["game"] != null) throw CliError("usage", Msg.t("auto.needs_system"), EXIT_USAGE)
        c0 = connect(io, a0)
        a = resolveAuto(io, c0, a0)
    }
    val sys = system(a)
    val db = loadDb(a, required = a.opts["game"] != null)
    var mapper = a.int("mapper"); var prg = a.int("prg"); var chr = a.int("chr")
    a.opts["game"]?.let { q ->
        if (sys != CartSystem.NES && sys != CartSystem.FAMICOM) throw CliError("usage", Msg.t("dump.game_only_nes"), EXIT_USAGE)
        val g = gameOptions(db!!, q); val o = g.nesOptions()!!
        if (mapper == 0) mapper = o.mapper; if (prg == 0) prg = o.prgKb; if (chr == 0) chr = o.chrKb
        if (!a.json) io.err(Msg.t("dump.game_base", "name" to g.name, "mapper" to o.mapper, "prg" to o.prgKb, "chr" to o.chrKb, "source" to g.source))
    }
    val raw = "raw" in a.flags
    if (raw && sys != CartSystem.NES && sys != CartSystem.FAMICOM) throw CliError("usage", Msg.t("dump.raw_only_nes"), EXIT_USAGE)
    val c = c0 ?: connect(io, a)
    var title = ""
    if (sys == CartSystem.N64) {                      // o tamanho vem da base (CRC1 do cabeçalho) ou de --prg (em MB); D158
        try { val r = n64Size(c, a, prg); prg = r.first; title = r.second } catch (e: CliError) { c.transport.close(); throw e }
    } else if (a.opts["output"] == null) title = try { c.client.detect(sys).name } catch (e: Exception) { if (e is DeviceError || e is ProtocolError || e is TimeoutError) "" else throw e }
    val twice = "twice" in a.flags
    var res2: DumpResult? = null
    val res = try {
        c.client.dumpRom(sys, a.int("block"), mapper, prg, chr, progress(io, a, "rom")).also {
            if (twice) res2 = c.client.dumpRom(sys, a.int("block"), mapper, prg, chr, progress(io, a, "rom 2"))
        }
    } finally { c.transport.close() }
    val ext = if (sys == CartSystem.GB && res.data.size > 0x143 && res.data[0x143].toInt() and 0x80 != 0) ".gbc" else sys.ext
    res2?.let { if (!it.data.contentEquals(res.data)) twiceMismatch(a, res, it, ext, safeName(title, "rom_${sys.name.lowercase()}")) }
    val chk = verifyRom(sys, res.data)
    val extra = linkedMapOf<String, Any?>("checksum" to chk.status.name.lowercase())
    val notes = mutableListOf<String>()
    if (res2 != null) { extra["twice"] = true; notes += Msg.t("dump.twice_ok", "crc" to res.crcHex) }
    if (chk.status != CheckStatus.NA) notes += if (chk.status == CheckStatus.MISMATCH) Msg.t("dump.warning") + Msg.t("check.mismatch", "name" to chk.name, "expected" to (chk.expected and 0xFFFF), "computed" to (chk.computed and 0xFFFF))
                 else Msg.t("check.ok", "name" to chk.name, "value" to (chk.expected and 0xFFFF))
    if (sys == CartSystem.GBA) {
        val known = GbaSaveDb.lookup(res.data)                    // P2 (D160): o SHA-1 do cabeçalho acha o save na base do FlashGBX; a cadeia da biblioteca de save fica de reserva
        if (known != null) {
            extra["gba_save_type"] = known.saveType
            extra["gba_save_db"] = Json.obj("name" to known.name, "crc32" to "%08X".format(known.crc32), "rom_size" to known.romSize, "save_type" to known.saveType, "save_label" to known.label, "save_size" to known.saveSize)
            notes += Msg.t("gba.save_db", "name" to known.name, "label" to known.label, "size" to known.saveSize, "code" to known.saveType)
        }
        val h = if (known != null) null else gbaSaveHint(res.data)
        if (known != null) { /* já dito */ }
        else if (h != null) { extra["gba_save_type"] = h.type; notes += Msg.t("gba.save_hint", "tag" to h.tag, "label" to (if (h.type == 2) Msg.t("gba.label.eeprom") else h.label), "code" to h.type, "more" to (if (h.type == 2) Msg.t("gba.save_hint.eeprom_more") else "")) }
        else notes += Msg.t("gba.save_none")
    }
    if (db != null) {
        val m = db.identify(sys, res.data)
        extra["game"] = m?.let { matchJson(it) }
        if (m != null) { title = m.entry.name; notes += Msg.t(if (m.others > 0) "dump.game_more" else "dump.game", "name" to m.entry.name, "source" to m.entry.source, "how" to m.how.text, "others" to m.others) }
        else notes += Msg.t("dump.game_missing", "n" to db.size)
    }
    if (raw) saveNesRaw(io, a, res, safeName(title, "rom_${sys.name.lowercase()}"), extra, notes)
    else saveResult(io, a, res, ext, safeName(title, "rom_${sys.name.lowercase()}"), extra, notes)
    return EXIT_OK
}

/** Tamanho da ROM do N64 em MB e o título: --prg vale sempre; senão o CRC1 do cabeçalho na base do projeto. */
internal fun n64Size(c: Conn, a: Args, prg: Int): Pair<Int, String> {
    val info = N64.info(c.client.detect(CartSystem.N64), N64Games.byCrc1)
    val g = info.game
    var mb = prg
    if (mb == 0) {
        mb = g?.sizeMb ?: 0
        if (mb == 0) throw CliError("usage", Msg.t("n64.need_size", "crc1" to (info.crc1Hex ?: "?"), "sizes" to N64.COMMON_MB.joinToString(", ")), EXIT_USAGE)
        if (info.ambiguous && !a.json) System.err.println(Msg.t("n64.ambiguous", "n" to (info.others + 1)))
    }
    if (!N64.sizeValid(mb)) throw CliError("usage", Msg.t("n64.size_range", "lo" to N64.MIN_MB, "hi" to N64.MAX_MB), EXIT_USAGE)
    return mb to (g?.name ?: "")
}

/** --raw (NES/Famicom): PRG e CHR em arquivos separados (.prg e .chr), sem cabeçalho iNES — a leitura "raw" do OSCR. */
internal fun saveNesRaw(io: CliIo, a: Args, res: DumpResult, default: String, extra: Map<String, Any?>, notes: List<String>) {
    val parts = splitInesRaw(res.data) ?: throw CliError("protocol", Msg.t("dump.raw_no_header"), EXIT_ERROR)
    val base = outPath(a, ".prg", default).let { f -> File(f.path.substringBeforeLast('.', f.path)) }
    base.absoluteFile.parentFile?.mkdirs()
    val prgF = File(base.path + ".prg"); prgF.writeBytes(parts.prg)
    val files = linkedMapOf<String, Any?>("prg" to prgF.path)
    val obj = linkedMapOf<String, Any?>("files" to files, "prg_bytes" to parts.prg.size, "prg_crc32" to hex8(crc32(parts.prg)), "crc32" to res.crcHex)
    val lines = mutableListOf("${prgF.path}  PRG ${parts.prg.size} bytes  CRC32 ${hex8(crc32(parts.prg))}")
    if (parts.chr.isNotEmpty()) {
        val chrF = File(base.path + ".chr"); chrF.writeBytes(parts.chr)
        files["chr"] = chrF.path; obj["chr_bytes"] = parts.chr.size; obj["chr_crc32"] = hex8(crc32(parts.chr))
        lines += "${chrF.path}  CHR ${parts.chr.size} bytes  CRC32 ${hex8(crc32(parts.chr))}"
    } else lines += Msg.t("dump.no_chr")
    lines += Msg.t("dump.ines_full", "crc" to res.crcHex)
    obj.putAll(extra)
    emit(io, a, obj, lines + notes)
}

/** --twice: as duas leituras diferem. Grava as duas (NOME.leitura1 e NOME.leitura2, como a CLI Python) e sai com erro. */
internal fun twiceMismatch(a: Args, r1: DumpResult, r2: DumpResult, ext: String, default: String): Nothing {
    val (diff, first) = diffSummary(r1.data, r2.data)
    val base = outPath(a, ext, default).let { f -> File(f.path.substringBeforeLast('.', f.path)) }
    base.absoluteFile.parentFile?.mkdirs()
    val suffix = outPath(a, ext, default).name.let { n -> if ('.' in n) "." + n.substringAfterLast('.') else "" }
    val f1 = File(base.path + ".leitura1" + suffix); val f2 = File(base.path + ".leitura2" + suffix)
    f1.writeBytes(r1.data); f2.writeBytes(r2.data)
    throw CliError("mismatch", Msg.t("dump.mismatch", "diff" to diff, "first" to "0x${first.toString(16)}", "crc1" to r1.crcHex, "crc2" to r2.crcHex), EXIT_ERROR,
        hint = Msg.t("dump.mismatch.hint"),
        extra = linkedMapOf("files" to listOf(f1.path, f2.path), "diff_bytes" to diff, "first_diff" to first))
}
