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

/** Neo Geo Pocket (F-20, D202): sistema 13, tamanhos aceitos e textos. Espelha host/tests/test_ngp.py. */
class NgpTest {
    @Test fun idEExtensao() {
        assertEquals(13, CartSystem.NGP.id); assertEquals(".ngp", CartSystem.NGP.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "ngp" })
    }

    @Test fun opcaoSoPrg() {
        assertEquals(listOf("prg"), OPTIONS["ngp"])
        assertEquals("2048", parseArgs(listOf("dump", "-s", "ngp", "--prg", "2048")).opts["prg"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(0, 512, 1024, 2048, 4096)) assertNull(Rules.romSize(CartSystem.NGP, kb), "$kb")
        for (kb in listOf(4, 256, 3072, 8192)) assertNotNull(Rules.romSize(CartSystem.NGP, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.NGP_HINT, S.V_NGP_SIZE)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
