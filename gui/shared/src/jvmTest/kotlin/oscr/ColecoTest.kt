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

/** ColecoVision (F-20, D201): sistema 12, tamanhos aceitos e textos. Espelha host/tests/test_coleco.py. */
class ColecoTest {
    @Test fun idEExtensao() {
        assertEquals(12, CartSystem.COLECO.id); assertEquals(".col", CartSystem.COLECO.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "coleco" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["coleco"])
        assertEquals("16", parseArgs(listOf("dump", "-s", "coleco", "--prg", "16")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(8, 12, 16, 20, 24, 32)) assertNull(Rules.romSize(CartSystem.COLECO, kb), "$kb")
        for (kb in listOf(0, 4, 10, 28, 64, 1024)) assertNotNull(Rules.romSize(CartSystem.COLECO, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.COLECO_HINT, S.V_COLECO_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
