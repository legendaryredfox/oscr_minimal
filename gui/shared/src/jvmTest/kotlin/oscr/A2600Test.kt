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

/** Atari 2600 (F-20, D206): sistema 15, mappers e textos. Espelha host/tests/test_a2600.py. */
class A2600Test {
    @Test fun idEExtensao() {
        assertEquals(15, CartSystem.A2600.id); assertEquals(".a26", CartSystem.A2600.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() { assertFalse(PLANNED_SYSTEMS.any { it.key == "a2600" }) }

    @Test fun opcaoSoMapper() { assertEquals(listOf("mapper"), OPTIONS["a2600"]) }

    @Test fun mapperEmHexadecimal() {
        assertEquals("0xF8", parseArgs(listOf("dump", "-s", "a2600", "--mapper", "0xF8")).opts["mapper"])
        assertEquals(0xF8, parseArgs(listOf("dump", "-s", "a2600", "--mapper", "0xF8")).int("mapper"))
        assertEquals(248, parseArgs(listOf("dump", "-s", "a2600", "--mapper", "248")).int("mapper"))
    }

    @Test fun tabela() {
        assertEquals(23, A2600.MAPPERS.size)
        assertEquals(A2600.MAPPERS.size, A2600.MAPPERS.map { it.id }.toSet().size)
        assertEquals(8, A2600.byId(0xF8)?.kb); assertEquals(0, A2600.byId(0xE7)?.kb); assertNull(A2600.byId(0x41))
    }

    @Test fun regra() {
        assertNull(Rules.a2600(0xF8)); assertNull(Rules.a2600(0x40))
        assertNotNull(Rules.a2600(0)); assertNotNull(Rules.a2600(0x41))
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.A2600_HINT, S.A2600_MAPPER, S.V_A2600_MAPPER)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
