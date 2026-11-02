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
    }
}
