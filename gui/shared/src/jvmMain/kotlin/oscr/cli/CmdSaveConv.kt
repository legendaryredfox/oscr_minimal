// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File

/** Comando save-convert: troca a ordem dos bytes de um save para emulador (H-1, D163). Não abre o dispositivo. */
internal fun cmdSaveConv(io: CliIo, a: Args): Int {
    val input = a.opts["input"] ?: throw CliError("usage", Msg.t("args.needs_input", "cmd" to "save-convert"), EXIT_USAGE)
    val op = a.opts["op"] ?: throw CliError("usage", Msg.t("saveconv.op"), EXIT_USAGE)
    if (op !in SaveConv.OPS) throw CliError("usage", Msg.t("saveconv.op"), EXIT_USAGE)
    val fillText = a.opts["fill"] ?: "0xFF"
    val fill = (if (fillText.startsWith("0x", true)) fillText.substring(2).toIntOrNull(16) else fillText.toIntOrNull()) ?: -1
    if (fill !in 0..255) throw CliError("usage", Msg.t("saveconv.fill"), EXIT_USAGE)
    val src = File(input); val data = src.readBytes()
    val converted = try { SaveConv.convert(data, op, fill) } catch (e: IllegalArgumentException) { throw CliError("bad_save", Msg.t("saveconv.bad_size", "size" to data.size, "op" to op), EXIT_ERROR) }
    val out = File(a.opts["output"] ?: (src.parentFile?.path?.let { "$it/" } ?: "") + src.nameWithoutExtension + "_" + op + (if (src.extension.isEmpty()) "" else "." + src.extension))
    out.writeBytes(converted)
    emit(io, a, linkedMapOf("input" to src.path, "output" to out.path, "op" to op, "in_bytes" to data.size, "out_bytes" to converted.size),
        listOf(Msg.t("saveconv.done", "op" to op, "n" to converted.size, "out" to out.path)))
    return EXIT_OK
}
