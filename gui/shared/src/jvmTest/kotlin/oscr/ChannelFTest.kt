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

/** Fairchild Channel F (F-20, D224): sistema 27, modos, tamanhos aceitos e textos. Espelha host/tests/test_channelf.py. */
class ChannelFTest {
    @Test fun idEExtensao() {
        assertEquals(27, CartSystem.CHANNELF.id); assertEquals(".bin", CartSystem.CHANNELF.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "channelf" })
    }

    @Test fun opcoesModoETamanho() {
        assertEquals(listOf("mapper", "prg"), OPTIONS["channelf"])
        val a = parseArgs(listOf("dump", "-s", "channelf", "--mapper", "1", "--prg", "3")); assertEquals("3", a.opts["prg"]); assertEquals("1", a.opts["mapper"])
    }

    @Test fun tamanhosDoFirmware() {
        for (kb in listOf(2, 3, 4, 6)) assertNull(Rules.romSize(CartSystem.CHANNELF, kb), "$kb")
        for (kb in listOf(0, 1, 5, 8, 16)) assertNotNull(Rules.romSize(CartSystem.CHANNELF, kb), "$kb")
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.CHANNELF_HINT, S.V_CHANNELF_SIZE, S.CHF_MODE, S.CHF_MODE_ROM, S.CHF_MODE_16K)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
