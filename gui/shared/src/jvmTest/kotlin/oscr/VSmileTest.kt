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

/** V.Smile (F-20, D228): sistema 30, tamanho em KB (4, 6, 8 ou 16 MB), com adaptador, fora dos planejados, aviso nos 4 idiomas. Espelha host/tests/test_vsmile.py e pc-tests/test_vsm.cpp. */
class VSmileTest {
    @Test fun idEExtensao() {
        assertEquals(30, CartSystem.VSMILE.id); assertEquals(".bin", CartSystem.VSMILE.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "vsmile" })
    }

    @Test fun opcaoDeTamanhoEComAdaptador() {
        assertEquals(listOf("prg"), OPTIONS["vsmile"])
        assertEquals("8192", parseArgs(listOf("dump", "-s", "vsmile", "--prg", "8192")).opts["prg"])
        assertTrue(CartSystem.VSMILE.needsAdapter)
    }

    @Test fun tamanhosAceitos() {
        for (kb in listOf(4096, 6144, 8192, 16384)) assertNull(Rules.romSize(CartSystem.VSMILE, kb), "$kb")
        for (kb in listOf(0, 4, 8, 2048, 12288, 32768)) assertNotNull(Rules.romSize(CartSystem.VSMILE, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) {
            val hint = I18n.t(l, S.VSMILE_HINT)
            assertTrue(hint.contains("3.3") || hint.contains("3,3"), "$l")
            assertTrue(hint.contains("VSmile.cpp"), "$l")
            assertTrue(I18n.t(l, S.V_VSMILE_SIZE).contains("16384"), "$l")
        }
    }
}
