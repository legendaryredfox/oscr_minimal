// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class I18nTest {
    @Test fun todosOsIdiomasTemTodasAsChaves() {
        for (lang in Lang.entries) for (k in S.entries) {
            val txt = I18n.t(lang, k)
            assertTrue(txt.isNotBlank(), "faltou $k em $lang")
        }
    }

    @Test fun portuguesEDiferenteDeIngles() {
        assertEquals("Ler ROM", I18n.t(Lang.PT, S.DUMP_ROM))
        assertEquals("Dump ROM", I18n.t(Lang.EN, S.DUMP_ROM))
    }

    @Test fun idiomaPadraoVemDoLocale() {
        assertEquals(Lang.PT, I18n.fromLocale("pt_BR")); assertEquals(Lang.EN, I18n.fromLocale("de_DE"))
        assertEquals(Lang.RU, I18n.fromLocale("ru_RU")); assertEquals(Lang.ZH, I18n.fromLocale("zh_CN"))
    }

    @Test fun russoEChinesTraduzidos() {
        assertEquals("Прочитать ROM", I18n.t(Lang.RU, S.DUMP_ROM)); assertEquals("读取 ROM", I18n.t(Lang.ZH, S.DUMP_ROM))
        for (k in S.entries) { // nenhuma tradução pode ficar igual ao inglês, salvo siglas
            if (k in setOf(S.ROM_LABEL, S.BAUD, S.MAPPER, S.PRG_KB, S.CHR_KB)) continue  // siglas iguais em todos os idiomas
            assertTrue(I18n.t(Lang.RU, k) != I18n.t(Lang.EN, k) && I18n.t(Lang.ZH, k) != I18n.t(Lang.EN, k), "sem tradução: $k")
        }
    }

    @Test fun ajudaTemTodosOsTopicos() {
        for (lang in Lang.entries) for (k in S.entries.filter { it.name.startsWith("HELP_") }) assertTrue(I18n.t(lang, k).length >= 2, "$k $lang")
    }
}
