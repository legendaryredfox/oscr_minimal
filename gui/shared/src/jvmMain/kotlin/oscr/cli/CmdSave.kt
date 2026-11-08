// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Comandos save-read e save-write. */
internal fun cmdSaveRead(io: CliIo, a: Args): Int {
    val c = connect(io, a); val sys = system(a)
    val res = try { c.client.readSave(sys, a.int("block"), a.int("mapper"), a.int("ram"), progress(io, a, "save")) } finally { c.transport.close() }
    saveResult(io, a, res, ".sav", "save_${sys.name.lowercase()}")
    return EXIT_OK
}

internal fun cmdSaveWrite(io: CliIo, a: Args): Int {
    val input = a.opts["input"] ?: throw CliError("usage", Msg.t("args.needs_input", "cmd" to "save-write"), EXIT_USAGE)
    val data = File(input).readBytes()
    val sys = system(a)
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", Msg.t("refused.save"), EXIT_REFUSED, Msg.t("refused.save.hint"))
        io.err(Msg.t("save.ask", "n" to data.size, "system" to sys.name.lowercase()))
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) { io.out(Msg.t("cancelled")); return EXIT_ERROR }
    }
    val c = connect(io, a)
    val extra = linkedMapOf<String, Any?>()
    val crc: Int
    var v: VerifyResult? = null
    try {
        if ("no-backup" !in a.flags) {
            val cur = c.client.readSave(sys, a.int("block"), a.int("mapper"), a.int("ram"), progress(io, a, "backup"))
            val dir = File((a.opts["backup-dir"] ?: "~/oscr_backups").let { if (it.startsWith("~")) io.home + it.substring(1) else it })
            dir.mkdirs()
            val f = File(dir, "${sys.name.lowercase()}_${LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss"))}.sav")
            f.writeBytes(cur.data)
            extra["backup"] = f.path
            if (!a.json) io.out(Msg.t("save.backup", "path" to f.path, "crc" to cur.crcHex))
        }
        crc = c.client.writeSave(sys, data, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, a.int("mapper"), a.int("ram"), progress(io, a, "write"))
        if ("no-verify" !in a.flags) v = verifySaveWritten(c.client, sys, data, a.int("mapper"), a.int("ram"), progress(io, a, "verify"))     // o WRITE_SAVE não relê: o PC lê de volta e compara
    } finally { c.transport.close() }
    val hex = (crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
    extra["bytes"] = data.size; extra["crc32"] = hex
    val lines = mutableListOf(Msg.t("save.written", "n" to data.size, "crc" to hex))
    if (v == null) { extra["verify"] = "skipped"; lines += Msg.t("verify.skipped_flag") }
    else {
        extra["verify"] = Json.obj("ok" to v.ok, "read_crc32" to hex8(v.readCrc), "expected_crc32" to hex8(v.expectedCrc), "first_diff" to v.firstDiff, "read_bytes" to v.readBytes)
        if (!v.ok) throw CliError("verify_failed", Msg.t("save.verify_failed", "first" to v.firstDiff, "read" to hex8(v.readCrc), "exp" to hex8(v.expectedCrc), "n" to v.readBytes, "total" to data.size),
            EXIT_ERROR, Msg.t("save.verify_failed.hint"), mapOf("written" to extra, "first_diff" to v.firstDiff))
        lines += Msg.t("verify.ok", "n" to v.readBytes, "crc" to hex8(v.readCrc))
    }
    emit(io, a, extra, lines)
    return EXIT_OK
}
