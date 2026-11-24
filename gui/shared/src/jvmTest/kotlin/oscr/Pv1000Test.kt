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

/** Casio PV-1000 (F-20, D219): sistema 25, tamanhos aceitos e textos. Espelha host/tests/test_pv1000.py. */
class Pv1000Test {
    @Test fun idEExtensao() {
        assertEquals(25, CartSystem.PV1000.id); assertEquals(".bin", CartSystem.PV1000.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "pv1000" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["pv1000"])
        assertEquals("16", parseArgs(listOf("dump", "-s", "pv1000", "--prg", "16")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(8, 16)) assertNull(Rules.romSize(CartSystem.PV1000, kb), "$kb")
        for (kb in listOf(0, 1, 4, 32, 64)) assertNotNull(Rules.romSize(CartSystem.PV1000, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.PV1000_HINT, S.V_PV1000_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
