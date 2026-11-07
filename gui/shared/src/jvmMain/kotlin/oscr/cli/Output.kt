// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/** Saída dos comandos: JSON ou texto, progresso, nome e gravação de arquivo, erros. */
/** Cor/arte nesta execução: --color always|never manda; no auto vale o terminal. `--json` nunca tem enfeite. */
internal fun colorOn(io: CliIo, a: Args): Boolean = Ui.on(a.opts["color"], io.stdoutTty, a.json)

internal fun fail(io: CliIo, json: Boolean, e: CliError, colorMode: String? = null): Int {
    if (json) {
        val err = linkedMapOf<String, Any?>("kind" to e.kind, "message" to e.message)
        e.hint?.let { err["hint"] = it }
        err.putAll(e.extra)
        io.out(Json.encode(Json.obj("ok" to false, "error" to err)))
    } else if (Ui.on(colorMode, io.stderrTty, false)) io.err(Ui.errorLine(true, e.message, e.hint))
    else io.err("error: ${e.message}" + (e.hint?.let { ". Hint: $it" } ?: ""))
    return e.exit
}

internal fun emit(io: CliIo, a: Args, obj: Map<String, Any?>, lines: List<String>) {
    if (a.json) io.out(Json.encode(if ("ok" in obj) obj else linkedMapOf<String, Any?>("ok" to true) + obj)) else { val on = colorOn(io, a); lines.forEach { io.out(Ui.decorate(on, it)) } }
}

internal fun progress(io: CliIo, a: Args, label: String): Progress {
    val mode = a.opts["progress"] ?: "auto"
    var last = -1
    val line = Ui.ProgressLine(label)
    return { done, total ->
        if (mode != "none" && total > 0) {
            val pct = (done * 100 / total).toInt()
            if (pct != last) {
                last = pct
                if (mode == "jsonl") io.err(Json.encode(Json.obj("event" to "progress", "label" to label, "done" to done, "total" to total, "percent" to pct)))
                else if (io.stderrTty) {
                    if (Ui.on(a.opts["color"], true, false)) System.err.print(line.render(true, done, total) + if (done >= total) "\n" else "")      // barra com degradê, velocidade e tempo restante
                    else System.err.print("\r$label: ${pct.toString().padStart(3)}%  ($done/$total bytes)" + if (done >= total) "\n" else "")
                }
            }
        }
    }
}

internal fun outPath(a: Args, ext: String, default: String): File {
    val f = File(a.opts["output"] ?: default)
    return if (f.name.lastIndexOf('.') <= 0) File(f.path + ext) else f
}

internal fun safeName(title: String, default: String): String =
    title.replace(Regex("[^A-Za-z0-9._ -]+"), "_").trim(' ', '.', '_').ifEmpty { default }

internal fun saveResult(io: CliIo, a: Args, res: DumpResult, ext: String, default: String, extra: Map<String, Any?> = emptyMap(), notes: List<String> = emptyList()) {
    val f = outPath(a, ext, default)
    f.absoluteFile.parentFile?.mkdirs()
    f.writeBytes(res.data)
    val obj = linkedMapOf<String, Any?>("file" to f.path, "bytes" to res.data.size, "crc32" to res.crcHex) + extra
    emit(io, a, obj, listOf("${f.path}  ${res.data.size} bytes  CRC32 ${res.crcHex}") + notes)
}

internal fun hex8(v: Int) = (v.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')

/** (bytes diferentes, deslocamento do primeiro). Tamanhos diferentes contam o excesso; sem diferença nos bytes comuns, o primeiro é o fim do menor. Iguais: (0, -1). */
internal fun diffSummary(a: ByteArray, b: ByteArray): Pair<Int, Int> {
    val n = minOf(a.size, b.size)
    var count = 0; var first = -1
    for (i in 0 until n) if (a[i] != b[i]) { count++; if (first < 0) first = i }
    if (a.size != b.size && first < 0) first = n
    return (count + kotlin.math.abs(a.size - b.size)) to first
}
