// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.Lang

/**
 * Mensagens da CLI Kotlin em vários idiomas (D133). O catálogo é o mesmo da CLI Python: `oscr/cli-messages.tsv`, gerado por
 * `tools/gen_cli_messages.py` a partir de `host/oscr_host/cli/messages.py` (uma só fonte, sem copiar texto à mão).
 * Idioma: `--lang`, senão OSCR_LANG, LC_ALL, LC_MESSAGES, LANG; sem nada reconhecível, inglês (reserva).
 * O que **não** muda: as chaves do `--json`, os valores de `kind` e os códigos de saída.
 */
object Msg {
    /** Idioma da execução atual (a CLI roda uma coisa por vez; `Cli.run` ajusta no começo). */
    @Volatile var lang: Lang = Lang.EN

    private val table: Map<String, Map<Lang, String>> by lazy { load() }

    private fun load(): Map<String, Map<Lang, String>> {
        val text = Msg::class.java.classLoader.getResourceAsStream("oscr/cli-messages.tsv")?.use { it.readBytes().toString(Charsets.UTF_8) } ?: return emptyMap()
        val order = listOf(Lang.PT, Lang.EN, Lang.RU, Lang.ZH)
        val out = HashMap<String, Map<Lang, String>>()
        for (line in text.lineSequence()) {
            if (line.isBlank() || line.startsWith("#")) continue
            val cells = line.split('\t')
            if (cells.size != 1 + order.size) continue
            out[cells[0]] = order.mapIndexed { i, l -> l to cells[i + 1] }.toMap()
        }
        return out
    }

    fun keys(): Set<String> = table.keys
    fun row(key: String): Map<Lang, String>? = table[key]

    /** Texto da chave no idioma atual (ou em inglês), com `{campo}` e `{campo:04X}` trocados pelos argumentos. */
    fun t(key: String, vararg args: Pair<String, Any?>): String = tIn(lang, key, *args)

    fun tIn(l: Lang, key: String, vararg args: Pair<String, Any?>): String {
        val row = table[key] ?: return key
        val text = (row[l] ?: row.getValue(Lang.EN)).let { if (key == "usage.text") it.replace("\\n", "\n") else it }
        return FIELD.replace(text) { m ->
            val v = args.firstOrNull { it.first == m.groupValues[1] }?.second
            val spec = m.groupValues[2]
            when {
                v == null -> m.value
                spec == "04X" && v is Number -> v.toLong().toString(16).uppercase().padStart(4, '0')
                else -> v.toString()
            }
        }
    }

    private val FIELD = Regex("""\{(\w+)(?::([^}]*))?\}""")

    /** 'pt_BR.UTF-8' -> PT; 'en_US' -> EN; 'zh' / 'zh-CN' -> ZH; desconhecido -> null. */
    fun parse(tag: String?): Lang? {
        if (tag.isNullOrBlank()) return null
        val t = tag.substringBefore('.').substringBefore('@').replace('_', '-')
        return Lang.entries.firstOrNull { it.tag.equals(t, true) } ?: Lang.entries.firstOrNull { it.tag.substringBefore('-').equals(t.substringBefore('-'), true) }
    }

    /** `--lang` (antes ou depois do comando), senão a primeira variável de ambiente reconhecível, senão inglês. */
    fun detect(argv: List<String>, env: (String) -> String?): Lang {
        for ((i, a) in argv.withIndex()) {
            if (a == "--lang" && i + 1 < argv.size) return parse(argv[i + 1]) ?: Lang.EN
            if (a.startsWith("--lang=")) return parse(a.substringAfter('=')) ?: Lang.EN
        }
        for (v in listOf("OSCR_LANG", "LC_ALL", "LC_MESSAGES", "LANG")) parse(env(v))?.let { return it }
        return Lang.EN
    }
}
