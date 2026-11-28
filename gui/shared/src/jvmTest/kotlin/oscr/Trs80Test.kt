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

/** TRS-80 Color Computer (F-20, D248): sistema 32, tamanho em KB (2 a 128), com adaptador, fora dos planejados, aviso nos 4 idiomas. Espelha host/tests/test_trs80.py e pc-tests/test_trs.cpp. */
class Trs80Test {
    @Test fun idEExtensao() {
        assertEquals(32, CartSystem.TRS80.id); assertEquals(".ccc", CartSystem.TRS80.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
        assertTrue(CartSystem.entries.filter { it != CartSystem.MOCK }.all { it.id <= 63 })   // máscara `systems()` de 64 bits (D232)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "trs80" })
    }

    @Test fun opcaoDeTamanhoEComAdaptador() {
        assertEquals(listOf("prg"), OPTIONS["trs80"])
        assertEquals("16", parseArgs(listOf("dump", "-s", "trs80", "--prg", "16")).opts["prg"])
        assertTrue(CartSystem.TRS80.needsAdapter)
    }

    @Test fun tamanhosAceitos() {
        for (kb in listOf(2, 4, 8, 10, 16, 32, 64, 128)) assertNull(Rules.romSize(CartSystem.TRS80, kb), "$kb")
        for (kb in listOf(0, 1, 12, 24, 48, 256)) assertNotNull(Rules.romSize(CartSystem.TRS80, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) {
            val hint = I18n.t(l, S.TRS80_HINT)
            assertTrue(hint.contains("TRS80.cpp") && (hint.contains("5 V") || hint.contains("5 В")), "$l")
            assertTrue(I18n.t(l, S.V_TRS80_SIZE).contains("128"), "$l")
        }
    }
}
