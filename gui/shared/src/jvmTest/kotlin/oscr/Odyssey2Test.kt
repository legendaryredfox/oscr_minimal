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

/** Magnavox Odyssey 2 / Videopac (F-20, D226): sistema 28, mapper (A10), tamanhos aceitos e textos. Espelha host/tests/test_odyssey2.py e pc-tests/test_ody.cpp. */
class Odyssey2Test {
    @Test fun idEExtensao() {
        assertEquals(28, CartSystem.ODYSSEY2.id); assertEquals(".bin", CartSystem.ODYSSEY2.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "odyssey2" })
    }

    @Test fun opcoesMapperETamanho() {
        assertEquals(listOf("mapper", "prg"), OPTIONS["odyssey2"])
        val a = parseArgs(listOf("dump", "-s", "odyssey2", "--mapper", "1", "--prg", "4"))
        assertEquals("1", a.opts["mapper"]); assertEquals("4", a.opts["prg"])
    }

    @Test fun regrasDoFirmware() {
        for (kb in listOf(2, 4, 8, 12, 16)) assertNull(Rules.odyssey2(0, kb), "$kb")
        for (kb in listOf(0, 1, 3, 6, 32)) assertNotNull(Rules.odyssey2(0, kb), "$kb")
        assertNull(Rules.odyssey2(1, 4))
        for (kb in listOf(2, 8, 16)) assertEquals(S.V_ODY2_A10, Rules.odyssey2(1, kb)?.key, "$kb")
        assertEquals(S.V_UNSUPPORTED_MAPPER, Rules.odyssey2(2, 4)?.key)
    }

    @Test fun textosNosQuatroIdiomas() {
        val keys = listOf(S.ODY2_HINT, S.V_ODY2_SIZE, S.V_ODY2_A10, S.ODY2_MAPPER, S.ODY2_MAPPER_STD, S.ODY2_MAPPER_A10)
        for (l in Lang.entries) for (k in keys) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
