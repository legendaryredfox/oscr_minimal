// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

/** Gerador mínimo de JSON (sem dependências): String, Number, Boolean, null, List e Map (ordem preservada). */
object Json {
    fun encode(v: Any?): String = StringBuilder().also { write(it, v) }.toString()

    fun obj(vararg pairs: Pair<String, Any?>): Map<String, Any?> = linkedMapOf(*pairs)

    private fun write(sb: StringBuilder, v: Any?) {
        when (v) {
            null -> sb.append("null")
            is Boolean, is Int, is Long -> sb.append(v.toString())
            is Number -> sb.append(v.toString())
            is Map<*, *> -> {
                sb.append('{'); var first = true
                for ((k, x) in v) { if (!first) sb.append(','); first = false; str(sb, k.toString()); sb.append(':'); write(sb, x) }
                sb.append('}')
            }
            is Iterable<*> -> {
                sb.append('['); var first = true
                for (x in v) { if (!first) sb.append(','); first = false; write(sb, x) }
                sb.append(']')
            }
            else -> str(sb, v.toString())
        }
    }

    private fun str(sb: StringBuilder, s: String) {
        sb.append('"')
        for (c in s) when {
            c == '"' -> sb.append("\\\"")
            c == '\\' -> sb.append("\\\\")
            c == '\n' -> sb.append("\\n")
            c == '\r' -> sb.append("\\r")
            c == '\t' -> sb.append("\\t")
            c < ' ' -> sb.append("\\u").append(c.code.toString(16).padStart(4, '0'))
            else -> sb.append(c)
        }
        sb.append('"')
    }
}
