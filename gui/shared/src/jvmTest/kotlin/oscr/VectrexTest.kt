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

/** Vectrex (F-20, D205): sistema 14, tamanhos aceitos e textos. Espelha host/tests/test_vectrex.py. */
class VectrexTest {
    @Test fun idEExtensao() {
        assertEquals(14, CartSystem.VECTREX.id); assertEquals(".vec", CartSystem.VECTREX.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "vectrex" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["vectrex"])
        assertEquals("16", parseArgs(listOf("dump", "-s", "vectrex", "--prg", "16")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(4, 8, 12, 16, 32, 64)) assertNull(Rules.romSize(CartSystem.VECTREX, kb), "$kb")
        for (kb in listOf(0, 2, 20, 128)) assertNotNull(Rules.romSize(CartSystem.VECTREX, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.VECTREX_HINT, S.V_VECTREX_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
