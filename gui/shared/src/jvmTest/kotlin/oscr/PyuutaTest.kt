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

/** Tomy Pyuuta (F-20, D217): sistema 23, tamanhos aceitos e textos. Espelha host/tests/test_pyuuta.py. */
class PyuutaTest {
    @Test fun idEExtensao() {
        assertEquals(23, CartSystem.PYUUTA.id); assertEquals(".bin", CartSystem.PYUUTA.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "pyuuta" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["pyuuta"])
        assertEquals("16", parseArgs(listOf("dump", "-s", "pyuuta", "--prg", "16")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(8, 16, 32)) assertNull(Rules.romSize(CartSystem.PYUUTA, kb), "$kb")
        for (kb in listOf(0, 1, 4, 64)) assertNotNull(Rules.romSize(CartSystem.PYUUTA, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.PYUUTA_HINT, S.V_PYUUTA_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
