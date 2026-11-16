// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Padrões das duas passadas do `eraseSRAM` do OSCR (F-10, D178). */
internal val RAM_TEST_PATTERNS = listOf(0x0F, 0xF0)

/**
 * Comando ram-test: o "Test RAM" do SNES do OSCR. Lê o save e o guarda, sobrescreve a SRAM inteira com 0x0F e 0xF0, grava o save de volta e confere lendo.
 * Se qualquer passo falha depois do backup, ainda tenta restaurar o save. Igual a cmd_ram_test em cmd_ramtest.py.
 */
internal fun cmdRamTest(io: CliIo, a: Args): Int {
    val sys = if (a.opts["system"] != null) system(a) else CartSystem.SNES
    if (sys != CartSystem.SNES) throw CliError("usage", Msg.t("ramtest.only_snes"), EXIT_USAGE)
    if ("yes" !in a.flags) {
        if (!io.interactive) throw CliError("refused", Msg.t("refused.ramtest"), EXIT_REFUSED, Msg.t("refused.repeat"))
        io.err(Msg.t("ramtest.ask"))
        if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) { io.out(Msg.t("cancelled")); return EXIT_ERROR }
    }
    val c = connect(io, a.withOpt("system", "snes"))
    val timeout = ((a.opts["begin-timeout"]?.toDoubleOrNull() ?: 90.0) * 1000).toLong()
    var failure: Throwable? = null
    val saved: DumpResult
    val backup: File
    val v: VerifyResult
    try {
        if (!c.info.flashProg) throw CliError("unsupported_firmware", Msg.t("fw.unsupported_erase"), EXIT_ERROR, Msg.t("fw.unsupported.hint"))
        saved = c.client.readSave(sys, a.int("block"), 0, 0, progress(io, a, "backup"), 0)
        val dir = File((a.opts["backup-dir"] ?: "~/oscr_backups").let { if (it.startsWith("~")) io.home + it.substring(1) else it })
        dir.mkdirs()
        backup = File(dir, "snes_ramtest_${LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss"))}.sav")
        backup.writeBytes(saved.data)
        if (!a.json) io.out(Msg.t("save.backup", "path" to backup.path, "crc" to saved.crcHex))
        try { for (p in RAM_TEST_PATTERNS) c.client.erase(sys, p, 0, 0, timeout) }
        catch (e: Exception) { failure = e }                          // a SRAM pode ter ficado pela metade: restaura de qualquer jeito, depois repassa o erro
        c.client.writeSave(sys, saved.data, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, 0, 0, progress(io, a, "restore"), 0)
        v = verifySaveWritten(c.client, sys, saved.data, 0, 0, progress(io, a, "verify"), 0)
    } finally { c.transport.close() }
    failure?.let { throw it }
    val vj = Json.obj("ok" to v.ok, "read_crc32" to hex8(v.readCrc), "expected_crc32" to hex8(v.expectedCrc), "first_diff" to v.firstDiff, "read_bytes" to v.readBytes)
    val out = linkedMapOf<String, Any?>("ok" to v.ok, "bytes" to saved.data.size, "crc32" to saved.crcHex, "patterns" to RAM_TEST_PATTERNS, "backup" to backup.path, "verify" to vj)
    if (!v.ok) throw CliError("verify_failed", Msg.t("ramtest.verify_failed", "first" to v.firstDiff, "read" to hex8(v.readCrc), "exp" to hex8(v.expectedCrc)),
        EXIT_ERROR, Msg.t("ramtest.verify_failed.hint"), mapOf("written" to out, "first_diff" to v.firstDiff))
    emit(io, a, out, listOf(Msg.t("ramtest.ok", "n" to saved.data.size, "crc" to saved.crcHex)))
    return EXIT_OK
}
