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

/** Watara Supervision (F-20, D218): sistema 24, tamanhos aceitos e textos. Espelha host/tests/test_supervision.py. */
class SupervisionTest {
    @Test fun idEExtensao() {
        assertEquals(24, CartSystem.SUPERVISION.id); assertEquals(".sv", CartSystem.SUPERVISION.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "supervision" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["supervision"])
        assertEquals("64", parseArgs(listOf("dump", "-s", "supervision", "--prg", "64")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(32, 64, 512)) assertNull(Rules.romSize(CartSystem.SUPERVISION, kb), "$kb")
        for (kb in listOf(0, 8, 16, 128)) assertNotNull(Rules.romSize(CartSystem.SUPERVISION, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.SUPERVISION_HINT, S.V_SUPERVISION_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
