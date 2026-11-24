// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import oscr.cli.OPTIONS
import oscr.cli.parseArgs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Emerson Arcadia 2001 (F-20, D215): sistema 21, tamanhos aceitos e textos. Espelha host/tests/test_arcadia.py. */
class ArcadiaTest {
    @Test fun idEExtensao() {
        assertEquals(21, CartSystem.ARCADIA.id); assertEquals(".bin", CartSystem.ARCADIA.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "arcadia" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["arcadia"])
        assertEquals("4", parseArgs(listOf("dump", "-s", "arcadia", "--prg", "4")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(2, 4, 6, 8)) assertNull(Rules.romSize(CartSystem.ARCADIA, kb), "$kb")
        for (kb in listOf(0, 1, 3, 16)) assertNotNull(Rules.romSize(CartSystem.ARCADIA, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.ARCADIA_HINT, S.V_ARCADIA_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
