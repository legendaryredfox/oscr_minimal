// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comando dump (ROM), com a leitura raw do NES. */
internal fun cmdDump(io: CliIo, a: Args): Int {
    val sys = system(a)
    val db = loadDb(a, required = a.opts["game"] != null)
    var mapper = a.int("mapper"); var prg = a.int("prg"); var chr = a.int("chr")
    a.opts["game"]?.let { q ->
        if (sys != CartSystem.NES && sys != CartSystem.FAMICOM) throw CliError("usage", "--game applies to NES and Famicom only", EXIT_USAGE)
        val g = gameOptions(db!!, q); val o = g.nesOptions()!!
        if (mapper == 0) mapper = o.mapper; if (prg == 0) prg = o.prgKb; if (chr == 0) chr = o.chrKb
        if (!a.json) io.err("database game: ${g.name}  mapper ${o.mapper}  PRG ${o.prgKb} KB  CHR ${o.chrKb} KB  (${g.source})")
    }
    val raw = "raw" in a.flags
    if (raw && sys != CartSystem.NES && sys != CartSystem.FAMICOM) throw CliError("usage", "--raw applies to NES and Famicom only", EXIT_USAGE)
    val c = connect(io, a)
    var title = ""
    if (a.opts["output"] == null) title = try { c.client.detect(sys).name } catch (e: Exception) { if (e is DeviceError || e is ProtocolError || e is TimeoutError) "" else throw e }
    val res = try { c.client.dumpRom(sys, a.int("block"), mapper, prg, chr, progress(io, a, "rom")) } finally { c.transport.close() }
    val ext = if (sys == CartSystem.GB && res.data.size > 0x143 && res.data[0x143].toInt() and 0x80 != 0) ".gbc" else sys.ext
    val chk = verifyRom(sys, res.data)
    val extra = linkedMapOf<String, Any?>("checksum" to chk.status.name.lowercase())
    val notes = mutableListOf<String>()
    if (chk.status != CheckStatus.NA) notes += (if (chk.status == CheckStatus.MISMATCH) "warning: " else "") + "${chk.name} checksum ${chk.status.name.lowercase()} (header ${chk.hex(chk.expected)}, computed ${chk.hex(chk.computed)})"
    if (sys == CartSystem.GBA) {
        val h = gbaSaveHint(res.data)
        if (h != null) { extra["gba_save_type"] = h.type; notes += "GBA save: ${h.tag}, ${h.label}: use --mapper ${h.type} with save-read" }
        else notes += "GBA save: no save library string in the ROM (no save, or unknown type)"
    }
    if (db != null) {
        val m = db.identify(sys, res.data)
        extra["game"] = m?.let { matchJson(it) }
        if (m != null) { title = m.entry.name; notes += "game: ${m.entry.name} (${m.entry.source}, ${m.how.text}" + (if (m.others > 0) ", ${m.others} identical more" else "") + ")" }
        else notes += "game: not found in the database (${db.size} entries): new dump, variant, or a read error if the CRC32 should be there"
    }
    if (raw) saveNesRaw(io, a, res, safeName(title, "rom_${sys.name.lowercase()}"), extra, notes)
    else saveResult(io, a, res, ext, safeName(title, "rom_${sys.name.lowercase()}"), extra, notes)
    return EXIT_OK
}

/** --raw (NES/Famicom): PRG e CHR em arquivos separados (.prg e .chr), sem cabeçalho iNES — a leitura "raw" do OSCR. */
internal fun saveNesRaw(io: CliIo, a: Args, res: DumpResult, default: String, extra: Map<String, Any?>, notes: List<String>) {
    val parts = splitInesRaw(res.data) ?: throw CliError("protocol", "--raw: the firmware did not return a usable iNES header to split PRG and CHR", EXIT_ERROR)
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
    } else lines += "no CHR-ROM (the cartridge uses CHR-RAM)"
    lines += "full iNES (PRG + CHR with header): CRC32 ${res.crcHex}"
    obj.putAll(extra)
    emit(io, a, obj, lines + notes)
}
