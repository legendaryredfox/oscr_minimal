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

/** Bally Astrocade (F-20, D223): sistema 26, tamanhos aceitos e textos. Espelha host/tests/test_astrocade.py. */
class AstrocadeTest {
    @Test fun idEExtensao() {
        assertEquals(26, CartSystem.ASTROCADE.id); assertEquals(".bin", CartSystem.ASTROCADE.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "astrocade" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["astrocade"])
        assertEquals("8", parseArgs(listOf("dump", "-s", "astrocade", "--prg", "8")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(2, 4, 8)) assertNull(Rules.romSize(CartSystem.ASTROCADE, kb), "$kb")
        for (kb in listOf(0, 1, 3, 16, 32)) assertNotNull(Rules.romSize(CartSystem.ASTROCADE, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.ASTROCADE_HINT, S.V_ASTROCADE_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
