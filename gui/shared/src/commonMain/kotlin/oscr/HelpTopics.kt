// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Tópicos da ajuda e a busca neles. A busca ignora maiúsculas e acentos e exige todas as palavras (igual em todos os idiomas). */
object HelpTopics {
    val use = listOf(S.HELP_USE_1, S.HELP_USE_2, S.HELP_USE_3, S.HELP_USE_4, S.HELP_USE_5, S.HELP_USE_6)
    val fix = listOf(S.HELP_FIX_1, S.HELP_FIX_2, S.HELP_FIX_3, S.HELP_FIX_4, S.HELP_FIX_5, S.HELP_FIX_6, S.HELP_FIX_7, S.HELP_FIX_8)

    private const val ACCENTED = "áàâãäåéèêëíìîïóòôõöúùûüçñýÿ"
    private const val PLAIN = "aaaaaaeeeeiiiiooooouuuucnyy"

    /** Minúsculas e sem acentos latinos (cirílico e chinês só passam para minúsculas). */
    fun fold(s: String): String = buildString(s.length) {
        for (ch in s.lowercase()) { val i = ACCENTED.indexOf(ch); append(if (i >= 0) PLAIN[i] else ch) }
    }

    /** Todas as palavras da busca (separadas por espaço) aparecem no texto. Busca vazia casa com tudo. */
    fun matches(text: String, query: String): Boolean {
        val words = fold(query).split(' ', '\t').filter { it.isNotEmpty() }
        if (words.isEmpty()) return true
        val hay = fold(text)
        return words.all { it in hay }
    }

    /** Os tópicos de [keys] que casam com [query], no idioma [lang]. */
    fun filter(lang: Lang, keys: List<S>, query: String): List<S> = keys.filter { matches(I18n.t(lang, it), query) }
}
