// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Interpretação dos argumentos da linha de comando. */
internal class Args(val cmd: String?, val opts: Map<String, String>, val flags: Set<String>, val positional: List<String> = emptyList()) {
    val json get() = "json" in flags
    fun int(name: String): Int {
        val v = opts[name] ?: return 0
        return v.toIntOrNull()?.takeIf { it >= 0 } ?: throw CliError("usage", "--$name needs a non-negative integer, got '$v'", EXIT_USAGE)
    }
}

internal val VALUED = mapOf("p" to "port", "b" to "baud", "s" to "system", "o" to "output", "i" to "input")
internal val LONG_VALUED = setOf("port", "baud", "system", "output", "input", "progress", "lang", "block", "mapper", "prg", "chr", "ram", "backup-dir", "db", "game", "limit", "chip", "begin-timeout", "capacity", "layout", "flash-type", "flash-mb", "sector-kb", "buffer", "block369", "bus", "flash-kb", "color")
internal val FLAGS = setOf("simulate", "no-builtin-db", "json", "yes", "no-backup", "no-verify", "flash-id", "raw", "help", "version")
internal val COMMANDS = setOf("ports", "systems", "errors", "info", "detect", "dump", "save-read", "save-write", "identify", "search", "rom-write", "flash-id", "flash-read", "flash-blank", "flash-erase", "flash-write")
internal val OPTIONS = mapOf("snes" to listOf("prg"), "nes" to listOf("mapper", "prg", "chr", "ram"), "famicom" to listOf("mapper", "prg", "chr", "ram"),
    "md" to listOf("prg"), "gba" to listOf("mapper"), "gb" to emptyList(), "flash" to listOf("bus", "flash-kb", "flash-type", "sector-kb", "buffer"), "mock" to emptyList())

internal fun parseArgs(argv: List<String>): Args {
    var cmd: String? = null
    val opts = linkedMapOf<String, String>(); val flags = linkedSetOf<String>(); val positional = ArrayList<String>()
    var i = 0
    while (i < argv.size) {
        val a = argv[i++]
        when {
            a == "-h" -> flags += "help"
            a.startsWith("--") -> {
                val body = a.substring(2); val eq = body.indexOf('=')
                val name = if (eq >= 0) body.substring(0, eq) else body
                when {
                    name in FLAGS -> { if (eq >= 0) throw CliError("usage", "--$name does not take a value", EXIT_USAGE); flags += name }
                    name in LONG_VALUED -> {
                        val v = if (eq >= 0) body.substring(eq + 1) else argv.getOrNull(i++) ?: throw CliError("usage", "--$name needs a value", EXIT_USAGE)
                        opts[name] = if (name == "db" && name in opts) opts[name] + "\n" + v else v      // --db pode repetir
                    }
                    else -> throw CliError("usage", "unknown option: --$name", EXIT_USAGE)
                }
            }
            a.length == 2 && a[0] == '-' && a[1].toString() in VALUED ->
                opts[VALUED.getValue(a[1].toString())] = argv.getOrNull(i++) ?: throw CliError("usage", "$a needs a value", EXIT_USAGE)
            a.startsWith("-") && a.length > 1 -> throw CliError("usage", "unknown option: $a", EXIT_USAGE)
            cmd == null -> cmd = a
            cmd == "identify" || cmd == "search" -> positional += a
            else -> throw CliError("usage", "unexpected argument: $a", EXIT_USAGE)
        }
    }
    return Args(cmd, opts, flags, positional)
}
