// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

/**
 * Cores, barra de progresso, banner e arte ASCII da CLI. Igual a host/oscr_host/cli/ui.py.
 * Só aparecem num terminal (ou com `--color always`); com `--json`, saída redirecionada, NO_COLOR ou `--color never`
 * a CLI continua em texto puro, como os scripts e os agentes esperam (docs/cli.md).
 */
internal object Ui {
    private const val RESET = "\u001b[0m"
    private val CODES = mapOf("bold" to "1", "dim" to "2", "red" to "31", "green" to "32", "yellow" to "33", "magenta" to "35", "cyan" to "36", "gray" to "90")
    private val ANSI = Regex("\u001b\\[[0-9;]*m")
    private val unicode = java.nio.charset.Charset.defaultCharset().name().startsWith("UTF", ignoreCase = true)

    /** Cor ligada? --color always/never mandam; no auto vale o terminal (tty) e NO_COLOR. `--json` nunca tem enfeite. */
    fun on(mode: String?, tty: Boolean, json: Boolean): Boolean = when {
        json -> false
        mode == "always" -> true
        mode == "never" || System.getenv("NO_COLOR") != null -> false
        else -> tty && System.getenv("TERM") != "dumb"
    }

    fun paint(on: Boolean, text: String, vararg styles: String): String =
        if (!on || styles.isEmpty()) text else "\u001b[" + styles.joinToString(";") { CODES.getValue(it) } + "m" + text + RESET

    fun c256(on: Boolean, text: String, n: Int): String = if (on) "\u001b[38;5;${n}m$text$RESET" else text

    fun icon(on: Boolean, kind: String): String {
        val (sym, plain, col) = when (kind) {
            "ok" -> Triple("✔", "[OK]", "green"); "err" -> Triple("✘", "[ERROR]", "red"); "warn" -> Triple("⚠", "[!]", "yellow"); else -> Triple("ℹ", "[i]", "cyan")
        }
        return paint(on, if (unicode) sym else plain, col, "bold")
    }

    private val GRADIENT = intArrayOf(196, 202, 208, 214, 220, 226, 190, 154, 118, 82, 46)      // vermelho -> amarelo -> verde

    fun bar(on: Boolean, fraction: Double, width: Int = 28): String {
        val f = fraction.coerceIn(0.0, 1.0)
        val (full, empty) = if (unicode) "█" to "░" else "#" to "-"
        val n = Math.round(f * width).toInt()
        if (!on) return "[" + full.repeat(n) + empty.repeat(width - n) + "]"
        val cells = (0 until n).joinToString("") { c256(true, full, GRADIENT[minOf(GRADIENT.size - 1, it * GRADIENT.size / width)]) }
        return "[" + cells + paint(true, empty.repeat(width - n), "gray") + "]"
    }

    fun humanBytes(n: Double): String {
        var v = n
        for (u in listOf("B", "KB", "MB")) { if (v < 1024) return if (u == "B") "%.0f %s".format(java.util.Locale.ROOT, v, u) else "%.1f %s".format(java.util.Locale.ROOT, v, u); v /= 1024 }
        return "%.1f GB".format(java.util.Locale.ROOT, v)
    }

    /** Linha de progresso em stderr: giro, rótulo, barra, porcentagem, velocidade e tempo restante. */
    class ProgressLine(private val label: String) {
        private val start = System.nanoTime()
        private var frame = 0
        fun render(on: Boolean, done: Long, total: Long): String {
            val frac = if (total > 0) done.toDouble() / total else 0.0
            val el = maxOf((System.nanoTime() - start) / 1e9, 1e-6)
            val rate = done / el
            val eta = if (rate > 0 && done < total && el > 1.0) "  ETA ${((total - done) / rate).toInt()}s" else ""
            val spin = if (unicode) "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" else "|/-\\"
            frame++
            val sp = if (done < total) paint(on, spin[frame % spin.length].toString(), "cyan") else icon(on, "ok")
            return "\r$sp ${paint(on, label.padEnd(14), "bold")} ${bar(on, frac)} ${"%3d".format((frac * 100).toInt())}%  ${humanBytes(done.toDouble())}/${humanBytes(total.toDouble())}  " +
                paint(on, humanBytes(rate) + "/s", "dim") + eta + "\u001b[K"
        }
    }

    private val RULES: List<Pair<Regex, (MatchResult, Boolean) -> String>> = listOf(
        Regex("\\b(CRC32 )([0-9A-Fa-f]{8})\\b") to { m, on -> m.groupValues[1] + paint(on, m.groupValues[2], "cyan", "bold") },
        Regex("\\b(OK)\\b") to { m, on -> paint(on, m.groupValues[1], "green", "bold") },
        Regex("(does NOT match|NOT match)") to { m, on -> paint(on, m.groupValues[1], "red", "bold") },
        Regex("(\\d[\\d.,]*)( bytes| KB| MB)") to { m, on -> paint(on, m.groupValues[1], "bold") + m.groupValues[2] },
    )

    /** Realça uma linha de saída humana (ícone no começo, CRC32 em ciano, OK em verde, avisos em amarelo). */
    fun decorate(on: Boolean, line: String): String {
        if (!on) return line
        val low = line.trimStart().lowercase()
        if (low.startsWith("warning") || low.startsWith("aviso")) return icon(true, "warn") + " " + paint(true, line, "yellow")
        val prefix = if (low.startsWith("rom written") || low.startsWith("save written") || (low.contains("verif") && Regex("\\bOK\\b").containsMatchIn(line))) icon(true, "ok") + " " else ""
        var out = line
        for ((rx, fn) in RULES) out = rx.replace(out) { fn(it, true) }
        return prefix + out
    }

    fun errorLine(on: Boolean, message: String, hint: String?): String {
        var s = icon(on, "err") + " " + paint(on, "error:", "red", "bold") + " " + message
        if (hint != null) s += "\n  " + icon(on, "info") + " " + paint(on, "hint: $hint", "yellow")
        return s
    }

    private val GLYPHS = mapOf(
        'O' to listOf("  ___  ", " / _ \\ ", "| | | |", "| |_| |", " \\___/ "),
        'S' to listOf(" ____  ", "/ ___| ", "\\___ \\ ", " ___) |", "|____/ "),
        'C' to listOf("  ____ ", " / ___|", "| |    ", "| |___ ", " \\____|"),
        'R' to listOf(" ____  ", "|  _ \\ ", "| |_) |", "|  _ < ", "|_| \\_\\"),
    )
    private val BANNER_COLORS = intArrayOf(51, 45, 39, 33, 99)        // ciano -> azul -> violeta

    fun logo(): List<String> = (0 until 5).map { r -> "OSCR".map { GLYPHS.getValue(it)[r] }.joinToString("") }

    fun banner(on: Boolean, version: String): String {
        val rows = logo().mapIndexed { i, l -> "  " + c256(on, l, BANNER_COLORS[i]) }.toMutableList()
        rows += "  " + paint(on, "minimal", "bold", "magenta") + paint(on, "  v$version", "dim") + paint(on, "  -  cartridge dumper over USB", "dim")
        val names = listOf("SNES", "NES", "Famicom", "Mega Drive", "GB", "GBC", "GBA"); val cols = intArrayOf(196, 208, 220, 82, 45, 99, 171)
        rows += "  " + names.indices.joinToString(paint(on, if (unicode) " · " else " | ", "gray")) { c256(on, names[it], cols[it]) }
        return rows.joinToString("\n")
    }

    // Cartuchos: o rótulo ({label}) é centralizado numa área de largura fixa, então todas as linhas têm o mesmo tamanho.
    private val ART = mapOf(
        1 to listOf("  .--------------------.  ", "  | .----------------. |  ", "  | |{label}| |  ", "  | '----------------' |  ", "  '--.              .--'  ", "     |::::::::::::::|     ", "     '--------------'     "),
        2 to listOf("   .------------------.   ", "   |  ______________  |   ", "   | |{label}| |   ", "   | |______________| |   ", "   |  o            o  |   ", "   '--.----------.----'   ", "      ||||||||||||||      "),
        3 to listOf("   .------------------.   ", "   | .--------------. |   ", "   | |{label}| |   ", "   | '--------------' |   ", "   |  o            o  |   ", "   '--.----------.----'   ", "      ||||||||||||||      "),
        4 to listOf(" .----------------------. ", " | //  //  //  //  //   | ", " | ==================== | ", " | |{label}| | ", " | ==================== | ", " '--.              .----' ", "     ||||||||||||||||     "),
        5 to listOf("    _________________    ", "   /  _____________  \\   ", "  |  |{label}|  |  ", "  |  |_____________|  |  ", "  |___.           .___|  ", "      ||||||||||||       "),
        6 to listOf("   ________________   ", "  |  ____________  \\  ", "  | |{label}|  | ", "  | |____________|  | ", "  |   o   o   o     | ", "  |__________________|", "     ||||||||||||     "),
    )
    private val ART_WIDTH = mapOf(1 to 16, 2 to 14, 3 to 14, 4 to 18, 5 to 13, 6 to 12)
    private val ART_LABEL = mapOf(1 to "S N E S", 2 to "N E S", 3 to "FAMICOM", 4 to "MEGA DRIVE", 5 to "G B A", 6 to "GAME BOY")
    private val ART_COLOR = mapOf(1 to 141, 2 to 203, 3 to 215, 4 to 75, 5 to 134, 6 to 108)

    /** Desenho do cartucho (1 SNES, 2 NES, 3 Famicom, 4 Mega Drive, 5 GBA, 6 GB/GBC); outro valor usa o do SNES. */
    fun cartridge(on: Boolean, system: Int): List<String> {
        val kind = if (system in ART) system else 1
        val label = ART_LABEL.getValue(kind).let { l -> val w = ART_WIDTH.getValue(kind); val pad = w - l.length; " ".repeat(pad / 2) + l + " ".repeat(pad - pad / 2) }
        val rows = ART.getValue(kind).map { it.replace("{label}", label) }
        val width = rows.maxOf { it.length }
        return rows.map { c256(on, it.padEnd(width), ART_COLOR.getValue(kind)) }
    }

    /** Cartucho ao lado dos dados do `detect`. */
    fun detectCard(on: Boolean, system: Int, statusText: String, ok: Boolean, fields: List<Pair<String, String>>): List<String> {
        val left = cartridge(on, system)
        val right = mutableListOf((if (ok) icon(on, "ok") else icon(on, "err")) + " " + paint(on, statusText, "bold"))
        fields.forEach { (k, v) -> right += "  ${paint(on, "$k:", "gray")} ${paint(on, v, "bold")}" }
        val width = left.maxOf { ANSI.replace(it, "").length }
        return (0 until maxOf(left.size, right.size)).map { i ->
            val l = left.getOrElse(i) { "" }
            l + " ".repeat(width - ANSI.replace(l, "").length + 2) + right.getOrElse(i) { "" }
        }
    }
}
