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

/** RCA Studio II (F-20, D216): sistema 22, tamanhos aceitos e textos. Espelha host/tests/test_rca2.py. */
class Rca2Test {
    @Test fun idEExtensao() {
        assertEquals(22, CartSystem.RCA2.id); assertEquals(".bin", CartSystem.RCA2.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "rca2" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["rca2"])
        assertEquals("1", parseArgs(listOf("dump", "-s", "rca2", "--prg", "1")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        assertNull(Rules.romSize(CartSystem.RCA2, 1))
        for (kb in listOf(0, 2, 4, 8, 16)) assertNotNull(Rules.romSize(CartSystem.RCA2, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.RCA2_HINT, S.V_RCA2_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
